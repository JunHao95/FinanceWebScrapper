---
phase: 13
slug: financial-health-score
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing, `tests/` directory) |
| **Config file** | `setup.py` / `pytest.ini` (existing) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | FHLTH-01 | manual smoke | n/a — browser visual | ❌ manual only | ⬜ pending |
| 13-01-02 | 01 | 1 | FHLTH-02 | manual smoke | n/a — browser interaction | ❌ manual only | ⬜ pending |
| 13-01-03 | 01 | 1 | FHLTH-03 | manual smoke | n/a — browser visual | ❌ manual only | ⬜ pending |
| 13-01-04 | 01 | 1 | FHLTH-04 | manual smoke | n/a — requires live scrape | ❌ manual only | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

- No new test files needed — `healthScore.js` is pure client-side JS with no backend changes.
- `pytest tests/ -x -q` serves as regression guard for existing Python backend.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Grade badge (A–F) appears in ticker card | FHLTH-01 | Browser visual rendering — no JS test framework present | Scrape AAPL → verify `div.deep-analysis-group` header shows letter grade badge |
| Four sub-scores expand when clicking header | FHLTH-02 | Requires browser DOM interaction | Click grade badge header → verify four metric rows visible with individual letters and raw values |
| One-sentence explanation appears in expanded panel | FHLTH-03 | Browser visual — text content check | Expand panel → verify explanation `<p>` visible with positive/negative factor summary |
| Missing-data `⚠` flag shown; grade still renders | FHLTH-04 | Requires sparse-data ticker live scrape | Scrape ticker with missing fields → verify ⚠ on affected row and overall grade still shown |
| Session expand state persists after re-scrape | FHLTH-01 | Browser session state — requires interaction sequence | Expand AAPL, re-scrape → verify expanded state preserved |
| `pageContext.tickerData[ticker].healthScore` populated | FHLTH-01 | Browser console verification | After scrape: `window.pageContext.tickerData['AAPL'].healthScore` → `{ grade, subScores, explanation }` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
