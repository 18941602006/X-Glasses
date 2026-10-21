"""Persistent isolated PC worker. No model imports in the HTTP process."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from threading import Event

from server.api.pc_jobs import MAX_OUTPUT, ROOT, JobFailure, ProcessRunner, stop_process_tree


class WarmProcessRunner:
    def __init__(self, python: Path, *, timeout: float = 180):
        self.fallback = ProcessRunner(python, timeout=timeout)
        self.process = None
        self.directory = None
        self.error = None
        self.closed = False

    def _start(self):
        if self.closed:
            raise JobFailure("worker_closed")
        if self.process is not None and self.process.poll() is None:
            return
        self._reset()
        self.directory = tempfile.TemporaryDirectory(prefix="xg-warm-")
        root = Path(self.directory.name)
        self.error = (root / "worker.err").open("w+b")
        environment = dict(
            os.environ,
            HF_HUB_OFFLINE="1",
            TRANSFORMERS_OFFLINE="1",
            PYTHONIOENCODING="utf-8",
            PYTHONUTF8="1",
        )
        self.process = subprocess.Popen(
            [str(self.fallback.python), "-m", "tools.pc_worker", "--serve", str(root)],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=self.error,
            env=environment,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    def __call__(self, request: dict, cancelled: Event) -> dict:
        if request["kind"] != "locate":
            return self.fallback(request, cancelled)
        try:
            self._start()
            root = Path(self.directory.name)
            token = uuid.uuid4().hex
            source, target = root / f"{token}.in", root / f"{token}.out"
            source.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
            self.error.seek(0)
            self.error.truncate()
            self.process.stdin.write((token + "\n").encode("ascii"))
            self.process.stdin.flush()
            started = time.monotonic()
            while True:
                if cancelled.wait(0.05):
                    raise JobFailure("cancelled")
                if time.monotonic() - started > self.fallback.timeout:
                    raise JobFailure("timeout")
                if self.process.poll() is not None:
                    raise JobFailure("worker_failed_check_local_setup")
                if os.fstat(self.error.fileno()).st_size > MAX_OUTPUT:
                    raise JobFailure("worker_output_limit")
                if target.exists():
                    raw = target.read_bytes()
                    if len(raw) > MAX_OUTPUT:
                        raise JobFailure("worker_output_limit")
                    response = json.loads(raw)
                    if set(response) != {"ok", "result"} or response["ok"] is not True:
                        raise JobFailure("worker_failed_check_local_setup")
                    source.unlink(missing_ok=True)
                    target.unlink(missing_ok=True)
                    return response["result"]
        except Exception:
            # Cancel/timeout/crash poison the worker. Never reuse uncertain GPU state.
            self._reset()
            raise

    def _reset(self):
        if self.process:
            stop_process_tree(self.process)
            if self.process.stdin:
                self.process.stdin.close()
            self.process = None
        if self.error:
            self.error.close()
            self.error = None
        if self.directory:
            for attempt in range(10):
                try:
                    self.directory.cleanup()
                    break
                except PermissionError:
                    if attempt == 9:
                        raise
                    time.sleep(0.05)
            self.directory = None

    def close(self):
        self.closed = True
        self._reset()
