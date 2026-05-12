# Random Forest Classifiers for Equity Return Direction Prediction

## Literature Review — Prepared for TSLA Context (RF Signal: 59% Bullish)

*Date: 2026-05-10*

---

## 1. What Random Forests Do in This Setting

A random forest (RF) classifier for equity direction prediction typically:
- Ingests technical indicators, lagged returns, volume features, and sometimes macro variables.
- Outputs a binary (up/down) or ternary (up/flat/down) class for forward returns over a horizon (1-day to 1-month).
- Aggregates votes across hundreds of decorrelated decision trees, each trained on a bootstrap sample of the data with a random feature subset at each split.

The appeal is intuitive: RFs handle nonlinear interactions, require minimal feature scaling, and are less prone to catastrophic overfitting than single deep trees. But "less prone" is not "immune," and the financial prediction domain has properties that stress every ML method.

---

## 2. Key Papers

### [1] Gu, Kelly & Xiu (2020) — "Empirical Asset Pricing via Machine Learning"
*The Review of Financial Studies, 33(5), 2223–2273.*

The benchmark study. Compares OLS, elastic net, PCR/PLS, random forests, gradient-boosted trees, and neural networks for cross-sectional return prediction on US equities (1957–2016). Key findings relevant to RF:

- **Trees and neural networks dominate** linear methods for out-of-sample R² of monthly individual stock returns.
- **RF out-of-sample R² ≈ 0.4–0.8%** (monthly), which sounds tiny but is economically meaningful for portfolio sorts.
- Interaction effects between firm characteristics and macroeconomic state are the main source of RF's edge over linear models.
- **Caveat**: All R² values are measured against a zero-prediction (historical mean) benchmark. The absolute level of predictability is low, and most of the cross-section remains unexplained.

**URL:** https://academic.oup.com/rfs/article/33/5/2223/5758276

---

### [2] Krauss, Do & Huck (2017) — "Deep Neural Networks, Gradient-Boosted Trees, Random Forests: Statistical Arbitrage on the S&P 500"
*European Journal of Operational Research, 259(2), 689–702.*

Applies RF, GBT, and deep nets to daily return direction prediction on S&P 500 constituents (1992–2015) in a pairs/statistical-arbitrage framework:

- **RF daily directional accuracy ≈ 51–53%**, modestly above the 50% coin-flip baseline.
- After transaction costs, profitability **erodes substantially**, especially post-2010 as markets became more efficient and spreads tightened.
- The ensemble of all three methods slightly outperforms any single method, suggesting each captures different signal subsets.
- **Key limitation noted**: performance degrades in later sample periods, consistent with adaptive market efficiency eroding the signal over time.

**URL:** https://ideas.repec.org/a/eee/ejores/v259y2017i2p689-702.html

---

### [3] Leung, Lohre, Mischlich, Shea & Stroh (2021) — "The Promises and Pitfalls of Machine Learning for Predicting Stock Returns"
*SSRN Working Paper (revised 2021).*

A practitioner-oriented review from Invesco/Robeco researchers that directly addresses the gap between in-sample hype and out-of-sample reality:

- Emphasises that **feature importance rankings from RF are unstable** across time periods and sensitive to correlated predictors.
- Documents how **hyperparameter tuning on financial data inflates apparent accuracy** — the number of trees, max depth, and min-samples-per-leaf choices act as implicit degrees of freedom.
- Recommends strict **temporal cross-validation** (expanding or rolling window, never random k-fold) and **purging/embargoing** to prevent lookahead leakage.
- Shows that ensemble methods including RF produce **economically marginal improvements** over penalised linear models when realistic constraints are applied.

**URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3546725

---

### [4] Arnott, Harvey & Markowitz (2019) — "A Backtesting Protocol in the Era of Machine Learning" (+ López de Prado, 2018)
*Journal of Financial Data Science, 1(1); and López de Prado, "Advances in Financial Machine Learning," Wiley, 2018.*

These works formalize the data-snooping problem for ML in finance:

- **Multiple testing bias**: If you evaluate 100 RF configurations and report the best one, the probability of a false discovery is not 5% — it approaches certainty. López de Prado's **Deflated Sharpe Ratio** adjusts for the number of trials.
- **Backtest overfitting**: López de Prado (2018, Ch. 11) shows that walk-forward validation helps but does not eliminate selection bias when the researcher iterates on the walk-forward results themselves.
- A single "59% bullish" signal from an RF should be interpreted in light of: how many alternative model specifications were tried, whether the training/test split is strictly temporal, and whether the probability is calibrated or just a raw vote fraction.

**URLs:**
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104847
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104816

---

### [5] Nikolopoulos (2026) — "Spurious Predictability in Financial Machine Learning"
*arXiv:2604.15531 (April 2026).*

The most recent and directly cautionary work:

- Introduces a **falsification audit** that tests complete ML prediction workflows against synthetic null environments (zero-predictability data).
- Demonstrates that adaptive specification search (tuning features, windows, thresholds) **generates statistically significant backtests even when the true data-generating process is a martingale** (i.e., truly unpredictable).
- Many "findings" in the applied ML-finance literature are shown to be **methodological artifacts** rather than genuine predictability.
- Proposes an **absolute magnitude gap** metric to quantify how much of apparent performance is attributable to selection/optimisation.

**URL:** https://arxiv.org/abs/2604.15531

---

## 3. Known Limitations of RF for Equity Direction Prediction

| Limitation | Explanation |
|---|---|
| **Low signal-to-noise ratio** | Equity returns are dominated by noise. Even the best ML models explain <1% of monthly return variance out-of-sample (Gu et al., 2020). A 59% vote fraction may reflect noise rather than signal. |
| **Non-stationarity** | Financial regimes shift. An RF trained on 2015–2023 data may embed relationships (e.g., "low vol → bullish") that invert in a new regime. Feature importance is unstable over time (Leung et al., 2021). |
| **No extrapolation** | RFs predict within the range of training targets. In tail events or unprecedented market conditions, RF outputs are bounded by historical experience and will not flag regime breaks. |
| **Probability mis-calibration** | The raw fraction of trees voting "up" is not a well-calibrated probability. Without explicit calibration (Platt scaling, isotonic regression), "59% bullish" may mean very little in absolute terms. |
| **Transaction cost erosion** | Directional accuracy of 51–53% can be profitable in theory but often fails to cover realistic bid-ask spreads and market impact, especially for single-name equities like TSLA (Krauss et al., 2017). |
| **Correlated features** | Technical indicators are highly collinear. RF splits among correlated features semi-randomly, making feature importance unreliable and inflating the model's apparent flexibility. |

---

## 4. Data-Snooping Risks — Specific to Your Context

1. **Hyperparameter search multiplicity.** Every choice of `n_estimators`, `max_depth`, `min_samples_leaf`, lookback window, and feature set is a trial. Reporting the best configuration without adjusting for the number of trials inflates apparent skill.

2. **Feature selection leakage.** If features were chosen because they "worked well" on the same data used for backtesting, the model has seen the test set indirectly.

3. **Survivorship in the target.** TSLA is in your universe *because* it survived and grew. A model trained on survivors inherits survivorship bias.

4. **Temporal leakage via random CV.** Standard k-fold cross-validation on time-series data shuffles future information into training folds. Only expanding-window or purged walk-forward validation is defensible (López de Prado, 2018; Leung et al., 2021).

5. **Publication / selection bias in the literature itself.** Papers reporting that RF "works" for stock prediction are more likely to be published than null results, inflating the prior expectation (Nikolopoulos, 2026).

---

## 5. Implications for the TSLA 59% Bullish Signal

- A **59% vote fraction** from an RF classifier is a weak signal in absolute terms. It means ~41% of the trees disagreed. In the Gu et al. (2020) framework, this would be at best marginally above the unconditional base rate.
- Without knowing the **calibration curve** of this specific model, the number cannot be interpreted as a 59% probability of positive returns.
- The signal should be **one input among many** — not a standalone trading trigger. Cross-check against fundamental valuation, macro regime, and volatility context.
- Ask: **how many model configurations were evaluated** before arriving at this one? If the answer is "many," apply a deflation factor (López de Prado's DSR framework).

---

## Sources

1. Gu, S., Kelly, B., & Xiu, D. (2020). Empirical Asset Pricing via Machine Learning. *The Review of Financial Studies*, 33(5), 2223–2273. https://academic.oup.com/rfs/article/33/5/2223/5758276
2. Krauss, C., Do, X.A., & Huck, N. (2017). Deep Neural Networks, Gradient-Boosted Trees, Random Forests: Statistical Arbitrage on the S&P 500. *European Journal of Operational Research*, 259(2), 689–702. https://ideas.repec.org/a/eee/ejores/v259y2017i2p689-702.html
3. Leung, E., Lohre, H., Mischlich, D., Shea, Y., & Stroh, M. (2021). The Promises and Pitfalls of Machine Learning for Predicting Stock Returns. *SSRN*. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3546725
4. López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104847
5. Nikolopoulos, S. (2026). Spurious Predictability in Financial Machine Learning. *arXiv:2604.15531*. https://arxiv.org/abs/2604.15531
