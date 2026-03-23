---
phase: 15
slug: dcf-valuation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Node.js `require` + assert (no Jest detected) |
| **Config file** | none — no JS test suite in project |
| **Quick run command** | `node -e "const m=require('./static/js/dcfValuation.js'); const r=m.computeValuation({'Free Cash Flow (AlphaVantage)':'1000000.00','Market Cap (Yahoo)':'10000000','Current Price (Yahoo)':'10.00'},0.10,0.10,0.03); console.log(r)"` |
| **Full suite command** | Manual browser check across one AV-data ticker and one no-FCF ticker |
| **Estimated runtime** | ~30 seconds (browser manual) |

---

## Sampling Rate

- **After every task commit:** Verify in browser — open app, scrape a ticker with AV key, confirm DCF section renders correctly
- **After every plan wave:** Check all five success criteria in browser across one AV-data ticker and one no-FCF ticker
- **Before `/gsd:verify-work`:** Full suite must be green

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | DCF-01, DCF-02, DCF-05 | unit | Node.js smoke test (computeValuation) | ❌ Wave 0 | ⬜ pending |
| 15-01-02 | 01 | 1 | DCF-01 | smoke (browser) | Manual browser check | ❌ Wave 0 | ⬜ pending |
| 15-01-03 | 01 | 1 | DCF-03, DCF-04 | smoke (browser) | Manual browser check | N/A — browser-only | ⬜ pending |
| 15-01-04 | 01 | 1 | DCF-02 | smoke (browser) | Manual browser check | N/A — browser-only | ⬜ pending |
| 15-01-05 | 01 | 1 | DCF-05 | smoke (browser) | Manual browser check | N/A — browser-only | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `static/js/dcfValuation.js` — module file must exist (created in Wave 1) before smoke tests can run
- [ ] No JS unit test infrastructure exists — verification is manual browser and Node.js smoke tests only

*Existing infrastructure covers all phase requirements that are amenable to automation. Browser-only requirements (DCF-03, DCF-04) require manual verification.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Three assumption inputs render with correct defaults | DCF-03 | DOM rendering requires browser | Scrape a ticker → expand Deep Analysis → verify WACC=10%, g1=10%, g2=3% inputs are visible |
| Recalculate updates display without page reload | DCF-04 | Interactive browser action required | Change WACC input to 12 → click Recalculate → verify intrinsic value updates, no full page reload |
| Premium/discount badge displays correctly | DCF-02 | Requires live scraped data | Confirm badge shows signed % with correct colour (green=discount, red=premium) |
| FCF absent case renders unavailable message | DCF-05 | Requires ticker with no FCF data | Scrape a ticker with no AV/Yahoo FCF → verify "DCF unavailable — FCF data missing" shown |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
