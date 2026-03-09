# Phase 7: Auto-Run Extended Analysis After Scrape - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

After the main scrape completes, automatically trigger Regime Detection (per scraped ticker, 2-year window) and Portfolio MDP (fixed SPY/IEF pair, always) — results and per-module status badges appear inline at the top of the Analytics tab with no additional user action required. The scrape form, manual Stochastic Models tab, and RL tab are out of scope; this phase only wires auto-run into the existing post-scrape flow.

</domain>

<decisions>
## Implementation Decisions

### MDP Ticker Sourcing
- Always use SPY as equity ticker and IEF as bond ticker, regardless of what the user scraped
- MDP is a consistent "portfolio context" widget — not personalized to the scraped tickers
- Date range: rolling window — train on 5 years ending 2 years ago, test on most recent 2 years (relative to today)
- An interpretation blurb appears **above** the MDP chart explaining how to read the output: what each regime state means, how to read the optimal policy bar chart, and what "optimal policy" implies in plain English (e.g., "In a bull regime, the policy recommends holding more equity; in a bear regime, shift to bonds")

### Status Badge Placement
- Each auto-run section has an **inline header** with the badge: e.g., `Regime Detection — AAPL  ⏳ Running...`
- Badge updates in-place as the module finishes: ⏳ Running... → ✓ Done / ⚠ Failed
- No separate global badge row needed
- When auto-run starts, **auto-switch the user to the Analytics tab** (same pattern as existing switch to Stocks tab after scrape) so they see the badges updating live

### Analytics Tab Layout
- Auto-run results appear at the **top of the Analytics tab**, above existing analytics data
- Each ticker gets its own regime detection block showing:
  - Inline header with ticker name + badge (spinner while running, chart container while loading)
  - Both charts on completion: probability time series (P(Stressed)) + price chart with bull/bear shading
- Portfolio MDP block appears after all ticker regime blocks
- Loading state per ticker: `AAPL  ⏳ Running...` with a spinner placeholder where the charts will appear

### Failure UX
- If regime detection fails for a ticker: show ⚠ Failed badge + short inline error message (e.g., "Regime detection failed: insufficient data")
- Other tickers are unaffected — independent async calls, partial success is normal
- No retry button — user re-runs the full scrape to retry
- MDP failure follows the same pattern: ⚠ Failed badge + short error message inline in the MDP section

### Claude's Discretion
- Exact spinner HTML/CSS (reuse existing loading patterns from the app)
- Exact wording of the MDP interpretation blurb
- Chart container IDs for auto-run (must not collide with existing `#regimeProbChart`, `#regimePriceChart`, `#markovMDPChart` IDs used in other tabs)
- Whether auto-run is triggered inside `displayResults()` or as a chained `.then()` after it

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `runRegimeDetection()` in `stochasticModels.js`: Existing function fetches `/api/regime_detection`, parses response, and renders both Plotly charts. Auto-run must replicate this logic with dynamic container IDs (e.g., `#autoRegimeProb_AAPL`, `#autoRegimePrice_AAPL`) rather than the static IDs used by the manual tab.
- `runPortfolioMDP()` in `rlModels.js` (line 351): Existing function that calls `/api/stoch_portfolio_mdp`. Auto-run version calls this with hardcoded SPY/IEF and rolling date window.
- Plotly chart helpers: All chart rendering via `Plotly.newPlot()` — same pattern for auto-run charts.

### Established Patterns
- Post-scrape hook: `displayResults()` in `stockScraper.js` (line 131) fires after successful scrape. Auto-run should start here.
- Tab switching: `TabManager.switchTab('analytics')` — same function used to switch to Stocks tab post-scrape.
- Badge pattern: Inline `<span>` badges already used in the Analytics tab button (lines 152/154 of stockScraper.js) — replicate this style for per-module inline badges.
- Error display: `renderAlert()` helper used throughout for error HTML.

### Integration Points
- `stockScraper.js displayResults()`: Add auto-run trigger here after switching to Analytics tab
- `#analyticsResults` div: Auto-run section injected at the top before existing `DisplayManager.displayAnalytics()` output
- `/api/regime_detection` POST: Existing route, called once per ticker with `{ ticker, start_date, end_date }`
- `/api/stoch_portfolio_mdp` POST: Existing route, called once with SPY/IEF and rolling date window

</code_context>

<specifics>
## Specific Ideas

- MDP interpretation text (above chart): Explain that the policy output tells you which asset (SPY=equity or IEF=bonds) the model recommends holding in each market state; bull regime → equity, bear regime → bonds; the backtest line shows how the optimal policy would have performed vs a 60/40 static allocation.
- Chart container IDs must be unique per ticker to allow multiple regime charts on the same page simultaneously (e.g., `autoRegimeProb_AAPL`, `autoRegimeProb_MSFT`).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-auto-run-extended-analysis-after-scrape*
*Context gathered: 2026-03-10*
