---
phase: 23
slug: end-to-end-test-suite-design
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-17
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.4 |
| **Config file** | None — add pytest.ini or pyproject.toml [tool.pytest.ini_options] in Wave 0 |
| **Quick run command** | `pytest -m "unit or integration" -q --tb=short` |
| **Full suite command** | `pytest -q` or `make test` |
| **Estimated runtime** | ~30 seconds (unit + integration), ~120 seconds (full with E2E) |

---

## Sampling Rate

- **After every task commit:** Run `pytest -m "unit or integration" -q --tb=short`
- **After every plan wave:** Run `pytest -q` (full suite including regression; skip E2E unless explicitly triggered)
- **Before `/gsd:verify-work`:** Full suite must be green, including E2E
- **Max feedback latency:** 30 seconds (unit + integration)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 23-01-01 | 01 | 1 | TEST-01 | manual | n/a — document in conftest.py module docstring | ❌ W0 | ⬜ pending |
| 23-01-02 | 01 | 1 | TEST-02 | smoke | `make test` | ❌ W0 | ⬜ pending |
| 23-02-01 | 02 | 1 | TEST-03 | unit | `pytest -m unit -q` | ❌ W0 | ⬜ pending |
| 23-03-01 | 03 | 2 | TEST-04 | integration | `pytest -m integration -q` | Partial | ⬜ pending |
| 23-04-01 | 04 | 2 | TEST-05 | regression | `pytest -m regression -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `Makefile` — targets: test, test-unit, test-integration, test-regression, test-e2e
- [ ] `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` — register markers, set testpaths = tests
- [ ] Install: `pip install pytest-playwright pytest-flask responses && playwright install chromium`
- [ ] Update `requirements.txt` with new dev dependencies
- [ ] Extend `tests/conftest.py` — add unit/integration/regression/e2e marker registrations + Flask live_server threading fixture
- [ ] `tests/fixtures/volume_profile_ohlcv.csv` — generate frozen OHLCV fixture
- [ ] `tests/fixtures/order_flow_ohlcv.csv` — generate frozen order flow fixture
- [ ] `tests/fixtures/heston_market_prices.json` — generate frozen Heston fixture

*Existing infrastructure covers partial integration tests (7 routes) but needs expansion.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Test plan document covers all critical flows | TEST-01 | Document review, not code | Read conftest.py docstring + test plan markdown; confirm all 5 flows listed |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
