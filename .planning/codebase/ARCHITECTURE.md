# Architecture

**Analysis Date:** 2026-04-25

## Pattern Overview

**Overall:** Server-rendered Flask application with thin HTML shell + multi-module vanilla JavaScript SPA-like behavior on a single page. Backend follows a layered modular Python structure with abstract base classes for scrapers and lazy-loaded heavy ML/analytics modules.

**Key Characteristics:**
- Monolithic Flask backend (`webapp.py`, ~2,250 lines) exposing 33 JSON API endpoints + a single HTML route.
- Frontend is a single Jinja-rendered HTML page (`templates/index.html`, 1,370 lines) wired to ~24 hand-written ES5/ES6 JavaScript modules loaded via `<script>` tags in dependency order (no bundler, no framework).
- All UI state and interactivity is client-side via global module objects (`AppState`, `FormManager`, `TabManager`, `API`, `DisplayManager`, `AnalyticsRenderer`, etc.). Communication with the backend is through `fetch()` JSON calls.
- Two parallel entry points: CLI (`main.py`) for batch scraping with persistence to MongoDB/CSV, and Flask web app (`webapp.py`) for interactive analysis (MongoDB explicitly disabled in webapp config).
- Heavy modules (PyTorch, transformers, sklearn-based analytics, derivatives pricers) are imported lazily inside route handlers to keep cold-start memory usage low on Render free tier.

## Layers

**Presentation Layer (Browser):**
- Purpose: Render the UI, capture user input, call JSON APIs, format and visualize results.
- Location: `templates/index.html`, `static/css/styles.css`, `static/js/*.js`
- Contains: One HTML document with five top-level "main tabs" (Stock Analysis, Options Pricing, Volatility Surface, Stochastic Models, Reinforcement Learning). All sub-views are nested `<div>` panels toggled by class `active`. Plotly.js (CDN, v2.27.0) is the only third-party JS dependency.
- Depends on: Backend JSON APIs under `/api/*`.
- Used by: End user via browser.

**HTTP / Routing Layer:**
- Purpose: Accept HTTP requests, validate payloads, delegate to scrapers/analytics, return JSON.
- Location: `webapp.py` (Flask app, all routes inline)
- Contains: 33 `@app.route` handlers, request validation, JSON serialization (`convert_numpy_types` helper for NumPy → native Python), error handlers for 404/500, `/health` endpoint for keep-alive.
- Depends on: `src/scrapers/*`, `src/analytics/*`, `src/derivatives/*`, `src/indicators/*`, `src/utils/*`.
- Used by: Frontend `fetch()` calls in `static/js/api.js`, `static/js/stochasticModels.js`, `static/js/autoRun.js`, `static/js/rlModels.js`, `static/js/portfolioHealth.js`, `static/js/peerComparison.js`, `static/js/tradingIndicators.js`, `static/js/chatbot.js`.

**Scraping Layer:**
- Purpose: Fetch raw financial data from external sources (HTTP scraping + REST APIs).
- Location: `src/scrapers/`
- Contains: `BaseScraper` (ABC) in `src/scrapers/base_scraper.py` defining `_scrape_data(ticker)` contract. Concrete classes: `YahooFinanceScraper`, `FinvizScraper`, `GoogleFinanceScraper`, `CNNFearGreedScraper`, `AlphaVantageAPIScraper`, `FinhubAPIScraper`, `EnhancedSentimentScraper` (FinBERT/transformers — heavy, lazy-loaded).
- Depends on: `src/utils/request_handler.py` for HTTP, `requests`, `beautifulsoup4`, `yfinance`.
- Used by: `webapp.py` `/api/scrape` and `main.py`.

**Analytics & Modeling Layer:**
- Purpose: Compute derived insights (analytics, pricing models, regime detection, RL agents).
- Location: `src/analytics/`, `src/derivatives/`, `src/indicators/`
- Contains:
  - `src/analytics/financial_analytics.py`: PCA, Monte Carlo VaR, regression, correlation, fundamental analysis scoring.
  - `src/analytics/regime_detection.py`: 2-state Hidden Markov Model on log-returns.
  - `src/analytics/markov_chains.py`, `src/analytics/credit_transitions.py`: Discrete-time Markov modeling.
  - `src/analytics/interest_rate_models.py`: Vasicek, CIR.
  - `src/analytics/rl_models.py`: MDPs, policy iteration, gridworld, Q-learning, portfolio rotation.
  - `src/analytics/trading_indicators.py`: VWAP, volume profile, footprint, order flow, liquidity sweeps.
  - `src/derivatives/options_pricer.py`, `fourier_pricer.py`, `trinomial_model.py`, `volatility_surface.py`, `model_calibration.py`, `implied_volatility.py`.
  - `src/indicators/technical_indicators.py`: RSI, MA, Bollinger Bands.
- Depends on: `numpy`, `scipy`, `sklearn`, `pandas`, `yfinance` (for price history). PyTorch/transformers are isolated to sentiment.
- Used by: Flask route handlers (lazy-imported on first call).

**Utility Layer:**
- Purpose: Cross-cutting concerns — formatting, persistence, email, HTTP helpers.
- Location: `src/utils/`
- Contains: `data_formatter.py` (CSV/Excel/DataFrame), `display_formatter.py` (CLI report), `email_utils.py` (SMTP), `mongodb_storage.py` (CLI-only), `request_handler.py` (retry/headers), `comparison_utils.py`.
- Depends on: `pandas`, `tabulate`, `pymongo`, `smtplib`.
- Used by: All upper layers.

## Data Flow

**Primary "Run Analysis" Flow (frontend rendering pipeline):**

1. User loads `/` → Flask `index()` route in `webapp.py:276` calls `render_template('index.html')` returning the full static HTML shell with all five main-tab panels in the DOM (display: none for inactive).
2. Browser loads `static/css/styles.css` and 24 JS modules in declared order (see `templates/index.html:1345-1367`). On `DOMContentLoaded`, `static/js/main.js` verifies all module globals (`window.AppState`, `window.FormManager`, etc.) and calls each module's `init()`.
3. User enters tickers via chip-input widget (`FormManager.initChipInput`), optionally configures portfolio allocation, clicks "Run Analysis".
4. `StockScraper.handleSubmit` (`static/js/stockScraper.js`) builds JSON `{tickers, sources, alpha_key, finhub_key, portfolio_allocation}` and calls `API.scrapeStocks` (`static/js/api.js:9`).
5. `fetch('/api/scrape')` → Flask `scrape_data()` (`webapp.py:358`) runs scrapers in a `ThreadPoolExecutor` (up to 4 workers), then computes analytics, returns JSON.
6. Frontend stores result in `AppState.currentData` and `window.pageContext.tickerData`, then `DisplayManager.displayCnnMetrics` and `DisplayManager.createTickerCard` build HTML strings (no virtual DOM) and inject into `#cnnMetrics` and `#tickerResults` via `innerHTML`.
7. Tab navigation (`TabManager.switchTab`, `TabManager.switchMainTab`) toggles CSS class `active` on `.tab-content` and `.main-tab-content` divs to swap views without page reload.
8. Plotly charts are rendered via `Plotly.newPlot('elementId', data, layout)` from `autoRun.js`, `rlModels.js`, `volatilitySurface.js`, `stochasticModels.js`.

**Frontend Rendering Style:** Hybrid server-rendered shell + client-side AJAX. Specifically:
- The initial HTML payload is fully rendered server-side by Jinja (`templates/index.html`). The Jinja template contains *no* server-side data interpolation beyond static markup — it is essentially a static shell.
- All dynamic content (ticker cards, analytics panels, chart visualizations) is generated client-side by concatenating HTML strings inside JS modules and assigning to `innerHTML`/`appendChild`. There are 156 occurrences of `innerHTML`/`appendChild`/`createElement` across the JS modules.
- Tab switching is purely client-side CSS class toggling — no route changes, no history API. URL never changes after the initial load.
- This is a "single-page application" by behavior but built with no framework (no React/Vue/Svelte/Angular), no build step, no module bundler, no source maps, no TypeScript. Modules expose globals via `window.<ModuleName>`.

**Module loading dependency chain (declared in `static/js/main.js:5-19`):**
1. `state.js` (no deps) → defines `window.AppState`, `window.pageContext`.
2. `utils.js` (no deps) → `Utils.escapeHtml`, `Utils.showAlert`.
3. `tabs.js` (depends on AppState) → `TabManager`.
4. `forms.js` (depends on AppState, Utils) → `FormManager`.
5. `api.js` (no deps) → `API` with all `fetch()` wrappers.
6. Feature renderers: `healthScore.js`, `earningsQuality.js`, `dcfValuation.js`, `peerComparison.js`, `tradingIndicators.js`, `displayManager.js`, `analyticsRenderer.js`, `optionsDisplay.js`.
7. Long-running services: `keepAlive.js` (pings `/health` every 14 minutes).
8. Feature controllers: `stockScraper.js`, `optionsPricing.js`, `volatilitySurface.js`, `stochasticModels.js`, `rlModels.js`, `portfolioHealth.js`, `autoRun.js`, `chatbot.js`.
9. `main.js` (depends on all) → orchestrates init.

**State Management:** Two global objects on `window`:
- `AppState` (`static/js/state.js:5`): Last scrape results (`currentData`, `currentCnnData`), `currentTickers`, `currentAnalytics`, `tradingIndicatorsData`, keep-alive bookkeeping.
- `pageContext` (`static/js/state.js:23`): Shared cross-module context for the chatbot — `tickers`, `tickerData`, `portfolio`, `cnnFearGreed`, `stochasticResults`, `rlResults`. Populated after each successful scrape/model run.
- No reactive bindings; updates are imperative — modules set state then call display functions directly.

## Key Abstractions

**BaseScraper (ABC):**
- Purpose: Common interface for all data sources (web scrapers + REST API clients).
- Examples: `src/scrapers/base_scraper.py`, `src/scrapers/yahoo_scraper.py`, `src/scrapers/api_scraper.py`.
- Pattern: Abstract method `_scrape_data(ticker)` returning `dict`. Public `get_data(ticker)` adds delay + try/except logging. All scrapers inherit logger via `self.__class__.__name__`.

**JS Module Pattern:**
- Purpose: Namespacing without modules — each `static/js/*.js` file defines a top-level `const ModuleName = { ... }` and assigns `window.ModuleName = ModuleName`.
- Examples: `const FormManager = { ... }` in `static/js/forms.js:5`, `const StockScraper = { ... }` in `static/js/stockScraper.js:5`.
- Pattern: Modules expose `init()` for lifecycle setup, internal `_initialized` guards, and method-style functions called via `ModuleName.method(args)`. Cross-module access goes through `window.<Name>` globals.

**Analytics Modules:**
- Purpose: Stateless or short-lived calculators instantiated per request.
- Examples: `FinancialAnalytics(config)` in `src/analytics/financial_analytics.py:22`, `RegimeDetector` in `src/analytics/regime_detection.py`.
- Pattern: Class takes optional config dict in constructor, exposes calculation methods returning dicts of metrics. No persistent state across requests.

**Lazy Module Loaders:**
- Purpose: Defer importing PyTorch/transformers/sklearn until first use to reduce cold-start memory.
- Examples: `get_enhanced_sentiment_scraper()` in `webapp.py:59`, `get_financial_analytics()` in `webapp.py:64`. Each route handler also re-imports derivatives modules locally (e.g., `webapp.py:701: from src.derivatives.options_pricer import OptionsPricer`).
- Pattern: Top-level imports are commented out with rationale; helper function or local-scope `import` defers loading.

## Entry Points

**Web Application Entry Point:**
- Location: `webapp.py:2244` (`if __name__ == '__main__':`), production via `Procfile` (`gunicorn webapp:app --workers 1 --timeout 600`).
- Triggers: HTTP request from browser, gunicorn on Render.com, or `python webapp.py` locally.
- Responsibilities: Bootstrap Flask app, register routes, configure logging to `logs/webapp.log` (RotatingFileHandler 5MB×5), disable MongoDB in cloud, serve `index.html` and JSON APIs.

**CLI Entry Point:**
- Location: `main.py` (1,012 lines).
- Triggers: `python main.py [args]`, or wrapper scripts `run_scraper.sh` / `uat_run_scraper.sh` / `start_webapp.sh`.
- Responsibilities: Argparse-driven batch scraping, optional MongoDB persistence (config-driven via `config.json`), CSV/Excel export, email reporting, sentiment analysis.

**Keep-Alive Entry Point (deprecated):**
- Location: `keep_alive.py:95`.
- Triggers: Manual `python keep_alive.py` (deprecated — see file docstring; external uptime monitoring is now preferred).
- Responsibilities: Pings `https://finance-web-scrapper.onrender.com/health` every 10 minutes.

**Browser Entry Point:**
- Location: `static/js/main.js:93` (`DOMContentLoaded` listener).
- Triggers: Browser loads HTML and parses scripts.
- Responsibilities: Verify all 12 required modules are loaded, initialize each in dependency order with `safeInitialize` wrapper, register inline-handler globals (`window.switchTab`, `window.clearForm`, etc.), wire `beforeunload` and `visibilitychange` for keep-alive lifecycle.

## Error Handling

**Strategy:** Try/except at every API route handler returning `jsonify({'success': False, 'error': str(e)}), 500`. Frontend `API.*` wrappers throw on non-OK responses and use `AbortController` for timeouts (2–10 minutes scaled by ticker count for `/api/scrape`, 30s for most pricing calls, 60s for volatility surface, 5s for `/health`).

**Patterns:**
- Backend: `logger.error(f"Error in <route>: {str(e)}")` followed by JSON error response (see `webapp.py:351-356`). Generic 404/500 handlers (`webapp.py:2227-2242`).
- Frontend: All `API.*` methods wrap `fetch` with try/catch, special-casing `AbortError` to surface user-friendly timeout messages. UI surfaces errors via `Utils.showAlert(message, 'error')` (`static/js/utils.js:45`).
- DOM safety: Every JS module checks for required DOM elements with `document.getElementById(...)` and logs `console.error` if missing rather than crashing.

## Cross-Cutting Concerns

**Logging:**
- Backend: Python `logging` with `RotatingFileHandler` writing to `logs/webapp.log` and `logs/stock_scraper.log` (5MB × 5 backups). Each scraper class gets its own logger via `logging.getLogger(self.__class__.__name__)`.
- Frontend: `console.log` / `console.warn` / `console.error` only — no remote logging.

**Validation:**
- Backend: Manual checks in each route (`if not data or 'tickers' not in data: return 400`). No schema library (no Pydantic, no marshmallow).
- Frontend: `FormManager.parseTickersInput`, ticker validation via `/api/validate_ticker` (`static/js/forms.js:271`), portfolio allocation totals computed live in `FormManager.calculateAllocationTotal`.

**Authentication:**
- None. App is unauthenticated. API keys (Alpha Vantage, Finhub, OpenAI) flow through environment variables or per-request payload fields.

**XSS Mitigation:**
- All user/API content is HTML-escaped via `Utils.escapeHtml` (`static/js/utils.js:9`), `DisplayManager.escapeHtml`, `AnalyticsRenderer.escapeHtml`, or local `escapeHTML()` helpers in `stochasticModels.js` before being inserted with `innerHTML`.

**Memory & Performance:**
- `gc.collect()` called explicitly after heavy analytics in route handlers (e.g., `webapp.py:344`).
- Worker pool sizing: `max_ticker_workers = min(4, max(2, sqrt(n) * 1.5))` for parallel scraping.
- `socket.setdefaulttimeout(600)` for cloud cold-start tolerance.
- Sentiment analysis defaults OFF on Render (`webapp.py:82`, `render.yaml:17`) to stay within 512MB free tier.

---

*Architecture analysis: 2026-04-25*
