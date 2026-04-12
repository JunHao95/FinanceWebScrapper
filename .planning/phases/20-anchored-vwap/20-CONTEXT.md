# Phase 20: Anchored VWAP - Context

**Gathered:** 2026-04-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Compute three Anchored VWAP lines (anchored to the 52-week high date, 52-week low date, and last earnings date) and display them overlaid on a dedicated price candlestick chart within the Trading Indicators panel. Each line shows a right-edge distance label; a convergence badge appears when any AVWAP line is within 0.3% of current price. Earnings fallback is handled gracefully. Order Flow, Liquidity Sweep, and Composite Bias are out of scope for this phase.

</domain>

<decisions>
## Implementation Decisions

### Chart Layout
- AVWAP gets its **own standalone candlestick chart** — separate from the Volume Profile panel. VP stays clean with its histogram; AVWAP is a distinct panel below it.
- The chart renders the user's **selected display lookback** (e.g. 90 days) as the visible candle window.
- AVWAP lines **start from the anchor date and run to today**. If the anchor is outside the display window, the line begins at the left edge of the chart (clipped at chart start, not truncated).
- **500px height**, matching Volume Profile.
- A **thin horizontal dashed line at current price** (last close) is added as a reference line for easy visual comparison to AVWAP levels.
- Three lines are distinguished by **color only (all solid)**:
  - 52-wk High AVWAP → blue
  - 52-wk Low AVWAP → orange
  - Earnings AVWAP → purple

### Right-Edge Labels
- Labels rendered as **Plotly annotations anchored to the right edge of the chart** at each AVWAP's y-level (not an HTML block below).
- Label format: **name + distance**, e.g. `52-wk High: +2.1%` (not just the distance alone).
- Label color **matches the AVWAP line color** (blue/orange/purple) for visual linking.

### Convergence Warning
- When any AVWAP line is **within 0.3% of the current price**, a warning badge appears **below the chart** (same position as the VP signal badge).
- Warning format: `⚠ Convergence: [line name] AVWAP within 0.3% of current price at $X.XX`
- When **no convergence** exists, show a muted `✓ No AVWAP convergence` badge (always visible, not hidden).

### Earnings Anchor Source
- Use **`yf.Ticker(ticker).calendar`** to retrieve the last earnings date. No new dependency — already imported in the codebase.
- When yfinance returns no earnings date: show a **text note below the chart** (not a badge): `"Earnings anchor unavailable — only 52-wk high & low lines shown."` The chart still renders the two remaining AVWAP lines normally.

### OHLCV Fetch Strategy
- **Always fetch 365 days** for anchor resolution (to find 52-wk high/low dates and earnings anchor). This is a separate call from the display fetch.
- The **display chart shows only the user-selected lookback** (e.g. 90 days), but AVWAP is computed from the full 365-day dataset for accurate anchor positioning.

### Claude's Discretion
- Exact Plotly annotation xanchor/xref positioning for right-edge labels
- Color shading or opacity of the current-price reference line
- Badge CSS styling (reuse `ti-va-badge` class or minor variant)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `fetch_ohlcv(ticker, days)` in `trading_indicators.py`: canonical OHLCV fetch — call with `days=365` for anchor resolution
- `compute_anchored_vwap(df)` stub in `trading_indicators.py`: replace with real implementation
- `tradingIndicators.js` `_renderTickerCard()`: already renders VP chart + badge per ticker — extend to also render AVWAP panel in the same card
- `ti-va-badge` CSS class: established badge pattern for signal display

### Established Patterns
- Dark Catppuccin theme: `paper_bgcolor='#1e1e2e'`, `plot_bgcolor='#1e1e2e'`, `font color='#cdd6f4'`
- Plotly shapes (dict with `type`, `xref`, `yref`) used for VP lines — same approach for AVWAP lines and price reference
- Flask route at `webapp.py:2154` returns `anchored_vwap: {'status': 'stub'}` — replace stub with real payload `{traces, layout, signal, labels, convergence}`
- `xaxis_rangeslider_visible=False`, `margin=dict(l=70, r=20, t=70, b=50)` from VP — reuse

### Integration Points
- `webapp.py` `/api/trading_indicators` route: change `anchored_vwap` from stub to real `compute_anchored_vwap(df, ticker, lookback)` output
- `tradingIndicators.js` `_renderTickerCard()`: add AVWAP chart div + badge div after the VP chart block
- `compute_anchored_vwap` must accept `ticker` and `lookback` params (not just `df`) to perform the 365-day fetch internally

</code_context>

<specifics>
## Specific Ideas

- AVWAP line visual: solid colored lines (blue/orange/purple) overlaid on candlestick — no fill between lines
- Right-edge label placement: Plotly annotation with `xref='paper'`, `x=1.01` to push slightly past the right axis edge
- Earnings fallback note is plain grey text, not a styled badge, to signal it's informational not a signal

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 20-anchored-vwap*
*Context gathered: 2026-04-12*
