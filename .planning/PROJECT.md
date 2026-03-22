# MFE Showcase Web App

## What This Is

An interactive web application that showcases quantitative finance skills built semester-by-semester through a Master in Financial Engineering program. Each section of the app corresponds to a completed module — users can interact with live financial models, view visualizations, and inspect clean implementations. The app grows with the program.

## Core Value

Every completed MFE module becomes a working, interactive demo that a recruiter can run and a peer can learn from.

## Requirements

### Validated

- ✓ Options pricing with Black-Scholes, Greeks, and interactive parameters — existing
- ✓ Portfolio analysis with stress testing and scenario parameters — existing
- ✓ Financial analytics (ratios, metrics, ticker analysis) — existing

### Validated

- ✓ One-click analysis: ticker symbols as the only required input — v2.0/Phase 6
- ✓ Advanced settings (data sources, API keys) collapsed behind a toggle — v2.0/Phase 6
- ✓ Portfolio allocation supports both % Weight mode and Value mode — v2.0/Phase 6
- ✓ After scrape completes, Regime Detection and Portfolio MDP run automatically — v2.0/Phase 7
- ✓ Portfolio Health Card summarises VaR, Sharpe, and regime per ticker — v2.0/Phase 8
- ✓ Chatbot widget with QuantAssistant + FinancialAnalyst personas — v2.0/Phase 10–10.1
- ✓ Chatbot context wired to scraped page data — v2.0/Phase 12

### Active

- [ ] Financial Health Score: A–F composite grade (liquidity, leverage, profitability, growth) displayed on each ticker card
- [ ] Earnings Quality: accruals ratio, cash conversion, consistency flag per ticker
- [ ] DCF Valuation: FCF-based intrinsic value estimate with user-overridable WACC/growth inputs
- [ ] Peer Comparison: percentile ranks for P/E, P/B, ROE, operating margin vs. 5–10 sector peers from Finviz

### Out of Scope

- Mobile app — web-first, modular tab structure is the priority
- Real-time market data feeds — static/fetched data sufficient for demos
- User authentication — this is a showcase, not a multi-user platform
- Rigorous production hardening — academic demo context, not production SaaS

## Context

- Built with Python (Flask/webapp.py) backend + vanilla JS frontend
- Modular tab-per-module structure in the UI (each MFE module = one section)
- Existing modules: Options Pricing, Portfolio Analysis, Financial Analytics
- Current WIP: Stochastic Models section (Markov chains, interest rate models, credit transitions, regime detection, Fourier pricing, model calibration) — backend files written, partially wired to frontend
- Next planned module: Machine Learning in Finance (next semester)
- ~3,200 lines of uncommitted work in progress at project initialization

## Constraints

- **Tech Stack**: Python backend (Flask), vanilla JS frontend — no framework changes
- **Structure**: Tab-per-module — each semester's module gets its own section
- **Validation**: Model outputs must be validated against benchmarks before a module is considered complete
- **Scope**: One active module at a time — complete current before starting next

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Separate tab per module | Matches program structure, easy for reviewers to navigate to specific domain | — Pending |
| Validate model results before shipping | Showcase app must be correct, not just functional | — Pending |
| Python backend for all models | MFE work is Python-native, keeps implementation authentic | — Pending |

## Current Milestone: v2.1 Deeper Stock Analysis

**Goal:** Expand each stock card with a "Deep Analysis" group containing four new analysis modules — financial health grading, earnings quality scoring, DCF intrinsic value estimation, and peer percentile comparison.

**Target features:**
- Financial Health Score (A–F grade from liquidity, leverage, profitability, growth)
- Earnings Quality (accruals ratio, cash conversion, consistency flag)
- DCF Valuation (FCF-based intrinsic value with user-overridable WACC/growth)
- Peer Comparison (percentile ranks vs. sector peers from Finviz)

---
*Last updated: 2026-03-22 after v2.1 milestone start*
