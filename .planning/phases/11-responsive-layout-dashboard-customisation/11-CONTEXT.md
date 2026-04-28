# Phase 11: Responsive Layout & Dashboard Customisation - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the app functional and presentable at 360px–1024px+ screen widths, and add collapse/expand toggles to per-ticker result card sections. No new features, no drag-to-reorder, no backend changes. Pure CSS/HTML/JS work.

Note: This phase was previously deferred from v2.0 ("web-first, desktop demo context"). It is now prioritised because both recruiter viewers and power users need mobile access.

</domain>

<decisions>
## Implementation Decisions

### Breakpoints
- Three breakpoints: 480px (phone), 768px (tablet), 1024px (desktop)
- Minimum target width: 360px (Android phones)
- All three in `static/css/styles.css` — no separate mobile stylesheet
- Viewport meta tag already present at `templates/index.html:5` — no change needed

### CSS Audit
- Full audit of fixed-px widths that overflow on small screens
- Replace hard-coded container widths with `max-width` + `width: 100%`
- Audit and fix: main layout container, results cards, forms, sidebar/drawer elements
- Existing `@media (max-width: 768px)` at `styles.css:1121` is the starting point — expand and layer the new 480px and 1024px rules around it

### Plotly Charts (Feature Parity)
- Charts render normally on mobile — no height cap, no collapse, no static replacement
- Plotly is already touch-capable (pinch-to-zoom, swipe-to-pan) — no extra JS needed
- Charts are not full-width capped — they follow their container width naturally

### Data Tables
- All multi-column tables (metrics, Greeks, peer comparison) get `overflow-x: auto` wrapper
- No card-per-row restructure — horizontal scroll is sufficient
- CSS class `.table-scroll-wrap` applied to all table containers at the relevant breakpoint

### Form Layout on Mobile
- Stack form inputs to single column, full width at 480px breakpoint
- Advanced settings already collapsed by default — no structural change needed
- Buttons already stack vertically (Phase 6 decision, `#scrapeForm .button-group flex-direction: column`)
- Portfolio allocation rows go full-width at 480px

### Tab Navigation
- Main tabs (5): `overflow-x: auto` on `.main-tab-buttons` container, hide scrollbar via `::-webkit-scrollbar { display: none }`
- Sub-tabs inside Stochastic Models and other panels: same treatment
- No JS change — pure CSS
- Active tab scrolled into view on activation (small JS addition: `element.scrollIntoView({ behavior: 'smooth', inline: 'nearest' })`)

### Chatbot on Mobile
- Toggle button: reduce from 60px to 44px at 480px breakpoint
- Chat window: `width: calc(100vw - 20px)` and `right: 10px` at 480px breakpoint (currently fixed at 360px width)
- No functionality change — all chat features accessible on mobile

### Dashboard Customisation
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

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `static/css/styles.css:1121`: Existing `@media (max-width: 768px)` block — expand here, add 480px and 1024px blocks alongside
- `static/css/styles.css:647`: `.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)) }` — already responsive for tablet, but needs 480px override to `1fr` single column
- `static/css/styles.css:719`: `.option-results-grid` — same auto-fit pattern, add 480px single-column override
- `static/js/chatbot.js`: All chatbot HTML injected via JS `innerHTML`. Mobile size adjustments target the injected `#chatbot-window` and `#chatbot-toggle-btn` via CSS — no JS change needed

### Established Patterns
- Phase 6 decision: `#scrapeForm .button-group { flex-direction: column }` already applied — form buttons are already stacked
- `flex-wrap: wrap` used throughout (`styles.css:134,140,159,439,478`) — many layouts already have basic wrapping
- Dark glassmorphism theme uses CSS variables (`--bg-deep`, `--accent`, `--border-glass`) — responsive overrides use the same variables, no colour changes

### Integration Points
- `templates/index.html`: Tab bar lives in `.main-tab-buttons` container — add `overflow-x: auto` CSS, no HTML change
- `static/js/tabs.js`: Add `element.scrollIntoView()` call after tab switch to keep active tab visible on mobile
- Per-ticker result cards: collapse toggle JS added to `static/js/displayManager.js` or a new small module; sessionStorage keys namespaced as `collapse-{ticker}-{section}`

</code_context>

<specifics>
## Specific Ideas

- No additional JS libraries for collapse — native `element.classList.toggle('collapsed')` + CSS transition on `max-height`
- Tabs scroll horizontally, no secondary nav component — keeps the existing tab identity and styling intact

</specifics>

<deferred>
## Deferred Ideas

- Drag-to-reorder sections — user can collapse but not reorder (explicit decision: out of scope)
- localStorage persistence across sessions — sessionStorage only (explicit decision)
- Replacing 3D charts with static images on mobile — charts render natively (explicit decision)
- Hamburger menu / dropdown for tab navigation — horizontal scroll chosen instead

</deferred>

---

*Phase: 11-responsive-layout-dashboard-customisation*
*Context gathered: 2026-04-29*
