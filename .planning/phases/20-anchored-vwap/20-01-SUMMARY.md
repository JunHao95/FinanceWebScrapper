---
phase: 20-anchored-vwap
plan: 01
status: completed
date: 2026-04-12
---

## Summary

Replaced `compute_anchored_vwap` stub with a full implementation and wired it into the Flask route.

## What was built

- `_get_last_earnings_date(ticker)` — fetches most recent past earnings date from yfinance, returns tz-naive timestamp or None
- `_avwap_series(df_full, anchor_date, display_index)` — computes AVWAP from anchor date forward, reindexed to display window
- `_safe_list(series)` — converts pd.Series to list replacing NaN with None for JSON safety
- `compute_anchored_vwap(df, ticker, lookback)` — full implementation returning traces, layout, signal, convergence, current_price, earnings_unavailable, labels
- `webapp.py` updated: imports `compute_anchored_vwap`, adds `df_365 = fetch_ohlcv(ticker, 365)`, replaces stub

## Test results

- All 7 `TestComputeAnchoredVwap` tests GREEN
- Full suite: 95 passed, 1 pre-existing failure (test_spy_march_2020_is_stressed, unrelated)

## Key decisions

- Used `go.Figure()` (not `make_subplots`) per plan spec
- `r=120` margin for right-edge label clearance
- `earnings_unavailable=True` when earnings_ts is None or predates df window
- Convergence threshold: `abs(current_price - val) / current_price <= 0.003`
