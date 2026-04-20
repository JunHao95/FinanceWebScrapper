# Project Research Summary — v2.2 Trading Indicators

**Project:** MFE Showcase Web App — v2.2 Trading Indicators Sub-Tab
**Domain:** Quantitative Finance Showcase — SMC/ICT-Style Technical Indicators on Daily OHLCV
**Researched:** 2026-04-07
**Confidence:** HIGH

---

## Executive Summary

The v2.2 milestone adds a Trading Indicators sub-tab to the existing Flask + Vanilla JS MFE showcase. The tab renders a 2×2 grid of four indicator panels per ticker — Liquidity Sweep, Order Flow, Anchored VWAP, and Volume Profile — plus a composite Bullish/Bearish/Neutral bias signal with a one-line rationale. All four indicators are implementable using only numpy and pandas, both already installed. No new backend dependencies are required. The recommended build approach is a single canonical yfinance OHLCV fetch function, a separate backend module (`src/analytics/trading_indicators.py`), a new lazy-loaded GET endpoint (`/api/trading_indicators`), and a new Vanilla JS module (`tradingIndicators.js`) that mirrors the existing `peerComparison.js` per-ticker session-cache pattern. The new tab wires into `tabs.js` `validTabs` and `switchTab()` without touching the deep-analysis-group architecture from Phases 13–16.

The dominant risks are precision and correctness, not infrastructure. Three categories of error can silently produce wrong outputs: (1) look-ahead bias in swing detection if the loop boundary is `range(n, len(data))` instead of `range(n, len(data) - n)`; (2) VWAP anchor truncation if the OHLCV fetch uses the display lookback instead of always fetching 365 days for anchor resolution; (3) NaN propagation in cumulative order flow delta from zero-range doji candles. A fourth non-obvious failure is the Plotly horizontal histogram for Volume Profile — the naive approach renders a vertical bar chart; it requires `make_subplots(cols=2, shared_yaxes=True)`. All other pitfalls are moderate and preventable with named constants and per-anchor try/except blocks.

The build order dictated by FEATURES.md and confirmed by ARCHITECTURE.md is: Volume Profile first (simplest, no external dependencies, establishes the Plotly payload shape), then Anchored VWAP (validates the earnings date fetch pattern), then Order Flow (three sub-components sharing one panel, simpler precision work than swing detection), and Liquidity Sweep last (most complex, off-by-one boundary errors are the primary risk). Composite bias and tab wiring complete the final phase after all four panels are stable.

---

## Key Findings

### Recommended Stack

**Zero new backend dependencies.** All four indicators require only numpy and pandas. `pandas_ta` is rejected because its VWAP is session-reset only (not anchored), it lacks Volume Profile and Liquidity Sweep pattern detection, and adds pandas version-conflict risk. `ta-lib` is rejected because it requires a compiled C binary that breaks on Render. `scipy.signal.argrelextrema` could simplify swing detection but is intentionally avoided to keep the showcase code transparent.

**Core technologies:**
- numpy + pandas: All four indicator computations — already installed, zero changes to requirements.txt
- yfinance: OHLCV via `Ticker.history()` and earnings dates via `Ticker.earnings_dates` — already installed; one canonical fetch function required
- Plotly.js (CDN): 2×2 chart grid, horizontal histogram, candlestick overlays — already loaded
- Flask: One new GET route `/api/trading_indicators?ticker=X&lookback=90` — ~20 lines in webapp.py following the `/api/peers` pattern

### Expected Features

**Must have (table stakes):**
- Swing high/low detection with Bullish/Bearish/No-Sweep signal label and chart markers
- Buy/sell pressure delta bar chart (green/red) with cumulative delta line overlay
- 52-week-high and 52-week-low AVWAP lines overlaid on price
- POC displayed numerically as a visible horizontal level (not a hairline)
- VAH/VAL shaded zone on Volume Profile
- Composite bias signal with identification of the dissenting indicator
- Lookback selector (30/90/180/365 days)
- 2×2 grid layout per ticker in a dedicated fourth tab

**Should have (differentiators):**
- Three simultaneous AVWAP lines including earnings anchor with graceful fallback
- Price-in-value-area badge on Volume Profile
- Volume divergence flag with displayed slope values
- Composite rationale text naming the dissenting indicator
- Right-edge AVWAP labels showing current distance-from-VWAP as a percentage
- Imbalance candle annotations on the Order Flow chart

**Defer to post-v2.2:**
- Custom AVWAP anchor date picker
- Walk-forward backtest of sweep signals
- Intraday VWAP / Market Profile TPO charts (require intraday data)
- Real-time order book / footprint charts (require tick data — anti-feature)

### Architecture Approach

The module follows the `peerComparison.js` pattern exactly: lazy-loaded on tab activation, per-ticker GET calls, session cache keyed by `ticker + '-' + lookback`, progressive rendering, `clearSession()` in `stockScraper.js displayResults()`. It renders into `div#tradingIndicatorsTabContent`, not into `deep-analysis-content-{TICKER}`.

The backend follows Pattern 2 (Fetch-Then-Compute): `compute_indicators(ticker, lookback)` in `src/analytics/trading_indicators.py` fetches OHLCV once, computes all four indicators, and returns a dict where each indicator includes Plotly-ready `{traces, layout, signal}`. The JS module calls `Plotly.newPlot(divId, payload.traces, payload.layout)` — it constructs zero Plotly layout objects in JavaScript.

**Major components:**

| Component | Status | Files |
|-----------|--------|-------|
| `src/analytics/trading_indicators.py` | NEW | Canonical OHLCV fetch, four indicator functions, composite bias, Plotly payload builders |
| `/api/trading_indicators` GET route | NEW (add to webapp.py) | ~20 lines: parse ticker + lookback, lazy import, convert_numpy_types, jsonify |
| `static/js/tradingIndicators.js` | NEW | Session cache, tab activation handler, per-ticker DOM shell, Plotly render loop |
| `templates/index.html` | MODIFIED | 4th tab button, content div, lookback selector, script tag |
| `static/js/tabs.js` | MODIFIED | `'tradingindicators'` in validTabs, switchTab case with lazy-load trigger |
| `static/js/stockScraper.js` | MODIFIED | `TradingIndicators.clearSession()` in `displayResults()` |
| `static/js/displayManager.js` | UNCHANGED | No changes needed |

### Critical Pitfalls

1. **Look-ahead bias in swing detection** — Loop bound must be `range(n, len(highs) - n)`, not `range(n, len(highs))`. Add regression test: swing indices on 90-day data must not shift when re-run on 91 days.

2. **VWAP anchor truncation** — Data fetch for VWAP computation must always cover 365 days regardless of display lookback. If the anchor date predates the fetched data, surface an explicit warning rather than silently computing from the first available bar.

3. **NaN propagation in order flow delta** — Guard doji candles with epsilon: `(close - low) / (high - low + 1e-10)`. Assert `not np.isnan(delta).any()` before any cumulative sum.

4. **Volume Profile horizontal histogram requires `make_subplots` with `shared_yaxes=True`** — `make_subplots(rows=1, cols=2, column_widths=[0.75, 0.25], shared_yaxes=True)` is mandatory. Without it the histogram renders as a vertical bar chart and the POC level will not align between the two axes.

5. **Composite bias overconfidence + silent failure masking** — Label as "Trend-following bias." Composite denominator must count only `ok == true` sub-indicators so a failed module shows as grey "unavailable" rather than distorting the ratio.

6. **Sweep detection close-back-below condition** — A sweep requires `high > prior_swing_high AND close < prior_swing_high` (bearish sweep) or `low < prior_swing_low AND close > prior_swing_low` (bullish sweep). Omitting the close condition flags every momentum breakout as a sweep.

---

## Implications for Roadmap

### Phase 1: Data Foundation and Backend Scaffold

**Rationale:** All four indicators share one canonical OHLCV fetch. Establishing it first, along with a stub Flask route returning hardcoded JSON, unblocks both backend math and JS development in parallel.

**Delivers:** `fetch_ohlcv(ticker, days, auto_adjust=True)` canonical function; `GET /api/trading_indicators` stub route; verified browser-to-JSON round-trip.

**Avoids:** Pitfall 13 (adjusted/unadjusted price mismatch); Pitfall 14 (stale anchor dates — `display_lookback` separated from `data_fetch_period` at API design level).

**Research flag:** Standard pattern — mirrors `/api/peers` exactly. No research needed.

---

### Phase 2: Volume Profile

**Rationale:** Simplest correct algorithm, no external data dependencies, highest visual impact. Establishes the Plotly `{traces, layout, signal}` payload shape all subsequent indicators must follow.

**Delivers:** POC/VAH/VAL with 50-bin histogram; horizontal bar chart with `shared_yaxes=True`; visible POC level (filled rectangle or annotated hline); VAH/VAL shaded zone; price-in-value-area badge.

**Avoids:** Pitfall 7 (bin count sensitivity — fixed 50 bins with `bin_width_usd` in metadata); Pitfall 8 (invisible hairline levels); Pitfall 9 (vertical vs. horizontal histogram — `make_subplots` established here); Pitfall 17 (volume attributed to close only — use range-spread approach).

**Research flag:** Standard pattern. No research needed.

---

### Phase 3: Anchored VWAP

**Rationale:** Second simplest indicator (one `cumsum` expression per anchor); validates the earnings date yfinance call and the anchor-resolution separation from display lookback before swing detection complexity begins.

**Delivers:** 52-wk-high, 52-wk-low, and earnings AVWAP lines with distinct styles; right-edge distance labels; convergence warning when lines are within 0.3%; `current_price_vs_avwap` sub-signals for composite.

**Avoids:** Pitfall 5 (anchor truncation); Pitfall 6 (converging lines look broken); Pitfall 14 (stale anchor on lookback change); Pitfall 19 (earnings KeyError crashes all VWAP — per-anchor try/except, null anchor with reason field).

**Research flag:** Verify `yf.Ticker('AAPL').earnings_dates` column names against installed yfinance version before implementing earnings anchor (MEDIUM confidence — 5-minute check, not a full research phase).

---

### Phase 4: Order Flow

**Rationale:** Three sub-components all use the same OHLCV data and can be built together. Numerically simpler than swing detection — getting the NaN guards and divergence definition right here reduces risk before the composite signal is wired.

**Delivers:** Delta bar chart (green/red) with cumulative delta overlay; volume divergence flag with slope values; imbalance candle detection with named constants (`IMBALANCE_BODY_RATIO = 0.70`, `IMBALANCE_VOLUME_MULTIPLIER = 1.2`); `delta_signal`, `divergence_flag`, `imbalance_signal` sub-signals.

**Avoids:** Pitfall 3 (NaN from doji — epsilon guard + assert); Pitfall 4 (divergence fires on every red bar — rolling-window definition, frequency cap, UI tooltip documents the definition); Pitfall 15 (imbalance threshold undefined — named constants + UI tooltip).

**Research flag:** Standard pattern. No research needed.

---

### Phase 5: Liquidity Sweep + Composite Bias + Tab Wiring

**Rationale:** Liquidity Sweep is the most complex indicator (two-pass algorithm: swing detection then sweep matching). Built last when the Flask-to-Plotly pipeline is known to work. Composite bias depends on all four modules. Tab wiring touches the most existing files and belongs at the end when failure impact is lowest.

**Delivers:** `_compute_liquidity_sweep()` with adaptive n (`max(2, min(5, lookback_days // 30))`), look-ahead-safe loop bounds, close-back-below sweep condition; `_compute_composite_bias()` with `ok` flag per sub-indicator and dissenting-indicator identification in rationale text; 4th tab button, `tradingIndicatorsTabContent` div, lookback dropdown, `tradingIndicators.js`, `tabs.js` validTabs extension, `stockScraper.js` clearSession hook.

**Avoids:** Pitfall 1 (look-ahead bias — `range(n, len-n)` + regression test); Pitfall 2 (breakouts flagged as sweeps — close-back-below required); Pitfall 10 (composite overconfidence — "Trend-following bias" label + caveat text); Pitfall 11 (silent failure masking — `ok` flag + grey unavailable state); Pitfall 12 (Plotly memory — `staticPlot: true` + `Plotly.react()` + IntersectionObserver + 5-ticker cap); Pitfall 16 (n too large for short lookbacks — adaptive n + "0 swings detected" message); Pitfall 18 (ambiguous grid labels — `subplot_titles` in `make_subplots`).

**Research flag:** Internal validation needed — run look-ahead regression test against AAPL and SPY at all four lookback values before wiring composite. Not an external research need.

---

### Phase Ordering Rationale

- Phase 1 before everything: one canonical fetch function prevents `auto_adjust` inconsistency from propagating across all four indicators.
- Phase 2 (Volume Profile) before Phase 3 (VWAP): no external data dependencies; establishes the Plotly payload shape contract.
- Phase 3 before Phase 4: earnings date yfinance call validated before swing detection complexity begins.
- Phase 4 before Phase 5: O(n) delta/divergence math is simpler than two-pass swing+sweep algorithm; NaN guards and threshold decisions are lower-stakes to get right first.
- Phase 5 last: swing detection loop bounds are the primary source of silent correctness bugs; tab wiring is the most disruptive change to existing code.

### Research Flags

Needs verification during Phase 3: `yf.Ticker('AAPL').earnings_dates` attribute and DataFrame column names against installed yfinance version.

All other phases: standard patterns documented in existing codebase. No phase-specific research sessions required.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Direct codebase inspection confirms numpy/pandas sufficiency; all library rejections are definitive |
| Features | HIGH (algorithms) / MEDIUM (thresholds) | Algorithm definitions are established math; imbalance multipliers and composite majority threshold are practitioner heuristics |
| Architecture | HIGH | Every integration point verified against actual source code (tabs.js, peerComparison.js, displayManager.js, webapp.py, index.html) |
| Pitfalls | HIGH | Critical pitfalls are deterministic implementation mistakes with exact prevention conditions; Plotly memory severity estimate is empirical |

**Overall confidence:** HIGH

### Gaps to Address

- **yfinance `earnings_dates` column names:** Verify against installed version before Phase 3 implementation (5-minute check).
- **Imbalance candle thresholds (70%/1.5×):** Calibrate empirically after Phase 4 — target 3–8 signals per 90-day window on AAPL/SPY. Raise to 1.8× if too frequent; lower to 1.3× if too sparse.
- **Composite bias majority threshold (2/3):** Decide before Phase 5 whether 2/3 majority or simple majority (>50%) better serves the showcase's intended behavior.
- **Plotly memory ceiling with 5+ tickers:** `staticPlot: true` is expected to reduce memory ~10×; actual threshold is empirical. The 5-ticker cap may be unnecessary if typical use is 2–3 tickers.

---

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection: `src/indicators/technical_indicators.py`, `static/js/tabs.js`, `static/js/peerComparison.js`, `static/js/stockScraper.js`, `static/js/displayManager.js`, `templates/index.html`, `webapp.py`
- `.planning/research/STACK.md` (v2.2, 2026-04-07)
- `.planning/research/FEATURES.md` (v2.2, 2026-04-07)
- `.planning/research/ARCHITECTURE.md` (v2.2, 2026-04-07)
- `.planning/research/PITFALLS.md` (v2.2, 2026-04-07)
- Market Profile theory (Steidlmayer) — Volume Profile POC/VAH/VAL 70% definition
- Elder (1993) "Trading for a Living" — buying/selling pressure per bar
- Kaufman (2013) "Trading Systems and Methods" — daily-bar volume approximations
- ICT/SMC methodology (public domain) — liquidity sweep and imbalance candle definitions

### Secondary (MEDIUM confidence)
- pandas-ta GitHub source — confirms session-VWAP only, no anchored VWAP
- yfinance 0.2.x changelog — `auto_adjust=True` default and `.earnings_dates` structure
- Plotly.js documentation — `make_subplots`, `shared_yaxes`, `staticPlot`, `Plotly.react()`

### Tertiary (LOW confidence)
- Composite signal 2/3 threshold — author recommendation; not a quant standard
- Imbalance candle thresholds — SMC community practitioner heuristics; not peer-reviewed

---

*Research completed: 2026-04-07*
*Ready for roadmap: yes*
