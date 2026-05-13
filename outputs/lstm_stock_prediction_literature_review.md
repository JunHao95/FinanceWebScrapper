# LSTM Models for Stock Return Direction Prediction: Literature Summary

**Context:** ABT (Abbott Laboratories) — LSTM signal reported as 89% Bullish.  
**Date:** 2026-05-11

---

## 1. What LSTM Models Do (and Claim to Do)

LSTM (Long Short-Term Memory) networks are a class of recurrent neural networks designed to capture long-range temporal dependencies. In stock prediction, they are typically fed sequences of historical prices, volumes, and/or technical indicators and trained to predict either next-period price level or return direction (up/down).

Reported directional accuracies in the literature commonly range from **50–60%** on properly validated out-of-sample tests, though many papers claim **>80%** — a red flag that usually correlates with methodological problems described below.

---

## 2. Key Papers

### [P1] Istiake Sunny et al. (2020) — "Deep Learning-Based Stock Price Prediction Using LSTM"
- Demonstrates a standard LSTM pipeline on daily closing prices.
- Reports low MSE on price prediction, but **price-level MSE is misleading** because stock prices are non-stationary and auto-correlated: a model that simply outputs yesterday's price achieves very low MSE.
- Illustrative of the *majority* of LSTM-stock papers that optimise on price level rather than return direction.

### [P2] Patel & Yalamalle (2022) — "Prediction of stock price direction using the LASSO-LSTM model" (*PLOS ONE*, PMC9680880)
- Combines LASSO feature selection with LSTM to predict direction.
- Uses technical and sentiment features.
- Claims accuracy around 58–62% on selected US and Chinese equities with LASSO-selected features.
- **Strength:** Uses directional accuracy, not just MSE. **Weakness:** Feature selection is performed on the full dataset before the train/test split — a common leakage vector (see §3).

### [P3] Minh et al. (2018) — "Deep Learning Approach for Short-Term Stock Trends Prediction" (*IEEE Access*)
- Two-stage model: CNN for feature extraction + LSTM for sequential modelling.
- Evaluates on S&P 500 constituents.
- Reports ~56% daily directional accuracy, which is consistent with efficient-market expectations.
- Notable for using **walk-forward validation** rather than random train/test splits.

### [P4] De Prado (2018) — *Advances in Financial Machine Learning* (Wiley)
- Not an LSTM paper per se, but the standard reference for **backtesting methodology** in financial ML.
- Introduces the concept of **purged cross-validation** and **combinatorial purged CV** to prevent temporal leakage.
- Argues most published financial ML results are inflated by look-ahead bias and overlapping train/test periods.
- Widely cited as the methodological baseline that LSTM papers should (but often don't) follow.

### [P5] Kapoor & Narayanan (2023) — "Leakage and the Reproducibility Crisis in Machine-Learning-Based Science" (*Patterns* 4(9))
- Surveyed 17 scientific fields and found **>290 papers affected by data leakage**.
- Shows that correcting leakage bugs often reduces claimed performance to levels comparable with simpler baselines.
- Categorises leakage into: (1) lack of clean train/test separation, (2) illegitimate features, (3) test set not drawn from the distribution of interest.
- Directly relevant to financial LSTM papers that use random k-fold CV on time-series data or fit scalers/feature-selectors on the full dataset.

### [P6 — Survey] Bustos & Pomares-Quimbaya (2020) — "Deep learning in the stock market — a systematic survey of practice" (*Artificial Intelligence Review*, Springer)
- Systematic review requiring **backtesting** as a primary inclusion criterion.
- Finds that the majority of DL-in-stock-market papers lack proper backtesting, reproducible code, or domain-appropriate evaluation metrics.
- Key finding: papers using only statistical metrics (MSE, RMSE, accuracy) without financial metrics (Sharpe, max drawdown, transaction costs) are **insufficient for practical assessment**.

---

## 3. Known Pitfalls and Leakage Risks

| # | Pitfall | How It Inflates Results |
|---|---------|------------------------|
| **L1** | **Look-ahead / temporal leakage** | Random train/test splits allow future data to leak into training. For time-series, only strict walk-forward or expanding-window splits are valid. |
| **L2** | **Preprocessing leakage** | Fitting scalers (MinMax, StandardScaler), PCA, or feature selectors on the *entire* dataset before splitting. The test set's distribution then informs the training transform. |
| **L3** | **Price-level evaluation** | Reporting MSE/RMSE on raw prices rather than returns. Prices are highly auto-correlated; a naïve "predict yesterday's close" baseline achieves very low MSE, making any model look good. |
| **L4** | **Survivorship bias** | Training and testing only on stocks that still exist (e.g., current S&P 500 constituents), ignoring delisted firms. Biases results upward. |
| **L5** | **Feature snooping** | Selecting technical indicators or hyperparameters after seeing test-period results. Equivalent to p-hacking in statistics. |
| **L6** | **No transaction cost / slippage** | Backtests that ignore bid-ask spread, commissions, and market impact. A 55% directional accuracy signal can be net-negative after costs. |
| **L7** | **Overlapping windows** | Using overlapping input sequences that share data points across train and test, violating independence assumptions. |
| **L8** | **Single-stock evaluation** | Reporting results on one carefully chosen stock rather than a broad universe. Prone to cherry-picking. |

---

## 4. What This Means for the ABT "89% Bullish" Signal

An 89% directional confidence from an LSTM is **extremely high** and warrants strong skepticism. Observations:

1. **Base rate:** Even the best-performing published LSTM models achieve ~55–62% out-of-sample directional accuracy after proper debiasing. 89% is far outside this range.
2. **Likely explanations for an inflated signal:**
   - The model may be predicting price *level* (which trends upward over time → "bullish"), not return *direction*.
   - Preprocessing or feature leakage may be present.
   - The confidence may be a softmax output (model certainty), not empirical accuracy — a model can be 89% "confident" while being right only 52% of the time.
   - The lookback window may include a recent bullish trend, and the LSTM is extrapolating the trend (momentum bias).
3. **Irreducible noise:** Daily stock returns contain large idiosyncratic and macro-driven noise. No single-stock LSTM model should be expected to reliably exceed ~60% directional accuracy on daily horizons.

**Bottom line:** Treat any LSTM signal with claimed directional confidence above ~65% as methodologically suspect unless accompanied by:
- Walk-forward or purged CV validation
- Comparison against a naïve baseline (random walk, buy-and-hold)
- Transaction-cost-adjusted financial metrics (Sharpe, net P&L)
- Out-of-sample period that was never used for tuning

---

## 5. Sources

1. Patel & Yalamalle (2022). "Prediction of stock price direction using the LASSO-LSTM model." *PLOS ONE*. https://pmc.ncbi.nlm.nih.gov/articles/PMC9680880/
2. De Prado, M. L. (2018). *Advances in Financial Machine Learning*. Wiley.
3. Kapoor, S. & Narayanan, A. (2023). "Leakage and the reproducibility crisis in ML-based science." *Patterns* 4(9). https://doi.org/10.1016/j.patter.2023.100804
4. Bustos, O. & Pomares-Quimbaya, A. (2020). "Deep learning in the stock market — a systematic survey of practice." *Artificial Intelligence Review*. https://link.springer.com/article/10.1007/s10462-022-10226-0
5. Apicella et al. (2025). "Don't push the button! Exploring data leakage risks in ML and transfer learning." *Artificial Intelligence Review*. https://link.springer.com/article/10.1007/s10462-025-11326-3
