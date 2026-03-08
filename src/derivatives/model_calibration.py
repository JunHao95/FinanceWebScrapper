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
from scipy.optimize import brute, fmin, minimize

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
        slice(0.1,  8.0, 2.0),     # kappa:   [0.1, 8)
        slice(0.01, 0.50, 0.12),   # theta:   [0.01, 0.50)
        slice(0.05, 0.80, 0.20),   # sigma_v: [0.05, 0.80)
        slice(-0.95, 0.05, 0.25),  # rho:     [-0.95, 0.05)
        slice(0.01, 0.50, 0.12),   # v0:      [0.01, 0.50)
    )

    FMIN_BOUNDS_LOW  = np.array([0.01, 0.001, 0.01, -0.999, 0.001])
    FMIN_BOUNDS_HIGH = np.array([10.0, 1.000, 1.00,  0.999, 1.000])

    def __init__(self):
        self.result_params: Optional[np.ndarray] = None
        self.mse: float = np.inf

    def calibrate(
        self,
        ticker: str,
        risk_free_rate: float = 0.05,
        option_type: str = 'call',
        max_contracts: int = 40,
        callback=None
    ) -> Dict:
        """
        Full two-stage calibration.

        Args:
            ticker:         Stock ticker (e.g. 'AAPL')
            risk_free_rate: Constant risk-free rate
            option_type:    'call' or 'put'
            max_contracts:  Maximum number of options to use for speed
            callback:       Optional callable(iteration: int, error: float) fired after each
                            Nelder-Mead iteration via scipy fmin callback mechanism.

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

        # Filter out contracts with market_price < 0.50 to prevent near-zero OTM options
        # from dominating the relative MSE objective (standard practice in calibration)
        MIN_MARKET_PRICE = 0.50
        raw = [d for d in raw if d['market_price'] >= MIN_MARKET_PRICE]
        if not raw:
            return {'error': f'No contracts remain after filtering market_price < {MIN_MARKET_PRICE} for {ticker}'}

        # Pack market data into arrays (from filtered raw)
        Ks    = np.array([d['strike'] for d in raw])
        Ts    = np.array([d['time_to_maturity'] for d in raw])
        mkt_p = np.array([d['market_price'] for d in raw])

        logger.info(f"Calibrating to {len(Ks)} contracts (S={S:.2f})")

        def mse_fn(params: np.ndarray) -> float:
            # Clip to feasible region inside the objective so that the bounded
            # Nelder-Mead sees a smooth landscape at the boundaries rather than
            # a discontinuous wall from a hard reject.
            kappa, theta, sigma_v, rho, v0 = np.clip(
                params, self.FMIN_BOUNDS_LOW, self.FMIN_BOUNDS_HIGH
            )
            if kappa <= 0 or theta <= 0 or sigma_v <= 0 or v0 <= 0 or abs(rho) >= 1:
                return 1e10
            errors = []
            for K, T, mp in zip(Ks, Ts, mkt_p):
                try:
                    res = heston_price(S, K, T, risk_free_rate,
                                       v0, kappa, theta, sigma_v, rho,
                                       option_type)
                    # Relative (percentage) MSE — OTM and ITM options contribute equally per unit of price.
                    # Dollar MSE caused large ITM contracts to dominate, producing a flat IV smile (MATH-02 fix).
                    if mp >= MIN_MARKET_PRICE:
                        errors.append(((res['price'] - mp) / mp) ** 2)
                    else:
                        errors.append((res['price'] - mp) ** 2)  # absolute fallback (should not reach here after filter)
                except Exception:
                    errors.append(1e4)
            base_mse = float(np.mean(errors))
            # Soft Feller penalty: add a weighted violation term so the optimizer
            # is steered away from 2κθ < σᵥ² (variance hits zero → pricer diverges).
            feller_violation = max(0.0, sigma_v ** 2 - 2.0 * kappa * theta)
            return base_mse + 0.5 * feller_violation

        # ---- 2. Stage 1: Brute force ----
        logger.info("Stage 1: coarse grid search…")
        try:
            brute_result = brute(mse_fn, self.BRUTE_RANGES, finish=None)
        except Exception as e:
            logger.warning(f"Brute search failed: {e}; using default init")
            brute_result = np.array([2.0, 0.04, 0.3, -0.5, 0.04])

        # ---- 3. Stage 2: Nelder-Mead refinement with hard bounds ----
        logger.info("Stage 2: Nelder-Mead fine-tuning…")

        # Build scipy callback wrapper if caller supplied one
        iteration_count = [0]
        def _scipy_callback(xk):
            iteration_count[0] += 1
            if callback is not None:
                current_error = mse_fn(xk)
                callback(iteration_count[0], float(current_error))

        # scipy.optimize.minimize with method='Nelder-Mead' supports bounds since scipy 1.7.
        # This prevents the optimizer from wandering into degenerate regions (kappa=20, sigma_v=2)
        # and then getting hard-clipped to a bad parameter set after the fact.
        bounds_list = list(zip(self.FMIN_BOUNDS_LOW, self.FMIN_BOUNDS_HIGH))
        x0 = np.clip(brute_result, self.FMIN_BOUNDS_LOW, self.FMIN_BOUNDS_HIGH)
        try:
            min_result = minimize(
                mse_fn, x0,
                method='Nelder-Mead',
                bounds=bounds_list,
                options={
                    'maxiter': 2000,
                    'fatol': 1e-8,
                    'xatol': 1e-6,
                    'disp': False,
                },
                callback=_scipy_callback,
            )
            opt_params = min_result.x
            opt_mse = float(min_result.fun)
        except Exception as e:
            logger.warning(f"Nelder-Mead failed: {e}; using brute result")
            opt_params = brute_result
            opt_mse = mse_fn(brute_result)

        # Clip to feasible region (safety net after bounded optimisation)
        opt_params = np.clip(opt_params, self.FMIN_BOUNDS_LOW, self.FMIN_BOUNDS_HIGH)
        kappa, theta, sigma_v, rho, v0 = opt_params

        # Recompute MSE for the clipped parameters (opt_mse may correspond to pre-clip params)
        recomputed_mse = float(mse_fn(opt_params))
        self.result_params = opt_params
        self.mse = recomputed_mse

        feller = 2 * kappa * theta > sigma_v ** 2

        # Compute market and fitted implied volatilities for IV comparison chart (CALIB-04)
        market_ivs: List[float] = []
        fitted_ivs: List[float] = []
        strikes_out: List[float] = []
        for K_i, T_i, mp_i in zip(Ks, Ts, mkt_p):
            try:
                fitted_price = heston_price(S, K_i, T_i, risk_free_rate,
                                            v0, kappa, theta, sigma_v, rho,
                                            option_type)['price']
                # Convert prices to implied vols via Black-Scholes inversion (Newton-Raphson)
                def _bs_price(sig, S_=S, K_=K_i, T_=T_i, r_=risk_free_rate, ot=option_type):
                    if sig <= 0 or T_ <= 0:
                        return 0.0
                    from scipy.stats import norm
                    d1 = (np.log(S_ / K_) + (r_ + 0.5 * sig ** 2) * T_) / (sig * np.sqrt(T_))
                    d2 = d1 - sig * np.sqrt(T_)
                    if ot == 'call':
                        return float(S_ * norm.cdf(d1) - K_ * np.exp(-r_ * T_) * norm.cdf(d2))
                    else:
                        return float(K_ * np.exp(-r_ * T_) * norm.cdf(-d2) - S_ * norm.cdf(-d1))

                def _iv(price):
                    lo, hi = 1e-4, 5.0
                    for _ in range(50):
                        mid = (lo + hi) / 2.0
                        if _bs_price(mid) > price:
                            hi = mid
                        else:
                            lo = mid
                        if hi - lo < 1e-6:
                            break
                    return float((lo + hi) / 2.0)

                strikes_out.append(float(K_i))
                market_ivs.append(_iv(mp_i))
                fitted_ivs.append(_iv(max(fitted_price, 1e-8)))
            except Exception:
                pass

        if strikes_out:
            sorted_triples = sorted(zip(strikes_out, market_ivs, fitted_ivs), key=lambda x: x[0])
            strikes_out, market_ivs, fitted_ivs = map(list, zip(*sorted_triples))

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
            'strikes': strikes_out,
            'market_ivs': market_ivs,
            'fitted_ivs': fitted_ivs,
        }


    def calibrate_stream(self, ticker: str, risk_free_rate: float = 0.05,
                         option_type: str = 'call'):
        """
        Generator that yields SSE-formatted progress strings in real time.

        Runs calibration in a background thread and streams iteration events via a
        queue so the frontend receives live updates rather than a burst at the end.
        """
        import json
        import threading
        import queue as _queue

        q: _queue.Queue = _queue.Queue()

        def _cb(iteration: int, error: float) -> None:
            q.put(json.dumps({'iteration': iteration, 'error': error}))

        def _run() -> None:
            try:
                self.calibrate(ticker, risk_free_rate, option_type=option_type, callback=_cb)
            except Exception as exc:
                q.put(json.dumps({'error': str(exc), 'done': True}))
            finally:
                q.put(None)  # sentinel

        threading.Thread(target=_run, daemon=True).start()

        try:
            while True:
                try:
                    msg = q.get(timeout=180)
                except _queue.Empty:
                    yield f"data: {json.dumps({'error': 'Calibration timed out', 'done': True})}\n\n"
                    return
                if msg is None:
                    break
                yield f"data: {msg}\n\n"
        except GeneratorExit:
            return

        yield f"data: {json.dumps({'done': True})}\n\n"


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

        JUMP_BOUNDS_LOW  = np.array([0.001, -1.0, 0.01])
        JUMP_BOUNDS_HIGH = np.array([10.0,   1.0, 1.00])
        MIN_MP = 0.50

        def jump_mse(jump_params: np.ndarray) -> float:
            lam, mu_j, delta_j = np.clip(jump_params, JUMP_BOUNDS_LOW, JUMP_BOUNDS_HIGH)
            if lam <= 0 or delta_j <= 0:
                return 1e10
            errors = []
            for K, T, mp in zip(Ks, Ts, mkt_p):
                try:
                    res = bcc_price(S, K, T, risk_free_rate,
                                    v0, kappa, theta, sigma_v, rho,
                                    0.0, lam, mu_j, delta_j, option_type)
                    if mp >= MIN_MP:
                        errors.append(((res['price'] - mp) / mp) ** 2)
                    else:
                        errors.append((res['price'] - mp) ** 2)
                except Exception:
                    errors.append(1e4)
            return float(np.mean(errors))

        # Stage 1: brute search over jump params
        try:
            j0 = brute(jump_mse, self.JUMP_BRUTE_RANGES, finish=None)
        except Exception:
            j0 = np.array([0.5, -0.1, 0.15])

        # Stage 2: bounded Nelder-Mead to prevent degenerate jump parameters
        j0_clipped = np.clip(j0, JUMP_BOUNDS_LOW, JUMP_BOUNDS_HIGH)
        try:
            jmin = minimize(
                jump_mse, j0_clipped,
                method='Nelder-Mead',
                bounds=list(zip(JUMP_BOUNDS_LOW, JUMP_BOUNDS_HIGH)),
                options={'maxiter': 1000, 'fatol': 1e-8, 'xatol': 1e-6, 'disp': False},
            )
            lam, mu_j, delta_j = np.clip(jmin.x, JUMP_BOUNDS_LOW, JUMP_BOUNDS_HIGH)
        except Exception:
            lam, mu_j, delta_j = j0_clipped

        final_mse = float(jump_mse(np.array([lam, mu_j, delta_j])))

        # Compute market and fitted implied volatilities for IV chart
        bcc_strikes: List[float] = []
        bcc_market_ivs: List[float] = []
        bcc_fitted_ivs: List[float] = []
        for K_i, T_i, mp_i in zip(Ks, Ts, mkt_p):
            try:
                fitted_price = bcc_price(S, K_i, T_i, risk_free_rate,
                                         v0, kappa, theta, sigma_v, rho,
                                         0.0, lam, mu_j, delta_j, option_type)['price']

                def _bs_price_bcc(sig, S_=S, K_=K_i, T_=T_i, r_=risk_free_rate, ot=option_type):
                    if sig <= 0 or T_ <= 0:
                        return 0.0
                    from scipy.stats import norm
                    d1 = (np.log(S_ / K_) + (r_ + 0.5 * sig ** 2) * T_) / (sig * np.sqrt(T_))
                    d2 = d1 - sig * np.sqrt(T_)
                    if ot == 'call':
                        return float(S_ * norm.cdf(d1) - K_ * np.exp(-r_ * T_) * norm.cdf(d2))
                    else:
                        return float(K_ * np.exp(-r_ * T_) * norm.cdf(-d2) - S_ * norm.cdf(-d1))

                def _iv_bcc(price):
                    lo, hi = 1e-4, 5.0
                    for _ in range(50):
                        mid = (lo + hi) / 2.0
                        if _bs_price_bcc(mid) > price:
                            hi = mid
                        else:
                            lo = mid
                        if hi - lo < 1e-6:
                            break
                    return float((lo + hi) / 2.0)

                bcc_strikes.append(float(K_i))
                bcc_market_ivs.append(_iv_bcc(mp_i))
                bcc_fitted_ivs.append(_iv_bcc(max(fitted_price, 1e-8)))
            except Exception:
                pass

        if bcc_strikes:
            sorted_triples = sorted(zip(bcc_strikes, bcc_market_ivs, bcc_fitted_ivs), key=lambda x: x[0])
            bcc_strikes, bcc_market_ivs, bcc_fitted_ivs = map(list, zip(*sorted_triples))

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
            'strikes':    bcc_strikes,
            'market_ivs': bcc_market_ivs,
            'fitted_ivs': bcc_fitted_ivs,
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
