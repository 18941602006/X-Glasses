import json
import threading
import unittest
from http.client import HTTPConnection

from server.api.http import create_server
from server.api.state import CommandBroker, CommandUnavailable, DashboardStore


class StateTests(unittest.TestCase):
    def test_default_is_explicitly_offline_and_isolated(self):
        store = DashboardStore(7)
        first = store.snapshot(8)
        self.assertEqual(first["schema"], "xg.status.v1")
        self.assertEqual(first["mode"], "offline")
        self.assertEqual(first["link"]["state"], "disconnected")
        first["link"]["state"] = "ready"
        self.assertEqual(store.snapshot(9)["link"]["state"], "disconnected")

    def test_bounded_logs_commands_and_terminal_transition(self):
        store = DashboardStore()
        broker = CommandBroker(store, lambda action, now: now + 1)
        for index in range(110):
            store.add_log("info", f"event {index}", index)
        for index in range(40):
            broker.submit("safe_stop", index + 1)
        snapshot = store.snapshot(200)
        self.assertEqual(len(snapshot["logs"]), 100)
        self.assertEqual(len(snapshot["commands"]), 32)
        request = snapshot["commands"][-1]["request_id"]
        self.assertTrue(store.resolve_command(request, "rejected"))
        self.assertFalse(store.resolve_command(request, "applied"))

    def test_broker_rejects_unknown_or_missing_dispatcher(self):
        broker = CommandBroker(DashboardStore())
        with self.assertRaises(ValueError):
            broker.submit("haptic", 1)
        with self.assertRaises(CommandUnavailable):
            broker.submit("safe_stop", 1)


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.store = DashboardStore()
        self.server = create_server(
            self.store, CommandBroker(self.store, lambda action, now: 42), port=0
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method, path, body=None, headers=None):
        self.connection.request(method, path, body=body, headers=headers or {})
        response = self.connection.getresponse()
        data = json.loads(response.read())
        return response.status, data

    def test_health_status_and_host_guard(self):
        status, body = self.request("GET", "/api/v1/health")
        self.assertEqual((status, body["scope"]), (200, "loopback"))
        status, body = self.request("GET", "/api/v1/status")
        self.assertEqual((status, body["mode"]), (200, "offline"))
        status, _ = self.request("GET", "/api/v1/status", headers={"Host": "example.com"})
        self.assertEqual(status, 421)
        status, body = self.request("GET", "/api/v1/health", headers={"Host": "[::1]:8765"})
        self.assertEqual((status, body["scope"]), (200, "loopback"))

    def test_command_pending_and_strict_input(self):
        headers = {"Content-Type": "application/json"}
        status, body = self.request(
            "POST", "/api/v1/commands", json.dumps({"action": "safe_stop"}), headers
        )
        self.assertEqual((status, body["request_id"], body["state"]), (202, "42", "pending"))
        status, body = self.request(
            "POST", "/api/v1/commands", json.dumps({"action": "haptic"}), headers
        )
        self.assertEqual((status, body["error"]), (400, "invalid_command"))

    def test_loopback_binding_only(self):
        with self.assertRaises(ValueError):
            create_server(self.store, CommandBroker(self.store), "0.0.0.0", 0)


if __name__ == "__main__":
    unittest.main()
