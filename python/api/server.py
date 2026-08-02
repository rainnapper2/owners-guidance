"""Simple HTTP REST API using Python standard library."""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# In-memory database for demo purposes
ITEMS = {
    1: {"id": 1, "name": "Item One", "status": "active"},
    2: {"id": 2, "name": "Item Two", "status": "pending"},
}
NEXT_ID = 3


class APIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for demo REST API."""

    def _send_json(self, status_code: int, data: dict | list) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_error(self, status_code: int, message: str) -> None:
        self._send_json(status_code, {"error": message})

    def do_GET(self) -> None:
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip("/")

        if path == "/health":
            self._send_json(200, {"status": "healthy", "service": "api"})
            return

        if path == "/items":
            self._send_json(200, list(ITEMS.values()))
            return

        if path.startswith("/items/"):
            try:
                item_id = int(path.split("/")[-1])
                if item_id in ITEMS:
                    self._send_json(200, ITEMS[item_id])
                else:
                    self._send_error(404, f"Item {item_id} not found")
            except ValueError:
                self._send_error(400, "Invalid item ID format")
            return

        self._send_error(404, "Endpoint not found")

    def do_POST(self) -> None:
        global NEXT_ID
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip("/")

        if path == "/items":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self._send_error(400, "Missing request body")
                return

            body = self.rfile.read(content_length)
            try:
                payload = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_error(400, "Invalid JSON body")
                return

            if "name" not in payload:
                self._send_error(400, "Field 'name' is required")
                return

            item = {
                "id": NEXT_ID,
                "name": payload["name"],
                "status": payload.get("status", "active"),
            }
            ITEMS[NEXT_ID] = item
            NEXT_ID += 1
            self._send_json(201, item)
            return

        self._send_error(404, "Endpoint not found")

    def log_message(self, format: str, *args: tuple) -> None:
        """Suppress default stdout logging during testing."""
        pass


def run_server(host: str = "127.0.0.1", port: int = 8080) -> HTTPServer:
    """Start and return HTTP server instance."""
    server = HTTPServer((host, port), APIHandler)
    print(f"Server running on http://{host}:{port}")
    return server


if __name__ == "__main__":
    server = run_server()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()
