---
phase: 03-frontend-wiring
plan: 05
subsystem: ui
tags: [plotly, javascript, markov, credit-risk, interest-rates, heatmap]

# Dependency graph
requires:
  - phase: 03-01
    provides: regime detection JS wired with Plotly charts
  - phase: 03-02
    provides: Heston Pricing sub-tab with 3D IV surface
  - phase: 03-03
    provides: Heston Calibration SSE + IV comparison chart
  - phase: 03-04
    provides: BCC Calibration sub-tab wired end-to-end
  - phase: 02-backend-completeness
    provides: /api/markov_chain, /api/credit_risk, /api/interest_rate_model backends
provides:
  - Markov transition matrix heatmap (Blues colorscale) in Credit tab via /api/markov_chain nstep n=1
  - Default probability term structure line chart (runCreditRisk)
  - Survival curve area chart with fill-to-zero (runCreditRisk)
  - CIR/Vasicek yield curve line chart (runCIRModel) with Feller badge
affects: [04-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns: [Plotly.newPlot for all result rendering, inline div IDs injected via innerHTML before chart call, purge-on-rerun via innerHTML reset]

key-files:
  created: []
  modified:
    - static/js/stochasticModels.js

key-decisions:
  - "Markov heatmap fetched via secondary call to /api/markov_chain nstep n=1 inside runCreditRisk — no separate Markov sub-tab needed"
  - "Survival curve uses ttd.survival_curve field (Monte Carlo path), not bond_analysis survival field, for chart data"
  - "Default probability chart uses term.cumulative_default_prob * 100 to convert to percentage axis"
  - "yieldCurveChart uses spot_rate * 100 from yield_curve array, not raw yields field — matches actual API response shape"

patterns-established:
  - "Pattern: Inject div IDs via innerHTML string, then call Plotly.newPlot immediately after — avoids timing issues"
  - "Pattern: Wrap secondary API calls (heatmap) in try/catch and swallow errors — bonus chart, not blocking"

requirements-completed: [CALIB-01, CALIB-02, CALIB-03, CALIB-04, CALIB-05, REGIME-01, REGIME-02, REGIME-03, REGIME-04, REGIME-05, HESTON-01, HESTON-02, HESTON-03, HESTON-04, HESTON-05]

# Metrics
duration: 5min
completed: 2026-03-07
---

# Phase 3 Plan 05: Markov/Credit/Rates Plotly Chart Upgrade Summary

**CIR yield curve + Feller badge, credit default prob term structure + survival area chart, and S&P Markov transition matrix heatmap all rendered via Plotly in their respective sub-tabs**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-06T23:00:00Z
- **Completed:** 2026-03-06T23:05:43Z
- **Tasks:** 1 of 1 auto tasks (+ 1 human-verify checkpoint pending)
- **Files modified:** 1

## Accomplishments

- `runCIRModel`: added `yieldCurveChart` Plotly line chart after parameter table, with Feller condition badge (green/red)
- `runCreditRisk`: added `defaultProbChart` (cumulative default prob term structure), `creditSurvivalChart` (survival area chart), and `markovHeatmap` (S&P 1-year transition matrix heatmap via secondary /api/markov_chain call)
- All three charts use `{ responsive: true }` config for display flexibility
- Zero breaking changes to existing table/card UI — charts append below existing metric cards

## Task Commits

1. **Task 1: Upgrade Markov, Credit, and Rates JS functions to render Plotly charts** - `3fcd60f` (feat)

## Files Created/Modified

- `static/js/stochasticModels.js` — Added yieldCurveChart to runCIRModel; added defaultProbChart + creditSurvivalChart + markovHeatmap to runCreditRisk

## Decisions Made

- Markov heatmap fetched via secondary call to `/api/markov_chain` with `mode: nstep, n: 1` inside `runCreditRisk` — reuses existing API, no separate Markov sub-tab needed
- Survival curve data taken from `ttd.survival_curve` (Monte Carlo time-to-default paths), sliced to 21 points
- Default prob chart renders `term[].cumulative_default_prob * 100` on Y-axis for percent display
- Yield curve chart uses `pt.spot_rate * 100` — matches actual API response field (not a raw `yields` array)

## Deviations from Plan

None — plan executed exactly as written. All three chart types (heatmap, line, area) implemented per spec. Feller badge already present from prior CIR implementation; confirmed and retained.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 5 Phase 3 plans complete — Phase 4 (deployment) can begin
- Every stochastic sub-tab (Regime, Heston Pricing, Heston Calibration, BCC Calibration, Credit/Markov, CIR) renders at least one Plotly chart
- Pending: human-verify checkpoint to confirm all 7 sub-tabs render correctly in browser

---
*Phase: 03-frontend-wiring*
*Completed: 2026-03-07*
