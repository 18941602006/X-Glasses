"""Optional pyserial loopback, never physical USB. Core suite works without installation."""

import unittest
from time import monotonic_ns

from server.input.serial_port import SerialPort

try:
    import serial
except ImportError:
    serial = None


class SerialPortTests(unittest.TestCase):
    def test_remote_and_implicit_ports_rejected(self):
        for name in ("", "auto", "socket://example.com:1", "rfc2217://localhost:1", "loop://"):
            with self.assertRaises(ValueError):
                SerialPort.open(name)

    @unittest.skipIf(serial is None, "optional pyserial not installed; loopback not tested")
    def test_local_loopback_short_read_and_closed_port(self):
        port = SerialPort(serial.serial_for_url("loop://", timeout=0.02, write_timeout=0.1))
        self.addCleanup(port.close)
        self.assertEqual(port.write(b"hello", monotonic_ns() + 1_000_000_000), 5)
        self.assertEqual(port.read(3, monotonic_ns() + 1_000_000_000), b"hel")
        self.assertEqual(port.read(3, monotonic_ns() + 1_000_000_000), b"lo")
        with self.assertRaises(TimeoutError):
            port.read(1, 0)
        with self.assertRaises(TimeoutError):
            port.write(b"x", 0)
        port.close()
        with self.assertRaises(OSError):
            port.read(1, monotonic_ns() + 1_000_000_000)


if __name__ == "__main__":
    unittest.main()
