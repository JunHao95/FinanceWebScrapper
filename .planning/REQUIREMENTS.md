# Requirements: MFE Showcase Web App

**Defined:** 2026-03-03
**Core Value:** Every completed MFE module becomes a working, interactive demo that a recruiter can run and a peer can learn from.

## v1 Requirements

Requirements for the current milestone: completing the Stochastic Models section and building the ML in Finance section.

### Model Correctness (Stochastic Models)

- [ ] **MATH-01**: Credit transitions bond valuation discounts coupons by time (non-discounted coupons bug fixed)
- [ ] **MATH-02**: Heston calibration uses relative/percentage MSE weighting so OTM options contribute to the smile (dollar-MSE bug fixed)
- [ ] **MATH-03**: CIR calibration enforces Feller condition (2κθ ≥ σ²) as a hard constraint, not a soft penalty
- [ ] **MATH-04**: HMM regime labels are stable and correctly identify high-volatility state as RISK_OFF (label-switching robustness)
- [ ] **MATH-05**: All stochastic model outputs validated against textbook benchmarks or closed-form solutions before UI wiring

### Markov Chain & MDP Module

- [ ] **MARKOV-01**: User can input a transition matrix and compute steady-state distribution
- [ ] **MARKOV-02**: User can compute absorption probabilities for absorbing Markov chains
- [ ] **MARKOV-03**: User can visualize state transition diagram or heatmap of transition matrix
- [ ] **MARKOV-04**: User can define a portfolio rebalancing Markov Decision Process (states, actions, rewards)
- [ ] **MARKOV-05**: User can compute optimal policy via value iteration or policy iteration for the MDP
- [ ] **MARKOV-06**: Markov/MDP results display in dedicated UI sub-tab with interactive parameters

### Credit Transitions Module

- [ ] **CREDIT-01**: User can select a rating transition matrix (Moody's/S&P style) and simulate credit migration
- [ ] **CREDIT-02**: User can view credit migration heatmap showing transition probabilities
- [ ] **CREDIT-03**: User can compute and view default probability / survival curve chart over time
- [ ] **CREDIT-04**: User can compute bond valuation with corrected time-discounted coupons
- [ ] **CREDIT-05**: Credit transitions results display in dedicated UI sub-tab

### Interest Rate Models Module

- [ ] **RATE-01**: User can simulate CIR (Cox-Ingersoll-Ross) interest rate paths with chosen parameters
- [ ] **RATE-02**: User can simulate Vasicek interest rate paths with chosen parameters
- [ ] **RATE-03**: User can view yield curve generated from the selected model
- [ ] **RATE-04**: UI displays whether Feller condition is satisfied for CIR parameters
- [ ] **RATE-05**: Interest rate model results display in dedicated UI sub-tab with Plotly chart output

### Regime Detection Module

- [ ] **REGIME-01**: User can run HMM regime detection on a selected ticker and date range
- [ ] **REGIME-02**: User can view filtered probability time series chart (bull/bear/crisis states over time)
- [ ] **REGIME-03**: User can view regime-annotated price chart (price series with regime background shading)
- [ ] **REGIME-04**: Model correctly identifies crisis periods (e.g., SPY March 2020 = RISK_OFF)
- [ ] **REGIME-05**: Regime detection results display in dedicated UI sub-tab

### Heston / Fourier Pricing Module

- [ ] **HESTON-01**: User can price European options using the Fourier/Heston model with chosen parameters
- [ ] **HESTON-02**: User can view implied volatility surface (strike vs. maturity) as a Plotly chart
- [ ] **HESTON-03**: User can compare Heston price vs. Black-Scholes price for the same contract
- [ ] **HESTON-04**: IV surface shows non-flat smile (volatility skew visible)
- [ ] **HESTON-05**: Heston pricing results display in dedicated UI sub-tab

### Model Calibration Module

- [ ] **CALIB-01**: User can calibrate Heston model to market option prices for a selected ticker
- [ ] **CALIB-02**: User can calibrate BCC (Bates-Chan-Chang) model to market option prices
- [ ] **CALIB-03**: Calibration shows live progress streaming (iteration count, current error) via SSE
- [ ] **CALIB-04**: Calibration results display relative RMSE and fitted vs. market IV comparison
- [ ] **CALIB-05**: BCC calibration has a Flask route and UI sub-tab (currently backend-complete, no route/UI)

### ML in Finance Module

- [ ] **ML-01**: User can run linear regression on financial factors and view coefficient table with significance tests
- [ ] **ML-02**: User can run logistic regression for return direction classification and view confusion matrix
- [ ] **ML-03**: User can run Random Forest / XGBoost return prediction and view feature importance chart
- [ ] **ML-04**: User can run PCA on a portfolio of stocks and view explained variance and component loadings
- [ ] **ML-05**: User can run k-means clustering for portfolio grouping and view cluster assignments
- [ ] **ML-06**: User can run ARIMA model on a return series and view forecast with confidence intervals
- [ ] **ML-07**: User can run GARCH volatility forecasting and view conditional volatility chart
- [ ] **ML-08**: All ML models use TimeSeriesSplit to prevent data leakage (no look-ahead bias)
- [ ] **ML-09**: ML module appears as a new main tab in the UI consistent with existing tab structure

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

Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MATH-01 through MATH-05 | Phase 1 | Pending |
| MARKOV-01 through MARKOV-06 | Phase 2 | Pending |
| CREDIT-01 through CREDIT-05 | Phase 2 | Pending |
| RATE-01 through RATE-05 | Phase 2 | Pending |
| REGIME-01 through REGIME-05 | Phase 3 | Pending |
| HESTON-01 through HESTON-05 | Phase 3 | Pending |
| CALIB-01 through CALIB-05 | Phase 3 | Pending |
| ML-01 through ML-09 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 40 total
- Mapped to phases: 40
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-03*
*Last updated: 2026-03-03 after initial definition*
