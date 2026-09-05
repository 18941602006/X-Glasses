import unittest

from server.common.sensors import TofSample, TofZone
from server.perception.navigation.contracts import (
    FusionProfile,
    NavigationConfig,
    NormalizedRect,
    TimedTof,
    WalkableMask,
)
from server.perception.navigation.fusion import evaluate_navigation


def profile(profile_id="cal-1"):
    boxes = []
    for row in range(4):
        for column in range(4):
            boxes.append(NormalizedRect(column / 4, row / 4, (column + 1) / 4, (row + 1) / 4))
    return FusionProfile(profile_id, 4, 4, tuple(boxes))


def config():
    return NavigationConfig(
        "synthetic-config",
        frame_ttl_ns=500_000_000,
        sync_budget_ns=80_000_000,
        event_ttl_ns=250_000_000,
        obstacle_mm=1200,
        emergency_mm=450,
        minimum_tof_valid_ratio=0.75,
        minimum_walkable_coverage=0.6,
        minimum_segmentation_quality=0.7,
        roi_top=0.5,
    )


def mask(now=1_000_000_000, values=None, calibration="cal-1", quality=0.9, session=7):
    width, height = 12, 8
    return WalkableMask(
        session,
        11,
        width,
        height,
        tuple(values if values is not None else [True] * 96),
        now - 20_000_000,
        2_000_000,
        now - 10_000_000,
        "synthetic-mask",
        quality,
        calibration,
        "synthetic",
    )


def tof(now=1_000_000_000, distances=None, calibration="cal-1", session=7):
    distances = distances if distances is not None else [2000] * 16
    zones = tuple(TofZone(value, 0 if value is not None else 255) for value in distances)
    return TimedTof(
        session,
        TofSample(22, 4, 4, zones),
        now - 18_000_000,
        2_000_000,
        now - 8_000_000,
        calibration,
    )


class NavigationCoreTests(unittest.TestCase):
    def test_forward_candidate_is_explicitly_not_safe(self):
        event = evaluate_navigation(mask(), tof(), profile(), config(), 1_000_000_000)
        self.assertEqual(
            (event.verdict, event.direction, event.reason),
            ("candidate", "forward", "candidate_corridor"),
        )
        self.assertEqual(event.source, "synthetic")
        self.assertEqual(event.expires_ns, 1_250_000_000)

    def test_center_obstacle_selects_unblocked_side(self):
        distances = [2000] * 16
        distances[13] = 800
        event = evaluate_navigation(
            mask(), tof(distances=distances), profile(), config(), 1_000_000_000
        )
        self.assertEqual((event.verdict, event.direction), ("candidate", "right"))
        self.assertEqual(event.nearest_obstacle_mm, 800)

    def test_emergency_center_obstacle_stops(self):
        distances = [2000] * 16
        distances[14] = 300
        event = evaluate_navigation(
            mask(), tof(distances=distances), profile(), config(), 1_000_000_000
        )
        self.assertEqual((event.verdict, event.direction), ("stop", "none"))
        self.assertEqual(event.reason, "emergency_center_obstacle")

    def test_unknown_tof_never_means_clear(self):
        event = evaluate_navigation(
            mask(), tof(distances=[None] * 16), profile(), config(), 1_000_000_000
        )
        self.assertEqual((event.verdict, event.reason), ("unknown", "tof_validity_low"))

    def test_local_center_tof_unknown_never_selects_forward(self):
        distances = [2000] * 16
        distances[13] = None
        distances[14] = None
        event = evaluate_navigation(
            mask(), tof(distances=distances), profile(), config(), 1_000_000_000
        )
        self.assertEqual(event.verdict, "candidate")
        self.assertIn(event.direction, {"left", "right"})

    def test_missing_walkable_corridor_stops(self):
        event = evaluate_navigation(
            mask(values=[False] * 96), tof(), profile(), config(), 1_000_000_000
        )
        self.assertEqual((event.verdict, event.reason), ("stop", "walkable_corridor_missing"))

    def test_calibration_session_and_quality_gates(self):
        now = 1_000_000_000
        cases = [
            (mask(calibration="other"), tof(), "calibration_mismatch"),
            (mask(session=8), tof(), "session_mismatch"),
            (mask(quality=0.2), tof(), "segmentation_quality_low"),
        ]
        for image, depth, reason in cases:
            with self.subTest(reason=reason):
                self.assertEqual(
                    evaluate_navigation(image, depth, profile(), config(), now).reason, reason
                )

    def test_expired_future_and_unsynchronized_gate(self):
        now = 1_000_000_000
        old_mask = mask(now=400_000_000)
        future_tof = tof(now=1_100_000_000)
        future_receive = TimedTof(7, tof().sample, 980_000_000, 2_000_000, 1_000_000_001, "cal-1")
        unsynced_tof = TimedTof(7, tof().sample, 800_000_000, 2_000_000, 990_000_000, "cal-1")
        self.assertEqual(
            evaluate_navigation(old_mask, tof(), profile(), config(), now).reason,
            "sample_expired",
        )
        self.assertEqual(
            evaluate_navigation(mask(), future_tof, profile(), config(), now).reason,
            "future_sample",
        )
        self.assertEqual(
            evaluate_navigation(mask(), future_receive, profile(), config(), now).reason,
            "future_receive",
        )
        self.assertEqual(
            evaluate_navigation(mask(), unsynced_tof, profile(), config(), now).reason,
            "samples_not_synchronized",
        )

    def test_contract_rejects_bad_dimensions_thresholds_and_projection(self):
        with self.assertRaises(ValueError):
            NormalizedRect(0, 0, 2, 1)
        with self.assertRaises(ValueError):
            WalkableMask(1, 1, 3, 3, (True,), 0, 0, 0, "m", 1, "c", "synthetic")
        with self.assertRaises(ValueError):
            NavigationConfig("x", 1, 1, 1, 100, 200, 0.5, 0.5, 0.5, 0.5)


if __name__ == "__main__":
    unittest.main()
