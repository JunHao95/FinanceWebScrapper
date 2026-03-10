---
phase: 07-auto-run-extended-analysis-after-scrape
plan: 01
subsystem: ui
tags: [javascript, plotly, fetch, promise, regime-detection, portfolio-mdp, auto-run]

# Dependency graph
requires:
  - phase: 06-form-streamlining-smart-defaults
    provides: scrape form and stockScraper.js entry point for post-scrape hooks
  - phase: 05-stochastic-models-ui-completion
    provides: stochasticModels.js Plotly rendering patterns for regime detection
  - phase: 04-ml-in-finance-module
    provides: rlModels.js Plotly rendering patterns for Portfolio MDP
provides:
  - window.AutoRun.triggerAutoRun(tickers) — entry point for post-scrape auto analysis
  - autoRun.js — self-contained module handling HTML scaffold, parallel API calls, badge transitions, chart rendering
  - autoRunSection injected at top of #analyticsResults with regime + MDP blocks
affects:
  - 07-02 — stockScraper.js integration will call AutoRun.triggerAutoRun after scrape

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Promise.allSettled for parallel fetch calls with isolated per-ticker error handling
    - insertAdjacentHTML afterbegin to prepend auto-run section above existing analytics
    - Container ID namespacing with auto prefix to avoid collision with manual Stochastic Models tab

key-files:
  created:
    - static/js/autoRun.js
  modified:
    - templates/index.html

key-decisions:
  - "autoRun.js uses rlEscapeHTML (from rlModels.js) for policy table cells — consistent with rlModels scope"
  - "MDP block rendered conditionally only when tickers.length >= 2 to avoid meaningless single-ticker MDP"
  - "Promise.allSettled used so one ticker failure does not block other regime calls or the MDP"
  - "autoRunSection removed and re-injected on each triggerAutoRun call to prevent duplicate sections on re-runs"

patterns-established:
  - "Auto-namespaced container IDs: autoRegimeProb_{ticker}, autoRegimePrice_{ticker}, autoMDP_line, autoMDP_vbar"
  - "Badge lifecycle: BADGE_RUNNING (gray) on inject -> BADGE_DONE (green) or BADGE_FAILED (red) after fetch"

requirements-completed:
  - AUTO-01
  - AUTO-02
  - AUTO-03
  - AUTO-04
  - AUTO-05

# Metrics
duration: 4min
completed: 2026-03-10
---

# Phase 7 Plan 01: Auto-Run Module Summary

**Self-contained autoRun.js orchestrator that injects regime detection and Portfolio MDP blocks into the Analytics tab after each scrape, using Promise.allSettled for parallel isolated API calls and Plotly charts with auto-namespaced container IDs**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-10T07:25:38Z
- **Completed:** 2026-03-10T07:29:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created static/js/autoRun.js exposing window.AutoRun.triggerAutoRun(tickers)
- Regime detection runs per ticker in parallel; each failure is isolated (other tickers continue)
- Portfolio MDP block conditionally rendered only for 2+ ticker scrapes, fixed to SPY/IEF
- Badge state transitions (Rolling.../Running... -> Done/Failed) inline on each section header
- Registered autoRun.js in index.html between rlModels.js and main.js

## Task Commits

Each task was committed atomically:

1. **Task 1: Create static/js/autoRun.js** - `b611268` (feat)
2. **Task 2: Add autoRun.js script tag to index.html** - `0872169` (feat)

## Files Created/Modified

- `static/js/autoRun.js` — Full auto-run orchestration module with buildAutoRunHTML, renderRegimeCharts, runAutoRegime, runAutoMDP, triggerAutoRun
- `templates/index.html` — Added script tag for autoRun.js after rlModels.js and before main.js

## Decisions Made

- Used `rlEscapeHTML` (from rlModels.js) for policy table rendering since it is globally available at runtime, consistent with the rlModels pattern
- MDP block only rendered when `tickers.length >= 2` — a single-ticker scrape silently skips it with no error shown
- `Promise.allSettled` used so one failing regime call does not cancel others
- `document.getElementById('autoRunSection')?.remove()` guards against duplicate injection on re-runs

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- window.AutoRun.triggerAutoRun is ready to be called from stockScraper.js (plan 07-02)
- All chart container IDs are namespaced and will not collide with manual Stochastic Models tab

---
*Phase: 07-auto-run-extended-analysis-after-scrape*
*Completed: 2026-03-10*
