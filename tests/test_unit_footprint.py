"""
Unit tests for Phase 24 Footprint indicator.
fetch_intraday, compute_footprint, and compute_composite_bias 5-voice extension.
All tests use deterministic inputs — no live network calls.
"""
import os
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from src.analytics.trading_indicators import compute_footprint, compute_composite_bias

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture(scope='module')
def fp_df():
    path = os.path.join(FIXTURES_DIR, 'footprint_15m_ohlcv.csv')
    df = pd.read_csv(path, index_col='Datetime', parse_dates=True)
    return df


def _make_mock_15m_df(n=10, tz_aware=True):
    idx = pd.date_range('2024-01-02 09:30', periods=n, freq='15min', tz='America/New_York' if tz_aware else None)
    return pd.DataFrame({
        'Open':   [150.0] * n,
        'High':   [152.0] * n,
        'Low':    [149.0] * n,
        'Close':  [151.0] * n,
        'Volume': [100000] * n,
    }, index=idx)


# FOOT-01: fetch_intraday returns tz-naive DataFrame with correct columns
def test_fetch_intraday_returns_ohlcv():
    mock_df = _make_mock_15m_df(tz_aware=True)
    with patch('src.analytics.trading_indicators.yf.Ticker') as mock_ticker:
        mock_ticker.return_value.history.return_value = mock_df
        from src.analytics.trading_indicators import fetch_intraday
        result = fetch_intraday('AAPL', 60)
        assert result.index.tz is None
        assert list(result.columns) == ['Open', 'High', 'Low', 'Close', 'Volume']


# FOOT-01 edge: empty DataFrame raises ValueError
def test_fetch_intraday_empty_raises():
    with patch('src.analytics.trading_indicators.yf.Ticker') as mock_ticker:
        mock_ticker.return_value.history.return_value = pd.DataFrame()
        from src.analytics.trading_indicators import fetch_intraday
        with pytest.raises(ValueError, match='No 15m intraday data'):
            fetch_intraday('FAKE', 60)


# FOOT-01: compute_footprint returns all required keys
def test_compute_footprint_keys(fp_df):
    result = compute_footprint(fp_df, 'TEST')
    for key in ('traces', 'layout', 'signal', 'cum_delta', 'total_volume'):
        assert key in result, f"Missing key: {key}"


# FOOT-01: empty DataFrame returns error payload without raising
def test_compute_footprint_empty():
    empty_df = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
    result = compute_footprint(empty_df, 'TEST')
    assert result.get('signal') is None or result.get('error') is not None


# FOOT-02: heatmap trace is the first trace
def test_heatmap_trace_present(fp_df):
    result = compute_footprint(fp_df, 'TEST')
    assert len(result['traces']) >= 1
    assert result['traces'][0]['type'] == 'heatmap'


# FOOT-03: signal = bullish when close near high (buy-dominant)
def test_signal_logic_bullish():
    n = 10
    df = pd.DataFrame({
        'Open':   [100.0] * n,
        'High':   [102.0] * n,
        'Low':    [99.0]  * n,
        'Close':  [101.8] * n,
        'Volume': [10000] * n,
    }, index=pd.date_range('2024-01-02 09:30', periods=n, freq='15min'))
    result = compute_footprint(df, 'X')
    assert result['signal'] == 'bullish'


# FOOT-03: signal = bearish when close near low (sell-dominant)
def test_signal_logic_bearish():
    n = 10
    df = pd.DataFrame({
        'Open':   [100.0] * n,
        'High':   [101.0] * n,
        'Low':    [98.0]  * n,
        'Close':  [98.2]  * n,
        'Volume': [10000] * n,
    }, index=pd.date_range('2024-01-02 09:30', periods=n, freq='15min'))
    result = compute_footprint(df, 'X')
    assert result['signal'] == 'bearish'


# FOOT-03: signal = neutral when close at midpoint
def test_signal_logic_neutral():
    n = 10
    df = pd.DataFrame({
        'Open':   [100.0] * n,
        'High':   [101.0] * n,
        'Low':    [99.0]  * n,
        'Close':  [100.0] * n,
        'Volume': [10000] * n,
    }, index=pd.date_range('2024-01-02 09:30', periods=n, freq='15min'))
    result = compute_footprint(df, 'X')
    assert result['signal'] == 'neutral'


# FOOT-05: composite bias with all 5 voices available → denominator is 5
def test_composite_5_voices():
    results = {
        'volume_profile':  {'signal': 'inside'},
        'anchored_vwap':   {'signal': 'above'},
        'order_flow':      {'signal': 'bullish'},
        'liquidity_sweep': {'signal': 'bullish'},
    }
    fp = {'signal': 'bullish'}
    result = compute_composite_bias(results, footprint_result=fp)
    assert '5' in result['score'], f"Expected 5-voice denominator, got {result['score']}"
    assert result['direction'] == 'bullish'


# FOOT-05: footprint unavailable → 4-voice fallback denominator
def test_composite_footprint_unavailable():
    results = {
        'volume_profile':  {'signal': 'inside'},
        'anchored_vwap':   {'signal': 'above'},
        'order_flow':      {'signal': 'bullish'},
        'liquidity_sweep': {'signal': 'bullish'},
    }
    result = compute_composite_bias(results, footprint_result=None)
    score_parts = result['score'].split('/')
    assert int(score_parts[-1]) == 4, f"Expected 4-voice fallback, got {result['score']}"


# FOOT-05: footprint as dissenter lowers bullish count but doesn't flip direction
def test_composite_footprint_dissenter():
    results = {
        'volume_profile':  {'signal': 'inside'},
        'anchored_vwap':   {'signal': 'above'},
        'order_flow':      {'signal': 'bullish'},
        'liquidity_sweep': {'signal': 'bullish'},
    }
    fp = {'signal': 'bearish'}
    result = compute_composite_bias(results, footprint_result=fp)
    assert result['direction'] == 'bullish'
    assert 'Footprint' in result['dissenters'], f"Footprint should dissent, got {result['dissenters']}"
