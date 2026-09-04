"""XG USB framing v1. CRC detects corruption; it is not authentication."""

from dataclasses import dataclass
from enum import IntEnum
from struct import Struct
from zlib import crc32

MAGIC = b"XG03"
VERSION = 1
MAX_PAYLOAD = 4096
MAX_READ = 65536
HEADER = Struct("<4sBBHQIQI")
U32 = Struct("<I")
HEADER_SIZE = HEADER.size + U32.size
MAX_WIRE = HEADER_SIZE + MAX_PAYLOAD + U32.size
PARTIAL_TIMEOUT_NS = 500_000_000


class Kind(IntEnum):
    JPEG = 1
    TOF = 2
    IMU = 3
    BUTTON = 4
    STATUS = 5
    COMMAND = 6
    ACK = 7
    CLOCK = 8


@dataclass(frozen=True)
class Packet:
    kind: Kind
    session_id: int
    sequence: int
    capture_us: int
    payload: bytes


def encode(packet: Packet) -> bytes:
    if not 0 < packet.session_id < 2**64:
        raise ValueError("session must be a nonzero uint64")
    if not 0 <= packet.sequence < 2**32 or not 0 <= packet.capture_us < 2**64:
        raise ValueError("invalid sequence or device timestamp")
    if not isinstance(packet.payload, bytes) or len(packet.payload) > MAX_PAYLOAD:
        raise ValueError("payload must be bounded immutable bytes")
    kind = Kind(packet.kind)
    header = HEADER.pack(
        MAGIC,
        VERSION,
        kind,
        0,
        packet.session_id,
        packet.sequence,
        packet.capture_us,
        len(packet.payload),
    )
    return header + U32.pack(crc32(header)) + packet.payload + U32.pack(crc32(packet.payload))


class Decoder:
    """Incremental, bounded parser. Call feed(b'', now_ns) during idle polling."""

    def __init__(self):
        self.buffer = bytearray()
        self.partial_since_ns = None
        self.last_now_ns = -1
        self.bad_headers = 0
        self.bad_payloads = 0
        self.timeouts = 0
        self.discarded_bytes = 0

    def reset(self):
        self.buffer.clear()
        self.partial_since_ns = None
        self.last_now_ns = -1

    def _drop(self, count):
        del self.buffer[:count]
        self.discarded_bytes += count
        self.partial_since_ns = None

    def feed(self, data: bytes, now_ns: int) -> list[Packet]:
        if len(data) > MAX_READ or now_ns < 0 or now_ns < self.last_now_ns:
            raise ValueError("oversized read or nonmonotonic host time")
        self.last_now_ns = now_ns
        if self.partial_since_ns is not None:
            if now_ns - self.partial_since_ns >= PARTIAL_TIMEOUT_NS:
                self.timeouts += 1
                self._drop(1)
        result = self._drain(now_ns)
        # Never append an unbounded caller buffer; even transient storage is bounded.
        for offset in range(0, len(data), MAX_WIRE):
            self.buffer.extend(data[offset : offset + MAX_WIRE])
            result.extend(self._drain(now_ns))
        return result

    def _drain(self, now_ns):
        packets = []
        while self.buffer:
            position = self.buffer.find(MAGIC)
            if position < 0:
                if len(self.buffer) > len(MAGIC) - 1:
                    self._drop(len(self.buffer) - len(MAGIC) + 1)
                break
            if position:
                self._drop(position)
            if len(self.buffer) < HEADER_SIZE:
                break
            raw = self.buffer[: HEADER.size]
            fields = HEADER.unpack(raw)
            _, version, kind, flags, session, sequence, capture, length = fields
            if (
                crc32(raw) != U32.unpack_from(self.buffer, HEADER.size)[0]
                or version != VERSION
                or flags != 0
                or session == 0
                or kind not in Kind._value2member_map_
                or length > MAX_PAYLOAD
            ):
                self.bad_headers += 1
                self._drop(1)
                continue
            size = HEADER_SIZE + length + U32.size
            if len(self.buffer) < size:
                break
            payload = bytes(self.buffer[HEADER_SIZE : HEADER_SIZE + length])
            if crc32(payload) != U32.unpack_from(self.buffer, HEADER_SIZE + length)[0]:
                self.bad_payloads += 1
                self._drop(1)
                continue
            packets.append(Packet(Kind(kind), session, sequence, capture, payload))
            del self.buffer[:size]
            self.partial_since_ns = None
        if self.buffer and self.partial_since_ns is None:
            self.partial_since_ns = now_ns
        return packets
