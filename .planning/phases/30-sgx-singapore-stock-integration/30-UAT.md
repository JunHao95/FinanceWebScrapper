---
status: diagnosed
phase: 30-sgx-singapore-stock-integration
source: 30-CONTEXT.md, 30-02-PLAN.md, 30-03-PLAN.md, 30-04-PLAN.md
started: 2026-05-13T00:00:00Z
updated: 2026-05-13T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. SGX Ticker Loads Without Error
expected: Enter D05.SI in the ticker input and submit. The page loads successfully — stock data appears (company name, price, market cap, etc.) without a crash or blank screen. Metadata shows SGD currency and SGX exchange somewhere on the page.
result: pass

### 2. Price Chart Renders for SGX Ticker
expected: After loading D05.SI, the candlestick price chart displays correctly. No error message like "Failed to load chart" or blank chart area. Chart shows historical OHLCV bars for DBS Bank.
result: pass

### 3. DCF Valuation Uses S$ and Singapore Defaults
expected: Open the DCF Valuation section for D05.SI. The currency symbol shows "S$" (not "$"). The default WACC input is 8% (not 10%) and the terminal growth rate g2 is 3%.
result: issue
reported: "there is no DCF"
severity: major

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
result: pass

## Summary

total: 8
passed: 5
issues: 3
pending: 0
skipped: 0

## Gaps

- truth: "DCF Valuation section renders for D05.SI with S$ currency and Singapore defaults (WACC 8%, g1 7%, g2 3%)"
  status: failed
  reason: "User reported: there is no DCF"
  severity: major
  test: 3
  root_cause: "querySelector('#deep-analysis-content-D05.SI') fails — dot in CSS selector parsed as class separator, not literal; container is null so DCFValuation.renderIntoGroup returns early"
  artifacts:
    - path: "static/js/dcfValuation.js:226"
      issue: "querySelector with unescaped ticker containing dot"
    - path: "static/js/peerComparison.js:218"
      issue: "same querySelector bug — shared root cause with Test 4"
    - path: "static/js/earningsQuality.js:147"
      issue: "same querySelector bug"
  missing:
    - "Escape dots in ticker before passing to querySelector, or switch to getElementById"
  debug_session: ""

- truth: "Peer Comparison section shows a clear unavailable message for SGX tickers (not blank/missing)"
  status: failed
  reason: "User reported: the peer comparison detail is missing"
  severity: major
  test: 4
  root_cause: "Same querySelector dot bug as Test 3 — peerComparison.js:218 uses querySelector('#deep-analysis-content-D05.SI') which fails CSS parsing. PeerComparison.renderIntoGroup returns early at null container check. The unavailable message logic in _fetchAndRender never executes because the container lookup fails before any fetch."
  artifacts:
    - path: "static/js/peerComparison.js:218"
      issue: "querySelector with unescaped ticker dot"
  missing:
    - "Same fix as Test 3: escape dot in ticker for querySelector"
  debug_session: ""

- truth: "Sentiment analysis returns at least some news articles (> 0) for D05.SI using company name search"
  status: failed
  reason: "User reported: there is no sentiment data — News Articles Analyzed: 0, FinBERT News Score: --, Overall Sentiment Label: No Data"
  severity: major
  test: 7
  root_cause: "search_terms = ['d05.si', 'dbs group holdings ltd', 'd05'] — articles say 'DBS' or 'DBS Group', not the full legal name. Line 168 filter `any(term in text_to_search for term in search_terms)` fails for all RSS feeds. Google News URL ANDs all terms together → poor query, and articles still filtered by full name. First word of resolved_name ('dbs') never added to search_terms."
  artifacts:
    - path: "src/sentiment/sentiment_analyzer.py:128-135"
      issue: "search_terms built with full legal name; no short-name variant added"
    - path: "src/sentiment/sentiment_analyzer.py:168"
      issue: "filter requires full legal name to appear in article text — too strict"
    - path: "src/sentiment/sentiment_analyzer.py:142-144"
      issue: "Google News URL AND-joins all search terms including ticker; should use just company name"
  missing:
    - "Extract first word(s) of resolved_name and add as search term (e.g. 'dbs' from 'DBS Group Holdings Ltd')"
    - "Google News URL should use only company name, not ticker+name"
  debug_session: ""
