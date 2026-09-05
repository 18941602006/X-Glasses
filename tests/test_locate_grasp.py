import unittest

from server.common.geometry import NormalizedRect
from server.common.sensors import TofSample, TofZone
from server.perception.locate.contracts import (
    LocateAnythingAdapter,
    LocatedObject,
    LocateFailure,
    LocateFrame,
    LocateResult,
)
from server.perception.locate.grasp import (
    ConfirmationGate,
    GraspConfig,
    HandObservation,
    evaluate_grasp,
)
from server.perception.navigation.contracts import FusionProfile, TimedTof


class Transport:
    def __init__(self, value=None, failure=None):
        self.value, self.failure, self.message = value, failure, None

    def request(self, message, timeout_ms):
        self.message = message
        if self.failure:
            raise self.failure
        return self.value


def worker_response(**changes):
    value = {
        "schema": "xg.locate.response.v1",
        "session_id": "7",
        "frame_id": 3,
        "model_id": "locate@fixed",
        "objects": [{"object_id": "cup-1", "box": [0.65, 0.4, 0.85, 0.7], "score": 0.9}],
    }
    value.update(changes)
    return value


def locate_frame():
    return LocateFrame(7, 3, 970_000_000, 2_000_000, 980_000_000, "cal-1", "synthetic")


def result(box=NormalizedRect(0.65, 0.4, 0.85, 0.7), score=0.9):
    return LocateResult(
        7,
        3,
        970_000_000,
        2_000_000,
        980_000_000,
        "cal-1",
        "synthetic",
        "杯子",
        "locate@fixed",
        (LocatedObject("cup-1", box, score),),
    )


def hand(box=NormalizedRect(0.1, 0.4, 0.3, 0.7), **changes):
    values = dict(
        session_id=7,
        frame_id=3,
        hand_id="right",
        box=box,
        capture_ns=972_000_000,
        uncertainty_ns=2_000_000,
        received_ns=982_000_000,
        quality=0.9,
        calibration_id="cal-1",
    )
    values.update(changes)
    return HandObservation(**values)


def fusion_profile():
    rectangles = tuple(
        NormalizedRect(column / 4, row / 4, (column + 1) / 4, (row + 1) / 4)
        for row in range(4)
        for column in range(4)
    )
    return FusionProfile("cal-1", 4, 4, rectangles)


def depth(distances=None, **changes):
    distances = distances or [1500] * 16
    zones = tuple(TofZone(value, 0 if value is not None else 255) for value in distances)
    values = dict(
        session_id=7,
        sample=TofSample(4, 4, 4, zones),
        capture_ns=974_000_000,
        uncertainty_ns=2_000_000,
        received_ns=984_000_000,
        calibration_id="cal-1",
    )
    values.update(changes)
    return TimedTof(**values)


def config():
    return GraspConfig("synthetic", 400_000_000, 60_000_000, 250_000_000, 0.6, 0.6, 0.05, 100, 0.1)


class LocateContractTests(unittest.TestCase):
    def test_valid_worker_result_retains_host_metadata(self):
        transport = Transport(worker_response())
        located = LocateAnythingAdapter(transport, "locate@fixed").locate(
            b"\xff\xd8x\xff\xd9", " 杯子 ", locate_frame()
        )
        self.assertEqual(
            (located.query, located.capture_ns, located.objects[0].object_id),
            ("杯子", 970_000_000, "cup-1"),
        )
        self.assertEqual(transport.message["session_id"], "7")

    def test_worker_timeout_stale_identity_extra_and_bad_box_rejected(self):
        adapter = LocateAnythingAdapter(Transport(failure=TimeoutError()), "locate@fixed")
        with self.assertRaises(LocateFailure):
            adapter.locate(b"\xff\xd8x\xff\xd9", "cup", locate_frame())
        cases = [
            worker_response(session_id="8"),
            {**worker_response(), "capture_ns": 1},
            worker_response(objects=[{"object_id": "x", "box": [0, 0, 2, 1], "score": 1}]),
        ]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(LocateFailure):
                LocateAnythingAdapter(Transport(value), "locate@fixed").locate(
                    b"\xff\xd8x\xff\xd9", "cup", locate_frame()
                )

    def test_query_jpeg_object_id_and_count_are_bounded(self):
        adapter = LocateAnythingAdapter(Transport(worker_response()), "locate@fixed")
        for jpeg, query in [(b"bad", "cup"), (b"\xff\xd8x\xff\xd9", "\n")]:
            with self.subTest(jpeg=jpeg, query=query), self.assertRaises(ValueError):
                adapter.locate(jpeg, query, locate_frame())
        duplicate = worker_response(objects=[worker_response()["objects"][0]] * 2)
        with self.assertRaises(LocateFailure):
            LocateAnythingAdapter(Transport(duplicate), "locate@fixed").locate(
                b"\xff\xd8x\xff\xd9", "cup", locate_frame()
            )


class GraspFusionTests(unittest.TestCase):
    def test_bounded_three_axis_guidance(self):
        distances = [1500] * 16
        distances[8] = 800
        distances[11] = 1400
        guide = evaluate_grasp(
            result(), "cup-1", hand(), depth(distances), fusion_profile(), config(), 1_000_000_000
        )
        self.assertEqual(
            (guide.verdict, guide.horizontal, guide.vertical), ("guide", "right", "aligned")
        )
        self.assertEqual(guide.depth, "forward")
        self.assertFalse(guide.requires_user_confirmation)

    def test_same_tof_zone_disables_depth(self):
        near_hand = hand(NormalizedRect(0.52, 0.42, 0.62, 0.62))
        target = result(NormalizedRect(0.64, 0.42, 0.74, 0.62))
        guide = evaluate_grasp(
            target, "cup-1", near_hand, depth(), fusion_profile(), config(), 1_000_000_000
        )
        self.assertEqual(
            (guide.verdict, guide.depth, guide.reason),
            ("guide", "unknown", "same_tof_zone_depth_unknown"),
        )

    def test_overlap_only_arms_explicit_single_use_confirmation(self):
        overlapping = hand(NormalizedRect(0.68, 0.45, 0.82, 0.68))
        guide = evaluate_grasp(
            result(), "cup-1", overlapping, depth(), fusion_profile(), config(), 1_000_000_000
        )
        self.assertEqual((guide.verdict, guide.depth), ("confirm", "unknown"))
        gate = ConfirmationGate()
        gate.arm(guide)
        self.assertFalse(gate.confirm("gesture", 1_100_000_000))
        gate.arm(guide)
        self.assertTrue(gate.confirm("button", 1_100_000_000))
        self.assertFalse(gate.confirm("button", 1_100_000_001))

    def test_expired_confirmation_and_nonconfirm_cannot_complete(self):
        gate = ConfirmationGate()
        guide = evaluate_grasp(
            result(),
            "cup-1",
            hand(NormalizedRect(0.68, 0.45, 0.82, 0.68)),
            depth(),
            fusion_profile(),
            config(),
            1_000_000_000,
        )
        gate.arm(guide)
        self.assertFalse(gate.confirm("voice", guide.expires_ns))
        gate.arm(
            evaluate_grasp(
                result(), "cup-1", hand(), depth(), fusion_profile(), config(), 1_000_000_000
            )
        )
        self.assertFalse(gate.confirm("voice", 1_100_000_000))

    def test_quality_occlusion_identity_calibration_and_time_gates(self):
        now = 1_000_000_000
        cases = [
            (result(score=0.2), hand(), depth(), "observation_quality_low"),
            (result(), hand(occluded=True), depth(), "hand_occluded"),
            (result(), hand(session_id=8), depth(), "session_mismatch"),
            (result(), hand(frame_id=4), depth(), "frame_mismatch"),
            (result(), hand(calibration_id="other"), depth(), "calibration_mismatch"),
            (result(), hand(capture_ns=500_000_000), depth(), "sample_expired"),
        ]
        for located, observed_hand, tof, reason in cases:
            with self.subTest(reason=reason):
                self.assertEqual(
                    evaluate_grasp(
                        located, "cup-1", observed_hand, tof, fusion_profile(), config(), now
                    ).reason,
                    reason,
                )

    def test_invalid_depth_is_unknown_not_clear(self):
        distances = [1500] * 16
        distances[11] = None
        guide = evaluate_grasp(
            result(), "cup-1", hand(), depth(distances), fusion_profile(), config(), 1_000_000_000
        )
        self.assertEqual((guide.verdict, guide.depth), ("guide", "unknown"))


if __name__ == "__main__":
    unittest.main()
