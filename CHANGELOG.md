# Changelog

## 0.1.0
- `request()` and `gather()`: run many requests in parallel with a concurrency limit; results keep input order.
- HTTP error statuses and network errors never raise: check `Response.ok` / `Response.error`.
