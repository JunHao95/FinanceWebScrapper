"""
Credit Transition Model Module

Implements Markov chain credit rating transition models for credit risk analysis.

Features:
    * Standard S&P-style transition matrix (AAA → D)
    * n-year transition via matrix power: P^n
    * Default probability extraction over multiple horizons
    * Monte Carlo time-to-default simulation
    * Expected bond value under credit risk

Based on Module 5 (L2): Markov chain credit transitions.

Standard rating scale: AAA, AA, A, BBB, BB, B, CCC, D (default)
"""

import numpy as np
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Standard S&P Average 1-Year Transition Matrix (1981–2023 approximate)
# Source: S&P Global Ratings (illustrative; use latest published for production)
# Rows = current rating, Columns = end-of-year rating
# Order: AAA, AA, A, BBB, BB, B, CCC, D
# ---------------------------------------------------------------------------
RATINGS = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'D']

SP_TRANSITION_MATRIX = np.array([
    # AAA    AA      A      BBB    BB     B      CCC    D
    [0.9081, 0.0833, 0.0068, 0.0006, 0.0008, 0.0002, 0.0000, 0.0002],  # AAA
    [0.0070, 0.9065, 0.0779, 0.0064, 0.0006, 0.0013, 0.0000, 0.0002],  # AA
    [0.0009, 0.0227, 0.9105, 0.0552, 0.0074, 0.0026, 0.0001, 0.0006],  # A
    [0.0002, 0.0033, 0.0595, 0.8693, 0.0530, 0.0117, 0.0012, 0.0018],  # BBB
    [0.0003, 0.0014, 0.0067, 0.0773, 0.8053, 0.0884, 0.0100, 0.0106],  # BB
    [0.0000, 0.0011, 0.0024, 0.0043, 0.0648, 0.8346, 0.0407, 0.0522],  # B
    [0.0022, 0.0000, 0.0022, 0.0130, 0.0238, 0.1124, 0.6486, 0.1978],  # CCC
    [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 1.0000],  # D (absorbing)
])

# Normalise rows to ensure they sum to 1 (handle rounding)
_row_sums = SP_TRANSITION_MATRIX.sum(axis=1, keepdims=True)
SP_TRANSITION_MATRIX = SP_TRANSITION_MATRIX / _row_sums


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def n_year_transition(P: np.ndarray, n: int) -> np.ndarray:
    """
    Compute n-year transition matrix as P^n (matrix power).

    Args:
        P: (K×K) annual transition probability matrix
        n: number of years

    Returns:
        (K×K) n-year transition probability matrix
    """
    if n <= 0:
        return np.eye(P.shape[0])
    result = np.linalg.matrix_power(P, n)
    # Clip small negatives from floating-point errors
    result = np.clip(result, 0, 1)
    result /= result.sum(axis=1, keepdims=True)
    return result


def default_probability_term_structure(
    current_rating: str,
    horizons: Optional[List[int]] = None,
    P: Optional[np.ndarray] = None
) -> List[Dict]:
    """
    Compute cumulative default probability over multiple time horizons.

    Args:
        current_rating: Current credit rating (e.g. 'BBB')
        horizons:       List of years to compute (default: 1–10, 15, 20, 30)
        P:              Transition matrix (defaults to SP_TRANSITION_MATRIX)

    Returns:
        List of {horizon, cumulative_default_prob, transition_row}
    """
    if P is None:
        P = SP_TRANSITION_MATRIX.copy()
    if horizons is None:
        horizons = list(range(1, 11)) + [15, 20, 30]

    rating_idx = RATINGS.index(current_rating.upper())
    default_idx = RATINGS.index('D')

    results = []
    for n in horizons:
        Pn = n_year_transition(P, n)
        row = Pn[rating_idx]
        results.append({
            'horizon_years': n,
            'cumulative_default_prob': float(row[default_idx]),
            'rating_distribution': {r: float(row[i]) for i, r in enumerate(RATINGS)},
        })

    return results


def expected_bond_value(
    current_rating: str,
    horizon: int,
    recovery_rate: float = 0.40,
    coupon_rate: float = 0.05,
    face_value: float = 1000.0,
    P: Optional[np.ndarray] = None
) -> Dict:
    """
    Compute expected bond value at a given horizon accounting for
    credit-rating-weighted state values.

    Simplified approach:
        E[V] = Σ_r P(current → r) · V(r, T)

    where V(r, T) for non-default states is estimated by par (coupon + face),
    adjusted for rating-spread discounting; V(D, T) = recovery × face.

    Args:
        current_rating: Starting credit rating
        horizon:        Investment horizon in years
        recovery_rate:  Recovery rate on default (0.40 = 40%)
        coupon_rate:    Annual coupon (decimal)
        face_value:     Face value of bond
        P:              Transition matrix

    Returns:
        dict with expected value, default probability, and state breakdown
    """
    if P is None:
        P = SP_TRANSITION_MATRIX.copy()

    rating_idx = RATINGS.index(current_rating.upper())
    default_idx = RATINGS.index('D')

    Pn = n_year_transition(P, horizon)
    state_probs = Pn[rating_idx]

    # Continuous-discounting annuity PV: C*F*(1-exp(-r*T))/r
    # Par bond assumption: discount_rate = coupon_rate (coupon equals yield at issuance)
    discount_rate = coupon_rate
    if discount_rate > 0 and horizon > 0:
        coupons_pv = coupon_rate * face_value * (1.0 - np.exp(-discount_rate * horizon)) / discount_rate
        # Discounted principal: face_value * exp(-r*T)
        # Together: face_value*exp(-rT) + coupon_rate*face_value*(1-exp(-rT))/r = face_value (par bond)
        principal_pv = face_value * np.exp(-discount_rate * horizon)
    else:
        coupons_pv = coupon_rate * face_value * horizon  # degenerate fallback: r=0 or T=0
        principal_pv = face_value
    state_bond_values = {
        'AAA':  principal_pv + coupons_pv * 1.00,
        'AA':   principal_pv + coupons_pv * 0.99,
        'A':    principal_pv + coupons_pv * 0.98,
        'BBB':  principal_pv + coupons_pv * 0.97,
        'BB':   principal_pv + coupons_pv * 0.94,
        'B':    principal_pv + coupons_pv * 0.90,
        'CCC':  principal_pv + coupons_pv * 0.75,
        'D':    recovery_rate * face_value,
    }

    exp_value = sum(
        state_probs[i] * state_bond_values[r]
        for i, r in enumerate(RATINGS)
    )

    default_prob = float(state_probs[default_idx])

    return {
        'current_rating': current_rating.upper(),
        'horizon_years': horizon,
        'expected_bond_value': float(exp_value),
        'face_value': face_value,
        'coupon_rate': coupon_rate,
        'recovery_rate': recovery_rate,
        'default_probability': default_prob,
        'state_distribution': {r: float(state_probs[i]) for i, r in enumerate(RATINGS)},
    }


def monte_carlo_time_to_default(
    current_rating: str,
    max_years: int = 30,
    n_simulations: int = 10000,
    P: Optional[np.ndarray] = None
) -> Dict:
    """
    Monte Carlo simulation of time-to-default.

    Args:
        current_rating: Starting credit rating
        max_years:      Maximum simulation horizon
        n_simulations:  Number of Monte Carlo paths
        P:              Annual transition matrix

    Returns:
        dict with default statistics (median TTD, probability, distribution)
    """
    if not isinstance(n_simulations, int) or n_simulations <= 0:
        raise ValueError("n_simulations must be a positive integer")

    if P is None:
        P = SP_TRANSITION_MATRIX.copy()

    K = len(RATINGS)
    default_idx = RATINGS.index('D')
    start_idx = RATINGS.index(current_rating.upper())

    defaulted = 0
    times_to_default: List[float] = []
    survival_counts = np.zeros(max_years + 1, dtype=int)

    rng = np.random.default_rng(42)

    for _ in range(n_simulations):
        state = start_idx
        ttd = None
        survival_counts[0] += 1

        for t in range(1, max_years + 1):
            row = P[state]
            next_state = rng.choice(K, p=row)
            if next_state == default_idx:
                defaulted += 1
                ttd = t
                break
            state = next_state
            survival_counts[t] += 1

        if ttd is not None:
            times_to_default.append(ttd)

    default_prob = defaulted / n_simulations
    survival_probs = survival_counts / n_simulations

    median_ttd = float(np.median(times_to_default)) if times_to_default else None
    mean_ttd   = float(np.mean(times_to_default))   if times_to_default else None

    return {
        'current_rating':    current_rating.upper(),
        'max_years':         max_years,
        'n_simulations':     n_simulations,
        'default_probability': float(default_prob),
        'median_time_to_default': median_ttd,
        'mean_time_to_default':   mean_ttd,
        'survival_curve': [
            {'year': t, 'survival_prob': float(survival_probs[t])}
            for t in range(max_years + 1)
        ],
    }


# ---------------------------------------------------------------------------
# High-Level Analysis
# ---------------------------------------------------------------------------

def credit_risk_analysis(
    current_rating: str,
    horizon: int = 5,
    recovery_rate: float = 0.40,
    face_value: float = 1000.0,
    coupon_rate: float = 0.05,
    mc_simulations: int = 5000,
    custom_matrix: Optional[np.ndarray] = None
) -> Dict:
    """
    Full credit risk analysis for a given bond/issuer rating.

    Args:
        current_rating:  Credit rating (e.g. 'BBB', 'A', 'BB')
        horizon:         Investment horizon in years
        recovery_rate:   Recovery rate on default
        face_value:      Bond face value
        coupon_rate:     Annual coupon rate
        mc_simulations:  Monte Carlo paths for TTD simulation
        custom_matrix:   Optional custom transition matrix

    Returns:
        Comprehensive dict with default term structure, bond value, and TTD
    """
    P = custom_matrix if custom_matrix is not None else SP_TRANSITION_MATRIX.copy()
    rating = current_rating.upper()

    if rating not in RATINGS or rating == 'D':
        return {'error': f"Invalid rating '{current_rating}'. Choose from: {RATINGS[:-1]}"}

    term_structure = default_probability_term_structure(rating, P=P)
    bond_val = expected_bond_value(rating, horizon, recovery_rate,
                                   coupon_rate, face_value, P)
    ttd = monte_carlo_time_to_default(rating, max_years=30,
                                      n_simulations=mc_simulations, P=P)

    return {
        'model':          'Markov Chain Credit Transitions (S&P)',
        'current_rating': rating,
        'ratings_scale':  RATINGS,
        'default_probability_term_structure': term_structure,
        'bond_analysis':  bond_val,
        'time_to_default': ttd,
    }


if __name__ == '__main__':
    # Quick par bond validation: AAA, 1-year, identity matrix (no migration/default)
    # Expected: ~1000.0 (continuous-discounting annuity PV of coupons = face + discounted coupons)
    P_identity = np.eye(len(RATINGS))
    result = expected_bond_value('AAA', 1, coupon_rate=0.05, face_value=1000.0, P=P_identity)
    val = result['expected_bond_value']
    status = 'PASS' if abs(val - 1000.0) < 0.01 else 'FAIL'
    print(f"{status}: Par bond (AAA, 1yr, zero-default) = {val:.4f} (expected ~1000.0)")
