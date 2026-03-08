---
status: resolved
trigger: "Heston characteristic function / Fourier pricer returns catastrophically wrong prices"
created: 2026-03-08T00:00:00Z
updated: 2026-03-08T00:05:00Z
---

## Current Focus

hypothesis: CONFIRMED (both issues) — (1) IV chart zigzag: mode:'markers' fix WAS already applied in JS but browser served cached JS; fix: added ?v=2 cache-buster to script tag. (2) Calibration degenerate kappa=20/sigma_v=2: scipy.fmin had no bounds enforcement so optimizer wandered into degenerate regions then got hard-clipped to a bad parameter set; fix: switch to bounded minimize(), tighten FMIN_BOUNDS_HIGH, add Feller penalty, clip inside objective.
test: Both fixes applied. Browser must hard-reload to pick up new JS.
expecting: IV charts show scatter dots (no zigzag). Calibration returns kappa in [0.5, 8] range, sigma_v in [0.1, 0.8] range, RMSE under 15%.
next_action: await human verification

## Symptoms

expected: ATM call should price at ~$10-12. IV surface shows non-flat smile. BCC converges.
actual: Heston=$68.36, BS=$14.23, flat IV surface (all ~2.0=200%), BCC degenerate (kappa=20, sigma_v=2.0).
errors: No exceptions — wrong numerical results.
reproduction: Stochastic Models > Heston Pricing sub-tab, default params S=100 K=100 T=1 r=0.05 v0=0.04 kappa=2 theta=0.04 sigma_v=0.3 rho=-0.7.
started: First-run UAT — never worked correctly.

## Eliminated

- hypothesis: Bug in Fourier characteristic function (branch-cut, sign error, wrong formula)
  evidence: Direct Python test heston_price(100,100,1,0.05,0.04,2,0.04,0.3,-0.7,'call')=10.394 — correct
  timestamp: 2026-03-08T00:01:00Z

- hypothesis: Webapp route passes wrong parameter order
  evidence: Route uses keyword arguments and reads correct JSON fields
  timestamp: 2026-03-08T00:01:00Z

- hypothesis: BS price formula wrong
  evidence: BS comparison correctly uses sqrt(v0) as sigma, gives 10.45 — correct
  timestamp: 2026-03-08T00:01:00Z

- hypothesis: mode:'markers' not yet applied in stochasticModels.js
  evidence: grep confirms mode:'markers' at lines 267, 272 (Heston) and 874, 879 (BCC) — fix was already present. The zigzag was from browser cache serving old JS.
  timestamp: 2026-03-08T00:05:00Z

- hypothesis: BCC RMSE=127% is purely a jump parameter issue unrelated to Heston
  evidence: BCC inherits degenerate Heston params (kappa=20, sigma_v=2) from unconstrained Heston calibration first, so fixing Heston calibration fixes the BCC starting point too.
  timestamp: 2026-03-08T00:05:00Z

## Evidence

- timestamp: 2026-03-08T00:00:30Z
  checked: fourier_pricer.py heston_price() with UAT params
  found: Returns $10.394 — correct answer
  implication: Backend pricer is fine

- timestamp: 2026-03-08T00:00:45Z
  checked: webapp.py /api/heston_price route
  found: Correctly passes keyword args to heston_price(); uses sqrt(v0) for BS comparison
  implication: Backend route is fine

- timestamp: 2026-03-08T00:01:00Z
  checked: templates/index.html — Stochastic Models Heston Pricing sub-tab IDs vs JS reads in runHestonPricing()
  found: HTML (committed version) used hestonV0/hestonKappa/hestonTheta/hestonSigmaV/hestonRho — same IDs as Options Pricing tab form. Options Pricing tab's hestonTheta=4 (in %²), hestonV0=4. getElementById on first match picks up Options Pricing tab values. runHestonPricing() does NOT divide by 100. So v0=4.0, theta=4.0 sent to backend → $68.36 exactly matches.
  implication: Root cause found — DOM ID collision causing wrong parameter values

- timestamp: 2026-03-08T00:01:30Z
  checked: git diff HEAD -- templates/index.html and static/js/stochasticModels.js
  found: Working tree already has partial fix — HTML IDs renamed to hestonPriceV0/hestonPriceKappa/hestonPriceTheta/hestonPriceSigmaV/hestonPriceRho; JS updated to match
  implication: Blocker fix already in working tree (unstaged). Still need to verify completeness and fix Issues 4 and 5.

- timestamp: 2026-03-08T00:02:00Z
  checked: Issue 4 — SSE iteration counter rendering
  found: calibProgress div exists, JS correctly sets style.display='block' and textContent. If Nelder-Mead converges with 0 iterations (brute result is optimal), lastIteration=0 and counter never updates with meaningful values. Also, SSE buffering could cause all events to arrive at once.
  implication: Secondary issue — counter may show 0 if Nelder-Mead does no iterations. Structural rendering is correct.

- timestamp: 2026-03-08T00:02:30Z
  checked: Issue 5 — Fitted IV chart zigzag
  found: Chart uses mode:'lines+markers' for fitted_ivs. Data includes multiple maturities sorted only by strike (not by maturity+strike). Two contracts at same strike but different maturities appear at same x with different y — line connects them vertically → zigzag.
  implication: Fix: change fitted IV trace to mode:'markers' to eliminate cross-maturity line zigzag. Alternative: separate traces per maturity.

- timestamp: 2026-03-08T00:05:00Z
  checked: stochasticModels.js lines 263-282 (Heston calib chart) and 870-889 (BCC calib chart)
  found: Both already have mode:'markers'. Bug was browser cache. Added ?v=2 query string to script tag in index.html to force cache bypass.
  implication: No JS code change needed. Cache-buster sufficient.

- timestamp: 2026-03-08T00:05:00Z
  checked: model_calibration.py HestonCalibrator — FMIN_BOUNDS_HIGH and fmin() call
  found: FMIN_BOUNDS_HIGH had kappa_max=20, sigma_v_max=2.0. scipy.fmin has NO bounds — optimizer roams freely, returns params outside bounds, then hard-clipping snaps them to the max boundary values (kappa=20, sigma_v=2). That hard-clipped point is not a minimum of the objective — it's an artifact of post-hoc clipping.
  implication: Root cause of degenerate calibration. Fix: use scipy.optimize.minimize with method='Nelder-Mead' and bounds= (supported since scipy 1.7; installed scipy=1.15.3). Also tighten bounds (kappa_max=10, sigma_v_max=1.0) and add Feller penalty inside objective.

## Resolution

root_cause: |
  Issue 1 (IV zigzag): mode:'markers' fix was correctly in JS but browser served cached file.
  Issue 2 (degenerate calibration): scipy.fmin has no bounds enforcement. Optimizer freely roamed to kappa≈25, sigma_v≈2.5 (degenerate region where Feller is violated and the characteristic function has numerical issues), then params were hard-clipped to the boundary values kappa=20, sigma_v=2.0 — which is not a minimum. Two contributing factors: (a) no bounds in optimizer, (b) no Feller condition penalty to steer away from the degenerate region.

fix: |
  1. templates/index.html: Added ?v=2 cache-buster to stochasticModels.js script tag.
  2. model_calibration.py HestonCalibrator:
     - Tightened FMIN_BOUNDS_HIGH: kappa 20→10, sigma_v 2.0→1.0, theta 2.0→1.0, v0 2.0→1.0
     - Tightened BRUTE_RANGES: kappa step 2.5→2.0, sigma_v max 1.0→0.8 step 0.25→0.20
     - Added np.clip() inside mse_fn so optimizer sees smooth boundary landscape
     - Added Feller soft penalty: base_mse + 0.5 * max(0, sigma_v^2 - 2*kappa*theta)
     - Switched from fmin() to minimize(method='Nelder-Mead', bounds=...) with hard bounds during optimization
  3. model_calibration.py BCCCalibrator:
     - Same bounded minimize() for jump parameters
     - Changed jump_mse to use relative MSE (matching Heston) instead of absolute MSE
     - Tightened JUMP_BOUNDS_HIGH: lambda 20→10, delta_j 2.0→1.0

verification: |
  Python import check passed (no syntax errors).
  Human verified 2026-03-08: all 5 UAT issues confirmed fixed.
  - Heston pricing: $68 → $10.39 (DOM ID collision resolved)
  - BS sigma: fixed to use sqrt(v0)
  - BCC endpoint: IV response fields added
  - Calibration RMSE: Heston 33%→8%, BCC 127%→8% (bounded minimize + Feller penalty)
  - IV scatter chart: cache-busted with ?v=2, mode:'markers' rendering correctly

resolved: 2026-03-08T00:10:00Z
resolved_by: human_verification

files_changed:
  - templates/index.html (cache-buster ?v=2 on stochasticModels.js)
  - src/derivatives/model_calibration.py (bounded optimizer, Feller penalty, tighter bounds)
