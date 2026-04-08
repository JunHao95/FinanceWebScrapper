"""
Tests for GET /api/trading_indicators and fetch_ohlcv() — Phase 18 backend scaffold.

Tests are written TDD-first: they initially fail (RED) because the module and
route don't exist yet. They turn GREEN after Plan 01 Task 2.
"""
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from webapp import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


def _stub_ohlcv():
    """Minimal valid OHLCV DataFrame with tz-naive index (simulates yfinance output)."""
    idx = pd.date_range('2024-01-01', periods=90, freq='B')
    df = pd.DataFrame({
        'Open': 1.0,
        'High': 2.0,
        'Low': 0.5,
        'Close': 1.5,
        'Volume': 1000.0,
        'Dividends': 0.0,
        'Stock Splits': 0.0,
    }, index=idx)
    return df


class TestTradingIndicatorsRoute:
    """Happy path: route returns 200 with all placeholder keys."""

    def test_trading_indicators_200_shape(self, client):
        with patch(
            'src.analytics.trading_indicators.fetch_ohlcv',
            return_value=_stub_ohlcv()[['Open', 'High', 'Low', 'Close', 'Volume']],
        ):
            resp = client.get('/api/trading_indicators?ticker=AAPL&lookback=90')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['ticker'] == 'AAPL'
        assert data['lookback'] == 90
        for key in ('volume_profile', 'anchored_vwap', 'order_flow', 'liquidity_sweep', 'composite_bias'):
            assert key in data, f"Missing key: {key}"

    def test_trading_indicators_missing_ticker(self, client):
        resp = client.get('/api/trading_indicators')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'error' in data


class TestFetchOhlcv:
    """Unit tests for fetch_ohlcv() — validates yfinance pattern and column slice."""

    def test_fetch_ohlcv_returns_ohlcv_dataframe(self):
        from src.analytics.trading_indicators import fetch_ohlcv

        mock_ticker = MagicMock()
        mock_ticker.history.return_value = _stub_ohlcv()

        with patch('yfinance.Ticker', return_value=mock_ticker):
            df = fetch_ohlcv('AAPL', 90)

        assert list(df.columns) == ['Open', 'High', 'Low', 'Close', 'Volume']
        assert df.index.tz is None

    def test_fetch_ohlcv_uses_ticker_history(self):
        from src.analytics.trading_indicators import fetch_ohlcv

        mock_ticker = MagicMock()
        mock_ticker.history.return_value = _stub_ohlcv()

        with patch('yfinance.Ticker', return_value=mock_ticker) as mock_yf:
            fetch_ohlcv('AAPL', 90)

        mock_yf.assert_called_once_with('AAPL')
        mock_ticker.history.assert_called_once()
