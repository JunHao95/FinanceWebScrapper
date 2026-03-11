---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: milestone
status: Roadmap defined; awaiting plan-phase for Phase 6
stopped_at: Completed 09-01-PLAN.md — Phase 9 and v2.0 milestone complete
last_updated: "2026-03-11T05:51:08.549Z"
last_activity: 2026-03-08 — Roadmap for v2.0 (phases 6-8) created
progress:
  total_phases: 9
  completed_phases: 9
  total_plans: 21
  completed_plans: 21
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-08)

**Core value:** Every completed MFE module becomes a working, interactive demo that a recruiter can run and a peer can learn from.
**Current focus:** Phase 6 — Form Streamlining & Smart Defaults (v2.0 milestone start)

## Current Position

Phase: Phase 6 — Form Streamlining & Smart Defaults (not yet started)
Plan: —
Status: Roadmap defined; awaiting plan-phase for Phase 6
Last activity: 2026-03-08 — Roadmap for v2.0 (phases 6-8) created

Progress: [░░░░░░░░░░] 0%  (v2.0 phases: 0 of 3 complete)

## Performance Metrics

**Velocity (v1.0 history):**
- Total plans completed: 14
- Average duration: ~4 min
- Total execution time: ~56 min

**By Phase (v1.0):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-math-correctness | 3 | ~9 min | ~3 min |
| 02-backend-completeness | 4 | ~20 min | ~5 min |
| 03-frontend-wiring | 5 | ~20 min | ~4 min |
| 04-ml-in-finance-module | 1 | ~5 min | ~5 min |
| 05-stochastic-models-ui-completion | 1 | ~8 min | ~8 min |

**Recent Trend:**
- Last 5 plans: 03-05 (~5 min), 04-01 (~5 min), 05-01 (~8 min)
- Trend: Stable

*Updated after each plan completion*
| Phase 03-frontend-wiring P02 | 8 | 2 tasks | 3 files |
| Phase 03-frontend-wiring P01 | 15 | 2 tasks | 3 files |
| Phase 02-backend-completeness P02 | 5 | 2 tasks | 3 files |
| Phase 02-backend-completeness P01 | 5 | 2 tasks | 2 files |
| Phase 01-math-correctness P02 | 3 | 2 tasks | 4 files |
| Phase 01-math-correctness P01 | 6 | 2 tasks | 4 files |
| Phase 01-math-correctness P03 | 3 | 2 tasks | 9 files |
| Phase 02-backend-completeness P04 | 2 | 2 tasks | 2 files |
| Phase 03-frontend-wiring P04 | 3 | 1 tasks | 2 files |
| Phase 03-frontend-wiring P03 | 4 | 2 tasks | 4 files |
| Phase 03-frontend-wiring P05 | 5 | 1 tasks | 1 files |
| Phase 04-ml-in-finance-module P01 | 5 | 1 tasks | 1 files |
| Phase 05-stochastic-models-ui-completion P01 | 8 | 2 tasks | 2 files |
| Phase 06-form-streamlining-smart-defaults P01 | 2 | 2 tasks | 2 files |
| Phase 06-form-streamlining-smart-defaults P02 | 3 | 2 tasks | 1 files |
| Phase 07-auto-run-extended-analysis-after-scrape P01 | 4 | 2 tasks | 2 files |
| Phase 07-auto-run-extended-analysis-after-scrape P02 | 2 | 1 tasks | 1 files |
| Phase 08-portfolio-health-summary-card P01 | 6 | 2 tasks | 2 files |
| Phase 08-portfolio-health-summary-card P02 | 52 | 3 tasks | 4 files |
| Phase 09-health-card-deep-links-and-auto-run-hardening P01 | 30 | 3 tasks | 7 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Phase 02-02]: Vasicek feller_ratio returns None (not a number) — Vasicek allows negative rates so Feller condition does not apply
- [Phase 02-02]: Route dispatch uses data.get('model','cir').lower() — backward-compatible; missing model field defaults to CIR
- [Phase 02-02]: vasicek_yield_curve mirrors cir_yield_curve signature exactly for Phase 3 frontend wiring compatibility
- [Phase 02-01]: Absorption detection threshold P[i,i] > 0.9999 and row_sum within 1e-6; linalg.solve for B, linalg.inv for N display
- [Phase 02-01]: Power iteration fallback for steady-state when eigenvector imaginary part exceeds 1e-6
- [Phase 02-01]: MDP gamma capped at 0.999, n_periods capped at 10000 as guard inputs; symmetric reward matrix encodes regime-aligned portfolio incentives
- [Roadmap]: Fix math correctness before frontend wiring — wiring UI to incorrect backends wastes all subsequent work and produces recruiter-visible failures
- [Roadmap]: MDP scope is unresolved — whether MARKOV-04/MARKOV-05 (MDP) belong in Phase 2 or are deferred to v2 should be decided before Phase 2 planning begins
- [Roadmap]: Calibration progress strategy (SSE streaming vs. pre-cached demo results) should be decided during Phase 2 planning, as it affects Phase 3 implementation
- [Init]: YOLO mode, Standard depth, parallel execution enabled; all 3 workflow agents active
- [Phase 01-math-correctness]: Relative MSE for Heston calibration normalises OTM/ITM options equally; 0.50 filter prevents near-zero numerical issues
- [Phase 01-math-correctness]: HMM dual-criterion labelling: sigma primary, mu secondary, 20% separation guard; AMBIGUOUS confidence forces NEUTRAL signal
- [Phase 01-math-correctness]: MATH-01: Par bond requires both coupon discounting AND principal discounting in state_bond_values; used continuous-discounting annuity PV formula
- [Phase 01-math-correctness]: MATH-03: CIR Feller guaranteed by construction via alpha reparameterisation: kappa=sigma^2/(2*theta)+exp(alpha) always satisfies Feller condition
- [Phase 01-math-correctness]: MATH-05: Fourier put-call parity holds within S*1e-4; BS convergence confirmed with sigma_v=0.001; intrinsic floor validated across 7 strikes
- [Phase 01-math-correctness]: Test strategy: black_scholes module-level wrapper added to options_pricer.py; slow marker isolates network-dependent SPY test from CI fast runs
- [Phase 02-04]: Mode dispatch uses data.get('mode','steady_state') — defaults to steady_state when mode missing
- [Phase 02-04]: nstep mode returns both transition_matrix_n AND term_structure in single response per plan spec
- [Phase 02-04]: Test assertions use horizon_years/cumulative_default_prob — actual credit_transitions output keys
- [Phase 03-01]: Retain backward-compatible 'regime' nested field in API response while adding flat dates/prices/regime_sequence/filtered_probs fields
- [Phase 03-01]: Identify stressed column in filtered_probs_full by comparing last row to current_probabilities.stressed value — avoids hardcoding internal state index
- [Phase 03-01]: regime_sequence derived as [1 if p >= 0.5 else 0 for p in filtered_probs_stressed] per plan spec
- [Phase 03-01]: Replace regimeDays input with start/end date pickers for precise date range control
- [Phase 03-02]: runHestonPricing sends spot/strike/maturity/risk_free_rate to /api/heston_price (not S/K/T/r) to match existing route field names
- [Phase 03-02]: /api/heston_iv_surface iv_grid shape is T_steps x K_steps; brentq back-solves IV floored at 0.001, capped at 2.0
- [Phase 03-04]: Inline RMSE quality label (Good/Acceptable/Poor) instead of calling rmseLabel helper — not defined in scope; plan already flagged it as optional fallback
- [Phase 03-03]: calibrate_stream buffers all SSE events then emits post-calibration (batch-emit) to avoid async server requirement on Render free tier
- [Phase 03-03]: IV inversion uses bisection over [1e-4, 5.0] — more robust than Newton-Raphson for edge cases
- [Phase 03-03]: Final chart data fetched from /api/calibrate_heston POST after SSE done event — keeps SSE route thin
- [Phase 03-05]: Markov heatmap fetched via secondary /api/markov_chain nstep n=1 call inside runCreditRisk — no separate Markov sub-tab needed
- [Phase 03-05]: Yield curve chart uses pt.spot_rate * 100 from yield_curve array — matches actual /api/interest_rate_model response field shape
- [Phase 04-01]: No rlModels.js script tag added — already present at line 1588 of index.html
- [Phase 04-01]: RL sub-tab IDs follow pattern rlTab_<name> for buttons and rlContent_<name> for content divs
- [Phase 05-01]: stochContent_markov uses selector-driven tab switching — switchStochasticTab finds div by pattern, no hardcoded reference needed in HTML
- [Phase 05-01]: cirModel select added before calibrate checkbox; updateCIRDefaults swaps kappa/theta/sigma defaults on model change
- [Phase 06-01]: equalWeightsHint hidden by default in HTML; JS toggles to block on totalValue===0 in value mode, hides in percent mode
- [Phase 06-01]: defaultsNote starts visible (display:block) as Advanced Settings collapsed by default; toggle event hides on open
- [Phase 06-02]: flex-direction:column + align-items:stretch on #scrapeForm .button-group stacks buttons vertically so width:100% on Run Analysis fills the column without displacing Clear
- [Phase 06-02]: #scrapeForm .button-group selector scopes the flex-direction layout change to only the scrape form, leaving other .button-group instances untouched
- [Phase 07-01]: autoRun.js uses Promise.allSettled for parallel regime calls with isolated per-ticker error handling
- [Phase 07-01]: MDP block conditional on tickers.length >= 2 — single-ticker scrape silently skips it
- [Phase 07-01]: Container IDs namespaced with auto prefix to prevent collision with manual Stochastic Models tab
- [Phase 07-02]: Tab switches to analytics (not stocks) after scrape so user sees live badge updates without manual navigation
- [Phase 08-01]: Import pandas as pd locally inside /api/portfolio_sharpe route body — consistent with existing local-import pattern in webapp.py lines 1323 and 1353
- [Phase 08-02]: PortfolioHealth.initCard called synchronously before AutoRun.triggerAutoRun() so card is visible before regime badges start updating
- [Phase 08-02]: Regime label derived from filtered_probs last value >= 0.5 threshold — consistent with autoRun.js convention
- [Phase 08-02]: updateRegime(ticker, null) called in catch branch so failed tickers show dash instead of staying on Analyzing...
- [Phase 09-01]: analyticsVarSection ID placed on portfolio-level Monte Carlo wrapper to avoid per-ticker ID collision
- [Phase 09-01]: yf.Ticker().history() replaces yf.download() to fix concurrent-download shape corruption (2D vs 1D DataFrame)
- [Phase 09-01]: _esc/_alert guard locals defined before try block in runAutoMDP so catch block can access them without ReferenceError

### Pending Todos

- Plan Phase 6: Form Streamlining & Smart Defaults (FORM-01..08)

### Blockers/Concerns

- [Phase 2]: MDP backend resolved — portfolio_mdp_value_iteration implemented in plan 02-01; blocker cleared
- [Phase 3]: Calibration latency on Render free tier unconfirmed (estimated 60-120s) — measure during Phase 1 to choose between SSE streaming vs. pre-caching

## Session Continuity

Last session: 2026-03-11T05:51:08.539Z
Stopped at: Completed 09-01-PLAN.md — Phase 9 and v2.0 milestone complete
Resume file: None
