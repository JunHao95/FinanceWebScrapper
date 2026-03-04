"""
Tests for src/analytics/markov_chains.py

Covers:
    - steady_state_distribution: eigendecomposition-based steady-state vector
    - absorption_probabilities: fundamental matrix and absorption matrix
    - portfolio_mdp_value_iteration: Bellman value iteration for portfolio MDP

All functions are standalone (no Flask, no live data) and independently testable.
"""
import numpy as np
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.analytics.markov_chains import (
    steady_state_distribution,
    absorption_probabilities,
    portfolio_mdp_value_iteration,
)
from src.analytics.credit_transitions import SP_TRANSITION_MATRIX, n_year_transition


# ---------------------------------------------------------------------------
# steady_state_distribution
# ---------------------------------------------------------------------------

def test_steady_state_sums_to_one():
    """steady_state_distribution(SP_TRANSITION_MATRIX) must sum to 1.0 within 1e-6."""
    pi = steady_state_distribution(SP_TRANSITION_MATRIX)
    assert abs(pi.sum() - 1.0) < 1e-6, (
        f"Steady-state vector sums to {pi.sum():.10f}, expected 1.0 within 1e-6"
    )


def test_steady_state_known_solution():
    """
    2-state ergodic chain [[0.7, 0.3], [0.4, 0.6]] has analytic steady state:
    pi = [0.4/(0.3+0.4), 0.3/(0.3+0.4)] = [4/7, 3/7] ≈ [0.5714, 0.4286]
    """
    P2 = np.array([[0.7, 0.3], [0.4, 0.6]])
    pi = steady_state_distribution(P2)
    assert abs(pi.sum() - 1.0) < 1e-6, "Steady-state does not sum to 1.0"
    assert abs(pi[0] - 4/7) < 1e-3, (
        f"pi[0]={pi[0]:.6f}, expected ~{4/7:.6f} (tolerance 1e-3)"
    )
    assert abs(pi[1] - 3/7) < 1e-3, (
        f"pi[1]={pi[1]:.6f}, expected ~{3/7:.6f} (tolerance 1e-3)"
    )


# ---------------------------------------------------------------------------
# absorption_probabilities
# ---------------------------------------------------------------------------

def test_absorption_rows_sum_to_one():
    """
    3-state absorbing chain: states 0, 1 transient; state 2 absorbing.
    absorption_matrix rows must each sum to 1.0 within 1e-6.
    """
    P_absorbing = np.array([
        [0.5, 0.3, 0.2],
        [0.2, 0.4, 0.4],
        [0.0, 0.0, 1.0],  # absorbing
    ])
    result = absorption_probabilities(P_absorbing)
    assert 'error' not in result, f"Unexpected error: {result.get('error')}"
    B = np.array(result['absorption_matrix'])
    row_sums = B.sum(axis=1)
    for i, rs in enumerate(row_sums):
        assert abs(rs - 1.0) < 1e-6, (
            f"absorption_matrix row {i} sums to {rs:.10f}, expected 1.0 within 1e-6"
        )


def test_absorption_no_absorbing_states():
    """
    Non-absorbing ergodic chain must return a dict with 'error' key (not raise).
    """
    P_ergodic = np.array([
        [0.7, 0.2, 0.1],
        [0.1, 0.8, 0.1],
        [0.2, 0.3, 0.5],
    ])
    result = absorption_probabilities(P_ergodic)
    assert isinstance(result, dict), "Result must be a dict"
    assert 'error' in result, (
        f"Expected 'error' key for non-absorbing chain, got keys: {list(result.keys())}"
    )


# ---------------------------------------------------------------------------
# n_year_transition (imported from credit_transitions — not duplicated)
# ---------------------------------------------------------------------------

def test_nstep_matrix_shape():
    """n_year_transition(SP_TRANSITION_MATRIX, 5) returns shape (8, 8)."""
    P5 = n_year_transition(SP_TRANSITION_MATRIX, 5)
    assert P5.shape == (8, 8), f"Expected shape (8, 8), got {P5.shape}"


def test_nstep_matrix_is_list():
    """After .tolist(), n-step matrix is a list-of-lists (JSON serialization ready)."""
    P5 = n_year_transition(SP_TRANSITION_MATRIX, 5)
    P5_list = P5.tolist()
    assert isinstance(P5_list, list), "tolist() result must be a list"
    assert all(isinstance(row, list) for row in P5_list), (
        "Each row must also be a list (list-of-lists)"
    )


# ---------------------------------------------------------------------------
# portfolio_mdp_value_iteration
# ---------------------------------------------------------------------------

def test_mdp_return_keys():
    """portfolio_mdp_value_iteration() must return the required keys."""
    result = portfolio_mdp_value_iteration()
    required_keys = {
        'optimal_policy', 'value_function', 'convergence_iterations',
        'states', 'actions', 'gamma',
    }
    missing = required_keys - set(result.keys())
    assert not missing, f"Missing keys: {missing}"


def test_mdp_policy_correct():
    """
    With default symmetric reward matrix R:
        risk_off state (0): underweight (action 0) should be optimal -> policy[0] == 0
        risk_on  state (2): overweight  (action 2) should be optimal -> policy[2] == 2
    Uses gamma=0.95 (default).
    """
    result = portfolio_mdp_value_iteration(gamma=0.95)
    policy = result['optimal_policy']
    assert policy[0] == 0, (
        f"risk_off state: expected underweight (0), got {policy[0]}. "
        f"Full policy: {policy}"
    )
    assert policy[2] == 2, (
        f"risk_on state: expected overweight (2), got {policy[2]}. "
        f"Full policy: {policy}"
    )
