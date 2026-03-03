"""
Interest Rate Models Module

Implements the Cox-Ingersoll-Ross (CIR, 1985) stochastic interest rate model:

    dr = κ(θ − r) dt + σ √r dW

Features:
    * Closed-form zero-coupon bond price B(0,T) = A(T) · exp(−B(T) · r₀)
    * Implied spot rate curve r(T) = −ln B(0,T) / T
    * Calibration to market yields via MSE minimisation (two-stage: brute + Nelder-Mead)
    * Feller condition check: 2κθ > σ² (ensures non-negative rates)

Based on Module 4 of the stochastic modelling course.
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from scipy.optimize import brute, fmin

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CIR Closed-Form Formulae
# ---------------------------------------------------------------------------

def cir_bond_price(
    r0: float,
    T: float,
    kappa: float,
    theta: float,
    sigma: float
) -> float:
    """
    Zero-coupon bond price B(0,T) under the CIR model.

    B(0,T) = A(T) · exp(−b(T) · r₀)

    where:
        γ    = √(κ² + 2σ²)
        b(T) = 2(e^{γT} − 1) / ((γ+κ)(e^{γT}−1) + 2γ)
        A(T) = [2γ exp((κ+γ)T/2) / ((γ+κ)(e^{γT}−1) + 2γ)]^{2κθ/σ²}

    Args:
        r0:    Current short rate
        T:     Maturity (years)
        kappa: Mean-reversion speed
        theta: Long-run mean rate
        sigma: Volatility of short rate

    Returns:
        Bond price in [0,1]
    """
    if T <= 0:
        return 1.0
    if kappa <= 0:
        raise ValueError("CIR kappa (mean-reversion speed) must be positive")
    if sigma <= 0:
        raise ValueError("CIR sigma must be positive")

    gamma = np.sqrt(kappa**2 + 2 * sigma**2)
    exp_gT = np.exp(gamma * T)

    denom = (gamma + kappa) * (exp_gT - 1) + 2 * gamma
    if denom <= 0:
        return 1.0

    b = 2 * (exp_gT - 1) / denom

    # A(T): use log for numerical stability
    log_A = (2 * kappa * theta / sigma**2) * np.log(
        2 * gamma * np.exp((kappa + gamma) * T / 2) / denom
    )
    A = np.exp(log_A)

    return float(np.clip(A * np.exp(-b * r0), 0, 1))


def cir_spot_rate(
    r0: float,
    T: float,
    kappa: float,
    theta: float,
    sigma: float
) -> float:
    """
    Spot (implied) rate from CIR model: r_impl(T) = −ln B(0,T) / T

    Args:
        r0, T, kappa, theta, sigma: as in cir_bond_price

    Returns:
        Implied annualised spot rate
    """
    if T <= 0:
        return r0
    B = cir_bond_price(r0, T, kappa, theta, sigma)
    if B <= 0:
        return theta   # fallback to long-run mean
    return float(-np.log(B) / T)


def cir_yield_curve(
    r0: float,
    maturities: List[float],
    kappa: float,
    theta: float,
    sigma: float
) -> List[Dict]:
    """
    Compute the full CIR yield curve for a list of maturities.

    Args:
        r0:         Current short rate
        maturities: List of maturities in years (e.g. [0.25, 0.5, 1, 2, 5, 10, 30])
        kappa:      Mean-reversion speed
        theta:      Long-run rate
        sigma:      Rate volatility

    Returns:
        List of dicts {maturity, bond_price, spot_rate}
    """
    curve = []
    for T in maturities:
        B = cir_bond_price(r0, T, kappa, theta, sigma)
        r_impl = -np.log(B) / T if T > 0 and B > 0 else r0
        curve.append({
            'maturity':   float(T),
            'bond_price': float(B),
            'spot_rate':  float(r_impl),
        })
    return curve


# ---------------------------------------------------------------------------
# Feller Reparameterisation Helper
# ---------------------------------------------------------------------------

def _feller_safe_params(alpha: float, theta: float, sigma: float):
    """
    Unpack reparameterised CIR params that guarantee Feller condition (2*kappa*theta >= sigma^2).

    Optimise over (alpha, theta, sigma). alpha is unconstrained; kappa recovered from it.
    kappa = sigma^2/(2*theta) + exp(alpha) is always > sigma^2/(2*theta) for all real alpha,
    which ensures 2*kappa*theta > sigma^2 by construction.

    Args:
        alpha: Unconstrained log-space surplus above Feller floor
        theta: Long-run mean rate (must be > 0)
        sigma: Volatility (must be > 0)

    Returns:
        (kappa, theta, sigma) tuple, or None if theta <= 0 or sigma <= 0
    """
    if theta <= 0 or sigma <= 0:
        return None
    # kappa = sigma^2/(2*theta) + exp(alpha) is always > sigma^2/(2*theta) for all real alpha
    kappa = (sigma ** 2) / (2.0 * theta) + np.exp(alpha)
    return kappa, theta, sigma


# ---------------------------------------------------------------------------
# CIR Calibrator
# ---------------------------------------------------------------------------

class CIRCalibrator:
    """
    Calibrate CIR parameters {κ, θ, σ} to observed market yield data
    using two-stage optimisation (brute grid search + Nelder-Mead).

    Market yield data format:
        [(maturity_years, yield_decimal), ...]
        e.g. [(0.25, 0.053), (1.0, 0.051), (5.0, 0.046), (10.0, 0.045)]
    """

    BRUTE_RANGES = (
        slice(-2.0, 2.0, 0.5),    # alpha (log-space kappa surplus over Feller floor)
        slice(0.01, 0.15, 0.02),  # theta
        slice(0.05, 0.5, 0.1),    # sigma
    )

    def calibrate(
        self,
        market_yields: List[Tuple[float, float]],
        r0: float = 0.05
    ) -> Dict:
        """
        Calibrate CIR to market yields.

        Args:
            market_yields: List of (maturity, yield) pairs
            r0:            Current short rate (initial condition)

        Returns:
            dict with calibrated {κ, θ, σ}, MSE, and implied yield curve
        """
        if not market_yields:
            return {'error': 'No market yield data provided'}

        Ts     = np.array([m for m, _ in market_yields])
        yields = np.array([y for _, y in market_yields])

        def mse_fn(params: np.ndarray) -> float:
            # Reparameterised (alpha, theta, sigma): Feller guaranteed by construction.
            # kappa = sigma^2/(2*theta) + exp(alpha) > sigma^2/(2*theta) for all real alpha.
            alpha, theta, sigma = params
            unpacked = _feller_safe_params(alpha, theta, sigma)
            if unpacked is None:
                return 1e10
            kappa, theta_val, sigma_val = unpacked
            errors = []
            for T, y_mkt in zip(Ts, yields):
                try:
                    y_mod = cir_spot_rate(r0, T, kappa, theta_val, sigma_val)
                    errors.append((y_mod - y_mkt) ** 2)
                except Exception:
                    errors.append(1.0)
            return float(np.mean(errors))

        # Stage 1: brute grid search over (alpha, theta, sigma)
        try:
            x0 = brute(mse_fn, self.BRUTE_RANGES, finish=None)
        except Exception:
            x0 = np.array([0.0, 0.05, 0.1])  # alpha=0 corresponds to kappa = sigma^2/(2*theta) + 1

        # Stage 2: Nelder-Mead
        try:
            result = fmin(mse_fn, x0, disp=False, maxiter=2000,
                          ftol=1e-10, xtol=1e-8, full_output=True)
            opt_params, opt_mse = result[0], result[1]
        except Exception:
            opt_params, opt_mse = x0, mse_fn(x0)

        # Unpack reparameterised (alpha, theta, sigma) to physical (kappa, theta, sigma)
        alpha_opt, theta_opt, sigma_opt = opt_params
        # Positivity clip on theta and sigma (alpha is unconstrained)
        theta_opt = max(theta_opt, 1e-6)
        sigma_opt = max(sigma_opt, 1e-6)
        unpacked = _feller_safe_params(alpha_opt, theta_opt, sigma_opt)
        if unpacked is None:
            return {'error': 'CIR calibration produced invalid parameters'}
        kappa, theta, sigma = unpacked

        # Recompute pure MSE for the unpacked physical parameters
        pure_errors = []
        for T_mat, y_mkt in zip(Ts, yields):
            try:
                y_mod = cir_spot_rate(r0, T_mat, kappa, theta, sigma)
                pure_errors.append((y_mod - y_mkt) ** 2)
            except Exception:
                pure_errors.append(1.0)
        pure_mse = float(np.mean(pure_errors)) if pure_errors else 0.0

        # Build implied curve at standard maturities
        std_mats = [0.083, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]
        curve = cir_yield_curve(r0, std_mats, kappa, theta, sigma)

        # Feller is always satisfied by construction (reparameterisation guarantee)
        feller_lhs = float(2 * kappa * theta)
        feller_rhs = float(sigma ** 2)

        return {
            'model': 'CIR (1985)',
            'calibrated_params': {
                'kappa': float(kappa),
                'theta': float(theta),
                'sigma': float(sigma),
            },
            'r0': float(r0),
            'feller_condition_satisfied': True,  # always True by construction
            'feller_lhs': feller_lhs,
            'feller_rhs': feller_rhs,
            'mse':  pure_mse,
            'rmse': float(np.sqrt(max(pure_mse, 0))),
            'implied_yield_curve': curve,
        }


# ---------------------------------------------------------------------------
# Convenience: US Treasury-based default calibration
# ---------------------------------------------------------------------------

# Approximate US Treasury yields as of early 2025 (illustrative defaults)
US_TREASURY_YIELDS_2025 = [
    (1/12,  0.0527),   # 1M
    (3/12,  0.0526),   # 3M
    (6/12,  0.0519),   # 6M
    (1,     0.0504),   # 1Y
    (2,     0.0476),   # 2Y
    (5,     0.0461),   # 5Y
    (10,    0.0460),   # 10Y
    (30,    0.0471),   # 30Y
]


def calibrate_to_treasuries(r0: float = 0.053) -> Dict:
    """
    Convenience function: calibrate CIR to approximate US Treasury yields.

    Args:
        r0: Current overnight rate (default ~5.3% as of 2024)

    Returns:
        Calibration result dict
    """
    cal = CIRCalibrator()
    return cal.calibrate(US_TREASURY_YIELDS_2025, r0=r0)
