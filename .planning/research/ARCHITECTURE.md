# Architecture Patterns

**Domain:** MFE Showcase Web App — Flask + Vanilla JS Quant Finance
**Researched:** 2026-04-07 (updated for v2.2 Trading Indicators milestone)
**Confidence:** HIGH (based on direct codebase inspection, no speculation)

---

## Existing Architecture (As-Built)

```
Browser (Vanilla JS)
        |
        |  fetch() — JSON body
        v
Flask Routes (webapp.py)
        |
        |  Python function call
        v
Model Layer (src/analytics/, src/derivatives/)
        |
        |  returns plain Python dict
        v
convert_numpy_types() → jsonify() → HTTP 200 JSON
```

### Layer Responsibilities

| Layer | Files | Responsibility | Must NOT Do |
|-------|-------|----------------|-------------|
| Model Layer | `src/analytics/*.py` | Pure computation, no Flask imports | Import Flask, reference HTTP objects |
| API Layer | `webapp.py` routes | Parse JSON, call model, serialize | Contain math logic |
| Frontend | `static/js/*.js`, `templates/index.html` | Collect params, call API, render HTML | Compute model math |

---

## Existing Sub-Tab Pattern (Stock Details / Advanced Analytics / Auto Analysis)

The Analysis Results section uses a three-tab structure:

```
div.tabs-container
  div.tabs
    button#stocksTab        onclick="switchTab('stocks')"
    button#analyticsTab     onclick="switchTab('analytics')"
    button#autoanalysisTab  onclick="switchTab('autoanalysis')"

div#tabContents
  div#stocksTabContent      (div#cnnMetrics + div#tickerResults)
  div#analyticsTabContent   (div#analyticsResults)
  div#autoanalysisTabContent
```

`TabManager.switchTab(tabName)` in `tabs.js` validates against a hardcoded `validTabs` array:
```js
const validTabs = ['stocks', 'analytics', 'autoanalysis'];
```

**This array must be extended to include the new tab name when the fourth tab is added.**

---

## Existing Per-Ticker Deep Analysis Pattern

Each ticker card has a `div.deep-analysis-group` injected by `HealthScore.computeGrade()` (Phase 13). Inside that group is a `div#deep-analysis-content-{TICKER}` that subsequent modules append into:

```
div.ticker-results
  div.ticker-header (collapsible)
  div.ticker-content
    div.metrics-grid
    div.deep-analysis-group#deep-analysis-group-{TICKER}
      div.deep-analysis-header (toggle)
      div#deep-analysis-content-{TICKER}
        ← EarningsQuality.renderIntoGroup() appends here (Phase 14)
        ← DCFValuation.renderIntoGroup()    appends here (Phase 15)
        ← PeerComparison.renderIntoGroup()  appends here (Phase 16)
```

The Trading Indicators module does NOT fit inside `deep-analysis-content-{TICKER}`. It is a full sub-tab with per-ticker chart sections, not a collapsible metric row. It belongs in its own `div#tradingIndicatorsTabContent` container alongside the existing three tab content divs.

---

## Trading Indicators Integration Architecture

### Decision: New Flask Route, Not an Extension of /api/scrape

**Use a new dedicated route: `GET /api/trading_indicators?ticker=AAPL&lookback=90`**

Reasons:
1. `/api/scrape` is already slow (10–90s for multi-ticker scraping). Adding OHLCV fetch + four indicator computations would make it unbearably slow and break the existing UX.
2. The Trading Indicators tab is triggered lazily when the user clicks into it — the data does not need to be ready when the scrape completes.
3. A GET endpoint with query params (ticker + lookback) mirrors the `/api/peers` pattern, which is the established pattern for per-ticker lazy-loaded analysis.
4. Lookback is user-selectable (30/90/180/365 days). A separate endpoint makes re-fetching on lookback change straightforward — just re-call the same endpoint with a new `lookback` param.
5. Re-using `/api/scrape` data would require passing raw OHLCV through the scrape response, polluting it with MB of time-series data that existing tabs do not need.

**Call timing:** `TradingIndicators.renderIntoTab(ticker, lookback)` is called per-ticker when the Trading Indicators tab is first activated. One fetch per ticker, triggered sequentially on tab click (not on scrape).

### Decision: One Call Per Ticker (Not Batch)

`/api/trading_indicators?ticker=AAPL&lookback=90` returns all four indicator payloads for a single ticker. The JS iterates over `AppState.currentTickers` and issues one fetch per ticker when the tab is activated. This mirrors how `PeerComparison` works per-ticker via `/api/peers?ticker=AAPL`.

**Do not batch multiple tickers into a single request.** The existing pattern is per-ticker lazy calls. Batching would require blocking all renders until the slowest ticker completes.

Session cache (keyed by `ticker + '-' + lookback`) prevents re-fetching on tab re-visits within the same session, matching the `_sessionCache` pattern in `peerComparison.js`.

---

## Component Boundaries: What Is New vs Modified

### New Components

| Component | File | What It Does |
|-----------|------|--------------|
| Backend indicator module | `src/analytics/trading_indicators.py` | Pure Python: fetch OHLCV via yfinance, compute all four indicators, return dict |
| Flask route | `webapp.py` — `/api/trading_indicators` | Parse ticker + lookback, call module, `convert_numpy_types`, jsonify |
| JS module | `static/js/tradingIndicators.js` | Session cache, fetch per ticker, build 2×2 grid HTML, call `Plotly.newPlot()` |

### Modified Components

| Component | File | Modification |
|-----------|------|--------------|
| HTML template | `templates/index.html` | Add 4th tab button + `div#tradingIndicatorsTabContent` |
| Tab router | `static/js/tabs.js` | Add `'tradingindicators'` to `validTabs` array, add case in `switchTab()` |
| Scraper display loop | `static/js/stockScraper.js` | Add `TradingIndicators.clearSession()` call alongside existing clearSession calls; add `TradingIndicators.primeTab(ticker)` call to register tickers |
| Display manager | `static/js/displayManager.js` | No change required — TradingIndicators renders into its own tab, not into `deep-analysis-content-{TICKER}` |

---

## Data Flow for Trading Indicators

```
User scrapes tickers (existing flow — no change)
        ↓
stockScraper.js displayResults() completes
        ↓
TradingIndicators.clearSession() called (alongside HealthScore, EarningsQuality etc.)
TradingIndicators.primeTab(tickers) stores ticker list, clears rendered state
        ↓
User clicks "Trading Indicators" tab button
        ↓
TabManager.switchTab('tradingindicators') called
        ↓
TradingIndicators.onTabActivated() fires (bound once to tab button click event)
        ↓
For each ticker in AppState.currentTickers:
  if (sessionCache[ticker+lookback]) → render from cache
  else → fetch('/api/trading_indicators?ticker=AAPL&lookback=90')
        ↓
Flask: yf.Ticker(ticker).history(period=...) → compute indicators
        ↓
Returns JSON: { ticker, lookback, bias, bias_rationale,
                liquidity_sweep: { dates, prices, swept_highs, swept_lows, signal, chart_data },
                order_flow: { ... },
                anchored_vwap: { ... },
                volume_profile: { ... } }
        ↓
JS: build per-ticker section (composite bias card + 2×2 Plotly grid)
Write to sessionCache[ticker+lookback]
```

---

## JS Module Structure: tradingIndicators.js

```js
(function () {
    'use strict';

    // Session cache: key = ticker + '-' + lookback, value = rendered DOM element
    var _cache = {};
    var _currentLookback = 90;  // default, updated by dropdown

    // -------------------------------------------------------------------------
    // Public API (mirrors pattern of peerComparison.js)
    // -------------------------------------------------------------------------

    // Called once by stockScraper.js after scrape completes (clears stale state)
    function clearSession() {
        _cache = {};
        var container = document.getElementById('tradingIndicatorsTabContent');
        if (container) container.innerHTML = '';
    }

    // Called when user clicks into the Trading Indicators tab
    // Renders all tickers (fetching as needed)
    function onTabActivated(tickers, lookback) {
        _currentLookback = lookback || _currentLookback;
        var container = document.getElementById('tradingIndicatorsTabContent');
        if (!container) return;
        container.innerHTML = '';

        tickers.forEach(function (ticker) {
            var section = _buildTickerShell(ticker);
            container.appendChild(section);
            _fetchAndRender(ticker, _currentLookback, section);
        });
    }

    // Called by lookback dropdown onChange — clears cache for new lookback and re-renders
    function onLookbackChange(newLookback, tickers) {
        _currentLookback = newLookback;
        // Only clear cache entries for the old lookback; new lookback may already be cached
        onTabActivated(tickers, newLookback);
    }

    // -------------------------------------------------------------------------
    // Internal: per-ticker section DOM structure
    // -------------------------------------------------------------------------

    function _buildTickerShell(ticker) {
        var div = document.createElement('div');
        div.className = 'ti-ticker-section';
        div.id = 'ti-section-' + ticker;
        div.innerHTML =
            '<div class="ti-ticker-header"><h3>' + ticker + '</h3></div>' +
            '<div class="ti-bias-card" id="ti-bias-' + ticker + '">Loading...</div>' +
            '<div class="ti-grid" id="ti-grid-' + ticker + '">' +
            '  <div class="ti-cell" id="ti-cell-liquidity-' + ticker + '"><div class="ti-chart" id="ti-chart-liquidity-' + ticker + '"></div></div>' +
            '  <div class="ti-cell" id="ti-cell-orderflow-' + ticker + '"><div class="ti-chart" id="ti-chart-orderflow-' + ticker + '"></div></div>' +
            '  <div class="ti-cell" id="ti-cell-vwap-' + ticker + '"><div class="ti-chart" id="ti-chart-vwap-' + ticker + '"></div></div>' +
            '  <div class="ti-cell" id="ti-cell-volume-' + ticker + '"><div class="ti-chart" id="ti-chart-volume-' + ticker + '"></div></div>' +
            '</div>';
        return div;
    }

    // -------------------------------------------------------------------------
    // Internal: fetch + render
    // -------------------------------------------------------------------------

    function _fetchAndRender(ticker, lookback, sectionEl) {
        var cacheKey = ticker + '-' + lookback;
        if (_cache[cacheKey]) {
            // Replace section with cached DOM (or re-use rendered state — simpler: just re-call Plotly.react)
            _renderFromData(ticker, _cache[cacheKey], sectionEl);
            return;
        }

        fetch('/api/trading_indicators?ticker=' + encodeURIComponent(ticker) + '&lookback=' + lookback)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) {
                    sectionEl.querySelector('#ti-bias-' + ticker).textContent = 'Unavailable: ' + data.error;
                    return;
                }
                _cache[cacheKey] = data;
                _renderFromData(ticker, data, sectionEl);
            })
            .catch(function () {
                sectionEl.querySelector('#ti-bias-' + ticker).textContent = 'Failed to load indicators.';
            });
    }

    function _renderFromData(ticker, data, sectionEl) {
        _renderBiasCard(ticker, data);
        _renderChart('liquidity', ticker, data.liquidity_sweep);
        _renderChart('orderflow', ticker, data.order_flow);
        _renderChart('vwap',      ticker, data.anchored_vwap);
        _renderChart('volume',    ticker, data.volume_profile);
    }

    function _renderBiasCard(ticker, data) {
        var el = document.getElementById('ti-bias-' + ticker);
        if (!el) return;
        var biasClass = { 'BULLISH': 'badge-success', 'BEARISH': 'badge-danger', 'NEUTRAL': 'badge-warning' }[data.bias] || 'badge-warning';
        el.innerHTML =
            '<span>Composite Bias: <span class="badge ' + biasClass + '">' + (data.bias || 'N/A') + '</span></span>' +
            '<span style="font-size:13px;color:#555;margin-left:12px;">' + (data.bias_rationale || '') + '</span>';
    }

    function _renderChart(key, ticker, payload) {
        var chartDivId = 'ti-chart-' + key + '-' + ticker;
        var chartDiv = document.getElementById(chartDivId);
        if (!chartDiv || !payload) return;
        // Each indicator provides its own Plotly traces + layout in the payload
        Plotly.newPlot(chartDivId, payload.traces, payload.layout, { responsive: true, displayModeBar: false });
        // Signal label
        var cellEl = document.getElementById('ti-cell-' + key + '-' + ticker);
        if (cellEl && payload.signal) {
            var labelEl = cellEl.querySelector('.ti-signal-label') || document.createElement('div');
            labelEl.className = 'ti-signal-label';
            labelEl.textContent = payload.signal;
            if (!cellEl.contains(labelEl)) cellEl.appendChild(labelEl);
        }
    }

    // -------------------------------------------------------------------------
    // Expose
    // -------------------------------------------------------------------------

    window.TradingIndicators = {
        clearSession:    clearSession,
        onTabActivated:  onTabActivated,
        onLookbackChange: onLookbackChange
    };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.TradingIndicators;
    }
}());
```

---

## HTML Structure Changes

### 1. Add the fourth tab button (in `templates/index.html`, inside `div.tabs`)

```html
<button class="tab-button" onclick="switchTab('tradingindicators')" id="tradingindicatorsTab">
    📉 Trading Indicators
</button>
```

Place it after the existing `autoanalysisTab` button.

### 2. Add the tab content div (inside `div#tabContents`)

```html
<!-- Tab 4: Trading Indicators -->
<div class="tab-content" id="tradingIndicatorsTabContent">
    <!-- Lookback selector -->
    <div style="margin-bottom: 16px; display: flex; align-items: center; gap: 12px;">
        <label style="font-weight: 600;">Lookback period:</label>
        <select id="tiLookbackSelect" onchange="TradingIndicators.onLookbackChange(parseInt(this.value), AppState.currentTickers)">
            <option value="30">30 days</option>
            <option value="90" selected>90 days</option>
            <option value="180">180 days</option>
            <option value="365">365 days</option>
        </select>
    </div>
    <!-- Per-ticker sections injected here by tradingIndicators.js -->
</div>
```

### 3. Add script tag in `index.html` (after existing module script tags)

```html
<script src="{{ url_for('static', filename='js/tradingIndicators.js') }}"></script>
```

---

## tabs.js Changes

```js
// Add 'tradingindicators' to validTabs array
const validTabs = ['stocks', 'analytics', 'autoanalysis', 'tradingindicators'];

// Add case in switchTab():
} else if (tabName === 'tradingindicators') {
    const tiTab = document.getElementById('tradingindicatorsTab');
    const tiContent = document.getElementById('tradingIndicatorsTabContent');
    if (tiTab && tiContent) {
        tiTab.classList.add('active');
        tiContent.classList.add('active');
        // Trigger lazy load on first activation
        if (window.TradingIndicators && window.AppState && window.AppState.currentTickers) {
            TradingIndicators.onTabActivated(AppState.currentTickers);
        }
    }
}
```

The lazy-load trigger in `switchTab()` is preferable to binding a click handler on the button — it avoids duplicate binding on re-renders and keeps all tab logic in one place.

---

## stockScraper.js Changes

In `displayResults()`, alongside the existing `clearSession` calls:

```js
// Clear Trading Indicators session cache on new scrape
if (typeof TradingIndicators !== 'undefined') TradingIndicators.clearSession();
```

No further change needed in `stockScraper.js`. The tab activation flow in `TabManager.switchTab('tradingindicators')` handles all rendering.

---

## Flask Backend Structure: src/analytics/trading_indicators.py

The backend module follows Pattern 2 (Fetch-Then-Compute) from the existing ARCHITECTURE.md. All indicator computation is pure Python. The module is lazy-imported inside the route function.

```python
# src/analytics/trading_indicators.py

import yfinance as yf
import numpy as np
import pandas as pd

def compute_indicators(ticker: str, lookback: int) -> dict:
    """
    Fetch OHLCV and compute all four indicators.
    Returns a dict safe to pass to convert_numpy_types() then jsonify().
    """
    end = pd.Timestamp.today()
    start = end - pd.Timedelta(days=lookback)
    hist = yf.Ticker(ticker).history(start=start.strftime('%Y-%m-%d'),
                                      end=end.strftime('%Y-%m-%d'),
                                      auto_adjust=True)
    if hist.empty:
        return {'error': f'No OHLCV data for {ticker}'}

    result = {}
    result['liquidity_sweep'] = _compute_liquidity_sweep(hist)
    result['order_flow']      = _compute_order_flow(hist)
    result['anchored_vwap']   = _compute_anchored_vwap(hist)
    result['volume_profile']  = _compute_volume_profile(hist)
    result['bias'], result['bias_rationale'] = _compute_composite_bias(result)

    return result


def _compute_liquidity_sweep(hist: pd.DataFrame) -> dict:
    # Detect swept swing highs/lows
    # Returns Plotly-ready traces + layout + signal label
    ...

def _compute_order_flow(hist: pd.DataFrame) -> dict:
    # Buy/sell delta, imbalance candles
    ...

def _compute_anchored_vwap(hist: pd.DataFrame) -> dict:
    # Auto-anchors: 52-wk high/low date, optional earnings date
    ...

def _compute_volume_profile(hist: pd.DataFrame) -> dict:
    # POC/VAH/VAL + horizontal bar histogram
    ...

def _compute_composite_bias(indicators: dict) -> tuple:
    # Aggregate signals into BULLISH / BEARISH / NEUTRAL + one-line rationale
    signals = [
        indicators.get('liquidity_sweep', {}).get('signal'),
        indicators.get('order_flow', {}).get('signal'),
        indicators.get('anchored_vwap', {}).get('signal'),
        indicators.get('volume_profile', {}).get('signal'),
    ]
    bull = sum(1 for s in signals if s == 'BULLISH')
    bear = sum(1 for s in signals if s == 'BEARISH')
    if bull >= 3:
        return 'BULLISH', f'{bull}/4 indicators bullish'
    elif bear >= 3:
        return 'BEARISH', f'{bear}/4 indicators bearish'
    else:
        return 'NEUTRAL', f'{bull} bullish, {bear} bearish'
```

### Flask Route

```python
@app.route('/api/trading_indicators', methods=['GET'])
def trading_indicators_endpoint():
    ticker  = request.args.get('ticker', '').strip().upper()
    lookback = int(request.args.get('lookback', 90))
    if not ticker:
        return jsonify({'error': 'ticker parameter required'}), 400
    if lookback not in (30, 90, 180, 365):
        return jsonify({'error': 'lookback must be 30, 90, 180, or 365'}), 400
    try:
        from src.analytics.trading_indicators import compute_indicators
        result = compute_indicators(ticker, lookback)
        result = convert_numpy_types(result)
        return jsonify(result)
    except Exception as e:
        logger.exception(f'trading_indicators error for {ticker}')
        return jsonify({'error': str(e)}), 500
```

---

## Plotly Chart Payload Shape (Per Indicator)

Each indicator's dict must include a `traces` list and `layout` dict that can be passed directly to `Plotly.newPlot(divId, traces, layout)`. This keeps all chart logic in Python and all DOM manipulation in JS.

```python
# Example shape for liquidity_sweep
{
    'traces': [
        {'type': 'candlestick', 'x': dates, 'open': opens, 'high': highs, 'low': lows, 'close': closes, 'name': 'Price'},
        {'type': 'scatter',     'x': sweep_dates, 'y': sweep_prices, 'mode': 'markers', 'marker': {'color': 'red'}, 'name': 'Swept Level'}
    ],
    'layout': {
        'title': 'Liquidity Sweep',
        'height': 280,
        'margin': {'t': 30, 'b': 30, 'l': 40, 'r': 10},
        'showlegend': False
    },
    'signal': 'BULLISH'   # one of BULLISH / BEARISH / NEUTRAL
}
```

The JS `_renderChart()` function simply calls `Plotly.newPlot(divId, payload.traces, payload.layout)`. The backend owns all chart configuration decisions.

---

## Suggested Build Order

Dependencies flow strictly downward: backend module → Flask route → JS module → HTML. Do not start a step until its dependency is complete.

### Step 1: Backend Module (`src/analytics/trading_indicators.py`)
Build all four indicator functions. Return hardcoded stub Plotly traces in early iterations to verify the round-trip before finalising math.

**Why first:** The Flask route and JS are useless without it. Stub data unblocks JS development.

### Step 2: Flask Route (`webapp.py`)
Add `GET /api/trading_indicators`. Wire to Step 1. Verify with curl or Postman that the response is valid JSON.

**Why before JS:** The JS fetch will fail until the route exists.

### Step 3: JS Module (`static/js/tradingIndicators.js`)
Implement the full module against the real API shape. Use the stub response from Step 1 to develop the rendering code before the real math is done.

**Why third:** Unblocks HTML wiring without needing correct indicator math.

### Step 4: HTML + tabs.js wiring
Add the fourth tab button, `tradingIndicatorsTabContent` div, lookback dropdown, and script tag. Extend `tabs.js` `validTabs` and `switchTab()`. Add `clearSession` call in `stockScraper.js`.

**Why last:** Structural change to the existing tab system is the most disruptive step and should only happen once the new component is known to work.

### Step 5: Indicator Math Completion
Implement the real Liquidity Sweep, Order Flow, Anchored VWAP, and Volume Profile algorithms. Validate each against known reference values or visual inspection before finalising signals.

**Why last:** Math can be iterated in isolation inside `trading_indicators.py` without touching frontend code. Once the pipeline is wired, math updates only require backend changes.

---

## Anti-Patterns to Avoid (Trading Indicators Specific)

### Anti-Pattern: Re-Fetching OHLCV on Every Tab Switch
Avoid calling the API again when the user switches away and back to the Trading Indicators tab. The session cache in `tradingIndicators.js` (keyed by `ticker + '-' + lookback`) prevents this. Check `_cache[cacheKey]` before every fetch call.

### Anti-Pattern: Blocking Scrape on Indicator Fetch
Never fetch indicator data inside `/api/scrape`. Indicators must be lazy-loaded when the tab is activated. Injecting OHLCV time-series into the scrape response would increase payload size by 10–100x and slow the initial load.

### Anti-Pattern: Plotly Layout in JS
Do not build Plotly layout objects in `tradingIndicators.js`. The backend `trading_indicators.py` owns all chart configuration (title, height, colors, axis config). JS only calls `Plotly.newPlot(id, payload.traces, payload.layout)`. This keeps chart logic testable in Python and avoids JS becoming a chart configuration layer.

### Anti-Pattern: Appending to deep-analysis-content-{TICKER}
Trading Indicators renders into its own tab content div, not inside the `deep-analysis-content-{TICKER}` container used by Phase 13–16 modules. Do not call `renderIntoGroup()` from within `displayManager.createTickerCard()`. The tab activation path is the correct trigger.

### Anti-Pattern: One Massive API Call for All Tickers
Do not add a `POST /api/trading_indicators` that accepts a list of tickers and returns all results at once. This would block rendering until the slowest ticker completes. The per-ticker GET pattern (`/api/peers` precedent) allows progressive rendering.

---

## Component Summary: Modified vs New

| Component | Status | Files |
|-----------|--------|-------|
| `src/analytics/trading_indicators.py` | NEW | All indicator math, yfinance fetch, Plotly payload builders |
| `/api/trading_indicators` route | NEW (add to webapp.py) | ~20 lines: parse GET params, lazy import, convert, jsonify |
| `static/js/tradingIndicators.js` | NEW | Session cache, tab activation handler, per-ticker render, Plotly calls |
| `templates/index.html` | MODIFIED | Add 4th tab button + content div + lookback select + script tag |
| `static/js/tabs.js` | MODIFIED | Extend validTabs array, add switchTab case with lazy-load trigger |
| `static/js/stockScraper.js` | MODIFIED | Add clearSession call in displayResults() |
| `static/js/displayManager.js` | UNCHANGED | No changes needed |

---

## Sources

- Direct inspection of `static/js/tabs.js` (full file, validTabs array and switchTab logic)
- Direct inspection of `static/js/stockScraper.js` (displayResults, clearSession calls, lines 185–274)
- Direct inspection of `static/js/displayManager.js` (createTickerCard, Phase 13–16 injection points)
- Direct inspection of `static/js/peerComparison.js` (per-ticker fetch pattern, session cache pattern)
- Direct inspection of `static/js/healthScore.js` (deep-analysis-group DOM structure)
- Direct inspection of `templates/index.html` (tab button structure, tab content div structure, lines 135–227)
- Direct inspection of `webapp.py` (all routes, `/api/peers` GET pattern at line 2070, `/api/regime_detection` yfinance fetch pattern at line 1296)
- `.planning/PROJECT.md` and `.planning/research/ARCHITECTURE.md` (prior architecture docs)
