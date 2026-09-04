"""Synthetic journal integrity and virtual-time replay tests."""

import io
import unittest
from unittest.mock import patch
from zlib import crc32

from test_usb_protocol import jpeg_packet

from server.common.protocol import MAX_READ, U32, encode
from server.input.frames import FRAME_TTL_NS
from server.input.recording import (
    FILE_MAGIC,
    RECORD_HEADER,
    SESSION,
    Record,
    RecordingReader,
    RecordingWriter,
    RecordKind,
    Source,
    replay_records,
)
from tools.replay_usb import demo_recording


class RecordingTests(unittest.TestCase):
    def test_virtual_tick_expires_incomplete_frame(self):
        records = [
            Record(RecordKind.START, 0, SESSION.pack(7)),
            Record(RecordKind.RX, 1, encode(jpeg_packet(data=b"\xff\xd8"))),
            Record(RecordKind.TICK, 1 + FRAME_TTL_NS),
            Record(
                RecordKind.RX,
                2 + FRAME_TTL_NS,
                encode(jpeg_packet(seq=2, offset=2, data=b"ok\xff\xd9")),
            ),
        ]
        self.assertEqual(list(replay_records(RecordingReader(self.journal(records)))), [])

    def journal(self, records, source=Source.SYNTHETIC):
        file = io.BytesIO()
        writer = RecordingWriter(file, source)
        for record in records:
            writer.append(record)
        file.seek(0)
        return file

    def test_demo_is_replay_never_live(self):
        reader = RecordingReader(demo_recording())
        frames = list(replay_records(reader))
        self.assertEqual(reader.source, Source.SYNTHETIC)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].origin, "replay")
        self.assertIsNone(frames[0].mapped_capture_ns)

    def test_round_trip_raw_chunks_and_source(self):
        records = [
            Record(RecordKind.START, 0, SESSION.pack(7)),
            Record(RecordKind.RX, 1, b"bad crc and noise"),
            Record(RecordKind.TICK, 2),
            Record(RecordKind.DISCONNECT, 3),
        ]
        reader = RecordingReader(self.journal(records, Source.LIVE))
        self.assertEqual(reader.source, Source.LIVE)
        self.assertEqual(list(reader), records)

    def test_short_file_reads(self):
        class ShortReader(io.BytesIO):
            def read(self, size=-1):
                return super().read(min(size, 2))

        reader = RecordingReader(ShortReader(demo_recording().getvalue()))
        self.assertEqual(len(list(replay_records(reader))), 1)

    def test_truncation_within_each_record_rejected(self):
        wire = demo_recording().getvalue()
        # Complete-record boundaries are valid prefixes (there is no final footer).
        boundaries = {len(FILE_MAGIC) + 5}
        reader = RecordingReader(io.BytesIO(wire))
        for _ in reader:
            boundaries.add(reader.bytes_read)
        for length in range(len(wire)):
            if length in boundaries:
                continue
            with self.subTest(length=length), self.assertRaises(ValueError):
                list(RecordingReader(io.BytesIO(wire[:length])))

    def test_corruption_and_unknown_version(self):
        original = demo_recording().getvalue()
        for index in (0, 8, 12, 20, len(original) - 1):
            wire = bytearray(original)
            wire[index] ^= 0x80
            with self.subTest(index=index), self.assertRaises(ValueError):
                list(RecordingReader(io.BytesIO(wire)))

    def test_malformed_record_bounds_and_time(self):
        writer = RecordingWriter(io.BytesIO(), Source.SYNTHETIC)
        writer.append(Record(RecordKind.START, 5, SESSION.pack(7)))
        for record in (
            Record(RecordKind.TICK, 4),
            Record(RecordKind.RX, 6),
            Record(RecordKind.RX, 6, b"x" * (MAX_READ + 1)),
            Record(RecordKind.START, 6, SESSION.pack(0)),
            Record(RecordKind.DISCONNECT, 6, b"x"),
        ):
            with self.assertRaises(ValueError):
                writer.append(record)

    def test_reader_rejects_forged_lengths_and_backward_time(self):
        file = self.journal([Record(RecordKind.START, 5, SESSION.pack(7))])
        prefix = file.getvalue()
        for kind, elapsed, data, length in (
            (RecordKind.RX, 6, b"", MAX_READ + 1),
            (RecordKind.TICK, 4, b"", 0),
            (99, 6, b"", 0),
        ):
            header = RECORD_HEADER.pack(kind, elapsed, length)
            wire = prefix + header + data + U32.pack(crc32(header + data))
            with self.assertRaises(ValueError):
                list(RecordingReader(io.BytesIO(wire)))

    def test_total_size_limit_reader_writer(self):
        file = io.BytesIO()
        writer = RecordingWriter(file, Source.SYNTHETIC)
        with patch("server.input.recording.MAX_RECORDING", 20):
            with self.assertRaises(ValueError):
                writer.append(Record(RecordKind.START, 0, SESSION.pack(7)))
            with self.assertRaises(ValueError):
                list(RecordingReader(demo_recording_unpatched()))

    def test_replay_requires_start_and_clears_partial_on_disconnect(self):
        records = [Record(RecordKind.RX, 0, encode(jpeg_packet()))]
        with self.assertRaises(ValueError):
            list(replay_records(RecordingReader(self.journal(records))))
        records = [
            Record(RecordKind.START, 0, SESSION.pack(7)),
            Record(RecordKind.RX, 1, encode(jpeg_packet(data=b"\xff\xd8"))),
            Record(RecordKind.DISCONNECT, 2),
            Record(RecordKind.START, 3, SESSION.pack(8)),
            Record(RecordKind.RX, 4, encode(jpeg_packet(seq=2, offset=2, data=b"ok\xff\xd9"))),
        ]
        self.assertEqual(list(replay_records(RecordingReader(self.journal(records)))), [])


# Build before patching the size constant so the reader limit is independently tested.
DEMO = demo_recording().getvalue()


def demo_recording_unpatched():
    return io.BytesIO(DEMO)


if __name__ == "__main__":
    unittest.main()
