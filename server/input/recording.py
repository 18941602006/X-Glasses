"""Bounded, checksummed raw input journal; explicit caller-owned file handles only."""

from dataclasses import dataclass
from enum import IntEnum
from struct import Struct
from typing import BinaryIO, Iterator
from zlib import crc32

from server.common.protocol import MAX_READ, U32
from server.input.stream import InputSession

FILE_MAGIC = b"XGR1\r\n\x1a\n"
RECORD_HEADER = Struct("<BQI")  # kind, host elapsed ns, payload length
SESSION = Struct("<Q")
MAX_RECORDING = 64 * 1024 * 1024


class Source(IntEnum):
    SYNTHETIC = 1
    LIVE = 2


class RecordKind(IntEnum):
    START = 1
    RX = 2
    TICK = 3
    DISCONNECT = 4


@dataclass(frozen=True)
class Record:
    kind: RecordKind
    elapsed_ns: int
    payload: bytes = b""


def _validate(record: Record):
    RecordKind(record.kind)
    if not 0 <= record.elapsed_ns < 2**64 or len(record.payload) > MAX_READ:
        raise ValueError("record timestamp or size out of range")
    if record.kind == RecordKind.START:
        if len(record.payload) != SESSION.size or SESSION.unpack(record.payload)[0] == 0:
            raise ValueError("invalid session record")
    elif record.kind == RecordKind.RX:
        if not record.payload:
            raise ValueError("empty RX; use TICK")
    elif record.payload:
        raise ValueError("control record must be empty")


def _write_all(file: BinaryIO, data: bytes):
    offset = 0
    while offset < len(data):
        count = file.write(data[offset:])
        if count is None or not 0 < count <= len(data) - offset:
            raise OSError("recording write made no progress")
        offset += count


def _read_exact(file: BinaryIO, count: int, allow_eof=False) -> bytes:
    result = bytearray()
    while len(result) < count:
        chunk = file.read(count - len(result))
        if not chunk:
            if allow_eof and not result:
                return b""
            raise ValueError("truncated recording")
        if len(chunk) > count - len(result):
            raise ValueError("reader exceeded requested length")
        result.extend(chunk)
    return bytes(result)


class RecordingWriter:
    """No automatic file creation/upload. Caller must opt in and use exclusive creation."""

    def __init__(self, file: BinaryIO, source: Source):
        self.file = file
        self.last_ns = -1
        prefix = FILE_MAGIC + bytes([Source(source)])
        _write_all(file, prefix + U32.pack(crc32(prefix)))
        self.bytes_written = len(prefix) + U32.size

    def append(self, record: Record):
        _validate(record)
        if record.elapsed_ns < self.last_ns:
            raise ValueError("record times must be monotonic")
        header = RECORD_HEADER.pack(record.kind, record.elapsed_ns, len(record.payload))
        data = header + record.payload
        wire = data + U32.pack(crc32(data))
        if self.bytes_written + len(wire) > MAX_RECORDING:
            raise ValueError("recording size limit; explicitly start another file")
        _write_all(self.file, wire)
        self.bytes_written += len(wire)
        self.last_ns = record.elapsed_ns


class RecordingReader:
    def __init__(self, file: BinaryIO):
        self.file = file
        prefix = _read_exact(file, len(FILE_MAGIC) + 1)
        checksum = U32.unpack(_read_exact(file, U32.size))[0]
        if prefix[:-1] != FILE_MAGIC or crc32(prefix) != checksum:
            raise ValueError("invalid recording header/version/checksum")
        self.source = Source(prefix[-1])
        self.bytes_read = len(prefix) + U32.size
        self.last_ns = -1

    def __iter__(self) -> Iterator[Record]:
        while True:
            header = _read_exact(self.file, RECORD_HEADER.size, allow_eof=True)
            if not header:
                return
            kind, elapsed, length = RECORD_HEADER.unpack(header)
            if length > MAX_READ:
                raise ValueError("record payload exceeds limit")
            size = RECORD_HEADER.size + length + U32.size
            if self.bytes_read + size > MAX_RECORDING:
                raise ValueError("recording exceeds size limit")
            data = _read_exact(self.file, length)
            checksum = U32.unpack(_read_exact(self.file, U32.size))[0]
            if crc32(header + data) != checksum:
                raise ValueError("record checksum mismatch")
            record = Record(RecordKind(kind), elapsed, data)
            _validate(record)
            if elapsed < self.last_ns:
                raise ValueError("record time moved backwards")
            self.bytes_read += size
            self.last_ns = elapsed
            yield record


def replay_records(reader: RecordingReader):
    """Virtual time, no sleeping and no hardware output. Frames always marked replay."""
    receiver = InputSession("replay")
    try:
        for record in reader:
            now = record.elapsed_ns
            if record.kind == RecordKind.START:
                receiver.start(SESSION.unpack(record.payload)[0], now)
            elif record.kind == RecordKind.DISCONNECT:
                receiver.disconnect(now)
            else:
                if receiver.session_id is None:
                    raise ValueError("RX/TICK outside an active session")
                receiver.feed(record.payload, now)
            frame = receiver.pop_latest(now)
            if frame is not None:
                yield frame
    finally:
        receiver.disconnect(max(0, receiver.last_now_ns))
