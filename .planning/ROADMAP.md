# Roadmap: MFE Showcase Web App

## Overview

This milestone completes the Stochastic Models section and builds the ML-in-Finance section of an interactive MFE portfolio showcase. The work proceeds in four phases ordered by risk: fix math correctness first (Phase 1), close backend gaps so all planned features have callable APIs (Phase 2), wire the frontend with Plotly visualizations so recruiters can interact with live models (Phase 3), then build the ML-in-Finance module as a new main tab when the semester begins (Phase 4). Phases 1-3 complete the current semester deliverable; Phase 4 is the next semester deliverable.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Math Correctness** - Fix all recruiter-visible model errors in the stochastic model backends before any UI is wired (completed 2026-03-03)
- [x] **Phase 2: Backend Completeness** - Close backend gaps so every planned stochastic feature has a callable Flask API (completed 2026-03-05)
- [x] **Phase 3: Frontend Wiring and Visualization** - Wire all stochastic model sub-tabs with interactive inputs and Plotly charts (completed 2026-03-07)
- [x] **Phase 4: ML-in-Finance Module** - Build the new ML main tab with supervised, unsupervised, and time-series models (completed 2026-03-08)
- [ ] **Phase 5: Stochastic Models UI Completion** - Wire Markov Chain sub-tab and Vasicek model selector (gap closure phase from v1.0 audit)

## Phase Details

### Phase 1: Math Correctness
**Goal**: All six stochastic model backends produce results that a quantitative recruiter cannot fault — no non-monotone survival curves, no flat IV smiles, no Heston prices below intrinsic value, no HMM mislabeling of known stress periods, no Feller violations silently accepted.
**Depends on**: Nothing (first phase)
**Requirements**: MATH-01, MATH-02, MATH-03, MATH-04, MATH-05
**Success Criteria** (what must be TRUE):
  1. Running credit transition bond valuation on a par bond produces a price of 100 (within 0.01), confirming coupon discounting is time-correct.
  2. Heston calibration on SPY options produces a non-flat fitted IV smile where OTM options show measurably different implied vol than ATM, confirming relative MSE weighting is active.
  3. Setting CIR parameters that violate the Feller condition (2κθ < σ²) causes the calibrator to reject or flag them as invalid — the bad parameter set does not produce a silently wrong yield curve.
  4. Running HMM regime detection on SPY for March 2020 labels that period RISK_OFF (not RISK_ON), confirming label-switching is resolved.
  5. All model backends pass a documented validation check against a closed-form or textbook benchmark before Phase 2 begins.
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Fix coupon discounting (MATH-01) and CIR Feller hard constraint (MATH-03)
- [ ] 01-02-PLAN.md — Fix Heston relative MSE calibration (MATH-02) and HMM dual-criterion labels (MATH-04)
- [ ] 01-03-PLAN.md — Benchmark test suite validating all five fixes (MATH-05)

### Phase 2: Backend Completeness
**Goal**: Every stochastic model feature described in requirements has a callable Python function and a Flask route — no planned UI element will be blocked by a missing backend when frontend wiring starts.
**Depends on**: Phase 1
**Requirements**: MARKOV-01, MARKOV-02, MARKOV-03, MARKOV-04, MARKOV-05, MARKOV-06, CREDIT-01, CREDIT-02, CREDIT-03, CREDIT-04, CREDIT-05, RATE-01, RATE-02, RATE-03, RATE-04, RATE-05
**Success Criteria** (what must be TRUE):
  1. A POST to `/api/markov_chain` with a valid transition matrix returns a steady-state distribution and absorption probabilities in JSON.
  2. A POST to `/api/markov_chain` with a 3-state matrix returns an n-step power matrix (P^n) and the associated default term structure series.
  3. A POST to `/api/calibrate_bcc` returns calibrated BCC parameters and a fitted vs. market IV comparison JSON — the route exists and returns 200.
  4. A POST to `/api/regime` returns a `filtered_probs` time series (not just a final signal) suitable for rendering a probability chart over time.
  5. CIR and Vasicek route responses include a `feller_satisfied` boolean and `feller_ratio` value that the frontend can display as a badge.
**Plans**: 4 plans

Plans:
- [ ] 02-01-PLAN.md — Markov chain Python functions: steady_state_distribution, absorption_probabilities, portfolio_mdp_value_iteration (MARKOV-01 through MARKOV-05, CREDIT-02, CREDIT-03)
- [ ] 02-02-PLAN.md — Vasicek model functions + extend /api/interest_rate_model with model selector and feller_ratio (RATE-01 through RATE-05)
- [ ] 02-03-PLAN.md — /api/calibrate_bcc Flask route wrapping BCCCalibrator (CREDIT-01, CREDIT-04, CREDIT-05)
- [ ] 02-04-PLAN.md — /api/markov_chain unified Flask route for all five modes (MARKOV-06, CREDIT-01, CREDIT-02, CREDIT-03, CREDIT-05) [depends on 02-01]

### Phase 3: Frontend Wiring and Visualization
**Goal**: The Stochastic Models tab is fully interactive — every sub-tab has parameter inputs, a working submit button, and Plotly chart output matching the quality of the existing Volatility Surface tab. A recruiter can run any stochastic model live without touching code.
**Depends on**: Phase 2
**Requirements**: REGIME-01, REGIME-02, REGIME-03, REGIME-04, REGIME-05, HESTON-01, HESTON-02, HESTON-03, HESTON-04, HESTON-05, CALIB-01, CALIB-02, CALIB-03, CALIB-04, CALIB-05
**Success Criteria** (what must be TRUE):
  1. A user can enter a ticker and date range in the Regime Detection sub-tab, click Run, and see a filtered-probability time series chart with regime shading on the price chart — SPY March 2020 shows RISK_OFF shading.
  2. A user can enter Heston parameters in the Heston Pricing sub-tab and see both the Heston price and the Black-Scholes price for the same contract side-by-side, plus an IV surface chart showing a non-flat smile.
  3. A user can click Calibrate Heston for a default ticker and see a calibration progress indicator (iteration count or stage label) while the calibration runs, then see a fitted vs. market IV comparison and relative RMSE with a qualitative label (Good / Acceptable / Poor).
  4. The BCC calibration sub-tab exists, accepts inputs, and returns calibrated parameters and a fitted vs. market IV chart — the route is wired end-to-end.
  5. Every stochastic model sub-tab (Markov, Credit, Rates, Regime, Heston, Calibration) displays results as Plotly charts (not raw tables) and shows a CIR Feller condition badge where applicable.
**Plans**: 5 plans

Plans:
- [x] 03-01-PLAN.md — Regime Detection tab: webapp.py patch (prices/dates/regime_sequence) + two Plotly charts (REGIME-01 through REGIME-05)
- [ ] 03-02-PLAN.md — Heston Pricing tab: new sub-tab, /api/heston_iv_surface route, price cards, 3D IV surface (HESTON-01 through HESTON-05)
- [ ] 03-03-PLAN.md — Heston Calibration SSE: callback in HestonCalibrator, /api/calibrate_heston_stream, EventSource JS, IV chart + RMSE badge (CALIB-01, CALIB-03, CALIB-04)
- [ ] 03-04-PLAN.md — BCC Calibration tab: new sub-tab HTML + runBCCCalibration JS wiring to existing /api/calibrate_bcc (CALIB-02, CALIB-05)
- [ ] 03-05-PLAN.md — Markov/Credit/Rates Plotly upgrade: heatmap, survival curve, yield curve + Feller badge; full integration smoke test checkpoint (all 15 requirements verified)

### Phase 4: ML-in-Finance Module
**Goal**: A new Reinforcement Learning main tab exists in the UI, contains 4 interactive sub-tabs (Investment MDP, Gridworld, Portfolio Rotation PI, Portfolio Rotation QL), and allows a user to run all four RL demos with interactive parameter inputs and Plotly output — all backed by Python RL algorithms already implemented in rl_models.py.
**Depends on**: Phase 3
**Requirements**: ML-01, ML-02, ML-03, ML-04, ML-05, ML-06, ML-07, ML-08, ML-09
**Success Criteria** (what must be TRUE):
  1. A user can adjust gamma and click Run Policy Iteration in the Investment MDP sub-tab, seeing Buy/Sell/Sell policy cards, a V* bar chart, and a Q-value heatmap.
  2. A user can toggle wind and run Gridworld PI, seeing a 4×4 arrow policy grid and V* heatmap, converging in 4 iterations.
  3. A user can set train/test dates and run Portfolio Rotation (PI), seeing a cumulative return line chart vs 60/40 benchmark with CAGR/Vol/Sharpe metrics.
  4. A user can adjust alpha/epochs/epsilon and run Portfolio Rotation (QL), seeing the same line chart plus a 12×5 Q-table heatmap.
  5. The Reinforcement Learning tab appears as a top-level tab in the nav bar after Stochastic Models.
  6. All models use TimeSeriesSplit-equivalent leakage-free design: vol terciles on train data only, signals lagged 1 month.
**Plans**: 1 plan

Plans:
- [ ] 04-01-PLAN.md — Add RL nav button and complete rlTab HTML to index.html (ML-01 through ML-09)

### Phase 5: Stochastic Models UI Completion
**Goal**: Every stochastic model feature that has a backend API is reachable by a user from the UI — Markov Chain modes (steady-state, absorption, MDP) have an interactive sub-tab, and the Interest Rate sub-tab exposes both CIR and Vasicek via a model selector.
**Depends on**: Phase 2 (backends already complete), Phase 3 (UI structure already exists)
**Requirements**: MARKOV-01, MARKOV-02, MARKOV-03, MARKOV-04, MARKOV-05, MARKOV-06, RATE-02, RATE-03
**Gap Closure**: Closes gaps from v1.0 audit — Markov sub-tab missing, Vasicek UI path missing
**Success Criteria** (what must be TRUE):
  1. A user can open the Stochastic Models tab, navigate to a Markov Chain sub-tab, enter a transition matrix, and see the steady-state distribution rendered as a Plotly bar chart.
  2. A user can switch to an absorption mode form, enter an absorbing Markov chain, and see absorption probabilities.
  3. A user can switch to an MDP mode form and see the optimal policy and value function.
  4. A user can select "Vasicek" from a model selector in the Interest Rate sub-tab, click Run, and see a Vasicek yield curve rendered as a Plotly chart.
**Plans**: 1 plan

Plans:
- [ ] 05-01-PLAN.md — Markov Chain sub-tab HTML+JS + Vasicek model selector (MARKOV-01 to MARKOV-06, RATE-02, RATE-03)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Math Correctness | 3/3 | Complete   | 2026-03-03 |
| 2. Backend Completeness | 4/4 | Complete   | 2026-03-05 |
| 3. Frontend Wiring and Visualization | 5/5 | Complete   | 2026-03-07 |
| 4. ML-in-Finance Module | 1/1 | Complete   | 2026-03-08 |
| 5. Stochastic Models UI Completion | 0/1 | Not started | - |
