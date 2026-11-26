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


if __name__ == "__main__":
    unittest.main()
