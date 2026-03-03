# Phase 1: Math Correctness - Research

**Researched:** 2026-03-03
**Domain:** Quantitative finance model validation — CIR interest rate models, Heston/Fourier option pricing, Heston calibration, HMM regime detection, Markov chain credit transitions
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MATH-01 | Credit transitions bond valuation discounts coupons by time (non-discounted coupons bug fixed) | `expected_bond_value()` in `credit_transitions.py` confirmed to use undiscounted `coupon_rate * face_value * horizon`; fix with annuity PV formula documented below |
| MATH-02 | Heston calibration uses relative/percentage MSE weighting so OTM options contribute to the smile (dollar-MSE bug fixed) | `HestonCalibrator.mse_fn()` confirmed to use raw dollar-squared MSE; OTM dominance pattern and relative MSE fix documented below |
| MATH-03 | CIR calibration enforces Feller condition (2κθ ≥ σ²) as a hard constraint, not a soft penalty | `CIRCalibrator.mse_fn()` confirmed to use soft `feller_penalty = 10.0`; hard-enforcement reparameterisation documented below |
| MATH-04 | HMM regime labels are stable and correctly identify high-volatility state as RISK_OFF (label-switching robustness) | `RegimeDetector._build_result()` uses `argmin(sigma)` for calm-state assignment; label-switching vulnerability when `sigma[0] ≈ sigma[1]` confirmed; secondary sort criterion and SPY March 2020 validation documented |
| MATH-05 | All stochastic model outputs validated against textbook benchmarks or closed-form solutions before UI wiring | Five specific validation benchmarks identified (par bond test, BS convergence test, Feller rejection test, regime crisis test, put-call parity test) |
</phase_requirements>

---

## Summary

Phase 1 targets five confirmed mathematical bugs across four backend files in the current repository. All bugs were identified through direct code review — no speculation is involved. The bugs range from a straightforward arithmetic error (undiscounted coupon sum in `credit_transitions.py`) to a subtle optimisation formulation error (dollar-MSE calibration in `model_calibration.py`) to a parameter constraint design flaw (soft Feller penalty in `interest_rate_models.py`) to an HMM identifiability issue (label switching in `regime_detection.py`). Each bug produces an output that a quantitative recruiter will catch in under 30 seconds, and each has a known, standard fix from the quant finance literature.

The Fourier pricer (`fourier_pricer.py`) does not have an obvious arithmetic bug but requires a validation pass — specifically, verifying that the P1/P2 quadrature integration is sufficient for standard parameter ranges and that pricing satisfies put-call parity and the intrinsic value floor. This validation constitutes MATH-05. The pricer uses the Albrecher et al. (2007) numerically stable Heston CF parameterisation, which is the correct, modern approach; the concern is the fixed integration limit of 500 across all maturities.

The fixes are all self-contained within their respective files (`credit_transitions.py`, `model_calibration.py`, `interest_rate_models.py`, `regime_detection.py`) plus a benchmarking script or pytest module for MATH-05. No new libraries are needed. No Flask routes or frontend JS need to change in this phase.

**Primary recommendation:** Fix bugs in this order — MATH-01 (coupon discounting, simplest, no optimisation), MATH-03 (Feller hard constraint, well-defined reparameterisation), MATH-02 (relative MSE calibration, requires testing against SPY options), MATH-04 (HMM label robustness, requires SPY 2020 validation run), MATH-05 (benchmark validation of all backends). Each fix must pass its specific success criterion before moving to the next.

---

## Standard Stack

### Core (Already Installed — No New Dependencies)

| Library | Version (in repo) | Purpose | Why Standard |
|---------|------------------|---------|--------------|
| numpy | >=1.23.0 | Matrix operations, random sampling, linear algebra | All model backends already import numpy; matrix power, eigenvalues, array ops used throughout |
| scipy | >=1.9.0 | Optimisation (`brute`, `fmin`, `minimize`), integration (`quad`), stats (`norm`) | CIR and Heston calibrators already use `scipy.optimize`; HMM uses `scipy.optimize.minimize`; Fourier pricer uses `scipy.integrate.quad` |
| pandas | >=1.5.0 | Time series handling for regime detection | `RegimeDetector.fetch_returns()` uses pandas; yfinance returns DataFrames |
| yfinance | >=0.2.18 | Market data fetching for SPY validation | Used in `RegimeDetector.fetch_returns()` already; needed to fetch SPY history for MATH-04 validation |
| pytest | >=7.0.0 | Test framework for MATH-05 benchmark validation | Already in requirements.txt; use for all five benchmark tests |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scipy.stats.norm | (part of scipy) | Gaussian PDF evaluation in HMM Hamilton filter | Already used in `regime_detection.py` |
| scipy.optimize.minimize (L-BFGS-B) | (part of scipy) | HMM MLE fitting with bounds | Already used; no changes to optimiser itself needed |
| numpy.linalg.matrix_power | (part of numpy) | n-year transition matrix computation | Already used in `credit_transitions.py` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom Gaussian HMM with scipy | hmmlearn | hmmlearn replaces course-derived code with a black box; defeats the showcase purpose; out of scope per REQUIREMENTS.md |
| Custom CIR closed-form | QuantLib | QuantLib has C++ build dependencies that break on Render; out of scope per REQUIREMENTS.md |
| Hand-rolled Fourier integration | FFT-based Carr-Madan | Carr-Madan is faster but requires additional implementation; the `scipy.integrate.quad` approach is correct for N < 100 contracts |

**Installation:** No new packages required. Verify existing environment:

```bash
python3 -c "
import numpy as np
import scipy
from scipy.optimize import brute, fmin, minimize
from scipy.integrate import quad
from scipy.stats import norm
import yfinance as yf
import pytest
print(f'numpy {np.__version__}, scipy {scipy.__version__} — OK')
"
```

---

## Architecture Patterns

### Recommended Project Structure (No Changes from Existing)

```
src/
├── analytics/
│   ├── credit_transitions.py    # MATH-01: fix expected_bond_value() coupon discounting
│   ├── interest_rate_models.py  # MATH-03: fix CIR Feller hard constraint
│   └── regime_detection.py      # MATH-04: fix HMM label switching robustness
└── derivatives/
    ├── fourier_pricer.py        # MATH-05: validate P1/P2 quadrature; check intrinsic value floor
    └── model_calibration.py     # MATH-02: fix HestonCalibrator to use relative MSE

tests/                           # New — create for MATH-05 benchmarks
├── __init__.py
├── conftest.py                  # Shared fixtures (par bond params, SPY params)
├── test_credit_transitions.py   # MATH-01: par bond price = 100 within 0.01
├── test_interest_rate_models.py # MATH-03: Feller violation → rejection/flag
├── test_heston_calibration.py   # MATH-02: non-flat fitted IV smile
├── test_regime_detection.py     # MATH-04: SPY March 2020 → RISK_OFF
└── test_fourier_pricer.py       # MATH-05: put-call parity, intrinsic value floor
```

### Pattern 1: Arithmetic Fix in Pure Function (MATH-01)

**What:** Replace the undiscounted coupon sum `coupon_rate * face_value * horizon` with a proper present-value annuity formula in `expected_bond_value()`.

**When to use:** When fixing a deterministic computation error — no optimisation involved, output is exactly correct or wrong, easy to verify with a known benchmark.

**The bug (credit_transitions.py line 150):**
```python
# WRONG — no time-value of money
coupons_pv = coupon_rate * face_value * horizon  # simplified (no discounting)
```

**The fix — continuous discounting annuity:**
```python
# CORRECT — continuous discounting PV of coupon stream
# PV of annuity = C * face * (1 - exp(-r * T)) / r
# Use a flat discount rate appropriate to the starting rating
# For a par bond at issuance, use coupon_rate as the discount rate
discount_rate = coupon_rate  # par bond assumption: coupon = yield at issuance
if discount_rate > 0 and horizon > 0:
    coupons_pv = coupon_rate * face_value * (1 - np.exp(-discount_rate * horizon)) / discount_rate
else:
    coupons_pv = coupon_rate * face_value * horizon  # fallback for r=0
```

**Verification (MATH-01 success criterion):** For a par bond (face=1000, coupon_rate=r, discount_rate=r, starting state=AAA with near-zero default probability, horizon=1), `expected_bond_value()` must return a value within 0.01 of 1000.

**Conceptual basis:** A par bond is priced at face value at issuance by definition of "par" — it pays coupons equal to its yield. If default probability is negligible and the bond starts at face value, the expected value must equal face value. This is the textbook par bond sanity check.

### Pattern 2: Objective Function Reformulation (MATH-02)

**What:** Replace raw dollar MSE in `HestonCalibrator.mse_fn()` with relative percentage MSE so that OTM options (small absolute prices) contribute proportionally to the calibration objective.

**When to use:** When the error metric systematically biases the optimiser toward fitting certain data points at the expense of others.

**The bug (model_calibration.py line 113):**
```python
# WRONG — dollar MSE; $50 ITM option dominates over $0.30 OTM option
errors.append((res['price'] - mp) ** 2)
```

**The fix — relative MSE:**
```python
# CORRECT — percentage error; equal weight per unit of market price
if mp > 1e-4:  # avoid division by zero for near-zero options
    errors.append(((res['price'] - mp) / mp) ** 2)
else:
    errors.append((res['price'] - mp) ** 2)  # fallback for near-zero prices
```

**Alternative fix (vega-weighted):** Weight each contract's squared error by its Black-Scholes vega at the market IV. Higher-vega contracts (near-ATM, longer tenor) contribute more. This is the industry-standard approach. Implementation requires a Black-Scholes vega function. The relative MSE fix is simpler and achieves the same goal for this showcase.

**Verification (MATH-02 success criterion):** After calibration on SPY options, plot model IV vs. market IV across strikes. OTM options (K/S < 0.95) must show a visibly different implied vol than ATM (K/S ≈ 1.0). The calibrated `rho` should be negative (equities show negative skew empirically).

### Pattern 3: Hard Constraint via Reparameterisation (MATH-03)

**What:** Replace the soft Feller penalty (`feller_penalty = 10.0` added to objective) with a hard constraint that enforces `2*kappa*theta >= sigma^2 + epsilon` during CIR calibration.

**When to use:** When a mathematical property must be enforced absolutely (not as a soft preference) to preserve model validity.

**The bug (interest_rate_models.py line 185-186):**
```python
# WRONG — soft penalty; Nelder-Mead can still converge to Feller-violating params
if 2 * kappa * theta <= sigma**2:
    feller_penalty = 10.0
```

**Two valid fix approaches:**

**Option A — Reparameterisation (recommended):** Express `kappa` as a function of `theta` and `sigma` to guarantee Feller is always satisfied:
```python
# Let alpha = log(kappa - sigma^2 / (2*theta)) so kappa = sigma^2/(2*theta) + exp(alpha)
# Optimise over (alpha, theta, sigma) instead of (kappa, theta, sigma)
# kappa is always > sigma^2/(2*theta) by construction
def _unpack_feller_safe(params):
    alpha, theta, sigma = params
    if theta <= 0 or sigma <= 0:
        return None
    kappa = sigma**2 / (2 * theta) + np.exp(alpha)
    return kappa, theta, sigma
```

**Option B — Hard rejection:** Return a very large penalty (1e20, not 10.0) for any Feller violation, making violating parameter sets effectively invisible to the optimiser:
```python
if 2 * kappa * theta < sigma**2:
    return 1e20  # hard rejection, not soft penalty
```

Option A (reparameterisation) is preferred because it guarantees the returned parameters are Feller-compliant regardless of optimiser behaviour. Option B can still produce Feller-violating parameters after the final `np.clip()` call.

**Verification (MATH-03 success criterion):** Pass CIR parameters with `kappa=0.1, theta=0.05, sigma=0.3` (Feller LHS = 2*0.1*0.05 = 0.01, Feller RHS = 0.3^2 = 0.09; violates Feller) to the calibrator. The result must either raise a ValueError, return an error dict, or return `feller_condition_satisfied: False` alongside a flagged yield curve. The key requirement: the calibrator must NOT silently return a "good" yield curve from these parameters.

**Note on the success criterion wording:** "causes the calibrator to reject or flag them as invalid" — both rejection (error raised) and flagging (returns result with explicit `feller_condition_satisfied: False` and a warning) satisfy MATH-03. Rejection is cleaner for Phase 1; flagging is sufficient if the UI later shows a warning banner.

### Pattern 4: Post-Fit Label Enforcement (MATH-04)

**What:** Strengthen the HMM calm/stressed state assignment in `_build_result()` to use both sigma ordering and mu ordering as redundant criteria, plus add a confidence check that flags ambiguous results.

**When to use:** When a model has a known identifiability problem (label switching in HMMs) that causes semantically wrong outputs.

**The vulnerability (regime_detection.py lines 292-293):**
```python
# FRAGILE — only sigma ordering; when sigma[0] ≈ sigma[1], assignment is arbitrary
calm_idx = int(np.argmin(self.sigma))
stressed_idx = int(np.argmax(self.sigma))
```

**The fix — dual-criterion assignment with confidence check:**
```python
# Primary criterion: calm state has lower sigma
calm_by_sigma = int(np.argmin(self.sigma))
# Secondary criterion: calm state has higher mu (positive drift)
calm_by_mu = int(np.argmax(self.mu))

# If both agree, assignment is confident
if calm_by_sigma == calm_by_mu:
    calm_idx = calm_by_sigma
    label_confidence = 'HIGH'
else:
    # Criteria disagree — use sigma (more reliable) but flag as ambiguous
    calm_idx = calm_by_sigma
    label_confidence = 'AMBIGUOUS'

stressed_idx = 1 - calm_idx  # only 2 states

# Confidence check: states must be clearly separated
sigma_separation = abs(self.sigma[calm_idx] - self.sigma[stressed_idx]) / max(self.sigma)
if sigma_separation < 0.20:  # less than 20% relative separation
    label_confidence = 'AMBIGUOUS'
```

**The ambiguous case:** When `label_confidence == 'AMBIGUOUS'`, `signal` should be set to `'NEUTRAL'` rather than `RISK_ON` or `RISK_OFF`. Do not output a directional signal when the model cannot reliably distinguish regimes.

**Verification (MATH-04 success criterion):** Fetch SPY data including March 2020 (at minimum: 2019-01-01 to 2021-01-01). Run `RegimeDetector.fit()`. For every trading day in March 2020 (2020-03-01 to 2020-03-31), the assigned regime must be `stressed` (equivalently, `signal` for that period must be `RISK_OFF`). This is a known historical fact — SPY fell ~34% peak-to-trough in five weeks during this period. The VIX peaked above 80.

**Implementation note:** The full `filtered_probs` time series is not currently returned by `_build_result()` — it stores on `self.filtered_probs` but only returns the last 20 in `recent_filtered_probs`. For MATH-04 validation, the test needs access to the full time series. Either expose `self.filtered_probs` directly or add a `filtered_probs_full` key to the result dict for the validation run.

### Pattern 5: Benchmark Validation Script (MATH-05)

**What:** A pytest test suite (or standalone validation script) that runs all five model backends against closed-form or textbook benchmarks and asserts correctness before any Phase 2 work begins.

**When to use:** As a phase gate — must pass before declaring Phase 1 complete.

**The five benchmark checks:**

1. **Par bond test (MATH-01 verification):** `expected_bond_value(rating='AAA', horizon=1, coupon_rate=0.05, face_value=1000)` with a transition matrix that has zero default probability for AAA at 1 year → result within 0.01 of 1000.

2. **Heston → Black-Scholes convergence (Fourier pricer):** With `sigma_v → 0` (e.g., `sigma_v=0.001`), `theta = v0 = vol^2`, `kappa` large, the Heston price must converge to the Black-Scholes price within 0.01 for ATM options. This validates the P1/P2 quadrature engine.

3. **Put-call parity (Fourier pricer):** For any set of Heston parameters, `C - P = S - K * exp(-r * T)` must hold within `S * 1e-4` (i.e., 1 basis point of spot). Test across a grid of strikes and maturities.

4. **Feller rejection test (MATH-03 verification):** CIR calibrator with Feller-violating parameters must not return `feller_condition_satisfied: True`. See Pattern 3 above.

5. **Regime crisis test (MATH-04 verification):** SPY March 2020 must be classified as stressed. See Pattern 4 above.

**Intrinsic value floor check (Fourier pricer):** For any K, T, S with the standard Heston parameters, `call_price >= max(S - K * exp(-r * T), 0)` must hold. Add this assertion to the put-call parity test.

### Anti-Patterns to Avoid

- **Soft Feller penalty (current code):** A penalty of 10.0 is orders of magnitude smaller than the objective function's Heston calibration surface — Nelder-Mead will walk through Feller-violating regions without issue. Always use hard rejection (1e20) or reparameterisation.

- **Testing calibration with fixed seeds only:** The HMM label-switching test must not use a seed that happens to produce the correct assignment. Test with multiple seeds (seeds 0-9) and assert all produce RISK_OFF for March 2020.

- **Undiscounted coupon as a known simplification left in place:** The comment `# simplified (no discounting)` exists in the current code. Leaving simplifications in place and hoping recruiters don't notice is not acceptable. Fix the formula.

- **Dollar-MSE for calibration without documentation:** If relative MSE is not implemented, the current behaviour must at minimum be documented prominently in the UI as a limitation. But fixing it is strongly preferred.

- **Skipping the Heston → BS convergence test:** This is the most efficient way to catch integration errors in the Fourier pricer without market data. If the convergence test fails, the pricer has a fundamental bug. If it passes, the pricer is likely correct for standard parameter ranges.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Complex annuity formula | Custom numerical loop | Standard PV annuity formula: `C * FV * (1 - exp(-r*T)) / r` | One line; no numerical error; exact closed form |
| Feller-safe parameter space | Custom gradient projection | Reparameterisation: `kappa = sigma^2/(2*theta) + exp(alpha)` | Standard trick from term-structure calibration literature; no constraint handling needed |
| HMM label resolution | Heuristic confidence score | Dual-criterion: argmin(sigma) + argmax(mu), with separation check | Both criteria are theoretically motivated; separation check flags genuinely ambiguous fits |
| Benchmark comparison | UI-level display | pytest assertions with tolerance bounds | Tests run offline; catch bugs before any UI demo |
| Vega-weighted calibration | Custom vega calculation | Use relative MSE as simpler alternative | For showcase purposes, relative MSE achieves the same goal without needing a separate BS implementation |

**Key insight:** All five fixes in Phase 1 are one-to-ten line changes to existing functions. The risk is not in implementation difficulty but in verification — each fix requires a specific numerical check to confirm it resolved the correct problem and did not introduce new issues.

---

## Common Pitfalls

### Pitfall 1: Feller Soft Penalty Not Enough

**What goes wrong:** The current CIR calibrator uses `feller_penalty = 10.0`. After Nelder-Mead optimisation and the final `np.clip()` call, the returned parameters can still violate Feller even though the penalty was applied.

**Why it happens:** Nelder-Mead does not respect discontinuous penalties well. The penalty makes Feller-violating regions less attractive but not impossible to reach, especially after clipping clips parameters back to a point that happens to violate Feller.

**How to avoid:** Use reparameterisation (Option A in Pattern 3 above) or a hard rejection threshold (1e20). Test with known Feller-violating inputs.

**Warning signs:** `feller_condition_satisfied: False` in calibration output despite the penalty being present.

### Pitfall 2: HMM Label Switching on Ambiguous Fits

**What goes wrong:** When both HMM states have similar volatility (e.g., `sigma[0] = 0.008, sigma[1] = 0.009` daily), `argmin(sigma)` is essentially random. Different random restarts assign different states as "calm," and the best-likelihood restart may not be the one that matches the correct historical labelling.

**Why it happens:** Gaussian HMMs have a fundamental label-switching problem — the likelihood function is symmetric in state labels. The `argmin` post-processing is the standard fix but fails when states are not clearly separated.

**How to avoid:** Add the sigma separation check (< 20% relative separation → ambiguous). When ambiguous, set signal to `NEUTRAL`. Add the secondary mu criterion. Validate on SPY 2020-03.

**Warning signs:** `stress_fraction_historical` near 50% (markets are not stressed 50% of the time); very frequent regime alternation in the sequence; mu[stressed] > mu[calm].

### Pitfall 3: Par Bond Test Requires Near-Zero Default Probability

**What goes wrong:** The par bond test (`expected_bond_value` returns ~1000) only works for a starting rating with negligible default probability over the horizon. For AAA over 1 year, the S&P transition matrix gives a default probability of ~0.02% — negligible. For BB over 1 year, default probability is ~1.06% — nontrivial. Using BBB as the test rating or a long horizon (10 years) will cause the test to fail even with a correct formula, because default probability materially reduces the expected value.

**How to avoid:** For the MATH-01 test, use: starting rating = AAA, horizon = 1, coupon_rate = discount_rate (par condition), face_value = 1000. Assert result within 0.01 of 1000. This is the only combination that cleanly isolates the discounting formula from credit risk effects.

**Warning signs:** Test passes at horizon=1 but fails at horizon=5 even with correct formula (expected — default risk accumulates); test fails at horizon=1 even with zero-default test matrix (formula is wrong).

### Pitfall 4: Relative MSE Breaks on Near-Zero Option Prices

**What goes wrong:** Deep OTM options can have market prices near zero (e.g., $0.01). If the model prices them slightly differently (e.g., $0.05), the relative error is 400% — dominating the calibration objective. This is the opposite of the dollar-MSE problem but equally bad.

**How to avoid:** Add a minimum price floor in the relative MSE calculation: only apply relative MSE when `mp > threshold` (e.g., $0.50 or 0.5% of spot). Below the threshold, exclude the contract from calibration or use absolute MSE. Add a filter in `HestonCalibrator.calibrate()` to remove contracts where `market_price < 0.005 * S` (0.5% of spot).

**Warning signs:** Calibration converges but fitted IV for deep OTM options is wildly wrong; `rho` calibrates to ±0.999 (boundary hit due to extreme OTM relative errors).

### Pitfall 5: Integration Limit 500 Is Insufficient for Long Maturities

**What goes wrong:** The Fourier pricer uses `integration_limit=500` for all maturities. For T > 2 years with high `sigma_v`, the integrand has not decayed to near-zero at u=500, causing the quadrature to underestimate the integral and produce a call price below intrinsic value.

**How to avoid:** Test with T=5, K = S (ATM), standard Heston parameters (kappa=2, theta=0.04, sigma_v=0.3, rho=-0.7, v0=0.04). If `C < max(S - K*exp(-rT), 0)`, the integration limit is insufficient. Adaptive limit: use 1000 for T > 1, 2000 for T > 5. This is fast to check and implement.

**Warning signs:** Call prices slightly below intrinsic value for long-dated options; put-call parity violation exceeds the tolerance; Heston price substantially below BS price for near-zero vol-of-vol.

### Pitfall 6: Fetching SPY Data Depends on yfinance Returning Sufficient History

**What goes wrong:** The MATH-04 validation (SPY March 2020 → RISK_OFF) requires at least 400+ trading days of history for the HMM to have enough data to fit reliably. yfinance is an external dependency that occasionally returns truncated data or fails silently.

**How to avoid:** For the validation test, fetch at least 1000 trading days of SPY (4+ years). Assert `len(log_ret) >= 800` before running `fit()`. If the assertion fails, the test is inconclusive (not a model failure). Cache the SPY data in a fixture or use a fixed date range (2017-01-01 to 2021-01-01) to ensure March 2020 is always included.

**Warning signs:** `n_observations` in the fit result is less than 500; the test passes but the data fetched did not include March 2020.

---

## Code Examples

Verified patterns from the existing codebase and standard quant finance references.

### Bond PV Annuity Formula (MATH-01 Fix)

```python
# Source: Standard fixed-income mathematics (Fabozzi, "Fixed Income Mathematics")
# Continuous discounting PV of coupon stream for a par bond
# P = C * F * (1 - exp(-r*T)) / r  where C=coupon rate, F=face, r=discount rate, T=horizon

def _coupon_pv_continuous(coupon_rate: float, face_value: float,
                           discount_rate: float, horizon: int) -> float:
    """
    Present value of a continuous coupon stream.
    For a par bond: discount_rate == coupon_rate.
    """
    if discount_rate <= 0 or horizon <= 0:
        return coupon_rate * face_value * horizon  # degenerate fallback
    return coupon_rate * face_value * (1.0 - np.exp(-discount_rate * horizon)) / discount_rate
```

### Relative MSE Objective (MATH-02 Fix)

```python
# Source: Standard calibration practice in quantitative finance
# Relative percentage error: weights OTM and ITM options equally per unit of price

def _relative_mse(model_price: float, market_price: float,
                  min_price_threshold: float = 0.50) -> float:
    """
    Compute relative squared error, falling back to absolute for near-zero prices.
    """
    if market_price >= min_price_threshold:
        return ((model_price - market_price) / market_price) ** 2
    else:
        return (model_price - market_price) ** 2  # absolute for tiny OTM options
```

### Feller-Safe CIR Reparameterisation (MATH-03 Fix, Option A)

```python
# Source: Term-structure calibration literature (Brigo & Mercurio, "Interest Rate Models")
# By parameterising kappa = sigma^2/(2*theta) + exp(alpha), we guarantee 2*kappa*theta > sigma^2

def _feller_safe_params(alpha: float, theta: float, sigma: float):
    """
    Unpack reparameterised CIR params that guarantee Feller condition.
    Optimise over (alpha, theta, sigma); recover kappa from constraint.
    alpha is unconstrained (real line), theta > 0, sigma > 0.
    """
    if theta <= 0 or sigma <= 0:
        return None
    # kappa is guaranteed > sigma^2/(2*theta) for all real alpha
    kappa = (sigma**2) / (2.0 * theta) + np.exp(alpha)
    return kappa, theta, sigma
```

### HMM Dual-Criterion Label Assignment (MATH-04 Fix)

```python
# Source: Standard HMM post-processing for Gaussian mixture models
# Primary: sigma ordering (stressed state has higher variance)
# Secondary: mu ordering (stressed state has lower/negative return)

def _assign_labels(mu: np.ndarray, sigma: np.ndarray) -> tuple:
    """
    Assign calm/stressed labels using dual criteria.
    Returns: (calm_idx, stressed_idx, label_confidence)
    """
    calm_by_sigma = int(np.argmin(sigma))   # lower vol = calm
    calm_by_mu    = int(np.argmax(mu))      # higher return = calm

    if calm_by_sigma == calm_by_mu:
        calm_idx = calm_by_sigma
        confidence = 'HIGH'
    else:
        calm_idx = calm_by_sigma  # sigma is primary; mu breaks ties
        confidence = 'AMBIGUOUS'

    # Check sigma separation
    sep = abs(sigma[calm_idx] - sigma[1 - calm_idx]) / max(sigma)
    if sep < 0.20:
        confidence = 'AMBIGUOUS'

    return calm_idx, 1 - calm_idx, confidence
```

### Put-Call Parity Validation (MATH-05)

```python
# Source: Black (1975), put-call parity; standard no-arbitrage result
# C - P = S - K * exp(-r * T)  for European options on non-dividend-paying stock

def assert_put_call_parity(S, K, T, r, call_price, put_price, tol_fraction=1e-4):
    """
    Assert put-call parity holds to within tol_fraction of spot price.
    tol_fraction = 1e-4 means tolerance is 1 basis point of spot price.
    """
    lhs = call_price - put_price
    rhs = S - K * np.exp(-r * T)
    tolerance = S * tol_fraction
    assert abs(lhs - rhs) < tolerance, (
        f"Put-call parity violated: C-P={lhs:.6f}, S-K*exp(-rT)={rhs:.6f}, "
        f"diff={abs(lhs-rhs):.6f}, tol={tolerance:.6f}"
    )
```

### Heston → Black-Scholes Convergence Check (MATH-05)

```python
# Source: Heston (1993) — as sigma_v → 0, Heston model collapses to GBM/Black-Scholes
# Used to validate the Fourier integration engine without market data

from src.derivatives.fourier_pricer import heston_price
from src.derivatives.options_pricer import black_scholes  # existing BS pricer

def test_heston_converges_to_bs():
    S, K, T, r = 100.0, 100.0, 1.0, 0.05
    vol = 0.20  # 20% annual vol
    v0 = vol**2   # variance, not vol
    theta = v0    # long-run variance = initial variance
    sigma_v = 0.001  # near-zero vol-of-vol → Heston ≈ BS
    kappa = 10.0     # high mean reversion forces v ≈ theta quickly
    rho = 0.0        # no correlation needed

    heston_result = heston_price(S, K, T, r, v0, kappa, theta, sigma_v, rho, 'call')
    bs_price = black_scholes(S, K, T, r, vol, 'call')['price']  # existing function

    assert abs(heston_result['price'] - bs_price) < 0.01, (
        f"Heston→BS convergence failed: Heston={heston_result['price']:.4f}, "
        f"BS={bs_price:.4f}"
    )
```

---

## State of the Art

| Old Approach | Current Approach | Status in Codebase | Impact for Phase 1 |
|--------------|------------------|--------------------|--------------------|
| Undiscounted coupon sum | Annuity PV formula `C*F*(1-exp(-rT))/r` | Bug present — must fix | MATH-01 |
| Dollar MSE calibration | Relative (percentage) MSE or IV-space calibration | Bug present — must fix | MATH-02 |
| Soft Feller penalty (10.0) | Hard rejection (1e20) or reparameterisation | Bug present — must fix | MATH-03 |
| Single-criterion label assignment (argmin sigma) | Dual-criterion + separation check | Fragile — must strengthen | MATH-04 |
| Integration limit fixed at 500 | Adaptive limits (500 short T, 1000 T>1yr, 2000 T>5yr) | Untested — must validate | MATH-05 |
| Albrecher et al. (2007) stable Heston CF | Albrecher et al. (2007) | Already implemented correctly | No change needed |
| L-BFGS-B for HMM MLE | L-BFGS-B with multiple restarts | Already implemented correctly | No change needed |

**Deprecated/outdated patterns to avoid:**
- Original Heston (1993) CF parameterisation (has branch cut discontinuity at long maturities): The codebase already uses the Albrecher et al. (2007) numerically stable version — do not revert.
- Baum-Welch EM for HMM: The codebase uses direct MLE via scipy.optimize.minimize. This is less standard than EM but is correct and produces better numerical control — do not switch.

---

## Open Questions

1. **Integration limit sufficiency for standard SPY parameter ranges**
   - What we know: The Fourier pricer uses integration_limit=500; PITFALL 2 identifies this as insufficient for T > 2 years with high sigma_v.
   - What's unclear: Whether typical SPY Heston calibration parameters (sigma_v usually 0.2-0.5 for SPY) actually cause under-integration at T=0.5-1 year (the most common option maturities traded).
   - Recommendation: Run the put-call parity check across a grid of (K, T) with typical SPY parameters. If parity holds at T <= 1 year with limit=500, the fix (adaptive limits) is only needed for long-dated options and the existing code is acceptable for the showcase's primary use case.

2. **Relative MSE with very illiquid OTM options may still cause instability**
   - What we know: The existing code uses `min_volume=0` when fetching options — this includes highly illiquid options with wide bid-ask spreads. Relative MSE on a $0.05 option with a $0.40 bid-ask spread creates extreme noise.
   - What's unclear: Whether SPY options (highly liquid market) have sufficient liquidity across the full strike range to make relative MSE stable without additional filtering.
   - Recommendation: Add a minimum market price filter (e.g., `market_price >= 0.50`) in `HestonCalibrator.calibrate()` before computing relative MSE. This is standard practice in production calibration.

3. **MATH-04 validation — whether yfinance reliably returns SPY data back to 2017**
   - What we know: yfinance is known to return partial data for some tickers and date ranges without raising errors.
   - What's unclear: Whether SPY daily data from 2017-01-01 to 2021-01-01 reliably loads at the time tests are run (network dependency, API rate limits).
   - Recommendation: Cache a small SPY return series (5 years of daily log-returns) as a numpy array in `tests/fixtures/spy_2017_2021.npy` for deterministic testing. Load from file if available; fetch from yfinance as fallback.

---

## Sources

### Primary (HIGH confidence)

- Direct code review: `src/analytics/credit_transitions.py` — `expected_bond_value()` undiscounted coupon confirmed at line 150
- Direct code review: `src/derivatives/model_calibration.py` — dollar MSE in `HestonCalibrator.mse_fn()` confirmed at line 113
- Direct code review: `src/analytics/interest_rate_models.py` — soft Feller penalty of 10.0 confirmed at lines 185-186; `CIRCalibrator.calibrate()` full review
- Direct code review: `src/analytics/regime_detection.py` — `_unpack_params()` sigma-only label assignment confirmed; `_build_result()` uses `argmin(self.sigma)` at line 292
- Direct code review: `src/derivatives/fourier_pricer.py` — Albrecher et al. (2007) CF implementation confirmed; `_compute_p1_p2()` integration limit = 500 at line 201; Albrecher parameterisation verified correct
- `.planning/research/PITFALLS.md` — detailed pitfall analysis pre-existing from project research
- `.planning/research/STACK.md` — technology stack confirmed
- `.planning/REQUIREMENTS.md` — MATH-01 through MATH-05 requirements confirmed
- `requirements.txt` — numpy, scipy, pandas, pytest all confirmed present

### Secondary (MEDIUM confidence)

- Albrecher, H., Mayer, P., Schachermayer, W., & Teichmann, J. (2007). "The Little Heston Trap." — Basis for the Heston CF implementation already in use; adaptive integration limits guidance
- Fabozzi, F. (standard reference). "Fixed Income Mathematics" — Annuity PV formula `C*F*(1-exp(-rT))/r` is textbook; no date uncertainty
- Brigo, D. & Mercurio, F. "Interest Rate Models — Theory and Practice" — Feller reparameterisation as `kappa = sigma^2/(2*theta) + exp(alpha)` is standard
- Hamilton, J.D. (1989). "A New Approach to the Economic Analysis of Nonstationary Time Series" — HMM dual-criterion label assignment is conventional

### Tertiary (LOW confidence)

- yfinance reliability for historical SPY data back to 2017: observed behaviour, not officially documented. See Open Question 3 above.
- Relative MSE stability with SPY options chain: standard practice but not empirically verified in this codebase. See Open Question 2 above.

---

## Metadata

**Confidence breakdown:**
- Bugs identified (MATH-01, 02, 03, 04): HIGH — all confirmed by direct code reading, not inference
- Fixes proposed: HIGH — all are standard quant finance techniques with textbook basis
- Integration limit concern (MATH-05): MEDIUM — identified in prior research; requires empirical validation with actual parameter values
- yfinance reliability for test fixture: LOW — external dependency, recommend caching

**Research date:** 2026-03-03
**Valid until:** 2026-06-03 (60 days — scipy/numpy APIs are stable; only yfinance API behaviour subject to change)
