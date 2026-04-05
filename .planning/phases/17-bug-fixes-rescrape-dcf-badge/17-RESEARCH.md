# Phase 17: Bug Fixes — Re-scrape & DCF Badge - Research

**Researched:** 2026-04-05
**Domain:** Vanilla JavaScript DOM manipulation, module session state management
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**clearSession call breadth (BREAK-01)**
- Call `clearSession()` on all 4 deep-analysis modules before each re-scrape: HealthScore, EarningsQuality, DCFValuation, PeerComparison
- Call site: `stockScraper.js` in `displayResults()`, immediately before `tickerResultsDiv.innerHTML = ''` (line 188)
- Rationale: consistent, future-proof — other modules' `clearSession()` are no-ops today but may not be forever

**DCF premium badge fix (BREAK-02)**
- Remove the inline `premiumHTML` block from `buildHTML()` in `dcfValuation.js`
- Populate `#dcf-premium-{ticker}` div with the badge HTML immediately during initial render (visible from first load, not hidden)
- `_recalculate()` continues to update `#dcf-premium-{ticker}` in-place — single source of truth for both initial and recalculated state
- Badge is rendered visible (`style` not needed or `display:block`) from the initial `buildHTML()` call — no second JS call required

**MISS-01 async pageContext write**
- Write `pageContext.tickerData[ticker].peerComparison = { sector, peers, percentiles }` inside the fetch callback in `peerComparison.js` after fetch resolves successfully
- Same pattern as `dcfValuation.js` already uses for its own pageContext write
- No changes to `stockScraper.js` for this item

**REQUIREMENTS.md documentation update**
- Mark all 19 v2.1 requirements as `[x] Complete` in the traceability table:
  - FHLTH-01 through FHLTH-04 (Phase 13)
  - QUAL-01 through QUAL-05 (Phase 14)
  - DCF-01 through DCF-05 (Phase 15)
  - PEER-01 through PEER-05 (Phase 16)

### Claude's Discretion
- Guard syntax for `clearSession()` calls (check `typeof X !== 'undefined'` or trust module load order)
- Exact whitespace/formatting of badge HTML in refactored `buildHTML()`
- Whether to add a brief inline comment at the `clearSession()` call site explaining why all 4 are cleared

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PEER-01 | User can see the ticker's P/E, P/B, ROE, and operating margin ranked as a percentile against 5-10 sector peers | BREAK-01 fix restores this on re-scrape by clearing `_sessionCache` before each scrape |
| PEER-02 | User can see which sector peer group was used (e.g., "Technology — comparable group") | BREAK-01 fix — same root cause, same fix |
| PEER-03 | User can see a visual above/below-median indicator for each of the four metrics | BREAK-01 fix — peer section must render for indicators to appear |
| PEER-04 | User can toggle a "Show peers" control to reveal the raw peer data table | BREAK-01 fix — section must render to expose toggle |
| PEER-05 | Module displays "Peer data unavailable" if Finviz peer fetch fails | BREAK-01 fix — failure HTML only shown when section renders |
| DCF-02 | User can see whether the stock is trading at a premium or discount vs. the DCF estimate | BREAK-02 fix removes duplicate badge; single `#dcf-premium-{ticker}` div is source of truth |
| DCF-04 | User can override default growth and WACC assumptions and recalculate without re-scraping | BREAK-02 fix ensures Recalculate produces exactly one badge after interaction |

</phase_requirements>

---

## Summary

Phase 17 is a surgical bug-fix phase targeting two runtime defects found in the v2.1 milestone audit. No new features are introduced. The scope is three code changes across two JS files, plus a documentation-only update to REQUIREMENTS.md.

**BREAK-01** is the more impactful defect: `peerComparison.js` guards against double-render via `_sessionCache[ticker]`, but nothing ever calls `PeerComparison.clearSession()` before a re-scrape. The result is a completely silent skip — no error, no spinner, no peer section — on any re-scrape of a ticker seen in the current page session.

**BREAK-02** is a lower-severity UX defect: `buildHTML()` renders the premium/discount badge both inline in the HTML string and as a hidden `#dcf-premium-{ticker}` div. When the user clicks Recalculate, `_recalculate()` makes the hidden div visible but leaves the original inline badge. Two badges appear side-by-side.

**MISS-01** is a tech debt item: `pageContext.tickerData[ticker].peerComparison` is already written inside the fetch callback (peerComparison.js lines 180-188), so this item is already partially done. Research confirms the write exists and follows the same pattern as `dcfValuation.js`. The fix is to verify and confirm rather than add net-new code.

**Primary recommendation:** Fix BREAK-01 first (highest user impact), then BREAK-02, then confirm MISS-01 is satisfied, then update REQUIREMENTS.md checkboxes.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vanilla JS (ES5-compatible) | — | DOM manipulation, fetch API, module pattern | Matches existing codebase style — IIFE modules, no build toolchain |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None | — | — | No new dependencies introduced in this phase |

### Alternatives Considered

None — all fixes are within existing module pattern. No new libraries needed.

---

## Architecture Patterns

### Module Pattern in Use
All deep-analysis JS files follow the same IIFE module pattern that exposes a `window.X` global:

```javascript
(function () {
    'use strict';
    // private state
    var _sessionCache = {};

    function clearSession() {
        Object.keys(_sessionCache).forEach(function (k) { delete _sessionCache[k]; });
    }

    window.PeerComparison = { renderIntoGroup, clearSession };
}());
```

### Existing clearSession Guard Pattern (HIGH confidence)
`stockScraper.js` already uses `typeof X !== 'undefined'` guards for all module calls (line 213):

```javascript
// Pattern from stockScraper.js line 213
if (typeof HealthScore !== 'undefined' && window.pageContext && ...) { ... }
```

The same guard must wrap `clearSession()` calls for consistency:

```javascript
// Source: static/js/stockScraper.js — existing guard pattern
if (typeof HealthScore !== 'undefined')    HealthScore.clearSession();
if (typeof EarningsQuality !== 'undefined') EarningsQuality.clearSession();
if (typeof DCFValuation !== 'undefined')   DCFValuation.clearSession();
if (typeof PeerComparison !== 'undefined') PeerComparison.clearSession();
```

### Single Source of Truth for DCF Badge (HIGH confidence)
The correct pattern is:
- `buildHTML()` populates `#dcf-premium-{ticker}` with badge HTML directly (visible, no `display:none`)
- `_recalculate()` updates `#dcf-premium-{ticker}` in-place (already correct, no changes needed)
- The inline `premiumHTML` variable and its use in the HTML string are removed entirely

### Anti-Patterns to Avoid
- **Double-badge anti-pattern:** Rendering the same data in two places (inline HTML + named div). Always use the named div as single source of truth.
- **Missing guard on clearSession:** Calling `PeerComparison.clearSession()` without a `typeof` check could throw a ReferenceError if the script failed to load.
- **Forgetting all 4 modules:** Even though HealthScore, EarningsQuality, and DCFValuation `clearSession()` are no-ops today, calling all 4 is the locked decision for future-proofing.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Session state clearing | Custom event system, page reload | Existing `clearSession()` on each module | Already implemented correctly — just needs to be called |
| Badge deduplication | DOM traversal + removal logic | Remove inline HTML, use named div as source of truth | Simpler and matches existing `_recalculate()` target |

---

## Common Pitfalls

### Pitfall 1: Inserting clearSession calls AFTER innerHTML clear
**What goes wrong:** If `clearSession()` is called after `tickerResultsDiv.innerHTML = ''`, the DOM is already reset but the module's `_sessionCache` was cleared after the card was already rebuilt — race condition is impossible here but ordering discipline matters.
**Why it happens:** Misreading the locked decision (call site is BEFORE the innerHTML clear).
**How to avoid:** Insert all 4 `clearSession()` calls immediately before line 188 (`tickerResultsDiv.innerHTML = ''`).
**Warning signs:** If `_sessionCache` is cleared after the render loop, a re-scrape in the same event loop tick would still be blocked.

### Pitfall 2: Leaving the hidden div in buildHTML after refactor
**What goes wrong:** If `<div id="dcf-premium-{ticker}" style="display:none;"></div>` is left in the HTML string (line 203 of `dcfValuation.js`), the hidden div persists and `_recalculate()` still makes it visible — the two-badge bug remains.
**Why it happens:** Partial refactor — removing `premiumHTML` from the string but forgetting to also populate the named div initially.
**How to avoid:** The named div should contain the badge HTML content AND not have `display:none`. Remove the variable `premiumHTML` and its insertion at line 202; move the badge HTML construction to populate the named div.

### Pitfall 3: MISS-01 already implemented
**What goes wrong:** Over-engineering — adding duplicate `pageContext` write to `stockScraper.js` when the write already exists inside `peerComparison.js`'s fetch callback (lines 180-188).
**Why it happens:** Misreading the tech debt item as "not implemented."
**How to avoid:** Reading `peerComparison.js` lines 179-188 shows the write is already there. MISS-01 is a confirmation task, not an implementation task. The write is inside `_fetchAndRender()` after `resp` is validated — exactly the right location.

### Pitfall 4: Marking wrong requirements in REQUIREMENTS.md
**What goes wrong:** Only updating the v2.1 traceability table checkboxes without also updating the inline requirement list checkboxes above the table.
**Why it happens:** REQUIREMENTS.md has two places where each requirement appears: the bulleted list (`- [ ] **FHLTH-01**:`) and the traceability table row.
**How to avoid:** Update both the bulleted list AND the traceability table for all 19 requirements.

---

## Code Examples

Verified patterns from source code inspection:

### BREAK-01 Fix — clearSession calls in stockScraper.js displayResults()
```javascript
// Insert immediately before: tickerResultsDiv.innerHTML = '';  (line 188)
// Source: static/js/stockScraper.js — matches existing typeof guard pattern (line 213)
if (typeof HealthScore !== 'undefined')     HealthScore.clearSession();
if (typeof EarningsQuality !== 'undefined') EarningsQuality.clearSession();
if (typeof DCFValuation !== 'undefined')    DCFValuation.clearSession();
if (typeof PeerComparison !== 'undefined')  PeerComparison.clearSession();
tickerResultsDiv.innerHTML = '';
```

### BREAK-02 Fix — refactored buildHTML() badge section in dcfValuation.js
Before (lines 155-203):
```javascript
// REMOVE: local premiumHTML variable built at lines 155-167
let premiumHTML = '';
if (result.premium !== null) {
    // ... badge HTML built here
    premiumHTML = '<div class="metric-item">...badge...</div>';
}

// REMOVE from HTML string at line 202:
premiumHTML +
// REMOVE at line 203:
'<div id="dcf-premium-' + ticker + '" style="display:none;"></div>' +
```

After:
```javascript
// Build badge HTML for the named div (same logic, different assignment target)
let badgeInnerHTML = '';
if (result.premium !== null) {
    const isDiscount = result.premium < 0;
    const badgeClass = isDiscount ? 'badge-success' : 'badge-danger';
    const sign       = isDiscount ? '' : '+';
    const label      = isDiscount ? 'Discount' : 'Premium';
    badgeInnerHTML =
        '<div class="metric-item">' +
        '<span class="metric-label">vs Current Price</span>' +
        '<span class="metric-value">' +
        '<span class="badge ' + badgeClass + '">' + label + ' ' + sign + result.premium.toFixed(1) + '%</span>' +
        '</span></div>';
}

// In the HTML string, replace the old two-line block with:
'<div id="dcf-premium-' + ticker + '">' + badgeInnerHTML + '</div>' +
```

### MISS-01 Verification — existing write in peerComparison.js
```javascript
// Already present at peerComparison.js lines 179-188 (no changes needed)
if (window.pageContext &&
    window.pageContext.tickerData &&
    window.pageContext.tickerData[ticker]) {
    window.pageContext.tickerData[ticker].peerComparison = {
        sector:      resp.sector,
        peers:       resp.peers,
        percentiles: resp.percentiles
    };
}
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Inline badge HTML + hidden named div | Named div only, populated on both initial render and recalculate | Eliminates BREAK-02 |
| No `clearSession()` call before re-scrape | All 4 module `clearSession()` calls in `displayResults()` | Eliminates BREAK-01 |
| REQUIREMENTS.md checkboxes `[ ]` | All 19 v2.1 checkboxes `[x]` | Closes documentation debt |

---

## Open Questions

1. **MISS-01 confirmation**
   - What we know: `peerComparison.js` lines 180-188 already contain the `pageContext` write inside `_fetchAndRender()`, which fires after successful fetch
   - What's unclear: Whether the phase context item MISS-01 expects additional synchronous write to `stockScraper.js` or purely async (confirmed async is acceptable)
   - Recommendation: Treat MISS-01 as a verification task only — the write is already in the correct location. Document confirmation in the plan's verification step.

2. **DCFValuation.clearSession() is a no-op**
   - What we know: `dcfValuation.js` `clearSession()` function body is empty — `_dataCache` is not cleared
   - What's unclear: Whether `_dataCache` should be cleared during re-scrape (prevents stale data for Recalculate on a re-scraped ticker)
   - Recommendation: Call `DCFValuation.clearSession()` as specified (it's a no-op per locked decision). Do NOT add cache clearing to `dcfValuation.js` `clearSession()` — that's out of scope for this phase.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None detected (no pytest.ini, no jest.config, no vitest.config) |
| Config file | None — browser-based JS modules only |
| Quick run command | Manual browser test: scrape ticker, scrape same ticker again, verify peer section appears both times |
| Full suite command | Manual browser test of all 3 bug fixes |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PEER-01 | Peer percentile rows visible on re-scrape | manual | — (browser only) | ❌ Wave 0 N/A |
| PEER-02 | Peer group label visible on re-scrape | manual | — (browser only) | ❌ Wave 0 N/A |
| PEER-03 | Above/below-median badge visible on re-scrape | manual | — (browser only) | ❌ Wave 0 N/A |
| PEER-04 | "Show peers" toggle works on re-scrape | manual | — (browser only) | ❌ Wave 0 N/A |
| PEER-05 | "Peer data unavailable" shows on failure on re-scrape | manual | — (browser only) | ❌ Wave 0 N/A |
| DCF-02 | Exactly one premium/discount badge after Recalculate | manual | — (browser only) | ❌ Wave 0 N/A |
| DCF-04 | Recalculate updates single badge, not two | manual | — (browser only) | ❌ Wave 0 N/A |

### Sampling Rate
- **Per task commit:** Manual browser smoke test of the specific fix just applied
- **Per wave merge:** Full manual E2E: scrape ticker A, scrape ticker A again (BREAK-01), click Recalculate (BREAK-02), verify REQUIREMENTS.md checkboxes
- **Phase gate:** All 3 manual checks pass before `/gsd:verify-work`

### Wave 0 Gaps
No automated test infrastructure applies to browser-only JS modules in this project. All verification is manual browser testing. No Wave 0 test file creation required.

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `static/js/stockScraper.js` — lines 186-244 (displayResults, clearSession guard pattern)
- Direct code inspection: `static/js/dcfValuation.js` — lines 126-220 (buildHTML, _recalculate)
- Direct code inspection: `static/js/peerComparison.js` — lines 168-219 (renderIntoGroup, clearSession, fetch callback pageContext write)
- `.planning/v2.1-MILESTONE-AUDIT.md` — exact line references and prescribed fixes for BREAK-01 and BREAK-02

### Secondary (MEDIUM confidence)
- `.planning/phases/17-bug-fixes-rescrape-dcf-badge/17-CONTEXT.md` — locked implementation decisions
- `.planning/REQUIREMENTS.md` — v2.1 traceability table current state (all 19 pending checkboxes confirmed)

### Tertiary (LOW confidence)
- None — all findings verified from direct source code inspection

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — existing codebase pattern, no new libraries
- Architecture: HIGH — source code directly inspected, bug root causes confirmed
- Pitfalls: HIGH — derived from direct reading of the exact lines to be modified
- MISS-01 status: HIGH — the pageContext write is already present in peerComparison.js lines 180-188

**Research date:** 2026-04-05
**Valid until:** Indefinite — no external dependencies, no version-sensitive patterns
