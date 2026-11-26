import json, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

COUNTS = {}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _reply(self, code, body=b"", headers=None):
        self.send_response(code)
        for k, v in (headers or {}).items(): self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def do_GET(self): self.route()
    def do_POST(self): self.route()

    def route(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        if u.path == "/slow":
            time.sleep(float(q.get("d", ["0.3"])[0])); self._reply(200, b"slow")
        elif u.path == "/echo":
            n = int(self.headers.get("Content-Length") or 0)
            self._reply(200, json.dumps({"method": self.command, "body": self.rfile.read(n).decode(), "ctype": self.headers.get("Content-Type")}).encode(), {"Content-Type": "application/json"})
        elif u.path == "/flaky":      # fails `fail` times per key, then works
            key = q.get("k", ["a"])[0]; COUNTS[key] = COUNTS.get(key, 0) + 1
            if COUNTS[key] <= int(q.get("fail", ["2"])[0]):
                self._reply(int(q.get("code", ["503"])[0]), b"no", {"Retry-After": "0"})
            else:
                self._reply(200, b"ok")
        elif u.path == "/missing": self._reply(404, b"nope")
        else: self._reply(200, b"ok")


def start():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"
