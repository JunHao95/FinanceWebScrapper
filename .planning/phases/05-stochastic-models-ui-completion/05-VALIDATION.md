---
phase: 5
slug: stochastic-models-ui-completion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — pytest discovers `tests/` from repo root |
| **Quick run command** | `pytest tests/test_markov_route.py tests/test_vasicek_model.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q --ignore=tests/test_math05_benchmarks.py` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_markov_route.py tests/test_vasicek_model.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q --ignore=tests/test_math05_benchmarks.py`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 5-01-01 | 01 | 1 | MARKOV-06 | smoke | `grep -c "stochContent_markov" templates/index.html` | ❌ W0 | ⬜ pending |
| 5-01-02 | 01 | 1 | MARKOV-01..05 | integration | `pytest tests/test_markov_route.py -x -q` | ✅ | ⬜ pending |
| 5-01-03 | 01 | 1 | RATE-02, RATE-03 | integration | `pytest tests/test_vasicek_model.py::test_vasicek_route -x` | ✅ | ⬜ pending |
| 5-01-04 | 01 | 1 | RATE-02 | smoke | `grep -c 'cirModel' templates/index.html` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing test infrastructure covers all backend requirements. HTML/JS changes are verified by grep smoke tests and manual browser verification.

- [ ] Confirm `tests/test_markov_route.py` tests for steady_state, absorption, mdp modes pass before HTML work begins
- [ ] Confirm `tests/test_vasicek_model.py::test_vasicek_route` passes before JS work begins

*If both pass before Wave 1 starts, Wave 0 is satisfied.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Markov sub-tab renders with 3 mode forms | MARKOV-06 | Browser UI interaction | Open app, click Stochastic Models, click Markov Chain sub-tab, verify 3 mode selector buttons visible |
| Steady-state bar chart renders | MARKOV-01 | Plotly rendering | Enter SP_TRANSITION_MATRIX (default), click Steady State, verify bar chart with 8 bars (AAA..D) appears |
| Absorption matrix heatmap renders | MARKOV-02 | Plotly rendering | Enter 3-state absorbing matrix (pre-filled), click Absorption, verify heatmap appears |
| MDP policy + value function renders | MARKOV-04/05 | Plotly rendering | Click MDP tab, click Run, verify policy cards and V* bar chart render |
| Vasicek yield curve renders | RATE-02/03 | Plotly rendering | Open Interest Rate sub-tab, select Vasicek from dropdown, click Run, verify yield curve chart appears |

---

## Curl Smoke Tests

```bash
# MARKOV-01: steady_state returns 8 floats summing to 1
curl -s -X POST http://localhost:5001/api/markov_chain \
  -H 'Content-Type: application/json' \
  -d '{"mode":"steady_state"}' | python3 -c "
import sys, json; d = json.load(sys.stdin)
pi = d['result']['steady_state']
print('PASS' if abs(sum(pi) - 1.0) < 1e-4 else 'FAIL', 'sum=', sum(pi))"

# MARKOV-02: absorption with custom absorbing matrix
curl -s -X POST http://localhost:5001/api/markov_chain \
  -H 'Content-Type: application/json' \
  -d '{"mode":"absorption","transition_matrix":[[1,0,0],[0.3,0.4,0.3],[0,0,1]]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'absorption_matrix' in d['result'] else 'FAIL')"

# MARKOV-04/05: mdp returns optimal_policy
curl -s -X POST http://localhost:5001/api/markov_chain \
  -H 'Content-Type: application/json' \
  -d '{"mode":"mdp"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'optimal_policy' in d['result'] else 'FAIL', d['result'].get('optimal_policy'))"

# RATE-02: Vasicek route returns yield_curve
curl -s -X POST http://localhost:5001/api/interest_rate_model \
  -H 'Content-Type: application/json' \
  -d '{"model":"vasicek","r0":0.03,"kappa":0.5,"theta":0.06,"sigma":0.02}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'yield_curve' in d and d.get('feller_ratio') is None else 'FAIL')"
```

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
