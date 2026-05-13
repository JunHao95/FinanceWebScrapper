# ML-Based Corporate Credit Risk Scoring — Literature Summary

**Context:** AAPL | P(distress) = 0% | Top risk factors: `debt_to_equity`, `earnings_growth`, `current_ratio`

---

## 1. Overview

Machine-learning (ML) methods for corporate credit risk have evolved through three generations: (i) statistical models (logistic regression, discriminant analysis — Altman Z-Score, 1968), (ii) classical ML (SVM, random forest, gradient boosting), and (iii) deep learning / neural-network architectures. Recent surveys converge on the finding that **ensemble tree methods (XGBoost, LightGBM) remain the strongest general-purpose performers** on tabular financial data, while deep models show advantages mainly when unstructured data (text, filings, news) is incorporated.

---

## 2. Key Papers

### [1] Feng, Cheng, Li et al. — *Corporate Credit Rating: A Survey* (2023)
- **arXiv:** [2309.14349](https://arxiv.org/abs/2309.14349)
- Comprehensive survey spanning statistical, ML, and neural-network models for corporate credit rating.
- Finds that neural-network models improve discrimination in high-dimensional feature spaces but remain harder to interpret and more sensitive to data quality than classical approaches.
- Catalogues standard databases (Compustat, CSMAR, Moody's KMV) and notes the persistent **label scarcity** problem — true default events are rare.

### [2] Altman — *Applications of Distress Prediction Models: What Have We Learned After 50 Years from the Z-Score Models?* (2018)
- **DOI/URL:** [IJFS 6(3), 70](https://www.mdpi.com/2227-7072/6/3/70)
- Retrospective by Altman himself. The Z-Score remains the most widely used distress proxy in academic studies, serving as both a standalone predictor and a **benchmark label generator** for ML pipelines.
- Emphasises that the Z-Score was calibrated on mid-20th-century US manufacturing firms; applying it as a ground-truth label to modern tech firms (e.g. AAPL) introduces **domain-shift bias**.

### [3] Muñoz-Cancino et al. — *Synthetic Data for Credit Scoring* (2023)
- **arXiv:** [2301.01212](https://arxiv.org/abs/2301.01212)
- Evaluates models trained on synthetic (generated) data vs. real borrower data. Synthetic-trained models lose ~3% AUC and ~6% KS relative to real-data baselines.
- Finds that **synthetic data quality degrades as feature dimensionality increases**, directly relevant to corporate risk models that consume dozens of financial ratios.

### [4] Mo, Zhang, Tan et al. — *Reassessment of Corporate Credit Risk Identification: Novel Discoveries from Integrated ML Models* (2024)
- **URL:** [Computational Economics, 2024](https://link.springer.com/article/10.1007/s10614-024-10801-3)
- Proposes integrated (stacking/blending) ML ensembles on CSMAR-sourced Chinese listed firms.
- Demonstrates that **feature engineering around leverage and liquidity ratios** (debt-to-equity, current ratio) remains the single largest driver of model performance, ahead of algorithmic choice — consistent with AAPL's top risk factors.

### [5] Comparative Analysis of Resampling Techniques for Financial Distress Prediction Using XGBoost (2025)
- **URL:** [Mathematics 13(13), 2186](https://www.mdpi.com/2227-7390/13/13/2186)
- Benchmarks SMOTE, ADASYN, Tomek, and random undersampling on imbalanced distress datasets.
- Shows that standard accuracy and precision metrics **overstate performance** when the distress class is <3% of the sample — a direct concern for any model scoring a company like AAPL where real defaults are extremely rare.

---

## 3. Limitations of Training on Synthetic / Proxy Distress Labels

Most academic ML credit-risk models **do not train on actual default events** because true corporate defaults are rare and databases are proprietary. Instead, they use one or more proxies:

| Proxy Label | How It Works | Key Limitation |
|---|---|---|
| **Altman Z-Score threshold** | Z < 1.81 → "distressed" | Calibrated on 1960s US manufacturing; biased for asset-light tech firms |
| **ST / \*ST designation** (China) | Regulatory flag for consecutive losses | Jurisdiction-specific; labels appear *after* distress is obvious |
| **Rating downgrade** | Drop below investment grade | Reflects agency opinion, not objective state; lags real risk |
| **Synthetic oversampling** (SMOTE, ADASYN) | Generate artificial minority samples | Inflates apparent recall; models learn interpolated feature space, not real tail behaviour |
| **Generative synthetic data** (GANs, FinGPT) | Generate entire borrower profiles | ~3-6% AUC/KS degradation vs. real data [3]; quality collapses in high dimensions |

**Consequences for an AAPL-like company:**

1. **Near-zero base rate.** AAPL's P(distress) ≈ 0%. Any binary classifier trained on proxy labels will either (a) never predict distress (high accuracy, zero recall) or (b) over-trigger false positives after SMOTE-style rebalancing. Standard classification metrics become unreliable.
2. **Domain shift.** Z-Score-derived labels embed assumptions about capital structure that do not transfer to companies with $160B+ cash reserves and ~100% debt-to-equity driven by share buybacks rather than operational weakness.
3. **Label noise compounds model error.** Muñoz-Cancino et al. [3] show that even modest label corruption propagates non-linearly — and proxy labels are *systematically*, not randomly, noisy.
4. **Temporal leakage.** Regulatory distress flags (ST status, rating actions) are backward-looking. Models trained on these labels learn to detect *already-distressed* firms, not to forecast future distress.

---

## 4. Implications for This Project

- The model's 0% P(distress) for AAPL is **plausible and likely correct**, but the confidence bound around that estimate is unknowable without calibration on true default data.
- The top risk factors (`debt_to_equity`, `earnings_growth`, `current_ratio`) align with the feature-importance findings of Mo et al. [4], lending credibility to the feature selection.
- Any threshold-based distress label used during training should be **documented explicitly**, and results should be presented as relative risk rankings rather than calibrated probabilities, unless validated against observed defaults.

---

## Sources

1. Feng et al., "Corporate Credit Rating: A Survey," arXiv:2309.14349 (2023) — https://arxiv.org/abs/2309.14349
2. Altman, "Applications of Distress Prediction Models," *Int. J. Financial Studies* 6(3):70 (2018) — https://www.mdpi.com/2227-7072/6/3/70
3. Muñoz-Cancino et al., "Synthetic Data for Credit Scoring," arXiv:2301.01212 (2023) — https://arxiv.org/abs/2301.01212
4. Mo et al., "Reassessment of Corporate Credit Risk Identification," *Computational Economics* (2024) — https://link.springer.com/article/10.1007/s10614-024-10801-3
5. "Comparative Analysis of Resampling Techniques for Financial Distress Prediction Using XGBoost," *Mathematics* 13(13):2186 (2025) — https://www.mdpi.com/2227-7390/13/13/2186
