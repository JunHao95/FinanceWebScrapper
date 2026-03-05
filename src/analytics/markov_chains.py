"""
Markov Chain Analytics Module

Standalone mathematical functions for Markov chain analysis:

    * steady_state_distribution  — left eigenvector for eigenvalue=1
    * absorption_probabilities   — fundamental matrix and absorption matrix
    * portfolio_mdp_value_iteration — Bellman value iteration for a 3-state MDP

These functions have no Flask dependency and no credit-domain coupling.
The /api/markov_chain route (Plan 02-04) calls these functions and
imports n_year_transition from credit_transitions.py (no duplicate here).

References:
    - Eigendecomposition pattern from regime_detection.py lines 295–298
    - MDP value iteration (Sutton & Barto, Chapter 4)
    - Absorbing Markov Chains (Kemeny & Snell, 1960)
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Function 1: steady_state_distribution
# ---------------------------------------------------------------------------

def steady_state_distribution(P: np.ndarray) -> np.ndarray:
    """
    Compute the steady-state (stationary) distribution of a Markov chain.

    Uses eigendecomposition to find the left eigenvector corresponding to
    eigenvalue 1. Falls back to power iteration if the imaginary part of
    the selected eigenvector is non-negligible (> 1e-6).

    Args:
        P: (K×K) row-stochastic transition matrix

    Returns:
        pi: (K,) probability vector summing to 1.0

    Notes:
        Pattern mirrors regime_detection.py lines 295–298:
            vals, vecs = np.linalg.eig(P.T)
            stat = np.real(vecs[:, np.argmin(np.abs(vals - 1))])
    """
    P = np.asarray(P, dtype=float)

    # Eigendecomposition of transpose to find left eigenvector
    vals, vecs = np.linalg.eig(P.T)
    idx = np.argmin(np.abs(vals - 1.0))

    # Check if imaginary parts are non-negligible
    imag_norm = np.max(np.abs(np.imag(vecs[:, idx])))
    if imag_norm > 1e-6:
        logger.debug(
            "Imaginary eigenvector components too large (%.2e > 1e-6), "
            "falling back to power iteration.", imag_norm
        )
        # Power iteration fallback: iterate pi = pi @ P for 10000 steps
        K = P.shape[0]
        pi = np.ones(K, dtype=float) / K
        for _ in range(10000):
            pi = pi @ P
        return pi

    stat = np.real(vecs[:, idx])
    stat = np.abs(stat)
    pi = stat / stat.sum()
    return pi


# ---------------------------------------------------------------------------
# Function 2: absorption_probabilities
# ---------------------------------------------------------------------------

def absorption_probabilities(P: np.ndarray) -> Dict:
    """
    Compute absorption probabilities for an absorbing Markov chain.

    Absorbing states are detected as rows where P[i,i] > 0.9999 and
    the row sum is within 1e-6 of 1.0. If no absorbing states are found,
    returns a dict with an 'error' key (does not raise).

    Uses np.linalg.solve(I - Q, R) instead of explicit inv() to avoid
    singular matrix errors. Returns the fundamental matrix N separately
    via np.linalg.inv(I - Q) for display purposes.

    Args:
        P: (K×K) row-stochastic transition matrix

    Returns:
        On success:
            {
                'transient_indices':  list[int],
                'absorbing_indices':  list[int],
                'fundamental_matrix': list[list[float]],  # N = (I - Q)^{-1}
                'absorption_matrix':  list[list[float]],  # B = N @ R
            }
        On no absorbing states:
            {'error': 'No absorbing states detected'}
    """
    P = np.asarray(P, dtype=float)
    K = P.shape[0]

    # Detect absorbing states: diagonal > 0.9999 and row sums to 1
    absorbing = [
        i for i in range(K)
        if P[i, i] > 0.9999 and abs(P[i, :].sum() - 1.0) < 1e-6
    ]

    if not absorbing:
        logger.debug("No absorbing states detected in %dx%d matrix.", K, K)
        return {'error': 'No absorbing states detected'}

    transient = [i for i in range(K) if i not in absorbing]

    if not transient:
        logger.debug("All states are absorbing — no transient states exist.")
        return {'error': 'No transient states detected'}

    # Build Q (transient × transient) and R (transient × absorbing)
    t_idx = np.array(transient)
    a_idx = np.array(absorbing)

    Q = P[np.ix_(t_idx, t_idx)]  # shape (n_t, n_t)
    R = P[np.ix_(t_idx, a_idx)]  # shape (n_t, n_a)

    n_t = len(transient)
    I_Q = np.eye(n_t) - Q  # I - Q

    # B = (I - Q)^{-1} R — solve the linear system for B directly
    try:
        B = np.linalg.solve(I_Q, R)
    except np.linalg.LinAlgError as e:
        logger.warning("linalg.solve failed: %s. Attempting pinv fallback.", e)
        B = np.linalg.pinv(I_Q) @ R

    # N = (I - Q)^{-1} — fundamental matrix (for display)
    try:
        N = np.linalg.inv(I_Q)
    except np.linalg.LinAlgError as e:
        logger.warning("linalg.inv failed for N: %s. Using pinv.", e)
        N = np.linalg.pinv(I_Q)

    return {
        'transient_indices':  transient,
        'absorbing_indices':  absorbing,
        'fundamental_matrix': N.tolist(),
        'absorption_matrix':  B.tolist(),
    }


# ---------------------------------------------------------------------------
# Function 3: portfolio_mdp_value_iteration
# ---------------------------------------------------------------------------

def portfolio_mdp_value_iteration(
    gamma: float = 0.95,
    n_periods: int = 1000,
    transition_override: Optional[List] = None,
    tol: float = 1e-8,
) -> Dict:
    """
    Bellman value iteration for a 3-state portfolio management MDP.

    States:  ['risk_off', 'neutral', 'risk_on']
    Actions: ['underweight', 'neutral', 'overweight']

    The default reward matrix encodes symmetric incentives:
        risk_off + underweight  ->  +2 (rewarded)
        risk_on  + overweight   ->  +2 (rewarded)
        risk_off + overweight   ->  -2 (penalized)
        risk_on  + underweight  ->  -2 (penalized)

    Args:
        gamma:               Discount factor (capped at 0.999)
        n_periods:           Maximum value-iteration steps (capped at 10000)
        transition_override: Optional 3×3×3 list-of-lists-of-lists replacing
                             the default action-dependent transition matrices
        tol:                 Convergence tolerance (max |V - V_old| < tol)

    Returns:
        {
            'optimal_policy':         list[int],   # action index per state
            'value_function':         list[float],
            'convergence_iterations': int,
            'converged':              bool,
            'states':                 list[str],
            'actions':                list[str],
            'gamma':                  float,
        }
    """
    # Guard inputs
    gamma = min(gamma, 0.999)
    n_periods = min(n_periods, 10000)

    # Default reward matrix R[state, action]
    R_mat = np.array([
        [ 2.0,  0.0, -2.0],   # risk_off: underweight rewarded, overweight penalized
        [ 0.0,  1.0,  0.0],   # neutral:  neutral_weight weakly rewarded
        [-2.0,  0.0,  2.0],   # risk_on:  overweight rewarded, underweight penalized
    ])

    # Default action-dependent transition matrices P[action, state, next_state]
    P_default = np.array([
        # action 0: underweight — risk_off is sticky, slowly recovers
        [[0.7, 0.2, 0.1], [0.3, 0.5, 0.2], [0.1, 0.3, 0.6]],
        # action 1: neutral — moderate mean-reversion
        [[0.6, 0.3, 0.1], [0.2, 0.6, 0.2], [0.1, 0.3, 0.6]],
        # action 2: overweight — risk_on is sticky
        [[0.6, 0.2, 0.2], [0.2, 0.4, 0.4], [0.1, 0.2, 0.7]],
    ])

    if transition_override is not None:
        P = np.array(transition_override, dtype=float)
        logger.debug("Using transition_override: shape %s", P.shape)
    else:
        P = P_default

    # Value iteration
    V = np.zeros(3)
    converged = False
    policy = np.zeros(3, dtype=int)

    for iteration in range(n_periods):
        V_old = V.copy()
        Q_vals = np.zeros((3, 3))  # Q_vals[state, action]

        for a in range(3):
            Q_vals[:, a] = R_mat[:, a] + gamma * P[a] @ V

        V = Q_vals.max(axis=1)
        policy = Q_vals.argmax(axis=1)

        if np.max(np.abs(V - V_old)) < tol:
            converged = True
            break

    logger.debug(
        "MDP converged=%s after %d iterations (gamma=%.3f, tol=%.2e)",
        converged, iteration + 1, gamma, tol,
    )

    return {
        'optimal_policy':         policy.tolist(),
        'value_function':         V.tolist(),
        'convergence_iterations': iteration + 1,
        'converged':              converged,
        'states':                 ['risk_off', 'neutral', 'risk_on'],
        'actions':                ['underweight', 'neutral', 'overweight'],
        'gamma':                  gamma,
    }
