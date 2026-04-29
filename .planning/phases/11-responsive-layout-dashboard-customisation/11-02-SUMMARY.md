---
phase: 11-responsive-layout-dashboard-customisation
plan: 02
status: complete
---

## What was done

Implemented `SectionCollapse` helper in `displayManager.js` and wired collapse toggles into healthScore.js, autoRun.js, and portfolioHealth.js.

### Changes

**displayManager.js**
- Added `SectionCollapse` object with `toggle`, `applyInitialState`, `getKey`, `isCollapsed`, `setCollapsed` methods
- Added `window.SectionCollapse = SectionCollapse` and `module.exports = { DisplayManager, SectionCollapse }` exports

**healthScore.js**
- Removed `_expandedTickers` Set (replaced by sessionStorage)
- Migrated `buildHTML` from inline `display:${displayStyle}` to `class="section-body"` and `class="section-header"`
- Deep analysis chevron changed to `<span class="section-chevron" id="deep-analysis-chevron-${ticker}">▼</span>`
- `toggleDeepAnalysis` now calls `SectionCollapse.toggle` (classList fallback if SectionCollapse unavailable)
- `computeGrade` schedules `SectionCollapse.applyInitialState` via `setTimeout(0)` after HTML insertion
- `clearSession` is now a no-op (sessionStorage keys are scoped per-key, not bulk-cleared)
- Zero `style.display` inline toggle calls remain

**autoRun.js**
- Each per-ticker `autoRegimeBlock` now has `.section-header` div with chevron + `.section-body` wrapper
- `triggerAutoRun` calls `SectionCollapse.applyInitialState` for each ticker body after HTML scaffold insertion

**portfolioHealth.js**
- `portfolioHealthCard` now has `.section-header` (with chevron) and `.section-body#portfolioHealthBody` structure
- `initCard` calls `SectionCollapse.applyInitialState` after card is inserted into DOM
- sessionStorage key: `collapse-portfolio-healthCard`

## Verification passed
- `SectionCollapse` defined with 5 methods
- `window.SectionCollapse` exported
- `healthScore.js`: `style.display` count = 0
- `autoRun.js`: section-header/section-body present
- `portfolioHealth.js`: section-header/section-body present
