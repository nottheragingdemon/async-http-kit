import asyncio, os, sys, time, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from asynchttp import Req, gather, request
from tests import server

os.environ["NO_PROXY"] = "127.0.0.1"
os.environ.pop("HTTP_PROXY", None); os.environ.pop("http_proxy", None)


class Core(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.srv, cls.base = server.start()
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown()

    def test_parallel_is_faster_than_serial(self):
        t = time.monotonic()
        rs = asyncio.run(gather([f"{self.base}/slow?d=0.4"] * 8, concurrency=8))
        self.assertTrue(all(r.ok for r in rs))
        self.assertLess(time.monotonic() - t, 1.6)      # serial would take 3.2 s

    def test_concurrency_limit_and_order(self):
        urls = [f"{self.base}/slow?d=0.2&i={i}" for i in range(6)]
        t = time.monotonic()
        rs = asyncio.run(gather(urls, concurrency=2))
        self.assertGreaterEqual(time.monotonic() - t, 0.55)   # 3 rounds of 0.2 s
        self.assertEqual([r.url for r in rs], urls)

    def test_status_and_errors_do_not_raise(self):
        a, b = asyncio.run(gather([f"{self.base}/missing", "http://127.0.0.1:1/x"]))
        self.assertEqual(a.status, 404); self.assertFalse(a.ok)
        self.assertEqual(b.status, 0); self.assertIn("Error", b.error)

    def test_json_body(self):
        r = asyncio.run(request(Req(f"{self.base}/echo", "POST", json={"a": 1})))
        d = r.json()
        self.assertEqual((d["method"], d["body"], d["ctype"]), ("POST", '{"a": 1}', "application/json"))

    def test_retry_until_success(self):
        r = asyncio.run(request(Req(f"{self.base}/flaky?k=r1&fail=2", retries=3), backoff=0.01))
        self.assertTrue(r.ok); self.assertEqual(r.attempts, 3)

    def test_gives_up_and_does_not_retry_4xx(self):
        a = asyncio.run(request(Req(f"{self.base}/flaky?k=r2&fail=9", retries=1), backoff=0.01))
        self.assertEqual((a.status, a.attempts), (503, 2))
        b = asyncio.run(request(Req(f"{self.base}/missing", retries=3), backoff=0.01))
        self.assertEqual((b.status, b.attempts), (404, 1))

    def test_gather_retries_in_parallel(self):
        rs = asyncio.run(gather([f"{self.base}/flaky?k=g{i}&fail=1" for i in range(5)], retries=2, backoff=0.01))
        self.assertTrue(all(r.ok and r.attempts == 2 for r in rs))

    def test_per_host_limit(self):
        t = time.monotonic()
        asyncio.run(gather([f"{self.base}/slow?d=0.3&i={i}" for i in range(4)], concurrency=4, per_host=2))
        self.assertGreaterEqual(time.monotonic() - t, 0.55)   # 2 rounds of 0.3 s, though 4 slots were free

    def test_cli(self):
        import subprocess
        out = subprocess.run([sys.executable, "-m", "asynchttp", "-c", "2", f"{self.base}/ok", f"{self.base}/missing"],
                             capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             env={**os.environ, "NO_PROXY": "127.0.0.1"})
        self.assertEqual(out.returncode, 1)
        self.assertIn("200", out.stdout); self.assertIn("404", out.stdout)


if __name__ == "__main__":
    unittest.main()
