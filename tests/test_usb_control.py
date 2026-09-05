"""Synthetic host control, sensor contract and clock-boundary tests."""

import unittest
from zlib import crc32

from test_usb_protocol import jpeg_packet

from server.common.clock import CLOCK_TTL_NS, MAX_RTT_NS, ClockMapper
from server.common.control import ACK, CLOCK_RESPONSE, COMMAND, HEARTBEAT, WELCOME, Opcode
from server.common.protocol import HEADER, MAX_PAYLOAD, U32, Kind, Packet, encode
from server.common.sensors import (
    BUTTON,
    IMU,
    TOF_HEADER,
    ZONE,
    decode_button,
    decode_imu,
    decode_tof,
)
from server.input.link import COMMAND_TTL_NS, HANDSHAKE_NS, HEARTBEAT_NS, MAX_PENDING, HostLink


def tof_payload(valid=True):
    zone = ZONE.pack(800, 1, 5) if valid else ZONE.pack(65535, 0, 255)
    return TOF_HEADER.pack(1, 4, 4) + zone * 16


class SensorTests(unittest.TestCase):
    def test_valid_and_unknown_tof(self):
        self.assertEqual(decode_tof(tof_payload()).zones[0].distance_mm, 800)
        unknown = decode_tof(tof_payload(False)).zones[0]
        self.assertIsNone(unknown.distance_mm)
        self.assertEqual(unknown.raw_status, 255)

    def test_tof_lengths_resolution_and_sentinels(self):
        for payload in (
            b"",
            tof_payload()[:-1],
            TOF_HEADER.pack(1, 8, 4),
            TOF_HEADER.pack(1, 4, 4) + ZONE.pack(0, 1, 5) * 16,
            TOF_HEADER.pack(1, 4, 4) + ZONE.pack(0, 0, 255) * 16,
            TOF_HEADER.pack(1, 4, 4) + ZONE.pack(10, 2, 255) * 16,
        ):
            with self.assertRaises(ValueError):
                decode_tof(payload)

    def test_imu_finite_and_validity(self):
        sample = decode_imu(IMU.pack(1, 0, 0, 9.81, 0, 0, 0, 1))
        self.assertTrue(sample.valid)
        for payload in (
            b"",
            IMU.pack(1, float("nan"), 0, 0, 0, 0, 0, 1),
            IMU.pack(1, 0, 0, 0, 0, 0, 0, 2),
        ):
            with self.assertRaises(ValueError):
                decode_imu(payload)
        self.assertFalse(decode_imu(IMU.pack(1, 0, 0, 0, 0, 0, 0, 0)).valid)

    def test_button_enum(self):
        self.assertTrue(decode_button(BUTTON.pack(1, 1, 1)).pressed)
        for payload in (b"", BUTTON.pack(1, 3, 1), BUTTON.pack(1, 1, 2)):
            with self.assertRaises(ValueError):
                decode_button(payload)


class ClockTests(unittest.TestCase):
    def test_discontinuous_device_clock_clears_old_estimate(self):
        clock = ClockMapper()
        clock.observe(1_000_000, 1000, 1000, 1_001_000)
        with self.assertRaises(ValueError):
            clock.observe(2_000_000, 1000000, 1000000, 2_001_000)
        self.assertFalse(clock.is_ready(2_001_000))

    def test_midpoint_error_and_expiry(self):
        clock = ClockMapper()
        self.assertIsNone(clock.map(1000, 0))
        clock.observe(1_000_000_000, 1000, 1100, 1_000_300_000)
        mapped = clock.map(1100, 1_000_300_000)
        self.assertEqual(mapped.host_ns, 1_000_200_000)
        self.assertEqual(mapped.uncertainty_ns, 102000)
        later = clock.map(1100, 1_000_400_000)
        self.assertGreaterEqual(later.uncertainty_ns, mapped.uncertainty_ns)
        self.assertIsNone(clock.map(1100, 1_000_300_000 + CLOCK_TTL_NS))

    def test_reject_invalid_order_processing_and_rtt(self):
        for values in (
            (-1, 0, 0, 10),
            (20, 1, 1, 10),
            (0, 20, 10, 100000),
            (0, 0, 1000, 10),
            (0, 0, 0, MAX_RTT_NS + 1),
        ):
            with self.assertRaises(ValueError):
                ClockMapper().observe(*values)

    def test_bounded_samples_reset_and_conservative_deadline(self):
        clock = ClockMapper()
        for n in range(20):
            clock.observe(n * 1_000_000, n * 1000, n * 1000, n * 1_000_000 + 1000)
        self.assertEqual(len(clock.samples), 8)
        self.assertLess(clock.device_deadline(19_001_000, 500_000_000), 519001)
        clock.reset()
        with self.assertRaises(ValueError):
            clock.device_deadline(20_000_000, 500_000_000)


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.link = HostLink("synthetic")
        self.sequence = 0
        self.link.begin(7, 123, 0)

    def send(self, kind, payload, now=1, capture=0, session=7):
        self.link.feed(encode(Packet(kind, session, self.sequence, capture, payload)), now)
        self.sequence += 1

    def ready(self):
        self.send(Kind.STATUS, WELCOME.pack(2, 123, 99, 0x3F))
        self.assertEqual(self.link.state, "ready")

    def sync(self):
        request = self.link.request_clock(1_000_000)
        req_id = self.link.clock_request[0]
        self.assertEqual(request.kind, Kind.CLOCK)
        self.send(Kind.CLOCK, CLOCK_RESPONSE.pack(req_id, 1_000_000, 1000, 1100), 1_200_000)

    def test_handshake_nonce_and_session(self):
        self.send(Kind.STATUS, WELCOME.pack(2, 456, 99, 0x3F))
        self.assertEqual(self.link.state, "handshaking")
        self.send(Kind.STATUS, WELCOME.pack(2, 123, 99, 0x3F), session=8)
        self.assertEqual(self.link.state, "handshaking")
        self.ready()

    def test_handshake_deadline(self):
        self.link.tick(HANDSHAKE_NS)
        self.assertEqual(self.link.reason, "handshake_timeout")
        with self.assertRaises(RuntimeError):
            self.link.command(Opcode.STOP_STREAM, HANDSHAKE_NS)

    def test_undeclared_sensor_clock_and_actuator_are_rejected(self):
        self.send(Kind.STATUS, WELCOME.pack(2, 123, 99, 0))
        with self.assertRaises(RuntimeError):
            self.link.request_clock(2)
        with self.assertRaises(RuntimeError):
            self.link.command(Opcode.HAPTIC, 2, 100, 10)
        with self.assertRaises(RuntimeError):
            self.link.command(Opcode.START_STREAM, 2)
        self.send(Kind.TOF, tof_payload(), 3, 1)
        self.assertEqual(self.link.malformed, 1)
        self.assertIsNone(self.link.sensor(Kind.TOF, 3))

    def test_heartbeat_timeout_and_reboot_clear_state(self):
        self.ready()
        self.sync()
        self.send(Kind.TOF, tof_payload(), 1_300_000, 1200)
        self.send(Kind.STATUS, HEARTBEAT.pack(3, 100), 1_400_000)
        self.assertEqual(self.link.reason, "device_reboot")
        self.assertEqual(self.link.sensors, {})
        self.assertEqual(len(self.link.clock.samples), 0)
        self.link.begin(8, 5, 2_000_000)
        self.send(Kind.STATUS, WELCOME.pack(2, 5, 100, 0x3F), 2_000_001, session=8)
        self.link.tick(2_000_001 + HEARTBEAT_NS)
        self.assertEqual(self.link.reason, "heartbeat_timeout")

    def test_unsolicited_clock_and_unsynchronized_actuation(self):
        self.ready()
        self.send(Kind.CLOCK, CLOCK_RESPONSE.pack(1, 0, 0, 0), 100)
        self.assertEqual(self.link.malformed, 1)
        with self.assertRaises(ValueError):
            self.link.command(Opcode.HAPTIC, 200, 100, 50)
        self.assertEqual(self.link.pending, {})
        self.assertIsNotNone(self.link.command(Opcode.CANCEL_HAPTIC, 300))

    def test_pending_only_becomes_applied_on_matching_ack(self):
        self.ready()
        self.sync()
        packet = self.link.command(Opcode.HAPTIC, 1_300_000, 100, 50)
        request, opcode, deadline, duration, intensity = COMMAND.unpack(packet.payload)
        self.assertGreater(deadline, 0)
        self.assertEqual((duration, intensity), (100, 50))
        self.assertEqual(len(self.link.results), 0)
        self.send(Kind.ACK, ACK.pack(request, Opcode.START_STREAM, 1), 1_400_000)
        self.assertIn(request, self.link.pending)
        self.send(Kind.ACK, ACK.pack(request, opcode, 1), 1_500_000)
        self.assertEqual(self.link.results[-1].state, "applied")
        self.assertEqual(self.link.results[-1].session_id, 7)
        self.send(Kind.ACK, ACK.pack(request, opcode, 1), 1_600_000)
        self.assertEqual(len(self.link.results), 1)

    def test_command_timeout_late_ack_and_queue_limit(self):
        self.ready()
        packets = [self.link.command(Opcode.STOP_STREAM, 100) for _ in range(MAX_PENDING)]
        with self.assertRaises(RuntimeError):
            self.link.command(Opcode.STOP_STREAM, 100)
        self.link.tick(100 + COMMAND_TTL_NS)
        self.assertEqual(len(self.link.pending), 0)
        request = COMMAND.unpack(packets[0].payload)[0]
        self.send(Kind.ACK, ACK.pack(request, Opcode.STOP_STREAM, 1), 101 + COMMAND_TTL_NS)
        self.assertTrue(all(result.state == "timeout" for result in self.link.results))

    def test_disconnect_marks_pending_with_old_session(self):
        self.ready()
        self.link.command(Opcode.STOP_STREAM, 100)
        self.link.disconnect(200)
        self.assertEqual(self.link.results[-1].state, "disconnected")
        self.assertEqual(self.link.results[-1].session_id, 7)
        self.assertEqual(self.link.pending, {})

    def test_sensor_freshness_unknown_and_bad_payload_invalidation(self):
        self.ready()
        self.send(Kind.TOF, tof_payload(), 100)
        self.assertIsNone(self.link.sensor(Kind.TOF, 200))
        self.sync()
        self.send(Kind.TOF, tof_payload(False), 1_300_000, 1200)
        value, estimate = self.link.sensor(Kind.TOF, 1_400_000)
        self.assertIsNone(value.zones[0].distance_mm)
        self.assertGreater(estimate.uncertainty_ns, 0)
        self.send(Kind.TOF, b"bad", 1_500_000, 1300)
        self.assertIsNone(self.link.sensor(Kind.TOF, 1_500_000))

    def test_future_and_old_samples_rejected(self):
        self.ready()
        self.sync()
        self.send(Kind.TOF, tof_payload(), 1_300_000, 1_000_000)
        self.assertIsNone(self.link.sensor(Kind.TOF, 1_400_000))
        self.send(Kind.TOF, tof_payload(), 600_000_000, 1000)
        self.assertIsNone(self.link.sensor(Kind.TOF, 600_000_001))

    def test_estimated_frame_and_buttons_consumed_once(self):
        self.ready()
        self.sync()
        packet = jpeg_packet(seq=self.sequence, capture=1200)
        self.link.feed(encode(packet), 1_300_000)
        self.sequence += 1
        frame = self.link.take_frame(1_400_000)
        self.assertEqual(frame.timing_status, "estimated")
        self.assertGreater(frame.time_uncertainty_ns, 0)
        self.assertIsNone(self.link.take_frame(1_400_000))
        self.send(Kind.BUTTON, BUTTON.pack(1, 1, 1), 1_500_000, 1400)
        self.assertEqual(len(self.link.take_buttons(1_600_000)), 1)
        self.assertEqual(self.link.take_buttons(1_600_000), [])

    def test_idle_resync_does_not_lose_handshake_packet(self):
        header = HEADER.pack(b"XG03", 1, Kind.STATUS, 0, 7, 0, 0, MAX_PAYLOAD)
        good = encode(Packet(Kind.STATUS, 7, 1, 0, WELCOME.pack(2, 123, 99, 0x3F)))
        self.link.feed(header + U32.pack(crc32(header)) + good, 0)
        self.link.tick(500_000_000)
        self.assertEqual(self.link.state, "ready")


if __name__ == "__main__":
    unittest.main()
