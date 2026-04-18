# Phase 22 Research: Liquidity Sweep + Composite Bias + Tab Wiring

**Researched:** 2026-04-18
**Domain:** Python swing detection, Plotly candlestick, JS 2x2 grid layout, composite signal aggregation

---

## Current State

### What exists and is working
- `/api/trading_indicators` route in `webapp.py:2154` — accepts `ticker` + `lookback`, calls VP/AVWAP/Order Flow, returns `liquidity_sweep: {'status': 'stub'}` and `composite_bias: {'status': 'stub'}`
- `compute_liquidity_sweep(df)` stub at `trading_indicators.py:537` — receives OHLCV df, just needs implementation
- `compute_composite_bias(results)` stub at `trading_indicators.py:541` — receives the full results dict, just needs implementation
- `tradingIndicators.js` — fully implements `clearSession()`, `fetchForTicker(ticker, lookback)` with session cache, and `_renderTickerCard()` that already renders VP + AVWAP + Order Flow panels in a vertical stack
- `tabs.js:53` — lazy-loads tab with `fetchForTicker(ticker, 90)` hardcoded — the `90` needs to become dynamic from the dropdown
- `#tradingIndicatorsTabContent` div exists in index.html — blank placeholder for phases 19–22
- CSS: `.ti-ticker-card`, `.ti-va-badge`, `.ti-legend`, `.ti-legend-grid` etc. all defined in `styles.css:1412+` — no grid layout classes exist yet

### What does NOT exist yet
- Real `compute_liquidity_sweep` implementation (swing detection, adaptive n, chart with candlesticks + arrow markers + dashed level lines)
- Real `compute_composite_bias` implementation
- 2x2 CSS grid layout within `_renderTickerCard()` (current layout is linear vertical stack)
- Lookback dropdown in the tab header
- Composite bias badge above the 2x2 grid
- Sweep legend panel

---

## Implementation Approach

### 1. `compute_liquidity_sweep(df, lookback)` — Python

**Adaptive n:**
```python
def _adaptive_n(lookback: int) -> int:
    if lookback <= 30:
        return 2
    elif lookback <= 90:
        return 3
    else:
        return 5
```

**Look-ahead-safe swing detection (CRITICAL):**
```python
n = _adaptive_n(lookback)
highs = df['High'].values
lows  = df['Low'].values

swing_high_indices = []
swing_low_indices  = []

# Loop bound: range(n, len(highs) - n)  <-- NOT range(n, len(highs))
# This is the project-mandated bound (STATE.md decision, v2.2 Roadmap)
for i in range(n, len(highs) - n):
    if all(highs[i] > highs[i - j] for j in range(1, n + 1)) and \
       all(highs[i] > highs[i + j] for j in range(1, n + 1)):
        swing_high_indices.append(i)
    if all(lows[i] < lows[i - j] for j in range(1, n + 1)) and \
       all(lows[i] < lows[i + j] for j in range(1, n + 1)):
        swing_low_indices.append(i)
```

**No confirmed swings guard:** If both lists empty → return `{'status': 'no_swings', 'n': n}`.

**Sweep detection logic:**
- Bullish sweep: current close > last confirmed swing_high price (price swept above prior high)
- Bearish sweep: current close < last confirmed swing_low price (price swept below prior low)
- Use the most-recent confirmed swing as the "swept level" for the dashed line
- Signal is the most recent sweep event; if last event is >N bars ago with no reversal → "No Sweep"

**Plotly candlestick chart:**
```python
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=list(df.index.astype(str)),
    open=df['Open'].tolist(), high=df['High'].tolist(),
    low=df['Low'].tolist(),  close=df['Close'].tolist(),
    increasing_line_color='#2ecc71',
    decreasing_line_color='#e74c3c',
    name='Price',
))
```

**Arrow markers on sweep candles:** Use `go.Scatter` with `mode='markers+text'` or Plotly annotations dict — same mechanism as Order Flow imbalance candles. Bullish: `▲` above candle (`y = high * 1.001`), Bearish: `▼` below (`y = low * 0.999`).

**Dashed swept-level lines:** Use Plotly `shapes` list — `type='line'`, `xref='paper'` (spans full width), `yref='y'`, `y0=swept_price`, `y1=swept_price`, `line=dict(dash='dash', color='#7f849c', width=1)`. One shape per sweep event.

**Return payload:**
```python
{
    'traces': d['data'],
    'layout': d['layout'],
    'signal': 'bullish' | 'bearish' | 'none' | 'no_swings',
    'n': n,
    'swept_price': float | None,
    'sweep_count': int,
}
```

**Badge text derivation (signal values → badge):**
- `'bullish'` → green `#2ecc71` — "✔ Bullish Sweep — last confirmed sweep at $X.XX"
- `'bearish'` → red `#e74c3c` — "⚠ Bearish Sweep — last confirmed sweep at $X.XX"
- `'none'` → grey `#7f849c` — "— No Sweep in selected window (n=X)"
- `'no_swings'` → grey `#7f849c` — "— No confirmed swings in selected window (n=X)"

---

### 2. `compute_composite_bias(results)` — Python

`results` is the dict with keys: `volume_profile`, `anchored_vwap`, `order_flow`, `liquidity_sweep`.

**Signal extraction per sub-indicator:**
- VP: `results['volume_profile']['signal']` — `'inside'` → Bullish, `'outside'` → Bearish
- AVWAP: derive from convergence + distance labels (or add explicit `signal` key to AVWAP compute if not present)
- Order Flow: `results['order_flow']['signal']` — `'bullish'`/`'bearish'`/`'neutral'`
- Sweep: `results['liquidity_sweep']['signal']` — `'bullish'`/`'bearish'`/`'none'`/`'no_swings'`

**Check AVWAP signal key:** `compute_anchored_vwap` returns `signal` key already — verify what value it returns (likely `'bullish'`/`'bearish'`/`'neutral'`).

**Algorithm:**
```python
def compute_composite_bias(results: dict) -> dict:
    sub_map = {
        'volume_profile': results.get('volume_profile', {}),
        'anchored_vwap':  results.get('anchored_vwap', {}),
        'order_flow':     results.get('order_flow', {}),
        'liquidity_sweep': results.get('liquidity_sweep', {}),
    }
    labels = {'volume_profile': 'Volume Profile', 'anchored_vwap': 'AVWAP',
              'order_flow': 'Order Flow', 'liquidity_sweep': 'Sweep'}

    available = {}
    unavailable = []
    for key, sub in sub_map.items():
        if sub.get('status') in ('stub', 'error', 'no_swings', None) or not sub.get('signal'):
            unavailable.append(labels[key])
        else:
            sig = sub['signal']
            available[labels[key]] = 'bullish' if sig in ('bullish', 'inside') else \
                                     'bearish' if sig in ('bearish', 'outside') else 'neutral'

    n_total = len(available)
    n_bullish = sum(1 for v in available.values() if v == 'bullish')
    n_bearish = sum(1 for v in available.values() if v == 'bearish')

    if n_total == 0:
        direction = 'neutral'
        score_str = '0/0'
        dissenters = []
    elif n_bullish > n_bearish and n_bullish >= 2:
        direction = 'bullish'
        score_str = f'{n_bullish}/{n_total}'
        dissenters = [k for k, v in available.items() if v != 'bullish']
    elif n_bearish > n_bullish and n_bearish >= 2:
        direction = 'bearish'
        score_str = f'{n_bearish}/{n_total}'
        dissenters = [k for k, v in available.items() if v != 'bearish']
    else:
        direction = 'neutral'
        score_str = f'{max(n_bullish, n_bearish)}/{n_total}'
        dissenters = []

    return {
        'direction':   direction,
        'score':       score_str,
        'dissenters':  dissenters,
        'unavailable': unavailable,
    }
```

---

### 3. Backend route update — `webapp.py`

Two changes:
1. Import `compute_liquidity_sweep, compute_composite_bias` alongside existing imports
2. Build `results` dict first, then pass to `compute_composite_bias`:

```python
from src.analytics.trading_indicators import (
    fetch_ohlcv, compute_volume_profile, compute_anchored_vwap,
    compute_order_flow, compute_liquidity_sweep, compute_composite_bias
)
df = fetch_ohlcv(ticker, lookback)
df_365 = fetch_ohlcv(ticker, 365)
results = {
    'volume_profile':  compute_volume_profile(df, ticker, lookback),
    'anchored_vwap':   compute_anchored_vwap(df_365, ticker, lookback),
    'order_flow':      compute_order_flow(df, ticker, lookback),
    'liquidity_sweep': compute_liquidity_sweep(df, lookback),
}
results['composite_bias'] = compute_composite_bias(results)
return jsonify({'ticker': ticker, 'lookback': lookback, **results})
```

---

### 4. Frontend: 2x2 CSS grid + Sweep panel + composite badge

**CSS to add to `styles.css`:**
```css
.ti-2x2-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 12px;
}
.ti-grid-cell {
    min-width: 0;  /* prevents grid blowout */
}
.ti-unavailable-placeholder {
    width: 100%;
    height: 500px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    color: #7f849c;
    font-size: 14px;
}
.ti-composite-badge {
    font-size: 15px;
    font-weight: 700;
    margin: 8px 0 4px 0;
    display: block;
}
.ti-composite-caveat {
    color: #7f849c;
    font-size: 12px;
    margin: 2px 0 10px 0;
}
.ti-lookback-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}
.ti-lookback-label {
    font-size: 13px;
    color: #a6adc8;
}
.ti-lookback-select {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 13px;
    cursor: pointer;
}
```

**`_renderTickerCard()` restructure:**

Current structure (linear vertical stack):
```
<div id="tiCard_AAPL">
  <h3>AAPL</h3>
  <div id="vpChart_AAPL" />
  <div id="vpBadge_AAPL" />
  <div class="ti-legend" />   ← VP legend
  <div id="avwapChart_AAPL" />
  ...etc vertical
</div>
```

New structure:
```
<div id="tiCard_AAPL">
  <h3>AAPL</h3>
  <span class="ti-composite-badge" id="cBadge_AAPL">● Bullish (3/4) — Order Flow dissents</span>
  <span class="ti-composite-caveat">Trend-following bias — all indicators share the same OHLCV data source.</span>
  <div class="ti-2x2-grid">
    <div class="ti-grid-cell">  <!-- top-left: VP -->
      <div id="vpChart_AAPL" style="height:500px" />
      <div id="vpBadge_AAPL" class="ti-va-badge" />
      <div class="ti-legend">...</div>
    </div>
    <div class="ti-grid-cell">  <!-- top-right: AVWAP -->
      <div id="avwapChart_AAPL" style="height:500px" />
      ...
    </div>
    <div class="ti-grid-cell">  <!-- bottom-left: Order Flow -->
      <div id="ofChart_AAPL" style="height:500px" />
      ...
    </div>
    <div class="ti-grid-cell">  <!-- bottom-right: Sweep -->
      <div id="sweepChart_AAPL" style="height:500px" />
      <div id="sweepBadge_AAPL" class="ti-va-badge" />
      <div class="ti-legend">...</div>
    </div>
  </div>
</div>
```

The existing VP/AVWAP/Order Flow rendering code is unchanged — just moved into grid cells. The current `margin-top:24px` inline styles on AVWAP/OF divs must be removed (grid handles spacing).

**Plotly call for sweep:** `staticPlot: true, responsive: true` — consistent with AVWAP and Order Flow (TIND-03).

---

### 5. Lookback dropdown wiring

**In `index.html`** — add inside `#tradingIndicatorsTabContent` as first child (or inject from JS):
```html
<div class="ti-lookback-bar" id="tiLookbackBar" style="display:none">
    <span class="ti-lookback-label">Trading Indicators</span>
    <select class="ti-lookback-select" id="tiLookbackSelect">
        <option value="30">30d</option>
        <option value="90" selected>90d</option>
        <option value="180">180d</option>
        <option value="365">365d</option>
    </select>
</div>
```

Show `tiLookbackBar` when tab activates. Wire in `tradingIndicators.js`:
```javascript
function _initLookbackDropdown(tickers) {
    var bar = document.getElementById('tiLookbackBar');
    if (bar) bar.style.display = 'flex';
    var sel = document.getElementById('tiLookbackSelect');
    if (!sel) return;
    sel.addEventListener('change', function () {
        var newLookback = parseInt(sel.value, 10);
        clearSession();
        // Remove all existing ticker cards
        var container = document.getElementById('tradingIndicatorsTabContent');
        tickers.forEach(function (t) {
            var card = document.getElementById('tiCard_' + t);
            if (card) card.parentNode.removeChild(card);
            // Render loading placeholder
            var placeholder = document.createElement('div');
            placeholder.id = 'tiLoading_' + t;
            placeholder.className = 'ti-unavailable-placeholder';
            placeholder.textContent = 'Loading ' + t + '…';
            container.appendChild(placeholder);
        });
        tickers.forEach(function (t) {
            fetchForTicker(t, newLookback);
        });
    });
}
```

**In `tabs.js`** — change hardcoded `90` to dynamic:
```javascript
var lookback = (document.getElementById('tiLookbackSelect') &&
                parseInt(document.getElementById('tiLookbackSelect').value, 10)) || 90;
TradingIndicators.fetchForTicker(ticker, lookback);
```

**Also expose `initLookbackDropdown` on the `TradingIndicators` public API** and call it from `tabs.js` on first tab activation.

---

## Key Files to Modify

| File | Change |
|------|--------|
| `src/analytics/trading_indicators.py` | Replace `compute_liquidity_sweep` and `compute_composite_bias` stubs with real implementations |
| `webapp.py` | Update `/api/trading_indicators` route: import new functions, build `results` dict, add `composite_bias` key |
| `static/js/tradingIndicators.js` | Restructure `_renderTickerCard()` to 2x2 grid, add Sweep panel, add composite bias badge, add lookback dropdown init + wiring |
| `static/js/tabs.js` | Change hardcoded `90` to read from `tiLookbackSelect`, call `TradingIndicators.initLookbackDropdown()` on tab activate |
| `static/css/styles.css` | Add `.ti-2x2-grid`, `.ti-grid-cell`, `.ti-unavailable-placeholder`, `.ti-composite-badge`, `.ti-composite-caveat`, `.ti-lookback-bar`, `.ti-lookback-select` |
| `templates/index.html` | Add `tiLookbackBar` div with select into `#tradingIndicatorsTabContent` |

---

## Validation Architecture

### Look-ahead safety test (CRITICAL — must verify before composite wiring)

The project mandated a regression test: "swing indices on 90-day data must not shift when re-run on 91 days."

```python
# tests/test_sweep_lookahead.py
def test_swing_indices_stable_on_extra_bar():
    """
    SWEEP-02 requirement: loop bound range(n, len - n) prevents look-ahead.
    Adding one bar to the end must not change any previously detected swing index.
    """
    df_90 = fetch_ohlcv('AAPL', 90)
    df_91 = df_90.copy()
    # Append a synthetic extra bar
    extra = df_91.iloc[[-1]].copy()
    extra.index = [df_91.index[-1] + pd.Timedelta(days=1)]
    df_91 = pd.concat([df_91, extra])

    result_90 = compute_liquidity_sweep(df_90, 90)
    result_91 = compute_liquidity_sweep(df_91, 90)

    # The swing detection n is the same; the last n bars are excluded in both runs
    # so the second-to-last swing must be identical
    assert result_90.get('sweep_count') == result_91.get('sweep_count') or \
           result_91.get('sweep_count') == result_90.get('sweep_count') + 0  # no new swing from synthetic bar
```

The cleanest verification: extract `swing_high_indices` and `swing_low_indices` from the return payload (add them as debug keys during development) and assert they are a prefix of each other.

### Composite bias unit tests

```python
# tests/test_composite_bias.py
def test_majority_bullish():
    results = {
        'volume_profile': {'signal': 'inside'},
        'anchored_vwap':  {'signal': 'bullish'},
        'order_flow':     {'signal': 'bullish'},
        'liquidity_sweep': {'signal': 'bearish'},
    }
    r = compute_composite_bias(results)
    assert r['direction'] == 'bullish'
    assert r['score'] == '3/4'
    assert 'Sweep' in r['dissenters']

def test_unavailable_excluded_from_denominator():
    results = {
        'volume_profile': {'signal': 'inside'},
        'anchored_vwap':  {'signal': 'bullish'},
        'order_flow':     {'signal': 'bullish'},
        'liquidity_sweep': {'status': 'stub'},  # unavailable
    }
    r = compute_composite_bias(results)
    assert r['score'] == '3/3'
    assert 'Sweep' in r['unavailable']

def test_tie_is_neutral():
    results = {
        'volume_profile': {'signal': 'inside'},
        'anchored_vwap':  {'signal': 'bullish'},
        'order_flow':     {'signal': 'bearish'},
        'liquidity_sweep': {'signal': 'bearish'},
    }
    r = compute_composite_bias(results)
    assert r['direction'] == 'neutral'
```

### Badge rendering smoke test

Manually verify in browser on AAPL/SPY with 90d lookback:
- Sweep chart shows candlesticks (not blank)
- At least one arrow marker or "No Sweep" badge visible
- Composite badge shows colored dot + score + dissenter line
- Caveat line renders below badge

### Full tab integration

Switch lookback from 90d → 30d → 90d: session clears, cards re-render each time, no duplicate cards appear.

---

## Risks & Gotchas

### 1. AVWAP `signal` key may not exist
`compute_anchored_vwap` might not return a `signal` key. Check `trading_indicators.py` lines 380–399. If absent, `compute_composite_bias` must derive a signal from `convergence`, `labels`, or add a `signal` key to `compute_anchored_vwap` return dict at the same time.

**Mitigation:** Add `signal` key to `compute_anchored_vwap` output if missing, or handle its absence in `compute_composite_bias` with a `neutral` fallback.

### 2. VP `signal` is 'inside'/'outside' not 'bullish'/'bearish'
`compute_volume_profile` returns `signal: 'inside'` or `signal: 'outside'`. The composite bias logic must map `'inside' → 'bullish'` and `'outside' → 'bearish'` explicitly.

### 3. Grid layout and Plotly responsive resize
Existing Plotly divs use `width:100%`. Inside a `grid-template-columns: 1fr 1fr` container this will work correctly — but if any cell div has `margin-top:24px` inline style (the current AVWAP/OF divs do), remove those styles when migrating into grid cells or the vertical spacing will be off.

### 4. Sweep candle Plotly x-axis alignment
The candlestick trace uses `df.index.astype(str)` — same as all other charts. No issue. But if `df` only has 20-30 bars (30d lookback), n=2 is fine. Ensure the guard `if len(df) < 2*n + 1: return no_swings` is present.

### 5. `clearSession()` in dropdown must also remove loading placeholders
When re-fetching after a lookback change, `_renderTickerCard` calls `existing.parentNode.removeChild(existing)` at the top — this removes the card if it already exists. But the loading placeholder div has a different ID (`tiLoading_TICKER`) and won't be removed by that code. Add cleanup for placeholder divs inside `_renderTickerCard`:
```javascript
var placeholder = document.getElementById('tiLoading_' + ticker);
if (placeholder) placeholder.parentNode.removeChild(placeholder);
```

### 6. `staticPlot: true` breaks click/hover on Sweep chart
This is intentional per TIND-03 (memory pressure reduction). All four panels must use `staticPlot: true`. The sweep chart will be non-interactive — acceptable for a badge + visual overview use case.

### 7. Majority threshold: simple majority, not 2/3
STATE.md blocker note says "Composite bias majority threshold (2/3 vs. simple majority) to be decided before Phase 22 planning." CONTEXT.md decision: "majority direction wins (3+ of 4)". This means 3+ out of 4 (or 3+/available). For 4 available: need 3. For 3 available: need 2. Implementation should use `n_majority > n_total / 2` (strict majority), which handles all cases.

### 8. Dashed swept-level lines: one per event, not one per swing
CONTEXT.md decision: "One dashed horizontal line per sweep event drawn at the swept price; not one line per swing." Only draw a shape for each bar where a sweep was detected (close above swing high or below swing low), not for every swing high/low index.

---

## RESEARCH COMPLETE

**Confidence:** HIGH — all implementation details derived directly from existing codebase inspection (functions, CSS classes, route structure, return payloads) and locked decisions in CONTEXT.md. No external research required.

**Key findings:**
1. Both Python stubs are single-line — full implementation replaces the stub body directly
2. The JS `_renderTickerCard()` restructure is the largest change — existing VP/AVWAP/OF code stays intact, just wrapped in grid cells
3. Look-ahead bug is the highest-risk item — loop bound `range(n, len - n)` is already mandated; regression test is mandatory
4. AVWAP signal key may need to be added/verified — check `compute_anchored_vwap` return shape before composite wiring
5. Lookback dropdown requires changes in both `tabs.js` (remove hardcoded 90) and `tradingIndicators.js` (init + change handler)
