import base64
import json
import subprocess
import sys
import threading
import time
import unittest
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch

from server.api.http import create_server
from server.api.pc_jobs import (
    JobBusy,
    JobFailure,
    PcJobs,
    ProcessRunner,
    public_result,
    validate_request,
)
from server.api.state import CommandBroker, DashboardStore

TEXT = {"kind": "dialogue", "question": "hello", "allow_cloud_text": True}
IMAGE = {
    "kind": "locate",
    "query": "cup",
    "image_base64": base64.b64encode(b"\xff\xd8xx\xff\xd9").decode(),
}


def wait_done(jobs, job_id):
    until = time.monotonic() + 2
    while jobs.active and time.monotonic() < until:
        time.sleep(0.005)
    if jobs.active:
        raise AssertionError("job still running")
    return jobs.get(job_id)


class PcJobTests(unittest.TestCase):
    def test_request_bounds_and_no_arbitrary_paths_or_cloud_images(self):
        self.assertEqual(validate_request(IMAGE), IMAGE)
        for request in (
            {**IMAGE, "image_path": "C:/private"},
            {**IMAGE, "image_base64": "invalid"},
            {**IMAGE, "query": "\n"},
            {**IMAGE, "image_base64": "A" * 1_500_000},
            {**TEXT, "allow_cloud_text": False},
            {**TEXT, "image_base64": IMAGE["image_base64"]},
            {**TEXT, "question": "a" * 1001},
        ):
            with self.assertRaises(ValueError):
                validate_request(request)

    def test_results_filter_private_fields_and_keep_depth_unknown(self):
        value = public_result(
            "locate",
            {
                "boxes": [[0, 0, 1, 1]],
                "image_size": [640, 480],
                "inference_ms": 12,
                "distance_m": 0.2,
                "secret": "hidden",
            },
        )
        self.assertIsNone(value["distance_m"])
        self.assertFalse(value["grasp_confirmed"])
        self.assertNotIn("secret", value)
        for box in ([0, 0, float("nan"), 1], [0, 0, 2, 1], [False, 0, 1, 1]):
            with self.assertRaises(ValueError):
                public_result("locate", {"boxes": [box], "image_size": [1, 1], "inference_ms": 0})

    def test_busy_cancel_no_late_result_and_closed(self):
        release = threading.Event()

        def runner(request, cancelled):
            release.wait(2)
            return {"text": "late"}

        jobs = PcJobs(runner)
        try:
            job = jobs.submit(TEXT)
            self.assertEqual(jobs.current()["job_id"], job["job_id"])
            with self.assertRaises(JobBusy):
                jobs.submit(TEXT)
            self.assertEqual(jobs.cancel(job["job_id"])["state"], "cancelled")
            with self.assertRaises(JobBusy):
                jobs.submit(TEXT)
            release.set()
            result = wait_done(jobs, job["job_id"])
            self.assertEqual(result["state"], "cancelled")
            self.assertIsNone(result["result"])
        finally:
            release.set()
            jobs.close()
        with self.assertRaises(JobBusy):
            jobs.submit(TEXT)

    def test_failure_never_serializes_exception_and_snapshot_copied(self):
        def runner(request, cancelled):
            raise RuntimeError("private credential diagnostic")

        jobs = PcJobs(runner)
        job = jobs.submit(TEXT)
        result = wait_done(jobs, job["job_id"])
        self.assertNotIn("private", json.dumps(result))
        self.assertEqual(result["state"], "failed")
        self.assertIsNone(jobs.current())
        result["error"] = "modified"
        self.assertNotEqual(jobs.get(job["job_id"])["error"], "modified")
        jobs.close()

    def test_bounded_records(self):
        jobs = PcJobs(lambda request, cancelled: {"text": "answer"})
        for _ in range(18):
            job = jobs.submit(TEXT)
            self.assertEqual(wait_done(jobs, job["job_id"])["state"], "succeeded")
        self.assertEqual(len(jobs.records), 16)
        jobs.close()

    def test_timeout_kills_real_child_and_removes_temporary_input(self):
        original = subprocess.Popen
        processes, inputs = [], []

        def launch(command, **kwargs):
            if command[0] == "taskkill.exe":
                return original(command, **kwargs)
            inputs.append(Path(command[-1]))
            process = original([sys.executable, "-c", "import time; time.sleep(5)"], **kwargs)
            processes.append(process)
            return process

        with patch("server.api.pc_jobs.subprocess.Popen", side_effect=launch):
            with self.assertRaisesRegex(JobFailure, "timeout"):
                ProcessRunner(Path(sys.executable), timeout=0.1)(TEXT, threading.Event())
        self.assertIsNotNone(processes[0].poll())
        self.assertFalse(inputs[0].exists())

    def test_cancel_kills_real_child(self):
        original = subprocess.Popen
        processes = []

        def launch(command, **kwargs):
            if command[0] == "taskkill.exe":
                return original(command, **kwargs)
            process = original([sys.executable, "-c", "import time; time.sleep(5)"], **kwargs)
            processes.append(process)
            return process

        cancelled = threading.Event()
        cancelled.set()
        with patch("server.api.pc_jobs.subprocess.Popen", side_effect=launch):
            with self.assertRaisesRegex(JobFailure, "cancelled"):
                ProcessRunner(Path(sys.executable))(TEXT, cancelled)
        self.assertIsNotNone(processes[0].poll())


class PcHttpTests(unittest.TestCase):
    def setUp(self):
        self.jobs = PcJobs(lambda request, cancelled: {"text": "test answer"})
        store = DashboardStore()
        self.server = create_server(store, CommandBroker(store), port=0, pc_jobs=self.jobs)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)

    def request(self, method, path, body=None, origin="http://127.0.0.1:5173", **extra):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        headers = {"Content-Type": "application/json", **extra}
        if origin:
            headers["Origin"] = origin
        try:
            connection.request(
                method, path, json.dumps(body) if body is not None else None, headers
            )
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def test_submit_poll_cancel_missing(self):
        status, receipt = self.request("POST", "/api/v1/pc/jobs", TEXT)
        self.assertEqual(status, 202)
        wait_done(self.jobs, receipt["job_id"])
        path = "/api/v1/pc/jobs/" + receipt["job_id"]
        status, result = self.request("GET", path)
        self.assertEqual((status, result["state"]), (200, "succeeded"))
        status, _ = self.request("POST", path + "/cancel", {})
        self.assertEqual(status, 200)
        status, _ = self.request("POST", path + "/cancel", {"extra": True})
        self.assertEqual(status, 400)
        status, _ = self.request("GET", "/api/v1/pc/jobs/" + "0" * 32)
        self.assertEqual(status, 404)

    def test_origin_host_and_body_limits(self):
        for origin in (None, "https://evil.example", "http://127.0.0.1:9999"):
            self.assertEqual(self.request("POST", "/api/v1/pc/jobs", TEXT, origin)[0], 403)
        self.assertEqual(self.request("POST", "/api/v1/pc/jobs", TEXT, Host="evil.example")[0], 421)
        self.assertEqual(
            self.request("POST", "/api/v1/pc/jobs", {**TEXT, "key": "not allowed"})[0], 400
        )
        self.assertEqual(
            self.request("POST", "/api/v1/pc/jobs", TEXT, **{"Content-Length": "1500000"})[0], 413
        )

    def test_opt_in_required(self):
        self.server.pc_jobs = None
        self.assertEqual(self.request("POST", "/api/v1/pc/jobs", TEXT)[0], 503)
        self.server.pc_jobs = self.jobs

    def test_active_recovery_and_unknown_cancel(self):
        status, value = self.request("GET", "/api/v1/pc/active")
        self.assertEqual((status, value), (200, {"job": None}))
        with self.assertRaises(KeyError):
            self.jobs.cancel("missing")

    def test_non_json_body_rejected(self):
        self.assertEqual(
            self.request("POST", "/api/v1/pc/jobs", TEXT, **{"Content-Type": "text/plain"})[0], 415
        )


if __name__ == "__main__":
    unittest.main()
