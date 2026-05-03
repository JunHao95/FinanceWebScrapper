# Phase 26: ML Finance Notebook Integration - Research

**Researched:** 2026-05-03
**Domain:** Supervised/unsupervised ML for finance (sklearn + Keras/TF), Flask API, Plotly, IIFE JavaScript tab pattern
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**UI placement**
- All five ML features live in a new "ML Signals" top-level tab — the 5th tab alongside Stocks / Analytics / Stochastic Models / Trading Indicators
- Tab wiring follows the same pattern established in Phases 18–22 (tradingIndicators.js lazy-load, tabs.js validTabs extension, clearSession on re-scrape)

**ML training timing**
- All models train on-demand per scrape — each time a ticker is analysed, fetch historical data and train the ML model live
- No pre-trained static models; no per-ticker TTL cache
- Acceptable latency cost (~2–5s per feature) consistent with the existing scrape-then-display pattern

**ML Direction Signal**
- Model: Binary classifier — Random Forest (handles non-linear momentum patterns, outputs `predict_proba`); Logistic Regression as fallback if RF is too slow
- Prediction target: 25-day forward return direction (sign of 25-day annualised momentum) — directly from M1 notebook
- Feature set: annualised momentum signals (Ret10_i, Ret25_i, Ret60_i, Ret120_i, Ret240_i from M1) + technical indicators (SMA_ratio, RSI_ratio, RC from M5)
- Chronological split: `shuffle=False` always — critical anti-leakage rule from M1 notebook
- Output: Direction badge (Bullish/Bearish), Confidence % (`predict_proba`), Feature importance bar chart (top 5, Plotly horizontal bar, dark Catppuccin theme)

**PCA Portfolio Decomposition**
- Only appears in multi-ticker (portfolio) mode — requires 2+ tickers; single-ticker hides with "Add more tickers to enable PCA"
- Input: daily return matrix across all analysed tickers, StandardScaler-normalised, no shuffling
- Components: PC1 (market factor), PC2 (sector tilt), PC3 (curvature) — top 3 only
- Visuals: scree plot + factor loadings heatmap (two Plotly charts)
- Interpretation labels: "Market Factor", "Sector Tilt" below charts

**K-Means Market Regime**
- Fixed k=4 regimes: Bull / Bear / Volatile / Ranging
- Labels assigned post-hoc by cluster centroid characteristics (mean return + mean volatility)
- Feature windows: rolling 20-day mean return + rolling 20-day annualised volatility per ticker
- Side-by-side with HMM: "Statistical Regime (HMM)" vs "ML Regime (K-Means)"; agree=green, disagree=amber "Models diverge"
- HMM remains source of truth; K-Means is ML complement; do NOT modify regime_detection.py

**Ensemble Credit Risk Score**
- Model: RF or GradientBoostingClassifier on financial ratios from existing `financial_analytics.py` output
- Training labels: synthetic distress labels from extreme ratio values (bottom-decile earnings + high leverage)
- Output: P(distress) 0–100% gauge + top 3 contributing factors (signed SHAP-style contributions)
- Caveat displayed: "Model trained on ratio thresholds — indicative only. Not a credit rating."
- Distinct from rule-based Financial Health Score A–F (Phase 13) which stays in Analytics tab

**LSTM Direction Signal (M6 — environment-gated)**
- Model: Single-layer LSTM (64 units) + Dense(1, sigmoid) — from M6 curriculum
- Sequence length: 20 trading days of daily returns as input window
- Prediction target: same as RF — 25-day forward return direction (binary)
- Environment gate: `is_cloud_environment()` (checks RENDER/RENDER_SERVICE_ID env vars)
  - Cloud: backend returns `{"lstm_available": false}` without importing keras
  - Local: train and return `{"lstm_available": true, "signal": ..., "confidence": ..., "loss_curve": [...]}`
- Import pattern: `try: from tensorflow import keras; KERAS_AVAILABLE = True\nexcept ImportError: KERAS_AVAILABLE = False` at top of `ml_signals.py`
- Render placeholder: grey card "Deep learning disabled on cloud — run locally to enable."
- Local output: Bullish/Bearish badge + confidence % + training loss curve (Plotly line) + side-by-side RF vs LSTM comparison
- Anti-leakage: chronological split, scale on train only

### Claude's Discretion
- Exact RF hyperparameters (n_estimators, max_depth) — keep fast: n_estimators <= 100
- Exact LSTM epochs and batch_size — keep fast locally: epochs <= 20, batch_size = 32
- Whether to use one combined `/api/ml_signals` route or separate routes per feature
- Exact Plotly colorscale stops for feature importance and factor loadings heatmaps
- How to handle tickers with insufficient history (<252 trading days) — grey placeholder with "Insufficient data" message
- Loading spinner placement and style during on-demand training
- Exact SHAP-style contribution calculation (signed importances vs permutation)

### Deferred Ideas (OUT OF SCOPE)
- Interactive hyperparameter sliders (adjust RF n_estimators, K-Means k)
- Cross-sectional ML (train across multiple tickers simultaneously)
- SMOTE / class imbalance handling for credit risk
- Bayesian hyperparameter optimisation (M7 Bayesian Opt)
</user_constraints>

---

## Summary

Phase 26 adds a new "ML Signals" fifth tab to the Stock Analysis view. It implements five ML models drawn directly from the WorldQuant University ML-in-Finance curriculum: an RF-based direction signal (M1), PCA portfolio decomposition (M2), K-Means market regime (M4), ensemble credit risk score (M3/M6), and an environment-gated LSTM direction signal (M6). All five features live in a new `src/analytics/ml_signals.py` module, are exposed via one or more new Flask routes, and are rendered by a new `static/js/mlSignals.js` IIFE that mirrors the `tradingIndicators.js` session-cache + lazy-load pattern.

The phase is entirely additive — no existing tabs, routes, or analytics modules are modified except for the three touch-points required by every new tab: `tabs.js` (add `'mlsignals'` to `validTabs`), `templates/index.html` (new tab button + content div + script tag), and `stockScraper.js` (call `MLSignals.clearSession()` in `displayResults()`). The existing `RegimeDetector` in `regime_detection.py` is called read-only for the HMM vs K-Means comparison.

**Primary recommendation:** Implement all sklearn models in `ml_signals.py` following the `rl_models.py` pattern (pure-Python dicts, numpy converted to lists). Gate Keras/TF with a module-level try/except that mirrors the `get_enhanced_sentiment_scraper()` lazy-load pattern. Route all features through `/api/ml_signals` with a `feature` query parameter, or one route per feature — either is workable but a single route with a `feature` param is simpler to test.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scikit-learn | 1.8.0 (already installed in venv) | RF, GradientBoost, KMeans, PCA, StandardScaler | Already in requirements.txt, confirmed importable |
| tensorflow | 2.21.0 (installed in venv) | Keras LSTM | Confirmed in venv; absent on Render (512MB ceiling) |
| keras | 3.9.x (ships with TF 2.21) | High-level LSTM layer API | Import via `from tensorflow import keras` |
| numpy | 2.4.4 (installed) | Feature construction, rolling windows | Already project-standard |
| pandas | 3.0.2 (installed) | Return series, rolling calculations | Already project-standard |
| yfinance | 0.2.58 (installed) | Historical OHLCV fetch | Canonical via `fetch_ohlcv()` already exists |
| plotly | 6.1.2 (installed) | Chart payloads as traces+layout JSON | Already project-standard |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scipy | 1.17.1 (installed) | Not directly needed for Phase 26 | Leave for future use |
| sklearn.preprocessing.StandardScaler | (in sklearn 1.8.0) | Normalise features before PCA/KMeans | Always scale on train set only |
| sklearn.model_selection (no TimeSeriesSplit needed — chronological split manual) | — | Manual split with `shuffle=False` is the M1 pattern | Use iloc-based split |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| RandomForestClassifier | XGBoost | XGBoost not in requirements; RF is already in sklearn and handles the problem equally well |
| Keras LSTM via TF | PyTorch LSTM | Torch is already installed (transformers dep), but CONTEXT.md explicitly specifies Keras; stick to decision |
| Single `/api/ml_signals?feature=X` route | Five separate routes | Separate routes are more RESTful but add boilerplate; single route with `feature` param mirrors trading_indicators consolidation; recommend single route |

**Installation:** All required packages are already installed in the venv. No new pip installs needed for sklearn features. TensorFlow/Keras is also already present locally. If tensorflow is not in requirements.txt for Render deployment, it must NOT be added (Render's 512MB ceiling forbids it; the env gate handles this).

---

## Architecture Patterns

### Recommended Project Structure

```
src/analytics/
├── ml_signals.py          # NEW: all 5 ML feature functions
├── financial_analytics.py # UNCHANGED (reuse ratios output)
├── regime_detection.py    # UNCHANGED (read-only HMM call)
└── trading_indicators.py  # UNCHANGED (reuse fetch_ohlcv)

static/js/
├── mlSignals.js           # NEW: IIFE — session cache, tab, Plotly render
└── tradingIndicators.js   # UNCHANGED (reference pattern only)

templates/
└── index.html             # MODIFIED: 5th tab button + content div + script tag

tests/
├── test_unit_ml_signals.py    # NEW: unit tests for ml_signals.py functions
└── test_integration_routes.py # MODIFIED: add /api/ml_signals route tests
```

### Pattern 1: ml_signals.py Module Structure

**What:** A single module exposing one function per ML feature. Each function accepts a ticker string, fetches data internally (using `fetch_ohlcv`), trains a model, and returns a pure-Python dict with `signal`, `confidence`, and Plotly `traces`/`layout` keys — exactly matching the `rl_models.py` return contract.

**When to use:** Every ML feature function follows this signature.

```python
# Source: matches rl_models.py pattern (src/analytics/rl_models.py:24-42)
try:
    from tensorflow import keras
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False

def compute_ml_direction_signal(ticker: str) -> dict:
    """Returns signal, confidence, feature_importance traces/layout."""
    from src.analytics.trading_indicators import fetch_ohlcv
    df = fetch_ohlcv(ticker, days=500)  # 500 days to cover Ret240 window + target
    # ... feature engineering, chronological split, RF fit ...
    return {
        "signal": "Bullish",       # or "Bearish"
        "confidence": 0.67,
        "traces": [...],           # Plotly horizontal bar trace dicts
        "layout": {...},           # Plotly layout dict — dark Catppuccin theme
    }
```

### Pattern 2: Flask Route — Single Route with `feature` Parameter

**What:** One GET route `/api/ml_signals` dispatching to per-feature functions based on `?feature=direction|pca|regime|credit|lstm`.

**When to use:** All ML Signals features. Mirrors `get_trading_indicators()` consolidation pattern.

```python
# Source: mirrors webapp.py:2423-2451 get_trading_indicators pattern
@app.route("/api/ml_signals", methods=["GET"])
def get_ml_signals():
    ticker = request.args.get("ticker", "").strip().upper()
    feature = request.args.get("feature", "").strip().lower()
    tickers = request.args.getlist("tickers")  # for PCA multi-ticker
    if not ticker and not tickers:
        return jsonify({"error": "ticker parameter required"})
    try:
        from src.analytics.ml_signals import (
            compute_ml_direction_signal,
            compute_pca_decomposition,
            compute_kmeans_regime,
            compute_credit_risk_score,
            compute_lstm_direction_signal,
        )
        if feature == "direction":
            result = compute_ml_direction_signal(ticker)
        elif feature == "pca":
            result = compute_pca_decomposition(tickers)
        elif feature == "regime":
            result = compute_kmeans_regime(ticker)
        elif feature == "credit":
            result = compute_credit_risk_score(ticker)
        elif feature == "lstm":
            if is_cloud_environment() or not KERAS_AVAILABLE:
                return jsonify({"lstm_available": False})
            result = compute_lstm_direction_signal(ticker)
        else:
            return jsonify({"error": f"Unknown feature: {feature}"})
        return jsonify({"ticker": ticker, "feature": feature, **result})
    except Exception as e:
        logger.error(f"Error in get_ml_signals [{feature}] for {ticker}: {e}")
        return jsonify({"error": str(e)}), 500
```

Note: `KERAS_AVAILABLE` must be imported from `ml_signals` at import time in webapp.py, or re-checked inside the route. The safest pattern is a lazy check inside the route body using the same try/except.

### Pattern 3: mlSignals.js IIFE

**What:** IIFE exposing `window.MLSignals = { fetchForTicker, clearSession }`. Session-cached per `ticker`. Tab activation calls `fetchForTicker` for each ticker in `pageContext.tickers` after each feature's API call resolves.

**When to use:** All JS rendering for ML Signals tab.

```javascript
// Source: mirrors static/js/tradingIndicators.js:1-54
(function () {
    'use strict';
    var _sessionCache = {};

    function clearSession() {
        Object.keys(_sessionCache).forEach(function(k) { delete _sessionCache[k]; });
    }

    function fetchForTicker(ticker) {
        if (_sessionCache[ticker]) return;
        _sessionCache[ticker] = true;
        // Fire all feature fetches in parallel
        Promise.all([
            fetch('/api/ml_signals?ticker=' + encodeURIComponent(ticker) + '&feature=direction').then(r => r.json()),
            fetch('/api/ml_signals?ticker=' + encodeURIComponent(ticker) + '&feature=regime').then(r => r.json()),
            fetch('/api/ml_signals?ticker=' + encodeURIComponent(ticker) + '&feature=credit').then(r => r.json()),
            fetch('/api/ml_signals?ticker=' + encodeURIComponent(ticker) + '&feature=lstm').then(r => r.json()),
        ]).then(function(results) {
            _renderTickerCard(ticker, results[0], results[1], results[2], results[3]);
        });
        // PCA fires separately with all tickers param
    }

    window.MLSignals = { fetchForTicker, clearSession };
})();
```

### Pattern 4: tabs.js Extension for 5th Tab

**What:** Add `'mlsignals'` to `validTabs` array and add an `else if (tabName === 'mlsignals')` block that lazy-loads `MLSignals.fetchForTicker` for each ticker.

**When to use:** Required as first step of HTML/JS wiring.

```javascript
// Source: mirrors tabs.js:16 + tabs.js:56-72 tradingindicators block
const validTabs = ['stocks', 'analytics', 'autoanalysis', 'tradingindicators', 'mlsignals'];
// ...
} else if (tabName === 'mlsignals') {
    const mlTab = document.getElementById('mlSignalsTab');
    const mlContent = document.getElementById('mlSignalsTabContent');
    if (mlTab && mlContent) {
        mlTab.classList.add('active');
        mlContent.classList.add('active');
        if (typeof MLSignals !== 'undefined' && window.pageContext && window.pageContext.tickers) {
            window.pageContext.tickers.forEach(function(ticker) {
                MLSignals.fetchForTicker(ticker);
            });
            // PCA fires once for all tickers
            if (window.pageContext.tickers.length >= 2) {
                MLSignals.fetchPCA(window.pageContext.tickers);
            }
        }
    }
}
```

### Pattern 5: M1 Feature Engineering — Momentum Signals

**What:** Annualised compounded return over windows [10, 25, 60, 120, 240] days.

```python
# Source: M1 notebook curriculum, confirmed from CONTEXT.md specifics
def _compute_momentum_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ret{n}_i = 100 * ((prod(1 + r)) ** (1/n) - 1) for n in [10,25,60,120,240]"""
    closes = df['Close']
    daily_ret = closes.pct_change()
    result = pd.DataFrame(index=df.index)
    for window in [10, 25, 60, 120, 240]:
        col = f'Ret{window}'
        result[col] = daily_ret.rolling(window).apply(
            lambda r: 100 * ((1 + r).prod() ** (1 / window) - 1),
            raw=False
        )
    return result
```

### Pattern 6: M5 Technical Indicators for Direction Signal

**What:** SMA_ratio, RSI_ratio, RC features.

```python
# Source: M5 curriculum, from CONTEXT.md specifics section
def compute_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    closes = df['Close']
    sma_5  = closes.rolling(5).mean()
    sma_15 = closes.rolling(15).mean()
    rsi_5  = _rsi(closes, 5)
    rsi_15 = _rsi(closes, 15)
    feats = pd.DataFrame(index=df.index)
    feats['SMA_ratio'] = sma_15 / sma_5
    feats['RSI_ratio'] = rsi_5 / rsi_15
    feats['RC']        = closes.pct_change(15)
    return feats

def _rsi(series: pd.Series, window: int) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(window).mean()
    loss  = (-delta.clip(upper=0)).rolling(window).mean()
    rs    = gain / loss.replace(0, float('nan'))
    return 100 - (100 / (1 + rs))
```

### Pattern 7: Chronological Train/Test Split (Anti-Leakage)

**What:** All ML training uses chronological split with `shuffle=False`. No TimeSeriesSplit — direct iloc split on sorted index.

```python
# Source: M1 notebook anti-leakage rule, from CONTEXT.md decisions
split_idx = int(len(X) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
# Scale on train only:
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)
X_latest   = scaler.transform(X.iloc[[-1]])  # most recent observation
```

### Pattern 8: Plotly Dark Catppuccin Theme

**What:** All chart payloads use the project's standard dark theme.

```python
# Source: project convention documented in CONTEXT.md code_context
DARK_LAYOUT = {
    "paper_bgcolor": "#1e1e2e",
    "plot_bgcolor":  "#1e1e2e",
    "font":          {"color": "#cdd6f4"},
}
# Render config passed from JS:
# Plotly.newPlot(div, traces, layout, {staticPlot: true, responsive: true})
```

### Pattern 9: K-Means Label Assignment

**What:** Post-hoc label assignment based on cluster centroid characteristics.

```python
# Source: CONTEXT.md decisions section — K-Means Market Regime
def _label_clusters(kmeans, feature_cols):
    """Assign Bull/Bear/Volatile/Ranging based on centroids."""
    centroids = pd.DataFrame(kmeans.cluster_centers_, columns=feature_cols)
    # centroids has columns: mean_return, ann_vol
    labels = {}
    for k, row in centroids.iterrows():
        if row['mean_return'] > 0 and row['ann_vol'] < centroids['ann_vol'].median():
            labels[k] = 'Bull'
        elif row['mean_return'] < 0:
            labels[k] = 'Bear'
        elif row['ann_vol'] > centroids['ann_vol'].quantile(0.75):
            labels[k] = 'Volatile'
        else:
            labels[k] = 'Ranging'
    return labels
```

### Pattern 10: LSTM Model Architecture

**What:** Single-layer LSTM from M6 curriculum. Input shape `(batch, 20, 1)`.

```python
# Source: M6 curriculum + CONTEXT.md decisions
from tensorflow import keras
model = keras.Sequential([
    keras.layers.Input(shape=(20, 1)),
    keras.layers.LSTM(64),
    keras.layers.Dense(1, activation='sigmoid'),
])
model.compile(optimizer='adam', loss='binary_crossentropy')
history = model.fit(
    X_train_lstm, y_train,
    epochs=20,         # keep fast: <=20 per CONTEXT.md
    batch_size=32,
    validation_split=0.1,
    verbose=0,
)
```

### Anti-Patterns to Avoid

- **Using `shuffle=True` in train/test split:** Creates look-ahead bias. ALL splits must be chronological (iloc-based).
- **Scaling on the full dataset before splitting:** Must `fit_transform` on train set only, then `transform` test/latest.
- **Importing keras at module top-level:** Will crash on Render if TF not installed. Always use `try/except ImportError`.
- **Calling `is_cloud_environment()` after importing keras:** The import itself will OOM on Render. The env gate must be checked before any `from tensorflow import keras` executes.
- **Modifying `regime_detection.py`:** The K-Means regime is a complement; HMM is source of truth. Call `RegimeDetector` from ml_signals.py, do not alter it.
- **Rendering PCA for single-ticker input:** PCA requires 2+ tickers. Render a placeholder card instead of calling the API.
- **Hardcoding financial ratio column names:** The financial_analytics.py output shape must be inspected — use `.get()` with fallbacks for graceful degradation when ratios are absent.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Feature scaling | Manual z-score | `sklearn.preprocessing.StandardScaler` | Handles edge cases (zero-variance columns), easily inverted, consistent API |
| PCA computation | Manual eigendecomposition | `sklearn.decomposition.PCA` | Handles numerical stability, `explained_variance_ratio_` already computed |
| RF feature importance | Manual permutation | `rf.feature_importances_` | Already computed after `.fit()`; permutation importance is slower and not needed for display |
| K-Means convergence | Manual Lloyd's algorithm | `sklearn.cluster.KMeans` | Handles random restarts (`n_init`), convergence criteria, empty cluster edge cases |
| RSI calculation | Manual Wilder's MA | Rolling mean approximation via `_rsi()` helper (acceptable for M5 parity) | Full Wilder MA is more accurate but not required for curriculum alignment |
| LSTM training loop | Manual backprop | `model.fit()` from Keras | 3 lines vs. 50; handles batching, gradient clipping, validation splitting |

**Key insight:** sklearn's ML primitives handle the numerical edge cases (degenerate covariance, empty clusters, zero-variance features) that would require hundreds of lines of defensive custom code. The curriculum implementation is intentionally sklearn-based; replicate it faithfully.

---

## Common Pitfalls

### Pitfall 1: Insufficient History for RF Direction Signal

**What goes wrong:** The RF feature construction requires Ret240 (240-day momentum window) plus a 25-day forward return target label. That means the minimum useful history is ~265 trading days. A ticker with under 252 rows in the OHLCV history will produce NaN-only feature rows.

**Why it happens:** `fetch_ohlcv(ticker, days=500)` fetches calendar days with a 1.4x buffer, but a newly listed ticker (IPO < 2 years) will return fewer than 265 trading rows.

**How to avoid:** Check `len(df_clean)` after dropping NaN rows from feature matrix. If < 50 clean rows remain, return the "Insufficient data" placeholder dict instead of calling `.fit()`.

**Warning signs:** `ValueError: Found array with 0 sample(s)` from sklearn during `fit()`.

### Pitfall 2: PCA Called with Single Ticker

**What goes wrong:** The frontend sends a single ticker when user navigates to ML Signals tab without multi-ticker input. `PCA.fit()` on a single-column return matrix produces trivially explained variance with no useful loadings.

**Why it happens:** Tab activation fires `MLSignals.fetchPCA()` before checking `tickers.length >= 2`.

**How to avoid:** Both the backend and the frontend must guard: backend returns `{"pca_available": false, "reason": "single_ticker"}` when `len(tickers) < 2`; frontend shows "Add more tickers to enable PCA" card and does not call the API at all.

### Pitfall 3: Keras Import OOMs on Render Before `is_cloud_environment()` Check

**What goes wrong:** If `from tensorflow import keras` executes at module import time, Render's 512MB memory limit is hit when `ml_signals.py` is first imported by the route handler — even if the LSTM route is never invoked.

**Why it happens:** Python imports are eager by default.

**How to avoid:** Place the try/except at module level but as a conditional flag — `KERAS_AVAILABLE` — and only do the actual Keras model build inside the route function body, guarded by `if is_cloud_environment() or not KERAS_AVAILABLE: return early`. The module-level import sets `KERAS_AVAILABLE = False` cleanly on Render without importing TF.

### Pitfall 4: K-Means Non-Determinism

**What goes wrong:** K-Means with random initialisation produces different cluster labels on each run, so the regime assignment changes every scrape even for the same ticker/date.

**Why it happens:** K-Means random centroid initialisation.

**How to avoid:** Always pass `random_state=42` to `KMeans(n_clusters=4, n_init=10, random_state=42)`. This makes results reproducible across runs.

### Pitfall 5: Credit Risk Synthetic Labels — All Same Class

**What goes wrong:** If the ratio thresholds used to construct synthetic distress labels result in zero distress examples (or 100% distress), the RF cannot learn and `predict_proba` returns a degenerate distribution.

**Why it happens:** For high-quality tickers, all financial ratios are above the distress thresholds, so no row gets label=1.

**How to avoid:** After constructing synthetic labels, check `y.sum()` and `(1 - y).sum()`. If either is 0, return a neutral/grey placeholder card. Document this as expected behaviour for fundamentally strong or fundamentally broken companies.

### Pitfall 6: Plotly JSON Serialisation of numpy Types

**What goes wrong:** Flask's `jsonify()` cannot serialise `numpy.float64`, `numpy.int64`, or `numpy.ndarray` directly. Returns `TypeError: Object of type float64 is not JSON serializable`.

**Why it happens:** sklearn and numpy return numpy scalar types, not Python built-ins.

**How to avoid:** Apply the project's existing `convert_numpy_types()` helper (defined in `webapp.py:174+`) on all result dicts before returning from the route. Alternatively, call `.tolist()` on arrays inside `ml_signals.py` functions — the `rl_models.py` pattern already does this (see `rl_models.py` docstring: "numpy converted to lists").

### Pitfall 7: HMM vs K-Means Regime Comparison — RegimeDetector Not Fitted

**What goes wrong:** `RegimeDetector().fit(returns)` is called inside `ml_signals.py` to get the HMM result for side-by-side display. If `regime_detection.py` raises during `.fit()` (insufficient data, optimisation failure), the entire K-Means regime route crashes.

**Why it happens:** The HMM optimisation can fail to converge for short return series.

**How to avoid:** Wrap the `RegimeDetector` call in a `try/except` inside `compute_kmeans_regime()`. If HMM fails, set `hmm_regime = None` and display a grey "HMM unavailable" badge rather than crashing. K-Means result is still displayed.

---

## Code Examples

Verified patterns from official sources and existing codebase:

### RandomForestClassifier with `predict_proba`

```python
# Source: sklearn 1.8.0 documentation — confirmed importable in venv
from sklearn.ensemble import RandomForestClassifier
rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42, n_jobs=-1)
rf.fit(X_train_sc, y_train)
proba = rf.predict_proba(X_latest)[0]   # shape (2,)
positive_class_idx = list(rf.classes_).index(1)
confidence = float(proba[positive_class_idx])
signal = "Bullish" if confidence >= 0.5 else "Bearish"
importances = dict(zip(feature_names, rf.feature_importances_.tolist()))
```

### PCA Variance Explained Scree Plot Traces

```python
# Source: sklearn 1.8.0 PCA + plotly 6.1.2 patterns
from sklearn.decomposition import PCA
pca = PCA(n_components=3)
pca.fit(X_train_sc)
evr = pca.explained_variance_ratio_.tolist()
# Scree bar trace
bar_trace = {
    "type": "bar",
    "x": ["PC1", "PC2", "PC3"],
    "y": [round(v * 100, 1) for v in evr],
    "marker": {"color": "#cba6f7"},
    "name": "Variance Explained %",
}
```

### KMeans with Fixed Random State

```python
# Source: sklearn 1.8.0 KMeans — confirmed importable in venv
from sklearn.cluster import KMeans
km = KMeans(n_clusters=4, n_init=10, random_state=42)
km.fit(X_regime_features)
labels = km.labels_          # array of 0–3 per time step
current_regime_cluster = int(labels[-1])
```

### LSTM Sequence Construction

```python
# Source: M6 curriculum pattern + keras 3.14 API (confirmed in venv)
import numpy as np
def make_sequences(arr: np.ndarray, seq_len: int = 20):
    X, y = [], []
    for i in range(seq_len, len(arr)):
        X.append(arr[i - seq_len:i])
        y.append(arr[i])
    return np.array(X)[..., np.newaxis], np.array(y)  # X shape: (N, 20, 1)
```

### Environment-Gated Keras Import (ml_signals.py top of file)

```python
# Source: mirrors webapp.py:48-51 lazy-import pattern
try:
    from tensorflow import keras
    KERAS_AVAILABLE = True
except ImportError:
    keras = None
    KERAS_AVAILABLE = False
```

### Fetch Route Lazy Import Pattern (webapp.py)

```python
# Source: webapp.py:2430-2437 get_trading_indicators pattern
@app.route("/api/ml_signals", methods=["GET"])
def get_ml_signals():
    from src.analytics.ml_signals import (
        compute_ml_direction_signal,
        ...
        KERAS_AVAILABLE,
    )
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Global keras/TF import | Lazy try/except + env gate | Phase 26 decision | Prevents OOM on Render |
| yf.download() for history | yf.Ticker().history() | Phase 09-01 decision | Prevents concurrent-call shape corruption |
| Four tabs in Stock Analysis view | Five tabs (ML Signals added) | Phase 26 | validTabs grows from 4 to 5 items |
| rl_models.py as only ML module in src/analytics | ml_signals.py added alongside | Phase 26 | New convention: each ML curriculum module gets its own file |

**Deprecated/outdated:**
- `yf.download()` for OHLCV: Replaced by `fetch_ohlcv()` using `yf.Ticker().history()` — do not use download() in ml_signals.py.

---

## Open Questions

1. **Single `/api/ml_signals?feature=X` vs five separate routes**
   - What we know: The CONTEXT.md lists this as "Claude's Discretion". Trading indicators uses a single route. rl_models.py has no route at all (it's used server-side via JS in stochasticModels.js).
   - Recommendation: Use a single route with `feature` query parameter — simplest test surface, follows the trading_indicators precedent.

2. **Financial analytics ratio availability for Credit Risk model**
   - What we know: `financial_analytics.py` computes ratios from scraped data, but the exact keys returned depend on which scrapers succeeded. Current ratio, D/E, ROE, operating margin, revenue growth are documented in CONTEXT.md as available.
   - What's unclear: The exact dict keys in the financial_analytics output that Phase 26 can consume — these need to be inspected at plan time by reading `financial_analytics.py` more deeply.
   - Recommendation: In Wave 0 / Plan 01, read `financial_analytics.py` to confirm ratio field names before writing Credit Risk model feature construction code.

3. **How PCA multi-ticker data reaches the backend**
   - What we know: PCA requires a matrix of return series across multiple tickers. The frontend has `window.pageContext.tickers`.
   - What's unclear: Whether to pass multiple tickers as `?tickers=AAPL&tickers=MSFT` (GET) or POST JSON body.
   - Recommendation: Use GET with `request.args.getlist('tickers')` — consistent with all existing routes being GET.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | No pytest.ini found in project root — markers defined in `tests/conftest.py:26-29` |
| Quick run command | `pytest tests/test_unit_ml_signals.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements to Test Map

No formal REQ-IDs were assigned to Phase 26. Mapping by feature:

| Feature | Behavior | Test Type | Automated Command | File Exists? |
|---------|----------|-----------|-------------------|-------------|
| ML Direction Signal | RF trains on momentum+technical features, returns signal+confidence | unit | `pytest tests/test_unit_ml_signals.py::test_direction_signal_returns_bullish_or_bearish -x` | Wave 0 |
| ML Direction Signal | Insufficient history returns placeholder dict | unit | `pytest tests/test_unit_ml_signals.py::test_direction_signal_insufficient_history -x` | Wave 0 |
| PCA Decomposition | Single-ticker input returns pca_available=False | unit | `pytest tests/test_unit_ml_signals.py::test_pca_single_ticker_returns_unavailable -x` | Wave 0 |
| PCA Decomposition | Multi-ticker returns 3 PCs and scree+heatmap traces | unit | `pytest tests/test_unit_ml_signals.py::test_pca_multi_ticker_returns_three_pcs -x` | Wave 0 |
| K-Means Regime | Returns one of Bull/Bear/Volatile/Ranging label | unit | `pytest tests/test_unit_ml_signals.py::test_kmeans_regime_label_valid -x` | Wave 0 |
| Credit Risk Score | Returns float in [0,1] for p_distress | unit | `pytest tests/test_unit_ml_signals.py::test_credit_risk_score_range -x` | Wave 0 |
| Credit Risk Score | Degenerate labels (all same class) returns placeholder | unit | `pytest tests/test_unit_ml_signals.py::test_credit_risk_degenerate_labels -x` | Wave 0 |
| LSTM | KERAS_AVAILABLE=False path returns lstm_available=False dict | unit | `pytest tests/test_unit_ml_signals.py::test_lstm_unavailable_when_keras_missing -x` | Wave 0 |
| /api/ml_signals route | 200 with valid shape for feature=direction | integration | `pytest tests/test_integration_routes.py::test_ml_signals_direction_route -x` | Wave 0 |
| /api/ml_signals route | Missing ticker param returns error JSON | integration | `pytest tests/test_integration_routes.py::test_ml_signals_missing_ticker -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_unit_ml_signals.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_unit_ml_signals.py` — covers all unit tests above (does not yet exist)
- [ ] `tests/test_integration_routes.py` — extend existing file with ml_signals route tests (file exists, add tests)
- [ ] No framework install needed — pytest 8.3.4 already installed

---

## Sources

### Primary (HIGH confidence)

- Direct codebase inspection: `src/analytics/rl_models.py` — return dict pattern (numpy to list)
- Direct codebase inspection: `src/analytics/trading_indicators.py` — `fetch_ohlcv()` canonical function
- Direct codebase inspection: `webapp.py:2423-2451` — `get_trading_indicators()` route structure
- Direct codebase inspection: `static/js/tradingIndicators.js:1-54` — IIFE session-cache pattern
- Direct codebase inspection: `static/js/tabs.js:16-76` — `validTabs` and tab switch dispatch
- Direct codebase inspection: `static/js/stockScraper.js:182-186` — `clearSession()` call pattern
- Direct venv verification: sklearn 1.8.0, tensorflow 2.21.0, keras 3.14.0 confirmed importable
- Direct codebase inspection: `requirements.txt` — confirmed scikit-learn==1.8.0, plotly==6.1.2
- 26-CONTEXT.md — all locked decisions, feature specs, code patterns verified against codebase

### Secondary (MEDIUM confidence)

- sklearn 1.8.0 API: `RandomForestClassifier.predict_proba`, `feature_importances_`, `KMeans`, `PCA.explained_variance_ratio_` — standard APIs stable across 1.x series
- Keras/TF 2.21 LSTM: `keras.layers.LSTM`, `keras.Sequential`, `model.fit()` — stable Keras 3.x API

### Tertiary (LOW confidence)

- None — all critical claims verified against installed packages or direct code inspection

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries confirmed installed and importable in venv
- Architecture: HIGH — all patterns verified against existing codebase files
- Pitfalls: HIGH — derived from existing codebase decisions (Phase 09-01 yfinance decision, webapp.py lazy-import pattern, rl_models.py numpy conversion)
- Validation: HIGH — existing conftest.py and test structure inspected directly

**Research date:** 2026-05-03
**Valid until:** 2026-06-03 (sklearn/keras APIs stable; yfinance may change data schema)
