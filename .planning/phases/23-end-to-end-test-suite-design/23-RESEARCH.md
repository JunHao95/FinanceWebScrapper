# Phase 23: End-to-End Test Suite Design - Research

**Researched:** 2026-04-17
**Domain:** pytest, pytest-playwright, Flask test client, regression pinning
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Use Playwright (Python SDK via pytest-playwright) for E2E browser tests
- Test harness spins up Flask server on a random port via pytest fixture — no manual server start
- Headless by default; add --headed flag for debugging
- Chromium only — no cross-browser matrix needed
- Frozen CSV/JSON fixture files in tests/fixtures/, committed to git
- Mock all external API calls (yfinance, OpenAI) using monkeypatch/responses — no live network calls in any test
- Priority order: Integration tests first → regression tests → unit gap fill → E2E
- Integration: All ~30 API routes get tests — each with happy-path and invalid-input coverage
- Unit gaps: Cover options_pricer, ml_models, rl_models, financial_analytics — happy path + one edge case per function
- Regression: Pin expected outputs for Volume Profile POC/VAH/VAL, Order Flow cumulative delta, Heston calibration convergence, HMM regime detection on frozen fixtures
- E2E: One golden path flow — enter ticker → Run Analysis → verify all 4 tabs render populated content without console errors
- Makefile targets: `make test` (all), `make test-unit`, `make test-integration`, `make test-regression`, `make test-e2e`
- pytest markers registered in conftest.py: unit, integration, regression, e2e
- `make test` runs all tiers including E2E
- Flat test directory layout with naming convention (test_unit_*, test_integration_*, test_regression_*, test_e2e_*) — no subdirectories
- Existing 19 test files remain in place; new tests follow the naming convention
- Claude's discretion: pick appropriate tolerance per computation type — tighter for pure math, looser for stochastic outputs

### Claude's Discretion
- Regression tolerance per computation type

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TEST-01 | Critical user flows documented in a test plan covering: stock scraping pipeline, stochastic model computation, trading indicator generation, chatbot interaction, and portfolio health scoring | Test plan document written as `tests/TEST_PLAN.md` or inline docstrings in conftest.py |
| TEST-02 | Testing framework configured with pytest (backend), pytest-flask (integration), and pytest-playwright (E2E), with `make test` entry point | Install pytest-playwright, pytest-flask, responses; add Makefile; extend conftest.py with markers + live server fixture |
| TEST-03 | Unit tests for all analytics modules — each function has at least one happy-path and one edge-case test, with deterministic inputs | New files: test_unit_options_pricer.py, test_unit_ml_models.py (financial_analytics), test_unit_rl_models.py, test_unit_financial_analytics.py — annotate existing 19 files with markers |
| TEST-04 | Integration tests for all Flask API routes — HTTP status, response schema, error handling | New file: test_integration_routes.py covering the ~22 routes not yet tested; extend existing partial-coverage files |
| TEST-05 | Regression tests pinning Volume Profile POC/VAH/VAL, Order Flow cumulative delta, Heston calibration convergence, HMM regime detection | New file: test_regression_indicators.py + test_regression_stochastic.py with frozen CSV/JSON fixtures |
</phase_requirements>

## Summary

The project already has a healthy pytest foundation: 103 tests across 19 files, a conftest.py with session-scoped fixtures, and an established Flask test client pattern (see test_bcc_route.py, test_chat_route.py, test_markov_route.py). pytest 8.3.4 is installed. What is missing is: (1) pytest-playwright and pytest-flask are not installed, (2) no Makefile exists, (3) the existing 19 test files have no tier markers (unit/integration/regression/e2e), (4) ~22 Flask routes have no integration tests, (5) options_pricer, rl_models, and financial_analytics have no unit tests, and (6) no regression fixtures exist for Volume Profile/Order Flow/HMM.

The work is primarily additive: install two packages, create a Makefile, extend conftest.py, annotate existing files, write new test files, and commit fixture data. No existing test infrastructure needs to be changed.

**Primary recommendation:** Install pytest-playwright + playwright browsers + pytest-flask first (Wave 0), then execute the priority order from CONTEXT.md: integration → regression → unit gaps → E2E.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 8.3.4 (already installed) | Test runner, fixtures, markers | Already in use across 19 files |
| pytest-playwright | 0.5.x | Chromium E2E automation via pytest fixtures | Official Playwright Python integration — provides `page`, `browser`, `context` fixtures directly |
| playwright | 1.x | Browser automation engine | Underlying library required by pytest-playwright |
| pytest-flask | 1.3.x | live_server fixture for Flask integration tests | Provides `live_server` fixture that starts Flask on a random port — no manual threading code needed |
| responses | 0.25.x | Mock HTTP requests (requests library) | Intercepts yfinance/OpenAI HTTP calls without subprocess patching |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unittest.mock (stdlib) | built-in | monkeypatch, patch, MagicMock | Already used in 7 test files — preferred for function-level mocking |
| numpy.testing | built-in with numpy | allclose, assert_array_almost_equal | Regression tests on float arrays |
| pytest.approx | built-in with pytest | Inline float tolerance assertions | Unit tests on scalar outputs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest-playwright | Selenium | Playwright is async-native, has better auto-wait, official Python SDK — Selenium is heavier |
| pytest-flask live_server | threading.Thread fixture | pytest-flask handles random port binding and teardown cleanly; threading requires manual port discovery |
| responses | unittest.mock patch on requests | responses intercepts at the HTTP layer; mock.patch only intercepts at the call site |

**Installation (Wave 0):**
```bash
pip install pytest-playwright pytest-flask responses
playwright install chromium
```

## Architecture Patterns

### Recommended Test Directory Layout
```
tests/
├── conftest.py                      # Extend with markers + live_server + Playwright server fixture
├── fixtures/
│   ├── spy_2017_2021.npy            # Existing
│   ├── spy_2017_2021_dates.npy      # Existing
│   ├── volume_profile_ohlcv.csv     # New: frozen OHLCV for VP regression
│   ├── order_flow_ohlcv.csv         # New: frozen OHLCV for OF regression
│   └── heston_market_prices.json    # New: frozen market prices for Heston regression
├── test_bcc_route.py                # Existing — add @pytest.mark.integration
├── test_chat_route.py               # Existing — add @pytest.mark.integration
├── [17 other existing files]        # Existing — annotate with markers
├── test_integration_routes.py       # NEW: covers all ~22 untested routes
├── test_unit_options_pricer.py      # NEW: OptionsPricer + black_scholes functions
├── test_unit_rl_models.py           # NEW: RL module functions
├── test_unit_financial_analytics.py # NEW: FinancialAnalytics class methods
├── test_regression_indicators.py    # NEW: Volume Profile + Order Flow pinned outputs
├── test_regression_stochastic.py   # NEW: Heston + HMM pinned outputs
└── test_e2e_golden_path.py         # NEW: Playwright E2E golden path
```

### Pattern 1: Flask Test Client (existing, for integration tests)
**What:** Creates a Flask test client via app.test_client(); no live HTTP server needed
**When to use:** Integration tests for all POST/GET routes — fastest, no port conflicts
```python
# Source: existing test_bcc_route.py pattern (verified in codebase)
@pytest.fixture
def client():
    import webapp
    webapp.app.config['TESTING'] = True
    with webapp.app.test_client() as c:
        yield c

def test_route_happy_path(client):
    resp = client.post('/api/heston_price', json={
        'S': 100, 'K': 100, 'T': 1.0, 'r': 0.05,
        'v0': 0.04, 'kappa': 2.0, 'theta': 0.04, 'sigma_v': 0.3, 'rho': -0.7
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'price' in data
```

### Pattern 2: Playwright E2E with threading Flask server
**What:** Starts Flask on a random port in a daemon thread; passes base_url to Playwright page fixture
**When to use:** E2E test — requires real HTTP server so the browser can load JS/CSS assets
```python
# Source: verified pattern from gist.github.com/eruvanos and playwright.dev/python/docs/test-runners
import threading, socket
import pytest

@pytest.fixture(scope='session')
def flask_server():
    import webapp
    webapp.app.config['TESTING'] = True
    # Bind to port 0 to get a random free port
    sock = socket.socket()
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    t = threading.Thread(
        target=webapp.app.run,
        kwargs=dict(host='localhost', port=port, use_reloader=False),
        daemon=True
    )
    t.start()
    import time; time.sleep(0.5)  # brief wait for server to bind
    yield f'http://localhost:{port}'

@pytest.mark.e2e
def test_golden_path(page, flask_server):
    errors = []
    page.on('pageerror', lambda err: errors.append(str(err)))
    page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
    page.goto(flask_server)
    page.fill('#tickers', 'AAPL')
    page.click('button:has-text("Run Analysis")')
    page.wait_for_selector('#stocksTabContent', state='visible', timeout=30000)
    # Verify all 4 tabs have populated content
    for tab_id in ('stocksTabContent', 'analyticsTabContent',
                   'stochasticTabContent', 'tradingIndicatorsTabContent'):
        page.click(f'[data-tab="{tab_id}"]')
        assert page.locator(f'#{tab_id}').inner_text() != ''
    assert errors == [], f'Console errors: {errors}'
```

**Note on pytest-flask live_server vs threading:** There is a known teardown hang when combining pytest-playwright with pytest-flask's live_server (GitHub issue microsoft/playwright-pytest#187). Use the threading pattern above instead of live_server for E2E tests.

### Pattern 3: Regression test with pinned fixture
**What:** Load frozen CSV, compute function, compare output against hardcoded expected values with tolerance
**When to use:** Volume Profile POC/VAH/VAL, Order Flow cumulative delta, Heston calibration, HMM regime detection
```python
# Source: follows existing tests/fixtures/spy_2017_2021.npy precedent (verified in codebase)
import pandas as pd
import numpy as np
import pytest

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'volume_profile_ohlcv.csv')

@pytest.mark.regression
def test_volume_profile_poc_regression():
    df = pd.read_csv(FIXTURE_PATH, index_col=0, parse_dates=True)
    from src.analytics.trading_indicators import compute_volume_profile
    result = compute_volume_profile(df, 'FIXTURE', 90)
    # Pinned on first run; any drift fails CI
    assert result['poc'] == pytest.approx(149.83, abs=0.05)
    assert result['vah'] == pytest.approx(158.20, abs=0.05)
    assert result['val'] == pytest.approx(141.40, abs=0.05)
```

### Pattern 4: Unit test with mocked external calls
**What:** Patch yfinance/OpenAI at the call site; provide synthetic deterministic inputs
**When to use:** Unit tests for analytics modules — options_pricer, rl_models, financial_analytics
```python
# Source: existing test_trading_indicators.py pattern (verified in codebase)
from unittest.mock import patch, MagicMock

@pytest.mark.unit
def test_black_scholes_atm_call():
    from src.derivatives.options_pricer import black_scholes
    price = black_scholes(S=100, K=100, T=1.0, r=0.05, sigma=0.2, option_type='call')
    # ATM call: BS closed form ~ 10.45
    assert price == pytest.approx(10.45, rel=1e-2)

@pytest.mark.unit
def test_black_scholes_intrinsic_floor():
    from src.derivatives.options_pricer import black_scholes
    # Deep ITM call (K=50, S=100): price >= intrinsic = 50
    price = black_scholes(S=100, K=50, T=1.0, r=0.05, sigma=0.2, option_type='call')
    assert price >= 50.0
```

### Pattern 5: Marker annotation for existing tests
**What:** Add `@pytest.mark.unit` or `@pytest.mark.integration` to existing test functions
**When to use:** All 19 existing test files need at least one tier marker
```python
# conftest.py addition (extends existing conftest.py)
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow (requires network/long runtime)")
    config.addinivalue_line("markers", "unit: pure function tests, no I/O")
    config.addinivalue_line("markers", "integration: Flask test client route tests")
    config.addinivalue_line("markers", "regression: pinned output tests with frozen fixtures")
    config.addinivalue_line("markers", "e2e: full browser tests via Playwright")
```

### Anti-Patterns to Avoid
- **Live network calls in non-slow tests:** The `@pytest.mark.slow` convention already guards some tests (test_portfolio_sharpe.py) — any new test hitting yfinance/OpenAI/Finviz must be marked slow or have its HTTP calls mocked
- **Hardcoded ports:** Never bind to a fixed port (e.g. 5000) in E2E fixtures — use `socket.bind(('', 0))` to get a free port
- **import webapp at module level in test files:** The existing pattern does `import webapp` inside the fixture function, not at module top — this avoids circular import issues at collection time; follow this convention
- **pytest-flask live_server + playwright:** Known teardown hang — use threading fixture instead (see Pattern 2)
- **assert on floating point equality without tolerance:** Always use `pytest.approx()` or `numpy.testing.assert_allclose()` for float regression comparisons

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Flask HTTP test client | Manual requests.get against running server | `webapp.app.test_client()` | Already proven in 19 test files; no port binding needed |
| Float tolerance comparison | `abs(result - expected) < 0.01` | `pytest.approx(expected, abs=tol)` | Handles NaN, numpy arrays, nested dicts correctly |
| HTTP mock | Manual monkeypatch on socket | `responses` library | Intercepts at HTTP layer, works with any requests-based code including yfinance internals |
| Playwright console error detection | Screenshot comparison | `page.on('pageerror', ...)` event listener | Exact JS exception capture, no visual comparison needed |
| Fixture data generation | Inline in test | CSV/JSON in tests/fixtures/ committed to git | Reproducible, reviewable, survives dependency upgrades |

**Key insight:** The test client pattern (`app.test_client()`) is already proven and covers all integration test needs. pytest-playwright adds the browser layer for E2E only — it should not be used for API tests.

## Common Pitfalls

### Pitfall 1: Regression values not seeded on first run
**What goes wrong:** Test asserts `result['poc'] == pytest.approx(149.83)` but the 149.83 was never verified — it was just the first output captured, which might itself be wrong
**Why it happens:** "Pinning" means hardcoding the output from the first known-correct run
**How to avoid:** Generate fixture CSV from real AAPL/SPY data, run function once, print and verify output manually, then hardcode those values into the test
**Warning signs:** Regression test passes on the first commit but the value is unrealistic (e.g. POC = 0.0 for a stock trading at $150)

### Pitfall 2: Stochastic regression tests are non-deterministic
**What goes wrong:** HMM regime detection uses random initialization; repeated runs produce different outputs even on the same data
**Why it happens:** hmmlearn or manual EM uses np.random
**How to avoid:** Seed numpy random before calling the function: `np.random.seed(42); result = detector.run(...)`. The existing test_regime_detection.py already loads the spy fixture — follow its seed pattern
**Warning signs:** Test passes 8/10 times locally

### Pitfall 3: Heston calibration "convergence" regression is parameter-sensitive
**What goes wrong:** Pinned RMSE = 0.032 passes on scipy 1.9 but fails on 1.11 because the optimizer changes step size
**Why it happens:** scipy.optimize internals change between minor versions
**How to avoid:** Use loose relative tolerance (rel=0.10 = 10%) for calibration RMSE; only pin that RMSE < some_threshold rather than exact value
**Warning signs:** Test passes locally, fails in CI after pip upgrade

### Pitfall 4: E2E tab selector mismatch
**What goes wrong:** Playwright click on `[data-tab="tradingIndicatorsTabContent"]` fails because the actual HTML uses a different attribute or ID
**Why it happens:** JS tab switching in this project uses custom attributes — need to verify against actual index.html
**How to avoid:** Before writing E2E, inspect templates/index.html for the exact tab button selectors and content div IDs
**Warning signs:** `page.click()` times out with "no element found"

### Pitfall 5: `import webapp` causes heavy ML imports at collection time
**What goes wrong:** `python -m pytest --collect-only` hangs for 30 seconds because importing webapp triggers torch/transformers load
**Why it happens:** webapp.py has lazy imports but some module-level code may trigger them
**How to avoid:** Existing test files put `import webapp` inside the fixture function (not at module top) — follow this exact pattern in all new files
**Warning signs:** pytest collect takes >5 seconds

### Pitfall 6: `responses` library doesn't intercept yfinance (httpx-based)
**What goes wrong:** yfinance in newer versions uses httpx internally, so `responses` (which only intercepts `requests`) misses the calls
**Why it happens:** yfinance 0.2.x+ shifted some internals to httpx
**How to avoid:** Use `unittest.mock.patch('yfinance.Ticker')` at the class level (existing pattern in test_trading_indicators.py) rather than HTTP-layer interception for yfinance; reserve `responses` for routes that use `requests.post` directly (e.g. `/api/chat` Groq calls)
**Warning signs:** "live network call made during test" warnings or flaky tests that pass with network and fail without

## Code Examples

### Makefile targets
```makefile
# Source: derived from CONTEXT.md locked decisions
.PHONY: test test-unit test-integration test-regression test-e2e

test: test-unit test-integration test-regression test-e2e

test-unit:
	pytest -m unit -q

test-integration:
	pytest -m integration -q

test-regression:
	pytest -m regression -q

test-e2e:
	pytest -m e2e -q --headed=false --browser=chromium
```

### Integration test for a route with mocked heavy dependency
```python
# Source: pattern verified in test_bcc_route.py (codebase)
@pytest.mark.integration
def test_heston_price_happy_path(client):
    resp = client.post('/api/heston_price', json={
        'S': 100.0, 'K': 100.0, 'T': 1.0, 'r': 0.05,
        'v0': 0.04, 'kappa': 2.0, 'theta': 0.04, 'sigma_v': 0.3, 'rho': -0.7
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data.get('price'), (int, float))

@pytest.mark.integration
def test_heston_price_missing_params(client):
    resp = client.post('/api/heston_price', json={})
    assert resp.status_code in (400, 422, 500)
```

### Fixture CSV generation script (run once, commit output)
```python
# scripts/generate_fixtures.py — run manually, not part of test suite
import pandas as pd, yfinance as yf, os

def generate_volume_profile_fixture():
    df = yf.Ticker('AAPL').history(period='6mo', auto_adjust=True)
    df = df[['Open','High','Low','Close','Volume']].dropna()
    out = os.path.join('tests', 'fixtures', 'volume_profile_ohlcv.csv')
    df.to_csv(out)
    print(f"Written {len(df)} rows to {out}")
    # Print expected values for hardcoding into test
    from src.analytics.trading_indicators import compute_volume_profile
    result = compute_volume_profile(df, 'AAPL', 90)
    print(f"poc={result['poc']}, vah={result['vah']}, val={result['val']}")

if __name__ == '__main__':
    generate_volume_profile_fixture()
```

### Console error capture in E2E test
```python
# Source: verified pattern from playwright.dev/python/docs/test-runners + alisterscott.github.io
@pytest.mark.e2e
def test_golden_path_no_console_errors(page, flask_server):
    js_errors = []
    page.on('pageerror', lambda err: js_errors.append(f'PAGE ERROR: {err}'))
    page.on('console', lambda msg: js_errors.append(f'CONSOLE ERROR: {msg.text}')
            if msg.type == 'error' else None)
    page.goto(flask_server)
    # ... test steps ...
    assert js_errors == [], '\n'.join(js_errors)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Selenium WebDriver | Playwright Python SDK | 2021-2022 | Playwright has better auto-wait, no driver management, native async support |
| Manual threading for live server | pytest-flask live_server | 2018+ | pytest-flask handles random port and teardown; but avoid with playwright (teardown hang) |
| numpy.isclose(a, b) | pytest.approx(b, rel=...) | pytest 3.0+ | approx integrates with assert messages, works in nested dicts |
| Hardcoded expected values in test file | pytest-regressions ndarray_regression | 2020+ | pytest-regressions auto-generates fixtures; but overkill here — inline approx is sufficient |

**Deprecated/outdated:**
- `werkzeug.server.shutdown`: Removed in Werkzeug 2.1 — do not use to stop the test server; daemon thread exits automatically when pytest exits
- `pytest.ini` with `[pytest]` section: Still valid, but pyproject.toml is the modern home for pytest config; not required to change for this phase

## Open Questions

1. **Exact HTML tab selectors for E2E test**
   - What we know: tabs exist for Stocks, Analytics, Stochastic Models, Trading Indicators
   - What's unclear: The exact button data attributes / IDs in index.html need to be read before writing the E2E test
   - Recommendation: Wave 0 task reads templates/index.html to extract tab selectors before writing test_e2e_golden_path.py

2. **HMM random seed requirement**
   - What we know: existing test_regime_detection.py passes (102/103 tests pass — the 1 failure is test_spy_march_2020_is_stressed which is a value regression)
   - What's unclear: whether RegimeDetector accepts a random_state parameter or numpy seed must be set globally
   - Recommendation: Check RegimeDetector.__init__ signature before writing regression test; if no random_state param, use np.random.seed(42) around the call

3. **Routes requiring long-running fixtures (e.g. /api/scrape)**
   - What we know: /api/scrape triggers full scrape pipeline — not suitable for fast integration test
   - What's unclear: Whether to mock the scrapers or skip /api/scrape integration test for this phase
   - Recommendation: Mock all scrapers at the class level using patch(); return a minimal valid scrape result dict to test the route handler logic without network calls

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | None — add pytest.ini or pyproject.toml [tool.pytest.ini_options] in Wave 0 |
| Quick run command | `pytest -m "unit or integration" -q --tb=short` |
| Full suite command | `pytest -q` or `make test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-01 | Critical user flows documented | manual | n/a — document in conftest.py module docstring | ❌ Wave 0 |
| TEST-02 | Framework configured, `make test` works | smoke | `make test` | ❌ Wave 0 |
| TEST-03 | Unit tests for analytics modules | unit | `pytest -m unit -q` | ❌ Wave 0 |
| TEST-04 | Integration tests for all routes | integration | `pytest -m integration -q` | Partial (7 routes) |
| TEST-05 | Regression tests for pinned outputs | regression | `pytest -m regression -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest -m "unit or integration" -q --tb=short`
- **Per wave merge:** `pytest -q` (full suite including regression; skip E2E unless explicitly triggered)
- **Phase gate:** Full suite green before `/gsd:verify-work`, including E2E

### Wave 0 Gaps
- [ ] `Makefile` — targets: test, test-unit, test-integration, test-regression, test-e2e
- [ ] `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` — register markers, set testpaths = tests
- [ ] Install: `pip install pytest-playwright pytest-flask responses && playwright install chromium`
- [ ] Update `requirements.txt` with new dev dependencies
- [ ] Extend `tests/conftest.py` — add unit/integration/regression/e2e marker registrations + Flask live_server threading fixture
- [ ] `tests/fixtures/volume_profile_ohlcv.csv` — run generate_fixtures.py once to create
- [ ] `tests/fixtures/order_flow_ohlcv.csv` — run generate_fixtures.py once to create
- [ ] `tests/fixtures/heston_market_prices.json` — run generate_fixtures.py once to create

## Route Coverage Audit

Routes currently with integration tests (full or partial):
- `/api/calibrate_bcc` — test_bcc_route.py (4 tests)
- `/api/chat` — test_chat_route.py (6 tests)
- `/api/markov_chain` — test_markov_route.py (7 tests)
- `/api/portfolio_sharpe` — test_portfolio_sharpe.py (3 tests, marked slow)
- `/api/trading_indicators` — test_trading_indicators.py (2 route tests)
- `/api/interest_rate_model` — test_vasicek_model.py (test_vasicek_route, test_cir_route_has_feller_ratio)
- `/api/peers` — test_peer_comparison.py (1 route test)

Routes needing new integration tests (22 untested routes):
```
/api/fundamental-analysis
/api/scrape
/api/send-email
/api/option_pricing
/api/implied_volatility
/api/greeks
/api/model_comparison
/api/convergence_analysis
/api/volatility_surface
/api/atm_term_structure
/api/heston_price
/api/heston_iv_surface
/api/merton_price
/api/regime_detection
/api/calibrate_heston
/api/calibrate_heston_stream
/api/calibrate_merton
/api/credit_risk
/api/rl_investment_mdp
/api/rl_gridworld
/api/rl_portfolio_rotation_pi
/api/stoch_portfolio_mdp
/api/rl_portfolio_rotation_ql
/api/validate_ticker
/health
```

## Sources

### Primary (HIGH confidence)
- Codebase inspection — tests/conftest.py, 19 existing test files, webapp.py routes, src/analytics/ modules (direct read, verified 2026-04-17)
- playwright.dev/python/docs/test-runners — pytest-playwright fixture API, base_url, headless/headed flags
- pypi.org/project/pytest-flask — live_server fixture, app fixture pattern

### Secondary (MEDIUM confidence)
- gist.github.com/eruvanos/c370b04e1be18b89d1babec188495c32 — threading Flask server pattern (verified working per community use)
- github.com/microsoft/playwright-pytest/issues/187 — confirmed teardown hang with pytest-flask + playwright (avoidance justified)
- alisterscott.github.io — pageerror/console event listener pattern for console error capture

### Tertiary (LOW confidence)
- WebSearch finding: responses library vs httpx for yfinance mocking — MEDIUM confidence the yfinance version in this project (0.2.18+) uses requests internally; verify with `pip show yfinance` before relying on responses library to intercept yfinance calls

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pytest/playwright/pytest-flask are official packages with stable APIs; versions verified
- Architecture: HIGH — patterns verified directly against existing codebase (19 test files read, conftest.py read, test_bcc_route.py/test_trading_indicators.py patterns confirmed)
- Pitfalls: HIGH for threading/teardown hang and import patterns (verified from codebase and known GitHub issues); MEDIUM for Heston calibration tolerance (depends on scipy version)

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (stable domain; pytest-playwright API changes slowly)
