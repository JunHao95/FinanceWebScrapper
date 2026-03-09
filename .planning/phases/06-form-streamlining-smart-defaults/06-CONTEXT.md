# Phase 6: Form Streamlining & Smart Defaults - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Reduce the stock analysis form to ticker-only required input with one-click defaults: data sources default silently when Advanced is collapsed, allocation supports % Weight and Value modes with live % feedback, and the submit button is prominently labelled "▶ Run Analysis". Creating new backend routes or triggering auto-analyses are out of scope (Phase 7).

</domain>

<decisions>
## Implementation Decisions

### Value mode partial fill
- Blank ticker in Value mode = 0 allocation = excluded from portfolio (not an error, not equal share)
- This is the current behavior in `getPortfolioAllocation()` — confirm and keep
- When ALL value fields are blank: fall back to equal weights AND show a subtle info hint near the allocation section (e.g., "No values entered — equal weights will be used")
- The hint should only appear when mode is Value and all inputs are empty/zero

### Value mode live feedback
- Live "→ XX.X%" label appears immediately as any value is typed — does not wait for all tickers to have values
- Percentages reflect entered amounts over running total of entered amounts (current behavior — confirm and keep)

### Mode switching
- Switching between % Weight and Value mode clears all allocation inputs (current behavior — confirm and keep)
- Currency selector appears only in Value mode (current behavior — confirm and keep)

### Smart defaults (collapse behavior)
- No additional discussion requested; behavior from FORM-03: use `['yahoo', 'finviz', 'google', 'technical']` when Advanced is collapsed
- Current code already implements this in `stockScraper.js` — verify it's correct end-to-end

### Hero layout
- No additional discussion requested; FORM-08 asks for "prominent hero layout" — Claude's discretion on visual treatment (button sizing, spacing, ticker input prominence)

### Claude's Discretion
- Hero button visual treatment (size, width, color weight)
- Exact wording and placement of the "equal weights" hint in Value mode
- Whether to add a small "Using defaults: all free sources" note when Advanced is collapsed (subtle, optional)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `FormManager` in `static/js/forms.js`: Full allocation logic already implemented — `switchAllocationMode()`, `updateAllocationInputs()`, `calculateAllocationTotal()`, `getPortfolioAllocation()`
- `static/js/stockScraper.js` lines 49-68: Smart defaults logic already present — `advancedDetails.open` check, falls back to `['yahoo', 'finviz', 'google', 'technical']` when collapsed
- `#currencySelect`, `#modePercentBtn`, `#modeValueBtn`, `#allocationSection`, `#allocationInputs`, `#allocationTotal` — all DOM elements already present in `templates/index.html`
- `<details id="advanced-settings">` — collapsible section already in HTML, collapsed by default

### Established Patterns
- `.hero-input-group` CSS class already exists for ticker input — hero layout partially in place
- `allocation-pct-label` span with `id="alloc-pct-${ticker}"` already emits "→ XX.X%" in value mode
- `calculateAllocationTotal()` already updates per-ticker pct labels on every input event

### Integration Points
- The equal-weights hint needs to appear inside `#allocationSection` (or near `#allocationTotal`) in Value mode
- `getPortfolioAllocation()` returns `null` when all values are zero — backend treats null as equal-weight allocation
- Backend `run_scrapers_for_ticker()` in `webapp.py` already handles `['yahoo', 'finviz', 'google', 'technical']` via the `'yahoo' in sources` / `'finviz' in sources` checks (lines 208-215)

### Gaps to Address
- Equal-weights hint: not currently shown — needs to be added to `calculateAllocationTotal()` in Value mode when all inputs are 0
- End-to-end verification: confirm that submitting with Advanced collapsed actually reaches backend with correct 4 default sources (quick smoke test)

</code_context>

<specifics>
## Specific Ideas

- No specific visual references given — open to standard approaches for hero layout
- Equal-weights hint should be subtle (small text, secondary color) — not a warning or error styling

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-form-streamlining-smart-defaults*
*Context gathered: 2026-03-09*
