---
phase: 12
slug: integrating-chatbot-to-the-details-in-stock-analysis-stochastic-models-tabs-etc-so-the-chatbot-can-access-the-content-scrapped
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | tests/conftest.py |
| **Quick run command** | `pytest tests/test_chat_route.py -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_chat_route.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 0 | CTX-01 | unit | `pytest tests/test_chat_route.py::test_chat_with_context -x` | ❌ W0 | ⬜ pending |
| 12-01-02 | 01 | 0 | CTX-02 | unit | `pytest tests/test_chat_route.py::test_chat_no_context -x` | ❌ W0 | ⬜ pending |
| 12-01-03 | 01 | 0 | CTX-03 | unit | `pytest tests/test_chat_route.py::test_chat_with_history -x` | ❌ W0 | ⬜ pending |
| 12-02-01 | 02 | 1 | CTX-01,CTX-02,CTX-03 | unit | `pytest tests/test_chat_route.py -x -q` | ✅ | ⬜ pending |
| 12-02-02 | 02 | 2 | CTX-04 | manual | Browser console: `buildContextSnapshot()` returns null when no tickers | N/A | ⬜ pending |
| 12-02-03 | 02 | 2 | CTX-05 | manual | Visual check: context indicator shows "Context: TICKER" | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_chat_route.py` — add `test_chat_with_context`, `test_chat_no_context`, `test_chat_with_history` test functions (file exists, extend it)

*Existing infrastructure covers framework and conftest — no new files needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `buildContextSnapshot()` returns null when no tickers loaded | CTX-04 | Requires browser JS runtime | Open console, call `buildContextSnapshot()` before any scrape — should return null |
| Context indicator shows "Context: TICKER" | CTX-05 | Visual UI check | Scrape AAPL, open chatbot — indicator line should show "Context: AAPL" |
| Agent switch preserves context indicator | CTX-05 | Visual UI check | Switch between FinancialAnalyst/Quant tabs — indicator should persist |
| Stochastic result captured after model run | CTX-04 | Requires browser interaction | Run Heston model, check `window.pageContext.stochasticResults` in console |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
