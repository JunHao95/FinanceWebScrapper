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

### Active

- [ ] One-click analysis: ticker symbols as the only required input — sources, analytics, and regime/MDP run automatically
- [ ] Advanced settings (data sources, API keys) collapsed behind a toggle — visible only when needed
- [ ] Portfolio allocation supports both % Weight mode and Value mode (auto-computed weights with live %-display)
- [ ] After scrape completes, Regime Detection and Portfolio MDP run automatically with inline results
- [ ] Portfolio Health Card summarises VaR, Sharpe, and regime per ticker at the top of results

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

## Current Milestone: v2.0 One-Click Analysis Dashboard

**Goal:** From ticker symbols to full analysis in one click — smart defaults eliminate all required configuration beyond the ticker input.

**Target features:**
- Collapsed advanced settings (data sources, API keys hidden by default)
- Portfolio allocation with % Weight / Value mode toggle + currency selector
- Auto-run Regime Detection and Portfolio MDP after scrape completes
- Portfolio Health Card with VaR, Sharpe, regime labels shown at top of results

---
*Last updated: 2026-03-08 after v2.0 milestone start*
