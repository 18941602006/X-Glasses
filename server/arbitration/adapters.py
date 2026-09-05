"""Explicit conversion from perception/assist events into bounded output candidates."""

from __future__ import annotations

from server.arbitration.core import OutputCandidate
from server.perception.assist.contracts import (
    DialogueEvent,
    EventStamp,
    MapInstructionEvent,
    OcrEvent,
    TrafficSignalEvent,
)
from server.perception.locate.grasp import GraspGuide
from server.perception.navigation.contracts import NavigationEvent


def from_navigation(event: NavigationEvent) -> OutputCandidate:
    stamp = EventStamp(
        event.session_id,
        f"navigation-{event.frame_id}-{event.tof_sample_id}",
        event.created_ns,
        event.expires_ns,
        event.source,
    )
    if event.verdict == "unknown":
        return OutputCandidate(
            stamp, "sensor_failure", "环境感知暂不可用，请停止并使用盲杖确认", "warning"
        )
    if event.verdict == "stop":
        return OutputCandidate(stamp, "emergency", "前方风险，请停止", "warning")
    messages = {
        "left": ("候选方向向左，请缓慢探路", "left"),
        "right": ("候选方向向右，请缓慢探路", "right"),
        "forward": ("前方为短时行进候选，请继续使用盲杖确认", "none"),
    }
    if event.direction not in messages:
        raise ValueError("navigation candidate has no usable direction")
    message, cue = messages[event.direction]
    return OutputCandidate(stamp, "local_direction", message, cue)


def from_grasp(event: GraspGuide) -> OutputCandidate:
    stamp = EventStamp(
        event.session_id,
        f"grasp-{event.frame_id}-{event.object_id}",
        event.created_ns,
        event.expires_ns,
        event.source,
    )
    if event.verdict == "unknown":
        return OutputCandidate(stamp, "locate", "拿取引导暂不可用，请重新定位目标")
    if event.verdict == "confirm":
        return OutputCandidate(stamp, "locate", "手已接近目标，请按键或语音确认拿到", "confirm")
    axes = {
        "left": "向左",
        "right": "向右",
        "up": "向上",
        "down": "向下",
        "forward": "向前",
        "back": "向后",
    }
    parts = [
        axes[value] for value in (event.horizontal, event.vertical, event.depth) if value in axes
    ]
    message = "，".join(parts) if parts else "方向已对齐，请缓慢接近"
    if event.depth == "unknown":
        message += "；前后距离无法确认"
    return OutputCandidate(stamp, "locate", message)


def from_signal(event: TrafficSignalEvent) -> OutputCandidate:
    cue = "warning" if event.state in {"red", "unknown"} or not event.direction_known else "none"
    return OutputCandidate(event.stamp, "traffic_signal", event.spoken_text(), cue)


def from_map(event: MapInstructionEvent) -> OutputCandidate:
    cue = "left" if event.maneuver == "left" else "right" if event.maneuver == "right" else "none"
    return OutputCandidate(event.stamp, "map", event.instruction, cue)


def from_ocr(event: OcrEvent) -> OutputCandidate:
    if len(event.original_text) > 500:
        raise ValueError("OCR text must be chunked before output arbitration")
    return OutputCandidate(event.stamp, "reading", event.original_text)


def from_dialogue(event: DialogueEvent) -> OutputCandidate:
    if len(event.text) > 500:
        raise ValueError("dialogue text must be chunked before output arbitration")
    return OutputCandidate(event.stamp, "dialogue", event.text)
