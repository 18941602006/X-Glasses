"""Real PC image/camera inference. Saves only when --output is explicitly provided."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from server.perception.locate.pc_runtime import DEFAULT_MODEL, PcLocateRuntime


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--image", type=Path)
    source.add_argument("--camera", type=int)
    parser.add_argument("--query", required=True, help="English description recommended")
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, help="Explicitly save annotated image and JSON")
    args = parser.parse_args()
    from PIL import Image, ImageDraw

    if args.image:
        with Image.open(args.image) as opened:
            image = opened.convert("RGB")
        source_name = "file"
    else:
        import cv2

        capture = cv2.VideoCapture(args.camera)
        try:
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError("PC camera unavailable")
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        finally:
            capture.release()
        source_name = "pc_camera"
    runtime = PcLocateRuntime(args.model_dir)
    result = runtime.locate(image, args.query, source=source_name)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.output:
        image.thumbnail((640, 480))
        draw = ImageDraw.Draw(image)
        for x1, y1, x2, y2 in result["boxes"]:
            draw.rectangle(
                (x1 * image.width, y1 * image.height, x2 * image.width, y2 * image.height),
                outline="lime",
                width=3,
            )
        draw.text((5, 5), "PC evaluation | ToF: UNKNOWN | no depth guidance", fill="red")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image.save(args.output)
        args.output.with_suffix(".json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
