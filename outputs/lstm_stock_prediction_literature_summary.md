# LSTM Models for Stock Return Direction Prediction: Literature Summary

**Context:** AAPL | LSTM signal reported as 90% Bullish  
**Date:** 2026-05-11

---

## 1. What the Literature Claims

LSTM networks are the most widely studied deep learning architecture for stock price and return direction forecasting. A bibliometric survey (Duarte et al., 2022) catalogued 333 authors publishing on the topic between 2018–2022 alone, concentrated in *Expert Systems with Applications*, *IEEE Access*, and *Neural Computing and Applications*.

The landmark empirical study is **Fischer & Krauss (2018)**, who applied LSTM to directional prediction of S&P 500 constituents (1992–2015). They reported daily returns of 0.46% and a Sharpe ratio of 5.8 *before transaction costs*, outperforming random forests, logistic regression, and standard RNNs. This paper is heavily cited but its extraordinary Sharpe has drawn scrutiny (see §3).

More recent work fuses LSTM with sentiment features. **Hasan et al. (2025)** combine technical indicators with financial sentiment analysis for direction prediction and report improved accuracy on several indices. **Survey papers** (e.g., the 2025 *Archives of Computational Methods in Engineering* review) consolidate results showing reported directional accuracies in the **55–85%** range across various markets, with the best results typically on indices rather than individual stocks, and on Chinese/emerging markets where microstructure differs.

## 2. What Actually Holds Up

An empirical comparison on Kaggle market data (**An Empirical Study Based on Machine Learning and LSTM in Stock Prediction**, 2025, published in *Frontiers in Economics*) tested LSTM against gradient boosting and logistic regression on 45 US stocks and 3 indices with proper walk-forward validation. **Finding: traditional ML methods matched or outperformed LSTM** once the evaluation used realistic out-of-sample splits rather than random train/test splits.

A well-known Kaggle notebook by **Carl McBride Ellis ("LSTM time series + stock price prediction = FAIL")** — with 32,000+ views — demonstrates the core failure mode pedagogically: an LSTM trained on raw price levels produces visually impressive "predictions" that are merely **lagged copies of the input** shifted by one timestep. The model learns to echo yesterday's price, which looks great on a chart but has zero predictive value for direction or magnitude.

## 3. Known Pitfalls & Leakage Risks

### 3.1 Temporal (Look-Ahead) Leakage

**"The Illusion of Alpha" (2025, preprint, doi:10.21203/rs.3.rs-9180656/v1)** provides the most rigorous quantification to date. Using a controlled synthetic panel of 30 stocks over 10 years, the authors show:

| Leakage Channel | Clean Sharpe | Leaked Sharpe |
|---|---|---|
| 16-day forward contamination in rolling normalization | 0.15–0.57 | 1.15–2.84 |
| Random K-fold cross-validation (XGBoost) | 0.17 | 1.75 |
| Leaky retraining schedule | 0.57 | 1.76 |

**Key finding:** A mere 16 trading days of forward contamination in feature normalization inflated Sharpe ratios by 3–7×. After correction, alpha t-statistics disappeared entirely. This applies directly to LSTM pipelines where `StandardScaler` or z-score normalization is fitted on the full dataset before the train/test split.

### 3.2 The "Lagged Copy" Illusion

When trained on raw price levels, LSTMs converge to predicting `price(t) ≈ price(t-1)`. This yields low MSE (prices are autocorrelated in levels) but **zero directional signal**. Most impressive-looking LSTM stock charts in blog posts and tutorials exhibit exactly this artefact. The correct target for direction prediction is **returns** (or sign of returns), not price levels.

### 3.3 Overfitting & Non-Stationarity

**"Long short-term memory networks in learning memory inconsistencies of stock markets" (2025, *Financial Innovation*)** shows that adding more training data can *degrade* LSTM performance because of **concept drift** — the statistical properties of financial returns shift over time (regime changes, volatility clustering, structural breaks). Standard LSTM architectures have no mechanism to forget obsolete regimes, leading to overfitting on stale patterns.

### 3.4 Survivorship & Universe Bias

The "Illusion of Alpha" paper also documents that cross-sectional leakage from survivorship-biased universes and future-rank features inflates results, especially in non-linear models like gradient-boosted trees and, by extension, LSTMs.

### 3.5 Transaction Cost Erasure

Fischer & Krauss (2018) themselves noted their strategy's profitability **declined sharply after 2001** and effectively disappeared after transaction costs in the most recent period tested. Many LSTM papers report gross returns without realistic cost assumptions.

## 4. Practical Implications for a "90% Bullish" LSTM Signal

A reported 90% bullish confidence from an LSTM model should be interpreted with extreme caution:

| Question | Red Flag If… |
|---|---|
| What is the target variable? | Raw price levels, not returns or direction |
| How is train/test split done? | Random shuffle, not strictly temporal |
| Is normalization fitted before the split? | Yes → temporal leakage |
| Is the accuracy on in-sample or out-of-sample data? | In-sample or overlapping windows |
| Are transaction costs included? | Not mentioned |
| What is the baseline? | Not compared to naïve "always up" or random walk |
| What is the calibration? | 90% confidence ≠ 90% accuracy; is the model calibrated? |

**Base rate context:** AAPL has historically been positive on ~54% of trading days. A well-calibrated model outputting 90% should be correct ~90% of the time *at that confidence level*. Most LSTM models in the literature are not calibrated and the raw sigmoid output should not be interpreted as a probability.

## 5. Key Papers Cited

1. **Fischer, T. & Krauss, C. (2018).** "Deep learning with long short-term memory networks for financial market predictions." *European Journal of Operational Research*, 270(2), 654–669.  
   https://ideas.repec.org/a/eee/ejores/v270y2018i2p654-669.html

2. **"The Illusion of Alpha: Quantifying Hidden Data Leakage in Financial Machine Learning" (2025, preprint).**  
   https://doi.org/10.21203/rs.3.rs-9180656/v1

3. **"Long short-term memory networks in learning memory inconsistencies of stock markets" (2025).** *Financial Innovation*, Springer.  
   https://link.springer.com/article/10.1186/s40854-025-00875-9

4. **Duarte, L.C.S. et al. (2022).** "Stock Price Forecasting with Artificial Neural Networks Long Short-Term Memory: A Bibliometric Analysis and Systematic Literature Review." *Open Journal of Business and Management*.  
   https://www.scirp.org/journal/paperinformation?paperid=121940

5. **McBride Ellis, C. (2022).** "LSTM time series + stock price prediction = FAIL." Kaggle Notebook (32k+ views, Gold medal).  
   https://www.kaggle.com/code/carlmcbrideellis/lstm-time-series-stock-price-prediction-fail

---

## Bottom Line

The academic consensus is that LSTMs *can* capture some short-term serial dependencies in returns, but reported accuracies are routinely inflated by data leakage, non-temporal cross-validation, survivorship bias, and the lagged-copy artefact. The most rigorous studies show that after proper decontamination, LSTM-based strategies produce Sharpe ratios close to zero and rarely survive transaction costs. **A 90% bullish confidence score from an LSTM should be treated as an unvalidated signal, not a reliable forecast, unless the full pipeline has been audited for the pitfalls above.**
