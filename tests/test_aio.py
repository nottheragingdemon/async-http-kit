"""asynchttp.aio.AsyncHTTPClient against a local server (skipped when aiohttp is not installed)."""
import json, threading, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    from asynchttp.aio import AsyncHTTPClient
except ImportError:   # aiohttp missing
    AsyncHTTPClient = None


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        self._send(404 if "missing" in self.path else 200, {"path": self.path})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        self._send(200, {"got": json.loads(self.rfile.read(n) or b"{}")})


@unittest.skipIf(AsyncHTTPClient is None, "aiohttp not installed")
class AioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def test_mixed_batch(self):
        res = AsyncHTTPClient(timeout=5).execute([
            {"_id": "a", "method": "get", "url": self.base + "/x", "params": {"q": "1"}},
            {"_id": "b", "method": "post", "url": self.base + "/y", "data": {"k": 2}},
            {"_id": "c", "method": "get", "url": self.base + "/missing"},
            {"_id": "d", "method": "get", "url": "http://127.0.0.1:9/"},
            {"_id": "e", "method": "get"},
        ])
        by = {r["id"]: r for r in res}
        self.assertEqual(by["a"]["body"]["path"], "/x?q=1")
        self.assertEqual(by["b"]["body"]["got"], {"k": 2})
        self.assertEqual((by["c"]["status_code"], by["c"]["success"]), (404, False))
        self.assertIsNone(by["d"]["status_code"]); self.assertEqual(by["d"]["error"]["type"], "ClientConnectorError")
        self.assertEqual(by["e"]["error"]["message"], "URL is required")


if __name__ == "__main__":
    unittest.main()
