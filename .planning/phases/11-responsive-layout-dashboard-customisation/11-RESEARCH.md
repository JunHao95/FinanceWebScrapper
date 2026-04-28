# Phase 11: Responsive Layout & Dashboard Customisation - Research

**Researched:** 2026-04-29
**Domain:** CSS responsive layout, JS collapse/expand toggles, sessionStorage state
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Breakpoints**
- Three breakpoints: 480px (phone), 768px (tablet), 1024px (desktop)
- Minimum target width: 360px (Android phones)
- All three in `static/css/styles.css` — no separate mobile stylesheet
- Viewport meta tag already present at `templates/index.html:5` — no change needed

**CSS Audit**
- Full audit of fixed-px widths that overflow on small screens
- Replace hard-coded container widths with `max-width` + `width: 100%`
- Audit and fix: main layout container, results cards, forms, sidebar/drawer elements
- Existing `@media (max-width: 768px)` at `styles.css:1121` is the starting point — expand and layer the new 480px and 1024px rules around it

**Plotly Charts (Feature Parity)**
- Charts render normally on mobile — no height cap, no collapse, no static replacement
- Plotly is already touch-capable (pinch-to-zoom, swipe-to-pan) — no extra JS needed
- Charts are not full-width capped — they follow their container width naturally

**Data Tables**
- All multi-column tables (metrics, Greeks, peer comparison) get `overflow-x: auto` wrapper
- No card-per-row restructure — horizontal scroll is sufficient
- CSS class `.table-scroll-wrap` applied to all table containers at the relevant breakpoint

**Form Layout on Mobile**
- Stack form inputs to single column, full width at 480px breakpoint
- Advanced settings already collapsed by default — no structural change needed
- Buttons already stack vertically (Phase 6 decision, `#scrapeForm .button-group flex-direction: column`)
- Portfolio allocation rows go full-width at 480px

**Tab Navigation**
- Main tabs (5): `overflow-x: auto` on `.main-tab-buttons` container, hide scrollbar via `::-webkit-scrollbar { display: none }`
- Sub-tabs inside Stochastic Models and other panels: same treatment
- No JS change — pure CSS
- Active tab scrolled into view on activation (small JS addition: `element.scrollIntoView({ behavior: 'smooth', inline: 'nearest' })`)

**Chatbot on Mobile**
- Toggle button: reduce from 60px to 44px at 480px breakpoint
- Chat window: `width: calc(100vw - 20px)` and `right: 10px` at 480px breakpoint (currently fixed at 360px width)
- No functionality change — all chat features accessible on mobile

**Dashboard Customisation**
- Collapse/expand toggles on per-ticker card sections only
- Collapsible sections: Health Card, Deep Analysis group (Health Score / Earnings Quality / DCF / Peer Comparison), Regime Detection autorun results, Trading Indicators panel
- Each section header gets a toggle chevron (▼/▶) — clicking collapses/expands the body
- State stored in `sessionStorage` keyed by `ticker-sectionName` — resets when browser tab closes
- Always expanded on initial load (first scrape for a ticker)
- Section remains collapsed/expanded if user re-runs analysis and updates same ticker

### Claude's Discretion
- Exact chevron icon / animation style for collapse toggles
- Scrollbar hide approach on tab nav (WebKit vs. standard scrollbar-width)
- Whether to add touch swipe gesture hints on tab bars
- Exact mobile typography scale adjustments (font-size, line-height)

### Deferred Ideas (OUT OF SCOPE)
- Drag-to-reorder sections
- localStorage persistence across sessions — sessionStorage only
- Replacing 3D charts with static images on mobile
- Hamburger menu / dropdown for tab navigation
</user_constraints>

---

## Summary

Phase 11 is a pure CSS/JS polish phase with zero backend changes. The codebase already has a solid responsive foundation: the `.container` uses `max-width: 1400px`, most grids use `auto-fit` or `flex-wrap`, and an existing `@media (max-width: 768px)` block at `styles.css:1121` handles the coarsest breakpoints. The gaps are (1) the 480px and 1024px breakpoints that don't yet exist, (2) fixed-width elements that overflow at 360–480px (settings drawer at 340px fixed, chatbot at 420px fixed, `.allocation-input-row` label at `flex: 0 0 100px`), and (3) the absence of per-section collapse toggles within per-ticker cards.

The collapse infrastructure is partially present: `displayManager.js` already uses `.collapsed` class + `max-height` transition for the top-level ticker card itself, and `healthScore.js` uses inline `display: none/block` toggling for the Deep Analysis group. Phase 11 standardises this pattern across four section types (Portfolio Health Card, Deep Analysis group, Regime Detection block, Trading Indicators panel) and moves state into `sessionStorage` so it persists across re-runs within the same browser tab.

**Primary recommendation:** Expand the existing `@media (max-width: 768px)` block, add flanking 480px and 1024px blocks in the same file, fix the five overflow-causing fixed widths, and add sessionStorage-backed collapse toggles to four named section types — all with no new libraries and no backend changes.

---

## Standard Stack

### Core (all already in-project, no new installs)

| Item | Version/Location | Purpose | Notes |
|------|-----------------|---------|-------|
| CSS custom properties (`--bg-deep`, `--accent`, etc.) | `styles.css:6-21` | Theme tokens used in all responsive overrides | Never hardcode colours in new media queries |
| `element.classList.toggle('collapsed')` | Native browser API | Section collapse/expand | Already used by `DisplayManager.toggleTicker` |
| `max-height` CSS transition | Native CSS | Smooth collapse animation | Already applied to `.ticker-content` at `styles.css:636-644` |
| `sessionStorage` | Native browser API | Per-section state persistence within tab session | Not yet used — must be added |
| `element.scrollIntoView({ behavior: 'smooth', inline: 'nearest' })` | Native browser API | Keep active tab visible on mobile | Must be added to `TabManager.switchTab` and `TabManager.switchMainTab` |

### No New Libraries Required
This phase must not introduce any npm packages, CDN scripts, or Python dependencies. All techniques used are native CSS and vanilla JS.

---

## Architecture Patterns

### Recommended File Change Scope

```
static/css/styles.css          — all responsive CSS changes (expand existing @media block, add 480px + 1024px blocks)
static/js/displayManager.js    — add SectionCollapse helper, wire into createTickerCard
static/js/tabs.js              — add scrollIntoView() call after tab activation
static/js/portfolioHealth.js   — optionally add section toggle to health card header (see pattern below)
static/js/autoRun.js           — optionally add section toggle to autoRegimeBlock header
```

### Pattern 1: CSS Breakpoint Layering

The existing block at `styles.css:1121` covers `max-width: 768px`. The correct structure to add 480px and 1024px flanking blocks is:

```css
/* Source: existing pattern at styles.css:1121 */

/* ── 1024px: side-by-side → constrained desktop ── */
@media (max-width: 1024px) {
    /* Tighten padding on panels that have 30px desktop padding */
    .input-section,
    .main-tabs { padding: 20px; }
}

/* ── 768px: tablet (EXISTING — expand here) ── */
@media (max-width: 768px) {
    header h1 { font-size: 1.8rem; }
    .metrics-grid { grid-template-columns: 1fr; }
    .button-group { flex-direction: column; }
    button { width: 100%; }
    .main-tab-button { padding: 12px 14px; font-size: 12px; }
    .settings-drawer { width: 100%; }      /* already present */
    .skeleton-preview { flex-direction: column; }

    /* NEW additions at 768px */
    .allocation-input-row { flex-wrap: wrap; }
    .allocation-input-row label { flex: 0 0 100%; }
    .allocation-input-row input { width: 100%; }
}

/* ── 480px: phone ── */
@media (max-width: 480px) {
    body { padding: 10px; }
    header h1 { font-size: 1.4rem; }
    header { padding: 16px; }
    .input-section { padding: 16px; }

    /* Tab scrolling */
    .tabs { flex-wrap: nowrap; overflow-x: auto; }
    .tabs::-webkit-scrollbar { display: none; }
    .tab-button { padding: 10px 16px; font-size: 14px; white-space: nowrap; flex-shrink: 0; }

    /* Chatbot */
    #chatbot-toggle-btn { width: 44px; height: 44px; font-size: 20px; }
    #chatbot-window { width: calc(100vw - 20px); right: 10px; }

    /* Table overflow */
    .table-scroll-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }

    /* Allocation rows */
    .allocation-input-row { flex-direction: column; align-items: stretch; }
    .allocation-input-row label { flex: none; }

    /* .metrics-grid already 1fr from 768px rule — no duplicate needed */
    .analysis-grid { grid-template-columns: 1fr; }
    .option-results-grid { grid-template-columns: 1fr; }
}
```

### Pattern 2: Section Collapse Toggle (sessionStorage-backed)

The **existing** collapse pattern in `displayManager.js` uses `classList.toggle('collapsed')` + `max-height` CSS. `healthScore.js` uses inline `display` toggling instead. Phase 11 standardises on `classList` + CSS `max-height` for all four section types, with `sessionStorage` for state.

Key naming convention: `sessionStorage` key = `collapse-{ticker}-{sectionName}`
Section name tokens: `healthCard`, `deepAnalysis`, `regimeDetection`, `tradingIndicators`

```javascript
// Pattern: SectionCollapse helper (add to displayManager.js or a new small module)
// Source: derived from existing DisplayManager.toggleTicker pattern (displayManager.js:266-281)

const SectionCollapse = {
    KEY_PREFIX: 'collapse-',

    getKey(ticker, section) {
        return `${this.KEY_PREFIX}${ticker}-${section}`;
    },

    isCollapsed(ticker, section) {
        return sessionStorage.getItem(this.getKey(ticker, section)) === '1';
    },

    setCollapsed(ticker, section, collapsed) {
        if (collapsed) {
            sessionStorage.setItem(this.getKey(ticker, section), '1');
        } else {
            sessionStorage.removeItem(this.getKey(ticker, section));
        }
    },

    toggle(bodyEl, headerEl, chevronEl, ticker, section) {
        const nowCollapsed = !bodyEl.classList.contains('collapsed');
        bodyEl.classList.toggle('collapsed', nowCollapsed);
        if (chevronEl) chevronEl.style.transform = nowCollapsed ? 'rotate(-90deg)' : '';
        this.setCollapsed(ticker, section, nowCollapsed);
    },

    applyInitialState(bodyEl, headerEl, chevronEl, ticker, section) {
        // Always expanded on first scrape (sessionStorage empty = not collapsed)
        const collapsed = this.isCollapsed(ticker, section);
        bodyEl.classList.toggle('collapsed', collapsed);
        if (chevronEl) chevronEl.style.transform = collapsed ? 'rotate(-90deg)' : '';
    }
};
```

CSS required for section collapse (same `max-height` pattern already used for `.ticker-content`):

```css
/* Section collapse — reuse existing pattern from styles.css:636-644 */
.section-body {
    max-height: 5000px;      /* large enough for any section */
    overflow: hidden;
    transition: max-height 0.35s ease, opacity 0.35s ease;
    opacity: 1;
}

.section-body.collapsed {
    max-height: 0;
    opacity: 0;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    user-select: none;
}

.section-chevron {
    transition: transform 0.3s ease;
    font-size: 0.9rem;
    color: var(--text-secondary);
}
```

### Pattern 3: Tab scrollIntoView

Add one call after activating a tab in both `switchTab` and `switchMainTab`:

```javascript
// Add to TabManager.switchTab (tabs.js) immediately after classList.add('active') on the button
// Source: MDN scrollIntoView API — https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollIntoView
if (targetButton) {
    targetButton.scrollIntoView({ behavior: 'smooth', inline: 'nearest', block: 'nearest' });
}
```

### Pattern 4: `.table-scroll-wrap` Application

Tables requiring the wrapper (HTML must be wrapped in `displayManager.js` or `analyticsRenderer.js` when building innerHTML):

- Peer comparison raw table (`.show-peers` toggle in `peerComparison.js`)
- Options Greeks table (`.result-card table` in `optionsDisplay.js`)
- Any `<table>` inside `.result-card` or `.metric-group`

Approach: in the JS that generates the table HTML, wrap `<table>` tags:

```javascript
// Wrap tables in JS-generated HTML (displayManager.js / analyticsRenderer.js)
html += '<div class="table-scroll-wrap"><table>...</table></div>';
```

### Anti-Patterns to Avoid

- **Hardcoding `max-height: 10000px` in JS style:** Already an issue in `displayManager.js` (line 636 uses 10000px inline). Use the `.section-body` CSS class instead — CSS transitions work correctly with classes.
- **Mixing `display: none` with `max-height` toggle on the same element:** `healthScore.js` uses `display` style toggling; Phase 11 must migrate those to `classList` toggle so CSS handles the transition.
- **Adding `!important` to responsive overrides:** The glassmorphism theme has low specificity by design; media queries at the same specificity level work without `!important`.
- **Applying `width: 100%` to the global `button` selector inside a media query:** Already done at `styles.css:1125` — don't duplicate. Scope overrides to specific button types (e.g., `.settings-gear-btn`) to avoid breaking small pill buttons.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Smooth collapse animation | JS height calculation with `requestAnimationFrame` | CSS `max-height` + `transition` (already in codebase) | Browser handles rendering; existing pattern at `styles.css:636` |
| Scrollbar hiding on tab nav | JS scroll detection | `::-webkit-scrollbar { display: none }` + `scrollbar-width: none` | Two-line CSS; works in all target browsers |
| sessionStorage key management | Ad-hoc `sessionStorage.setItem` calls scattered in each module | Centralised `SectionCollapse` helper | Avoids key name collisions across 4 section types |
| Mobile viewport detection | JS `window.innerWidth` checks | CSS media queries | More performant; no layout thrash |

---

## Common Pitfalls

### Pitfall 1: `max-height` Value Too Small
**What goes wrong:** A section body contains a Plotly chart that is taller than the `max-height` value set in `.section-body`, causing the chart to be clipped even when "expanded."
**Why it happens:** Plotly charts with many data points or legends can be 600px+ tall; autorun regime blocks contain two stacked charts.
**How to avoid:** Set `max-height: 5000px` on the expanded state. This is safe — the transition duration (0.35s) is fixed regardless of the max-height value; only the animated distance differs.
**Warning signs:** Section header toggles correctly but content appears cut off.

### Pitfall 2: Settings Drawer Overlapping on Mobile
**What goes wrong:** The `.settings-drawer` is `width: 340px` and fixed-positioned. On a 360px screen it leaves only 20px of the main content visible when open.
**Why it happens:** `width: 100%` is already in the 768px block (`styles.css:1127`) but the breakpoint may not trigger at 360px-wide Android Chrome (due to device-pixel-ratio scaling).
**How to avoid:** Confirm the 768px rule applies at 360px physical width. The viewport meta tag is already set to `width=device-width` at `index.html:5`, so CSS pixel width matches device width.

### Pitfall 3: `button { width: 100% }` at 768px Breaks Small Buttons
**What goes wrong:** The global `button { width: 100% }` rule at `styles.css:1125` makes `.ticker-badge`, `.mode-btn`, `.chip .chip-remove`, and `.drawer-close-btn` all stretch to 100% width on tablet/phone.
**Why it happens:** Those elements use the base `button` selector, not a more specific class.
**How to avoid:** The fix already scopes the overrides but auditing is needed. Add `width: auto` resets for pill/icon buttons inside the same media query block:

```css
@media (max-width: 768px) {
    /* existing rules ... */
    .ticker-badge,
    .mode-btn,
    .chip .chip-remove,
    .drawer-close-btn,
    .settings-gear-btn { width: auto; }
}
```

### Pitfall 4: sessionStorage Key Collision on Re-Scrape
**What goes wrong:** User scrapes AAPL, collapses Deep Analysis, then re-scrapes AAPL. Because the key is `collapse-AAPL-deepAnalysis`, the second render reads it and starts collapsed — correct behaviour. But if `clearSession()` in `stockScraper.js` calls `sessionStorage.clear()`, it wipes all keys including ones the user deliberately set.
**Why it happens:** `PeerComparison.clearSession()` uses an in-memory cache, not `sessionStorage`. The collapse keys live in `sessionStorage` and must survive re-runs within the same tab.
**How to avoid:** Do NOT call `sessionStorage.clear()` anywhere. Only call `sessionStorage.removeItem(key)` for specific keys when a ticker is removed from the analysis. Section state is designed to survive re-runs (per CONTEXT.md: "Section remains collapsed/expanded if user re-runs analysis and updates same ticker").

### Pitfall 5: `.main-tab-buttons` Already Has `overflow-x: auto`
**What goes wrong:** Planner adds `overflow-x: auto` to `.main-tab-buttons` in the media query, but it's already set unconditionally at `styles.css:1045`. The addition is harmless but redundant.
**Why it happens:** The CONTEXT.md says to add it, but it already exists.
**How to avoid:** Verify before adding. The remaining gap is scrollbar hiding and `scrollIntoView` — those are the actual changes needed for the main tab bar. The inner `.tabs` container (results tabs at `styles.css:954`) uses `flex-wrap: wrap` — it needs to be changed to `flex-wrap: nowrap; overflow-x: auto` at 480px.

### Pitfall 6: `healthScore.js` Uses `display` Not `classList`
**What goes wrong:** `healthScore.js:toggleDeepAnalysis` uses `content.style.display = 'none'/'block'`. If Phase 11 adds `.section-body.collapsed { max-height: 0 }` CSS, the inline style overrides the class, breaking the transition.
**Why it happens:** Phase 13 implemented its own ad-hoc toggle before the Phase 11 standard was defined.
**How to avoid:** Migrate `toggleDeepAnalysis` in `healthScore.js` to use `classList.toggle('collapsed')` and remove the inline `display` style. Also add the `section-body`/`section-header` class names to the generated HTML in `buildHTML`.

---

## Code Examples

### Existing Collapse Pattern (reference for new sections)
```css
/* Source: styles.css:636-644 */
.ticker-content {
    max-height: 10000px;
    opacity: 1;
    overflow: hidden;
    transition: max-height 0.4s ease, opacity 0.4s ease;
}

.ticker-content.collapsed {
    max-height: 0;
    opacity: 0;
}
```

### `.allocation-input-row` Mobile Fix
```css
/* Source: styles.css:847-873 (existing desktop), new 480px override */
@media (max-width: 480px) {
    .allocation-input-row {
        flex-direction: column;
        align-items: stretch;
    }
    .allocation-input-row label {
        flex: none;
    }
    .allocation-input-row input {
        width: 100%;
    }
}
```

### Chatbot Mobile Override
```css
/* Source: styles.css:1141 (existing 60px), 1166 (existing 420px fixed width) */
@media (max-width: 480px) {
    #chatbot-toggle-btn {
        width: 44px;
        height: 44px;
        font-size: 20px;
    }
    #chatbot-window {
        width: calc(100vw - 20px);
        right: 10px;
    }
}
```

### Hiding Tab Scrollbar (Cross-Browser)
```css
/* Standard (Firefox 64+) */
.tabs { scrollbar-width: none; }
/* WebKit (Chrome, Safari, Edge) */
.tabs::-webkit-scrollbar { display: none; }
```

---

## State of the Art

| Old Approach | Current Approach | Confidence | Impact |
|--------------|-----------------|------------|--------|
| Separate mobile stylesheet | Single file, layered `@media` blocks | HIGH | No approach change needed |
| JS height animation | CSS `max-height` transition | HIGH | Already used in codebase |
| `localStorage` for UI state | `sessionStorage` for tab-session state | HIGH — locked decision | Resets on tab close |
| `display: none/block` for collapse | `classList.toggle + max-height` | HIGH | Migrating `healthScore.js` required |

---

## Open Questions

1. **Portfolio Health Card (`#portfolioHealthCard`) section toggle**
   - What we know: The card is injected by `portfolioHealth.js` via inline HTML string (line 160). The card ID is `portfolioHealthCard` and it appears above the tab nav.
   - What's unclear: CONTEXT.md says "Health Card" is a collapsible section, but the Health Card is portfolio-level (not per-ticker). The collapse key would be `collapse-portfolio-healthCard` with no ticker.
   - Recommendation: Use a fixed key `collapse-portfolio-healthCard`. Implement toggle the same way as per-ticker sections. This is Claude's discretion territory.

2. **Trading Indicators per-ticker panel**
   - What we know: Trading Indicators renders into `#tradingIndicatorsTabContent` (not inside `.ticker-results` cards). It is a separate tab, not a section within a per-ticker card.
   - What's unclear: CONTEXT.md lists "Trading Indicators panel" as a collapsible section in per-ticker cards. But the Trading Indicators tab renders globally. This may refer to the per-ticker block within that tab (each ticker gets a `.autoRegimeBlock`-style div), not the tab itself.
   - Recommendation: Interpret as the per-ticker Plotly block inside `#tradingIndicatorsTabContent`. Each ticker block gets a collapse header.

---

## Validation Architecture

`workflow.nyquist_validation` is not set in `.planning/config.json` — treated as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, no version pinned in config) |
| Config file | `pytest.ini` — not found; `Makefile` shows `pytest -m unit -q` |
| Quick run command | `pytest -m unit -q` |
| Full suite command | `make test` |

### Phase Requirements → Test Map

Phase 11 has no formal REQ-IDs. All deliverables are CSS/JS UI changes with no backend routes. Testing strategy:

| Deliverable | Behavior | Test Type | Automated Command | File Exists? |
|-------------|----------|-----------|-------------------|-------------|
| CSS breakpoints compile without errors | `styles.css` has no invalid CSS | smoke (manual lint) | `npx stylelint static/css/styles.css` (optional) | CSS file exists |
| Section collapse JS helper | `SectionCollapse.toggle` / `isCollapsed` / `setCollapsed` work correctly | unit (JS — not in pytest) | Manual or browser test | No pytest coverage (JS module) |
| `TabManager.switchTab` scrollIntoView | Method calls `scrollIntoView` after activating tab | Manual browser test | Open DevTools, verify no console errors | N/A |
| `healthScore.js` collapse migration | `toggleDeepAnalysis` uses `classList` not `display` | unit JS or grep check | `grep "display" static/js/healthScore.js` confirms removal | Partial — needs update |

**Note:** This phase is entirely frontend CSS/JS with no Python backend changes. The existing pytest suite covers backend routes; it is not affected by this phase and remains green without modification.

### Sampling Rate
- **Per task commit:** Manual smoke test — resize browser to 360px, verify no horizontal overflow
- **Per wave merge:** Full pytest suite (`make test`) — confirms no backend regression
- **Phase gate:** Visual check at 360px, 480px, 768px, 1024px before `/gsd:verify-work`

### Wave 0 Gaps
None — existing test infrastructure covers all backend. This phase introduces no new Python files.
Frontend JS unit testing is manual only (no Jest/Vitest configured in this project).

---

## Sources

### Primary (HIGH confidence)
- Direct codebase read: `static/css/styles.css` (1538 lines) — confirmed all existing selectors, breakpoints, and fixed widths
- Direct codebase read: `static/js/displayManager.js` — confirmed existing collapse pattern (`classList`, `max-height`)
- Direct codebase read: `static/js/healthScore.js` — confirmed inline `display` toggle (migration target)
- Direct codebase read: `static/js/tabs.js` — confirmed no `scrollIntoView` present
- Direct codebase read: `templates/index.html` — confirmed `.tabs`, `.main-tab-buttons`, chatbot element IDs, viewport meta
- MDN Web Docs (common knowledge, HIGH): `scrollIntoView`, `sessionStorage`, `classList.toggle`, CSS `@media`, `overflow-x: auto`

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions — locked by user in prior discussion session (treated as authoritative)
- `styles.css:1045` confirms `.main-tab-buttons` already has `overflow-x: auto` — the remaining gap is scrollbar hiding + inner `.tabs` container

### Tertiary (LOW confidence)
- None — all research derived from direct codebase inspection

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all techniques are native browser APIs already used in-project
- Architecture: HIGH — patterns derived from existing code; no novel patterns introduced
- Pitfalls: HIGH — identified by reading actual implementation (not hypothetical)

**Research date:** 2026-04-29
**Valid until:** This research is tied to the codebase state as of 2026-04-29. Valid indefinitely unless JS modules or CSS are significantly restructured.
