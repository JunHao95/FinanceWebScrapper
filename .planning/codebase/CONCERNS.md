# Codebase Concerns

**Analysis Date:** 2026-04-26

## Tech Debt

### Monolithic `webapp.py`
- 2,250-line single file — all routes, middleware, startup, helper functions
- No route blueprints; adding features worsens the problem
- **Impact:** Hard to navigate; merge conflicts; slow to onboard

### No JavaScript Build Step
- 23 vanilla JS files loaded via `<script>` tags; no bundler (Vite, webpack, esbuild)
- No tree shaking, no minification, no TypeScript, no module bundling
- `static/js/` is ~8,500 lines with no compilation verification
- **Impact:** Browser loads 23+ network requests on first paint; no compile-time error checking; adding a framework requires retrofitting a build step

### Loose pip Constraints
- Several packages in `requirements.txt` unpinned or with `>=` bounds
- **Impact:** `pip install` on a fresh deploy may pull breaking versions

### Hardcoded Fallback Secret Key
- `app.secret_key` falls back to a hardcoded string if `SECRET_KEY` env var unset
- **Impact:** Sessions are predictable on misconfigured deploys

### Pervasive Inline Styles
- Significant inline `style=` usage throughout `templates/index.html`
- **Impact:** Hard to theme; no design system; style changes require HTML edits

### Duplicated JS Helpers
- `parseNumeric()` and `escapeHtml()` reimplemented in multiple JS files
- `utils.js` exists but not consistently imported
- **Impact:** Bug fixes must be applied in multiple places

### Unenforced Linting
- No `.flake8`, `pyproject.toml` linting config, or pre-commit hooks
- No ESLint/Prettier config for JS
- **Impact:** Inconsistent style; no automated quality gate

---

## Known Bugs

### `print(f"DEBUG...")` in Production
- Debug print statements present in `webapp.py` and `src/` modules
- **Impact:** Clutters gunicorn logs; may expose internal data in log aggregators

### Broken `advanced-settings` Element Reference
- JS code references `document.getElementById("advanced-settings")` but element ID doesn't match HTML
- User checkbox selections for advanced options silently ignored
- **Impact:** Feature appears to work but has no effect; data loss UX

### Floating-Point Percentile Rank Always Returns 50
- Percentile rank computation in analytics module returns 50.0 for all inputs due to incorrect comparison logic
- **Impact:** Percentile metrics are meaningless; displayed to users without warning

---

## Security

### No Authentication or Rate Limiting
- All `/api/*` endpoints publicly accessible — no login, no API key, no rate limit
- Any user can trigger expensive computations (HMM fitting, FinBERT, DCF) without restriction
- **Impact:** DoS via repeated `/api/regime-detection` or `/api/sentiment` calls

### API Keys Passed in Request Bodies
- Some routes accept API keys from the client request JSON
- **Impact:** Keys logged in access logs, visible in browser devtools Network tab

### Unvalidated Email Recipients
- Email report route accepts arbitrary recipient addresses from form input
- No allowlist check against `config.json` recipients
- **Impact:** Open relay risk; server can be used to send email to arbitrary addresses

---

## Performance

### Single Gunicorn Worker
- `Procfile`: `gunicorn webapp:app` — no `--workers` flag
- **Impact:** All requests serialized; one slow analytics call blocks all other users

### Double yfinance Fetch per Trading Indicator Request
- Trading indicator route fetches price data twice — once in the route handler and once in the indicator function
- **Impact:** 2× latency and API call count for every `/api/trading-indicators` request

### HMM Refitted on Every Request
- `RegimeDetector` fits a Hidden Markov Model from scratch on each `/api/regime-detection` call
- No caching; fitting takes 2–10 seconds depending on data length
- **Impact:** Extremely slow response; blocks the worker thread

### Unbounded In-Memory Caches
- Several module-level dicts used as caches with no eviction policy
- **Impact:** Memory grows unbounded under load; hits 512MB Render limit and crashes

---

## Fragile Areas

### Module Loading Order in `webapp.py`
- Heavy modules (`FinancialAnalytics`, `EnhancedSentimentScraper`) loaded lazily via globals set in route handlers
- Race condition possible if two concurrent requests both trigger initialization
- **Impact:** Rare `AttributeError` or double-initialization on cold start under load

### Global Mutable State
- Several module-level variables in `webapp.py` mutated by route handlers
- **Impact:** State bleeds between requests in same worker; hard to reproduce bugs

### Yahoo Finance HTML Parser Fragility
- `src/scrapers/yahoo_scraper.py` parses HTML in addition to using `yfinance`
- Yahoo has broken this scraper multiple times historically
- **Impact:** Silent data gaps when Yahoo changes page structure

### Unbounded Peer/Validation Caches
- Peer comparison and ticker validation caches grow without bound
- **Impact:** Memory pressure in long-running workers

---

## Scaling Limits

### 512MB RAM Ceiling (Render Free Tier)
- FinBERT alone is ~500MB — cannot run with any other analytics simultaneously
- **Impact:** Sentiment features disabled on cloud; upgrade required to enable

### No Streaming for Multi-Ticker Responses
- Bulk analysis requests block until all tickers complete before returning
- SSE stream (`/api/stream`) exists but not used for bulk routes
- **Impact:** Frontend shows spinner for 30–120 seconds on multi-ticker runs

---

## Dependencies at Risk

| Package | Risk |
|---|---|
| `yfinance` | Unpinned; Yahoo breaks it periodically; unofficial API |
| `newspaper3k` | Unmaintained; Python 3.13 compatibility uncertain |
| `pytrends` | Unofficial Google Trends API; frequently blocked by Google rate limiting |
| `openai` | Imported but unused — dead dependency, version drift risk |

---

## Test Coverage Gaps

- **No JavaScript tests** — 8,500 lines of JS with zero unit tests (see TESTING.md)
- **E2E never runs in CI** — Playwright tests are local-only
- **No live scraper tests** — scraper breakage only detected at runtime
- `src/utils/email_utils.py` (1281 lines) largely untested
- FinBERT/sentiment path untested (disabled on cloud)

---

## UI/UX Concerns (Frontend Framework Relevance)

### Current Limitations

| Problem | Detail |
|---|---|
| 1,370-line monolithic `index.html` | Single file with all tabs, forms, result containers inline; hard to maintain |
| No reactive state | Results displayed by direct DOM manipulation; stale data remains visible on re-run |
| URL never updates on tab switch | No routing; back button breaks; can't share deep links |
| Global spinner | Single loading indicator for all operations; no per-section feedback |
| No mobile layout | No responsive breakpoints; unusable on phones |
| Chatbot as raw `innerHTML` | `chatbot.js` sets `innerHTML` directly — XSS risk if any user input reflected |
| No form validation feedback | Invalid inputs silently fail or return generic errors |
| Tab state lost on refresh | Active tab not persisted; always resets to first tab |

### Where HTMX Would Help
- Progressive enhancement — minimal JS, server renders HTML fragments
- Replace `fetch + DOM manipulation` pattern with `hx-post` + server-rendered partials
- Best fit for: scrape results, email report form, chatbot
- Low migration cost — keep Flask/Jinja2, add `htmx.js` to CDN list

### Where React Would Help
- Component isolation — each analytics section becomes a self-contained component
- React Query / SWR for request deduplication and loading states
- React Router for tab routing with URL persistence
- Best fit for: complex forms (options pricing, DCF), charts (volatility surface), chatbot
- Higher migration cost — requires build step (Vite), rewrite of 22 JS modules as components

### Where Vue Would Help
- Similar to React; gentler migration path from vanilla JS
- Vue's Options API mirrors the current module-per-feature structure
- Pinia replaces `state.js` directly
- Best fit if team prefers gradual migration from existing JS

### Recommended Path for Frontend Enhancement
1. **Phase 1:** Add Vite build step — bundle existing JS, add TypeScript, fix `parseNumeric` duplication
2. **Phase 2 (HTMX):** Replace fetch/DOM manipulation for simple forms (email report, scrape trigger)
3. **Phase 3 (React/Vue):** Migrate complex interactive sections (options pricing, volatility surface, chatbot)
4. **Parallel:** Add Vitest for JS unit tests from day one of any framework adoption

---

*Concerns analysis: 2026-04-26*
