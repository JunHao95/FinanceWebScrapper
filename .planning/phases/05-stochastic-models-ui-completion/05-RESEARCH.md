# Phase 5: Stochastic Models UI Completion - Research

**Researched:** 2026-03-08
**Domain:** Frontend HTML/JS wiring — Markov Chain sub-tab + Vasicek model selector in CIR sub-tab
**Confidence:** HIGH (all findings derived from reading the actual source files, no external APIs needed)

---

## Summary

Phase 5 closes two specific UI gaps that existed after Phase 3. The backends are 100% complete and tested. The gap is purely in `templates/index.html` (new HTML div + sub-tab button) and `static/js/stochasticModels.js` (new `runMarkovChain()` function and a `<select>` model-selector patch to `runCIRModel()`).

**Gap 1 — Markov Chain sub-tab:** There is no `stochContent_markov` div and no `stochTab_markov` button in the existing tab list. The backend `/api/markov_chain` accepts five modes (`steady_state`, `absorption`, `nstep`, `term_structure`, `mdp`) but there is no UI entry point for three of them (steady_state, absorption, mdp). The Credit Risk tab internally calls the `nstep` mode as a bonus heatmap; the user has no way to call `steady_state`, `absorption`, or `mdp` directly.

**Gap 2 — Vasicek selector:** The CIR tab (`stochContent_cir`) only sends `model: undefined` (i.e., defaults to CIR). There is no model selector `<select>` allowing the user to switch to `model: vasicek`. The backend branch is fully implemented and returns the same `yield_curve` array structure with `feller_condition_satisfied: true, feller_ratio: null`.

**Primary recommendation:** Add a single new `stochContent_markov` sub-tab (HTML + JS) with an internal mode selector (`<select id="markovMode">`) driving three forms. Patch the CIR sub-tab with a `<select id="cirModel">` and update `runCIRModel()` to pass `model` in the payload.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MARKOV-01 | User can input a transition matrix and compute steady-state distribution | `mode=steady_state` returns `{steady_state: float[], ratings: string[]}` — render as Plotly bar chart |
| MARKOV-02 | User can compute absorption probabilities for absorbing Markov chains | `mode=absorption` returns `{transient_indices, absorbing_indices, fundamental_matrix, absorption_matrix}` — render `absorption_matrix` as heatmap |
| MARKOV-03 | User can visualize state transition diagram or heatmap of transition matrix | `mode=steady_state` includes default S&P 8-state matrix; a second `nstep n=1` call fetches the 8x8 heatmap (same pattern as Credit Risk bonus heatmap) |
| MARKOV-04 | User can define a portfolio rebalancing MDP (states, actions, rewards) | `mode=mdp` accepts `gamma` and `n_periods`; the 3-state model is fixed (risk_off/neutral/risk_on x underweight/neutral/overweight) — inputs are the tuning knobs |
| MARKOV-05 | User can compute optimal policy via value iteration for the MDP | `mode=mdp` returns `{optimal_policy, value_function, states, actions, convergence_iterations, converged}` — render as policy cards + V* bar chart |
| MARKOV-06 | Markov/MDP results display in dedicated UI sub-tab with interactive parameters | New `stochContent_markov` div + `stochTab_markov` button following existing pattern |
| RATE-02 | User can simulate Vasicek interest rate paths with chosen parameters | Add `<select id="cirModel">` to `stochContent_cir`, pass `model` to payload; Vasicek uses same `r0/kappa/theta/sigma` inputs with different defaults |
| RATE-03 | User can view yield curve generated from the selected model | `runCIRModel()` already plots `yield_curve` via Plotly; same code path works for Vasicek since both return identical `yield_curve` array structure |
</phase_requirements>

---

## Standard Stack

### Core (already in project — no new installs)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Plotly.js | 2.27.0 (CDN) | All charts in stochastic tab | Already loaded at line 8 of index.html |
| Vanilla JS (ES2020) | — | All `stochasticModels.js` functions | No framework used in this project |
| Flask + jsonify | 3.x | Backend routes | Already in use |

### Supporting utilities already in scope

| Utility | Location | What it does |
|---------|----------|-------------|
| `escapeHTML(str)` | stochasticModels.js:28 | XSS-safe string rendering |
| `renderKVTable(obj, title)` | stochasticModels.js:41 | Key-value table for param display |
| `renderAlert(msg, type)` | stochasticModels.js:55 | Styled error/info banners |
| `switchStochasticTab(name)` | stochasticModels.js:10 | Shows `stochContent_<name>`, marks `stochTab_<name>` active |

**Installation:** No new packages. All dependencies already present.

---

## Architecture Patterns

### Sub-tab Registration Pattern (from index.html lines 1220–1246)

```html
<!-- Button in tabs div -->
<button class="tab-button" onclick="switchStochasticTab('markov')" id="stochTab_markov">
    Markov Chain
</button>

<!-- Content div after other stochContent divs -->
<div id="stochContent_markov" class="stoch-content" style="display:none;">
    <!-- content here -->
</div>
```

`switchStochasticTab()` works by selector: hides all `.stoch-content` elements, deactivates all `[id^="stochTab_"]` buttons, then shows `stochContent_<name>` and activates `stochTab_<name>`. No registration step needed in JS.

### JS Function Pattern (from runCIRModel, runCreditRisk)

Every existing run function follows this exact structure:

```javascript
async function runMarkovChain() {
    // 1. Read inputs from DOM with optional chaining + default
    const mode = document.getElementById('markovMode')?.value || 'steady_state';

    // 2. Get results container, show it, set loading message
    const resultsDiv = document.getElementById('markovResults');
    if (!resultsDiv) return;
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<p style="color:#666;">⏳ Computing…</p>';

    try {
        // 3. Build payload, POST to route
        const resp = await fetch('/api/markov_chain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, /* other params */ })
        });
        const data = await resp.json();

        // 4. Check success flag
        if (!data.success) {
            resultsDiv.innerHTML = renderAlert(`Error: ${data.error}`);
            return;
        }

        const r = data.result;

        // 5. Build innerHTML with result-card div
        resultsDiv.innerHTML = `<div class="result-card">...</div>`;

        // 6. Call Plotly.newPlot on IDs injected in step 5
        Plotly.newPlot('markovChart', [...], {...}, { responsive: true });

    } catch (err) {
        resultsDiv.innerHTML = renderAlert(`Request failed: ${err.message}`);
    }
}
```

### Mode-switching within a sub-tab

The Markov sub-tab needs three distinct form layouts (steady_state, absorption, mdp). The recommended pattern is a `<select>` element that triggers `showMarkovForm()` to hide/show form section divs. This is consistent with existing `cirCalibrateTreasuries` checkbox-based UI branching in `runCIRModel`.

```javascript
function showMarkovForm(mode) {
    ['steady_state', 'absorption', 'mdp'].forEach(m => {
        const el = document.getElementById('markovForm_' + m);
        if (el) el.style.display = m === mode ? 'block' : 'none';
    });
}
```

### Recommended Project Structure (no changes to file layout)

The plan touches three files only:

```
templates/
└── index.html              # Add stochTab_markov button + stochContent_markov div
                            # Add <select id="cirModel"> to stochContent_cir
static/js/
└── stochasticModels.js     # Add runMarkovChain() + showMarkovForm()
                            # Patch runCIRModel() to read cirModel select
```

---

## API Response Shapes (verified by reading webapp.py + markov_chains.py)

### POST /api/markov_chain — mode=steady_state

Request:
```json
{ "mode": "steady_state" }
```
Response `data.result`:
```json
{
  "mode": "steady_state",
  "steady_state": [0.07, 0.12, 0.22, 0.25, 0.15, 0.12, 0.05, 0.02],
  "ratings": ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]
}
```
- `steady_state` is a flat `float[]` of length 8 (S&P default matrix) or N (custom matrix)
- `ratings` is a parallel `string[]` — use as bar chart x-axis labels
- Plotly chart type: `bar` (x: ratings, y: steady_state * 100 as %)

### POST /api/markov_chain — mode=absorption

Request:
```json
{ "mode": "absorption" }
```
Response `data.result` (success):
```json
{
  "mode": "absorption",
  "transient_indices": [0, 1, 2, 3, 4, 5, 6],
  "absorbing_indices": [7],
  "fundamental_matrix": [[...], ...],
  "absorption_matrix": [[...], ...]
}
```
Response `data.result` (no absorbing states — S&P detection threshold is P[i,i] > 0.9999):
```json
{ "mode": "absorption", "error": "No absorbing states detected" }
```

**CRITICAL**: The S&P default matrix may trigger the "No absorbing states" path because the D (default) state has P[D,D] ≈ 0.9 (not 0.9999). The UI must handle the `error` field without crashing. For a meaningful demo, the user should enter a custom 3-state matrix with a true absorbing state.

- `absorption_matrix` shape: `n_transient x n_absorbing` (list-of-lists)
- Plotly chart type: `heatmap` (z: absorption_matrix, colorscale: 'Blues')

### POST /api/markov_chain — mode=mdp

Request:
```json
{ "mode": "mdp", "gamma": 0.95, "n_periods": 1000 }
```
Response `data.result`:
```json
{
  "mode": "mdp",
  "optimal_policy": [0, 1, 2],
  "value_function": [12.5, 10.0, 15.5],
  "convergence_iterations": 47,
  "converged": true,
  "states": ["risk_off", "neutral", "risk_on"],
  "actions": ["underweight", "neutral", "overweight"],
  "gamma": 0.95
}
```
- `optimal_policy` is `int[]` of length 3 — index into `actions`
- `value_function` is `float[]` of length 3
- Plotly chart type: `bar` for V* (x: states, y: value_function)
- Policy display: cards showing `states[i]` → `actions[optimal_policy[i]]`

### POST /api/interest_rate_model — model=vasicek

Request:
```json
{ "model": "vasicek", "r0": 0.053, "kappa": 0.5, "theta": 0.06, "sigma": 0.02 }
```
Response `data.result`:
```json
{
  "model": "Vasicek (1977)",
  "params": { "r0": 0.053, "kappa": 0.5, "theta": 0.06, "sigma": 0.02 },
  "feller_condition_satisfied": true,
  "feller_ratio": null,
  "yield_curve": [
    { "maturity": 0.25, "bond_price": 0.9872, "spot_rate": 0.0513 },
    ...
  ]
}
```

**Key difference from CIR**: `feller_ratio` is always `null` for Vasicek (Feller does not apply). The existing `fellerBadge` logic in `runCIRModel()` already handles this gracefully — `feller: true` renders the green badge, and `null` for feller_ratio is ignored by the display code. The `yield_curve` array structure is **identical** to CIR: `[{ maturity, bond_price, spot_rate }]`.

**Vasicek defaults** (from webapp.py line 1625–1628): `r0=0.053, kappa=0.5, theta=0.06, sigma=0.02`. These differ from CIR defaults (`kappa=1.5, theta=0.05, sigma=0.1`). The UI should use these as default values when Vasicek is selected.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tab switching | Custom JS event system | `switchStochasticTab()` already exists | Handles all selector patterns correctly |
| Chart rendering | Custom SVG/Canvas charts | `Plotly.newPlot()` already loaded | Plotly handles responsive resize, tooltip, legend |
| Heatmap for absorption/transition matrix | Custom grid renderer | Plotly `type:'heatmap'` with `texttemplate` | Already used in Credit Risk markovHeatmap |
| Error display | Custom alert components | `renderAlert(msg, type)` already exists | Consistent styling, XSS-safe |
| HTML escaping | Manual string replace | `escapeHTML(str)` already exists | Covers all special characters |

**Key insight:** Every rendering primitive needed for Phase 5 already exists in `stochasticModels.js`. The only new code is application logic calling these primitives.

---

## Common Pitfalls

### Pitfall 1: S&P default matrix has no absorbing state at the absorption threshold

**What goes wrong:** User opens Markov tab, selects "Absorption" mode, clicks Run with default inputs, gets `{error: "No absorbing states detected"}` — appears broken.

**Why it happens:** The S&P matrix D row has P[D,D] ≈ 0.9, not > 0.9999. The absorbing state detector requires `P[i,i] > 0.9999`.

**How to avoid:** Provide a default custom matrix in the absorption form that has a genuine absorbing state. A simple 3-state example: `[[0.7, 0.2, 0.1], [0.3, 0.5, 0.2], [0, 0, 1.0]]` (state 2 is absorbing). Pre-fill the textarea with this.

**Warning signs:** The `error` field appears in the result even on HTTP 200.

### Pitfall 2: Plotly chart ID collision if results div is re-rendered

**What goes wrong:** User runs Markov twice. The `resultsDiv.innerHTML = ...` wipes the DOM including the Plotly chart div. `Plotly.newPlot` on the new div works correctly. However if the Plotly div ID (`markovSteadyChart`) is used elsewhere in the page, traces stack.

**How to avoid:** Use IDs that include the sub-tab prefix: `markovSteadyChart`, `markovAbsorptionHeatmap`, `markovMDPChart`. The existing phase decision note confirms this is a past issue: `[Phase 03-05]: Heston DOM ID collision`. Always use unique, namespaced IDs.

### Pitfall 3: Vasicek feller_ratio is null — badge logic must handle it

**What goes wrong:** The existing `fellerBadge` code reads `r.feller_condition_satisfied` (a boolean). For Vasicek this is `true`. If any downstream code tries `r.feller_ratio.toFixed(2)` it crashes because `feller_ratio` is `null`.

**How to avoid:** The existing `runCIRModel()` already guards: it only renders feller_ratio in the badge text if `feller` is truthy, and the badge only checks the boolean. Vasicek's `feller_ratio: null` is handled safely. No extra guard needed, but do not add code that calls `.toFixed()` on `feller_ratio` directly.

### Pitfall 4: markovMode select must be read before building payload

**What goes wrong:** `showMarkovForm()` hides forms but the run function doesn't re-read the mode select — it hardcodes `mode: 'steady_state'`.

**How to avoid:** Always read `document.getElementById('markovMode').value` inside `runMarkovChain()` to determine which payload to build. The mode select drives both form visibility and payload construction.

### Pitfall 5: Vasicek input defaults need updating when model selector changes

**What goes wrong:** User switches from CIR to Vasicek but the input fields still show CIR defaults (kappa=1.5, sigma=0.1). A Vasicek sigma of 0.1 (10%) is unrealistically high and produces extreme curves.

**How to avoid:** Add an `onchange` handler to the `cirModel` select that swaps the default values. CIR defaults: `kappa=1.5, theta=5.0%, sigma=10%`. Vasicek defaults: `kappa=0.5, theta=6.0%, sigma=2.0%`.

---

## Code Examples

### Existing Plotly heatmap pattern (from runCreditRisk, stochasticModels.js:610)

```javascript
// Source: static/js/stochasticModels.js lines 610-624
Plotly.newPlot('markovHeatmap', [{
    z: mr.transition_matrix_n,
    x: labels,
    y: labels,
    type: 'heatmap',
    colorscale: 'Blues',
    text: mr.transition_matrix_n.map(row => row.map(v => (v * 100).toFixed(1) + '%')),
    texttemplate: '%{text}',
    showscale: true
}], {
    title: 'S&P 1-Year Rating Transition Matrix',
    height: 420,
    margin: { t: 50, l: 80, r: 20, b: 80 }
}, { responsive: true });
```

### Existing bar chart pattern (from runRegimeDetection, stochasticModels.js:88)

```javascript
// Source: static/js/stochasticModels.js — Plotly.newPlot standard call
Plotly.newPlot('chartId', [{
    x: labels,
    y: values,
    type: 'bar',
    marker: { color: '#667eea' }
}], {
    title: 'Steady-State Distribution',
    xaxis: { title: 'Rating' },
    yaxis: { title: 'Probability (%)', tickformat: '.2f' },
    height: 350,
    margin: { t: 40, l: 70, r: 20, b: 50 }
}, { responsive: true });
```

### Vasicek payload (from webapp.py line 1624-1637)

```javascript
// Model selector determines which model branch runs
const model = document.getElementById('cirModel')?.value || 'cir';
const payload = calibrate
    ? { r0, calibrate_to_treasuries: true }
    : { model, r0, kappa, theta, sigma,
        maturities: [0.083, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30] };
```

### MDP policy display pattern (new, modeled on RL tab)

```javascript
// states and actions come from data.result
const policyCards = r.states.map((state, i) =>
    `<div style="background:#f8f9fa; padding:10px; border-radius:4px; text-align:center;">
        <div style="font-weight:bold;">${escapeHTML(state)}</div>
        <div style="font-size:12px; color:#667eea;">${escapeHTML(r.actions[r.optimal_policy[i]])}</div>
    </div>`
).join('');
```

---

## Validation Architecture

`workflow.nyquist_validation` is not set in `.planning/config.json` — treat as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (detected: `tests/` directory, `conftest.py`, multiple `test_*.py` files) |
| Config file | none — `pytest` run from repo root discovers `tests/` automatically |
| Quick run command | `pytest tests/test_markov_route.py tests/test_vasicek_model.py -x -q` |
| Full suite command | `pytest tests/ -x -q --ignore=tests/test_math05_benchmarks.py` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MARKOV-01 | `mode=steady_state` returns 8-float list summing to 1 | integration | `pytest tests/test_markov_route.py::test_steady_state_mode -x` | ✅ |
| MARKOV-02 | `mode=absorption` returns absorption_matrix list-of-lists | integration | `pytest tests/test_markov_route.py::test_absorption_mode -x` | ✅ |
| MARKOV-03 | Transition heatmap renders via nstep n=1 call | smoke (browser) | manual: open Markov tab, run steady_state, verify heatmap appears | N/A |
| MARKOV-04 | MDP inputs (gamma, n_periods) accepted by route | integration | `pytest tests/test_markov_route.py::test_mdp_mode -x` | ✅ |
| MARKOV-05 | `mode=mdp` returns optimal_policy length 3, value_function length 3 | integration | `pytest tests/test_markov_route.py::test_mdp_mode -x` | ✅ |
| MARKOV-06 | Sub-tab button and content div exist in HTML | smoke (browser) | manual: load page, click Markov Chain tab, verify form visible | N/A |
| RATE-02 | Vasicek route returns yield_curve with correct structure | integration | `pytest tests/test_vasicek_model.py::test_vasicek_route -x` | ✅ |
| RATE-03 | Yield curve Plotly chart renders for Vasicek | smoke (browser) | manual: select Vasicek, click Run, verify chart appears | N/A |

### Sampling Rate

- **Per task commit:** `pytest tests/test_markov_route.py tests/test_vasicek_model.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q --ignore=tests/test_math05_benchmarks.py`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

None — existing test infrastructure covers all backend requirements. The HTML and JS changes have no automated unit tests (browser integration tests are out of scope). Validation is via curl smoke tests and manual browser verification.

#### Curl smoke tests for validation

```bash
# MARKOV-01: steady_state returns 8 floats summing to 1
curl -s -X POST http://localhost:5001/api/markov_chain \
  -H 'Content-Type: application/json' \
  -d '{"mode":"steady_state"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
pi = d['result']['steady_state']
print('PASS' if abs(sum(pi) - 1.0) < 1e-4 else 'FAIL', 'sum=', sum(pi))"

# MARKOV-02: absorption returns absorption_matrix
curl -s -X POST http://localhost:5001/api/markov_chain \
  -H 'Content-Type: application/json' \
  -d '{"mode":"absorption","transition_matrix":[[0.7,0.2,0.1],[0.3,0.5,0.2],[0,0,1.0]]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'absorption_matrix' in d['result'] else 'FAIL', d['result'].get('error',''))"

# MARKOV-05: mdp returns 3-element policy
curl -s -X POST http://localhost:5001/api/markov_chain \
  -H 'Content-Type: application/json' \
  -d '{"mode":"mdp","gamma":0.95}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
p = d['result']['optimal_policy']
print('PASS' if len(p) == 3 else 'FAIL', p)"

# RATE-02: Vasicek route returns yield_curve
curl -s -X POST http://localhost:5001/api/interest_rate_model \
  -H 'Content-Type: application/json' \
  -d '{"model":"vasicek","r0":0.053,"kappa":0.5,"theta":0.06,"sigma":0.02}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); r=d['result']; print('PASS' if r['feller_ratio'] is None and len(r['yield_curve'])>0 else 'FAIL')"
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Separate Markov endpoint per mode | Unified `/api/markov_chain` with `mode` dispatch | All modes reachable from single URL; mode drives both payload and response shape |
| CIR-only interest rate tab | `model` field in payload selects CIR vs Vasicek | Same inputs, different defaults; `feller_ratio: null` signals Vasicek |

---

## Open Questions

1. **Absorption mode with S&P default matrix**
   - What we know: S&P D-state has P[D,D] ≈ 0.90, below the 0.9999 threshold. Default inputs will return `{error: "No absorbing states detected"}`.
   - What's unclear: Should the UI silently switch to showing a "no absorbing states" explanation, or should the default form pre-fill a custom 3-state matrix with a genuine absorbing state?
   - Recommendation: Pre-fill the matrix textarea with the 3-state example `[[0.7,0.2,0.1],[0.3,0.5,0.2],[0,0,1.0]]` as default and add a note "Enter a matrix with at least one absorbing state (row sums to 1 with P[i,i]=1)."

2. **Transition matrix input UX**
   - What we know: The backend accepts `transition_matrix` as a nested JSON array. No existing stochastic sub-tab uses a textarea input for matrix entry.
   - What's unclear: Whether a `<textarea>` with JSON format is acceptable UX or if a grid input is needed.
   - Recommendation: Use a `<textarea>` with JSON placeholder and parse via `JSON.parse()`. Add a validation check that rows sum to 1 before sending. This matches the simplest existing pattern (other sub-tabs use plain `<input type="number">`).

---

## Sources

### Primary (HIGH confidence)

- `static/js/stochasticModels.js` — complete source read: switchStochasticTab pattern, runCIRModel (lines 379–477), runCreditRisk (lines 482–630), renderAlert, escapeHTML, Plotly call signatures
- `templates/index.html` — lines 1217–1556: all existing stochastic sub-tab HTML structure, element IDs, form field names, button onclick patterns
- `webapp.py` — lines 1592–1783: `/api/interest_rate_model` and `/api/markov_chain` route implementations, request/response shapes
- `src/analytics/markov_chains.py` — complete source: `steady_state_distribution`, `absorption_probabilities`, `portfolio_mdp_value_iteration` — exact return dict keys and shapes
- `tests/test_markov_route.py` — all 7 integration tests confirm expected field names
- `tests/test_vasicek_model.py` — confirms `feller_ratio: None` and `yield_curve` structure

### Secondary (MEDIUM confidence)

- `.planning/STATE.md` — decision log confirming Phase 02-02 and Phase 03-05 decisions that directly constrain this phase

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in project, no installation decisions
- Architecture patterns: HIGH — derived directly from existing code, not documentation
- API response shapes: HIGH — read from webapp.py and markov_chains.py source
- Pitfalls: HIGH — three of five pitfalls are documented in STATE.md decision log; two (S&P absorption, Vasicek defaults) derived from reading source

**Research date:** 2026-03-08
**Valid until:** Stable indefinitely (all findings are from local source files, not external dependencies)
