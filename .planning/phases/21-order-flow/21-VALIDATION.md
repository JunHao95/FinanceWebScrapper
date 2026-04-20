---
phase: 21
slug: order-flow
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-12
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — pytest auto-discovers `tests/` |
| **Quick run command** | `pytest tests/test_trading_indicators.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_trading_indicators.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 0 | FLOW-01 | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow -x -q` | ❌ W0 | ⬜ pending |
| 21-02-01 | 02 | 1 | FLOW-01 | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_no_nan_in_cumulative_delta -x` | ❌ W0 | ⬜ pending |
| 21-02-02 | 02 | 1 | FLOW-01 | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_epsilon_guard_on_zero_range -x` | ❌ W0 | ⬜ pending |
| 21-02-03 | 02 | 1 | FLOW-01 | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_order_flow_keys -x` | ❌ W0 | ⬜ pending |
| 21-03-01 | 03 | 1 | FLOW-02 | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_divergence_detected_opposite_slopes -x` | ❌ W0 | ⬜ pending |
| 21-03-02 | 03 | 1 | FLOW-02 | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_no_divergence_same_sign_slopes -x` | ❌ W0 | ⬜ pending |
| 21-04-01 | 04 | 1 | FLOW-03 | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_imbalance_candle_annotation -x` | ❌ W0 | ⬜ pending |
| 21-04-02 | 04 | 1 | FLOW-03 | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_no_annotation_normal_candle -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_trading_indicators.py` — add `TestComputeOrderFlow` class with stubs for FLOW-01, FLOW-02, FLOW-03

*File exists — class must be appended. No new test files needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Delta bars render green/red in browser | FLOW-01 | Visual chart rendering | Load ticker, inspect Order Flow panel — bars should be green for positive delta, red for negative |
| Cumulative delta overlay visible | FLOW-01 | Visual chart rendering | Verify white/light-grey line traces across all bars on right axis |
| Divergence badge shows correct message | FLOW-02 | DOM/badge rendering | Trigger divergence condition — badge should show `⚠ Volume Divergence — price slope: X, vol slope: Y` |
| Imbalance annotations visible on chart | FLOW-03 | Visual annotation placement | Confirm ▲ above bullish and ▼ below bearish imbalance bars |
| Order Flow panel below AVWAP panel | FLOW-01 | Layout ordering | Panel sequence: VP → AVWAP → Order Flow within ticker card |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
