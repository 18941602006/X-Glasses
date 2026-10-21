import json
import subprocess
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from server.api.pc_jobs import JobFailure, validate_request
from server.api.warm_worker import WarmProcessRunner
from server.perception.assist.deepseek import DeepSeekDialogue, DialogueFailure
from tools.pc_worker import WorkerState

FAKE = """
import json,os,sys,time
from pathlib import Path
root=Path(sys.argv[1])
for token in sys.stdin:
 token=token.strip()
 request=json.loads((root/(token+'.in')).read_text(encoding='utf-8'))
 query=request['query']
 if query=='sleep': time.sleep(5)
 if query=='crash': sys.exit(3)
 result={'pid':os.getpid(),'boxes':[],'image_size':[8,8],'inference_ms':1}
 path=root/(token+'.tmp')
 path.write_text(json.dumps({'ok':True,'result':result}),encoding='utf-8')
 path.replace(root/(token+'.out'))
"""


class WarmWorkerTests(unittest.TestCase):
    def setUp(self):
        self.original = subprocess.Popen
        self.processes = []

        def launch(command, **kwargs):
            if command[0] == "taskkill.exe":
                return self.original(command, **kwargs)
            process = self.original([sys.executable, "-u", "-c", FAKE, command[-1]], **kwargs)
            self.processes.append(process)
            return process

        self.patch = patch("server.api.warm_worker.subprocess.Popen", side_effect=launch)
        self.patch.start()
        self.runner = WarmProcessRunner(Path(sys.executable), timeout=3)

    def tearDown(self):
        self.runner.close()
        self.patch.stop()

    def run_job(self, query="cat", cancelled=None):
        return self.runner({"kind": "locate", "query": query}, cancelled or threading.Event())

    def test_two_jobs_reuse_one_process_and_remove_request_images(self):
        first, second = self.run_job(), self.run_job()
        self.assertEqual(first["pid"], second["pid"])
        self.assertEqual(len(self.processes), 1)
        root = Path(self.runner.directory.name)
        self.assertEqual([path.name for path in root.iterdir()], ["worker.err"])
        self.runner.close()
        self.assertFalse(root.exists())
        self.assertIsNotNone(self.processes[0].poll())

    def test_cancel_poisoned_worker_does_not_get_reused(self):
        self.run_job()
        cancelled = threading.Event()
        cancelled.set()
        with self.assertRaisesRegex(JobFailure, "cancelled"):
            self.run_job(cancelled=cancelled)
        self.assertIsNotNone(self.processes[0].poll())
        self.run_job()
        self.assertEqual(len(self.processes), 2)

    def test_timeout_kills_and_next_job_restarts(self):
        self.runner.fallback.timeout = 0.15
        with self.assertRaisesRegex(JobFailure, "timeout"):
            self.run_job("sleep")
        self.assertIsNotNone(self.processes[0].poll())
        self.runner.fallback.timeout = 3
        self.run_job()
        self.assertEqual(len(self.processes), 2)

    def test_crashed_process_fails_closed_and_can_restart(self):
        with self.assertRaises(JobFailure):
            self.run_job("crash")
        self.run_job()
        self.assertEqual(len(self.processes), 2)

    def test_closed_runner_never_starts_another_model(self):
        self.runner.close()
        with self.assertRaises(JobFailure):
            self.run_job()
        self.assertEqual(self.processes, [])


class TranslationTests(unittest.TestCase):
    def test_chinese_requires_consent_and_source_is_bounded(self):
        import base64

        request = {
            "kind": "locate",
            "query": "眼镜",
            "image_base64": base64.b64encode(b"\xff\xd8xx").decode(),
        }
        with self.assertRaises(ValueError):
            validate_request(request)
        request["allow_cloud_translation"] = True
        self.assertEqual(validate_request(request), request)
        with self.assertRaises(ValueError):
            validate_request({**request, "source": "cloud_camera"})

    def test_same_description_reuses_translation_and_still_requires_consent(self):
        state = WorkerState()
        request = {"query": "桌上的眼镜", "allow_cloud_translation": True}
        with (
            patch("server.perception.assist.deepseek.load_api_key", return_value="test-secret"),
            patch(
                "server.perception.assist.deepseek.DeepSeekDialogue.translate_query",
                return_value="eyeglasses on the table",
            ) as translated,
        ):
            self.assertEqual(state.english(request), "eyeglasses on the table")
            self.assertEqual(state.english(request), "eyeglasses on the table")
            translated.assert_called_once_with("桌上的眼镜")
            with self.assertRaises(ValueError):
                state.english({"query": "桌上的眼镜"})
        self.assertEqual(state.english({"query": "red cup"}), "red cup")

    def test_translation_payload_contains_no_image_and_rejects_non_english(self):
        with patch.object(DeepSeekDialogue, "_complete", return_value="eyeglasses") as completed:
            self.assertEqual(DeepSeekDialogue("test-secret").translate_query("眼镜"), "eyeglasses")
        payload = completed.call_args.args[0]
        self.assertEqual(payload["messages"][1]["content"], "眼镜")
        self.assertNotIn("image_url", json.dumps(payload))
        with patch.object(DeepSeekDialogue, "_complete", return_value="眼镜在桌上"):
            with self.assertRaises(DialogueFailure):
                DeepSeekDialogue("test-secret").translate_query("眼镜")


if __name__ == "__main__":
    unittest.main()
