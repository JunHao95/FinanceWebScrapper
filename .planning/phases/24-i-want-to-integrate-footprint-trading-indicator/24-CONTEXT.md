# Phase 24: Integrate Footprint Trading Indicator - Context

**Gathered:** 2026-04-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a Footprint-style indicator panel to the Trading Indicators tab. Fetch 15-minute intraday bars (60-day max horizon) per ticker, approximate buy/sell volume via the existing Close-Low proxy (same as Phase 21 Order Flow), render as a delta heatmap with adaptive price bins, expose a new `GET /api/footprint` backend route, and integrate as the 5th panel in an expanded 3×2 grid. Footprint participates in the composite bias signal as a 5th voice (denominator becomes 5).

**Out of scope:**
- True tick-level / L2 footprint data (yfinance does not provide it — approximation only)
- Alternative visual styles (numeric-cell footprint, split-color stacked bars, per-candle VP overlay)
- Secondary footprint signals (stacked imbalance, delta divergence, POC migration) — deferred
- Any changes to VP / AVWAP / Order Flow / Sweep panel internals (only their grid position changes)

</domain>

<decisions>
## Implementation Decisions

### Data approximation
- **Intraday source**: yfinance 15-minute bars, up to 60 days of history (yfinance 15m data horizon)
- **Buy/sell split per bar**: `buy_volume = (Close − Low) / (High − Low + 1e-10) × Volume`; `sell_volume = Volume − buy_volume` — same Close-Low proxy as Phase 21 `compute_order_flow`, with the same epsilon guard on zero-range bars
- **Delta per bar**: `buy_volume − sell_volume`
- **Aggregation**: 15m buy/sell/delta aggregated into per-(day, price-bin) cells for the heatmap; daily deltas summed into a cumulative delta series
- **Lookback handling**: Footprint panel is ALWAYS capped at 60 days regardless of the tab-level lookback dropdown (30/90/180/365). When the user selects a lookback > 60d, all other panels honor it; the footprint panel shows the most recent 60 days and displays a note: `"Footprint limited to 60d — 15m data horizon"`

### Visual style
- **Chart type**: Plotly heatmap (Heatmap trace) — X-axis = daily candle dates, Y-axis = price bins
- **Price bins**: Adaptive bin count targeting ~0.2% bin width of the 60d price range (same convention as Phase 19 Volume Profile)
- **Color**: Diverging palette around zero — strong green for positive delta (buy-dominant), deep red for negative delta (sell-dominant), near-background (#1e1e2e / #7f849c) for ≈zero. Anchored to Catppuccin green `#2ecc71` / red `#e74c3c` family to stay consistent with the tab
- **Overlays**:
  - Dashed horizontal line at current close price across the full heatmap
  - Small dot/triangle markers at the POC (price bin with max total volume) per candle — reveals POC migration visually
- **Hover**: Each cell tooltip shows `buy`, `sell`, `delta`, and bin price range
- **Panel height**: 500px (consistent with existing VP/AVWAP/Order Flow/Sweep panel heights)

### Tab integration
- **Grid expansion**: Trading Indicators grid expands from 2×2 to **3 columns × 2 rows**
  - Row 1: Volume Profile, Anchored VWAP, Order Flow
  - Row 2: Liquidity Sweep, **Footprint**, (empty placeholder for future indicator)
  - CSS change: `grid-template-columns: 1fr 1fr` → `grid-template-columns: 1fr 1fr 1fr`
- **Composite bias badge**: remains ABOVE the grid (unchanged position from Phase 22)
- **Backend route**: new `GET /api/footprint?ticker=X&days=60` (separate from `/api/trading_indicators`) — keeps the intraday-fetch cost scoped to this panel
- **Frontend fetch**: JS calls `/api/footprint` **in parallel** with `/api/trading_indicators` per ticker; session cache keyed by `ticker + '-footprint'`
- **Session cache invalidation**: `TradingIndicators.clearSession()` must also clear the footprint cache on re-scrape and on lookback-dropdown change
- **Failure mode**: if the intraday fetch fails or returns empty (yfinance rate-limit, non-US ticker, etc.), render a grey placeholder cell with message `"Footprint unavailable — intraday data not available for this ticker"` — matches the Phase 22 Sweep "unavailable" pattern; other panels unaffected

### Signals & composite bias
- **Primary signal**: sign of cumulative delta across the 60d window (`cum_delta = Σ daily_delta`)
- **Neutral threshold**: `|cum_delta| < 0.05 × total_60d_volume` → Neutral; otherwise positive → Bullish, negative → Bearish (relative threshold scales across large-cap and small-cap tickers)
- **Badge format** (below the heatmap, matching VP/AVWAP/Sweep convention):
  - Bullish: `✔ Bullish Footprint — Cum Δ: +2.4M shares (60d)` (green `#2ecc71`)
  - Bearish: `⚠ Bearish Footprint — Cum Δ: −1.1M shares (60d)` (red `#e74c3c`)
  - Neutral: `— Neutral Footprint — Cum Δ: +12K shares (60d)` (grey `#7f849c`)
  - Unavailable: `— Footprint unavailable` (grey `#7f849c`)
- **Composite bias participation**: Footprint is the **5th voice** in `compute_composite_bias`
  - Denominator becomes 5 (successfully computed sub-indicators only; unavailable footprint excludes itself, so a ticker with 4 working modules still shows `3/4 indicators` as per BIAS-03)
  - Dissenter identification extended to consider footprint (e.g., `● Bullish (4/5) — Footprint dissents`)
  - Phase 22's Phase BIAS-02 "Trend-following bias — all indicators share the same OHLCV data source" caveat STILL HOLDS (footprint is OHLCV-derived)
  - Majority rule: same as Phase 22 (simple majority; ties → Neutral); update majority-threshold logic to handle odd N=5 (3 votes carries)

### Claude's Discretion
- Exact Plotly colorscale stops (midpoint color, gradient spacing)
- Exact POC marker shape (dot vs triangle vs star) and size
- Current-price-line dash pattern, color, and width
- Exact CSS class names for the 3-column grid wrapper and empty placeholder cell
- Loading spinner style during intraday fetch
- Cache TTL and exact key format (e.g., `ticker + '-footprint'` vs `ticker + '-footprint-60'`)
- Hover tooltip HTML formatting and number formatting (e.g., `2.4M` vs `2,400,000`)
- Badge font size and exact icon glyphs (✔/⚠/— suggested, not locked)
- Requirements ID prefix — suggested `FOOT-01 … FOOT-05`:
  - FOOT-01: 15m intraday fetch + buy/sell/delta compute
  - FOOT-02: Delta heatmap rendering (adaptive bins, diverging palette, overlays)
  - FOOT-03: Cumulative-delta badge with ±5% volume neutral threshold
  - FOOT-04: 3×2 grid expansion + parallel fetch wiring + unavailable handling
  - FOOT-05: Composite bias extended to 5-voice denominator + dissenter identification

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `fetch_ohlcv(ticker, days, auto_adjust=True)` at `src/analytics/trading_indicators.py:16` — pattern to mirror for a new `fetch_intraday(ticker, days, interval='15m')` function
- `compute_volume_profile(df, ticker, lookback)` at `trading_indicators.py:44` — adaptive bin-count logic (~0.2% bin width) to reuse verbatim for the heatmap Y-axis
- `compute_order_flow(df, ticker, lookback)` at `trading_indicators.py:402` — Close-Low proxy with epsilon guard to reuse for the intraday buy/sell split
- `compute_composite_bias(results)` at `trading_indicators.py:663` — extend to accept a 5th sub-indicator (footprint) and update the dissenter rationale
- `_renderTickerCard(container, ticker, lookback, resp)` in `static/js/tradingIndicators.js:34` — extend grid CSS to 3 columns and add a Footprint cell
- `clearSession()` in `tradingIndicators.js:7` — extend to clear the footprint-specific cache entries
- `ti-va-badge` / `ti-legend` CSS classes — reuse for badge and legend styling
- `peerComparison.js` lazy-load + session cache pattern — mirror for the parallel footprint fetch

### Established Patterns
- Dark Catppuccin theme: `paper_bgcolor='#1e1e2e'`, `plot_bgcolor='#1e1e2e'`, `font color='#cdd6f4'`
- Plotly `{ staticPlot: true, responsive: true }` render options for all indicator charts (TIND-03)
- Python payload shape: `{traces, layout, signal, ...}` — Footprint response must follow
- Badge color convention: `#2ecc71` positive, `#e74c3c` warning, `#7f849c` muted/neutral
- Adaptive bin width ≈ 0.2% of price range (Phase 19 VP convention)
- Epsilon-guarded ratio: `(Close − Low) / (High − Low + 1e-10)` (Phase 21 FLOW-01)
- Unavailable-panel pattern: grey placeholder cell with a single-line message (Phase 22 Sweep)

### Integration Points
- New Flask route: `GET /api/footprint?ticker=X&days=60` in `webapp.py` (follows existing `/api/trading_indicators` and `/api/peers` patterns)
- New backend functions in `src/analytics/trading_indicators.py`: `fetch_intraday()` and `compute_footprint(df_15m)`
- `static/js/tradingIndicators.js`:
  - `_renderTickerCard()` — expand grid CSS, add Footprint cell + badge + legend, wire parallel `/api/footprint` fetch
  - `clearSession()` — also purge footprint cache entries
- Tab header / lookback dropdown handler in `tradingIndicators.js` / `tabs.js` — on lookback change, clear footprint cache AND re-fetch footprint along with the other panels (even though footprint itself is 60d-capped, user expects a consistent refresh)
- `compute_composite_bias()` in `trading_indicators.py` — extend to 5 voices; update BIAS-01 rationale template strings to handle 5-way dissenter mention
- Tests (per CLAUDE.md requirement — every new feature ships with tests in the same branch):
  - `tests/test_unit_footprint.py` — unit tests for `fetch_intraday`, `compute_footprint` (happy-path + empty-intraday edge case)
  - `tests/test_integration_routes.py` — integration test for `/api/footprint` (200 response, schema, invalid-ticker error handling)
  - `tests/test_regression_indicators.py` — regression test pinning cumulative-delta value for a frozen 15m fixture
  - Extend existing composite-bias tests to cover 5-voice scenarios (all 5 working, 1 unavailable → 4-voice fallback, footprint as dissenter)

</code_context>

<specifics>
## Specific Ideas

- "Footprint" is used loosely here — true footprint charts need Level 2 / tick-level data showing bid vs ask volume at each price. yfinance provides neither. This phase ships a practical OHLCV-approximation footprint using the Phase 21 Close-Low proxy applied to 15m intraday bars. The badge, caveat text, and rationale should not oversell the analytic depth.
- The 60d hard cap comes from yfinance itself: 15m intraday history is ~60 days. Going longer would require 1h bars (sparse) or paid data sources (out of scope).
- Composite bias must stay coherent with Phase 22's BIAS-02 caveat: `"Trend-following bias — all indicators share the same OHLCV data source."` The caveat still holds for footprint (15m is just finer-grained OHLCV).
- Footprint cumulative delta and Order Flow cumulative delta use the same formula but on different bar granularities (15m aggregated-to-daily vs native daily). They can disagree; that disagreement is informative and visible as a dissent in the composite bias.

</specifics>

<deferred>
## Deferred Ideas

- Secondary footprint signals (stacked imbalance detection, delta divergence vs price trend, POC migration direction) — evaluated and scoped out of this phase; worth revisiting as a follow-up phase once the basic footprint is live
- Alternate visual styles for footprint: numeric-cell annotations inside each candle, split-color stacked bars, per-candle volume-profile overlays — rejected in favor of the heatmap; can revisit if UX feedback warrants
- True tick-level / L2 footprint data — requires paid data feeds (Polygon, IEX Cloud, Databento); indefinitely out of scope for this academic showcase
- Footprint-specific lookback selector (7/14/30/60 day dropdown dedicated to the panel) — rejected in favor of the 60d hard cap for UI simplicity; revisit if users report wanting shorter windows
- Weighted-voice composite bias (footprint counts at 0.5 because it shares data source with Order Flow) — rejected; go with equal voting (1.0) for simplicity and revisit if correlation analysis shows double-counting is distorting the composite
- 6th cell populated with a summary card — rejected for this phase; leave placeholder empty for a future indicator

</deferred>

---

*Phase: 24-i-want-to-integrate-footprint-trading-indicator*
*Context gathered: 2026-04-21*
