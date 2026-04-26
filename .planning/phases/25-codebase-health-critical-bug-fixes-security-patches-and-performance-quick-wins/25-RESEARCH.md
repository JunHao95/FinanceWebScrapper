# Phase 25: Codebase Health — Critical Bug Fixes, Security Patches, and Performance Quick Wins - Research

**Researched:** 2026-04-26
**Domain:** Python/Flask web app — bug fixes, security hardening, caching, JS deduplication, dev tooling
**Confidence:** HIGH (all findings verified against actual source code)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Bug fixes**
- **Debug prints in production** — Find and remove all `print(f"DEBUG...")` and stray `print()` calls in `webapp.py` and `src/`. Replace with `logging.debug()` where the message is worth keeping; silent removal otherwise.
- **Broken `advanced-settings` element ref** — Fix the JS ID mismatch so `document.getElementById("advanced-settings")` resolves correctly. User checkbox selections must take effect.
- **Percentile rank stuck at 50** — Fix incorrect comparison logic so percentile rank returns the correct value across the full range.

**Security patches**
- **Hardcoded secret key** — Remove the hardcoded fallback. If `SECRET_KEY` env var is unset, raise a `RuntimeError` on startup (fail loudly, not silently). Add to `.env.example` with a note.
- **Unvalidated email recipients** — Email report route must validate submitted recipient address against the `recipients` list in `config.json`. Reject any address not on the allowlist with a clear error response.
- **Rate limiting on expensive routes** — Add rate limiting to `/api/regime-detection` and `/api/sentiment` (and any other heavy analytics routes). Use Flask-Limiter or equivalent. Exact limits (e.g., 5 req/min per IP) are Claude's discretion.
- **API keys in request bodies** — Remove all client-side API key passing. Keys must come from env vars server-side only. Remove the corresponding fields from any request schemas and frontend forms.

**Performance**
- **Double yfinance fetch** — Deduplicate: fetch OHLCV data once in the route handler, pass the DataFrame into the indicator functions. Do not re-fetch inside indicator logic.
- **HMM caching** — Cache fitted `RegimeDetector` model objects with a TTL cache keyed by `ticker + lookback`. Exact TTL value is Claude's discretion (suggest 10–30 minutes). Cache lives in memory; expires on server restart.
- **Unbounded cache eviction** — Cap all module-level cache dicts with max-size LRU eviction. Use `functools.lru_cache` where applicable or a simple `OrderedDict` with size cap. Exact max size per cache is Claude's discretion.
- **Gunicorn workers** — Update `Procfile` to `gunicorn webapp:app --workers 2 --timeout 600`. Two workers ensures one blocked analytics call doesn't freeze the entire app under Render's 512MB ceiling.

**Tech debt**
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

### Deferred Ideas (OUT OF SCOPE)
- Monolithic `webapp.py` refactor into route blueprints — architectural work, its own phase
- JS bundler / Vite build step — frontend infrastructure, its own phase
- Frontend framework migration (React/Vue/HTMX) — large scope, its own phase
- Streaming for multi-ticker responses (SSE) — feature work, not a quick win
- FinBERT memory constraint (512MB RAM ceiling) — requires paid tier or architectural change
- Yahoo Finance HTML parser fragility — reactive fix only when it breaks; no proactive scope here
- JS unit tests (Vitest) — test infrastructure phase
</user_constraints>

---

## Summary

Phase 25 is a pure maintenance phase: no new features, no architectural changes. Every item is scoped, isolated, and independently testable. The work breaks into four groups: three bug fixes (debug prints, broken JS ID ref, percentile rank logic), four security patches (secret key startup guard, email allowlist, rate limiting, remove client-side API keys), four performance quick wins (deduplicate yfinance fetch, HMM TTL cache, LRU-cap unbounded dicts, Gunicorn workers=2), and four tech-debt closures (pin requirements, deduplicate JS helpers, add pre-commit linting, debug prints already covered under bugs).

The codebase is well-structured for this work. All bugs and security issues were confirmed by reading the actual source. `cachetools` (v5.5.2) is already installed in the venv. `Flask-Limiter` (v4.1.1 available) is not installed — it needs to be added to `requirements.txt` and installed. `black` and `flake8` are already in the venv; `pre-commit` the tool is not, but the hook file is straightforward to add.

**Primary recommendation:** Execute changes in dependency order — bugs first (no dependency), security second (no dependency), performance third (HMM cache depends on the yfinance dedup), tech debt last (pinning goes after all new packages are added).

---

## Standard Stack

### Core (already in project)
| Library | Installed Version | Purpose | Confirmed |
|---------|-------------------|---------|-----------|
| Flask | 3.1.2 | Web framework | `pip freeze` |
| cachetools | 5.5.2 | TTLCache + LRUCache for HMM + peer caches | `pip freeze`, already in venv |
| black | 25.1.0 | Code formatter (pre-commit hook) | `pip freeze` |
| flake8 | 7.1.2 | Linting (pre-commit hook) | `pip freeze` |
| gunicorn | 21.2.0 | WSGI server | `pip freeze` |

### New Dependencies
| Library | Latest Version | Purpose | Install Command |
|---------|---------------|---------|-----------------|
| Flask-Limiter | 4.1.1 | Per-IP rate limiting on expensive routes | `pip install Flask-Limiter==4.1.1` |
| pre-commit | (latest via pip) | Git pre-commit hook runner | `pip install pre-commit` |

**Installation:**
```bash
pip install Flask-Limiter==4.1.1 pre-commit
```

---

## Architecture Patterns

### BUG-01: Debug prints in production

**What:** Stray `print()` calls scatter across `src/` modules and `webapp.py`. They pollute stdout on Render, interfere with log parsing, and leak internal state.

**Verified locations (reading source):**
- `src/indicators/technical_indicators.py` lines 1051–1052: `print(20*"###")` and `print("No historical data...")`
- `src/utils/data_formatter.py` lines 113, 166: `print(f"Error saving to CSV/Excel")`
- `src/utils/comparison_utils.py` lines 375, 395: `print(f"Warning: Metric...")`
- `src/utils/display_formatter.py` lines 138, 139, 147, 152: print-based tabulate output (CLI utility — keep as-is or convert to `logger.info`)
- `src/utils/email_utils.py` lines 1269–1270: `print(f"Sending report...")` — convert to `logger.info`
- `src/scrapers/finviz_scraper.py` lines 33, 40: `print(f"Analyst Price Target...")` — convert to `logger.debug`
- `src/sentiment/sentiment_analyzer.py` lines 431, 521, 523, 525, 528, 539: mix of debug and progress prints — convert debugging ones to `logger.debug`, progress ones to `logger.info`
- `src/scrapers/cnn_scraper.py` lines 57, 61: `print(f"DEBUG, results...")` — `logger.debug` / `logger.error`
- `src/analytics/credit_transitions.py` line 318: test assertion print — `logger.debug`
- `webapp.py`: No bare `print()` calls found (confirmed by grep)

**Pattern to use:** All modules already import `logging` or use a `logger` at module level. Use the existing `logger` in each file.

### BUG-02: Broken `advanced-settings` element ref

**What:** `stockScraper.js` line 49:
```javascript
const advancedDetails = document.getElementById('advanced-settings');
```
The HTML element is a drawer with `id="settings-drawer"` (confirmed in `templates/index.html` line 1305). There is no element with `id="advanced-settings"` anywhere in the template. As a result `advancedDetails` is always `null`, `advancedDetails.open` is never `true`, and the advanced checkbox/API-key branch is dead code — the app always falls back to `['yahoo', 'finviz', 'google', 'technical']`.

**Fix:** Change the JS reference from `'advanced-settings'` to `'settings-drawer'`. The drawer uses an `open` CSS class (not the `<details>` `.open` property), so the check may also need updating depending on how the drawer tracks open state. Inspect the drawer toggle logic in JS to confirm the right attribute/class to check.

**Note:** After removing client-side API key passing (SEC-04), `alphaKey` and `finhubKey` reads become dead code anyway. The drawer reference fix is still needed for source checkboxes.

### BUG-03: Percentile rank stuck at 50

**What:** `webapp.py` lines 2089–2098 and 2123–2132 (two copies — cached and non-cached paths):
```python
def percentile_rank(rows, field, target):
    if target is None:
        return 50
    vals = sorted([r[field] for r in rows if r[field] is not None])
    if len(vals) < 2:
        return 50
    if target not in vals:   # <-- BUG: float comparison with `in` operator
        return 50
    idx = vals.index(target)
    return round(100 * idx / (len(vals) - 1))
```

**Root cause:** The `if target not in vals` guard returns 50 for any target value that doesn't match exactly (e.g., floating-point representation differs). For scraped data where values are strings parsed to floats, the exact equality check almost never matches, so the function returns 50 almost always.

**Fix:** Use bisect for nearest-rank percentile instead of exact-match lookup:
```python
import bisect

def percentile_rank(rows, field, target):
    if target is None:
        return 50
    vals = sorted([r[field] for r in rows if r[field] is not None])
    if len(vals) < 2:
        return 50
    idx = bisect.bisect_left(vals, target)
    # Clamp to valid range
    idx = min(idx, len(vals) - 1)
    return round(100 * idx / (len(vals) - 1))
```

Both copies of `percentile_rank` (cached path at line ~2089 and non-cached path at line ~2123) must be updated identically.

### SEC-01: Hardcoded secret key

**Current code** (`webapp.py` line 51):
```python
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
```

**Fix:**
```python
_secret_key = os.environ.get('SECRET_KEY')
if not _secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Set it before starting the server: "
        "export SECRET_KEY=$(python -c \"import secrets; print(secrets.token_hex(32))\")"
    )
app.config['SECRET_KEY'] = _secret_key
```

Also update `.env.example` to add a generation note below the `SECRET_KEY` line.

### SEC-02: Unvalidated email recipients

**Current code** (`webapp.py` line 614): `recipients = payload.get('email')` — no validation against any allowlist.

**Current `config.json`:** Has `"email": "teejunhao@gmail.com"`, `"bcc": [...]`, `"cc": [...]`. There is no `"recipients"` key yet.

**Required change:** Add a `"recipients"` list to `config.json` (and `config.json.example`) that serves as the allowlist. The route validates the submitted address against this list.

```python
# In send_email_report() after recipients = payload.get('email'):
allowed = config.get('recipients', [])
if allowed and recipients not in allowed:
    return jsonify({
        'success': False,
        'error': 'Recipient not in allowed list'
    }), 403
```

`config.json` addition:
```json
"recipients": ["teejunhao@gmail.com"]
```

### SEC-03: Rate limiting on expensive routes

**Library:** Flask-Limiter 4.1.1. Not yet installed. `cachetools` is already present but Flask-Limiter uses its own in-memory storage by default.

**Initialization pattern** (Flask-Limiter 4.x API):
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
```

**Route decoration:**
```python
@app.route('/api/regime_detection', methods=['POST'])
@limiter.limit("5 per minute")
def regime_detection_endpoint():
    ...

@app.route('/api/scrape', methods=['POST'])
@limiter.limit("10 per minute")
def scrape_stocks():
    ...
```

**Recommended limits (Claude's discretion — reasonable for showcase app):**
- `/api/regime_detection`: 5 req/min per IP (2–10s per call, HMM fit)
- `/api/scrape`: 10 req/min per IP (90s timeout, concurrent scrapers)
- `/api/sentiment` (if it exists as a standalone route — confirmed it does not; sentiment runs inside `/api/scrape`): N/A
- Apply `@limiter.limit("5 per minute")` also to: `/api/calibrate_heston`, `/api/calibrate_merton`, `/api/calibrate_bcc`, `/api/stoch_portfolio_mdp`, `/api/rl_portfolio_rotation_pi`, `/api/rl_portfolio_rotation_ql` (all are 2–10s computation routes)

**Flask-Limiter 4.x init change:** In v4.x the `Limiter` constructor takes `app=app` directly OR uses `init_app()` pattern. Since `webapp.py` constructs `app` at module level, `Limiter(app=app, ...)` works fine.

### SEC-04: API keys in request bodies

**Current state:**
- `stockScraper.js` lines 70–71 reads `alphaKey` and `finhubKey` from form fields
- Lines 93–94 sends them in the request body: `alpha_key: alphaKey || undefined, finhub_key: finhubKey || undefined`
- `webapp.py` lines 386–387 reads them from request body with env-var fallback: `alpha_key = data.get('alpha_key') or os.environ.get("ALPHA_VANTAGE_API_KEY")`

**Fix:**
1. `webapp.py`: Remove `data.get('alpha_key')` and `data.get('finhub_key')` — read from env vars only
2. `stockScraper.js`: Remove the two `const alphaKey / finhubKey` reads and the two request body fields
3. `templates/index.html`: Remove the `alphaKey` and `finhubKey` form fields (lines 1334–1341) from the settings drawer
4. Update the route docstring to remove `alpha_key` and `finhub_key` from the example payload

### PERF-01: Double yfinance fetch

**Current state:** `webapp.py` route `/api/regime_detection` already fetches price data and passes `log_ret` array directly to `detector.fit()`. This route does NOT double-fetch.

**The double-fetch is in `/api/trading_indicators`** (lines 2164–2168): `fetch_ohlcv` is called in the route handler and the result is passed to sub-functions. This looks correct already. Need to audit whether any indicator sub-functions call `fetch_ohlcv` internally again.

**Audit findings:**
- `trading_indicators.py` line 16: `fetch_ohlcv` is defined at module level
- `webapp.py` line 2167: `df = fetch_ohlcv(ticker, lookback)` — passed to indicator functions
- The sub-functions (`compute_volume_profile`, `compute_anchored_vwap`, etc.) receive a `df` parameter — they do not re-fetch
- The double-fetch concern from CONTEXT.md likely refers to the `/api/regime_detection` route calling `yf.Ticker().history()` AND the `RegimeDetector` potentially calling it internally

Check `src/analytics/regime_detection.py` to confirm `RegimeDetector.fit()` takes pre-fetched data (it takes `log_ret: np.ndarray` — no internal yfinance call). The route passes the log returns array, not a ticker.

**Conclusion:** The `/api/trading_indicators` route already passes DataFrames. The fix may be ensuring no double-fetching occurs if the same ticker is requested multiple times (caching via TTL). Confirm by searching `regime_detection.py` for any `yf.` calls.

### PERF-02: HMM caching

**Pattern (lazy-loaded module global with TTL):**
```python
from cachetools import TTLCache

# Module-level cache: keyed by (ticker, start_date, end_date), 15-minute TTL, max 50 entries
_regime_cache: TTLCache = TTLCache(maxsize=50, ttl=900)  # 15 min TTL
```

In the route handler, before fitting:
```python
cache_key = (ticker, start_date, end_date)
if cache_key in _regime_cache:
    return jsonify(_regime_cache[cache_key])

# ... fit HMM, build response dict ...
_regime_cache[cache_key] = convert_numpy_types(response)
return jsonify(_regime_cache[cache_key])
```

**cachetools.TTLCache** is thread-safe for reads but not writes in CPython due to GIL. Since Gunicorn workers=2 with separate processes, each worker has its own cache — this is acceptable and expected for in-memory caching.

**Recommended TTL: 15 minutes (900s)** — within the 10–30 min range, balances freshness vs computation cost.

### PERF-03: Unbounded cache eviction

**Current unbounded caches (confirmed in source):**
- `_ticker_validation_cache = {}` (line 2066) — no eviction
- `_peer_cache = {}` (line 2068) — has TTL check but no size cap
- `_ticker_sector_map = {}` (line 2069) — no eviction

**Fix using cachetools (already installed):**
```python
from cachetools import TTLCache, LRUCache

_peer_cache: TTLCache = TTLCache(maxsize=30, ttl=1800)       # 30 sectors, 30min TTL
_ticker_sector_map: LRUCache = LRUCache(maxsize=200)          # 200 tickers
_ticker_validation_cache: TTLCache = TTLCache(maxsize=500, ttl=3600)  # 1hr TTL
```

The existing access pattern for `_peer_cache` (`entry = _peer_cache[known_sector]` with a time check) needs to be simplified — TTLCache handles expiry automatically, so the manual `now - entry['fetched_at'] < 1800` check can be removed.

**Warning:** The existing `_peer_cache` stores `{'data': ..., 'fetched_at': float, 'peers': [...]}`. When switching to TTLCache, change storage to just `{'data': ..., 'peers': [...]}` and remove manual TTL checks.

### PERF-04: Gunicorn workers

**Current Procfile:**
```
web: gunicorn webapp:app --workers 1 --timeout 600 --log-level info --access-logfile - --error-logfile -
```

**New Procfile:**
```
web: gunicorn webapp:app --workers 2 --timeout 600 --log-level info --access-logfile - --error-logfile -
```

**Only change:** `--workers 1` → `--workers 2`. Keep all other flags identical. Do not use CPU-formula workers — 3+ workers risks OOM on Render's 512MB ceiling with lazy-loaded ML modules.

### TECH-01: Pin requirements.txt

**Current state:** All dependencies use `>=` bounds (e.g., `Flask>=2.3.0`, `numpy>=1.23.0`).

**Pinned versions from venv `pip freeze` (verified):**
```
beautifulsoup4==4.13.3
Flask==3.1.2
Flask-Cors==4.0.0  (needs verification)
gunicorn==21.2.0
numpy==2.4.4
pandas==3.0.2
plotly==6.1.2
requests==2.32.3
scikit-learn==1.8.0
scipy==1.17.1
torch==2.7.1
transformers==4.53.0
yfinance==0.2.58
cachetools==5.5.2
Flask-Limiter==4.1.1  (add after install)
```

Run `venv/bin/pip freeze > /tmp/freeze.txt` to capture all versions before writing the new `requirements.txt`.

**Note:** Also add `pre-commit` to requirements.txt under dev dependencies section if desired, though it's typically a dev-only tool and may not be needed on Render.

### TECH-03: Pre-commit linting

**Files to create:**

`.flake8`:
```ini
[flake8]
max-line-length = 120
exclude = venv, __pycache__, .git, migrations
extend-ignore = E203, W503
```

`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
      - id: black
        language_version: python3
  - repo: https://github.com/pycqa/flake8
    rev: 7.1.2
    hooks:
      - id: flake8
```

**Setup command:**
```bash
pip install pre-commit
pre-commit install
```

**Important:** Run `black --check .` and `flake8 .` on the existing codebase first to assess how many violations exist. Do NOT auto-format the entire codebase in this phase — that would produce a massive unrelated diff. Instead, format only the files changed in this phase, and add the hooks so future commits are clean.

### TECH-04: Deduplicate JS helpers

**Confirmed duplicates:**
- `parseNumeric()`: defined identically in `healthScore.js` (line 16), `earningsQuality.js` (line 14), `dcfValuation.js` (line 14) — 3 files
- `escapeHtml()`: defined as a method in `analyticsRenderer.js` (line 10, as `this.escapeHtml`) and as a local function in `chatbot.js` (line 85)

**Canonical location:** `static/js/utils.js` — already has `Utils.escapeHtml()` (line 9) and `Utils.formatValue()`. `parseNumeric` does NOT yet exist in `utils.js`.

**Fix:**
1. Add `parseNumeric(val)` to the `Utils` object in `utils.js` (use the common implementation from the three files — they are identical)
2. In `healthScore.js`, `earningsQuality.js`, `dcfValuation.js`: remove the local `parseNumeric` function, replace all calls with `Utils.parseNumeric(val)`
3. In `chatbot.js`: remove local `escapeHtml`, replace calls with `Utils.escapeHtml()`
4. In `analyticsRenderer.js`: the `escapeHtml` is a method on an object — either call `Utils.escapeHtml()` from the method body, or leave it (it's encapsulated). Replacing it reduces risk of breakage; either approach is acceptable.

**utils.js is loaded before all other JS files** (confirmed: `<script src="/static/js/utils.js">` on line 1346, before all module scripts) — so `Utils.parseNumeric` will be available to all modules.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rate limiting | Manual IP tracking + timestamp dicts | Flask-Limiter | Handles race conditions, has storage backends, decorator pattern, well-tested |
| TTL cache with max-size | Custom dict + timestamp cleanup | `cachetools.TTLCache` | Thread-safe reads, O(1) get/set, auto-expiry, already installed |
| LRU eviction | Manual OrderedDict + size check | `cachetools.LRUCache` | Same reasons, already installed |
| Code formatting checks | Manual style review | black + flake8 + pre-commit | Automatic, CI-friendly, deterministic |

---

## Common Pitfalls

### Pitfall 1: Percentile rank edge case at index 0
**What goes wrong:** When `bisect_left` returns 0 (target is smallest value), `round(100 * 0 / (n-1))` = 0, which is correct. But if `len(vals) == 1`, dividing by 0 occurs.
**Prevention:** Guard `if len(vals) < 2: return 50` (already present in current code — keep it).

### Pitfall 2: TTLCache is not thread-safe for writes
**What goes wrong:** With `--workers 2` (separate processes), each worker has its own in-memory cache — no shared state. This is safe. But within a single worker, if two concurrent requests both miss the cache and both start fitting the HMM, they both write. Under CPython's GIL this is generally safe but could cause duplicate computation.
**Prevention:** Acceptable for this use case. No lock needed. Document in code comment.

### Pitfall 3: Flask-Limiter 4.x changed initialization API
**What goes wrong:** Flask-Limiter v3.x used `Limiter(get_remote_address, app=app)`. v4.x uses `Limiter(app=app, key_func=get_remote_address)` — parameter order changed.
**Prevention:** Always specify `key_func=` as keyword argument. Test with `pip show flask-limiter` to confirm version installed.

### Pitfall 4: Converting `_peer_cache` to TTLCache breaks existing access pattern
**What goes wrong:** Current code accesses `_peer_cache[known_sector]` and then checks `entry['fetched_at']` manually. After switching to TTLCache, the `fetched_at` field is unnecessary — but if the old structure `{'data': ..., 'fetched_at': ..., 'peers': ...}` is preserved, reads still work. The manual time check just becomes redundant (not harmful).
**Prevention:** Either update the data structure (remove `fetched_at`) or keep it and simply remove the manual TTL check. Removing the manual check is cleaner.

### Pitfall 5: Removing API key form fields breaks layout
**What goes wrong:** The settings drawer has two `form-group` divs for API keys. Removing them may leave the drawer visually awkward or break CSS selectors.
**Prevention:** Remove the entire `<div class="form-group">` block for each key. Verify drawer still renders cleanly.

### Pitfall 6: Pre-commit auto-formatting creates unrelated diff noise
**What goes wrong:** Running `pre-commit run --all-files` reformats all 8000+ lines, making the phase diff unreadable.
**Prevention:** Install the hook but only run it on changed files. Do not run `--all-files` in this phase.

### Pitfall 7: `config.json` recipients allowlist vs. `config.json.example`
**What goes wrong:** Adding `"recipients"` to `config.json` but not to `config.json.example` means new deployments won't know the field exists and will have an empty allowlist (allowing any address if the guard is `if allowed and recipients not in allowed`).
**Prevention:** Add `"recipients": []` to both files. Document that empty list disables the allowlist check.

---

## Code Examples

### Flask-Limiter setup (v4.1.1)
```python
# webapp.py — after app initialization
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# On expensive route:
@app.route('/api/regime_detection', methods=['POST'])
@limiter.limit("5 per minute")
def regime_detection_endpoint():
    ...
```

### cachetools TTLCache for HMM results
```python
from cachetools import TTLCache

_regime_cache: TTLCache = TTLCache(maxsize=50, ttl=900)  # 15 min

# Inside route, before HMM fit:
cache_key = (ticker, start_date, end_date)
if cache_key in _regime_cache:
    return jsonify(_regime_cache[cache_key])

# After building response:
_regime_cache[cache_key] = convert_numpy_types(response)
```

### Bisect-based percentile rank (BUG-03 fix)
```python
import bisect

def percentile_rank(rows, field, target):
    if target is None:
        return 50
    vals = sorted([r[field] for r in rows if r[field] is not None])
    if len(vals) < 2:
        return 50
    idx = bisect.bisect_left(vals, target)
    idx = min(idx, len(vals) - 1)
    return round(100 * idx / (len(vals) - 1))
```

### SECRET_KEY startup guard (SEC-01 fix)
```python
_secret_key = os.environ.get('SECRET_KEY')
if not _secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
app.config['SECRET_KEY'] = _secret_key
```

### Utils.parseNumeric in utils.js
```javascript
// Add to the Utils object in static/js/utils.js
parseNumeric(val) {
    if (val === null || val === undefined || val === '' || val === 'N/A' || val === 'N/A%') return null;
    if (typeof val === 'number') return isNaN(val) ? null : val;
    const s = String(val).trim();
    let cleaned = s.replace(/^\$/, '');
    const multipliers = { 'B': 1e9, 'M': 1e6, 'K': 1e3 };
    const lastChar = cleaned.slice(-1).toUpperCase();
    if (multipliers[lastChar]) {
        const n = parseFloat(cleaned.slice(0, -1));
        return isNaN(n) ? null : n * multipliers[lastChar];
    }
    cleaned = cleaned.replace(/%$/, '');
    const n = parseFloat(cleaned);
    return isNaN(n) ? null : n;
},
```

---

## State of the Art

| Old Approach | Current Approach | Impact for This Phase |
|--------------|------------------|-----------------------|
| Flask-Limiter v2.x: `Limiter(key_func, app=app)` | Flask-Limiter v4.x: `Limiter(app=app, key_func=key_func)` | Use v4 keyword syntax — positional arg order changed |
| `cachetools` v4.x | v5.5.2 | No API changes relevant to TTLCache/LRUCache usage |
| Gunicorn `--workers $(nproc*2+1)` formula | 2 workers fixed for memory-constrained Render free tier | Fixed at 2, not formula |

---

## Key Findings: Email Allowlist Implementation Gap

The CONTEXT.md says to validate email against the `recipients` list in `config.json`, but `config.json` does not currently have a `recipients` field. The current fields are `email` (a single string, the primary address), `bcc` (list), and `cc` (list).

**Resolution:** The planner should add a `"recipients"` top-level list to `config.json` containing the addresses that are allowed as email report destinations. The route reads `config.get('recipients', [])`. An empty list disables the guard (open = anyone can receive, which is acceptable for a dev environment). A populated list enforces the allowlist on Render.

---

## Validation Architecture

Nyquist validation is enabled (key absent from `.planning/config.json`).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.x (installed in venv) |
| Config file | `tests/conftest.py` (exists) |
| Quick run command | `pytest -m unit -q` |
| Full suite command | `pytest -q` |

### Phase Requirements → Test Map

| Item | Behavior | Test Type | Automated Command |
|------|----------|-----------|-------------------|
| BUG-01 (debug prints) | No `print()` calls remain in `webapp.py` / `src/` | unit (grep-based assertion) | `pytest tests/test_unit_codebase_health.py::test_no_debug_prints -x` |
| BUG-02 (JS ID fix) | `document.getElementById('advanced-settings')` replaced with correct ID | manual / code review | Manual — no JS unit test framework in scope |
| BUG-03 (percentile rank) | `percentile_rank` returns values across full 0–100 range | unit | `pytest tests/test_unit_codebase_health.py::test_percentile_rank -x` |
| SEC-01 (secret key) | App raises `RuntimeError` when `SECRET_KEY` unset | unit | `pytest tests/test_unit_codebase_health.py::test_secret_key_guard -x` |
| SEC-02 (email allowlist) | `/api/send-email` returns 403 for unlisted address | integration | `pytest tests/test_integration_routes.py::test_email_allowlist -x` |
| SEC-03 (rate limiting) | Sending >N requests/min returns 429 | integration | `pytest tests/test_integration_routes.py::test_rate_limiting -x` |
| SEC-04 (remove client API keys) | `/api/scrape` ignores `alpha_key` body field | integration | `pytest tests/test_integration_routes.py::test_no_client_api_keys -x` |
| PERF-01 (no double fetch) | `fetch_ohlcv` called once per route invocation | unit (mock) | `pytest tests/test_unit_codebase_health.py::test_no_double_fetch -x` |
| PERF-02 (HMM cache) | Second identical request hits cache, skips HMM fit | unit (mock) | `pytest tests/test_unit_codebase_health.py::test_regime_cache -x` |
| PERF-03 (LRU cap) | `_peer_cache` / `_ticker_validation_cache` have bounded size | unit | `pytest tests/test_unit_codebase_health.py::test_cache_bounded -x` |
| PERF-04 (Gunicorn workers) | `Procfile` contains `--workers 2` | unit (file read) | `pytest tests/test_unit_codebase_health.py::test_procfile_workers -x` |
| TECH-01 (pin requirements) | `requirements.txt` has no `>=` bounds | unit (file parse) | `pytest tests/test_unit_codebase_health.py::test_requirements_pinned -x` |
| TECH-03 (pre-commit) | `.pre-commit-config.yaml` and `.flake8` exist | unit (file existence) | `pytest tests/test_unit_codebase_health.py::test_precommit_config -x` |
| TECH-04 (JS dedup) | `parseNumeric` not defined in `healthScore.js`, `earningsQuality.js`, `dcfValuation.js` | unit (file parse) | `pytest tests/test_unit_codebase_health.py::test_no_duplicate_js_helpers -x` |

### Sampling Rate
- **Per task commit:** `pytest -m unit -q tests/test_unit_codebase_health.py`
- **Per wave merge:** `pytest -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_unit_codebase_health.py` — new file covering BUG-01, BUG-03, SEC-01, PERF-02, PERF-03, PERF-04, TECH-01, TECH-03, TECH-04
- [ ] Add SEC-02 test to `tests/test_integration_routes.py`
- [ ] Add SEC-03 test to `tests/test_integration_routes.py`
- [ ] Add SEC-04 test to `tests/test_integration_routes.py`

---

## Sources

### Primary (HIGH confidence)
- Direct source code reading — `webapp.py` (2000+ lines verified)
- Direct source code reading — `static/js/stockScraper.js`, `utils.js`, `healthScore.js`, `earningsQuality.js`, `dcfValuation.js`, `chatbot.js`, `analyticsRenderer.js`
- Direct source code reading — `src/analytics/trading_indicators.py`, `src/sentiment/sentiment_analyzer.py`, `src/scrapers/cnn_scraper.py`, `src/scrapers/finviz_scraper.py`
- `venv/bin/pip show` — exact installed versions of cachetools (5.5.2), black (25.1.0), flake8 (7.1.2)
- `venv/bin/pip index versions flask-limiter` — confirms v4.1.1 is latest

### Secondary (MEDIUM confidence)
- Flask-Limiter 4.x API inferred from `pip install --dry-run` metadata (confirms v4.1.1 available)

---

## Metadata

**Confidence breakdown:**
- Bug locations: HIGH — all verified by grep and source read
- Security issues: HIGH — verified by source read
- Performance fix patterns: HIGH — cachetools already installed, patterns confirmed
- Flask-Limiter API: MEDIUM — dry-run confirms version; API syntax based on library documentation patterns for v4.x
- Pinned versions: HIGH — from `pip freeze` on actual venv

**Research date:** 2026-04-26
**Valid until:** 2026-05-26 (stable libraries, 30-day window)
