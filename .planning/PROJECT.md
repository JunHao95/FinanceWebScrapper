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

- [ ] Markov Chain and Markov Decision Process models running in UI with validated results
- [ ] Credit transition models (Markov-based) wired to frontend with charts
- [ ] Regime detection (bull/bear/crisis state identification) with visual output
- [ ] Interest rate models (stochastic) with yield curve visualization
- [ ] Fourier-based option pricer and model calibration exposed in UI
- [ ] All stochastic model results validated against known benchmarks or test cases
- [ ] Machine learning in finance section (next semester module)

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

---
*Last updated: 2026-03-03 after initialization*
