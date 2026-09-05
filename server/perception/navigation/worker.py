"""Bounded adapter for an isolated segmentation process; contains no model runtime."""

from __future__ import annotations

import base64
import math
from dataclasses import dataclass
from typing import Protocol

from server.perception.navigation.contracts import WalkableMask

MAX_JPEG = 256 * 1024
MAX_MASK_PIXELS = 1920 * 1080


class WorkerFailure(RuntimeError):
    pass


class WorkerTransport(Protocol):
    def request(self, message: dict, timeout_ms: int) -> dict: ...


@dataclass(frozen=True)
class FrameRequest:
    session_id: int
    frame_id: int
    capture_ns: int
    uncertainty_ns: int
    received_ns: int
    calibration_id: str
    source: str

    def __post_init__(self):
        if not 0 < self.session_id < 2**64 or not 0 <= self.frame_id < 2**32:
            raise ValueError("invalid frame identity")
        if min(self.capture_ns, self.uncertainty_ns, self.received_ns) < 0:
            raise ValueError("invalid frame timing")
        if not self.calibration_id or self.source not in {"live", "replay", "synthetic"}:
            raise ValueError("invalid frame provenance")


def decode_binary_rle(width: int, height: int, runs: object) -> tuple[bool, ...]:
    if not isinstance(width, int) or not isinstance(height, int) or width < 3 or height < 3:
        raise WorkerFailure("invalid mask dimensions")
    pixels = width * height
    if pixels > MAX_MASK_PIXELS or not isinstance(runs, list) or not runs:
        raise WorkerFailure("mask size or RLE invalid")
    result: list[bool] = []
    if len(runs) > pixels * 2:
        raise WorkerFailure("RLE exceeds pixel bound")
    for run in runs:
        if (
            not isinstance(run, list)
            or len(run) != 2
            or type(run[0]) is not int
            or run[0] not in (0, 1)
            or type(run[1]) is not int
            or not 0 < run[1] <= pixels - len(result)
        ):
            raise WorkerFailure("invalid binary RLE run")
        result.extend([bool(run[0])] * run[1])
    if len(result) != pixels:
        raise WorkerFailure("RLE pixel count mismatch")
    return tuple(result)


class IsolatedSegmentationAdapter:
    """Converts a worker response to WalkableMask without trusting remote metadata."""

    def __init__(self, transport: WorkerTransport, expected_model_id: str, timeout_ms: int = 250):
        if not expected_model_id or not 1 <= timeout_ms <= 2000:
            raise ValueError("bounded model id and timeout required")
        self.transport = transport
        self.model_id = expected_model_id
        self.timeout_ms = timeout_ms

    def segment(self, jpeg: bytes, *, frame: FrameRequest) -> WalkableMask:
        if not isinstance(jpeg, bytes) or not 4 <= len(jpeg) <= MAX_JPEG:
            raise ValueError("bounded JPEG required")
        if not jpeg.startswith(b"\xff\xd8") or not jpeg.endswith(b"\xff\xd9"):
            raise ValueError("JPEG markers required")
        message = {
            "schema": "xg.segment.request.v1",
            "session_id": str(frame.session_id),
            "frame_id": frame.frame_id,
            "jpeg_base64": base64.b64encode(jpeg).decode("ascii"),
        }
        try:
            response = self.transport.request(message, self.timeout_ms)
        except TimeoutError as exc:
            raise WorkerFailure("segmentation worker timeout") from exc
        if not isinstance(response, dict) or set(response) != {
            "schema",
            "session_id",
            "frame_id",
            "model_id",
            "width",
            "height",
            "quality",
            "rle",
        }:
            raise WorkerFailure("unexpected worker response fields")
        if (
            response["schema"] != "xg.segment.response.v1"
            or response["session_id"] != str(frame.session_id)
            or response["frame_id"] != frame.frame_id
            or response["model_id"] != self.model_id
        ):
            raise WorkerFailure("worker provenance mismatch")
        quality = response["quality"]
        if type(quality) not in (int, float) or not math.isfinite(quality):
            raise WorkerFailure("invalid worker quality")
        values = decode_binary_rle(response["width"], response["height"], response["rle"])
        return WalkableMask(
            session_id=frame.session_id,
            frame_id=frame.frame_id,
            width=response["width"],
            height=response["height"],
            values=values,
            capture_ns=frame.capture_ns,
            uncertainty_ns=frame.uncertainty_ns,
            received_ns=frame.received_ns,
            model_id=self.model_id,
            quality=float(quality),
            calibration_id=frame.calibration_id,
            source=frame.source,
        )
