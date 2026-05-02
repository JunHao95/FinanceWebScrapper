# Technology Stack

**Analysis Date:** 2026-04-25

## Languages

**Primary:**
- Python 3.13.0 - Backend, scrapers, analytics, financial models, web server (`webapp.py`, `main.py`, `src/`)
- Vanilla JavaScript (ES6, browser-native) - Frontend interactivity, all UI logic (`static/js/*.js`)

**Secondary:**
- HTML5 - Single-page templating via Jinja2 (`templates/index.html`, 1370 lines)
- CSS3 - Styling with custom properties / dark glassmorphism theme (`static/css/styles.css`, 1538 lines)
- Bash - Shell scripts for CLI scraper runs (`run_scraper.sh`, `start_webapp.sh`, `uat_run_scraper.sh`)
- Batch - Windows launcher (`start_webapp.bat`)
- YAML - CI workflow + Render deployment manifest (`.github/workflows/keep-alive.yml`, `render.yaml`)

## Runtime

**Environment:**
- Python 3.13.0 (pinned in `runtime.txt` and `render.yaml`)
- Production WSGI: `gunicorn==21.2.0` with `--workers 1 --timeout 600` (`Procfile`)
- Local dev: `flask run` / `python webapp.py` via `start_webapp.sh`

**Package Manager:**
- pip (Python) - dependencies in `requirements.txt`
- Lockfile: NOT present (no `Pipfile.lock`, `poetry.lock`, or `requirements.lock`); versions use `>=` constraints
- No JavaScript package manager - **no `package.json`, `node_modules`, or lockfile exists**. All JS dependencies are loaded via `<script>` tags from CDNs in `templates/index.html`.

## Frameworks

**Core (Backend):**
- Flask >= 2.3.0 - Web application framework, exposes 36+ JSON API routes (`webapp.py`)
- Flask-Cors >= 4.0.0 - CORS handling (declared but not visibly invoked in `webapp.py`)
- Werkzeug (transitive via Flask) - WSGI utilities, request/response

**Frontend (No framework):**
- **Plain vanilla JavaScript** - No React, Vue, Svelte, Angular, or jQuery. UI is built from 23 hand-written modules in `static/js/` totaling ~8,500 lines.
- **Module pattern:** Each JS file declares a global namespace object (e.g. `AppState`, `API`, `Utils`, `TabManager`, `FormManager`, `DisplayManager`, `KeepAlive`, `StockScraper`, `OptionsPricing`, `VolatilitySurface`, `AnalyticsRenderer`, `OptionsDisplay`). Loaded in dependency order via `<script>` tags in `templates/index.html` lines 1345-1367.
- **Templating:** Jinja2 (Flask-bundled) — used minimally; `templates/index.html` is essentially a static SPA shell.
- **No build step:** No webpack/vite/rollup/esbuild/babel. JS is served raw from `static/js/`. Cache-busting via query strings (e.g. `displayManager.js?v=2.2`).
- **CommonJS export shim:** `static/js/utils.js:79` and `static/js/state.js:18` include `if (typeof module !== 'undefined' && module.exports)` blocks for theoretical Node testing, but this is unused.

**Frontend Libraries (CDN):**
- Plotly.js 2.27.0 - 3D interactive charts, heatmaps, volatility surfaces (loaded from `https://cdn.plot.ly/plotly-2.27.0.min.js` in `templates/index.html:8`). Used heavily by `static/js/rlModels.js`, `static/js/stochasticModels.js`, `static/js/autoRun.js`, `static/js/volatilitySurface.js`.
- Google Fonts - Inter (400/600/700) + JetBrains Mono (400/600), loaded via `https://fonts.googleapis.com/css2` in `templates/index.html:10`.
- **No CSS framework** - no Bootstrap, Tailwind, Bulma, etc. Custom CSS uses CSS variables (`--bg-deep`, `--accent`, `--border-glass`) for a dark glassmorphism aesthetic (`static/css/styles.css:6-21`).

**Testing:**
- pytest >= 7.0.0 - Test runner with custom markers `unit`, `integration`, `regression`, `e2e`, `slow` (`tests/conftest.py:20-26`)
- pytest-flask >= 1.3.0 - Flask test client fixtures
- pytest-playwright >= 0.4.0 - Browser-based E2E tests (chromium)
- responses >= 0.25.0 - HTTP request mocking
- 30 test files in `tests/` covering analytics, derivatives, integration routes, regression, and golden-path E2E

**Build/Dev:**
- Make - Test orchestration (`Makefile`): `make test`, `make test-unit`, `make test-integration`, `make test-regression`, `make test-e2e`
- black >= 22.8.0 - Python formatter (declared, not enforced via hooks)
- flake8 >= 5.0.4 - Python linter (declared, not enforced via hooks)
- setuptools - Packaging via `setup.py` (entry point `stock-scraper=stock_scraper.main:main`)

## Key Dependencies

**Critical (Web Scraping & Data):**
- requests >= 2.28.1 - HTTP client (used by every scraper; centralized in `src/utils/request_handler.py`)
- beautifulsoup4 >= 4.11.1 - HTML parsing for Yahoo, Finviz, Google scrapers
- lxml >= 4.9.1 + lxml_html_clean >= 0.1.0 - Fast XML/HTML parser
- yfinance >= 0.2.18 - Yahoo Finance API client (used in `src/scrapers/yahoo_scraper.py`, `src/indicators/technical_indicators.py`, `src/analytics/regime_detection.py`, `src/analytics/financial_analytics.py`, `src/analytics/trading_indicators.py`, `src/derivatives/volatility_surface.py`)

**Critical (Data Science):**
- pandas >= 1.5.0 - DataFrames, time series
- numpy >= 1.23.0 - Numerical arrays
- scipy >= 1.9.0 - Optimization (`scipy.optimize.brute`, `fmin`, `minimize`), integration (`scipy.integrate.quad`), stats (`scipy.stats.norm`), interpolation (`scipy.interpolate.griddata`) - heavily used in `src/derivatives/` and `src/analytics/interest_rate_models.py`
- scikit-learn >= 1.1.0 - PCA, StandardScaler, LinearRegression, TfidfVectorizer, KMeans (`src/analytics/financial_analytics.py`, `src/sentiment/sentiment_analyzer.py`)

**Critical (ML/Sentiment - lazy-loaded):**
- transformers >= 4.21.0 - FinBERT model loader (`src/sentiment/sentiment_analyzer.py:23`)
- torch >= 1.12.0 - PyTorch backend for transformers (>500MB memory; lazy-loaded in `webapp.py:59-67` via `get_enhanced_sentiment_scraper()`)
- nltk >= 3.8.0 - VADER sentiment, tokenization (auto-downloads `vader_lexicon`, `punkt`, `stopwords` on import)
- pytrends >= 4.9.0 - Google Trends data
- feedparser >= 6.0.0 - RSS feed parsing for news sentiment
- newspaper3k >= 0.2.8 - Article extraction
- praw >= 7.6.0 - Reddit API client (`src/sentiment/sentiment_analyzer.py:217`)

**Critical (LLM Chatbot):**
- openai >= 1.0.0 - Imported optionally (`webapp.py:23-26`) but actual chat uses raw `requests.post` to Groq/Ollama HTTP endpoints (`webapp.py:2013, 2037`)

**Critical (Storage & Export):**
- pymongo >= 4.5.0 - MongoDB client (`src/utils/mongodb_storage.py`)
- xlsxwriter >= 3.0.3 - Excel export engine (`src/utils/data_formatter.py:132`)
- tabulate >= 0.9.0 - Console + email table formatting

**Visualization (server-side):**
- plotly >= 5.0.0 - `plotly.graph_objects`, `plotly.subplots` for trading indicator charts (`src/analytics/trading_indicators.py:11-12`)
- matplotlib >= 3.5.0 - Used in `src/utils/comparison_utils.py:8`
- seaborn >= 0.12.0 - Declared but minimal use

**Infrastructure:**
- python-dotenv >= 1.0.0 - `.env` loader, called at top of `webapp.py:29` and `main.py:19`
- gunicorn == 21.2.0 - Production WSGI server (only pinned exact version)

## Configuration

**Environment:**
- `.env` file (gitignored) loaded via `dotenv.load_dotenv()` at `webapp.py:29`
- `.env.example` documents required vars (`ALPHA_VANTAGE_API_KEY`, `FINHUB_API_KEY`, `FINANCE_SENDER_EMAIL`, `FINANCE_SENDER_PASSWORD`, `FINANCE_SMTP_SERVER`, `FINANCE_SMTP_PORT`, `FINANCE_USE_TLS`, `SECRET_KEY`, `FLASK_DEBUG`, `PORT`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`)
- Optional: `GROQ_API_KEY`, `GROQ_MODEL`, `OLLAMA_API_URL`, `OLLAMA_MODEL`, `MONGODB_ENABLED`, `ENABLE_SENTIMENT_ANALYSIS`, `ENABLE_ADVANCED_ANALYTICS`, `CONNECTION_POOL_SIZE`, `CONNECTION_POOL_MAXSIZE`, `RENDER`, `RENDER_SERVICE_ID`
- `config.json` (gitignored) for portfolio allocations, MongoDB, email defaults, logging — schema in `config.json.example`

**Build:**
- `setup.py` - setuptools packaging (`name="stock_scraper"`, `version="0.1.0"`)
- `Procfile` - Heroku/Render-style start command
- `render.yaml` - Render Blueprint with env var declarations
- `runtime.txt` - Python version pin (`python-3.13.0`)
- `Makefile` - test target shortcuts
- `.renderignore` - excludes `__pycache__`, `venv`, `.env`, `config.json`, `logs/*` from deploy

## Platform Requirements

**Development:**
- Python 3.13.0 (or any 3.7+ per `setup.py` `python_requires`)
- pip (no Pipenv/Poetry)
- Optional MongoDB instance at `mongodb://localhost:27017/`
- Optional Ollama at `http://localhost:11434/api/chat` for local LLM chatbot
- ~2GB free disk for `transformers` + `torch` if sentiment analysis enabled

**Production:**
- Render.com free-tier web service (Oregon region) per `render.yaml`
- 512MB RAM constraint - drives `--workers 1` and `ENABLE_SENTIMENT_ANALYSIS=false` defaults
- Health check: `/health` endpoint
- External keep-alive: GitHub Actions cron pings every 10min (`.github/workflows/keep-alive.yml`); legacy `keep_alive.py` script is deprecated

---

*Stack analysis: 2026-04-25*
