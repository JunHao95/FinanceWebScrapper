# ML-Based Corporate Credit Risk Scoring: Literature Summary

**Context:** AAPL — P(distress) = 0%. Top risk factors: `debt_to_equity`, `earnings_growth`, `current_ratio`.

---

## 1. Evolution of Methods

Corporate credit risk modelling has progressed through three statistical generations—discriminant analysis (Altman Z-score, 1968), binary response models (Ohlson O-score, 1980), and hazard/survival models (Shumway, 2001)—before the current wave of ML approaches. Modern ML methods treat default/distress prediction as a classification task and generally outperform classical statistical models on AUC and accuracy metrics, though they sacrifice interpretability and causal insight.

### Key ML families used in credit risk

| Family | Representative algorithms | Strengths | Weaknesses |
|---|---|---|---|
| SVMs | Linear/RBF kernel SVM | Good on small, high-dimensional data; less sensitive to imbalance | Opaque; expensive on large N |
| Tree ensembles | Random Forest, XGBoost, LightGBM | Handles non-linearity; feature importance built in; strong empirical performance | Can overfit without tuning; still a black box at depth |
| Neural networks | MLP, CNN, RNN/LSTM, Transformer | Captures complex temporal patterns; scalable | Data-hungry; opaque; prone to overfitting on rare-event data |
| Hybrid / ensemble | Stacked models, boosted heterogeneous ensembles | State-of-the-art accuracy in several benchmarks | Complexity; reproducibility concerns |

---

## 2. Core Papers (5 cited)

### [1] Kim, Cho & Ryu (2020) — "Corporate Default Predictions Using Machine Learning: Literature Review"
- **Source:** *Sustainability* 12(16), 6325. [DOI](https://www.mdpi.com/2071-1050/12/16/6325)
- **Contribution:** Comprehensive review bridging financial-engineering models (discriminant, logit, hazard) and ML methods (SVM, DT/RF, ANN). Identifies three open challenges: (a) models should be multi-period, (b) stock-market signals are under-used, (c) ML models rarely explain *why* default occurs.
- **Relevance to AAPL context:** Supports using financial ratios (current ratio, D/E) as features, but warns that single-period classification ignores path dependence.

### [2] Feng, Cheng, Li, Liu & Xue (2023) — "Corporate Credit Rating: A Survey"
- **Source:** arXiv:2309.14349 [cs.LG]. [Link](https://arxiv.org/abs/2309.14349)
- **Contribution:** Surveys statistical, ML, and neural-network models for corporate credit rating. Highlights recent progress of deep learning (CNN, RNN, attention) and common databases (Compustat, CSMAR). Notes that neural network models still struggle with small labeled datasets and class imbalance.
- **Relevance:** Directly addresses the rating problem rather than binary default; useful framing for AAPL since distress probability is ~0% and gradations of credit quality matter more than binary classification.

### [3] Barboza et al. (2017) — "Machine learning models and bankruptcy prediction"
- **Source:** *Expert Systems with Applications* 83, 405–417. (Cited extensively in [1] and [5])
- **Contribution:** Head-to-head comparison showing RF/boosting outperform logistic regression and discriminant analysis on bankruptcy prediction benchmarks by ~10 pp accuracy. Establishes ensemble tree methods as the de facto baseline.
- **Relevance:** Validates tree-based models as first-line tools; the features used overlap with AAPL's flagged risk factors.

### [4] Comparative Analysis of Resampling Techniques for Financial Distress Prediction (2025)
- **Source:** *Mathematics* 13(13), 2186. [DOI](https://www.mdpi.com/2227-7390/13/13/2186)
- **Contribution:** Benchmarks SMOTE, ADASYN, random under/oversampling, and Borderline-SMOTE with XGBoost on financial distress data. Finds that SMOTE+XGBoost yields the most stable F1 across minority ratios, but synthetic oversampling can inject artefactual patterns that inflate within-sample performance.
- **Relevance:** Directly bears on the synthetic-label problem (§3 below).

### [5] Systematic Review of Financial Distress Identification Using ML (2022)
- **Source:** *Applied Artificial Intelligence* 36(1). [DOI](https://www.tandfonline.com/doi/full/10.1080/08839514.2022.2138124)
- **Contribution:** Surveys 150+ studies. Categorises methods (threshold, one-class, cost-sensitive, ensemble). Highlights that definition of "distress" varies widely—some use Altman Z-score thresholds, others use actual bankruptcy filings, ST-designation, or negative equity—and that this label heterogeneity is a first-order problem for benchmarking.

---

## 3. Limitations of Training on Synthetic Distress Labels

This is the most relevant methodological concern for an internal scoring system like the one producing `P(distress) = 0%` for AAPL.

### What are "synthetic distress labels"?
In practice, true corporate distress events (Chapter 11 filings, debt defaults, rating downgrades to CCC or below) are **extremely rare** in public-company datasets—typically 1–3% of firm-years. Researchers and practitioners therefore often construct *proxy* labels:

- **Altman Z-score < 1.81** → labelled "distressed"
- **Negative net income for 2+ consecutive years**
- **Current ratio < 1 and D/E > threshold**
- **SMOTE / ADASYN-generated synthetic minority samples**

### Known problems

| Issue | Detail |
|---|---|
| **Label noise** | Proxy labels conflate temporary weakness with genuine distress. A profitable firm with a high D/E (e.g., a leveraged buyback programme, common for AAPL) gets mislabelled as risky. Studies show 5–50% label noise is common in tabular financial data (Springer ML 2024, DOI: 10.1007/s10994-024-06629-5). |
| **Circular features** | When the label is derived from the same ratios used as inputs (e.g., current ratio used both to define distress and to predict it), the model learns a tautology, not a genuine risk signal. |
| **Distribution shift from SMOTE** | Synthetic samples interpolate in feature space and can create instances that violate real-world constraints (e.g., negative revenue, impossible leverage ratios). This inflates AUC on held-out sets but degrades out-of-distribution calibration (Mathematics 2025, [4] above). |
| **Temporal leakage** | Many synthetic labelling schemes use annual snapshots, ignoring that distress unfolds over quarters. Models trained on annual labels cannot distinguish a firm that recovered in Q3 from one that defaulted in Q4. |
| **Survivorship bias** | Public-company datasets (Compustat, Yahoo Finance) drop delisted firms, so the "non-distressed" class is contaminated by firms that were distressed but disappeared from the sample. |
| **Calibration failure** | A model may rank firms correctly (good AUC) but assign meaningless absolute probabilities. A `P(distress) = 0%` for AAPL is plausible directionally, but the point estimate is unverifiable without knowing the label definition and calibration procedure used. |

### Implication for AAPL scoring
AAPL's flagged risk factors (`debt_to_equity`, `earnings_growth`, `current_ratio`) are standard Altman-style inputs. If the distress label was itself derived from a Z-score-like formula using these same features, the model's 0% probability is mechanically driven—it tells you AAPL passes the same threshold used to define the training labels, not that AAPL has zero credit risk in any economically meaningful sense.

---

## 4. Recommendations

1. **Audit label provenance.** Document exactly how `distressed = 1` is defined. If it is Z-score-derived, ensure the prediction features do not include the Z-score components verbatim.
2. **Prefer event-based labels.** Use actual bankruptcy filings, missed coupon payments, or agency downgrades (Moody's/S&P) rather than ratio thresholds.
3. **Calibrate, don't just classify.** Use Platt scaling or isotonic regression on the model output; report prediction intervals, not point estimates.
4. **Benchmark against hazard models.** Multi-period survival models (Shumway 2001; Duffie et al. 2007) handle temporal structure that single-period classifiers miss.
5. **Stress-test with macro variables.** ML models trained only on firm-level ratios will miss systemic risk; include credit-spread, GDP-growth, or VIX features.

---

## Sources

1. Kim, H., Cho, H. & Ryu, D. (2020). Corporate Default Predictions Using Machine Learning: Literature Review. *Sustainability*, 12(16), 6325. https://www.mdpi.com/2071-1050/12/16/6325
2. Feng, B., Cheng, X., Li, D., Liu, Z. & Xue, W. (2023). Corporate Credit Rating: A Survey. arXiv:2309.14349. https://arxiv.org/abs/2309.14349
3. Barboza, F., Kimura, H. & Altman, E. (2017). Machine learning models and bankruptcy prediction. *Expert Systems with Applications*, 83, 405–417.
4. Comparative Analysis of Resampling Techniques for Class Imbalance in Financial Distress Prediction Using XGBoost (2025). *Mathematics*, 13(13), 2186. https://www.mdpi.com/2227-7390/13/13/2186
5. Systematic Review of Financial Distress Identification using Machine Learning (2022). *Applied Artificial Intelligence*, 36(1). https://www.tandfonline.com/doi/full/10.1080/08839514.2022.2138124
6. An empirical study on impact of label noise on synthetic tabular data generation (2024). *Machine Learning*, Springer. https://link.springer.com/article/10.1007/s10994-024-06629-5
