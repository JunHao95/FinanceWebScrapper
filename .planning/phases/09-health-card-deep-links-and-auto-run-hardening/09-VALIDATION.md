---
phase: 9
slug: health-card-deep-links-and-auto-run-hardening
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-11
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual browser test (no automated JS test suite in project) |
| **Config file** | none |
| **Quick run command** | Open app, run scrape, click VaR/Sharpe chips and observe behavior |
| **Full suite command** | Test VaR chip, Sharpe chip, and simulate rlModels.js removal |
| **Estimated runtime** | ~5 minutes (manual) |

---

## Sampling Rate

- **After every task commit:** Manually verify the targeted behavior in browser
- **After every plan wave:** Run full manual test suite (all 3 success criteria)
- **Before `/gsd:verify-work`:** Full suite must pass all 3 success criteria
- **Max feedback latency:** ~5 minutes (manual smoke test)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 9-01-01 | 01 | 1 | HEALTH-02 | manual smoke | Open browser, run scrape, click VaR chip → Analytics tab scrolls to Monte Carlo with blue highlight | N/A | ⬜ pending |
| 9-01-02 | 01 | 1 | HEALTH-02 | manual smoke | Open browser, run scrape, click Sharpe chip → Analytics tab scrolls to correlation/Sharpe section with blue highlight | N/A | ⬜ pending |
| 9-01-03 | 01 | 1 | AUTO-05 | manual smoke | Remove rlModels.js `<script>` tag from index.html, reload, run analysis → MDP section shows graceful error, no uncaught ReferenceError in console | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements — no automated test framework needed. All verification is manual browser testing per success criteria.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| VaR chip → Analytics tab + scroll to Monte Carlo section + blue pulse | HEALTH-02 | No JS test runner in project; requires browser DOM interaction | Run scrape, click VaR chip in Portfolio Health card, verify: (1) Analytics tab activates, (2) page scrolls to Monte Carlo section, (3) blue box-shadow pulse appears for ~800ms |
| Sharpe chip → Analytics tab + scroll to correlation/Sharpe section + blue pulse | HEALTH-02 | Same as above | Run scrape, click Sharpe chip, verify: (1) Analytics tab activates, (2) page scrolls to correlation section, (3) blue box-shadow pulse appears for ~800ms |
| rlModels.js load failure → graceful MDP error, no ReferenceError | AUTO-05 | Requires simulating script load failure in browser DevTools | Remove `<script src=".../rlModels.js">` from index.html, reload, run analysis, verify: (1) MDP section shows unavailability message (not a JS crash), (2) browser console shows no uncaught ReferenceError |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 300s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
