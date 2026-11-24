"""Serve the UI and the loopback-only Java integration."""
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from agent import CaseStore, resolve
from copilot import lookup

ROOT = Path(__file__).resolve().parent


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT / "dist", **kwargs)

    def do_POST(self):
        if self.path != "/api/turn":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 8192 or self.headers.get_content_type() != "application/json":
                raise ValueError()
            data = json.loads(self.rfile.read(length))
            message, previous = data["message"], data.get("previous")
            if not isinstance(message, str) or (previous is not None and not isinstance(previous, str)):
                raise ValueError()
            from uuid import UUID
            if previous:
                previous = str(UUID(previous)).upper()
        except (ValueError, TypeError, KeyError, AttributeError):
            self.send_error(400)
            return
        result = resolve(message, previous, lookup, store.create, store.find)
        payload = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    import os
    os.environ.setdefault("RISK_SERVICE_URL", "http://127.0.0.1:8080")
    store = CaseStore(ROOT / "reviews.sqlite")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
