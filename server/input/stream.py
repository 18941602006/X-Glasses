"""Host stream core, without serial enumeration, hardware writes or safety output."""

from time import monotonic_ns
from typing import Callable, Protocol

from server.common.protocol import MAX_READ, Decoder, Packet, encode
from server.input.frames import FrameAssembler, newer_u32


class ByteStream(Protocol):
    """Adapter must bound its own blocking read/write by the supplied deadline."""

    def read(self, size: int, deadline_ns: int) -> bytes: ...

    def write(self, data: bytes, deadline_ns: int) -> int: ...


def write_packet(
    stream: ByteStream, packet: Packet, deadline_ns: int, clock: Callable[[], int] = monotonic_ns
):
    """Short writes are completed; failure is not ACK and must invalidate the link."""
    wire = encode(packet)
    offset = 0
    while offset < len(wire):
        if clock() >= deadline_ns:
            raise TimeoutError("packet write deadline")
        count = stream.write(wire[offset:], deadline_ns)
        if not isinstance(count, int) or not 0 < count <= len(wire) - offset:
            raise OSError("write made no progress or returned invalid count")
        offset += count
        if clock() >= deadline_ns:
            raise TimeoutError("packet write exceeded deadline")


class InputSession:
    """Caller explicitly binds a negotiated session. Unknown packets cannot rebind it."""

    def __init__(self, origin="synthetic"):
        self.decoder = Decoder()
        self.frames = FrameAssembler(origin)
        self.session_id = None
        self.last_sequence = None
        self.last_now_ns = -1
        self.last_invalidation = "not_connected"
        self.wrong_session = 0
        self.old_packets = 0
        self.sequence_gaps = 0

    def _time(self, now_ns):
        if now_ns < 0 or now_ns < self.last_now_ns:
            raise ValueError("host time must be monotonic")
        self.last_now_ns = now_ns

    def start(self, session_id: int, now_ns: int):
        if not 0 < session_id < 2**64:
            raise ValueError("invalid session")
        self._time(now_ns)
        self.decoder.reset()
        self.frames.reset()
        self.session_id = session_id
        self.last_sequence = None
        self.last_invalidation = "session_started_unsynchronized"

    def disconnect(self, now_ns: int):
        self._time(now_ns)
        self.decoder.reset()
        self.frames.reset()
        self.session_id = None
        self.last_sequence = None
        self.last_invalidation = "disconnected"

    def feed(self, data: bytes, now_ns: int) -> list[Packet]:
        self._time(now_ns)
        if len(data) > MAX_READ:
            raise ValueError("oversized read")
        if self.session_id is None:
            return []
        self.frames.expire(now_ns)
        accepted = []
        for packet in self.decoder.feed(data, now_ns):
            if packet.session_id != self.session_id:
                self.wrong_session += 1
                continue
            if self.last_sequence is not None:
                if not newer_u32(packet.sequence, self.last_sequence):
                    self.old_packets += 1
                    continue
                gap = (packet.sequence - self.last_sequence - 1) & 0xFFFFFFFF
                self.sequence_gaps += gap
            self.last_sequence = packet.sequence
            self.frames.push(packet, now_ns)
            accepted.append(packet)
        return accepted

    def pop_latest(self, now_ns):
        self._time(now_ns)
        return self.frames.pop_latest(now_ns)

    def poll(
        self, stream: ByteStream, deadline_ns: int, clock: Callable[[], int] = monotonic_ns
    ) -> list[Packet]:
        if self.session_id is None:
            raise RuntimeError("start a negotiated session before reading")
        try:
            if clock() >= deadline_ns:
                raise TimeoutError("read deadline")
            data = stream.read(MAX_READ, deadline_ns)
            now_ns = clock()
            if now_ns > deadline_ns:
                raise TimeoutError("read exceeded deadline")
            return self.feed(data, now_ns)  # b'' is an idle tick, not proof of disconnection.
        except (OSError, ValueError):
            self.disconnect(max(clock(), self.last_now_ns))
            raise
