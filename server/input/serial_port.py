"""Explicit local serial adapter. Never scans-and-opens devices or accepts network URLs."""

import re
from time import monotonic_ns

from server.common.protocol import MAX_READ


class SerialPort:
    def __init__(self, port):
        self.port = port

    @classmethod
    def open(cls, name):
        if not re.fullmatch(r"COM[1-9][0-9]*|/dev/(?:ttyACM|ttyUSB|cu\.)[A-Za-z0-9_.-]+", name):
            raise ValueError("explicit local CDC port required; URLs and auto-open forbidden")
        import serial

        port = serial.Serial(
            port=None,
            baudrate=115200,
            timeout=0.02,
            write_timeout=0.1,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )
        # DTR allows native CDC firmware to detect a host. This is not a bootloader toggle.
        port.dtr = True
        port.rts = False
        port.port = name
        try:
            port.open()
        except Exception:
            port.close()
            raise
        return cls(port)

    def read(self, size, deadline_ns):
        if not 0 < size <= MAX_READ:
            raise ValueError("invalid read size")
        remaining = (deadline_ns - monotonic_ns()) / 1_000_000_000
        if remaining <= 0:
            raise TimeoutError("serial read deadline")
        self.port.timeout = min(0.02, remaining)
        # Do not wait to fill 64KiB when only a short packet is currently available.
        return self.port.read(min(size, max(1, self.port.in_waiting)))

    def write(self, data, deadline_ns):
        remaining = (deadline_ns - monotonic_ns()) / 1_000_000_000
        if remaining <= 0:
            raise TimeoutError("serial write deadline")
        self.port.write_timeout = min(0.1, remaining)
        return self.port.write(data)

    def close(self):
        self.port.close()
