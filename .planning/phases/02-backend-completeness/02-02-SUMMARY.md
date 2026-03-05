---
phase: 02-backend-completeness
plan: 02
subsystem: api
tags: [vasicek, cir, interest-rate-models, flask, pytest, tdd]

# Dependency graph
requires:
  - phase: 01-math-correctness
    provides: CIR bond pricing functions, calibrate_to_treasuries, existing /api/interest_rate_model route
provides:
  - vasicek_bond_price() closed-form Vasicek bond pricing function
  - vasicek_yield_curve() Vasicek yield curve mirroring CIR signature
  - Extended /api/interest_rate_model supporting model=vasicek and feller_ratio in CIR response
affects:
  - 03-frontend-wiring

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lazy import inside route function body for analytics modules"
    - "model= query param dispatch pattern (cir/vasicek) within single Flask endpoint"
    - "feller_ratio = 2*kappa*theta / sigma^2 added as numeric field alongside boolean feller_condition_satisfied"

key-files:
  created:
    - tests/test_vasicek_model.py
  modified:
    - src/analytics/interest_rate_models.py
    - webapp.py

key-decisions:
  - "Vasicek feller_ratio returns None (not a number) because Vasicek allows negative rates — no Feller condition applies"
  - "Route dispatch uses data.get('model','cir').lower() — backward-compatible; missing field defaults to CIR"
  - "vasicek_yield_curve mirrors cir_yield_curve signature exactly to simplify Phase 3 frontend wiring"

patterns-established:
  - "TDD pattern: test scaffold committed first (RED), then implementation (GREEN), then route extension (GREEN)"

requirements-completed: [RATE-01, RATE-02, RATE-03, RATE-04, RATE-05]

# Metrics
duration: 5min
completed: 2026-03-05
---

# Phase 02 Plan 02: Vasicek Model and CIR Feller Ratio Summary

**Vasicek closed-form bond pricing added to interest_rate_models.py and /api/interest_rate_model extended with model=vasicek dispatch and numeric feller_ratio for CIR**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-05T00:00:00Z
- **Completed:** 2026-03-05T00:05:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added `vasicek_bond_price()` with correct closed-form Vasicek formula (T=0 boundary returns 1.0, T>0 returns value in (0,1))
- Added `vasicek_yield_curve()` mirroring `cir_yield_curve()` signature — list of dicts with maturity/bond_price/spot_rate
- Extended `/api/interest_rate_model` to dispatch on `model=vasicek` or default CIR, adding `feller_ratio` to CIR and calibrate_to_treasuries responses
- All 5 tests in `test_vasicek_model.py` pass; all 3 existing `test_interest_rate_models.py` tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add vasicek_bond_price and vasicek_yield_curve** - `a7e5140` (test: failing scaffold), `45fbe9e` (feat: implementation)
2. **Task 2: Extend /api/interest_rate_model route and write tests** - `e4fb517` (feat: webapp route extension)

_Note: TDD tasks have multiple commits (test RED -> feat GREEN). test_vasicek_model.py was written in an earlier session._

## Files Created/Modified
- `src/analytics/interest_rate_models.py` - Added vasicek_bond_price() and vasicek_yield_curve() after cir_yield_curve()
- `webapp.py` - Extended interest_rate_model_endpoint with model dispatch, feller_ratio in all branches
- `tests/test_vasicek_model.py` - 5 pytest tests covering unit functions and route integration

## Decisions Made
- Vasicek `feller_ratio` returns `None` because Vasicek allows negative rates by design — no Feller condition applies
- Route dispatch uses `data.get('model', 'cir').lower()` for backward compatibility — existing callers with no model field continue using CIR
- `feller_ratio = float((2 * kappa * theta) / sigma**2)` added to CIR branch and calibrate_to_treasuries branch as an additive (non-breaking) field

## Deviations from Plan

None - plan executed exactly as written. The Vasicek functions and test scaffolds were committed in a prior session; this execution committed the webapp route extension and ran final verification.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Vasicek and CIR backends are complete and tested
- `/api/interest_rate_model` supports model selection via POST body field
- Phase 3 (frontend wiring) can wire yield curve charts to model=vasicek or default CIR
- feller_ratio badge data available for Phase 3 RATE-04 UI requirement

---
*Phase: 02-backend-completeness*
*Completed: 2026-03-05*
