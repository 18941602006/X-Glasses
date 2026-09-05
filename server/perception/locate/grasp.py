"""Conservative hand/target/ToF guidance; completion always needs explicit user confirmation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from server.common.geometry import NormalizedRect
from server.perception.locate.contracts import LocateResult
from server.perception.navigation.contracts import FusionProfile, TimedTof


@dataclass(frozen=True)
class HandObservation:
    session_id: int
    frame_id: int
    hand_id: str
    box: NormalizedRect
    capture_ns: int
    uncertainty_ns: int
    received_ns: int
    quality: float
    calibration_id: str
    occluded: bool = False

    def __post_init__(self):
        if not 0 < self.session_id < 2**64 or not 0 <= self.frame_id < 2**32:
            raise ValueError("invalid hand identity")
        if not self.hand_id or not self.calibration_id:
            raise ValueError("hand provenance required")
        if type(self.occluded) is not bool:
            raise ValueError("invalid hand occlusion state")
        if min(self.capture_ns, self.uncertainty_ns, self.received_ns) < 0:
            raise ValueError("invalid hand timing")
        if not math.isfinite(self.quality) or not 0 <= self.quality <= 1:
            raise ValueError("invalid hand quality")


@dataclass(frozen=True)
class GraspConfig:
    config_id: str
    sample_ttl_ns: int
    sync_budget_ns: int
    event_ttl_ns: int
    minimum_object_score: float
    minimum_hand_quality: float
    axis_deadband: float
    depth_deadband_mm: int
    overlap_iou_for_confirmation: float

    def __post_init__(self):
        if (
            not self.config_id
            or min(self.sample_ttl_ns, self.sync_budget_ns, self.event_ttl_ns) <= 0
        ):
            raise ValueError("invalid grasp config identity/timing")
        ratios = (
            self.minimum_object_score,
            self.minimum_hand_quality,
            self.axis_deadband,
            self.overlap_iou_for_confirmation,
        )
        if not all(math.isfinite(value) and 0 < value < 1 for value in ratios):
            raise ValueError("invalid grasp ratio")
        if not 0 < self.depth_deadband_mm < 65535:
            raise ValueError("invalid grasp depth deadband")


@dataclass(frozen=True)
class GraspGuide:
    verdict: Literal["unknown", "guide", "confirm"]
    reason: str
    horizontal: Literal["left", "aligned", "right", "unknown"]
    vertical: Literal["up", "aligned", "down", "unknown"]
    depth: Literal["forward", "aligned", "back", "unknown"]
    requires_user_confirmation: bool
    created_ns: int
    expires_ns: int
    session_id: int
    frame_id: int
    object_id: str
    hand_id: str
    target_distance_mm: int | None
    hand_distance_mm: int | None
    source: str


def _unknown(reason, now, result, object_id, hand, config):
    return GraspGuide(
        "unknown",
        reason,
        "unknown",
        "unknown",
        "unknown",
        False,
        now,
        now + config.event_ttl_ns,
        result.session_id,
        result.frame_id,
        object_id,
        hand.hand_id,
        None,
        None,
        result.source,
    )


def _zone_at(point, tof: TimedTof, profile: FusionProfile):
    x, y = point
    matches = [
        zone
        for zone, rectangle in zip(tof.sample.zones, profile.zone_projections, strict=True)
        if rectangle.left <= x < rectangle.right and rectangle.top <= y < rectangle.bottom
    ]
    if not matches and x == 1 and y == 1:
        matches = [tof.sample.zones[-1]]
    return matches[0] if len(matches) == 1 else None


def evaluate_grasp(
    result: LocateResult,
    object_id: str,
    hand: HandObservation,
    tof: TimedTof,
    profile: FusionProfile,
    config: GraspConfig,
    now_ns: int,
) -> GraspGuide:
    target = next((item for item in result.objects if item.object_id == object_id), None)
    if target is None:
        return _unknown("target_not_found", now_ns, result, object_id, hand, config)
    if result.session_id != hand.session_id or result.session_id != tof.session_id:
        return _unknown("session_mismatch", now_ns, result, object_id, hand, config)
    if result.frame_id != hand.frame_id:
        return _unknown("frame_mismatch", now_ns, result, object_id, hand, config)
    if not (
        result.calibration_id == hand.calibration_id == tof.calibration_id == profile.profile_id
    ):
        return _unknown("calibration_mismatch", now_ns, result, object_id, hand, config)
    if (tof.sample.rows, tof.sample.columns) != (profile.rows, profile.columns):
        return _unknown("tof_shape_mismatch", now_ns, result, object_id, hand, config)
    if target.score < config.minimum_object_score or hand.quality < config.minimum_hand_quality:
        return _unknown("observation_quality_low", now_ns, result, object_id, hand, config)
    samples = (
        (result.capture_ns, result.uncertainty_ns, result.received_ns),
        (hand.capture_ns, hand.uncertainty_ns, hand.received_ns),
        (tof.capture_ns, tof.uncertainty_ns, tof.received_ns),
    )
    for capture, uncertainty, received in samples:
        if capture > now_ns + uncertainty or received > now_ns:
            return _unknown("future_sample", now_ns, result, object_id, hand, config)
        if (
            now_ns - capture + uncertainty >= config.sample_ttl_ns
            or now_ns - received >= config.sample_ttl_ns
        ):
            return _unknown("sample_expired", now_ns, result, object_id, hand, config)
    captures = [sample[0] for sample in samples]
    uncertainties = sum(sample[1] for sample in samples)
    if max(captures) - min(captures) + uncertainties > config.sync_budget_ns:
        return _unknown("samples_not_synchronized", now_ns, result, object_id, hand, config)
    if hand.occluded:
        return _unknown("hand_occluded", now_ns, result, object_id, hand, config)

    hand_center, target_center = hand.box.center, target.box.center
    if target.box.iou(hand.box) >= config.overlap_iou_for_confirmation or target.box.contains(
        hand_center
    ):
        return GraspGuide(
            "confirm",
            "hand_target_overlap_requires_confirmation",
            "aligned",
            "aligned",
            "unknown",
            True,
            now_ns,
            now_ns + config.event_ttl_ns,
            result.session_id,
            result.frame_id,
            object_id,
            hand.hand_id,
            None,
            None,
            result.source,
        )

    dx, dy = target_center[0] - hand_center[0], target_center[1] - hand_center[1]
    horizontal = "aligned" if abs(dx) <= config.axis_deadband else "right" if dx > 0 else "left"
    vertical = "aligned" if abs(dy) <= config.axis_deadband else "down" if dy > 0 else "up"
    target_zone, hand_zone = (
        _zone_at(target_center, tof, profile),
        _zone_at(hand_center, tof, profile),
    )
    target_distance = target_zone.distance_mm if target_zone else None
    hand_distance = hand_zone.distance_mm if hand_zone else None
    same_zone = target_zone is not None and target_zone is hand_zone
    depth = "unknown"
    reason = "depth_unavailable"
    if not same_zone and target_distance is not None and hand_distance is not None:
        delta = target_distance - hand_distance
        depth = (
            "aligned"
            if abs(delta) <= config.depth_deadband_mm
            else "forward"
            if delta > 0
            else "back"
        )
        reason = "bounded_guidance"
    elif same_zone:
        reason = "same_tof_zone_depth_unknown"
    return GraspGuide(
        "guide",
        reason,
        horizontal,
        vertical,
        depth,
        False,
        now_ns,
        now_ns + config.event_ttl_ns,
        result.session_id,
        result.frame_id,
        object_id,
        hand.hand_id,
        target_distance,
        hand_distance,
        result.source,
    )


class ConfirmationGate:
    def __init__(self):
        self._armed: GraspGuide | None = None

    def arm(self, guide: GraspGuide) -> None:
        self._armed = guide if guide.verdict == "confirm" else None

    def confirm(self, source: str, now_ns: int) -> bool:
        guide = self._armed
        self._armed = None
        return bool(
            guide
            and source in {"button", "voice"}
            and guide.created_ns <= now_ns < guide.expires_ns
            and guide.requires_user_confirmation
        )
