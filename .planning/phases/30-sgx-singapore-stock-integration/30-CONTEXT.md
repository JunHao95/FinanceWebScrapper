# Phase 30: SGX Singapore Stock Integration — Context

**Drafted:** 2026-05-12
**Status:** Complete

<domain>
## Phase Boundary

Add first-class support for SGX-listed stocks (Yahoo Finance `.SI` suffix, e.g. `D05.SI` = DBS Bank) in the webapp. Users in Singapore should be able to enter a local ticker and receive meaningful data, analytics, and display with correct currency (SGD) and market context (Straits Times Index benchmark).

The fix is layered across four areas:
1. **Scraper pipeline** — Google Finance scraper was hardcoded to `:NASDAQ`/`:NYSE`; now detects `.SI` and tries `:SGX` first. Yahoo scraper now surfaces `Currency` and `Stock Exchange` metadata from yfinance.
2. **Analytics** — Regression benchmark was hardcoded to `SPY`; now auto-selects `^STI` for `.SI` tickers via `get_exchange_info()`.
3. **Peer comparison** — Finviz covers US exchanges only; `/api/peers` now returns `{available: false, reason: "..."}` immediately for non-US tickers without calling Finviz.
4. **Frontend** — DCF valuation: currency symbol is now dynamic (`S$` for SGD), and WACC/growth defaults are adjusted for Singapore (8%/3% vs 10%/3% for US).

**Explicitly out of scope:**
- Full internationalization for all markets (`.HK`, `.L`, `.AX`, `.T` etc.)
- Adjusting P/E scoring thresholds per country
- FX-adjusted portfolio VaR across multi-currency portfolios
- Currency conversion in price displays beyond DCF

The `src/utils/exchange_utils.py` utility is designed as an **extension point**: adding support for `.HK` or `.L` later requires adding one dict entry to `_EXCHANGE_MAP`.

</domain>

<decisions>
## Implementation Decisions

### Exchange detection
- `get_exchange_info(ticker)` inspects the suffix after the last `.` (e.g. `D05.SI` → suffix `SI`)
- Lookup table `_EXCHANGE_MAP` maps suffix → exchange metadata
- Unknown/US tickers return `_US_DEFAULTS` (`SPY`, `$`, `is_us=True`)

### Google Finance scraper
- For non-US tickers with a known `google_exchange` code, the scraper builds `{base}:{google_exchange}` as the first URL attempt
- Falls back to bare URL (existing behaviour) as last resort

### Peer comparison skip
- `/api/peers` checks `get_exchange_info(ticker)["is_us"]` before any scraping
- Non-US tickers receive `{"available": false, "reason": "..."}` with HTTP 200 — no error, just an availability flag
- Frontend `peerComparison.js` renders a `buildUnavailableHTML(reason)` block instead of empty table

### DCF currency
- `renderIntoGroup` reads `data["Currency"]` (added by Yahoo scraper) and calls `_getCurrencySymbol()` + `_getDefaultsForCurrency()`
- SGD defaults: WACC 8%, g1 7%, g2 3% (Singapore risk-free ~3.5%, equity premium ~4.5%)
- All `$` occurrences in `buildHTML` replaced with `currencySymbol` parameter
- `_recalculate` also reads currency from `_dataCache[ticker]["Currency"]`

</decisions>
