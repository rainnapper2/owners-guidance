"""CLI client for interacting with the Python API service."""

import argparse
import json
import sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


class APIClient:
    """API client helper for communicating with the server."""

    def __init__(self, base_url: str = "http://127.0.0.1:8080") -> None:
        self.base_url = base_url.rstrip("/")

    def health(self) -> dict:
        return self._request("GET", "/health")

    def list_items(self) -> list:
        return self._request("GET", "/items")

    def get_item(self, item_id: int) -> dict:
        return self._request("GET", f"/items/{item_id}")

    def create_item(self, name: str, status: str = "active") -> dict:
        return self._request("POST", "/items", data={"name": name, "status": status})

    def _request(self, method: str, endpoint: str, data: dict | None = None) -> dict | list:
        url = f"{self.base_url}{endpoint}"
        payload = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {"Content-Type": "application/json"} if payload else {}

        req = Request(url, data=payload, headers=headers, method=method)
        try:
            with urlopen(req) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_body)
                raise RuntimeError(f"HTTP {e.code}: {err_json.get('error', e.reason)}")
            except json.JSONDecodeError:
                raise RuntimeError(f"HTTP {e.code}: {e.reason}")
        except URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}")


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for CLI client."""
    parser = argparse.ArgumentParser(description="CLI Client for Demo REST API")
    parser.add_argument("--url", default="http://127.0.0.1:8080", help="Base URL of the API server")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to execute")

    # health command
    subparsers.add_parser("health", help="Check server health")

    # list command
    subparsers.add_parser("list", help="List all items")

    # get command
    get_parser = subparsers.add_parser("get", help="Get item by ID")
    get_parser.add_argument("--id", type=int, required=True, help="Item ID")

    # create command
    create_parser = subparsers.add_parser("create", help="Create a new item")
    create_parser.add_argument("--name", type=str, required=True, help="Item name")
    create_parser.add_argument("--status", type=str, default="active", help="Item status")

    return parser


def main(args: list[str] | None = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args)
    client = APIClient(base_url=parsed.url)

    try:
        if parsed.command == "health":
            result = client.health()
        elif parsed.command == "list":
            result = client.list_items()
        elif parsed.command == "get":
            result = client.get_item(parsed.id)
        elif parsed.command == "create":
            result = client.create_item(parsed.name, parsed.status)
        else:
            parser.print_help()
            return 1

        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
