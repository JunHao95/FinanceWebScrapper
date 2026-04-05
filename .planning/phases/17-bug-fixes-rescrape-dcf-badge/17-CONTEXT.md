# Phase 17: Bug Fixes — Re-scrape & DCF Badge - Context

**Gathered:** 2026-04-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix two runtime bugs identified in the v2.1 milestone audit (BREAK-01 and BREAK-02) and update REQUIREMENTS.md to mark all 19 v2.1 requirements as `[x] Complete`. Also address tech debt item MISS-01 (async pageContext write for peer comparison).

- **BREAK-01**: `PeerComparison.clearSession()` never called before re-scrape → peer section silently skips on second scrape of same ticker (`peerComparison.js` line 201 guard never cleared).
- **BREAK-02**: `buildHTML` in `dcfValuation.js` renders initial premium badge inline AND creates a hidden `#dcf-premium-{ticker}` div; `_recalculate` shows the hidden div but leaves the original badge — two badges visible after first recalculate.
- **MISS-01** (tech debt): `pageContext.tickerData[ticker].peerComparison` written async inside fetch callback in `peerComparison.js` but timing is already correct — confirm write happens after fetch resolves inside the module.

No new features in this phase. Scope is: two JS bug fixes + one async context write fix + REQUIREMENTS.md documentation update.

</domain>

<decisions>
## Implementation Decisions

### clearSession call breadth (BREAK-01)
- Call `clearSession()` on **all 4 deep-analysis modules** before each re-scrape: HealthScore, EarningsQuality, DCFValuation, PeerComparison
- Call site: `stockScraper.js` in `displayResults()`, immediately before `tickerResultsDiv.innerHTML = ''` (line 188)
- Rationale: consistent, future-proof — other modules' `clearSession()` are no-ops today but may not be forever

### DCF premium badge fix (BREAK-02)
- **Remove** the inline `premiumHTML` block from `buildHTML()` in `dcfValuation.js`
- **Populate** `#dcf-premium-{ticker}` div with the badge HTML immediately during initial render (visible from first load, not hidden)
- `_recalculate()` continues to update `#dcf-premium-{ticker}` in-place — single source of truth for both initial and recalculated state
- Badge is rendered visible (`style` not needed or `display:block`) from the initial `buildHTML()` call — no second JS call required

### MISS-01 async pageContext write
- Write `pageContext.tickerData[ticker].peerComparison = { sector, peers, percentiles }` **inside the fetch callback** in `peerComparison.js` after fetch resolves successfully
- Same pattern as `dcfValuation.js` already uses for its own pageContext write
- No changes to `stockScraper.js` for this item

### REQUIREMENTS.md documentation update
- Mark all 19 v2.1 requirements as `[x] Complete` in the traceability table:
  - FHLTH-01 through FHLTH-04 (Phase 13)
  - QUAL-01 through QUAL-05 (Phase 14)
  - DCF-01 through DCF-05 (Phase 15)
  - PEER-01 through PEER-05 (Phase 16)

### Claude's Discretion
- Guard syntax for `clearSession()` calls (check `typeof X !== 'undefined'` or trust module load order)
- Exact whitespace/formatting of badge HTML in refactored `buildHTML()`
- Whether to add a brief inline comment at the `clearSession()` call site explaining why all 4 are cleared

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `peerComparison.js` line 201: `if (_sessionCache[ticker]) return;` — this is the guard that causes BREAK-01; `clearSession()` at line 215 clears `_sessionCache`
- `dcfValuation.js` lines 154–166: inline `premiumHTML` block to remove; lines 202–203: `premiumHTML` insertion + hidden `#dcf-premium-{ticker}` div to refactor
- `dcfValuation.js` lines 273–289: `_recalculate()` already targets `#dcf-premium-{ticker}` correctly — no changes needed here

### Established Patterns
- `clearSession()` exists on all 4 modules: `window.HealthScore`, `window.EarningsQuality`, `window.DCFValuation`, `window.PeerComparison`
- Module existence guard pattern: `typeof HealthScore !== 'undefined'` (used in `stockScraper.js` line 213)
- `pageContext.tickerData[ticker].dcfValuation = {...}` written in `dcfValuation.js` after computation — MISS-01 fix mirrors this exact pattern for peerComparison

### Integration Points
- `stockScraper.js` `displayResults()` at line 188: insert 4x `clearSession()` calls here
- `dcfValuation.js` `buildHTML()`: remove inline premiumHTML, populate `#dcf-premium-{ticker}` with badge content directly
- `peerComparison.js` fetch callback: add `pageContext.tickerData[ticker].peerComparison = {...}` write after successful parse

</code_context>

<specifics>
## Specific Ideas

- The audit doc at `.planning/v2.1-MILESTONE-AUDIT.md` contains exact line references and prescribed fixes — planner should consult it
- BREAK-01 fix is one-line per module (4 lines total) plus a guard check — very surgical
- BREAK-02 fix is ~10 lines changed in `buildHTML()`: delete the inline premiumHTML variable and its use in the HTML string; make `#dcf-premium-{ticker}` div contain the badge HTML directly with `display:block`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 17-bug-fixes-rescrape-dcf-badge*
*Context gathered: 2026-04-05*
