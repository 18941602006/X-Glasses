"""Minimal loopback HTTP transport for the Phase 2B dashboard."""

from __future__ import annotations

import ipaddress
import json
import re
import time
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from server.api.pc_jobs import MAX_REQUEST, JobBusy, PcJobs
from server.api.state import CommandBroker, CommandUnavailable, DashboardStore

MAX_BODY = 1024


class LocalApiServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store: DashboardStore, broker: CommandBroker, pc_jobs=None):
        super().__init__(address, LocalApiHandler)
        self.store = store
        self.broker = broker
        self.pc_jobs: PcJobs | None = pc_jobs

    def server_close(self):
        if self.pc_jobs:
            self.pc_jobs.close()
        super().server_close()


class LocalApiHandler(BaseHTTPRequestHandler):
    server: LocalApiServer
    protocol_version = "HTTP/1.1"

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, format, *args):  # noqa: A002
        return

    def _send(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        self.end_headers()
        self.wfile.write(data)

    def _local_host(self) -> bool:
        header = self.headers.get("Host", "").lower()
        if header.startswith("[") and "]" in header:
            host = header[1 : header.index("]")]
        else:
            host = header.rsplit(":", 1)[0] if ":" in header else header
        return host in {"127.0.0.1", "localhost", "::1"}

    def do_GET(self):  # noqa: N802
        if not self._local_host():
            self._send(421, {"error": "local_host_required"})
            return
        path = urlsplit(self.path).path
        if path == "/api/v1/health":
            self._send(200, {"status": "ok", "scope": "loopback"})
        elif path == "/api/v1/status":
            self._send(200, self.server.store.snapshot(time.monotonic_ns()))
        elif path.startswith("/api/v1/pc/"):
            self._pc_request(path, post=False)
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self):  # noqa: N802
        if not self._local_host():
            self._send(421, {"error": "local_host_required"})
            return
        path = urlsplit(self.path).path
        if path.startswith("/api/v1/pc/"):
            self._pc_request(path, post=True)
            return
        if urlsplit(self.path).path != "/api/v1/commands":
            self._send(404, {"error": "not_found"})
            return
        if self.headers.get_content_type() != "application/json":
            self._send(415, {"error": "json_required"})
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._send(400, {"error": "invalid_content_length"})
            return
        if not 0 < length <= MAX_BODY:
            self._send(413, {"error": "body_size_invalid"})
            return
        try:
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict) or set(body) != {"action"}:
                raise ValueError
            receipt = self.server.broker.submit(body["action"], time.monotonic_ns())
        except (json.JSONDecodeError, TypeError, ValueError):
            self._send(400, {"error": "invalid_command"})
        except CommandUnavailable:
            self._send(503, {"error": "device_unavailable"})
        except RuntimeError:
            self._send(409, {"error": "command_rejected"})
        else:
            self._send(202, asdict(receipt))

    def _pc_request(self, path: str, *, post: bool) -> None:
        self.close_connection = True
        raw = b""
        if post:
            try:
                length = int(self.headers.get("Content-Length", ""))
                if not 0 < length <= MAX_REQUEST or self.headers.get("Transfer-Encoding"):
                    self._send(413, {"error": "body_size_invalid"})
                    return
                # Drain bounded bodies before early rejection: Windows may reset
                # connections closed with unread data and hide the error response.
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValueError
            except (ValueError, OSError):
                self._send(400, {"error": "invalid_pc_request"})
                return
        jobs = self.server.pc_jobs
        if jobs is None:
            self._send(503, {"error": "pc_runtime_disabled"})
            return
        if post:
            origins = {
                f"http://{host}:{port}"
                for host in ("127.0.0.1", "localhost")
                for port in (5173, self.server.server_port)
            }
            if self.headers.get("Origin") not in origins:
                self._send(403, {"error": "local_origin_required"})
                return
        match = re.fullmatch(r"/api/v1/pc/jobs/([0-9a-f]{32})(/cancel)?", path)
        try:
            if path == "/api/v1/pc/active" and not post:
                self._send(200, {"job": jobs.current()})
            elif path == "/api/v1/pc/jobs" and post:
                if self.headers.get_content_type() != "application/json":
                    self._send(415, {"error": "json_required"})
                    return
                self._send(202, jobs.submit(json.loads(raw)))
            elif match and post == bool(match[2]):
                if post and (
                    self.headers.get_content_type() != "application/json" or json.loads(raw) != {}
                ):
                    raise ValueError("empty cancellation object required")
                result = jobs.cancel(match[1]) if post else jobs.get(match[1])
                self._send(200, result)
            else:
                self._send(404, {"error": "not_found"})
        except JobBusy:
            self._send(409, {"error": "pc_worker_busy"})
        except KeyError:
            self._send(404, {"error": "job_not_found"})
        except (ValueError, TypeError, OSError):
            self._send(400, {"error": "invalid_pc_request"})


def create_server(
    store: DashboardStore,
    broker: CommandBroker,
    bind: str = "127.0.0.1",
    port: int = 8765,
    *,
    pc_jobs: PcJobs | None = None,
) -> LocalApiServer:
    try:
        if not ipaddress.ip_address(bind).is_loopback:
            raise ValueError("dashboard API must bind to a numeric loopback address")
    except ValueError as exc:
        if str(exc).startswith("dashboard"):
            raise
        raise ValueError("dashboard API must bind to a numeric loopback address") from exc
    if not 0 <= port <= 65535:
        raise ValueError("invalid port")
    return LocalApiServer((bind, port), store, broker, pc_jobs)
