"""One in-flight JPEG and one consumable latest frame; no image/model imports."""

from dataclasses import dataclass
from struct import Struct

from server.common.protocol import Kind, Packet

FRAGMENT = Struct("<III")  # frame_id, total JPEG length, byte offset
MAX_JPEG = 256 * 1024
FRAME_TTL_NS = 500_000_000


def newer_u32(value: int, previous: int) -> bool:
    return 0 < ((value - previous) & 0xFFFFFFFF) < 0x80000000


@dataclass(frozen=True)
class Frame:
    session_id: int
    frame_id: int
    capture_us: int
    first_received_ns: int
    completed_ns: int
    jpeg: bytes
    origin: str
    mapped_capture_ns: int | None = None
    timing_status: str = "unsynchronized"
    calibration_id: str | None = None
    time_uncertainty_ns: int | None = None


class FrameAssembler:
    def __init__(self, origin: str):
        if origin not in ("live", "replay", "synthetic"):
            raise ValueError("unknown input origin")
        self.origin = origin
        self.reset()

    def reset(self):
        self.frame_id = None
        self.capture_us = None
        self.total = 0
        self.started_ns = 0
        self.data = bytearray()
        self.latest = None
        self.last_started_id = None

    def _abandon(self):
        self.frame_id = None
        self.data.clear()

    def expire(self, now_ns):
        if self.frame_id is not None and now_ns - self.started_ns >= FRAME_TTL_NS:
            self._abandon()
        if self.latest is not None:
            if now_ns - self.latest.first_received_ns >= FRAME_TTL_NS:
                self.latest = None

    def push(self, packet: Packet, now_ns: int):
        self.expire(now_ns)
        if packet.kind != Kind.JPEG:
            return
        if len(packet.payload) <= FRAGMENT.size:
            self._abandon()
            return
        frame_id, total, offset = FRAGMENT.unpack_from(packet.payload)
        fragment = packet.payload[FRAGMENT.size :]
        if not 4 <= total <= MAX_JPEG or offset + len(fragment) > total:
            self._abandon()
            return
        if offset == 0:
            if self.last_started_id is not None and not newer_u32(frame_id, self.last_started_id):
                return
            self._abandon()
            self.last_started_id = frame_id
            self.frame_id, self.total = frame_id, total
            self.capture_us, self.started_ns = packet.capture_us, now_ns
        if (
            frame_id != self.frame_id
            or total != self.total
            or packet.capture_us != self.capture_us
            or offset != len(self.data)
        ):
            self._abandon()
            return
        self.data.extend(fragment)
        if len(self.data) == total:
            jpeg = bytes(self.data)
            if jpeg.startswith(b"\xff\xd8") and jpeg.endswith(b"\xff\xd9"):
                self.latest = Frame(
                    packet.session_id,
                    frame_id,
                    packet.capture_us,
                    self.started_ns,
                    now_ns,
                    jpeg,
                    self.origin,
                )
            self._abandon()

    def pop_latest(self, now_ns: int) -> Frame | None:
        self.expire(now_ns)
        frame, self.latest = self.latest, None
        return frame
