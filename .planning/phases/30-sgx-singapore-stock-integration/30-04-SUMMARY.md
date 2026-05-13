---
phase: 30
plan: "04"
status: complete
tags: [bug-fix, sgx, sentiment, company-name, yfinance]
key-files:
  modified:
    - src/scrapers/enhanced_sentiment_scraper.py
    - src/sentiment/sentiment_analyzer.py
    - README.md
  created:
    - tests/test_unit_sgx_sentiment.py
commits:
  - e429933
---

# Plan 30-04: Sentiment Company Name Query for SGX Tickers

Fixed sentiment analysis returning zero results for SGX tickers by resolving the company's human-readable name (yfinance `longName`) and injecting it into news search terms. Raw ticker `"d05.si"` returns nothing from English RSS feeds; `"DBS Group Holdings Ltd"` finds relevant articles.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add company name resolution in `enhanced_sentiment_scraper.py` | e429933 | src/scrapers/enhanced_sentiment_scraper.py |
| 2 | Add `company_name` param to `get_comprehensive_sentiment_analysis` | e429933 | src/sentiment/sentiment_analyzer.py |
| 3 | Use `company_name` in `get_news_sentiment` search terms | e429933 | src/sentiment/sentiment_analyzer.py |
| 4 | Pass `company_name` through Reddit/Trends scrapers where applicable | e429933 | src/sentiment/sentiment_analyzer.py |
| 5 | Tests — mock yfinance, verify search terms, backward compat | e429933 | tests/test_unit_sgx_sentiment.py |

## Changes Made

- `enhanced_sentiment_scraper.py`: For dotted tickers (e.g. `D05.SI`), calls `yf.Ticker(ticker).info` to get `longName`; passes as `company_name` to analyzer. Exception-safe, no new dependency.
- `sentiment_analyzer.py`: `company_name` param propagated to `get_news_sentiment`, `get_comprehensive_sentiment_analysis`. Search terms: `[ticker, company_name, base_ticker]` (e.g. `["d05.si","dbs group holdings ltd","d05"]`). Falls back to hardcoded dict for US tickers.
- `tests/test_unit_sgx_sentiment.py`: 9 tests — company name in search terms, base ticker added, US ticker backward compat, yfinance called for dotted tickers, None on failure.

## Verification

All 9 tests in `tests/test_unit_sgx_sentiment.py` pass.

## Self-Check: PASSED
