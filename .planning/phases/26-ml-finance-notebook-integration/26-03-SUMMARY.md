---
phase: 26-ml-finance-notebook-integration
plan: "03"
status: complete
date: 2026-05-03
---

# Phase 26-03 Summary — Flask Route Registration

## What was built

Added `GET /api/ml_signals` route to `webapp.py` (inserted after `/api/trading_indicators`, before `/api/footprint`).

## Route behaviour

| Query | Response |
|---|---|
| `?ticker=AAPL&feature=direction` | `{ticker, feature, signal, confidence, traces, layout}` |
| `?ticker=AAPL&feature=regime` | `{ticker, feature, current_regime, hmm_regime, models_agree, ...}` |
| `?ticker=AAPL&feature=credit` | `{ticker, feature, p_distress, top_factors, caveat}` |
| `?ticker=AAPL&feature=lstm` (cloud) | `{ticker, feature, lstm_available: false}` |
| `?tickers=AAPL&tickers=MSFT&feature=pca` | `{pca_available, variance_explained, scree_traces, heatmap_traces}` |
| No ticker | `{error: "ticker parameter required"}` |
| Unknown feature | `{error: "Unknown feature '...'"}` |

## Key implementation notes

- Lazy import of `src.analytics.ml_signals` inside route body — same pattern as `/api/trading_indicators`
- `is_cloud_environment()` guard on LSTM path before any Keras reference
- `convert_numpy_types()` applied to all responses
- Credit route passes `{}` ratios dict — `compute_credit_risk_score` handles missing keys via `.get()` fallbacks (ratio integration deferred to future phase)

## Test results

```
test_ml_signals_direction_route  PASSED
test_ml_signals_missing_ticker   PASSED
```

Route confirmed at `/api/ml_signals` via `webapp.app.url_map`.
