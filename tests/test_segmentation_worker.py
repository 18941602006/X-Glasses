import unittest

from server.perception.navigation.worker import (
    FrameRequest,
    IsolatedSegmentationAdapter,
    WorkerFailure,
    decode_binary_rle,
)


class FakeTransport:
    def __init__(self, response=None, failure=None):
        self.response = response
        self.failure = failure
        self.message = None
        self.timeout = None

    def request(self, message, timeout_ms):
        self.message, self.timeout = message, timeout_ms
        if self.failure:
            raise self.failure
        return self.response


def response(**changes):
    value = {
        "schema": "xg.segment.response.v1",
        "session_id": "9",
        "frame_id": 7,
        "model_id": "model@sha256:abc",
        "width": 3,
        "height": 3,
        "quality": 0.8,
        "rle": [[1, 6], [0, 3]],
    }
    value.update(changes)
    return value


def frame():
    return FrameRequest(9, 7, 100, 2, 110, "cal-1", "replay")


class SegmentationWorkerTests(unittest.TestCase):
    def test_valid_response_retains_only_host_timing_and_provenance(self):
        transport = FakeTransport(response())
        adapter = IsolatedSegmentationAdapter(transport, "model@sha256:abc", 200)
        mask = adapter.segment(b"\xff\xd8ok\xff\xd9", frame=frame())
        self.assertEqual((mask.width, mask.height, sum(mask.values)), (3, 3, 6))
        self.assertEqual(
            (mask.capture_ns, mask.calibration_id, mask.source), (100, "cal-1", "replay")
        )
        self.assertEqual(transport.timeout, 200)
        self.assertEqual(transport.message["session_id"], "9")

    def test_timeout_is_not_a_mask(self):
        adapter = IsolatedSegmentationAdapter(FakeTransport(failure=TimeoutError()), "m")
        with self.assertRaisesRegex(WorkerFailure, "timeout"):
            adapter.segment(b"\xff\xd8x\xff\xd9", frame=frame())

    def test_stale_identity_model_and_extra_fields_rejected(self):
        cases = [
            response(session_id="8"),
            response(frame_id=8),
            response(model_id="other"),
            {**response(), "trusted_capture_ns": 1},
        ]
        for value in cases:
            with self.subTest(value=value):
                adapter = IsolatedSegmentationAdapter(FakeTransport(value), "model@sha256:abc")
                with self.assertRaises(WorkerFailure):
                    adapter.segment(b"\xff\xd8x\xff\xd9", frame=frame())

    def test_rle_is_binary_bounded_and_exact(self):
        self.assertEqual(decode_binary_rle(3, 3, [[0, 9]]), (False,) * 9)
        for runs in ([[2, 9]], [[1, 8]], [[1, 10]], [[True, 9]], "not-runs"):
            with self.subTest(runs=runs), self.assertRaises(WorkerFailure):
                decode_binary_rle(3, 3, runs)

    def test_jpeg_and_timeout_bounds(self):
        with self.assertRaises(ValueError):
            IsolatedSegmentationAdapter(FakeTransport(response()), "")
        with self.assertRaises(ValueError):
            IsolatedSegmentationAdapter(FakeTransport(response()), "m", 0)
        adapter = IsolatedSegmentationAdapter(FakeTransport(response()), "model@sha256:abc")
        with self.assertRaises(ValueError):
            adapter.segment(b"not-jpeg", frame=frame())
        with self.assertRaises(ValueError):
            FrameRequest(0, 1, 0, 0, 0, "cal", "live")
        with self.assertRaises(ValueError):
            FrameRequest(1, 1, 0, 0, 0, "cal", "untrusted")

    def test_nonfinite_quality_rejected(self):
        adapter = IsolatedSegmentationAdapter(
            FakeTransport(response(quality=float("nan"))), "model@sha256:abc"
        )
        with self.assertRaises(WorkerFailure):
            adapter.segment(b"\xff\xd8x\xff\xd9", frame=frame())


if __name__ == "__main__":
    unittest.main()
