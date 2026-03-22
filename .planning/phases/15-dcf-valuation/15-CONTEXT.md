# Phase 15: DCF Valuation - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Each ticker card displays a 2-stage FCF-based intrinsic value estimate (price per share) alongside the current market price premium or discount. Three user-overridable inputs (WACC, Stage 1 growth rate, Stage 2 terminal growth rate) allow local recalculation without triggering a new scrape. Phase 15 appends its section into the existing `div.deep-analysis-group` container created in Phase 13.

</domain>

<decisions>
## Implementation Decisions

### DCF model
- **2-stage DCF model**: Stage 1 = 5 explicit annual FCF projections discounted at WACC; Stage 2 = Gordon Growth terminal value using terminal growth rate
- Formula:
  - Stage 1: Σ FCFₜ / (1+WACC)^t for t = 1..5, where FCFₜ = FCF₀ × (1+g₁)^t
  - Stage 2: Terminal = FCF₅ × (1+g₂) / (WACC − g₂); PV(Terminal) = Terminal / (1+WACC)^5
  - Intrinsic equity value = Stage 1 + PV(Terminal)
  - Per-share value = Intrinsic equity value / Shares Outstanding
- **Forecast horizon fixed at 5 years** — not user-overridable
- **Raw latest FCF** used (no smoothing/averaging)

### Default assumptions
- WACC: **10%**
- Stage 1 FCF growth rate: **10%**
- Stage 2 terminal growth rate: **3%**

### Input UX
- Input fields (WACC, Stage 1 growth, Stage 2 growth) are **inline, always visible** when the DCF section is expanded
- Inputs are `<input type="number">` with `%` suffix labels — not sliders
- Recalculation is triggered by a **"Recalculate" button** (not on-change/on-blur) — avoids mid-type flickering
- Clicking Recalculate updates intrinsic value and premium/discount percentage in-place without scraping

### FCF data source
- Priority: **Alpha Vantage first** (`Free Cash Flow (AlphaVantage)`), fall back to Yahoo Finance (`Free Cash Flow (Yahoo)`)
- Both use the same `extractMetric` alias pattern from prior modules
- **Source footnote**: Small label shown below the estimate (e.g., "FCF source: Alpha Vantage")
- When FCF is absent or zero: render "DCF unavailable — FCF data missing", suppress all numeric outputs (per DCF-05)
- When FCF is available but Shares Outstanding can't be derived (Market Cap or Current Price missing): show **total intrinsic equity value in $ billions** without a per-share figure; skip premium/discount calculation; section still renders

### Shares Outstanding derivation
- Derived as: `Shares Outstanding = Market Cap (Yahoo) / Current Price (Yahoo)`
- Both fields already present in scraped payload

### Premium / discount display
- Signed percentage: e.g., "+23% premium" (green) or "−11% discount" (red)
- Formula: `(currentPrice − intrinsicValue) / intrinsicValue × 100`
- Positive = market price above intrinsic = premium (overvalued signal)
- Negative = market price below intrinsic = discount (undervalued signal)

### Claude's Discretion
- Exact CSS for input row layout, button styling, and footnote typography
- Element IDs and CSS class names for DCF section elements
- Handling of WACC ≤ terminal growth rate (guard: show error inline if WACC ≤ g₂ to avoid division by zero)
- Exact wording for section header in collapsed state (follow emoji-header pattern from Phase 13/14)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `earningsQuality.js` (Phase 14): Full module pattern to replicate — `parseNumeric`, `extractMetric`, IIFE, `window.DCFValuation = { computeValuation, renderIntoGroup, clearSession }`
- `healthScore.js` (Phase 13): Same pattern; `renderIntoGroup` queries `#deep-analysis-content-{ticker}` and silently returns if not found
- `.badge`, `.badge-success`, `.badge-danger`, `.badge-warning` (styles.css:824–836): Reuse for premium/discount colour-coding
- `displayManager.js createTickerCard()`: Already calls `EarningsQuality.renderIntoGroup(ticker, data, div)` — Phase 15 adds a parallel call for `DCFValuation.renderIntoGroup`

### Established Patterns
- Window global module pattern: `window.DCFValuation` follows `window.HealthScore` / `window.EarningsQuality`
- `extractMetric(data, aliases)` — alias-based field lookup with null-safe parsing, already implemented in earningsQuality.js
- Post-scrape `pageContext` update: write `pageContext.tickerData[ticker].dcfValuation = { intrinsicValue, premium, wacc, g1, g2, fcfSource }` for FinancialAnalyst chatbot

### Integration Points
- `displayManager.js createTickerCard(ticker, data)`: Add `DCFValuation.renderIntoGroup(ticker, data, div)` call after EarningsQuality call
- `index.html`: Add `<script src="/static/js/dcfValuation.js">` after earningsQuality.js and before displayManager.js
- `stockScraper.js`: Write dcfValuation results into `pageContext.tickerData[ticker]` after render
- FCF fields already in scraped payload: `Free Cash Flow (AlphaVantage)`, `Free Cash Flow (Yahoo)`, `Current Price (Yahoo)`, `Market Cap (Yahoo)`

</code_context>

<specifics>
## Specific Ideas

- 2-stage model was chosen to reflect a realistic High-Growth Phase (5 years) followed by a Stable Growth phase — user's framing
- Collapsed section header should follow the emoji-header pattern: e.g., "💰 DCF Value: $142.30  ▼"
- When shares can't be derived, show equity value label clearly: e.g., "Intrinsic Equity Value: $84.2B (per-share unavailable)"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 15-dcf-valuation*
*Context gathered: 2026-03-23*
