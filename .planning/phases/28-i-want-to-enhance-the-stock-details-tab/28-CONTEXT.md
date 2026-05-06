# Phase 28: Enhance the Stock Details Tab - Context

**Gathered:** 2026-05-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Enhance the existing "📊 Stock Details" tab — the first tab showing CNN Fear & Greed Index and per-ticker collapsible cards. Enhancements cover: adding a price history chart, visualizing analyst price targets, improving metric display quality with color coding and tooltips, and restructuring the long ticker card into sub-tabs. No new data sources, no new backend compute features.

</domain>

<decisions>
## Implementation Decisions

### Price chart
- **Style:** Candlestick chart via Plotly (consistent with existing ML Signals and Trading Indicators charts)
- **Timeframe selector:** 1M / 3M / 6M / 1Y toggle buttons (four presets)
- **Placement:** Top of each expanded ticker card, before all other content
- **Overlays:** Volume bars as a subplot below the candlestick — no MA overlays (MAs already shown as separate metric rows)
- **Backend requirement:** New endpoint needed to serve OHLC + volume historical data per ticker (yfinance `Ticker.history()`)

### Analyst price target visualization
- **Style:** Horizontal range bar showing Low–Mean–High analyst target range with current price as a dot/marker overlay
- **Consensus badge:** Show Buy/Hold/Sell consensus badge alongside the range bar (using existing Finhub/Yahoo recommendation data already scraped)
- **Placement:** After price chart, before the metrics grid — creates flow: visual price history → analyst outlook → detailed numbers
- **Backend:** No new endpoint needed; data already in scrape response (`Analyst Price Target Mean/Low/High (Yahoo)`, `Analyst Price Target Mean/Low/High (Finhub)`)

### Metrics display quality
- **Color coding:** Threshold-based — fixed thresholds per metric (e.g. P/E > 30 = red, ROE > 15% = green, Debt/Equity > 2 = red). Color only on key financial ratios, not all metrics.
- **Trend arrows:** None — color coding is sufficient; trend arrows would require backend YoY delta data not currently scraped
- **Tooltips:** Hover tooltip on key metrics only: P/E, Forward P/E, P/B, P/S, PEG, EV/EBITDA, ROE, ROA, ROIC, Profit Margin, Operating Margin, Debt/Equity, Current Ratio. Plain text definition shown on hover. Pure frontend — no backend change needed.

### Ticker card layout (sub-tabs)
- **Structure:** Five sub-tabs inside each expanded ticker card:
  - **Overview** — price chart + analyst target range bar + Basic Info metrics (Company Name, Sector, Industry, Exchange, Description)
  - **Financials** — Valuation + Profitability + Earnings + Financial Metrics + Cash/CashFlow metric groups
  - **Technical** — RSI, MA10/20/50, BB Signal metrics
  - **Sentiment** — full Sentiment Analysis block (Google Trends, News, Reddit, FinBERT)
  - **Deep Analysis** — Health Score (Phase 13) + Earnings Quality (Phase 14) + DCF Valuation (Phase 15) + Peer Comparison (Phase 16) + Fundamental Analysis
- **Active tab persistence:** Active sub-tab per ticker persists in sessionStorage (consistent with existing `SectionCollapse` pattern using `collapse-{ticker}-{section}` key scheme)
- **Default:** Overview sub-tab active when ticker card first opened

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Plotly` (already loaded globally): Use `Plotly.newPlot` for candlestick + volume subplot — same pattern as Trading Indicators and ML Signals charts
- `SectionCollapse` (`displayManager.js`): sessionStorage pattern for per-ticker state — extend same scheme for sub-tab persistence
- `DisplayManager.createTickerCard` (`displayManager.js:99`): Entry point for all ticker card HTML — sub-tab markup and price chart injection go here
- `AnalyticsRenderer.renderFundamental` (`analyticsRenderer.js:24`): Currently injected at top of ticker card — move into Deep Analysis sub-tab
- `HealthScore`, `EarningsQuality`, `DCFValuation`, `PeerComparison`: Already injected via `renderIntoGroup` calls in `createTickerCard` (lines 185–203) — move into Deep Analysis sub-tab
- `Utils.formatValue` (`utils.js`): Already used for metric value formatting — extend for color-coded output

### Established Patterns
- **Plotly dark theme:** All existing charts use Catppuccin-dark theme (`#1e1e2e` background, `#cdd6f4` text) — price chart must match
- **Lazy-load on tab switch:** Trading Indicators and ML Signals fetch data when tab is activated (`tabs.js:56–88`). Price chart should fetch OHLC data when sub-tab is first opened, not on initial scrape.
- **Per-ticker fetch pattern:** `TradingIndicators.fetchForTicker(ticker)` and `MLSignals.fetchForTicker(ticker)` — price chart follows same async fetch pattern
- **Metrics groups object** (`displayManager.js:115–130`): `groups` object defines which metric keys go in which section — extend to route metrics into correct sub-tabs

### Integration Points
- `DisplayManager.createTickerCard`: Restructure to emit sub-tab markup; move existing metric groups into Financials/Technical/Sentiment sub-tabs
- `stockScraper.js:displayResults`: No change needed — ticker data already passed to `createTickerCard`
- New `GET /api/price_history?ticker=AAPL&period=3mo` endpoint in `webapp.py` — returns OHLC + volume JSON for Plotly candlestick
- `tabs.js` `validTabs`: No change needed — sub-tabs are within the existing 'stocks' tab, not top-level tabs

</code_context>

<specifics>
## Specific Ideas

- Sub-tab layout mocked as: `[Overview][Financials][Technical][Sentiment][Deep Analysis]` across the top of the expanded ticker card, with content below switching per selection
- Analyst range bar: horizontal bar from Low to High, mean shown as a tick/label in the middle, current price as a colored dot (green if below mean target = upside, red if above = overvalued relative to consensus)
- Metric tooltips: appear on hover over the metric label (not value), simple CSS tooltip — no library needed

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 28-i-want-to-enhance-the-stock-details-tab*
*Context gathered: 2026-05-06*
