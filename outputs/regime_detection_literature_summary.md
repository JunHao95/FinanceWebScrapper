# K-Means vs HMM Market Regime Detection — Literature Summary

**Context:** ABT (Abbott Laboratories) — both HMM and K-Means classifiers agree on a **Bull** regime.  
**Date:** 2026-05-11

---

## 1. Overview

Market regime detection aims to classify latent states of financial markets — typically *bull* (rising, low-volatility) and *bear* (falling, high-volatility) — from observed price or return data. Two dominant unsupervised approaches have emerged:

| Dimension | Hidden Markov Model (HMM) | K-Means Clustering |
|---|---|---|
| **Model class** | Probabilistic generative (parametric) | Distance-based partitioning (non-parametric) |
| **Temporal structure** | Explicit — transition matrix governs regime persistence & switching | None intrinsic — each window is classified independently |
| **Output** | Posterior probabilities over states at each time step | Hard cluster assignment per observation / window |
| **Key parameters** | Number of states, emission distribution family | Number of clusters *k*, feature set, distance metric |
| **Training** | Baum-Welch (EM) on sequential likelihood | Lloyd's / k-means++ on feature vectors |
| **Strengths** | Captures regime duration & switching dynamics; probabilistic uncertainty | Simple, fast, distribution-free; scales to high-dimensional feature spaces |
| **Weaknesses** | Sensitive to distributional assumptions (Gaussian emissions); prone to local optima; can misread short-term noise as regime shifts | No memory of prior state; sensitive to feature engineering; cluster labels need post-hoc economic interpretation |

---

## 2. Key Papers

### [P1] Oelschläger & Adam (2023) — *Detecting Bearish and Bullish Markets in Financial Time Series Using Hierarchical Hidden Markov Models*

- **Source:** Statistical Modelling, Vol 23(2); arXiv [2007.14874](https://arxiv.org/abs/2007.14874)
- **Method:** Hierarchical HMM (HHMM) that nests a short-term state process within a long-term regime process, allowing simultaneous capture of intra-regime fluctuations and macro bull/bear trends.
- **Data:** DAX and S&P 500 daily returns.
- **Key finding:** Standard 2-state HMMs conflate short-term corrections with genuine regime changes. The hierarchical extension materially reduces false regime-switch signals and improves out-of-sample classification of bull vs bear periods.
- **Relevance:** Demonstrates a core HMM limitation — sensitivity to transient noise — and a structured fix.

### [P2] Yuan & Mitra (2019) — *Market Regime Identification Using Hidden Markov Models*

- **Source:** SSRN 3406068, OptiRisk Systems. [Link](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3406068)
- **Method:** Gaussian-emission HMM fitted to FTSE 100 and S&P 500 weekly returns. Two and three-state models compared.
- **Key finding:** A 2-state HMM cleanly separates bull (positive mean, low variance) from bear (negative mean, high variance) regimes. The 3-state model adds a "stressed-but-not-bear" intermediate. Regime-conditional portfolio tilts improve Sharpe ratios relative to buy-and-hold.
- **Relevance:** Canonical application of HMM to equity regime detection; provides baseline bull/bear parameterisation comparable to ABT's HMM output.

### [P3] Akioyamen, Qian & Ren (2021) — *A Hybrid Learning Framework for Detection of Regime Switches in US Financial Markets*

- **Source:** arXiv [2108.05801](https://arxiv.org/abs/2108.05801)
- **Method:** PCA for dimensionality reduction on macroeconomic features, followed by **k-means clustering** to identify regimes. A classification model is then trained on the labelled clusters for real-time detection.
- **Data:** Publicly available US economic indicators; trading strategies benchmarked on S&P 500.
- **Key finding:** K-means on macro features identifies economically meaningful regimes (expansion vs contraction) without imposing distributional assumptions. Resulting trading strategies outperform buy-and-hold. The non-parametric approach avoids the Gaussian-emission constraint of standard HMMs.
- **Relevance:** Directly demonstrates k-means regime detection as a viable alternative to HMM on equities.

### [P4] McGreevy & Lam (2024) — *Detecting Multivariate Market Regimes via Clustering Algorithms*

- **Source:** SSRN 4758243; Imperial College MSc thesis. [Link](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4758243)
- **Method:** Wasserstein k-means clustering applied to windows of multivariate return distributions. Distance between empirical distributions (not point features) defines cluster membership.
- **Data:** Multi-asset US equity data; applied to pairs trading and portfolio design.
- **Key finding:** Distribution-aware k-means outperforms standard Euclidean k-means in regime separation quality. The method is non-parametric and extends naturally to high-dimensional, multivariate settings where HMM emission specification becomes difficult.
- **Relevance:** Advances the k-means approach by replacing naïve feature distances with distributional distances, addressing a key limitation.

### [P5] Nystrup, Madsen & Lindström (2020) — *Regime-Switching Factor Investing with Hidden Markov Models*

- **Source:** Journal of Risk and Financial Management, 13(12), 311. [PDF](https://mdpi-res.com/d_attachment/jrfm/jrfm-13-00311/article_deploy/jrfm-13-00311-v2.pdf)
- **Method:** HMM-based regime detection on S&P 500 ETF; regime labels drive rotation among factor models (value, momentum, quality, etc.).
- **Data:** ~10.5 years of US equity data (2007–2017).
- **Key finding:** Factor exposures that are optimal in bull regimes degrade in bear regimes. HMM-driven switching between factor models improves risk-adjusted returns vs static factor allocation.
- **Relevance:** Shows how HMM regime labels translate into actionable portfolio decisions — analogous to how ABT's regime label could condition trading strategy.

---

## 3. Head-to-Head Comparison

| Criterion | HMM | K-Means |
|---|---|---|
| **Theoretical grounding** | Strong — rooted in stochastic process theory; transition matrix has economic interpretation (regime persistence) | Weaker — no generative model; regimes are defined by proximity in feature space |
| **Temporal coherence** | High — Markov property penalises rapid switching; Viterbi path is smooth | Low — unless windowed features or post-hoc smoothing is applied, labels can flicker |
| **Distributional flexibility** | Constrained by emission family (usually Gaussian or mixture); fat tails / skewness require extensions (Student-t, regime-dependent GARCH) | Unconstrained — any feature set; Wasserstein variants [P4] handle distributional shape directly |
| **Scalability to high dimensions** | Poor — number of parameters grows quadratically with feature count; multivariate emissions are hard to estimate | Good — k-means scales linearly; PCA pre-processing [P3] handles dimensionality |
| **Interpretability** | Excellent — each state has a mean-return / volatility characterisation and a transition matrix | Moderate — cluster centres are interpretable but lack transition dynamics |
| **Uncertainty quantification** | Built-in — posterior state probabilities | None natively — requires bootstrap or ensemble extensions |
| **Practical use in trading** | Directly feeds regime-switching portfolio models [P2, P5] | Feeds classifier-based or rule-based strategies [P3] |

### When models agree (as for ABT)

Agreement between HMM and K-Means increases confidence in the regime label because the two methods have **orthogonal failure modes**:
- HMM may misclassify due to distributional mis-specification or short-term noise sensitivity [P1].
- K-Means may misclassify due to poor feature selection or lack of temporal context.

When both independently assign "Bull," the label is robust to both failure modes.

---

## 4. Open Questions & Limitations

1. **Regime count selection** — both methods require pre-specifying the number of regimes. BIC/AIC for HMM; elbow/silhouette for k-means. Neither has a universally accepted selection criterion.
2. **Lookahead bias** — many studies fit models on full samples. Online / expanding-window implementations are necessary for live trading but under-studied.
3. **Label alignment** — HMM and k-means may define "bull" differently (HMM: positive expected return state; k-means: low-volatility cluster). Comparing outputs requires careful post-hoc label matching.
4. **Regime granularity** — 2-state models (bull/bear) may be too coarse; 3+ state models (adding "recovery" or "correction") improve fit but increase estimation noise.

---

## Sources

1. Oelschläger & Adam (2023). *Detecting Bearish and Bullish Markets…* arXiv:2007.14874 — https://arxiv.org/abs/2007.14874
2. Yuan & Mitra (2019). *Market Regime Identification Using HMMs.* SSRN 3406068 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3406068
3. Akioyamen, Qian & Ren (2021). *A Hybrid Learning Framework…* arXiv:2108.05801 — https://arxiv.org/abs/2108.05801
4. McGreevy & Lam (2024). *Detecting Multivariate Market Regimes via Clustering Algorithms.* SSRN 4758243 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4758243
5. Nystrup et al. (2020). *Regime-Switching Factor Investing with HMMs.* JRFM 13(12):311 — https://doi.org/10.3390/jrfm13120311
