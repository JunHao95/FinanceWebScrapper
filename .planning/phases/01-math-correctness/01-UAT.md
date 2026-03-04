---
status: complete
phase: 01-math-correctness
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md]
started: 2026-03-04T00:00:00Z
updated: 2026-03-04T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Par Bond Returns 1000
expected: Running expected_bond_value('AAA', 1, coupon_rate=0.05, face_value=1000) with an identity transition matrix (no default) returns exactly 1000.00 (not 1050). The par bond identity holds: coupon PV + discounted principal = face value.
result: pass

### 2. CIR Feller Condition Always Satisfied
expected: CIRCalibrator.calibrate() returns a dict with feller_condition_satisfied=True regardless of the input data. The structural reparameterisation guarantees 2*kappa*theta > sigma^2 cannot be violated.
result: pass

### 3. Heston Calibration Uses Relative MSE
expected: Running HestonCalibrator.calibrate() on a small set of option prices does NOT produce a perfectly flat IV smile. The calibrated parameters fit the smile shape (OTM options weighted equally with ITM options). Contracts with market_price < 0.50 are excluded automatically.
result: pass

### 4. RegimeDetector Outputs label_confidence Field
expected: RegimeDetector.detect() (or equivalent) returns a dict that includes a label_confidence key with value either 'HIGH' or 'AMBIGUOUS'. When confidence is AMBIGUOUS, the signal is 'NEUTRAL'.
result: pass

### 5. Benchmark Test Suite Passes
expected: Running `pytest tests/ -m "not slow" -v` from the project root completes with 37 passed, 0 failures (1 deselected for the slow SPY network test). All 5 test modules run.
result: pass

### 6. black_scholes Module-Level Import
expected: `from src.derivatives.options_pricer import black_scholes` succeeds without ImportError. Calling `black_scholes(S=100, K=100, r=0.05, T=1.0, sigma=0.2, option_type='call')` returns a positive float (approximately 10.45).
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
