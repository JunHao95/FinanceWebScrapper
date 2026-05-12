# Random Forest Classifiers for Equity Return Direction Prediction
## Literature Summary — May 2026

---

## 1. Overview

Random Forests (RF), introduced by Breiman (2001), are a bagged ensemble of decorrelated decision trees. Their appeal for equity-direction classification rests on three properties: (i) they handle non-linear feature interactions without explicit specification, (ii) they provide built-in variable importance rankings, and (iii) Out-of-Bag (OOB) error gives a low-cost cross-validation estimate. A growing body of finance/ML literature applies RF to the binary problem *"will next-period return be positive or negative?"* using technical indicators, fundamentals, or macro features as inputs.

---

## 2. Key Papers

### P1 — Khaidem, Saha & Dey (2016)
**"Predicting the direction of stock market prices using random forest"**
arXiv:1605.00003

- **Setup:** RF classifier trained on technical indicators (RSI, Stochastic Oscillator, Williams %R, MACD, Price Rate of Change) for multiple US stocks.
- **Claims:** RF outperforms logistic regression, SVM, and single decision trees on directional accuracy. OOB error converges to low values.
- **Limitations noted by us:** Uses OOB error only—no true walk-forward / expanding-window out-of-sample test. Feature set is entirely technical; no fundamental or macro controls. No transaction-cost analysis.

### P2 — Ballings et al. (2015)
**"Evaluating multiple classifiers for stock price direction prediction"**
*Expert Systems with Applications*, 42(20), 7046–7056.

- **Setup:** Benchmarks RF, AdaBoost, Kernel Factory, Neural Networks, Logistic Regression, SVM, and k-NN on 5,767 European firms over 2002–2012 using 5×2 cross-validation and AUC.
- **Key finding:** RF ranks first among all classifiers on AUC, ahead of boosting and neural nets.
- **Limitations noted by us:** Cross-validation is randomised, not time-respecting—this is a serious information-leakage risk for time-series data (see §3). AUC advantage is statistically significant but economically modest once realistic costs are considered.

### P3 — Lohrmann & Luukka (2019)
**"Classification of intraday S&P500 returns with a Random Forest"**
*International Journal of Forecasting*, 35(1), 390–407.

- **Setup:** Intraday S&P 500 direction prediction using lagged returns, implied volatility (VIX), volume, and calendar features. Walk-forward evaluation.
- **Key finding:** RF achieves ~56–58% hit rate on intraday direction; performance is sensitive to feature selection and market regime. Feature importance is dominated by lagged returns and VIX rather than higher-order technical indicators.
- **Strength:** Uses proper temporal train/test splits, avoiding look-ahead bias.

### P4 — Deep et al. (2024)
**"Assessing the Impact of Technical Indicators on Machine Learning Models for Stock Price Prediction"**
arXiv:2412.15448

- **Setup:** 13 RF regression configurations on minute-level SPY data with Bollinger Bands, EMA, Fibonacci, RSI, etc.
- **Key finding:** In-sample R² of 0.75–0.81 collapses to **negative** out-of-sample R². Models underperform buy-and-hold by 2–4%. Primary price features account for >60% of importance; technical indicators only 14–15%.
- **Implication:** A stark demonstration that in-sample fit is almost meaningless for financial time-series RF models. Technical indicators add risk-management value (improved Rachev ratios) but not return-prediction value.

### P5 — Arnott, Harvey & Markowitz (2019) / related: Sorokina, Booth & Thornton (2021)
**"Data Snooping Bias in Tests of the Relative Performance of Multiple Forecasting Models"**
*Journal of Banking & Finance*, 2021.

- Not RF-specific, but directly applicable. Demonstrates that evaluating many model specifications on the same financial dataset without multiple-testing corrections (e.g., White's Reality Check, Hansen's SPA, Romano-Wolf) leads to severe data-snooping bias. The probability of finding at least one "significant" model rises rapidly with the number of specifications tried.

---

## 3. Known Limitations of RF for Equity Direction

| Limitation | Detail |
|---|---|
| **No temporal modelling** | RF treats each sample as i.i.d. It cannot model autocorrelation, momentum decay, or regime shifts inherent in financial returns. |
| **Randomised CV leaks information** | Standard k-fold CV shuffles time order, allowing future data to inform training. Only expanding-window or walk-forward splits are valid for time-series. Ballings et al. (P2) uses randomised splits—a common but problematic choice. |
| **Overfitting to noise** | Financial returns have very low signal-to-noise ratios (daily equity R² ≈ 0.01–0.05 for known factors). RF can easily memorise noise, especially with deep trees and many features—Deep et al. (P4) show R² collapsing OOS. |
| **Feature importance ≠ causation** | RF variable importance is a measure of predictive contribution within the fitted model, not causal effect. Correlated features dilute importance scores (the "feature masking" problem). |
| **Transaction costs ignored** | Most studies report hit rates or AUC without deducting bid-ask spreads, commissions, or market impact. A 55% hit rate on daily direction may be economically worthless net of costs. |
| **Non-stationarity** | The data-generating process in financial markets changes over time (regulation, market structure, participant composition). A model trained on 2010–2015 data may have no predictive power in 2020–2025. |

---

## 4. Data-Snooping Risks — Specific to This Literature

1. **Specification search:** Researchers try many indicator sets, tree depths, number-of-trees values, and report only the best. Without a pre-registered hypothesis or multiple-testing adjustment, the reported accuracy is biased upward.
2. **Publication bias:** Papers showing RF "works" are published; null results are filed away. The published literature therefore overstates RF's predictive power.
3. **Shared test sets:** Many papers test on the same indices (S&P 500, DJIA) over overlapping periods. Collective data-snooping across the literature inflates apparent predictability of these specific series.
4. **Target leakage through features:** Some technical indicators (e.g., using close price in both the feature and the label) introduce subtle look-ahead contamination.
5. **Survivorship bias:** Studies that use only currently-listed stocks miss delisted firms, biasing the sample toward winners.

---

## 5. Practical Takeaways

- RF can achieve modest directional accuracy (~53–58%) on equity returns, but this is **fragile** and highly sensitive to evaluation methodology.
- Any study using randomised cross-validation on financial time-series should be treated with extreme scepticism.
- The strongest evidence for RF value is in **feature screening** (identifying which variables matter) rather than in end-to-end trading signal generation.
- Walk-forward evaluation, transaction-cost accounting, and multiple-testing corrections are necessary conditions for credible results—most published RF-equity papers fail at least one of these.
- Deep et al. (2024) provide the clearest recent evidence that in-sample RF performance is an unreliable guide to real-world profitability.

---

## Sources

1. Khaidem, Saha & Dey (2016). *Predicting the direction of stock market prices using random forest.* arXiv:1605.00003. https://arxiv.org/abs/1605.00003
2. Ballings et al. (2015). *Evaluating multiple classifiers for stock price direction prediction.* Expert Systems with Applications, 42(20). https://doi.org/10.1016/j.eswa.2015.05.013
3. Lohrmann & Luukka (2019). *Classification of intraday S&P500 returns with a Random Forest.* International Journal of Forecasting, 35(1). https://doi.org/10.1016/j.ijforecast.2018.08.004
4. Deep et al. (2024). *Assessing the Impact of Technical Indicators on ML Models for Stock Price Prediction.* arXiv:2412.15448. https://arxiv.org/abs/2412.15448
5. Sorokina, Booth & Thornton (2021). *Data Snooping Bias in Tests of the Relative Performance of Multiple Forecasting Models.* Journal of Banking & Finance. https://doi.org/10.1016/j.jbankfin.2021.106716
