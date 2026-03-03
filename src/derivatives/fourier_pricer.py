"""
Fourier Option Pricing Module

Implements stochastic-volatility option pricing via characteristic functions
using the Heston (1993) P1/P2 formula.

Models included:
    * Heston (1993)  — stochastic volatility
    * Merton (1976)  — log-normal jump-diffusion
    * BCC            — Bates (1996): Heston + Merton jumps
                       with optional CIR stochastic discounting

Pricing formula (Heston 1993 P1/P2):
    C = S₀ P₁ − K e^{−rT} P₂

where:
    Pⱼ = ½ + (1/π) ∫₀^∞ Re[ φⱼ(u) e^{−iu ln K} / (iu) ] du

    φ₂(u) = E^Q[e^{iu ln S_T}]          (CF of ln S_T under risk-neutral Q)
    φ₁(u) = φ₂(u − i) / (S₀ e^{rT})    (CF under stock-numeraire measure)

Reference:
    Heston (1993) "A closed-form solution for options with stochastic volatility"
    Albrecher et al. (2007) "The little Heston trap" (numerically stable parameterisation)
"""

import numpy as np
from scipy.integrate import quad
from typing import Dict, Optional, Callable
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Characteristic Functions of ln(S_T)
# ---------------------------------------------------------------------------

def _heston_log_price_cf(
    u: complex,
    S: float,
    T: float,
    r: float,
    kappa: float,
    theta: float,
    sigma_v: float,
    rho: float,
    v0: float
) -> complex:
    """
    Heston (1993) characteristic function of ln(S_T).
    Uses the Albrecher et al. (2007) numerically stable parameterisation.

    φ₂(u) = E^Q[e^{iu ln(S_T)}]
           = exp( iu(ln S₀ + rT) + C(T, u) + D(T, u) v₀ )

    Args:
        u:       Complex Fourier variable
        S:       Current stock price S₀
        T:       Time to maturity (years)
        r:       Risk-free rate (annualised)
        kappa:   Mean-reversion speed κ
        theta:   Long-run variance θ
        sigma_v: Vol of variance σᵥ
        rho:     Correlation ρ(S, v)
        v0:      Initial variance v₀

    Returns:
        Complex CF value
    """
    i = 1j

    xi = kappa - rho * sigma_v * u * i
    d  = np.sqrt(xi**2 + sigma_v**2 * (u**2 + i * u))
    g  = (xi - d) / (xi + d)

    exp_dT = np.exp(-d * T)

    # Numerically stable log term (Albrecher et al.)
    log_arg = (1.0 - g * exp_dT) / (1.0 - g)
    if abs(log_arg) < 1e-14:
        log_arg = 1e-14 + 0j

    C = (i * u * (np.log(S) + r * T)
         + kappa * theta / sigma_v**2
         * ((xi - d) * T - 2.0 * np.log(log_arg)))

    denom = 1.0 - g * exp_dT
    if abs(denom) < 1e-14:
        denom = 1e-14 + 0j

    D = (xi - d) / sigma_v**2 * (1.0 - exp_dT) / denom

    return np.exp(C + D * v0)


def _merton_log_price_cf(
    u: complex,
    S: float,
    T: float,
    r: float,
    sigma: float,
    lam: float,
    mu_j: float,
    delta_j: float
) -> complex:
    """
    Merton (1976) jump-diffusion characteristic function of ln(S_T).

    Under risk-neutral Q:
        dS/S = (r − λμ̄ⱼ) dt + σ dZ + (J−1) dN
    where N ~ Poisson(λ), ln J ~ N(μⱼ, δⱼ²), μ̄ⱼ = e^{μⱼ+δⱼ²/2} − 1.

    φ(u) = exp{ iu[ln S + (r − λμ̄ⱼ − σ²/2)T]
                − σ²u²T/2
                + λT(e^{iuμⱼ − δⱼ²u²/2} − 1) }
    """
    i = 1j
    mu_bar = np.exp(mu_j + 0.5 * delta_j**2) - 1.0  # risk-neutral compensator

    return np.exp(
        i * u * (np.log(S) + (r - lam * mu_bar - 0.5 * sigma**2) * T)
        - 0.5 * sigma**2 * u**2 * T
        + lam * T * (np.exp(i * u * mu_j - 0.5 * delta_j**2 * u**2) - 1.0)
    )


def _bcc_log_price_cf(
    u: complex,
    S: float,
    T: float,
    r: float,
    kappa: float,
    theta: float,
    sigma_v: float,
    rho: float,
    v0: float,
    lam: float,
    mu_j: float,
    delta_j: float
) -> complex:
    """
    BCC (Bates 1996) log-price CF: Heston stochastic vol × Merton jump component.

    φ_BCC(u) = φ_Heston(u; r − λμ̄ⱼ) × exp(λT(e^{iuμⱼ − δⱼ²u²/2} − 1))

    The Heston CF handles the drift adjusted for jump compensation.
    The exponential factor adds the Poisson-driven log-normal jumps.
    """
    i = 1j
    mu_bar = np.exp(mu_j + 0.5 * delta_j**2) - 1.0
    r_eff  = r - lam * mu_bar  # drift adjusted for jump risk premium

    phi_heston = _heston_log_price_cf(u, S, T, r_eff, kappa, theta, sigma_v, rho, v0)
    phi_jump   = np.exp(lam * T * (np.exp(i * u * mu_j - 0.5 * delta_j**2 * u**2) - 1.0))

    return phi_heston * phi_jump


# ---------------------------------------------------------------------------
# P1/P2 Quadrature Engine
# ---------------------------------------------------------------------------

def _compute_p1_p2(
    phi_fn: Callable[[complex], complex],
    K: float,
    F: float,
    integration_limit: float = 500.0
) -> tuple:
    """
    Compute P₁ and P₂ via Gill-Peterson quadrature.

    P₂ = ½ + (1/π) ∫₀^∞ Re[ φ₂(u)   · e^{−iu ln K} / (iu) ] du
    P₁ = ½ + (1/π) ∫₀^∞ Re[ φ₂(u−i)/F · e^{−iu ln K} / (iu) ] du

    The lower bound 1e-5 avoids the removable singularity at u = 0
    (the integrand has a finite limit there: Im[∂φ/∂u|_{u=0}] / F).

    Args:
        phi_fn:           φ₂(u) — log-price CF callable
        K:                Strike price
        F:                Forward price S₀ e^{rT}
        integration_limit: Upper integration bound

    Returns:
        (P1, P2) as floats ∈ (0, 1)
    """
    if K <= 0:
        raise ValueError(f"Strike K must be positive, got {K}")
    log_K = np.log(K)

    def p2_integrand(u: float) -> float:
        phi = phi_fn(complex(u, 0.0))
        return (phi * np.exp(-1j * u * log_K) / (1j * u)).real

    def p1_integrand(u: float) -> float:
        phi = phi_fn(complex(u, -1.0))   # φ₂(u − i)
        return (phi / F * np.exp(-1j * u * log_K) / (1j * u)).real

    p2_int, _ = quad(p2_integrand, 1e-5, integration_limit,
                     limit=500, epsabs=1e-8, epsrel=1e-8)
    p1_int, _ = quad(p1_integrand, 1e-5, integration_limit,
                     limit=500, epsabs=1e-8, epsrel=1e-8)

    P2 = 0.5 + p2_int / np.pi
    P1 = 0.5 + p1_int / np.pi

    P1 = float(np.clip(P1, 0.0, 1.0))
    P2 = float(np.clip(P2, 0.0, 1.0))
    return P1, P2


# ---------------------------------------------------------------------------
# Public Pricing Functions
# ---------------------------------------------------------------------------

def heston_price(
    S: float,
    K: float,
    T: float,
    r: float,
    v0: float,
    kappa: float,
    theta: float,
    sigma_v: float,
    rho: float,
    option_type: str = 'call',
    integration_limit: float = 500.0
) -> Dict:
    """
    Price a European option under Heston (1993) stochastic volatility.

    Formula:  C = S P₁ − K e^{−rT} P₂

    Args:
        S:        Current stock price
        K:        Strike price
        T:        Time to maturity (years)
        r:        Risk-free rate (annualised)
        v0:       Initial variance (e.g. 0.04 → 20% vol)
        kappa:    Mean-reversion speed (κ)
        theta:    Long-run variance (θ)
        sigma_v:  Vol of variance (σᵥ)
        rho:      Correlation stock–variance (ρ, typically negative)
        option_type: 'call' or 'put'
        integration_limit: Upper limit for quadrature

    Returns:
        dict with price, feller_condition_satisfied, and inputs
    """
    feller = 2.0 * kappa * theta > sigma_v**2
    F = S * np.exp(r * T)

    def phi(u: complex) -> complex:
        return _heston_log_price_cf(u, S, T, r, kappa, theta, sigma_v, rho, v0)

    P1, P2 = _compute_p1_p2(phi, K, F, integration_limit)

    call_price = S * P1 - K * np.exp(-r * T) * P2

    if option_type.lower() == 'put':
        price = call_price - S + K * np.exp(-r * T)
    else:
        price = call_price

    price = max(float(price), 0.0)

    return {
        'price': price,
        'model': 'Heston (1993)',
        'feller_condition_satisfied': bool(feller),
        'feller_lhs': float(2.0 * kappa * theta),
        'feller_rhs': float(sigma_v**2),
        'inputs': {
            'S': S, 'K': K, 'T': T, 'r': r,
            'v0': v0, 'kappa': kappa, 'theta': theta,
            'sigma_v': sigma_v, 'rho': rho,
            'option_type': option_type
        }
    }


def merton_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    lam: float,
    mu_j: float,
    delta_j: float,
    option_type: str = 'call',
    integration_limit: float = 500.0
) -> Dict:
    """
    Price a European option under Merton (1976) jump-diffusion.

    Args:
        S:        Current stock price
        K:        Strike price
        T:        Time to maturity (years)
        r:        Risk-free rate
        sigma:    Diffusion volatility (annualised)
        lam:      Jump intensity λ (jumps per year)
        mu_j:     Mean log-jump size μⱼ
        delta_j:  Std dev of log-jump size δⱼ
        option_type: 'call' or 'put'
        integration_limit: Upper limit for quadrature

    Returns:
        dict with price and inputs
    """
    F = S * np.exp(r * T)

    def phi(u: complex) -> complex:
        return _merton_log_price_cf(u, S, T, r, sigma, lam, mu_j, delta_j)

    P1, P2 = _compute_p1_p2(phi, K, F, integration_limit)

    call_price = S * P1 - K * np.exp(-r * T) * P2

    if option_type.lower() == 'put':
        price = call_price - S + K * np.exp(-r * T)
    else:
        price = call_price

    price = max(float(price), 0.0)

    return {
        'price': price,
        'model': 'Merton Jump-Diffusion (1976)',
        'inputs': {
            'S': S, 'K': K, 'T': T, 'r': r,
            'sigma': sigma, 'lam': lam, 'mu_j': mu_j, 'delta_j': delta_j,
            'option_type': option_type
        }
    }


def bcc_price(
    S: float,
    K: float,
    T: float,
    r: float,
    v0: float,
    kappa: float,
    theta: float,
    sigma_v: float,
    rho: float,
    sigma_gbm: float,           # kept for API compatibility; unused in BCC
    lam: float,
    mu_j: float,
    delta_j: float,
    option_type: str = 'call',
    discount_factor: Optional[float] = None,
    integration_limit: float = 500.0
) -> Dict:
    """
    BCC model price: Heston stochastic volatility + Merton log-normal jumps.

    Optionally accepts an external discount factor B(0,T) from a CIR model
    replacing e^{−rT} for stochastic discounting.

    Formula:  C = S P₁ − K B(0,T) P₂

    Args:
        discount_factor: If provided and positive, used as B(0,T) instead of e^{-rT}.
                         Set to None to use constant r.

    Returns:
        dict with price, Feller condition, and discount factor used
    """
    feller = 2.0 * kappa * theta > sigma_v**2

    if discount_factor is not None and discount_factor > 0:
        B     = float(discount_factor)
        r_eff = -np.log(B) / T if T > 0 else r
    else:
        B     = np.exp(-r * T)
        r_eff = r

    F = S / B   # Forward price: S₀ / B(0,T)

    def phi(u: complex) -> complex:
        return _bcc_log_price_cf(u, S, T, r_eff, kappa, theta, sigma_v, rho, v0,
                                 lam, mu_j, delta_j)

    P1, P2 = _compute_p1_p2(phi, K, F, integration_limit)

    call_price = S * P1 - K * B * P2

    if option_type.lower() == 'put':
        price = call_price - S + K * B
    else:
        price = call_price

    price = max(float(price), 0.0)

    return {
        'price': price,
        'model': 'BCC (Heston + Merton Jumps)',
        'feller_condition_satisfied': bool(feller),
        'discount_factor_used': float(B),
        'inputs': {
            'S': S, 'K': K, 'T': T, 'r': r, 'r_eff': r_eff,
            'v0': v0, 'kappa': kappa, 'theta': theta,
            'sigma_v': sigma_v, 'rho': rho,
            'lam': lam, 'mu_j': mu_j, 'delta_j': delta_j,
            'option_type': option_type
        }
    }
