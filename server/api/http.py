"""Minimal loopback HTTP transport for the Phase 2B dashboard."""

from __future__ import annotations

import ipaddress
import json
import time
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from server.api.state import CommandBroker, CommandUnavailable, DashboardStore

MAX_BODY = 1024


class LocalApiServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store: DashboardStore, broker: CommandBroker):
        super().__init__(address, LocalApiHandler)
        self.store = store
        self.broker = broker


class LocalApiHandler(BaseHTTPRequestHandler):
    server: LocalApiServer
    protocol_version = "HTTP/1.1"

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
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self):  # noqa: N802
        if not self._local_host():
            self._send(421, {"error": "local_host_required"})
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


def create_server(
    store: DashboardStore,
    broker: CommandBroker,
    bind: str = "127.0.0.1",
    port: int = 8765,
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
    return LocalApiServer((bind, port), store, broker)
