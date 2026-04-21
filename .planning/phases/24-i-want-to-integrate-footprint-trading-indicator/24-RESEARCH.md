# Phase 24: Integrate Footprint Trading Indicator - Research

**Researched:** 2026-04-21
**Domain:** Plotly heatmap, yfinance intraday fetch, Flask route, JS parallel fetch, composite bias extension
**Confidence:** HIGH — all findings verified against live project source code; no external library research required

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Data approximation**
- Intraday source: yfinance 15-minute bars, up to 60 days of history
- Buy/sell split per bar: `buy_volume = (Close - Low) / (High - Low + 1e-10) * Volume`; `sell_volume = Volume - buy_volume`
- Delta per bar: `buy_volume - sell_volume`
- Aggregation: 15m buy/sell/delta aggregated into per-(day, price-bin) cells for the heatmap; daily deltas summed into a cumulative delta series
- Lookback handling: Footprint panel is ALWAYS capped at 60 days regardless of the tab-level lookback dropdown; displays note `"Footprint limited to 60d — 15m data horizon"`

**Visual style**
- Chart type: Plotly `go.Heatmap` trace
- Price bins: Adaptive bin count targeting ~0.2% bin width of the 60d price range (same as Phase 19 VP)
- Color: Diverging palette — strong green for positive delta (`#2ecc71`), deep red for negative delta (`#e74c3c`), near-background (`#1e1e2e` / `#7f849c`) for ~zero
- Overlays: dashed horizontal line at current close price; small dot/triangle markers at per-day POC (price bin with max total volume)
- Hover: each cell tooltip shows `buy`, `sell`, `delta`, and bin price range
- Panel height: 500px

**Tab integration**
- Grid expansion: `ti-2x2-grid` from `1fr 1fr` to `1fr 1fr 1fr` (3×2)
- Row 1: Volume Profile, Anchored VWAP, Order Flow
- Row 2: Liquidity Sweep, Footprint, (empty placeholder)
- New Flask route: `GET /api/footprint?ticker=X&days=60` (separate from `/api/trading_indicators`)
- JS fetches `/api/footprint` in parallel with `/api/trading_indicators`; session cache keyed by `ticker + '-footprint'`
- `TradingIndicators.clearSession()` must also clear footprint cache entries
- Failure mode: grey placeholder cell with message `"Footprint unavailable — intraday data not available for this ticker"`

**Signals and composite bias**
- Primary signal: sign of `cum_delta = sum(daily_delta)` over 60d window
- Neutral threshold: `|cum_delta| < 0.05 * total_60d_volume`
- Footprint is the 5th voice in `compute_composite_bias`; denominator becomes 5 (or 4 if footprint unavailable)
- Dissenter identification extended to consider footprint
- Badge formats (below heatmap):
  - Bullish: `✔ Bullish Footprint — Cum Δ: +2.4M shares (60d)` (green `#2ecc71`)
  - Bearish: `⚠ Bearish Footprint — Cum Δ: −1.1M shares (60d)` (red `#e74c3c`)
  - Neutral: `— Neutral Footprint — Cum Δ: +12K shares (60d)` (grey `#7f849c`)
  - Unavailable: `— Footprint unavailable` (grey `#7f849c`)

**Tests (per CLAUDE.md)**
- `tests/test_unit_footprint.py` — unit tests for `fetch_intraday`, `compute_footprint`
- `tests/test_integration_routes.py` — integration test for `/api/footprint`
- `tests/test_regression_indicators.py` — regression test pinning cumulative-delta value for a frozen 15m fixture
- Extend existing composite-bias tests to cover 5-voice scenarios

### Claude's Discretion
- Exact Plotly colorscale stops (midpoint color, gradient spacing)
- Exact POC marker shape (dot vs triangle vs star) and size
- Current-price-line dash pattern, color, and width
- Exact CSS class names for the 3-column grid wrapper and empty placeholder cell
- Loading spinner style during intraday fetch
- Cache TTL and exact key format
- Hover tooltip HTML formatting and number formatting
- Badge font size and exact icon glyphs
- Requirements ID prefix suggested as FOOT-01...FOOT-05

### Deferred Ideas (OUT OF SCOPE)
- Secondary footprint signals (stacked imbalance, delta divergence, POC migration direction)
- Alternate visual styles (numeric-cell annotations, split-color stacked bars, per-candle VP overlays)
- True tick-level / L2 footprint data (requires paid feeds)
- Footprint-specific lookback selector
- Weighted-voice composite bias (0.5 weighting for footprint)
- 6th cell populated with a summary card
</user_constraints>

---

## Summary

Phase 24 adds a Footprint indicator as the 5th panel in the Trading Indicators tab. The core work is: (1) a new `fetch_intraday()` backend function using yfinance 15m bars, (2) a `compute_footprint()` function that aggregates buy/sell/delta into a per-(day, price-bin) matrix and renders a Plotly heatmap, (3) a new `GET /api/footprint` Flask route that is fetched in parallel with `/api/trading_indicators`, (4) grid expansion from 2×2 to 3×2 in both CSS and JS, and (5) extension of `compute_composite_bias()` to handle a 5th voice.

All building blocks already exist in the project. `fetch_intraday()` mirrors `fetch_ohlcv()` but passes `interval='15m'`. The buy/sell formula is verbatim from `compute_order_flow()`. Bin logic is verbatim from `compute_volume_profile()`. The JS session cache, parallel fetch, and `clearSession()` patterns are already established by `peerComparison.js` and the existing `TradingIndicators` module. The only genuinely new Plotly surface is `go.Heatmap` — the rest is composition of existing patterns.

The key risk is yfinance 15m data availability: rate limits, non-US tickers, and weekends/holidays can return empty data. The unavailable-panel fallback pattern (grey placeholder + message) from Phase 22 Sweep already handles this case.

**Primary recommendation:** Implement in 4 logical tasks: (1) backend `fetch_intraday` + `compute_footprint` + `/api/footprint` route, (2) `compute_composite_bias` 5-voice extension, (3) JS grid expansion + parallel fetch wiring + badge rendering, (4) tests (unit + integration + regression + composite-bias).

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yfinance | installed (project-wide) | 15m intraday OHLCV fetch | Already used for all indicator data; `yf.Ticker().history(interval='15m')` is the established call pattern |
| plotly | installed (project-wide) | `go.Heatmap` trace rendering | All Trading Indicator charts use Plotly; same dark-theme config across all panels |
| numpy | installed | Per-bar delta calc, bin aggregation | Already used in `compute_volume_profile` and `compute_order_flow` |
| pandas | installed | DataFrame manipulation for 15m → daily aggregation | Already used throughout |
| Flask | installed | `GET /api/footprint` route | Project web framework |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest / unittest.mock | installed | Test suite | All new features require tests per CLAUDE.md |

**Installation:** No new packages required — all dependencies are already installed.

---

## Architecture Patterns

### Recommended Project Structure

```
src/analytics/trading_indicators.py   # add fetch_intraday() + compute_footprint()
                                       # extend compute_composite_bias() to 5 voices
webapp.py                              # add GET /api/footprint route
static/js/tradingIndicators.js         # expand grid, add parallel fetch, add footprint cell
static/css/styles.css                  # update .ti-2x2-grid to 3-column
tests/test_unit_footprint.py           # new: unit tests
tests/test_integration_routes.py       # extend: /api/footprint route tests
tests/test_regression_indicators.py    # extend: cumulative delta pinned regression
tests/fixtures/footprint_15m_ohlcv.csv # new: frozen 15m fixture for regression
```

### Pattern 1: fetch_intraday() — mirrors fetch_ohlcv()

**What:** yfinance 15m history fetch with tz-localize strip, 40% buffer, and empty guard.
**When to use:** Called only from `compute_footprint()` and the `/api/footprint` route. Never called from the main `fetch_ohlcv` path.

```python
# Mirrors fetch_ohlcv() at trading_indicators.py:16 but adds interval='15m'
def fetch_intraday(ticker: str, days: int = 60) -> pd.DataFrame:
    end = datetime.now()
    start = end - timedelta(days=int(days * 1.4))
    df = yf.Ticker(ticker).history(
        start=start.strftime('%Y-%m-%d'),
        end=end.strftime('%Y-%m-%d'),
        interval='15m',
        auto_adjust=True,
    )
    if df.empty:
        raise ValueError(f"No 15m intraday data returned for {ticker}")
    df.index = df.index.tz_localize(None) if df.index.tz is not None else df.index
    return df[['Open', 'High', 'Low', 'Close', 'Volume']]
```

**Verified against:** `fetch_ohlcv` source at `trading_indicators.py:16-37`.

### Pattern 2: compute_footprint() — delta aggregation + Heatmap

**What:** Applies Close-Low proxy to 15m bars, groups by (date, price-bin) to build a 2D delta matrix, renders as `go.Heatmap` with diverging colorscale.
**When to use:** Called from the `/api/footprint` route.

Key sub-steps:
1. Compute per-15m-bar buy/sell/delta using the epsilon-guarded formula from `compute_order_flow`.
2. Assign each 15m bar to a price bin using the `compute_volume_profile` adaptive-bin logic (targeting ~0.2% bin width of 60d range).
3. Group by `(date, bin_idx)` → sum delta per cell.
4. Build 2D matrix: X = unique dates, Y = bin price centers.
5. Render `go.Heatmap` with `colorscale` anchored at zero.
6. Add overlays: current-close horizontal line (shape), per-day POC markers (scatter).
7. Return `{traces, layout, signal, cum_delta, total_volume}`.

```python
# Adaptive bin logic — reuse verbatim from compute_volume_profile:
# mid_price = (price_min + price_max) / 2.0
# n_bins = max(20, min(200, int(price_range / (mid_price * 0.002))))

# Delta formula — reuse verbatim from compute_order_flow:
# ranges = (df['High'] - df['Low']).clip(lower=1e-10)
# buy_volume = (df['Close'] - df['Low']) / ranges * df['Volume']
# sell_volume = df['Volume'] - buy_volume
# delta = buy_volume - sell_volume
```

### Pattern 3: /api/footprint route — mirrors /api/trading_indicators

**What:** GET route that calls `fetch_intraday` + `compute_footprint`, catches exceptions, returns JSON.
**When to use:** Called exclusively from the footprint panel fetch in `tradingIndicators.js`.

```python
# Source: webapp.py:2154 (trading_indicators route pattern)
@app.route('/api/footprint', methods=['GET'])
def get_footprint():
    ticker = request.args.get('ticker', '').strip().upper()
    days = int(request.args.get('days', 60))
    if not ticker:
        return jsonify({'error': 'ticker parameter required'})
    try:
        from src.analytics.trading_indicators import fetch_intraday, compute_footprint
        df_15m = fetch_intraday(ticker, days)
        result = compute_footprint(df_15m, ticker)
        return jsonify({'ticker': ticker, 'days': days, **result})
    except Exception as e:
        logger.error(f"Error in get_footprint for {ticker}: {e}")
        return jsonify({'error': str(e)}), 500
```

### Pattern 4: compute_composite_bias() 5-voice extension

**What:** Add `footprint` as a 5th key to `sub_map` and `labels` dicts in the existing function. The denominator logic is already correct — it counts only `available` (non-error) sub-indicators.
**When to use:** Called from `get_trading_indicators()` only — not from `get_footprint()`.

The existing `compute_composite_bias` receives the full `results` dict from `/api/trading_indicators`. Footprint lives in a separate fetch; its signal must be passed in separately. Two design options:

- **Option A (recommended):** The `/api/trading_indicators` route does NOT call `/api/footprint`. Instead, `compute_composite_bias` accepts an optional `footprint_result` kwarg and merges it with the other 4 sub-indicators. The JS waits for both fetches to complete, then re-renders the composite badge client-side (or makes a third `/api/composite` call).
- **Option B:** `/api/trading_indicators` internally calls `fetch_intraday` + `compute_footprint` and bundles footprint in its own response. This simplifies JS but couples the slow intraday fetch to the main route.

**CONTEXT.md decision:** "Frontend fetch: JS calls `/api/footprint` in parallel with `/api/trading_indicators` per ticker." This rules out Option B. The composite badge must be computed after both fetches complete.

**Recommended implementation:** Compute composite bias client-side in JS after both responses arrive, OR add a lightweight server-side helper that accepts pre-computed sub-signals as query params. The cleanest approach given the existing architecture: extend `compute_composite_bias` to accept a pre-computed footprint sub-signal and call it inside the `/api/trading_indicators` route with `footprint_signal=None` (so it computes 4/4 or 4-voice result), then update the badge in JS after `/api/footprint` returns using a client-side re-compute of the composite.

**Simpler and safer option:** Expose a new `POST /api/composite_bias` route that accepts all 5 sub-signals as a JSON body, or pass footprint signal back to `/api/trading_indicators` via a second request. Given the complexity, the planner should decide: the most surgical approach is to call `/api/footprint` in parallel and update the composite badge client-side using the JS logic already present in `tradingIndicators.js` (the badge-rendering code is straightforward enough to duplicate or abstract).

### Pattern 5: JS parallel fetch + grid expansion

**What:** Mirror the existing `fetchForTicker` structure. Add a second fetch to `/api/footprint` that runs concurrently via `Promise.all`. Expand `.ti-2x2-grid` CSS class to `grid-template-columns: 1fr 1fr 1fr`.

```javascript
// Current grid HTML class (tradingIndicators.js:84)
// '<div class="ti-2x2-grid">' → becomes '<div class="ti-3x2-grid">'
// or update the existing CSS: .ti-2x2-grid { grid-template-columns: 1fr 1fr 1fr; }

// Parallel fetch pattern (mirrors peerComparison.js lazy-load):
Promise.all([
    fetch('/api/trading_indicators?ticker=...&lookback=...').then(r => r.json()),
    fetch('/api/footprint?ticker=...&days=60').then(r => r.json()),
]).then(function([resp, fpResp]) {
    _renderTickerCard(container, ticker, lookback, resp, fpResp);
});
```

### Anti-Patterns to Avoid

- **Blocking the main `/api/trading_indicators` route with the 15m fetch.** The 15m intraday fetch is slower than daily OHLCV; bundling it in the main route would increase P50 latency for all 4 existing panels.
- **Using `yf.download()` for 15m data.** Project decision (Phase 09-01): always use `yf.Ticker().history()` to avoid concurrent 2D/1D shape corruption.
- **Zero-range bar divide-by-zero.** The epsilon guard `clip(lower=1e-10)` is mandatory — copy verbatim from `compute_order_flow`.
- **Re-using `.ti-2x2-grid` CSS class name without renaming.** The class name `ti-2x2-grid` implies a 2-column layout. Rename to `ti-indicator-grid` or update the comment — but keep CSS change minimal (just update `grid-template-columns`).
- **Dropping `no_swings` / `none` signals from composite bias `_to_direction` map.** These are already excluded by the `raw_signal not in _to_direction` guard. Footprint's `neutral` signal IS in the map, so it will be counted as neutral (not excluded). This is correct behaviour.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Adaptive price bins | Custom binning logic | Reuse `compute_volume_profile` bin logic verbatim | Already handles zero-range, min/max n_bins, and the 0.2% convention |
| Buy/sell volume proxy | Another formula | Reuse `compute_order_flow` epsilon-guarded ratio | Ensures consistency between Order Flow and Footprint panels (same formula, different bar granularity) |
| yfinance 15m fetch | Custom session/retry wrapper | Mirror `fetch_ohlcv()` pattern directly | Project has established the `yf.Ticker().history()` pattern; no retry logic needed for showcase context |
| Dark-theme Plotly config | New theme constants | Reuse `PAPER_BG`, `PLOT_BG`, `FONT_CLR` constants already defined in `trading_indicators.py` | Ensures visual consistency across all 5 panels |
| Unavailable placeholder | New CSS class | Reuse `.ti-unavailable-placeholder` already in `styles.css:1494` | Exact same visual treatment as Sweep panel's unavailable state |
| Badge color convention | New color variables | Use `#2ecc71` / `#e74c3c` / `#7f849c` already used in every other badge | Consistency with existing VP, AVWAP, Order Flow, Sweep badges |

---

## Common Pitfalls

### Pitfall 1: yfinance 15m data returns tz-aware index
**What goes wrong:** `df.index.tz` is not None for intraday bars (yfinance returns UTC-aware timestamps for 15m data). Grouping by date before stripping timezone produces wrong date keys.
**Why it happens:** yfinance 15m returns `DatetimeTZDtype` index; daily history may not.
**How to avoid:** Strip timezone BEFORE grouping by date: `df.index = df.index.tz_localize(None) if df.index.tz is not None else df.index`. Consistent with `fetch_ohlcv` line 36.
**Warning signs:** `KeyError` on date-string group keys, or date groupings that span midnight UTC instead of local trading hours.

### Pitfall 2: yfinance 15m history horizon is strictly ~59 calendar days
**What goes wrong:** Requesting 60 calendar days of 15m data with a 40% buffer (84 days) may be accepted by the API but silently truncated to ~59 days.
**Why it happens:** yfinance hard-limits 15m data to approximately 60 calendar days regardless of the `start` parameter.
**How to avoid:** Use `days=60` as the hard maximum; add the standard 40% buffer but accept that actual bars may only cover ~45–59 trading days. The unavailable-panel fallback handles empty returns.
**Warning signs:** `fetch_intraday` returning fewer than expected bars (< 60 * 0.7 * 6.5 ≈ 273 bars for a US ticker).

### Pitfall 3: Empty price-bin matrix for tickers with no intraday data
**What goes wrong:** Non-US tickers, ETFs with restricted history, or newly listed stocks may return empty DataFrames from yfinance 15m.
**Why it happens:** yfinance 15m only covers US equities reliably.
**How to avoid:** Wrap `fetch_intraday` in try/except in the route; return `{'error': '...', 'signal': None}` so JS renders the grey placeholder. Consistent with Phase 22 Sweep failure mode.
**Warning signs:** Empty DataFrame passed to `compute_footprint` causing a ZeroDivisionError in the bin-width calculation.

### Pitfall 4: Composite bias badge rendered before footprint fetch completes
**What goes wrong:** The composite badge shows 4/4 (or 3/4) initially, then should update to 4/5 or 5/5 after the parallel footprint fetch returns. If not handled, the badge stays at the 4-voice reading.
**Why it happens:** The `/api/trading_indicators` route computes composite bias without footprint (since footprint is a separate route). The badge is rendered in `_renderTickerCard` immediately when the main response arrives.
**How to avoid:** Either (a) compute composite bias client-side in JS after both Promise.all responses resolve, updating the badge once, or (b) have the server accept all 5 sub-signals in a single endpoint. Option (a) is preferred (no extra route, aligns with locked decisions).
**Warning signs:** Composite badge shows "4/4" permanently even when footprint is available.

### Pitfall 5: CSS class name mismatch after grid expansion
**What goes wrong:** `tradingIndicators.js` hardcodes `'<div class="ti-2x2-grid">'` in the `_renderTickerCard` string. If CSS is updated but JS still emits the old class name, grid remains 2-column.
**Why it happens:** The class name and the CSS definition are coupled but in different files.
**How to avoid:** When updating `grid-template-columns` in `styles.css`, also update the class name emission in `tradingIndicators.js` (or keep the same class name and just change the CSS rule — simplest option).
**Warning signs:** Footprint cell wrapping to a 3rd row instead of appearing in row 2 position 2.

---

## Code Examples

### Heatmap trace structure (Plotly go.Heatmap)

```python
# Source: Plotly official docs pattern; consistent with existing fig.to_dict() serialize path
import plotly.graph_objects as go

# z[i][j] = delta value for date i, price_bin j
fig = go.Figure(go.Heatmap(
    z=delta_matrix,          # 2D list: shape (n_days, n_bins)
    x=date_strings,          # list of 'YYYY-MM-DD' strings
    y=bin_centers,           # list of float price values
    colorscale=[
        [0.0, '#e74c3c'],    # max negative delta (sell-dominant)
        [0.5, '#1e1e2e'],    # zero delta (background color)
        [1.0, '#2ecc71'],    # max positive delta (buy-dominant)
    ],
    zmid=0,                  # center the diverging scale at zero
    hovertemplate=(
        'Date: %{x}<br>'
        'Price Bin: %{y:.2f}<br>'
        'Delta: %{z:,.0f}<extra></extra>'
    ),
    showscale=True,
    colorbar=dict(
        thickness=12,
        tickfont=dict(color='#cdd6f4', size=10),
        outlinecolor='rgba(0,0,0,0)',
    ),
))
fig.update_layout(
    paper_bgcolor='#1e1e2e',
    plot_bgcolor='#1e1e2e',
    font=dict(color='#cdd6f4'),
    title=f'Footprint Delta Heatmap — {ticker}',
    xaxis=dict(title='Date', gridcolor='#313244'),
    yaxis=dict(title='Price ($)', gridcolor='#313244'),
    margin=dict(l=40, r=40, t=50, b=30),
    height=500,
)
```

### Per-day delta aggregation into 2D matrix

```python
# Group 15m bars by date and bin index
import numpy as np

df_15m['date'] = df_15m.index.date
df_15m['bin_idx'] = np.digitize(df_15m['Close'], bin_edges) - 1
df_15m['bin_idx'] = df_15m['bin_idx'].clip(0, n_bins - 1)

# Group-sum delta per (date, bin_idx)
grouped = df_15m.groupby(['date', 'bin_idx'])['delta'].sum().reset_index()

# Pivot to 2D matrix
unique_dates = sorted(df_15m['date'].unique())
delta_matrix = np.zeros((len(unique_dates), n_bins))
date_to_idx = {d: i for i, d in enumerate(unique_dates)}
for _, row in grouped.iterrows():
    di = date_to_idx[row['date']]
    delta_matrix[di, int(row['bin_idx'])] = row['delta']
```

### POC overlay per day (scatter trace)

```python
# Per-day POC: price bin with max total volume for that day
# Using buy_volume + sell_volume (total volume per cell)
poc_markers = []
for di, d in enumerate(unique_dates):
    day_mask = df_15m['date'] == d
    day_df = df_15m[day_mask].copy()
    if day_df.empty:
        continue
    day_df['buy_vol'] = (day_df['Close'] - day_df['Low']) / (day_df['High'] - day_df['Low']).clip(lower=1e-10) * day_df['Volume']
    by_bin = day_df.groupby('bin_idx')['Volume'].sum()
    poc_bin = int(by_bin.idxmax())
    poc_markers.append({'x': str(d), 'y': float(bin_centers[poc_bin])})

fig.add_trace(go.Scatter(
    x=[m['x'] for m in poc_markers],
    y=[m['y'] for m in poc_markers],
    mode='markers',
    marker=dict(symbol='circle', size=6, color='#f9e2af', opacity=0.85),
    name='Daily POC',
    hovertemplate='POC: %{y:.2f}<extra></extra>',
))
```

### JS parallel fetch pattern (from peerComparison.js cache model)

```javascript
// Extend fetchForTicker to use Promise.all (mirrors peerComparison.js:168 pattern)
function fetchForTicker(ticker, lookback) {
    var cacheKey = ticker + '-' + lookback;
    var fpCacheKey = ticker + '-footprint';
    if (_sessionCache[cacheKey]) return;
    _sessionCache[cacheKey] = true;
    _sessionCache[fpCacheKey] = true;

    var container = document.getElementById('tradingIndicatorsTabContent');
    if (!container) return;

    Promise.all([
        fetch('/api/trading_indicators?ticker=' + encodeURIComponent(ticker)
              + '&lookback=' + encodeURIComponent(lookback)).then(function(r) { return r.json(); }),
        fetch('/api/footprint?ticker=' + encodeURIComponent(ticker)
              + '&days=60').then(function(r) { return r.json(); }),
    ]).then(function(results) {
        var resp   = results[0];
        var fpResp = results[1];
        if (resp.error) { console.warn('[TradingIndicators] API error:', resp.error); return; }
        _renderTickerCard(container, ticker, lookback, resp, fpResp);
    }).catch(function(err) {
        console.error('[TradingIndicators] fetch failed:', err);
    });
}
```

### clearSession() extension

```javascript
// Extend to also purge footprint cache keys (adds 3 lines to existing function)
function clearSession() {
    Object.keys(_sessionCache).forEach(function (k) { delete _sessionCache[k]; });
    // Note: footprint keys (ticker + '-footprint') are already in _sessionCache
    // so the forEach above clears them automatically — no extra code needed
    // IF footprint keys share the same _sessionCache object.
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `yf.download()` | `yf.Ticker().history()` | Phase 09-01 | Prevents 2D/1D shape corruption in concurrent calls |
| 2×2 grid (`1fr 1fr`) | 3×2 grid (`1fr 1fr 1fr`) | Phase 24 | Adds 2 new cells (footprint + empty placeholder) |
| 4-voice composite bias | 5-voice composite bias | Phase 24 | Denominator changes from 4 to 5 (or 4 if footprint unavailable) |

---

## Open Questions

1. **Composite bias update timing**
   - What we know: `/api/footprint` is a separate parallel fetch; `/api/trading_indicators` computes composite with 4 voices.
   - What's unclear: Should the composite badge show 4/4 briefly, then update to 4/5 or 5/5 when footprint resolves? Or should JS wait for both before rendering the badge at all?
   - Recommendation: Render the entire card (including badge) only after `Promise.all` resolves with both responses. This avoids the flash of a stale 4-voice badge. The `Promise.all` pattern already waits for both; pass both responses to `_renderTickerCard`.

2. **`compute_composite_bias` signature change**
   - What we know: Current signature is `compute_composite_bias(results: dict)` where `results` has keys `volume_profile`, `anchored_vwap`, `order_flow`, `liquidity_sweep`. Footprint comes from a different route.
   - What's unclear: How does the server-side call in `get_trading_indicators` include footprint without calling `fetch_intraday`?
   - Recommendation: The server-side `compute_composite_bias` call in `get_trading_indicators` continues to compute a 4-voice result (footprint = None/unavailable). The JS then re-computes or overwrites the composite badge using client-side logic after both fetches complete. This keeps the route boundary clean.

3. **Fixture generation for 15m regression test**
   - What we know: `tests/fixtures/` has CSVs for daily OHLCV; `test_regression_indicators.py` uses `scripts/generate_fixtures.py`.
   - What's unclear: Does `scripts/generate_fixtures.py` exist and does it support 15m interval?
   - Recommendation: Create a `tests/fixtures/footprint_15m_ohlcv.csv` fixture using a one-time live fetch during Wave 0, pin the expected cumulative delta value, and reference it in `test_regression_indicators.py`.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (project-wide) |
| Config file | `pytest.ini` or `pyproject.toml` (check root) |
| Quick run command | `pytest tests/test_unit_footprint.py -x -q` |
| Full suite command | `pytest -x -q` |

### Phase Requirements → Test Map

| ID | Behavior | Test Type | Automated Command | File Exists? |
|----|----------|-----------|-------------------|-------------|
| FOOT-01 | `fetch_intraday` returns 15m OHLCV DataFrame with tz-naive index | unit | `pytest tests/test_unit_footprint.py::test_fetch_intraday_returns_ohlcv -x` | Wave 0 |
| FOOT-01 | `compute_footprint` happy-path returns required keys | unit | `pytest tests/test_unit_footprint.py::test_compute_footprint_keys -x` | Wave 0 |
| FOOT-01 | `compute_footprint` empty-DataFrame edge case renders placeholder | unit | `pytest tests/test_unit_footprint.py::test_compute_footprint_empty -x` | Wave 0 |
| FOOT-01 | Cumulative delta pinned regression on frozen 15m fixture | regression | `pytest tests/test_regression_indicators.py -k footprint -x` | Wave 0 |
| FOOT-02 | Heatmap trace present in compute_footprint output | unit | `pytest tests/test_unit_footprint.py::test_heatmap_trace_present -x` | Wave 0 |
| FOOT-03 | Signal is bullish/bearish/neutral based on cum_delta threshold | unit | `pytest tests/test_unit_footprint.py::test_signal_logic -x` | Wave 0 |
| FOOT-04 | GET /api/footprint returns 200 with correct schema | integration | `pytest tests/test_integration_routes.py -k footprint -x` | Wave 0 |
| FOOT-04 | GET /api/footprint returns error for invalid ticker | integration | `pytest tests/test_integration_routes.py -k footprint_invalid -x` | Wave 0 |
| FOOT-05 | compute_composite_bias with 5 working voices returns 5/5 | unit | `pytest tests/test_unit_footprint.py::test_composite_5_voices -x` | Wave 0 |
| FOOT-05 | compute_composite_bias with footprint unavailable returns 4/4 | unit | `pytest tests/test_unit_footprint.py::test_composite_footprint_unavailable -x` | Wave 0 |
| FOOT-05 | Footprint as dissenter identified in rationale string | unit | `pytest tests/test_unit_footprint.py::test_composite_footprint_dissenter -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_unit_footprint.py -x -q`
- **Per wave merge:** `pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_unit_footprint.py` — covers FOOT-01 through FOOT-05 (unit + composite bias)
- [ ] `tests/fixtures/footprint_15m_ohlcv.csv` — frozen 15m fixture for regression test
- [ ] `tests/test_integration_routes.py` — extend with `/api/footprint` tests
- [ ] `tests/test_regression_indicators.py` — extend with footprint cumulative-delta regression

---

## Sources

### Primary (HIGH confidence)
- `src/analytics/trading_indicators.py` (lines 16–37, 44–99, 402–534, 663–719) — verified existing patterns for fetch, bin logic, delta formula, composite bias
- `static/js/tradingIndicators.js` (full file, 367 lines) — verified current grid HTML, cache pattern, badge rendering
- `static/css/styles.css` (lines 1484–1515) — verified `.ti-2x2-grid` definition and `.ti-unavailable-placeholder`
- `webapp.py` (lines 2154–2177) — verified `/api/trading_indicators` route pattern
- `tests/test_regression_indicators.py` — verified regression test structure and fixture pattern
- `tests/test_trading_indicators.py` — verified integration test mock pattern (`patch fetch_ohlcv`)
- `static/js/peerComparison.js` (lines 17, 168–225) — verified session cache and lazy-load pattern

### Secondary (MEDIUM confidence)
- yfinance documentation: 15m interval is supported via `yf.Ticker().history(interval='15m')`; 60-day horizon is the documented limit for sub-daily intervals

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all dependencies already installed and in active use
- Architecture: HIGH — all patterns verified against live source code
- Pitfalls: HIGH — derived from actual code paths and yfinance known limitations documented in project history
- Test patterns: HIGH — regression and integration test structure copied from existing working tests

**Research date:** 2026-04-21
**Valid until:** 2026-05-21 (stable codebase; only risk is yfinance API changes)
