#!/usr/bin/env python3
"""Tiny CORS-enabled static server so the embedded browser can fetch eval job files.
Dev utility for browser-driven eval runs; serves the repo root on :8765."""
import http.server


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_PUT(self):
        # Only allow writes into eval/runs/ so the browser can save transcripts.
        rel = self.path.lstrip("/")
        if not rel.startswith("eval/runs/") or ".." in rel:
            self.send_response(403)
            self.end_headers()
            return
        body = self.rfile.read(int(self.headers["Content-Length"]))
        import pathlib
        p = pathlib.Path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
        self.send_response(200)
        self.end_headers()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    http.server.HTTPServer(("127.0.0.1", port), Handler).serve_forever()
