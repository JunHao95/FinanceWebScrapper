---
phase: 06-form-streamlining-smart-defaults
plan: 01
subsystem: ui
tags: [javascript, html, forms, ux, smart-defaults]

# Dependency graph
requires:
  - phase: 05-stochastic-models-ui-completion
    provides: Stable FormManager with calculateAllocationTotal() and initEventListeners() in place
provides:
  - equalWeightsHint toggle logic in calculateAllocationTotal() (value and percent branches)
  - defaultsNote toggle listener in initEventListeners()
  - Static HTML elements #equalWeightsHint and #defaultsNote in index.html
affects:
  - 06-02-plan (button group / hero styling — shares index.html and forms.js)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "DOM id toggle pattern: getElementById + style.display toggle driven by JS state"
    - "details[open] toggle event listener for collapsible section visibility"

key-files:
  created: []
  modified:
    - static/js/forms.js
    - templates/index.html

key-decisions:
  - "equalWeightsHint hidden by default (display:none in HTML); JS controls visibility based on totalValue === 0"
  - "defaultsNote visible by default (display:block in HTML) because Advanced Settings is collapsed on load; toggle event hides it when section opens"
  - "Percent-mode branch explicitly hides hint to guard against mode-switch persistence bug (Pitfall 4)"

patterns-established:
  - "Hint elements start in correct initial state (HTML display attribute) — JS only updates on state change"

requirements-completed: [FORM-01, FORM-02, FORM-03, FORM-04, FORM-05, FORM-06, FORM-07]

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 6 Plan 01: Form Streamlining Smart Defaults Summary

**Equal-weights hint (Value mode, all-blank) and collapsed Advanced Settings defaults note added to forms.js and index.html with display-only DOM toggling**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T14:26:16Z
- **Completed:** 2026-03-09T14:27:50Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `#equalWeightsHint` show/hide logic inside `calculateAllocationTotal()` — appears when `totalValue === 0` in Value mode, disappears when any value is entered
- Added guard to hide hint in percent-mode branch, preventing persistence when user switches modes
- Added `details[toggle]` event listener in `initEventListeners()` to hide `#defaultsNote` when Advanced Settings opens and show it when closed
- Inserted static `#equalWeightsHint` and `#defaultsNote` HTML elements with correct initial display states

## Task Commits

Each task was committed atomically:

1. **Task 1: Add equal-weights hint toggle to calculateAllocationTotal() and initEventListeners()** - `0953697` (feat)
2. **Task 2: Insert static hint element and defaults note element into index.html** - `0bcf95c` (feat)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified

- `static/js/forms.js` - Three edits: hint toggle in value branch, hint hide guard in percent branch, toggle listener for defaultsNote
- `templates/index.html` - Two insertions: #equalWeightsHint after #allocationTotal, #defaultsNote after </details>

## Decisions Made

- `#equalWeightsHint` starts hidden via inline `style="display:none"` — JS only needs to switch to `block` on zero total
- `#defaultsNote` starts visible via `style="display:block"` because Advanced Settings is collapsed by default; no initial JS call needed
- Percent-mode branch hides hint explicitly to guard against mode-switch edge case

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Forms UX foundation (hints and notes) complete; ready for Plan 02 (button group / hero styling)
- No blockers

---
*Phase: 06-form-streamlining-smart-defaults*
*Completed: 2026-03-09*
