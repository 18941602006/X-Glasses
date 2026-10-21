"""Download only the reviewed, pinned inference snapshot; no training binaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from server.perception.locate.pc_runtime import DEFAULT_MODEL, MODEL_REPO, MODEL_REVISION

WEIGHTS = {
    "model-00001-of-00002.safetensors": (
        4_959_632_160,
        "923cfc10fed19808067da6df85a9a4220ddc1f9eb91ceee94c0fecd05d0f2d58",
    ),
    "model-00002-of-00002.safetensors": (
        2_701_795_216,
        "3459ba101f40594f3f62d3312014f1f8378b4ba3da3b1d562480045938fc7d47",
    ),
}


def download_ranges(directory: Path, name: str, size: int, expected_sha: str) -> None:
    """Resume verified HTTP ranges when a full CDN stream stalls."""
    target = directory / name
    if target.is_file() and target.stat().st_size == size:
        with target.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() == expected_sha:
                print(f"Verified existing {name}", flush=True)
                return
        raise RuntimeError(f"existing weight hash mismatch: {name}")
    parts = directory / ".xg-parts" / name
    parts.mkdir(parents=True, exist_ok=True)
    chunk_size = 16 * 1024 * 1024

    def get_part(start: int) -> Path:
        end = min(start + chunk_size, size) - 1
        part = parts / f"{start:012d}.part"
        if part.is_file() and part.stat().st_size == end - start + 1:
            return part
        url = (
            f"https://huggingface.co/{MODEL_REPO}/resolve/{MODEL_REVISION}/{name}"
            f"?download=true&xg_offset={start}"
        )
        request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    expected_range = f"bytes {start}-{end}/{size}"
                    if (
                        response.status != 206
                        or response.headers.get("Content-Range") != expected_range
                    ):
                        raise RuntimeError("CDN returned an unexpected range")
                    data = response.read(end - start + 2)
                if len(data) != end - start + 1:
                    raise RuntimeError("incomplete weight range")
                part.write_bytes(data)
                return part
            except (OSError, RuntimeError):
                if attempt == 2:
                    raise
        raise RuntimeError("range download failed")

    offsets = list(range(0, size, chunk_size))
    with ThreadPoolExecutor(max_workers=6) as pool:
        pending = [pool.submit(get_part, start) for start in offsets]
        for done, future in enumerate(as_completed(pending), 1):
            future.result()
            if done % 10 == 0 or done == len(offsets):
                print(f"{name}: {done}/{len(offsets)} ranges", flush=True)
    staging = target.with_suffix(".assembling")
    digest = hashlib.sha256()
    with staging.open("wb") as output:
        for start in offsets:
            data = (parts / f"{start:012d}.part").read_bytes()
            digest.update(data)
            output.write(data)
    if digest.hexdigest() != expected_sha:
        raise RuntimeError("weight SHA256 mismatch")
    os.replace(staging, target)
    # Only remove chunks created by this downloader, after successful verification.
    for start in offsets:
        (parts / f"{start:012d}.part").unlink()
    print(f"SHA256 verified {name}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--range-download", action="store_true")
    args = parser.parse_args()
    from huggingface_hub import snapshot_download

    snapshot_download(
        MODEL_REPO,
        revision=MODEL_REVISION,
        local_dir=args.model_dir,
        allow_patterns=["*.py", "*.json", "*.txt", "*.safetensors", "LICENSE", "README.md"],
        ignore_patterns=["*.safetensors"] if args.range_download else None,
        max_workers=2,
    )
    if args.range_download:
        for name, (size, digest) in WEIGHTS.items():
            download_ranges(args.model_dir, name, size, digest)
    hashes = {}
    for path in sorted(args.model_dir.glob("*")):
        if path.is_file() and path.name not in {"xg_revision.txt", "xg_sha256.json"}:
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                    digest.update(block)
            hashes[path.name] = digest.hexdigest()
    (args.model_dir / "xg_sha256.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    (args.model_dir / "xg_revision.txt").write_text(MODEL_REVISION + "\n", encoding="utf-8")
    print(f"Prepared {MODEL_REPO}@{MODEL_REVISION}; {len(hashes)} hashed files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
