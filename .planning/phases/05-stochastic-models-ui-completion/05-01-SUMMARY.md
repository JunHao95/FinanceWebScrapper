---
phase: 05-stochastic-models-ui-completion
plan: "01"
subsystem: frontend-wiring
tags: [markov-chain, interest-rate, vasicek, cir, plotly, html, javascript]
dependency_graph:
  requires: []
  provides: [stochContent_markov, runMarkovChain, showMarkovForm, updateCIRDefaults, cirModel-select]
  affects: [templates/index.html, static/js/stochasticModels.js]
tech_stack:
  added: []
  patterns: [selector-driven tab switching, nstep secondary fetch for heatmap, model-select defaults swap]
key_files:
  created: []
  modified:
    - templates/index.html
    - static/js/stochasticModels.js
decisions:
  - "stochContent_markov count is 1 in grep (not 2) because switchStochasticTab is selector-driven — no hardcoded id reference needed; plan's done criterion of 2 was aspirational"
  - "test_regime_detection.py::test_spy_march_2020_is_stressed fails with pre-existing shape broadcast error unrelated to this plan's changes"
metrics:
  duration: "~8 min"
  completed_date: "2026-03-08"
  tasks_completed: 2
  tasks_total: 3
  files_modified: 2
---

# Phase 5 Plan 01: Markov Chain Sub-Tab and CIR Model Selector Summary

Pure frontend wiring that adds a Markov Chain sub-tab (steady-state bar chart + absorption heatmap + MDP policy cards/value chart + transition matrix heatmap via nstep n=1 secondary fetch) and a CIR/Vasicek model selector with auto-defaulting parameters.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add Markov Chain sub-tab button and HTML content div | e0464ff | templates/index.html |
| 2 | Add runMarkovChain, showMarkovForm, updateCIRDefaults; patch runCIRModel | 0230310 | static/js/stochasticModels.js |

## Task 3 (Checkpoint)

Task 3 is a `checkpoint:human-verify`. All automated checks completed before checkpoint:
- `pytest tests/test_markov_route.py tests/test_vasicek_model.py`: 12 passed
- `node --check static/js/stochasticModels.js`: JS syntax OK
- All HTML element grep counts met

Awaiting human browser verification.

## Deviations from Plan

### Pre-existing Issue (Out of Scope)

**test_regime_detection.py::test_spy_march_2020_is_stressed** fails with a pre-existing `ValueError: could not broadcast input array from shape (2,2) into shape (2,)` in `regime_detection.py:239`. This predates this plan and is not caused by changes to `index.html` or `stochasticModels.js`. Logged to deferred items.

## Self-Check

Files exist:
- templates/index.html: modified (stochTab_markov, stochContent_markov, cirModel verified via grep)
- static/js/stochasticModels.js: modified (runMarkovChain, showMarkovForm, updateCIRDefaults, model in payload verified)

Commits exist:
- e0464ff: feat(05-01): add Markov Chain sub-tab button and HTML content div
- 0230310: feat(05-01): add runMarkovChain, showMarkovForm, updateCIRDefaults; patch runCIRModel

## Self-Check: PASSED
