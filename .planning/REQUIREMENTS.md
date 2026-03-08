# Requirements: MFE Showcase Web App

**Defined:** 2026-03-03
**Core Value:** Every completed MFE module becomes a working, interactive demo that a recruiter can run and a peer can learn from.

## v1 Requirements

Requirements for the current milestone: completing the Stochastic Models section and building the ML in Finance section.

### Model Correctness (Stochastic Models)

- [x] **MATH-01**: Credit transitions bond valuation discounts coupons by time (non-discounted coupons bug fixed)
- [x] **MATH-02**: Heston calibration uses relative/percentage MSE weighting so OTM options contribute to the smile (dollar-MSE bug fixed)
- [x] **MATH-03**: CIR calibration enforces Feller condition (2κθ ≥ σ²) as a hard constraint, not a soft penalty
- [x] **MATH-04**: HMM regime labels are stable and correctly identify high-volatility state as RISK_OFF (label-switching robustness)
- [x] **MATH-05**: All stochastic model outputs validated against textbook benchmarks or closed-form solutions before UI wiring

### Markov Chain & MDP Module

- [x] **MARKOV-01**: User can input a transition matrix and compute steady-state distribution
- [x] **MARKOV-02**: User can compute absorption probabilities for absorbing Markov chains
- [x] **MARKOV-03**: User can visualize state transition diagram or heatmap of transition matrix
- [x] **MARKOV-04**: User can define a portfolio rebalancing Markov Decision Process (states, actions, rewards)
- [x] **MARKOV-05**: User can compute optimal policy via value iteration or policy iteration for the MDP
- [x] **MARKOV-06**: Markov/MDP results display in dedicated UI sub-tab with interactive parameters

### Credit Transitions Module

- [x] **CREDIT-01**: User can select a rating transition matrix (Moody's/S&P style) and simulate credit migration
- [x] **CREDIT-02**: User can view credit migration heatmap showing transition probabilities
- [x] **CREDIT-03**: User can compute and view default probability / survival curve chart over time
- [x] **CREDIT-04**: User can compute bond valuation with corrected time-discounted coupons
- [x] **CREDIT-05**: Credit transitions results display in dedicated UI sub-tab

### Interest Rate Models Module

- [x] **RATE-01**: User can simulate CIR (Cox-Ingersoll-Ross) interest rate paths with chosen parameters
- [x] **RATE-02**: User can simulate Vasicek interest rate paths with chosen parameters
- [x] **RATE-03**: User can view yield curve generated from the selected model
- [x] **RATE-04**: UI displays whether Feller condition is satisfied for CIR parameters
- [x] **RATE-05**: Interest rate model results display in dedicated UI sub-tab with Plotly chart output

### Regime Detection Module

- [x] **REGIME-01**: User can run HMM regime detection on a selected ticker and date range
- [x] **REGIME-02**: User can view filtered probability time series chart (bull/bear/crisis states over time)
- [x] **REGIME-03**: User can view regime-annotated price chart (price series with regime background shading)
- [x] **REGIME-04**: Model correctly identifies crisis periods (e.g., SPY March 2020 = RISK_OFF)
- [x] **REGIME-05**: Regime detection results display in dedicated UI sub-tab

### Heston / Fourier Pricing Module

- [x] **HESTON-01**: User can price European options using the Fourier/Heston model with chosen parameters
- [x] **HESTON-02**: User can view implied volatility surface (strike vs. maturity) as a Plotly chart
- [x] **HESTON-03**: User can compare Heston price vs. Black-Scholes price for the same contract
- [x] **HESTON-04**: IV surface shows non-flat smile (volatility skew visible)
- [x] **HESTON-05**: Heston pricing results display in dedicated UI sub-tab

### Model Calibration Module

- [x] **CALIB-01**: User can calibrate Heston model to market option prices for a selected ticker
- [x] **CALIB-02**: User can calibrate BCC (Bates-Chan-Chang) model to market option prices
- [x] **CALIB-03**: Calibration shows live progress streaming (iteration count, current error) via SSE
- [x] **CALIB-04**: Calibration results display relative RMSE and fitted vs. market IV comparison
- [x] **CALIB-05**: BCC calibration has a Flask route and UI sub-tab (currently backend-complete, no route/UI)

### ML in Finance Module

- [x] **ML-01**: User can run linear regression on financial factors and view coefficient table with significance tests
- [x] **ML-02**: User can run logistic regression for return direction classification and view confusion matrix
- [x] **ML-03**: User can run Random Forest / XGBoost return prediction and view feature importance chart
- [x] **ML-04**: User can run PCA on a portfolio of stocks and view explained variance and component loadings
- [x] **ML-05**: User can run k-means clustering for portfolio grouping and view cluster assignments
- [x] **ML-06**: User can run ARIMA model on a return series and view forecast with confidence intervals
- [x] **ML-07**: User can run GARCH volatility forecasting and view conditional volatility chart
- [x] **ML-08**: All ML models use TimeSeriesSplit to prevent data leakage (no look-ahead bias)
- [x] **ML-09**: ML module appears as a new main tab in the UI consistent with existing tab structure

## v2 Requirements

Deferred to future semesters/milestones.

### Advanced Models

- **V2-01**: Multi-factor interest rate models (HJM, LMM)
- **V2-02**: LSTM / deep learning for return prediction
- **V2-03**: n-state HMM (n > 2) for finer regime granularity
- **V2-04**: Real-time market data streaming
- **V2-05**: MDP with reinforcement learning (Q-learning) for dynamic hedging

### Infrastructure

- **V2-06**: Model result caching for demo tickers (pre-computed results)
- **V2-07**: Export / download results as CSV or PDF report

## Out of Scope

| Feature | Reason |
|---------|--------|
| User authentication | Showcase app, not multi-user platform |
| Mobile app / responsive design | Web-first, desktop demo context |
| Real-time market data feeds | Static/fetched data sufficient for demos |
| QuantLib / hmmlearn / ta-lib | Black-box libraries defeat the showcase purpose; also have C build deps that break on Render |
| Production hardening (rate limiting, auth, etc.) | Academic demo context |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| MATH-01 | Phase 1: Math Correctness | Complete |
| MATH-02 | Phase 1: Math Correctness | Complete |
| MATH-03 | Phase 1: Math Correctness | Complete |
| MATH-04 | Phase 1: Math Correctness | Complete |
| MATH-05 | Phase 1: Math Correctness | Complete |
| MARKOV-01 | Phase 5: Stochastic Models UI Completion | Complete |
| MARKOV-02 | Phase 5: Stochastic Models UI Completion | Complete |
| MARKOV-03 | Phase 5: Stochastic Models UI Completion | Complete |
| MARKOV-04 | Phase 5: Stochastic Models UI Completion | Complete |
| MARKOV-05 | Phase 5: Stochastic Models UI Completion | Complete |
| MARKOV-06 | Phase 5: Stochastic Models UI Completion | Complete |
| CREDIT-01 | Phase 2: Backend Completeness | Complete |
| CREDIT-02 | Phase 2: Backend Completeness | Complete |
| CREDIT-03 | Phase 2: Backend Completeness | Complete |
| CREDIT-04 | Phase 1: Math Correctness | Complete |
| CREDIT-05 | Phase 2: Backend Completeness | Complete |
| RATE-01 | Phase 2: Backend Completeness | Complete |
| RATE-02 | Phase 5: Stochastic Models UI Completion | Complete |
| RATE-03 | Phase 5: Stochastic Models UI Completion | Complete |
| RATE-04 | Phase 2: Backend Completeness | Complete |
| RATE-05 | Phase 2: Backend Completeness | Complete |
| REGIME-01 | Phase 3: Frontend Wiring and Visualization | Complete |
| REGIME-02 | Phase 3: Frontend Wiring and Visualization | Complete |
| REGIME-03 | Phase 3: Frontend Wiring and Visualization | Complete |
| REGIME-04 | Phase 3: Frontend Wiring and Visualization | Complete |
| REGIME-05 | Phase 3: Frontend Wiring and Visualization | Complete |
| HESTON-01 | Phase 3: Frontend Wiring and Visualization | Complete |
| HESTON-02 | Phase 3: Frontend Wiring and Visualization | Complete |
| HESTON-03 | Phase 3: Frontend Wiring and Visualization | Complete |
| HESTON-04 | Phase 3: Frontend Wiring and Visualization | Complete |
| HESTON-05 | Phase 3: Frontend Wiring and Visualization | Complete |
| CALIB-01 | Phase 3: Frontend Wiring and Visualization | Complete |
| CALIB-02 | Phase 3: Frontend Wiring and Visualization | Complete |
| CALIB-03 | Phase 3: Frontend Wiring and Visualization | Complete |
| CALIB-04 | Phase 3: Frontend Wiring and Visualization | Complete |
| CALIB-05 | Phase 3: Frontend Wiring and Visualization | Complete |
| ML-01 | Phase 4: ML-in-Finance Module | Complete |
| ML-02 | Phase 4: ML-in-Finance Module | Complete |
| ML-03 | Phase 4: ML-in-Finance Module | Complete |
| ML-04 | Phase 4: ML-in-Finance Module | Complete |
| ML-05 | Phase 4: ML-in-Finance Module | Complete |
| ML-06 | Phase 4: ML-in-Finance Module | Complete |
| ML-07 | Phase 4: ML-in-Finance Module | Complete |
| ML-08 | Phase 4: ML-in-Finance Module | Complete |
| ML-09 | Phase 4: ML-in-Finance Module | Complete |

**Coverage:**
- v1 requirements: 40 total
- Mapped to phases: 40
- Unmapped: 0
- Pending (gap closure): 8 (MARKOV-01..06, RATE-02, RATE-03 → Phase 5)

---
*Requirements defined: 2026-03-03*
*Last updated: 2026-03-03 after roadmap creation*
