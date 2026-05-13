---
phase: 30
plan: "02"
status: complete
tags: [bug-fix, nan, json, chart, sgx]
key-files:
  modified:
    - webapp.py
  created:
    - tests/test_unit_chart_nan.py
commits:
  - b311c41
---

# Plan 30-02: Chart NaN Fix for SGX Tickers

Fixed invalid JSON serialisation bug where trailing NaN OHLCV rows from yfinance SGX intraday data caused `json.dumps` to emit literal `NaN` tokens, crashing browser `JSON.parse` and leaving the price chart blank.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Drop NaN rows in `get_price_history` route | b311c41 | webapp.py |
| 2 | Drop NaN rows in `/api/trading_indicators` route | b311c41 | webapp.py |
| 3 | Unit tests — mock trailing NaN row, verify JSON valid | b311c41 | tests/test_unit_chart_nan.py |

## Changes Made

- `webapp.py`: `df = df.dropna(subset=["Open","High","Low","Close"])` applied after each `fetch_ohlcv` call. All-NaN result returns `{"error": "No price data available"}` with HTTP 200 instead of crashing.
- `tests/test_unit_chart_nan.py`: 5 tests — valid JSON (no literal NaN), response parseable, NaN row excluded from dates, all-NaN returns 200+error, clean DF unaffected.

## Verification

All 5 tests in `tests/test_unit_chart_nan.py` pass.

## Self-Check: PASSED
