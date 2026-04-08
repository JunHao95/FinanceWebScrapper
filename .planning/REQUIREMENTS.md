# Requirements: MFE Showcase Web App

**Defined:** 2026-03-03
**Updated for v2.0:** 2026-03-08
**Core Value:** Every completed MFE module becomes a working, interactive demo that a recruiter can run and a peer can learn from.

## v1 Requirements (Milestone v1.0 — Complete)

All 40 v1 requirements are complete. See `.planning/v1.0-MILESTONE-AUDIT.md` for full details.

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
- [x] **CALIB-05**: BCC calibration has a Flask route and UI sub-tab

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

---

## v2 Requirements (Milestone v2.0 — Active)

**Milestone:** v2.0 One-Click Analysis Dashboard
**Goal:** From ticker symbols to full analysis in one click.

### Form UX

- [x] **FORM-01**: User can submit analysis with only ticker symbols entered (no required source selection or API key input)
- [x] **FORM-02**: User can toggle advanced settings (sources, API keys) via a collapsible "⚙ Advanced" section
- [x] **FORM-03**: System applies smart defaults (yahoo + finviz + google + technical) when advanced settings are collapsed or unconfigured
- [x] **FORM-04**: User can switch between "% Weight" and "Value" allocation modes via a mode toggle
- [x] **FORM-05**: In Value mode, user enters currency amounts per ticker and sees live computed % weights (e.g., "→ 66.7%")
- [x] **FORM-06**: In Value mode, user can select currency (USD/SGD/EUR/GBP) next to the mode toggle
- [x] **FORM-07**: Leaving all value fields blank in either mode falls back to equal-weight allocation
- [x] **FORM-08**: "Analyze Stocks" button relabelled to "▶ Run Analysis" and presented in a prominent hero layout

### Auto Analysis

- [x] **AUTO-01**: After scrape completes, Regime Detection runs automatically for each ticker using a 2-year window
- [x] **AUTO-02**: After scrape completes, Portfolio MDP runs automatically (skipped gracefully for single-ticker input)
- [x] **AUTO-03**: Analytics tab shows per-module status badges ("⏳ Running…" → "✓ Done" / "⚠ Failed")
- [x] **AUTO-04**: Auto-run regime results render inline in Analytics sub-tab (charts via existing Plotly helpers)
- [x] **AUTO-05**: Auto-run Portfolio MDP policy output renders inline in Analytics sub-tab

### Portfolio Health Card

- [x] **HEALTH-01**: A "Portfolio Health" card appears above the tab nav in results showing VaR (95%), Sharpe ratio, and regime per ticker
- [x] **HEALTH-02**: Each metric in the health card links/jumps to its relevant analytics tab section
- [x] **HEALTH-03**: Health card shows available metrics only when fewer tickers are submitted (no correlation/PCA for single ticker)

## Out of Scope

| Feature | Reason |
|---------|--------|
| User authentication | Showcase app, not multi-user platform |
| Mobile app / responsive design | Web-first, desktop demo context |
| Real-time market data feeds | Static/fetched data sufficient for demos |
| QuantLib / hmmlearn / ta-lib | Black-box libraries defeat the showcase purpose |
| Production hardening (rate limiting, auth, etc.) | Academic demo context |
| Options Pricing auto-run | Requires strike and maturity — user-specific params |
| Volatility Surface auto-run | Requires date range selection — keep as manual tab |
| CIR/Vasicek auto-run | Need rate model params — keep as manual tab |
| RL training auto-run | Needs hyperparameter selection — keep as manual tab |

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
| FORM-01 | Phase 6: Form Streamlining & Smart Defaults | Complete |
| FORM-02 | Phase 6: Form Streamlining & Smart Defaults | Complete |
| FORM-03 | Phase 6: Form Streamlining & Smart Defaults | Complete |
| FORM-04 | Phase 6: Form Streamlining & Smart Defaults | Complete |
| FORM-05 | Phase 6: Form Streamlining & Smart Defaults | Complete |
| FORM-06 | Phase 6: Form Streamlining & Smart Defaults | Complete |
| FORM-07 | Phase 6: Form Streamlining & Smart Defaults | Complete |
| FORM-08 | Phase 6: Form Streamlining & Smart Defaults | Complete |
| AUTO-01 | Phase 7: Auto-Run Extended Analysis | Complete |
| AUTO-02 | Phase 7: Auto-Run Extended Analysis | Complete |
| AUTO-03 | Phase 7: Auto-Run Extended Analysis | Complete |
| AUTO-04 | Phase 7: Auto-Run Extended Analysis | Complete |
| AUTO-05 | Phase 7: Auto-Run Extended Analysis | Complete |
| HEALTH-01 | Phase 8: Portfolio Health Summary Card | Complete |
| HEALTH-02 | Phase 9: Health Card Deep-Links & Auto-Run Hardening | Complete |
| HEALTH-03 | Phase 8: Portfolio Health Summary Card | Complete |

**Coverage:**
- v1 requirements: 40 total — all Complete
- v2 requirements: 16 total (FORM: 8, AUTO: 5, HEALTH: 3)
- Mapped to phases: 16
- Unmapped: 0 ✓
- Gap closure: HEALTH-02 reassigned to Phase 9

---

## v2.1 Requirements (Milestone v2.1 — Active)

**Milestone:** v2.1 Deeper Stock Analysis
**Goal:** Expand each stock card with a "Deep Analysis" group containing four new analysis modules.

### Financial Health Score

- [x] **FHLTH-01**: User can see a composite financial health grade (A–F) for each ticker on its stock card
- [x] **FHLTH-02**: User can see the four component sub-scores (liquidity, leverage, profitability, growth) that make up the overall grade
- [x] **FHLTH-03**: User can see a brief explanation of what drove the grade (e.g., "strong ROE offset by high debt/equity")
- [x] **FHLTH-04**: Score degrades gracefully when any single component is missing — partial score shown with a warning flag

### Earnings Quality

- [x] **QUAL-01**: User can see an earnings quality label (High / Medium / Low) for each ticker
- [x] **QUAL-02**: User can see the accruals ratio (Net Income − OCF) / Total Assets displayed numerically
- [x] **QUAL-03**: User can see the cash conversion ratio (OCF / Net Income) displayed numerically
- [x] **QUAL-04**: User can see an earnings consistency flag (Consistent / Volatile) based on EPS growth stability
- [x] **QUAL-05**: Quality label degrades gracefully to "Insufficient Data" when OCF or Net Income is unavailable

### DCF Valuation

- [x] **DCF-01**: User can see an intrinsic value estimate (price per share) derived from FCF
- [x] **DCF-02**: User can see whether the stock is trading at a premium or discount vs. the DCF estimate, expressed as a percentage
- [x] **DCF-03**: User can see the key assumptions (FCF growth rate, terminal growth rate, WACC) displayed alongside the estimate
- [x] **DCF-04**: User can override default growth and WACC assumptions via input fields and recalculate without re-scraping
- [x] **DCF-05**: Module displays "DCF unavailable — FCF data missing" if Alpha Vantage FCF is absent or zero

### Peer Comparison

- [x] **PEER-01**: User can see the ticker's P/E, P/B, ROE, and operating margin ranked as a percentile against 5–10 sector peers
- [x] **PEER-02**: User can see which sector peer group was used (e.g., "Technology — comparable group")
- [x] **PEER-03**: User can see a visual above/below-median indicator for each of the four metrics
- [x] **PEER-04**: User can toggle a "Show peers" control to reveal the raw peer data table
- [x] **PEER-05**: Module displays "Peer data unavailable" and hides percentile rows if Finviz peer fetch fails or times out

## v2.1 Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FHLTH-01 | Phase 13: Financial Health Score | Complete |
| FHLTH-02 | Phase 13: Financial Health Score | Complete |
| FHLTH-03 | Phase 13: Financial Health Score | Complete |
| FHLTH-04 | Phase 13: Financial Health Score | Complete |
| QUAL-01 | Phase 14: Earnings Quality | Complete |
| QUAL-02 | Phase 14: Earnings Quality | Complete |
| QUAL-03 | Phase 14: Earnings Quality | Complete |
| QUAL-04 | Phase 14: Earnings Quality | Complete |
| QUAL-05 | Phase 14: Earnings Quality | Complete |
| DCF-01 | Phase 15: DCF Valuation | Complete |
| DCF-02 | Phase 17: Bug Fixes — Re-scrape & DCF Badge | Complete |
| DCF-03 | Phase 15: DCF Valuation | Complete |
| DCF-04 | Phase 17: Bug Fixes — Re-scrape & DCF Badge | Complete |
| DCF-05 | Phase 15: DCF Valuation | Complete |
| PEER-01 | Phase 17: Bug Fixes — Re-scrape & DCF Badge | Complete |
| PEER-02 | Phase 17: Bug Fixes — Re-scrape & DCF Badge | Complete |
| PEER-03 | Phase 16: Peer Comparison | Complete |
| PEER-04 | Phase 17: Bug Fixes — Re-scrape & DCF Badge | Complete |
| PEER-05 | Phase 17: Bug Fixes — Re-scrape & DCF Badge | Complete |

**v2.1 Coverage:**
- v2.1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0 ✓
- Gap closure: DCF-02, DCF-04, PEER-01, PEER-02, PEER-04, PEER-05 reassigned to Phase 17

---

## v2.2 Requirements (Milestone v2.2 — Active)

**Milestone:** v2.2 Trading Indicators
**Goal:** Add a Trading Indicators fourth tab showing per-ticker 2×2 indicator grid (Liquidity Sweep, Order Flow, Anchored VWAP, Volume Profile) with a composite bias signal.

### Liquidity Sweep

- [ ] **SWEEP-01**: User sees a Bullish Sweep, Bearish Sweep, or No Sweep signal label for each ticker, derived from swing high/low detection with a lookback-adaptive n-bar window
- [ ] **SWEEP-02**: Sweep detection n scales automatically with selected lookback (n=2 for 30d, n=3 for 90d, n=5 for 180d+); if zero swings are detected the panel displays "No confirmed swings in selected window (n=X)"
- [ ] **SWEEP-03**: Plotly scatter markers appear on sweep candles and dashed horizontal lines are drawn at swept price levels on the Liquidity Sweep chart

### Order Flow

- [ ] **FLOW-01**: User sees a green/red buy/sell pressure delta bar chart with a cumulative delta overlay line for each ticker, computed from the (Close−Low)/(High−Low)×Volume proxy with epsilon guard on zero-range bars
- [ ] **FLOW-02**: A volume divergence flag with displayed price-slope and volume-slope values appears when rolling-window trend directions diverge over a 10-bar window
- [ ] **FLOW-03**: Imbalance candles (body > 70% of high-low range AND volume > 1.2× 20-day average) are annotated on the Order Flow chart with Bullish/Bearish labels

### Anchored VWAP

- [ ] **AVWAP-01**: User sees two AVWAP lines anchored to the 52-week high date and 52-week low date, overlaid on the price chart, with current price vs. each AVWAP reported as a sub-signal
- [ ] **AVWAP-02**: A third AVWAP line anchored to the last earnings date is computed and displayed when available; if unavailable the panel notes "Earnings anchor unavailable" without crashing the other two lines
- [ ] **AVWAP-03**: Each AVWAP line shows a right-edge distance label (e.g. "+2.1% above AVWAP"); when any two lines are within 0.3% of current price a convergence note is shown

### Volume Profile

- [ ] **VPROF-01**: User sees a horizontal volume histogram with POC (Point of Control), VAH, and VAL displayed as visible filled levels (not hairlines) and a shaded 70% value area zone
- [ ] **VPROF-02**: A badge indicates whether the current price is inside or outside the value area
- [ ] **VPROF-03**: Bin count adapts to price range (targeting ~0.2% bin width); bin width in USD is reported in the chart metadata

### Composite Bias Signal

- [ ] **BIAS-01**: Each ticker card shows a Bullish / Bearish / Neutral composite bias badge with a one-line rationale that identifies which sub-indicator dissents from the majority
- [ ] **BIAS-02**: The composite card is labeled "Trend-following bias" with a caveat that all indicators share the same OHLCV data source
- [ ] **BIAS-03**: Failed sub-indicators show a grey "unavailable" state; the composite denominator counts only successfully computed modules (e.g., "3/4 indicators" if one fails)

### Tab & UX

- [ ] **TIND-01**: A "Trading Indicators" fourth tab renders a 2×2 Plotly grid per scraped ticker, lazy-loaded on tab activation; `TradingIndicators.clearSession()` is called on re-scrape
- [ ] **TIND-02**: A lookback dropdown (30/90/180/365 days) is visible in the tab; changing the value clears the session cache and re-fetches all tickers
- [ ] **TIND-03**: All Trading Indicator Plotly charts render with `staticPlot: true` to prevent memory pressure when multiple tickers are loaded

## v2.2 Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SWEEP-01 | Phase 22: Liquidity Sweep + Composite Bias + Tab Wiring | Pending |
| SWEEP-02 | Phase 22: Liquidity Sweep + Composite Bias + Tab Wiring | Pending |
| SWEEP-03 | Phase 22: Liquidity Sweep + Composite Bias + Tab Wiring | Pending |
| FLOW-01 | Phase 21: Order Flow | Pending |
| FLOW-02 | Phase 21: Order Flow | Pending |
| FLOW-03 | Phase 21: Order Flow | Pending |
| AVWAP-01 | Phase 20: Anchored VWAP | Pending |
| AVWAP-02 | Phase 20: Anchored VWAP | Pending |
| AVWAP-03 | Phase 20: Anchored VWAP | Pending |
| VPROF-01 | Phase 19: Volume Profile | Pending |
| VPROF-02 | Phase 19: Volume Profile | Pending |
| VPROF-03 | Phase 19: Volume Profile | Pending |
| BIAS-01 | Phase 22: Liquidity Sweep + Composite Bias + Tab Wiring | Pending |
| BIAS-02 | Phase 22: Liquidity Sweep + Composite Bias + Tab Wiring | Pending |
| BIAS-03 | Phase 22: Liquidity Sweep + Composite Bias + Tab Wiring | Pending |
| TIND-01 | Phase 22: Liquidity Sweep + Composite Bias + Tab Wiring | Pending |
| TIND-02 | Phase 22: Liquidity Sweep + Composite Bias + Tab Wiring | Pending |
| TIND-03 | Phase 22: Liquidity Sweep + Composite Bias + Tab Wiring | Pending |

**v2.2 Coverage:**
- v2.2 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0 ✓
- Phase 18 (Backend Scaffold) is an infrastructure phase with no direct REQ-IDs; it unblocks all 18 requirements

---
*Requirements defined: 2026-03-03*
*Last updated: 2026-04-08 — v2.2 roadmap created, all 18 requirements mapped to phases 19–22*
