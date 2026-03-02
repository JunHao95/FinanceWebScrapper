# Technology Stack

**Project:** MFE Showcase Web App — Stochastic Models + ML-in-Finance Additions
**Researched:** 2026-03-03
**Overall confidence:** HIGH (existing codebase is ground truth; recommendations derived from actual imports and requirements.txt)

---

## Context: What the Existing Codebase Already Uses

Before recommending additions, the existing stack is:

| Layer | Technology | Notes |
|-------|------------|-------|
| Backend runtime | Python 3.x (Flask) | Flask >=2.3.0, gunicorn 21.2.0 for hosting |
| Numerical core | numpy >=1.23.0, scipy >=1.9.0 | Used throughout all models |
| Data layer | pandas >=1.5.0, yfinance >=0.2.18 | Market data fetching |
| ML | scikit-learn >=1.1.0 | PCA, LinearRegression, StandardScaler in financial_analytics.py |
| Visualization (server) | matplotlib >=3.5.0, seaborn >=0.12.0 | Currently "future use" |
| Frontend | Vanilla JS (no framework) | Plotly.js loaded via CDN from templates |
| Optimization | scipy.optimize (brute, fmin, minimize) | Used in CIR calibration, Heston calibration, HMM |
| Integration | scipy.integrate.quad | Used in Fourier pricer for characteristic function inversion |

The existing code imports confirm: **numpy + scipy + sklearn + pandas is the complete numerical stack already in place.** No new numerical infrastructure is needed for the stochastic models module.

---

## Recommended Stack: Stochastic Models Module (Current Work)

### Core Numerical Libraries (Already Installed — Confirm Versions)

| Library | Min Version | Current Req | Purpose | Confidence |
|---------|-------------|-------------|---------|------------|
| numpy | 1.26.x | >=1.23.0 | Matrix ops, random sampling, linear algebra for Markov chains, Monte Carlo | HIGH |
| scipy | 1.13.x | >=1.9.0 | Optimization (brute/fmin/minimize), integration (quad), stats (norm) — all used in existing WIP | HIGH |
| pandas | 2.1.x | >=1.5.0 | Time series for regime detection, data handling | HIGH |

**Version note (confidence: MEDIUM — based on PyPI releases up to August 2025):**
- numpy 2.0 released June 2024; 2.1.x is stable as of late 2024. The existing `>=1.23.0` pin is permissive enough to get numpy 2.x. No action needed unless numpy 2.x causes breaking changes in existing code (check via test run).
- scipy 1.13.x released 2024; `>=1.9.0` pin is fine.
- pandas 2.x is the current stable line; `>=1.5.0` is too permissive but works.

**Why not upgrade pins aggressively:** The existing codebase's `>=X` style pins work correctly with Render's build environment. Pin only if a specific feature is needed.

### Stochastic Models: No New Libraries Required

The existing WIP files confirm that all stochastic model implementations are pure numpy/scipy:

| Model | File | Libraries Used |
|-------|------|---------------|
| CIR interest rate model | `src/analytics/interest_rate_models.py` | numpy, scipy.optimize (brute, fmin) |
| Credit transitions (Markov chain) | `src/analytics/credit_transitions.py` | numpy only |
| Regime detection (HMM) | `src/analytics/regime_detection.py` | numpy, pandas, scipy.optimize.minimize, scipy.stats.norm, yfinance |
| Fourier option pricer (Heston/Merton/BCC) | `src/derivatives/fourier_pricer.py` | numpy, scipy.integrate.quad |
| Model calibration | `src/derivatives/model_calibration.py` | numpy, scipy.optimize (brute, fmin) |

**Decision: Do NOT add QuantLib, hmmlearn, or pymdptoolbox.** The implementations are hand-rolled to match the MFE course content. Third-party stochastic model libraries would replace the coursework code rather than showcase it, defeating the app's purpose.

### What "hmmlearn" Provides vs. What You Have

| Capability | hmmlearn | Your regime_detection.py |
|------------|----------|--------------------------|
| HMM with Gaussian emissions | Yes | Yes (Hamilton filter, custom MLE via L-BFGS-B) |
| Baum-Welch EM training | Yes | No (MLE via scipy.optimize) |
| Interpretability for showcase | Low (black box) | High (course-derived formulas visible) |
| Recommendation | Do NOT add | Keep yours |

---

## Recommended Stack: Machine Learning in Finance Module (Next Semester)

This section is forward-looking. Confidence is MEDIUM — based on standard MFE ML-in-finance curricula patterns.

### Core ML Libraries (Partially Installed)

| Library | Version to Target | Purpose | Why | Confidence |
|---------|-------------------|---------|-----|------------|
| scikit-learn | >=1.3.0 | Supervised/unsupervised learning: regression, classification, clustering, PCA | Already installed; covers 80% of ML-in-finance coursework | HIGH |
| pandas | >=2.0.0 | Feature engineering, time series manipulation | Already installed | HIGH |
| numpy | >=1.24.0 | Array operations for custom implementations | Already installed | HIGH |
| statsmodels | >=0.14.0 | OLS regression with diagnostics, ARIMA, time series tests (ADF, Ljung-Box) | NOT currently installed; expected for any finance ML module | MEDIUM |
| xgboost | >=2.0.0 | Gradient boosting for return prediction, credit scoring — common in MFE ML modules | NOT currently installed; add when module starts | MEDIUM |

**Why statsmodels over sklearn for regression in finance:** statsmodels outputs p-values, R-squared, F-statistics, confidence intervals, and residual diagnostics — the output format expected in academic/MFE work. sklearn LinearRegression does not. For the ML module, keep sklearn for ML tasks and add statsmodels for econometric regression.

**Why NOT add PyTorch/TensorFlow now:** The existing requirements.txt already has `torch>=1.12.0` for the sentiment analysis transformer. Deep learning for the ML-in-finance module (e.g., LSTM for price prediction) would reuse this existing torch dependency. No new install needed — just use it when the module begins.

### Feature Engineering for Finance (No New Libraries)

| Task | Tool | Rationale |
|------|------|-----------|
| Rolling statistics (volatility, momentum) | pandas (.rolling()) | Already available |
| Technical indicators | pandas (manual) | No ta-lib; avoids C dependency hell on Render |
| Lag features / return series | pandas (.shift()) | Already available |
| Train/test split with time-awareness | sklearn.model_selection.TimeSeriesSplit | Already available in sklearn |

**Do NOT add ta-lib.** It has a C binary dependency that frequently breaks on Render and other hosted environments. Implement indicators manually in pandas (straightforward for SMA, EMA, RSI, Bollinger Bands).

---

## Frontend Visualization Stack

### For Stochastic Models (Current Work)

| Library | Source | Purpose | Why | Confidence |
|---------|--------|---------|-----|------------|
| Plotly.js | CDN | Interactive charts for yield curves, regime probability time series, credit transition heatmaps | Already used in existing tabs (optionsPricing.js, volatilitySurface.js); consistent with rest of app | HIGH |
| Vanilla JS | Local | Tab switching, API calls, rendering | Project constraint — no framework changes | HIGH |

**Plotly chart types needed for stochastic models:**

| Feature | Plotly Chart Type | Notes |
|---------|-------------------|-------|
| CIR yield curve | Scatter/Line | x=maturity, y=rate |
| Regime detection probabilities | Scatter/Line with dual y-axis or fill | Smoothed/filtered probabilities over time |
| Credit transition heatmap | Heatmap | n×n transition matrix visualization |
| HMM state sequence | Scatter colored by state | Returns series colored by detected regime |
| Fourier pricer vol surface | Surface3D or Heatmap | Strike × maturity → implied vol |
| Calibration convergence (optional) | Scatter/Line | MSE vs iteration |

**CDN version to use:** Plotly.js 2.x (currently 2.35.x as of mid-2025). Load via:
```html
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
```
Check https://github.com/plotly/plotly.js/releases for latest stable before shipping.

**Do NOT switch to Chart.js or D3.js.** Plotly is already embedded in the app and handles all required chart types (including 3D surfaces and heatmaps) without additional code. Consistency matters for a showcase app.

### For ML-in-Finance Module (Future)

Plotly.js covers everything needed:
- Feature importance bar charts
- Confusion matrices (heatmap)
- Learning curves (line charts)
- Prediction vs. actual scatter plots

No additional visualization libraries needed.

---

## Backend API Layer (No Changes Needed)

| Component | Technology | Status |
|-----------|------------|--------|
| Web framework | Flask >=2.3.0 | Keep as-is |
| CORS | Flask-Cors >=4.0.0 | Keep as-is |
| Production server | gunicorn 21.2.0 | Keep as-is |
| Data serialization | Python json (stdlib) + Flask jsonify | Keep as-is |

**Do NOT add FastAPI or async frameworks.** The app is CPU-bound on model computation (Fourier integration, Monte Carlo), not I/O bound. Flask's synchronous model is fine. Switching frameworks provides no benefit and breaks the existing working system.

**Long-running computation concern:** Some operations (Heston calibration with brute-search, Monte Carlo with 10K+ paths) can take 10-30 seconds. For a showcase app this is acceptable — add a loading state in JS. If this becomes a problem, the right fix is Flask-Executor or a background task queue (not a framework switch).

---

## Alternatives Considered and Rejected

| Category | Recommended | Alternative Considered | Why Not |
|----------|-------------|----------------------|---------|
| HMM implementation | Custom (scipy.optimize) | hmmlearn | Replaces course-derived code; defeats showcase purpose |
| Markov chain | numpy matrix power | quantecon | Overkill; numpy.linalg.matrix_power() is one line |
| MDP solver | Custom / scipy | pymdptoolbox | Library makes MDP a black box; MFE course implements it manually |
| Interest rate models | Custom (numpy/scipy) | QuantLib | QuantLib Python bindings are complex to install on Render; C++ dependency; defeats showcase purpose |
| Gradient boosting | xgboost (when ML module starts) | lightgbm | Both are valid; xgboost is more commonly taught in MFE curricula and has simpler sklearn API compatibility |
| Frontend framework | Vanilla JS | React/Vue | Project constraint; no benefit for a multi-tab showcase app |
| Visualization | Plotly.js (CDN) | D3.js | D3 requires 10x more code for the same charts; Plotly already handles finance-specific chart types |
| Econometric regression | statsmodels (add for ML module) | sklearn LinearRegression | sklearn doesn't produce academic-style regression tables with significance tests |

---

## Installation: What to Add

### For Stochastic Models Module (Current Work)

**No new dependencies required.** All modules use existing numpy/scipy/pandas stack. Verify existing install satisfies actual imports:

```bash
# Verify existing requirements satisfy current WIP imports
pip install -r requirements.txt

# Confirm scipy version supports all used functions
python3 -c "from scipy.optimize import brute, fmin, minimize; from scipy.integrate import quad; from scipy.stats import norm; print('scipy OK')"
```

### For Machine Learning Module (Add When Starting Next Semester)

```bash
# Add to requirements.txt when ML module begins
pip install statsmodels>=0.14.0
pip install xgboost>=2.0.0

# torch is already installed (>=1.12.0 via sentiment module)
# sklearn is already installed
```

Update `requirements.txt` by adding:
```
# ML-in-finance module dependencies
statsmodels>=0.14.0
xgboost>=2.0.0
```

---

## Sources and Confidence

| Area | Confidence | Basis |
|------|------------|-------|
| Existing stack (numpy/scipy/pandas/sklearn) | HIGH | Direct from requirements.txt and source file imports |
| Fourier/calibration/HMM using scipy.optimize | HIGH | Direct from source files in repo |
| No new libraries for stochastic models | HIGH | All WIP files confirmed to import only existing deps |
| statsmodels for ML module | MEDIUM | Standard in MFE ML curricula; not yet confirmed by course materials |
| xgboost for ML module | MEDIUM | Common in MFE programs; specific course may differ |
| numpy 2.x compatibility | MEDIUM | numpy 2.0 released June 2024; existing code may need minor updates |
| Plotly CDN version | MEDIUM | Version 2.35.x known good as of mid-2025; verify before release |
| QuantLib rejection | HIGH | C++ build dependency documented issue with Render/Heroku environments |
| ta-lib rejection | HIGH | Known C binary dependency that breaks on Render |

**Sources:**
- Existing codebase: `requirements.txt`, `src/analytics/interest_rate_models.py`, `src/analytics/regime_detection.py`, `src/analytics/credit_transitions.py`, `src/derivatives/fourier_pricer.py`, `src/derivatives/model_calibration.py`
- numpy 2.0 migration guide: https://numpy.org/doc/stable/release/2.0.0-notes.html
- Plotly.js releases: https://github.com/plotly/plotly.js/releases
- scipy documentation: https://docs.scipy.org/doc/scipy/
