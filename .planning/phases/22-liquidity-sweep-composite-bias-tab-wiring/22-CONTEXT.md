# Phase 22: Liquidity Sweep + Composite Bias + Tab Wiring - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete the 4th Trading Indicators tab — implement Liquidity Sweep detection (adaptive n, OHLCV candlestick chart, arrow markers, dashed swept-level lines); build the composite bias badge (dissenter identification, unavailable handling); wire the tab UI (2×2 CSS grid per ticker, lookback dropdown in tab header, cache-clear + progressive re-fetch on change). All 9 requirements (SWEEP-01–03, BIAS-01–03, TIND-01–03) must be satisfied.

</domain>

<decisions>
## Implementation Decisions

### Sweep chart visualization
- **Base chart**: Full OHLCV candlestick chart as backdrop — sweep markers sit on the actual candles that triggered the sweep, preserving wick context
- **Sweep markers**: Plotly text annotation (▲ above for Bullish, ▼ below for Bearish) on the sweep candle — same annotation mechanism as Order Flow imbalance candles
- **Swept price level**: One dashed horizontal line per sweep event drawn at the swept price; not one line per swing (avoids clutter)
- **Badge states and colors**:
  - Bullish Sweep: green (#2ecc71) — "✔ Bullish Sweep — last confirmed sweep at $X.XX"
  - Bearish Sweep: red (#e74c3c) — "⚠ Bearish Sweep — last confirmed sweep at $X.XX"
  - No Sweep: grey (#7f849c) — "— No Sweep in selected window (n=X)"
  - No confirmed swings: grey (#7f849c) — "— No confirmed swings in selected window (n=X)"

### 2×2 grid layout
- **Architecture**: CSS 2-column flex/grid layout with 4 separate Plotly divs — NOT a single Plotly `make_subplots(rows=2, cols=2)`
  - Minimal restructuring: existing VP, AVWAP, and Order Flow rendering code stays intact; just wrap their divs in a grid container and append the Sweep panel
  - Grid: `display: grid; grid-template-columns: 1fr 1fr; gap: 16px`
- **Panel order**: VP (top-left), AVWAP (top-right), Order Flow (bottom-left), Liquidity Sweep (bottom-right)
- **Panel height**: Equal 500px per panel — consistent with existing VP/AVWAP/Order Flow heights
- **Cell contents**: Each cell is self-contained: chart div + badge div + legend div (no shared legend)
- **Unavailable panel**: If a sub-indicator fails, render a grey placeholder div in its grid cell ("Liquidity Sweep unavailable") instead of an empty/missing cell

### Composite bias badge
- **Position**: Top of each ticker card, before the 2×2 grid — summary-first reading order
- **Format**: `● Bullish (3/4) — Order Flow dissents` with dot color: green (Bullish majority), red (Bearish majority), grey (Neutral / split)
- **Brief rationale**: Include a short one-line rationale naming the dissenting indicator(s) — e.g. "Order Flow dissents" or "AVWAP, Sweep dissent"
- **BIAS-02 caveat**: Muted line below the badge: "Trend-following bias — all indicators share the same OHLCV data source."
- **BIAS-03 unavailable handling**: Failed sub-indicators excluded from denominator (e.g., "3/4 indicators"); badge explicitly names which is unavailable ("Sweep unavailable")

### Lookback dropdown + refetch UX
- **Position**: Tab header bar, right-aligned — "Trading Indicators  90d ▼" — single global control for all tickers
- **Options**: 30 / 90 / 180 / 365 days
- **Default**: 90 days (matches existing hardcoded default in fetchForTicker calls; n=3 for sweep detection)
- **On change behavior**:
  1. `clearSession()` fires immediately
  2. All existing ticker cards removed from DOM
  3. Per-card "Loading…" placeholder divs rendered for each scraped ticker
  4. `fetchForTicker(ticker, newLookback)` called for each ticker
  5. Cards appear progressively as each ticker's fetch resolves (no waiting for all)

### Claude's Discretion
- Exact CSS class names and styling for the 2-column grid wrapper
- Candlestick colors for the Sweep chart (may reuse Catppuccin green/red or neutral)
- Annotation font size and offset from candle tip for sweep markers
- "Loading…" placeholder height and spinner style
- Exact HTML structure of the tab header bar dropdown

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `compute_liquidity_sweep(df)` stub at `trading_indicators.py:537` — replace with real implementation; receives OHLCV df already fetched by route handler
- `compute_composite_bias(results)` stub at `trading_indicators.py:541` — replace with real implementation; receives dict of all 4 indicator results
- `fetch_ohlcv(ticker, days)` at `trading_indicators.py:28` — canonical OHLCV fetch; already used by route handler
- `fetchForTicker(ticker, lookback)` in `tradingIndicators.js:11` — already has session cache keyed by `ticker + '-' + lookback`; already calls the API with lookback param
- `clearSession()` in `tradingIndicators.js:7` — already implemented; just needs to be wired to dropdown change event
- `_renderTickerCard(container, ticker, lookback, resp)` in `tradingIndicators.js:34` — extend to use 2×2 grid layout and add Sweep panel
- `ti-va-badge` CSS class — established badge style (color, font-weight, font-size, display:block)
- `ti-legend` CSS class — established legend panel HTML structure used by VP, AVWAP, Order Flow

### Established Patterns
- Dark Catppuccin theme: `paper_bgcolor='#1e1e2e'`, `plot_bgcolor='#1e1e2e'`, `font color='#cdd6f4'`
- Plotly shapes dict for reference lines (type, xref, yref) — use for dashed swept-level line
- Plotly annotations dict for on-chart text — same mechanism as AVWAP right-edge labels and Order Flow imbalance annotations
- `{ staticPlot: true, responsive: true }` for all indicator Plotly charts (TIND-03)
- Badge colors: `#2ecc71` positive, `#e74c3c` warning, `#7f849c` muted/neutral
- Python payload shape: `{traces, layout, signal, ...}` — Sweep must follow this convention

### Integration Points
- `webapp.py` `/api/trading_indicators` route: replace `liquidity_sweep: {'status': 'stub'}` with real `compute_liquidity_sweep(df)` output; add `composite_bias` key from `compute_composite_bias(results)`
- `tradingIndicators.js` `_renderTickerCard()`: restructure card layout to 2-column CSS grid; add Sweep panel in bottom-right cell; move composite bias badge above the grid
- Tab HTML in `index.html` or tabs.js: add lookback dropdown to the Trading Indicators tab header area; wire `onchange` to `clearSession()` + re-trigger fetch for all scraped tickers

</code_context>

<specifics>
## Specific Ideas

- Sweep detection uses adaptive n: n=2 for 30d lookback, n=3 for 90d, n=5 for 180d+; this is already specified in SWEEP-02 and must be implemented with look-ahead-safe loop bounds (regression test: swing indices on 90-day data must not shift when re-run on 91 days)
- Composite bias: majority direction wins (3+ of 4); ties → Neutral; count excludes failed/unavailable sub-indicators
- The 2-column grid wrapper should be added inside `_renderTickerCard()` — the existing VP, AVWAP, and Order Flow divs are placed into grid cells; the new Sweep div goes in the 4th cell

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 22-liquidity-sweep-composite-bias-tab-wiring*
*Context gathered: 2026-04-18*
