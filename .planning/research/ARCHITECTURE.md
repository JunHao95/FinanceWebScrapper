# Architecture Patterns

**Domain:** MFE Showcase Web App — Flask + Vanilla JS Quant Finance
**Researched:** 2026-03-03
**Confidence:** HIGH (based on direct codebase inspection, no speculation)

---

## Existing Architecture (As-Built)

The app follows a clean three-layer architecture that is already working well and must be preserved for all new modules.

```
Browser (Vanilla JS)
        |
        |  fetch() POST — JSON body
        v
Flask Routes (webapp.py)
        |
        |  Python function call
        v
Model Layer (src/analytics/, src/derivatives/)
        |
        |  returns plain Python dict
        v
convert_numpy_types() → jsonify() → HTTP 200 JSON
```

### Layer Responsibilities

| Layer | Files | Responsibility | Must NOT Do |
|-------|-------|----------------|-------------|
| Model Layer | `src/analytics/*.py`, `src/derivatives/*.py` | Pure computation, no Flask imports, no HTTP concepts | Import Flask, reference request/response objects |
| API Layer | `webapp.py` routes | Parse JSON, call model functions, serialize result | Contain math logic, access DOM |
| Frontend | `static/js/*.js`, `templates/index.html` | Collect parameters, call API, render HTML result | Compute model math, import Python |

This separation is already clean in the WIP code. All six stochastic model backend files (`credit_transitions.py`, `interest_rate_models.py`, `regime_detection.py`, `fourier_pricer.py`, `model_calibration.py`) return plain Python dicts with no Flask dependency. All six corresponding routes in `webapp.py` follow the same lazy-import + `convert_numpy_types()` + `jsonify()` pattern. This must be replicated exactly for new modules.

---

## Recommended Architecture (Confirmed From Codebase)

### Component Boundaries

| Component | Responsibility | Communicates With | Location |
|-----------|---------------|-------------------|----------|
| Model Modules | Pure quant math: solve equations, simulate paths, calibrate params | Nothing (pure functions / classes) | `src/analytics/`, `src/derivatives/` |
| Flask API Routes | Validate input, dispatch to model, call `convert_numpy_types()`, return JSON | Model Modules (via lazy import) | `webapp.py` |
| JS Module Files | Read form fields, POST to API, render response as HTML string | Flask API Routes (via fetch) | `static/js/<module>.js` |
| HTML Template | Tab structure, form inputs, result container divs | JS modules (via script tags) | `templates/index.html` |
| Tab Router | Show/hide main tab panels, show/hide sub-tab panels | HTML DOM | `static/js/tabs.js`, `switchStochasticTab()` in `stochasticModels.js` |

### Data Flow Direction (Explicit)

```
User fills form inputs
        ↓
JS reads DOM values (getElementById, parseFloat)
        ↓
Input validation in JS (check for NaN, empty fields)
        ↓
fetch('/api/<endpoint>', { method: 'POST', body: JSON.stringify({...}) })
        ↓
Flask route receives request.json
        ↓
Lazy import of model module (avoids startup cost for heavy scipy/numpy libs)
        ↓
Model function called with typed Python args (float/int/str/list)
        ↓
Model returns plain Python dict (numpy floats already cast to float())
        ↓
convert_numpy_types(result) strips any remaining np.float64 / np.nan / np.inf
        ↓
jsonify({'success': True, 'result': result})
        ↓
JS receives JSON, reads data.success
        ↓
JS builds HTML string (innerHTML template literal) and sets resultsDiv.innerHTML
        ↓
Plotly.newPlot() called if chart needed (separate div, not innerHTML)
```

The `convert_numpy_types()` helper in `webapp.py` (line 136) is critical — it recursively converts `np.float64`, `np.int64`, `np.nan`, `np.inf` to JSON-safe Python types. Every new route MUST call this before `jsonify()`.

---

## Parameter → Compute → Visualize Pipeline Patterns

### Pattern 1: Pure-Parameter Model (No External Data)

Used by: CIR yield curve, Heston pricing, Merton pricing, Credit Risk (non-MC mode).

```
HTML: numeric inputs (sliders or number fields)
  ↓
JS: read + validate all fields, POST { param1, param2, ... }
  ↓
Flask: parse floats, call function(param1, param2, ...)
  ↓
Model: return { value, diagnostic_flag, supporting_data[] }
  ↓
JS: render scalar results in styled div, render table for arrays
```

Key: no async waiting UX needed, results return in under 1 second. No loading spinner required for truly pure computations. Show spinner only for calibration or MC paths.

### Pattern 2: Fetch-Then-Compute (External Data Dependency)

Used by: Regime Detection (yfinance), Heston Calibration (VolatilitySurface → yfinance), Merton Calibration.

```
HTML: ticker input + optional params
  ↓
JS: POST { ticker, days } → show loading message immediately
  ↓
Flask: call model, which fetches from yfinance internally
  ↓
Model: fetch → fit → return result dict
  ↓
JS: render on success
```

These routes take 10–120 seconds. The established pattern is to set `resultsDiv.innerHTML` to a "Computing..." message before the await, then replace it on response. This is already implemented in all six stochastic model functions. Do not change this pattern.

### Pattern 3: Multi-Step Pipeline (Calibration → Pricing)

Used by: BCC calibration (Heston params → add jump params), Heston calibrate → Heston price.

```
Step 1: Calibrate (call /api/calibrate_heston)
  ↓ Store calibrated params in JS variables
Step 2: Price (call /api/heston_price with calibrated params pre-filled)
```

This is currently done by the user manually copying values between sub-tabs. For ML modules, consider auto-populating downstream inputs from upstream calibration results using JS state variables. This avoids a stateful backend.

### Pattern 4: Benchmark Comparison

Used by: Heston pricing (compared against Black-Scholes at the same vol). Already established.

```
Model call → also compute reference model in same route
Return: { primary_result, reference_result, difference }
JS: render both side-by-side with difference highlighted
```

This is the validation pattern for model correctness. New models MUST include a benchmark comparison in their API response, not just the model output.

---

## Sub-Tab Pattern for Stochastic Models

The Stochastic Models main tab uses a two-level tab structure:

```
Main tab: "stochasticModels" → shows div#stochasticModelsTab
  Sub-tabs (buttons call switchStochasticTab()):
    - regime       → div#stochContent_regime
    - heston_cal   → div#stochContent_heston_cal
    - merton_cal   → div#stochContent_merton_cal
    - cir          → div#stochContent_cir
    - credit       → div#stochContent_credit
```

To add a new sub-tab (e.g., for a Markov chain / MDP tool):
1. Add a `<button class="tab-button" onclick="switchStochasticTab('markov')" id="stochTab_markov">` in the button row in `index.html`
2. Add `<div id="stochContent_markov" class="stoch-content" style="display:none;">` with form inputs + result div
3. Add the corresponding async function in `stochasticModels.js`
4. Add the corresponding Flask route in `webapp.py`
5. Add the model logic in `src/analytics/` or `src/derivatives/`

This is the exact same pattern for ML modules — they get a new main tab, not a sub-tab.

---

## Model Correctness Validation (Benchmarking Patterns)

### Current Established Patterns

1. **Feller condition check**: CIR and Heston both return `feller_condition_satisfied: bool` with `feller_lhs` and `feller_rhs` values. The JS renders a colored badge. Do this for all models with mathematical stability conditions.

2. **Black-Scholes comparison**: `/api/heston_price` runs a Black-Scholes comparison in the same route and returns `black_scholes_comparison` and `price_difference`. Use this for any new pricing model — compare against the simplest valid model.

3. **MSE/RMSE fit quality**: Calibration routes return `mse` and `rmse`. The JS displays these. All calibration endpoints must return fit quality metrics.

4. **Monte Carlo convergence check**: Credit risk returns `n_simulations` and survival curves. For any MC-based model, return enough supporting data that the user can visually verify convergence.

### Recommended Pattern for Each New Model Type

| New Model | Validation Benchmark | What to Return |
|-----------|---------------------|----------------|
| Markov chain (standalone) | Stationary distribution via eigenvector vs. long-run matrix power | Both computations, assert agreement |
| MDP (policy iteration) | Value iteration vs. policy iteration convergence | Both results, iteration count |
| ML models | Train/test split metrics, out-of-sample R² or accuracy | Full confusion matrix or regression metrics |

---

## What Is Currently Missing (WIP Gaps)

Based on direct inspection of all files:

1. **Markov chain / MDP standalone sub-tab**: `PROJECT.md` lists this as active, but there is no backend file for generic Markov chains (as opposed to the credit-specific `credit_transitions.py`) and no sub-tab in `index.html` for it. The `stochasticModels.js` has no `runMarkov()` or `runMDP()` function. This is the primary gap in the stochastic module.

2. **Plotly charts in stochastic models**: The existing stochastic model JS renders all results as HTML tables and text — none use `Plotly.newPlot()`. The volatility surface does use Plotly (confirmed in `volatilitySurface.js` line 234). For regime detection (time-series of calm/stressed probabilities), a Plotly line chart would be the correct output. For CIR yield curve, a line chart. For default probability term structure, a bar/line chart. These are currently tables only. The benchmark for visualization is set by the Volatility Surface tab.

3. **BCC calibration route**: The `BCCCalibrator` class is implemented in `model_calibration.py` but no `/api/calibrate_bcc` route exists in `webapp.py` and there is no corresponding JS function or sub-tab.

4. **Markov chain frontend form for credit transitions**: The credit sub-tab does not expose the custom matrix input (the backend `credit_risk_analysis()` accepts `custom_matrix` but the frontend only sends defaults).

---

## Build Order for Completing Current WIP and Adding ML

### Phase 1: Complete Stochastic Module (Current WIP)

**Priority: highest — don't start ML before this is done.**

Order within this phase:
1. Add Markov chain / MDP backend module (`src/analytics/markov_chain.py`) with generic transition matrix, stationary distribution, n-step distribution, policy iteration for MDP
2. Add `/api/markov_chain` and `/api/mdp` routes in `webapp.py`
3. Add `markov` sub-tab in `index.html` with the two-level form
4. Add `runMarkovChain()` and `runMDP()` async functions in `stochasticModels.js`
5. Validate: check that `P^n` row sums to 1, stationary dist matches eigenvector result
6. Add BCC calibration route (`/api/calibrate_bcc`) and sub-tab
7. Replace table-only output for CIR and credit risk with Plotly charts (yield curve line chart, survival curve line chart)
8. Add Plotly chart for regime detection (filtered probability over time, requires returning full `filtered_probs` time series from backend)

**Reason for this order**: Routes and backend code are nearly complete; the structural gap is the Markov/MDP piece and the visualization upgrade. Do backend before frontend in each case.

### Phase 2: Machine Learning in Finance (Next Semester)

New main tab, same pattern as Stochastic Models tab with sub-tabs.

Order:
1. Create `src/ml/` package with one file per model type (e.g., `regression_models.py`, `classification_models.py`, `neural_nets.py`)
2. Add `/api/ml/<model>` routes using the lazy import pattern
3. Add `mlFinance.js` file in `static/js/`
4. Add new main tab button and `mlFinanceTab` div in `index.html`
5. Wire up sub-tabs and forms per model

**Key architectural concern for ML**: sklearn models load fast; PyTorch/transformers load slow (500MB+). The lazy import pattern in `webapp.py` (already used for `EnhancedSentimentScraper`) is the correct solution. Never import torch at module level.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Numpy Types Leaking to JSON

**What goes wrong:** `jsonify()` raises a `TypeError` for `np.float64`, `np.nan`, `np.inf`.

**Why it happens:** Model functions use numpy internally and return numpy scalars. If `convert_numpy_types()` is skipped, the response fails.

**Prevention:** Every route MUST call `result = convert_numpy_types(result)` before `jsonify()`. This is already done in all six stochastic routes — copy this pattern exactly.

### Anti-Pattern 2: Heavy Module Import at Startup

**What goes wrong:** Flask app takes 30–60 seconds to start and uses 500MB+ RAM, makes cloud deployment impractical.

**Why it happens:** `import torch` or `from sklearn.ensemble import RandomForestClassifier` at module level forces load at startup.

**Prevention:** Use lazy imports inside route functions as the existing code does:
```python
@app.route('/api/ml_model', methods=['POST'])
def ml_model_endpoint():
    from src.ml.regression_models import MyModel  # import here, not at top
    ...
```

### Anti-Pattern 3: Computation Inside Flask Route

**What goes wrong:** Model math in `webapp.py` cannot be unit-tested, cannot be reused from CLI, cannot be benchmarked in isolation.

**Why it happens:** Developer adds a quick calculation directly in the route function.

**Prevention:** Route functions must only do: parse input, call model function, call `convert_numpy_types`, call `jsonify`. All math goes in `src/`.

### Anti-Pattern 4: DOM Manipulation in Model Layer

**What goes wrong:** Python model code cannot be tested in isolation and becomes coupled to the web framework.

**Prevention:** Python files in `src/` must have zero awareness of HTTP, HTML, or Flask. They return Python dicts.

### Anti-Pattern 5: Missing Input Validation in JS

**What goes wrong:** `NaN` sent to backend causes cryptic errors. Already partially mitigated in Heston pricing JS (explicit `Number.isFinite` check).

**Prevention:** For every new form, validate all numeric inputs before `fetch()`. The Heston pricing JS function (lines 567–576 in `stochasticModels.js`) is the reference implementation.

### Anti-Pattern 6: Missing Loading State for Slow Routes

**What goes wrong:** User sees blank result div for 30–120 seconds with no feedback, assumes it broke.

**Prevention:** Set `resultsDiv.innerHTML` to loading message before `await fetch()`. All six stochastic functions already do this — copy exactly.

---

## Scalability Considerations

This is an academic showcase app, not a production service. The relevant scalability concerns are:

| Concern | Current State | Implication |
|---------|--------------|-------------|
| Long-running routes (calibration: 30–120s) | Flask dev server, single process | Do not add async task queue; the loading spinner + long timeout is acceptable for a demo |
| Memory for ML models | Lazy imports protect startup | Keep lazy; avoid caching model instances globally in webapp.py |
| Concurrent users | Not a concern (showcase, single user) | No changes needed |
| Frontend chart performance | Plotly via CDN (2.27.0) | Add Plotly charts selectively; do not plot thousands of MC paths directly |

---

## Sources

- Direct inspection of `webapp.py` (all routes, lines 268–1389)
- Direct inspection of `src/analytics/credit_transitions.py`, `interest_rate_models.py`, `regime_detection.py`
- Direct inspection of `src/derivatives/fourier_pricer.py`, `model_calibration.py`
- Direct inspection of `static/js/stochasticModels.js` (all 701 lines)
- Direct inspection of `templates/index.html` (tab structure, lines 640–660, 1206–1438)
- Direct inspection of `static/js/volatilitySurface.js` (Plotly usage at lines 234, 375)
- `.planning/PROJECT.md` for requirements and constraints
