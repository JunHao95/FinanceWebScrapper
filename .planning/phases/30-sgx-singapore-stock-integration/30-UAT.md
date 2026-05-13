---
status: testing
phase: 30-sgx-singapore-stock-integration
source: 30-CONTEXT.md, 30-02-PLAN.md, 30-03-PLAN.md, 30-04-PLAN.md
started: 2026-05-13T00:00:00Z
updated: 2026-05-13T00:00:00Z
---

## Current Test

number: 2
name: Price Chart Renders for SGX Ticker
expected: |
  After loading D05.SI, the candlestick price chart displays correctly. No error message like "Failed to load chart" or blank chart area. Chart shows historical OHLCV bars for DBS Bank.
awaiting: user response

## Tests

### 1. SGX Ticker Loads Without Error
expected: Enter D05.SI in the ticker input and submit. The page loads successfully — stock data appears (company name, price, market cap, etc.) without a crash or blank screen. Metadata shows SGD currency and SGX exchange somewhere on the page.
result: pass

### 2. Price Chart Renders for SGX Ticker
expected: After loading D05.SI, the candlestick price chart displays correctly. No error message like "Failed to load chart" or blank chart area. Chart shows historical OHLCV bars for DBS Bank.
result: [pending]

### 3. DCF Valuation Uses S$ and Singapore Defaults
expected: Open the DCF Valuation section for D05.SI. The currency symbol shows "S$" (not "$"). The default WACC input is 8% (not 10%) and the terminal growth rate g2 is 3%.
result: [pending]

### 4. Peer Comparison Shows Unavailable Message
expected: The Peer Comparison section for D05.SI shows a clear "not available" message (e.g. "Peer comparison is not available for SGX-listed stocks. Finviz covers US exchanges only.") — NOT a generic error or spinner stuck loading.
result: issue
reported: "the peer comparison detail is missing"
severity: major

### 5. Financial Health Score Shows N/A for SGX Bank
expected: The Financial Health sub-score for D05.SI shows "N/A" (not "0.0/10"). DBS is a bank — liquidity ratios (currentRatio, quickRatio, debtToEquity) are not applicable, so the score cannot be computed.
result: pass

### 6. Growth Score is Non-Zero for D05.SI
expected: The Growth sub-score for D05.SI shows a non-zero value (e.g. 4.0/10 or similar) — NOT "0.0/10". DBS has ~3.2% revenue growth, so the score should reflect that.
result: pass

### 7. Sentiment Analysis Returns Articles for D05.SI
expected: The Sentiment section for D05.SI shows at least some "News Articles Analyzed" (> 0) and non-"--" values for News Sentiment Score or FinBERT Score. The scraper now searches by company name "DBS Group Holdings Ltd" instead of raw ticker "d05.si".
result: issue
reported: "there is no sentiment data — News Articles Analyzed: 0, FinBERT News Score: --, Overall Sentiment Label: No Data"
severity: major

### 8. US Ticker Unaffected (Regression Check)
expected: Load AAPL. Price chart renders, DCF shows "$" (not "S$"), WACC default is 10%, Peer Comparison loads normally (not showing unavailable message), and all scores appear as before. No regressions.
result: [pending]

## Summary

total: 8
passed: 3
issues: 2
pending: 3
skipped: 0

## Gaps

- truth: "Peer Comparison section shows a clear unavailable message for SGX tickers (not blank/missing)"
  status: failed
  reason: "User reported: the peer comparison detail is missing"
  severity: major
  test: 4
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Sentiment analysis returns at least some news articles (> 0) for D05.SI using company name search"
  status: failed
  reason: "User reported: there is no sentiment data — News Articles Analyzed: 0, FinBERT News Score: --, Overall Sentiment Label: No Data"
  severity: major
  test: 7
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
