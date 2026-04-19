"""
Shared fixtures and configuration for the FinanceWebScrapper test suite.

Critical user flows (TEST-01):
  1. Stock scraping pipeline — user enters a ticker, scraper fetches financials, results returned as JSON.
  2. Stochastic model computation — user POSTs parameters, backend runs Heston/CIR/Vasicek, returns calibrated curve.
  3. Trading indicator generation — user GETs /api/trading_indicators?ticker=X, backend returns volume profile,
     anchored VWAP, order flow, liquidity sweep, and composite bias.
  4. Chatbot interaction — user POSTs a message with optional context, LLM agent responds with financial analysis.
  5. Portfolio health scoring — user POSTs ticker list, backend fetches returns, computes Sharpe/VaR metrics.
"""
import socket
import threading
import time
import numpy as np
import pytest
import os


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow (requires network/long runtime)")
    config.addinivalue_line("markers", "unit: fast, isolated, no I/O")
    config.addinivalue_line("markers", "integration: uses Flask test client or real subsystems")
    config.addinivalue_line("markers", "regression: guards against previously fixed bugs")
    config.addinivalue_line("markers", "e2e: full browser end-to-end via Playwright")


@pytest.fixture
def client():
    import webapp
    webapp.app.config['TESTING'] = True
    with webapp.app.test_client() as c:
        yield c


@pytest.fixture(scope='session')
def flask_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()

    import webapp
    t = threading.Thread(
        target=webapp.app.run,
        kwargs=dict(host='localhost', port=port, use_reloader=False),
        daemon=True,
    )
    t.start()
    time.sleep(0.5)
    yield f'http://localhost:{port}'


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
        returns = np.load(fixture_path).ravel()  # ensure 1-D (fixture may be stored as (N,1))
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
