# Project Research Summary

**Project:** MFE Showcase Web App — Stochastic Models + ML-in-Finance Additions
**Domain:** Quantitative Finance / Academic Portfolio Showcase
**Researched:** 2026-03-03
**Confidence:** HIGH

## Executive Summary

This project is an MFE-level quantitative finance showcase app built on Flask + Vanilla JS, targeting quant recruiters and MFE peers. The existing codebase already contains a complete numerical stack (numpy, scipy, pandas, scikit-learn) and six nearly-complete stochastic model backend files (CIR, credit transitions, regime detection, Fourier/Heston pricer, Merton pricer, and calibration). The recommended approach is to complete the current stochastic models milestone before beginning the ML-in-finance module — the backends are largely done, and the primary remaining work is frontend wiring, Plotly chart integration, and a targeted validation pass to eliminate model correctness errors that would embarrass the app in front of a recruiter.

The greatest risks are not architectural but mathematical: seven specific pitfalls can cause catastrophically wrong outputs that a quantitative recruiter will catch in under 30 seconds (non-monotone survival curves, Heston prices below intrinsic value, wrong regime labels during known stress periods, Feller condition violations, flat IV smile post-calibration). These must be fixed before any UI wiring is considered complete. The secondary risk is UX latency: Heston calibration takes 60-120 seconds and the current frontend gives no progress feedback, which causes demo abandonment at the most technically impressive feature.

The stack requires no new dependencies for the stochastic models milestone. For the ML-in-finance module (next semester), add statsmodels and xgboost to requirements.txt — all other ML infrastructure is already installed. Do not add QuantLib, hmmlearn, ta-lib, or any deep-learning-specific libraries in this milestone; they either conflict with the showcase purpose (replacing hand-rolled course code with black-box libraries) or create deployment problems on Render.

---

## Key Findings

### Recommended Stack

The existing numpy/scipy/pandas/scikit-learn stack satisfies all computational requirements for the stochastic models milestone without modification. All six WIP backend files confirm pure numpy/scipy implementations — this is intentional and correct, as the app showcases MFE coursework code rather than wrapping third-party quant libraries. For the ML module, two libraries should be added when that semester begins: statsmodels (for econometric regression tables with p-values, not available in sklearn) and xgboost (gradient boosting for return prediction). PyTorch is already installed via the sentiment module and can be reused for any LSTM work in the ML module.

Frontend visualization uses Plotly.js via CDN, consistent throughout all existing tabs. The current stochastic models JS renders results as HTML tables only — the key upgrade is adding Plotly charts (yield curves, survival curves, regime probability time series) to match the quality benchmark set by the Volatility Surface tab.

**Core technologies:**
- numpy + scipy: All stochastic model math (matrix operations, optimization, Fourier integration) — already installed, no changes needed
- pandas + yfinance: Time series handling and market data fetching — already installed
- scikit-learn: Existing ML infrastructure; LinearRegression and PCA already used in financial_analytics.py
- Flask + gunicorn: Web layer — keep as-is; do not switch to async frameworks
- Plotly.js 2.x (CDN): All charts including 3D surfaces and heatmaps — already embedded in app
- statsmodels (add for ML module): OLS with diagnostics, ARIMA, ADF tests — not currently installed
- xgboost (add for ML module): Gradient boosting for return prediction — not currently installed

### Expected Features

From a recruiter's perspective, the showcase succeeds if it covers all table-stakes features with correct model outputs. The differentiators (cross-model comparison, live calibration, regime-conditioned interpretation) are what separate this app from a typical MFE student project.

**Must have (table stakes — stochastic models):**
- Markov chain transition matrix display with row-stochastic validation — foundational MFE topic
- n-year matrix power (P^n) with cumulative default term structure chart — standard credit risk deliverable
- Monte Carlo survival curve — demonstrates MC fluency alongside analytical result
- CIR yield curve with Feller condition badge — interest rate model core deliverable
- HMM regime detection with filtered probability chart — modern staple; real ticker required
- Heston pricing with parameter inputs and Black-Scholes comparison — most famous SV model
- Heston calibration with RMSE display and calibrated parameter interpretation
- Interactive parameter inputs for all models (not static output)

**Should have (differentiators):**
- Side-by-side Heston / Merton / BCC price comparison for same contract — rare in student demos
- CIR calibration to live US Treasury yields with RMSE — practitioner-level feature
- BCC pricing with CIR discount factor toggle — demonstrates cross-module integration
- Regime-conditioned annualized return and vol display — economic interpretation of HMM states
- Visual credit migration heatmap (colored grid, not table)
- Relative RMSE percentage display with qualitative fit label (Good/Acceptable/Poor)
- Calibration progress indicator ("Stage 1 grid search: 40%...")

**Defer (ML module — next semester):**
- LASSO/Ridge regression for factor selection
- Backtesting framework for ML signals
- GARCH vs. HMM volatility comparison
- SHAP values with XGBoost
- Rolling time-series cross-validation framework
- MDP portfolio rebalancing demo (requires new backend; high complexity)

### Architecture Approach

The existing three-layer architecture (Model Layer → Flask API → Vanilla JS frontend) is clean and must be replicated exactly for all new modules. Model files in `src/` are pure Python with no Flask imports; routes in `webapp.py` parse JSON, call model functions, run `convert_numpy_types()`, and return `jsonify()`; JS files read form inputs, POST to API, and render HTML results or Plotly charts. Lazy imports inside route functions (not at module level) are critical for startup performance and are already established in all existing routes.

**Major components:**
1. Model Layer (`src/analytics/`, `src/derivatives/`) — pure quant math, returns Python dicts, no HTTP awareness
2. Flask API Layer (`webapp.py`) — input parsing, model dispatch, numpy type conversion, JSON serialization
3. JS Frontend (`static/js/*.js`, `templates/index.html`) — form collection, API calls, HTML + Plotly rendering
4. Tab Router (`tabs.js`, `switchStochasticTab()`) — two-level tab structure (main tabs + stochastic sub-tabs)

Four established data-flow patterns cover all model types: Pure-Parameter (no data fetch, sub-second response), Fetch-Then-Compute (yfinance dependency, 10-120s, requires loading state), Multi-Step Pipeline (calibration then pricing, JS state variables), and Benchmark Comparison (primary model + reference model in same route response).

### Critical Pitfalls

Research identified 7 critical pitfalls (causing recruiter-visible model failures) and 11 moderate/minor pitfalls. The top 5 to address before any demo:

1. **Non-monotone survival curves** — `credit_risk_analysis()` passes custom matrices without row normalization. Add `_validate_transition_matrix()` that enforces row sums to 1.0 ±1e-6 before any matrix is used in computation.

2. **Heston price below intrinsic value** — Fourier integration truncated at 500 for all maturities; insufficient for T > 2 years. Add adaptive integration limits (1000 for T > 1yr, 2000 for T > 5yr) and add post-price put-call parity assertion.

3. **Flat IV smile after Heston calibration** — Raw dollar MSE causes deep ITM options to dominate calibration, effectively ignoring the OTM options that carry smile information. Switch to relative MSE `((model - market) / market)^2` or vega-weighted calibration.

4. **HMM regime mislabeling during COVID March 2020** — Label switching produces wrong RISK_ON/RISK_OFF assignment when `sigma[0] ≈ sigma[1]`. Add confidence threshold: if `abs(sigma[calm] - sigma[stressed]) / sigma[stressed] < 0.2`, label result "ambiguous." Validate on SPY 2020-03.

5. **Calibration demo abandonment** — 60-120s Heston calibration with no progress feedback causes users to assume the app crashed. Add expected time display upfront and progress streaming, or pre-cache results for default demo tickers.

Additional critical issues:
- `expected_bond_value()` uses undiscounted coupon sum — must add proper annuity discounting before connecting to frontend
- CIR Feller condition violation not blocked — add UI warning banner when Feller is violated; add hard enforcement option in calibration

---

## Implications for Roadmap

Based on combined research, a four-phase structure is recommended. Phases 1-3 cover the current stochastic models milestone; Phase 4 is the ML-in-finance module for next semester.

### Phase 1: Backend Validation and Math Correctness

**Rationale:** All critical pitfalls are backend math errors that must be fixed before any frontend work. Wiring a UI to a backend that returns non-monotone survival curves or flat IV smiles wastes all subsequent UI work. Validation first ensures the demo is safe to show.

**Delivers:** All six stochastic model backends with verified correct outputs and no recruiter-visible errors.

**Addresses:** Table-stakes features that are already implemented but mathematically flawed (credit transitions, CIR, Heston pricing, calibration).

**Avoids:**
- Pitfall 1: Add row normalization validator for transition matrices
- Pitfall 2: Fix Fourier integration limits with adaptive strategy; add put-call parity assertion
- Pitfall 3: Switch calibration to relative MSE
- Pitfall 4: Fix bond value discounting in `expected_bond_value()`
- Pitfall 5: Add HMM label confidence check and SPY 2020-03 validation
- Pitfall 6: Add Feller hard enforcement in CIR calibration
- Pitfall 17: Add input validation with bounds in all API routes

**Research flag:** Standard patterns — no additional research needed. All pitfalls are directly identified from code review.

### Phase 2: Complete Missing Backend Pieces

**Rationale:** Several backend gaps block table-stakes features entirely. The Markov chain standalone backend does not exist, BCC calibration has no Flask route, and the regime detector does not return the full filtered probability time series needed for a chart. These gaps must be closed before frontend wiring.

**Delivers:** Complete backend coverage for all planned stochastic model features; no UI-visible gaps.

**Addresses:**
- Markov chain / MDP backend module (`src/analytics/markov_chain.py`) with generic transition matrix, stationary distribution, n-step distribution
- `/api/markov_chain` and (deferred) `/api/mdp` Flask routes
- `/api/calibrate_bcc` Flask route wiring the existing `BCCCalibrator`
- Regime detection response extended to return full `filtered_probs` time series (not just final signal)
- BCC sub-tab in `index.html` and `stochasticModels.js`

**Avoids:**
- Pitfall 10: MDP should have well-defined reward function and baseline comparison or be explicitly deferred
- Pitfall 9: Ensure smoothed probabilities are never used for signal generation; label them clearly

**Research flag:** MDP design may benefit from phase-specific research if implemented in this milestone. If deferred, no research needed.

### Phase 3: Frontend Wiring and Visualization Upgrade

**Rationale:** With all backends validated and complete, frontend wiring is safe and efficient. The primary upgrade beyond form wiring is replacing table-only outputs with Plotly charts — this is what moves the UI from homework-grade to analysis-grade.

**Delivers:** Fully interactive stochastic models tab with Plotly visualizations matching the Volatility Surface tab quality benchmark.

**Addresses:**
- All table-stakes interactive parameter inputs
- Plotly yield curve chart for CIR (line: maturity vs. rate)
- Plotly survival curve chart for credit transitions (line: horizon vs. survival probability)
- Plotly regime probability chart (time series colored by calm/stressed state)
- Plotly credit transition heatmap (n×n matrix colored by probability magnitude)
- Heston vs. Black-Scholes side-by-side price display
- Differentiator: Heston / Merton / BCC side-by-side comparison tab
- Differentiator: Calibration progress indicator or cached demo results for default tickers
- Relative RMSE percentage with qualitative label for all calibration outputs
- Feller condition badge and ratio display for CIR and Heston
- Data source date range display for all yfinance-dependent outputs

**Avoids:**
- Pitfall 7: Add expected computation time and progress feedback for calibration
- Pitfall 8: Filter options chain by minimum open interest and max bid-ask spread
- Pitfall 11: Standardize all volatility outputs to annualized standard deviation
- Pitfall 12: Assert minimum observation count for yfinance fetches; display data range in UI
- Pitfall 14: Add relative RMSE % with Good/Acceptable/Poor label
- Pitfall 15: Add Monte Carlo standard error and 95% CI display
- Pitfall 16: Remove or document unused `sigma_gbm` parameter in BCC
- Pitfall 18: Display S&P matrix source and vintage in credit transitions UI

**Research flag:** Plotly chart types are well-documented — no research phase needed. Calibration progress streaming (SSE) may need brief implementation research if chosen over pre-caching.

### Phase 4: ML-in-Finance Module (Next Semester)

**Rationale:** Deferred until stochastic models milestone is complete and publishable. Starting ML before stochastic models are validated creates competing priorities and a fragmented demo.

**Delivers:** New main tab with sub-tabs for supervised learning (OLS, LASSO/Ridge), unsupervised learning (PCA, clustering), and backtesting.

**Uses:**
- scikit-learn (already installed): TimeSeriesSplit, regularized regression, classification
- statsmodels (add to requirements.txt): OLS with diagnostics, GARCH
- xgboost (add to requirements.txt): Gradient boosting with SHAP values
- PyTorch (already installed): LSTM if included

**Architecture:** Same pattern as Stochastic Models — new main tab button, `mlFinanceTab` div, `mlFinance.js`, `src/ml/` package with lazy imports in new Flask routes.

**Avoids:**
- Pitfall 13: Compute features within TimeSeriesSplit to prevent data leakage — enforce before any model training
- ML overfitting: Show OOS Sharpe explicitly; compare to buy-and-hold baseline

**Research flag:** Needs phase-specific research for GARCH implementation (statsmodels API), SHAP integration with XGBoost, and backtesting framework design. These are well-documented individually but the integration pattern for this specific app needs thought.

### Phase Ordering Rationale

- Backend validation must precede frontend wiring because wiring UI to incorrect math produces demos that fail under recruiter scrutiny in ways that are worse than no demo at all.
- Missing backend pieces (Markov chain module, BCC route, filtered probability time series) must exist before frontend forms that depend on them.
- Visualization upgrade is bundled with frontend wiring because the same JS functions that wire forms also drive the Plotly calls — separating them creates redundant work.
- ML module is gated on stochastic models completion because: (a) the HMM regime output feeds ML features, (b) adding new tab infrastructure while existing tabs are broken creates confusion, and (c) stochastic models are the current semester's deliverable.

### Research Flags

Phases needing deeper research during planning:
- **Phase 4 (ML module):** GARCH/statsmodels API, SHAP+XGBoost integration, backtesting framework design — these have well-documented components but the integration approach for this app's architecture needs planning research.
- **Phase 3 (calibration progress streaming):** If server-sent events (SSE) are chosen over pre-cached results, a brief implementation research pass is warranted for Flask SSE patterns.

Phases with standard patterns (skip research-phase):
- **Phase 1 (backend validation):** All pitfalls are directly identified from code; fixes follow standard numerical analysis patterns.
- **Phase 2 (backend gaps):** Markov chain implementation follows established numpy.linalg.matrix_power pattern; BCC route follows existing route pattern exactly.
- **Phase 3 (Plotly wiring):** Plotly.js documentation is comprehensive; chart types are already confirmed from volatilitySurface.js reference implementation.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Derived directly from requirements.txt and import analysis of all WIP source files; no speculation |
| Features | HIGH | Table stakes from established MFE curricula; differentiators cross-referenced against existing backend capabilities |
| Architecture | HIGH | Based on direct inspection of webapp.py (all routes), stochasticModels.js (701 lines), index.html (tab structure), and all six model backend files |
| Pitfalls | HIGH | All 7 critical pitfalls derived from direct code review of WIP files; not speculative; confirmed against domain theory |

**Overall confidence:** HIGH

### Gaps to Address

- **ML module content:** Confidence is MEDIUM for ML-in-finance features because the specific course content for next semester is not yet confirmed. The feature list is inferred from standard MFE ML curricula (Columbia IEOR, Baruch, CMU MSCF patterns). Validate against actual course syllabus when available.
- **numpy 2.x compatibility:** The existing `>=1.23.0` pin may resolve to numpy 2.x. A test run against all WIP imports should confirm no breaking changes before Phase 1 work begins.
- **Calibration latency measurement:** The 60-120 second estimate for Heston calibration is from architecture analysis; actual latency on Render's free tier may differ. Measure during Phase 1 to choose between SSE streaming vs. pre-caching approach.
- **MDP scope:** Whether MDP (Markov Decision Process) belongs in Phase 2 or is deferred to a later milestone is unresolved. The backend does not exist and complexity is high. Recommend explicit scoping decision before Phase 2 begins.

---

## Sources

### Primary (HIGH confidence)
- Existing codebase: `requirements.txt`, `webapp.py`, `src/analytics/credit_transitions.py`, `src/analytics/interest_rate_models.py`, `src/analytics/regime_detection.py`, `src/derivatives/fourier_pricer.py`, `src/derivatives/model_calibration.py`, `static/js/stochasticModels.js`, `templates/index.html`
- Albrecher, H. et al. (2007). "The Little Heston Trap." — Pitfall 2 basis
- Heston, S.L. (1993). "A Closed-Form Solution for Options with Stochastic Volatility." — model basis
- Hamilton, J.D. (1989). "A New Approach to the Economic Analysis of Nonstationary Time Series." — HMM basis
- Cox, Ingersoll, Ross (1985). "A Theory of the Term Structure of Interest Rates." — CIR basis
- `.planning/PROJECT.md` — requirements and constraints

### Secondary (MEDIUM confidence)
- Standard MFE curricula patterns (Columbia IEOR, Baruch MFE, CMU MSCF, NYU Courant) — ML-in-finance feature list
- scipy documentation (docs.scipy.org) — version compatibility
- Plotly.js releases (github.com/plotly/plotly.js/releases) — CDN version guidance

### Tertiary (LOW confidence)
- numpy 2.0 migration guide — compatibility with existing `>=1.23.0` pin; needs empirical validation

---
*Research completed: 2026-03-03*
*Ready for roadmap: yes*
