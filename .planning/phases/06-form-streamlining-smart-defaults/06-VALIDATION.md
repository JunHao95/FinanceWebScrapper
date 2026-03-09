---
phase: 6
slug: form-streamlining-smart-defaults
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Python backend only) — no JS test framework |
| **Config file** | none (no `pytest.ini` or `pyproject.toml` found) |
| **Quick run command** | `pytest tests/ -x -q --ignore=tests/test_regime_detection.py` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Reload browser, submit with Advanced collapsed, confirm no JS errors in console
- **After every plan wave:** Full manual smoke: test each FORM requirement scenario in sequence
- **Before `/gsd:verify-work`:** All 5 success criteria in phase description pass
- **Max feedback latency:** ~30 seconds (manual browser test)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 6-01-01 | 01 | 1 | FORM-01, FORM-03 | manual smoke | Open browser, submit with Advanced collapsed, check network tab | N/A | ⬜ pending |
| 6-01-02 | 01 | 1 | FORM-02 | manual | Toggle `<details>` in browser | N/A | ⬜ pending |
| 6-01-03 | 01 | 1 | FORM-04, FORM-05 | manual | Switch modes, type values, verify live % labels | N/A | ⬜ pending |
| 6-01-04 | 01 | 1 | FORM-06 | manual | Switch modes, verify currency selector visibility | N/A | ⬜ pending |
| 6-01-05 | 01 | 1 | FORM-07 | manual | Leave all Value inputs blank, submit | N/A | ⬜ pending |
| 6-01-06 | 01 | 1 | FORM-08 | visual | Open browser, verify button prominence | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- None — existing test infrastructure (pytest) is unaffected. No new test files needed for a UI-only phase with no JS test framework.

*Existing infrastructure covers all phase requirements (backend pytest unaffected).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Submit with only tickers, no error | FORM-01 | No JS test framework | Open browser, enter tickers, click Run Analysis with Advanced collapsed |
| Advanced toggle shows/hides section | FORM-02 | DOM interaction | Click `<details>` summary, verify expand/collapse |
| Sources payload = defaults when collapsed | FORM-03 | Network request inspection | Open devtools Network tab, submit, check request body |
| Mode toggle switches allocation mode | FORM-04 | UI interaction | Click % Weight / Value mode buttons |
| Live % labels update on input | FORM-05 | Real-time DOM update | Type values in Value mode, verify `→ XX.X%` updates |
| Currency selector visibility per mode | FORM-06 | Conditional DOM | Switch modes, verify selector appears/disappears |
| Blank allocation = equal weights | FORM-07 | Form submission logic | Leave all Value inputs blank, submit, verify backend receives equal weights |
| Run Analysis button is prominent | FORM-08 | Visual/layout | Open browser, verify button is full-width and prominent |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
