"""Internal isolated worker for explicitly enabled PC evaluation jobs."""

from __future__ import annotations

import argparse
import base64
import contextlib
import io
import json
import re
import sys
import time
from pathlib import Path

from server.api.pc_jobs import MAX_REQUEST, validate_request


class WorkerState:
    def __init__(self):
        self.locator = None
        self.translations = {}

    def english(self, request: dict) -> str:
        query = request["query"].strip()
        if not any("\u3400" <= c <= "\u9fff" for c in query):
            return query
        if request.get("allow_cloud_translation") is not True:
            raise ValueError("translation consent required")
        if query not in self.translations:
            from server.perception.assist.deepseek import DeepSeekDialogue, load_api_key

            translated = DeepSeekDialogue(load_api_key(), timeout_seconds=20).translate_query(query)
            if len(self.translations) >= 32:
                self.translations.pop(next(iter(self.translations)))
            self.translations[query] = translated
        return self.translations[query]


def execute(request: dict, state: WorkerState | None = None) -> dict:
    state = state or WorkerState()
    if request["kind"] == "locate":
        from PIL import Image, ImageOps

        from server.perception.locate.pc_runtime import PcLocateRuntime

        raw = base64.b64decode(request["image_base64"], validate=True)
        with Image.open(io.BytesIO(raw)) as opened:
            if opened.format not in {"JPEG", "PNG"} or opened.width * opened.height > 16_000_000:
                raise ValueError("bounded JPEG/PNG required")
            image = ImageOps.exif_transpose(opened).convert("RGB")
        query_en = state.english(request)
        reused = state.locator is not None
        if state.locator is None:
            state.locator = PcLocateRuntime()
        result = state.locator.locate(image, query_en, source=request.get("source", "file"))
        result.update(query_en=query_en, model_reused=reused)
        return result
    from server.perception.assist.contracts import EventStamp
    from server.perception.assist.deepseek import DeepSeekDialogue, load_api_key

    now = time.monotonic_ns()
    event = DeepSeekDialogue(load_api_key()).ask(
        request["question"], EventStamp(1, "pc-text", now, now + 60_000_000_000, "external")
    )
    return {"text": event.text}


def serve(root: Path) -> int:
    state = WorkerState()
    while True:
        token = sys.stdin.readline(128)
        if not token:
            return 0
        token = token.strip()
        if not re.fullmatch(r"[0-9a-f]{32}", token):
            return 1
        source = root / f"{token}.in"
        temporary, target = root / f"{token}.tmp", root / f"{token}.out"
        try:
            with source.open("rb") as stream:
                raw = stream.read(MAX_REQUEST + 1)
            if len(raw) > MAX_REQUEST:
                raise ValueError("request too large")
            request = validate_request(json.loads(raw))
            with contextlib.redirect_stdout(sys.stderr):
                result = execute(request, state)
            payload = {"ok": True, "result": result}
        except Exception:
            payload = {"ok": False, "result": None}
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, allow_nan=False), encoding="utf-8"
        )
        temporary.replace(target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--input", type=Path)
    mode.add_argument("--serve", type=Path)
    args = parser.parse_args()
    if args.serve:
        return serve(args.serve)
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
