import asyncio, json as _json, random, time, urllib.error, urllib.request
from dataclasses import dataclass, field


@dataclass
class Req:
    url: str
    method: str = "GET"
    headers: dict = field(default_factory=dict)
    json: object = None
    data: bytes | None = None
    timeout: float = 30.0
    retries: int = 0                 # extra attempts after the first (429, 5xx and network errors)


@dataclass
class Response:
    url: str
    status: int = 0                 # 0 = no HTTP response (network error or timeout); see .error
    headers: dict = field(default_factory=dict)   # lower-case names
    body: bytes = b""
    elapsed: float = 0.0
    error: str | None = None
    attempts: int = 1

    @property
    def ok(self):
        return 200 <= self.status < 300

    def text(self, encoding="utf-8"):
        return self.body.decode(encoding, "replace")

    def json(self):
        return _json.loads(self.body)


def _send(r: Req) -> Response:
    """one blocking request; runs in a worker thread so many can be in flight at once"""
    t0 = time.monotonic()
    body, headers = r.data, dict(r.headers)
    if r.json is not None:
        body = _json.dumps(r.json).encode()
        headers.setdefault("Content-Type", "application/json")
    headers.setdefault("User-Agent", "asynchttp")
    req = urllib.request.Request(r.url, data=body, headers=headers, method=r.method)
    try:
        with urllib.request.urlopen(req, timeout=r.timeout) as f:
            return Response(r.url, f.status, {k.lower(): v for k, v in f.headers.items()}, f.read(), time.monotonic() - t0)
    except urllib.error.HTTPError as e:
        return Response(r.url, e.code, {k.lower(): v for k, v in e.headers.items()}, e.read(), time.monotonic() - t0)
    except Exception as e:   # DNS, refused, timeout ...
        return Response(r.url, 0, {}, b"", time.monotonic() - t0, f"{type(e).__name__}: {e}")


def _as_req(x) -> Req:
    return x if isinstance(x, Req) else Req(x)


RETRY_STATUS = {429, 500, 502, 503, 504}


def _delay(resp: Response, attempt: int, backoff: float) -> float:
    ra = resp.headers.get("retry-after", "")
    if ra.strip().isdigit():                       # the server said how long to wait
        return min(float(ra), 60.0)
    return backoff * (2 ** attempt) * (0.5 + random.random())   # exponential backoff with jitter


async def request(req, *, backoff: float = 0.5, **overrides) -> Response:
    """Send one request (a URL string or a Req). Never raises for HTTP status codes or network errors: check .ok / .error.
    With retries=N it tries again (up to N more times) on 429, 5xx and network errors, waiting Retry-After or an exponential backoff."""
    r = _as_req(req)
    if overrides:
        r = Req(**{**r.__dict__, **overrides})
    resp = await asyncio.to_thread(_send, r)
    for attempt in range(r.retries):
        if resp.status != 0 and resp.status not in RETRY_STATUS:
            break
        await asyncio.sleep(_delay(resp, attempt, backoff))
        resp = await asyncio.to_thread(_send, r)
        resp.attempts = attempt + 2
    return resp


async def gather(requests, concurrency: int = 10, retries: int | None = None, backoff: float = 0.5) -> list[Response]:
    """Run many requests in parallel (at most `concurrency` at a time). Results keep the input order.
    `retries` (if given) overrides each request's own retry count."""
    sem = asyncio.Semaphore(concurrency)

    async def one(x):
        async with sem:
            return await request(x, backoff=backoff, **({} if retries is None else {"retries": retries}))

    return list(await asyncio.gather(*(one(x) for x in requests)))
