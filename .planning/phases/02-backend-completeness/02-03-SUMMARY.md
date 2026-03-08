---
phase: 02-backend-completeness
plan: 03
subsystem: derivatives/calibration
tags: [flask-route, bcc-calibration, tdd, jump-diffusion]
dependency_graph:
  requires: [src.derivatives.model_calibration.BCCCalibrator]
  provides: [POST /api/calibrate_bcc]
  affects: [webapp.py, Phase 3 BCC UI wiring]
tech_stack:
  added: []
  patterns: [lazy-import inside route function, jump-param field name normalization]
key_files:
  created:
    - tests/test_bcc_route.py
  modified:
    - webapp.py
key_decisions:
  - "Normalize BCCCalibrator jump field names in route: lam->lambda_j, delta_j->sigma_j (BCC uses different convention than Merton)"
  - "Return {'success': true, 'result': result} not {'success': true, 'calibration': result} (newer route convention)"
  - "Propagate calibrator 'error' key as HTTP 500 with success:false (graceful error path, no unhandled exception)"
metrics:
  duration: "~2 min"
  completed: "2026-03-05"
  tasks_completed: 2
  files_created: 1
  files_modified: 1
---

# Phase 2 Plan 3: BCC Calibration Flask Route Summary

**One-liner:** Flask route wrapping BCCCalibrator with jump-param field name normalization (lam->lambda_j, delta_j->sigma_j) and graceful market-error propagation.

## What Was Built

Added `POST /api/calibrate_bcc` to `webapp.py` immediately after the Merton calibration route (line 1297). The route wraps the existing `BCCCalibrator.calibrate()` via lazy import, normalizes BCC's internal jump parameter naming to the API response convention, and propagates "no market data" errors gracefully as `success:false` with HTTP 500.

## Tasks Executed

### Task 1: Write failing tests (TDD RED)
- **Files:** `tests/test_bcc_route.py` (created)
- **Commit:** `670c2ef`
- **Outcome:** 4 tests written, all fail with 404 (route not registered) — confirmed RED state

### Task 2: Add /api/calibrate_bcc route to webapp.py (TDD GREEN)
- **Files:** `webapp.py` (modified)
- **Commit:** `03918f0`
- **Outcome:** All 4 tests pass; route registered; no regression in other routes

## Verification Results

```
tests/test_bcc_route.py::test_bcc_route_exists PASSED
tests/test_bcc_route.py::test_bcc_route_returns_success_structure PASSED
tests/test_bcc_route.py::test_bcc_route_jump_params_keys PASSED
tests/test_bcc_route.py::test_bcc_route_error_propagation PASSED
4 passed in 0.62s
```

Route registration: PASS (`/api/calibrate_bcc` confirmed in url_map)

Full regression: 44 passed (2 pre-existing failures in test_vasicek_model.py unrelated to this plan — Feller ratio key mismatch from plan 02-02 scope)

## Decisions Made

1. **Jump param normalization in route:** BCCCalibrator internally uses `lam` (not `lambda_j`) and `delta_j` (not `sigma_j`). The route normalizes to `lambda_j`/`mu_j`/`sigma_j` for the API response. Fallback keys handle edge cases where calibrator may already use final names.

2. **Response key is `result` not `calibration`:** Older routes (`calibrate_merton`) use `calibration` key; newer convention (from CONTEXT.md) uses `result`. BCC route follows newer convention.

3. **Error propagation via HTTP 500:** When `BCCCalibrator.calibrate()` returns `{'error': '...'}`, route returns `success:false` with status 500 — same behavior as unhandled exception path, ensuring client can always parse `success` field.

## Deviations from Plan

None — plan executed exactly as written.

## Key Links Implemented

- `calibrate_bcc_endpoint()` -> `BCCCalibrator.calibrate()` via lazy import `from src.derivatives.model_calibration import BCCCalibrator`
- `BCCCalibrator.calibrate()` result `jump` sub-dict -> normalized `jump_params` response field

## Self-Check: PASSED
- `tests/test_bcc_route.py` exists: FOUND
- `webapp.py` contains `calibrate_bcc_endpoint`: FOUND
- Commit `670c2ef` (test RED): FOUND
- Commit `03918f0` (feat GREEN): FOUND
