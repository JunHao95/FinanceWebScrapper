# Phase 28: Enhance the Stock Details Tab - Research

**Researched:** 2026-05-06
**Domain:** Frontend UI restructure (vanilla JS, Plotly, sessionStorage) + Flask backend endpoint (yfinance OHLC)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Price chart style:** Candlestick via Plotly (not Chart.js, not a line chart). Volume bars as a subplot below. No MA overlays.
- **Price chart timeframe:** 1M / 3M / 6M / 1Y toggle buttons (four presets, ~30/90/180/365 days).
- **Price chart placement:** Top of each expanded ticker card, before all other content.
- **Backend for price chart:** New `GET /api/price_history?ticker=AAPL&period=3mo` endpoint using `fetch_ohlcv` from `trading_indicators.py`.
- **Analyst target visualization:** Horizontal range bar (Low–Mean–High) with current price as a dot overlay. Color: green dot if price < mean target (upside), red if price > mean target.
- **Consensus badge:** Show Buy/Hold/Sell alongside range bar using existing scraped data.
- **Analyst target placement:** After price chart, before metrics grid.
- **Analyst target backend:** No new endpoint — data already in scrape response (`Analyst Price Target Mean/Low/High (Yahoo)`, `Analyst Price Target Mean/Low/High (Finhub)`).
- **Color coding:** Threshold-based per metric on key financial ratios only. No trend arrows.
- **Tooltips:** Hover tooltip on key metrics only (P/E, Forward P/E, P/B, P/S, PEG, EV/EBITDA, ROE, ROA, ROIC, Profit Margin, Operating Margin, Debt/Equity, Current Ratio). Pure CSS — no library.
- **Sub-tab structure (five tabs):**
  - Overview: price chart + analyst range bar + Basic Info metrics
  - Financials: Valuation + Profitability + Earnings + Financial Metrics + Cash/CashFlow groups
  - Technical: RSI, MA10/20/50, BB Signal
  - Sentiment: full Sentiment Analysis block
  - Deep Analysis: HealthScore + EarningsQuality + DCFValuation + PeerComparison + FundamentalAnalysis
- **Sub-tab persistence:** sessionStorage, keyed as `subtab-{ticker}` (extends existing `collapse-{ticker}-{section}` scheme). Default: Overview active on first open.

### Claude's Discretion
- None noted — discussion stayed within locked decisions.

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 28 is a pure frontend restructure of `DisplayManager.createTickerCard` (the central function that renders every per-ticker card in the Stock Details tab) plus a single new Flask endpoint for OHLC history. All analysis modules already exist and produce data — the work is reorganizing HTML output into five sub-tabs, adding a candlestick chart fetched lazily, rendering an SVG/HTML analyst target range bar from already-scraped data, and applying color coding + CSS tooltips to metric labels.

The phase has no new Python analytics to build, no new scraping, and no new external dependencies. The entire risk surface is in refactoring `createTickerCard` without breaking existing module injection points (HealthScore, EarningsQuality, DCFValuation, PeerComparison all call `renderIntoGroup` on the card DOM element after `innerHTML` is set).

The price history endpoint reuses the existing `fetch_ohlcv` function from `src/analytics/trading_indicators.py` — tested, production-proven, and already handles the yfinance `.history()` + timezone-normalization pattern.

**Primary recommendation:** Refactor `createTickerCard` to emit five sub-tab shells, move existing group assignments into sub-tab content divs, then add price chart JS module and backend endpoint following the `TradingIndicators`/`MLSignals` lazy-fetch pattern exactly.

---

## Standard Stack

### Core (all already loaded in the project — no new installs)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Plotly.js | Already global | Candlestick chart + volume subplot | All other indicator charts use it; `Plotly.newPlot` already called from multiple JS modules |
| yfinance | Already installed | OHLC history fetch via `Ticker.history()` | Used by every other backend data fetch; `fetch_ohlcv` in `trading_indicators.py` is canonical |
| sessionStorage (Web API) | Browser native | Sub-tab persistence per ticker | `SectionCollapse` already uses this pattern with `collapse-{ticker}-{section}` keys |
| Vanilla JS (IIFE pattern) | N/A | All new JS follows existing module pattern | Every JS module (tradingIndicators, mlSignals, peerComparison) uses `(function(){ 'use strict'; ... }())` |
| Flask | Already running | New `/api/price_history` endpoint | Existing Flask app in `webapp.py` |

### No New Dependencies

This phase introduces zero new pip packages and zero new JS libraries. The analyst range bar is pure HTML/CSS. Tooltips are pure CSS. The chart is Plotly (already present). The OHLC fetch reuses `fetch_ohlcv`.

---

## Architecture Patterns

### Recommended Project Structure

No new files needed for the backend — add one route to `webapp.py`. For the frontend, add one new JS module:

```
static/js/
├── displayManager.js     # MODIFY — refactor createTickerCard for sub-tabs
├── utils.js              # MODIFY — add colorCodeMetric() helper
├── priceChart.js         # NEW — lazy-fetch candlestick + volume chart
└── (all others unchanged)

webapp.py                 # MODIFY — add /api/price_history route
```

### Pattern 1: Sub-tab HTML Markup (within `createTickerCard`)

**What:** Replace the flat `metrics-grid` div with five labeled sub-tab buttons and five content panes inside each `ticker-content` div.

**When to use:** Called once per ticker in `createTickerCard`; markup must be self-contained and ticker-namespaced.

**Key detail:** Sub-tab IDs must be ticker-namespaced to prevent collisions when multiple tickers are expanded simultaneously.

```html
<!-- Inside ticker-content div, replacing the flat metrics-grid -->
<div class="ticker-subtabs">
  <div class="ticker-subtab-nav">
    <button class="ticker-subtab-btn active" onclick="DisplayManager.switchSubTab('AAPL', 'overview')">Overview</button>
    <button class="ticker-subtab-btn"        onclick="DisplayManager.switchSubTab('AAPL', 'financials')">Financials</button>
    <button class="ticker-subtab-btn"        onclick="DisplayManager.switchSubTab('AAPL', 'technical')">Technical</button>
    <button class="ticker-subtab-btn"        onclick="DisplayManager.switchSubTab('AAPL', 'sentiment')">Sentiment</button>
    <button class="ticker-subtab-btn"        onclick="DisplayManager.switchSubTab('AAPL', 'deep')">Deep Analysis</button>
  </div>
  <div id="subtab-AAPL-overview"   class="ticker-subtab-content active">...</div>
  <div id="subtab-AAPL-financials" class="ticker-subtab-content">...</div>
  <div id="subtab-AAPL-technical"  class="ticker-subtab-content">...</div>
  <div id="subtab-AAPL-sentiment"  class="ticker-subtab-content">...</div>
  <div id="subtab-AAPL-deep"       class="ticker-subtab-content">...</div>
</div>
```

### Pattern 2: sessionStorage Sub-tab Persistence

**What:** Extend existing `SectionCollapse` key scheme — store active sub-tab name per ticker in sessionStorage.

**Key used:** `subtab-{ticker}` (e.g., `subtab-AAPL`)

**Implementation in `DisplayManager.switchSubTab`:**

```javascript
function switchSubTab(ticker, tabName) {
    // deactivate all subtab content panes and buttons for this ticker
    document.querySelectorAll(`[id^="subtab-${ticker}-"]`).forEach(el => el.classList.remove('active'));
    document.querySelectorAll(`.ticker-subtab-btn[data-ticker="${ticker}"]`).forEach(b => b.classList.remove('active'));
    // activate selected
    document.getElementById(`subtab-${ticker}-${tabName}`).classList.add('active');
    // find and activate button
    // persist
    sessionStorage.setItem(`subtab-${ticker}`, tabName);
    // lazy-trigger price chart on first overview open
    if (tabName === 'overview' && typeof PriceChart !== 'undefined') {
        PriceChart.fetchIfNeeded(ticker, '3mo');
    }
}
```

### Pattern 3: Lazy-Fetch Price Chart Module (priceChart.js)

**What:** New IIFE module following `tradingIndicators.js` / `mlSignals.js` pattern. Session cache keyed by `ticker + '-' + period`. Fetch triggers on Overview sub-tab activation (not on scrape).

**Backend call:** `GET /api/price_history?ticker=AAPL&period=3mo`

**Plotly candlestick + volume subplot pattern (matches existing backend layout):**

```javascript
// priceChart.js — key structure
(function () {
    'use strict';
    var _sessionCache = {};

    function clearSession() {
        Object.keys(_sessionCache).forEach(function (k) { delete _sessionCache[k]; });
    }

    function fetchIfNeeded(ticker, period) {
        var key = ticker + '-' + period;
        if (_sessionCache[key]) return;
        _sessionCache[key] = true;
        fetch('/api/price_history?ticker=' + encodeURIComponent(ticker) + '&period=' + encodeURIComponent(period))
            .then(function (r) { return r.json(); })
            .then(function (resp) { _render(ticker, period, resp); })
            .catch(function (err) { console.error('[PriceChart] fetch failed:', err); });
    }

    function _render(ticker, period, resp) {
        var chartId = 'priceChart-' + ticker;
        if (!document.getElementById(chartId)) return;
        // resp.traces = [candlestick trace, volume bar trace]
        // resp.layout = Plotly layout with dark theme
        Plotly.newPlot(chartId, resp.traces, resp.layout, { responsive: true, displayModeBar: false });
    }

    window.PriceChart = { fetchIfNeeded: fetchIfNeeded, clearSession: clearSession };
}());
```

### Pattern 4: Backend `/api/price_history` Endpoint

**What:** New GET route in `webapp.py` that maps `period` query param to day count and calls `fetch_ohlcv`.

**Period mapping:** `1mo=30`, `3mo=90`, `6mo=180`, `1y=365`

**Returns:** JSON with Plotly-ready traces (candlestick + volume) and layout.

```python
@app.route("/api/price_history", methods=["GET"])
def get_price_history():
    ticker = request.args.get("ticker", "").strip().upper()
    period = request.args.get("period", "3mo").strip()
    if not ticker:
        return jsonify({"error": "ticker parameter required"})
    period_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}
    days = period_map.get(period, 90)
    try:
        from src.analytics.trading_indicators import fetch_ohlcv
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        df = fetch_ohlcv(ticker, days)
        dates = df.index.strftime('%Y-%m-%d').tolist()

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            row_heights=[0.75, 0.25], vertical_spacing=0.02)
        fig.add_trace(go.Candlestick(
            x=dates, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name='Price'
        ), row=1, col=1)
        fig.add_trace(go.Bar(
            x=dates, y=df['Volume'], name='Volume',
            marker_color='#45475a'
        ), row=2, col=1)
        fig.update_layout(
            paper_bgcolor='#1e1e2e', plot_bgcolor='#1e1e2e',
            font=dict(color='#cdd6f4'),
            xaxis_rangeslider_visible=False,
            showlegend=False,
            margin=dict(l=60, r=20, t=40, b=40),
            height=400,
        )
        d = fig.to_dict()
        d['layout'].pop('template', None)
        return jsonify({"traces": d['data'], "layout": d['layout']})
    except Exception as e:
        logger.error(f"Error in get_price_history for {ticker}: {e}")
        return jsonify({"error": str(e)}), 500
```

### Pattern 5: Analyst Target Range Bar (Pure HTML/CSS)

**What:** Horizontal bar rendered entirely in JS as HTML markup. No Plotly needed. Uses existing scraped keys.

**Data source resolution order:**
1. `data['Analyst Price Target Mean (Yahoo)']`, Low, High — preferred
2. Fall back to `data['Analyst Price Target Mean (Finhub)']`, Low, High — secondary
3. If neither present: render nothing (skip the range bar entirely)

**Consensus badge:** Derive from `data['recommendationKey']` if present in yfinance info. Note: the yahoo scraper currently does NOT store `recommendationKey` from `yf.Ticker.info`. This field exists in yfinance (`info.get('recommendationKey')` → `'buy'`, `'hold'`, `'sell'`, `'strong_buy'`, `'strong_sell'`) but is not yet scraped. **The planner must include a task to add this field to the yahoo_scraper.** For the badge display: map `strong_buy`/`buy` → green "Buy", `hold` → yellow "Hold", `sell`/`strong_sell` → red "Sell".

**Range bar CSS logic:**
- Container div with known pixel width (100%)
- Low/High define 0%–100% span; Mean is a tick at `(mean - low) / (high - low) * 100%`
- Current price dot at `clamp((currentPrice - low) / (high - low) * 100%, 0%, 100%)`
- Color of current price dot: green if `currentPrice < mean`, red if `currentPrice >= mean`

### Pattern 6: Metric Color Coding

**What:** Extend `Utils.formatValue` (or add a new `Utils.colorCodeMetric(key, value)` helper) to apply color classes based on fixed thresholds.

**Thresholds (locked in CONTEXT.md):**

| Metric keys (partial match) | Green condition | Red condition |
|----------------------------|-----------------|---------------|
| P/E Ratio, Forward P/E | value < 15 | value > 30 |
| P/B Ratio | value < 1.5 | value > 4 |
| P/S Ratio | value < 2 | value > 8 |
| PEG Ratio | value < 1 | value > 2 |
| EV/EBITDA | value < 10 | value > 25 |
| ROE | value > 15 | value < 0 |
| ROA | value > 5 | value < 0 |
| ROIC | value > 10 | value < 0 |
| Profit Margin | value > 10 | value < 0 |
| Operating Margin | value > 10 | value < 0 |
| Debt/Equity, Debt to Equity | value < 0.5 | value > 2 |
| Current Ratio | value > 2 | value < 1 |

**CSS classes to add:** `.metric-value-good` (green text), `.metric-value-bad` (red text). Neutral = no class (existing default).

**Important:** `Utils.parseNumeric` already handles stripping `%`, `$`, `B`, `M`, `K` suffixes — reuse it to extract numeric value before threshold comparison.

### Pattern 7: CSS Tooltips on Metric Labels

**What:** Pure CSS tooltip — no JS, no library.

**How:** Add `data-tooltip="definition text"` attribute to the `.metric-label` span for key metrics. CSS uses `::after` pseudo-element with `content: attr(data-tooltip)` triggered on `.metric-label:hover`.

**Key metrics that get tooltips (13 total):**
P/E Ratio, Forward P/E, P/B Ratio, P/S Ratio, PEG Ratio, EV/EBITDA, ROE, ROA, ROIC, Profit Margin, Operating Margin, Debt/Equity, Current Ratio.

**Tooltip CSS pattern:**
```css
.metric-label[data-tooltip] {
    position: relative;
    cursor: help;
}
.metric-label[data-tooltip]::after {
    content: attr(data-tooltip);
    position: absolute;
    bottom: 125%;
    left: 0;
    background: #313244;
    color: #cdd6f4;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 0.78rem;
    width: 220px;
    white-space: normal;
    z-index: 100;
    display: none;
    pointer-events: none;
}
.metric-label[data-tooltip]:hover::after {
    display: block;
}
```

### Anti-Patterns to Avoid

- **Rebuilding the card on sub-tab switch:** The sub-tab JS only toggles CSS `active` classes — it never re-renders the card HTML. All five content panes are built once when the card is first expanded.
- **Fetching OHLC on scrape:** Price chart data is fetched lazily on Overview sub-tab activation, not during the main scrape. Fetching at scrape time would add N×4 yfinance calls to the scrape latency.
- **Calling `Plotly.newPlot` on a hidden div:** Only render the price chart when the chart container is visible (i.e., when Overview sub-tab is active). Otherwise Plotly cannot calculate correct dimensions.
- **Modifying `renderIntoGroup` target:** EarningsQuality, DCFValuation, PeerComparison call `renderIntoGroup(ticker, data, div)` and append into `div.deep-analysis-group`. The new sub-tab for Deep Analysis must contain a `div.deep-analysis-group` element with the same CSS class — the existing module code must not be changed.
- **Using `yf.download()` instead of `yf.Ticker().history()`:** The project-wide decision (Phase 09-01) mandates `yf.Ticker().history()` to avoid shape corruption in concurrent calls.
- **Breaking the `toggleTicker` collapse:** `createTickerCard` currently emits `ticker-header` + `ticker-content` with `collapsed` classes. The sub-tab refactor must preserve these outer wrappers; sub-tabs live inside `ticker-content`, not replacing it.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OHLC data fetch | Custom yfinance wrapper | `fetch_ohlcv(ticker, days)` from `trading_indicators.py` | Already handles 1.4× buffer for non-trading days, tz normalization, and column slicing |
| Candlestick chart rendering | Canvas/SVG drawing | `Plotly.newPlot` with `go.Candlestick` | Plotly handles OHLC coloring, hover, zoom; already used for all other charts |
| Plotly subplot (price + volume) | Two separate charts | `make_subplots(rows=2, shared_xaxes=True)` | Built-in Plotly utility; shared x-axis sync is not trivial to hand-roll |
| sessionStorage state mgmt | Custom localStorage adapter | Extend `SectionCollapse` key scheme | Pattern is already tested, handles edge cases (missing key = not collapsed) |
| Metric number parsing | Custom string-to-float | `Utils.parseNumeric(val)` | Already strips `%`, `$`, `B`, `M`, `K`, handles `N/A` |
| CSS tooltips | JS tooltip library (tippy, popper) | Pure CSS `::after` with `data-tooltip` attribute | Zero dependency, zero JS; CONTEXT.md says "pure frontend — no library needed" |

---

## Common Pitfalls

### Pitfall 1: `renderIntoGroup` fails because `div.deep-analysis-group` is missing

**What goes wrong:** After the sub-tab refactor, `HealthScore.computeGrade` returns HTML containing `div.deep-analysis-group`. If this gets placed inside the Deep Analysis sub-tab pane, the subsequent `EarningsQuality.renderIntoGroup(ticker, data, div)` call (which does `div.querySelector('.deep-analysis-group')`) works correctly. But if the refactor accidentally puts the HealthScore HTML outside the `div` element passed to `renderIntoGroup`, the `querySelector` returns null and modules silently skip injection.

**How to avoid:** Verify that `HealthScore.computeGrade` output is placed inside the Deep Analysis sub-tab pane, and that the same `div` element (the root `.ticker-results` div) is passed to `renderIntoGroup` calls after `div.innerHTML` is set.

**Warning signs:** Deep Analysis sub-tab shows HealthScore but not EarningsQuality / DCF / Peer Comparison.

### Pitfall 2: `Plotly.newPlot` called on non-existent or hidden container

**What goes wrong:** The chart div `priceChart-{ticker}` is inside the Overview sub-tab pane. If `PriceChart.fetchIfNeeded` is called before the ticker card is expanded (or before the Overview pane is made visible), Plotly will either throw an error or render a 0×0 chart.

**How to avoid:** `fetchIfNeeded` is called inside `switchSubTab` after the Overview pane is made active. The `toggleTicker` expand logic should also call `PriceChart.fetchIfNeeded(ticker, '3mo')` once, immediately after the content div becomes visible (if Overview is the active sub-tab).

**Warning signs:** Chart container exists in DOM but Plotly renders nothing or a tiny 0-height chart.

### Pitfall 3: Period toggle re-fetches same data from cache

**What goes wrong:** The session cache key is `ticker + '-' + period`. Clicking "1Y" then back to "3M" should re-render the cached 3M chart, not re-fetch. But if `Plotly.newPlot` is not called on the re-activation (because the cache is hit and `_render` is not re-called), the chart div shows blank.

**How to avoid:** Separate the "fetch from network" cache from "chart has been rendered for this period" state. On period toggle, always call `_render` if trace data is in cache, even without re-fetching.

**Implementation:** Store fetched traces/layout in the session cache (not just `true`), and on period toggle, call `_render(ticker, period, _sessionCache[key])` if cache hit.

### Pitfall 4: Analyst range bar when only one source has data

**What goes wrong:** Yahoo has Low/Mean/High but Finhub has none (or vice versa). The range bar must not crash if one source is missing.

**How to avoid:** Check `data['Analyst Price Target Mean (Yahoo)']` first. If any of Low/Mean/High for Yahoo is missing/undefined, fall back to Finhub. If both sources are incomplete (can't form a valid Low < Mean < High triple), render nothing (no range bar section).

**Warning signs:** `Uncaught TypeError: Cannot read properties of undefined` in console when a ticker has partial analyst data.

### Pitfall 5: Sub-tab buttons collide across multiple open ticker cards

**What goes wrong:** If onclick handlers use generic class queries (e.g., `document.querySelectorAll('.ticker-subtab-btn')`) instead of ticker-scoped queries, clicking a sub-tab on AAPL's card also deactivates MSFT's card sub-tabs.

**How to avoid:** All subtab DOM operations must be scoped to `document.querySelectorAll('[data-ticker="AAPL"].ticker-subtab-btn')` or equivalent. Use `data-ticker` attributes on all button elements.

### Pitfall 6: `recommendationKey` not in scraped data

**What goes wrong:** The analyst consensus badge requires `recommendationKey` from yfinance `info`. The current `yahoo_scraper.py` does NOT store this field (verified by code inspection: only `targetMeanPrice`, `targetLowPrice`, `targetHighPrice` are extracted from `info`). The badge will always show "N/A" unless the scraper is extended.

**How to avoid:** Add one line to `yahoo_scraper.py`'s yfinance block: `rec_key = info.get('recommendationKey', None); if rec_key: data['Analyst Recommendation (Yahoo)'] = rec_key`. This is a 3-line addition with zero risk.

---

## Code Examples

### Existing `fetch_ohlcv` signature (reuse verbatim)

```python
# Source: src/analytics/trading_indicators.py:16
def fetch_ohlcv(ticker: str, days: int, auto_adjust: bool = True) -> pd.DataFrame:
    # Uses yf.Ticker().history() — NOT yf.download()
    # Returns DataFrame with columns: Open, High, Low, Close, Volume
    # Index: timezone-naive DatetimeIndex
```

### Existing Plotly dark theme constants (copy into new endpoint)

```python
# Source: src/analytics/trading_indicators.py:198-200
PAPER_BG = '#1e1e2e'
PLOT_BG  = '#1e1e2e'
FONT_CLR = '#cdd6f4'
```

### Existing SectionCollapse sessionStorage pattern (extend for sub-tabs)

```javascript
// Source: static/js/displayManager.js:11-47
// Key scheme: 'collapse-{ticker}-{sectionName}'
// Proposed extension: 'subtab-{ticker}' → active sub-tab name string
sessionStorage.setItem('subtab-AAPL', 'financials');
sessionStorage.getItem('subtab-AAPL'); // → 'financials' or null (default: 'overview')
```

### Existing `renderIntoGroup` call site (must not break)

```javascript
// Source: static/js/displayManager.js:192-202
// After div.innerHTML is set, these calls find .deep-analysis-group inside `div`:
EarningsQuality.renderIntoGroup(ticker, data, div);
DCFValuation.renderIntoGroup(ticker, data, div);
PeerComparison.renderIntoGroup(ticker, data, div);
// Deep Analysis sub-tab pane must contain div.deep-analysis-group for these to work
```

### `Utils.parseNumeric` (reuse for threshold color coding)

```javascript
// Source: static/js/utils.js:18-31
// Handles: '15.23%' → 15.23, '$142.5B' → 142_500_000_000, '2.5' → 2.5, 'N/A' → null
Utils.parseNumeric('15.23%'); // → 15.23
Utils.parseNumeric('N/A');    // → null
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `yf.download()` | `yf.Ticker().history()` | Phase 09-01 | Prevents shape corruption in concurrent calls — mandatory for new endpoint |
| Flat metrics-grid (all groups in one scrollable list) | Five sub-tabs per ticker card | Phase 28 | Reduces scroll fatigue; groups related metrics; enables chart placement without excessive page length |
| `deep-analysis-group` appended at bottom of card | Deep Analysis sub-tab | Phase 28 | Same DOM structure, different placement in tab pane |

---

## Open Questions

1. **Analyst consensus badge without `recommendationKey` in scraped data**
   - What we know: The field `recommendationKey` exists in `yf.Ticker.info` (values: `buy`, `hold`, `sell`, `strong_buy`, `strong_sell`) but is not currently extracted by `yahoo_scraper.py`.
   - What's unclear: Whether the field is reliably present for all tickers or only those with analyst coverage.
   - Recommendation: Add the field extraction to the scraper as Wave 0 setup task. If the field is absent for a ticker, omit the consensus badge gracefully (show only the range bar).

2. **Price chart `clearSession` on re-scrape**
   - What we know: `TradingIndicators.clearSession()` and `MLSignals.clearSession()` are called from `stockScraper.js displayResults`. `PriceChart.clearSession()` must also be called there.
   - What's unclear: Whether `stockScraper.js displayResults` has a central location to add this call.
   - Recommendation: Inspect `stockScraper.js displayResults` during planning and add `PriceChart.clearSession()` alongside the existing clear calls.

3. **Plotly render timing for initially-active Overview sub-tab**
   - What we know: Price chart must be fetched lazily on tab activation. But when a user re-expands a previously collapsed ticker (with Overview already active), the chart div exists but Plotly was never called.
   - Recommendation: `toggleTicker` should call `PriceChart.fetchIfNeeded(ticker, currentPeriod)` after expanding if the active sub-tab is 'overview'. Store the active period on the toggle button or read it from a data attribute.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, no version change) |
| Config file | none (pytest.ini not present; uses `pytest` CLI directly) |
| Quick run command | `pytest tests/test_unit_price_chart.py -x -q` |
| Full suite command | `pytest -x -q` |

### Phase Requirements → Test Map

| Behavior | Test Type | Automated Command | File |
|----------|-----------|-------------------|------|
| `/api/price_history` returns 200 with `traces` and `layout` keys | integration | `pytest tests/test_integration_routes.py -k price_history -x` | Wave 0 gap |
| `/api/price_history` with invalid ticker returns `{"error": ...}` | integration | `pytest tests/test_integration_routes.py -k price_history_error -x` | Wave 0 gap |
| `fetch_ohlcv` period-to-days mapping (1mo=30, 3mo=90, 6mo=180, 1y=365) | unit | `pytest tests/test_unit_price_chart.py::test_period_map -x` | Wave 0 gap |
| Analyst range bar renders with Yahoo data present | unit (DOM) | manual-only (DOM rendering) | manual |
| Analyst range bar omitted when no target data | unit | `pytest tests/test_unit_price_chart.py::test_range_bar_missing_data -x` | Wave 0 gap |
| Color coding returns correct CSS class for threshold breach | unit | `pytest tests/test_unit_price_chart.py::test_color_coding -x` | Wave 0 gap |
| Sub-tab sessionStorage key scheme | manual-only (browser) | manual | manual |

### Sampling Rate

- **Per task commit:** `pytest tests/test_unit_price_chart.py tests/test_integration_routes.py -x -q`
- **Per wave merge:** `pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_unit_price_chart.py` — unit tests for period-to-days mapping, analyst range bar logic, color coding thresholds
- [ ] Integration tests for `/api/price_history` route added to `tests/test_integration_routes.py` (or a new `tests/test_price_history.py`)
- [ ] `recommendationKey` scraper addition must be tested with a mock yfinance `info` dict

*(Existing test infrastructure — pytest, conftest.py, `_stub_ohlcv()` fixture pattern — covers all scaffolding needs. No new framework install required.)*

---

## Sources

### Primary (HIGH confidence)

- `static/js/displayManager.js` — full read; confirmed `createTickerCard` structure, `SectionCollapse` pattern, `renderIntoGroup` call sites
- `static/js/tradingIndicators.js` — confirmed IIFE + session cache + `fetchForTicker` lazy pattern
- `static/js/mlSignals.js` — confirmed `clearSession` + `fetchForTicker` pattern
- `static/js/utils.js` — confirmed `parseNumeric` API and `formatValue` structure
- `src/analytics/trading_indicators.py` — confirmed `fetch_ohlcv` signature, Plotly dark theme constants (`#1e1e2e`, `#cdd6f4`), `make_subplots` usage
- `src/scrapers/yahoo_scraper.py` — confirmed analyst price target keys and absence of `recommendationKey` extraction
- `webapp.py` routes — confirmed `/api/trading_indicators` route pattern for new endpoint modeling
- `tests/test_trading_indicators.py` — confirmed `_stub_ohlcv()` fixture and mock pattern for new tests
- `.planning/config.json` — `nyquist_validation` key absent → validation section included

### Secondary (MEDIUM confidence)

- `src/scrapers/api_scraper.py` — confirmed Finhub analyst price target keys (`targetHigh`, `targetLow`, `targetMean`)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all confirmed from direct code inspection; no new dependencies
- Architecture: HIGH — patterns directly verified from existing working modules
- Pitfalls: HIGH — derived from code inspection (renderIntoGroup, yfinance patterns, DOM ID scoping)
- Missing `recommendationKey`: HIGH — confirmed absent from yahoo_scraper.py by direct inspection

**Research date:** 2026-05-06
**Valid until:** 2026-06-06 (stable codebase; yfinance API field names could shift but are verified as of today)
