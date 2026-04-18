---
phase: 22-liquidity-sweep-composite-bias-tab-wiring
plan: 01
status: complete
completed_date: 2026-04-19
tests_passed: true
commit: 5085519
---

## What was built
Replaced `compute_liquidity_sweep` and `compute_composite_bias` stubs in `src/analytics/trading_indicators.py` with real implementations. Added `_adaptive_n` helper. Updated `/api/trading_indicators` Flask route in `webapp.py` to call real implementations and build `composite_bias` after all four indicators resolve. Added 16 TDD tests across `TestComputeLiquiditySweep` (8 tests) and `TestComputeCompositeBias` (8 tests). Total suite: 39 tests, all green.

## one_liner
Backend liquidity sweep + composite bias implemented with TDD — 16 new tests + 23 existing all green.

## Key decisions
- Loop bound `range(n, len-n)` prevents look-ahead bias (SWEEP-02 mandate)
- `no_swings` status excluded from composite bias denominator
- AVWAP 'between' maps to neutral; VP 'inside' maps to bullish
- Route builds composite_bias inline after all four indicator calls resolve
