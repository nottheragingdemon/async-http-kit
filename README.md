# asynchttp

A tiny async HTTP kit for Python 3.10+, standard library only. Fire many requests in parallel and get the results back in order.

```python
import asyncio
from asynchttp import Req, gather

urls = [f"https://example.com/item/{i}" for i in range(50)]
responses = asyncio.run(gather(urls, concurrency=10))
for r in responses:
    print(r.status, r.url, r.error or len(r.body))

# retries (429, 5xx, network errors) and a per-host cap
asyncio.run(gather(urls, concurrency=20, per_host=4, retries=3))

# POST JSON
asyncio.run(gather([Req("https://example.com/api", "POST", json={"a": 1})]))
```

`Response` has `.status` (0 when there was no HTTP response), `.ok`, `.headers` (lower-case), `.body`, `.text()`, `.json()`, `.elapsed` and `.error`. Requests never raise for HTTP status codes or network errors.

From the shell: `asynchttp URL [URL ...] -c 10 --per-host 2 -r 3` (or `python -m asynchttp ...`).

## Install a version
```
pip install "git+https://github.com/nottheragingdemon/async-http-kit@v0.3.0"
sh scripts/install.sh            # newest release, falling back to older ones if it fails
```
Versions, rollbacks and fallbacks are described in [docs/GIT_PLAN.md](docs/GIT_PLAN.md); changes per version are in [CHANGELOG.md](CHANGELOG.md).

## Tests
```
python -m unittest discover -s . -t . -v
```
