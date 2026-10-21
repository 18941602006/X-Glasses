"""Explicit PC text-dialogue smoke test; key input never appears in command history."""

from __future__ import annotations

import argparse
import getpass
import json
import time
import uuid
from pathlib import Path

from server.perception.assist.contracts import EventStamp
from server.perception.assist.deepseek import (
    LOCAL_CONFIG,
    DeepSeekDialogue,
    DialogueFailure,
    load_api_key,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configure", action="store_true", help="Save key to ignored local config")
    parser.add_argument("--question")
    parser.add_argument("--image", type=Path)
    parser.add_argument("--allow-image-upload", action="store_true")
    args = parser.parse_args()
    if args.image and (not args.question or not args.allow_image_upload):
        parser.error("--image requires --question and explicit --allow-image-upload")
    if args.configure:
        if LOCAL_CONFIG.exists():
            raise SystemExit("Local config already exists; edit it locally to avoid overwriting")
        key = getpass.getpass("DeepSeek API key (hidden): ").strip()
        if not key or any(not c.isprintable() for c in key):
            raise SystemExit("Invalid key")
        with LOCAL_CONFIG.open("x", encoding="utf-8") as stream:
            json.dump({"deepseek_api_key": key}, stream)
        print("Saved local-only credential configuration")
    if args.question:
        now = time.monotonic_ns()
        stamp = EventStamp(1, uuid.uuid4().hex, now, now + 60_000_000_000, "external")
        try:
            if args.image and args.image.stat().st_size > 2 * 1024 * 1024:
                raise DialogueFailure("image exceeds 2 MiB")
            event = DeepSeekDialogue(load_api_key()).ask(
                args.question,
                stamp,
                image=args.image.read_bytes() if args.image else None,
                allow_image_upload=args.allow_image_upload,
            )
        except DialogueFailure as error:
            print(str(error))
            return 1
        print(event.text)
    elif not args.configure:
        parser.error("provide --configure or --question")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
