"""Internal isolated worker for explicitly enabled PC evaluation jobs."""

from __future__ import annotations

import argparse
import base64
import contextlib
import io
import json
import sys
import time
from pathlib import Path

from server.api.pc_jobs import MAX_REQUEST, validate_request


def execute(request: dict) -> dict:
    if request["kind"] == "locate":
        from PIL import Image, ImageOps

        from server.perception.locate.pc_runtime import PcLocateRuntime

        raw = base64.b64decode(request["image_base64"], validate=True)
        with Image.open(io.BytesIO(raw)) as opened:
            if opened.format not in {"JPEG", "PNG"} or opened.width * opened.height > 16_000_000:
                raise ValueError("bounded JPEG/PNG required")
            image = ImageOps.exif_transpose(opened).convert("RGB")
        return PcLocateRuntime().locate(image, request["query"], source="file")
    from server.perception.assist.contracts import EventStamp
    from server.perception.assist.deepseek import DeepSeekDialogue, load_api_key

    now = time.monotonic_ns()
    event = DeepSeekDialogue(load_api_key()).ask(
        request["question"], EventStamp(1, "pc-text", now, now + 60_000_000_000, "external")
    )
    return {"text": event.text}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        raw = args.input.read_bytes()
        if len(raw) > MAX_REQUEST:
            raise ValueError("request too large")
        request = validate_request(json.loads(raw))
        with contextlib.redirect_stdout(sys.stderr):
            result = execute(request)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except Exception:
        # Do not serialize exception text, request content or credentials.
        print(
            "PC worker failed; verify the isolated environment/model/credential setup",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
