# Phase 9: Health Card Deep-Links & Auto-Run Hardening - Research

**Researched:** 2026-03-11
**Domain:** Vanilla JS DOM navigation (scrollIntoView, CSS highlight pulse) + defensive global-guard patterns
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Smooth scroll: `scrollIntoView({ behavior: 'smooth' })` — not instant jump
- After scrolling, briefly highlight the target section with a blue pulse (#667eea) lasting ~800ms then fading out
- Implementation: add/toggle a CSS class that applies `box-shadow` or `outline` in #667eea, remove it after 800ms via `setTimeout`
- Highlight implementation: `el.style.transition = 'box-shadow 0.8s'; el.style.boxShadow = '0 0 0 3px #667eea'; setTimeout(() => el.style.boxShadow = '', 800)` — clean, no extra CSS class needed
- The VaR anchor should wrap the entire Monte Carlo metrics block (not just the heading) so the scrolled-to element is visible above the fold

### Claude's Discretion
- Timing: tab switch happens first, then scroll. If analytics content is already rendered (it is, post-scrape), scroll fires immediately after `switchTab`
- Exact CSS for the pulse animation (outline, box-shadow, or background tint — whichever is cleanest given existing card styles)
- Sharpe scroll target: whichever Analytics tab section most naturally represents "returns / Sharpe" (e.g., Summary Statistics section or the portfolio-level Sharpe display if one exists) — Claude to determine from the rendered HTML structure
- MDP section shows a graceful error when `rlEscapeHTML`/`rlAlert` are unavailable (same ⚠ Failed badge pattern as normal MDP failure)
- Exact wording of the unavailability message is Claude's call — should distinguish from a normal MDP compute error if straightforward to do so

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| HEALTH-02 | Each metric in the health card links/jumps to its relevant analytics tab section | scrollIntoView + anchor IDs + highlight pulse pattern verified below; guard pattern for rlEscapeHTML/rlAlert also confirmed |
</phase_requirements>

---

## Summary

Phase 9 is a two-concern surgical fix with no new libraries and no backend changes. The first concern is deep-linking: both the VaR chip and Sharpe chip in `portfolioHealth.js` already call `TabManager.switchTab('analytics')`, but they navigate only to the tab top. The fix requires adding `id` attributes to the relevant rendered sections in `analyticsRenderer.js` and `displayManager.js`, then calling `scrollIntoView({ behavior: 'smooth' })` plus the user-approved inline `box-shadow` pulse immediately after `switchTab`.

The second concern is defensive hardening: `autoRun.js` calls `rlEscapeHTML` and `rlAlert` as bare names (4 call sites: lines 279, 280, 293, 316) with no guard, while both functions are module-scoped in `rlModels.js` with no `window.*` exposure. If `rlModels.js` fails to load, the MDP rendering block throws `ReferenceError`. The fix is to expose both functions on `window` at the end of `rlModels.js` and add inline fallback guards at each call site in `autoRun.js`.

**Primary recommendation:** Add anchor IDs in `analyticsRenderer.js` / `displayManager.js`, extend chip onclick handlers in `portfolioHealth.js`, then expose `window.rlEscapeHTML` / `window.rlAlert` and add guarded fallbacks in `autoRun.js` — all in one plan.

---

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| `Element.scrollIntoView({ behavior:'smooth' })` | Web standard | Smooth-scroll to anchor element | Native browser API, no dependency |
| Inline `style.boxShadow` + `setTimeout` | Web standard | Transient highlight pulse | Used in project (user-approved pattern) |
| `window.*` global exposure | ES5 pattern | Cross-script function sharing | Existing pattern in project (`window.AutoRun`, `window.PortfolioHealth`) |

### Supporting
| Pattern | Purpose | When to Use |
|---------|---------|-------------|
| Guard: `window.rlEscapeHTML \|\| (s => ...)` | Inline fallback for missing global | At each bare call site in autoRun.js |
| `id` attribute on rendered HTML container | Provides `document.getElementById` target | Anchor IDs added during HTML generation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Inline style pulse | CSS class + stylesheet rule | Inline is cleaner for one-off; no stylesheet edit needed |
| Guard at call site | Pre-check before MDP block | Pre-check is also valid but requires restructuring the try block |

---

## Architecture Patterns

### Pattern 1: Tab-Switch Then Scroll
**What:** `switchTab` first (makes the element visible), then `getElementById` + `scrollIntoView` + inline highlight.
**When to use:** Any time a chip/button in a different area navigates to a specific sub-section in a hidden tab.
**Example:**
```javascript
// portfolioHealth.js chip onclick — after phase 9
if (window.TabManager) TabManager.switchTab('analytics');
const el = document.getElementById('analyticsVarSection');
if (el) {
    el.scrollIntoView({ behavior: 'smooth' });
    el.style.transition = 'box-shadow 0.8s';
    el.style.boxShadow = '0 0 0 3px #667eea';
    setTimeout(() => { el.style.boxShadow = ''; }, 800);
}
```

### Pattern 2: window.* Exposure for Cross-Script Globals
**What:** Append `window.fn = fn;` at end of the defining script so other scripts can call `window.fn` regardless of load order.
**When to use:** Any time a function defined in one `<script>` file is called by another `<script>` file without a bundler.
**Example:**
```javascript
// End of rlModels.js (to add)
window.rlEscapeHTML = rlEscapeHTML;
window.rlAlert = rlAlert;
```

### Pattern 3: Inline Fallback Guard
**What:** Replace bare `fn(x)` with `(window.fn || fallback)(x)` at each call site.
**When to use:** When the function may be absent (load-order failure, script error) and a meaningful fallback exists.
**Example:**
```javascript
// autoRun.js — guarded rlEscapeHTML
const _esc = window.rlEscapeHTML || (s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])));
// Then use _esc(state), _esc(action), _esc(eq), _esc(bd)

// autoRun.js — guarded rlAlert
const _alert = window.rlAlert || (msg => `<div style="background:#f8d7da;border:1px solid #f5c6cb;padding:12px;border-radius:4px;margin-top:10px;">${_esc(msg)}</div>`);
```

### Pattern 4: Unavailability vs Compute Error Distinction
**What:** When guards fire (rlEscapeHTML/rlAlert missing), show a message that names the dependency as unavailable rather than saying "MDP failed".
**Example message:** `'Portfolio MDP unavailable: rlModels.js did not load. Reload the page and try again.'`
This wording is distinct from a normal compute error (`'Portfolio MDP failed: <api error>'`).

### Anti-Patterns to Avoid
- **Adding id to heading element only:** Scroll target should be the outer wrapper div so the heading and content are above the fold.
- **Scrolling before tab switch:** The target element is in a hidden tab content div. scrollIntoView has no effect until the tab is visible.
- **Mutating analyticsRenderer.js return value in displayManager.js:** The container `id` for portfolio Monte Carlo must be placed on the wrapper div created in `displayManager.js` line 202, not inside `renderMonteCarlo()`, because the individual-ticker path (`renderTickerAnalytics`) wraps MonteCarlo inside a ticker block.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Smooth scroll animation | Custom JS animation loop | `scrollIntoView({ behavior:'smooth' })` | Native, zero code, works across browsers |
| Highlight animation | requestAnimationFrame loop | Inline transition + setTimeout | One-liner, already user-approved |
| XSS-safe string escaping | Custom regex in autoRun | Fallback inline in guard or `window.rlEscapeHTML` | `rlEscapeHTML` already correct; fallback is identical logic |

---

## Common Pitfalls

### Pitfall 1: Scroll Target in Hidden Tab
**What goes wrong:** `el.scrollIntoView()` called while the tab's content div has `display:none` — no visible scroll occurs.
**Why it happens:** The tab content is hidden until `switchTab` shows it.
**How to avoid:** Always call `switchTab` before `scrollIntoView`. In this project, tab content is rendered statically after the first scrape, so no async wait is needed — calling switchTab then scrollIntoView synchronously in the same onclick handler works.
**Warning signs:** No scroll on click; element exists in DOM but is not visible.

### Pitfall 2: Anchor ID Collision Between Portfolio and Per-Ticker Monte Carlo
**What goes wrong:** Both portfolio-level (`displayManager.js` wrapper) and per-ticker Monte Carlo (`analyticsRenderer.js renderTickerAnalytics`) render Monte Carlo sections. If both get the same id, `getElementById` returns the first match only.
**Why it happens:** `renderMonteCarlo()` is called from two code paths.
**How to avoid:** Add the anchor `id` only on the outer wrapper div in `displayManager.js` (line 202 area), not inside `renderMonteCarlo()`. The VaR chip should link to the portfolio-level section.
**Warning signs:** Click scrolls to wrong element for multi-ticker portfolios.

### Pitfall 3: rlAlert Calls rlEscapeHTML Internally
**What goes wrong:** The fallback for `rlAlert` itself calls `rlEscapeHTML` — if that fallback is not also guarded, the fallback throws.
**Why it happens:** `rlAlert` in `rlModels.js` line 30 calls `rlEscapeHTML(msg)` internally.
**How to avoid:** Define `_esc` guard first, then define `_alert` guard using `_esc` — both in the same block at the top of the `runAutoMDP` try block, or as local const declarations before the policy table rendering code.
**Warning signs:** Even the graceful error display fails with ReferenceError.

### Pitfall 4: Sharpe Scroll Target May Not Exist for Single-Ticker
**What goes wrong:** For single-ticker portfolios there is no Correlation/PCA section; the Sharpe section target might not be present in the rendered DOM.
**Why it happens:** `displayManager.js` skips correlation/PCA for single-ticker input.
**How to avoid:** Guard scroll with `if (el)` check — if target element is absent, the tab switch still succeeds gracefully; scroll is just skipped.
**Warning signs:** TypeError on `el.scrollIntoView(...)` when el is null.

---

## Code Examples

Verified from direct source inspection:

### VaR Chip Onclick — Current (portfolioHealth.js line 171)
```javascript
onclick="if(window.TabManager)TabManager.switchTab('analytics')"
```

### VaR Chip Onclick — After Phase 9
```javascript
onclick="if(window.TabManager){TabManager.switchTab('analytics');var el=document.getElementById('analyticsVarSection');if(el){el.scrollIntoView({behavior:'smooth'});el.style.transition='box-shadow 0.8s';el.style.boxShadow='0 0 0 3px #667eea';setTimeout(function(){el.style.boxShadow=''},800);}}"
```

### Portfolio Monte Carlo Wrapper — Current (displayManager.js line 202)
```javascript
html += '<div style="background: #ffffff; border-radius: 12px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-top: 4px solid #9b59b6;">';
```

### Portfolio Monte Carlo Wrapper — After Phase 9 (add id)
```javascript
html += '<div id="analyticsVarSection" style="background: #ffffff; border-radius: 12px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-top: 4px solid #9b59b6;">';
```

### Sharpe Target — Correlation / Summary Statistics section (displayManager.js ~line 189)
The correlation section renders first in `analyticsResults` and includes "Summary Statistics" which is the most natural Sharpe proxy. Add `id="analyticsSharpeSection"` on its outer wrapper in `renderCorrelation()` (analyticsRenderer.js line 117) or on the correlation wrapper in `displayManager.js`. For single-ticker (no correlation), fall back to scrolling to `analyticsVarSection` if `analyticsSharpeSection` is absent.

### window.* Exposure — End of rlModels.js (to add)
```javascript
// Expose shared helpers for cross-script access (e.g. autoRun.js)
window.rlEscapeHTML = rlEscapeHTML;
window.rlAlert      = rlAlert;
```

### Guard Pattern — autoRun.js runAutoMDP (lines 276-316 area)
```javascript
// Guards at top of the policy-table rendering block
const _esc   = window.rlEscapeHTML || (s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])));
const _alert = window.rlAlert      || (msg => `<div style="background:#f8d7da;border:1px solid #f5c6cb;padding:12px;border-radius:4px;margin-top:10px;">${_esc(msg)}</div>`);
// Then replace rlEscapeHTML( → _esc( and rlAlert( → _alert( in this function
```

---

## Files to Modify

| File | Change |
|------|--------|
| `static/js/portfolioHealth.js` | Lines 171 & 180: extend onclick handlers to scroll + highlight after switchTab |
| `static/js/displayManager.js` | Line ~202: add `id="analyticsVarSection"` to portfolio Monte Carlo wrapper div |
| `static/js/analyticsRenderer.js` | Line ~117: add `id="analyticsSharpeSection"` to correlation section outer div (or displayManager.js line ~189 wrapper) |
| `static/js/rlModels.js` | End of file: add `window.rlEscapeHTML = rlEscapeHTML; window.rlAlert = rlAlert;` |
| `static/js/autoRun.js` | Lines 279, 280, 293, 316: replace bare `rlEscapeHTML`/`rlAlert` with guarded `_esc`/`_alert` |

Total: 5 files, all frontend JS, no backend changes, no new dependencies.

---

## Validation Architecture

> `workflow.nyquist_validation` key is absent from `.planning/config.json` — treating as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual browser test (no automated JS test suite detected) |
| Config file | none |
| Quick run command | Open app, run scrape, observe chip behavior |
| Full suite command | Test VaR chip, Sharpe chip, simulate rlModels.js removal |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HEALTH-02 (VaR deep-link) | VaR chip switches to Analytics tab AND scrolls to Monte Carlo section with highlight | manual smoke | Open browser, click VaR chip post-scrape | N/A — manual only |
| HEALTH-02 (Sharpe deep-link) | Sharpe chip switches to Analytics tab AND scrolls to correlation/Sharpe section | manual smoke | Open browser, click Sharpe chip post-scrape | N/A — manual only |
| AUTO-05 (guard) | Removing rlModels.js script tag: MDP section shows graceful error, no uncaught ReferenceError | manual smoke | Remove `<script src=".../rlModels.js">` from index.html, reload, run analysis | N/A — manual only |

### Wave 0 Gaps
None — no automated test infrastructure needed for this phase. All verification is manual browser testing per success criteria.

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| `scrollTop` manual calculation | `scrollIntoView()` | scrollIntoView is the modern standard |
| CSS animation classes | Inline style + setTimeout | Both valid; inline chosen per user decision |
| Bare global function calls | `window.fn \|\| fallback` guard | Guard pattern is the defensive standard |

---

## Open Questions

1. **Sharpe anchor placement**
   - What we know: The Sharpe chip currently links to `analytics` tab top; the correlation section (first rendered) contains "Summary Statistics" with avg correlation and diversification score — not Sharpe directly.
   - What's unclear: Whether a dedicated Sharpe metric is rendered visibly in the per-ticker regression block (`renderRegression`) or only inside the portfolio health card itself.
   - Recommendation: Claude's discretion — place `id="analyticsSharpeSection"` on the correlation section wrapper (closest proxy for portfolio-level returns stats), with a graceful `if(el)` guard for single-ticker fallback.

2. **Timing of switchTab + scrollIntoView**
   - What we know: `TabManager.switchTab` sets `display:block` synchronously; `scrollIntoView` fires immediately after.
   - What's unclear: Whether a layout reflow is needed between the two calls on all browsers.
   - Recommendation: No sleep/setTimeout needed for the scroll. The `box-shadow` transition already has 0.8s CSS time; if scroll timing proves unreliable in practice, wrap in `setTimeout(..., 0)` (one tick).

---

## Sources

### Primary (HIGH confidence)
- Direct source inspection of `static/js/portfolioHealth.js` — confirmed chip onclick call sites at lines 171/180
- Direct source inspection of `static/js/autoRun.js` — confirmed bare `rlEscapeHTML`/`rlAlert` at lines 279, 280, 293, 316
- Direct source inspection of `static/js/rlModels.js` lines 21-31 — confirmed module-scoped definitions, no `window.*` exposure
- Direct source inspection of `static/js/displayManager.js` lines 188-210 — confirmed portfolio Monte Carlo wrapper location for anchor placement
- Direct source inspection of `static/js/analyticsRenderer.js` lines 361-364 — confirmed `renderMonteCarlo()` wrapper has no id
- MDN Web Docs (knowledge): `Element.scrollIntoView({ behavior: 'smooth' })` — native browser API, no polyfill needed for modern browsers

### Secondary (MEDIUM confidence)
- CONTEXT.md (user-approved) — inline `box-shadow` pulse technique and exact CSS values

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools are native browser APIs or established JS patterns, confirmed in project source
- Architecture: HIGH — based on direct code inspection, not assumptions
- Pitfalls: HIGH — anchor collision and scroll-in-hidden-tab are verified from the actual rendering path in displayManager.js
- Guard pattern: HIGH — confirmed rlAlert calls rlEscapeHTML internally (rlModels.js line 30)

**Research date:** 2026-03-11
**Valid until:** 2026-04-10 (stable — no external dependencies)
