"""Unit tests for CLI client."""

import io
import json
import threading
import unittest
from unittest.mock import patch

try:
    from demo.python.api.server import run_server
    from demo.python.cli.client import APIClient, main
except ImportError:
    from python.api.server import run_server
    from python.cli.client import APIClient, main


class TestCLIClient(unittest.TestCase):
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

    def test_client_health(self) -> None:
        client = APIClient(self.base_url)
        res = client.health()
        self.assertEqual(res["status"], "healthy")

    def test_client_list_items(self) -> None:
        client = APIClient(self.base_url)
        res = client.list_items()
        self.assertIsInstance(res, list)

    def test_main_health_cmd(self) -> None:
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = main(["--url", self.base_url, "health"])
            self.assertEqual(exit_code, 0)
            data = json.loads(fake_out.getvalue())
            self.assertEqual(data["status"], "healthy")

    def test_main_create_cmd(self) -> None:
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            exit_code = main(["--url", self.base_url, "create", "--name", "CLI Created Item"])
            self.assertEqual(exit_code, 0)
            data = json.loads(fake_out.getvalue())
            self.assertEqual(data["name"], "CLI Created Item")

    def test_main_error_handling(self) -> None:
        with patch("sys.stderr", new=io.StringIO()) as fake_err:
            exit_code = main(["--url", self.base_url, "get", "--id", "9999"])
            self.assertEqual(exit_code, 1)
            self.assertIn("Item 9999 not found", fake_err.getvalue())


if __name__ == "__main__":
    unittest.main()
