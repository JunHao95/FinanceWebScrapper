---
phase: 03-frontend-wiring
plan: 01
subsystem: ui
tags: [plotly, hmm, regime-detection, flask, javascript, yfinance]

# Dependency graph
requires:
  - phase: 02-backend-completeness
    provides: RegimeDetector.fit() with filtered_probs_full array; HMM backend validated correct
provides:
  - /api/regime_detection accepting ticker + start_date + end_date with dates/prices/regime_sequence in response
  - runRegimeDetection() rendering two Plotly charts (probability area + regime-shaded price)
  - Regime Detection sub-tab with start/end date pickers wired to live HMM backend
affects:
  - 03-02 (options pricing wiring can reference this chart pattern)
  - 03-03 (interest rate model wiring)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Flat API response: top-level dates/prices/regime_sequence aligned arrays for Plotly"
    - "Dual calling convention: new ticker+dates API alongside backward-compatible tickers+days"
    - "Plotly vrect shading via shapes array built from regime_sequence 0/1 transition scan"
    - "innerHTML purge before Plotly.newPlot prevents double traces on re-run"

key-files:
  created: []
  modified:
    - webapp.py
    - templates/index.html
    - static/js/stochasticModels.js

key-decisions:
  - "Keep backward-compatible legacy 'regime' nested field in response while adding new flat fields for Plotly"
  - "Derive regime_sequence from filtered_probs as [1 if p >= 0.5 else 0] — threshold-based, consistent with plan spec"
  - "Identify stressed column in filtered_probs_full by comparing last row to reported current_probabilities.stressed"
  - "Replace regimeDays input with regimeStartDate + regimeEndDate for precise date range control (SPY March 2020 demo use case)"

patterns-established:
  - "Chart containers injected into resultsDiv.innerHTML before Plotly.newPlot to enable clean re-runs"
  - "Stressed regime shading: scan regime_sequence for 0->1 and 1->0 transitions, push rect shapes"

requirements-completed: [REGIME-01, REGIME-02, REGIME-03, REGIME-04, REGIME-05]

# Metrics
duration: 15min
completed: 2026-03-06
---

# Phase 3 Plan 1: Regime Detection Frontend Summary

**HMM regime detection wired end-to-end: /api/regime_detection now returns dates/prices/regime_sequence, and the UI renders a P(Stressed) area chart plus a price chart with red stressed-period shading**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-06T00:00:00Z
- **Completed:** 2026-03-06T00:15:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Patched `webapp.py` regime_detection_endpoint to accept `ticker`+`start_date`+`end_date` and return aligned `dates`, `prices`, `filtered_probs`, `regime_sequence` arrays
- Replaced `regimeDays` input with `regimeStartDate` and `regimeEndDate` date pickers in the Regime Detection sub-tab
- Replaced old table-based `runRegimeDetection()` with Plotly dual-chart rendering: probability area chart + regime-shaded price chart

## Task Commits

Each task was committed atomically:

1. **Task 1: Patch webapp.py regime endpoint** - `6ac46b2` (feat)
2. **Task 2: Wire tab inputs and Plotly charts** - `2ec5d1d` (feat)

## Files Created/Modified
- `webapp.py` - Extended regime_detection_endpoint: new calling convention, yfinance data fetch for dates/prices, regime_sequence derivation, backward-compatible nested 'regime' field retained
- `templates/index.html` - Replaced regimeDays input with regimeStartDate + regimeEndDate date inputs (default 2019-01-01 to 2021-12-31)
- `static/js/stochasticModels.js` - Replaced old tabular runRegimeDetection() with Plotly area chart (P(Stressed)) and vrect-shaded price chart

## Decisions Made
- Retained backward-compatible `regime` nested field so any existing callers are unbroken
- Identified stressed column in filtered_probs_full by comparing last row values to reported `current_probabilities.stressed` value — avoids hardcoding internal state index
- Used `p >= 0.5` threshold for `regime_sequence` derivation (consistent with plan spec)
- Date pickers default to 2019-01-01 / 2021-12-31 so SPY March 2020 RISK_OFF is visible immediately on first run

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Flask server runs on port 5173 (not 5000 as shown in plan's verification command) — adjusted verification curl accordingly; functionality is identical

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Regime Detection tab fully wired and interactive; SPY 2019-2021 shows red shading in Q1 2020
- API returns dates/prices/regime_sequence; pattern established for other stochastic model tabs
- Ready for 03-02 (interest rate model / yield curve wiring)

---
*Phase: 03-frontend-wiring*
*Completed: 2026-03-06*
