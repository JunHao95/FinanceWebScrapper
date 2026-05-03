---
phase: 26-ml-finance-notebook-integration
plan: "02"
status: complete
date: 2026-05-03
---

# Phase 26-02 Summary — ml_signals.py Implementation

## What was built

Created `src/analytics/ml_signals.py` (new file, ~310 lines) with five compute functions:

| Function | Model | Status |
|---|---|---|
| `compute_ml_direction_signal` | RandomForestClassifier (n=50, depth=5) | ✅ |
| `compute_pca_decomposition` | PCA + StandardScaler, top 3 PCs | ✅ |
| `compute_kmeans_regime` | KMeans (k=4) + HMM side-by-side | ✅ |
| `compute_credit_risk_score` | RandomForestClassifier (n=50, depth=4) | ✅ |
| `compute_lstm_direction_signal` | Keras LSTM(64) + Dense, env-gated | ✅ |

## Key design decisions

- **Chronological split** (`shuffle=False`) enforced in all supervised paths via `X.iloc[:split_idx]` / `X.iloc[split_idx:]`
- **Scaler fit on train only** — `scaler.fit_transform(X_train)`, then `scaler.transform(X_latest)` — anti-leakage rule from M1
- **Credit risk synthetic peers** centred on input ratios with `std_de = max(2 * debt_to_equity, 0.2)` — ensures degenerate-label detection for ultra-low-leverage companies (expected design, not a bug)
- **KERAS_AVAILABLE** module-level flag: gated at function entry, never imports TF on `False` path
- **Numpy → Python builtins** via `.tolist()` on arrays, `float()` on scalars throughout
- **PCA variance_explained** always padded to length 3 with 0.0 — handles 2-ticker case

## Test results

```
tests/test_unit_ml_signals.py — 10 passed (including LSTM, Keras available locally)
```

All 10 unit tests GREEN. Import smoke test confirms all exports available.
