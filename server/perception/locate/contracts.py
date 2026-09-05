"""Bounded LocateAnything result contracts; model loading lives outside the main service."""

from __future__ import annotations

import base64
import math
from dataclasses import dataclass
from typing import Protocol

from server.common.geometry import NormalizedRect

MAX_JPEG = 256 * 1024
MAX_QUERY = 160
MAX_OBJECTS = 16


class LocateFailure(RuntimeError):
    pass


class LocateTransport(Protocol):
    def request(self, message: dict, timeout_ms: int) -> dict: ...


@dataclass(frozen=True)
class LocateFrame:
    session_id: int
    frame_id: int
    capture_ns: int
    uncertainty_ns: int
    received_ns: int
    calibration_id: str
    source: str

    def __post_init__(self):
        if not 0 < self.session_id < 2**64 or not 0 <= self.frame_id < 2**32:
            raise ValueError("invalid locate frame identity")
        if min(self.capture_ns, self.uncertainty_ns, self.received_ns) < 0:
            raise ValueError("invalid locate frame timing")
        if not self.calibration_id or self.source not in {"live", "replay", "synthetic"}:
            raise ValueError("invalid locate frame provenance")


@dataclass(frozen=True)
class LocatedObject:
    object_id: str
    box: NormalizedRect
    score: float

    def __post_init__(self):
        if not isinstance(self.object_id, str) or not self.object_id or len(self.object_id) > 80:
            raise ValueError("invalid object id")
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise ValueError("invalid object score")
        if not math.isfinite(self.score) or not 0 <= self.score <= 1:
            raise ValueError("invalid object score")


@dataclass(frozen=True)
class LocateResult:
    session_id: int
    frame_id: int
    capture_ns: int
    uncertainty_ns: int
    received_ns: int
    calibration_id: str
    source: str
    query: str
    model_id: str
    objects: tuple[LocatedObject, ...]


class LocateAnythingAdapter:
    def __init__(self, transport: LocateTransport, model_id: str, timeout_ms: int = 2000):
        if not model_id or not 100 <= timeout_ms <= 10_000:
            raise ValueError("fixed model id and bounded timeout required")
        self.transport, self.model_id, self.timeout_ms = transport, model_id, timeout_ms

    def locate(self, jpeg: bytes, query: str, frame: LocateFrame) -> LocateResult:
        if not isinstance(jpeg, bytes) or not 4 <= len(jpeg) <= MAX_JPEG:
            raise ValueError("bounded JPEG required")
        if not jpeg.startswith(b"\xff\xd8") or not jpeg.endswith(b"\xff\xd9"):
            raise ValueError("JPEG markers required")
        query = query.strip()
        if not query or len(query) > MAX_QUERY or any(not char.isprintable() for char in query):
            raise ValueError("bounded printable query required")
        request = {
            "schema": "xg.locate.request.v1",
            "session_id": str(frame.session_id),
            "frame_id": frame.frame_id,
            "query": query,
            "jpeg_base64": base64.b64encode(jpeg).decode("ascii"),
        }
        try:
            response = self.transport.request(request, self.timeout_ms)
        except TimeoutError as exc:
            raise LocateFailure("LocateAnything timeout") from exc
        required = {"schema", "session_id", "frame_id", "model_id", "objects"}
        if not isinstance(response, dict) or set(response) != required:
            raise LocateFailure("unexpected LocateAnything response")
        if (
            response["schema"] != "xg.locate.response.v1"
            or response["session_id"] != str(frame.session_id)
            or response["frame_id"] != frame.frame_id
            or response["model_id"] != self.model_id
            or not isinstance(response["objects"], list)
            or len(response["objects"]) > MAX_OBJECTS
        ):
            raise LocateFailure("LocateAnything provenance or object count mismatch")
        objects = []
        seen = set()
        for item in response["objects"]:
            if not isinstance(item, dict) or set(item) != {"object_id", "box", "score"}:
                raise LocateFailure("invalid object fields")
            box = item["box"]
            if not isinstance(box, list) or len(box) != 4:
                raise LocateFailure("invalid object box")
            try:
                obj = LocatedObject(item["object_id"], NormalizedRect(*box), item["score"])
            except (TypeError, ValueError) as exc:
                raise LocateFailure("invalid object value") from exc
            if obj.object_id in seen:
                raise LocateFailure("duplicate object id")
            seen.add(obj.object_id)
            objects.append(obj)
        return LocateResult(
            frame.session_id,
            frame.frame_id,
            frame.capture_ns,
            frame.uncertainty_ns,
            frame.received_ns,
            frame.calibration_id,
            frame.source,
            query,
            self.model_id,
            tuple(objects),
        )
