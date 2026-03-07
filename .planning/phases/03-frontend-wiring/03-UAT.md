---
status: complete
phase: 03-frontend-wiring
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md, 03-05-SUMMARY.md]
started: 2026-03-07T00:00:00Z
updated: 2026-03-08T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Regime Detection Charts
expected: Navigate to Stochastic Models > Regime Detection sub-tab. You should see Start Date and End Date pickers (not a "Days" input). Enter SPY, 2019-01-01 to 2021-12-31, click Run. Two Plotly charts render: P(Stressed) area chart on top, and a price chart below with red shading over Q1 2020.
result: pass

### 2. Heston Pricing — Price Cards
expected: Navigate to Heston Pricing sub-tab. Confirm 9 parameter inputs are present (S, K, T, r, v0, kappa, theta, sigma_v, rho) plus an option type selector. Click "Price Option". Two color-coded cards appear: a green Heston price card and a blue Black-Scholes price card, each showing a numerical value.
result: issue
reported: "S=100 K=100 T=1 r=0.05 v0=0.04 kappa=2 theta=0.04 sigma_v=0.3 rho=-0.7 — Heston price=68.3566 vs BS=14.2313. With standard equity Heston params (rho=-0.7) and 20% vol ATM 1yr call, Heston should be ~$10-12 close to BS. Price is catastrophically wrong; BS also slightly high (~10.44 expected)."
severity: blocker

### 3. Heston Pricing — 3D IV Surface
expected: After clicking Price Option (same run as above), a 3D Plotly surface chart appears below the price cards showing the implied volatility smile. The surface should be non-flat — with default rho=-0.7, IV should visibly decrease from low to high strikes (leverage effect).
result: issue
reported: "Surface renders but is a completely flat yellow plateau — all cells capped at ~2.0 IV (200%). brentq back-solver hitting upper bound everywhere because Heston prices are too high to invert. Same root cause as test 2."
severity: blocker

### 4. Heston Calibration — Live Progress
expected: Navigate to Heston Calibration sub-tab. Click Calibrate. While calibration runs, a live iteration counter appears in the progress area and increments (e.g., "Iteration 10... 20... 30..."). It should not be a frozen spinner — iterations should be visible.
result: issue
reported: "Iteration counter only visible in backend (server logs), not on the frontend. Page shows no progress during calibration — SSE EventSource updates are not rendering in the calibProgress div."
severity: major

### 5. Heston Calibration — RMSE Badge + IV Chart
expected: After calibration completes, an RMSE badge appears labeled "Good", "Acceptable", or "Poor" with appropriate color coding (green/amber/red). Below it, a Plotly scatter chart shows Market IV as markers and Fitted IV as a smooth line through the strikes (sorted by strike, not zigzagging).
result: issue
reported: "RMSE badge renders correctly (red Poor 33.12%). IV chart renders but Fitted IV draws separate horizontal segments instead of a smooth curve — line connects points in array order across maturity groups rather than sorted by strike, causing zigzag/crossing lines pattern."
severity: major

### 6. BCC Calibration
expected: Navigate to BCC Calibration sub-tab. It should have ticker, risk-free rate, and option type inputs. Click Calibrate. Three things appear: (1) an RMSE quality badge (Good/Acceptable/Poor), (2) a parameter table showing calibrated BCC params, and (3) a two-trace Plotly chart with Market IV as scatter markers and BCC Fitted IV as a line.
result: issue
reported: "RMSE badge (Poor 127.20%) and parameter table render. IV chart did not render at all. Parameters are degenerate: kappa=20 and sigma_v=2.0 both at optimizer bounds, RMSE=127% — calibration failed to find meaningful minimum. Same root cause as Heston math bug (BCC uses Heston characteristic function internally)."
severity: blocker

### 7. CIR/Vasicek Yield Curve
expected: Navigate to the CIR/Vasicek (Interest Rate) sub-tab. Enter parameters and click Run. A Plotly line chart of the yield curve appears. A Feller condition badge is visible — green if the condition 2*kappa*theta > sigma^2 is satisfied, red if not.
result: pass

### 8. Credit Risk Charts
expected: Navigate to the Credit Risk sub-tab. Enter parameters and click Run. Three visualizations appear below any existing metric cards: (1) a cumulative default probability term structure line chart, (2) a survival curve area chart (filled to zero), and (3) an S&P transition matrix heatmap in Blues colorscale.
result: pass

## Summary

total: 8
passed: 3
issues: 5
pending: 0
skipped: 0

## Gaps

- truth: "Heston price and BS price for ATM call (S=100,K=100,T=1,r=0.05,v0=0.04,kappa=2,theta=0.04,sigma_v=0.3,rho=-0.7) should both be approximately $10-12"
  status: failed
  reason: "User reported: Heston=68.3566 vs BS=14.2313 — standard equity Heston parameters (rho=-0.7) returning catastrophically wrong price; BS also elevated vs ~10.44 theoretical. Likely Fourier characteristic function branch-cut error or integration bounds issue."
  severity: blocker
  test: 2
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "3D IV surface should show non-flat smile shape — IV decreasing from low to high strikes (leverage effect) with rho=-0.7"
  status: failed
  reason: "User reported: flat yellow plateau across entire surface — all cells capped at ~2.0 IV. brentq back-solver hitting upper cap everywhere because underlying Heston prices are too high to invert."
  severity: blocker
  test: 3
  root_cause: "Same as test 2 — broken Heston Fourier pricer propagates to IV surface"
  artifacts: []
  missing: []
  debug_session: ""

- truth: "SSE EventSource should display iteration counter in calibProgress div while Heston calibration runs"
  status: failed
  reason: "User reported: iteration counter only visible in backend server logs, not on frontend. Page shows no progress during calibration."
  severity: major
  test: 4
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Fitted IV line in Heston Calibration chart should be a smooth curve sorted by strike"
  status: failed
  reason: "User reported via screenshot: Fitted IV draws separate horizontal segments — line connects points in array order across maturity groups, causing zigzag/crossing lines pattern instead of a smooth curve."
  severity: major
  test: 5
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "BCC Calibration should render RMSE badge, parameter table, and Market IV vs Fitted IV chart"
  status: failed
  reason: "User reported: RMSE badge and parameter table render, but IV chart did not render. Parameters degenerate (kappa=20, sigma_v=2.0 at bounds, RMSE=127%) — calibration failed. Root cause same as Heston math bug: BCC uses Heston characteristic function internally."
  severity: blocker
  test: 6
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
