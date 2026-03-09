---
phase: 05-stochastic-models-ui-completion
verified: 2026-03-08T00:00:00Z
status: human_needed
score: 5/5 must-haves verified
human_verification:
  - test: "Open Stochastic Models tab, click Markov Chain sub-tab, leave matrix blank, click Run Markov Analysis"
    expected: "Steady-state distribution bar chart renders with S&P rating labels on x-axis; Transition Matrix heatmap renders below it in Blues colorscale"
    why_human: "Plotly rendering, chart labels, and visual output require browser execution"
  - test: "On Markov Chain sub-tab, change Analysis Mode to Absorption Probabilities, verify pre-filled matrix [[0.7,0.2,0.1],[0.3,0.5,0.2],[0,0,1.0]] is shown, click Run"
    expected: "Absorption Probability Matrix heatmap renders with transient/absorbing state labels"
    why_human: "Chart rendering and correct label display require browser execution"
  - test: "On Markov Chain sub-tab, change Analysis Mode to MDP — Portfolio Value Iteration, click Run"
    expected: "Policy cards appear for risk_off/neutral/risk_on states showing their optimal actions; V* bar chart renders"
    why_human: "Card layout and chart output require browser execution"
  - test: "Open CIR Interest Rate sub-tab, select Vasicek (1977) from the Model dropdown"
    expected: "kappa field updates to 0.5, sigma updates to 2.0, then click Run — Vasicek yield curve renders with Feller badge showing green (satisfied)"
    why_human: "Default-swap behavior (updateCIRDefaults), Feller badge colour, and yield curve chart require browser execution"
---

# Phase 5: Stochastic Models UI Completion — Verification Report

**Phase Goal:** Every stochastic model feature that has a backend API is reachable by a user from the UI — Markov Chain modes (steady-state, absorption, MDP) have an interactive sub-tab, and the Interest Rate sub-tab exposes both CIR and Vasicek via a model selector.
**Verified:** 2026-03-08
**Status:** human_needed — all automated checks pass; browser smoke-tests remain
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A user can open the Stochastic Models tab, navigate to a Markov Chain sub-tab, enter a transition matrix, and see the steady-state distribution rendered as a Plotly bar chart | ? HUMAN | `stochTab_markov` button present (index.html:1248); `runMarkovChain()` defined (stochasticModels.js:973); Plotly.newPlot call for `markovSteadyChart` confirmed (js:1032); backend 12/12 tests pass |
| 2 | A user can switch to absorption mode, enter an absorbing Markov chain matrix, and see absorption probabilities rendered as a Plotly heatmap | ? HUMAN | `markovForm_absorption` div present (index.html:1473) with pre-filled matrix; `runMarkovChain()` absorption branch renders `markovAbsorptionHeatmap` (js:1097–1110); backend `test_absorption_mode` passes |
| 3 | A user can switch to MDP mode, click Run, and see optimal policy cards and a V* value-function bar chart | ? HUMAN | `markovForm_mdp` div present (index.html:1485); MDP branch renders policy cards and `markovMDPChart` (js:1118–1147); backend `test_mdp_mode` passes |
| 4 | A user can select Vasicek from a model selector in the Interest Rate sub-tab, click Run, and see a Vasicek yield curve rendered as a Plotly chart | ? HUMAN | `cirModel` select present (index.html:1381–1384); `const model = document.getElementById('cirModel')?.value` read in `runCIRModel()` (js:385); `model` included in non-calibrate payload (js:396); backend `test_vasicek_route` passes |
| 5 | A user can see the transition matrix as a color heatmap alongside the steady-state distribution | ? HUMAN | `markovTransitionHeatmap` div present (index.html:1508); secondary fetch `mode:'nstep', n:1` to `/api/markov_chain` implemented (js:1046–1077); `Plotly.newPlot('markovTransitionHeatmapPlot', ...)` with `colorscale:'Blues'` confirmed (js:1060); backend `test_nstep_mode` passes |

**Score:** 5/5 truths have full automated evidence — all pending human browser confirmation only

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `templates/index.html` | stochTab_markov button + stochContent_markov div with three mode-panel sub-forms + cirModel select in stochContent_cir + markovTransitionHeatmap div | VERIFIED | All elements confirmed: line 1248 (button), 1443 (content div), 1459/1473/1485 (mode forms), 1381 (cirModel select), 1508 (heatmap div) |
| `static/js/stochasticModels.js` | runMarkovChain() and showMarkovForm() functions; runCIRModel() reads cirModel select; nstep n=1 fetch renders transition_matrix_n as heatmap | VERIFIED | `showMarkovForm` at line 966, `runMarkovChain` at line 973, `updateCIRDefaults` at line 1158, `cirModel` read at line 385, nstep secondary fetch at lines 1046–1077, heatmap rendered at lines 1059–1073. JS syntax: `node --check` passes. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| stochContent_markov Run button | /api/markov_chain | runMarkovChain() fetch POST | WIRED | `onclick="runMarkovChain()"` (index.html:1504); `fetch('/api/markov_chain', { method:'POST', ... })` (js:1004–1008) |
| runMarkovChain() steady_state branch | /api/markov_chain mode=nstep n=1 | second fetch after steady_state chart renders | WIRED | `{ mode: 'nstep', n: 1 }` payload at js:1046; `fetch('/api/markov_chain', ...)` at js:1048 |
| cirModel select | /api/interest_rate_model model field | runCIRModel() payload construction | WIRED | `cirModel?.value` read at js:385; `model` included in payload at js:396 (`{ model, r0, kappa, theta, sigma, maturities: [...] }`) |
| markovMode select | showMarkovForm() | onchange handler | WIRED | `onchange="showMarkovForm(this.value)"` (index.html:1451); function toggles display of markovForm_* divs (js:966–971) |
| cirModel select | updateCIRDefaults() | onchange handler | WIRED | `onchange="updateCIRDefaults(this.value)"` (index.html:1381); function sets cirKappa/cirTheta/cirSigma/cirR0 (js:1158–1169) |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| MARKOV-01 | 05-01-PLAN.md | User can input a transition matrix and compute steady-state distribution | SATISFIED | `markovMatrixSS` textarea + `runMarkovChain()` steady_state branch; backend `test_steady_state_mode` passes |
| MARKOV-02 | 05-01-PLAN.md | User can compute absorption probabilities for absorbing Markov chains | SATISFIED | `markovMatrixAbs` textarea + absorption branch in `runMarkovChain()`; backend `test_absorption_mode` passes |
| MARKOV-03 | 05-01-PLAN.md | User can visualize state transition diagram or heatmap of transition matrix | SATISFIED | Secondary `nstep n=1` fetch renders Blues heatmap in `markovTransitionHeatmap` div; backend `test_nstep_mode` passes |
| MARKOV-04 | 05-01-PLAN.md | User can define a portfolio rebalancing MDP (states, actions, rewards) | SATISFIED | `markovForm_mdp` panel with gamma + max-iterations inputs; MDP payload sent to `/api/markov_chain` with `mode:'mdp'` |
| MARKOV-05 | 05-01-PLAN.md | User can compute optimal policy via value iteration for the MDP | SATISFIED | MDP branch renders policy cards + V* bar chart from `r.optimal_policy` and `r.value_function`; backend `test_mdp_mode` passes |
| MARKOV-06 | 05-01-PLAN.md | Markov/MDP results display in dedicated UI sub-tab with interactive parameters | SATISFIED | `stochTab_markov` sub-tab button present; `stochContent_markov` div contains all three mode sub-forms; `switchStochasticTab('markov')` wires tab switching |
| RATE-02 | 05-01-PLAN.md | User can simulate Vasicek interest rate paths with chosen parameters | SATISFIED | `cirModel` dropdown with `value="vasicek"` option; `model` field sent in payload; backend `test_vasicek_route` passes |
| RATE-03 | 05-01-PLAN.md | User can view yield curve generated from the selected model | SATISFIED | `runCIRModel()` renders Plotly yield curve chart from API response regardless of CIR or Vasicek selection; backend `test_vasicek_route` confirms yield_curve array returned |

No orphaned requirements — all 8 requirement IDs declared in the plan are accounted for and evidenced.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `static/js/stochasticModels.js` | 1076 | `console.warn(...)` in nstep catch block | Info | Non-fatal; intentional silent fallback if secondary heatmap fetch fails — does not block primary chart |

No blocker anti-patterns found. No TODO/FIXME/placeholder markers in modified files. No stub implementations (all branches produce real Plotly renders from real API data).

---

### Human Verification Required

#### 1. Markov Steady-State + Transition Heatmap

**Test:** Open the app in a browser. Click the Stochastic Models main tab. Click the "Markov Chain" sub-tab button (visible at the right end of the sub-tab row). Leave the Transition Matrix textarea blank. Click "Run Markov Analysis".
**Expected:** A "Steady-State Distribution" bar chart appears with S&P rating labels (AAA, AA, A, BBB, BB, B, CCC, D) on the x-axis. Below it, a "Transition Matrix" heatmap in Blues colorscale appears showing 1-step transition probabilities.
**Why human:** Plotly chart rendering, axis label content, and visual layout cannot be verified without a browser.

#### 2. Absorption Mode

**Test:** On the Markov Chain sub-tab, change the Analysis Mode dropdown to "Absorption Probabilities". Confirm the textarea is pre-filled with `[[0.7,0.2,0.1],[0.3,0.5,0.2],[0,0,1.0]]`. Click "Run Markov Analysis".
**Expected:** An "Absorption Probability Matrix" heatmap renders with transient states on the y-axis and absorbing state on the x-axis.
**Why human:** Pre-fill content visibility and heatmap label accuracy require browser execution.

#### 3. MDP Mode

**Test:** On the Markov Chain sub-tab, change the Analysis Mode dropdown to "MDP — Portfolio Value Iteration". Confirm gamma defaults to 0.95 and Max Iterations to 1000. Click "Run Markov Analysis".
**Expected:** Policy cards appear for three states (risk_off, neutral, risk_on) each showing an action label. A "V* — Optimal Value Function" bar chart renders below.
**Why human:** Policy card layout and value function chart require browser execution.

#### 4. Vasicek Model Selector

**Test:** Click the CIR Interest Rate sub-tab. Locate the "Model" dropdown. Select "Vasicek (1977)". Confirm the kappa field changes to 0.5 and sigma changes to 2.0%. Click "Compute Yield Curve".
**Expected:** A yield curve chart renders; the Feller condition badge shows green/satisfied (Vasicek always satisfies feller_condition_satisfied=true). Chart title contains "Vasicek".
**Why human:** updateCIRDefaults DOM mutation, Feller badge colour, and chart title content require browser execution.

---

### Gaps Summary

No gaps. All five observable truths have complete automated evidence across three levels (existence, substance, wiring). The eight requirement IDs (MARKOV-01 through MARKOV-06, RATE-02, RATE-03) are all satisfied. Backend tests are 12/12 green. JS syntax is valid. The only remaining work is human browser confirmation of visual output — which is expected for a UI-wiring phase and does not represent a code deficiency.

---

_Verified: 2026-03-08_
_Verifier: Claude (gsd-verifier)_
