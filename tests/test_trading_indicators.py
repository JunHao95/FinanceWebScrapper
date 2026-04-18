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


def _synthetic_365d_ohlcv():
    """365-row OHLCV with closes rising 100→150, uniform volume = 1_000_000."""
    import numpy as np
    idx = pd.date_range('2023-01-01', periods=365, freq='B')
    closes = (pd.RangeIndex(365).astype(float) / 364 * 50 + 100).values  # 100..150
    df = pd.DataFrame({
        'Open':   closes - 0.5,
        'High':   closes + 1.0,
        'Low':    closes - 1.0,
        'Close':  closes,
        'Volume': 1_000_000.0,
    }, index=idx)
    return df


def _make_mock_ticker_no_earnings():
    """yfinance Ticker mock with no earnings data."""
    mock = MagicMock()
    mock.earnings_dates = None
    return mock


def _make_mock_ticker_with_earnings(past_date):
    """yfinance Ticker mock with a valid past earnings date."""
    import numpy as np
    idx = pd.DatetimeIndex([past_date], tz='America/New_York')
    ed = pd.DataFrame({'Reported EPS': [1.23]}, index=idx)
    mock = MagicMock()
    mock.earnings_dates = ed
    return mock


class TestComputeAnchoredVwap:
    """Phase 20 unit tests for compute_anchored_vwap."""

    def test_avwap_keys(self):
        from src.analytics.trading_indicators import compute_anchored_vwap
        df = _synthetic_365d_ohlcv()
        with patch('yfinance.Ticker', return_value=_make_mock_ticker_no_earnings()):
            result = compute_anchored_vwap(df, 'AAPL', 90)
        for key in ('traces', 'layout', 'signal', 'convergence', 'current_price',
                    'earnings_unavailable', 'labels'):
            assert key in result, f"Missing key: {key}"

    def test_avwap_values_in_range(self):
        from src.analytics.trading_indicators import compute_anchored_vwap
        df = _synthetic_365d_ohlcv()
        with patch('yfinance.Ticker', return_value=_make_mock_ticker_no_earnings()):
            result = compute_anchored_vwap(df, 'AAPL', 90)
        lo, hi = df['Low'].min(), df['High'].max()
        # find scatter traces (non-candlestick) and check their final y value
        scatter_traces = [t for t in result['traces'] if t.get('type') == 'scatter']
        for t in scatter_traces:
            y_vals = [v for v in t['y'] if v is not None]
            if y_vals:
                assert lo <= y_vals[-1] <= hi, f"AVWAP value {y_vals[-1]} out of range [{lo}, {hi}]"

    def test_earnings_unavailable_when_no_data(self):
        from src.analytics.trading_indicators import compute_anchored_vwap
        df = _synthetic_365d_ohlcv()
        with patch('yfinance.Ticker', return_value=_make_mock_ticker_no_earnings()):
            result = compute_anchored_vwap(df, 'AAPL', 90)
        assert result['earnings_unavailable'] is True
        scatter_traces = [t for t in result['traces'] if t.get('type') == 'scatter']
        assert len(scatter_traces) == 2, f"Expected 2 scatter traces, got {len(scatter_traces)}"

    def test_earnings_avwap_present_when_date_found(self):
        from src.analytics.trading_indicators import compute_anchored_vwap
        df = _synthetic_365d_ohlcv()
        past_date = pd.Timestamp('2023-06-01')
        with patch('yfinance.Ticker', return_value=_make_mock_ticker_with_earnings(past_date)):
            result = compute_anchored_vwap(df, 'AAPL', 90)
        assert result['earnings_unavailable'] is False
        scatter_traces = [t for t in result['traces'] if t.get('type') == 'scatter']
        assert len(scatter_traces) == 3, f"Expected 3 scatter traces, got {len(scatter_traces)}"

    def test_convergence_detection(self):
        from src.analytics.trading_indicators import compute_anchored_vwap
        import numpy as np
        # All bars have High = Low = Close = 100 -> TP = 100 = current_price
        # AVWAP from any anchor = 100.0, which equals current_price -> convergence fires
        idx = pd.date_range('2023-01-01', periods=365, freq='B')
        closes = np.full(365, 100.0)
        df = pd.DataFrame({
            'Open':   closes,
            'High':   closes,
            'Low':    closes,
            'Close':  closes,
            'Volume': 1_000_000.0,
        }, index=idx)
        with patch('yfinance.Ticker', return_value=_make_mock_ticker_no_earnings()):
            result = compute_anchored_vwap(df, 'AAPL', 90)
        assert len(result['convergence']) > 0, "Expected at least one converging AVWAP line"

    def test_no_convergence_when_far(self):
        from src.analytics.trading_indicators import compute_anchored_vwap
        import numpy as np
        # current_price ~150, but AVWAP will be anchored at index[0] where High=200 -> very far
        idx = pd.date_range('2023-01-01', periods=365, freq='B')
        highs = np.linspace(200, 201, 365)   # 52-wk high anchor at start price=200
        lows  = np.linspace(50, 51, 365)     # 52-wk low anchor at start price=50
        closes = np.linspace(100, 150, 365)  # current price ~150
        df = pd.DataFrame({
            'Open':   closes,
            'High':   highs,
            'Low':    lows,
            'Close':  closes,
            'Volume': 1_000_000.0,
        }, index=idx)
        with patch('yfinance.Ticker', return_value=_make_mock_ticker_no_earnings()):
            result = compute_anchored_vwap(df, 'AAPL', 90)
        assert result['convergence'] == [], f"Expected empty convergence, got {result['convergence']}"

    def test_short_lookback_uses_365d_anchor(self):
        from src.analytics.trading_indicators import compute_anchored_vwap
        df = _synthetic_365d_ohlcv()
        lookback = 30
        with patch('yfinance.Ticker', return_value=_make_mock_ticker_no_earnings()):
            result = compute_anchored_vwap(df, 'AAPL', lookback)
        scatter_traces = [t for t in result['traces'] if t.get('type') == 'scatter']
        # Each scatter trace should have exactly `lookback` x-values in the display window
        for t in scatter_traces:
            assert len(t['x']) == lookback, (
                f"Expected trace length {lookback}, got {len(t['x'])}"
            )


def _make_ohlcv(n=30, price_start=100.0, price_step=0.5, vol_start=1000.0, vol_step=0.0,
                doji_idx=None):
    """Build a synthetic OHLCV DataFrame. Optionally insert a doji bar (High==Low) at doji_idx."""
    import numpy as np
    idx = pd.date_range('2024-01-01', periods=n, freq='B')
    closes = [price_start + i * price_step for i in range(n)]
    opens  = [c - 0.2 for c in closes]
    highs  = [c + 0.5 for c in closes]
    lows   = [c - 0.5 for c in closes]
    vols   = [vol_start + i * vol_step for i in range(n)]
    if doji_idx is not None:
        highs[doji_idx] = closes[doji_idx]
        lows[doji_idx]  = closes[doji_idx]
    return pd.DataFrame({
        'Open': opens, 'High': highs, 'Low': lows, 'Close': closes, 'Volume': vols,
    }, index=idx)


class TestComputeOrderFlow:

    def test_order_flow_keys(self):
        from src.analytics.trading_indicators import compute_order_flow
        df = _make_ohlcv(n=30)
        result = compute_order_flow(df, 'TEST', 30)
        assert set(result.keys()) >= {'traces', 'layout', 'signal', 'divergence'}
        assert set(result['divergence'].keys()) >= {'detected', 'price_slope', 'vol_slope'}

    def test_no_nan_in_cumulative_delta(self):
        from src.analytics.trading_indicators import compute_order_flow
        # Insert a doji bar (High==Low) at index 5 to exercise epsilon guard
        df = _make_ohlcv(n=30, doji_idx=5)
        result = compute_order_flow(df, 'TEST', 30)
        # cumulative delta is traces[1]['y']
        cum_delta = result['traces'][1]['y']
        assert all(v is not None for v in cum_delta), "NaN found in cumulative delta series"

    def test_epsilon_guard_on_zero_range(self):
        from src.analytics.trading_indicators import compute_order_flow
        # Single bar where Open=Close=High=Low (zero range)
        df = pd.DataFrame({
            'Open': [100.0], 'High': [100.0], 'Low': [100.0],
            'Close': [100.0], 'Volume': [1000.0],
        }, index=pd.date_range('2024-01-01', periods=1, freq='B'))
        result = compute_order_flow(df, 'TEST', 1)
        assert result['signal'] in ('bullish', 'bearish', 'neutral')

    def test_divergence_detected_opposite_slopes(self):
        from src.analytics.trading_indicators import compute_order_flow
        import numpy as np
        n = 15
        idx = pd.date_range('2024-01-01', periods=n, freq='B')
        closes = [100.0 + i * 0.5 for i in range(n)]          # rising price
        vols   = [2000.0 - i * 100.0 for i in range(n)]       # falling volume
        df = pd.DataFrame({
            'Open':  [c - 0.1 for c in closes],
            'High':  [c + 0.5 for c in closes],
            'Low':   [c - 0.5 for c in closes],
            'Close': closes,
            'Volume': vols,
        }, index=idx)
        result = compute_order_flow(df, 'TEST', n)
        assert result['divergence']['detected'] is True

    def test_no_divergence_same_sign_slopes(self):
        from src.analytics.trading_indicators import compute_order_flow
        n = 15
        idx = pd.date_range('2024-01-01', periods=n, freq='B')
        closes = [100.0 + i * 0.5 for i in range(n)]
        vols   = [1000.0 + i * 50.0 for i in range(n)]        # rising volume
        df = pd.DataFrame({
            'Open':  [c - 0.1 for c in closes],
            'High':  [c + 0.5 for c in closes],
            'Low':   [c - 0.5 for c in closes],
            'Close': closes,
            'Volume': vols,
        }, index=idx)
        result = compute_order_flow(df, 'TEST', n)
        assert result['divergence']['detected'] is False

    def test_imbalance_candle_annotation(self):
        from src.analytics.trading_indicators import compute_order_flow
        n = 25
        idx = pd.date_range('2024-01-01', periods=n, freq='B')
        # All normal bars first (body_ratio ~0.3)
        closes = [100.0 + i * 0.1 for i in range(n)]
        opens  = [c - 0.15 for c in closes]
        highs  = [c + 0.35 for c in closes]
        lows   = [c - 0.35 for c in closes]
        vols   = [100.0] * n
        # Override bar 24 (last): Open=100, Close=108, High=108, Low=100 -> 100% body ratio
        # Volume=1000 vs avg_vol_20=100 -> 10x spike
        closes[24] = 108.0
        opens[24]  = 100.0
        highs[24]  = 108.0
        lows[24]   = 100.0
        vols[24]   = 1000.0
        df = pd.DataFrame({
            'Open': opens, 'High': highs, 'Low': lows, 'Close': closes, 'Volume': vols,
        }, index=idx)
        result = compute_order_flow(df, 'TEST', n)
        annotations = result['layout'].get('annotations', [])
        assert len(annotations) >= 1, "Expected at least one imbalance annotation"
        texts = [a.get('text', '') for a in annotations]
        assert any('\u25b2' in t or '\u25bc' in t for t in texts), \
            f"No ▲/▼ annotation found in {texts}"

    def test_no_annotation_normal_candle(self):
        from src.analytics.trading_indicators import compute_order_flow
        n = 25
        idx = pd.date_range('2024-01-01', periods=n, freq='B')
        # body_ratio ~0.3, volume at 1x average everywhere
        closes = [100.0 + i * 0.1 for i in range(n)]
        opens  = [c - 0.15 for c in closes]
        highs  = [c + 0.35 for c in closes]
        lows   = [c - 0.35 for c in closes]
        vols   = [100.0] * n
        df = pd.DataFrame({
            'Open': opens, 'High': highs, 'Low': lows, 'Close': closes, 'Volume': vols,
        }, index=idx)
        result = compute_order_flow(df, 'TEST', n)
        annotations = result['layout'].get('annotations', [])
        assert annotations == [], f"Expected no annotations, got {annotations}"


class TestComputeLiquiditySweep:

    def _sweep_ohlcv(self, n=90):
        import numpy as np
        idx = pd.date_range('2024-01-01', periods=n, freq='B')
        t = np.linspace(0, 4 * np.pi, n)
        closes = 100.0 + 10 * np.sin(t)
        df = pd.DataFrame({
            'Open':   closes - 0.2,
            'High':   closes + 1.0,
            'Low':    closes - 1.0,
            'Close':  closes,
            'Volume': 1_000_000.0,
        }, index=idx)
        return df

    def test_sweep_keys(self):
        from src.analytics.trading_indicators import compute_liquidity_sweep
        df = self._sweep_ohlcv(90)
        result = compute_liquidity_sweep(df, 90)
        for key in ('signal', 'n', 'swept_price', 'sweep_count'):
            assert key in result, f"Missing key: {key}"

    def test_signal_valid_values(self):
        from src.analytics.trading_indicators import compute_liquidity_sweep
        df = self._sweep_ohlcv(90)
        result = compute_liquidity_sweep(df, 90)
        assert result['signal'] in ('bullish', 'bearish', 'none', 'no_swings')

    def test_adaptive_n_30d(self):
        from src.analytics.trading_indicators import _adaptive_n
        assert _adaptive_n(30) == 2

    def test_adaptive_n_90d(self):
        from src.analytics.trading_indicators import _adaptive_n
        assert _adaptive_n(90) == 3

    def test_adaptive_n_180d(self):
        from src.analytics.trading_indicators import _adaptive_n
        assert _adaptive_n(180) == 5

    def test_no_swings_when_too_few_bars(self):
        from src.analytics.trading_indicators import compute_liquidity_sweep
        idx = pd.date_range('2024-01-01', periods=5, freq='B')
        df = pd.DataFrame({
            'Open': 100.0, 'High': 101.0, 'Low': 99.0, 'Close': 100.0, 'Volume': 1000.0,
        }, index=idx)
        result = compute_liquidity_sweep(df, 90)
        assert result['signal'] == 'no_swings'

    def test_look_ahead_regression(self):
        from src.analytics.trading_indicators import compute_liquidity_sweep
        df_90 = self._sweep_ohlcv(90)
        extra = df_90.iloc[[-1]].copy()
        extra.index = [df_90.index[-1] + pd.Timedelta(days=1)]
        df_91 = pd.concat([df_90, extra])
        r90 = compute_liquidity_sweep(df_90, 90)
        r91 = compute_liquidity_sweep(df_91, 90)
        assert r90['sweep_count'] == r91['sweep_count'], (
            f"Look-ahead detected: 90-bar sweep_count={r90['sweep_count']} "
            f"differs from 91-bar sweep_count={r91['sweep_count']}"
        )

    def test_candlestick_trace_present(self):
        from src.analytics.trading_indicators import compute_liquidity_sweep
        df = self._sweep_ohlcv(90)
        result = compute_liquidity_sweep(df, 90)
        assert 'traces' in result
        types = [t.get('type') for t in result.get('traces', [])]
        assert 'candlestick' in types, f"No candlestick trace found: {types}"


class TestComputeCompositeBias:

    def _results(self, vp='inside', avwap='above', of='bullish', sweep='bullish'):
        return {
            'volume_profile':  {'signal': vp},
            'anchored_vwap':   {'signal': avwap},
            'order_flow':      {'signal': of},
            'liquidity_sweep': {'signal': sweep},
        }

    def test_majority_bullish(self):
        from src.analytics.trading_indicators import compute_composite_bias
        r = compute_composite_bias(self._results(sweep='bearish'))
        assert r['direction'] == 'bullish'
        assert r['score'] == '3/4'
        assert len(r['dissenters']) == 1

    def test_majority_bearish(self):
        from src.analytics.trading_indicators import compute_composite_bias
        r = compute_composite_bias(self._results(vp='outside', avwap='below', of='bearish', sweep='bullish'))
        assert r['direction'] == 'bearish'
        assert r['score'] == '3/4'

    def test_tie_is_neutral(self):
        from src.analytics.trading_indicators import compute_composite_bias
        r = compute_composite_bias(self._results(of='bearish', sweep='bearish'))
        assert r['direction'] == 'neutral'

    def test_unavailable_excluded_from_denominator(self):
        from src.analytics.trading_indicators import compute_composite_bias
        results = self._results()
        results['liquidity_sweep'] = {'status': 'stub'}
        r = compute_composite_bias(results)
        assert r['score'] == '3/3'
        assert 'Sweep' in r['unavailable']

    def test_vp_inside_maps_to_bullish(self):
        from src.analytics.trading_indicators import compute_composite_bias
        r = compute_composite_bias(self._results(vp='inside'))
        assert r['direction'] in ('bullish', 'neutral', 'bearish')

    def test_avwap_above_maps_to_bullish(self):
        from src.analytics.trading_indicators import compute_composite_bias
        r = compute_composite_bias(self._results(vp='inside', avwap='above', of='bullish', sweep='bullish'))
        assert r['direction'] == 'bullish'

    def test_avwap_between_maps_to_neutral(self):
        from src.analytics.trading_indicators import compute_composite_bias
        results = {
            'volume_profile':  {'signal': 'inside'},
            'anchored_vwap':   {'signal': 'between'},
            'order_flow':      {'signal': 'bullish'},
            'liquidity_sweep': {'signal': 'bullish'},
        }
        r = compute_composite_bias(results)
        assert r['direction'] == 'bullish'

    def test_keys_present(self):
        from src.analytics.trading_indicators import compute_composite_bias
        r = compute_composite_bias(self._results())
        for k in ('direction', 'score', 'dissenters', 'unavailable'):
            assert k in r, f"Missing key: {k}"
