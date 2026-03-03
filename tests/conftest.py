"""
Shared fixtures for Phase 1 math correctness benchmarks.
"""
import numpy as np
import pytest
import os


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow (requires network/long runtime)")


@pytest.fixture
def zero_default_matrix():
    """
    8x8 identity transition matrix: every rating stays put, zero default probability.
    Used for par bond test (MATH-01): isolates coupon discounting from credit risk.
    Ratings order: AAA AA A BBB BB B CCC D (same as RATINGS in credit_transitions.py)
    """
    return np.eye(8)


@pytest.fixture
def standard_heston_params():
    """
    Standard Heston model parameters for Fourier pricer tests (MATH-05).
    Chosen to be well within typical SPY calibrated range.
    """
    return {
        'S': 100.0,
        'K': 100.0,   # ATM
        'T': 1.0,
        'r': 0.05,
        'v0': 0.04,       # initial variance (vol = 20%)
        'kappa': 2.0,     # mean reversion speed
        'theta': 0.04,    # long-run variance
        'sigma_v': 0.30,  # vol of vol
        'rho': -0.70,     # correlation (negative for equity)
    }


@pytest.fixture(scope='session')
def spy_returns():
    """
    SPY log-returns from 2017-01-01 to 2021-01-01.
    Loads from cached fixture file if available; fetches from yfinance as fallback.
    The date range guarantees March 2020 is included.
    """
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'spy_2017_2021.npy')
    dates_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'spy_2017_2021_dates.npy')

    if os.path.exists(fixture_path):
        returns = np.load(fixture_path)
        dates = np.load(dates_path, allow_pickle=True) if os.path.exists(dates_path) else None
        return returns, dates

    # Fallback: fetch from yfinance
    try:
        import yfinance as yf
        import pandas as pd
        spy = yf.download('SPY', start='2017-01-01', end='2021-01-01',
                          progress=False, auto_adjust=True)
        prices = spy['Close'].dropna()
        log_ret = np.log(prices / prices.shift(1)).dropna()
        returns = log_ret.values
        dates = log_ret.index.to_numpy()

        # Cache for future runs
        os.makedirs(os.path.dirname(fixture_path), exist_ok=True)
        np.save(fixture_path, returns)
        np.save(dates_path, dates)

        return returns, dates
    except Exception as e:
        pytest.skip(f'Could not fetch SPY data: {e}')


@pytest.fixture
def market_yields_normal():
    """
    A set of market yields where CIR calibration should succeed with Feller satisfied.
    Approximate US Treasury curve (realistic).
    """
    return [(1, 0.050), (2, 0.052), (5, 0.055), (7, 0.058), (10, 0.060)]
