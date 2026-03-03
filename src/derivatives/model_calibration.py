"""
Model Calibration Module

Two-stage calibration of Heston / Merton / BCC parameters to real
options market data fetched via the existing VolatilitySurfaceBuilder.

Stage 1: scipy.optimize.brute — coarse grid search over parameter space
Stage 2: scipy.optimize.fmin (Nelder-Mead) — fine-tune from brute best

Error metric: MSE between model prices and market mid-prices.

Based on Module 3/4 calibration workflow.
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from scipy.optimize import brute, fmin

from .fourier_pricer import heston_price, bcc_price, merton_price

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Heston Calibrator
# ---------------------------------------------------------------------------

class HestonCalibrator:
    """
    Calibrate Heston (1993) parameters {κ, θ, σᵥ, ρ, ν₀} to market options.

    Usage::
        calibrator = HestonCalibrator()
        result = calibrator.calibrate('AAPL', risk_free_rate=0.05)
    """

    # Parameter bounds for brute search
    BRUTE_RANGES = (
        slice(0.1, 10.0, 2.5),    # kappa:   [0.1, 10)
        slice(0.01, 0.50, 0.12),   # theta:   [0.01, 0.50)
        slice(0.05, 1.00, 0.25),   # sigma_v: [0.05, 1.00)
        slice(-0.95, 0.00, 0.25),  # rho:     [-0.95, 0)
        slice(0.01, 0.50, 0.12),   # v0:      [0.01, 0.50)
    )

    FMIN_BOUNDS_LOW  = np.array([0.01, 0.001, 0.01, -0.999, 0.001])
    FMIN_BOUNDS_HIGH = np.array([20.0, 2.000, 2.00,  0.999, 2.000])

    def __init__(self):
        self.result_params: Optional[np.ndarray] = None
        self.mse: float = np.inf

    def calibrate(
        self,
        ticker: str,
        risk_free_rate: float = 0.05,
        option_type: str = 'call',
        max_contracts: int = 40
    ) -> Dict:
        """
        Full two-stage calibration.

        Args:
            ticker:         Stock ticker (e.g. 'AAPL')
            risk_free_rate: Constant risk-free rate
            option_type:    'call' or 'put'
            max_contracts:  Maximum number of options to use for speed

        Returns:
            dict with calibrated parameters and fit quality
        """
        from .volatility_surface import VolatilitySurfaceBuilder

        logger.info(f"Starting Heston calibration for {ticker}")

        # ---- 1. Fetch market data ----
        builder = VolatilitySurfaceBuilder()
        surface = builder.build_surface(
            ticker, risk_free_rate=risk_free_rate,
            option_type=option_type, min_volume=0
        )
        raw = surface['raw_data']
        S = surface['current_price']

        if not raw:
            return {'error': f'No options data returned for {ticker}'}

        # Subsample to limit calibration time
        if len(raw) > max_contracts:
            step = len(raw) // max_contracts
            raw = raw[::step][:max_contracts]

        # Pack market data into arrays
        Ks    = np.array([d['strike'] for d in raw])
        Ts    = np.array([d['time_to_maturity'] for d in raw])
        mkt_p = np.array([d['market_price'] for d in raw])

        logger.info(f"Calibrating to {len(Ks)} contracts (S={S:.2f})")

        def mse_fn(params: np.ndarray) -> float:
            kappa, theta, sigma_v, rho, v0 = params
            # Enforce positivity and bounds
            if (kappa <= 0 or theta <= 0 or sigma_v <= 0 or v0 <= 0
                    or abs(rho) >= 1):
                return 1e10
            errors = []
            for K, T, mp in zip(Ks, Ts, mkt_p):
                try:
                    res = heston_price(S, K, T, risk_free_rate,
                                       v0, kappa, theta, sigma_v, rho,
                                       option_type)
                    errors.append((res['price'] - mp) ** 2)
                except Exception:
                    errors.append(1e4)
            return float(np.mean(errors))

        # ---- 2. Stage 1: Brute force ----
        logger.info("Stage 1: coarse grid search…")
        try:
            brute_result = brute(mse_fn, self.BRUTE_RANGES, finish=None)
        except Exception as e:
            logger.warning(f"Brute search failed: {e}; using default init")
            brute_result = np.array([2.0, 0.04, 0.3, -0.5, 0.04])

        # ---- 3. Stage 2: Nelder-Mead refinement ----
        logger.info("Stage 2: Nelder-Mead fine-tuning…")
        try:
            fmin_result = fmin(mse_fn, brute_result, disp=False,
                               maxiter=2000, ftol=1e-8, xtol=1e-6,
                               full_output=True)
            opt_params, opt_mse = fmin_result[0], fmin_result[1]
        except Exception as e:
            logger.warning(f"Nelder-Mead failed: {e}; using brute result")
            opt_params = brute_result
            opt_mse = mse_fn(brute_result)

        # Clip to feasible region
        opt_params = np.clip(opt_params, self.FMIN_BOUNDS_LOW, self.FMIN_BOUNDS_HIGH)
        kappa, theta, sigma_v, rho, v0 = opt_params

        # Recompute MSE for the clipped parameters (opt_mse may correspond to pre-clip params)
        recomputed_mse = float(mse_fn(opt_params))
        self.result_params = opt_params
        self.mse = recomputed_mse

        feller = 2 * kappa * theta > sigma_v ** 2

        return {
            'model': 'Heston (1993)',
            'ticker': ticker,
            'n_contracts': len(Ks),
            'calibrated_params': {
                'kappa':   float(kappa),
                'theta':   float(theta),
                'sigma_v': float(sigma_v),
                'rho':     float(rho),
                'v0':      float(v0),
            },
            'feller_condition_satisfied': bool(feller),
            'mse': recomputed_mse,
            'rmse': float(np.sqrt(recomputed_mse)),
            'spot': float(S),
            'risk_free_rate': risk_free_rate,
        }


# ---------------------------------------------------------------------------
# BCC Calibrator
# ---------------------------------------------------------------------------

class BCCCalibrator:
    """
    Sequential calibration for the BCC model:
        1. Calibrate Heston (SV only)
        2. Add Merton jump parameters {λ, μ_j, δ_j}
        3. Joint fine-tune

    Requires HestonCalibrator to be run first (or pass heston_params directly).
    """

    JUMP_BRUTE_RANGES = (
        slice(0.1,  5.0, 1.5),    # lam:     jump intensity
        slice(-0.3,  0.1, 0.1),   # mu_j:    mean log-jump
        slice(0.05,  0.5, 0.15),  # delta_j: std log-jump
    )

    def calibrate(
        self,
        ticker: str,
        heston_params: Optional[Dict] = None,
        risk_free_rate: float = 0.05,
        option_type: str = 'call',
        max_contracts: int = 40
    ) -> Dict:
        """
        Two-step BCC calibration.

        Args:
            heston_params: Pre-calibrated Heston dict (from HestonCalibrator)
                           If None, runs Heston calibration first.
        """
        # Step 1: Heston calibration (or use provided)
        from .volatility_surface import VolatilitySurfaceBuilder
        builder = VolatilitySurfaceBuilder()
        surface = builder.build_surface(ticker, risk_free_rate, option_type, min_volume=0)
        raw = surface['raw_data']
        if not raw:
            return {'error': f'No market data for {ticker}'}

        if heston_params is None:
            heston_cal = HestonCalibrator()
            heston_result = heston_cal.calibrate(
                ticker, risk_free_rate, option_type, max_contracts
            )
            if 'error' in heston_result:
                return heston_result
            heston_params = heston_result['calibrated_params']
            S = heston_result['spot']
        else:
            S = float(surface.get('current_price') or 0)
            if S <= 0:
                return {'error': f'Could not retrieve valid spot price for {ticker} from VolatilitySurfaceBuilder'}

        if len(raw) > max_contracts:
            step = len(raw) // max_contracts
            raw = raw[::step][:max_contracts]

        Ks    = np.array([d['strike'] for d in raw])
        Ts    = np.array([d['time_to_maturity'] for d in raw])
        mkt_p = np.array([d['market_price'] for d in raw])

        kappa   = heston_params['kappa']
        theta   = heston_params['theta']
        sigma_v = heston_params['sigma_v']
        rho     = heston_params['rho']
        v0      = heston_params['v0']

        def jump_mse(jump_params: np.ndarray) -> float:
            lam, mu_j, delta_j = jump_params
            if lam <= 0 or delta_j <= 0:
                return 1e10
            errors = []
            for K, T, mp in zip(Ks, Ts, mkt_p):
                try:
                    res = bcc_price(S, K, T, risk_free_rate,
                                    v0, kappa, theta, sigma_v, rho,
                                    0.0, lam, mu_j, delta_j, option_type)
                    errors.append((res['price'] - mp) ** 2)
                except Exception:
                    errors.append(1e4)
            return float(np.mean(errors))

        # Stage 1: brute search over jump params
        try:
            j0 = brute(jump_mse, self.JUMP_BRUTE_RANGES, finish=None)
        except Exception:
            j0 = np.array([0.5, -0.1, 0.15])

        # Stage 2: Nelder-Mead
        try:
            jfmin = fmin(jump_mse, j0, disp=False, maxiter=1000)
            lam, mu_j, delta_j = np.clip(jfmin, [0.001, -1.0, 0.01],
                                          [20.0, 1.0, 2.0])
        except Exception:
            lam, mu_j, delta_j = j0

        final_mse = float(jump_mse(np.array([lam, mu_j, delta_j])))

        return {
            'model': 'BCC (Heston + Merton Jumps)',
            'ticker': ticker,
            'calibrated_params': {
                'heston': heston_params,
                'jump': {
                    'lambda':  float(lam),
                    'mu_j':    float(mu_j),
                    'delta_j': float(delta_j),
                }
            },
            'mse':  final_mse,
            'rmse': float(np.sqrt(final_mse)),
            'spot': float(S),
        }


# ---------------------------------------------------------------------------
# Merton Calibrator
# ---------------------------------------------------------------------------

class MertonCalibrator:
    """
    Calibrate Merton (1976) jump-diffusion parameters {σ, λ, μⱼ, δⱼ} to
    market option prices using two-stage optimisation (brute grid + Nelder-Mead).

    The Merton model augments GBM with a compound Poisson jump process:
        dS/S = (r − λμ̄ⱼ) dt + σ dW + J dN

    Usage::
        calibrator = MertonCalibrator()
        result = calibrator.calibrate('AAPL', risk_free_rate=0.05)
    """

    BRUTE_RANGES = (
        slice(0.05, 0.80, 0.20),    # sigma:   diffusion vol
        slice(0.10, 8.00, 2.50),    # lam:     jump intensity (jumps/yr)
        slice(-0.30, 0.05, 0.10),   # mu_j:    mean log-jump
        slice(0.02, 0.50, 0.15),    # delta_j: std log-jump
    )

    BOUNDS_LOW  = np.array([0.001, 0.001, -1.0,  0.001])
    BOUNDS_HIGH = np.array([2.000, 20.00,  1.0,  2.000])

    def __init__(self):
        self.result_params: Optional[np.ndarray] = None
        self.mse: float = np.inf

    def calibrate(
        self,
        ticker: str,
        risk_free_rate: float = 0.05,
        option_type: str = 'call',
        max_contracts: int = 40
    ) -> Dict:
        """
        Full two-stage Merton calibration.

        Args:
            ticker:         Stock ticker (e.g. 'AAPL')
            risk_free_rate: Constant risk-free rate
            option_type:    'call' or 'put'
            max_contracts:  Maximum number of options to use for speed

        Returns:
            dict with calibrated parameters and fit quality
        """
        from .volatility_surface import VolatilitySurfaceBuilder

        logger.info(f"Starting Merton calibration for {ticker}")

        # Fetch market data
        builder = VolatilitySurfaceBuilder()
        surface = builder.build_surface(
            ticker, risk_free_rate=risk_free_rate,
            option_type=option_type, min_volume=0
        )
        raw = surface['raw_data']
        S   = surface['current_price']

        if not raw:
            return {'error': f'No options data returned for {ticker}'}

        if len(raw) > max_contracts:
            step = len(raw) // max_contracts
            raw = raw[::step][:max_contracts]

        Ks    = np.array([d['strike'] for d in raw])
        Ts    = np.array([d['time_to_maturity'] for d in raw])
        mkt_p = np.array([d['market_price'] for d in raw])

        logger.info(f"Calibrating Merton to {len(Ks)} contracts (S={S:.2f})")

        def mse_fn(params: np.ndarray) -> float:
            sigma, lam, mu_j, delta_j = params
            if sigma <= 0 or lam <= 0 or delta_j <= 0:
                return 1e10
            errors = []
            for K, T, mp in zip(Ks, Ts, mkt_p):
                try:
                    res = merton_price(S, K, T, risk_free_rate,
                                       sigma, lam, mu_j, delta_j, option_type)
                    errors.append((res['price'] - mp) ** 2)
                except Exception:
                    errors.append(1e4)
            return float(np.mean(errors))

        # Stage 1: brute grid search
        logger.info("Merton Stage 1: coarse grid search…")
        try:
            brute_result = brute(mse_fn, self.BRUTE_RANGES, finish=None)
        except Exception as e:
            logger.warning(f"Merton brute search failed: {e}; using default init")
            brute_result = np.array([0.20, 1.0, -0.05, 0.10])

        # Stage 2: Nelder-Mead refinement
        logger.info("Merton Stage 2: Nelder-Mead fine-tuning…")
        try:
            fmin_result = fmin(mse_fn, brute_result, disp=False,
                               maxiter=2000, ftol=1e-8, xtol=1e-6,
                               full_output=True)
            opt_params, opt_mse = fmin_result[0], fmin_result[1]
        except Exception as e:
            logger.warning(f"Merton Nelder-Mead failed: {e}; using brute result")
            opt_params = brute_result
            opt_mse = mse_fn(brute_result)

        opt_params = np.clip(opt_params, self.BOUNDS_LOW, self.BOUNDS_HIGH)
        sigma, lam, mu_j, delta_j = opt_params

        # Recompute MSE for clipped parameters
        recomputed_mse = float(mse_fn(opt_params))
        self.result_params = opt_params
        self.mse = recomputed_mse

        mu_bar = float(np.exp(mu_j + 0.5 * delta_j ** 2) - 1)

        return {
            'model': 'Merton Jump-Diffusion (1976)',
            'ticker': ticker,
            'n_contracts': len(Ks),
            'calibrated_params': {
                'sigma':   float(sigma),
                'lambda':  float(lam),
                'mu_j':    float(mu_j),
                'delta_j': float(delta_j),
                'mu_bar':  mu_bar,          # mean jump size
            },
            'mse':  recomputed_mse,
            'rmse': float(np.sqrt(max(recomputed_mse, 0))),
            'spot': float(S),
            'risk_free_rate': risk_free_rate,
        }
