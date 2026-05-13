# Phase 30: SGX Singapore Stock Integration — Context

**Drafted:** 2026-05-12
**Status:** Complete

<domain>
## Phase Boundary

Add first-class support for SGX-listed stocks (Yahoo Finance `.SI` suffix, e.g. `D05.SI` = DBS Bank) in the webapp. Users in Singapore can enter a local ticker and receive meaningful data, analytics, and display with correct currency (SGD) and market context (Straits Times Index benchmark).

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

### Exchange detection utility (`src/utils/exchange_utils.py`)
- `get_exchange_info(ticker)` inspects the suffix after the last `.` (e.g. `D05.SI` → suffix `SI`)
- `_EXCHANGE_MAP` dict maps suffix → exchange metadata dict; unknown/US tickers fall through to `_US_DEFAULTS`
- Each entry carries: `exchange`, `currency`, `currency_symbol`, `benchmark`, `google_exchange`, `is_us`
- Unknown suffix (e.g. `.ZZ`) returns US defaults — safe fallback, avoids false negatives
- Mirror of `KERAS_AVAILABLE` pattern: single-module check, imported at call sites in `webapp.py` and scrapers

### Google Finance scraper
- For non-US tickers with a known `google_exchange` code, builds `{base}:{google_exchange}` as first URL
- Falls back to bare URL (existing behaviour) as last resort
- `base` is derived by stripping the suffix: `ticker.rsplit(".", 1)[0]` — D05.SI → D05

### Yahoo scraper metadata
- After market cap extraction, reads `info.get("currency")` and `info.get("exchange") or info.get("exchangeTimezoneName")`
- Adds `"Currency"` and `"Stock Exchange"` keys to the returned data dict
- Both are optional: only set when present in yfinance response — no breaking change for existing US tickers

### Regression benchmark auto-selection
- `webapp.py` calls `get_exchange_info(ticker)["benchmark"]` to select benchmark before calling `linear_regression_analysis()`
- SGX tickers use `^STI`; all others fall back to `SPY`

### Peer comparison skip
- `/api/peers` checks `get_exchange_info(ticker)["is_us"]` before any Finviz call
- Non-US tickers receive `{"available": false, "reason": "...Finviz covers US exchanges only.", "ticker": ticker}` with HTTP 200 — not an error, just an availability flag
- Frontend `peerComparison.js` detects `resp.available === false` before the existing error check and renders `buildUnavailableHTML(reason)` instead

### DCF currency
- `renderIntoGroup` reads `data["Currency"]` (populated by Yahoo scraper) and calls two helpers:
  - `_getCurrencySymbol(currency)` — maps `{SGD: "S$", USD: "$", GBP: "£", EUR: "€", HKD: "HK$", AUD: "A$", JPY: "¥", CAD: "C$"}`, defaults to `$`
  - `_getDefaultsForCurrency(currency)` — `SGD` → `{wacc: 0.08, g1: 0.07, g2: 0.03}`; all others → `{wacc: 0.10, g1: 0.10, g2: 0.03}`
- `buildHTML` signature updated with `currencySymbol` parameter; all 4 hardcoded `$` replaced
- `_recalculate` also reads currency from `_dataCache[ticker]["Currency"]`
- SGD defaults: WACC 8%, g1 7%, g2 3% (Singapore risk-free ~3.5%, equity premium ~4.5%)

</decisions>

<code_context>
## Existing Code Insights

### Reusable patterns
- `KERAS_AVAILABLE` flag in `ml_signals.py`: mirror pattern for `_EXCHANGE_MAP` — single-module import, checked at call time
- Google scraper already iterated a URL list at lines 25–28 — extended with conditional non-US entry prepend
- `skip_analytics` gate in `webapp.py:543` — mirrors pattern for `not exch_info["is_us"]` early return in `/api/peers`
- `_ticker_validation_cache` in `webapp.py`: reference pattern for in-process cache (peer cache already existed from Phase 16)
- `window.PeerComparison` module pattern (IIFE, `renderIntoGroup`, `clearSession`): existed from Phase 16 — `buildUnavailableHTML` added inside same IIFE

### Integration points
- `webapp.py:51` — `from src.utils.exchange_utils import get_exchange_info` import added
- `webapp.py:610–612` — regression benchmark auto-selection
- `webapp.py:2309–2316` — `/api/peers` non-US early return
- `src/scrapers/google_scraper.py:10,26–33` — exchange-specific URL construction
- `src/scrapers/yahoo_scraper.py:228–234` — Currency/Stock Exchange metadata extraction
- `static/js/dcfValuation.js:36–50` — `_getCurrencySymbol`, `_getDefaultsForCurrency` helpers
- `static/js/dcfValuation.js:125` — `buildHTML` signature extended with `currencySymbol`
- `static/js/dcfValuation.js:232–235` — `renderIntoGroup` currency detection
- `static/js/peerComparison.js:168–176` — `buildUnavailableHTML(reason)` new function
- `static/js/peerComparison.js:181–184` — `_fetchAndRender` checks `resp.available === false`

### Test coverage
- `tests/test_unit_exchange_utils.py` (NEW): 7 unit tests covering SI suffix, case-insensitivity, US no-suffix, unknown suffix, MSFT defaults, ^STI benchmark for all SGX tickers, required keys schema
- `tests/test_peer_comparison.py`: 4 new tests in `TestPeersSGXSkip` class — `available:false` for D05.SI, Finviz not called for O39.SI, ticker echoed back for U11.SI, AAPL not short-circuited
- Pre-existing full-suite failures (3 peer tests in `TestPeersShape`/`TestPeersCacheHit`) are caused by E2E golden path test populating `_ticker_sector_map`/`_peer_cache` for AAPL, contaminating subsequent mocked tests — not introduced by Phase 30

</code_context>

<specifics>
## Specific Implementation Notes

### Exchange map structure
```python
_EXCHANGE_MAP = {
    "SI": {
        "exchange": "SGX",
        "currency": "SGD",
        "currency_symbol": "S$",
        "benchmark": "^STI",
        "google_exchange": "SGX",
        "is_us": False,
    },
}
_US_DEFAULTS = {
    "exchange": "US",
    "currency": "USD",
    "currency_symbol": "$",
    "benchmark": "SPY",
    "google_exchange": None,
    "is_us": True,
}
```

### Peer skip response shape
```json
{
  "available": false,
  "reason": "Peer comparison is not available for SGX-listed stocks. Finviz covers US exchanges only.",
  "ticker": "D05.SI"
}
```

### DCF SGD defaults rationale
- Singapore 10-yr bond yield ~3.5% → risk-free rate
- Equity risk premium ~4.5% → WACC ≈ 8%
- Singapore GDP growth ~3% long-run → terminal growth
- High-growth stage: 7% (below US 10% default — Singapore market matures faster)

### Commit
- Branch: `feature/phase-30-sgx-integration`
- Commit: `f43c69c` — `feat(phase-30): add SGX Singapore stock support`
- 30 files changed (includes untracked `logs/` and `outputs/` that were staged)

</specifics>

<deferred>
## Deferred to Later Phases

- Support for `.HK` (HKEX), `.L` (LSE), `.AX` (ASX), `.T` (TSE) — add one `_EXCHANGE_MAP` entry per market
- Currency conversion in price display fields (Current Price, 52-wk range etc.) beyond DCF
- P/E and valuation scoring threshold adjustments per market (SGX stocks warrant different "cheap" thresholds)
- FX-adjusted portfolio VaR across multi-currency holdings
- SGX peer comparison via an alternative data source (e.g. SGX website, Yahoo Finance peer list)
- Country-specific financial health score weighting

</deferred>

---

*Phase: 30-sgx-singapore-stock-integration*
*Context drafted: 2026-05-12 | Updated: 2026-05-13*
