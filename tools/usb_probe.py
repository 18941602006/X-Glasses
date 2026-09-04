"""Explicit CDC handshake/clock probe; no capture, recording, haptic, or auto-connect."""

import argparse
import json
import secrets
from time import monotonic_ns

from server.common.protocol import MAX_READ
from server.input.link import HostLink
from server.input.serial_port import SerialPort
from server.input.stream import write_packet


def probe(port_name, seconds):
    link = HostLink("live")
    port = SerialPort.open(port_name)
    end_ns = monotonic_ns() + int(seconds * 1_000_000_000)
    next_clock = 0
    try:
        now = monotonic_ns()
        hello = link.begin(secrets.randbits(64) or 1, secrets.randbits(64) or 1, now)
        write_packet(port, hello, now + 100_000_000)
        while monotonic_ns() < end_ns:
            now = monotonic_ns()
            link.tick(now)
            if link.state == "disconnected":
                raise OSError(link.reason)
            if link.state == "ready" and now >= next_clock and link.clock_request is None:
                write_packet(port, link.request_clock(now), now + 100_000_000)
                next_clock = now + 1_000_000_000
            data = port.read(MAX_READ, monotonic_ns() + 100_000_000)
            link.feed(data, monotonic_ns())
        link.tick(monotonic_ns())
        if link.state != "ready" or not link.clock.is_ready(monotonic_ns()):
            raise OSError("probe ended without a live synchronized session")
        return {
            "state": link.state,
            "reason": link.reason,
            "origin": "live",
            "clock_samples": len(link.clock.samples),
            "malformed": link.malformed,
            "product_acceptance": False,
        }
    finally:
        link.disconnect(monotonic_ns(), "probe_finished")
        port.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--list", action="store_true", help="list port names/VID/PID, never open")
    modes.add_argument("--port", help="explicit local port with X-Glasses native CDC firmware")
    parser.add_argument("--seconds", type=float, default=5.0)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 60:
        parser.error("seconds must be 1..60")
    try:
        if args.list:
            from serial.tools.list_ports import comports

            print(json.dumps([{"port": p.device, "vid": p.vid, "pid": p.pid} for p in comports()]))
        else:
            print(json.dumps(probe(args.port, args.seconds)))
        return 0
    except (ImportError, OSError, ValueError) as exc:
        print(f"USB probe failed: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
