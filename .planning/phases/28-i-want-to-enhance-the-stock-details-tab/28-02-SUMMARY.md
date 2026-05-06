---
phase: 28-i-want-to-enhance-the-stock-details-tab
plan: "02"
status: complete
---

## Result

Backend data contract implemented. `/api/price_history` route live; analyst recommendation field added to scraper.

## Files Modified

- `webapp.py` — `GET /api/price_history` route at line 2555 (candlestick + volume subplots, dark Catppuccin theme, Plotly template stripped)
- `src/scrapers/yahoo_scraper.py` — `recommendationKey` extraction at line 127-129
- `tests/test_integration_routes.py` — TestPriceHistory xfail markers removed (now real passing tests)
- `tests/test_unit_price_chart.py` — TestAnalystRangeBar converted from xfail stubs to passing yfinance mock tests

## Test Results

```
70 passed, 7 xfailed   (up from 65 passed, 11 xfailed in 28-01)
TestSendEmail 2 failures: pre-existing, unrelated
```

## Next

28-03-PLAN.md — frontend `priceChart.js` module + HTML wiring
