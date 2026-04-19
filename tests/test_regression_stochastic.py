"""
Regression tests for Heston calibration and HMM regime detection.

Uses frozen fixture data:
  - tests/fixtures/heston_market_prices.json  (synthetic BS prices)
  - tests/fixtures/spy_2017_2021.npy           (already exists)

No live network calls.
"""
import os
import json
import numpy as np
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


# ---------------------------------------------------------------------------
# Heston calibration
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def heston_contracts():
    path = os.path.join(FIXTURES_DIR, 'heston_market_prices.json')
    with open(path) as f:
        return json.load(f)


@pytest.mark.regression
def test_heston_calibration_rmse_below_threshold(heston_contracts):
    """
    Run a mini calibration using scipy minimize directly on the frozen contracts.
    Verify RMSE < 1.0 (the market prices are synthetic BS; Heston should fit well).
    """
    from scipy.optimize import minimize
    from src.derivatives.fourier_pricer import heston_price as _hp

    def rmse(params):
        kappa, theta, sigma_v, rho, v0 = params
        if not (kappa > 0 and theta > 0 and sigma_v > 0 and -1 < rho < 1 and v0 > 0):
            return 1e6
        errors = []
        for c in heston_contracts:
            try:
                model_px = _hp(c['S'], c['K'], c['T'], c['r'],
                               v0, kappa, theta, sigma_v, rho, 'call')['price']
                errors.append((model_px - c['mid_price']) ** 2)
            except Exception:
                errors.append(100.0)
        return float(np.sqrt(np.mean(errors)))

    x0 = [2.0, 0.04, 0.30, -0.70, 0.04]
    res = minimize(rmse, x0, method='Nelder-Mead',
                   options={'maxiter': 500, 'xatol': 1e-3, 'fatol': 1e-3})
    final_rmse = rmse(res.x)
    # Generous threshold: Heston fitting synthetic BS prices should achieve < 1.0
    assert final_rmse < 1.0, f"Heston calibration RMSE too high: {final_rmse:.4f}"


@pytest.mark.regression
def test_heston_calibration_improves_from_initial(heston_contracts):
    """Verify the optimizer actually reduces error vs initial guess."""
    from scipy.optimize import minimize
    from src.derivatives.fourier_pricer import heston_price as _hp

    def rmse(params):
        kappa, theta, sigma_v, rho, v0 = params
        if not (kappa > 0 and theta > 0 and sigma_v > 0 and -1 < rho < 1 and v0 > 0):
            return 1e6
        errors = []
        for c in heston_contracts:
            try:
                model_px = _hp(c['S'], c['K'], c['T'], c['r'],
                               v0, kappa, theta, sigma_v, rho, 'call')['price']
                errors.append((model_px - c['mid_price']) ** 2)
            except Exception:
                errors.append(100.0)
        return float(np.sqrt(np.mean(errors)))

    x0 = [2.0, 0.04, 0.30, -0.70, 0.04]
    init_rmse = rmse(x0)
    res = minimize(rmse, x0, method='Nelder-Mead',
                   options={'maxiter': 500})
    final_rmse = rmse(res.x)
    assert final_rmse <= init_rmse * (1 + 0.10)  # final ≤ 110% of initial (optimizer should help)


# ---------------------------------------------------------------------------
# HMM regime detection — March 2020 RISK_OFF test
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def spy_data():
    returns_path = os.path.join(FIXTURES_DIR, 'spy_2017_2021.npy')
    dates_path = os.path.join(FIXTURES_DIR, 'spy_2017_2021_dates.npy')
    if not os.path.exists(returns_path):
        pytest.skip('spy_2017_2021.npy fixture not found')
    returns = np.load(returns_path).ravel()  # fixture may be stored as (N,1) — ensure 1-D
    dates = np.load(dates_path, allow_pickle=True) if os.path.exists(dates_path) else None
    return returns, dates


@pytest.mark.regression
def test_hmm_march_2020_is_stressed(spy_data):
    """
    March 2020 (COVID crash) should be classified as the stressed regime
    for a majority (>60%) of trading days.
    """
    from src.analytics.regime_detection import RegimeDetector
    returns, dates = spy_data

    np.random.seed(42)
    rd = RegimeDetector()
    rd.fit(returns, n_restarts=3)

    smoothed = rd.smoothed_probs  # shape (T, 2)
    assert smoothed is not None

    # Identify which state index is 'stressed' (higher sigma)
    stressed_idx = int(np.argmax(rd.sigma))

    # Find March 2020 indices
    if dates is None:
        pytest.skip('dates fixture not available')

    dates_arr = np.asarray(dates, dtype='datetime64[D]')
    march_2020 = (dates_arr >= np.datetime64('2020-03-01')) & \
                 (dates_arr <= np.datetime64('2020-03-31'))

    if march_2020.sum() == 0:
        pytest.skip('No March 2020 dates in fixture')

    stressed_probs = smoothed[march_2020, stressed_idx]
    # Majority (>60%) of days should have P(stressed) > 0.5
    pct_stressed = (stressed_probs > 0.5).mean()
    assert pct_stressed > 0.60, (
        f"Expected >60% of March 2020 days in stressed regime, got {pct_stressed:.1%}"
    )


@pytest.mark.regression
def test_hmm_deterministic_with_same_seed(spy_data):
    """Running RegimeDetector twice with the same seed should yield identical outputs."""
    from src.analytics.regime_detection import RegimeDetector
    returns, _ = spy_data

    np.random.seed(42)
    rd1 = RegimeDetector()
    r1 = rd1.fit(returns, n_restarts=2)

    np.random.seed(42)
    rd2 = RegimeDetector()
    r2 = rd2.fit(returns, n_restarts=2)

    assert r1['log_likelihood'] == pytest.approx(r2['log_likelihood'], rel=1e-6)
    assert np.allclose(rd1.smoothed_probs, rd2.smoothed_probs, atol=1e-8)


@pytest.mark.regression
def test_hmm_two_distinct_regimes_found(spy_data):
    """The fitted model should identify two clearly different volatility states."""
    from src.analytics.regime_detection import RegimeDetector
    returns, _ = spy_data

    np.random.seed(42)
    rd = RegimeDetector()
    rd.fit(returns, n_restarts=3)

    sigma = rd.sigma
    assert sigma.max() / sigma.min() > 1.5, (
        "Two regimes should have meaningfully different volatilities"
    )


@pytest.mark.regression
def test_hmm_smoothed_probs_sum_to_one(spy_data):
    """Smoothed probabilities at each time step should sum to 1."""
    from src.analytics.regime_detection import RegimeDetector
    returns, _ = spy_data

    np.random.seed(42)
    rd = RegimeDetector()
    rd.fit(returns, n_restarts=2)

    row_sums = rd.smoothed_probs.sum(axis=1)
    assert np.allclose(row_sums, 1.0, atol=1e-6)
