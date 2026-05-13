---
phase: 30
plan: "03"
status: complete
tags: [bug-fix, sgx, fundamentals, growth-score, health-score]
key-files:
  modified:
    - src/scrapers/yahoo_scraper.py
    - src/analytics/financial_analytics.py
    - static/js/analyticsRenderer.js
  created:
    - tests/test_unit_sgx_fundamentals.py
commits:
  - c6e8b55
---

# Plan 30-03: Financial Health & Growth Data Gaps for SGX Tickers

Fixed two data bugs: (A) `yahoo_scraper.py` never mapped `revenueGrowth`/`earningsQuarterlyGrowth` so growth score stayed 0 for SGX banks; (B) `financial_analytics.py` defaulted health score to `0` instead of `None` causing banks with no liquidity ratios to show `0.0/10` rather than N/A.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Map `revenueGrowth` → `Revenue Growth (Yahoo)`; `earningsQuarterlyGrowth` fallback | c6e8b55 | src/scrapers/yahoo_scraper.py |
| 2 | Change `financial_health_score` default `0` → `None` | c6e8b55 | src/analytics/financial_analytics.py |
| 3 | Render `N/A` card for null sub-scores in frontend | c6e8b55 | static/js/analyticsRenderer.js |
| 4 | Unit tests covering both bugs | c6e8b55 | tests/test_unit_sgx_fundamentals.py |

## Changes Made

- `yahoo_scraper.py`: Added `revenueGrowth` mapping; `earningsQuarterlyGrowth` used as fallback when `earningsGrowth` absent (annual field not provided for SGX banks).
- `financial_analytics.py`: `"financial_health_score": 0` → `"financial_health_score": None`; caller guard already present.
- `analyticsRenderer.js`: Null sub-scores rendered as N/A card, excluded from overall average.
- `tests/test_unit_sgx_fundamentals.py`: 11 tests — revenue growth mapping, quarterly fallback, health score None default, growth score non-zero from revenue data.

## Verification

All 11 tests in `tests/test_unit_sgx_fundamentals.py` pass.

## Self-Check: PASSED
