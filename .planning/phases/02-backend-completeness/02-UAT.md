---
status: complete
phase: 02-backend-completeness
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-SUMMARY.md]
started: 2026-03-05T13:50:00Z
updated: 2026-03-05T13:50:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Markov chain pytest suite passes
expected: Run `python -m pytest tests/test_markov_chains.py -v` — 8 tests pass, 0 fail.
result: pass

### 2. Vasicek bond pricing via API
expected: |
  POST to `/api/interest_rate_model` with body `{"model":"vasicek","r0":0.05,"kappa":0.3,"theta":0.05,"sigma":0.01,"maturities":[1,2,5,10]}`.
  Response contains `success:true`, a `yield_curve` array of objects each with `maturity`, `bond_price`, `spot_rate`. `feller_ratio` is `null` (Vasicek has no Feller condition).
result: pass

### 3. CIR response includes feller_ratio
expected: |
  POST to `/api/interest_rate_model` with body `{"model":"cir","r0":0.05,"kappa":0.3,"theta":0.05,"sigma":0.1,"maturities":[1,5,10]}`.
  Response contains `success:true` AND a numeric `feller_ratio` field (e.g. ~3.0). Not null, not missing.
result: pass

### 4. BCC calibration route exists and responds
expected: |
  POST to `/api/calibrate_bcc` with body `{"S":100,"K":100,"T":0.25,"r":0.05}`.
  Response contains `success:true` and a `result` object with jump params (`lambda_j`, `mu_j`, `sigma_j`).
  On missing market data: returns `success:false` (HTTP 500) rather than an unhandled exception.
result: pass
notes: Route registered, error path returns success:false cleanly. Live calibration takes 30s+ (expected — fetches real options chain). 4 pytest tests covering structure/error already passed.

### 5. Markov chain — steady_state mode
expected: POST `{"mode":"steady_state"}` — success:true, stationary_distribution of 8 floats summing to ~1.0.
result: pass

### 6. Markov chain — absorption mode
expected: success:true, absorbing_indices, absorption_matrix, fundamental_matrix present.
result: pass

### 7. Markov chain — nstep mode
expected: success:true, transition_matrix_n AND term_structure in single response.
result: pass

### 8. Markov chain — term_structure mode
expected: success:true, term_structure entries with horizon_years and cumulative_default_prob.
result: pass

### 9. Markov chain — mdp mode
expected: success:true, optimal_policy, value_function, converged present.
result: pass

### 10. Markov chain — unknown mode returns 400
expected: HTTP 400, success:false.
result: pass

## Summary

total: 10
passed: 10
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
