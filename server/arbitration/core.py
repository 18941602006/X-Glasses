"""Bounded output arbitration with fixed safety priorities and cancellation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from server.perception.assist.contracts import EventStamp, bounded_text

Category = Literal[
    "sensor_failure",
    "emergency",
    "local_direction",
    "traffic_signal",
    "map",
    "locate",
    "reading",
    "dialogue",
]

PRIORITY: dict[Category, int] = {
    "sensor_failure": 600,
    "emergency": 550,
    "local_direction": 450,
    "traffic_signal": 400,
    "map": 300,
    "locate": 220,
    "reading": 210,
    "dialogue": 100,
}


@dataclass(frozen=True)
class OutputCandidate:
    stamp: EventStamp
    category: Category
    message: str
    cue: Literal["none", "warning", "left", "right", "confirm"] = "none"

    def __post_init__(self):
        if not isinstance(self.category, str) or self.category not in PRIORITY:
            raise ValueError("invalid output category")
        bounded_text(self.message, "output message", 500)
        normalized = self.message.casefold().replace(" ", "")
        forbidden = ("可以过街", "安全过街", "现在过街", "safetocross", "crossnow")
        if any(phrase in normalized for phrase in forbidden):
            raise ValueError("crossing authorization is forbidden")
        if self.cue not in {"none", "warning", "left", "right", "confirm"}:
            raise ValueError("invalid output cue")


@dataclass(frozen=True)
class OutputDecision:
    decision_id: str
    candidate: OutputCandidate
    selected_ns: int
    priority: int


class OutputArbiter:
    """Keeps only the newest item per category and never reads sensors or models."""

    def __init__(self, maximum_categories: int = 8, minimum_repeat_ns: int = 500_000_000):
        if maximum_categories != len(PRIORITY) or minimum_repeat_ns <= 0:
            raise ValueError("fixed bounded arbitration configuration required")
        self._items: dict[Category, OutputCandidate] = {}
        self._minimum_repeat_ns = minimum_repeat_ns
        self._last_fingerprint: tuple[str, str] | None = None
        self._last_selected_ns: int | None = None
        self._sequence = 0

    def submit(self, candidate: OutputCandidate, now_ns: int, session_id: int) -> bool:
        if not candidate.stamp.active(now_ns, session_id):
            return False
        previous = self._items.get(candidate.category)
        if previous is not None and previous.stamp.created_ns > candidate.stamp.created_ns:
            return False
        self._items[candidate.category] = candidate
        return True

    def cancel(self, correlation_id: str, session_id: int) -> int:
        removed = [
            category
            for category, item in self._items.items()
            if item.stamp.session_id == session_id and item.stamp.correlation_id == correlation_id
        ]
        for category in removed:
            del self._items[category]
        return len(removed)

    def clear_session(self) -> None:
        self._items.clear()
        self._last_fingerprint = None
        self._last_selected_ns = None

    def decide(self, now_ns: int, session_id: int) -> OutputDecision | None:
        self._items = {
            category: item
            for category, item in self._items.items()
            if item.stamp.active(now_ns, session_id)
        }
        if not self._items:
            return None
        selected = max(
            self._items.values(),
            key=lambda item: (PRIORITY[item.category], item.stamp.created_ns),
        )
        fingerprint = (selected.category, selected.message)
        if (
            fingerprint == self._last_fingerprint
            and self._last_selected_ns is not None
            and now_ns - self._last_selected_ns < self._minimum_repeat_ns
        ):
            return None
        self._sequence += 1
        self._last_fingerprint = fingerprint
        self._last_selected_ns = now_ns
        return OutputDecision(
            f"out-{session_id}-{self._sequence}", selected, now_ns, PRIORITY[selected.category]
        )
