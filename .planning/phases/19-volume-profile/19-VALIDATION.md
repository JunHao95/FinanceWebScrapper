---
phase: 19
slug: volume-profile
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-10
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | existing `pytest.ini` / `setup.cfg` |
| **Quick run command** | `pytest tests/test_trading_indicators.py -v` |
| **Full suite command** | `pytest tests/ -q -m "not slow"` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_trading_indicators.py -v`
- **After every plan wave:** Run `pytest tests/ -q -m "not slow"`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 19-01-01 | 01 | 1 | VPROF-01 | unit | `pytest tests/test_trading_indicators.py::TestComputeVolumeProfile::test_volume_profile_keys -v` | ❌ W0 | ⬜ pending |
| 19-01-02 | 01 | 1 | VPROF-01 | unit | `pytest tests/test_trading_indicators.py::TestComputeVolumeProfile::test_poc_inside_price_range -v` | ❌ W0 | ⬜ pending |
| 19-01-03 | 01 | 1 | VPROF-02 | unit | `pytest tests/test_trading_indicators.py::TestComputeVolumeProfile::test_value_area_coverage -v` | ❌ W0 | ⬜ pending |
| 19-01-04 | 01 | 1 | VPROF-03 | unit | `pytest tests/test_trading_indicators.py::TestComputeVolumeProfile::test_bin_width_usd -v` | ❌ W0 | ⬜ pending |
| 19-01-05 | 01 | 1 | VPROF-01 | unit | `pytest tests/test_trading_indicators.py::TestTradingIndicatorsRoute::test_route_includes_volume_profile_traces -v` | ❌ W0 | ⬜ pending |
| 19-02-01 | 02 | 2 | VPROF-01 | manual | Open browser, confirm horizontal histogram renders with POC/VAH/VAL visible | N/A | ⬜ pending |
| 19-02-02 | 02 | 2 | VPROF-02 | manual | Confirm 70% value area is shaded and badge shows price inside/outside | N/A | ⬜ pending |
| 19-02-03 | 02 | 2 | VPROF-03 | manual | Confirm bin width USD shown in chart subtitle | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_trading_indicators.py` — add `TestComputeVolumeProfile` class (already exists, just add class)
- [ ] No new test files needed — extends Phase 18 test file

*Existing pytest infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Horizontal histogram renders with shared y-axis | VPROF-01 | Requires browser Plotly rendering | Open app, run ticker, click Trading Indicators tab, confirm histogram is horizontal |
| VAH/VAL shaded value area visible | VPROF-02 | Visual rendering check | Confirm shaded zone between VAH and VAL lines |
| Price-in-value-area badge displayed | VPROF-02 | DOM element check | Confirm badge reads "Price inside value area" or "Price outside value area" |
| Bin width USD shown in subtitle | VPROF-03 | Chart annotation check | Confirm subtitle/annotation shows bin width in USD |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
