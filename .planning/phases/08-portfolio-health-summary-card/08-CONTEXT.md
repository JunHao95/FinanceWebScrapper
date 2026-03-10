# Phase 8: Portfolio Health Summary Card - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

A compact Portfolio Health card appears above the tab nav (between `<h2>📈 Analysis Results</h2>` and `.tabs-container`) once the scrape completes, showing portfolio VaR (95%), portfolio Sharpe ratio, and a regime label per ticker. Each metric links to its relevant analytics section. The card is purely presentational — no new models or analytics pipelines, only surfacing values already computed by existing routes plus one new lightweight Sharpe endpoint.

</domain>

<decisions>
## Implementation Decisions

### Card timing & updates
- Card appears immediately after scrape completes (progressive reveal) — VaR and Sharpe are populated right away from analytics data
- Regime slots show "Analyzing..." while auto-run is in progress, then update in-place as each ticker's regime detection completes
- No explicit "fully loaded" signal needed — slots just transition naturally from "Analyzing..." to their final colored badges
- On re-run: card is cleared and rebuilt fresh (same pattern as `#autoRunSection` removal in autoRun.js)

### Visual layout
- Compact single-row layout: `[VaR 95%: 12.3%] | [Sharpe: 1.42] | [AAPL: RISK_ON 🟢] [MSFT: RISK_OFF 🔴]`
- Card sits above `.tabs-container` inside `#resultsSection`, below the `<h2>` heading
- Regime labels are color-coded badges: RISK_ON = green, RISK_OFF = red/amber
- Overall traffic-light status icon (green/amber/red) is regime-driven:
  - All tickers RISK_ON → green
  - Mixed (some RISK_ON, some RISK_OFF) → amber
  - Majority RISK_OFF → red
- A one-line action-oriented summary appears below the metric row, e.g.:
  - "Portfolio is in a mixed regime — consider reviewing MSFT (RISK_OFF)."
  - "All tickers in risk-on regime — portfolio positioned for growth."
  - "Majority of holdings in risk-off regime — consider defensive rebalancing."
- Single-ticker mode: card shows VaR, Sharpe, and that ticker's regime — no correlation/PCA entries

### Sharpe data source
- New backend endpoint: `/api/portfolio_sharpe`
  - Accepts: list of tickers + allocation weights + date range
  - Computes: annualized portfolio-level Sharpe using weighted combined returns over the 2-year window (matching regime detection window)
  - Risk-free rate: fetch current 3-month T-bill rate via Yahoo Finance (`^IRX`)
  - Returns: `{ sharpe: float, rf_rate: float, period: string }`
- Called once after scrape completes, in parallel with auto-run regime calls
- Result appears in the health card immediately when the endpoint responds

### Metric navigation (click behavior)
- Claude's Discretion — standard approach: clicking a metric switches to the relevant tab using existing `switchTab()`, no custom scroll-to-anchor needed for MVP

### Claude's Discretion
- Exact HTML/CSS for the compact card (reuse existing badge and card styles from the app)
- Exact wording of the one-line summary signals per regime combination
- Element ID for the health card (`#portfolioHealthCard`)
- Whether the Sharpe metric has a loading state ("Computing...") while the endpoint responds, or shows a spinner inline
- T-bill fetch fallback: if `^IRX` fetch fails, fall back to rf=0% silently

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `autoRun.js triggerAutoRun(tickers)`: Entry point after scrape. Health card trigger should be added here — regime slot updates can call back into the health card once each ticker resolves.
- `BADGE_RUNNING / BADGE_DONE / BADGE_FAILED` inline styles in `autoRun.js`: Reuse for regime slots in the health card.
- `switchTab(tabName)` in `tabs.js`: Existing function for metric click navigation.
- VaR (95%) extraction: `analyticsRenderer.js:372-374` — `mc.VaR["VaR at 95% confidence"].Percentage / 100`. Available from analytics result data already passed to the renderer.

### Established Patterns
- `#autoRunSection` cleared and rebuilt on re-run: health card should follow same pattern.
- Progressive badge updates: auto-run regime uses `document.getElementById('autoRegimeBadge_' + ticker)` to update in-place — replicate for regime slots in health card.
- Post-scrape hook: `stockScraper.js displayResults()` fires after scrape; auto-run already triggered here. Health card initialization should also happen here.

### Integration Points
- `#resultsSection`: Card inserts as first child after `<h2>`, before `.tabs-container`
- `/api/regime_detection` response: `data.filtered_probs` last value ≥ 0.5 → RISK_OFF, else RISK_ON (regime label derivation for health card)
- Analytics result data: VaR passed through existing `displayAnalytics()` → `analyticsRenderer.js` pipeline; health card needs to intercept or receive the same data object
- `/api/portfolio_sharpe` (new): called in parallel with regime calls in `triggerAutoRun` or a new health card init function

</code_context>

<specifics>
## Specific Ideas

- User's stated goal: "provide insightful feedback for the portfolio from the user input tickers and re-adjust" — the one-line summary signal directly serves this intent. The signal should name specific tickers in risk-off regime to prompt action.
- One-line signal examples:
  - All RISK_ON: "All holdings in risk-on regime — portfolio positioned well."
  - Mixed: "Mixed regime detected — MSFT in risk-off, consider rebalancing toward AAPL."
  - All RISK_OFF: "All holdings in risk-off regime — consider defensive rebalancing or cash."

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-portfolio-health-summary-card*
*Context gathered: 2026-03-10*
