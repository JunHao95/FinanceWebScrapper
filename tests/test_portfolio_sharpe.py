"""
Tests for POST /api/portfolio_sharpe — HEALTH-01 backend coverage.

All tests are marked @pytest.mark.slow because they make real network calls
to yfinance. Skip them in fast CI runs with: pytest -m "not slow"
"""
import pytest
from webapp import app as flask_app

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


@pytest.mark.slow
def test_portfolio_sharpe_missing_tickers(client):
    """POST {} (no tickers) should respond gracefully — 500 with error or 200."""
    resp = client.post('/api/portfolio_sharpe',
                       json={},
                       content_type='application/json')
    assert resp.status_code in (200, 500)
    data = resp.get_json()
    assert data is not None


@pytest.mark.slow
def test_portfolio_sharpe_returns_keys(client):
    """Multi-ticker POST returns JSON with sharpe, rf_rate, and period keys."""
    resp = client.post(
        '/api/portfolio_sharpe',
        json={
            'tickers': ['AAPL', 'MSFT'],
            'weights': {'AAPL': 0.6, 'MSFT': 0.4},
            'start_date': '2023-01-01',
            'end_date': '2024-01-01',
        },
        content_type='application/json',
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'sharpe' in data
    assert 'rf_rate' in data
    assert 'period' in data


@pytest.mark.slow
def test_portfolio_sharpe_single_ticker(client):
    """Single-ticker POST returns a numeric sharpe (not None, not an error key)."""
    resp = client.post(
        '/api/portfolio_sharpe',
        json={
            'tickers': ['AAPL'],
            'weights': {'AAPL': 1.0},
            'start_date': '2023-01-01',
            'end_date': '2024-01-01',
        },
        content_type='application/json',
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'error' not in data, f"Route returned error: {data.get('error')}"
    assert data.get('sharpe') is not None
    assert isinstance(data['sharpe'], (int, float))
