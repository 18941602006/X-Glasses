"""Synthetic protocol tests, not serial/hardware acceptance."""

import random
import unittest
from zlib import crc32

from server.common.protocol import (
    HEADER,
    HEADER_SIZE,
    MAGIC,
    MAX_PAYLOAD,
    MAX_READ,
    MAX_WIRE,
    PARTIAL_TIMEOUT_NS,
    U32,
    Decoder,
    Kind,
    Packet,
    encode,
)
from server.input.frames import FRAGMENT, FRAME_TTL_NS, MAX_JPEG
from server.input.stream import InputSession, write_packet


def jpeg_packet(
    seq=1, frame=1, offset=0, data=b"\xff\xd8ok\xff\xd9", total=6, session=7, capture=123
):
    return Packet(Kind.JPEG, session, seq, capture, FRAGMENT.pack(frame, total, offset) + data)


class ProtocolTests(unittest.TestCase):
    def test_golden_wire_layout(self):
        # Independent literal vector: little-endian fields plus CRC32/ISO-HDLC.
        packet = Packet(Kind.STATUS, 1, 2, 3, b"abc")
        header = bytes.fromhex("5847303301050000010000000000000002000000030000000000000003000000")
        self.assertEqual(HEADER_SIZE, 36)
        self.assertEqual(
            encode(packet), header + U32.pack(crc32(header)) + b"abc" + bytes.fromhex("c2412435")
        )
        self.assertEqual(Decoder().feed(encode(packet), 0), [packet])

    def test_every_split_and_bytewise(self):
        packet = jpeg_packet()
        wire = encode(packet)
        for split in range(len(wire) + 1):
            decoder = Decoder()
            self.assertEqual(
                decoder.feed(wire[:split], 0) + decoder.feed(wire[split:], 1), [packet]
            )
        decoder = Decoder()
        packets = []
        for index, byte in enumerate(wire):
            packets.extend(decoder.feed(bytes([byte]), index))
        self.assertEqual(packets, [packet])

    def test_coalesced_noise_and_crc_recovery(self):
        good = encode(jpeg_packet())
        for index in (8, HEADER_SIZE + 1, len(good) - 1):
            bad = bytearray(good)
            bad[index] ^= 0x80
            decoder = Decoder()
            self.assertEqual(decoder.feed(b"debug garbage" + bad + good, 0), [jpeg_packet()])
            self.assertGreater(decoder.discarded_bytes, 0)

    def test_valid_crc_invalid_header_rejected(self):
        good = encode(jpeg_packet())
        fields = list(HEADER.unpack(good[: HEADER.size]))
        for index, value in ((1, 99), (2, 99), (3, 1), (4, 0), (7, MAX_PAYLOAD + 1)):
            modified = fields.copy()
            modified[index] = value
            header = HEADER.pack(*modified)
            bad = header + U32.pack(crc32(header))
            decoder = Decoder()
            self.assertEqual(decoder.feed(bad + good, 0), [jpeg_packet()])
            self.assertGreater(decoder.bad_headers, 0)

    def test_partial_timeout_recovers_embedded_next_packet(self):
        header = HEADER.pack(MAGIC, 1, Kind.STATUS, 0, 7, 1, 0, MAX_PAYLOAD)
        decoder = Decoder()
        self.assertEqual(
            decoder.feed(header + U32.pack(crc32(header)) + encode(jpeg_packet()), 0), []
        )
        self.assertEqual(decoder.feed(b"", PARTIAL_TIMEOUT_NS), [jpeg_packet()])
        self.assertEqual(decoder.timeouts, 1)

    def test_limits_and_monotonic_time(self):
        decoder = Decoder()
        for _ in range(8):
            decoder.feed(b"x" * MAX_READ, 1)
            self.assertLess(len(decoder.buffer), MAX_WIRE)
        with self.assertRaises(ValueError):
            decoder.feed(b"x" * (MAX_READ + 1), 2)
        with self.assertRaises(ValueError):
            decoder.feed(b"", 0)
        for packet in (
            Packet(Kind.STATUS, 0, 0, 0, b""),
            Packet(Kind.STATUS, 7, -1, 0, b""),
            Packet(Kind.STATUS, 7, 1, -1, b""),
            Packet(Kind.STATUS, 7, 1, 0, b"x" * (MAX_PAYLOAD + 1)),
        ):
            with self.assertRaises(ValueError):
                encode(packet)

    def test_seeded_random_chunking(self):
        rng = random.Random(42)
        packets = [Packet(Kind.STATUS, 7, n, n * 100, rng.randbytes(n)) for n in range(100)]
        wire = b"".join(map(encode, packets))
        decoder, output, offset = Decoder(), [], 0
        while offset < len(wire):
            size = rng.randint(1, 500)
            output.extend(decoder.feed(wire[offset : offset + size], offset))
            offset += size
        self.assertEqual(output, packets)


class InputTests(unittest.TestCase):
    def setUp(self):
        self.input = InputSession("synthetic")
        self.input.start(7, 0)

    def send(self, packet, now=0):
        return self.input.feed(encode(packet), now)

    def test_maximum_frame_and_payload_boundary(self):
        jpeg = b"\xff\xd8" + b"x" * (MAX_JPEG - 4) + b"\xff\xd9"
        chunk_size = MAX_PAYLOAD - FRAGMENT.size
        for sequence, offset in enumerate(range(0, len(jpeg), chunk_size)):
            self.send(
                jpeg_packet(
                    seq=sequence,
                    offset=offset,
                    data=jpeg[offset : offset + chunk_size],
                    total=len(jpeg),
                )
            )
        self.assertEqual(self.input.pop_latest(0).jpeg, jpeg)
        self.assertEqual(self.input.frames.data, b"")

    def test_latest_consumed_once_unsynchronized(self):
        self.send(jpeg_packet())
        frame = self.input.pop_latest(1)
        self.assertEqual(frame.jpeg, b"\xff\xd8ok\xff\xd9")
        self.assertEqual(frame.capture_us, 123)
        self.assertIsNone(frame.mapped_capture_ns)
        self.assertEqual(frame.timing_status, "unsynchronized")
        self.assertEqual(frame.origin, "synthetic")
        self.assertIsNone(self.input.pop_latest(2))

    def test_interleaved_sensor_packet_preserved(self):
        self.send(jpeg_packet(data=b"\xff\xd8"))
        sensor = Packet(Kind.TOF, 7, 2, 130, b"opaque-not-a-distance")
        self.assertEqual(self.send(sensor), [sensor])
        self.send(jpeg_packet(seq=3, offset=2, data=b"ok\xff\xd9"))
        self.assertIsNotNone(self.input.pop_latest(0))

    def test_new_frame_replaces_partial_and_latest(self):
        self.send(jpeg_packet(data=b"\xff\xd8"))
        self.send(jpeg_packet(seq=2, frame=2))
        self.send(jpeg_packet(seq=3, frame=3))
        self.assertEqual(self.input.pop_latest(0).frame_id, 3)

    def test_out_of_order_overlap_wrong_metadata_drop(self):
        for change in ({"offset": 3}, {"offset": 1}, {"capture": 999}, {"total": 7}):
            with self.subTest(change=change):
                self.input.start(7, 0)
                self.send(jpeg_packet(data=b"\xff\xd8"))
                options = dict(seq=2, offset=2, data=b"ok\xff\xd9")
                options.update(change)
                self.send(jpeg_packet(**options))
                self.assertIsNone(self.input.pop_latest(0))
                self.assertEqual(len(self.input.frames.data), 0)

    def test_expiry_for_partial_and_completed(self):
        self.send(jpeg_packet())
        self.assertIsNone(self.input.pop_latest(FRAME_TTL_NS))
        self.send(jpeg_packet(seq=2, frame=2, data=b"\xff\xd8"), FRAME_TTL_NS)
        self.send(jpeg_packet(seq=3, frame=2, offset=2, data=b"ok\xff\xd9"), 2 * FRAME_TTL_NS)
        self.assertIsNone(self.input.pop_latest(2 * FRAME_TTL_NS))

    def test_bad_jpeg_and_oversized_frame(self):
        for packet in (
            jpeg_packet(data=b"notjpg"),
            jpeg_packet(total=MAX_JPEG + 1),
            Packet(Kind.JPEG, 7, 1, 0, b"short"),
        ):
            self.input.start(7, 0)
            self.send(packet)
            self.assertIsNone(self.input.pop_latest(0))

    def test_wrong_session_duplicates_sequence_and_wrap(self):
        self.assertEqual(self.send(jpeg_packet(session=9)), [])
        self.send(jpeg_packet(seq=0xFFFFFFFF, frame=0xFFFFFFFF))
        self.send(jpeg_packet(seq=0, frame=0))
        self.assertEqual(self.send(jpeg_packet(seq=0, frame=0)), [])
        self.assertEqual(self.input.pop_latest(0).frame_id, 0)
        self.assertEqual(self.input.wrong_session, 1)
        self.assertEqual(self.input.old_packets, 1)

    def test_gap_and_repeated_frame_not_republished(self):
        self.send(jpeg_packet())
        self.input.pop_latest(0)
        self.send(jpeg_packet(seq=3))
        self.assertIsNone(self.input.pop_latest(0))
        self.assertEqual(self.input.sequence_gaps, 1)

    def test_disconnect_and_rebind_clear_all_old_data(self):
        self.send(jpeg_packet())
        self.input.feed(encode(jpeg_packet(seq=2))[:20], 0)
        self.input.disconnect(1)
        self.assertIsNone(self.input.pop_latest(1))
        self.assertEqual(self.input.decoder.buffer, b"")
        self.assertEqual(self.send(jpeg_packet(), 1), [])
        self.input.start(8, 2)
        self.assertEqual(self.send(jpeg_packet(session=7), 2), [])
        self.send(jpeg_packet(session=8), 2)
        self.assertEqual(self.input.pop_latest(2).session_id, 8)


class FakeStream:
    def __init__(self, data=b"", size=3, failure=None):
        self.data, self.size, self.failure = data, size, failure
        self.written = bytearray()

    def read(self, size, deadline_ns):
        if self.failure:
            raise self.failure
        result, self.data = self.data[: min(size, self.size)], self.data[min(size, self.size) :]
        return result

    def write(self, data, deadline_ns):
        self.written.extend(data[: self.size])
        return min(self.size, len(data))


class TransportTests(unittest.TestCase):
    def test_read_overrun_invalidates_link_and_write_overrun_fails(self):
        receiver = InputSession("synthetic")
        receiver.start(7, 0)
        times = iter([0, 101, 101])
        with self.assertRaises(TimeoutError):
            receiver.poll(FakeStream(), 100, clock=lambda: next(times))
        self.assertIsNone(receiver.session_id)
        times = iter([0, 101])
        with self.assertRaises(TimeoutError):
            write_packet(FakeStream(), jpeg_packet(), 100, clock=lambda: next(times))

    def test_short_writes(self):
        stream = FakeStream()
        write_packet(stream, jpeg_packet(), 100, clock=lambda: 0)
        self.assertEqual(stream.written, encode(jpeg_packet()))

    def test_zero_write_and_deadline_fail(self):
        with self.assertRaises(OSError):
            write_packet(FakeStream(size=0), jpeg_packet(), 100, clock=lambda: 0)
        with self.assertRaises(TimeoutError):
            write_packet(FakeStream(), jpeg_packet(), 100, clock=lambda: 100)

    def test_short_reads_idle_and_disconnect(self):
        receiver = InputSession("synthetic")
        receiver.start(7, 0)
        stream = FakeStream(encode(jpeg_packet()))
        while stream.data:
            receiver.poll(stream, 100, clock=lambda: 0)
        receiver.poll(stream, 100, clock=lambda: 0)
        self.assertEqual(receiver.session_id, 7)
        self.assertIsNotNone(receiver.pop_latest(0))
        with self.assertRaises(OSError):
            receiver.poll(FakeStream(failure=OSError("unplug")), 100, clock=lambda: 0)
        self.assertIsNone(receiver.session_id)
        self.assertEqual(receiver.last_invalidation, "disconnected")


if __name__ == "__main__":
    unittest.main()
