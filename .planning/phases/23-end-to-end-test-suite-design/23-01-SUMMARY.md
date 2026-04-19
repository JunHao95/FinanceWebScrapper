---
phase: 23-end-to-end-test-suite-design
plan: 01
status: complete
---

# Phase 23-01 Summary — Test Framework Infrastructure

## What was built

- **Makefile** — 5 targets: `test`, `test-unit`, `test-integration`, `test-regression`, `test-e2e` using `pytest -m <marker>` dispatch.
- **tests/conftest.py** — Extended with:
  - Module docstring documenting 5 critical user flows (TEST-01)
  - `pytest_configure` registering 4 new markers: `unit`, `integration`, `regression`, `e2e` (alongside existing `slow`)
  - `client` fixture (function-scoped) — Flask test client via `webapp.app.test_client()`
  - `flask_server` fixture (session-scoped) — threading-based live server on a random port for E2E tests
- **requirements.txt** — Added `pytest-playwright>=0.4.0`, `pytest-flask>=1.3.0`, `responses>=0.25.0` under `# Testing` section
- **19 test files annotated** with tier markers:
  - 11 pure-unit files: module-level `pytestmark = pytest.mark.unit`
  - 3 pure-integration files: module-level `pytestmark = pytest.mark.integration`
  - 5 mixed files: per-function/class `@pytest.mark.unit` or `@pytest.mark.integration`

## Verification results

```
pytest -m unit --collect-only      → 88 tests collected
pytest -m integration --collect-only → 31 tests collected
Total: 119 tests, 0 without a tier marker
make test-unit                      → 87 passed, 1 pre-existing failure
                                      (test_spy_march_2020_is_stressed requires live yfinance)
python -c "import pytest_playwright; import responses" → deps ok
```

## Pre-existing failure (not introduced by this phase)

`tests/test_regime_detection.py::test_spy_march_2020_is_stressed` — fails due to a `ValueError` in `regime_detection.py:238` when SPY fixture data is loaded. Confirmed failing on `main` before any changes in this phase.
