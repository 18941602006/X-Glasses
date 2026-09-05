import unittest

from server.arbitration.adapters import (
    from_dialogue,
    from_grasp,
    from_map,
    from_navigation,
    from_ocr,
    from_signal,
)
from server.arbitration.core import OutputArbiter, OutputCandidate, OutputDecision
from server.output.executor import SafeOutputExecutor
from server.perception.assist.contracts import (
    DialogueEvent,
    EventStamp,
    MapInstructionEvent,
    OcrEvent,
    OcrLine,
    TrafficSignalEvent,
    parse_dialogue_response,
    parse_map_event,
    parse_ocr_response,
    parse_signal_response,
)
from server.perception.assist.worker import AssistFailure, AssistWorkerAdapter
from server.perception.locate.grasp import GraspGuide
from server.perception.navigation.contracts import NavigationEvent


def stamp(correlation_id="c1", created_ns=100, expires_ns=1000, session_id=7):
    return EventStamp(session_id, correlation_id, created_ns, expires_ns, "synthetic")


class AssistContractTests(unittest.TestCase):
    def test_signal_never_grants_crossing_permission(self):
        for state in ("red", "green", "unknown"):
            event = TrafficSignalEvent(stamp(), state, True, 0.9, "signal@fixed")
            self.assertIn("不是过街许可", event.spoken_text())
            self.assertNotIn("可以过街", event.spoken_text())
        self.assertIn(
            "方向无法确认", TrafficSignalEvent(stamp(), "green", False, 0.8, "m").spoken_text()
        )

    def test_signal_response_requires_exact_provenance(self):
        response = {
            "schema": "xg.signal.response.v1",
            "session_id": "7",
            "correlation_id": "c1",
            "model_id": "signal@fixed",
            "state": "red",
            "direction_known": True,
            "confidence": 0.8,
        }
        self.assertEqual(parse_signal_response(response, stamp(), "signal@fixed").state, "red")
        for bad in (
            {**response, "session_id": "8"},
            {**response, "extra": 1},
            {**response, "confidence": float("nan")},
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_signal_response(bad, stamp(), "signal@fixed")

    def test_ocr_preserves_order_and_original_text(self):
        response = {
            "schema": "xg.ocr.response.v1",
            "session_id": "7",
            "correlation_id": "c1",
            "model_id": "ocr@fixed",
            "language": "zh",
            "lines": [
                {"order": 0, "text": "第一行", "confidence": 0.9},
                {"order": 1, "text": "第二行", "confidence": 0.8},
            ],
        }
        event = parse_ocr_response(response, stamp(), "ocr@fixed")
        self.assertEqual(event.original_text, "第一行\n第二行")
        response["lines"].reverse()
        with self.assertRaises(ValueError):
            parse_ocr_response(response, stamp(), "ocr@fixed")

    def test_ocr_is_bounded_and_rejects_duplicate_order(self):
        with self.assertRaises(ValueError):
            OcrEvent(stamp(), (OcrLine(0, "a", 1), OcrLine(0, "b", 1)), "zh", "m")
        with self.assertRaises(ValueError):
            OcrLine(0, "x" * 401, 1)

    def test_map_is_external_guidance_not_safety(self):
        message = {
            "schema": "xg.map.event.v1",
            "session_id": "7",
            "correlation_id": "c1",
            "provider_id": "offline-test",
            "route_id": "r1",
            "maneuver": "left",
            "distance_m": 20,
            "instruction": "二十米后左转",
        }
        event = parse_map_event(message, stamp(), "offline-test")
        self.assertIsInstance(event, MapInstructionEvent)
        self.assertFalse(hasattr(event, "safe_to_cross"))

    def test_dialogue_requires_provider_and_model_echo(self):
        response = {
            "schema": "xg.dialogue.response.v1",
            "session_id": "7",
            "correlation_id": "c1",
            "provider_id": "fake",
            "model_id": "fake-model",
            "text": "测试回答",
        }
        event = parse_dialogue_response(response, stamp(), "fake", "fake-model")
        self.assertIsInstance(event, DialogueEvent)
        with self.assertRaises(ValueError):
            parse_dialogue_response(
                {**response, "model_id": "other"}, stamp(), "fake", "fake-model"
            )

    def test_untrusted_types_and_untrimmed_text_are_rejected(self):
        with self.assertRaises(ValueError):
            TrafficSignalEvent(stamp(), [], True, 0.9, "m")
        with self.assertRaises(ValueError):
            MapInstructionEvent(stamp(), "r", "left", "20", "左转", "p")
        with self.assertRaises(ValueError):
            DialogueEvent(stamp(), " padded ", "p", "m")


class ArbitrationTests(unittest.TestCase):
    def candidate(
        self,
        category,
        correlation_id=None,
        created_ns=100,
        expires_ns=1000,
        message=None,
        session_id=7,
    ):
        correlation_id = correlation_id or category
        message = message or category
        return OutputCandidate(
            stamp(correlation_id, created_ns, expires_ns, session_id), category, message
        )

    def test_fixed_safety_priority_preempts_dialogue_and_map(self):
        arbiter = OutputArbiter(minimum_repeat_ns=10)
        for category in ("dialogue", "map", "local_direction", "emergency", "sensor_failure"):
            self.assertTrue(arbiter.submit(self.candidate(category), 200, 7))
        self.assertEqual(arbiter.decide(200, 7).candidate.category, "sensor_failure")

    def test_local_direction_preempts_green_signal_and_map(self):
        arbiter = OutputArbiter(minimum_repeat_ns=10)
        for category in ("map", "traffic_signal", "local_direction"):
            arbiter.submit(self.candidate(category), 200, 7)
        self.assertEqual(arbiter.decide(200, 7).candidate.category, "local_direction")

    def test_expired_future_and_wrong_session_are_rejected(self):
        arbiter = OutputArbiter()
        self.assertFalse(arbiter.submit(self.candidate("map", expires_ns=150), 200, 7))
        self.assertFalse(arbiter.submit(self.candidate("map", created_ns=300), 200, 7))
        self.assertFalse(arbiter.submit(self.candidate("map", session_id=8), 200, 7))
        self.assertIsNone(arbiter.decide(200, 7))

    def test_newest_same_category_replaces_and_old_cannot_overwrite(self):
        arbiter = OutputArbiter(minimum_repeat_ns=10)
        self.assertTrue(
            arbiter.submit(self.candidate("map", created_ns=200, message="new"), 250, 7)
        )
        self.assertFalse(
            arbiter.submit(self.candidate("map", created_ns=100, message="old"), 250, 7)
        )
        self.assertEqual(arbiter.decide(250, 7).candidate.message, "new")

    def test_cancel_is_scoped_to_session_and_correlation(self):
        arbiter = OutputArbiter(minimum_repeat_ns=10)
        arbiter.submit(self.candidate("reading", "task"), 200, 7)
        arbiter.submit(self.candidate("dialogue", "task"), 200, 7)
        self.assertEqual(arbiter.cancel("task", 8), 0)
        self.assertEqual(arbiter.cancel("task", 7), 2)
        self.assertIsNone(arbiter.decide(200, 7))

    def test_repeat_is_throttled_but_new_message_is_not(self):
        arbiter = OutputArbiter(minimum_repeat_ns=100)
        arbiter.submit(self.candidate("dialogue", message="same"), 200, 7)
        self.assertIsNotNone(arbiter.decide(200, 7))
        self.assertIsNone(arbiter.decide(250, 7))
        arbiter.submit(self.candidate("dialogue", created_ns=260, message="changed"), 270, 7)
        self.assertEqual(arbiter.decide(270, 7).candidate.message, "changed")

    def test_clear_session_discards_pending_state(self):
        arbiter = OutputArbiter()
        arbiter.submit(self.candidate("emergency"), 200, 7)
        arbiter.clear_session()
        self.assertIsNone(arbiter.decide(200, 7))

    def test_free_text_cannot_reintroduce_crossing_permission(self):
        for message in ("现在可以过街", "SAFE TO CROSS", "cross now"):
            with self.subTest(message=message), self.assertRaises(ValueError):
                self.candidate("traffic_signal", message=message)


class FakeAssistTransport:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def request(self, message, timeout_ms):
        self.calls.append((message, timeout_ms))
        if self.error:
            raise self.error
        return self.response


class WorkerBoundaryTests(unittest.TestCase):
    def adapter(self, transport):
        return AssistWorkerAdapter(
            transport,
            signal_model_id="signal@fixed",
            ocr_model_id="ocr@fixed",
            dialogue_provider_id="fake-provider",
            dialogue_model_id="fake-model",
        )

    def test_signal_request_is_bounded_and_has_no_path_or_url(self):
        response = {
            "schema": "xg.signal.response.v1",
            "session_id": "7",
            "correlation_id": "c1",
            "model_id": "signal@fixed",
            "state": "unknown",
            "direction_known": False,
            "confidence": 0.4,
        }
        transport = FakeAssistTransport(response)
        event = self.adapter(transport).recognize_signal(b"\xff\xd8x\xff\xd9", stamp())
        self.assertEqual(event.state, "unknown")
        self.assertEqual(
            set(transport.calls[0][0]), {"schema", "session_id", "correlation_id", "jpeg_base64"}
        )

    def test_bad_media_question_timeout_and_provenance_fail_closed(self):
        for action in (
            lambda: self.adapter(FakeAssistTransport({})).read_text(b"bad", stamp()),
            lambda: self.adapter(FakeAssistTransport({})).ask("x" * 1001, stamp()),
        ):
            with self.subTest(action=action), self.assertRaises(ValueError):
                action()
        with self.assertRaises(AssistFailure):
            self.adapter(FakeAssistTransport(error=TimeoutError())).ask("问题", stamp())
        with self.assertRaises(AssistFailure):
            self.adapter(FakeAssistTransport({})).ask("问题", stamp())


class FakeOutputTransport:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def speak(self, text, deadline_ns):
        self.calls.append(("speak", text, deadline_ns))
        if self.fail:
            raise RuntimeError("offline")

    def cue(self, cue, deadline_ns):
        self.calls.append(("cue", cue, deadline_ns))


class OutputBoundaryTests(unittest.TestCase):
    def decision(self, expires_ns=1000, session_id=7, cue="warning"):
        candidate = OutputCandidate(
            stamp("out", 100, expires_ns, session_id), "emergency", "停止", cue
        )
        return OutputDecision("decision-1", candidate, 200, 550)

    def test_executor_requires_active_arbitrated_decision_and_is_idempotent(self):
        transport = FakeOutputTransport()
        executor = SafeOutputExecutor(transport)
        self.assertEqual(
            executor.execute(self.decision(), session_id=7, now_ns=200).status, "applied"
        )
        self.assertEqual(
            executor.execute(self.decision(), session_id=7, now_ns=210).reason, "duplicate_decision"
        )
        self.assertEqual(len(transport.calls), 2)
        with self.assertRaises(TypeError):
            executor.execute(object(), session_id=7, now_ns=200)

    def test_executor_rejects_expired_or_wrong_session_and_reports_failure(self):
        for session_id, now_ns in ((8, 200), (7, 1000)):
            transport = FakeOutputTransport()
            receipt = SafeOutputExecutor(transport).execute(
                self.decision(), session_id=session_id, now_ns=now_ns
            )
            self.assertEqual(receipt.status, "rejected")
            self.assertFalse(transport.calls)
        receipt = SafeOutputExecutor(FakeOutputTransport(fail=True)).execute(
            self.decision(), session_id=7, now_ns=200
        )
        self.assertEqual((receipt.status, receipt.reason), ("failed", "transport_failure"))


class CandidateAdapterTests(unittest.TestCase):
    def test_navigation_unknown_and_stop_map_to_safety_priorities(self):
        base = dict(
            created_ns=100,
            expires_ns=1000,
            session_id=7,
            frame_id=2,
            tof_sample_id=3,
            profile_id="cal",
            config_id="cfg",
            lane_coverage=(0.0, 0.0, 0.0),
            nearest_obstacle_mm=None,
            source="synthetic",
        )
        unknown = NavigationEvent("unknown", "none", "stale", **base)
        stopped = NavigationEvent("stop", "none", "obstacle", **base)
        candidate = NavigationEvent("candidate", "right", "candidate_corridor", **base)
        self.assertEqual(from_navigation(unknown).category, "sensor_failure")
        self.assertEqual(from_navigation(stopped).category, "emergency")
        self.assertEqual(
            (from_navigation(candidate).category, from_navigation(candidate).cue),
            ("local_direction", "right"),
        )

    def test_grasp_unknown_confirm_and_depth_unknown_are_explicit(self):
        base = (100, 1000, 7, 2, "cup", "hand", None, None, "synthetic")
        unknown = GraspGuide("unknown", "stale", "unknown", "unknown", "unknown", False, *base)
        confirm = GraspGuide("confirm", "overlap", "aligned", "aligned", "unknown", True, *base)
        guide = GraspGuide("guide", "same_zone", "right", "aligned", "unknown", False, *base)
        self.assertIn("不可用", from_grasp(unknown).message)
        self.assertEqual(from_grasp(confirm).cue, "confirm")
        self.assertIn("无法确认", from_grasp(guide).message)

    def test_assist_events_map_without_crossing_permission(self):
        signal = TrafficSignalEvent(stamp(), "green", True, 0.9, "m")
        map_event = MapInstructionEvent(stamp(), "r", "left", 20, "二十米后左转", "p")
        ocr = OcrEvent(stamp(), (OcrLine(0, "原文", 0.9),), "zh", "m")
        dialogue = DialogueEvent(stamp(), "回答", "p", "m")
        self.assertNotIn("可以过街", from_signal(signal).message)
        self.assertEqual(from_map(map_event).cue, "left")
        self.assertEqual(from_ocr(ocr).message, "原文")
        self.assertEqual(from_dialogue(dialogue).category, "dialogue")

    def test_long_reading_and_dialogue_require_chunking(self):
        with self.assertRaises(ValueError):
            from_ocr(
                OcrEvent(
                    stamp(),
                    (OcrLine(0, "字" * 300, 0.9), OcrLine(1, "字" * 300, 0.9)),
                    "zh",
                    "m",
                )
            )
        with self.assertRaises(ValueError):
            from_dialogue(DialogueEvent(stamp(), "a" * 501, "p", "m"))


if __name__ == "__main__":
    unittest.main()
