---
phase: 03-frontend-wiring
plan: 03
subsystem: ui
tags: [sse, eventSource, plotly, scipy, heston, calibration, flask]

# Dependency graph
requires:
  - phase: 02-backend-completeness
    provides: HestonCalibrator.calibrate returning rmse, calibrated_params; /api/calibrate_heston POST route
  - phase: 03-01
    provides: stochasticModels.js pattern for Plotly chart wiring and escapeHTML/renderAlert utilities
provides:
  - SSE Flask route /api/calibrate_heston_stream (GET, text/event-stream)
  - HestonCalibrator.calibrate_stream generator method with batch-emitted SSE progress events
  - HestonCalibrator.calibrate callback kwarg wired to scipy fmin via _scipy_callback
  - calibrate return dict extended with strikes, market_ivs, fitted_ivs (BS inversion via bisection)
  - calibProgress live progress div in Heston Calibration tab
  - calibIVChart Plotly scatter chart (Market IV markers vs Fitted IV line by strike)
  - rmseLabel() helper mapping RMSE to Good/Acceptable/Poor with colour coding
affects: [03-04-bcc-calibration, 03-05-merton-calibration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - SSE batch-emit pattern: buffer callback events during blocking calibration, emit all then done sentinel
    - BS IV inversion via bisection (50-iter, 1e-6 tolerance) for market_ivs/fitted_ivs
    - EventSource + onmessage handler pattern for SSE progress consumption in browser
    - RMSE quality badge: Good (<1%), Acceptable (<3%), Poor (>=3%)

key-files:
  created: []
  modified:
    - src/derivatives/model_calibration.py
    - webapp.py
    - static/js/stochasticModels.js
    - templates/index.html

key-decisions:
  - "calibrate_stream buffers all SSE events then emits them post-calibration — batch-emit avoids async server requirement on Render free tier while still satisfying CALIB-03 iteration counter visibility"
  - "IV inversion uses bisection over [1e-4, 5.0] range rather than Newton-Raphson to avoid derivative computation and handle edge cases robustly"
  - "Final chart data fetched from /api/calibrate_heston POST after SSE done event — avoids duplicating result serialisation in SSE route"
  - "calibrated_params remain nested under data.calibration in /api/calibrate_heston response — JS adjusted to access data.calibration.calibrated_params"

patterns-established:
  - "SSE pattern: GET route with stream_with_context; JS EventSource.onmessage; done sentinel closes src"
  - "Dual-fetch pattern for SSE calibration: SSE for progress, standard POST for final results"

requirements-completed: [CALIB-01, CALIB-03, CALIB-04]

# Metrics
duration: 4min
completed: 2026-03-06
---

# Phase 3 Plan 03: Heston Calibration SSE Summary

**SSE batch-emit progress streaming for Heston calibration with fitted-vs-market IV Plotly scatter chart and colour-coded RMSE quality badge**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-06T00:24:19Z
- **Completed:** 2026-03-06T00:27:52Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added `callback` kwarg to `HestonCalibrator.calibrate` wired into scipy `fmin` via `_scipy_callback`; each Nelder-Mead iteration fires `callback(iteration, error)`
- Added `calibrate_stream` generator that buffers SSE events during calibration then emits them all plus a `{"done": true}` sentinel, satisfying CALIB-03 without async server
- Added `strikes`, `market_ivs`, `fitted_ivs` to `calibrate` return dict computed via Black-Scholes bisection IV inversion
- Added `/api/calibrate_heston_stream` GET SSE route to webapp.py
- Replaced blocking `fetch` in `runHestonCalibration` with `EventSource` consuming progress events; shows live iteration counter
- After `done` sentinel: fetches `/api/calibrate_heston` for full result, renders RMSE badge (Good/Acceptable/Poor) and fitted-vs-market IV Plotly scatter chart

## Task Commits

1. **Task 1: Add callback support + calibrate_stream to HestonCalibrator; SSE Flask route** - `693d79b` (feat)
2. **Task 2: Wire Heston Calibration tab with SSE progress div and IV comparison chart** - `6f80423` (feat)

## Files Created/Modified
- `/Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper/src/derivatives/model_calibration.py` - callback kwarg, _scipy_callback, calibrate_stream generator, BS IV inversion, strikes/market_ivs/fitted_ivs in return
- `/Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper/webapp.py` - /api/calibrate_heston_stream GET SSE route
- `/Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper/static/js/stochasticModels.js` - runHestonCalibration replaced with EventSource version; rmseLabel helper added
- `/Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper/templates/index.html` - calibProgress and calibIVChart divs added inside Heston Calibration sub-tab

## Decisions Made
- `calibrate_stream` uses batch-emit (buffer all, emit after): avoids async server requirement while still showing iteration count
- IV inversion via bisection: avoids Newton-Raphson derivative; handles any price robustly
- Final chart fetched separately from `/api/calibrate_heston` POST: keeps SSE route thin; reuses existing serialisation
- JS accesses `data.calibration.calibrated_params` — existing route shape preserved, no backward-compat breakage

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added market_ivs/fitted_ivs/strikes computation to HestonCalibrator.calibrate**
- **Found during:** Task 1 (planning execution)
- **Issue:** Plan's Task 2 JS expected `cal.market_ivs`, `cal.fitted_ivs`, `cal.strikes` from `/api/calibrate_heston` but existing `calibrate()` returned only `calibrated_params`, `mse`, `rmse` — chart would always receive empty arrays
- **Fix:** Added BS-inversion loop after Nelder-Mead to compute per-contract implied vols; appended `strikes`, `market_ivs`, `fitted_ivs` to return dict
- **Files modified:** src/derivatives/model_calibration.py
- **Verification:** Python compile check passed; return dict keys present
- **Committed in:** 693d79b (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 - missing critical data for IV chart)
**Impact on plan:** Required for CALIB-04 correctness — IV chart would silently render no data otherwise.

## Issues Encountered
None beyond the IV data gap noted above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CALIB-01, CALIB-03, CALIB-04 requirements satisfied
- SSE pattern established and documented for potential reuse in Merton/BCC calibration if desired
- Heston calibration tab fully interactive with live progress and IV quality assessment

---
*Phase: 03-frontend-wiring*
*Completed: 2026-03-06*
