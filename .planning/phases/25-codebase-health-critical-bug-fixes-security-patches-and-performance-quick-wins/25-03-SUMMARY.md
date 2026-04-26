---
phase: 25-codebase-health-critical-bug-fixes-security-patches-and-performance-quick-wins
plan: 03
status: complete
completed: 2026-04-26
---

## What Was Done

**TECH-03 — Pre-commit linting config**
- Created `.flake8`: `max-line-length = 120`, excludes venv/__pycache__/.git/migrations, ignores E203/W503
- Created `.pre-commit-config.yaml`: black 25.1.0 + flake8 7.1.2 hooks
- Ran `pip install pre-commit && pre-commit install` — hooks registered at `.git/hooks/pre-commit`

**PERF-04 — Gunicorn workers**
- `Procfile`: `--workers 1` → `--workers 2` (all other flags unchanged)

**TECH-04 — Deduplicate JS helpers**
- Added `Utils.parseNumeric` to `static/js/utils.js` (canonical impl with comma-stripping, superset of all source files)
- Removed local `function parseNumeric` from `healthScore.js`, `earningsQuality.js`, `dcfValuation.js`; replaced all calls with `Utils.parseNumeric(...)`
- Removed local `function escapeHtml` from `chatbot.js`; replaced calls at lines 73–74 with `Utils.escapeHtml(...)`

**Note:** `dcfValuation.js`'s local impl had extra comma-stripping (`s.replace(/,/g, '')`). This was folded into `Utils.parseNumeric` so DCF calculations for values like `"1,234,567"` remain correct.

## Verification

```
pytest tests/test_unit_codebase_health.py::test_precommit_config tests/test_unit_codebase_health.py::test_procfile_workers tests/test_unit_codebase_health.py::test_no_duplicate_js_helpers -v
# 3 passed
```

## Success Criteria

- [x] test_precommit_config: PASS
- [x] test_procfile_workers: PASS
- [x] test_no_duplicate_js_helpers: PASS
- [x] `.flake8` with max-line-length = 120
- [x] `.pre-commit-config.yaml` with black 25.1.0 and flake8 7.1.2
- [x] Procfile shows --workers 2
- [x] `Utils.parseNumeric` defined in utils.js
- [x] No local `parseNumeric` in healthScore, earningsQuality, dcfValuation
- [x] No standalone `escapeHtml` in chatbot.js
