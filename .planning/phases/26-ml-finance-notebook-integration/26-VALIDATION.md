---
phase: 26
slug: ml-finance-notebook-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-03
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini / conftest.py |
| **Quick run command** | `pytest tests/test_unit_ml_signals.py -v` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_unit_ml_signals.py -v`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 26-01-01 | 01 | 1 | ML-SIGNALS | unit | `pytest tests/test_unit_ml_signals.py::test_random_forest -v` | ❌ W0 | ⬜ pending |
| 26-01-02 | 01 | 1 | ML-SIGNALS | unit | `pytest tests/test_unit_ml_signals.py::test_gradient_boost -v` | ❌ W0 | ⬜ pending |
| 26-01-03 | 01 | 1 | ML-SIGNALS | unit | `pytest tests/test_unit_ml_signals.py::test_kmeans -v` | ❌ W0 | ⬜ pending |
| 26-01-04 | 01 | 1 | ML-SIGNALS | unit | `pytest tests/test_unit_ml_signals.py::test_lstm -v` | ❌ W0 | ⬜ pending |
| 26-01-05 | 01 | 1 | ML-SIGNALS | unit | `pytest tests/test_unit_ml_signals.py::test_credit_risk -v` | ❌ W0 | ⬜ pending |
| 26-02-01 | 02 | 2 | ML-ROUTE | integration | `pytest tests/test_integration_routes.py::test_ml_signals_route -v` | ❌ W0 | ⬜ pending |
| 26-02-02 | 02 | 2 | ML-ROUTE | integration | `pytest tests/test_integration_routes.py::test_ml_signals_invalid -v` | ❌ W0 | ⬜ pending |
| 26-03-01 | 03 | 3 | ML-UI | manual | Browser tab smoke test | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_unit_ml_signals.py` — stubs for all five ML feature functions
- [ ] `tests/test_integration_routes.py` — extend with ml_signals route tests

*Existing conftest.py covers shared fixtures — no new conftest needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ML Signals tab renders in browser | ML-UI | Frontend rendering requires browser | Open app, click ML Signals tab, verify chart/table renders for each feature |
| LSTM env gate (cloud) | ML-ENV | Cannot reproduce Render env locally | Verify `KERAS_AVAILABLE=False` path runs without error in unit test with mocked env |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
