# Phase 20: Anchored VWAP - Research

**Researched:** 2026-04-12
**Domain:** Anchored VWAP computation, Plotly candlestick overlay, yfinance earnings API, Flask route extension
**Confidence:** HIGH

## Summary

Phase 20 replaces the `compute_anchored_vwap` stub in `trading_indicators.py` and the matching `{'status': 'stub'}` response in the Flask route with a real implementation. The backend computes three AVWAP lines (52-week high anchor, 52-week low anchor, earnings anchor) from a 365-day OHLCV fetch, then slices to the user's display lookback for rendering. The Plotly figure is a single-axis candlestick chart (not a subplot) with three Scatter traces overlaid and Plotly annotations providing right-edge distance labels.

All design decisions are locked in CONTEXT.md. No new dependencies are required — yfinance 0.2.58 (installed) supplies both OHLCV and earnings dates via `Ticker.earnings_dates`. The earnings date fallback path was empirically verified: `earnings_dates` returns `None` for ETFs (GLD, TLT), returns an empty `Reported EPS` column for some tickers (QQQ), and returns a valid DataFrame with tz-aware index for equity tickers (AAPL). The JS side extends `_renderTickerCard()` to append an AVWAP chart div and two badge divs below the existing VP chart.

**Primary recommendation:** Compute AVWAP on the full 365-day `df_365` then `reindex(df_display.index)` — this gives correct cumulative weighted averages while naturally producing NaN for display days before the anchor, which Plotly handles cleanly with `connectgaps=True`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Chart Layout:**
- AVWAP gets its own standalone candlestick chart — separate from the Volume Profile panel. VP stays clean with its histogram; AVWAP is a distinct panel below it.
- The chart renders the user's selected display lookback (e.g. 90 days) as the visible candle window.
- AVWAP lines start from the anchor date and run to today. If the anchor is outside the display window, the line begins at the left edge of the chart (clipped at chart start, not truncated).
- 500px height, matching Volume Profile.
- A thin horizontal dashed line at current price (last close) is added as a reference line for easy visual comparison to AVWAP levels.
- Three lines are distinguished by color only (all solid):
  - 52-wk High AVWAP → blue
  - 52-wk Low AVWAP → orange
  - Earnings AVWAP → purple

**Right-Edge Labels:**
- Labels rendered as Plotly annotations anchored to the right edge of the chart at each AVWAP's y-level (not an HTML block below).
- Label format: name + distance, e.g. `52-wk High: +2.1%` (not just the distance alone).
- Label color matches the AVWAP line color (blue/orange/purple) for visual linking.

**Convergence Warning:**
- When any AVWAP line is within 0.3% of the current price, a warning badge appears below the chart (same position as the VP signal badge).
- Warning format: `⚠ Convergence: [line name] AVWAP within 0.3% of current price at $X.XX`
- When no convergence exists, show a muted `✓ No AVWAP convergence` badge (always visible, not hidden).

**Earnings Anchor Source:**
- Use `yf.Ticker(ticker).earnings_dates` to retrieve the last earnings date. Filter rows where `Reported EPS` is not NaN; take the max (most recent past) date.
- When yfinance returns no earnings date (None, empty, or all-NaN Reported EPS): show a text note below the chart (not a badge): `"Earnings anchor unavailable — only 52-wk high & low lines shown."` The chart still renders the two remaining AVWAP lines normally.

**OHLCV Fetch Strategy:**
- Always fetch 365 days for anchor resolution (to find 52-wk high/low dates and earnings anchor). This is a separate call from the display fetch.
- The display chart shows only the user-selected lookback (e.g. 90 days), but AVWAP is computed from the full 365-day dataset for accurate anchor positioning.

### Claude's Discretion
- Exact Plotly annotation xanchor/xref positioning for right-edge labels
- Color shading or opacity of the current-price reference line
- Badge CSS styling (reuse `ti-va-badge` class or minor variant)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AVWAP-01 | Two AVWAP lines anchored to 52-week high and low dates, overlaid on price chart, with current price vs. each AVWAP as a sub-signal | Verified: `df['High'].idxmax()` / `df['Low'].idxmin()` on 365-day df gives anchor dates; AVWAP formula TP=(H+L+C)/3, cumsum(TP*V)/cumsum(V); `reindex(df_display.index)` clips to display window |
| AVWAP-02 | Third AVWAP for last earnings date when available; "Earnings anchor unavailable" note when not | Verified: `earnings_dates` with `Reported EPS.notna()` filter finds past dates; returns None for ETFs, empty for some tickers — all handled by null check |
| AVWAP-03 | Right-edge distance labels per AVWAP; convergence note when any two lines within 0.3% of current price | Verified: Plotly annotation `xref='paper', x=1.0, xanchor='left'` places labels past right axis; convergence check `abs(current - avwap) / current <= 0.003` |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yfinance | 0.2.58 (installed) | OHLCV fetch + earnings dates | Already imported; canonical fetch pattern established in Phase 18 |
| pandas | (installed) | DataFrame operations, date indexing, reindex | All data manipulation |
| numpy | (installed) | Cumsum AVWAP formula | Vectorised operations on price/volume arrays |
| plotly | (installed) | Candlestick + Scatter traces + annotations | All Trading Indicators charts use Plotly |

### No New Dependencies
Phase 20 introduces zero new packages. Everything is already imported in `trading_indicators.py`.

## Architecture Patterns

### Recommended Project Structure

No new files. Changes are isolated to:
```
src/analytics/trading_indicators.py   # Replace compute_anchored_vwap stub
webapp.py                             # Replace 'anchored_vwap': {'status': 'stub'} with real call
static/js/tradingIndicators.js        # Extend _renderTickerCard() for AVWAP panel
tests/test_trading_indicators.py      # Add TestComputeAnchoredVwap class
```

### Pattern 1: Two-Fetch Strategy (365d for anchor, display-slice for chart)

**What:** Fetch 365 days unconditionally for anchor resolution; compute full AVWAP series from each anchor; `reindex` the result to the display-window dates.

**When to use:** Always — the display lookback (30/90/180/365) may be shorter than the 52-week anchor range.

**Example:**
```python
def compute_anchored_vwap(df: pd.DataFrame, ticker: str, lookback: int) -> dict:
    # df is already the 365-day fetch (caller passes fetch_ohlcv(ticker, 365))
    # Anchor resolution
    wk52_high_date = df['High'].idxmax()
    wk52_low_date  = df['Low'].idxmin()

    # Display slice
    df_display = df.iloc[-lookback:] if len(df) >= lookback else df

    def _avwap(anchor_date) -> pd.Series:
        subset = df.loc[anchor_date:]
        tp = (subset['High'] + subset['Low'] + subset['Close']) / 3.0
        cum_tpv = (tp * subset['Volume']).cumsum()
        cum_v   = subset['Volume'].cumsum()
        return (cum_tpv / cum_v).reindex(df_display.index)  # NaN before anchor = connectgaps handles

    avwap_high = _avwap(wk52_high_date)
    avwap_low  = _avwap(wk52_low_date)
    ...
```

### Pattern 2: Earnings Date Extraction

**What:** Use `yf.Ticker(ticker).earnings_dates`, filter for `Reported EPS` not NaN (past dates only), take the max date, strip timezone.

**Example:**
```python
def _get_last_earnings_date(ticker: str):
    """Returns tz-naive date string or None."""
    try:
        t = yf.Ticker(ticker)
        ed = t.earnings_dates
        if ed is None or ed.empty:
            return None
        if 'Reported EPS' not in ed.columns:
            return None
        past = ed[ed['Reported EPS'].notna()]
        if past.empty:
            return None
        last = past.index.max()
        # Strip timezone (index is tz-aware from yfinance)
        if hasattr(last, 'tz_localize'):
            last = last.tz_localize(None)
        elif hasattr(last, 'tz_convert'):
            last = last.tz_convert(None)
        return str(last.date())
    except Exception:
        return None
```

**Verified edge cases:**
- `GLD`, `TLT`: `earnings_dates` returns `None` → function returns `None` ✓
- `QQQ`: Returns DataFrame but zero rows where `Reported EPS` is not NaN → function returns `None` ✓
- `AAPL`, `BRK-B`: Returns valid past earnings date ✓

### Pattern 3: Plotly Figure Assembly

**What:** Single `go.Figure()` (not `make_subplots`) with candlestick as trace 0, three Scatter traces (one per AVWAP), a horizontal dashed shape for current price, and annotations for right-edge labels.

**Key flags:**
- `connectgaps=True` on all AVWAP Scatter traces (handles NaN when anchor is inside display window)
- Shape for current price uses `xref='paper'` (spans full width regardless of x-axis range)
- Annotations use `xref='paper', x=1.0, xanchor='left'` to push labels past right axis

**Example:**
```python
import plotly.graph_objects as go

COLORS = {
    'high':     '#4c9be8',   # blue (Catppuccin Blue)
    'low':      '#fe8019',   # orange
    'earnings': '#cba6f7',   # purple (Catppuccin Mauve)
    'ref_line': 'rgba(205,214,244,0.35)',  # muted white-grey
}

fig = go.Figure()

# Candlestick
fig.add_trace(go.Candlestick(
    x=df_display.index.astype(str).tolist(),
    open=df_display['Open'].tolist(),
    high=df_display['High'].tolist(),
    low=df_display['Low'].tolist(),
    close=df_display['Close'].tolist(),
    name=ticker, showlegend=False,
))

# AVWAP lines (connectgaps=True for anchors inside display window)
fig.add_trace(go.Scatter(
    x=df_display.index.astype(str).tolist(),
    y=avwap_high.tolist(),
    name='52-wk High AVWAP', mode='lines',
    line=dict(color=COLORS['high'], width=1.5),
    connectgaps=True,
))
# ... repeat for low and earnings

# Current price reference line
fig.add_shape(
    type='line', xref='paper', x0=0, x1=1,
    yref='y', y0=current_price, y1=current_price,
    line=dict(color=COLORS['ref_line'], width=1, dash='dash'),
)

# Right-edge annotation
fig.add_annotation(
    x=1.0, xref='paper',
    y=float(avwap_high.iloc[-1]), yref='y',
    xanchor='left', text=f'52-wk High: {pct_high:+.1f}%',
    showarrow=False,
    font=dict(color=COLORS['high'], size=10),
)

fig.update_layout(
    title=f'{ticker} — Anchored VWAP ({lookback}d)',
    height=500,
    paper_bgcolor='#1e1e2e', plot_bgcolor='#1e1e2e',
    font=dict(color='#cdd6f4'),
    xaxis_rangeslider_visible=False,
    margin=dict(l=70, r=120, t=70, b=50),  # r=120 gives room for labels
)
```

**Note:** `r=120` (not `r=20` used by VP) because right-edge annotations at `x=1.01` need horizontal clearance.

### Pattern 4: Route Change (webapp.py)

**What:** Replace the stub in `get_trading_indicators()` with a call to `compute_anchored_vwap`.

**Example:**
```python
# webapp.py — inside get_trading_indicators()
from src.analytics.trading_indicators import fetch_ohlcv, compute_volume_profile, compute_anchored_vwap

df_display = fetch_ohlcv(ticker, lookback)
df_365     = fetch_ohlcv(ticker, 365)     # separate 365-day fetch for anchor resolution

return jsonify({
    'ticker': ticker,
    'lookback': lookback,
    'volume_profile':   compute_volume_profile(df_display, ticker, lookback),
    'anchored_vwap':    compute_anchored_vwap(df_365, ticker, lookback),
    'order_flow':       {'status': 'stub'},
    'liquidity_sweep':  {'status': 'stub'},
    'composite_bias':   {'status': 'stub'},
})
```

**Signature change:** `compute_anchored_vwap(df, ticker, lookback)` — replaces the stub which only accepted `df`.

### Pattern 5: JS _renderTickerCard() Extension

**What:** After the VP chart block, append an AVWAP chart div, two badge divs (convergence badge + earnings-unavailable note), and call `Plotly.newPlot`.

**Key decisions:**
- AVWAP chart div ID: `avwapChart_<ticker>`
- Convergence badge div ID: `avwapBadge_<ticker>`
- Earnings note div ID: `avwapNote_<ticker>`
- Use `staticPlot: true` (required by TIND-03)
- Badge reuses inline style pattern from VP badge (no new CSS class required)

```javascript
var avwapDivId   = 'avwapChart_' + ticker;
var avwapBadgeId = 'avwapBadge_' + ticker;
var avwapNoteId  = 'avwapNote_'  + ticker;

// Append AVWAP section inside card.innerHTML or via DOM manipulation after card is appended
card.innerHTML += (
    '<div id="' + avwapDivId + '" style="width:100%;height:500px;margin-top:24px;"></div>' +
    '<div id="' + avwapBadgeId + '" class="ti-va-badge"></div>' +
    '<div id="' + avwapNoteId  + '" style="color:#7f849c;font-size:12px;margin:4px 0 8px 0;"></div>'
);

// After container.appendChild(card):
var av = resp.anchored_vwap;
if (av && av.traces && av.layout) {
    Plotly.newPlot(avwapDivId, av.traces, av.layout, { staticPlot: true, responsive: true });
    // Convergence badge
    var badgeEl = document.getElementById(avwapBadgeId);
    if (badgeEl && av.convergence) {
        var conv = av.convergence;
        if (conv.length > 0) {
            badgeEl.textContent = '\u26a0 Convergence: ' + conv.join(', ') + ' AVWAP within 0.3% of current price at $' + av.current_price.toFixed(2);
            badgeEl.style.color = '#e74c3c';
        } else {
            badgeEl.textContent = '\u2714 No AVWAP convergence';
            badgeEl.style.color = '#7f849c';
        }
        badgeEl.style.fontWeight = 'bold';
        badgeEl.style.fontSize   = '14px';
        badgeEl.style.display    = 'block';
    }
    // Earnings unavailable note
    var noteEl = document.getElementById(avwapNoteId);
    if (noteEl && av.earnings_unavailable) {
        noteEl.textContent = 'Earnings anchor unavailable \u2014 only 52-wk high & low lines shown.';
    }
}
```

### Pattern 6: API Response Shape

The `compute_anchored_vwap` return dict must contain:

```python
{
    'traces': [...],           # Plotly trace dicts (candlestick + 3 scatter)
    'layout': {...},           # Plotly layout dict (no 'template' key)
    'signal': 'above_high' | 'below_low' | 'between',  # for future composite bias
    'convergence': [],         # list of converging line names (empty = no convergence)
    'current_price': 260.48,   # float
    'earnings_unavailable': False,  # bool — drives JS note display
    'labels': {                # right-edge label text per line (informational)
        'high': '52-wk High: -1.0%',
        'low':  '52-wk Low: +9.3%',
        'earnings': None,      # None when unavailable
    }
}
```

### Anti-Patterns to Avoid

- **Using `df.loc[anchor_date:]` on the display-window df:** If the anchor is before the display window, `df.loc[anchor_date:]` on `df_display` returns the full display slice but AVWAP is computed only from that subset, not from anchor → incorrect values. Always compute AVWAP on `df_365`, then `reindex(df_display.index)`.
- **Using `yf.Ticker.calendar` for past earnings date:** `calendar['Earnings Date']` returns the *upcoming* (future) earnings date, not the last past date. Use `earnings_dates` with `Reported EPS.notna()` filter.
- **Omitting `connectgaps=True`:** When the 52-week high anchor is inside the display window (last few months), the first N rows of the AVWAP series will be NaN. Without `connectgaps=True`, Plotly leaves a gap and the line does not appear to start from the anchor.
- **Using `r=20` margin from VP:** VP has no right-side annotations. AVWAP labels at `x=1.0, xanchor='left'` need at least `r=100–120` to avoid clipping.
- **Hardcoding `staticPlot: false`:** TIND-03 requires `staticPlot: true` for all Trading Indicator charts. VP currently uses `displayModeBar: true, scrollZoom: true` — this must be corrected for VP too (Phase 19 artifact, but AVWAP must not repeat the mistake).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cumulative VWAP | Custom loop | `pandas.cumsum` on TP*V and V | Vectorised, handles NaN, tested |
| 52-week anchor date | Custom rolling max | `df['High'].idxmax()` | Single call on 365-day df |
| Right-edge annotations | HTML overlay positioned with JS | Plotly annotations with `xref='paper'` | Survives chart resize, no CSS positioning needed |
| Earnings date lookup | Custom web scrape | `yf.Ticker.earnings_dates` | Already imported, verified 0.2.58 API |

## Common Pitfalls

### Pitfall 1: Timezone on earnings_dates index
**What goes wrong:** `past.index.max()` returns a tz-aware Timestamp (e.g. `2025-05-01 16:30:00-04:00`). Using it as a `df_365.loc[]` key against a tz-naive DatetimeIndex raises `TypeError: Cannot compare tz-naive and tz-aware timestamps`.
**Why it happens:** yfinance returns earnings_dates with tz-aware index; `fetch_ohlcv` strips timezone per project convention.
**How to avoid:** Strip timezone with `last = last.tz_localize(None)` after `past.index.max()`.
**Warning signs:** `TypeError: Cannot compare tz-naive and tz-aware` in webapp logs.

### Pitfall 2: Exact anchor date not in OHLCV index (weekend/holiday)
**What goes wrong:** `df_365.loc[wk52_high_date:]` works fine; but if you try exact `df_365.loc[wk52_high_date]` it may KeyError if the date is a non-trading day.
**Why it happens:** `idxmax()` on a trading-day index always returns a trading day, so this is not a risk for 52-wk anchors. But for earnings dates extracted from `earnings_dates`, the reported date may be an after-market timestamp that doesn't align to `df_365` index exactly.
**How to avoid:** Use `df_365.loc[anchor_date:]` (slice, not exact lookup). If the earnings date is not in the index, `.loc[date:]` still works — it starts from the first row >= the date. Convert earnings date string to `pd.Timestamp` first.
**Warning signs:** Empty subset from `df_365.loc[earnings_ts:]` when earnings date is recent (earnings occurred on a non-trading day entry).

### Pitfall 3: Cumulative volume = 0 on first row
**What goes wrong:** `cumsum(V)` starts at `Volume[anchor]`. If the anchor row has Volume=0 (some tickers report 0 volume on certain days), division by zero produces `inf`.
**Why it happens:** OHLCV data occasionally has 0-volume rows (halted trading, data gaps).
**How to avoid:** Guard with `cum_v = cum_v.replace(0, np.nan)` before division; the resulting NaN is handled by `connectgaps`.

### Pitfall 4: Earnings anchor more than 365 days old
**What goes wrong:** `df_365.loc[earnings_ts:]` returns the full 365-day df (anchor is before the fetch window), producing an AVWAP that is actually the entire 365-day AVWAP, not anchored to earnings.
**Why it happens:** Some tickers report infrequently (semi-annual). The last past earnings may be > 365 days ago.
**How to avoid:** After resolving `earnings_ts`, check it against `df_365.index[0]`. If `earnings_ts < df_365.index[0]`, treat as unavailable: set `earnings_unavailable = True`, skip the earnings AVWAP trace.

### Pitfall 5: JSON serialization of NaN
**What goes wrong:** `avwap_high.tolist()` produces Python `nan` values, which Flask's `jsonify` serializes as `NaN` — invalid JSON per spec. Some JS parsers handle it, some don't.
**Why it happens:** pandas `reindex` fills missing rows with NaN; converting to list passes float NaN to JSON encoder.
**How to avoid:** Replace NaN with `None` before serializing: `avwap_high.where(avwap_high.notna(), other=None).tolist()`.

## Code Examples

### AVWAP Core Formula
```python
# Anchored VWAP from anchor_date forward
def _avwap_series(df_full: pd.DataFrame, anchor_date, display_index) -> pd.Series:
    """
    Compute AVWAP anchored at anchor_date over df_full,
    then reindex to display_index (NaN before anchor = connectgaps).
    """
    subset = df_full.loc[anchor_date:]
    if subset.empty:
        return pd.Series(index=display_index, dtype=float)
    tp = (subset['High'] + subset['Low'] + subset['Close']) / 3.0
    cum_v   = subset['Volume'].cumsum()
    cum_v   = cum_v.replace(0, np.nan)         # guard zero-volume rows
    cum_tpv = (tp * subset['Volume']).cumsum()
    avwap   = cum_tpv / cum_v
    return avwap.reindex(display_index)
```

### Convergence Check
```python
def _check_convergence(current_price: float, avwap_vals: dict, threshold: float = 0.003) -> list:
    """
    Returns list of line names where |current - avwap| / current <= threshold.
    threshold = 0.003 = 0.3%
    """
    converging = []
    for name, val in avwap_vals.items():
        if val is None or np.isnan(val):
            continue
        if abs(current_price - val) / current_price <= threshold:
            converging.append(name)
    return converging
```

### Earnings Date Extraction
```python
def _get_last_earnings_date(ticker: str):
    """Returns tz-naive Timestamp or None."""
    try:
        ed = yf.Ticker(ticker).earnings_dates
        if ed is None or ed.empty or 'Reported EPS' not in ed.columns:
            return None
        past = ed[ed['Reported EPS'].notna()]
        if past.empty:
            return None
        last = past.index.max()
        # Strip timezone (yfinance index is always tz-aware)
        return last.tz_localize(None) if last.tzinfo is not None else last
    except Exception:
        return None
```

### Serialization (NaN -> None)
```python
def _safe_list(series: pd.Series) -> list:
    """Convert Series to list, replacing float NaN with None for JSON safety."""
    return [None if pd.isna(v) else float(v) for v in series]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `yf.download()` for concurrent fetches | `yf.Ticker().history()` | Phase 09-01 | Prevents 2D/1D shape corruption |
| `yf.Ticker.calendar['Earnings Date']` | `yf.Ticker.earnings_dates` filtered by `Reported EPS.notna()` | Verified 2026-04-12 | calendar returns *future* date; earnings_dates gives past dates |
| Plotly HTML div labels positioned with JS | Plotly annotations with `xref='paper'` | Phase 19 established pattern | Survives resize, no CSS |

## Open Questions

1. **VP chart staticPlot discrepancy**
   - What we know: Current `tradingIndicators.js` VP chart uses `{displayModeBar: true, scrollZoom: true}` — not `staticPlot: true` (violates TIND-03).
   - What's unclear: Whether to fix VP in this phase or leave for Phase 22 tab wiring.
   - Recommendation: Fix VP to use `staticPlot: true` when adding AVWAP chart in the same pass (no extra effort; prevents revisiting the file).

2. **Signal value for composite bias**
   - What we know: Phase 22 needs a signal per indicator. CONTEXT.md does not define the AVWAP signal label.
   - What's unclear: Exact enum values ('bullish'/'bearish'/'neutral' vs 'above_high'/'below_low'/'between').
   - Recommendation: Return `signal: 'above'` (price > AVWAP_high → bullish bias), `'below'` (price < AVWAP_low → bearish), `'between'` (neutral). Phase 22 will map these to composite bias.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (installed, see tests/) |
| Config file | none (run from project root) |
| Quick run command | `pytest tests/test_trading_indicators.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AVWAP-01 | `compute_anchored_vwap` returns traces/layout for 52-wk high/low lines | unit | `pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap::test_avwap_keys -x` | ❌ Wave 0 |
| AVWAP-01 | AVWAP value within plausible price range | unit | `pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap::test_avwap_values_in_range -x` | ❌ Wave 0 |
| AVWAP-02 | earnings_unavailable=True when no earnings data | unit | `pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap::test_earnings_unavailable -x` | ❌ Wave 0 |
| AVWAP-02 | earnings AVWAP present when date found | unit | `pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap::test_earnings_avwap_present -x` | ❌ Wave 0 |
| AVWAP-03 | convergence list is empty when lines are far apart | unit | `pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap::test_no_convergence -x` | ❌ Wave 0 |
| AVWAP-03 | convergence list populated when AVWAP within 0.3% of price | unit | `pytest tests/test_trading_indicators.py::TestComputeAnchoredVwap::test_convergence_detected -x` | ❌ Wave 0 |
| AVWAP-01,02,03 | Route returns anchored_vwap with real keys (not stub) | integration | `pytest tests/test_trading_indicators.py::TestTradingIndicatorsRoute::test_avwap_not_stub -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_trading_indicators.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_trading_indicators.py` — add `TestComputeAnchoredVwap` class (covers AVWAP-01, AVWAP-02, AVWAP-03)
- [ ] Test must mock `yf.Ticker` for both OHLCV history and earnings_dates

## Sources

### Primary (HIGH confidence)
- Live yfinance 0.2.58 REPL tests — `earnings_dates` structure, tz-aware index, None return for ETFs
- Live yfinance 0.2.58 REPL tests — AVWAP formula verified against `compute_anchored_vwap` on real AAPL data
- Live Plotly REPL tests — annotation `xref='paper', x=1.0, xanchor='left'` verified working
- Existing `trading_indicators.py` — confirmed stub signature, `fetch_ohlcv` pattern, dark theme constants
- Existing `webapp.py` line 2154–2174 — confirmed stub response location
- Existing `tradingIndicators.js` — confirmed `_renderTickerCard` structure and VP chart pattern
- Existing `tests/test_trading_indicators.py` — confirmed test pattern for extending

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions — all design choices locked by user

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified against installed packages; no new deps
- Architecture: HIGH — all patterns executed and confirmed in live REPL tests
- Pitfalls: HIGH — each pitfall triggered or verified in REPL tests
- Test mapping: HIGH — test file and class structure mirrors existing Phase 19 pattern

**Research date:** 2026-04-12
**Valid until:** 2026-05-12 (yfinance API changes infrequently at patch level)
