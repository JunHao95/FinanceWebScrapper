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


def _synthetic_ohlcv():
    """60-row OHLCV with close prices 140–160, uniform volume = 1_000_000."""
    import numpy as np
    idx = pd.date_range('2024-01-01', periods=60, freq='B')
    closes = (pd.RangeIndex(60).astype(float) / 59 * 20 + 140).values  # numpy array 140..160
    df = pd.DataFrame({
        'Open':   closes - 0.5,
        'High':   closes + 1.0,
        'Low':    closes - 1.0,
        'Close':  closes,
        'Volume': 1_000_000.0,
    }, index=idx)
    return df


class TestComputeVolumeProfile:
    """Phase 19 unit tests for compute_volume_profile."""

    def test_volume_profile_keys(self):
        from src.analytics.trading_indicators import compute_volume_profile
        df = _synthetic_ohlcv()
        result = compute_volume_profile(df, 'AAPL', 90)
        for key in ('traces', 'layout', 'signal', 'bin_width_usd', 'poc', 'vah', 'val'):
            assert key in result, f"Missing key: {key}"

    def test_poc_inside_price_range(self):
        from src.analytics.trading_indicators import compute_volume_profile
        df = _synthetic_ohlcv()
        result = compute_volume_profile(df, 'AAPL', 90)
        assert df['Low'].min() <= result['poc'] <= df['High'].max()

    def test_value_area_coverage(self):
        from src.analytics.trading_indicators import compute_volume_profile
        df = _synthetic_ohlcv()
        result = compute_volume_profile(df, 'AAPL', 90)
        assert result['signal'] in ('inside', 'outside')
        assert result['val'] <= result['vah']

    def test_bin_width_usd(self):
        from src.analytics.trading_indicators import compute_volume_profile
        df = _synthetic_ohlcv()
        result = compute_volume_profile(df, 'AAPL', 90)
        assert result['bin_width_usd'] > 0
        assert isinstance(result['bin_width_usd'], float)

    def test_route_includes_volume_profile_traces(self, client):
        stub_vp = {
            'traces': [], 'layout': {}, 'signal': 'inside',
            'bin_width_usd': 0.50, 'poc': 150.0, 'vah': 155.0, 'val': 145.0,
        }
        with patch('src.analytics.trading_indicators.fetch_ohlcv', return_value=_stub_ohlcv()), \
             patch('src.analytics.trading_indicators.compute_volume_profile', return_value=stub_vp):
            resp = client.get('/api/trading_indicators?ticker=AAPL&lookback=90')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['volume_profile']['traces'] == []
