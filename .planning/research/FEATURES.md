# Feature Landscape

**Domain:** MFE Showcase Web App — Stochastic Models + ML-in-Finance sections
**Researched:** 2026-03-03
**Confidence:** HIGH (domain expert knowledge, cross-referenced against existing codebase)

---

## Context: What Recruiters and MFE Peers Actually Evaluate

Recruiters at quantitative shops (sell-side strats, buy-side quants, risk desks) look for:

1. **Correct model output** — parameters must match theory (Feller condition, absorbing default state, positive yields). An incorrect result is worse than no result.
2. **Model interpretability** — can a non-coder understand what the model is telling them? Labeled axes, parameter interpretation, economic intuition.
3. **Breadth of the model zoo** — covering Markov chains, stochastic rates, stochastic volatility, and regime detection in one app demonstrates curriculum depth.
4. **Comparison across models** — showing that Heston prices differ from Black-Scholes, or that BCC adds jump risk, demonstrates that the builder knows *why* each model exists.
5. **Live data tie-ins** — calibrating to real market data (even if infrequently) signals practical awareness, not just textbook execution.

MFE peers and faculty look for:
- Implementation fidelity (correct formula, numerically stable)
- Clean separation of analytical logic from UI
- Validation against known benchmarks

---

## Table Stakes

Features that must be present or the showcase feels incomplete. A recruiter clicking through the Stochastic Models tab will notice if these are missing.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Markov chain transition matrix display | Core MFE stochastic processes topic; shows you know matrix probability mechanics | Low | Display heatmap or table with row-stochastic validation |
| n-year matrix power (P^n) | Textbook exercise every MFE student does; instantly verifiable by recruiter | Low | Already implemented in credit_transitions.py |
| Credit rating term structure of default | Standard credit risk interview topic; S&P/Moody matrices are industry reference | Low-Med | Already implemented; needs chart (cumulative default prob vs. horizon) |
| Survival curve from Monte Carlo | Demonstrates MC fluency and links analytical vs. simulation results | Med | Already implemented in monte_carlo_time_to_default |
| CIR yield curve output | Interest rate models are a core MFE module; yield curve is the deliverable | Low-Med | Already implemented in cir_yield_curve |
| CIR parameter interpretation (Feller condition) | Feller 2κθ > σ² is a known gotcha; showing it signals model depth | Low | Already returned by backend; needs badge in UI |
| HMM regime detection result | Regime models are a modern staple; showing bull/bear/crisis state on a real ticker is immediately impressive | Med | Already implemented; frontend in stochasticModels.js |
| Heston pricing with parameter inputs | Most famous SV model; every MFE student is expected to know it | Med | Fourier pricer backend done; needs UI form |
| Heston vs. Black-Scholes price comparison | Shows the delta from SV — makes the model choice meaningful | Low (additive) | Backend already has BS in options_pricer.py |
| Model calibration result display (Heston to real options data) | Calibration is the bridge from theory to practice; RMSE, n_contracts, Feller | High | HestonCalibrator already implemented; UI wiring needed |
| Interactive parameter sliders / inputs for all models | Static output with no interactivity feels like a report, not a demo | Med | All models need at least numeric input fields |

---

## Differentiators

Features that elevate this showcase above a typical MFE student project. These are not expected but are highly valued by senior quants and technical hiring managers.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Side-by-side Heston / Merton / BCC price comparison for same contract | Directly shows what jumps add to stochastic vol — rare in student demos | Med | All three pricers exist; need UI that runs all three on one form submit |
| CIR calibration to live US Treasury yields with RMSE display | Connecting a theoretical model to observable market data is practitioner-level | Med | CIRCalibrator and US_TREASURY_YIELDS_2025 defaults already in backend |
| BCC pricing with CIR discount factor toggle | Shows cross-module integration (stochastic rates + stochastic vol + jumps); very sophisticated | Med-High | Backend already supports discount_factor param in bcc_price; needs UI checkbox |
| Visual credit migration heatmap (transition matrix as colored grid) | Heatmaps are the standard format in credit risk decks; immediately recognizable | Med | Use CSS grid or canvas; color-code by probability magnitude |
| Regime-conditioned annualized return and vol display | Shows economic interpretation of HMM states — not just "calm/stressed" labels | Low (additive) | mu_annualized and sigma_annualized already in backend response |
| Default probability term structure chart (line chart, not table) | Visualization lifts the presentation quality; tables read like homework, charts read like analysis | Med | Charting library (Chart.js) already present in project |
| Expected bond value vs. recovery rate sensitivity (sliders) | Connects credit transitions to fixed income valuation — MFE interview staple | Med | expected_bond_value function already implemented |
| Merton jump-diffusion pricing with jump parameter interpretation | Jump diffusion is taught in every MFE options theory course; showing λ, μ_j, δ_j interpretation is differentiating | Med | merton_price backend done; needs UI form |
| MDP (Markov Decision Process) toy demo — portfolio rebalancing | Shows optimization layer on top of Markov processes; very few student apps include this | High | Not yet implemented in backend; would be a new feature |
| Stationary distribution display and convergence visualization | Ergodic Markov chains converge to stationary dist; showing this demonstrates theoretical depth | Low-Med | Stationary dist already returned by regime detector via eigendecomposition |

---

## ML-in-Finance Section (Next Module)

These are features expected in an ML-in-finance showcase. Categorized separately because they belong to the next semester module.

### Table Stakes for ML Section

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Return prediction with linear regression (OLS) | Baseline ML model; foundation for everything else | Low | financial_analytics.py already has LinearRegression |
| PCA for dimensionality reduction on portfolio returns | Core unsupervised ML in finance; factor models are the application | Med | Already implemented in financial_analytics.py |
| LASSO / Ridge regression for factor selection | Regularized regression is the practical upgrade to OLS; MFE curricula always include this | Med | Not yet implemented |
| Classification of market states (e.g. SVM or logistic regression on features) | Supervised ML applied to market regimes; bridges ML module to stochastic models module | High | Could reuse HMM regime labels as targets |
| Backtesting framework for ML-driven signals | ML signal without backtest is theory; with backtest it becomes a strategy | High | New feature; complex to implement correctly |
| Feature importance / coefficient display | Model interpretability — shows you understand what drives the prediction | Low (additive) | Required alongside any ML model output |

### Differentiators for ML Section

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Rolling cross-validation (time-series aware, not random) | Critical for avoiding lookahead bias; most beginners miss this; immediately impresses quants | High | TimeSeriesSplit from scikit-learn; conceptually important |
| Volatility forecasting with GARCH vs. HMM comparison | Connects ML forecasting to stochastic models section | High | GARCH is implemented in statsmodels; HMM already built |
| Regime-conditioned portfolio weights (using HMM signal as input to optimizer) | Cross-module integration; practical application of regime detection | High | Links stochastic models section to ML section |
| Gradient boosting (XGBoost/LightGBM) for return prediction with SHAP values | Modern ML; SHAP is now expected in any serious ML-in-finance project | High | Adds significant complexity but strong recruiter signal |

---

## Anti-Features

Features to deliberately NOT build in this milestone. Including them would bloat scope without proportionate recruiter value.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Vasicek model alongside CIR | CIR is strictly better for this showcase (non-negative rates, Feller condition); adding Vasicek dilutes focus without adding insight | Mention CIR extends Vasicek in the parameter interpretation text |
| Ho-Lee or Hull-White multi-factor models | Multi-factor rate models exceed MFE module 4 scope; calibration complexity is high and UI becomes unwieldy | Note as "out of scope for this module" in UI tooltip |
| Moody's KMV structural credit model | Requires equity vol, debt structure, distance-to-default — separate calibration stack; Markov-based is sufficient for this module | Mention KMV as an alternative approach in explanatory text |
| Real-time streaming price updates | WebSocket complexity, rate limits, infrastructure cost — zero added value for a showcase that uses historical data | Static yfinance fetches are sufficient; add "last updated" timestamp |
| Portfolio optimization (mean-variance, black-litterman) | Already exists in the portfolio stress testing tab; duplicating it in stochastic models creates confusion | Cross-link from stochastic models output to portfolio tab |
| User-uploaded custom transition matrices (arbitrary n×n) | Validation complexity is high; arbitrary matrices can be non-stochastic; limited recruiter value | Provide a pre-set "custom matrix" field with a well-known example (Moody's vs S&P) |
| n-state HMM (n > 2) | Adding a 3-state HMM requires full UI re-design; 2-state (calm/stressed) is the standard and sufficient for the MFE curriculum | Document 2-state assumption in the UI |
| Deep learning (LSTM, Transformer) for price prediction | LSTM requires significant data preprocessing, training time, GPU consideration; out of scope for the ML-in-finance module as typically taught | Reserve for a potential future module; mention it as "planned" |
| Real options (binomial/trinomial) in stochastic models tab | Trinomial model already exists in derivatives tab; don't duplicate | Cross-link to derivatives tab |

---

## Feature Dependencies

```
CIR calibration to Treasuries
    → requires: CIR yield curve display (must exist first)

BCC pricing with CIR discount factor
    → requires: CIR bond price (already implemented)
    → requires: Heston pricing (must work first)
    → requires: Merton pricing (must work first)

Model comparison (Heston vs. Merton vs. BCC side-by-side)
    → requires: All three individual pricing forms working independently

Credit term structure chart
    → requires: n-year transition working correctly (P^n validated)
    → requires: default_probability_term_structure backend endpoint

Expected bond value sensitivity analysis
    → requires: expected_bond_value backend endpoint
    → requires: credit term structure chart (builds on it conceptually)

ML: regime-conditioned portfolio weights
    → requires: HMM regime detection working (stochastic models tab)
    → requires: PCA / regression infrastructure (ML tab)

ML: GARCH vs. HMM volatility comparison
    → requires: HMM regime detection (already built)
    → requires: GARCH implementation (new; in statsmodels)
```

---

## MVP Recommendation for Current Milestone (Stochastic Models)

Prioritize in this order:

1. **Credit transitions tab** — Matrix display, P^n, cumulative default term structure (line chart), Monte Carlo survival curve. All backend logic exists; primary work is frontend wiring and charts.
2. **CIR interest rate tab** — Yield curve chart, parameter inputs (κ, θ, σ, r₀), Feller condition badge, calibration to US Treasury defaults.
3. **Regime detection tab** — Already partially wired; add a Chart.js line chart of regime probabilities over time (calm/stressed probability history).
4. **Heston / Merton / BCC pricing tab** — Three sub-forms with parameter inputs; side-by-side price output; Heston vs. BS delta.
5. **Heston calibration tab** — Input ticker + rate; show calibrated parameters with interpretation, RMSE, Feller badge.

Defer to ML module:
- MDP portfolio rebalancing demo (new backend required; high complexity)
- LASSO/Ridge regression (no backend yet)
- Backtesting framework (significant infrastructure)
- GARCH implementation (new dependency)

---

## Sources

All findings are based on:
- Direct inspection of existing Python backend files in `src/analytics/` and `src/derivatives/`
- Direct inspection of existing JavaScript frontend in `static/js/stochasticModels.js`
- Domain knowledge of MFE curricula (Columbia IEOR, Baruch MFE, CMU MSCF, NYU Courant standard syllabi)
- Domain knowledge of quantitative finance recruiting expectations (sell-side strats, buy-side quant research, risk roles)
- Standard academic references: Heston (1993), Merton (1976), Bates (1996), Cox-Ingersoll-Ross (1985), Hamilton (1989) for HMM filter

**Confidence breakdown:**
- Stochastic models feature landscape: HIGH (well-established curriculum; backend code confirmed existing)
- ML-in-finance features: MEDIUM (next semester module; content inferred from standard MFE ML curricula, not yet a codebase artifact)
- Recruiter expectations: HIGH (domain expertise; consistent with standard quant finance hiring practices)
- Anti-feature rationale: HIGH (derived from scope constraints in PROJECT.md and codebase inspection)
