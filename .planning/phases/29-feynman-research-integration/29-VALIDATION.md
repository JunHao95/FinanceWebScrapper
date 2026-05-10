---
phase: 29
slug: feynman-research-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-10
---

# Phase 29 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini / setup.cfg |
| **Quick run command** | `pytest tests/test_unit_feynman_runner.py -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_unit_feynman_runner.py -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 29-01-01 | 01 | 1 | POC-backend | unit | `pytest tests/test_unit_feynman_runner.py -q` | ❌ W0 | ⬜ pending |
| 29-01-02 | 01 | 1 | POC-backend | unit | `pytest tests/test_unit_feynman_runner.py::test_ansi_stripping -q` | ❌ W0 | ⬜ pending |
| 29-01-03 | 01 | 1 | POC-backend | unit | `pytest tests/test_unit_feynman_runner.py::test_empty_output_guard -q` | ❌ W0 | ⬜ pending |
| 29-02-01 | 02 | 1 | POC-routes | integration | `pytest tests/test_integration_routes.py -k feynman -q` | ❌ W0 | ⬜ pending |
| 29-02-02 | 02 | 1 | POC-routes | integration | `pytest tests/test_integration_routes.py -k feynman_unavailable -q` | ❌ W0 | ⬜ pending |
| 29-03-01 | 03 | 2 | POC-ui | manual | n/a | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_unit_feynman_runner.py` — stubs for feynman_runner unit tests
- [ ] `tests/test_integration_routes.py` — add feynman route test stubs (file exists, append)

*Existing pytest infrastructure covers framework requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| "Research This Model" button visible in RF card | POC-ui | Browser DOM inspection | Load ML Signals tab, verify button appears below RF signal badge |
| Spinner shown while job pending | POC-ui | Timing-dependent visual | Click button, verify "Searching academic papers…" text appears |
| Academic Context panel renders markdown | POC-ui | Feynman requires live API keys | With valid API keys, click button, verify collapsible panel renders |
| Button hidden when Feynman not installed | POC-ui | Environment-dependent | Temporarily rename feynman binary, reload page, verify button absent |
| Timeout message shown | POC-ui | Requires 120s wait | Mock timeout in backend, verify error message in UI |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
