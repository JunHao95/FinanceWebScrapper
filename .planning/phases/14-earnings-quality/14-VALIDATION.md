---
phase: 14
slug: earnings-quality
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) + manual browser checks (frontend) |
| **Config file** | pytest.ini or pyproject.toml (existing) |
| **Quick run command** | `python -m pytest tests/ -x -q 2>&1 | tail -20` |
| **Full suite command** | `python -m pytest tests/ -v 2>&1 | tail -40` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q 2>&1 | tail -20`
- **After every plan wave:** Run `python -m pytest tests/ -v 2>&1 | tail -40`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 0 | QUAL-02, QUAL-03 | unit | `python -m pytest tests/test_earnings_quality.py::test_scraper_fields -x -q` | ❌ W0 | ⬜ pending |
| 14-01-02 | 01 | 1 | QUAL-01, QUAL-02, QUAL-03 | unit | `python -m pytest tests/test_earnings_quality.py::test_compute_metrics -x -q` | ❌ W0 | ⬜ pending |
| 14-01-03 | 01 | 1 | QUAL-04 | unit | `python -m pytest tests/test_earnings_quality.py::test_consistency_flag -x -q` | ❌ W0 | ⬜ pending |
| 14-01-04 | 01 | 1 | QUAL-05 | unit | `python -m pytest tests/test_earnings_quality.py::test_insufficient_data -x -q` | ❌ W0 | ⬜ pending |
| 14-02-01 | 02 | 2 | QUAL-01 | manual | Open browser, scrape ticker, verify colour-coded label in Deep Analysis | N/A | ⬜ pending |
| 14-02-02 | 02 | 2 | QUAL-02, QUAL-03 | manual | Verify accruals ratio and cash conversion ratio show 2 decimal places | N/A | ⬜ pending |
| 14-02-03 | 02 | 2 | QUAL-04 | manual | Verify Consistent/Volatile flag with tooltip text | N/A | ⬜ pending |
| 14-02-04 | 02 | 2 | QUAL-05 | manual | Use ticker with missing OCF — verify "Insufficient Data" renders, no JS error | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_earnings_quality.py` — stubs for QUAL-01 through QUAL-05
- [ ] Fixtures: mock payload with OCF + Net Income + Total Assets + EPS fields; mock payload with missing OCF

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Colour-coded quality label renders in DOM | QUAL-01 | Frontend rendering, no JS test harness | Scrape any ticker → expand Deep Analysis → confirm label "High/Medium/Low" with green/yellow/red colour |
| Accruals ratio displayed to 2 decimal places | QUAL-02 | Visual formatting check | Confirm numeric value like "-0.05" appears in earnings quality section |
| Cash conversion ratio displayed to 2 decimal places | QUAL-03 | Visual formatting check | Confirm numeric value like "1.23" appears in earnings quality section |
| Consistent/Volatile flag with tooltip | QUAL-04 | Tooltip content is runtime DOM | Hover over flag label — confirm tooltip/title text explains criterion |
| "Insufficient Data" when OCF absent, no JS error | QUAL-05 | Requires specific scrape scenario | Open DevTools console, scrape a ticker known to lack OCF data, confirm no errors and section shows "Insufficient Data" |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
