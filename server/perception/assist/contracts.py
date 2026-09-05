"""Provider-independent assist events; none of these events authorizes movement."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal


def bounded_text(value: object, name: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be text")
    if (
        not value
        or value != value.strip()
        or len(value) > maximum
        or any(not char.isprintable() for char in value)
    ):
        raise ValueError(f"invalid {name}")
    return value


@dataclass(frozen=True)
class EventStamp:
    session_id: int
    correlation_id: str
    created_ns: int
    expires_ns: int
    source: Literal["live", "replay", "synthetic", "external"]

    def __post_init__(self):
        if not 0 < self.session_id < 2**64:
            raise ValueError("invalid event session")
        bounded_text(self.correlation_id, "correlation id", 80)
        if self.created_ns < 0 or self.expires_ns <= self.created_ns:
            raise ValueError("invalid event lifetime")
        if self.source not in {"live", "replay", "synthetic", "external"}:
            raise ValueError("invalid event source")

    def active(self, now_ns: int, session_id: int) -> bool:
        return session_id == self.session_id and self.created_ns <= now_ns < self.expires_ns


@dataclass(frozen=True)
class TrafficSignalEvent:
    stamp: EventStamp
    state: Literal["red", "green", "unknown"]
    direction_known: bool
    confidence: float
    model_id: str

    def __post_init__(self):
        if not isinstance(self.state, str) or self.state not in {"red", "green", "unknown"}:
            raise ValueError("invalid signal state")
        if type(self.direction_known) is not bool:
            raise ValueError("invalid direction state")
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
            raise ValueError("invalid signal confidence")
        if not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1:
            raise ValueError("invalid signal confidence")
        bounded_text(self.model_id, "model id", 120)

    def spoken_text(self) -> str:
        if not self.direction_known:
            return "检测到信号灯，但方向无法确认；请勿据此过街"
        labels = {"red": "红灯", "green": "绿灯", "unknown": "信号状态无法确认"}
        return f"检测到{labels[self.state]}；这不是过街许可，请结合现场安全判断"


@dataclass(frozen=True)
class MapInstructionEvent:
    stamp: EventStamp
    route_id: str
    maneuver: Literal["straight", "left", "right", "arrive", "reroute", "unknown"]
    distance_m: int | None
    instruction: str
    provider_id: str

    def __post_init__(self):
        if not isinstance(self.maneuver, str) or self.maneuver not in {
            "straight",
            "left",
            "right",
            "arrive",
            "reroute",
            "unknown",
        }:
            raise ValueError("invalid map maneuver")
        bounded_text(self.route_id, "route id", 120)
        bounded_text(self.instruction, "map instruction", 300)
        bounded_text(self.provider_id, "map provider", 120)
        if self.distance_m is not None and (
            isinstance(self.distance_m, bool)
            or not isinstance(self.distance_m, int)
            or not 0 <= self.distance_m <= 100_000
        ):
            raise ValueError("invalid map distance")


@dataclass(frozen=True)
class OcrLine:
    order: int
    text: str
    confidence: float

    def __post_init__(self):
        if isinstance(self.order, bool) or not isinstance(self.order, int) or self.order < 0:
            raise ValueError("invalid OCR order")
        bounded_text(self.text, "OCR text", 400)
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
            raise ValueError("invalid OCR confidence")
        if not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1:
            raise ValueError("invalid OCR confidence")


@dataclass(frozen=True)
class OcrEvent:
    stamp: EventStamp
    lines: tuple[OcrLine, ...]
    language: str
    model_id: str

    def __post_init__(self):
        if not 0 < len(self.lines) <= 64 or len({line.order for line in self.lines}) != len(
            self.lines
        ):
            raise ValueError("bounded unique OCR lines required")
        if tuple(sorted(self.lines, key=lambda line: line.order)) != self.lines:
            raise ValueError("OCR lines must retain reading order")
        if sum(len(line.text) for line in self.lines) > 8000:
            raise ValueError("OCR result too large")
        bounded_text(self.language, "OCR language", 32)
        bounded_text(self.model_id, "model id", 120)

    @property
    def original_text(self) -> str:
        return "\n".join(line.text for line in self.lines)


@dataclass(frozen=True)
class DialogueEvent:
    stamp: EventStamp
    text: str
    provider_id: str
    model_id: str

    def __post_init__(self):
        bounded_text(self.text, "dialogue text", 2000)
        bounded_text(self.provider_id, "dialogue provider", 120)
        bounded_text(self.model_id, "model id", 120)


def parse_signal_response(response: object, stamp: EventStamp, model_id: str) -> TrafficSignalEvent:
    required = {
        "schema",
        "session_id",
        "correlation_id",
        "model_id",
        "state",
        "direction_known",
        "confidence",
    }
    if not isinstance(response, dict) or set(response) != required:
        raise ValueError("unexpected signal response")
    if (
        response["schema"] != "xg.signal.response.v1"
        or response["session_id"] != str(stamp.session_id)
        or response["correlation_id"] != stamp.correlation_id
        or response["model_id"] != model_id
    ):
        raise ValueError("signal response provenance mismatch")
    return TrafficSignalEvent(
        stamp, response["state"], response["direction_known"], response["confidence"], model_id
    )


def parse_ocr_response(response: object, stamp: EventStamp, model_id: str) -> OcrEvent:
    required = {"schema", "session_id", "correlation_id", "model_id", "language", "lines"}
    if not isinstance(response, dict) or set(response) != required:
        raise ValueError("unexpected OCR response")
    if (
        response["schema"] != "xg.ocr.response.v1"
        or response["session_id"] != str(stamp.session_id)
        or response["correlation_id"] != stamp.correlation_id
        or response["model_id"] != model_id
        or not isinstance(response["lines"], list)
    ):
        raise ValueError("OCR response provenance mismatch")
    lines = []
    for item in response["lines"]:
        if not isinstance(item, dict) or set(item) != {"order", "text", "confidence"}:
            raise ValueError("invalid OCR line fields")
        lines.append(OcrLine(item["order"], item["text"], item["confidence"]))
    return OcrEvent(stamp, tuple(lines), response["language"], model_id)


def parse_map_event(message: object, stamp: EventStamp, provider_id: str) -> MapInstructionEvent:
    required = {
        "schema",
        "session_id",
        "correlation_id",
        "provider_id",
        "route_id",
        "maneuver",
        "distance_m",
        "instruction",
    }
    if not isinstance(message, dict) or set(message) != required:
        raise ValueError("unexpected map event")
    if (
        message["schema"] != "xg.map.event.v1"
        or message["session_id"] != str(stamp.session_id)
        or message["correlation_id"] != stamp.correlation_id
        or message["provider_id"] != provider_id
    ):
        raise ValueError("map event provenance mismatch")
    return MapInstructionEvent(
        stamp,
        message["route_id"],
        message["maneuver"],
        message["distance_m"],
        message["instruction"],
        provider_id,
    )


def parse_dialogue_response(
    response: object, stamp: EventStamp, provider_id: str, model_id: str
) -> DialogueEvent:
    required = {"schema", "session_id", "correlation_id", "provider_id", "model_id", "text"}
    if not isinstance(response, dict) or set(response) != required:
        raise ValueError("unexpected dialogue response")
    if (
        response["schema"] != "xg.dialogue.response.v1"
        or response["session_id"] != str(stamp.session_id)
        or response["correlation_id"] != stamp.correlation_id
        or response["provider_id"] != provider_id
        or response["model_id"] != model_id
    ):
        raise ValueError("dialogue response provenance mismatch")
    return DialogueEvent(stamp, response["text"], provider_id, model_id)
