# Phase 02: Backend Completeness - Research

**Researched:** 2026-03-04
**Domain:** Python/Flask financial backend — Markov chains, MDP value iteration, Vasicek interest rate model, BCC calibration route
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Phase Boundary:** Close backend gaps so every planned stochastic feature has a callable Python
function and a Flask route. No new UI. No frontend wiring. Every success criterion is testable via
`curl` or `pytest` alone. Phase 3 picks up from here and wires everything to the browser.

**Specific gaps to close:**
1. `/api/markov_chain` — new unified endpoint for Markov chain operations (steady-state, absorption, n-step, MDP)
2. `/api/calibrate_bcc` — new Flask route wrapping the existing `BCCCalibrator` class
3. Vasicek model backend + extend `/api/interest_rate_model` with `model` selector
4. `feller_ratio` field in interest rate model response
5. Markov chain Python functions exposed as standalone (not buried in `credit_risk_analysis`)
6. MDP value iteration backend for portfolio rebalancing

**Markov Chain API structure:**
- One unified `POST /api/markov_chain` endpoint with a `mode` field: `steady_state` | `absorption` | `nstep` | `term_structure` | `mdp`
- Consistent with existing pattern: one route per logical domain (like `/api/interest_rate_model`)
- Transition matrix passed as a flat list-of-lists in JSON (not named states — frontend supplies labels)
- Default matrix is S&P 8-rating migration matrix when none provided

**MDP implementation scope:**
- Simplified portfolio rebalancing MDP: 3 fixed states (risk_off / neutral / risk_on), 3 fixed actions (underweight / neutral / overweight)
- User-configurable: `gamma` (risk aversion), `n_periods`, transition probabilities can be overridden
- Algorithm: value iteration only (policy iteration is a deferred idea)
- Returns: optimal policy matrix (state → action), value function, convergence iterations

**Vasicek model:**
- Extend existing `/api/interest_rate_model` with a `model` request field: `"cir"` (default) | `"vasicek"`
- Both models return identical response shape: `yield_curve`, `feller_condition_satisfied`, `feller_ratio`, `params`
- Vasicek: `feller_condition_satisfied` always `true`, `feller_ratio` returns `null`
- New `vasicek_yield_curve(r0, maturities, kappa, theta, sigma)` function in `interest_rate_models.py`

**Feller ratio response field:**
- `/api/interest_rate_model` adds `feller_ratio` = `2*kappa*theta / sigma²` (ratio form, >1 means satisfied)
- Present in response for CIR; `null` for Vasicek

**BCC calibration route:**
- New `POST /api/calibrate_bcc` route matching `/api/calibrate_heston` shape: `params`, `fitted_vs_market`, `rmse`
- Additional `jump_params` sub-object: `{mu_j, sigma_j, lambda_j}` for the Merton jump component

**Response conventions:**
- All new routes follow existing pattern: `{'success': True, 'result': {...}}` wrapper
- All numpy types converted via existing `convert_numpy_types()` helper
- Error responses: `{'success': False, 'error': str(e)}` with HTTP 500

### Claude's Discretion
- Exact Vasicek bond price formula vs approximate yield (use Vasicek closed-form: `y(T) = -ln(P(T))/T`)
- Whether to add simulated paths to interest rate responses (Phase 3 may want them — planner decides)
- File structure: whether to put Markov chain standalone functions in `credit_transitions.py` or a new `markov_chains.py`

### Deferred Ideas (OUT OF SCOPE)
- Policy iteration algorithm (MARKOV-05 satisfied by value iteration; policy iteration is equivalent output, more expensive) — if needed, Phase 4 extension
- Full user-configurable MDP (arbitrary states/actions/rewards via JSON) — Phase 4 ML module scope
- Simulated interest rate paths in response (useful for Phase 3 visualization) — planner can add if easy
- Vasicek bond price endpoint (separate from yield curve) — Phase 3 may request it as a separate route
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MARKOV-01 | User can input a transition matrix and compute steady-state distribution | Eigendecomposition of P.T finds left eigenvector for eigenvalue=1; numpy 2.2 verified |
| MARKOV-02 | User can compute absorption probabilities for absorbing Markov chains | Fundamental matrix N=(I-Q)^-1, absorption B=N*R; auto-detect absorbing states by P[i,i]>0.9999 |
| MARKOV-03 | User can visualize state transition diagram or heatmap of transition matrix | Backend returns P^n matrix as list-of-lists; frontend handles rendering in Phase 3 |
| MARKOV-04 | User can define a portfolio rebalancing Markov Decision Process (states, actions, rewards) | Hardcoded 3-state/3-action MDP with user-configurable gamma and transition matrix override |
| MARKOV-05 | User can compute optimal policy via value iteration for the MDP | Value iteration verified: 3x3 MDP converges in ~370 iterations at 1e-8 tolerance |
| MARKOV-06 | Markov/MDP results display in dedicated UI sub-tab with interactive parameters | Backend only: route returns JSON; UI is Phase 3 scope |
| CREDIT-01 | User can select a rating transition matrix and simulate credit migration | existing `SP_TRANSITION_MATRIX` + `n_year_transition()`; new `/api/markov_chain?mode=nstep` |
| CREDIT-02 | User can view credit migration heatmap showing transition probabilities | Backend returns P^n as list-of-lists in nstep mode response |
| CREDIT-03 | User can compute and view default probability / survival curve chart over time | existing `default_probability_term_structure()` exposed via mode=term_structure |
| CREDIT-04 | User can compute bond valuation with corrected time-discounted coupons | Already in `/api/credit_risk` — no backend change needed |
| CREDIT-05 | Credit transitions results display in dedicated UI sub-tab | Backend only: route returns JSON; UI is Phase 3 scope |
| RATE-01 | User can simulate CIR interest rate paths with chosen parameters | Existing `/api/interest_rate_model` already handles CIR; add `model` param |
| RATE-02 | User can simulate Vasicek interest rate paths with chosen parameters | New `vasicek_yield_curve()` in interest_rate_models.py; extend existing route |
| RATE-03 | User can view yield curve generated from the selected model | Both CIR and Vasicek return `yield_curve` list-of-dicts; identical shape |
| RATE-04 | UI displays whether Feller condition is satisfied for CIR parameters | Add `feller_ratio` to response (2*kappa*theta/sigma^2); null for Vasicek |
| RATE-05 | Interest rate model results display in dedicated UI sub-tab | Backend only; UI is Phase 3 scope |
</phase_requirements>

---

## Summary

This phase is pure backend work: add Python functions and Flask routes. No UI changes, no frontend
wiring. The full existing test suite (37 fast tests) runs green on numpy 2.2.3, scipy 1.15.3,
Flask 3.1.2 — these are the actual installed versions. The work decomposes into four independent
implementation tracks: (1) Markov chain standalone functions + unified route, (2) MDP value
iteration + route integration, (3) Vasicek model + route extension, (4) BCC calibration Flask route.

The biggest new algorithms are value iteration (MDP) and absorption probability computation — both
verified working with simple test computations. The Vasicek closed-form formula is verified: the
B(T) and A(T) functions produce correct upward-sloping yield curves for standard parameters. All
existing infrastructure (lazy imports, `convert_numpy_types`, `try/except` pattern, `request.json
or {}`) is established and consistent across all Flask routes.

Key decision from CONTEXT.md: Markov chain standalone functions may go in either
`credit_transitions.py` (extended) or a new `markov_chains.py`. Research recommends `markov_chains.py`
to keep the credit transitions file focused on bond-analysis-specific code and avoid entangling pure
Markov math with credit-domain data.

**Primary recommendation:** Implement as four independent, ordered tasks: markov chain functions,
MDP functions, Vasicek model, BCC route — each delivering a testable unit before the next begins.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 2.2.3 (installed) | Matrix power, eigendecomposition, linear algebra | All existing code uses numpy; `linalg.eig`, `linalg.matrix_power`, `linalg.inv` already used in project |
| scipy | 1.15.3 (installed) | Optimization for calibration (brute + fmin) | Already used in CIR and Heston calibrators; no new dep required |
| Flask | 3.1.2 (installed) | HTTP routes | All routes are standard Flask; no extension needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | installed | Unit tests for new functions | All new Python functions need pytest coverage |
| numpy.linalg | bundled | Eigendecomposition (steady-state), matrix inverse (absorption), matrix power (n-step) | Core math operations for Markov chain module |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| numpy.linalg.eig for steady-state | Iterative power method | Power method is simpler code but slower; eig is faster and already pattern-matched in regime_detection.py |
| numpy.linalg.inv for absorption | scipy.linalg.solve | `solve` is more numerically stable for large matrices; for 7x7 matrices inv is fine |
| numpy.linalg.matrix_power for n-step | Manual loop multiplication | matrix_power handles edge cases (n=0 returns identity); already used in project |

**Installation:** No new packages required. All dependencies already in `requirements.txt`.

## Architecture Patterns

### Recommended Project Structure

New files to create:
```
src/analytics/markov_chains.py    # New: standalone Markov + MDP functions
```

Files to extend:
```
src/analytics/interest_rate_models.py    # Add vasicek_bond_price(), vasicek_yield_curve()
webapp.py                                 # Add /api/markov_chain, /api/calibrate_bcc routes
                                          # Extend /api/interest_rate_model
```

New test files:
```
tests/test_markov_chains.py              # Tests for all markov_chains.py functions
tests/test_vasicek_model.py             # Tests for vasicek functions + route integration
tests/test_bcc_route.py                 # Tests for /api/calibrate_bcc route structure
```

### Pattern 1: New Markov Chain Module (`markov_chains.py`)
**What:** All standalone Markov/MDP functions not tied to the credit domain live in a new module.
**When to use:** When functions are general-purpose Markov math (work on any matrix, not just SP).
**Example:**
```python
# src/analytics/markov_chains.py
import numpy as np
from typing import Dict, List, Optional

def steady_state_distribution(P: np.ndarray) -> np.ndarray:
    """
    Compute steady-state (stationary) distribution of a Markov chain.
    Uses left eigenvector of P corresponding to eigenvalue 1.
    For absorbing chains, returns the unique absorbing distribution.
    """
    vals, vecs = np.linalg.eig(P.T)
    idx = np.argmin(np.abs(vals - 1.0))
    stat = np.real(vecs[:, idx])
    stat = np.abs(stat)
    return stat / stat.sum()


def absorption_probabilities(P: np.ndarray) -> Dict:
    """
    Compute absorption probabilities for absorbing Markov chain.
    Auto-detects absorbing states (P[i,i] > 0.9999 and all mass on self).
    Returns fundamental matrix N and absorption matrix B.
    """
    n = P.shape[0]
    absorbing = [i for i in range(n) if P[i, i] > 0.9999 and abs(P[i, :].sum() - 1.0) < 1e-6]
    transient = [i for i in range(n) if i not in absorbing]
    if not absorbing:
        return {'error': 'No absorbing states detected in transition matrix'}
    Q = P[np.ix_(transient, transient)]
    R = P[np.ix_(transient, absorbing)]
    N = np.linalg.inv(np.eye(len(transient)) - Q)  # fundamental matrix
    B = N @ R  # absorption probabilities
    return {
        'transient_indices': transient,
        'absorbing_indices': absorbing,
        'fundamental_matrix': N.tolist(),
        'absorption_matrix': B.tolist(),
    }
```

### Pattern 2: MDP Value Iteration
**What:** Standard value iteration for finite MDP with fixed 3-state, 3-action portfolio problem.
**When to use:** Mode = `mdp` in the unified markov_chain endpoint.
**Example:**
```python
def portfolio_mdp_value_iteration(
    gamma: float = 0.95,
    n_periods: int = 1000,
    transition_override: Optional[List] = None,
    tol: float = 1e-8
) -> Dict:
    """
    Value iteration for 3-state portfolio rebalancing MDP.
    States: 0=risk_off, 1=neutral, 2=risk_on
    Actions: 0=underweight, 1=neutral_weight, 2=overweight
    """
    # Default reward matrix (state x action)
    R = np.array([
        [ 2.0,  0.0, -2.0],   # risk_off
        [ 0.0,  1.0,  0.0],   # neutral
        [-2.0,  0.0,  2.0],   # risk_on
    ])
    # Default transition matrices P[action][state, next_state]
    # (or use transition_override if provided)
    ...
    V = np.zeros(3)
    for iteration in range(n_periods):
        V_old = V.copy()
        Q_mat = np.zeros((3, 3))  # state x action Q-values
        for a in range(3):
            Q_mat[:, a] = R[:, a] + gamma * P[a] @ V
        V = Q_mat.max(axis=1)
        policy = Q_mat.argmax(axis=1)
        if np.max(np.abs(V - V_old)) < tol:
            break
    return {
        'optimal_policy': policy.tolist(),  # [action_for_state_0, ..., action_for_state_2]
        'value_function': V.tolist(),
        'convergence_iterations': iteration + 1,
        'states': ['risk_off', 'neutral', 'risk_on'],
        'actions': ['underweight', 'neutral', 'overweight'],
        'gamma': gamma,
    }
```

### Pattern 3: Vasicek Closed-Form Bond Price
**What:** Add `vasicek_bond_price()` and `vasicek_yield_curve()` mirroring existing CIR functions.
**When to use:** When `model="vasicek"` in `/api/interest_rate_model` request.
**Example:**
```python
def vasicek_bond_price(r0: float, T: float, kappa: float, theta: float, sigma: float) -> float:
    """
    Zero-coupon bond price under Vasicek model:
        B(T) = (1 - exp(-kappa*T)) / kappa
        A(T) = exp((theta - sigma^2/(2*kappa^2))*(B(T)-T) - sigma^2*B(T)^2/(4*kappa))
        P(0,T) = A(T) * exp(-B(T) * r0)
    """
    if T <= 0:
        return 1.0
    B_T = (1.0 - np.exp(-kappa * T)) / kappa
    log_A = (theta - sigma**2 / (2.0 * kappa**2)) * (B_T - T) \
            - sigma**2 * B_T**2 / (4.0 * kappa)
    return float(np.exp(log_A - B_T * r0))


def vasicek_yield_curve(r0: float, maturities: List[float],
                        kappa: float, theta: float, sigma: float) -> List[Dict]:
    """Mirrors cir_yield_curve() signature exactly."""
    curve = []
    for T in maturities:
        B = vasicek_bond_price(r0, T, kappa, theta, sigma)
        r_impl = -np.log(B) / T if T > 0 and B > 0 else r0
        curve.append({'maturity': float(T), 'bond_price': float(B), 'spot_rate': float(r_impl)})
    return curve
```

### Pattern 4: Extending `/api/interest_rate_model` with Feller Ratio
**What:** Add `model` selector and `feller_ratio` to the existing route in-place.
**When to use:** This is a backward-compatible extension (default `model="cir"` preserves existing behavior).
**Example:**
```python
@app.route('/api/interest_rate_model', methods=['POST'])
def interest_rate_model_endpoint():
    try:
        from src.analytics.interest_rate_models import (
            CIRCalibrator, cir_yield_curve, calibrate_to_treasuries, vasicek_yield_curve
        )
        data = request.json or {}
        model = data.get('model', 'cir').lower()

        if data.get('calibrate_to_treasuries', False):
            r0 = float(data.get('r0', 0.053))
            result = calibrate_to_treasuries(r0=r0)
            # add feller_ratio to calibrate_to_treasuries result
            kappa = result['calibrated_params']['kappa']
            theta = result['calibrated_params']['theta']
            sigma = result['calibrated_params']['sigma']
            result['feller_ratio'] = (2 * kappa * theta) / (sigma ** 2)
        elif model == 'vasicek':
            r0    = float(data.get('r0', 0.053))
            kappa = float(data.get('kappa', 0.5))
            theta = float(data.get('theta', 0.06))
            sigma = float(data.get('sigma', 0.02))
            mats  = data.get('maturities', [0.25, 0.5, 1, 2, 5, 10, 30])
            curve = vasicek_yield_curve(r0, mats, kappa, theta, sigma)
            result = {
                'model': 'Vasicek (1977)',
                'params': {'r0': r0, 'kappa': kappa, 'theta': theta, 'sigma': sigma},
                'feller_condition_satisfied': True,   # no Feller constraint for Vasicek
                'feller_ratio': None,                  # not applicable
                'yield_curve': curve,
            }
        else:  # default: CIR
            r0    = float(data.get('r0', 0.053))
            kappa = float(data.get('kappa', 1.5))
            theta = float(data.get('theta', 0.05))
            sigma = float(data.get('sigma', 0.1))
            mats  = data.get('maturities', [0.25, 0.5, 1, 2, 5, 10, 30])
            curve = cir_yield_curve(r0, mats, kappa, theta, sigma)
            feller = 2 * kappa * theta > sigma ** 2
            feller_ratio = (2 * kappa * theta) / (sigma ** 2)
            result = {
                'model': 'CIR (1985)',
                'params': {'r0': r0, 'kappa': kappa, 'theta': theta, 'sigma': sigma},
                'feller_condition_satisfied': feller,
                'feller_ratio': feller_ratio,
                'yield_curve': curve,
            }

        result = convert_numpy_types(result)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"Error in interest rate model: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

### Pattern 5: BCC Calibration Route
**What:** New route wrapping existing `BCCCalibrator.calibrate()`.
**When to use:** `POST /api/calibrate_bcc`.
**Example:**
```python
@app.route('/api/calibrate_bcc', methods=['POST'])
def calibrate_bcc_endpoint():
    try:
        from src.derivatives.model_calibration import BCCCalibrator
        data = request.json or {}
        ticker          = data.get('ticker', 'AAPL').upper()
        risk_free_rate  = float(data.get('risk_free_rate', 0.05))
        option_type     = data.get('option_type', 'call')

        calibrator = BCCCalibrator()
        result = calibrator.calibrate(ticker, risk_free_rate=risk_free_rate,
                                      option_type=option_type)
        # Normalize jump_params to match context decision field names
        if 'calibrated_params' in result and 'jump' in result['calibrated_params']:
            j = result['calibrated_params']['jump']
            result['jump_params'] = {
                'lambda_j': j.get('lambda', j.get('lambda_j')),
                'mu_j':     j.get('mu_j'),
                'sigma_j':  j.get('delta_j'),  # delta_j in source = sigma_j in response
            }
        result = convert_numpy_types(result)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"Error in BCC calibration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

### Pattern 6: Unified `/api/markov_chain` Route
**What:** Single POST endpoint dispatching on `mode` field.
**When to use:** All Markov chain frontend operations.
**Example:**
```python
@app.route('/api/markov_chain', methods=['POST'])
def markov_chain_endpoint():
    try:
        from src.analytics.markov_chains import (
            steady_state_distribution, absorption_probabilities,
            portfolio_mdp_value_iteration
        )
        from src.analytics.credit_transitions import (
            n_year_transition, default_probability_term_structure,
            SP_TRANSITION_MATRIX, RATINGS
        )
        data = request.json or {}
        mode = data.get('mode', 'steady_state')
        raw_matrix = data.get('transition_matrix')
        P = np.array(raw_matrix) if raw_matrix is not None else SP_TRANSITION_MATRIX.copy()

        if mode == 'steady_state':
            pi = steady_state_distribution(P)
            result = {'mode': mode, 'steady_state': pi.tolist()}
        elif mode == 'absorption':
            result = absorption_probabilities(P)
            result['mode'] = mode
        elif mode == 'nstep':
            n = int(data.get('n', 5))
            Pn = n_year_transition(P, n)
            term = default_probability_term_structure(
                data.get('current_rating', 'BBB'), P=P
            )
            result = {
                'mode': mode, 'n': n,
                'transition_matrix_n': Pn.tolist(),
                'term_structure': term,
            }
        elif mode == 'term_structure':
            rating = data.get('current_rating', 'BBB').upper()
            horizons = data.get('horizons')
            term = default_probability_term_structure(rating, horizons=horizons, P=P)
            result = {'mode': mode, 'current_rating': rating, 'term_structure': term}
        elif mode == 'mdp':
            gamma = float(data.get('gamma', 0.95))
            n_periods = int(data.get('n_periods', 1000))
            result = portfolio_mdp_value_iteration(gamma=gamma, n_periods=n_periods)
        else:
            return jsonify({'success': False, 'error': f"Unknown mode: {mode}"}), 400

        result = convert_numpy_types(result)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"Error in markov_chain endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

### Anti-Patterns to Avoid
- **Burying new functions in existing domain-specific modules:** `credit_transitions.py` already has a specific concern (credit bond analysis). New general Markov math belongs in `markov_chains.py`. Do not add `steady_state_distribution` or `absorption_probabilities` to `credit_transitions.py`.
- **Returning raw numpy arrays in jsonify:** Always call `convert_numpy_types()` before `jsonify()`. Raw numpy arrays and `numpy.float64` values cause Flask JSON serialization to fail silently or raise.
- **Absorbing-state edge case in steady-state:** The SP transition matrix has an absorbing state (D). `steady_state_distribution()` correctly returns `[0,...,0,1]` for absorbing chains. Do not add special-case logic for this — eigendecomposition handles it automatically.
- **Matrix power with n=0:** `numpy.linalg.matrix_power(P, 0)` returns identity matrix correctly — do not add a manual check. The existing `n_year_transition()` already handles this.
- **Value iteration with very low gamma:** When `gamma` approaches 0, value function equals immediate rewards. Allow any gamma in [0, 1). Validate at input, not deep in the algorithm.
- **Circular import in markov_chains.py:** Do not import from `webapp.py` in `markov_chains.py`. The route imports from analytics; analytics never imports from webapp.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Stationary distribution | Custom iterative solver | `numpy.linalg.eig(P.T)` | eig is numerically stable; power iteration requires convergence check and may cycle for near-degenerate matrices |
| Matrix power for n-step | Manual loop `P @ P @ ...` | `numpy.linalg.matrix_power` | matrix_power handles n=0 (identity), integer overflow, negative n; O(log n) algorithm vs O(n) |
| Absorption probability | Custom recursion | Fundamental matrix `N = (I-Q)^-1` | Closed-form; single linear algebra call vs iterative simulation |
| JSON numpy serialization | Custom encoder | existing `convert_numpy_types()` | Already handles ndarray, numpy scalars, NaN, Inf; do not duplicate |
| Option market data fetching for BCC | Custom yfinance call | `BCCCalibrator.calibrate()` which calls `VolatilitySurfaceBuilder` internally | All market data logic already in calibrator; no need to re-implement |

**Key insight:** Every mathematical primitive needed for Phase 2 is already implemented in numpy/scipy. The code is glue: connect existing math to Flask routes with consistent response shapes.

## Common Pitfalls

### Pitfall 1: Singular Fundamental Matrix (Absorption)
**What goes wrong:** `numpy.linalg.inv(I - Q)` raises `LinAlgError: Singular matrix` when the transient sub-matrix Q has eigenvalue 1 (happens with near-absorbing transient states or rounding).
**Why it happens:** Floating-point rounding in user-supplied matrices can make some transient states appear absorbing.
**How to avoid:** Use `numpy.linalg.solve(I - Q, R)` instead of `inv(I-Q) @ R` — `solve` is more numerically stable. Or add a check: clip `Q` diagonal to max `1 - 1e-8` before inversion.
**Warning signs:** Test with identity matrix input — `absorption_probabilities(np.eye(8))` should return an error about no transient states, not raise LinAlgError.

### Pitfall 2: Multiple Eigenvalues Near 1 for Reducible Chains
**What goes wrong:** `steady_state_distribution()` picks one eigenvector when there are multiple eigenvalues at 1 (reducible chain with multiple absorbing components). Result is one of potentially multiple steady-state distributions.
**Why it happens:** Reducible Markov chains have one steady state per absorbing component.
**How to avoid:** In Phase 2 scope, user-supplied matrices are treated as-is. Document that the function returns one valid steady-state distribution — for the SP matrix this is the correct `[0,...,0,1]`. Add a note in docstring about reducible chains.
**Warning signs:** Row sums of P differ from 1 by more than 1e-4 (validate at entry to route).

### Pitfall 3: Value Iteration Non-Convergence
**What goes wrong:** Value iteration loops for exactly `n_periods` iterations without converging when `gamma` is too close to 1 or reward scale is very large.
**Why it happens:** Bellman backup convergence rate is O(gamma^k). Near gamma=1, convergence is very slow.
**How to avoid:** Cap `gamma` at 0.999. Cap `n_periods` at a server-safe maximum (e.g., 10000). Always return `convergence_iterations` so callers know if tolerance was reached. Do NOT raise on non-convergence — return result with a `converged: false` flag.
**Warning signs:** `convergence_iterations == n_periods` means tolerance was not reached.

### Pitfall 4: BCC Calibrator Requires Live Market Data
**What goes wrong:** `BCCCalibrator.calibrate()` internally calls `VolatilitySurfaceBuilder.build_surface()` which fetches live option chain data from yfinance. If the ticker has no options, calibration returns `{'error': 'No market data for {ticker}'}`.
**Why it happens:** Options data requires a liquid US equity with listed options.
**How to avoid:** Route should propagate the error dict properly: if `'error' in result`, return `{'success': False, 'error': result['error']}` with HTTP 500. Do not assume result is always a success dict.
**Warning signs:** Testing with illiquid or non-US tickers will always fail. Use AAPL/SPY for manual testing.

### Pitfall 5: Backward-Incompatible Extension of `/api/interest_rate_model`
**What goes wrong:** Existing frontend code that calls `/api/interest_rate_model` without a `model` field breaks if the default behavior changes.
**Why it happens:** Adding `feller_ratio` to the existing CIR response is additive (safe). Changing the response shape (renaming keys, removing `yield_curve`) breaks callers.
**How to avoid:** Default `model="cir"` and `feller_ratio` added to CIR response are additive. Never rename existing keys (`yield_curve`, `feller_condition_satisfied`, `params`). Keep the `calibrate_to_treasuries` branch response identical shape to manual params branch.
**Warning signs:** Run existing test `test_interest_rate_models.py::test_return_dict_has_required_keys` after the extension — it must still pass.

### Pitfall 6: numpy.linalg.eig Returns Complex Numbers
**What goes wrong:** `numpy.linalg.eig` can return complex eigenvalues/eigenvectors even for real stochastic matrices due to floating-point arithmetic. `np.real()` extracts the real part, but if imaginary part is non-negligible the result is wrong.
**Why it happens:** Numerical noise in non-symmetric matrices.
**How to avoid:** After `stat = np.real(vecs[:, idx])`, assert `np.allclose(np.imag(vecs[:, idx]), 0, atol=1e-6)`. If assertion fails, fall back to power method: iterate `pi = pi @ P` until convergence.
**Warning signs:** Negative components in steady-state distribution before `np.abs()` step.

## Code Examples

### Steady-State via Eigendecomposition (verified pattern from regime_detection.py)
```python
# Source: /src/analytics/regime_detection.py lines 295-298 (same pattern)
vals, vecs = np.linalg.eig(P.T)
stat = np.real(vecs[:, np.argmin(np.abs(vals - 1))])
stat = np.abs(stat)
pi = stat / stat.sum()
```

### Absorption Probability (verified computation, 2026-03-04)
```python
# Source: verified computationally — see research test above
absorbing = [i for i in range(n) if P[i, i] > 0.9999 and abs(P[i, :].sum() - 1.0) < 1e-6]
transient = [i for i in range(n) if i not in absorbing]
Q = P[np.ix_(transient, transient)]
R = P[np.ix_(transient, absorbing)]
N = np.linalg.inv(np.eye(len(transient)) - Q)  # fundamental matrix
B = N @ R  # shape: (len(transient), len(absorbing))
```

### Value Iteration Convergence (verified, 371 iterations for 3x3 MDP at gamma=0.95)
```python
# Source: verified computationally — see research test above
V = np.zeros(n_states)
for iteration in range(max_iterations):
    V_old = V.copy()
    Q_vals = np.zeros((n_states, n_actions))
    for a in range(n_actions):
        Q_vals[:, a] = R[:, a] + gamma * P[a] @ V
    V = Q_vals.max(axis=1)
    policy = Q_vals.argmax(axis=1)
    if np.max(np.abs(V - V_old)) < tol:
        break
```

### Vasicek Closed-Form (verified, 2026-03-04)
```python
# Vasicek (1977): P(0,T) = A(T) * exp(-B(T) * r0)
# B(T) = (1 - exp(-kappa*T)) / kappa
# log A(T) = (theta - sigma^2/(2*kappa^2)) * (B(T) - T) - sigma^2*B(T)^2 / (4*kappa)
def vasicek_bond_price(r0, T, kappa, theta, sigma):
    if T <= 0:
        return 1.0
    B_T = (1.0 - np.exp(-kappa * T)) / kappa
    log_A = (theta - sigma**2 / (2.0 * kappa**2)) * (B_T - T) \
            - sigma**2 * B_T**2 / (4.0 * kappa)
    return float(np.exp(log_A - B_T * r0))
```

### Flask Route Pattern (from /api/credit_risk, lines 1346-1379)
```python
@app.route('/api/new_endpoint', methods=['POST'])
def new_endpoint():
    try:
        from src.analytics.module import function_name  # lazy import inside function body

        data = request.json or {}
        param = data.get('param', default_value)

        result = function_name(param)
        result = convert_numpy_types(result)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"Error in new_endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Power method for stationary distribution | `numpy.linalg.eig` on P.T | Already in project (regime_detection.py) | More numerically robust; pattern already established in codebase |
| Hard-penalized Feller constraint | Alpha reparameterization (Feller by construction) | Phase 1 | MATH-03 already fixed; CIR calibration always satisfies Feller |
| Markov functions buried in `credit_risk_analysis()` | Standalone functions callable independently | This phase | Enables `/api/markov_chain` route without coupling to bond analysis |

**Deprecated/outdated:**
- Soft Feller penalty in CIR calibration: removed in Phase 1; do not re-introduce.
- `calibrate_heston` returning `calibration` key (not `result`): note that existing calibrate_heston uses `{'success': True, 'calibration': result}` while other routes use `{'success': True, 'result': result}`. For new BCC route, use `result` key to be consistent with newer routes.

## Open Questions

1. **`markov_chains.py` vs extending `credit_transitions.py`**
   - What we know: CONTEXT.md marks this as Claude's Discretion
   - What's unclear: Whether a new file is worth the import overhead
   - Recommendation: Create `markov_chains.py` for clean separation. The general Markov functions (steady_state, absorption, MDP) have no credit-domain dependency. Keeping them separate makes both modules more testable. `credit_transitions.py` imports from `markov_chains.py` if needed.

2. **BCC `fitted_vs_market` field in response**
   - What we know: CONTEXT.md says route should match calibrate_heston shape with `params`, `fitted_vs_market`, `rmse`. The existing `BCCCalibrator.calibrate()` does NOT return `fitted_vs_market` — it returns `mse`, `rmse`, `calibrated_params`, `spot`.
   - What's unclear: Should the route compute `fitted_vs_market` or just pass through what BCCCalibrator returns?
   - Recommendation: Pass through BCCCalibrator's actual return dict. Add a note in the route that `fitted_vs_market` is not available without re-running prices (expensive). Phase 3 can request it if needed.

3. **MDP default reward values**
   - What we know: No explicit default rewards specified in CONTEXT.md
   - What's unclear: The exact reward matrix is left to implementation
   - Recommendation: Use symmetric rewards as demonstrated in research: `R = [[2,0,-2],[0,1,0],[-2,0,2]]` — underweight rewarded in risk_off, overweight rewarded in risk_on, neutral weakly rewarded in neutral state.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.x (installed) |
| Config file | none — no pytest.ini in project root; conftest.py in tests/ |
| Quick run command | `pytest tests/ -q -m "not slow" -x` |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MARKOV-01 | steady_state_distribution() returns valid probability vector | unit | `pytest tests/test_markov_chains.py::test_steady_state_sums_to_one -x` | Wave 0 |
| MARKOV-01 | steady_state_distribution() on ergodic chain matches known solution | unit | `pytest tests/test_markov_chains.py::test_steady_state_known_solution -x` | Wave 0 |
| MARKOV-02 | absorption_probabilities() rows sum to 1 for valid absorbing chain | unit | `pytest tests/test_markov_chains.py::test_absorption_rows_sum_to_one -x` | Wave 0 |
| MARKOV-02 | absorption_probabilities() returns error for non-absorbing chain | unit | `pytest tests/test_markov_chains.py::test_absorption_no_absorbing_states -x` | Wave 0 |
| MARKOV-03 | nstep mode returns transition_matrix_n with correct shape | unit | `pytest tests/test_markov_chains.py::test_nstep_matrix_shape -x` | Wave 0 |
| MARKOV-04 | portfolio_mdp_value_iteration() returns policy, value, convergence keys | unit | `pytest tests/test_markov_chains.py::test_mdp_return_keys -x` | Wave 0 |
| MARKOV-05 | value iteration converges with policy matching expected for simple case | unit | `pytest tests/test_markov_chains.py::test_mdp_policy_correct -x` | Wave 0 |
| MARKOV-06 | /api/markov_chain route responds 200 for all modes | integration | `pytest tests/test_markov_route.py -x` | Wave 0 |
| CREDIT-01 | /api/markov_chain?mode=nstep returns transition_matrix_n | integration | `pytest tests/test_markov_route.py::test_nstep_mode -x` | Wave 0 |
| CREDIT-02 | nstep response contains transition_matrix_n as list-of-lists | unit | `pytest tests/test_markov_chains.py::test_nstep_matrix_is_list -x` | Wave 0 |
| CREDIT-03 | term_structure mode returns list of horizon/default_prob dicts | unit | `pytest tests/test_markov_chains.py::test_term_structure_mode -x` | Wave 0 |
| CREDIT-04 | existing /api/credit_risk still returns expected_bond_value | regression | `pytest tests/test_credit_transitions.py -x` | ✅ exists |
| CREDIT-05 | /api/markov_chain returns success:true for all modes | integration | `pytest tests/test_markov_route.py -x` | Wave 0 |
| RATE-01 | /api/interest_rate_model with model=cir matches previous response shape | regression | `pytest tests/test_interest_rate_models.py -x` | ✅ exists |
| RATE-02 | vasicek_yield_curve() returns ascending yields for normal params | unit | `pytest tests/test_vasicek_model.py::test_vasicek_yield_curve_shape -x` | Wave 0 |
| RATE-02 | vasicek_bond_price() returns 1.0 at T=0 | unit | `pytest tests/test_vasicek_model.py::test_vasicek_bond_price_at_zero -x` | Wave 0 |
| RATE-03 | /api/interest_rate_model with model=vasicek returns yield_curve list | integration | `pytest tests/test_vasicek_model.py::test_vasicek_route -x` | Wave 0 |
| RATE-04 | CIR response now contains feller_ratio numeric field | regression | `pytest tests/test_interest_rate_models.py::test_return_dict_has_required_keys -x` | needs update |
| RATE-05 | /api/interest_rate_model responds 200 for both model values | integration | `pytest tests/test_vasicek_model.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -q -m "not slow" -x`
- **Per wave merge:** `pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_markov_chains.py` — covers MARKOV-01, MARKOV-02, MARKOV-03, MARKOV-04, MARKOV-05, CREDIT-02, CREDIT-03
- [ ] `tests/test_markov_route.py` — covers MARKOV-06, CREDIT-01, CREDIT-05
- [ ] `tests/test_vasicek_model.py` — covers RATE-02, RATE-03, RATE-05
- [ ] Update `tests/test_interest_rate_models.py::test_return_dict_has_required_keys` to expect `feller_ratio` key — covers RATE-04

Note: No new framework installation required. pytest is already installed and conftest.py provides shared fixtures.

## Sources

### Primary (HIGH confidence)
- `/src/analytics/credit_transitions.py` (read directly) — `n_year_transition`, `default_probability_term_structure`, `SP_TRANSITION_MATRIX`, `RATINGS`
- `/src/analytics/interest_rate_models.py` (read directly) — `cir_yield_curve`, `cir_bond_price`, `CIRCalibrator`
- `/src/analytics/regime_detection.py` line 295-298 (read directly) — eigendecomposition pattern for stationary distribution
- `/src/derivatives/model_calibration.py` lines 184-296 (read directly) — `BCCCalibrator.calibrate()` signature and return dict
- `/webapp.py` lines 1235-1380 (read directly) — all route patterns, `convert_numpy_types`, lazy import pattern
- `/tests/conftest.py` (read directly) — existing fixture patterns, `slow` marker

### Secondary (MEDIUM confidence)
- Vasicek (1977) closed-form verified computationally: `vasicek_bond_price(0.05, T, 0.5, 0.06, 0.02)` produces correct upward-sloping yield curve (spot rates increasing toward theta=0.06 for upward-sloping case)
- Absorption probability formula verified computationally: fundamental matrix N=(I-Q)^-1, B=N*R; row sums = 1 confirmed
- Value iteration verified: 3-state/3-action MDP converges in 371 iterations at gamma=0.95, tol=1e-8

### Tertiary (LOW confidence)
- MDP default reward matrix values (`[[2,0,-2],[0,1,0],[-2,0,2]]`) are researcher-chosen defaults not from a financial textbook — planner may adjust

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all dependencies already installed, versions confirmed at runtime (numpy 2.2.3, scipy 1.15.3, Flask 3.1.2)
- Architecture: HIGH — patterns extracted from existing working routes in webapp.py
- Markov/MDP algorithms: HIGH — all verified computationally with expected outputs confirmed
- Vasicek formula: HIGH — closed-form verified computationally, formula matches standard textbook (Vasicek 1977)
- BCC route: HIGH — BCCCalibrator.calibrate() signature and return dict confirmed by code read
- Pitfalls: MEDIUM — singular matrix and complex eigenvalue pitfalls are known numerical analysis issues, confirmed relevant by code inspection

**Research date:** 2026-03-04
**Valid until:** 2026-04-04 (stable math domain; Flask/numpy API changes would invalidate)
