---
phase: 17
slug: bug-fixes-rescrape-dcf-badge
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-05
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — browser-based vanilla JS modules, no test runner |
| **Config file** | none — no jest/vitest/pytest config detected |
| **Quick run command** | Manual browser smoke test of the specific fix just applied |
| **Full suite command** | Manual E2E: scrape ticker A → re-scrape ticker A (BREAK-01) → click Recalculate (BREAK-02) → verify REQUIREMENTS.md |
| **Estimated runtime** | ~2 minutes manual |

---

## Sampling Rate

- **After every task commit:** Manual browser smoke test of the specific fix just applied
- **After every plan wave:** Full manual E2E: scrape ticker A, re-scrape ticker A, click Recalculate, check REQUIREMENTS.md checkboxes
- **Before `/gsd:verify-work`:** All 3 manual checks pass
- **Max feedback latency:** ~2 minutes (manual)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 17-01-01 | 01 | 1 | PEER-01–05 | manual | — (browser only) | ❌ manual | ⬜ pending |
| 17-01-02 | 01 | 1 | DCF-02, DCF-04 | manual | — (browser only) | ❌ manual | ⬜ pending |
| 17-01-03 | 01 | 1 | PEER-01–05, DCF-02, DCF-04 | manual | — (browser only) | ❌ manual | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.* No automated test framework applies to browser-only JS modules. All verification is manual browser testing. No Wave 0 test file creation required.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Peer section renders on re-scrape of same ticker | PEER-01, PEER-02, PEER-03, PEER-04, PEER-05 | Browser-only vanilla JS, no test runner | 1. Open app, scrape AAPL. 2. Scrape AAPL again. 3. Verify peer comparison section shows — not blank. |
| Exactly one premium/discount badge after Recalculate | DCF-02, DCF-04 | Browser-only vanilla JS, no test runner | 1. Open app, scrape AAPL. 2. Click Recalculate in DCF section. 3. Verify exactly one badge appears — no duplicate stale+fresh side-by-side. |
| All 19 v2.1 requirements marked Complete | All v2.1 reqs | Documentation check | Open REQUIREMENTS.md, confirm all 19 v2.1 requirement checkboxes are `[x]` in both bulleted list and traceability table. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
