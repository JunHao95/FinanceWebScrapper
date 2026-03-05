---
phase: 02-backend-completeness
plan: 01
subsystem: analytics
tags: [markov-chains, numpy, eigendecomposition, mdp, value-iteration, absorption]

# Dependency graph
requires:
  - phase: 02-backend-completeness
    provides: credit_transitions.py with n_year_transition and SP_TRANSITION_MATRIX

provides:
  - steady_state_distribution function (eigendecomposition with power-iteration fallback)
  - absorption_probabilities function (fundamental matrix via linalg.solve)
  - portfolio_mdp_value_iteration function (Bellman backup, action-dependent transitions)
affects: [02-04-markov-chain-route]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD RED-GREEN: test scaffold committed first (c025c8d), implementation committed second (e174d68)"
    - "Eigendecomposition pattern for steady-state mirrored from regime_detection.py lines 295-298"
    - "linalg.solve preferred over linalg.inv to avoid singular matrix errors in absorption calc"
    - "MDP action-dependent transition matrices P[action, state, next_state]"

key-files:
  created:
    - src/analytics/markov_chains.py
    - tests/test_markov_chains.py
  modified: []

key-decisions:
  - "Absorption detection threshold: P[i,i] > 0.9999 and row_sum within 1e-6 of 1.0"
  - "linalg.solve(I-Q, R) for absorption matrix B; linalg.inv(I-Q) for display of N (fundamental matrix)"
  - "Power iteration fallback when eigenvector imaginary part exceeds 1e-6"
  - "MDP default reward matrix is symmetric: risk_off+underweight=+2, risk_on+overweight=+2, cross-pairs=-2"
  - "gamma capped at 0.999 and n_periods capped at 10000 as guard inputs"

patterns-established:
  - "Standalone analytics module pattern: no Flask imports, no live-data coupling, pure numpy"
  - "Error dict return (not raise) for graceful error signaling in analytical functions"

requirements-completed: [MARKOV-01, MARKOV-02, MARKOV-03, MARKOV-04, MARKOV-05, CREDIT-02, CREDIT-03]

# Metrics
duration: 5min
completed: 2026-03-05
---

# Phase 02 Plan 01: Markov Chain Analytics Module Summary

**Three standalone numpy Markov chain functions (steady-state, absorption probabilities, portfolio MDP) with 8 green pytest tests covering eigendecomposition, fundamental matrix, and Bellman value iteration.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-05T00:00:00Z
- **Completed:** 2026-03-05T00:05:00Z
- **Tasks:** 2 (TDD RED already committed as c025c8d; GREEN committed as e174d68)
- **Files modified:** 2

## Accomplishments
- `steady_state_distribution`: eigendecomposition of P.T for left eigenvector at eigenvalue=1, with power-iteration fallback for chains with non-negligible imaginary components
- `absorption_probabilities`: detects absorbing states, builds Q/R sub-matrices, uses linalg.solve for B (absorption matrix) and linalg.inv for N (fundamental matrix); returns `{'error': ...}` for non-absorbing chains
- `portfolio_mdp_value_iteration`: Bellman backup with action-dependent 3x3x3 transition tensor; default symmetric reward matrix; converges in ~371 iterations for gamma=0.95, tol=1e-8
- All 8 tests pass; full regression suite (54 tests) passes with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Write test scaffold (TDD RED)** - `c025c8d` (test) — pre-existing commit
2. **Task 2: Implement markov_chains.py (TDD GREEN)** - `e174d68` (feat)

## Files Created/Modified
- `src/analytics/markov_chains.py` - Three exported analytics functions, no Flask dependency
- `tests/test_markov_chains.py` - 8 pytest tests covering all three functions and edge cases

## Decisions Made
- Used `linalg.solve(I-Q, R)` instead of `linalg.inv(I-Q) @ R` for numerical stability when computing the absorption matrix B; kept `linalg.inv` only for returning the fundamental matrix N for display
- Absorption state detection uses `P[i,i] > 0.9999` threshold to handle floating-point stochastic matrices
- Power iteration fallback for steady-state covers degenerate chains where eigendecomposition yields large imaginary parts
- MDP `gamma` capped at 0.999 (prevents division-by-zero in infinite-horizon value) and `n_periods` capped at 10000

## Deviations from Plan

None - plan executed exactly as written. Implementation file was already present from prior partial execution; committed cleanly as TDD GREEN step.

## Issues Encountered
None - all 8 tests passed on first run after implementation. Full regression suite (54 tests) clean.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `steady_state_distribution`, `absorption_probabilities`, `portfolio_mdp_value_iteration` ready for Plan 02-04 (`/api/markov_chain` Flask route)
- `n_year_transition` imported from `credit_transitions.py` in tests (confirmed working, no duplication needed)
- No blockers for Plan 02-04

---
*Phase: 02-backend-completeness*
*Completed: 2026-03-05*
