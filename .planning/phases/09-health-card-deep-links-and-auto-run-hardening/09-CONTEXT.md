# Phase 9: Health Card Deep-Links & Auto-Run Hardening - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Two targeted fixes: (1) clicking VaR/Sharpe chips in the Portfolio Health card switches to the Analytics tab AND smooth-scrolls to the specific subsection with a brief highlight — not just the tab top; (2) `rlEscapeHTML` and `rlAlert` are exposed on `window` from `rlModels.js` and `autoRun.js` adds defensive guards so MDP rendering cannot throw `ReferenceError` if `rlModels.js` fails to load. No new models, no new analytics pipelines.

</domain>

<decisions>
## Implementation Decisions

### Scroll behavior
- Smooth scroll: `scrollIntoView({ behavior: 'smooth' })` — not instant jump
- After scrolling, briefly highlight the target section with a blue pulse (#667eea) lasting ~800ms then fading out
- Implementation: add/toggle a CSS class that applies `box-shadow` or `outline` in #667eea, remove it after 800ms via `setTimeout`

### Scroll UX — Claude's Discretion
- Timing: tab switch happens first, then scroll. If analytics content is already rendered (it is, post-scrape), scroll fires immediately after `switchTab`
- Exact CSS for the pulse animation (outline, box-shadow, or background tint — whichever is cleanest given existing card styles)
- Sharpe scroll target: whichever Analytics tab section most naturally represents "returns / Sharpe" (e.g., Summary Statistics section or the portfolio-level Sharpe display if one exists) — Claude to determine from the rendered HTML structure

### Guard failure message
- Claude's Discretion: MDP section shows a graceful error when `rlEscapeHTML`/`rlAlert` are unavailable (same ⚠ Failed badge pattern as normal MDP failure)
- Exact wording of the unavailability message is Claude's call — should distinguish from a normal MDP compute error if straightforward to do so

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `portfolioHealth.js` lines 171/180: VaR chip (`healthVarValue`) and Sharpe chip (`healthSharpeValue`) both currently call `TabManager.switchTab('analytics')` — add `scrollIntoView` + highlight after this call
- `rlEscapeHTML` (line 21) and `rlAlert` (line 27) defined as module-scoped functions in `rlModels.js` — expose via `window.rlEscapeHTML` and `window.rlAlert` at end of `rlModels.js`
- `analyticsRenderer.js` `renderMonteCarlo()` (line 363): renders the `🎲 Monte Carlo` VaR section — needs an anchor `id` on its container element for VaR chip scroll target
- `autoRun.js` lines 279/280/293/316: uses bare `rlEscapeHTML` and `rlAlert` — replace with guarded calls (`window.rlEscapeHTML || (s => ...)` pattern) or check `window.rlEscapeHTML` before MDP rendering

### Established Patterns
- Color palette: `#667eea` is the existing accent color (MDP table headers, badge styles in autoRun.js)
- Error display: `⚠ Failed` badge + inline message already used for regime/MDP failures in autoRun.js
- Tab switch: `TabManager.switchTab('analytics')` already in both chip onclick handlers

### Integration Points
- `portfolioHealth.js` chip onclick handlers: extend to scroll + highlight after tab switch
- `analyticsRenderer.js`: add `id` attributes to VaR section container and Sharpe/returns section container so chips can `document.getElementById(...).scrollIntoView()`
- `rlModels.js` end of file: add `window.rlEscapeHTML = rlEscapeHTML; window.rlAlert = rlAlert;`
- `autoRun.js` MDP rendering block: guard against missing globals

</code_context>

<specifics>
## Specific Ideas

- Highlight implementation: `el.style.transition = 'box-shadow 0.8s'; el.style.boxShadow = '0 0 0 3px #667eea'; setTimeout(() => el.style.boxShadow = '', 800)` — clean, no extra CSS class needed
- The VaR anchor should wrap the entire Monte Carlo metrics block (not just the heading) so the scrolled-to element is visible above the fold

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-health-card-deep-links-and-auto-run-hardening*
*Context gathered: 2026-03-11*
