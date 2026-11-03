"""Two-origin local privacy experiment fixture.

Run with: python scripts/lab_server.py
First-party: http://127.0.0.1:8780
Third-party: http://127.0.0.1:8781
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


events: list[dict[str, str]] = []
lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    server_version = "SOVRIVA-Lab/0.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        event = {"host": self.headers.get("Host", ""), "path": parsed.path}
        with lock:
            events.append(event)
        if parsed.path == "/report":
            with lock:
                body = json.dumps(events).encode()
            self._send(200, "application/json", body)
            return
        if self.server.server_address[1] == 8780:
            body = b"""<!doctype html><html><head><meta charset='utf-8'><title>SOVRIVA Lab</title></head>
<body><h1>SOVRIVA Privacy Experiment</h1><p>Essential content should remain available.</p>
<script src='http://127.0.0.1:8780/essential.js'></script>
<script src='http://127.0.0.1:8781/analytics.js'></script>
<script src='http://127.0.0.1:8781/ad-like.js'></script>
<img src='http://127.0.0.1:8781/tracker.gif' alt='fixture pixel'>
<div class='sovriva-ad-slot'>Advertisement-like fixture slot</div></body></html>"""
            content_type = "text/html; charset=utf-8"
        elif parsed.path.endswith(".js"):
            body = b"window.sovrivaLab = { loaded: true };"
            content_type = "application/javascript"
        elif parsed.path.endswith(".gif"):
            body = b"GIF89a"
            content_type = "image/gif"
        else:
            body = b"ok"
            content_type = "text/plain"
        self._send(200, content_type, body)


def main() -> None:
    first = ThreadingHTTPServer(("127.0.0.1", 8780), Handler)
    third = ThreadingHTTPServer(("127.0.0.1", 8781), Handler)
    threading.Thread(target=first.serve_forever, daemon=True).start()
    threading.Thread(target=third.serve_forever, daemon=True).start()
    print("SOVRIVA lab: first-party http://127.0.0.1:8780")
    print("SOVRIVA lab: third-party http://127.0.0.1:8781")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        first.shutdown()
        third.shutdown()


if __name__ == "__main__":
    main()
