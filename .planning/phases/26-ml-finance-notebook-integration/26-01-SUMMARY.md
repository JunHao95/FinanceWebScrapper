# Phase 26-01 Summary — ML Signals Test Scaffold

## What Was Created

### tests/test_unit_ml_signals.py (new file)
10 unit test stubs covering 5 ML features from the forthcoming `src/analytics/ml_signals.py`:

| # | Test | Feature |
|---|------|---------|
| 1 | `test_direction_signal_returns_bullish_or_bearish` | ML direction signal (happy path) |
| 2 | `test_direction_signal_insufficient_history` | ML direction signal (edge case: <100 rows) |
| 3 | `test_pca_single_ticker_returns_unavailable` | PCA decomposition (single ticker guard) |
| 4 | `test_pca_multi_ticker_returns_three_pcs` | PCA decomposition (multi-ticker happy path) |
| 5 | `test_kmeans_regime_label_valid` | K-means regime (label validation) |
| 6 | `test_kmeans_regime_hmm_compare_keys_present` | K-means regime (HMM comparison keys) |
| 7 | `test_credit_risk_score_range` | Credit risk score (probability bounds) |
| 8 | `test_credit_risk_degenerate_labels` | Credit risk score (degenerate case) |
| 9 | `test_lstm_unavailable_when_keras_missing` | LSTM signal (Keras not installed) |
| 10 | `test_lstm_returns_valid_signal_locally` | LSTM signal (Keras installed, happy path) |

Design: top-of-file try/except sets `IMPORT_OK`; every test body calls `pytest.skip()` when `IMPORT_OK is False`. All patches target `src.analytics.ml_signals.fetch_ohlcv`. LSTM test 10 is additionally `skipif` on `KERAS_AVAILABLE_GLOBALLY`.

### tests/test_integration_routes.py (appended)
Two new functions appended at end of existing file, covered by the module-level `pytestmark = pytest.mark.integration`:

- `test_ml_signals_direction_route` — patches `webapp.compute_ml_direction_signal`, asserts status 200, ticker echo, and signal validity; skips on 404 (route not yet registered).
- `test_ml_signals_missing_ticker` — asserts missing-ticker request returns an error key; skips on 404.

## Test Results

```
tests/test_unit_ml_signals.py        10 skipped (ml_signals not yet implemented)
test_ml_signals_direction_route      1 skipped  (route not yet registered)
test_ml_signals_missing_ticker       1 skipped  (route not yet registered)
tests/test_integration_routes.py     58 passed, 2 skipped, 2 pre-existing FAILED
                                     (TestSendEmail failures pre-date Phase 26)
```

No new failures introduced. All scaffold tests collected without ERROR.
