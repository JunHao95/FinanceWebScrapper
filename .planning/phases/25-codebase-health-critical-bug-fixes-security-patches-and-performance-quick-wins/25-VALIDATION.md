---
phase: 25
slug: codebase-health-critical-bug-fixes-security-patches-and-performance-quick-wins
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-26
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini or setup.cfg |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

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
| 25-01-01 | 01 | 1 | security | unit | `pytest tests/ -x -q -k "security"` | ❌ W0 | ⬜ pending |
| 25-01-02 | 01 | 1 | bug-fix | unit | `pytest tests/ -x -q -k "bug"` | ❌ W0 | ⬜ pending |
| 25-02-01 | 02 | 2 | perf | integration | `pytest tests/ -x -q -k "perf"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_security_patches.py` — stubs for security fixes
- [ ] `tests/test_bug_fixes.py` — stubs for critical bug fixes
- [ ] `tests/test_performance.py` — stubs for performance quick wins
- [ ] `tests/conftest.py` — shared fixtures (if not exists)

*Existing infrastructure may cover some requirements — verify during Wave 0.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Security headers in HTTP responses | security | Requires live server | Run app, curl endpoints, inspect headers |
| Memory usage under load | performance | Requires profiling tool | Run with memory profiler during load test |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
