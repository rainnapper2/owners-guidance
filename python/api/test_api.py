"""Unit tests for Python API server."""

import json
import threading
import unittest
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from python.api.server import run_server


class TestAPIServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = run_server("127.0.0.1", 0)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def test_health_check(self) -> None:
        with urlopen(f"{self.base_url}/health") as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(data["status"], "healthy")
            self.assertEqual(data["service"], "api")

    def test_list_items(self) -> None:
        with urlopen(f"{self.base_url}/items") as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertIsInstance(data, list)
            self.assertGreaterEqual(len(data), 2)

    def test_get_item_success(self) -> None:
        with urlopen(f"{self.base_url}/items/1") as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(data["id"], 1)
            self.assertEqual(data["name"], "Item One")

    def test_get_item_not_found(self) -> None:
        with self.assertRaises(HTTPError) as ctx:
            urlopen(f"{self.base_url}/items/9999")
        self.assertEqual(ctx.exception.code, 404)

    def test_create_item_success(self) -> None:
        payload = json.dumps({"name": "New Test Item", "status": "active"}).encode("utf-8")
        req = Request(f"{self.base_url}/items", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req) as response:
            self.assertEqual(response.status, 201)
            data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(data["name"], "New Test Item")
            self.assertIn("id", data)

    def test_create_item_missing_name(self) -> None:
        payload = json.dumps({"status": "active"}).encode("utf-8")
        req = Request(f"{self.base_url}/items", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req)
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
