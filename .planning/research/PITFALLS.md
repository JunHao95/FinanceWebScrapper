# Domain Pitfalls

**Domain:** MFE showcase web app — stochastic financial models + ML in finance
**Researched:** 2026-03-03
**Confidence:** HIGH (based on direct code review of all WIP modules + domain expertise)

---

## Critical Pitfalls

Mistakes that cause rewrites, recruiter embarrassment, or model invalidity.

---

### Pitfall 1: Transition Matrix Rows That Don't Sum to One After Custom Input

**What goes wrong:** `credit_transitions.py` normalises `SP_TRANSITION_MATRIX` on load, but the `custom_matrix` path in `credit_risk_analysis()` passes an external matrix straight through without re-normalisation. A recruiter entering a custom transition matrix with rounding error (e.g., rows summing to 0.999) will get probabilities that silently drift — default probabilities become slightly wrong and the survival curve dips below or above 1. This is immediately visible if anyone checks the numbers against a textbook.

**Why it happens:** Normalisation is applied once at module load for the hardcoded matrix, but not as a defensive step inside functions that accept external input.

**Consequences:** The n-year matrix power `P^n` computes transition probabilities that don't form a proper stochastic matrix. Survival curves become non-monotone. A quant recruiter spotting a survival probability that increases over time will not ask a follow-up question — they will close the tab.

**Warning signs:**
- Survival curve values > 1.0 or non-monotone
- Default probability at year 30 less than year 10 for the same rating
- Any row of an n-year transition matrix summing to something other than 1.0

**Prevention:**
- Add a `_validate_transition_matrix(P)` helper that asserts rows sum to 1 (within 1e-6) and all entries are in [0,1]. Call it at the top of every function accepting a matrix parameter.
- Normalise the custom matrix before use, and surface a warning if normalisation correction exceeded 1%.

**Phase:** Stochastic Models validation pass (before frontend wiring is considered complete).

---

### Pitfall 2: Heston "Little Heston Trap" — Branch Cut Discontinuity in the Characteristic Function

**What goes wrong:** The Heston CF implementation in `fourier_pricer.py` uses the Albrecher et al. (2007) numerically stable reparameterisation, which is correct. However, the `_compute_p1_p2` quadrature integrates from `1e-5` to `500.0`. For long maturities (T > 2 years) or deep OTM options, the integrand oscillates rapidly and the upper bound of 500 may be insufficient — the quadrature silently under-integrates, producing a price that is too low. This is undetectable without a benchmark comparison.

**Why it happens:** The integration limit is fixed at 500. The Carr-Madan and Gil-Pelaez formulations require the integrand to have decayed to near-zero at the truncation point. For extreme parameters or long maturities, convergence is slower.

**Consequences:** Heston call prices that are below Black-Scholes intrinsic value for long-dated options, or that violate put-call parity by a visible margin. Any recruiter running `C - P = S - K*exp(-rT)` mentally will notice.

**Warning signs:**
- `P1 < P2` when the stock is far above the strike (a theoretical violation)
- Call price below intrinsic value `max(S - K*exp(-rT), 0)` for short maturities
- Large discrepancy between Heston price and BS price when vol-of-vol is small (they should converge as `sigma_v → 0`)

**Prevention:**
- Add an integration limit adaptive strategy: for T > 1 year, increase to 1000; for T > 5, increase to 2000.
- Add a post-price sanity check: assert `call >= max(S - K*exp(-rT), 0)` (intrinsic value floor) and assert put-call parity holds to within 0.01% of spot price.
- Benchmark against Black-Scholes at `sigma_v = 0.001` (near-zero vol-of-vol); Heston should converge to BS.

**Phase:** Fourier pricing validation (required before the UI demo is shown to anyone).

---

### Pitfall 3: MSE Calibration Without Relative Weighting — Deep ITM Options Dominate

**What goes wrong:** Both `HestonCalibrator` and `MertonCalibrator` minimise raw MSE in dollar price terms: `(model_price - market_price)^2`. Deep in-the-money options have large absolute prices (e.g., $50 for AAPL). OTM options are priced at $0.30. The calibration routine will effectively ignore the OTM options entirely, fitting the deep ITM options instead. But OTM options carry the most information about the volatility smile — exactly what Heston was designed to capture.

**Why it happens:** Absolute dollar MSE is the natural first implementation choice. The flaw is not obvious until you plot model vs. market IV across strikes.

**Consequences:** Calibrated Heston parameters produce an IV smile that looks flat (near-BS behaviour) despite having stochastic vol parameters. A recruiter who knows Heston will ask "why doesn't your surface show a skew?" and the implicit vol surface visualisation will look wrong.

**Warning signs:**
- Calibrated `theta` (long-run variance) is close to the ATM implied variance but the smile is flat across strikes
- Moneyness-sorted residuals show systematic over-pricing of OTM options
- `rho` calibrates to a value near zero despite equities having well-known negative skew

**Prevention:**
- Use relative MSE: `((model_price - market_price) / market_price)^2`, or weight by vega: errors on high-vega contracts matter more.
- Alternatively, calibrate to implied volatility differences rather than price differences.
- At minimum, document the limitation in the UI: "Calibration uses price-MSE; OTM options are weighted by vega in production implementations."

**Phase:** Model calibration implementation (before exposing calibration UI).

---

### Pitfall 4: Bond Value Formula Uses Undiscounted Coupon Sum

**What goes wrong:** In `credit_transitions.py`, the `expected_bond_value()` function computes coupon present value as `coupon_rate * face_value * horizon` — a plain sum with no discounting. This is textbook-wrong: coupons at year 10 are worth less than coupons at year 1. For a 10-year horizon at 5% coupon, this overstates coupon PV by ~25% compared to the correctly discounted sum.

**Why it happens:** The docstring even says "(simplified (no discounting))." It was intentionally simplified, but it produces wrong numbers on the UI.

**Consequences:** Expected bond values will be systematically too high for longer horizons. Anyone with a fixed income background — which includes virtually every credit quant recruiter — will immediately see that the expected value at year 10 exceeds what the bond should be worth even in the zero-default scenario.

**Warning signs:**
- Expected bond value at long horizons substantially exceeds `face_value + discounted coupon stream`
- For the D (default) state the function correctly uses `recovery * face`, but all other states return inflated values
- Values increase with horizon in a way that doesn't account for time value

**Prevention:**
- Replace the coupon sum with a proper annuity formula: `coupon * face * (1 - exp(-r*T)) / r` for continuous discounting, or the standard bond PV formula for discrete.
- Use a flat discount rate tied to the credit spread of each destination rating.
- If keeping the simplification for scope reasons, display a prominent note in the UI: "Simplified model: coupons are not discounted. For demonstration only."

**Phase:** Credit transitions backend validation (before connecting to frontend).

---

### Pitfall 5: HMM Label Switching — Calm and Stressed States May Swap Between Runs

**What goes wrong:** `RegimeDetector._unpack_params()` determines which state is "calm" by comparing `sigma` values after optimisation (`calm_idx = np.argmin(self.sigma)`). This works if optimisation is stable, but with 5 random restarts, the optimiser may converge to a solution where state indices have swapped but the log-likelihood is equivalent. The `current_regime` label in results could say "calm" when the market is in the high-volatility state, or vice versa, depending on which restart happened to produce the best `res.success`.

**Why it happens:** Gaussian HMMs have a label-switching problem — the likelihood is invariant to permutation of state labels. The post-fit relabelling by sigma magnitude (`argmin`) is the right fix, but only works reliably if the fitted sigmas are clearly ordered. When `sigma[0] ≈ sigma[1]` (ambiguous regime), the label assignment is arbitrary.

**Consequences:** The UI shows "RISK_ON" during the 2020 COVID crash or "RISK_OFF" during a bull run, which is exactly the kind of catastrophic embarrassment that kills a demo.

**Warning signs:**
- Annualised `sigma` for "stressed" state is only slightly larger than "calm"
- Historical stress fraction is outside the range 15-35% (for typical equity series, stressed periods should represent roughly 20-30% of time)
- Regime sequence shows very frequent alternation (multiple regime switches per week)

**Prevention:**
- After fitting, enforce the convention `mu[calm] > mu[stressed]` as a secondary sort criterion in addition to `sigma`. Both conditions should hold simultaneously for a valid calm/stressed decomposition.
- Add a confidence check: if `abs(sigma[calm] - sigma[stressed]) / sigma[stressed] < 0.2`, mark the result as "ambiguous regime" rather than making a firm RISK_ON/RISK_OFF call.
- Validate on known periods: SPY 2020-03 should be stressed, 2021-07 should be calm.

**Phase:** Regime detection validation (before UI display of signals).

---

### Pitfall 6: CIR Feller Condition Violation Produces Negative Rates in Simulation (Not Caught in Closed-Form Path)

**What goes wrong:** The closed-form CIR bond price function in `interest_rate_models.py` does not break when the Feller condition `2κθ > σ²` is violated — it returns a mathematically valid (but economically wrong) price because the formula is still defined. The CIR calibrator applies a Feller penalty of `10.0` in the objective, but after Nelder-Mead and parameter clipping, the returned parameters may still violate Feller. The UI reports `feller_condition_satisfied: False` but does not block the yield curve from being shown, meaning a user can generate and present a "CIR yield curve" from a parameterisation that, in the simulation domain, allows negative interest rates — which the CIR model was explicitly designed to prevent.

**Why it happens:** The closed-form solution doesn't enforce Feller (it's a constraint on simulation behaviour, not the closed-form formula). The penalty in calibration is soft, not a hard constraint.

**Consequences:** A recruiter who knows CIR theory will immediately ask "does this satisfy the Feller condition?" and the answer displayed in the UI will be "No." This invalidates the model's key advantage over Vasicek. It signals the student doesn't understand *why* CIR matters.

**Warning signs:**
- `feller_condition_satisfied: False` in calibration output
- `kappa` is very small relative to `sigma^2 / (2 * theta)`
- Calibrated short-end of the yield curve exhibits unusual curvature

**Prevention:**
- During calibration, use hard parameter bounds that enforce Feller: `kappa >= sigma^2 / (2 * theta) + epsilon` at each evaluation step, or reparametrise as `kappa = sigma^2 / (2*theta) + exp(alpha)`.
- In the UI, if Feller is violated, display a warning banner: "These parameters violate the Feller condition. In Monte Carlo simulation, negative rates would occur. Results shown are from the closed-form formula only."
- Show the Feller ratio `2κθ / σ²` as a named metric so the user can see how close to the boundary the calibration landed.

**Phase:** CIR/interest rate model validation.

---

### Pitfall 7: Calibration Latency Makes the Demo Appear Broken

**What goes wrong:** Heston calibration fetches a live options chain (yfinance API call), then runs a brute-force grid search over a 5-dimensional parameter space (`slice(0.1, 10.0, 2.5)` × `slice(0.01, 0.50, 0.12)` × ...) before Nelder-Mead. Each grid point evaluates Fourier integrals for up to 40 contracts. This can take 60-120 seconds on commodity hardware. The current JS frontend shows a loading spinner but gives no time estimate. A recruiter clicking "Calibrate" and waiting 90 seconds with no feedback will assume the app has crashed.

**Why it happens:** The two-stage brute+Nelder-Mead approach is computationally expensive by design (it's thorough). The UX doesn't account for this latency.

**Consequences:** Demo abandonment at the most interesting model. If the recruiter stops before seeing calibration results, the most technically impressive feature is never seen.

**Warning signs:**
- No progress indicator beyond generic spinner
- Browser request timeout if latency exceeds the default fetch timeout (typically 300s in some browsers)
- User clicks "Calibrate" again thinking the first click didn't register, triggering a second expensive computation

**Prevention:**
- Add a server-sent event (SSE) or polling endpoint that streams progress: "Stage 1 grid search: 40%... Stage 2 Nelder-Mead: running..."
- Alternatively, pre-compute calibration for 2-3 demo tickers on page load (cached results), with live calibration available as an "advanced" option.
- Display the expected computation time upfront: "Heston calibration typically takes 30-90 seconds."
- Add a 90-second client-side timeout with a graceful message, not a silent spinner.

**Phase:** Stochastic models UI integration.

---

## Moderate Pitfalls

---

### Pitfall 8: Using Market Bid-Ask Midpoint as "Market Price" for Calibration

**What goes wrong:** `VolatilitySurfaceBuilder` and the calibrators use `market_price` from the options chain, which is likely the last trade price or a bid-ask midpoint. For illiquid strikes, the bid-ask spread can be $1-3 wide on a $0.50 option. Calibrating to stale or wide-spread prices introduces substantial noise.

**Prevention:**
- Filter by minimum open interest (currently `min_volume=0` — set to at least 100) and maximum bid-ask spread as a fraction of mid (< 20%).
- Use bid-ask midpoint explicitly: `(bid + ask) / 2` rather than last trade, and flag if `ask - bid > 0.5 * mid`.
- In the UI, show how many contracts were filtered out and why.

**Phase:** Model calibration data cleaning.

---

### Pitfall 9: HMM Fitted to Price Returns but Trading Signal Shown Without Lag Correction

**What goes wrong:** The `RegimeDetector` uses `filtered_probs[-1]` (the last filtered probability at time T) to generate a RISK_ON/RISK_OFF signal. Filtered probabilities at time T use data up to and including T — there is no look-ahead bias. However, the `smoothed_probs` (Kim smoother) use the full dataset and *do* look ahead. If smoothed probabilities are ever used to generate signals (or are displayed alongside filtered ones without clear labelling), a recruiter with HMM experience will correctly call this out as in-sample look-ahead.

**Prevention:**
- Never use `smoothed_probs` for signal generation. Use them only for historical visualisation, labelled explicitly "In-sample smoothed (uses future data)."
- In the UI, label `filtered_probs[-1]` as "Real-time estimate" and `smoothed_probs` as "Full-sample smoother (not tradeable)."

**Phase:** Regime detection UI wiring.

---

### Pitfall 10: MDP/Markov Decision Process Without a Well-Defined Reward Function or Validated Policy

**What goes wrong:** The project lists "Markov Decision Process models" as a requirement, but the current code contains only `credit_transitions.py` (Markov chains, not MDPs). An MDP requires a reward function and a policy. Showing an MDP that uses an arbitrary or unexplained reward function, or one where the optimal policy is not validated against a known benchmark, signals a shallow understanding.

**Prevention:**
- If implementing MDP: define the state space (e.g., credit ratings), action space (hold/sell/hedge), and reward function (risk-adjusted return) explicitly, citing the formulation source.
- Validate the policy against a simple baseline (e.g., always-hold) and show that the MDP policy dominates.
- If MDP is out of scope for this milestone, remove it from the UI and defer clearly.

**Phase:** MDP section design (before implementation).

---

### Pitfall 11: Sigma Annualisation Inconsistency Between Models

**What goes wrong:** `RegimeDetector` outputs `sigma_annualized = sigma_daily * sqrt(252)`. `HestonCalibrator` and `fourier_pricer.py` work with variance (`v0`, `theta`) as daily or annual depending on how input data is formatted. If the UI displays both "Heston theta = 0.04 (4% variance)" and "HMM calm sigma = 0.18 annualised (18% vol)", a user might compare them and get confused — or worse, a recruiter might notice that the units are inconsistent between the two modules when the same underlying asset is used.

**Prevention:**
- Standardise all volatility outputs to annualised standard deviation throughout the UI.
- For Heston: display `sqrt(theta) * 100` as "Long-run vol (%)" rather than raw variance.
- For HMM: confirm `sigma_daily * sqrt(252)` is correct (it is, for log-returns).
- Add a units legend to every volatility figure.

**Phase:** UI integration and display formatting.

---

### Pitfall 12: yfinance API Failures Cause Silent Wrong Results (Not Errors)

**What goes wrong:** Both `RegimeDetector.fetch_returns()` and `FinancialAnalytics.get_historical_returns()` use yfinance. yfinance has a known behaviour where it returns partial or empty data without raising exceptions for certain tickers or date ranges, especially for non-US tickers or tickers with recent corporate actions. The code handles `data.empty` but not cases where data is present but truncated (e.g., only 100 days returned when 1260 were requested). The HMM will fit on 100 observations and silently return parameters that are much less stable.

**Prevention:**
- After fetching, assert `len(log_ret) >= 0.7 * requested_days` and surface a warning if not met.
- Display the actual data range used (start date, end date, number of observations) in the UI output.
- For the demo, use tickers known to have long, clean histories (SPY, ^SPX, AAPL, MSFT) as defaults.

**Phase:** All API-dependent modules.

---

### Pitfall 13: ML in Finance Section — Data Leakage from Feature Engineering

**What goes wrong:** When the ML module is added, the most common mistake in finance ML is computing features (e.g., rolling average, RSI, volatility) that use forward data when the rolling window straddles the train/test split. For example, if features are computed on the full dataset before splitting, a 20-day rolling mean at day 200 uses days 181-200, but if the split is at day 210, the test set features at day 201 will have been computed using data from days 182-201 — some of which was in the train set. This is standard data leakage.

**Prevention:**
- Always compute features within a TimeSeriesSplit cross-validation framework, or compute them strictly on training data and apply (not refit) the transformation to test data.
- Use `sklearn.model_selection.TimeSeriesSplit` rather than `train_test_split` (which shuffles).
- Show train vs. validation performance explicitly; if in-sample Sharpe >> out-of-sample Sharpe, flag it.

**Phase:** ML in Finance module design (before any model training).

---

### Pitfall 14: Calibration MSE Reported in Dollar Squared — Uninterpretable to Viewers

**What goes wrong:** The calibration results return `mse` and `rmse` in raw dollar values (price MSE). An `rmse` of `$3.50` means the model is off by $3.50 per contract on average, but this number is meaningless without context (is $3.50 bad for a $100 option? Good for a $1 option?). A recruiter seeing `rmse: 3.47` will not know if this is a good or bad calibration.

**Prevention:**
- Add `relative_rmse_pct = rmse / mean(market_prices) * 100` to the result dict.
- Display calibration quality as "Average relative error: X.X%" in the UI.
- Provide a qualitative label: < 2% = "Good", 2-5% = "Acceptable", > 5% = "Poor fit."

**Phase:** Calibration result UI display.

---

## Minor Pitfalls

---

### Pitfall 15: Fixed Random Seed in Monte Carlo Hides Variance

**What goes wrong:** `monte_carlo_time_to_default` uses `rng = np.random.default_rng(42)` — a fixed seed. Every run gives identical results. This is correct for reproducibility, but a recruiter who clicks "Run" multiple times and gets identical results might ask whether this is truly Monte Carlo. More seriously, the fixed seed could happen to produce an unusual sample, and there is no way to estimate the Monte Carlo standard error of the default probability estimate.

**Prevention:**
- Add a `seed` parameter (default 42 for reproducibility) and an option to use random seeds.
- Display the Monte Carlo standard error alongside the estimate: `se = sqrt(p * (1-p) / n_simulations)`.
- Show a "95% confidence interval" for the default probability.

**Phase:** Credit transitions UI.

---

### Pitfall 16: BCC Model Has Unused `sigma_gbm` Parameter

**What goes wrong:** `bcc_price()` has a parameter `sigma_gbm: float` with the comment "kept for API compatibility; unused in BCC." If a recruiter reads the function signature, they will see an undocumented dead parameter. This suggests copy-paste from a previous version without cleanup.

**Prevention:**
- Either remove the parameter (if no external callers) or rename to `_sigma_gbm_unused` with a deprecation note.
- Add a docstring note explaining why it exists.

**Phase:** Code cleanup before any showcase.

---

### Pitfall 17: No Input Validation on Stochastic Model API Endpoints

**What goes wrong:** The webapp accepts user-facing JSON for parameters like `kappa`, `theta`, `sigma_v`, `rho`. If a user (or curious recruiter) sends `rho = 1.5` or `sigma_v = -0.1`, the backend will either throw an unhandled exception or clip silently and return a result without informing the user that their input was invalid.

**Prevention:**
- Add explicit input validation in Flask routes with clear error messages returned in JSON: `{"error": "rho must be in (-1, 1), got 1.5"}`.
- Validate ranges match known financial constraints: `kappa > 0`, `theta > 0`, `sigma_v > 0`, `-1 < rho < 1`, `0 < v0 < 1` (variance, not vol).

**Phase:** All new API routes.

---

### Pitfall 18: The "S&P Transition Matrix" is Presented as Current but Has No Source Date

**What goes wrong:** `credit_transitions.py` uses `SP_TRANSITION_MATRIX` sourced from "S&P Global Ratings (illustrative; use latest published for production), 1981–2023 approximate." This disclaimer is in a code comment, not visible in the UI. A recruiter from a credit desk will know that S&P publishes updated transition matrices annually and that the 2023 matrix differs materially from the 1981-2023 average during stress periods.

**Prevention:**
- Display the source and vintage of the transition matrix prominently in the UI: "Using S&P 1981-2023 average annual transition matrix. Source: S&P Global Ratings Transition Study."
- Add a hyperlink to the S&P methodology document.
- Note that custom matrices can be entered to override defaults.

**Phase:** Credit transitions UI display.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| Credit transitions validation | Undiscounted coupon formula (Pitfall 4) | Fix before UI wiring; not a display issue, a math error |
| Credit transitions validation | Custom matrix row normalisation (Pitfall 1) | Add validator function before any demo |
| Fourier/Heston pricing | Integration limit insufficient for long T (Pitfall 2) | Benchmark against BS at near-zero vol-of-vol first |
| Fourier/Heston pricing | Put-call parity check absent | Add as automated test before shipping |
| Model calibration | Dollar-MSE dominance by ITM options (Pitfall 3) | Switch to relative MSE or IV-space calibration |
| Model calibration | Calibration latency UX (Pitfall 7) | Add progress streaming or caching for demo tickers |
| Model calibration | Uninterpretable MSE reported to UI (Pitfall 14) | Add relative RMSE % and qualitative label |
| Regime detection | Label switching produces wrong signal (Pitfall 5) | Validate on 2020-03 (SPY must be stressed) |
| Regime detection | Smoothed probs used for signal (Pitfall 9) | Only use filtered for signals; label smoothed clearly |
| CIR interest rate | Feller violation silently accepted (Pitfall 6) | Hard-enforce in calibration; warn prominently in UI |
| All stochastic models | yfinance partial data (Pitfall 12) | Assert minimum observation count; show date range |
| All models | Sigma/variance unit inconsistency (Pitfall 11) | Standardise on annualised vol % throughout UI |
| ML in Finance | Data leakage in feature engineering (Pitfall 13) | Use TimeSeriesSplit before any model training |
| ML in Finance | Overfitting without out-of-sample validation | Show OOS Sharpe explicitly; compare to buy-and-hold |
| All API endpoints | No parameter bounds validation (Pitfall 17) | Add validation layer in all new Flask routes |

---

## Recruiter-Specific Red Flags

The following specific observations will immediately signal "this student doesn't understand what they built" to a quantitative recruiter:

1. **Survival probability that increases over time.** This is impossible in a proper Markov chain model with an absorbing default state.

2. **Heston call price below intrinsic value.** Violates the no-arbitrage lower bound. Visible in any numerical sanity check.

3. **"CIR model does not satisfy Feller condition."** This is CIR's entire selling point over Vasicek. A violated Feller condition means the model you labelled "CIR" behaves like Vasicek (can go negative). This specific question is a classic screen.

4. **Regime detector says "RISK_ON" during COVID March 2020.** Any recruiter will test the obvious stress period. If the signal is wrong, the model is wrong.

5. **Calibration runs for 3 minutes and the app appears frozen.** Recruiters have 5-10 minutes for a demo. Losing 3 of them to a frozen spinner is fatal.

6. **Implied volatility smile is flat after Heston calibration.** The entire point of Heston is to capture the smile. If calibration produces a flat IV surface, the student has implemented the formula but doesn't understand what it's for.

7. **Merton jump compensation mu_bar = exp(mu_j + 0.5*delta_j^2) - 1 shown as a "jump size" in the UI without explanation.** This is the risk-neutral compensator, not the average physical jump. Mislabelling it in the UI suggests the student memorised the formula without understanding the measure change.

## Sources

- Direct code review of all WIP modules (`credit_transitions.py`, `interest_rate_models.py`, `regime_detection.py`, `fourier_pricer.py`, `model_calibration.py`)
- Albrecher, H., Mayer, P., Schachermayer, W., & Teichmann, J. (2007). "The Little Heston Trap." — referenced in `fourier_pricer.py` docstring
- Heston, S.L. (1993). "A Closed-Form Solution for Options with Stochastic Volatility." — referenced in `fourier_pricer.py`
- Hamilton, J.D. (1989). "A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle." — theoretical basis for `regime_detection.py`
- Cox, J.C., Ingersoll, J.E., & Ross, S.A. (1985). "A Theory of the Term Structure of Interest Rates." — basis for `interest_rate_models.py`
- Domain expertise in quantitative finance model validation and MFE recruiting standards
- Confidence: HIGH — all pitfalls derived from direct inspection of implemented code, not speculative
