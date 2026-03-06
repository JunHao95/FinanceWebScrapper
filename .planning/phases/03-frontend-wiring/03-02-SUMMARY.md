---
phase: 03-frontend-wiring
plan: 02
subsystem: ui
tags: [heston, options-pricing, implied-volatility, plotly, flask, scipy]

# Dependency graph
requires:
  - phase: 01-math-correctness
    provides: fourier_pricer.heston_price and options_pricer.black_scholes validated
  - phase: 02-backend-completeness
    provides: /api/heston_price route returning heston/black_scholes_comparison fields
provides:
  - /api/heston_iv_surface route — Heston IV grid (K_steps x T_steps) via brentq back-solving
  - stochContent_heston_price sub-tab with 9 Heston parameter inputs and Price Option button
  - runHestonPricing JS function: renders Heston vs BS price cards and 3D Plotly IV surface
affects: [03-frontend-wiring-03, 03-frontend-wiring-04, 03-frontend-wiring-05]

# Tech tracking
tech-stack:
  added: [scipy.optimize.brentq (used inside new route)]
  patterns: [IV back-solving via brentq on BS price function, 3D Plotly surface chart with Viridis colorscale]

key-files:
  created: []
  modified:
    - webapp.py
    - templates/index.html
    - static/js/stochasticModels.js

key-decisions:
  - "JS runHestonPricing sends spot/strike/maturity/risk_free_rate to /api/heston_price (not S/K/T/r) to match existing route field names"
  - "/api/heston_iv_surface reads S/r/v0/kappa/theta/sigma_v/rho/K_min/K_max/K_steps/T_min/T_max/T_steps from request JSON with defaults"
  - "IV capped at [0.001, 2.0]; brentq failures default to 0.001 to keep grid well-defined"
  - "iv_grid shape is T_steps x K_steps (maturities outer, strikes inner) matching Plotly surface z convention"

patterns-established:
  - "Pattern: 3D surface chart — Plotly.newPlot with type:surface, x=strikes, y=maturities, z=iv_grid (2D list)"
  - "Pattern: IV surface route — brentq back-solve loops over (T, K) grid, floors/caps to avoid NaN propagation"

requirements-completed: [HESTON-01, HESTON-02, HESTON-03, HESTON-04, HESTON-05]

# Metrics
duration: 8min
completed: 2026-03-06
---

# Phase 3 Plan 2: Heston Pricing Sub-Tab Summary

**Heston vs Black-Scholes price cards and 3D Plotly IV smile surface via new /api/heston_iv_surface brentq back-solving route**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-06T00:20:00Z
- **Completed:** 2026-03-06T00:28:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- New `/api/heston_iv_surface` Flask route computes an 8x10 IV grid (T_steps x K_steps) by calling fourier_pricer.heston_price per cell and back-solving IV via scipy brentq
- `stochContent_heston_price` sub-tab with 9 Heston parameter inputs (S, K, T, r, v0, kappa, theta, sigma_v, rho) and option type selector
- `runHestonPricing` JS function renders two color-coded price cards (green for Heston, blue for BS) then a 3D Plotly surface showing the non-flat IV smile
- Non-flat smile confirmed: with rho=-0.7, IVs decrease monotonically from low to high strikes (typical leverage effect)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add /api/heston_iv_surface route** - `4aade9f` (feat)
2. **Task 2: Add Heston Pricing sub-tab and runHestonPricing** - `b86f697` (feat)

**Plan metadata:** (docs commit — see final commit)

## Files Created/Modified
- `webapp.py` - Added /api/heston_iv_surface POST route (70 lines)
- `templates/index.html` - Added stochTab_heston_price button and stochContent_heston_price div
- `static/js/stochasticModels.js` - Added runHestonPricing function (100 lines)

## Decisions Made
- JS sends `spot/strike/maturity/risk_free_rate` field names to match the existing `/api/heston_price` route signature (not `S/K/T/r` as the plan spec showed) — existing route reads those exact keys and would return "Missing field" errors otherwise
- iv_grid is organized as maturities-outer / strikes-inner (shape T_steps x K_steps) to match Plotly surface convention where z[i][j] = iv at (y[i], x[j])

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed field name mismatch between JS and /api/heston_price route**
- **Found during:** Task 2 (runHestonPricing implementation)
- **Issue:** Plan spec showed JS sending `{S, K, T, r, ...}` but existing /api/heston_price route reads `data['spot']`, `data['strike']`, `data['maturity']`, `data['risk_free_rate']` — would return 400 "Missing field: spot"
- **Fix:** Updated JS to map params to route's expected field names before sending POST
- **Files modified:** static/js/stochasticModels.js
- **Verification:** Fields matched against existing route code at webapp.py:1120-1124
- **Committed in:** b86f697 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - field name bug)
**Impact on plan:** Fix essential for correctness — without it every price fetch would return 400. No scope creep.

## Issues Encountered
None - implementation was straightforward once field name mismatch was identified.

## User Setup Required
None - no external service configuration required.

## Self-Check: PASSED

All created/modified files verified present. Both task commits confirmed in git log.

## Next Phase Readiness
- HESTON-01 through HESTON-05 all satisfied
- Heston Pricing sub-tab functional; recruiter can enter parameters, click Price, and see both price cards and 3D IV smile surface
- Ready for plan 03-03 (next stochastic models tab)

---
*Phase: 03-frontend-wiring*
*Completed: 2026-03-06*
