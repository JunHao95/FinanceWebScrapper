"""
Market Regime Detection Module

Implements Hidden Markov Model (HMM) with Hamilton filter for detecting
market regimes (calm vs. stressed) from historical returns.

Based on Module 5: HMM, Hamilton filter, and MLE via L-BFGS-B.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from scipy.optimize import minimize
from scipy.stats import norm
import yfinance as yf
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    Detects market regimes using a 2-state Hidden Markov Model.

    States:
        0 = Calm (low volatility, positive drift)
        1 = Stressed (high volatility, negative drift)

    Parameters per state:
        μ  = mean daily return
        σ  = daily return standard deviation
    Transition matrix:
        P[i,j] = P(state_t = j | state_{t-1} = i)
    """

    def __init__(self, n_states: int = 2):
        if n_states != 2:
            raise ValueError(
                f"RegimeDetector supports exactly 2 states (calm/stressed); "
                f"got n_states={n_states}"
            )
        self.n_states = n_states
        self.logger = logging.getLogger(self.__class__.__name__)
        # Estimated parameters (filled after fit)
        self.mu: Optional[np.ndarray] = None
        self.sigma: Optional[np.ndarray] = None
        self.P: Optional[np.ndarray] = None          # (n_states, n_states)
        self.pi: Optional[np.ndarray] = None         # initial state distribution
        self.filtered_probs: Optional[np.ndarray] = None   # (T, n_states)
        self.smoothed_probs: Optional[np.ndarray] = None   # (T, n_states)
        self.log_likelihood: float = -np.inf

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_returns(self, ticker: str, days: int = 1260) -> np.ndarray:
        """
        Fetch historical log-returns for a ticker via yfinance.

        Args:
            ticker: e.g. 'SPY', '^VIX'
            days:   number of calendar days of history (~5y = 1260 trading)

        Returns:
            1-D numpy array of log-returns
        """
        end = datetime.now()
        start = end - timedelta(days=int(days * 1.5))
        self.logger.info(f"Fetching {ticker} history from {start.date()} to {end.date()}")

        data = yf.download(ticker, start=start.strftime('%Y-%m-%d'),
                           end=end.strftime('%Y-%m-%d'),
                           auto_adjust=True, progress=False)

        if data.empty:
            raise ValueError(f"No data returned for {ticker}")

        closes = data['Close']
        if hasattr(closes, 'squeeze'):
            closes = closes.squeeze()
        closes = closes.dropna()

        log_ret = np.log(closes / closes.shift(1)).dropna().values
        self.logger.info(f"Got {len(log_ret)} log-returns for {ticker}")
        return log_ret

    def fit(self, returns: np.ndarray, n_restarts: int = 5) -> Dict:
        """
        Fit the 2-state HMM by maximum likelihood using L-BFGS-B.

        Args:
            returns:    1-D array of observed returns
            n_restarts: number of random restarts to avoid local optima

        Returns:
            dict with fitted parameters and diagnostics
        """
        best_ll = -np.inf
        best_params = None

        if returns is None:
            raise ValueError("returns must not be None")
        if not hasattr(returns, 'size') or returns.size == 0:
            raise ValueError("returns must be a non-empty array")
        if not np.all(np.isfinite(returns)):
            raise ValueError("returns contains non-finite values (NaN or Inf)")

        for trial in range(n_restarts):
            x0 = self._random_init(returns, trial)
            try:
                res = minimize(
                    fun=self._neg_log_likelihood,
                    x0=x0,
                    args=(returns,),
                    method='L-BFGS-B',
                    bounds=self._get_bounds(),
                    options={'maxiter': 500, 'ftol': 1e-10}
                )
                if res.success and -res.fun > best_ll:
                    best_ll = -res.fun
                    best_params = res.x
            except Exception as e:
                self.logger.debug(f"Restart {trial} failed: {e}")
                continue

        if best_params is None:
            raise RuntimeError("HMM fitting failed on all restarts")

        self._unpack_params(best_params)
        self.log_likelihood = best_ll

        # Run Hamilton filter to get filtered probabilities
        self.filtered_probs, _ = self._hamilton_filter(returns)

        # Run backward pass for smoothed probabilities
        self.smoothed_probs = self._backward_smooth(returns, self.filtered_probs)

        return self._build_result(returns)

    def analyze(self, tickers: List[str], days: int = 1260) -> Dict:
        """
        High-level wrapper: fetch returns for tickers, fit HMM, return results.
        Uses the first ticker in the list (or '^VIX' if available).

        Args:
            tickers: list of stock ticker symbols
            days:    history length in calendar days

        Returns:
            dict with regime analysis results
        """
        try:
            # Use first ticker if available, otherwise fall back to SPY
            primary = tickers[0] if len(tickers) > 0 else 'SPY'

            returns = self.fetch_returns(primary, days=days)
            result = self.fit(returns, n_restarts=3)
            result['ticker_used'] = primary
            return result

        except Exception as e:
            self.logger.error(f"Regime detection failed: {e}")
            return {'error': str(e)}

    # ------------------------------------------------------------------
    # Hamilton Filter
    # ------------------------------------------------------------------

    def _hamilton_filter(
        self, returns: np.ndarray
    ) -> Tuple[np.ndarray, float]:
        """
        Forward pass: compute filtered regime probabilities P(S_t | y_1..t).

        Returns:
            filtered (T, n_states), log-likelihood scalar
        """
        T = len(returns)
        K = self.n_states
        filtered = np.zeros((T, K))
        log_lik = 0.0

        # Initial distribution
        prob = self.pi.copy()

        for t in range(T):
            # Emission probabilities
            # f(y_t | S_t = k)
            emission = np.array([
                norm.pdf(returns[t], loc=self.mu[k], scale=self.sigma[k])
                for k in range(K)
            ])
            emission = np.clip(emission, 1e-300, None)

            # Joint: P(S_t=k, y_1..t) = P(S_t=k | y_1..t-1) * f(y_t | S_t=k)
            joint = prob * emission
            lik_t = joint.sum()
            if lik_t < 1e-300:
                lik_t = 1e-300
            log_lik += np.log(lik_t)

            # Filtered: P(S_t=k | y_1..t)
            filtered[t] = joint / lik_t

            # Predict: P(S_{t+1}=j | y_1..t) = sum_k P(S_{t+1}=j | S_t=k) * filtered[t,k]
            prob = self.P.T @ filtered[t]
            prob = np.clip(prob, 1e-300, None)
            prob /= prob.sum()

        return filtered, log_lik

    def _backward_smooth(
        self, returns: np.ndarray, filtered: np.ndarray
    ) -> np.ndarray:
        """
        Backward pass (Kim smoother) for smoothed P(S_t | all data).
        """
        T = len(returns)
        K = self.n_states
        smoothed = np.zeros((T, K))
        smoothed[-1] = filtered[-1]

        for t in range(T - 2, -1, -1):
            # Predicted next state prob
            pred_next = self.P.T @ filtered[t]
            pred_next = np.clip(pred_next, 1e-300, None)

            for k in range(K):
                ratio = (self.P[k, :] * smoothed[t + 1] / pred_next)
                smoothed[t, k] = filtered[t, k] * ratio.sum()

            s = smoothed[t].sum()
            if s > 0:
                smoothed[t] /= s

        return smoothed

    # ------------------------------------------------------------------
    # Negative log-likelihood & helpers
    # ------------------------------------------------------------------

    def _neg_log_likelihood(self, params: np.ndarray, returns: np.ndarray) -> float:
        try:
            self._unpack_params(params)
            _, log_lik = self._hamilton_filter(returns)
            return -log_lik
        except Exception:
            return 1e10

    def _unpack_params(self, params: np.ndarray):
        """Unpack flat parameter vector into model attributes."""
        K = self.n_states
        self.mu = params[:K]
        self.sigma = np.abs(params[K:2 * K]) + 1e-6
        # Transition probabilities via softmax within each row
        raw_P = params[2 * K:].reshape(K, K)
        self.P = np.exp(raw_P) / np.exp(raw_P).sum(axis=1, keepdims=True)
        # Stationary distribution as initial pi
        vals, vecs = np.linalg.eig(self.P.T)
        stat = np.real(vecs[:, np.argmin(np.abs(vals - 1))])
        stat = np.abs(stat)
        self.pi = stat / stat.sum()

    def _random_init(self, returns: np.ndarray, seed: int) -> np.ndarray:
        rng = np.random.default_rng(seed)
        mu_init = [returns.mean() + rng.normal(0, returns.std()),
                   returns.mean() - rng.normal(0, returns.std())]
        sig_init = [abs(rng.normal(returns.std(), 0.001)),
                    abs(rng.normal(returns.std() * 2, 0.001))]
        # raw transition matrix (will be softmax'd)
        P_raw = rng.normal(0, 0.5, size=(self.n_states, self.n_states)).flatten()
        return np.array(mu_init + sig_init + list(P_raw))

    def _get_bounds(self):
        K = self.n_states
        mu_bounds = [(-0.1, 0.1)] * K
        sig_bounds = [(1e-5, 0.3)] * K
        P_bounds = [(-10, 10)] * (K * K)
        return mu_bounds + sig_bounds + P_bounds

    # ------------------------------------------------------------------
    # Result builder
    # ------------------------------------------------------------------

    def _build_result(self, returns: np.ndarray) -> Dict:
        """Build output dict with regime info and trading signal."""
        K = self.n_states

        # Determine which state is "calm" (lower sigma)
        calm_idx = int(np.argmin(self.sigma))
        stressed_idx = int(np.argmax(self.sigma))

        # Current regime: last filtered probability
        current_probs = self.filtered_probs[-1].tolist()
        current_regime_idx = int(np.argmax(self.filtered_probs[-1]))
        current_regime = 'calm' if current_regime_idx == calm_idx else 'stressed'

        # Regime sequence (0 = calm, 1 = stressed at each time step)
        regime_sequence = [
            'calm' if int(np.argmax(self.filtered_probs[t])) == calm_idx else 'stressed'
            for t in range(len(returns))
        ]

        # Fraction of time in stressed regime
        stress_fraction = regime_sequence.count('stressed') / len(regime_sequence)

        # Trading signal
        stressed_prob = current_probs[stressed_idx]
        if stressed_prob >= 0.7:
            signal = 'RISK_OFF'
            signal_desc = 'High stress probability — consider defensive positioning'
        elif stressed_prob >= 0.4:
            signal = 'NEUTRAL'
            signal_desc = 'Uncertain regime — maintain balanced exposure'
        else:
            signal = 'RISK_ON'
            signal_desc = 'Calm regime detected — risk assets favored'

        # Feller condition equivalent: not applicable for returns HMM, but
        # record calibration quality via log-likelihood
        params_per_state = {
            f'state_{k}': {
                'regime': 'calm' if k == calm_idx else 'stressed',
                'mu_daily': float(self.mu[k]),
                'mu_annualized': float(self.mu[k] * 252),
                'sigma_daily': float(self.sigma[k]),
                'sigma_annualized': float(self.sigma[k] * np.sqrt(252)),
            }
            for k in range(K)
        }

        transition_matrix = {
            f'P({i}->{j})': float(self.P[i, j])
            for i in range(K) for j in range(K)
        }

        # Recent regime probabilities (last 20 observations)
        recent_filtered = [
            {
                'calm_prob': float(self.filtered_probs[t, calm_idx]),
                'stressed_prob': float(self.filtered_probs[t, stressed_idx])
            }
            for t in range(-min(20, len(returns)), 0)
        ]

        return {
            'model': '2-State HMM (Hamilton Filter)',
            'log_likelihood': float(self.log_likelihood),
            'n_observations': len(returns),
            'parameters': params_per_state,
            'transition_matrix': transition_matrix,
            'stationary_distribution': {
                'calm': float(self.pi[calm_idx]),
                'stressed': float(self.pi[stressed_idx])
            },
            'current_regime': current_regime,
            'current_probabilities': {
                'calm': float(current_probs[calm_idx]),
                'stressed': float(current_probs[stressed_idx])
            },
            'signal': signal,
            'signal_description': signal_desc,
            'stress_fraction_historical': float(stress_fraction),
            'recent_filtered_probs': recent_filtered,
        }
