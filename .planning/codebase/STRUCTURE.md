# Codebase Structure

**Analysis Date:** 2026-04-26

## Directory Layout

```
FinanceWebScrapper/
├── webapp.py               # Flask web application (2250 lines) — primary server entry point
├── main.py                 # CLI scraper entry point (1012 lines) — batch/scheduled runs
├── config.json             # Runtime configuration (tickers, email recipients, portfolio allocations)
├── config.json.example     # Template for config.json (committed; config.json is gitignored)
├── requirements.txt        # Python package dependencies
├── runtime.txt             # Python version pin (3.13.0) for Render
├── Procfile                # gunicorn start command for Render
├── render.yaml             # Render deployment configuration
├── Makefile                # Test runner shortcuts (test, test-unit, test-integration, etc.)
├── setup.py                # Package installation (legacy, not used for deployment)
├── keep_alive.py           # Deprecated keep-alive script (superseded by Uptime Monitor)
├── ANALYTICS_GUIDE.md      # Developer reference for analytics modules
├── run_scraper.sh           # Shell wrapper for CLI scraper
├── uat_run_scraper.sh       # UAT shell wrapper
├── start_webapp.sh          # Shell script to launch Flask dev server (Unix)
├── start_webapp.bat         # Shell script to launch Flask dev server (Windows)
├── src/                    # All importable Python source modules
│   ├── __init__.py
│   ├── scrapers/           # Data collection from external sources
│   ├── indicators/         # Technical indicator computation
│   ├── analytics/          # Quantitative analytics and ML models
│   ├── derivatives/        # Options pricing and volatility models
│   ├── sentiment/          # Sentiment analysis pipeline
│   └── utils/              # Shared utilities (formatting, email, storage, HTTP)
├── templates/              # Flask Jinja2 templates
│   └── index.html          # Single-page app shell
├── static/                 # Frontend static assets
│   ├── css/
│   │   └── styles.css
│   └── js/                 # Modular frontend JavaScript (23 files)
├── tests/                  # Pytest test suite
│   ├── conftest.py         # Shared fixtures (Flask client, mock data, session fixtures)
│   ├── fixtures/           # Static test data files (.npy, .csv, .json)
│   └── test_*.py           # Individual test modules (28 files)
├── scripts/
│   └── generate_fixtures.py  # Script to regenerate test fixture files
├── snippets/               # Ad-hoc development scripts (not production code)
├── logs/                   # Runtime log files (gitignored except .gitkeep)
└── .github/
    └── workflows/
        └── keep-alive.yml  # GitHub Actions workflow (deprecated keep-alive)
```

## Directory Purposes

**`src/scrapers/`**
- Purpose: Data collection from Yahoo Finance, Finviz, Google Finance, CNN Fear & Greed, Alpha Vantage, and Finnhub APIs
- Contains: One class per data source, all extending `BaseScraper`
- Key files:
  - `src/scrapers/base_scraper.py` — abstract base class `BaseScraper` (ABC)
  - `src/scrapers/yahoo_scraper.py` — `YahooFinanceScraper`
  - `src/scrapers/finviz_scraper.py` — `FinvizScraper`
  - `src/scrapers/google_scraper.py` — `GoogleFinanceScraper`
  - `src/scrapers/cnn_scraper.py` — `CNNFearGreedScraper`
  - `src/scrapers/api_scraper.py` — `AlphaVantageAPIScraper`, `FinhubAPIScraper`
  - `src/scrapers/enhanced_sentiment_scraper.py` — `EnhancedSentimentScraper` (heavy; lazy-loaded in webapp)

**`src/indicators/`**
- Purpose: Technical indicator computation (RSI, MACD, Bollinger Bands, etc.)
- Key files:
  - `src/indicators/technical_indicators.py` — `TechnicalIndicators` class

**`src/analytics/`**
- Purpose: Quantitative analytics, ML models, regime detection, and advanced financial computations
- Key files:
  - `src/analytics/financial_analytics.py` — `FinancialAnalytics` class (1733 lines; lazy-loaded in webapp)
  - `src/analytics/trading_indicators.py` — volume profile, anchored VWAP, order flow, liquidity sweep, footprint (module-level functions, 833 lines)
  - `src/analytics/regime_detection.py` — `RegimeDetector` class (HMM-based)
  - `src/analytics/rl_models.py` — reinforcement learning (policy iteration, Q-learning, MDP)
  - `src/analytics/markov_chains.py` — steady-state, absorption probabilities, portfolio MDP
  - `src/analytics/interest_rate_models.py` — CIR and Vasicek models, `CIRCalibrator` class
  - `src/analytics/credit_transitions.py` — credit rating transition matrices, default probabilities

**`src/derivatives/`**
- Purpose: Options pricing, implied volatility, volatility surface construction, model calibration
- Key files:
  - `src/derivatives/options_pricer.py` — `OptionsPricer` class + standalone `black_scholes()` function
  - `src/derivatives/fourier_pricer.py` — Heston, Merton, BCC pricing via Fourier transform
  - `src/derivatives/implied_volatility.py` — `ImpliedVolatilityCalculator`
  - `src/derivatives/volatility_surface.py` — `VolatilitySurfaceBuilder`
  - `src/derivatives/model_calibration.py` — `HestonCalibrator`, `BCCCalibrator`, `MertonCalibrator`
  - `src/derivatives/trinomial_model.py` — `TrinomialModel`

**`src/sentiment/`**
- Purpose: NLP-based sentiment analysis pipeline (news, Reddit, Google Trends)
- Key files:
  - `src/sentiment/sentiment_analyzer.py` — `SentimentAnalyzer`, `NewsCollector`, `RedditCollector`, `GoogleTrendsCollector`, `TopicAnalyzer`, `EnhancedSentimentAnalyzer` (598 lines)

**`src/utils/`**
- Purpose: Cross-cutting utilities used by both `webapp.py` and `main.py`
- Key files:
  - `src/utils/data_formatter.py` — `format_data_as_dataframe()`, `save_to_csv()`, `save_to_excel()`
  - `src/utils/display_formatter.py` — terminal display formatting
  - `src/utils/email_utils.py` — HTML email generation and SMTP delivery (1281 lines)
  - `src/utils/mongodb_storage.py` — `MongoDBStorage` class (optional local persistence)
  - `src/utils/request_handler.py` — shared HTTP session with retry logic (`make_request()`, `get_session()`)
  - `src/utils/comparison_utils.py` — peer comparison, ranking, stock screener

**`templates/`**
- Purpose: Flask Jinja2 HTML templates
- Contains: Single file `index.html` — the SPA shell rendered on `GET /`

**`static/`**
- Purpose: Frontend assets served directly by Flask
- `static/css/styles.css` — all application styles (single stylesheet)
- `static/js/` — 23 modular JavaScript files:
  - `main.js` — application bootstrap
  - `state.js` — shared client-side state
  - `api.js` — fetch wrappers for backend API calls
  - `forms.js` — form submission handling
  - `tabs.js` — tab switching logic
  - `displayManager.js` — result display orchestration
  - `stockScraper.js` — stock scraping UI
  - `tradingIndicators.js` — trading indicator display
  - `analyticsRenderer.js` — analytics result rendering
  - `optionsPricing.js` / `optionsDisplay.js` — options pricing UI
  - `stochasticModels.js` — stochastic model parameter forms
  - `volatilitySurface.js` — volatility surface charts
  - `dcfValuation.js` — DCF input/output
  - `earningsQuality.js` — earnings quality display
  - `healthScore.js` — health score rendering
  - `peerComparison.js` — peer comparison tables
  - `portfolioHealth.js` — portfolio metrics display
  - `rlModels.js` — reinforcement learning UI
  - `chatbot.js` — chatbot interface
  - `autoRun.js` — automatic refresh logic
  - `keepAlive.js` — client-side ping (deprecated)
  - `utils.js` — shared JS helpers

**`tests/`**
- Purpose: Full pytest test suite
- Contains: 28 test files spanning unit, integration, regression, and e2e categories
- Key files:
  - `tests/conftest.py` — shared fixtures: `client` (Flask test client), `flask_server` (live server), `spy_returns`, `standard_heston_params`, `zero_default_matrix`, `market_yields_normal`
  - `tests/fixtures/` — static binary/CSV/JSON test data (`.npy`, `.csv`, `.json`); committed to git

## Key File Locations

**Entry Points:**
- `webapp.py` — Flask application; `gunicorn webapp:app` is the production start command
- `main.py` — CLI entry point for batch scraping runs

**Configuration:**
- `config.json` — active runtime config (gitignored; create from `config.json.example`)
- `.env` — secrets and API keys (gitignored; create from `.env.example`)
- `render.yaml` — Render PaaS deployment spec

**Core Logic:**
- `src/analytics/financial_analytics.py` — DCF, earnings quality, peer comparison, portfolio health
- `src/analytics/trading_indicators.py` — volume profile, VWAP, order flow, footprint
- `src/scrapers/base_scraper.py` — abstract `BaseScraper` all scrapers inherit from
- `src/utils/email_utils.py` — HTML email report generation and delivery

**Testing:**
- `tests/conftest.py` — all shared fixtures
- `tests/fixtures/` — committed static test data
- `Makefile` — test category shortcuts (`make test`, `make test-unit`, etc.)

## Naming Conventions

**Files:**
- Source modules: `snake_case.py`
- Test files: `test_<subject>.py` matching the module or feature under test
- Math-pinned tests: `test_math<NN>_<description>.py` (e.g., `test_math01_coupon_discounting.py`)

**Directories:**
- All lowercase, underscore-separated

## Where to Add New Code

**New data source (scraper):**
- `src/scrapers/<source>_scraper.py` extending `BaseScraper`
- Wire up in `webapp.py::run_scrapers_for_ticker()` and `main.py`

**New analytics function:**
- `src/analytics/<domain>.py` or add to existing domain file
- Add Flask route in `webapp.py` with `@app.route('/api/<endpoint>', methods=['POST'])`

**New Flask API route:**
- Add to `webapp.py`; return `jsonify(...)` for all API endpoints
- Tests: `tests/test_integration_routes.py`

**New frontend feature:**
- Add JS module: `static/js/<feature>.js`
- Wire into `static/js/main.js` or appropriate orchestrator
- Styles: `static/css/styles.css`

**Frontend framework migration:**
- Current: 23 vanilla JS modules (~8,500 lines), no build step
- Hook point: `static/js/main.js` bootstraps everything — React/Vue can take over individual feature modules incrementally
- `state.js` is the Zustand/context analog — replace first if adopting React state management

---

*Structure analysis: 2026-04-26*
