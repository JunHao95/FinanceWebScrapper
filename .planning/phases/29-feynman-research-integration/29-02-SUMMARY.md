---
phase: 29
plan: "02"
subsystem: feynman-research
tags: [backend, feynman-runner, flask-routes, tdd]
key_files:
  created:
    - src/analytics/feynman_runner.py
  modified:
    - webapp.py
    - README.md
---

# Phase 29 Plan 02: feynman_runner + Flask Routes

**One-liner:** async feynman CLI wrapper with in-memory job store + two non-blocking Flask routes.

## Tasks

| Task | Commit | Files |
|------|--------|-------|
| 1 — feynman_runner.py | 8a4c8a2 | src/analytics/feynman_runner.py |
| 2 — Flask routes + README | 379aec5 | webapp.py, README.md |

## Verification

```
tests/test_unit_feynman_runner.py    5 passed
tests/test_integration_routes.py -k feynman    3 passed
tests/test_integration_routes.py (full)    68 passed
```

## Self-Check: PASSED

- src/analytics/feynman_runner.py exists ✓
- subprocess uses ["feynman", "--prompt", query] ✓
- POST /api/feynman_research + GET /api/feynman_status/<job_id> in webapp.py ✓
- 68 tests GREEN, no regressions ✓
