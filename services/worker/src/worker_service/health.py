from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread


def start_health_server(port: int = 8080) -> Thread:
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in {"/healthz", "/readyz"}:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok","service":"worker"}')

    def log_message(self, format: str, *args: object) -> None:
        return

