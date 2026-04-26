---
phase: 25-codebase-health-critical-bug-fixes-security-patches-and-performance-quick-wins
plan: 05
status: complete
date: 2026-04-26
---

# Plan 25-05 Summary — Pin requirements.txt & Update README

## What was done

### Task 1: Pin requirements.txt from pip freeze
- Ran `venv/bin/pip freeze` to get exact installed versions.
- Rewrote `requirements.txt` replacing every `>=` bound with `==` at the exact venv-installed version.
- Deduplicated the duplicate `numpy` and `pandas` entries (each appeared twice in the original).
- `Flask-Limiter==4.1.1` confirmed present (installed in plan 02).
- `pre-commit` excluded — dev-only tool, not needed on Render.
- Zero `>=` bounds remain.

### Task 2: Update README.md with Phase 25 changes
Added a new **Security & Performance Hardening (Phase 25)** section before `## 📦 Installation`, covering:
- `SECRET_KEY` startup guard (SEC-01)
- Email recipient allowlist validation (SEC-02)
- Rate limiting on analytics/scrape routes (SEC-03)
- API keys read from env vars only (SEC-04)
- HMM regime TTL cache (PERF-01)
- Bounded LRU/TTL caches (PERF-02)
- Gunicorn 2 workers (PERF-03)
- Bug fixes: percentile rank bisect, JS drawer ID, removed debug prints

### Bonus fix: test_secret_key_guard regression
`test_secret_key_guard` was failing because the project `.env` file (containing `SECRET_KEY`) was being loaded by `load_dotenv()` in the subprocess — even when the test stripped `SECRET_KEY` from the subprocess environment. Fixed by running the subprocess from a `tempfile.TemporaryDirectory()` (no `.env` file present) with `PYTHONPATH=_ROOT` so `import webapp` still resolves.

## Verification results

| Check | Result |
|---|---|
| `test_requirements_pinned` | PASS |
| `grep ">=" requirements.txt \| wc -l` | 0 |
| `grep "Flask-Limiter" requirements.txt` | Flask-Limiter==4.1.1 ✓ |
| `grep "Flask==" requirements.txt` | Flask==3.1.2 ✓ |
| `grep -c "SECRET_KEY\|rate limit\|percentile\|workers 2" README.md` | 8 ✓ |
| `test_secret_key_guard` | PASS (after fix) |
| All 9 codebase health tests | PASS |

## Files modified
- `requirements.txt`
- `README.md`
- `tests/test_unit_codebase_health.py` (test_secret_key_guard fix)
