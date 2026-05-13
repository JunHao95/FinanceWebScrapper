"""
Unit tests for plan 30-02: Chart NaN fix for SGX tickers.

Verifies that fetch_ohlcv results with trailing NaN rows are stripped before
serialisation, so the /api/price_history route returns valid JSON.
"""

import json
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest


def _make_ohlcv(n: int = 5, add_nan_row: bool = False) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = np.linspace(3.1, 3.5, n)
    df = pd.DataFrame(
        {
            "Open": close * 0.99,
            "High": close * 1.01,
            "Low": close * 0.98,
            "Close": close,
            "Volume": [1_000_000] * n,
        },
        index=idx,
    )
    if add_nan_row:
        nan_row = pd.DataFrame(
            {
                "Open": [float("nan")],
                "High": [float("nan")],
                "Low": [float("nan")],
                "Close": [float("nan")],
                "Volume": [0],
            },
            index=[idx[-1] + pd.Timedelta(days=1)],
        )
        df = pd.concat([df, nan_row])
    return df


# ---------------------------------------------------------------------------
# /api/price_history
# ---------------------------------------------------------------------------


class TestPriceHistoryNaN:

    @pytest.mark.unit
    @patch("src.analytics.trading_indicators.fetch_ohlcv")
    def test_valid_json_no_nan_literal(self, mock_fetch, client):
        """Response body must not contain the literal string NaN."""
        mock_fetch.return_value = _make_ohlcv(add_nan_row=True)
        resp = client.get("/api/price_history?ticker=D05.SI&period=1mo")
        body = resp.data.decode()
        assert "NaN" not in body, f"NaN literal found in response: {body[:200]}"

    @pytest.mark.unit
    @patch("src.analytics.trading_indicators.fetch_ohlcv")
    def test_response_parses_as_json(self, mock_fetch, client):
        """Response must be parseable JSON even when NaN row present."""
        mock_fetch.return_value = _make_ohlcv(add_nan_row=True)
        resp = client.get("/api/price_history?ticker=D05.SI&period=1mo")
        data = json.loads(resp.data)
        assert "traces" in data or "error" in data

    @pytest.mark.unit
    @patch("src.analytics.trading_indicators.fetch_ohlcv")
    def test_nan_row_excluded_from_dates(self, mock_fetch, client):
        """The date corresponding to the NaN row must not appear in the response."""
        df = _make_ohlcv(n=5, add_nan_row=True)
        nan_date = df.index[-1].strftime("%Y-%m-%d")
        mock_fetch.return_value = df
        resp = client.get("/api/price_history?ticker=D05.SI&period=1mo")
        body = resp.data.decode()
        assert nan_date not in body

    @pytest.mark.unit
    @patch("src.analytics.trading_indicators.fetch_ohlcv")
    def test_all_nan_returns_200_with_error(self, mock_fetch, client):
        """All-NaN DataFrame must return 200 with an error key (not crash)."""
        df = _make_ohlcv(n=3, add_nan_row=True)
        df["Close"] = float("nan")
        df["Open"] = float("nan")
        df["High"] = float("nan")
        df["Low"] = float("nan")
        mock_fetch.return_value = df
        resp = client.get("/api/price_history?ticker=D05.SI&period=1mo")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "error" in data

    @pytest.mark.unit
    @patch("src.analytics.trading_indicators.fetch_ohlcv")
    def test_clean_df_unaffected(self, mock_fetch, client):
        """Clean DataFrame (no NaNs) must still return valid response."""
        mock_fetch.return_value = _make_ohlcv(n=30, add_nan_row=False)
        resp = client.get("/api/price_history?ticker=AAPL&period=3mo")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "NaN" not in resp.data.decode()
        assert "traces" in data
