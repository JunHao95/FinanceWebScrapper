---
phase: 01-math-correctness
plan: 01
subsystem: analytics
tags: [numpy, scipy, credit-risk, cir, markov-chain, bond-pricing, feller-condition, tdd]

# Dependency graph
requires: []
provides:
  - "expected_bond_value() with continuous-discounting annuity PV formula (MATH-01)"
  - "CIRCalibrator with Feller hard constraint via alpha reparameterisation (MATH-03)"
  - "_feller_safe_params() helper function"
affects: [02-frontend-wiring, 03-webapp-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD: write failing tests first, commit RED, fix implementation, confirm GREEN"
    - "Continuous-discounting annuity formula: C*F*(1-exp(-r*T))/r for bond coupon PV"
    - "CIR Feller reparameterisation: optimise over alpha where kappa=sigma^2/(2*theta)+exp(alpha)"

key-files:
  created:
    - tests/test_math01_coupon_discounting.py
    - tests/test_math03_cir_feller_constraint.py
  modified:
    - src/analytics/credit_transitions.py
    - src/analytics/interest_rate_models.py

key-decisions:
  - "Principal discounting is required alongside coupon discounting: state_bond_values uses face_value*exp(-rT) + coupons_pv to produce par bond result"
  - "CIR Feller guaranteed via kappa=sigma^2/(2*theta)+exp(alpha) reparameterisation over (alpha, theta, sigma) - soft penalty removed"
  - "BRUTE_RANGES updated to alpha range [-2, 2] from kappa range [0.01, 5.0] to match new parameterisation"

patterns-established:
  - "Par bond identity: face_value*exp(-rT) + coupon_rate*face_value*(1-exp(-rT))/coupon_rate = face_value (exact cancellation when coupon rate = discount rate)"
  - "Feller structural guarantee: exp(alpha) > 0 for all real alpha, so kappa > sigma^2/(2*theta) always holds"

requirements-completed: [MATH-01, MATH-03]

# Metrics
duration: 6min
completed: 2026-03-03
---

# Phase 1 Plan 01: Fix Coupon Discounting and CIR Feller Constraint Summary

**Continuous-discounting bond PV formula and CIR Feller hard constraint via alpha reparameterisation, fixing two recruiter-visible numerical errors**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-03T14:48:32Z
- **Completed:** 2026-03-03T14:54:37Z
- **Tasks:** 2
- **Files modified:** 4 (2 source, 2 test)

## Accomplishments

- Fixed MATH-01: replaced undiscounted coupon sum with continuous-discounting annuity formula; par bond (AAA, 1yr, zero-default) now returns exactly 1000.00 instead of 1050.00
- Fixed MATH-03: replaced soft Feller penalty (10.0 additive) with structural reparameterisation - kappa is recovered from alpha via kappa=sigma^2/(2*theta)+exp(alpha), guaranteeing 2*kappa*theta > sigma^2 for all real alpha
- 10/10 TDD tests pass (4 for MATH-01, 6 for MATH-03) with no regressions

## Task Commits

Each task was committed atomically using TDD (RED then GREEN):

1. **Task 1 RED: Failing tests for MATH-01 coupon discounting** - `8d3d419` (test)
2. **Task 1 GREEN: Fix coupon discounting in credit_transitions.py** - `c62d732` (feat)
3. **Task 2 RED: Failing tests for MATH-03 CIR Feller reparameterisation** - `ec38e98` (test)
4. **Task 2 GREEN: Fix CIR Feller constraint via reparameterisation** - `0f83724` (feat)

_Note: TDD tasks have RED (test) and GREEN (implementation) commits per task._

## Files Created/Modified

- `src/analytics/credit_transitions.py` - Added continuous-discounting coupon PV formula and principal discounting; degenerate fallback for r=0/T=0; `__main__` validation block
- `src/analytics/interest_rate_models.py` - Added `_feller_safe_params()` helper; rewrote `CIRCalibrator.calibrate()` to optimise over (alpha, theta, sigma); updated BRUTE_RANGES; removed soft penalty and BOUNDS_LOW/BOUNDS_HIGH
- `tests/test_math01_coupon_discounting.py` - 4 TDD tests for coupon discounting fix
- `tests/test_math03_cir_feller_constraint.py` - 6 TDD tests for CIR Feller constraint

## Decisions Made

- **Principal discounting required:** The plan specified only changing `coupons_pv` but mathematical analysis showed the par bond test (result ~1000) requires discounting the principal too: `state_bond_values` now uses `principal_pv = face_value * exp(-r*T)` in place of `face_value`. This is Rule 1 (auto-fix bug) - the plan's description of "surgical fix" was incomplete.
- **State_bond_values structure preserved:** Only `face_value` replaced with `principal_pv`; all rating multipliers (1.00, 0.99, 0.98...) and the D-state recovery formula unchanged.
- **feller_condition_satisfied hardcoded to True:** By construction the reparameterisation guarantees it; return value changed from `bool(feller)` to literal `True` with explanatory comment.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Principal discounting required alongside coupon discounting for par bond correctness**
- **Found during:** Task 1 (Fix credit_transitions.py coupon discounting)
- **Issue:** Plan specified changing only `coupons_pv` line, but `state_bond_values['AAA'] = face_value + coupons_pv` with the continuous annuity formula still returned 1048.77 (not 1000.00). The plan's formula is correct for coupons; principal must also be discounted for the total to equal par.
- **Fix:** Added `principal_pv = face_value * np.exp(-discount_rate * horizon)` and replaced `face_value` with `principal_pv` in the `state_bond_values` dict. Mathematical identity: `principal_pv + coupons_pv = face_value` when coupon_rate = discount_rate (par bond property).
- **Files modified:** src/analytics/credit_transitions.py
- **Verification:** `expected_bond_value('AAA', 1, coupon_rate=0.05, face_value=1000, P=identity)` returns 1000.0000
- **Committed in:** c62d732 (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in plan's surgical scope specification)
**Impact on plan:** Fix is mathematically necessary for correctness. No scope creep; all return dict shapes and function signatures unchanged.

## Issues Encountered

None beyond the deviation documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Both analytics backends now produce mathematically correct output
- Par bond identity verified: 1000.0000 (exact)
- CIR Feller condition structurally guaranteed: cannot silently produce invalid yield curves
- Ready for Phase 1 Plan 02 (derivatives/options) and subsequent frontend wiring in Phase 2

---
*Phase: 01-math-correctness*
*Completed: 2026-03-03*

## Self-Check: PASSED

- FOUND: tests/test_math01_coupon_discounting.py
- FOUND: tests/test_math03_cir_feller_constraint.py
- FOUND: 01-01-SUMMARY.md
- FOUND: 8d3d419 (Task 1 TDD RED commit)
- FOUND: c62d732 (Task 1 TDD GREEN commit)
- FOUND: ec38e98 (Task 2 TDD RED commit)
- FOUND: 0f83724 (Task 2 TDD GREEN commit)
