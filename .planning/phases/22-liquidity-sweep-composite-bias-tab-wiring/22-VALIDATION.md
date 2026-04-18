---
phase: 22
slug: liquidity-sweep-composite-bias-tab-wiring
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-18
---

# Phase 22 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini or pyproject.toml (existing) |
| **Quick run command** | `pytest tests/test_phase22.py -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_phase22.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 22-01-01 | 01 | 1 | SWEEP-01 | unit | `pytest tests/test_trading_indicators.py::TestComputeLiquiditySweep -x -q` | ❌ W0 | ⬜ pending |
| 22-01-02 | 01 | 1 | SWEEP-02 | unit | `pytest tests/test_trading_indicators.py::TestComputeLiquiditySweep::test_lookahead_regression -x -q` | ❌ W0 | ⬜ pending |
| 22-01-03 | 01 | 1 | SWEEP-01 | unit | `pytest tests/test_trading_indicators.py::TestComputeLiquiditySweep::test_no_swings_guard -x -q` | ❌ W0 | ⬜ pending |
| 22-01-04 | 01 | 1 | BIAS-01 | unit | `pytest tests/test_trading_indicators.py::TestComputeCompositeBias -x -q` | ❌ W0 | ⬜ pending |
| 22-01-05 | 01 | 1 | BIAS-02 | unit | `pytest tests/test_trading_indicators.py::TestComputeCompositeBias::test_failed_module_grey -x -q` | ❌ W0 | ⬜ pending |
| 22-01-06 | 01 | 1 | BIAS-03 | unit | `pytest tests/test_trading_indicators.py::TestComputeCompositeBias::test_dissenter_rationale -x -q` | ❌ W0 | ⬜ pending |
| 22-03-01 | 02 | 2 | TIND-01 | manual | — | — | ⬜ pending |
| 22-03-02 | 02 | 2 | TIND-02 | manual | — | — | ⬜ pending |
| 22-03-03 | 02 | 2 | TIND-03 | manual | — | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_trading_indicators.py` — classes `TestComputeLiquiditySweep` and `TestComputeCompositeBias` for SWEEP-01, SWEEP-02, SWEEP-03, BIAS-01, BIAS-02, BIAS-03 (written TDD-style in Plan 22-01 before implementation)
- [ ] Fixtures: synthetic OHLCV DataFrame with known swing highs/lows for deterministic testing

*Existing infrastructure (pytest) covers the framework; only the test file is new.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Trading Indicators tab button visible in tab bar | TIND-01 | DOM/UI check | Open app, scrape 1 ticker, verify "Trading Indicators" tab appears in results tab bar |
| 2×2 Plotly grid renders for all tickers without re-scrape | TIND-02 | Browser rendering | Click Trading Indicators tab after scrape, verify 4 panels render for each ticker card |
| Lookback dropdown changes clear cache and re-fetch | TIND-03 | Session state | Change dropdown from 90→30, verify network requests fire and charts update |
| Sweep markers appear on sweep candles | SWEEP-02 | Visual | After sweep detection, inspect chart for ▲/▼ markers on sweep candles |
| Dashed horizontal lines at swept price | SWEEP-02 | Visual | Verify dashed lines in Plotly chart at swept_price levels |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
