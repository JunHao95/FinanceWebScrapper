# Roadmap: MFE Showcase Web App — Milestone v2.2 Trading Indicators

## Overview

Milestone v2.2 adds a Trading Indicators fourth tab to the Analysis Results area. The tab renders a 2×2 Plotly grid per scraped ticker showing four indicator panels — Volume Profile, Anchored VWAP, Order Flow, and Liquidity Sweep — plus a composite Bullish/Bearish/Neutral bias signal with a one-line rationale. All computation uses numpy and pandas against a canonical yfinance OHLCV fetch; no new backend dependencies are required.

Phases are ordered by implementation risk, not alphabetically. Volume Profile is built first (simplest, no external data dependencies, establishes the Plotly payload contract). Anchored VWAP validates the earnings date fetch before swing detection begins. Order Flow clears the NaN guard and divergence definition at lower stakes. Liquidity Sweep is last (most complex, primary source of look-ahead bugs). Composite bias and tab wiring complete when all four panels are stable.

**Phase numbering:** Continues from v2.1 which ended at Phase 17. v2.2 phases start at 18.

---

## Phases

- [ ] **Phase 18: Backend Scaffold** - Canonical OHLCV fetch function, stub Flask route returning hardcoded JSON, stub JS module confirming browser-to-API round-trip
- [ ] **Phase 19: Volume Profile** - POC/VAH/VAL horizontal histogram with shaded value area, price-in-value-area badge, adaptive bin count (VPROF-01, VPROF-02, VPROF-03)
- [ ] **Phase 20: Anchored VWAP** - Three AVWAP lines (52-wk high, 52-wk low, earnings) with right-edge labels, convergence warning, earnings fallback (AVWAP-01, AVWAP-02, AVWAP-03)
- [ ] **Phase 21: Order Flow** - Delta bar chart with cumulative overlay, volume divergence flag with slope values, imbalance candle annotations (FLOW-01, FLOW-02, FLOW-03)
- [ ] **Phase 22: Liquidity Sweep + Composite Bias + Tab Wiring** - Sweep detection with adaptive n and chart markers, composite bias badge with dissenter identification, fourth tab + lookback dropdown fully wired (SWEEP-01, SWEEP-02, SWEEP-03, BIAS-01, BIAS-02, BIAS-03, TIND-01, TIND-02, TIND-03)

---

## Phase Details

### Phase 18: Backend Scaffold
**Goal**: The infrastructure for all four Trading Indicators is in place — one canonical OHLCV fetch function, a stub Flask route that returns valid hardcoded JSON, and a stub JS module that calls it and confirms the browser-to-API round-trip — so that indicator implementations in Phases 19–21 can be built and tested independently without touching the integration layer again.
**Depends on**: Phase 17 (v2.1 complete)
**Requirements**: None (infrastructure phase — unblocks VPROF-01 through TIND-03)
**Success Criteria** (what must be TRUE):
  1. `GET /api/trading_indicators?ticker=AAPL&lookback=90` returns a 200 response with valid JSON containing placeholder keys for all four indicator panels.
  2. The canonical `fetch_ohlcv(ticker, days, auto_adjust=True)` function exists in `src/analytics/trading_indicators.py` and returns an OHLCV DataFrame with no adjusted/unadjusted mismatch.
  3. `static/js/tradingIndicators.js` exists with a `TradingIndicators.clearSession()` method and a per-ticker session cache keyed by `ticker + '-' + lookback`.
  4. A browser developer-tools network trace confirms the JS module calls the route and receives the stub JSON without any console error.
**Plans**: 2 plans
Plans:
- [ ] 18-01-PLAN.md — Python backend: fetch_ohlcv function, stub trading_indicators module, Flask GET route (wave 1)
- [ ] 18-02-PLAN.md — Browser scaffold: tradingIndicators.js IIFE, tab button + content div in index.html, clearSession wiring, tabs.js update, DevTools checkpoint (wave 2)

### Phase 19: Volume Profile
**Goal**: Each ticker's Trading Indicators panel shows a horizontal volume histogram with clearly visible POC, VAH, and VAL levels, a shaded 70% value area zone, a price-in-value-area badge, and adaptive bin sizing — establishing the Plotly `{traces, layout, signal}` payload shape that all subsequent indicators must follow.
**Depends on**: Phase 18
**Requirements**: VPROF-01, VPROF-02, VPROF-03
**Success Criteria** (what must be TRUE):
  1. The Volume Profile panel renders as a horizontal bar chart (not vertical) with the price axis shared on the y-axis, confirming `make_subplots(shared_yaxes=True)` is correctly applied.
  2. POC, VAH, and VAL are visible as filled levels or annotated horizontal lines — not hairlines — and the 70% value area between VAH and VAL is shaded in a distinct colour.
  3. A badge below the chart reads "Price inside value area" or "Price outside value area" reflecting the current close price position.
  4. The chart metadata or subtitle displays the bin width in USD so a user can verify the resolution (targeting approximately 0.2% bin width of price range).
**Plans**: TBD

### Phase 20: Anchored VWAP
**Goal**: Each ticker's Anchored VWAP panel shows three VWAP lines — anchored to the 52-week high date, the 52-week low date, and the last earnings date — overlaid on the price chart, with right-edge distance labels and a convergence warning when any two lines are within 0.3% of current price.
**Depends on**: Phase 19
**Requirements**: AVWAP-01, AVWAP-02, AVWAP-03
**Success Criteria** (what must be TRUE):
  1. Two AVWAP lines anchored to the 52-week high and 52-week low dates are visible on the price chart as distinct line styles, and each shows a right-edge label reporting current price distance as a signed percentage (e.g., "+2.1% above AVWAP").
  2. A third AVWAP line anchored to the last earnings date renders when available; when unavailable the panel shows "Earnings anchor unavailable" without removing or breaking the other two lines.
  3. When any two AVWAP lines are within 0.3% of current price, a convergence note appears on the panel identifying which lines are converging.
  4. The OHLCV fetch for anchor resolution always covers 365 days regardless of the display lookback, so a 30-day display can still compute a valid 52-week anchor.
**Plans**: TBD

### Phase 21: Order Flow
**Goal**: Each ticker's Order Flow panel shows a green/red buy/sell pressure delta bar chart with a cumulative delta overlay line, a volume divergence flag when price and volume trends diverge over a 10-bar window, and imbalance candle annotations marking bars where body size and volume exceed defined thresholds.
**Depends on**: Phase 20
**Requirements**: FLOW-01, FLOW-02, FLOW-03
**Success Criteria** (what must be TRUE):
  1. The Order Flow chart shows per-bar delta bars coloured green (buy pressure) or red (sell pressure), with a continuous cumulative delta line overlaid — zero-range doji candles do not produce NaN or crash the chart.
  2. When price slope and volume slope diverge over a 10-bar rolling window, a volume divergence flag appears on the panel displaying the actual price-slope and volume-slope values so the user can verify the signal.
  3. Bars where the body exceeds 70% of the high-low range AND volume exceeds 1.2× the 20-day average are annotated on the chart with "Bullish" or "Bearish" imbalance candle labels.
  4. Running the Order Flow computation on AAPL over a 90-day window produces no NaN values in the cumulative delta series, confirmed by the epsilon guard on zero-range bars.
**Plans**: TBD

### Phase 22: Liquidity Sweep + Composite Bias + Tab Wiring
**Goal**: The fourth Trading Indicators tab is fully functional — Liquidity Sweep detection is live with adaptive n, look-ahead-safe loop bounds, and chart markers; the composite bias badge identifies the dissenting sub-indicator; the tab renders a 2×2 Plotly grid per ticker with a lookback dropdown that clears cache and re-fetches on change; all 18 v2.2 requirements are satisfied.
**Depends on**: Phase 21
**Requirements**: SWEEP-01, SWEEP-02, SWEEP-03, BIAS-01, BIAS-02, BIAS-03, TIND-01, TIND-02, TIND-03
**Success Criteria** (what must be TRUE):
  1. The Liquidity Sweep panel shows a Bullish Sweep, Bearish Sweep, or No Sweep signal label for the ticker; when zero swings are detected in the selected window the panel displays "No confirmed swings in selected window (n=X)" with the actual n value shown.
  2. Sweep detection markers appear on sweep candles and dashed horizontal lines are drawn at the swept price level on the chart, and the look-ahead regression test confirms swing indices on 90-day data do not shift when re-run on 91 days.
  3. Each ticker card in the Trading Indicators tab shows a Bullish, Bearish, or Neutral composite bias badge with a one-line rationale that names the dissenting sub-indicator; failed sub-indicators appear as grey "unavailable" and the badge denominator reflects only successfully computed modules (e.g., "3/4 indicators").
  4. A "Trading Indicators" tab button is visible in the results tab bar; activating it lazy-loads the 2×2 Plotly grid for all scraped tickers without requiring a re-scrape.
  5. A lookback dropdown (30 / 90 / 180 / 365 days) is visible in the tab; changing the selection clears the session cache and re-fetches all tickers; all charts render with `staticPlot: true`.
**Plans**: TBD

---

## Progress

**Execution Order:**
Phases execute in numeric order: 18 → 19 → 20 → 21 → 22

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 18. Backend Scaffold | 0/2 | Not started | - |
| 19. Volume Profile | 0/? | Not started | - |
| 20. Anchored VWAP | 0/? | Not started | - |
| 21. Order Flow | 0/? | Not started | - |
| 22. Liquidity Sweep + Composite Bias + Tab Wiring | 0/? | Not started | - |

---

## Coverage

**v2.2 Requirements → Phase Mapping**

| Requirement | Phase |
|-------------|-------|
| VPROF-01 | Phase 19 |
| VPROF-02 | Phase 19 |
| VPROF-03 | Phase 19 |
| AVWAP-01 | Phase 20 |
| AVWAP-02 | Phase 20 |
| AVWAP-03 | Phase 20 |
| FLOW-01 | Phase 21 |
| FLOW-02 | Phase 21 |
| FLOW-03 | Phase 21 |
| SWEEP-01 | Phase 22 |
| SWEEP-02 | Phase 22 |
| SWEEP-03 | Phase 22 |
| BIAS-01 | Phase 22 |
| BIAS-02 | Phase 22 |
| BIAS-03 | Phase 22 |
| TIND-01 | Phase 22 |
| TIND-02 | Phase 22 |
| TIND-03 | Phase 22 |

**Coverage:** 18/18 v2.2 requirements mapped. No orphans.

---

## Architecture Constraints (from research)

**New files:**
- `src/analytics/trading_indicators.py` — canonical OHLCV fetch, four indicator functions, composite bias, Plotly payload builders
- `static/js/tradingIndicators.js` — session cache, tab activation handler, per-ticker DOM shell, Plotly render loop

**Modified files:**
- `webapp.py` — new `GET /api/trading_indicators?ticker=X&lookback=90` route (~20 lines, follows `/api/peers` pattern)
- `templates/index.html` — 4th tab button, `tradingIndicatorsTabContent` div, lookback selector, script tag
- `static/js/tabs.js` — `'tradingindicators'` added to `validTabs`, `switchTab()` lazy-load case
- `static/js/stockScraper.js` — `TradingIndicators.clearSession()` called in `displayResults()`

**Critical correctness guards (from research/PITFALLS.md):**
- Swing detection loop: `range(n, len(highs) - n)` not `range(n, len(highs))` — prevents look-ahead bias
- AVWAP data fetch: always 365 days regardless of display lookback — prevents anchor truncation
- Order flow doji guard: `(close - low) / (high - low + 1e-10)` — prevents NaN propagation
- Volume Profile histogram: `make_subplots(rows=1, cols=2, shared_yaxes=True)` — prevents vertical render
- Composite label: "Trend-following bias" + caveat text — prevents overconfidence framing

---

*Roadmap created: 2026-04-08*
*Milestone: v2.2 Trading Indicators*
*Previous milestone: v2.1 (Phases 13–17, all Complete)*
