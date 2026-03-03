---
phase: 01-math-correctness
plan: 02
subsystem: derivatives, analytics
tags: [heston, hmm, calibration, relative-mse, regime-detection, options-pricing]

# Dependency graph
requires:
  - phase: 01-math-correctness
    provides: plan 01 (bond/coupon math)
provides:
  - HestonCalibrator using relative percentage MSE with market_price >= 0.50 filter
  - RegimeDetector._assign_labels() module-level function with dual-criterion label logic
  - label_confidence field in RegimeDetector output (HIGH or AMBIGUOUS)
  - filtered_probs_full series exposed for MATH-05 validation
affects:
  - 01-math-correctness (subsequent plans using calibration or regime output)
  - Phase 2 (UI wiring depends on correct HMM and Heston outputs)
  - Phase 3 (calibration endpoint depends on corrected mse_fn)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Relative percentage MSE for options calibration: ((model - mp) / mp)^2"
    - "Dual-criterion HMM label assignment: sigma (primary) + mu (secondary) + 20% separation check"
    - "AMBIGUOUS confidence forces NEUTRAL signal — uncertainty is explicit, not hidden"
    - "TDD RED-GREEN cycle: failing tests committed before implementation"

key-files:
  created:
    - tests/test_math02_heston_relative_mse.py
    - tests/test_math04_regime_dual_criterion.py
  modified:
    - src/derivatives/model_calibration.py
    - src/analytics/regime_detection.py

key-decisions:
  - "Relative MSE ((model-mp)/mp)^2 normalises each contract by its own price so OTM options shape the smile equally with ITM options"
  - "MIN_MARKET_PRICE = 0.50 filter applied before mse_fn to avoid numerical issues with near-zero options (relative error explodes as mp -> 0)"
  - "sigma is primary label criterion; mu provides secondary confirmation — sigma separation < 20% is AMBIGUOUS even if both criteria agree directionally"
  - "AMBIGUOUS label_confidence forces signal = NEUTRAL regardless of stressed_prob thresholds — uncertainty is surfaced explicitly"
  - "filtered_probs_full added to return dict for downstream MATH-05 SPY-March-2020 validation test"

patterns-established:
  - "Options calibration: use relative MSE, filter prices < $0.50"
  - "HMM labelling: dual-criterion with sigma separation guard, AMBIGUOUS -> NEUTRAL"

requirements-completed: [MATH-02, MATH-04]

# Metrics
duration: 3min
completed: 2026-03-03
---

# Phase 1 Plan 02: Heston Relative MSE and HMM Dual-Criterion Label Fix Summary

**Replaced dollar-MSE with relative percentage MSE in HestonCalibrator and added dual-criterion sigma+mu label assignment with 20% separation guard to RegimeDetector, fixing flat IV smile (MATH-02) and stochastic calm/stressed label swapping (MATH-04)**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-03T14:48:36Z
- **Completed:** 2026-03-03T14:51:49Z
- **Tasks:** 2 (each with TDD RED + GREEN commits)
- **Files modified:** 4 (2 source, 2 test)

## Accomplishments
- HestonCalibrator.mse_fn() now uses relative (percentage) squared error so OTM options weight equally with ITM options, enabling a non-flat calibrated IV smile
- Contracts with market_price < $0.50 are filtered before calibration to avoid numerical blow-up in relative MSE for near-zero prices
- _assign_labels() added as a module-level testable function implementing dual-criterion calm/stressed assignment with 20% sigma separation guard
- RegimeDetector._build_result() now calls _assign_labels() and emits NEUTRAL when confidence is AMBIGUOUS, making uncertainty explicit
- filtered_probs_full and label_confidence added to _build_result() return dict for downstream validation

## Task Commits

Each task was committed atomically following TDD RED-GREEN pattern:

1. **Task 1 RED — Heston test (MATH-02)** - `7fbee63` (test)
2. **Task 1 GREEN — Heston fix (MATH-02)** - `d3bb70c` (feat)
3. **Task 2 RED — Regime test (MATH-04)** - `7f9257d` (test)
4. **Task 2 GREEN — Regime fix (MATH-04)** - `daf42b7` (feat)

_TDD: failing tests committed before implementation._

## Files Created/Modified
- `src/derivatives/model_calibration.py` - Added MIN_MARKET_PRICE filter and relative MSE in HestonCalibrator.calibrate()
- `src/analytics/regime_detection.py` - Added _assign_labels() module function; updated _build_result() for dual-criterion labelling, AMBIGUOUS->NEUTRAL signal, and new return keys
- `tests/test_math02_heston_relative_mse.py` - TDD tests for relative MSE and price filter
- `tests/test_math04_regime_dual_criterion.py` - TDD tests for dual-criterion label assignment

## Decisions Made
- Relative MSE normalises by contract price so a $1 error on a $2 OTM option counts the same as a $1 error on a $200 ITM option — this is standard practice in Heston calibration (Cont & Tankov 2004)
- sigma is primary criterion for calm/stressed labelling; mu provides corroborating evidence — sigma criterion is economically better grounded (volatility directly indexes risk aversion)
- 20% relative sigma separation threshold chosen to detect degenerate fits where both HMM states converge to similar volatility (common when data span is short or market is very stable)
- AMBIGUOUS confidence forces NEUTRAL to prevent spurious RISK_ON/RISK_OFF signals during uncertain fitting — downstream users can check label_confidence for transparency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- MATH-02 and MATH-04 are resolved; calibration and regime detection produce quant-correct outputs
- filtered_probs_full in the return dict enables the MATH-05 SPY-March-2020 validation test (next plan in sequence)
- BCCCalibrator, MertonCalibrator, and all other RegimeDetector methods are unchanged — no downstream breakage

## Self-Check: PASSED

- FOUND: src/derivatives/model_calibration.py
- FOUND: src/analytics/regime_detection.py
- FOUND: tests/test_math02_heston_relative_mse.py
- FOUND: tests/test_math04_regime_dual_criterion.py
- FOUND: .planning/phases/01-math-correctness/01-02-SUMMARY.md
- FOUND commit: 7fbee63 (test MATH-02 RED)
- FOUND commit: d3bb70c (feat MATH-02 GREEN)
- FOUND commit: 7f9257d (test MATH-04 RED)
- FOUND commit: daf42b7 (feat MATH-04 GREEN)

---
*Phase: 01-math-correctness*
*Completed: 2026-03-03*
