---
plan: "16-01"
phase: "16-peer-comparison"
status: complete
tasks_completed: 2
tasks_total: 2
---

# Plan 16-01 Summary: Peer Comparison Backend

## What Was Built

- `src/scrapers/finviz_scraper.py` — Added `get_peer_data(ticker)` method to `FinvizScraper`. Parses the "Similar" section from Finviz's snapshot table using BeautifulSoup, extracts up to 10 peer tickers, then calls `_scrape_data()` for each to collect P/E, P/B, ROE, and Operating Margin. Includes the primary ticker as the first row. Returns `{sector, peers, peer_data}`.

- `webapp.py` — Added `_peer_cache` (sector-scoped TTL dict) and `_ticker_sector_map` (ticker→sector lookup). Added `GET /api/peers?ticker=AAPL` route that short-circuits on warm cache, computes nearest-rank percentiles for all 4 metrics, and returns the full response shape. Failure states (< 2 peers, network exception) return `{error: ...}` with HTTP 200.

- `tests/test_peer_comparison.py` — 5 pytest tests: shape validation, percentile range check, cache-hit (mock called only once), fewer-than-2-peers failure, network exception failure. All pass GREEN.

## Key Decisions

- Added `_ticker_sector_map` alongside `_peer_cache` so the second request with the same ticker bypasses `get_peer_data()` entirely rather than calling it to discover the sector before checking the cache.
- Cache fixture reset (both dicts) moved to the `client` pytest fixture so each test starts with a clean slate.

## Verification

```
python -m pytest tests/test_peer_comparison.py -v
# 5 passed in 0.83s
```

## Key Files

### Created
- `tests/test_peer_comparison.py`

### Modified
- `src/scrapers/finviz_scraper.py` — added `get_peer_data()`
- `webapp.py` — added `_peer_cache`, `_ticker_sector_map`, `GET /api/peers`
- `README.md` — added Peer Comparison section

## Commits
- `1e2a101` test(16-01): write TDD scaffold for /api/peers — RED state
- `0e486a1` feat(16-01): add /api/peers route and FinvizScraper.get_peer_data()
