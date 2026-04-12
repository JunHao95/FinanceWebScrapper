# Phase 21: Order Flow — Research

**Researched:** 2026-04-12
**Domain:** Plotly dual-axis bar chart, delta computation, rolling regression, imbalance candle annotation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Delta Chart Y-axis**
- Dual Y-axis: delta bars on the left axis (raw volume units), cumulative delta line on the right axis (independent scale)
- Cumulative delta line color: white/light grey (`#cdd6f4`) — high contrast against dark background, distinct from green/red bars
- Thin dashed zero line drawn at y=0 on the delta bars axis — shows where buying flips to selling
- Right axis (cumulative delta) tick labels are visible — user can read the cumulative magnitude

**Divergence Flag Placement**
- Badge below the chart — matches the VP and AVWAP badge pattern
- Badge is always visible: shows `✔ No divergence` in muted grey when trends align; shows `⚠ Volume Divergence` in red when detected
- Format on divergence: `⚠ Volume Divergence — price slope: +0.23, vol slope: −0.15` — raw slope values shown so user can verify signal magnitude

**Imbalance Candle Annotations**
- Plotly text annotations on the chart — same annotation mechanism as AVWAP right-edge labels
- Label: ▲ for Bullish, ▼ for Bearish (arrow symbols only — compact, unambiguous)
- Annotation color matches bar color: green ▲ above bullish imbalance bars, red ▼ below bearish imbalance bars
- Position: ▲ above the bar top, ▼ below the bar bottom

**Panel Structure**
- One Plotly chart (500px height): delta bars + cumulative delta overlay + imbalance annotations all in a single figure
- Layout within ticker card: below the AVWAP panel — sequence is VP → AVWAP → Order Flow
- Brief legend panel below the badge, consistent with VP legend pattern, explaining: green = buy pressure, red = sell pressure, white line = cumulative delta, ▲/▼ = imbalance candle

### Claude's Discretion
- Exact Plotly `yaxis2` range configuration and tick formatting
- Zero-line style (color, dash pattern, width)
- Annotation font size and offset from bar top/bottom
- Legend HTML structure (reuse `ti-legend` CSS class pattern)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FLOW-01 | Green/red buy/sell pressure delta bar chart with cumulative delta overlay line, computed from `(Close−Low)/(High−Low)×Volume` proxy with epsilon guard on zero-range bars | Delta formula, epsilon guard, Plotly dual-axis pattern covered in Code Examples |
| FLOW-02 | Volume divergence flag with price-slope and volume-slope values when rolling-window trend directions diverge over a 10-bar window | Rolling linear regression slope via `numpy.polyfit`, divergence detection covered in Architecture Patterns |
| FLOW-03 | Imbalance candles (body > 70% of high-low range AND volume > 1.2× 20-day average) annotated on the chart with Bullish/Bearish labels | Annotation mechanism mirrors existing AVWAP pattern; threshold logic covered in Code Examples |
</phase_requirements>

---

## Summary

Phase 21 replaces the `compute_order_flow` stub in `src/analytics/trading_indicators.py` with a real implementation and wires the result into `tradingIndicators.js`. The computation itself is pure pandas/numpy — no new libraries are required. The Plotly chart uses a single `go.Figure` with `yaxis` for delta bars and `yaxis2` overlaid for the cumulative delta line; this is the standard Plotly secondary-axis pattern.

The two subtleties worth planning around are (1) the epsilon guard on zero-range bars, which prevents NaN propagation through the cumulative delta series, and (2) making annotation `y` positions reference `yaxis` (the bar axis, not `yaxis2`) because imbalance candle annotations must appear at bar-relative positions, not cumulative delta values.

The JS side follows the established AVWAP pattern exactly: append a new `div` for the chart, a `ti-va-badge` div for the divergence signal, and a `ti-legend` div for the legend after the AVWAP legend block in `_renderTickerCard()`.

**Primary recommendation:** Implement `compute_order_flow(df)` returning `{traces, layout, signal, divergence}`, wire it into `webapp.py` (replace the `{'status':'stub'}` line), then extend `_renderTickerCard()` in `tradingIndicators.js` to render the chart, badge, and legend.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `plotly` | installed (project-wide) | Build interactive chart dict | Already used for every indicator; `go.Figure`, `yaxis2`, `annotations` all available |
| `numpy` | installed (project-wide) | Delta computation, rolling polyfit, imbalance threshold math | `np.polyfit` covers rolling regression; vectorised ops throughout codebase |
| `pandas` | installed (project-wide) | DataFrame rolling windows, 20-day rolling mean volume | `df['Volume'].rolling(20).mean()` pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `plotly.graph_objects` | same | `go.Bar` (delta bars) + `go.Scatter` (cumulative line) | The two trace types needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `numpy.polyfit` for slope | `scipy.stats.linregress` | `scipy` not in requirements; `np.polyfit(x, y, 1)[0]` returns slope directly — same result, zero new dependency |
| Single-axis with scaled overlay | Dual-axis `yaxis2` | Dual-axis keeps delta and cumulative delta on independent scales; single-axis would compress one signal |

**Installation:** No new dependencies — all required libraries already installed.

---

## Architecture Patterns

### Recommended Project Structure

No new files needed. All changes in:
```
src/analytics/trading_indicators.py    # Replace compute_order_flow stub
static/js/tradingIndicators.js         # Extend _renderTickerCard()
webapp.py                              # Wire compute_order_flow into route
tests/test_trading_indicators.py       # Add TestComputeOrderFlow class
```

### Pattern 1: Dual-Axis Plotly Figure (Bar + Scatter)

**What:** A `go.Figure` where `go.Bar` traces are assigned to `yaxis='y'` (left axis, delta values) and `go.Scatter` is assigned to `yaxis='y2'` (right axis, cumulative delta). The layout defines `yaxis2` with `overlaying='y'`, `side='right'`.

**When to use:** Whenever two series have incompatible scales on the same chart — cumulative delta grows monotonically and would dwarf per-bar delta values on a shared axis.

**Example (adapted to project patterns):**
```python
# Source: Plotly official docs — secondary y-axis
fig = go.Figure()

fig.add_trace(go.Bar(
    x=dates, y=delta_values,
    marker_color=bar_colors,      # list: '#2ecc71' or '#e74c3c'
    name='Delta',
    yaxis='y',
))

fig.add_trace(go.Scatter(
    x=dates, y=cumulative_delta,
    mode='lines',
    line=dict(color='#cdd6f4', width=1.5),
    name='Cumulative Delta',
    yaxis='y2',
))

fig.update_layout(
    yaxis=dict(title='Delta (volume units)'),
    yaxis2=dict(
        title='Cumulative Delta',
        overlaying='y',
        side='right',
        showgrid=False,
    ),
    paper_bgcolor='#1e1e2e',
    plot_bgcolor='#1e1e2e',
    font=dict(color='#cdd6f4'),
    height=500,
)
```

### Pattern 2: Annotation Positioning on Bar-Axis

**What:** Imbalance candle annotations reference `yref='y'` (the bar delta axis) with `y` set to the bar top (for bullish ▲) or bar bottom (for bearish ▼). This is identical to the AVWAP right-edge annotation pattern at `trading_indicators.py:364–370` but with `xref='x'` (not `'paper'`) because annotations pin to specific bars.

**When to use:** Whenever an annotation must appear above/below a specific bar at a specific x position.

**Example:**
```python
# Source: Project codebase — trading_indicators.py:364 (AVWAP annotations adapted)
annotations = []
for i, bar_date in enumerate(dates):
    if imbalance_direction[i] == 'bullish':
        annotations.append(dict(
            xref='x', x=bar_date,
            yref='y', y=delta_values[i] + y_offset,  # above bar top
            text='\u25b2',       # ▲
            showarrow=False,
            font=dict(size=10, color='#2ecc71'),
        ))
    elif imbalance_direction[i] == 'bearish':
        annotations.append(dict(
            xref='x', x=bar_date,
            yref='y', y=delta_values[i] - y_offset,  # below bar bottom
            text='\u25bc',       # ▼
            showarrow=False,
            font=dict(size=10, color='#e74c3c'),
        ))
```

### Pattern 3: Zero-Range Epsilon Guard

**What:** When `High == Low` (doji/gap bar), `(Close − Low) / (High − Low)` produces a division-by-zero NaN. Replace the denominator with `max(High − Low, epsilon)` before the division.

**When to use:** Always, in the delta computation — a single NaN propagates into the cumulative delta via `cumsum()` and corrupts all subsequent values.

**Example:**
```python
# Source: CONTEXT.md specifics, project decision
EPSILON = 1e-9
ranges = (df['High'] - df['Low']).clip(lower=EPSILON)
buy_ratio = (df['Close'] - df['Low']) / ranges   # always in [0, 1]
delta = (2 * buy_ratio - 1) * df['Volume']        # positive = buy pressure, negative = sell pressure
cumulative_delta = delta.cumsum()
```

Note: The formula `(Close−Low)/(High−Low)` gives a ratio in [0,1] where 1.0 = full buy pressure. Multiplying by `2×ratio − 1` maps it to [−1, +1] then by Volume gives signed delta. Alternatively `buy_vol = ratio × Volume`, `sell_vol = (1−ratio) × Volume`, `delta = buy_vol − sell_vol` — identical numerically.

### Pattern 4: Rolling Linear Regression Slope (numpy.polyfit)

**What:** Compute the slope of a 10-bar rolling window on both price and volume using `np.polyfit(x, y, 1)[0]`. Volume divergence fires when `price_slope * volume_slope < 0` (opposite signs).

**When to use:** FLOW-02 requires 10-bar rolling windows. `pandas.rolling` does not expose slope directly, so iterate with a loop or use `numpy.polyfit` on each window.

**Example:**
```python
# Source: numpy documentation — polyfit slope extraction
def _rolling_slope(series: pd.Series, window: int = 10) -> pd.Series:
    slopes = pd.Series(index=series.index, dtype=float)
    x = np.arange(window, dtype=float)
    for i in range(window - 1, len(series)):
        y = series.iloc[i - window + 1 : i + 1].values.astype(float)
        slopes.iloc[i] = np.polyfit(x, y, 1)[0]
    return slopes

price_slopes = _rolling_slope(df['Close'], 10)
vol_slopes   = _rolling_slope(df['Volume'], 10)

# Detect divergence at the last bar (most recent signal)
divergence = bool(price_slopes.iloc[-1] * vol_slopes.iloc[-1] < 0)
price_slope_val = float(price_slopes.iloc[-1]) if pd.notna(price_slopes.iloc[-1]) else 0.0
vol_slope_val   = float(vol_slopes.iloc[-1])   if pd.notna(vol_slopes.iloc[-1])   else 0.0
```

### Pattern 5: Imbalance Candle Detection

**What:** A bar is an imbalance candle when `body_size / bar_range > 0.70` AND `volume > 1.2 × rolling_20day_avg_volume`.

**When to use:** FLOW-03. Compute once vectorized before building annotations.

**Example:**
```python
body = (df['Close'] - df['Open']).abs()
bar_range = (df['High'] - df['Low']).clip(lower=EPSILON)
body_ratio = body / bar_range                                    # [0, 1]

avg_vol_20 = df['Volume'].rolling(20, min_periods=1).mean()
vol_spike = df['Volume'] > 1.2 * avg_vol_20

is_imbalance = (body_ratio > 0.70) & vol_spike
is_bullish   = is_imbalance & (df['Close'] > df['Open'])
is_bearish   = is_imbalance & (df['Close'] < df['Open'])
```

### Pattern 6: JS Rendering — Extending _renderTickerCard()

**What:** After the AVWAP legend block (line 180 in `tradingIndicators.js`), append three DOM elements: order flow chart div, divergence badge div, legend div. Render the chart with `Plotly.newPlot(..., { staticPlot: true, responsive: true })`.

**When to use:** Exactly once, at the tail of `_renderTickerCard()` before the closing brace of the function.

**Example:**
```javascript
// Source: Project codebase — tradingIndicators.js:127 (AVWAP render pattern)
var ofDivId   = 'ofChart_'  + ticker;
var ofBadgeId = 'ofBadge_'  + ticker;

var ofChartEl = document.createElement('div');
ofChartEl.id = ofDivId;
ofChartEl.style.cssText = 'width:100%;height:500px;margin-top:24px;';
card.appendChild(ofChartEl);

var ofBadgeEl = document.createElement('div');
ofBadgeEl.id = ofBadgeId;
ofBadgeEl.className = 'ti-va-badge';
card.appendChild(ofBadgeEl);

var of = resp.order_flow;
if (of && of.traces && of.layout) {
    Plotly.newPlot(ofDivId, of.traces, of.layout, { staticPlot: true, responsive: true });
}

if (of && of.divergence !== undefined) {
    var hasDivergence = of.divergence.detected;
    ofBadgeEl.textContent = hasDivergence
        ? '\u26a0 Volume Divergence \u2014 price slope: ' + of.divergence.price_slope.toFixed(4)
          + ', vol slope: ' + of.divergence.vol_slope.toFixed(4)
        : '\u2714 No divergence';
    ofBadgeEl.style.color = hasDivergence ? '#e74c3c' : '#7f849c';
    ofBadgeEl.style.fontWeight = 'bold';
    ofBadgeEl.style.fontSize   = '14px';
    ofBadgeEl.style.display    = 'block';
}
```

### Pattern 7: API Response Shape

`compute_order_flow` must return a dict matching the shape that `_renderTickerCard()` destructures:

```python
{
    'traces':  [...],    # list of Plotly trace dicts
    'layout':  {...},    # Plotly layout dict (template removed)
    'signal':  'bullish' | 'bearish' | 'neutral',   # dominant direction of last bar
    'divergence': {
        'detected':    bool,
        'price_slope': float,
        'vol_slope':   float,
    },
}
```

### Anti-Patterns to Avoid

- **Assigning cumulative delta annotations to `yref='y2'`:** Imbalance annotations must use `yref='y'` (the delta bar axis). Annotations that reference `yaxis2` will position relative to cumulative delta values, placing them at wrong heights.
- **Using `fig.add_trace(..., secondary_y=True)`** via `make_subplots(specs=...)`: That pattern is for row/col subplots. For a single-panel dual-axis, use `yaxis2` in layout + `yaxis='y2'` on the scatter trace — `make_subplots` is not needed here.
- **Returning `NaN` in `cumulative_delta` list:** `json.dumps(float('nan'))` raises `ValueError` in Flask's `jsonify`. Use `_safe_list()` (already defined in the module at line 238) to replace NaN with `None`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Linear regression slope | Custom least-squares loop | `np.polyfit(x, y, 1)[0]` | Numerically stable, one line, handles any window size |
| NaN-to-None conversion for JSON | Custom loop | `_safe_list()` already in `trading_indicators.py:238` | Reuse, consistency |
| Rolling 20-day average volume | Custom accumulator | `df['Volume'].rolling(20, min_periods=1).mean()` | Handles partial windows at start of series |

**Key insight:** All helper infrastructure (`_safe_list`, `PAPER_BG`, `PLOT_BG`, `FONT_CLR`) already exists in the module. No new utilities needed.

---

## Common Pitfalls

### Pitfall 1: NaN Propagation from Doji Bars

**What goes wrong:** A single zero-range bar (`High == Low`) causes `(Close−Low)/(High−Low)` to produce NaN. `cumsum()` on a series containing NaN propagates NaN to all subsequent values. The cumulative delta line becomes a flat line after the first doji.

**Why it happens:** Stock data commonly includes pre-market, gap, or halted bars where High == Low. yfinance does not filter these.

**How to avoid:** Apply epsilon guard before the division: `ranges = (df['High'] - df['Low']).clip(lower=1e-9)`.

**Warning signs:** Cumulative delta line terminates early or shows a sudden flat section when plotted.

### Pitfall 2: Annotation yref Mismatch on Dual-Axis Chart

**What goes wrong:** If `yref='y2'` is used for imbalance annotations, annotation y-coordinates are interpreted against the cumulative delta scale (which may be in the thousands), placing labels far off-screen or at incorrect positions.

**Why it happens:** Plotly has two y-axes; annotation `yref` must explicitly target the correct one.

**How to avoid:** Always use `yref='y'` for imbalance candle annotations. The annotation y value is the delta bar value (raw signed volume), not cumulative delta.

**Warning signs:** Annotations invisible on chart, or appear at extreme top/bottom of chart area.

### Pitfall 3: Stub Still in webapp.py Route

**What goes wrong:** If the import line in `webapp.py` is not updated to include `compute_order_flow`, the route still returns `{'status': 'stub'}` and the JS renders nothing for the Order Flow panel.

**Why it happens:** The import at `webapp.py:2161` explicitly lists `fetch_ohlcv, compute_volume_profile, compute_anchored_vwap`. `compute_order_flow` must be added to this import and the stub line replaced.

**How to avoid:** Update both the `from ... import` statement and the `'order_flow': {'status': 'stub'}` line simultaneously.

**Warning signs:** Order Flow panel renders empty; network tab shows `order_flow: {status: 'stub'}` in API response.

### Pitfall 4: Zero-Delta Bar Color (delta == 0)

**What goes wrong:** When `delta == 0` (perfectly symmetrical bar or zero-volume bar), neither green nor red applies. Using a conditional that only checks `> 0` or `< 0` leaves zero-delta bars without a color, which Plotly renders as its default blue, breaking the visual theme.

**Why it happens:** `np.where(delta > 0, '#2ecc71', '#e74c3c')` assigns red to zero as well as negative — this is acceptable, but worth documenting as intentional.

**How to avoid:** Use `np.where(delta >= 0, '#2ecc71', '#e74c3c')` — treat exactly-zero as buy-neutral (green). Document the convention.

### Pitfall 5: Volume Rolling Mean with Short Series

**What goes wrong:** If the lookback window is 30 days, the DataFrame has ~21 trading-day rows. `rolling(20)` produces NaN for the first 19 rows. Volume spike check `volume > 1.2 × NaN` is always False, so no imbalance candles appear in the first 19 rows.

**Why it happens:** Default `rolling(20)` requires exactly 20 observations. Rows 0–18 are NaN.

**How to avoid:** Use `rolling(20, min_periods=1)` — this fills early rows using however many observations are available, giving meaningful (if imprecise) averages from row 1 onward.

---

## Code Examples

Verified patterns from project codebase and official sources:

### Complete compute_order_flow Skeleton
```python
# Source: trading_indicators.py patterns (AVWAP, VP) + project decisions
def compute_order_flow(df: pd.DataFrame) -> dict:
    """
    Compute Order Flow delta bars, cumulative delta, divergence signal,
    and imbalance candle annotations.

    Returns dict: {traces, layout, signal, divergence}
    """
    EPSILON = 1e-9
    dates = df.index.astype(str).tolist()

    # --- Delta computation (FLOW-01) ---
    ranges = (df['High'] - df['Low']).clip(lower=EPSILON)
    buy_ratio = (df['Close'] - df['Low']) / ranges
    delta = (2 * buy_ratio - 1) * df['Volume']
    cumulative_delta = delta.cumsum()

    bar_colors = ['#2ecc71' if v >= 0 else '#e74c3c' for v in delta]

    # --- Rolling regression for divergence (FLOW-02) ---
    WINDOW = 10
    x = np.arange(WINDOW, dtype=float)

    def _last_slope(series):
        if len(series) < WINDOW:
            return 0.0
        y = series.iloc[-WINDOW:].values.astype(float)
        return float(np.polyfit(x, y, 1)[0])

    price_slope = _last_slope(df['Close'])
    vol_slope   = _last_slope(df['Volume'])
    divergence_detected = (price_slope * vol_slope < 0) and (len(df) >= WINDOW)

    # --- Imbalance candle detection (FLOW-03) ---
    body = (df['Close'] - df['Open']).abs()
    bar_range = (df['High'] - df['Low']).clip(lower=EPSILON)
    body_ratio = body / bar_range
    avg_vol_20 = df['Volume'].rolling(20, min_periods=1).mean()
    vol_spike = df['Volume'] > 1.2 * avg_vol_20
    is_imbalance = (body_ratio > 0.70) & vol_spike
    is_bullish = is_imbalance & (df['Close'] >= df['Open'])
    is_bearish = is_imbalance & (df['Close'] < df['Open'])

    # --- Build annotations ---
    delta_values = delta.tolist()
    delta_range = max(abs(max(delta_values)), abs(min(delta_values)), 1.0)
    y_offset = delta_range * 0.05   # 5% of range above/below bar

    annotations = []
    for i, date in enumerate(dates):
        if is_bullish.iloc[i]:
            annotations.append(dict(
                xref='x', x=date,
                yref='y', y=delta_values[i] + y_offset,
                text='\u25b2',
                showarrow=False,
                font=dict(size=10, color='#2ecc71'),
            ))
        elif is_bearish.iloc[i]:
            annotations.append(dict(
                xref='x', x=date,
                yref='y', y=delta_values[i] - y_offset,
                text='\u25bc',
                showarrow=False,
                font=dict(size=10, color='#e74c3c'),
            ))

    # --- Build Plotly figure ---
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dates,
        y=_safe_list(delta),
        marker_color=bar_colors,
        name='Delta',
        yaxis='y',
    ))
    fig.add_trace(go.Scatter(
        x=dates,
        y=_safe_list(cumulative_delta),
        mode='lines',
        line=dict(color='#cdd6f4', width=1.5),
        name='Cumulative Delta',
        yaxis='y2',
    ))

    shapes = [dict(
        type='line', xref='paper', x0=0, x1=1,
        yref='y', y0=0, y1=0,
        line=dict(color='rgba(205,214,244,0.4)', width=1, dash='dash'),
    )]

    fig.update_layout(
        title=f'{df.index[-1].strftime("%Y-%m-%d") if hasattr(df.index[-1], "strftime") else ""} Order Flow',
        height=500,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=FONT_CLR),
        shapes=shapes,
        annotations=annotations,
        yaxis=dict(title='Delta (vol)', side='left'),
        yaxis2=dict(
            title='Cumulative Delta',
            overlaying='y',
            side='right',
            showgrid=False,
        ),
        margin=dict(l=70, r=90, t=50, b=50),
        showlegend=False,
        barmode='relative',
    )

    d = fig.to_dict()
    d['layout'].pop('template', None)

    signal = 'bullish' if float(delta.iloc[-1]) >= 0 else 'bearish'

    return {
        'traces': d['data'],
        'layout': d['layout'],
        'signal': signal,
        'divergence': {
            'detected':    divergence_detected,
            'price_slope': round(price_slope, 6),
            'vol_slope':   round(vol_slope, 6),
        },
    }
```

### webapp.py Route Update
```python
# Source: webapp.py:2161 — extend the import and replace stub
from src.analytics.trading_indicators import (
    fetch_ohlcv, compute_volume_profile, compute_anchored_vwap, compute_order_flow
)
# Replace:
#   'order_flow': {'status': 'stub'},
# With:
    'order_flow': compute_order_flow(df),
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `yf.download()` for OHLCV | `yf.Ticker().history()` | Phase 09-01 | Prevents 2D/1D shape corruption in concurrent calls — already enforced in `fetch_ohlcv` |
| Stub `{'status': 'stub'}` | Real `compute_order_flow(df)` | This phase | Order Flow panel renders for real data |

**Deprecated/outdated:**
- The `compute_order_flow` stub body — replaced in this phase.

---

## Open Questions

1. **Ticker parameter for chart title in compute_order_flow**
   - What we know: `compute_order_flow` currently receives only `df`, not `ticker` or `lookback`.
   - What's unclear: Whether the chart title should show the ticker symbol.
   - Recommendation: Add `ticker: str = ''` and `lookback: int = 0` parameters to `compute_order_flow` signature, matching `compute_volume_profile`'s signature. The route call becomes `compute_order_flow(df, ticker, lookback)`.

2. **Annotation offset calculation**
   - What we know: Offset should be proportional to the delta range.
   - What's unclear: Whether a flat 5% offset looks right across different tickers (high-volume stocks have very large delta values).
   - Recommendation: Use `delta_range * 0.05` as computed in the skeleton above — Claude's discretion per CONTEXT.md.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | none (pytest auto-discovers `tests/`) |
| Quick run command | `pytest tests/test_trading_indicators.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FLOW-01 | Delta series contains no NaN; cumulative delta has same length as df | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_no_nan_in_cumulative_delta -x` | ❌ Wave 0 |
| FLOW-01 | Zero-range bars produce valid delta (epsilon guard) | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_epsilon_guard_on_zero_range -x` | ❌ Wave 0 |
| FLOW-01 | Response has required keys: traces, layout, signal, divergence | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_order_flow_keys -x` | ❌ Wave 0 |
| FLOW-02 | Divergence detected when slopes have opposite signs | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_divergence_detected_opposite_slopes -x` | ❌ Wave 0 |
| FLOW-02 | No divergence when slopes have same sign | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_no_divergence_same_sign_slopes -x` | ❌ Wave 0 |
| FLOW-03 | Imbalance candle with large body + volume spike → annotation present | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_imbalance_candle_annotation -x` | ❌ Wave 0 |
| FLOW-03 | Normal candle → no annotation | unit | `pytest tests/test_trading_indicators.py::TestComputeOrderFlow::test_no_annotation_normal_candle -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_trading_indicators.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_trading_indicators.py` — add `TestComputeOrderFlow` class (file exists, class absent)

*(No new test files needed — the class is appended to the existing test file.)*

---

## Sources

### Primary (HIGH confidence)
- Project codebase: `src/analytics/trading_indicators.py` — existing patterns for `go.Figure`, `_safe_list`, constants, AVWAP annotation mechanism
- Project codebase: `static/js/tradingIndicators.js` — AVWAP panel append pattern at lines 106–180
- Project codebase: `tests/test_trading_indicators.py` — existing test fixture patterns
- Project CONTEXT.md — locked implementation decisions

### Secondary (MEDIUM confidence)
- Plotly official docs — `yaxis2` / `overlaying='y'` dual-axis pattern (standard documented feature, consistent with installed version)
- `numpy.polyfit` docs — slope extraction from degree-1 polynomial fit

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed and used in adjacent phases
- Architecture: HIGH — patterns directly mirror AVWAP implementation in same file
- Pitfalls: HIGH — epsilon guard and annotation yref issues are verifiable from code inspection
- Algorithm: HIGH — delta formula and thresholds are explicitly specified in CONTEXT.md

**Research date:** 2026-04-12
**Valid until:** 2026-05-12 (stable domain — no external API changes expected)
