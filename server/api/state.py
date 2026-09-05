"""Thread-safe, bounded status projection for the desktop dashboard."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from typing import Callable

SCHEMA = "xg.status.v1"
CAPABILITIES = ("clock", "tof", "imu", "button", "camera", "haptic")
COMMANDS = ("start_stream", "stop_stream", "cancel_haptic", "safe_stop")
MAX_COMMANDS = 32
MAX_LOGS = 100


def initial_snapshot(now_ns: int = 0) -> dict:
    return {
        "schema": SCHEMA,
        "revision": 0,
        "generated_ns": str(now_ns),
        "mode": "offline",
        "link": {
            "state": "disconnected",
            "reason": "not_connected",
            "session_id": None,
            "boot_id": None,
            "capabilities": {name: False for name in CAPABILITIES},
            "clock": {"state": "unknown", "uncertainty_ms": None},
        },
        "frame": {
            "state": "absent",
            "source": "none",
            "frame_id": None,
            "age_ms": None,
            "width": None,
            "height": None,
            "calibration_id": None,
        },
        "tof": {"state": "unknown", "valid_zones": 0, "total_zones": 0, "zones_mm": []},
        "imu": {"state": "unknown", "sample_id": None},
        "calibration": {"state": "missing", "calibration_id": None},
        "commands": [],
        "logs": [],
    }


class DashboardStore:
    def __init__(self, now_ns: int = 0):
        self._lock = RLock()
        self._value = initial_snapshot(now_ns)

    def snapshot(self, now_ns: int) -> dict:
        if now_ns < 0:
            raise ValueError("monotonic timestamp must be nonnegative")
        with self._lock:
            value = deepcopy(self._value)
        value["generated_ns"] = str(now_ns)
        return value

    def update(self, section: str, value: dict) -> None:
        if section not in {"link", "frame", "tof", "imu", "calibration"}:
            raise ValueError("unknown dashboard section")
        if not isinstance(value, dict):
            raise TypeError("dashboard section must be an object")
        with self._lock:
            self._value[section] = deepcopy(value)
            self._value["revision"] += 1

    def set_mode(self, mode: str) -> None:
        if mode not in {"offline", "live", "replay"}:
            raise ValueError("unknown source mode")
        with self._lock:
            self._value["mode"] = mode
            self._value["revision"] += 1

    def add_log(self, level: str, message: str, now_ns: int) -> None:
        if level not in {"info", "warning", "error"} or not message or len(message) > 240:
            raise ValueError("invalid bounded log entry")
        with self._lock:
            self._value["logs"].append({"level": level, "message": message, "at_ns": str(now_ns)})
            self._value["logs"] = self._value["logs"][-MAX_LOGS:]
            self._value["revision"] += 1

    def record_command(self, command: dict) -> None:
        with self._lock:
            self._value["commands"].append(deepcopy(command))
            self._value["commands"] = self._value["commands"][-MAX_COMMANDS:]
            self._value["revision"] += 1

    def resolve_command(self, request_id: int | str, state: str) -> bool:
        if state not in {"applied", "rejected", "expired", "timeout", "disconnected"}:
            raise ValueError("invalid terminal command state")
        with self._lock:
            for command in reversed(self._value["commands"]):
                if command["request_id"] == str(request_id) and command["state"] == "pending":
                    command["state"] = state
                    self._value["revision"] += 1
                    return True
        return False


class CommandUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandReceipt:
    request_id: str
    action: str
    state: str = "pending"


class CommandBroker:
    """Policy boundary between HTTP requests and an injected host controller."""

    def __init__(
        self,
        store: DashboardStore,
        dispatcher: Callable[[str, int], int] | None = None,
    ):
        self.store = store
        self.dispatcher = dispatcher

    def submit(self, action: str, now_ns: int) -> CommandReceipt:
        if action not in COMMANDS:
            raise ValueError("unknown command action")
        if self.dispatcher is None:
            raise CommandUnavailable("no device command dispatcher is attached")
        request_id = self.dispatcher(action, now_ns)
        if not isinstance(request_id, int) or not 0 < request_id < 2**64:
            raise RuntimeError("dispatcher returned invalid request id")
        receipt = CommandReceipt(str(request_id), action)
        self.store.record_command(
            {
                "request_id": receipt.request_id,
                "action": action,
                "state": receipt.state,
                "at_ns": str(now_ns),
            }
        )
        return receipt
