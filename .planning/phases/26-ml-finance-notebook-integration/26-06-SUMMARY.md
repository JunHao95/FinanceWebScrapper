---
phase: 26-ml-finance-notebook-integration
plan: "06"
status: complete
date: 2026-05-04
---

# Phase 26-06 Summary — Human Verification & Bug Fixes

## Verification outcome

Human-approved after browser testing with AAPL (single-ticker) and AAPL+MSFT (multi-ticker).

## Bugs fixed during verification

### 1. Credit Risk bullets showing `[object Object]`
`top_factors` returns `{name, value, contribution}` objects. Render was calling `f` directly.
Fix: `var label = (f && typeof f === 'object') ? f.name : f;`

### 2. PCA section never rendered
`mlSignalsPcaSection` div pre-exists in HTML (added in 26-05). `fetchPCA` hit `if (existing) return` early-exit guard and bailed without fetching.
Fix: reuse existing div instead of bailing; added loading placeholder; added session cache key to prevent duplicate fetches on tab re-activation.

## Feature guide added

Collapsible `<details>` panel added to `mlSignalsTabContent` in `index.html`. Explains all 5 ML features (PCA, RF Direction, Market Regime, Credit Risk, LSTM) with interpretation guidance. Collapsed by default to keep tab uncluttered.

## All features verified working

| Feature | AAPL result | Notes |
|---|---|---|
| RF Direction Signal | 69% Bullish | Feature importance chart rendered |
| Market Regime | HMM Bear / K-Means Bull (diverge) | Timeline chart rendered |
| Credit Risk | Fallback message | Expected — AAPL has single-class label variation |
| LSTM Direction Signal | 59% Bullish (agree) | Loss curve rendered |
| PCA Decomposition | Scree + heatmap | Market Factor / Sector Tilt / Curvature |
