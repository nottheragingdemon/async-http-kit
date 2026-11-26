"""python -m asynchttp URL [URL ...]   (or the `asynchttp` command): fetch many URLs in parallel and print one line each."""
import argparse, asyncio, sys
from . import gather


def main(argv=None):
    p = argparse.ArgumentParser(prog="asynchttp", description="fetch many URLs in parallel")
    p.add_argument("urls", nargs="+")
    p.add_argument("-c", "--concurrency", type=int, default=10)
    p.add_argument("--per-host", type=int, help="max simultaneous requests to one host")
    p.add_argument("-r", "--retries", type=int, default=0)
    p.add_argument("--body", action="store_true", help="print response bodies instead of the summary line")
    a = p.parse_args(argv)
    rs = asyncio.run(gather(a.urls, a.concurrency, a.retries, per_host=a.per_host))
    for r in rs:
        print(r.text() if a.body else f"{r.status}\\t{r.elapsed:.2f}s\\t{r.url}" + (f"\\t{r.error}" if r.error else ""))
    return 0 if all(r.ok for r in rs) else 1


if __name__ == "__main__":
    sys.exit(main())
