# Changelog

## 0.3.1
- `scripts/install.sh`: the smoke test now runs in isolated mode, so it checks the installed package and not a copy in the current folder. Before, running the script from inside a clone printed the clone's version instead of the version it had just installed.
- Behaviour change from 0.3.0: none (the library code is unchanged).

## 0.3.0
- `gather(..., per_host=N)`: at most N simultaneous requests to the same host, so one server is never flooded while others run at full speed.
- Command line: `asynchttp URL [URL ...] [-c N] [--per-host N] [-r N] [--body]`, also `python -m asynchttp`.
- Behaviour change from 0.2.0: none (the new options are off by default).

## 0.2.0
- Retries: `Req(retries=N)` / `gather(..., retries=N)` retry on 429, 5xx and network errors, waiting for `Retry-After` or an exponential backoff with jitter. `Response.attempts` says how many tries were used.
- Behaviour change from 0.1.0: none unless `retries` is set (default 0).

## 0.1.0
- `request()` and `gather()`: run many requests in parallel with a concurrency limit; results keep input order.
- HTTP error statuses and network errors never raise: check `Response.ok` / `Response.error`.
