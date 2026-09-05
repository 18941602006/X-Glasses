"""Model-independent, time-bound contracts for walkable-area and ToF fusion."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Protocol

from server.common.geometry import NormalizedRect
from server.common.sensors import TofSample

Direction = Literal["none", "left", "forward", "right"]
Verdict = Literal["unknown", "stop", "candidate"]


@dataclass(frozen=True)
class WalkableMask:
    session_id: int
    frame_id: int
    width: int
    height: int
    values: tuple[bool, ...]
    capture_ns: int
    uncertainty_ns: int
    received_ns: int
    model_id: str
    quality: float
    calibration_id: str
    source: Literal["live", "replay", "synthetic"]

    def __post_init__(self):
        if not 0 < self.session_id < 2**64 or not 0 <= self.frame_id < 2**32:
            raise ValueError("invalid mask identity")
        if self.width < 3 or self.height < 3 or len(self.values) != self.width * self.height:
            raise ValueError("invalid mask dimensions")
        if min(self.capture_ns, self.uncertainty_ns, self.received_ns) < 0:
            raise ValueError("invalid mask timing")
        if not self.model_id or not self.calibration_id or not math.isfinite(self.quality):
            raise ValueError("mask provenance is required")
        if not 0 <= self.quality <= 1:
            raise ValueError("mask quality outside [0,1]")
        if self.source not in {"live", "replay", "synthetic"}:
            raise ValueError("invalid mask source")


@dataclass(frozen=True)
class TimedTof:
    session_id: int
    sample: TofSample
    capture_ns: int
    uncertainty_ns: int
    received_ns: int
    calibration_id: str

    def __post_init__(self):
        if not 0 < self.session_id < 2**64:
            raise ValueError("invalid ToF session")
        if min(self.capture_ns, self.uncertainty_ns, self.received_ns) < 0:
            raise ValueError("invalid ToF timing")
        if not self.calibration_id:
            raise ValueError("ToF calibration id required")


@dataclass(frozen=True)
class FusionProfile:
    profile_id: str
    rows: int
    columns: int
    zone_projections: tuple[NormalizedRect, ...]

    def __post_init__(self):
        if not self.profile_id or (self.rows, self.columns) not in {(4, 4), (8, 8)}:
            raise ValueError("invalid fusion profile")
        if len(self.zone_projections) != self.rows * self.columns:
            raise ValueError("projection count mismatch")


@dataclass(frozen=True)
class NavigationConfig:
    config_id: str
    frame_ttl_ns: int
    sync_budget_ns: int
    event_ttl_ns: int
    obstacle_mm: int
    emergency_mm: int
    minimum_tof_valid_ratio: float
    minimum_walkable_coverage: float
    minimum_segmentation_quality: float
    roi_top: float

    def __post_init__(self):
        if not self.config_id:
            raise ValueError("config id required")
        if min(self.frame_ttl_ns, self.sync_budget_ns, self.event_ttl_ns) <= 0:
            raise ValueError("timing thresholds must be positive")
        if not 0 < self.emergency_mm < self.obstacle_mm < 65535:
            raise ValueError("distance thresholds must be ordered")
        ratios = (
            self.minimum_tof_valid_ratio,
            self.minimum_walkable_coverage,
            self.minimum_segmentation_quality,
            self.roi_top,
        )
        if not all(math.isfinite(value) and 0 < value < 1 for value in ratios):
            raise ValueError("ratio thresholds must be inside (0,1)")


@dataclass(frozen=True)
class NavigationEvent:
    verdict: Verdict
    direction: Direction
    reason: str
    created_ns: int
    expires_ns: int
    session_id: int
    frame_id: int
    tof_sample_id: int
    profile_id: str
    config_id: str
    lane_coverage: tuple[float, float, float]
    nearest_obstacle_mm: int | None
    source: str


class SegmentationAdapter(Protocol):
    """A real model adapter may only produce the validated mask contract."""

    model_id: str

    def segment(self, jpeg: bytes, *, session_id: int, frame_id: int) -> WalkableMask: ...
