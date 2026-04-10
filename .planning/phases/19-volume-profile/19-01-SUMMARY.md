---
phase: 19-volume-profile
plan: 01
status: completed
---

# Plan 01 Summary — Volume Profile Backend

## What was built
- Replaced `compute_volume_profile` stub in `src/analytics/trading_indicators.py` with a full implementation:
  - Proportional-overlap volume distribution across adaptive bins (n_bins clamped [20, 200])
  - POC = bin with maximum accumulated volume
  - Value area: greedy expansion from POC until ≥70% of total volume captured; VAH = max center, VAL = min center
  - Signal: `'inside'` if latest close is between VAL and VAH, else `'outside'`
  - Plotly `make_subplots(rows=1, cols=2, shared_yaxes=True)` — candlestick left, horizontal bar histogram right
  - POC/VAH/VAL shapes on histogram subplot using `xref='x2', yref='y2'`
  - Template stripped from `fig.to_dict()` to save ~7 KB
  - All scalars cast to Python `float`/`round()`
- Updated `webapp.py` `/api/trading_indicators` route to call `compute_volume_profile(df, ticker, lookback)` (not stub)
- Added `plotly>=5.0.0` to `requirements.txt`
- Added `TestComputeVolumeProfile` class (5 tests) to `tests/test_trading_indicators.py`

## Verification
- 9/9 tests green (`test_trading_indicators.py`)
- Full suite: 85 passed, 0 regressions
- `grep "compute_volume_profile" src/analytics/trading_indicators.py` — real implementation present
- `grep "plotly" requirements.txt` — plotly>=5.0.0 present

## Key fix during execution
`_synthetic_ohlcv()` in test file had index alignment bug — Series with RangeIndex assigned to DataFrame with DatetimeIndex produced NaN. Fixed by using `.values` (numpy array) for column data.
