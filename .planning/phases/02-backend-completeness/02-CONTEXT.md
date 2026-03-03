# Phase 2: Backend Completeness - Context

**Gathered:** 2026-03-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Close backend gaps so every planned stochastic feature has a callable Python function and a Flask route. No new UI. No frontend wiring. Every success criterion is testable via `curl` or `pytest` alone. Phase 3 picks up from here and wires everything to the browser.

Specific gaps to close:
1. `/api/markov_chain` — new unified endpoint for Markov chain operations (steady-state, absorption, n-step, MDP)
2. `/api/calibrate_bcc` — new Flask route wrapping the existing `BCCCalibrator` class
3. Vasicek model backend + extend `/api/interest_rate_model` with `model` selector
4. `feller_ratio` field in interest rate model response
5. Markov chain Python functions exposed as standalone (not buried in `credit_risk_analysis`)
6. MDP value iteration backend for portfolio rebalancing

</domain>

<decisions>
## Implementation Decisions

### Markov Chain API structure
- One unified `POST /api/markov_chain` endpoint with a `mode` field: `steady_state` | `absorption` | `nstep` | `term_structure` | `mdp`
- Consistent with existing pattern: one route per logical domain (like `/api/interest_rate_model`)
- Transition matrix passed as a flat list-of-lists in JSON (not named states — frontend supplies labels)
- Default matrix is S&P 8-rating migration matrix when none provided

### MDP implementation scope
- Simplified portfolio rebalancing MDP: 3 fixed states (risk_off / neutral / risk_on), 3 fixed actions (underweight / neutral / overweight)
- User-configurable: `gamma` (risk aversion), `n_periods`, transition probabilities can be overridden
- Algorithm: value iteration only (policy iteration is a deferred idea — same output, more expensive)
- Returns: optimal policy matrix (state → action), value function, convergence iterations

### Vasicek model
- Extend existing `/api/interest_rate_model` with a `model` request field: `"cir"` (default) | `"vasicek"`
- Both models return identical response shape: `yield_curve`, `feller_condition_satisfied`, `feller_ratio`, `params`
- Vasicek: `feller_condition_satisfied` always `true` (no Feller constraint), `feller_ratio` returns `null`
- New `vasicek_yield_curve(r0, maturities, kappa, theta, sigma)` function in `interest_rate_models.py`

### Feller ratio response field
- `/api/interest_rate_model` adds `feller_ratio` = `2*kappa*theta / sigma²` (ratio form, >1 means satisfied)
- Present in response for CIR; `null` for Vasicek
- Allows frontend to display numeric badge like "Feller ratio: 1.43 ✓"

### BCC calibration route
- New `POST /api/calibrate_bcc` route matching `/api/calibrate_heston` shape: `params`, `fitted_vs_market`, `rmse`
- Additional `jump_params` sub-object: `{mu_j, sigma_j, lambda_j}` for the Merton jump component
- Frontend can use or ignore jump_params — won't block Phase 3 wiring

### Response conventions
- All new routes follow existing pattern: `{'success': True, 'result': {...}}` wrapper
- All numpy types converted via existing `convert_numpy_types()` helper
- Error responses: `{'success': False, 'error': str(e)}` with HTTP 500

### Claude's Discretion
- Exact Vasicek bond price formula vs approximate yield (use Vasicek closed-form: `y(T) = -ln(P(T))/T`)
- Whether to add simulated paths to interest rate responses (Phase 3 may want them — planner decides)
- File structure: whether to put Markov chain standalone functions in `credit_transitions.py` or a new `markov_chains.py`

</decisions>

<specifics>
## Specific Ideas

- Markov chain mode=`nstep` should return both `P^n` matrix AND default term structure in one call (avoids two round trips from frontend)
- BCC `jump_params` in response enables Phase 3 to show a breakdown of "Heston component vs jump component" in the UI — worth capturing even if Phase 3 doesn't use it immediately

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BCCCalibrator.calibrate()` in `model_calibration.py:184` — full two-stage BCC calibration exists, just needs a Flask wrapper
- `n_year_transition()` in `credit_transitions.py:53` — computes P^n, reuse directly
- `default_probability_term_structure()` in `credit_transitions.py:73` — reuse for term_structure mode
- `cir_yield_curve()` in `interest_rate_models.py:105` — Vasicek function will mirror this signature
- `convert_numpy_types()` in `webapp.py:136` — all new routes must call this before jsonify
- `SP_TRANSITION_MATRIX` and `RATINGS` in `credit_transitions.py` — default matrix and rating labels for markov_chain endpoint

### Established Patterns
- All Flask routes use `try/except Exception as e` with `logger.error` and 500 fallback
- Lazy imports inside endpoint function body: `from src.analytics.X import Y` pattern
- Request data accessed via `data = request.json or {}` with `.get()` defaults
- Numpy conversion: `result = convert_numpy_types(result)` before `return jsonify(...)`

### Integration Points
- `/api/markov_chain` will be new — no refactoring of `/api/credit_risk` needed (that stays for bond analysis)
- `/api/interest_rate_model` gets extended in-place (new `model` param, add Vasicek branch, add `feller_ratio` to CIR branch)
- `/api/calibrate_bcc` is a new route at the end of the calibration route block (after `/api/calibrate_merton`)

</code_context>

<deferred>
## Deferred Ideas

- Policy iteration algorithm (MARKOV-05 satisfied by value iteration; policy iteration is equivalent output, more expensive) — if needed, Phase 4 extension
- Full user-configurable MDP (arbitrary states/actions/rewards via JSON) — Phase 4 ML module scope
- Simulated interest rate paths in response (useful for Phase 3 visualization) — planner can add if easy
- Vasicek bond price endpoint (separate from yield curve) — Phase 3 may request it as a separate route

</deferred>

---

*Phase: 02-backend-completeness*
*Context gathered: 2026-03-03*
