---
phase: 28
slug: i-want-to-enhance-the-stock-details-tab
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-06
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` or `tests/` directory |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 28-01-01 | 01 | 1 | backend: price_history endpoint | integration | `pytest tests/test_integration_routes.py::test_price_history -v` | ❌ W0 | ⬜ pending |
| 28-01-02 | 01 | 1 | backend: recommendationKey scraper patch | unit | `pytest tests/test_unit_yahoo_scraper.py::test_recommendation_key -v` | ❌ W0 | ⬜ pending |
| 28-02-01 | 02 | 2 | frontend: sub-tab HTML structure | manual | browser inspection | n/a | ⬜ pending |
| 28-02-02 | 02 | 2 | frontend: sessionStorage persistence | manual | browser DevTools check | n/a | ⬜ pending |
| 28-03-01 | 03 | 3 | frontend: price chart lazy render | manual | browser network tab inspection | n/a | ⬜ pending |
| 28-03-02 | 03 | 3 | frontend: analyst range bar renders | manual | visual check in browser | n/a | ⬜ pending |
| 28-04-01 | 04 | 4 | frontend: color coding on metrics | manual | visual check in browser | n/a | ⬜ pending |
| 28-04-02 | 04 | 4 | frontend: CSS tooltips on hover | manual | hover test in browser | n/a | ⬜ pending |
| 28-05-01 | 05 | 5 | integration: Deep Analysis sub-tab modules render | manual | expand ticker card, check Deep Analysis tab | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_integration_routes.py` — add test for `GET /api/price_history?ticker=AAPL&period=1mo` (200 status, JSON keys: open/high/low/close/volume, at least 1 row)
- [ ] `tests/test_unit_yahoo_scraper.py` — add test for `recommendationKey` field extraction with mock yfinance info dict containing the field and one without (null safety)

*Existing pytest infrastructure covers general test needs; only two new test stubs needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Sub-tab HTML renders 5 tabs per ticker card | Sub-tab structure | DOM structure, no automated HTML assertion | Expand ticker card, verify 5 sub-tab buttons visible |
| Sub-tab sessionStorage persistence | Sub-tab persistence | Requires browser session state | Switch tabs, refresh page, verify active tab restored |
| Price chart renders after first Overview tab click | Lazy load | Requires browser Plotly rendering | Click Overview tab, verify candlestick chart appears |
| Volume subplot visible below candlestick | Plotly subplot | Visual rendering check | Inspect chart for 2 row layout |
| Timeframe toggle buttons (1M/3M/6M/1Y) work | Price chart timeframes | Network request + re-render | Click each button, verify chart updates |
| Analyst range bar SVG renders correctly | Analyst visualization | SVG/CSS rendering | Expand ticker, verify horizontal bar with price dot |
| Consensus badge shows correct label | Consensus display | Text rendering | Check badge shows Buy/Hold/Sell/Strong Buy etc. |
| Color coding on P/E, ROE, Debt/Equity etc. | Metric color coding | CSS class visual check | Inspect metric cells for expected colors |
| Tooltip appears on hover over metric label | CSS tooltips | Browser hover interaction | Hover over P/E label, verify tooltip text appears |
| Deep Analysis modules (HealthScore, DCF, etc.) render inside sub-tab | renderIntoGroup integration | JS module injection check | Click Deep Analysis tab, verify all modules appear |
| Existing features unbroken after refactor | Non-regression | Full E2E check | Scrape a ticker, verify all tabs and features work |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
