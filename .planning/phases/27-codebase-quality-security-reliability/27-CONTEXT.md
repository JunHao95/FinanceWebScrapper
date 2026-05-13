# Phase 27 Context: Codebase Quality, Security, and Reliability Hardening

## Goal

All 12 identified reliability, security, code-quality, and test-coverage gaps are closed — no new features. Every change is isolated and independently tested.

## Source

Identified via static code review on 2026-05-04.

## Requirements

### Reliability
- **REL-01**: Add `timeout=30` to all `requests` calls in `yahoo_scraper.py` and `api_scraper.py` — currently hang indefinitely on network stalls.
- **REL-02**: Add explicit `verify=True` to all `requests` calls in scrapers — no SSL verify params found, MITM risk.
- **REL-03**: Wrap `request.get_json()` / `request.json` in `try/except (TypeError, ValueError)` in all POST endpoints (`webapp.py:430-445`, `835-909`) — malformed JSON currently produces silent `None` or unhandled 500.
- **REL-04**: Apply Flask-Limiter rate limit to I/O-heavy endpoints (at minimum: `fundamental_analysis`, `send_consolidated_report`) — only `/api/scrape` is currently protected.

### Code Quality
- **QA-01**: Remove `print(f"DEBBUUGG save reports , ", save_reports_enabled)` from `main.py:713`.
- **QA-02**: Replace all 95 `print()` calls with `logger.*` in `main.py` — logger is already configured.
- **QA-03**: Narrow bare `except:` to `except OSError` in `webapp.py:794` (temp file cleanup).
- **QA-04**: Standardise all Flask error responses to `{"error": "<message>"}` — currently inconsistent mix of `{"error": ...}` and `{"success": False, "error": ...}`.

### Test Coverage
- **TEST-09**: Add Flask error-path tests to `tests/test_integration_routes.py` — malformed JSON body, missing required fields, invalid ticker format (symbols, length > 10, special chars).
- **TEST-10**: Add email injection test for `send_consolidated_report` endpoint (`webapp.py:703`) — assert newlines/headers in email field return 400.
- **TEST-11**: Add scraper failure simulation tests — mock `requests.get` to raise `requests.exceptions.ConnectionError` and `requests.exceptions.Timeout`, assert graceful error returned.

### Architecture
- **ARCH-01**: Cap `max_workers` in webapp scraper thread path to 4 — `main.py:301` caps at 4 but the webapp code path has no cap, risking unbounded thread growth under concurrent requests.

## Key File References

| File | Lines | Issue |
|------|-------|-------|
| `main.py` | 713 | Debug print (QA-01) |
| `main.py` | 22 | `sys.path.insert` (note only — low risk) |
| `main.py` | 80–90 | Double logging handler setup |
| `main.py` | 301 | `max_workers` cap (ARCH-01 reference) |
| `main.py` | 323 | Dead fallback `run_scrapers_sequential` |
| `webapp.py` | 430–445 | `request.get_json()` no error handling (REL-03) |
| `webapp.py` | 703 | `send_consolidated_report` — email injection (TEST-10) |
| `webapp.py` | 794 | Bare `except:` (QA-03) |
| `webapp.py` | 835–909 | `request.json` no error handling (REL-03) |
| `yahoo_scraper.py` | various | No `timeout=` on requests (REL-01, REL-02) |
| `api_scraper.py` | various | No `timeout=` on requests (REL-01, REL-02) |

## Plan Wave Structure

| Plan | Wave | Content |
|------|------|---------|
| 27-01-PLAN.md | 1 | Test scaffold — TEST-09, TEST-10, TEST-11 stubs (all failing) |
| 27-02-PLAN.md | 2 | Security + reliability — REL-01, REL-02, REL-03, REL-04 |
| 27-03-PLAN.md | 2 (parallel) | Code quality — QA-01, QA-02, QA-03, QA-04, dead fallback removal |
| 27-04-PLAN.md | 3 | Architecture — ARCH-01 thread cap + README update + full test suite run |

## Success Criteria

1. All `requests` calls in `yahoo_scraper.py` and `api_scraper.py` include `timeout=30, verify=True`.
2. Every POST endpoint in `webapp.py` handles malformed JSON with a `400 {"error": "..."}` response, confirmed by TEST-09 passing.
3. `send_consolidated_report` returns `400` when email field contains `\n` or `\r`, confirmed by TEST-10 passing.
4. Mocked `ConnectionError` and `Timeout` in scraper tests return graceful error dict, not unhandled exception, confirmed by TEST-11 passing.
5. `main.py` has zero bare `print()` calls (all replaced with `logger.*` or removed if debug).
6. `webapp.py:794` catch clause is `except OSError`.
7. All Flask error responses across `webapp.py` use `{"error": "..."}` shape.
8. `pytest` runs green on all 29+ test files after Phase 27 changes.
