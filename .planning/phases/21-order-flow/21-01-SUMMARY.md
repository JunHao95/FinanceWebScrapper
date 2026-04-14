---
phase: 21-order-flow
plan: 01
status: completed
date: 2026-04-12
---

# Plan 21-01 Summary — Order Flow Backend

## What was built
- `compute_order_flow(df, ticker, lookback)` in `src/analytics/trading_indicators.py` replaces the stub
- 7-test `TestComputeOrderFlow` class added to `tests/test_trading_indicators.py`
- `webapp.py` import extended and route wired to call `compute_order_flow`

## Key implementation details
- Epsilon guard: `ranges = (df['High'] - df['Low']).clip(lower=1e-9)` prevents divide-by-zero on doji bars
- Delta: `(2 * buy_ratio - 1) * Volume` — positive = buy pressure, negative = sell pressure
- Cumulative delta: `delta.cumsum()`, serialised via `_safe_list()` for NaN-safe JSON
- Divergence: `price_slope * vol_slope < 0` over last 10 bars using `np.polyfit`
- Imbalance: `body_ratio > 0.70 AND volume > 1.2 × rolling(20).mean()` → `▲`/`▼` annotations
- Dual-axis layout: Bar on `yaxis='y'`, Scatter on `yaxis='y2'` with `overlaying='y', side='right'`
- Signal derived from cumulative delta slope (bullish / bearish / neutral)

## Test results
```
7 passed in 1.38s  (TestComputeOrderFlow)
74 passed, 1 pre-existing failure in test_regime_detection (unrelated)
```

## API output shape
```json
{
  "order_flow": {
    "traces":  [...],
    "layout":  {...},
    "signal":  "bullish" | "bearish" | "neutral",
    "divergence": {
      "detected":    true | false,
      "price_slope": 0.2345,
      "vol_slope":   -0.1234
    }
  }
}
```
