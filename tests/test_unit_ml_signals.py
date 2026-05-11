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
    assert "best_params" in result
    assert "n_estimators" in result["best_params"]
    assert "max_depth" in result["best_params"]


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
    assert "portfolio_var" in result
    pv = result["portfolio_var"]
    assert pv["var_99_1d_pct"] >= pv["var_95_1d_pct"] >= 0
    assert len(pv["pc_contributions"]) >= 1


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


# ---------------------------------------------------------------------------
# Tests — _KM_TO_BINARY Ranging fix (bug fix/ranging-regime-binary-map)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_km_to_binary_ranging_maps_to_none():
    """Ranging must not map to Bull — it returns None (inconclusive)."""
    from src.analytics.ml_signals import _KM_TO_BINARY

    assert _KM_TO_BINARY["Ranging"] is None


@pytest.mark.unit
def test_km_to_binary_bull_bear_volatile_unchanged():
    from src.analytics.ml_signals import _KM_TO_BINARY

    assert _KM_TO_BINARY["Bull"] == "Bull"
    assert _KM_TO_BINARY["Bear"] == "Bear"
    assert _KM_TO_BINARY["Volatile"] == "Bear"


@pytest.mark.unit
def test_kmeans_regime_ranging_sets_models_agree_to_none():
    """When K-Means current regime is Ranging, models_agree must be None."""
    if not IMPORT_OK:
        pytest.skip("ml_signals not yet implemented")

    ohlcv = _make_ohlcv()

    with patch("src.analytics.ml_signals.fetch_ohlcv", return_value=ohlcv), patch(
        "src.analytics.ml_signals.KMeans"
    ) as mock_km, patch(
        "src.analytics.regime_detection.RegimeDetector"
    ) as mock_hmm_cls:
        # Force K-Means to label current point as Ranging
        km_instance = mock_km.return_value
        n_rows = len(ohlcv) - 19  # rolling(20) drops first 19
        km_instance.fit_predict.return_value = [0] * n_rows
        km_instance.cluster_centers_ = [
            [0.0005, 0.15],  # 0 = Ranging (moderate vol, moderate ret)
            [0.002, 0.10],  # 1 = Bull
            [-0.002, 0.10],  # 2 = Bear
            [0.000, 0.40],  # 3 = Volatile
        ]
        # Force _label_clusters to assign 0 → Ranging
        with patch(
            "src.analytics.ml_signals._label_clusters",
            return_value={0: "Ranging", 1: "Bull", 2: "Bear", 3: "Volatile"},
        ):
            # HMM returns Bull
            hmm_instance = mock_hmm_cls.return_value
            hmm_instance.fit.return_value = {"current_regime": "calm"}

            result = compute_kmeans_regime("AAPL")

    assert result["current_regime"] == "Ranging"
    assert result["models_agree"] is None
