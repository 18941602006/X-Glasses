"""Bounded PC evaluation jobs; no hardware control, cloud images or model imports."""

from __future__ import annotations

import base64
import json
import math
import os
import subprocess
import tempfile
import time
import uuid
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
from threading import Event, RLock, Thread

MAX_IMAGE = 1024 * 1024
MAX_REQUEST = 1_410_000
MAX_OUTPUT = 131_072
ROOT = Path(__file__).resolve().parents[2]


class JobBusy(RuntimeError):
    pass


class JobFailure(RuntimeError):
    pass


def validate_request(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("invalid job")
    kind = value.get("kind")
    if kind == "locate" and set(value) == {"kind", "query", "image_base64"}:
        text, limit = value["query"], 160
        encoded = value["image_base64"]
        if not isinstance(encoded, str) or len(encoded) > (MAX_IMAGE + 2) // 3 * 4:
            raise ValueError("image too large")
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError):
            raise ValueError("invalid image encoding") from None
        if not 4 <= len(raw) <= MAX_IMAGE or not (
            raw.startswith(b"\xff\xd8") or raw.startswith(b"\x89PNG\r\n\x1a\n")
        ):
            raise ValueError("JPEG or PNG required")
    elif kind == "dialogue" and set(value) == {"kind", "question", "allow_cloud_text"}:
        if value["allow_cloud_text"] is not True:
            raise ValueError("explicit cloud text consent required")
        text, limit = value["question"], 1000
    else:
        raise ValueError("unexpected job fields")
    if not isinstance(text, str) or not text.strip() or len(text) > limit:
        raise ValueError("invalid query")
    if any(not char.isprintable() for char in text):
        raise ValueError("invalid query")
    return deepcopy(value)


def public_result(kind: str, value: object) -> dict:
    """Revalidate worker data; never expose diagnostics, credentials or arbitrary fields."""
    if not isinstance(value, dict):
        raise ValueError("invalid worker result")
    if kind == "dialogue":
        text = value.get("text")
        if not isinstance(text, str) or not text or len(text) > 2000:
            raise ValueError("invalid answer")
        return {"text": text, "source": "deepseek-official", "observation": "text_only"}
    boxes = value.get("boxes")
    if not isinstance(boxes, list) or len(boxes) > 16:
        raise ValueError("invalid boxes")
    for box in boxes:
        if (
            not isinstance(box, list)
            or len(box) != 4
            or any(type(n) not in (int, float) or not math.isfinite(n) for n in box)
        ):
            raise ValueError("invalid box")
        if not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
            raise ValueError("invalid box")
    size = value.get("image_size")
    if (
        not isinstance(size, list)
        or len(size) != 2
        or any(type(n) is not int or not 1 <= n <= 640 for n in size)
    ):
        raise ValueError("invalid image size")
    elapsed = value.get("inference_ms")
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError("invalid duration")
    return {
        "source": "file",
        "boxes": boxes,
        "image_size": size,
        "inference_ms": elapsed,
        "confidence": None,
        "distance_m": None,
        "tof_status": "not_connected",
        "grasp_confirmed": False,
        "observation": "static_image_not_live",
    }


class ProcessRunner:
    def __init__(self, python: Path, *, timeout: float = 180):
        if not python.is_file() or not 0 < timeout <= 180:
            raise ValueError("PC Python executable and bounded timeout required")
        self.python, self.timeout = python.resolve(), timeout

    def __call__(self, request: dict, cancelled: Event) -> dict:
        with tempfile.TemporaryDirectory(prefix="xg-pc-") as directory:
            root = Path(directory)
            request_path = root / "request.json"
            request_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
            with (root / "out").open("w+b") as output, (root / "err").open("w+b") as error:
                environment = dict(
                    os.environ,
                    HF_HUB_OFFLINE="1",
                    TRANSFORMERS_OFFLINE="1",
                    PYTHONIOENCODING="utf-8",
                    PYTHONUTF8="1",
                )
                process = subprocess.Popen(
                    [str(self.python), "-m", "tools.pc_worker", "--input", str(request_path)],
                    cwd=ROOT,
                    stdin=subprocess.DEVNULL,
                    stdout=output,
                    stderr=error,
                    env=environment,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                started = time.monotonic()
                try:
                    while process.poll() is None:
                        if cancelled.wait(0.05):
                            raise JobFailure("cancelled")
                        if time.monotonic() - started >= self.timeout:
                            raise JobFailure("timeout")
                        if any(
                            os.fstat(stream.fileno()).st_size > MAX_OUTPUT
                            for stream in (output, error)
                        ):
                            raise JobFailure("worker_output_limit")
                    if process.returncode != 0:
                        raise JobFailure("worker_failed_check_local_setup")
                    if os.fstat(error.fileno()).st_size > MAX_OUTPUT:
                        raise JobFailure("worker_output_limit")
                    output.seek(0)
                    raw = output.read(MAX_OUTPUT + 1)
                    if len(raw) > MAX_OUTPUT:
                        raise JobFailure("worker_output_limit")
                    return json.loads(raw)
                finally:
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=5)


class PcJobs:
    """One active process, no waiting queue, sixteen in-memory terminal receipts."""

    def __init__(self, runner):
        self.runner = runner
        self.lock = RLock()
        self.records: OrderedDict[str, dict] = OrderedDict()
        self.active: str | None = None
        self.cancelled = Event()
        self.thread: Thread | None = None
        self.closed = False

    def submit(self, request: object) -> dict:
        request = validate_request(request)
        with self.lock:
            if self.closed or self.active is not None:
                raise JobBusy("worker busy or closed")
            job_id = uuid.uuid4().hex
            record = {
                "job_id": job_id,
                "kind": request["kind"],
                "state": "running",
                "result": None,
                "error": None,
            }
            self.records[job_id] = record
            while len(self.records) > 16:
                self.records.popitem(last=False)
            self.active, self.cancelled = job_id, Event()
            self.thread = Thread(
                target=self._run, args=(job_id, request, self.cancelled), daemon=True
            )
            self.thread.start()
            return deepcopy(record)

    def _run(self, job_id: str, request: dict, cancelled: Event) -> None:
        result, failure = None, None
        try:
            result = public_result(request["kind"], self.runner(request, cancelled))
        except JobFailure as exc:
            failure = (
                str(exc)
                if str(exc) in {"timeout", "cancelled", "worker_output_limit"}
                else "worker_failed_check_local_setup"
            )
        except Exception:
            failure = "worker_failed_check_local_setup"
        with self.lock:
            record = self.records[job_id]
            if record["state"] != "cancelled":
                record.update(
                    state="failed" if failure else "succeeded", result=result, error=failure
                )
            self.active = None

    def current(self) -> dict | None:
        with self.lock:
            return self.get(self.active) if self.active else None

    def get(self, job_id: str) -> dict:
        with self.lock:
            if job_id not in self.records:
                raise KeyError("job not found")
            return deepcopy(self.records[job_id])

    def cancel(self, job_id: str) -> dict:
        with self.lock:
            if job_id == self.active:
                self.records[job_id].update(state="cancelled", result=None, error="cancelled")
                self.cancelled.set()
            return self.get(job_id)

    def close(self) -> None:
        with self.lock:
            self.closed = True
            if self.active:
                self.cancel(self.active)
            thread = self.thread
        if thread:
            thread.join(timeout=10)
