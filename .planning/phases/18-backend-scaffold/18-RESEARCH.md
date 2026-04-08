# Phase 18: Backend Scaffold - Research

**Researched:** 2026-04-08
**Domain:** Flask route scaffolding, yfinance OHLCV fetch, vanilla JS session-cache module
**Confidence:** HIGH

---

## Summary

Phase 18 is a pure infrastructure phase. Its sole output is a tested integration seam — one canonical Python fetch function, one stub Flask route, and one stub JS module — that Phases 19–22 can build on without ever touching the integration layer again. There are no new external dependencies: yfinance is already in `requirements.txt`, Flask is already running, and Plotly is already loaded in the browser.

The codebase has established, repeated patterns for every deliverable in this phase. The Flask GET route follows the `/api/peers` pattern (query-param dispatch, `jsonify`, module-level cache variable). The JS module follows `peerComparison.js` exactly (IIFE, `_sessionCache` object, `clearSession()` public API, `window.TradingIndicators` export). The Python analytics module follows `regime_detection.py` for yfinance usage (`yf.Ticker(ticker).history(auto_adjust=True)` not `yf.download()`).

The critical correctness guard for the OHLCV fetch — using `yf.Ticker().history()` rather than `yf.download()` — is already documented as a project decision from Phase 09-01 ("yf.Ticker().history() replaces yf.download() to fix concurrent-download shape corruption") and must be replicated exactly here.

**Primary recommendation:** Mirror existing patterns exactly. Do not invent new patterns for anything in this phase.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yfinance | >=0.2.18 (requirements.txt) | OHLCV data fetch | Already in project; `yf.Ticker().history()` pattern established in Phase 09-01 |
| Flask | >=2.3.0 | Route registration, `jsonify` | Existing app; same pattern as `/api/peers` |
| pandas | >=1.5.0 | DataFrame return type from fetch function | Already used throughout analytics modules |
| numpy | >=1.23.0 | Downstream indicator math | Already imported by all analytics modules |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=7.0.0 | Route + function unit tests | Phase 18 writes one test file following `test_peer_comparison.py` pattern |
| unittest.mock | stdlib | Patch yfinance in tests | Prevents live network calls in CI |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `yf.Ticker().history()` | `yf.download()` | `yf.download()` causes 2D vs 1D shape corruption under concurrent calls — **do not use** (Phase 09-01 decision) |

**Installation:** No new packages needed. All dependencies already present.

---

## Architecture Patterns

### Files Created in This Phase

```
src/analytics/trading_indicators.py   # NEW — canonical fetch function + stub compute functions
static/js/tradingIndicators.js         # NEW — session cache, clearSession(), per-ticker fetch
tests/test_trading_indicators_route.py # NEW — route smoke test + fetch_ohlcv unit test
```

### Files Modified in This Phase

```
webapp.py                              # ADD ~20 lines: GET /api/trading_indicators route
templates/index.html                   # ADD: 4th tab button, tradingIndicatorsTabContent div, script tag
static/js/tabs.js                      # ADD: 'tradingindicators' to validTabs, switchTab case
static/js/stockScraper.js              # ADD: TradingIndicators.clearSession() in displayResults()
```

### Pattern 1: Flask GET Route (follow /api/peers exactly)

**What:** Query-param route returning hardcoded stub JSON with all four indicator placeholder keys.
**When to use:** Stub routes during scaffold phases; real compute slots into the same structure in Phases 19–22.

```python
# Source: webapp.py lines 2070-2151 (/api/peers pattern)
@app.route('/api/trading_indicators', methods=['GET'])
def get_trading_indicators():
    ticker  = request.args.get('ticker', '').strip().upper()
    lookback = int(request.args.get('lookback', 90))
    if not ticker:
        return jsonify({'error': 'ticker parameter required'})
    try:
        from src.analytics.trading_indicators import fetch_ohlcv
        df = fetch_ohlcv(ticker, lookback)
        # Stub: return placeholder payload — real compute added in Phases 19–22
        return jsonify({
            'ticker':   ticker,
            'lookback': lookback,
            'volume_profile': {'status': 'stub'},
            'anchored_vwap':  {'status': 'stub'},
            'order_flow':     {'status': 'stub'},
            'liquidity_sweep':{'status': 'stub'},
            'composite_bias': {'status': 'stub'},
        })
    except Exception as e:
        logger.error(f"Error in get_trading_indicators for {ticker}: {e}")
        return jsonify({'error': str(e)}), 500
```

### Pattern 2: Canonical OHLCV Fetch Function

**What:** Single function returning a clean OHLCV DataFrame with timezone-stripped DatetimeIndex.
**When to use:** Called by all four indicator functions in Phases 19–22. Never call `yf.download()`.

```python
# Source: webapp.py lines 1331–1334 and src/analytics/regime_detection.py lines 109–111
# (yf.Ticker().history() pattern — Phase 09-01 decision)
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_ohlcv(ticker: str, days: int, auto_adjust: bool = True) -> pd.DataFrame:
    """
    Canonical OHLCV fetch. Uses yf.Ticker().history() (not yf.download())
    to avoid concurrent-call shape corruption (Phase 09-01 decision).

    Returns a DataFrame with columns: Open, High, Low, Close, Volume
    Index: timezone-naive DatetimeIndex
    """
    end   = datetime.now()
    start = end - timedelta(days=int(days * 1.4))  # 40% buffer for non-trading days
    df = yf.Ticker(ticker).history(
        start=start.strftime('%Y-%m-%d'),
        end=end.strftime('%Y-%m-%d'),
        auto_adjust=auto_adjust
    )
    if df.empty:
        raise ValueError(f"No OHLCV data returned for {ticker}")
    df.index = df.index.tz_localize(None) if df.index.tz is not None else df.index
    return df[['Open', 'High', 'Low', 'Close', 'Volume']]
```

**Key correctness point:** `auto_adjust=True` ensures split- and dividend-adjusted prices, eliminating the adjusted/unadjusted mismatch documented in the roadmap.

### Pattern 3: JS Module (follow peerComparison.js exactly)

**What:** IIFE exposing `window.TradingIndicators = { fetchForTicker, clearSession }`.
**When to use:** The pattern for all v2.1/v2.2 lazy-loaded per-ticker modules.

```javascript
// Source: static/js/peerComparison.js — exact structural pattern
(function () {
    'use strict';

    // Per-ticker session cache keyed by ticker + '-' + lookback
    var _sessionCache = {};

    function clearSession() {
        Object.keys(_sessionCache).forEach(function (k) { delete _sessionCache[k]; });
    }

    function fetchForTicker(ticker, lookback) {
        var cacheKey = ticker + '-' + lookback;
        if (_sessionCache[cacheKey]) return;          // guard against double-render
        _sessionCache[cacheKey] = true;

        var container = document.getElementById('tradingIndicatorsTabContent');
        if (!container) return;

        fetch('/api/trading_indicators?ticker=' + encodeURIComponent(ticker) +
              '&lookback=' + encodeURIComponent(lookback))
            .then(function (r) { return r.json(); })
            .then(function (resp) {
                if (resp.error) {
                    console.warn('[TradingIndicators] API error:', resp.error);
                    return;
                }
                // Phase 19–22 will render Plotly charts here
                console.log('[TradingIndicators] stub OK for', cacheKey, resp);
            })
            .catch(function (err) {
                console.error('[TradingIndicators] fetch failed:', err);
            });
    }

    window.TradingIndicators = { fetchForTicker: fetchForTicker, clearSession: clearSession };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.TradingIndicators;
    }
}());
```

### Pattern 4: clearSession() wiring in stockScraper.js

**What:** Add one guard-wrapped line to `displayResults()` alongside the existing four clearSession calls.
**When to use:** Must be in `displayResults()` so that re-scraping a new ticker set clears stale indicator data.

```javascript
// Source: static/js/stockScraper.js lines 187–190 (existing pattern)
// ADD after PeerComparison.clearSession():
if (typeof TradingIndicators !== 'undefined') TradingIndicators.clearSession();
```

### Pattern 5: Tab Button + Content Div in index.html

**What:** Add a fourth `tab-button` and `tab-content` div following the existing three-tab structure.
**When to use:** Phase 22 will populate the content; Phase 18 only needs the div shell.

```html
<!-- Source: templates/index.html lines 140–151 (existing tab structure) -->
<button class="tab-button" onclick="switchTab('tradingindicators')" id="tradingIndicatorsTab">
    📊 Trading Indicators
</button>
<!-- ... inside tabContents: -->
<div class="tab-content" id="tradingIndicatorsTabContent">
    <!-- Phase 22 populates this with 2x2 Plotly grid per ticker -->
</div>
```

### Pattern 6: tabs.js validTabs update

**What:** Add `'tradingindicators'` to `validTabs` and add a corresponding `else if` branch in `switchTab()`.
**When to use:** Without this, `switchTab('tradingindicators')` logs a console error and does nothing.

```javascript
// Source: static/js/tabs.js lines 16–53 (existing switchTab pattern)
const validTabs = ['stocks', 'analytics', 'autoanalysis', 'tradingindicators'];
// ... add else if branch:
} else if (tabName === 'tradingindicators') {
    const tiTab = document.getElementById('tradingIndicatorsTab');
    const tiContent = document.getElementById('tradingIndicatorsTabContent');
    if (tiTab && tiContent) {
        tiTab.classList.add('active');
        tiContent.classList.add('active');
    }
}
```

### Anti-Patterns to Avoid

- **Using `yf.download()`:** Causes 2D vs 1D DataFrame shape corruption under concurrent calls (Phase 09-01 confirmed). Use `yf.Ticker(ticker).history()` exclusively.
- **Hardcoding indicator compute in the stub route:** The route body should call `fetch_ohlcv()` (proving the import chain works) and return hardcoded placeholder keys. Real compute goes into Phases 19–22.
- **Rendering into `deep-analysis-content-{TICKER}`:** Trading Indicators render into `tradingIndicatorsTabContent`, NOT into the v2.1 deep analysis divs (roadmap decision).
- **Omitting the `auto_adjust=True` parameter:** Without it yfinance may return unadjusted prices causing mismatch across indicators that all share the same OHLCV source.
- **Adding `tradingIndicators.js` without a script tag in index.html:** The module will silently never load; add the `<script src="/static/js/tradingIndicators.js"></script>` tag before `main.js`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Adjusted price fetch | Custom HTTP call to Yahoo Finance | `yf.Ticker().history(auto_adjust=True)` | Handles splits, dividends, timezone; already validated in project |
| Session deduplication | `Set` or `Map` in JS | `var _sessionCache = {}` object (peerComparison.js pattern) | Matches existing modules; consistent clearSession interface |
| Route response shape | Custom schema class | Plain `jsonify({...})` | Every other route uses this; no abstraction layer needed |

---

## Common Pitfalls

### Pitfall 1: Timezone-Aware DatetimeIndex from yfinance

**What goes wrong:** `yf.Ticker().history()` returns a timezone-aware DatetimeIndex (UTC). Downstream pandas operations that mix timezone-aware and timezone-naive indexes raise `TypeError: Cannot compare tz-naive and tz-aware`.
**Why it happens:** yfinance attaches UTC timezone to the index by default.
**How to avoid:** Strip timezone immediately in `fetch_ohlcv`: `df.index = df.index.tz_localize(None) if df.index.tz is not None else df.index`.
**Warning signs:** `TypeError: Cannot compare tz-naive and tz-aware DatetimeLikeArrayMixin` in test output.

### Pitfall 2: Double-Render on Tab Re-activation

**What goes wrong:** If `fetchForTicker()` is called every time the Trading Indicators tab is activated (not just the first time), the same ticker fires multiple API calls and DOM nodes accumulate.
**Why it happens:** Lazy-load handler calls fetch unconditionally.
**How to avoid:** Check `_sessionCache[cacheKey]` before firing the request, exactly as `peerComparison.js` checks `_sessionCache[ticker]`.

### Pitfall 3: Script Tag Ordering

**What goes wrong:** `stockScraper.js` calls `TradingIndicators.clearSession()`, but if `tradingIndicators.js` loads after `stockScraper.js`, the guard `if (typeof TradingIndicators !== 'undefined')` is always false.
**Why it happens:** Script tags execute in order; the guard is defensive but order still matters.
**How to avoid:** Add the `tradingIndicators.js` script tag before `stockScraper.js` in `index.html`, mirroring how `peerComparison.js` is listed before `stockScraper.js` at line 1337/1342.

### Pitfall 4: Missing ticker parameter returns 500 instead of 400

**What goes wrong:** If the ticker guard returns a plain dict without an HTTP status code, Flask defaults to 200 for error JSON — acceptable for this project's convention but should be consistent.
**Why it happens:** `return jsonify({'error': ...})` without a status code is 200.
**How to avoid:** Follow the `/api/peers` convention: missing ticker returns `jsonify({'error': ...})` with no status code (200) — this is deliberate and consistent with every other route in webapp.py.

---

## Code Examples

### Minimal Route Test (follows test_peer_comparison.py pattern)

```python
# tests/test_trading_indicators_route.py
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from webapp import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


def _stub_ohlcv():
    idx = pd.date_range('2024-01-01', periods=90, freq='B')
    return pd.DataFrame({
        'Open':   [150.0] * 90,
        'High':   [152.0] * 90,
        'Low':    [148.0] * 90,
        'Close':  [151.0] * 90,
        'Volume': [1_000_000] * 90,
    }, index=idx)


def test_trading_indicators_200_shape(client):
    with patch('src.analytics.trading_indicators.fetch_ohlcv', return_value=_stub_ohlcv()):
        resp = client.get('/api/trading_indicators?ticker=AAPL&lookback=90')
    assert resp.status_code == 200
    data = resp.get_json()
    for key in ('volume_profile', 'anchored_vwap', 'order_flow', 'liquidity_sweep', 'composite_bias'):
        assert key in data, f"Missing key: {key}"


def test_trading_indicators_missing_ticker(client):
    resp = client.get('/api/trading_indicators')
    assert resp.status_code == 200
    assert 'error' in resp.get_json()
```

### fetch_ohlcv Unit Test

```python
def test_fetch_ohlcv_returns_ohlcv_dataframe():
    """Verify return shape and column names without live network call."""
    import pandas as pd
    from unittest.mock import patch, MagicMock

    stub = pd.DataFrame({
        'Open':   [100.0],
        'High':   [101.0],
        'Low':    [99.0],
        'Close':  [100.5],
        'Volume': [500_000],
        'Dividends': [0.0],   # yfinance includes these; fetch_ohlcv should drop them
        'Stock Splits': [0.0],
    }, index=pd.DatetimeIndex(['2024-01-02']))

    mock_ticker = MagicMock()
    mock_ticker.history.return_value = stub

    with patch('yfinance.Ticker', return_value=mock_ticker):
        from src.analytics.trading_indicators import fetch_ohlcv
        df = fetch_ohlcv('AAPL', 90)

    assert list(df.columns) == ['Open', 'High', 'Low', 'Close', 'Volume']
    assert df.index.tz is None  # timezone stripped
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `yf.download()` for OHLCV | `yf.Ticker().history()` | Phase 09-01 | Eliminates 2D/1D shape corruption under concurrency |
| Inline yfinance calls inside routes | Dedicated analytics module function | Phases 13–16 | Keeps routes thin; allows unit-testing the fetch in isolation |

---

## Open Questions

1. **yfinance column naming after auto_adjust=True**
   - What we know: `auto_adjust=True` renames the adjusted Close to `Close` and drops `Adj Close` in recent yfinance versions.
   - What's unclear: Exact column set when `auto_adjust=True` — could include `Dividends` and `Stock Splits`. The fetch function should explicitly select `['Open', 'High', 'Low', 'Close', 'Volume']` to be safe.
   - Recommendation: Always slice to five columns in `fetch_ohlcv` return. Do not assume upstream columns.

2. **Lookback buffer multiplier**
   - What we know: `regime_detection.py` uses `days * 1.5` as the calendar-to-trading-day buffer. The roadmap states AVWAP fetch covers 365 days regardless of display lookback.
   - What's unclear: Whether `1.4` or `1.5` is the right buffer for the trading indicators use case.
   - Recommendation: Use `1.4` (gives ~126% coverage) — safe for 5-day trading weeks without over-fetching.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=7.0.0 |
| Config file | none — discovered via `tests/` directory |
| Quick run command | `pytest tests/test_trading_indicators_route.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements to Test Map

Phase 18 has no formal REQ-IDs. The four success criteria map to tests as follows:

| Success Criterion | Behavior | Test Type | Automated Command | File Exists? |
|-------------------|----------|-----------|-------------------|-------------|
| SC-1: Route returns 200 + 5 keys | `/api/trading_indicators?ticker=AAPL&lookback=90` returns status 200 with all four indicator keys | unit (Flask test client) | `pytest tests/test_trading_indicators_route.py::test_trading_indicators_200_shape -x` | Wave 0 |
| SC-2: fetch_ohlcv returns OHLCV DataFrame | Function returns 5-column DataFrame, tz-naive index | unit | `pytest tests/test_trading_indicators_route.py::test_fetch_ohlcv_returns_ohlcv_dataframe -x` | Wave 0 |
| SC-3: clearSession exists | JS module exports clearSession method | manual browser check | — | n/a (JS) |
| SC-4: Browser network trace | GET request succeeds, no console errors | manual browser DevTools | — | n/a |

### Sampling Rate

- **Per task commit:** `pytest tests/test_trading_indicators_route.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_trading_indicators_route.py` — covers SC-1 and SC-2 (route shape + fetch_ohlcv unit test)

---

## Sources

### Primary (HIGH confidence)

- Codebase: `webapp.py` lines 2070–2151 — `/api/peers` route pattern (GET, query params, jsonify, module-level cache)
- Codebase: `static/js/peerComparison.js` — IIFE + `_sessionCache` + `clearSession()` + `window.PeerComparison` export pattern
- Codebase: `src/analytics/regime_detection.py` lines 109–111 — `yf.Ticker().history(auto_adjust=True)` pattern
- Codebase: `static/js/stockScraper.js` lines 187–190 — `clearSession()` call pattern in `displayResults()`
- Codebase: `static/js/tabs.js` lines 16–53 — `validTabs` array and `switchTab()` pattern
- Codebase: `templates/index.html` lines 140–172 — tab button + tab content div structure
- Project decisions log (STATE.md): `yf.Ticker().history() replaces yf.download()` (Phase 09-01 decision)
- Project decisions log (STATE.md): `Trading Indicators tab renders into div#tradingIndicatorsTabContent` (v2.2 Roadmap decision)
- Project decisions log (STATE.md): `JS module follows peerComparison.js pattern` (v2.2 Roadmap decision)

### Secondary (MEDIUM confidence)

- `requirements.txt` — confirms yfinance >=0.2.18, Flask >=2.3.0, pandas >=1.5.0 all present; no new installs needed

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed and in use
- Architecture patterns: HIGH — directly mirrored from existing code in the same repo
- Pitfalls: HIGH — Phase 09-01 decision and existing codebase patterns verify all pitfalls
- Test patterns: HIGH — `test_peer_comparison.py` provides exact template

**Research date:** 2026-04-08
**Valid until:** 2026-05-08 (stable stack; no external API changes expected for yfinance on this timeline)
