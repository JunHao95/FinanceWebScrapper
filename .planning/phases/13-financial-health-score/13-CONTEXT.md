# Phase 13: Financial Health Score - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Each ticker card displays a composite financial health grade (A–F) at the bottom of the card, derived from already-scraped fields — no new network calls or scrape triggers. Phase 13 creates the `div.deep-analysis-group` container that Phases 14–16 will append their own sections into, so card HTML is not touched again in later phases.

</domain>

<decisions>
## Implementation Decisions

### Default visibility
- Deep Analysis section starts **collapsed** — only the section header with letter grade is visible inline (e.g., "🏥 Financial Health: B  ▼")
- User clicks to expand and see four sub-scores + one-sentence explanation
- Collapsed state shows: letter grade + section label (no sub-scores visible)
- Expand/collapse state is **persisted per session** — if a user expanded AAPL's Deep Analysis, it stays expanded until a new scrape runs
- Card placement: `div.deep-analysis-group` appended **inside** the existing `.ticker-content` div, after the metrics grid, at the bottom of each ticker card

### Trigger timing
- Score is computed **synchronously inside `createTickerCard()`** (displayManager.js) — no async, no loading placeholder
- All required fields are available in the scraped data object at render time, so no delay is needed
- Health score results (grade, sub-scores, explanation) are **also added to `pageContext`** so the FinancialAnalyst chatbot (Phase 12) can reference them

### Computation location
- New **`healthScore.js`** module — pure JS, client-side, no backend round-trip
- Exposed as `window.HealthScore = { computeGrade }` — consistent with DisplayManager, AutoRun, PortfolioHealth pattern
- Phases 14–16 will follow the same pattern (e.g., `window.EarningsQuality`, `window.DCFValuation`)
- **No new Flask route needed** for Phase 13 (data already in the browser)

### Scoring algorithm
- Four equal-weight sub-scores (25% each): **Liquidity, Leverage, Profitability, Growth**
- Each sub-score maps to a letter (A=4, B=3, C=2, D=1, F=0)
- Overall grade = average of four numeric scores, mapped back to A–F
- Use same scoring thresholds as `financial_analytics.py` for consistency:
  - **Liquidity**: Current Ratio, Quick Ratio
  - **Leverage**: Debt/Equity ratio
  - **Profitability**: ROE, ROA, Profit Margin
  - **Growth**: EPS Growth, Revenue Growth / Earnings Growth
- When a field is missing: sub-score still computed from available metrics with a warning flag (FHLTH-04); overall grade still rendered with visible indicator showing which component had incomplete data

### Claude's Discretion
- Exact numeric thresholds for each sub-score band (mirror `financial_analytics.py` logic)
- Raw metric value display within each sub-score row (whether to show "Liquidity: B — Current Ratio 1.8" or just "Liquidity: B")
- Exact CSS for the collapsed header and expanded panel (reuse `.badge` and `.metric-group` patterns)
- Element IDs and CSS class names for the deep-analysis-group and its children
- Exact wording template for the one-sentence explanation (e.g., "Strong {positive factor} offset by {negative factor}")

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `displayManager.js createTickerCard()`: Injection point for the deep-analysis-group; append after `</div>` closing the metrics-grid, inside `ticker-content`
- `.badge`, `.badge-success`, `.badge-danger`, `.badge-warning`, `.badge-info` (styles.css:824–836): Reuse for grade letter colour-coding
- `.metric-group` (styles.css:654): Existing group container pattern for sub-score rows
- `financial_analytics.py` scoring logic: Lines ~1457–1632 contain threshold logic for all four dimensions — replicate these thresholds in `healthScore.js`
- `autoRun.js` badge update pattern (`BADGE_RUNNING / BADGE_DONE / BADGE_FAILED`): Reference for inline badge styling if needed

### Established Patterns
- Window global module pattern: `window.DisplayManager`, `window.AutoRun`, `window.PortfolioHealth` — `window.HealthScore` follows the same
- `displayManager.js` uses inline HTML string construction — `healthScore.js` returns an HTML string that `createTickerCard()` appends
- Post-scrape `pageContext` update: Phase 12 established the pattern of updating `pageContext` after each piece of analysis; health score adds to that object

### Integration Points
- `displayManager.js createTickerCard(ticker, data)`: Call `HealthScore.computeGrade(data)` and append the returned HTML as `div.deep-analysis-group` inside `ticker-content`
- `pageContext` object (chatbot.js / stockScraper.js): After computing grade, write `pageContext.healthScores[ticker] = { grade, subScores, explanation }` for FinancialAnalyst awareness
- `index.html`: Add `<script src="/static/js/healthScore.js">` before `displayManager.js`
- Phases 14–16: Will call `document.querySelector('#ticker-content-{ticker} .deep-analysis-group').appendChild(...)` — the container must exist at card render time

</code_context>

<specifics>
## Specific Ideas

- Section header format (collapsed): `🏥 Financial Health: B  ▼` — follows the emoji-header style used in other ticker card groups
- Grade colour: A = green (`.badge-success`), B = light green, C = yellow (`.badge-warning`), D = orange, F = red (`.badge-danger`)
- Missing-data warning: small `⚠` flag next to the affected sub-score label (e.g., "Growth: N/A ⚠") rather than hiding the row entirely

</specifics>

<deferred>
## Deferred Ideas

- User-adjustable sub-score weights (sliders) — future phase or v2.2 enhancement
- Historical grade trend (how the grade changed over multiple scrapes) — requires persistence, out of scope

</deferred>

---

*Phase: 13-financial-health-score*
*Context gathered: 2026-03-22*
