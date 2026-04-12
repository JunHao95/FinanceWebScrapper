# Phase 21: Order Flow - Context

**Gathered:** 2026-04-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the Order Flow panel per ticker — a single Plotly chart showing green/red buy/sell pressure delta bars with a cumulative delta overlay line, imbalance candle annotations (▲/▼) on qualifying bars, and a volume divergence badge below the chart. Liquidity Sweep, Composite Bias, and tab wiring are out of scope (Phase 22).

</domain>

<decisions>
## Implementation Decisions

### Delta Chart Y-axis
- **Dual Y-axis**: delta bars on the left axis (raw volume units), cumulative delta line on the right axis (independent scale)
- Cumulative delta line color: **white / light grey** (`#cdd6f4`) — high contrast against dark background, distinct from green/red bars
- **Thin dashed zero line** drawn at y=0 on the delta bars axis — shows where buying flips to selling
- Right axis (cumulative delta) tick labels are **visible** — user can read the cumulative magnitude

### Divergence Flag Placement
- **Badge below the chart** — matches the VP and AVWAP badge pattern
- Badge is **always visible**: shows `✔ No divergence` in muted grey when trends align; shows `⚠ Volume Divergence` in red when detected
- Format on divergence: `⚠ Volume Divergence — price slope: +0.23, vol slope: −0.15` — **raw slope values shown** so user can verify signal magnitude

### Imbalance Candle Annotations
- **Plotly text annotations on the chart** — same annotation mechanism as AVWAP right-edge labels
- Label: **▲ for Bullish, ▼ for Bearish** (arrow symbols only — compact, unambiguous)
- Annotation color **matches bar color**: green ▲ above bullish imbalance bars, red ▼ below bearish imbalance bars
- Position: ▲ above the bar top, ▼ below the bar bottom

### Panel Structure
- **One Plotly chart** (500px height): delta bars + cumulative delta overlay + imbalance annotations all in a single figure
- Layout within ticker card: **below the AVWAP panel** — sequence is VP → AVWAP → Order Flow
- **Brief legend panel** below the badge, consistent with VP legend pattern, explaining: green = buy pressure, red = sell pressure, white line = cumulative delta, ▲/▼ = imbalance candle

### Claude's Discretion
- Exact Plotly `yaxis2` range configuration and tick formatting
- Zero-line style (color, dash pattern, width)
- Annotation font size and offset from bar top/bottom
- Legend HTML structure (reuse `ti-legend` CSS class pattern)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `compute_order_flow(df)` stub at `trading_indicators.py:402` — replace with real implementation
- `fetch_ohlcv(ticker, days)` at `trading_indicators.py:28` — canonical OHLCV fetch; use with `days=lookback` (no 365-day separate fetch needed for Order Flow)
- `_renderTickerCard()` in `tradingIndicators.js:34` — extend by appending Order Flow div + badge + legend after the AVWAP block (lines 148+)
- `ti-va-badge` CSS class — established badge style for signal display below charts
- `ti-legend` CSS class — established legend panel style (VP legend at lines 42–72 of tradingIndicators.js)

### Established Patterns
- Dark Catppuccin theme: `paper_bgcolor='#1e1e2e'`, `plot_bgcolor='#1e1e2e'`, `font color='#cdd6f4'`
- Plotly shapes dict (`type`, `xref`, `yref`) for reference lines — use for zero line
- Plotly annotations dict for on-chart text — same mechanism as AVWAP right-edge labels
- `{ staticPlot: true, responsive: true }` render options — use for Order Flow chart
- Badge pattern: `#2ecc71` for positive/clean signals, `#e74c3c` for warning/divergence signals, `#7f849c` for muted/neutral

### Integration Points
- `webapp.py` `/api/trading_indicators` route: replace `order_flow: {'status': 'stub'}` with real `compute_order_flow(df)` output `{traces, layout, signal, divergence}`
- `tradingIndicators.js` `_renderTickerCard()`: add Order Flow chart div + badge div + legend div after the AVWAP legend block
- `compute_order_flow` receives the OHLCV `df` already fetched by the route handler (same `lookback` window used for VP/AVWAP display)

</code_context>

<specifics>
## Specific Ideas

- Delta bar computation: `(Close − Low) / (High − Low) × Volume` proxy with epsilon guard on zero-range bars (as specified in FLOW-01)
- Volume divergence: 10-bar rolling linear regression slope on price and volume — flag when slopes have opposite signs
- Imbalance candle criteria: body > 70% of high-low range AND volume > 1.2× 20-day average (as specified in FLOW-03)
- The Order Flow chart is a bar chart (not candlestick) — x-axis is dates, bars are per-day delta values

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 21-order-flow*
*Context gathered: 2026-04-12*
