---
phase: 11
slug: responsive-layout-dashboard-customisation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-29
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend), browser DevTools / manual (CSS/JS) |
| **Config file** | pytest.ini or none |
| **Quick run command** | `pytest tests/` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | Responsive CSS | manual | `pytest tests/` (smoke) | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | Tab scrollbar hide | manual | browser 480px viewport | ✅ | ⬜ pending |
| 11-01-03 | 01 | 1 | Table overflow-x | manual | browser 360px viewport | ✅ | ⬜ pending |
| 11-01-04 | 01 | 1 | Form stacking | manual | browser 480px viewport | ✅ | ⬜ pending |
| 11-02-01 | 02 | 2 | Collapse toggles | manual | browser interaction | ✅ | ⬜ pending |
| 11-02-02 | 02 | 2 | sessionStorage persist | manual | browser DevTools | ✅ | ⬜ pending |
| 11-02-03 | 02 | 2 | healthScore.js migration | unit | `pytest tests/test_integration_routes.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers all phase requirements (no new test files needed for Wave 0; CSS/JS changes are manually verified via browser viewport resize and DevTools).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 360px layout no overflow | Responsive CSS | CSS viewport state untestable in pytest | Open Chrome DevTools → 360px → scroll all sections |
| Tab bar horizontal scroll at 480px | Tab nav | Browser scroll behavior | DevTools 480px → click each tab → confirm scroll |
| Chatbot window fits 480px | Chatbot mobile | DOM injection via JS innerHTML | DevTools 480px → open chatbot |
| Collapse/expand toggles animate | Dashboard UX | CSS transitions | Click section headers → verify chevron + smooth collapse |
| sessionStorage key persists on re-scrape | Dashboard UX | sessionStorage state | Collapse a section → re-run scrape same ticker → confirm state retained |
| Plotly charts follow container width | Chart responsive | Plotly rendering | Resize window → charts reflow |

---

## Validation Architecture

The primary validation mechanism for this phase is **browser viewport testing** — all responsive behaviors are CSS/JS and cannot be asserted by pytest. The backend test suite (`pytest tests/`) runs as a smoke check to ensure no regressions were introduced to backend routes or analytics.

Automated tests cover:
- Existing Flask route smoke tests confirm no regressions from CSS/JS changes
- Integration tests verify no Python files were accidentally broken

Manual tests cover:
- Visual layout at 360px, 480px, 768px, 1024px
- Collapse/expand toggle behavior and sessionStorage persistence

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
