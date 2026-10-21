import hashlib
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from server.perception.assist.contracts import EventStamp
from server.perception.assist.deepseek import DeepSeekDialogue, DialogueFailure
from server.perception.locate.pc_runtime import parse_model_boxes
from tools.prepare_locate_pc import download_ranges


class PcRuntimeTests(unittest.TestCase):
    def test_weight_range_requires_matching_header_and_hash(self):
        class Response(io.BytesIO):
            status = 206
            headers = {"Content-Range": "bytes 0-3/4"}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("urllib.request.urlopen", return_value=Response(b"abcd")):
                download_ranges(root, "test.safetensors", 4, hashlib.sha256(b"abcd").hexdigest())
            self.assertEqual((root / "test.safetensors").read_bytes(), b"abcd")

    def test_bad_weight_range_never_becomes_model_file(self):
        class Response(io.BytesIO):
            status = 200
            headers = {}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("urllib.request.urlopen", side_effect=lambda *a, **k: Response(b"abcd")):
                with self.assertRaisesRegex(RuntimeError, "unexpected range"):
                    download_ranges(root, "test.safetensors", 4, "unused")
            self.assertFalse((root / "test.safetensors").exists())

    def test_image_upload_requires_explicit_consent(self):
        with self.assertRaisesRegex(ValueError, "consent"):
            DeepSeekDialogue("test-secret").ask(
                "描述图片", EventStamp(1, "q1", 1, 100, "external"), image=b"\xff\xd8\xff\xd9"
            )

    def test_box_coordinates_and_explicit_absence(self):
        self.assertEqual(
            parse_model_boxes("<ref>cup</ref><box><10><20><300><400></box>"),
            [[0.01, 0.02, 0.3, 0.4]],
        )
        self.assertEqual(parse_model_boxes("<box>none</box>"), [])

    def test_bad_or_missing_boxes_are_failure_not_absence(self):
        for answer in (
            "",
            "cup is on the left",
            "<box><20><0><10><100></box>",
            "<box><0><0><1001><100></box>",
        ):
            with self.subTest(answer=answer), self.assertRaises(ValueError):
                parse_model_boxes(answer)

    def test_deepseek_maps_real_format_to_event(self):
        response = io.BytesIO(
            json.dumps(
                {
                    "choices": [
                        {"finish_reason": "stop", "message": {"content": "你好！\n我是对话助手。"}}
                    ]
                }
            ).encode()
        )
        stamp = EventStamp(1, "q1", 1, 100, "external")
        with patch("urllib.request.OpenerDirector.open", return_value=response) as opened:
            event = DeepSeekDialogue("test-secret").ask("你好", stamp)
        self.assertEqual(event.text, "你好！ 我是对话助手。")
        self.assertEqual(event.stamp, stamp)
        self.assertEqual(
            opened.call_args.args[0].full_url, "https://api.deepseek.com/chat/completions"
        )

    def test_deepseek_http_error_does_not_echo_key_or_body(self):
        error = urllib.error.HTTPError("url", 401, "test-secret", {}, None)
        with patch("urllib.request.OpenerDirector.open", side_effect=error):
            with self.assertRaisesRegex(DialogueFailure, "^DeepSeek HTTP 401$"):
                DeepSeekDialogue("test-secret").ask("你好", EventStamp(1, "q1", 1, 100, "external"))


if __name__ == "__main__":
    unittest.main()
