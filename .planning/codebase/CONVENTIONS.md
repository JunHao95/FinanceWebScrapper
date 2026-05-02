# Coding Conventions

**Analysis Date:** 2026-04-25

## Naming Patterns

**Files:**
- Python source modules: lowercase with underscores (snake_case): `financial_analytics.py`, `trading_indicators.py`, `request_handler.py`
- Test files: prefixed `test_` followed by category and target: `test_unit_<module>.py`, `test_integration_routes.py`, `test_regression_indicators.py`, `test_e2e_golden_path.py`, `test_<feature>.py`
- JavaScript files in `static/js/`: camelCase: `analyticsRenderer.js`, `displayManager.js`, `stockScraper.js`
- Fixture data files: snake_case with descriptors: `volume_profile_ohlcv.csv`, `spy_2017_2021.npy`

**Classes:**
- PascalCase: `FinancialAnalytics`, `OptionsPricer`, `BaseScraper`, `YahooFinanceScraper`, `TechnicalIndicators`, `CNNFearGreedScraper`, `EnhancedSentimentScraper`
- Scrapers always end with `Scraper` (e.g., `FinvizScraper`, `GoogleFinanceScraper`, `AlphaVantageAPIScraper`)
- Calibrators end with `Calibrator` (e.g., `HestonCalibrator`, `MertonCalibrator`)

**Functions:**
- snake_case: `compute_volume_profile`, `fetch_ohlcv`, `make_request`, `run_scrapers_for_ticker`, `convert_numpy_types`
- Private methods/helpers prefixed with single underscore: `_scrape_data`, `_parse_numeric_value`, `_extract_metric`, `_analyze_valuation`, `_normal_cdf`
- Module-level convenience wrappers mirror class method names: e.g., `black_scholes(...)` wraps `OptionsPricer().black_scholes(...)`

**Variables:**
- snake_case for locals and module globals: `mock_stock_data`, `cum_delta_last`, `pool_connections`
- UPPER_SNAKE_CASE for constants and module-level fixtures: `BASE_DIR`, `LOGS_DIR`, `CONFIG_FILE`, `FIXTURES_DIR`, `EXPECTED_POC`, `EXPECTED_VAH`, `_OPTION_PARAMS`, `_HESTON_PARAMS`
- Leading underscore on module-level "private" globals: `_session`, `_OPTION_PARAMS`

**Types:**
- Type hints from `typing` module: `Dict`, `List`, `Tuple`, `Optional`, `Optional[Dict]`, `Optional[float]`
- Pandas/numpy types referenced directly: `pd.DataFrame`, `np.ndarray`

## Code Style

**Formatting:**
- `black` declared in `requirements.txt` as a dev dependency (no `pyproject.toml` config — defaults assumed: 88-char line, double quotes)
- Indentation: 4 spaces (Python), 2 spaces (HTML/JS — implicit)
- No `pyproject.toml`, `setup.cfg`, `.flake8`, or `.pre-commit-config.yaml` present — formatting is convention-only, not enforced

**Linting:**
- `flake8` listed in `requirements.txt` but no config file present — defaults apply
- No CI lint job in `.github/workflows/keep-alive.yml`

**String formatting:**
- f-strings preferred throughout: `f"Error scraping data for {ticker}: {str(e)}"`
- Logger messages use f-strings: `self.logger.info(f"Fetching statistics from Yahoo Finance for {ticker}")`

**Quotes:**
- Single quotes dominant in source code: `'call'`, `'AAPL'`, `'Close'`
- Double quotes used inside f-strings and for messages with apostrophes

## Import Organization

**Order observed in `webapp.py`, `src/analytics/financial_analytics.py`, scrapers:**
1. Standard library: `import os`, `import sys`, `import json`, `import logging`, `from datetime import datetime, timedelta`
2. Third-party: `import numpy as np`, `import pandas as pd`, `import requests`, `from flask import Flask`, `import yfinance as yf`, `from sklearn.preprocessing import StandardScaler`
3. Local relative imports: `from .base_scraper import BaseScraper`, `from ..utils.request_handler import make_request`
4. Local absolute imports (in tests/webapp): `from src.analytics.financial_analytics import FinancialAnalytics`, `from src.scrapers.yahoo_scraper import YahooFinanceScraper`

**Path Aliases:**
- None (no `tsconfig.json`, no Python path aliases). `webapp.py` mutates `sys.path`: `sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))`
- Tests import via `from src.<package>.<module> import ...` from project root

**Lazy imports:**
- Used to defer heavy ML library loads (torch, transformers): see `webapp.py:60-67` `get_enhanced_sentiment_scraper()` and `get_financial_analytics()` helpers
- Top-level `try / except ImportError` pattern for optional deps: `try: import openai\nexcept ImportError: openai = None` (`webapp.py:23-26`)

## Error Handling

**Patterns:**
- **Library/scraper layer raises `ValueError`** for invalid inputs:
  ```python
  if T <= 0:
      raise ValueError("Time to maturity must be positive")
  if sigma <= 0:
      raise ValueError("Volatility must be positive")
  ```
  See `src/derivatives/options_pricer.py:63-68`, `src/derivatives/implied_volatility.py:126-130`, `src/analytics/trading_indicators.py:35` (`raise ValueError(f"No OHLCV data returned for {ticker}")`)

- **Scraper base class swallows exceptions and returns error dict** (`src/scrapers/base_scraper.py:42-46`):
  ```python
  try:
      return self._scrape_data(ticker)
  except Exception as e:
      self.logger.error(f"Error scraping data for {ticker}: {str(e)}")
      return {"error": f"Error scraping data: {str(e)}"}
  ```

- **Flask routes wrap entire handler in try/except, return JSON with HTTP status code** (`webapp.py:281-356`):
  ```python
  try:
      payload = request.get_json()
      if not payload:
          return jsonify({'success': False, 'error': 'No data provided'}), 400
      # ...success path
      return jsonify({'success': True, 'analysis': analysis, ...})
  except Exception as e:
      logger.error(f"Error in fundamental_analysis endpoint: {str(e)}")
      return jsonify({'success': False, 'error': str(e)}), 500
  ```

- **HTTP request retry with backoff** in `src/utils/request_handler.py:70-123`: 3 retries on `RequestException`, 429 status forces explicit retry loop, raises `RequestException` after exhaustion

- **Bare `except:` blocks present in `src/utils/email_utils.py`** at lines 232, 327, 454, 476, 511 — antipattern (catches `KeyboardInterrupt`/`SystemExit`)

**Response shape conventions for Flask routes:**
- Success: `{'success': True, '<payload_key>': <data>, 'timestamp': '<YYYY-MM-DD HH:MM:SS>'}`
- Validation error: HTTP 400, `{'success': False, 'error': '<message>'}`
- Internal error: HTTP 500, `{'success': False, 'error': str(e)}`
- Some routes return error keys without `success` field (e.g., `/api/footprint`, `/api/trading_indicators`) — return HTTP 200 with `{'error': '<message>'}` body when ticker is missing

## Logging

**Framework:** Python `logging` (stdlib)

**Patterns:**
- **Class-scoped logger** named after class: `self.logger = logging.getLogger(self.__class__.__name__)` — used in `BaseScraper`, `FinancialAnalytics`, `OptionsPricer` (`src/scrapers/base_scraper.py:21`, `src/analytics/financial_analytics.py:34`)
- **Module-scoped logger**: `logger = logging.getLogger(__name__)` — used in `request_handler.py`, `email_utils.py`, `model_calibration.py`, `volatility_surface.py`
- **App-scoped logger** in `webapp.py:100`: `logger = logging.getLogger(__name__)` plus `RotatingFileHandler` writing to `logs/webapp.log` (5MB max, 5 backups)
- **Level usage:**
  - `info`: progress and successful operations (`Fetching statistics for {ticker}`, `Successfully scraped...`)
  - `warning`: missing data, rate limits, fallbacks (`Could not find snapshot table for {ticker}`)
  - `error`: caught exceptions, request failures (`Error scraping data for {ticker}: ...`)
  - `debug`: low-volume diagnostics (`Successfully fetched data from {url}`)
- All log messages use f-strings; no structured logging

## Comments

**When to Comment:**
- Module-level docstring describes the module purpose and lists capabilities (e.g., `src/analytics/financial_analytics.py:1-9`)
- Class docstrings on every class describing its role
- Public method docstrings mandatory; private methods (`_foo`) typically have shorter docstrings
- Inline comments mark phase boundaries: `# Phase 09-01 decision`, `# Phases 19-22 replace stub bodies`
- Tactical inline comments explain non-obvious math: `# d1: Standardized distance to strike price, adjusted for drift...`

**Docstring Style (Google-style):**
```python
def compute_pct_increase(base: float, new: float, initial_investment: float) -> Optional[float]:
    """
    Safely compute percentage increase as a percentage of initial investment.

    Args:
        base (float): The base value
        new (float): The new value
        initial_investment (float): The initial investment amount

    Returns:
        Optional[float]: Percentage change relative to initial investment, or None if initial_investment is zero
    """
```
- `Args:` and `Returns:` sections present on most public functions
- `Raises:` documented when applicable (`src/utils/request_handler.py:84-86`)
- No Sphinx/reST docstring style used

## Function Design

**Size:** No enforced limit; analytics modules contain large multi-hundred-line methods (e.g., `compute_volume_profile` ~80 lines, `fundamental_analysis` ~150 lines including helpers)

**Parameters:**
- Type hints used inconsistently — well-typed in `src/analytics/financial_analytics.py`, `src/derivatives/options_pricer.py`; older scraper files have no type hints
- Default values for optional params: `option_type: str = 'call'`, `delay=1`, `auto_adjust: bool = True`
- Keyword arguments preferred for complex calls

**Return Values:**
- Analytics/pricer functions return dicts with named keys: `{'price': ..., 'delta': ..., 'gamma': ..., 'theta': ..., 'vega': ..., 'rho': ...}`
- Scrapers return dicts of metric_name → value, or `{"error": "<msg>"}` on failure
- Compute functions for plot routes return dicts with Plotly-shaped payload: `{'traces': [...], 'layout': {...}, 'signal': '...', ...}`

## Module Design

**Exports:**
- `__init__.py` files exist in each src package but are empty (no explicit re-exports)
- Imports done by full dotted path: `from src.analytics.trading_indicators import compute_footprint`

**Barrel Files:**
- Not used. Each module imported explicitly.

**Singleton patterns:**
- Connection pool: `_session` global in `src/utils/request_handler.py` lazy-initialized via `get_session()` (lines 14, 58-68)

## Inheritance & Abstraction

**ABC pattern for scrapers:** `src/scrapers/base_scraper.py:10-59`
```python
class BaseScraper(ABC):
    def get_data(self, ticker):  # template method
        try:
            return self._scrape_data(ticker)
        except Exception as e:
            self.logger.error(...)
            return {"error": ...}

    @abstractmethod
    def _scrape_data(self, ticker):
        pass
```
All concrete scrapers (`YahooFinanceScraper`, `FinvizScraper`, `GoogleFinanceScraper`, `CNNFearGreedScraper`, `AlphaVantageAPIScraper`, `FinhubAPIScraper`) override `_scrape_data`.

## Numeric / JSON Conventions

- All numpy types converted to native Python via `convert_numpy_types(...)` (`webapp.py:144-177`) before `jsonify()` to avoid JSON serialization errors
- NaN and Inf converted to `None` to produce valid JSON
- Pandas DatetimeIndex stripped of timezone: `df.index.tz_localize(None) if df.index.tz is not None else df.index` (`src/analytics/trading_indicators.py:36`)

## Configuration

- `config.json` loaded at app start (`webapp.py:114-127`); never mutated at runtime
- Environment variables read via `os.environ.get(...)` with sensible defaults
- `python-dotenv` loaded at top of `webapp.py` and `email_utils.py`: `load_dotenv()`
- Cloud detection helper `is_cloud_environment()` checks for `RENDER`, `RENDER_SERVICE_ID`, `RENDER_EXTERNAL_URL` env vars (`webapp.py:70-80`)

---

*Convention analysis: 2026-04-25*
