# Phase 26: ML Finance Notebook Integration - Context

**Gathered:** 2026-05-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Extract key ML concepts from the WorldQuant University "Machine Learning in Finance" notebook (Modules 1–7) and implement five new analytical features in a dedicated "ML Signals" tab. The notebook lives at:
`/Users/junhaotee/Library/Mobile Documents/com~apple~CloudDocs/Desktop/mfe/6 Machine Learning in Finance/ML_Finance_Consolidated_All_Modules.ipynb`

The five features:
1. **ML Direction Signal** — supervised binary classifier predicting 25-day forward return direction per ticker (sklearn RF)
2. **PCA Portfolio Decomposition** — factor analysis on multi-ticker return covariance matrix (sklearn)
3. **K-Means Market Regime** — unsupervised clustering to label current market regime (sklearn)
4. **Ensemble Credit Risk Score** — RF/GradBoost model outputting P(financial distress) with feature contributions (sklearn)
5. **LSTM Direction Signal** — M6 deep learning model (Keras/TensorFlow) predicting 25-day return direction; **environment-gated**: enabled locally, disabled on Render (512MB ceiling)

**Explicitly out of scope:**
- Modifying existing Analytics tab content (Financial Health Score, DCF, Peers, Earnings Quality remain untouched)
- New trading signals that aren't derived from ML model outputs
- Interactive parameter sliders for model hyperparameters

</domain>

<decisions>
## Implementation Decisions

### UI placement
- All five ML features live in a new **"ML Signals"** top-level tab — the 5th tab alongside Stocks / Analytics / Stochastic Models / Trading Indicators
- Tab wiring follows the same pattern established in Phases 18–22 (tradingIndicators.js lazy-load, tabs.js validTabs extension, clearSession on re-scrape)

### ML training timing
- All models train **on-demand per scrape** — each time a ticker is analysed, fetch historical data and train the ML model live
- No pre-trained static models; no per-ticker TTL cache
- Acceptable latency cost (~2–5s per feature) consistent with the existing scrape-then-display pattern

### ML Direction Signal
- **Model**: Binary classifier — Random Forest preferred (handles non-linear momentum patterns, outputs `predict_proba`); Logistic Regression as fallback if RF is too slow
- **Prediction target**: 25-day forward return direction (sign of 25-day annualised momentum) — directly from M1 notebook
- **Feature set**: annualised momentum signals (Ret10_i, Ret25_i, Ret60_i, Ret120_i, Ret240_i from M1) + technical indicators (SMA_ratio, RSI_ratio, RC from M5 `compute_technical_indicators`)
- **Chronological split**: `shuffle=False` always — critical anti-leakage rule from M1 notebook
- **Output displayed per ticker**:
  - Direction badge: Bullish (green) / Bearish (red) matching existing badge colour convention
  - Confidence %: `model.predict_proba(X_latest)[positive_class]` formatted as "67% Bullish"
  - Feature importance bar chart: top 5 features by RF `feature_importances_`, Plotly horizontal bar, dark Catppuccin theme

### PCA Portfolio Decomposition
- **Only appears in multi-ticker (portfolio) mode** — requires 2+ tickers; single-ticker view hides this section with a note "Add more tickers to enable PCA"
- **Input**: daily return matrix across all analysed tickers, StandardScaler-normalised, no shuffling
- **Components shown**: PC1 (market factor), PC2 (sector tilt), PC3 (curvature) — top 3 only
- **Visuals** (two Plotly charts):
  1. Scree plot: bar chart of variance explained % per PC, with cumulative line — directly from M2 curriculum
  2. Factor loadings heatmap: tickers (rows) × PCs (columns), diverging colour scale — shows which tickers co-move (high PC1 loading) and which diversify
- **Interpretation aid**: label PC1 as "Market Factor", PC2 as "Sector Tilt" below the charts

### K-Means Market Regime
- **Fixed k=4 regimes**: Bull / Bear / Volatile / Ranging
- **Labels assigned post-hoc** by cluster centroid characteristics (mean return + mean volatility of each cluster):
  - High return, low vol → Bull
  - Negative return, moderate vol → Bear
  - Any return, high vol → Volatile
  - Near-zero return, low vol → Ranging
- **Feature windows**: rolling 20-day mean return + rolling 20-day annualised volatility per ticker
- **Current regime**: label the most recent window's cluster assignment as the "current" regime
- **Side-by-side with HMM**: ML Signals tab shows BOTH:
  - "Statistical Regime (HMM)": result from existing `RegimeDetector` in `src/analytics/regime_detection.py`
  - "ML Regime (K-Means)": result from new K-Means model
  - When they agree → reinforce in green; when they disagree → amber note "Models diverge"
  - HMM is the existing source of truth; K-Means is the ML complement

### Ensemble Credit Risk Score
- **Model**: Random Forest Classifier (or GradientBoostingClassifier) trained on financial ratios available from the existing `financial_analytics.py` output (current ratio, D/E ratio, ROE, operating margin, revenue growth, etc.)
- **Training labels**: synthetic distress labels derived from extreme ratio values (bottom-decile earnings + high leverage = distress proxy) — no external credit dataset required
- **Output**:
  - P(distress) displayed as a 0–100% probability gauge
  - Top 3 contributing factors shown as signed feature contributions (SHAP-style, computed via RF feature importances × feature values relative to training mean)
  - Framing: "ML Credit Risk Score" — explicitly distinct from the rule-based "Financial Health Score" A–F grade (Phase 13) which remains in the Analytics tab unchanged
- **Caveat displayed**: "Model trained on ratio thresholds — indicative only. Not a credit rating."

### LSTM Direction Signal (M6 — environment-gated)
- **Model**: Single-layer LSTM (64 units) + Dense(1, activation='sigmoid') — from M6 curriculum
- **Sequence length**: 20 trading days of daily returns as input window
- **Prediction target**: same as RF Direction Signal — 25-day forward return direction (binary)
- **Environment gate**: `is_cloud_environment()` (checks `RENDER`/`RENDER_SERVICE_ID` env vars) — same pattern as `get_enhanced_sentiment_scraper()` for torch/transformers in `webapp.py:60-67`
  - If cloud: backend returns `{"lstm_available": false}` immediately without importing keras
  - If local: train and return `{"lstm_available": true, "signal": ..., "confidence": ..., "loss_curve": [...]}`
- **Import pattern**: `try: from tensorflow import keras; KERAS_AVAILABLE = True\nexcept ImportError: KERAS_AVAILABLE = False` at top of `ml_signals.py`
- **Render placeholder**: Grey card with text "Deep learning disabled on cloud — run locally to enable." Consistent with insufficient-data placeholder style
- **Local output displayed**:
  - Same Bullish/Bearish badge + confidence % as RF Direction Signal
  - Training loss curve: Plotly line chart (train loss vs. epoch) — shows M6 convergence behaviour
  - Side-by-side comparison row: RF signal vs. LSTM signal — when they agree, reinforce in green; when diverge, amber note
- **Anti-leakage**: chronological split (`shuffle=False`), scale on train only — same rules as all other ML features

### Claude's Discretion
- Exact RF hyperparameters (n_estimators, max_depth) — keep fast: n_estimators ≤ 100
- Exact LSTM epochs and batch_size — keep fast locally: epochs ≤ 20, batch_size = 32
- Whether to use one combined `/api/ml_signals` route or separate routes per feature
- Exact Plotly colorscale stops for feature importance and factor loadings heatmaps
- How to handle tickers with insufficient history (<252 trading days) — grey placeholder with "Insufficient data" message
- Loading spinner placement and style during on-demand training
- Exact SHAP-style contribution calculation (signed importances vs permutation)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/analytics/financial_analytics.py:16-18`: already imports `StandardScaler`, `PCA`, `LinearRegression` from sklearn — extend with RF, KMeans, GradBoost imports in the same file or new `src/analytics/ml_signals.py`
- `src/analytics/regime_detection.py`: existing `RegimeDetector` class — K-Means regime will call this in parallel and compare outputs; do NOT modify regime_detection.py
- `fetch_ohlcv(ticker, days, auto_adjust=True)` in `trading_indicators.py:16` — reuse for ML Direction Signal historical data fetch
- `compute_technical_indicators()` defined in M5 notebook — implement in `ml_signals.py` (not yet in codebase)
- `src/analytics/rl_models.py`: existing ML module structure to follow (pure Python dicts returned, numpy converted to lists)
- `static/js/tradingIndicators.js`: session-cache + lazy-load + clearSession pattern — mirror for `static/js/mlSignals.js`
- Plotly dark theme: `paper_bgcolor='#1e1e2e'`, `plot_bgcolor='#1e1e2e'`, `font color='#cdd6f4'`, `staticPlot: true, responsive: true`
- Badge colour convention: `#2ecc71` bullish/positive, `#e74c3c` bearish/warning, `#7f849c` neutral/muted

### Established Patterns
- Chronological split (`shuffle=False`) — enforced from M1 notebook; must be in all ML training code
- Return `{traces, layout, signal, confidence, ...}` JSON payload shape from route → JS renderer
- All sklearn data scaled on train only, `scaler.transform()` on test/latest — M1 anti-leakage rule
- Plotly `{ staticPlot: true, responsive: true }` render config for all charts
- Heavy ML gating: `webapp.py:60-67` `get_enhanced_sentiment_scraper()` lazy-loads torch — mirror for Keras: `try/except ImportError` at module level + `is_cloud_environment()` guard in route handler; never import keras on Render path

### Integration Points
- `webapp.py`: new route(s) for ML Signals (follows `/api/trading_indicators` pattern)
- `src/analytics/ml_signals.py`: new file — ML Direction Signal, PCA, K-Means, Credit Risk functions
- `static/js/mlSignals.js`: new IIFE — session cache, tab activation, per-ticker DOM shell, Plotly render
- `templates/index.html`: 5th tab button ("ML Signals"), `mlSignalsTabContent` div, script tag
- `static/js/tabs.js`: add `'mlsignals'` to `validTabs`, `switchTab()` lazy-load case
- `static/js/stockScraper.js`: call `MLSignals.clearSession()` in `displayResults()`
- `tests/`: unit tests for `ml_signals.py` functions, integration tests for new route(s), regression tests pinning key outputs on frozen fixtures

</code_context>

<specifics>
## Specific Ideas

- Source notebook path (for researcher reference): `/Users/junhaotee/Library/Mobile Documents/com~apple~CloudDocs/Desktop/mfe/6 Machine Learning in Finance/ML_Finance_Consolidated_All_Modules.ipynb`
- M1 momentum feature construction: annualised compounded signals `100 * ((prod(1 + r)) ** (1/window) - 1)` for windows [10, 25, 60, 120, 240]
- M5 technical indicators: SMA_ratio = SMA_15 / SMA_5, RSI_ratio = RSI_5 / RSI_15, RC = pct_change(15)
- M2 PCA variance explained labelling: display "PC1 explains 72% of portfolio variance" inline
- K-Means regime timeline: show a colour-coded date strip (last 252 trading days) with regime colour per day — visual analogue to the existing HMM regime chart
- Credit Risk caveat phrasing: "Model trained on ratio thresholds — indicative only. Not a credit rating." Small grey italic text below the gauge.

</specifics>

<deferred>
## Deferred Ideas

- Interactive hyperparameter sliders (adjust RF n_estimators, K-Means k) — UI complexity not warranted for v1
- Cross-sectional ML (train across multiple tickers simultaneously) — current design is per-ticker; cross-sectional training is its own phase
- SMOTE / class imbalance handling for credit risk — synthetic labels make class balance controllable; defer real imbalance handling until real credit data is used
- Bayesian hyperparameter optimisation (M7 Bayesian Opt) — grid/random search sufficient for on-demand latency constraints

</deferred>

---

*Phase: 26-ml-finance-notebook-integration*
*Context gathered: 2026-05-03*
