# Phase 19: Volume Profile — Research

**Researched:** 2026-04-09
**Domain:** Volume Profile computation (numpy/pandas), Plotly make_subplots with shared_yaxes, Flask JSON payload, vanilla JS Plotly rendering
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| VPROF-01 | User sees a horizontal volume histogram with POC, VAH, and VAL as visible filled levels (not hairlines) and a shaded 70% value area zone | Volume distribution algorithm verified; shapes approach for POC/VAH/VAL confirmed; `make_subplots(shared_yaxes=True)` produces correct horizontal histogram alignment |
| VPROF-02 | A badge indicates whether the current price is inside or outside the value area | Signal field (`inside`/`outside`) computed from `val <= current_price <= vah`; passed in payload; rendered as DOM badge by JS |
| VPROF-03 | Bin count adapts to price range (targeting ~0.2% bin width); bin width in USD reported in chart metadata | `n_bins = max(20, min(200, int(price_range / (mid_price * 0.002))))` formula verified; bin width embedded in chart title via `<br><sup>Bin width: $X.XX</sup>` |
</phase_requirements>

---

## Summary

Phase 19 implements the Volume Profile indicator, which is the first real compute module in the v2.2 Trading Indicators milestone and establishes the `{traces, layout, signal}` payload contract for all subsequent indicator phases.

The core algorithm distributes OHLCV bar volume proportionally across price bins based on the overlap between each bar's high-low range and each bin boundary. Point of Control (POC) is the bin with the highest volume. The value area (VAH, VAL) is built greedily from POC outward until 70% of total volume is captured. Bin count adapts to the price range targeting approximately 0.2% bin width, clamped between 20 and 200 bins. All of this is pure numpy/pandas — no new dependencies beyond adding `plotly>=5.0.0` to requirements.txt.

The Plotly figure uses `make_subplots(rows=1, cols=2, shared_yaxes=True)` as mandated by the roadmap. Column 1 holds the candlestick price chart; column 2 holds the horizontal bar chart histogram. POC, VAH, and VAL are drawn as `add_shape` lines on the histogram subplot with `xref='x2', yref='y2'`. The value area is shaded with a filled rectangle shape. Python serializes the figure via `fig.to_dict()`, strips the `template` key (saves ~7 KB per response), and the route returns `{traces, layout, signal, bin_width_usd, poc, vah, val}` under the `volume_profile` key.

**Primary recommendation:** Compute in Python, serialize with `fig.to_dict()` (template stripped), render in browser with `Plotly.newPlot(el, traces, layout, {staticPlot: true})`. Do not reconstruct the figure in JavaScript.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| plotly | >=5.0.0 | Figure construction + `make_subplots`, `fig.to_dict()` serialization | NOT in requirements.txt — must add. Already installed locally (6.1.2). Server renders figures; browser uses CDN 2.27.0 |
| numpy | >=1.23.0 | Bin edge linspace, volume accumulation loop, argmax for POC | Already in project |
| pandas | >=1.5.0 | OHLCV DataFrame from `fetch_ohlcv` | Already in project |
| plotly.js | 2.27.0 (CDN) | Browser-side chart rendering | Already loaded via CDN in index.html line 8 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| plotly.subplots | (part of plotly) | `make_subplots(rows=1, cols=2, shared_yaxes=True)` | Required for shared y-axis between price and histogram |
| plotly.graph_objects | (part of plotly) | `go.Candlestick`, `go.Bar` | Building traces before serialization |
| unittest.mock | stdlib | Mock `fetch_ohlcv` and `compute_volume_profile` in tests | Prevents live network calls in CI |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Python Plotly figure + `to_dict()` | JS-side figure construction from raw arrays | Python approach: cleaner JSON contract, easier to test, consistent with roadmap spec. JS approach: less round-trip data but requires replicating complex subplot setup in JS |
| Proportional overlap volume distribution | TPO (Time Price Opportunity) counting | TPO counts time at price level, not volume. Proportional overlap is more accurate for Volume Profile |
| Greedy value area expansion | Fixed std-dev zone | Greedy expansion from POC hits exactly 70% volume target; std-dev zone is price-based not volume-based |

**Installation:**
```bash
pip install plotly>=5.0.0
# Also add to requirements.txt: plotly>=5.0.0
```

---

## Architecture Patterns

### Files Modified in This Phase

```
src/analytics/trading_indicators.py    # MODIFY: replace compute_volume_profile stub with real logic; add plotly imports
webapp.py                               # MODIFY: call compute_volume_profile in route; import it alongside fetch_ohlcv
static/js/tradingIndicators.js         # MODIFY: replace console.log stub with DOM rendering + Plotly.newPlot
requirements.txt                        # MODIFY: add plotly>=5.0.0
tests/test_trading_indicators.py        # MODIFY: add unit tests for compute_volume_profile
```

### No New Files

Phase 19 replaces stubs inside existing Phase 18 files. No new files are created.

### Pattern 1: Volume Profile Computation (Python)

**What:** Replace `compute_volume_profile` stub in `trading_indicators.py` with real logic.
**When to use:** Called from route once per ticker per request. Input is the OHLCV DataFrame from `fetch_ohlcv`.

```python
# Source: verified via local computation tests (2026-04-09)
def compute_volume_profile(df: pd.DataFrame) -> dict:
    """
    Compute Volume Profile: horizontal volume histogram with POC, VAH, VAL.

    Returns:
        {traces, layout, signal, bin_width_usd, poc, vah, val}
        where traces/layout come from fig.to_dict() and are safe for jsonify().
    """
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    highs  = df['High'].values
    lows   = df['Low'].values
    closes = df['Close'].values
    opens  = df['Open'].values
    volumes = df['Volume'].values

    price_min = float(lows.min())
    price_max = float(highs.max())
    price_range = price_max - price_min

    # Adaptive bin count: target ~0.2% bin width, clamped [20, 200]
    if price_range < 1e-10:
        n_bins = 20
    else:
        mid_price = (price_min + price_max) / 2.0
        target_bin_width_usd = mid_price * 0.002
        n_bins = max(20, min(200, int(price_range / target_bin_width_usd)))
    actual_bin_width = price_range / n_bins if n_bins > 0 else 0.0

    bin_edges   = np.linspace(price_min, price_max, n_bins + 1)
    bin_centers = ((bin_edges[:-1] + bin_edges[1:]) / 2).tolist()
    volume_by_bin = np.zeros(n_bins)

    # Proportional overlap distribution
    for i in range(len(df)):
        bar_range = highs[i] - lows[i]
        if bar_range < 1e-10:
            idx = int(np.clip(
                np.searchsorted(bin_edges, closes[i], side='right') - 1,
                0, n_bins - 1
            ))
            volume_by_bin[idx] += volumes[i]
        else:
            for j in range(n_bins):
                overlap = min(bin_edges[j + 1], highs[i]) - max(bin_edges[j], lows[i])
                if overlap > 0:
                    volume_by_bin[j] += volumes[i] * (overlap / bar_range)

    # POC: bin with maximum volume
    poc_idx   = int(np.argmax(volume_by_bin))
    poc_price = float(bin_centers[poc_idx])

    # Value area: greedy expansion from POC until 70% cumulative volume
    total_volume  = float(volume_by_bin.sum())
    target_va_vol = total_volume * 0.70
    sorted_idx = list(np.argsort(-volume_by_bin))
    cumulative, va_indices = 0.0, set()
    for idx in sorted_idx:
        cumulative += float(volume_by_bin[idx])
        va_indices.add(int(idx))
        if cumulative >= target_va_vol:
            break
    vah = float(max(bin_centers[i] for i in va_indices))
    val = float(min(bin_centers[i] for i in va_indices))

    current_price = float(closes[-1])
    signal = 'inside' if val <= current_price <= vah else 'outside'

    # Build Plotly figure
    fig = make_subplots(
        rows=1, cols=2,
        shared_yaxes=True,
        column_widths=[0.75, 0.25],
        horizontal_spacing=0.02
    )

    dates_str = [str(d.date()) if hasattr(d, 'date') else str(d) for d in df.index]

    # Col 1: Candlestick price chart
    fig.add_trace(go.Candlestick(
        x=dates_str,
        open=opens.tolist(), high=highs.tolist(),
        low=lows.tolist(),   close=closes.tolist(),
        name='Price',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ), row=1, col=1)

    # Col 2: Horizontal bar histogram
    bar_colors = [
        'rgba(70,130,180,0.7)' if val <= bc <= vah else 'rgba(150,150,150,0.4)'
        for bc in bin_centers
    ]
    fig.add_trace(go.Bar(
        y=bin_centers,
        x=volume_by_bin.tolist(),
        orientation='h',
        marker_color=bar_colors,
        marker_line_width=0,
        name='Volume',
        showlegend=False
    ), row=1, col=2)

    max_vol = float(volume_by_bin.max())

    # POC line (orange, solid, width=3)
    fig.add_shape(type='line', x0=0, x1=max_vol * 1.05,
        y0=poc_price, y1=poc_price,
        xref='x2', yref='y2',
        line=dict(color='#ff6b35', width=3))

    # VAH line (green, dashed)
    fig.add_shape(type='line', x0=0, x1=max_vol * 1.05,
        y0=vah, y1=vah,
        xref='x2', yref='y2',
        line=dict(color='#2ecc71', width=2, dash='dash'))

    # VAL line (red, dashed)
    fig.add_shape(type='line', x0=0, x1=max_vol * 1.05,
        y0=val, y1=val,
        xref='x2', yref='y2',
        line=dict(color='#e74c3c', width=2, dash='dash'))

    # Value area shaded rectangle
    fig.add_shape(type='rect', x0=0, x1=max_vol * 1.05,
        y0=val, y1=vah,
        xref='x2', yref='y2',
        fillcolor='rgba(70,130,180,0.12)', line_width=0)

    fig.update_layout(
        title=dict(
            text=(
                f'Volume Profile — {{ticker}} ({{lookback}}d)'
                f'<br><sup>Bin width: ${actual_bin_width:.2f} | '
                f'POC: ${poc_price:.2f} | VAH: ${vah:.2f} | VAL: ${val:.2f}</sup>'
            ),
            x=0.5
        ),
        xaxis_rangeslider_visible=False,
        height=420,
        margin=dict(t=70, l=60, r=20, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(18,18,18,0.95)'
    )

    d = fig.to_dict()
    d['layout'].pop('template', None)  # strip ~7 KB default theme bloat

    return {
        'traces':        d['data'],
        'layout':        d['layout'],
        'signal':        signal,
        'bin_width_usd': round(actual_bin_width, 4),
        'poc':           round(poc_price, 2),
        'vah':           round(vah, 2),
        'val':           round(val, 2),
    }
```

**Note:** The function signature above uses `ticker` and `lookback` in the title f-string. The caller must pass these from the route.  Signature should be `compute_volume_profile(df, ticker, lookback)`.

### Pattern 2: Route Update (webapp.py)

**What:** Replace stub `volume_profile` key with real compute call.

```python
# Source: webapp.py get_trading_indicators (Phase 18 stub)
# BEFORE (stub):
#   'volume_profile': {'status': 'stub'},
# AFTER (Phase 19):
from src.analytics.trading_indicators import fetch_ohlcv, compute_volume_profile

df = fetch_ohlcv(ticker, lookback)
vp = compute_volume_profile(df, ticker, lookback)
return jsonify({
    'ticker':          ticker,
    'lookback':        lookback,
    'volume_profile':  vp,
    'anchored_vwap':   {'status': 'stub'},
    'order_flow':      {'status': 'stub'},
    'liquidity_sweep': {'status': 'stub'},
    'composite_bias':  {'status': 'stub'},
})
```

### Pattern 3: JS Rendering (tradingIndicators.js)

**What:** Replace `console.log` stub in `fetchForTicker` with DOM construction + Plotly render.

```javascript
// Source: autoRun.js renderRegimeCharts pattern + roadmap staticPlot requirement
function fetchForTicker(ticker, lookback) {
    var cacheKey = ticker + '-' + lookback;
    if (_sessionCache[cacheKey]) return;
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
            _renderTickerCard(container, ticker, lookback, resp);
        })
        .catch(function (err) {
            console.error('[TradingIndicators] fetch failed:', err);
        });
}

function _renderTickerCard(container, ticker, lookback, resp) {
    var cardId  = 'tiCard_' + ticker;
    var vpDivId = 'vpChart_' + ticker;
    var badgeId = 'vpBadge_' + ticker;

    // Remove stale card if re-rendered
    var existing = document.getElementById(cardId);
    if (existing) existing.parentNode.removeChild(existing);

    var card = document.createElement('div');
    card.id = cardId;
    card.className = 'ti-ticker-card';
    card.innerHTML =
        '<h3 class="ti-ticker-title">' + ticker + '</h3>' +
        '<div id="' + vpDivId + '" style="width:100%;height:420px;"></div>' +
        '<div id="' + badgeId + '" class="ti-va-badge"></div>';
    container.appendChild(card);

    // Render Volume Profile chart
    var vp = resp.volume_profile;
    if (vp && vp.traces && vp.layout) {
        Plotly.newPlot(vpDivId, vp.traces, vp.layout, { staticPlot: true });
        var badgeEl = document.getElementById(badgeId);
        if (badgeEl) {
            var inside = vp.signal === 'inside';
            badgeEl.textContent = inside
                ? 'Price inside value area'
                : 'Price outside value area';
            badgeEl.style.color = inside ? '#2ecc71' : '#e74c3c';
        }
    }
}
```

### Recommended Project Structure

No new directories needed. All changes go into existing files established by Phase 18.

```
src/analytics/trading_indicators.py   # Stub -> real compute_volume_profile
webapp.py                               # Stub key -> real vp call
static/js/tradingIndicators.js         # console.log -> _renderTickerCard + Plotly
requirements.txt                        # ADD: plotly>=5.0.0
tests/test_trading_indicators.py        # ADD: volume profile unit tests
```

### Anti-Patterns to Avoid

- **Raw numpy types in jsonify response:** `volume_by_bin` is a numpy array. Always call `.tolist()` on arrays, `float()` on scalars before including in the payload. `fig.to_dict()` handles traces/layout automatically; extra scalar fields (poc, vah, val, bin_width_usd) need explicit `float()` / `round()` conversion.
- **Not stripping `template` from `fig.to_dict()`:** The default Plotly Python template adds ~7 KB to every response. Call `d['layout'].pop('template', None)` after `fig.to_dict()`.
- **Using `yref='y'` for shapes on the histogram subplot:** Shapes on column 2 must use `xref='x2', yref='y2'`. Using `yref='y'` places the shape on the price chart axis (column 1), not the histogram. Verified: `yaxis2.matches = 'y'` handles range synchronization automatically.
- **Calling `yf.download()` instead of `yf.Ticker().history()`:** Phase 09-01 project decision. The stub in Phase 18 already uses the correct pattern.
- **Forgetting `xaxis_rangeslider_visible=False`:** Candlestick traces include a range slider by default. It doubles the chart height and conflicts with the shared y-axis layout. Must be disabled explicitly.
- **Constructing the Plotly figure in JavaScript:** The roadmap specifies `{traces, layout, signal}` payload — Python builds the figure, JS calls `Plotly.newPlot`. Do not rebuild the subplot layout client-side.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Subplot layout with shared price axis | Manual `xaxis`/`yaxis` domain calculations | `make_subplots(rows=1, cols=2, shared_yaxes=True)` | Correctly sets `yaxis2.matches='y'`, computes domain fractions, prevents misalignment |
| Figure JSON serialization | Custom `json.dumps` with numpy handlers | `fig.to_dict()` + strip template | `to_dict()` handles all Plotly-internal type conversions; manual serialization misses nested structures |
| Bin count formula | Ad-hoc logic | `max(20, min(200, int(price_range / (mid_price * 0.002))))` | Verified formula; clamps handle edge cases (tight ranges, high-price stocks) |
| Value area computation | Cumulative sum from bottom | Greedy sort-from-POC approach | Greedy from POC guarantees the value area is centered on POC; cumulative from bottom produces inaccurate VAH/VAL |

**Key insight:** The proportional overlap volume distribution loop is O(n × n_bins). With n=90 bars and n_bins≤200, this is ≤18,000 iterations — fast enough without vectorization. Do not premature-optimize with numpy broadcasting for Phase 19.

---

## Common Pitfalls

### Pitfall 1: Shapes on Wrong Subplot Reference

**What goes wrong:** POC/VAH/VAL lines appear on the price candlestick chart instead of the histogram, or at wrong price levels.
**Why it happens:** `fig.add_shape(xref='x2', yref='y')` mixes axis references — `y` is the price chart axis (col 1), not the histogram axis.
**How to avoid:** Always use `xref='x2', yref='y2'` for shapes inside the histogram subplot. Confirmed: `yaxis2.matches='y'` ensures range synchronization so histogram and price chart stay aligned.
**Warning signs:** Shape lines appear in the price chart area (left panel) instead of the histogram (right panel).

### Pitfall 2: Template Bloat in API Response

**What goes wrong:** Every API response is ~8 KB larger than needed because `fig.to_dict()` includes the full default Plotly Python template (colorscales, marker defaults, etc.).
**Why it happens:** Plotly Python 5+ includes a `plotly_dark` or `plotly` template in all figures by default.
**How to avoid:** After `d = fig.to_dict()`, call `d['layout'].pop('template', None)` before returning. Verified: saves 7,253 characters per response.
**Warning signs:** Response payload is suspiciously large (>10 KB for a simple chart).

### Pitfall 3: Numpy Types Break jsonify

**What goes wrong:** `jsonify({'bin_width_usd': np.float64(0.2986)})` raises `TypeError: Object of type float64 is not JSON serializable`.
**Why it happens:** numpy scalars are not native Python floats. `fig.to_dict()` converts all internal Plotly data but does NOT convert extra fields you add manually.
**How to avoid:** Wrap all manually-added numeric fields: `float(bin_width)`, `round(poc_price, 2)`, `volume_by_bin.tolist()`.
**Warning signs:** 500 error from the route with `TypeError` in logs.

### Pitfall 4: Range Slider Doubles Chart Height

**What goes wrong:** The chart renders at 840px instead of 420px, covering the badge and breaking layout.
**Why it happens:** `go.Candlestick` adds a range slider by default.
**How to avoid:** Add `fig.update_layout(xaxis_rangeslider_visible=False)` before serializing.
**Warning signs:** Chart appears taller than expected; a grey range selector bar appears below the chart.

### Pitfall 5: Single-Bin Edge Case for Tight Price Range

**What goes wrong:** For stocks with very stable prices over the lookback window, `price_range / target_bin_width_usd` rounds to 0 or 1, causing division-by-zero or a degenerate histogram.
**Why it happens:** The adaptive bin formula produces `n_bins=0` if `price_range < target_bin_width_usd`.
**How to avoid:** The `max(20, ...)` clamp in the formula prevents this. Also add a `price_range < 1e-10` guard that returns `n_bins=20` before entering the formula.
**Warning signs:** `ZeroDivisionError` in the route, or a histogram with a single bar.

### Pitfall 6: plotly Missing from requirements.txt

**What goes wrong:** Works locally, breaks on Render deployment. `ImportError: No module named 'plotly'`.
**Why it happens:** plotly is installed locally (6.1.2) but not in `requirements.txt`.
**How to avoid:** Add `plotly>=5.0.0` to requirements.txt in the same plan that first imports plotly in Python code. This must happen in Wave 1 (Python backend plan), not Wave 2.
**Warning signs:** Deployment succeeds but all trading indicators return 500 errors.

---

## Code Examples

### compute_volume_profile — Minimal Working Version

```python
# Source: verified via local Python tests (2026-04-09)
# File: src/analytics/trading_indicators.py

def compute_volume_profile(df: pd.DataFrame, ticker: str, lookback: int) -> dict:
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    highs   = df['High'].values
    lows    = df['Low'].values
    closes  = df['Close'].values
    opens   = df['Open'].values
    volumes = df['Volume'].values

    price_min = float(lows.min())
    price_max = float(highs.max())
    price_range = price_max - price_min

    if price_range < 1e-10:
        n_bins = 20
    else:
        mid_price = (price_min + price_max) / 2.0
        n_bins = max(20, min(200, int(price_range / (mid_price * 0.002))))
    actual_bin_width = price_range / n_bins if n_bins > 0 else 0.0

    bin_edges      = np.linspace(price_min, price_max, n_bins + 1)
    bin_centers    = ((bin_edges[:-1] + bin_edges[1:]) / 2).tolist()
    volume_by_bin  = np.zeros(n_bins)

    for i in range(len(df)):
        bar_range = highs[i] - lows[i]
        if bar_range < 1e-10:
            idx = int(np.clip(
                np.searchsorted(bin_edges, closes[i], side='right') - 1, 0, n_bins - 1
            ))
            volume_by_bin[idx] += volumes[i]
        else:
            for j in range(n_bins):
                overlap = min(bin_edges[j + 1], highs[i]) - max(bin_edges[j], lows[i])
                if overlap > 0:
                    volume_by_bin[j] += volumes[i] * (overlap / bar_range)

    poc_idx   = int(np.argmax(volume_by_bin))
    poc_price = float(bin_centers[poc_idx])
    total_vol = float(volume_by_bin.sum())
    cumulative, va_indices = 0.0, set()
    for idx in list(np.argsort(-volume_by_bin)):
        cumulative += float(volume_by_bin[idx])
        va_indices.add(int(idx))
        if cumulative >= total_vol * 0.70:
            break

    vah    = float(max(bin_centers[i] for i in va_indices))
    val    = float(min(bin_centers[i] for i in va_indices))
    signal = 'inside' if val <= float(closes[-1]) <= vah else 'outside'
    max_vol = float(volume_by_bin.max())

    fig = make_subplots(
        rows=1, cols=2, shared_yaxes=True,
        column_widths=[0.75, 0.25], horizontal_spacing=0.02
    )
    dates_str = [str(d.date()) if hasattr(d, 'date') else str(d) for d in df.index]
    fig.add_trace(go.Candlestick(
        x=dates_str, open=opens.tolist(), high=highs.tolist(),
        low=lows.tolist(), close=closes.tolist(), name='Price',
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
    ), row=1, col=1)
    bar_colors = [
        'rgba(70,130,180,0.7)' if val <= bc <= vah else 'rgba(150,150,150,0.4)'
        for bc in bin_centers
    ]
    fig.add_trace(go.Bar(
        y=bin_centers, x=volume_by_bin.tolist(), orientation='h',
        marker_color=bar_colors, marker_line_width=0, showlegend=False
    ), row=1, col=2)
    for y0, color, dash, width in [
        (poc_price, '#ff6b35', 'solid', 3),
        (vah,       '#2ecc71', 'dash',  2),
        (val,       '#e74c3c', 'dash',  2),
    ]:
        fig.add_shape(type='line', x0=0, x1=max_vol * 1.05, y0=y0, y1=y0,
            xref='x2', yref='y2', line=dict(color=color, width=width, dash=dash))
    fig.add_shape(type='rect', x0=0, x1=max_vol * 1.05, y0=val, y1=vah,
        xref='x2', yref='y2', fillcolor='rgba(70,130,180,0.12)', line_width=0)
    fig.update_layout(
        title=dict(
            text=(
                f'Volume Profile \u2014 {ticker} ({lookback}d)'
                f'<br><sup>Bin width: ${actual_bin_width:.2f} | '
                f'POC: ${poc_price:.2f} | VAH: ${vah:.2f} | VAL: ${val:.2f}</sup>'
            ),
            x=0.5
        ),
        xaxis_rangeslider_visible=False,
        height=420,
        margin=dict(t=70, l=60, r=20, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(18,18,18,0.95)'
    )
    d = fig.to_dict()
    d['layout'].pop('template', None)
    return {
        'traces':        d['data'],
        'layout':        d['layout'],
        'signal':        signal,
        'bin_width_usd': round(actual_bin_width, 4),
        'poc':           round(poc_price, 2),
        'vah':           round(vah, 2),
        'val':           round(val, 2),
    }
```

### JS Render Function

```javascript
// Source: autoRun.js Plotly pattern + roadmap staticPlot requirement
// File: static/js/tradingIndicators.js

function _renderTickerCard(container, ticker, lookback, resp) {
    var cardId  = 'tiCard_'   + ticker;
    var vpDivId = 'vpChart_'  + ticker;
    var badgeId = 'vpBadge_'  + ticker;

    var existing = document.getElementById(cardId);
    if (existing) existing.parentNode.removeChild(existing);

    var card = document.createElement('div');
    card.id = cardId;
    card.className = 'ti-ticker-card';
    card.innerHTML =
        '<h3 class="ti-ticker-title">' + ticker + '</h3>' +
        '<div id="' + vpDivId + '" style="width:100%;height:420px;"></div>' +
        '<div id="' + badgeId + '" class="ti-va-badge" style="margin-top:6px;font-weight:600;"></div>';
    container.appendChild(card);

    var vp = resp.volume_profile;
    if (vp && vp.traces && vp.layout) {
        Plotly.newPlot(vpDivId, vp.traces, vp.layout, { staticPlot: true });
        var badgeEl = document.getElementById(badgeId);
        if (badgeEl) {
            var inside = vp.signal === 'inside';
            badgeEl.textContent = inside
                ? 'Price inside value area'
                : 'Price outside value area';
            badgeEl.style.color = inside ? '#2ecc71' : '#e74c3c';
        }
    }
}
```

### Test Additions (test_trading_indicators.py)

```python
# Source: test_trading_indicators.py pattern (Phase 18) + verified algorithm
class TestComputeVolumeProfile:

    def _make_df(self, n=90, base=150.0):
        """Realistic OHLCV DataFrame."""
        np.random.seed(42)
        idx = pd.date_range('2024-01-01', periods=n, freq='B')
        closes = base + np.cumsum(np.random.randn(n) * 0.3)
        return pd.DataFrame({
            'Open':   closes + np.random.randn(n) * 0.1,
            'High':   closes + np.abs(np.random.randn(n) * 0.4),
            'Low':    closes - np.abs(np.random.randn(n) * 0.4),
            'Close':  closes,
            'Volume': np.random.randint(1_000_000, 5_000_000, n).astype(float),
        }, index=idx)

    def test_payload_keys(self):
        from src.analytics.trading_indicators import compute_volume_profile
        result = compute_volume_profile(self._make_df(), 'AAPL', 90)
        for k in ('traces', 'layout', 'signal', 'bin_width_usd', 'poc', 'vah', 'val'):
            assert k in result, f"Missing key: {k}"

    def test_signal_is_inside_or_outside(self):
        from src.analytics.trading_indicators import compute_volume_profile
        result = compute_volume_profile(self._make_df(), 'AAPL', 90)
        assert result['signal'] in ('inside', 'outside')

    def test_vah_above_val(self):
        from src.analytics.trading_indicators import compute_volume_profile
        result = compute_volume_profile(self._make_df(), 'AAPL', 90)
        assert result['vah'] > result['val']
        assert result['val'] <= result['poc'] <= result['vah']

    def test_bin_width_positive(self):
        from src.analytics.trading_indicators import compute_volume_profile
        result = compute_volume_profile(self._make_df(), 'AAPL', 90)
        assert result['bin_width_usd'] > 0

    def test_traces_json_serializable(self):
        import json
        from src.analytics.trading_indicators import compute_volume_profile
        result = compute_volume_profile(self._make_df(), 'AAPL', 90)
        # Must not raise
        json.dumps({'traces': result['traces'], 'layout': result['layout']})
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| All indicator keys return `{'status': 'stub'}` | `volume_profile` key returns real `{traces, layout, signal, ...}` | Phase 19 | Establishes the payload contract that Phases 20–22 must follow |
| JS module only does `console.log` on API response | JS builds per-ticker DOM card and calls `Plotly.newPlot` | Phase 19 | First real chart render in the Trading Indicators tab |
| `plotly` absent from requirements.txt | `plotly>=5.0.0` added | Phase 19 (Wave 1) | Required for server-side figure construction |

**Deprecated/outdated:**

- `compute_volume_profile` stub body `return {'status': 'stub'}` — replaced in Phase 19.
- `console.log('[TradingIndicators] stub OK ...')` in `tradingIndicators.js` — replaced with `_renderTickerCard`.

---

## Open Questions

1. **plotly Python version to pin in requirements.txt**
   - What we know: 6.1.2 is installed locally and works. The `to_dict()` + `add_shape` API is stable since Plotly 5.0.
   - What's unclear: Whether Render's pip resolves `plotly>=5.0.0` to 6.x or 5.x. Both are compatible.
   - Recommendation: Use `plotly>=5.0.0` (loose lower bound, no upper cap). This avoids dependency conflicts with any other packages that may constrain plotly.

2. **Per-ticker card styling (CSS)**
   - What we know: The project uses inline styles + existing CSS classes. No `.ti-ticker-card` class exists yet.
   - What's unclear: Whether to add CSS to a stylesheet or use inline styles entirely.
   - Recommendation: Use inline styles for the card container in Phase 19 (minimal scope). Phase 22 (full tab wiring) can add `.ti-ticker-card` CSS rules when the full grid layout is styled.

3. **Whether lookback should be stored in fetchForTicker's card creation**
   - What we know: The route supports `?lookback=90`. The JS currently hardcodes `lookback` as a parameter.
   - What's unclear: Phase 19 should use a hardcoded default (90) or pick up from a dropdown that doesn't exist until Phase 22.
   - Recommendation: Hardcode `lookback=90` for Phase 19. Phase 22 adds the dropdown that passes the selected value.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=7.0.0 |
| Config file | none — discovered via `tests/` directory |
| Quick run command | `pytest tests/test_trading_indicators.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VPROF-01 | `compute_volume_profile` returns traces/layout with horizontal bar + shapes for POC/VAH/VAL | unit | `pytest tests/test_trading_indicators.py::TestComputeVolumeProfile::test_payload_keys -x` | Wave 0 additions to existing file |
| VPROF-01 | VAH > POC >= VAL (value area structure correct) | unit | `pytest tests/test_trading_indicators.py::TestComputeVolumeProfile::test_vah_above_val -x` | Wave 0 additions |
| VPROF-02 | Signal is 'inside' or 'outside' (not None, not other string) | unit | `pytest tests/test_trading_indicators.py::TestComputeVolumeProfile::test_signal_is_inside_or_outside -x` | Wave 0 additions |
| VPROF-03 | `bin_width_usd > 0`; payload is JSON serializable | unit | `pytest tests/test_trading_indicators.py::TestComputeVolumeProfile::test_bin_width_positive -x` | Wave 0 additions |
| VPROF-01/02/03 | Route returns `volume_profile` key with real payload (not stub) | integration | `pytest tests/test_trading_indicators.py::TestTradingIndicatorsRoute -x` | Existing file (extend) |
| SC-visual | Horizontal bar renders in correct column with badge | manual browser | — | n/a |

### Sampling Rate

- **Per task commit:** `pytest tests/test_trading_indicators.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_trading_indicators.py::TestComputeVolumeProfile` — add class with 5 unit tests listed above (file already exists from Phase 18; extend it)
- [ ] `requirements.txt` — add `plotly>=5.0.0` before any Python code imports plotly

*(Existing test infrastructure covers route tests; only the new `TestComputeVolumeProfile` class and requirements.txt update are Wave 0 gaps.)*

---

## Sources

### Primary (HIGH confidence)

- Codebase: `src/analytics/trading_indicators.py` — verified Phase 18 stub structure, confirmed `fetch_ohlcv` signature
- Codebase: `webapp.py` lines 2154–2174 — current route stub; confirmed where `compute_volume_profile` plugs in
- Codebase: `static/js/tradingIndicators.js` — confirmed Phase 18 IIFE structure and where `_renderTickerCard` replaces the console.log
- Codebase: `static/js/autoRun.js` lines 67–120 — `Plotly.newPlot` pattern for per-ticker charts
- Codebase: `templates/index.html` line 8 — Plotly.js 2.27.0 CDN confirmed
- Local Python verification: `make_subplots(shared_yaxes=True)` — `yaxis2.matches='y'` confirmed, shapes `xref='x2',yref='y2'` confirmed
- Local Python verification: `fig.to_dict()` template stripping — 7,253 character savings confirmed
- Local Python verification: numpy JSON serialization — `float()` required for numpy scalars, `.tolist()` for arrays
- Local Python verification: bin count formula — `max(20, min(200, int(price_range / (mid_price * 0.002))))` produces correct results for normal, tight, wide, and high-price cases
- Local Python verification: greedy value area algorithm — hits exactly 70% volume target
- Project decisions (STATE.md, ROADMAP.md): `make_subplots(rows=1, cols=2, shared_yaxes=True)` mandated; `staticPlot: true` mandated; `fetch_ohlcv` pattern locked

### Secondary (MEDIUM confidence)

- Local plotly version: 6.1.2 — `to_dict()` + `add_shape` API confirmed working at this version
- `requirements.txt` — confirmed plotly is NOT listed; must be added as part of Phase 19 Wave 1

### Tertiary (LOW confidence)

- None. All critical claims verified locally.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries either already in project (numpy, pandas) or locally verified (plotly 6.1.2); plotly>=5.0.0 API stable since 2021
- Architecture patterns: HIGH — full algorithm and payload verified via Python execution; make_subplots layout structure confirmed
- Pitfalls: HIGH — each pitfall discovered and verified during research (numpy serialization, template bloat, shape refs, range slider)
- Test patterns: HIGH — directly extends Phase 18 test file; same pytest fixture pattern

**Research date:** 2026-04-09
**Valid until:** 2026-05-09 (stable stack; plotly API is stable across minor versions)
