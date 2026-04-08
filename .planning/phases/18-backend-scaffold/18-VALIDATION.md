---
phase: 18
slug: backend-scaffold
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-08
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` or `setup.cfg` (existing) |
| **Quick run command** | `pytest tests/test_trading_indicators.py -v` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_trading_indicators.py -v`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | SC-2 | unit | `pytest tests/test_trading_indicators.py::test_fetch_ohlcv_returns_ohlcv_dataframe -v` | ❌ W0 | ⬜ pending |
| 18-01-02 | 01 | 1 | SC-2 | unit | `pytest tests/test_trading_indicators.py::test_fetch_ohlcv_uses_ticker_history -v` | ❌ W0 | ⬜ pending |
| 18-01-03 | 01 | 1 | SC-1 | unit | `pytest tests/test_trading_indicators.py::test_route_returns_200 -v` | ❌ W0 | ⬜ pending |
| 18-01-04 | 01 | 1 | SC-1 | unit | `pytest tests/test_trading_indicators.py::test_route_returns_placeholder_keys -v` | ❌ W0 | ⬜ pending |
| 18-02-01 | 02 | 2 | SC-3 | manual | Open browser DevTools Network tab, load ticker, confirm JS calls route | N/A | ⬜ pending |
| 18-02-02 | 02 | 2 | SC-4 | manual | Confirm no console errors in browser DevTools | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_trading_indicators.py` — stubs for SC-1 and SC-2 (route 200 + fetch function unit tests)
- [ ] Existing `tests/conftest.py` — reuse shared fixtures if present

*All test infrastructure uses existing pytest + unittest.mock patterns from `test_peer_comparison.py`.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Browser network trace shows JS calling route | SC-4 | Requires real browser DevTools inspection | Open app, open DevTools Network tab, search ticker, confirm `GET /api/trading_indicators` appears with 200 status and valid JSON |
| No console errors when tab loads | SC-4 | Requires real browser JS runtime | Open app, open DevTools Console tab, navigate to Trading Indicators tab, confirm no errors |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
