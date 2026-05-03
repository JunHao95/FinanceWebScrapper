"""
Unit test scaffold for Phase 26 ML signal functions.

All tests skip automatically when src/analytics/ml_signals.py does not yet exist,
so this file is safe to commit before the implementation module is written.
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Conditional import — set IMPORT_OK and KERAS_AVAILABLE_GLOBALLY
# ---------------------------------------------------------------------------

try:
    from src.analytics.ml_signals import (
        compute_ml_direction_signal,
        compute_pca_decomposition,
        compute_kmeans_regime,
        compute_credit_risk_score,
        compute_lstm_direction_signal,
    )

    try:
        from src.analytics.ml_signals import KERAS_AVAILABLE as KERAS_AVAILABLE_GLOBALLY
    except ImportError:
        KERAS_AVAILABLE_GLOBALLY = False
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False
    KERAS_AVAILABLE_GLOBALLY = False


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_ohlcv(n=600):
    """Return a synthetic OHLCV DataFrame with a DatetimeIndex (business days)."""
    np.random.seed(42)
    idx = pd.date_range(end=pd.Timestamp("2024-01-01"), periods=n, freq="B")
    close = 150.0 + np.cumsum(np.random.randn(n) * 0.5)
    return pd.DataFrame(
        {
            "Open": close - np.abs(np.random.randn(n) * 0.3),
            "High": close + np.abs(np.random.randn(n) * 0.5),
            "Low": close - np.abs(np.random.randn(n) * 0.5),
            "Close": close,
            "Volume": np.random.randint(1_000_000, 10_000_000, size=n).astype(float),
        },
        index=idx,
    )


# ---------------------------------------------------------------------------
# Tests — direction signal
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_direction_signal_returns_bullish_or_bearish():
    """Happy path: 600-row OHLCV → valid signal, confidence, traces."""
    if not IMPORT_OK:
        pytest.skip("ml_signals not yet implemented")

    with patch("src.analytics.ml_signals.fetch_ohlcv", return_value=_make_ohlcv()):
        result = compute_ml_direction_signal("AAPL")

    assert result["signal"] in ("Bullish", "Bearish")
    assert 0.0 <= result["confidence"] <= 1.0
    assert "traces" in result


@pytest.mark.unit
def test_direction_signal_insufficient_history():
    """50-row df is too short → insufficient_data flag."""
    if not IMPORT_OK:
        pytest.skip("ml_signals not yet implemented")

    with patch("src.analytics.ml_signals.fetch_ohlcv", return_value=_make_ohlcv(n=50)):
        result = compute_ml_direction_signal("AAPL")

    assert result.get("insufficient_data") is True


# ---------------------------------------------------------------------------
# Tests — PCA decomposition
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_pca_single_ticker_returns_unavailable():
    """Single ticker → PCA requires at least 2 tickers → pca_available=False."""
    if not IMPORT_OK:
        pytest.skip("ml_signals not yet implemented")

    result = compute_pca_decomposition(["AAPL"])

    assert result["pca_available"] is False


@pytest.mark.unit
def test_pca_multi_ticker_returns_three_pcs():
    """Multi-ticker 400-row mock → 3 PCs, scree_traces, heatmap_traces."""
    if not IMPORT_OK:
        pytest.skip("ml_signals not yet implemented")

    with patch("src.analytics.ml_signals.fetch_ohlcv", return_value=_make_ohlcv(n=400)):
        result = compute_pca_decomposition(["AAPL", "MSFT"])

    assert len(result["variance_explained"]) == 3
    assert "scree_traces" in result
    assert "heatmap_traces" in result


# ---------------------------------------------------------------------------
# Tests — K-means regime
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_kmeans_regime_label_valid():
    """K-means regime label must be one of the four canonical labels."""
    if not IMPORT_OK:
        pytest.skip("ml_signals not yet implemented")

    with patch("src.analytics.ml_signals.fetch_ohlcv", return_value=_make_ohlcv()):
        result = compute_kmeans_regime("AAPL")

    assert result["current_regime"] in ("Bull", "Bear", "Volatile", "Ranging")


@pytest.mark.unit
def test_kmeans_regime_hmm_compare_keys_present():
    """Result must include hmm_regime and models_agree comparison keys."""
    if not IMPORT_OK:
        pytest.skip("ml_signals not yet implemented")

    with patch("src.analytics.ml_signals.fetch_ohlcv", return_value=_make_ohlcv()):
        result = compute_kmeans_regime("AAPL")

    assert "hmm_regime" in result
    assert "models_agree" in result


# ---------------------------------------------------------------------------
# Tests — credit risk score
# ---------------------------------------------------------------------------

_GOOD_RATIOS = {
    "current_ratio": 2.1,
    "debt_to_equity": 0.5,
    "return_on_equity": 0.15,
    "operating_margin": 0.20,
    "revenue_growth": 0.08,
    "earnings_growth": 0.10,
}

_EXCEPTIONAL_RATIOS = {
    "current_ratio": 3.0,
    "debt_to_equity": 0.1,
    "return_on_equity": 0.30,
    "operating_margin": 0.35,
    "revenue_growth": 0.20,
    "earnings_growth": 0.25,
}


@pytest.mark.unit
def test_credit_risk_score_range():
    """p_distress must be a probability; top_factors must have ≤ 3 entries."""
    if not IMPORT_OK:
        pytest.skip("ml_signals not yet implemented")

    result = compute_credit_risk_score("AAPL", _GOOD_RATIOS)

    assert 0.0 <= result["p_distress"] <= 1.0
    assert len(result["top_factors"]) <= 3


@pytest.mark.unit
def test_credit_risk_degenerate_labels():
    """Exceptionally strong ratios may produce degenerate labels or insufficient_data."""
    if not IMPORT_OK:
        pytest.skip("ml_signals not yet implemented")

    result = compute_credit_risk_score("AAPL", _EXCEPTIONAL_RATIOS)

    assert (
        result.get("insufficient_data") is True
        or result.get("degenerate_labels") is True
    )


# ---------------------------------------------------------------------------
# Tests — LSTM direction signal
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_lstm_unavailable_when_keras_missing():
    """When KERAS_AVAILABLE is patched to False the function returns unavailable dict."""
    if not IMPORT_OK:
        pytest.skip("ml_signals not yet implemented")

    with patch("src.analytics.ml_signals.KERAS_AVAILABLE", False):
        result = compute_lstm_direction_signal("AAPL")

    assert result == {"lstm_available": False}


@pytest.mark.unit
@pytest.mark.skipif(not KERAS_AVAILABLE_GLOBALLY, reason="keras not available")
def test_lstm_returns_valid_signal_locally():
    """When Keras is available and given 600 rows, LSTM returns a valid signal."""
    if not IMPORT_OK:
        pytest.skip("ml_signals not yet implemented")

    with patch("src.analytics.ml_signals.fetch_ohlcv", return_value=_make_ohlcv()):
        result = compute_lstm_direction_signal("AAPL")

    assert result["lstm_available"] is True
    assert result["signal"] in ("Bullish", "Bearish")
