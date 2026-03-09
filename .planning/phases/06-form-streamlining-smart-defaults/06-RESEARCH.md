# Phase 6: Form Streamlining & Smart Defaults - Research

**Researched:** 2026-03-09
**Domain:** Vanilla JavaScript UI / HTML form patterns / CSS layout
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Blank ticker in Value mode = 0 allocation = excluded from portfolio (not an error, not equal share) — this is the current behavior in `getPortfolioAllocation()`, confirm and keep
- When ALL value fields are blank: fall back to equal weights AND show a subtle info hint near the allocation section (e.g., "No values entered — equal weights will be used")
- The hint should only appear when mode is Value and all inputs are empty/zero
- Live "→ XX.X%" label appears immediately as any value is typed — does not wait for all tickers to have values
- Percentages reflect entered amounts over running total of entered amounts (current behavior — confirm and keep)
- Switching between % Weight and Value mode clears all allocation inputs (current behavior — confirm and keep)
- Currency selector appears only in Value mode (current behavior — confirm and keep)
- Smart defaults use `['yahoo', 'finviz', 'google', 'technical']` when Advanced is collapsed — current `stockScraper.js` already implements this; verify end-to-end
- Equal-weights hint: not currently shown — needs to be added to `calculateAllocationTotal()` in Value mode when all inputs are 0

### Claude's Discretion

- Hero button visual treatment (size, width, color weight)
- Exact wording and placement of the "equal weights" hint in Value mode
- Whether to add a small "Using defaults: all free sources" note when Advanced is collapsed (subtle, optional)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FORM-01 | User can submit analysis with only ticker symbols entered (no required source selection or API key input) | Smart defaults already implemented in `stockScraper.js` lines 49-68; confirm `advancedDetails.open` check is working end-to-end |
| FORM-02 | User can toggle advanced settings (sources, API keys) via a collapsible "⚙ Advanced" section | `<details id="advanced-settings">` already in HTML, collapsed by default; no structural change needed |
| FORM-03 | System applies smart defaults (yahoo + finviz + google + technical) when advanced settings are collapsed or unconfigured | Code path: `sources = ['yahoo', 'finviz', 'google', 'technical']` at `stockScraper.js` line 67; backend `run_scrapers_for_ticker()` handles each via `'yahoo' in sources` checks |
| FORM-04 | User can switch between "% Weight" and "Value" allocation modes via a mode toggle | `switchAllocationMode()` in `FormManager` already handles mode toggle, button active state, currency visibility, hint text update |
| FORM-05 | In Value mode, user enters currency amounts per ticker and sees live computed % weights (e.g., "→ 66.7%") | `calculateAllocationTotal()` already updates `alloc-pct-${ticker}` spans on every input event; spans emit "→ XX.X%" |
| FORM-06 | In Value mode, user can select currency (USD/SGD/EUR/GBP) next to the mode toggle | `#currencySelect` already in HTML with all 4 options; shown/hidden by `switchAllocationMode()`; total display uses selected value |
| FORM-07 | Leaving all value fields blank in either mode falls back to equal-weight allocation | `getPortfolioAllocation()` returns `null` when all values are zero; backend treats `null` as equal-weight; equal-weights hint in Value mode is the one gap to add |
| FORM-08 | "Analyze Stocks" button relabelled to "▶ Run Analysis" and presented in a prominent hero layout | Button already reads "▶ Run Analysis" in current HTML (line 776); `.hero-input-group` CSS already present; hero visual polish is the remaining gap |
</phase_requirements>

---

## Summary

Phase 6 is a **UI-only, zero-backend phase**. All required backend logic is already in place: smart defaults are implemented in `stockScraper.js`, the `<details id="advanced-settings">` collapsible section exists, the allocation mode system (`FormManager`) is fully implemented, and the submit button already reads "▶ Run Analysis". The gap inventory is narrow and precise.

The three concrete gaps to close are: (1) adding an equal-weights info hint in `calculateAllocationTotal()` when mode is Value and all inputs are 0, (2) verifying the end-to-end smoke path that submitting with Advanced collapsed delivers exactly `['yahoo','finviz','google','technical']` to the backend, and (3) optionally polishing the hero layout (button width/sizing, optional "Using defaults" note).

No new libraries, routes, or API contracts are needed. All changes are confined to `static/js/forms.js`, `static/js/stockScraper.js`, and the inline `<style>` block in `templates/index.html`.

**Primary recommendation:** Implement the equal-weights hint in `calculateAllocationTotal()`, add an optional collapsed-defaults note, verify the smart-defaults path end-to-end with a manual smoke test, and apply minor hero-layout CSS tweaks — all within the existing JS/HTML files.

---

## Standard Stack

### Core
| Technology | Version | Purpose | Why Standard |
|------------|---------|---------|--------------|
| Vanilla JS (ES2020) | browser-native | DOM manipulation, event handling | Project uses no JS framework; all existing modules follow plain-object pattern |
| HTML `<details>`/`<summary>` | HTML5 | Collapsible advanced section | Already in use for `#advanced-settings`; no JS collapse logic needed |
| CSS custom properties / inline styles | browser-native | Hero layout, hint styling | Consistent with project pattern of inline `<style>` in `index.html` + external `styles.css` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None required | — | — | Phase is pure DOM/CSS work |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Inline `<style>` in index.html | External `styles.css` | Both patterns coexist in the project; use inline `<style>` for phase-specific component rules, `styles.css` for shared rules |

---

## Architecture Patterns

### Current Form Structure
```
templates/index.html
  <form id="scrapeForm">
    <div class="form-group hero-input-group">   <!-- ticker input -->
    <details id="advanced-settings">            <!-- collapsed by default -->
      data sources checkboxes + API key inputs
    </details>
    <div id="allocationSection">               <!-- shown when >= 2 tickers -->
      mode toggle + currency select + per-ticker inputs + total
    </div>
    <div class="button-group">
      <button id="runAnalysisBtn">▶ Run Analysis</button>
    </div>
  </form>
```

### Pattern 1: Equal-Weights Hint Injection
**What:** Add/remove a hint element inside `#allocationSection` when Value mode is active and all inputs sum to zero.
**When to use:** Called at end of `calculateAllocationTotal()` after the Value-mode branch.
**Example:**
```javascript
// In calculateAllocationTotal(), Value mode branch, after updating pct labels:
const hintEl = document.getElementById('equalWeightsHint');
const allZero = totalValue === 0;
if (hintEl) {
    hintEl.style.display = (this._allocationMode === 'value' && allZero) ? 'block' : 'none';
}
```
The hint element itself is a static `<small id="equalWeightsHint">` placed after `#allocationTotal` in the HTML. It is toggled via `style.display`, not created dynamically, to keep DOM mutation minimal.

### Pattern 2: Collapsed-Defaults Note (Optional)
**What:** Show a subtle note below the Advanced summary when the section is closed, to reassure users that free sources are active.
**When to use:** Toggle visibility on the `<details>` `toggle` event.
**Example:**
```javascript
// In FormManager.initEventListeners() or StockScraper.init():
const advDet = document.getElementById('advanced-settings');
const defaultsNote = document.getElementById('defaultsNote');
if (advDet && defaultsNote) {
    advDet.addEventListener('toggle', () => {
        defaultsNote.style.display = advDet.open ? 'none' : 'block';
    });
}
```
The note element is a `<small id="defaultsNote">` placed immediately after the `</details>` closing tag.

### Pattern 3: Hero Button Prominence
**What:** Make `#runAnalysisBtn` visually dominant — full-width or near-full-width, slightly larger, with heavier weight.
**When to use:** CSS-only change in the inline `<style>` block.
**Example:**
```css
#runAnalysisBtn {
    width: 100%;
    font-size: 1.2em;
    padding: 16px 32px;
    letter-spacing: 0.03em;
}
```
The `.button-group` flex layout will need `flex-direction: column` or the Clear button de-emphasized to keep hierarchy clear.

### Anti-Patterns to Avoid
- **Dynamic DOM creation for the hint:** Creating/removing hint elements in JS is fragile. Prefer a static element toggled with `display`.
- **Modifying `getPortfolioAllocation()` for the hint:** The hint is a presentation concern; do not add display logic to the data-retrieval method.
- **Changing `switchAllocationMode()` to show the hint:** The hint is dynamic per input state, not per mode switch; it belongs in `calculateAllocationTotal()`.
- **Validating blank allocation as an error:** FORM-07 and CONTEXT.md decisions are explicit — blank = equal weights, no validation error shown.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Collapsible section | Custom JS toggle with classes | Native `<details>`/`<summary>` | Already in use; browser-native, no JS needed, `open` attribute readable by `stockScraper.js` |
| Live percentage recalculation | Custom event system | `addEventListener('input', ...)` on each allocation input | Already implemented in `updateAllocationInputs()` — do not replace |
| Equal-weight fallback | Re-implement in JS | Existing `getPortfolioAllocation()` returning `null` | Backend already treats `null` allocation as equal-weight; no new code path needed |

---

## Common Pitfalls

### Pitfall 1: `advancedDetails.open` check timing
**What goes wrong:** If a test submits the form programmatically, `details.open` reflects the DOM state at submit time. If the `<details>` element was never rendered (hidden tab, etc.), `open` is `false` and defaults kick in unexpectedly.
**Why it happens:** `open` is a DOM attribute, not a JS state variable.
**How to avoid:** The current implementation is correct — just verify the smoke test opens the browser tab and submits with the section visually collapsed.
**Warning signs:** Backend logs showing all 4 default sources when user expected custom sources (or vice versa).

### Pitfall 2: `calculateAllocationTotal()` called before DOM is ready
**What goes wrong:** `updateAllocationInputs()` calls `calculateAllocationTotal()` at the end, which tries to find `#equalWeightsHint` before it exists if the hint is injected after the function runs.
**Why it happens:** Function call order during `updateAllocationInputs()` initialization.
**How to avoid:** Place the static `#equalWeightsHint` element in the HTML before the page is loaded (inside `#allocationSection`), not injected dynamically.

### Pitfall 3: Hero button breaking the Clear button layout
**What goes wrong:** Making `#runAnalysisBtn` full-width inside `.button-group` (flex row) pushes the Clear button to a new line with mismatched widths.
**Why it happens:** `.button-group` uses `display: flex; flex-wrap: wrap`.
**How to avoid:** Either set `.button-group` to `flex-direction: column` with explicit width, or keep the button in the row but use `flex: 2` / `flex: 1` ratios to give Run Analysis more weight without going full-width.

### Pitfall 4: Hint persists after switching to Percent mode
**What goes wrong:** `equalWeightsHint` stays visible after user switches from Value → Percent mode if the hint is only toggled in `calculateAllocationTotal()`.
**Why it happens:** `switchAllocationMode()` calls `updateAllocationInputs()` which calls `calculateAllocationTotal()` — but the hint check must test `this._allocationMode === 'value'`, which is already set before `updateAllocationInputs()` is called in `switchAllocationMode()`. The guard condition handles it correctly IF the mode is checked at hint display time.
**How to avoid:** Ensure the hint display condition always checks `this._allocationMode === 'value' && allZero`, not just `allZero`.

### Pitfall 5: `technical` source requires Alpha Vantage key
**What goes wrong:** Default sources include `'technical'`, but `webapp.py` line 233 shows technical data only runs when `alpha_key or os.environ.get("ALPHA_VANTAGE_API_KEY")` is present. With no key configured, technical is silently skipped.
**Why it happens:** Technical indicators are gated behind an API key server-side.
**How to avoid:** This is existing behavior and does not need to change for this phase. The default source list `['yahoo','finviz','google','technical']` is correct — technical simply produces no data when no key is present, which is the intended graceful degradation. No UI change needed.

---

## Code Examples

Verified patterns from existing codebase (HIGH confidence — direct code inspection):

### Current smart-defaults path (stockScraper.js lines 49-68)
```javascript
const advancedDetails = document.getElementById('advanced-settings');
const advancedOpen = advancedDetails && advancedDetails.open;

let sources = [];
if (advancedOpen) {
    // user-configured sources
} else {
    sources = ['yahoo', 'finviz', 'google', 'technical'];
}
```
This path is ALREADY CORRECT. Verification task: submit a form with Advanced collapsed and confirm the request body has `sources: ['yahoo','finviz','google','technical']`.

### Adding the equal-weights hint — minimal change to `calculateAllocationTotal()`
```javascript
// Inside the `if (this._allocationMode === 'value')` branch, after updating pct labels:
const equalWeightsHint = document.getElementById('equalWeightsHint');
if (equalWeightsHint) {
    equalWeightsHint.style.display = totalValue === 0 ? 'block' : 'none';
}
```

### Static HTML for equal-weights hint (place inside `#allocationSection`, after `#allocationTotal`)
```html
<small id="equalWeightsHint" style="display:none; color:#6c757d; margin-top:6px; display:none;">
    No values entered — equal weights will be used.
</small>
```

### Hero button CSS (minimal, additive — inside existing inline `<style>`)
```css
#runAnalysisBtn {
    width: 100%;
    font-size: 1.15em;
    padding: 16px 32px;
}
.button-group {
    flex-direction: column;
    align-items: stretch;
}
```

### Optional collapsed-defaults note HTML (place after `</details>`)
```html
<small id="defaultsNote" style="color:#6c757d; font-size:0.85em; display:block; margin-top:4px;">
    Using defaults: Yahoo Finance, Finviz, Google Finance, Technical Indicators
</small>
```

---

## State of the Art

| Old State | Current State | Impact on Phase |
|-----------|---------------|-----------------|
| Button labelled "Analyze Stocks" | Already "▶ Run Analysis" in HTML | No label change needed |
| No collapsible advanced section | `<details id="advanced-settings">` already in HTML, collapsed by default | No structural change needed |
| No smart defaults | Smart defaults already in `stockScraper.js` | Verify only, no implementation needed |
| No equal-weights hint | Not present | Only new JS/HTML to add |
| No hero layout | `.hero-input-group` CSS + `#runAnalysisBtn` sizing partially done | Minor CSS polish remaining |

---

## Open Questions

1. **Technical source silently absent without API key**
   - What we know: `webapp.py` line 233 gates technical behind `alpha_key or env var`
   - What's unclear: Should the UI hint about this when Advanced is collapsed? (e.g., "Technical Indicators requires an API key")
   - Recommendation: No change for this phase; the current silent skip is correct graceful degradation. If desired, it can be addressed in a future phase.

2. **Exact hero layout extent**
   - What we know: CONTEXT.md gives Claude discretion on visual treatment
   - What's unclear: Whether button should be 100% width or just wider with Clear button still visible
   - Recommendation: Full-width Run Analysis button in a column-direction button-group, with Clear button styled as a secondary/ghost button below it. This matches common "hero CTA + secondary action" patterns.

---

## Validation Architecture

> `nyquist_validation` key is absent from `.planning/config.json` — treating as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (detected in `tests/conftest.py`) |
| Config file | none (no `pytest.ini` or `pyproject.toml` found) |
| Quick run command | `pytest tests/ -x -q --ignore=tests/test_regime_detection.py` |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FORM-01 | Submit with only tickers — no error, reaches backend with correct sources | manual smoke | Open browser, submit with Advanced collapsed, check network tab | N/A (no browser test infra) |
| FORM-02 | Advanced toggle shows/hides data source section | manual | Toggle `<details>` in browser | N/A |
| FORM-03 | Sources payload = `['yahoo','finviz','google','technical']` when collapsed | manual smoke | Check request body in browser devtools | N/A |
| FORM-04 | Mode toggle switches between % Weight and Value, clears inputs | manual | Click mode buttons in browser | N/A |
| FORM-05 | Live % labels update as values typed | manual | Type values in Value mode | N/A |
| FORM-06 | Currency selector visible in Value mode, hidden in % mode | manual | Switch modes | N/A |
| FORM-07 | Blank allocation = equal weights, hint shown in Value mode | manual | Leave all Value inputs blank | N/A |
| FORM-08 | Run Analysis button is prominent | visual verification | Open browser | N/A |

**Note:** All FORM requirements are pure front-end UI behaviors. The project has no JS testing framework (no Jest, no Vitest, no Playwright). All verification for this phase is manual browser smoke testing. The existing pytest suite covers Python backend only and is not affected by this phase.

### Sampling Rate
- **Per task commit:** Reload browser, submit with Advanced collapsed, confirm no JS errors in console
- **Per wave merge:** Full manual smoke: test each FORM requirement scenario in sequence
- **Phase gate:** All 5 success criteria in phase description pass before `/gsd:verify-work`

### Wave 0 Gaps
- None — existing test infrastructure (pytest) is unaffected. No new test files needed for a UI-only phase with no JS test framework.

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `static/js/forms.js` — full `FormManager` implementation read
- Direct code inspection: `static/js/stockScraper.js` — smart-defaults path at lines 49-68 confirmed
- Direct code inspection: `templates/index.html` — form structure, CSS classes, existing DOM IDs confirmed
- Direct code inspection: `webapp.py` lines 208-233 — backend source dispatch confirmed

### Secondary (MEDIUM confidence)
- MDN: `<details>`/`<summary>` `open` attribute behavior — standard HTML5, well-established

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all technology is existing project code; no new libraries
- Architecture: HIGH — all patterns are verified against actual source files
- Pitfalls: HIGH — derived from direct reading of the implementation
- Validation: HIGH — test infra confirmed by directory inspection

**Research date:** 2026-03-09
**Valid until:** 2026-06-09 (stable vanilla JS/HTML domain; no expiry concerns)
