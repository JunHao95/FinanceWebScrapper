# Random Forest Classifiers for Equity Return Direction Prediction
## Literature Summary — ABT Context (RF Signal: 79% Bullish)

*Generated: 2026-05-11*

---

## 1. Core Finding: RF Consistently Tops Single-Classifier Benchmarks (In-Sample)

Across the surveyed literature, random forests (RF) reliably rank first or near-first among ML classifiers for predicting the *direction* (up/down) of equity returns when evaluated on the training period or via random cross-validation.

| Study | Asset(s) | Best Classifier | Reported Accuracy |
|---|---|---|---|
| Ballings et al. (2015) | 5767 European stocks | Random Forest | AUC top across 5×2 CV |
| Khaidem et al. (2016) | Multiple US equities | Random Forest | ~85–90% (OOB) |
| Lohrmann & Luukka (2019) | Intraday S&P 500 | Random Forest | ~56–58% directional |
| Ampomah et al. (2020) | S&P 500, DJIA, NYSE | Voting (RF component) | ~56–62% directional |

**Key caveat**: accuracy figures are sensitive to how classes are defined (daily vs. weekly vs. monthly direction), feature sets used, and — critically — whether temporal ordering is respected in the evaluation split.

---

## 2. Key Papers

### [P1] Ballings, Van den Poel & Hespeels (2015)
**"Evaluating multiple classifiers for stock price direction prediction"**
*Expert Systems with Applications, 42(20), 7046–7056.*

- Benchmarked RF, AdaBoost, kernel factory, SVM, logit, LDA, k-NN, neural nets across 5,767 European stocks.
- RF achieved the highest AUC using 5×2 fold cross-validation.
- **Limitation**: used *random* CV folds, not temporal splits — this violates temporal ordering and inflates measured accuracy via look-ahead leakage.

### [P2] Khaidem, Saha & Dey (2016)
**"Predicting the direction of stock market prices using random forest"**
*arXiv:1605.00003*

- Used RSI, stochastic oscillator, and Williams %R as RF input features on multiple US equities.
- Reported OOB error rates suggesting 85–90% directional accuracy.
- **Limitation**: OOB estimation within RF does *not* respect temporal ordering — each tree's OOB sample is drawn uniformly, not from future-only data. The reported accuracy is therefore an unreliable estimate of true out-of-sample performance.

### [P3] Lohrmann & Luukka (2019)
**"Classification of intraday S&P500 returns with a Random Forest"**
*International Journal of Forecasting, 35(1), 390–407.*

- Applied RF to intraday S&P 500 data with a richer feature set.
- Achieved modest ~56–58% directional accuracy, closer to what theory would predict for a liquid, efficient market.
- More realistic evaluation design than P1/P2, but still subject to feature selection bias from prior literature.

### [P4] Nikolopoulos (2026)
**"Spurious Predictability in Financial Machine Learning"**
*arXiv:2604.15531*

- Introduced a formal **falsification audit** for ML-based financial prediction workflows.
- Showed that adaptive specification search (tuning features, hyperparameters, thresholds) generates statistically significant backtests *even under zero-predictability (martingale) nulls*.
- Quantified "selection-induced performance inflation" — the gap between optimized in-sample evidence and disjoint walk-forward realizations.
- **Core result**: many apparent ML forecasting discoveries are methodological artifacts rather than genuine predictability.

### [P5] Lo (1994) / Lo & MacKinlay
**"Data-Snooping Biases in Financial Analysis"**
*Working paper, MIT/Wharton*

- Foundational treatment of data-snooping in finance — the risk that "enough attempts on the same dataset will find spurious patterns."
- Argued this is especially severe in finance because (a) the same datasets (S&P 500, CRSP) are reused across thousands of studies, and (b) publication bias filters for positive results.
- The problem compounds with ML because the model space (hyperparameters × features × architectures) is vastly larger than classical regression.

---

## 3. Known Limitations of RF for Equity Prediction

### 3.1 Look-Ahead Bias in Standard CV
Random k-fold cross-validation shuffles temporal observations. A sample from 2024 can train the model while a sample from 2022 is used for testing. This violates causal ordering and inflates accuracy. **Papers P1 and P2 above both suffer from this.** Correct evaluation requires *expanding-window* or *walk-forward* splits where the training set always precedes the test set.

### 3.2 OOB Error ≠ Temporal Out-of-Sample Error
RF's out-of-bag (OOB) estimate is often cited as "built-in cross-validation." However, OOB samples are drawn *uniformly at random* from the training set, not from future periods. For time-series data, OOB accuracy is systematically over-optimistic (Nikolopoulos 2026, §3).

### 3.3 Data Snooping from Cumulative Literature
Even if a single study uses honest walk-forward testing, the *choice* to use RF with RSI + stochastic oscillator + Williams %R as features is itself informed by decades of prior studies on the same indices. This is "indirect data snooping" or "collective multiple testing" (Lo 1994). The more published studies exist for S&P 500 direction prediction, the higher the probability that *some* combination looks significant by chance.

### 3.4 Non-Stationarity and Regime Change
RF is a static learner — it assumes the data-generating process is stationary. Financial return distributions shift with monetary policy, volatility regimes, and market microstructure changes. A model trained on 2015–2020 data may embed relationships that reversed post-2020. RF provides no built-in mechanism for detecting or adapting to structural breaks.

### 3.5 Feature Importance ≠ Causal Importance
RF's permutation or Gini importance rankings reflect statistical association in the training data, not causal mechanisms. High importance of RSI in a trained model does not mean RSI *causes* future returns — it may proxy for an omitted variable or reflect a transient correlation.

### 3.6 Out-of-Sample Degradation
Empirical evidence consistently shows ML models (including RF) degrade out-of-sample relative to in-sample. Sarwar et al. (2025) found RF models with technical indicators "struggled with out-of-sample generalization" at minute-level frequency (arXiv:2412.15448). Similarly, Wong et al. (2025) showed RF outperformed logit in cross-sectional OOS but *failed* in temporal OOS for IPO prediction.

---

## 4. Implications for the ABT 79% Bullish RF Signal

| Question | Assessment |
|---|---|
| **Is 79% a realistic directional confidence?** | Almost certainly **inflated** relative to true forward-looking accuracy. Even well-designed RF models on liquid US equities achieve ~55–60% directional accuracy OOS (P3). A 79% signal likely reflects in-sample or look-ahead-contaminated calibration. |
| **Could the signal still contain information?** | Yes — but the *magnitude* of the edge should be heavily discounted. If the true directional accuracy is 55% and the signal says 79%, treat the direction as weakly suggestive, not as a high-confidence forecast. |
| **What would increase trust?** | (1) Walk-forward backtest on genuinely held-out data with transaction costs. (2) Comparison against a naïve "always predict up" baseline (which is ~53% accurate for US large-caps due to equity premium). (3) A falsification test per Nikolopoulos (2026) against synthetic null data. |

---

## 5. Sources

1. Ballings, M., Van den Poel, D., & Hespeels, N. (2015). "Evaluating multiple classifiers for stock price direction prediction." *Expert Systems with Applications*, 42(20), 7046–7056. https://doi.org/10.1016/j.eswa.2015.04.026
2. Khaidem, L., Saha, S., & Dey, S.R. (2016). "Predicting the direction of stock market prices using random forest." arXiv:1605.00003. https://arxiv.org/abs/1605.00003
3. Lohrmann, C. & Luukka, P. (2019). "Classification of intraday S&P500 returns with a Random Forest." *International Journal of Forecasting*, 35(1), 390–407. https://doi.org/10.1016/j.ijforecast.2018.07.004
4. Nikolopoulos, S. (2026). "Spurious Predictability in Financial Machine Learning." arXiv:2604.15531. https://arxiv.org/abs/2604.15531
5. Lo, A.W. (1994). "Data-Snooping Biases in Financial Analysis." MIT Working Paper. https://web.mit.edu/Alo/www/Papers/lo-94b.html

*Supplementary*: Sarwar et al. (2024), arXiv:2412.15448; Ampomah et al. (2020), *Information* 11(7), 332; Wong et al. (2025), *Intelligent Systems in Accounting, Finance and Management*.
