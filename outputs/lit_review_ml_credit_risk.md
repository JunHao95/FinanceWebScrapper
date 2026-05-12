# ML-Based Corporate Credit Risk Scoring: Literature Summary

**Context:** ABT (Abbott Laboratories) — P(distress) = 0%. Top risk factors: debt_to_equity, earnings_growth, current_ratio.

---

## 1. Evolution of Corporate Default Prediction

The literature traces three generations of statistical models — discriminant analysis (Altman Z-score, 1968), binary response / logit models (Ohlson O-score, 1980), and hazard / survival models (Shumway, 2001) — followed by a wave of ML approaches starting in the 2000s that now dominate accuracy benchmarks.

## 2. Key Papers

### [P1] Kim, Cho & Ryu (2020) — "Corporate Default Predictions Using Machine Learning: Literature Review"
*Sustainability* 12(16), 6325. [DOI](https://doi.org/10.3390/su12166325)

- Comprehensive review comparing three generations of statistical models (discriminant analysis → logit → hazard) with three ML families (SVM, decision trees/random forests, neural networks).
- **Key finding:** ML classifiers generally outperform statistical models on accuracy, but treat default as a static classification problem, ignoring the multi-period, path-dependent nature of distress. They also rarely explain *why* a firm defaults.
- Notes that class imbalance (defaults are rare events) is a pervasive problem; SVM is reported as least sensitive to imbalance.

### [P2] Zhao, Ouenniche & De Smedt (2025) — "Survey, Classification and Critical Analysis of the Literature on Corporate Bankruptcy and Financial Distress Prediction"
*Machine Learning with Applications*. [PDF](https://anjammaghaleh.com/wp-content/uploads/2025/06/Machine-Learning-with-Applications-.pdf)

- PRISMA-based review of 207 empirical studies (2012–2023).
- Finds hybrid/ensemble models (e.g., XGBoost + neural nets) consistently improve accuracy and robustness.
- Highlights that financial ratios remain the dominant feature set, but text, macro, and governance variables are increasingly incorporated.

### [P3] Mo et al. (2024) — "Reassessment of Corporate Credit Risk Identification: Novel Discoveries from Integrated Machine Learning Models"
*Computational Economics*. [DOI](https://doi.org/10.1007/s10614-024-10801-3)

- Proposes integrated ML models (stacking ensembles) for corporate credit risk.
- Demonstrates that combining heterogeneous learners captures non-linear interactions among ratios like **debt-to-equity**, **current ratio**, and earnings metrics — directly relevant to ABT's top risk factors.

### [P4] Maurino et al. (2025) — "How Data Quality Affects Machine Learning Models for Credit Risk Assessment"
arXiv:2511.10964. [Link](https://arxiv.org/abs/2511.10964)

- Systematically corrupts an open-source credit dataset (missing values, noisy attributes, outliers, **label errors**) using the Pucktrick library.
- Tests 10 models (RF, SVM, logistic regression, etc.).
- **Key finding:** Label noise degrades all models, but tree-based ensembles (Random Forest, XGBoost) are more robust than linear models. At 20%+ label corruption, even robust models show significant accuracy drops (~5–10 pp AUC loss).
- Directly relevant to the synthetic-label concern below.

### [P5] Díaz-Rodríguez et al. (2025) — "Corporate Failure Prediction: A Literature Review of Altman Z-Score and Machine Learning Models Within a Technology Adoption Framework"
*J. Risk Financial Management* 18(8), 465. [DOI](https://doi.org/10.3390/jrfm18080465)

- Compares ML models against the classic Altman Z-score through a technology-adoption lens.
- Finds ML models achieve higher statistical accuracy, but Z-score retains advantages in **interpretability and adoption** among practitioners — a point that matters for production credit-risk systems.

---

## 3. Limitations of Training on Synthetic Distress Labels

Most academic ML credit-risk models do **not** train on actual default events (which are rare and unevenly reported). Instead they rely on **proxy / synthetic distress labels** such as:

| Proxy Label | Construction | Known Bias |
|---|---|---|
| Altman Z-score threshold | Z < 1.81 → "distressed" | Calibrated on 1960s US manufacturing; misclassifies asset-light or high-growth firms |
| Negative equity / coverage ratios | Book equity < 0, interest coverage < 1 | Ignores firms that are technically distressed but operationally viable (e.g., leveraged buyouts) |
| Credit-rating downgrades | Rating falls below investment grade | Lagging indicator; ratings are sticky and biased toward incumbents |
| Delisting / filing events | SEC filing or exchange delisting | Survivorship bias; voluntary delistings conflated with distress |
| SMOTE-generated minority samples | Interpolation between real distress cases | Creates synthetic points in feature space that may not correspond to any plausible firm state |

**Core problems:**

1. **Label noise → biased decision boundaries.** [P4] shows that even 10% label error shifts learned thresholds materially. When the "distressed" label itself is a noisy proxy (e.g., Z < 1.81 on firms that never default), the model learns to predict the proxy, not true default.

2. **Class imbalance amplifies proxy errors.** Corporate default rates are ~1–2% annually. If the positive class is already tiny, even small label contamination flips the effective base rate. SMOTE and oversampling can amplify mislabeled minority examples [P1, P2].

3. **Temporal leakage.** Many proxy labels (rating downgrades, equity turning negative) are contemporaneous with or lag the distress event, making the model retrospectively accurate but prospectively useless.

4. **Domain shift.** Models trained on proxy labels from one economic regime (e.g., low-rate environment) may not transfer. [P5] notes that Altman Z-score parameters were fit on 1960s manufacturing — applying them as ground truth to 2020s healthcare (like ABT) introduces systematic bias.

5. **Calibration failure.** A model may rank-order firms correctly (good AUC) but produce meaningless probability estimates. When ABT gets P(distress) = 0%, that point estimate is likely an artifact of the proxy label never firing for firms with ABT's ratio profile, not a calibrated probability.

---

## 4. Implications for ABT's 0% Distress Score

ABT's top risk factors (debt_to_equity, earnings_growth, current_ratio) are standard Altman-family inputs. A 0% distress probability for a large-cap, investment-grade healthcare firm is **expected under any reasonable model** — but the precision of "0%" is illusory:

- It likely reflects that no training example with ABT-like ratios was labeled "distressed" under the chosen proxy, not that default risk is literally zero.
- The model's discrimination power is concentrated in the distressed tail; it tells you almost nothing about the *relative* risk among healthy firms.
- For ABT-class firms, market-based measures (CDS spreads, Merton distance-to-default) are more informative than accounting-ratio classifiers.

---

## 5. Open Questions

1. Can **self-supervised or contrastive learning** on financial time series reduce dependence on binary distress labels?
2. Do **LLM-extracted features** from 10-K filings improve early warning beyond ratio-based models?
3. What is the right **evaluation protocol** when ground-truth defaults are too rare for standard train/test splits?

---

## Sources

1. Kim, Cho & Ryu (2020). *Corporate Default Predictions Using ML: Literature Review.* Sustainability 12(16), 6325. https://doi.org/10.3390/su12166325
2. Zhao, Ouenniche & De Smedt (2025). *Survey, Classification and Critical Analysis… Corporate Bankruptcy and Financial Distress Prediction.* ML with Applications. https://anjammaghaleh.com/wp-content/uploads/2025/06/Machine-Learning-with-Applications-.pdf
3. Mo et al. (2024). *Reassessment of Corporate Credit Risk Identification.* Computational Economics. https://doi.org/10.1007/s10614-024-10801-3
4. Maurino et al. (2025). *How Data Quality Affects ML Models for Credit Risk Assessment.* arXiv:2511.10964. https://arxiv.org/abs/2511.10964
5. Díaz-Rodríguez et al. (2025). *Corporate Failure Prediction: Altman Z-Score and ML Models.* J. Risk Financial Management 18(8), 465. https://doi.org/10.3390/jrfm18080465
