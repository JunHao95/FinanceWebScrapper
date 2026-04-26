# Phase 25: Codebase Health — Critical Bug Fixes, Security Patches, and Performance Quick Wins - Context

**Gathered:** 2026-04-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix all three known bugs, patch all four identified security issues, apply four performance quick wins, and close four tech debt items — no new features, no architectural refactors, no frontend framework migration. Every change is isolated, independently testable, and reversible.

**Explicitly out of scope:**
- Monolithic `webapp.py` refactor / route blueprints
- JS bundler / build step introduction
- Frontend framework migration (React, Vue, HTMX)
- Database layer changes
- New analytics capabilities

</domain>

<decisions>
## Implementation Decisions

### Bug fixes
- **Debug prints in production** — Find and remove all `print(f"DEBUG...")` and stray `print()` calls in `webapp.py` and `src/`. Replace with `logging.debug()` where the message is worth keeping; silent removal otherwise.
- **Broken `advanced-settings` element ref** — Fix the JS ID mismatch so `document.getElementById("advanced-settings")` resolves correctly. User checkbox selections must take effect.
- **Percentile rank stuck at 50** — Fix incorrect comparison logic so percentile rank returns the correct value across the full range.

### Security patches
- **Hardcoded secret key** — Remove the hardcoded fallback. If `SECRET_KEY` env var is unset, raise a `RuntimeError` on startup (fail loudly, not silently). Add to `.env.example` with a note.
- **Unvalidated email recipients** — Email report route must validate submitted recipient address against the `recipients` list in `config.json`. Reject any address not on the allowlist with a clear error response.
- **Rate limiting on expensive routes** — Add rate limiting to `/api/regime-detection` and `/api/sentiment` (and any other heavy analytics routes). Use Flask-Limiter or equivalent. Exact limits (e.g., 5 req/min per IP) are Claude's discretion.
- **API keys in request bodies** — Remove all client-side API key passing. Keys must come from env vars server-side only. Remove the corresponding fields from any request schemas and frontend forms.

### Performance
- **Double yfinance fetch** — Deduplicate: fetch OHLCV data once in the route handler, pass the DataFrame into the indicator functions. Do not re-fetch inside indicator logic.
- **HMM caching** — Cache fitted `RegimeDetector` model objects with a TTL cache keyed by `ticker + lookback`. Exact TTL value is Claude's discretion (suggest 10–30 minutes). Cache lives in memory; expires on server restart.
- **Unbounded cache eviction** — Cap all module-level cache dicts with max-size LRU eviction. Use `functools.lru_cache` where applicable or a simple `OrderedDict` with size cap. Exact max size per cache is Claude's discretion.
- **Gunicorn workers** — Update `Procfile` to `gunicorn webapp:app --workers 2 --timeout 600`. Two workers ensures one blocked analytics call doesn't freeze the entire app under Render's 512MB ceiling.

### Tech debt
- **Pin requirements.txt** — Replace all `>=` bounds with exact pinned versions from `pip freeze`. Prevents surprise breakage on fresh deploys.
- **Remove debug prints** — Covered under bug fixes above; treat as same task.
- **Add pre-commit linting** — Add `.flake8` config and a `pre-commit` hook running `flake8` + `black --check`. Enforces style automatically going forward.
- **Deduplicate JS helpers** — Consolidate `parseNumeric()` and `escapeHtml()` to `static/js/utils.js`. Remove reimplementations in other JS files (~4 files affected). No new behaviour — pure deduplication.

### Claude's Discretion
- Exact rate limit thresholds (requests/min per IP per route)
- TTL value for HMM cache (within 10–30 min range)
- Max cache size for LRU-capped dicts
- Whether to use `cachetools` or a stdlib `OrderedDict` wrapper for LRU
- Exact `logging` level for replaced debug prints (debug vs info)
- Order of fix delivery across plans

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `functools.lru_cache`: stdlib, already available — apply to pure functions with hashable args
- `src/utils/request_handler.py`: centralised HTTP client — useful reference pattern for caching wrapper
- `config.json` / `config.json.example`: already has `recipients` list — email allowlist validation reads from here
- `.env.example`: already documents `SECRET_KEY` — add startup guard note here

### Established Patterns
- Lazy-loaded module globals in `webapp.py` (e.g., `get_enhanced_sentiment_scraper()`) — same pattern applies for cached HMM model retrieval
- `convert_numpy_types` helper in `webapp.py` — example of a cross-cutting utility; LRU-capped dicts follow same module-level pattern
- `static/js/utils.js:79` already has `parseNumeric` and `escapeHtml` — the canonical location to keep

### Integration Points
- `webapp.py` route handlers: rate limiter attaches here (Flask-Limiter `@limiter.limit` decorator)
- `Procfile`: gunicorn worker count change here
- `requirements.txt`: pin versions here; add `Flask-Limiter` if chosen
- `.pre-commit-config.yaml` + `.flake8`: new files for linting enforcement
- `src/analytics/trading_indicators.py`: double yfinance fetch fix happens here (route passes DataFrame in)
- `src/analytics/regime_detection.py`: HMM cache wraps `RegimeDetector.fit()` call

</code_context>

<specifics>
## Specific Ideas

- Rate limiting should protect at minimum: `/api/regime-detection`, `/api/sentiment` — the two known 2–10s+ calls. Also apply to `/api/scrape` if not already limited.
- Gunicorn workers = 2, not CPU formula (3 would risk 512MB ceiling with lazy-loaded analytics modules).
- Secret key: fail loudly on startup (`RuntimeError`) rather than generate a random key — ensures deployed environments are always configured explicitly.
- Email allowlist: reject at the route level with HTTP 403 and a message like `"Recipient not in allowed list"` — don't silently drop the request.

</specifics>

<deferred>
## Deferred Ideas

- Monolithic `webapp.py` refactor into route blueprints — architectural work, its own phase
- JS bundler / Vite build step — frontend infrastructure, its own phase
- Frontend framework migration (React/Vue/HTMX) — large scope, its own phase
- Streaming for multi-ticker responses (SSE) — feature work, not a quick win
- FinBERT memory constraint (512MB RAM ceiling) — requires paid tier or architectural change
- Yahoo Finance HTML parser fragility — reactive fix only when it breaks; no proactive scope here
- JS unit tests (Vitest) — test infrastructure phase

</deferred>

---

*Phase: 25-codebase-health-critical-bug-fixes-security-patches-and-performance-quick-wins*
*Context gathered: 2026-04-26*
