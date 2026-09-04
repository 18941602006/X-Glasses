"""Run with python -m tools.replay_usb --demo or --replay <explicit recording>."""

import argparse
import io
import json
from pathlib import Path

from server.common.protocol import Kind, Packet, encode
from server.input.frames import FRAGMENT
from server.input.recording import (
    SESSION,
    Record,
    RecordingReader,
    RecordingWriter,
    RecordKind,
    Source,
    replay_records,
)


def demo_recording() -> io.BytesIO:
    file = io.BytesIO()
    writer = RecordingWriter(file, Source.SYNTHETIC)
    writer.append(Record(RecordKind.START, 0, SESSION.pack(7)))
    # Deliberately only marker-wrapped synthetic bytes, NOT a decodable camera image.
    wire = encode(Packet(Kind.JPEG, 7, 1, 123, FRAGMENT.pack(1, 6, 0) + b"\xff\xd8ok\xff\xd9"))
    writer.append(Record(RecordKind.RX, 1_000_000, wire[:17]))
    writer.append(Record(RecordKind.RX, 2_000_000, wire[17:]))
    writer.append(Record(RecordKind.DISCONNECT, 3_000_000))
    file.seek(0)
    return file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--demo", action="store_true", help="in-memory synthetic data; no files written"
    )
    mode.add_argument("--replay", type=Path, help="read a recording, never send to hardware")
    args = parser.parse_args()
    try:
        with demo_recording() if args.demo else args.replay.open("rb") as file:
            reader = RecordingReader(file)
            frames, jpeg_bytes = 0, 0
            for frame in replay_records(reader):
                frames += 1
                jpeg_bytes += len(frame.jpeg)
            print(
                json.dumps(
                    {
                        "input_source": reader.source.name.lower(),
                        "mode": "replay",
                        "frames": frames,
                        "jpeg_bytes": jpeg_bytes,
                        "timing": "unsynchronized",
                        "hardware_verified": False,
                    }
                )
            )
        return 0
    except (OSError, ValueError) as exc:
        print(f"Replay failed: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
