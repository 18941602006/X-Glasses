"""Small normalized geometry primitives shared by perception contracts."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedRect:
    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self):
        values = (self.left, self.top, self.right, self.bottom)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("nonfinite rectangle")
        if not 0 <= self.left < self.right <= 1 or not 0 <= self.top < self.bottom <= 1:
            raise ValueError("rectangle outside normalized image")

    @property
    def area(self) -> float:
        return (self.right - self.left) * (self.bottom - self.top)

    @property
    def center(self) -> tuple[float, float]:
        return ((self.left + self.right) / 2, (self.top + self.bottom) / 2)

    def overlaps(self, left: float, top: float, right: float, bottom: float) -> bool:
        return self.left < right and self.right > left and self.top < bottom and self.bottom > top

    def intersection_area(self, other: "NormalizedRect") -> float:
        width = max(0.0, min(self.right, other.right) - max(self.left, other.left))
        height = max(0.0, min(self.bottom, other.bottom) - max(self.top, other.top))
        return width * height

    def iou(self, other: "NormalizedRect") -> float:
        intersection = self.intersection_area(other)
        union = self.area + other.area - intersection
        return intersection / union if union else 0.0

    def contains(self, point: tuple[float, float]) -> bool:
        return self.left <= point[0] <= self.right and self.top <= point[1] <= self.bottom
