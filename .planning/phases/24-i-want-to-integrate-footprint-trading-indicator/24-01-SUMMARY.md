---
phase: 24-i-want-to-integrate-footprint-trading-indicator
plan: "01"
status: complete
---

# Plan 24-01 Summary — Footprint Backend

## What was built

**Task 1 — `fetch_intraday` + `compute_footprint` in `trading_indicators.py`**
- `fetch_intraday(ticker, days=60)`: mirrors `fetch_ohlcv` with `interval='15m'`, hard-caps at 60 days, strips timezone, raises `ValueError` on empty response.
- `compute_footprint(df_15m, ticker)`: epsilon-guarded buy/sell/delta formula (reused from `compute_order_flow`), adaptive price bins (reused from `compute_volume_profile`), per-day delta matrix, `go.Heatmap` + POC scatter + current-close reference line, dark theme layout. Returns `{traces, layout, signal, cum_delta, total_volume}`. Signal threshold: ±5% of total volume. Handles empty DataFrame gracefully.

**Task 2 — `compute_composite_bias` extended + `/api/footprint` route**
- `compute_composite_bias` signature extended to `(results, footprint_result=None)`. Footprint added to `sub_map`/`labels`; existing `available`/`unavailable` logic handles `signal=None` as unavailable automatically. Backward-compatible (4-voice callers unchanged).
- `GET /api/footprint` route added in `webapp.py` after `get_trading_indicators`, following the identical pattern: ticker validation, lazy import, `fetch_intraday` → `compute_footprint`, JSON response.

## Verification results

| Check | Result |
|---|---|
| `from src.analytics.trading_indicators import fetch_intraday, compute_footprint, compute_composite_bias` | PASS |
| `GET /api/footprint` (no ticker) → `{"error": "ticker parameter required"}` | PASS |
| 5-voice composite bias score → `"5/5"` | PASS |
| `compute_footprint` with synthetic DataFrame → keys `{traces,layout,signal,cum_delta,total_volume}` | PASS |
| `pytest tests/test_trading_indicators.py` (49 tests) | 49 passed |

## Files changed

- `src/analytics/trading_indicators.py` — extended `compute_composite_bias`, appended `fetch_intraday` and `compute_footprint`
- `webapp.py` — added `GET /api/footprint` route
- `tests/test_trading_indicators.py` — added `TestComputeFootprint`, `TestFootprintRoute`, `TestComputeCompositeBias5Voice` (14 new tests)
- `README.md` — Phase 24-01 section added
