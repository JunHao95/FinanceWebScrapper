---
phase: 24
slug: i-want-to-integrate-footprint-trading-indicator
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-21
---

# Phase 24 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini / pyproject.toml (existing) |
| **Quick run command** | `pytest tests/test_unit_footprint.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_unit_footprint.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 24-01-01 | 01 | 0 | Fixture setup | fixture | `pytest tests/test_unit_footprint.py -x -q` | ❌ W0 | ⬜ pending |
| 24-01-02 | 01 | 1 | fetch_intraday | unit | `pytest tests/test_unit_footprint.py::test_fetch_intraday -x -q` | ❌ W0 | ⬜ pending |
| 24-01-03 | 01 | 1 | compute_footprint | unit | `pytest tests/test_unit_footprint.py::test_compute_footprint -x -q` | ❌ W0 | ⬜ pending |
| 24-02-01 | 02 | 2 | /api/footprint route | integration | `pytest tests/test_integration_routes.py -k footprint -x -q` | ❌ W0 | ⬜ pending |
| 24-02-02 | 02 | 2 | composite bias 5-voice | unit | `pytest tests/test_unit_footprint.py::test_composite_bias -x -q` | ❌ W0 | ⬜ pending |
| 24-03-01 | 03 | 3 | JS parallel fetch | manual | Browser console test | N/A | ⬜ pending |
| 24-03-02 | 03 | 3 | Heatmap render | manual | Visual browser check | N/A | ⬜ pending |
| 24-03-03 | 03 | 3 | Grid 3-col layout | manual | Visual browser check | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_unit_footprint.py` — stubs for fetch_intraday, compute_footprint, composite bias
- [ ] `tests/fixtures/footprint_15m_ohlcv.csv` — deterministic fixture (one-time live fetch or hand-crafted)
- [ ] `tests/test_integration_routes.py` — stub for `/api/footprint` route tests

*Existing pytest infrastructure covers remaining requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Heatmap renders with diverging colorscale | CONTEXT: go.Heatmap visual | Plotly canvas rendering not testable in pytest | Open browser, load ticker, verify footprint panel appears with green/red cells |
| Grid expands to 3-column layout | CONTEXT: ti-2x2-grid → 1fr 1fr 1fr | CSS layout requires browser | Inspect element, confirm grid-template-columns = 1fr 1fr 1fr |
| Failure placeholder shows for unsupported ticker | CONTEXT: failure mode | Requires live ticker without intraday | Test with a mutual fund ticker, verify grey placeholder |
| Session cache clears footprint on clearSession() | CONTEXT: TradingIndicators.clearSession() | JS state management | Open DevTools, trigger clearSession, verify cache entry removed |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
