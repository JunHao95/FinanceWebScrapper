---
phase: 20
slug: anchored-vwap
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-12
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini / setup.cfg (existing) |
| **Quick run command** | `python -m pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap -x -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 1 | AVWAP-01 | unit | `python -m pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap::test_52wk_high_low_avwap_computed -x -q` | ❌ W0 | ⬜ pending |
| 20-01-02 | 01 | 1 | AVWAP-02 | unit | `python -m pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap::test_earnings_anchor_available -x -q` | ❌ W0 | ⬜ pending |
| 20-01-03 | 01 | 1 | AVWAP-02 | unit | `python -m pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap::test_earnings_anchor_unavailable -x -q` | ❌ W0 | ⬜ pending |
| 20-01-04 | 01 | 1 | AVWAP-03 | unit | `python -m pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap::test_convergence_detection -x -q` | ❌ W0 | ⬜ pending |
| 20-01-05 | 01 | 1 | AVWAP-01 | unit | `python -m pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap::test_short_lookback_uses_365d_anchor -x -q` | ❌ W0 | ⬜ pending |
| 20-02-01 | 02 | 2 | AVWAP-01 | integration | `python -m pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap -x -q` | ❌ W0 | ⬜ pending |
| 20-02-02 | 02 | 2 | AVWAP-03 | manual | See Manual-Only below | N/A | ⬜ pending |
| 20-02-03 | 02 | 2 | AVWAP-02 | manual | See Manual-Only below | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_trading_indicators.py` — add `TestComputeAnchoredVwap` class with stubs for AVWAP-01/02/03
- [ ] Stubs: `test_52wk_high_low_avwap_computed`, `test_earnings_anchor_available`, `test_earnings_anchor_unavailable`, `test_convergence_detection`, `test_short_lookback_uses_365d_anchor`
- [ ] Existing fixtures in `tests/test_trading_indicators.py` can be reused for mock OHLCV data

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Right-edge Plotly annotations visible and correctly positioned | AVWAP-03 | Visual layout check — can't automate annotation pixel position | Open app, search a ticker, switch to AVWAP tab, verify blue/orange/purple labels appear to the right of the chart axis |
| Convergence badge text correct | AVWAP-03 | UI string format verification | Find a ticker where two AVWAPs are within 0.3% of current price; verify badge shows `⚠ Convergence: [name] AVWAP within 0.3% of current price at $X.XX` |
| Earnings anchor unavailable note | AVWAP-02 | Requires real ETF (GLD/TLT) to trigger | Search GLD or TLT, verify `Earnings anchor unavailable — only 52-wk high & low lines shown.` note appears below chart |
| Chart renders two AVWAP lines for ETF (no earnings) | AVWAP-02 | Requires live data + UI | Verify chart still shows 52-wk high and low lines when earnings unavailable |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
