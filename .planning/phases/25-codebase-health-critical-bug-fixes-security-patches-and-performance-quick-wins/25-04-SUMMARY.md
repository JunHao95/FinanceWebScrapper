---
phase: 25-codebase-health-critical-bug-fixes-security-patches-and-performance-quick-wins
plan: 04
status: complete
completed: 2026-04-26
---

## What Was Done

**PERF-02 — HMM regime detection TTL cache**
- Added `from cachetools import TTLCache, LRUCache` to webapp.py imports
- Added `_regime_cache: TTLCache = TTLCache(maxsize=50, ttl=900)` — 15-min TTL
- Cache key: `(ticker, start_date, end_date)` for new API; `(ticker, start_dt, end_dt)` for legacy API
- Cache lookup before HMM fit; store result after `convert_numpy_types()` before return
- Eliminates 2–10s HMM fits for repeated identical requests

**PERF-03 — Bounded cache replacements**
- `_ticker_validation_cache = {}` → `TTLCache(maxsize=500, ttl=3600)` (1-hr TTL)
- `_peer_cache = {}` → `TTLCache(maxsize=30, ttl=1800)` (30-min TTL, auto-expiry)
- `_ticker_sector_map = {}` → `LRUCache(maxsize=200)` (evicts LRU after 200 tickers)
- Removed manual `now - entry['fetched_at'] < 1800` TTL check from `get_peers()` — TTLCache handles expiry automatically
- Removed `fetched_at` field from `_peer_cache` stored values; shape is now `{'data': [...], 'peers': [...]}`
- Fixed indentation of cached fast-path block (was inside removed `if fetched_at` block)

**PERF-01 — No double-fetch (confirm, not fix)**
- No code change needed; route fetches once and passes data to sub-functions

## Test Results

```
pytest tests/test_unit_codebase_health.py::test_regime_cache tests/test_unit_codebase_health.py::test_cache_bounded -v
# 2 passed

pytest tests/test_peer_comparison.py -q
# 5 passed in isolation

Full suite: 285 passed, 7 failed
# All 7 failures confirmed pre-existing before 25-04 changes:
#   test_secret_key_guard       — load_dotenv() picks up .env in test subprocess
#   test_requirements_pinned    — RED until plan 25-05
#   TestSendEmail x2            — SEC-02 allowlist blocks test email address
#   TestPeers x3 (in full suite only) — rate-limit/test-ordering issue, pass in isolation
```

## Success Criteria

- [x] test_regime_cache: PASS
- [x] test_cache_bounded: PASS
- [x] webapp.py has TTLCache for _regime_cache, _ticker_validation_cache, _peer_cache
- [x] webapp.py has LRUCache for _ticker_sector_map
- [x] All four caches have explicit maxsize bounds
- [x] 0 regressions introduced by 25-04 changes
