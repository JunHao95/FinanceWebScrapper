"""
ML Signals Module — Phase 26

Five ML analytics functions for the ML Signals tab:
  1. compute_ml_direction_signal   — RF binary classifier (M1 + M5)
  2. compute_pca_decomposition     — PCA on multi-ticker return matrix (M2)
  3. compute_kmeans_regime         — K-Means market regime labelling (M4)
  4. compute_credit_risk_score     — Ensemble RF credit distress scorer (M3)
  5. compute_lstm_direction_signal — LSTM direction signal, env-gated (M6)

All functions return plain-Python dicts (numpy types converted to builtins).
Chronological split (shuffle=False) enforced in all supervised training paths.
"""

import logging
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

try:
    from tensorflow import keras

    KERAS_AVAILABLE = True
except ImportError:
    keras = None
    KERAS_AVAILABLE = False

from src.analytics.trading_indicators import fetch_ohlcv

logger = logging.getLogger(__name__)

DARK_LAYOUT: dict = {
    "paper_bgcolor": "#1e1e2e",
    "plot_bgcolor": "#1e1e2e",
    "font": {"color": "#cdd6f4"},
}

_RATIO_KEYS = [
    "current_ratio",
    "debt_to_equity",
    "return_on_equity",
    "operating_margin",
    "revenue_growth",
    "earnings_growth",
]

_INSUF_DIRECTION: dict = {
    "insufficient_data": True,
    "signal": None,
    "confidence": None,
    "traces": [],
    "layout": DARK_LAYOUT,
}

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _rsi(series: pd.Series, window: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _compute_momentum_features(df: pd.DataFrame) -> pd.DataFrame:
    """Annualised compounded momentum signals for windows [10, 25, 60, 120, 240]."""
    close = df["Close"]
    feats: Dict[str, pd.Series] = {}
    for w in [10, 25, 60, 120, 240]:
        r_w = close.pct_change(w).clip(lower=-0.9999)
        feats[f"Ret{w}"] = 100 * ((1 + r_w) ** (252 / w) - 1)
    return pd.DataFrame(feats, index=df.index)


def _compute_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """SMA_ratio, RSI_ratio, RC — M5 technical indicator set."""
    close = df["Close"]
    sma5 = close.rolling(5).mean()
    sma15 = close.rolling(15).mean()
    rsi5 = _rsi(close, 5)
    rsi15 = _rsi(close, 15)
    return pd.DataFrame(
        {
            "SMA_ratio": sma5 / sma15.replace(0, np.nan),
            "RSI_ratio": rsi5 / rsi15.replace(0, np.nan),
            "RC": close.pct_change(15),
        },
        index=df.index,
    )


def _label_clusters(kmeans: KMeans) -> Dict[int, str]:
    """Assign Bull/Bear/Volatile/Ranging to cluster indices by centroid characteristics."""
    centroids = kmeans.cluster_centers_  # shape (4, 2): [mean_return, ann_vol]
    indices = list(range(len(centroids)))
    by_vol = sorted(indices, key=lambda i: centroids[i][1], reverse=True)
    volatile_idx = by_vol[0]
    remaining = by_vol[1:]
    by_ret = sorted(remaining, key=lambda i: centroids[i][0], reverse=True)
    bull_idx = by_ret[0]
    bear_idx = by_ret[-1]
    ranging_idx = by_ret[1] if len(by_ret) > 2 else bear_idx
    return {
        volatile_idx: "Volatile",
        bull_idx: "Bull",
        bear_idx: "Bear",
        ranging_idx: "Ranging",
    }


def _make_sequences(arr: np.ndarray, seq_len: int = 20):
    """Return (X, y) arrays for LSTM. y=1 if 25-day forward cumulative return > 0."""
    X, y = [], []
    for i in range(seq_len, len(arr) - 25):
        X.append(arr[i - seq_len : i])
        y.append(1 if arr[i : i + 25].sum() > 0 else 0)
    return (
        np.array(X, dtype=np.float32).reshape(-1, seq_len, 1),
        np.array(y, dtype=np.float32),
    )


# ---------------------------------------------------------------------------
# 1. ML Direction Signal (RF, M1 + M5)
# ---------------------------------------------------------------------------


def compute_ml_direction_signal(ticker: str) -> dict:
    try:
        df = fetch_ohlcv(ticker, days=500)
    except Exception as exc:
        logger.warning("fetch_ohlcv failed for %s: %s", ticker, exc)
        return _INSUF_DIRECTION

    if len(df) < 265:
        return _INSUF_DIRECTION

    mom = _compute_momentum_features(df)
    tech = _compute_technical_indicators(df)
    forward_ret = df["Close"].pct_change(25).shift(-25)
    target = (forward_ret > 0).astype(int)

    feature_df = pd.concat([mom, tech], axis=1)
    feature_df["target"] = target
    feature_df = feature_df.dropna()

    if len(feature_df) < 50:
        return _INSUF_DIRECTION

    feat_cols = [c for c in feature_df.columns if c != "target"]
    X = feature_df[feat_cols]
    y = feature_df["target"]

    split_idx = int(len(X) * 0.8)
    X_train = X.iloc[:split_idx]
    y_train = y.iloc[:split_idx]

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_latest_sc = scaler.transform(X.iloc[[-1]])

    rf = RandomForestClassifier(
        n_estimators=50, max_depth=5, random_state=42, n_jobs=-1
    )
    rf.fit(X_train_sc, y_train.values)

    proba = rf.predict_proba(X_latest_sc)[0]
    classes = list(rf.classes_)
    pos_idx = classes.index(1) if 1 in classes else 0
    confidence = float(proba[pos_idx])
    signal = "Bullish" if confidence >= 0.5 else "Bearish"

    importances = rf.feature_importances_
    top_idx = np.argsort(importances)[::-1][:5]
    top_features = [feat_cols[i] for i in top_idx]
    top_vals = [float(importances[i]) for i in top_idx]

    traces = [
        {
            "type": "bar",
            "orientation": "h",
            "x": top_vals[::-1],
            "y": top_features[::-1],
            "marker": {"color": "#89b4fa"},
        }
    ]
    layout = {
        **DARK_LAYOUT,
        "title": {
            "text": f"Feature Importance — {ticker}",
            "font": {"color": "#cdd6f4"},
        },
        "xaxis": {"title": "Importance"},
    }
    return {
        "signal": signal,
        "confidence": confidence,
        "traces": traces,
        "layout": layout,
    }


# ---------------------------------------------------------------------------
# 2. PCA Portfolio Decomposition (M2)
# ---------------------------------------------------------------------------


def compute_pca_decomposition(tickers: List[str]) -> dict:
    if len(tickers) < 2:
        return {"pca_available": False, "reason": "single_ticker"}

    returns_map: Dict[str, pd.Series] = {}
    for t in tickers:
        try:
            df = fetch_ohlcv(t, days=365)
            returns_map[t] = df["Close"].pct_change().dropna()
        except Exception as exc:
            logger.warning("PCA: could not fetch %s: %s", t, exc)

    if len(returns_map) < 2:
        return {"pca_available": False, "reason": "insufficient_data"}

    ret_df = pd.DataFrame(returns_map).dropna()
    if len(ret_df) < 30:
        return {"pca_available": False, "reason": "insufficient_data"}

    n_components = min(3, len(tickers), ret_df.shape[1])
    scaler = StandardScaler()
    X_sc = scaler.fit_transform(ret_df)

    pca = PCA(n_components=n_components)
    pca.fit(X_sc)

    evr = [float(v) for v in pca.explained_variance_ratio_]
    while len(evr) < 3:
        evr.append(0.0)

    pc_label_names = ["Market Factor", "Sector Tilt", "Curvature"]
    x_labels = pc_label_names[:n_components] + pc_label_names[n_components:3]

    scree_traces = [
        {
            "type": "bar",
            "x": x_labels,
            "y": evr,
            "name": "Variance Explained",
            "marker": {"color": "#89dceb"},
        }
    ]

    loadings = pca.components_.T  # (n_features, n_components)
    while loadings.shape[1] < 3:
        loadings = np.hstack([loadings, np.zeros((loadings.shape[0], 1))])

    heatmap_traces = [
        {
            "type": "heatmap",
            "z": loadings.tolist(),
            "x": pc_label_names,
            "y": list(ret_df.columns),
            "colorscale": "RdBu",
            "zmid": 0,
        }
    ]

    return {
        "pca_available": True,
        "variance_explained": evr,
        "scree_traces": scree_traces,
        "heatmap_traces": heatmap_traces,
        "layout": DARK_LAYOUT,
    }


# ---------------------------------------------------------------------------
# 3. K-Means Market Regime (M4)
# ---------------------------------------------------------------------------

_REGIME_COLOURS = {
    "Bull": "#2ecc71",
    "Bear": "#e74c3c",
    "Volatile": "#f39c12",
    "Ranging": "#7f849c",
}
_KM_TO_BINARY = {"Bull": "Bull", "Bear": "Bear", "Volatile": "Bear", "Ranging": "Bull"}


def compute_kmeans_regime(ticker: str) -> dict:
    _empty = {
        "current_regime": None,
        "hmm_regime": None,
        "models_agree": None,
        "regime_timeline_traces": [],
        "layout": DARK_LAYOUT,
    }
    try:
        df = fetch_ohlcv(ticker, days=365)
    except Exception as exc:
        logger.warning("K-Means: fetch failed for %s: %s", ticker, exc)
        return _empty

    returns = df["Close"].pct_change().dropna()
    rolling_mean = returns.rolling(20).mean()
    rolling_vol = returns.rolling(20).std() * np.sqrt(252)

    regime_df = pd.DataFrame(
        {"mean_return": rolling_mean, "ann_vol": rolling_vol}
    ).dropna()

    if len(regime_df) < 40:
        return {**_empty, "current_regime": "Ranging"}

    X_regime = regime_df.values
    kmeans = KMeans(n_clusters=4, n_init=10, random_state=42)
    labels = kmeans.fit_predict(X_regime)

    label_map = _label_clusters(kmeans)
    named_labels = [label_map[int(lb)] for lb in labels]
    current_regime = named_labels[-1]

    hmm_regime = None
    try:
        from src.analytics.regime_detection import RegimeDetector

        hmm_result = RegimeDetector().fit(returns.values)
        hmm_raw = hmm_result.get("current_regime")
        hmm_regime = {"calm": "Bull", "stressed": "Bear"}.get(hmm_raw, hmm_raw)
    except Exception as exc:
        logger.debug("HMM unavailable: %s", exc)

    models_agree = (
        (_KM_TO_BINARY.get(current_regime) == hmm_regime)
        if hmm_regime is not None
        else None
    )

    dates = [str(d) for d in regime_df.index.tolist()]
    regime_timeline_traces = [
        {
            "type": "scatter",
            "mode": "markers",
            "x": dates,
            "y": named_labels,
            "marker": {
                "color": [_REGIME_COLOURS.get(r, "#cdd6f4") for r in named_labels],
                "size": 6,
            },
            "name": "Regime",
        }
    ]

    return {
        "current_regime": current_regime,
        "hmm_regime": hmm_regime,
        "models_agree": models_agree,
        "regime_timeline_traces": regime_timeline_traces,
        "layout": DARK_LAYOUT,
    }


# ---------------------------------------------------------------------------
# 4. Ensemble Credit Risk Score (M3)
# ---------------------------------------------------------------------------


def compute_credit_risk_score(ticker: str, ratios: dict) -> dict:
    _CAVEAT = (
        "Model trained on ratio thresholds — indicative only. Not a credit rating."
    )

    np.random.seed(42)
    n_synth = 200

    de = float(ratios.get("debt_to_equity", 1.0))
    eg = float(ratios.get("earnings_growth", 0.05))
    cr = float(ratios.get("current_ratio", 1.5))
    roe = float(ratios.get("return_on_equity", 0.10))
    om = float(ratios.get("operating_margin", 0.10))
    rg = float(ratios.get("revenue_growth", 0.05))

    # Synthetic peers centred on input ratios; std_de proportional to de so that
    # exceptionally low-leverage companies (de≈0) almost never cross the distress
    # threshold (de>1.5), producing degenerate all-zero labels — by design.
    std_de = max(2.0 * de, 0.2)
    synth_de = np.clip(np.random.normal(de, std_de, n_synth), 0, None)
    synth_eg = np.random.normal(eg, 0.20, n_synth)
    synth_cr = np.clip(np.random.normal(cr, 0.8, n_synth), 0, None)
    synth_roe = np.random.normal(roe, 0.15, n_synth)
    synth_om = np.random.normal(om, 0.15, n_synth)
    synth_rg = np.random.normal(rg, 0.10, n_synth)

    X_synth = np.column_stack(
        [synth_cr, synth_de, synth_roe, synth_om, synth_rg, synth_eg]
    )
    y_synth = ((synth_eg < -0.05) & (synth_de > 1.5)).astype(int)

    if y_synth.sum() == 0 or (len(y_synth) - y_synth.sum()) == 0:
        return {
            "p_distress": None,
            "degenerate_labels": True,
            "insufficient_data": True,
            "top_factors": [],
            "caveat": _CAVEAT,
        }

    rf = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
    rf.fit(X_synth, y_synth)

    ticker_vec = np.array([[cr, de, roe, om, rg, eg]], dtype=float)
    classes = list(rf.classes_)
    pos_idx = classes.index(1) if 1 in classes else 0
    p_distress = float(rf.predict_proba(ticker_vec)[0][pos_idx])

    train_mean = X_synth.mean(axis=0)
    contributions = rf.feature_importances_ * np.abs(ticker_vec[0] - train_mean)
    top_idx = np.argsort(contributions)[::-1][:3]

    top_factors = [
        {
            "name": _RATIO_KEYS[i],
            "value": float(ticker_vec[0][i]),
            "contribution": float(contributions[i]),
        }
        for i in top_idx
    ]

    return {"p_distress": p_distress, "top_factors": top_factors, "caveat": _CAVEAT}


# ---------------------------------------------------------------------------
# 5. LSTM Direction Signal (M6 — environment-gated)
# ---------------------------------------------------------------------------


def compute_lstm_direction_signal(ticker: str) -> dict:
    if not KERAS_AVAILABLE:
        return {"lstm_available": False}

    try:
        df = fetch_ohlcv(ticker, days=500)
    except Exception as exc:
        logger.warning("LSTM: fetch failed for %s: %s", ticker, exc)
        return {"lstm_available": False, "insufficient_data": True}

    returns = df["Close"].pct_change().dropna().values.astype(np.float32)

    if len(returns) < 100:
        return {"lstm_available": False, "insufficient_data": True}

    X, y = _make_sequences(returns, seq_len=20)
    if len(X) < 50:
        return {"lstm_available": False, "insufficient_data": True}

    split_idx = int(len(X) * 0.8)
    X_train = X[:split_idx]
    y_train = y[:split_idx]

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train.reshape(-1, 1)).reshape(X_train.shape)
    X_latest_sc = scaler.transform(X[-1].reshape(-1, 1)).reshape(1, 20, 1)

    model = keras.Sequential(
        [
            keras.layers.Input(shape=(20, 1)),
            keras.layers.LSTM(64),
            keras.layers.Dense(1, activation="sigmoid"),
        ]
    )
    model.compile(optimizer="adam", loss="binary_crossentropy")
    history = model.fit(
        X_train_sc,
        y_train,
        epochs=20,
        batch_size=32,
        validation_split=0.1,
        verbose=0,
    )

    confidence = float(model.predict(X_latest_sc, verbose=0)[0][0])
    signal = "Bullish" if confidence >= 0.5 else "Bearish"

    loss_curve_traces = [
        {
            "type": "scatter",
            "x": list(range(len(history.history["loss"]))),
            "y": [float(v) for v in history.history["loss"]],
            "name": "Train Loss",
            "marker": {"color": "#cba6f7"},
        }
    ]

    return {
        "lstm_available": True,
        "signal": signal,
        "confidence": confidence,
        "loss_curve_traces": loss_curve_traces,
        "layout": DARK_LAYOUT,
    }
