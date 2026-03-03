---
phase: 01-math-correctness
verified: 2026-03-03T15:05:42Z
status: passed
score: 10/10 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Run HestonCalibrator.calibrate('SPY') on live market data and inspect IV smile"
    expected: "OTM options (K/S < 0.95) produce measurably different implied volatility than ATM, showing a non-flat smile. rho calibrates to a negative value."
    why_human: "Requires live market data from yfinance/options APIs. Structural check confirmed relative MSE is in place; actual smile non-flatness depends on live data quality and market conditions."
  - test: "Run RegimeDetector on SPY 2017-2021 data and inspect March 2020 labels"
    expected: "At least 80% of March 2020 trading days labelled as stressed (RISK_OFF). label_confidence is HIGH for that fit."
    why_human: "test_spy_march_2020_is_stressed is marked @pytest.mark.slow and excluded from CI. Requires network. Structural dual-criterion logic confirmed in code."
---

# Phase 1: Math Correctness Verification Report

**Phase Goal:** All six stochastic model backends produce results that a quantitative recruiter cannot fault — no non-monotone survival curves, no flat IV smiles, no Heston prices below intrinsic value, no HMM mislabeling of known stress periods, no Feller violations silently accepted.

**Verified:** 2026-03-03T15:05:42Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Par bond (AAA, 1yr, coupon=5%, zero-default) returns within 0.01 of 1000 | VERIFIED | `expected_bond_value` returns 1000.000000 exactly; continuous annuity formula + principal discounting confirmed in source |
| 2 | Feller-violating CIR params cannot escape the calibrator — violation is structurally impossible | VERIFIED | Reparameterisation: `kappa = sigma^2/(2*theta) + exp(alpha)` guarantees `2*kappa*theta > sigma^2` for all real `alpha`. Three yield curve shapes all returned `feller_condition_satisfied: True` |
| 3 | CIR calibration with valid params produces correct yield curve and feller_condition_satisfied: True | VERIFIED | Flat, normal, and inverted curves all calibrate without error and return `feller_condition_satisfied: True` |
| 4 | HestonCalibrator uses relative MSE — OTM options shape the smile | VERIFIED | `((res['price'] - mp) / mp) ** 2` confirmed in source; `MIN_MARKET_PRICE = 0.50` filter confirmed before `mse_fn` |
| 5 | Contracts with market_price < $0.50 are excluded before calibration | VERIFIED | `raw = [d for d in raw if d['market_price'] >= MIN_MARKET_PRICE]` confirmed at lines 97-99 of `model_calibration.py` |
| 6 | HMM dual-criterion: both sigma and mu agree -> HIGH; disagree -> AMBIGUOUS | VERIFIED | `_assign_labels(mu=[0.001,-0.002], sigma=[0.008,0.020])` returns HIGH; `_assign_labels(mu=[-0.001,0.002], sigma=[0.008,0.020])` returns AMBIGUOUS |
| 7 | Low sigma separation (< 20%) forces AMBIGUOUS even when criteria agree directionally | VERIFIED | `_assign_labels(mu=[0.001,-0.002], sigma=[0.0095,0.010])` returns AMBIGUOUS (separation ~5%) |
| 8 | AMBIGUOUS label_confidence forces signal = NEUTRAL | VERIFIED | `if label_confidence == 'AMBIGUOUS': signal = 'NEUTRAL'` confirmed in `_build_result()` |
| 9 | Fourier pricer: put-call parity holds within S*1e-4 at ATM | VERIFIED | `C-P = 4.877058`, `S-Ke^-rT = 4.877058`, diff = 0.000000 (tol = 0.010000) |
| 10 | Fourier pricer: Heston converges to Black-Scholes when sigma_v -> 0 | VERIFIED | heston=10.4506, bs=10.4506, diff=0.0000 (within 0.01 tolerance) |

**Score:** 10/10 truths verified

Additional sanity checks:
- Survival curve for BBB is monotone non-decreasing (default prob increases with horizon): VERIFIED
- Intrinsic value floor: Heston call prices >= max(S - K*e^(-rT), 0) for all 7 tested strikes: VERIFIED
- 37 fast tests pass, 1 deselected (slow marker), 0 failures: VERIFIED

---

### Required Artifacts

#### Plan 01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analytics/credit_transitions.py` | `expected_bond_value()` with continuous-discounting annuity PV formula | VERIFIED | Contains `coupon_rate * face_value * (1.0 - np.exp(-discount_rate * horizon)) / discount_rate` and `principal_pv = face_value * np.exp(-discount_rate * horizon)` |
| `src/analytics/interest_rate_models.py` | `CIRCalibrator` with Feller hard constraint via reparameterisation | VERIFIED | Contains `_feller_safe_params()` helper and `mse_fn` operating over `(alpha, theta, sigma)` |

#### Plan 02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/derivatives/model_calibration.py` | `HestonCalibrator.mse_fn()` using relative percentage MSE with minimum price filter | VERIFIED | Contains `(res['price'] - mp) / mp` and `MIN_MARKET_PRICE = 0.50` filter |
| `src/analytics/regime_detection.py` | `_build_result()` with dual-criterion sigma+mu label assignment | VERIFIED | Contains module-level `_assign_labels()` function; `_build_result()` calls it; `label_confidence` and `filtered_probs_full` in return dict |

#### Plan 03 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/__init__.py` | Makes tests/ a Python package | VERIFIED | File exists (empty) |
| `tests/conftest.py` | Shared fixtures: zero_default_matrix, spy_returns, standard_heston_params, market_yields_normal | VERIFIED | All four fixtures present; `slow` marker configured |
| `tests/test_credit_transitions.py` | MATH-01 benchmark — par bond = 1000 within 0.01 | VERIFIED | 3 tests, all pass; uses `.get()` fallback for key name compatibility |
| `tests/test_interest_rate_models.py` | MATH-03 benchmark — Feller always satisfied after reparameterisation | VERIFIED | 3 tests, all pass |
| `tests/test_heston_calibration.py` | MATH-02 smoke test — relative MSE code path present | VERIFIED | 3 tests, all pass |
| `tests/test_regime_detection.py` | MATH-04 benchmark — _assign_labels dual-criterion; SPY March 2020 (slow) | VERIFIED | 3 fast tests pass; 1 slow test deselected by default |
| `tests/test_fourier_pricer.py` | MATH-05 Fourier engine benchmarks — BS convergence, put-call parity, intrinsic floor | VERIFIED | 4 tests pass |
| `tests/fixtures/.gitkeep` | Placeholder for cached SPY data | VERIFIED | File exists |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `CIRCalibrator.calibrate()` | `_feller_safe_params()` | reparameterised `(alpha, theta, sigma)` | WIRED | `alpha, theta, sigma = params` then `_feller_safe_params(alpha, theta, sigma)` confirmed in source |
| `expected_bond_value()` | `coupons_pv` computation | continuous annuity formula `1 - np.exp` | WIRED | `1.0 - np.exp(-discount_rate * horizon)` confirmed in source; `principal_pv` also wired |
| `HestonCalibrator.calibrate()` | `mse_fn` | relative MSE on filtered contracts `mp >= 0.50` | WIRED | `MIN_MARKET_PRICE = 0.50` filter applied before arrays built; `/ mp` confirmed in mse_fn |
| `RegimeDetector._build_result()` | `_assign_labels()` | dual-criterion calm/stressed assignment | WIRED | `_assign_labels(self.mu, self.sigma)` called at top of `_build_result()` |
| `tests/test_regime_detection.py` | `RegimeDetector.fit() + _build_result()` | `filtered_probs_full` time series | WIRED | `filtered_probs_full` imported and used in slow benchmark test |
| `tests/test_fourier_pricer.py` | `heston_price() + black_scholes()` | BS convergence with `sigma_v=0.001` | WIRED | Both functions imported; convergence test uses `sigma_v=0.001` |

All 6 key links: WIRED.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| MATH-01 | 01-01 | Credit transitions bond valuation discounts coupons by time | SATISFIED | Continuous annuity PV formula in source; par bond = 1000.000000 |
| MATH-02 | 01-02 | Heston calibration uses relative/percentage MSE weighting | SATISFIED | `((res['price'] - mp) / mp) ** 2` in source; `MIN_MARKET_PRICE = 0.50` filter confirmed |
| MATH-03 | 01-01 | CIR calibration enforces Feller condition as hard constraint | SATISFIED | Reparameterisation `kappa = sigma^2/(2*theta) + exp(alpha)` guarantees Feller structurally |
| MATH-04 | 01-02 | HMM regime labels stable and correctly identify high-vol state | SATISFIED | `_assign_labels()` dual-criterion with 20% sigma separation guard confirmed |
| MATH-05 | 01-03 | All stochastic model outputs validated against textbook benchmarks | SATISFIED | pytest tests/ -m "not slow": 37 passed, 0 failures; put-call parity, BS convergence, intrinsic floor all verified |

All 5 requirements for Phase 1 satisfied. No orphaned requirements (REQUIREMENTS.md traceability table marks all MATH-01 through MATH-05 as Complete / Phase 1).

---

### Anti-Patterns Found

No blocking anti-patterns found in modified source files:

- No TODO/FIXME/PLACEHOLDER comments in `credit_transitions.py`, `interest_rate_models.py`, `model_calibration.py`, `regime_detection.py`, or `fourier_pricer.py`
- No empty implementations (return null/return {}) in modified functions
- No console.log-only handlers
- No stub return values

**Warnings (non-blocking):**

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `src/analytics/interest_rate_models.py` lines 64-74 | `RuntimeWarning: overflow encountered in exp` / `divide by zero encountered in log` during CIR brute search over wide alpha range | Warning | Calibrator catches these via try/except, returns `1e10` penalty, and recovers via Nelder-Mead. Tests pass. Not a blocker — these warnings occur during brute grid search over parameter space that includes numerically extreme regions. |

---

### Human Verification Required

#### 1. Heston IV Smile Non-Flatness

**Test:** Run `HestonCalibrator().calibrate('SPY')` with live market data. Inspect the fitted IV smile by computing implied volatility at K/S = 0.85, 0.90, 0.95, 1.00, 1.05.

**Expected:** IV at K/S = 0.85 should be meaningfully higher than IV at K/S = 1.00 (negative skew). The calibrated `rho` parameter should be negative (typically -0.5 to -0.9 for equities).

**Why human:** Requires live yfinance options data which is unavailable at static verification time. The structural fix (relative MSE + price filter) is confirmed. Whether the actual fitted smile is non-flat depends on the data quality and market state at runtime.

#### 2. SPY March 2020 Regime Label

**Test:** Run `pytest tests/test_regime_detection.py -m slow` (requires network, ~60s). Alternatively, run `RegimeDetector().fetch_returns('SPY', days=1461)` followed by `fit(returns)` and check `filtered_probs_full` for March 2020 trading days.

**Expected:** At least 80% of March 2020 trading days (approximately 2020-03-01 to 2020-03-31) should have P(stressed) > 0.5. `label_confidence` should be `HIGH` for this fit.

**Why human:** Network dependency (yfinance). The dual-criterion label assignment logic is structurally confirmed in code; the actual March 2020 classification requires a live fit which can take 30-60 seconds and requires SPY historical data.

---

### Gaps Summary

No gaps found. All must-haves from all three plan frontmatter sections are satisfied:

- **Plan 01-01 truths:** Par bond = 1000.0 (exact), Feller structurally impossible to violate, valid calibration returns Feller=True
- **Plan 01-01 artifacts:** Both files present, substantive, and their content patterns match
- **Plan 01-01 key links:** Both calibrator and bond-value links WIRED
- **Plan 01-02 truths:** Relative MSE confirmed, $0.50 filter confirmed, dual-criterion logic confirmed, AMBIGUOUS->NEUTRAL confirmed
- **Plan 01-02 artifacts:** Both files present, substantive, content patterns match
- **Plan 01-02 key links:** All four links WIRED
- **Plan 01-03 truths:** 37 tests pass (0 failures), all benchmarks confirmed in automated execution
- **Plan 01-03 artifacts:** All 8 test infrastructure files present
- **Plan 01-03 key links:** Both test-to-implementation links WIRED

Deviations from plans that were auto-fixed by executor (do not affect goal achievement):

1. **Principal discounting added** (Plan 01-01): Plan specified changing only `coupons_pv` but executor correctly added `principal_pv = face_value * exp(-r*T)` to achieve the par bond identity. This is mathematically necessary and a correct fix.
2. **Return key is `expected_bond_value` not `expected_value`** (Plan 01-03): Tests adapted with `.get()` fallback. Tests pass.
3. **`black_scholes()` module-level wrapper added to `options_pricer.py`** (Plan 01-03): Test imports required standalone function; executor added wrapper delegating to `OptionsPricer().black_scholes()`.

---

_Verified: 2026-03-03T15:05:42Z_
_Verifier: Claude (gsd-verifier)_
