---
phase: 8
slug: portfolio-health-summary-card
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — run from project root |
| **Quick run command** | `pytest tests/test_portfolio_sharpe.py -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_portfolio_sharpe.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 8-01-01 | 01 | 0 | HEALTH-01 | unit | `pytest tests/test_portfolio_sharpe.py -x -q` | ❌ W0 | ⬜ pending |
| 8-01-02 | 01 | 1 | HEALTH-01 | unit | `pytest tests/test_portfolio_sharpe.py -x -q` | ❌ W0 | ⬜ pending |
| 8-02-01 | 02 | 2 | HEALTH-01 | manual | open browser, confirm card shows VaR + Sharpe | — | ⬜ pending |
| 8-02-02 | 02 | 2 | HEALTH-02 | manual | click metric in card, verify tab switches | — | ⬜ pending |
| 8-02-03 | 02 | 2 | HEALTH-03 | manual | single-ticker run, confirm correlation/PCA absent | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_portfolio_sharpe.py` — stubs/tests for HEALTH-01 backend route (Flask test client)
- [ ] `tests/conftest.py` — Flask test client fixture (verify if already exists; create if not)

*Wave 0 must be complete before plan waves execute.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Card appears above tab nav with VaR, Sharpe, regime badges | HEALTH-01 | Browser DOM interaction, no automation layer in project | Run multi-ticker scrape, confirm `#portfolioHealthCard` visible above `.tabs-container` |
| Clicking a metric switches to correct Analytics tab | HEALTH-02 | Requires JS event + DOM interaction | Click VaR metric → confirm Analytics tab active; click Sharpe → same |
| Single-ticker: correlation/PCA absent from card | HEALTH-03 | Conditional DOM rendering check | Run single-ticker scrape, inspect card HTML for absence of correlation/PCA elements |
| Regime badges update from "Analyzing..." to final labels | HEALTH-01 | Async auto-run timing | Watch card slots during auto-run; confirm transition from placeholder to colored badge |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
