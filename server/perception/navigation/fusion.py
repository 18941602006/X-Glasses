"""Conservative candidate-corridor selection; never a crossing or safety permission."""

from __future__ import annotations

from server.perception.navigation.contracts import (
    FusionProfile,
    NavigationConfig,
    NavigationEvent,
    TimedTof,
    WalkableMask,
)

LANES = ((0.0, 1 / 3), (1 / 3, 2 / 3), (2 / 3, 1.0))


def _coverage(mask: WalkableMask, left: float, right: float, roi_top: float) -> float:
    x0 = max(0, int(mask.width * left))
    x1 = min(mask.width, max(x0 + 1, int(mask.width * right)))
    y0 = min(mask.height - 1, max(0, int(mask.height * roi_top)))
    total = (x1 - x0) * (mask.height - y0)
    walkable = sum(
        mask.values[y * mask.width + x] for y in range(y0, mask.height) for x in range(x0, x1)
    )
    return walkable / total


def _event(
    verdict,
    direction,
    reason,
    now_ns,
    mask,
    tof,
    profile,
    config,
    coverage=(0.0, 0.0, 0.0),
    nearest=None,
):
    return NavigationEvent(
        verdict=verdict,
        direction=direction,
        reason=reason,
        created_ns=now_ns,
        expires_ns=now_ns + config.event_ttl_ns,
        session_id=mask.session_id,
        frame_id=mask.frame_id,
        tof_sample_id=tof.sample.sample_id,
        profile_id=profile.profile_id,
        config_id=config.config_id,
        lane_coverage=coverage,
        nearest_obstacle_mm=nearest,
        source=mask.source,
    )


def evaluate_navigation(
    mask: WalkableMask,
    tof: TimedTof,
    profile: FusionProfile,
    config: NavigationConfig,
    now_ns: int,
) -> NavigationEvent:
    if now_ns < 0:
        raise ValueError("monotonic time must be nonnegative")
    if mask.session_id != tof.session_id:
        return _event("unknown", "none", "session_mismatch", now_ns, mask, tof, profile, config)
    if mask.calibration_id != profile.profile_id or tof.calibration_id != profile.profile_id:
        return _event("unknown", "none", "calibration_mismatch", now_ns, mask, tof, profile, config)
    if (tof.sample.rows, tof.sample.columns) != (profile.rows, profile.columns):
        return _event("unknown", "none", "tof_shape_mismatch", now_ns, mask, tof, profile, config)
    if mask.quality < config.minimum_segmentation_quality:
        return _event(
            "unknown", "none", "segmentation_quality_low", now_ns, mask, tof, profile, config
        )
    for capture_ns, uncertainty_ns, received_ns in (
        (mask.capture_ns, mask.uncertainty_ns, mask.received_ns),
        (tof.capture_ns, tof.uncertainty_ns, tof.received_ns),
    ):
        if capture_ns > now_ns + uncertainty_ns:
            return _event("unknown", "none", "future_sample", now_ns, mask, tof, profile, config)
        if received_ns > now_ns:
            return _event("unknown", "none", "future_receive", now_ns, mask, tof, profile, config)
        if now_ns - capture_ns + uncertainty_ns >= config.frame_ttl_ns:
            return _event("unknown", "none", "sample_expired", now_ns, mask, tof, profile, config)
        if now_ns - received_ns >= config.frame_ttl_ns:
            return _event("unknown", "none", "transport_stale", now_ns, mask, tof, profile, config)
    if (
        abs(mask.capture_ns - tof.capture_ns) + mask.uncertainty_ns + tof.uncertainty_ns
        > config.sync_budget_ns
    ):
        return _event(
            "unknown", "none", "samples_not_synchronized", now_ns, mask, tof, profile, config
        )

    coverage = tuple(_coverage(mask, left, right, config.roi_top) for left, right in LANES)
    valid = [zone for zone in tof.sample.zones if zone.distance_mm is not None]
    if len(valid) / len(tof.sample.zones) < config.minimum_tof_valid_ratio:
        return _event(
            "unknown", "none", "tof_validity_low", now_ns, mask, tof, profile, config, coverage
        )

    blocked = [False, False, False]
    lane_zone_total = [0, 0, 0]
    lane_zone_valid = [0, 0, 0]
    nearest = None
    emergency_center = False
    for zone, projection in zip(tof.sample.zones, profile.zone_projections, strict=True):
        distance = zone.distance_mm
        if not projection.overlaps(0, config.roi_top, 1, 1):
            continue
        for lane_index, (left, right) in enumerate(LANES):
            if projection.overlaps(left, config.roi_top, right, 1):
                lane_zone_total[lane_index] += 1
                if distance is not None:
                    lane_zone_valid[lane_index] += 1
        if distance is None:
            continue
        if nearest is None or distance < nearest:
            nearest = distance
        if distance < config.obstacle_mm:
            for lane_index, (left, right) in enumerate(LANES):
                if projection.overlaps(left, config.roi_top, right, 1):
                    blocked[lane_index] = True
                    if lane_index == 1 and distance < config.emergency_mm:
                        emergency_center = True

    if emergency_center:
        return _event(
            "stop",
            "none",
            "emergency_center_obstacle",
            now_ns,
            mask,
            tof,
            profile,
            config,
            coverage,
            nearest,
        )

    eligible = [
        lane
        for lane in range(3)
        if not blocked[lane]
        and coverage[lane] >= config.minimum_walkable_coverage
        and lane_zone_total[lane] > 0
        and lane_zone_valid[lane] / lane_zone_total[lane] >= config.minimum_tof_valid_ratio
    ]
    if not eligible:
        lane_unknown = any(
            total and valid / total < config.minimum_tof_valid_ratio
            for valid, total in zip(lane_zone_valid, lane_zone_total, strict=True)
        )
        reason = (
            "obstacles_block_corridors"
            if any(blocked)
            else "tof_corridors_unknown"
            if lane_unknown
            else "walkable_corridor_missing"
        )
        return _event("stop", "none", reason, now_ns, mask, tof, profile, config, coverage, nearest)

    # Prefer center, then the highest-coverage side. This is a short-lived candidate, not permission.
    if 1 in eligible:
        selected = 1
    else:
        selected = max(eligible, key=lambda lane: (coverage[lane], -lane))
    direction = ("left", "forward", "right")[selected]
    return _event(
        "candidate",
        direction,
        "candidate_corridor",
        now_ns,
        mask,
        tof,
        profile,
        config,
        coverage,
        nearest,
    )
