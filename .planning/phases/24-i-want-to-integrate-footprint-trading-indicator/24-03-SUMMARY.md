---
phase: 24-i-want-to-integrate-footprint-trading-indicator
plan: "03"
status: complete
---

# Plan 24-03 Summary — Footprint Test Suite

## What was built

**tests/fixtures/footprint_15m_ohlcv.csv**
- 30-row synthetic 15m OHLCV fixture covering 2 trading dates (2024-01-02 bullish, 2024-01-03 bearish).
- Deterministic values; no live network calls.
- Produces a pinned `cum_delta = -189166.667` and `signal = 'bearish'`.

**tests/test_unit_footprint.py** (11 tests)
- `test_fetch_intraday_returns_ohlcv` — verifies tz-naive stripping and correct columns (FOOT-01).
- `test_fetch_intraday_empty_raises` — verifies `ValueError` on empty response (FOOT-01 edge).
- `test_compute_footprint_keys` — verifies all 5 return keys present (FOOT-01).
- `test_compute_footprint_empty` — verifies no exception on empty DataFrame (FOOT-01).
- `test_heatmap_trace_present` — verifies first trace type is `heatmap` (FOOT-02).
- `test_signal_logic_bullish/bearish/neutral` — verifies signal classification at extremes and midpoint (FOOT-03).
- `test_composite_5_voices` — verifies denominator is 5 with all voices available (FOOT-05).
- `test_composite_footprint_unavailable` — verifies 4-voice fallback when footprint is None (FOOT-05).
- `test_composite_footprint_dissenter` — verifies Footprint appears in dissenters when bearish vs bullish majority (FOOT-05).

**tests/test_integration_routes.py** (3 tests added — `TestFootprintRoute` class)
- `test_footprint_route_200` — mocks `fetch_intraday` + `compute_footprint`, asserts 200 and schema keys `ticker`, `signal`, `cum_delta`, `traces`.
- `test_footprint_route_missing_ticker` — no ticker param returns JSON `{error: ...}` with HTTP 200.
- `test_footprint_route_invalid_ticker` — `fetch_intraday` raises `ValueError`, asserts HTTP 500 with `error` key.

**tests/test_regression_indicators.py** (2 tests added)
- `test_footprint_cumulative_delta_regression` — pins `cum_delta` to `-189166.667` with tolerance < 1.0; any numerical drift breaks this test.
- `test_footprint_signal_on_fixture` — pins `signal = 'bearish'` on the frozen fixture.

## Verification results

| Check | Result |
|---|---|
| `pytest tests/test_unit_footprint.py -q` | 11 passed |
| `pytest tests/test_regression_indicators.py -k footprint -q` | 2 passed |
| `pytest tests/test_integration_routes.py -k footprint -q` | 3 passed |
| `pytest tests/test_unit_footprint.py tests/test_regression_indicators.py tests/test_integration_routes.py tests/test_trading_indicators.py -q` | 127 passed |

## Files changed

- `tests/fixtures/footprint_15m_ohlcv.csv` — new frozen 15m fixture (30 rows)
- `tests/test_unit_footprint.py` — new file, 11 unit tests
- `tests/test_integration_routes.py` — extended with `TestFootprintRoute` (3 tests)
- `tests/test_regression_indicators.py` — extended with 2 footprint regression tests
