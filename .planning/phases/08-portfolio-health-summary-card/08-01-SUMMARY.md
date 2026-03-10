---
phase: 08-portfolio-health-summary-card
plan: "01"
subsystem: backend-api
tags: [flask, sharpe, yfinance, tdd, portfolio]
dependency_graph:
  requires: []
  provides: ["/api/portfolio_sharpe route", "tests/test_portfolio_sharpe.py"]
  affects: [webapp.py]
tech_stack:
  added: []
  patterns: ["Flask route POST", "yfinance ^IRX rf-rate fetch", "weighted log-return Sharpe computation"]
key_files:
  created:
    - tests/test_portfolio_sharpe.py
  modified:
    - webapp.py
decisions:
  - "Import pandas as pd locally inside route body (not at module level) — consistent with existing local-import pattern in webapp.py"
  - "Route appended before /health endpoint — keeps error handlers at bottom of file"
  - "Pre-existing test_spy_march_2020_is_stressed failure confirmed as pre-existing, not caused by this plan"
metrics:
  duration: "~6 min"
  completed_date: "2026-03-10"
  tasks_completed: 2
  files_changed: 2
---

# Phase 8 Plan 01: Portfolio Sharpe Backend Route Summary

**One-liner:** POST /api/portfolio_sharpe computes annualized portfolio Sharpe via weighted yfinance log-returns, with ^IRX rf-rate fetch and silent 0.0 fallback.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write test scaffold for /api/portfolio_sharpe (RED) | 6c7bd3c | tests/test_portfolio_sharpe.py (created) |
| 2 | Add /api/portfolio_sharpe Flask route to webapp.py (GREEN) | 29febde | webapp.py (modified) |

## What Was Built

### `/api/portfolio_sharpe` Flask route (webapp.py line 1895)

- Accepts POST body: `{ tickers, weights, start_date, end_date }`
- Fetches current 3-month T-bill rate via `yf.Ticker('^IRX').history(period='5d')`, divides by 100 to convert percent to decimal; falls back silently to `rf_rate=0.0` on any exception
- Downloads OHLCV data via `yf.download(tickers, ...)['Close']`; coerces single-ticker `pd.Series` result to `pd.DataFrame` before weight multiplication (guard against yfinance Series collapse)
- Builds weight vector from input dict; normalizes; applies equal-weight fallback for any ticker absent from weights
- Computes weighted daily log-returns, annualizes mean and vol (x252), calculates Sharpe = (ann_ret - rf_rate) / ann_vol
- Returns `{ sharpe: float, rf_rate: float, period: "YYYY-MM-DD to YYYY-MM-DD" }` on success, or `{ error: str }` with status 500 on exception

### `tests/test_portfolio_sharpe.py` (3 tests)

- `test_portfolio_sharpe_missing_tickers` — empty body returns 200 or 500 gracefully
- `test_portfolio_sharpe_returns_keys` — multi-ticker returns all three keys
- `test_portfolio_sharpe_single_ticker` — single ticker returns numeric sharpe (no error key)
- All marked `@pytest.mark.slow` for network-aware CI skipping
- Local `client` fixture (not added to conftest.py to avoid touching existing test infrastructure)

## Verification Results

```
pytest tests/test_portfolio_sharpe.py -q -m slow
3 passed in 1.36s

grep portfolio_sharpe webapp.py
1895:@app.route('/api/portfolio_sharpe', methods=['POST'])
1896:def portfolio_sharpe():
1949:        logger.error(f"Error in portfolio_sharpe: {e}")

pytest tests/ -q --ignore=tests/test_portfolio_sharpe.py
1 failed (pre-existing), 61 passed — no regressions
```

The pre-existing failure (`test_spy_march_2020_is_stressed`) is unrelated to this plan — confirmed present before any changes.

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

**Note on `pd` import:** The plan comment said "pd is already imported in webapp.py — confirm before adding". Inspection found pandas was only imported locally inside other route functions (not at module level). Added `import pandas as pd` inside the route body alongside `import yfinance as yf` and `import numpy as np`, consistent with the existing local-import pattern at lines 1323 and 1353.

## Self-Check: PASSED

- tests/test_portfolio_sharpe.py: FOUND
- webapp.py route: FOUND at line 1895
- Commit 6c7bd3c: FOUND (test RED phase)
- Commit 29febde: FOUND (route GREEN phase)
