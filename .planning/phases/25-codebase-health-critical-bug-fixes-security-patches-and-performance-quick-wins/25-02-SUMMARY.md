---
phase: 25-codebase-health-critical-bug-fixes-security-patches-and-performance-quick-wins
plan: 02
status: complete
date: 2026-04-26
---

# Plan 25-02 Summary — Security Patches (SEC-01 → SEC-04)

## What was done

### SEC-01 — SECRET_KEY startup guard
- Replaced `os.environ.get('SECRET_KEY', 'your-secret-key-here')` fallback with a hard `RuntimeError` if `SECRET_KEY` env var is absent.
- App now refuses to start in any environment without the key set.

### SEC-02 — Email recipient allowlist
- Added `"recipients": ["teejunhao@gmail.com"]` to `config.json`.
- `/api/send-email` now validates the recipient against `config.get('recipients', [])` before sending; returns HTTP 403 for unlisted addresses.

### SEC-03 — Rate limiting (Flask-Limiter 4.1.1)
- Installed `Flask-Limiter==4.1.1`; added to `requirements.txt`.
- Limiter initialised with in-memory storage and default limits (200/day, 50/hour).
- 8 routes decorated: `@limiter.limit("10 per minute")` on `/api/scrape`; `@limiter.limit("5 per minute")` on `/api/regime_detection`, `/api/calibrate_heston`, `/api/calibrate_merton`, `/api/calibrate_bcc`, `/api/rl_portfolio_rotation_pi`, `/api/stoch_portfolio_mdp`, `/api/rl_portfolio_rotation_ql`.

### SEC-04 — Remove client-side API key passing
- Removed `alphaKey`/`finhubKey` DOM reads and request-body fields from `stockScraper.js`.
- Removed the two API key `<div class="form-group">` blocks from `templates/index.html`.
- Backend (`webapp.py` scrape handler) now reads `alpha_key`/`finhub_key` from env vars only.
- Removed `alpha_key`/`finhub_key` from route docstring.

## Tests added / updated
- `conftest.py`: added `os.environ.setdefault('SECRET_KEY', ...)` so webapp imports succeed in test runner.
- `test_integration_routes.py`:
  - Fixed existing class stubs (`TestEmailAllowlist`, `TestRateLimiting`, `TestNoClientApiKeys`) — corrected route path, removed skip marker, fixed patch target.
  - Added standalone functions `test_email_allowlist`, `test_rate_limiting`, `test_no_client_api_keys` matching plan pytest node IDs.

## Verification results

| Check | Result |
|---|---|
| `test_secret_key_guard` | PASS |
| `test_email_allowlist` | PASS |
| `test_rate_limiting` | PASS |
| `test_no_client_api_keys` | PASS |
| `grep "RuntimeError" webapp.py` | ✓ |
| `grep "recipients" config.json` | ✓ |
| `grep "Flask-Limiter" requirements.txt` | ✓ |
| `grep "limiter.limit" webapp.py \| wc -l` | 8 |
| No `alpha_key` / `alphaKey` in `stockScraper.js` | ✓ |
| No `alpha_key` / `finhub_key` in `index.html` | ✓ |

## Files modified
- `webapp.py`
- `config.json`
- `requirements.txt`
- `static/js/stockScraper.js`
- `templates/index.html`
- `tests/conftest.py`
- `tests/test_integration_routes.py`
- `README.md`
