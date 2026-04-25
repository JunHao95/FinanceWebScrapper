# Testing

**Analysis Date:** 2026-04-26

## Framework

- **Runner:** pytest
- **E2E browser:** pytest-playwright (Chromium)
- **Shortcuts:** `Makefile` targets (`make test`, `make test-unit`, `make test-integration`, `make test-regression`, `make test-slow`, `make test-e2e`)

## Test Suite Overview

- **28 test files**, **277 test functions**
- **Test categories by marker:**

| Marker | Count | Description |
|---|---|---|
| `unit` | 85 | Pure logic, no network, no Flask |
| `regression` | 19 | Math-pinned expected values against fixtures |
| `integration` | 11 | Flask routes via test client |
| `slow` | 5 | Long-running computation tests |
| `e2e` | 1 | Full browser via Playwright |

## Directory Structure

```
tests/
├── conftest.py                          # Shared fixtures (see below)
├── fixtures/                            # Static binary/CSV/JSON test data
│   ├── *.npy                            # NumPy arrays (pinned market data)
│   ├── *.csv                            # Price series
│   └── *.json                           # Scraper response snapshots
├── test_unit_financial_analytics.py     # FinancialAnalytics class
├── test_unit_trading_indicators.py      # Trading indicator functions
├── test_unit_options_pricing.py         # Options pricing models
├── test_unit_stochastic_models.py       # Stochastic model logic
├── test_unit_credit_transitions.py      # Credit transition matrices
├── test_unit_markov_chains.py           # Markov chain computations
├── test_unit_regime_detection.py        # HMM regime detection
├── test_integration_routes.py           # Flask API route tests
├── test_regression_indicators.py        # Pinned indicator values
├── test_regression_stochastic.py        # Pinned stochastic model values
├── test_math01_coupon_discounting.py    # Fixed-income math proofs
├── test_math02_*.py                     # Additional math-pinned tests
├── test_e2e_webapp.py                   # Playwright browser tests
└── test_*.py                            # Other feature/module tests
```

## Shared Fixtures (`tests/conftest.py`)

| Fixture | Scope | Purpose |
|---|---|---|
| `client` | function | Flask test client (no live server) |
| `flask_server` | session | Live Flask server with mocked scrapers |
| `spy_returns` | session | SPY return series loaded from `tests/fixtures/` |
| `standard_heston_params` | session | Pinned Heston model parameters |
| `zero_default_matrix` | session | Credit matrix with no defaults |
| `market_yields_normal` | session | Normal yield curve fixture |

## Unit Tests

**Pattern:** Pure function call with deterministic inputs. No network, no Flask.

```python
# tests/test_unit_financial_analytics.py
def test_dcf_positive_growth(financial_analytics):
    result = financial_analytics.dcf_valuation(
        ticker="AAPL",
        growth_rate=0.10,
        ...
    )
    assert result["intrinsic_value"] > 0

def test_dcf_negative_equity_flagged(financial_analytics):
    # Negative shareholders' equity → unrealistic ROE flagged
    result = financial_analytics.dcf_valuation(ticker="NEGATIVE_EQUITY_MOCK", ...)
    assert result["flags"]["unrealistic_roe"] is True
```

**Naming:** `test_<thing>_<scenario>` (e.g., `test_dcf_negative_equity_flagged`)

## Regression Tests

**Pattern:** Load fixture, compute, assert against pinned expected value.

```python
# tests/test_regression_indicators.py
def test_rsi_pinned_value(spy_returns):
    result = TechnicalIndicators.rsi(spy_returns, period=14)
    assert abs(result.iloc[-1] - EXPECTED_RSI) < 0.01
```

Fixture files in `tests/fixtures/` are **committed to git**. Regenerate via:
```bash
python scripts/generate_fixtures.py
```

## Integration Tests

**Pattern:** POST to Flask route via test client, assert HTTP status + response schema.

```python
# tests/test_integration_routes.py
def test_scrape_route_returns_200(client):
    resp = client.post("/api/scrape", json={"ticker": "AAPL"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "price" in data

def test_scrape_route_invalid_ticker(client):
    resp = client.post("/api/scrape", json={"ticker": ""})
    assert resp.status_code == 400
```

## E2E Tests (Playwright)

**Pattern:** Full browser against live Flask server with mocked API responses.

```python
# tests/test_e2e_webapp.py
def test_stock_scrape_flow(page, flask_server):
    page.goto(flask_server.url)
    page.fill("#ticker-input", "AAPL")
    page.click("#scrape-btn")
    page.wait_for_selector(".results-container")
    assert page.locator(".price-display").is_visible()
```

Browser-level API mocking via `page.route()`:
```python
page.route("**/api/scrape", lambda route: route.fulfill(json=MOCK_SCRAPE_RESPONSE))
```

**Status:** E2E tests **never run in CI** — only available locally. No Playwright in Render/GitHub Actions.

## Mocking Strategy

- **Primary:** `unittest.mock.patch` + `MagicMock` for external dependencies (scrapers, API calls, SMTP)
- **Scraper mocks:** `flask_server` fixture replaces all scrapers with mocks returning fixture data
- **No database mocks:** MongoDB disabled in test environment; no mock needed
- **No JS mocks:** Zero JavaScript unit tests exist

## Running Tests

```bash
# All tests
make test
# or: pytest

# By category
make test-unit          # pytest -m unit
make test-integration   # pytest -m integration
make test-regression    # pytest -m regression
make test-slow          # pytest -m slow
make test-e2e           # pytest -m e2e

# Single file
pytest tests/test_unit_financial_analytics.py -v

# Single test
pytest tests/test_unit_financial_analytics.py::test_dcf_positive_growth -v
```

## Coverage Gaps

### Critical

- **No JavaScript tests** — `static/js/` has ~8,500 lines across 22 modules with **zero JS unit tests**
  - No Vitest, Jest, or any JS test framework configured
  - Component logic (state management, API calls, form handling) entirely untested
  - This is the largest test coverage gap relative to code volume

- **E2E tests not in CI** — `test_e2e_webapp.py` requires local Playwright install; never runs automatically

- **No live scraper smoke tests** — all scraper tests use mocked data; scraper breakage (e.g., Yahoo Finance HTML change) only caught at runtime

### Minor

- `src/utils/email_utils.py` (1281 lines) has minimal unit coverage
- `src/sentiment/` modules partially covered; FinBERT path untested (disabled on cloud)

## Adding New Tests

**New analytics function:**
```
tests/test_unit_<module>.py — happy path + edge case, no network
```

**New Flask route:**
```
tests/test_integration_routes.py — status code + response schema + invalid input handling
```

**New indicator/model with expected values:**
```
tests/test_regression_indicators.py — pin expected output; add fixture data to tests/fixtures/
```

**Frontend JavaScript (if framework adopted):**
- Add Vitest (Vite-native) or Jest config at project root
- Test `static/js/<module>.js` or framework component files
- Recommend: Vitest for React/Vue components, Testing Library for DOM assertions

---

*Testing analysis: 2026-04-26*
