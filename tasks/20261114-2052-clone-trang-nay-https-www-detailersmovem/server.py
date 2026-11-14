#!/usr/bin/env python3
"""Local backend for the cloned site: serves static files and stores form submissions.
Run:  python3 server.py [port]   -> http://127.0.0.1:8000
POST /api/form (JSON or form) -> appended to submissions.jsonl ; GET /api/submissions lists them."""
import json, os, sys, time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site_orig")
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "submissions.jsonl")

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def _json(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        path = unquote(urlsplit(self.path).path)
        ajax = path.rstrip("/").endswith("/wp-admin/admin-ajax.php")
        if path != "/api/form" and not ajax:
            return self._json({"ok": False}, 404)
        n = min(int(self.headers.get("Content-Length") or 0), 100_000)
        raw = self.rfile.read(n).decode("utf-8", "ignore")
        try:
            data = json.loads(raw)
        except Exception:
            data = {k: v[0] for k, v in parse_qs(raw).items()}
        if ajax and data.get("action") != "elementor_pro_forms_send_form":
            return self._json({"ok": False}, 404)
        data["_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        self._json({"success": True, "data": {"message": "Thank you!", "data": []}} if ajax else {"ok": True})

    def do_GET(self):
        if unquote(urlsplit(self.path).path) == "/api/submissions":
            rows = [json.loads(l) for l in open(LOG, encoding="utf-8")] if os.path.exists(LOG) else []
            return self._json(rows)
        return super().do_GET()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
