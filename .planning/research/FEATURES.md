# Feature Landscape — v2.2 Trading Indicators Sub-Tab

**Domain:** MFE Showcase Web App — Trading Indicators (Liquidity Sweep, Order Flow, Anchored VWAP, Volume Profile)
**Researched:** 2026-04-07
**Confidence:** HIGH for algorithm definitions (well-established quant finance; independent of external sources). MEDIUM for edge-case handling (pragmatic recommendations from training knowledge; no external verification available in this session).

---

## Context

This FEATURES.md replaces the prior entry which covered Stochastic Models + ML-in-Finance. The v2.2 milestone adds a **Trading Indicators sub-tab** inside the existing "Analysis Results" deep-analysis group per ticker. The sub-tab renders a 2×2 grid of four indicator panels — Liquidity Sweep, Order Flow, Anchored VWAP, Volume Profile — plus a composite Bullish/Bearish/Neutral signal with a one-line rationale. All computation runs on **daily OHLCV data** fetched via `yfinance`. No tick data, no Level 2, no real-time feed.

### Data available from existing stack

The existing `TechnicalIndicators.get_historical_data(ticker, days)` returns a pandas DataFrame with columns: `open`, `high`, `low`, `close`, `volume` indexed by date (daily bars). This is the only OHLCV source needed for all four indicators. The existing `yf.Ticker(ticker).history(...)` call (as used in regime detection) can also fetch `fiftyTwoWeekHigh`, `fiftyTwoWeekLow`, and `calendar` (next earnings date) from `yf.Ticker(ticker).info` and `yf.Ticker(ticker).calendar`. No new data sources required.

---

## Data Source Dependency Matrix

| Indicator | Requires | Source | Tick Data? |
|-----------|----------|--------|-----------|
| Liquidity Sweep | OHLCV daily, lookback window | yfinance history | NO |
| Order Flow (delta bar) | OHLCV daily (Close, High, Low, Volume) | yfinance history | NO — approximation |
| Order Flow (divergence flag) | OHLCV daily | yfinance history | NO |
| Order Flow (imbalance candle) | OHLCV daily | yfinance history | NO |
| Anchored VWAP | OHLCV daily, anchor date | yfinance history | NO — daily approximation |
| VWAP 52-wk anchors | 52-wk high/low dates | yfinance history argmax/argmin | NO |
| VWAP earnings anchor | Last earnings date | yf.Ticker.calendar or yf.Ticker.info | NO |
| Volume Profile | OHLCV daily, price bins | yfinance history | NO — daily approximation |

**Critical quality gate finding:** All four indicators are achievable with daily OHLCV. The results are approximations of their intraday equivalents, which is fully acceptable for a showcase/educational app. This is the standard approach for daily-resolution implementations in academic and open-source quant tools (e.g., `pandas-ta`, `vectorbt`). No indicator in scope requires tick data or intraday bars.

---

## Indicator Algorithms — Precise Definitions

### 1. Liquidity Sweep

**Concept:** A liquidity sweep occurs when price briefly violates a prior swing high or swing low (sweeping the stop-loss orders clustered there) before reversing. The detection algorithm identifies these "false breakouts" and labels them as Bullish Sweep (price swept below a swing low then closed back above it) or Bearish Sweep (price swept above a swing high then closed back below it).

**Algorithm (daily bars):**

Step 1 — Swing detection:
- A **swing high** at bar `i` is defined as: `high[i] > high[i-n]` AND `high[i] > high[i+n]` for all 1 ≤ k ≤ n, where `n` is the lookback (default n=5 bars on each side).
- A **swing low** at bar `i` is defined as: `low[i] < low[i-n]` AND `low[i] < low[i+n]` for all 1 ≤ k ≤ n.
- Collect all swing highs and swing lows over the lookback window (default: 60 trading days, configurable via 30/90/180/365 selector).

Step 2 — Sweep detection (scanning forward from each swing):
- **Bullish Sweep** at bar `j > i` where swing low at `i` was detected:
  - `low[j] < swing_low_price[i]` (price dips below the swing low), AND
  - `close[j] > swing_low_price[i]` (close recovers back above it in the same bar).
  - Mark bar `j` as a Bullish Sweep event. Record `sweep_level = swing_low_price[i]`.
- **Bearish Sweep** at bar `j > i` where swing high at `i` was detected:
  - `high[j] > swing_high_price[i]` (price spikes above the swing high), AND
  - `close[j] < swing_high_price[i]` (close reverses back below it in the same bar).
  - Mark bar `j` as a Bearish Sweep event. Record `sweep_level = swing_high_price[i]`.
- A swing level may only be swept once (mark as consumed after first sweep).

Step 3 — Signal:
- Most recent sweep event (within lookback) determines the label: "Bullish Sweep", "Bearish Sweep", or "No Sweep" if none detected.
- Report the sweep level price and the date of the event.

**Output payload:**
```json
{
  "signal": "Bullish Sweep | Bearish Sweep | No Sweep",
  "sweep_level": 182.45,
  "sweep_date": "2026-03-14",
  "swing_highs": [{"date": "...", "price": 190.1}, ...],
  "swing_lows":  [{"date": "...", "price": 178.3}, ...],
  "sweep_events": [{"date": "...", "type": "Bullish", "level": 178.3}]
}
```

**Edge cases:**
- Fewer than `2n + 1` bars available: reduce `n` to `floor(len(df)/4)` or return "Insufficient data".
- Multiple swing levels close together (within 0.5% of each other): merge them into a single zone (use the average price) to avoid noise.
- Gap-down open below swing low that does not recover same-day: this is NOT a sweep (it is a genuine breakdown). Require same-bar close recovery.

**Lookback interaction:** With 30-day lookback, swing detection lookback `n` should reduce to n=3 to ensure enough swings are found. With 180+ days, n=5 to n=10 is appropriate.

---

### 2. Order Flow

Three sub-components, all computable from daily OHLCV.

#### 2a. Buy/Sell Pressure Delta Bar Chart

**Concept:** Approximates the net directional volume pressure per bar using the candle's position within its range as a proxy for buyer vs. seller aggression. This is the daily-bar equivalent of the tick-based Volume Delta used on intraday charts.

**Algorithm:**
```
buy_pressure[i]  = ((close[i] - low[i])  / (high[i] - low[i])) * volume[i]
sell_pressure[i] = ((high[i] - close[i]) / (high[i] - low[i])) * volume[i]
delta[i]         = buy_pressure[i] - sell_pressure[i]
```

Edge case — doji bar where `high == low`: set `buy_pressure = sell_pressure = volume/2`, delta = 0.

**Output:** Array of `delta` values per bar (positive = net buy pressure, negative = net sell pressure), rendered as a bar chart with green bars for positive delta and red bars for negative delta. Also compute and return `cumulative_delta` (running sum of delta over the lookback window) and `delta_signal` ("Positive" if last bar delta > 0, else "Negative").

**Confidence note:** This formula is standard in daily-bar order flow approximation. The academic term is "buying pressure" per Stoll (1989) and is used in `pandas-ta`'s `ebsw` (Elder's Bull and Bear Power) and similar indicators. HIGH confidence.

#### 2b. Price vs. Volume Trend Divergence Flag

**Concept:** Flags when price and volume are moving in opposite directions over a rolling window — a classical warning signal for trend exhaustion.

**Algorithm:**
```
price_trend[i]  = sign of linear regression slope of close[-window:]
volume_trend[i] = sign of linear regression slope of volume[-window:]
divergence      = (price_trend > 0 AND volume_trend < 0) OR (price_trend < 0 AND volume_trend > 0)
```
Default window = 10 bars. Use `numpy.polyfit(range(window), series[-window:], 1)` for slope.

**Output:** Boolean `divergence_flag` + `divergence_type` ("Price up / Volume down" | "Price down / Volume up" | "None") + `price_slope` and `volume_slope` as floats.

**Edge case:** Window larger than available data — clamp window to `min(10, len(df)-1)`.

#### 2c. Imbalance Candle Detection

**Concept:** An imbalance candle is a candle with an abnormally large range AND above-average volume, indicating a sudden surge of directional conviction. These are supply/demand imbalance zones used in Smart Money Concepts (SMC) analysis.

**Algorithm:**
```
candle_range[i] = high[i] - low[i]
avg_range       = mean(candle_range[-lookback:])
avg_volume      = mean(volume[-lookback:])

imbalance[i] = True if:
    candle_range[i] > 1.5 * avg_range   AND
    volume[i]       > 1.5 * avg_volume
```

**Direction of imbalance:**
- Bullish imbalance: `close[i] > open[i]` (up candle)
- Bearish imbalance: `close[i] < open[i]` (down candle)

**Output:** List of imbalance candle events `{date, type: "Bullish|Bearish", range, volume, price_level}` within lookback window. Most recent event determines `imbalance_signal` ("Bullish Imbalance | Bearish Imbalance | None").

**Threshold rationale:** 1.5x multiplier for both range and volume is the community standard. Values below 1.3x generate too much noise on daily bars; values above 2.0x miss most events on lower-volatility names.

---

### 3. Anchored VWAP (AVWAP)

**Concept:** VWAP anchored to a specific historical date rather than recalculated each day from midnight. Price above AVWAP = bullish bias relative to that anchor period; price below = bearish.

**Formula (daily bars):**
```
For bars i = anchor_index to current bar N:
    typical_price[i] = (high[i] + low[i] + close[i]) / 3
    AVWAP[N] = sum(typical_price[i] * volume[i], i=anchor to N)
               / sum(volume[i], i=anchor to N)
```

This is a running weighted average from the anchor date forward. Each AVWAP line is re-evaluated on every new bar but never resets.

**Three auto-anchors (all required):**

1. **52-week high anchor:** `anchor_date = df['high'].idxmax()` within the trailing 252 trading days.
2. **52-week low anchor:** `anchor_date = df['low'].idxmin()` within the trailing 252 trading days.
3. **Last earnings anchor:** Fetch from `yf.Ticker(ticker).calendar` (returns next earnings date). To get the *last* earnings date, use `yf.Ticker(ticker).earnings_dates` (returns a DataFrame of recent earnings dates) and take the most recent past date. If unavailable, fall back to `info.get('lastEarningsDate')` or skip this line with a UI note "Earnings date unavailable".

**Custom anchor input:** Optional date picker in UI. If user provides a date, compute a fourth AVWAP line (labeled "Custom"). Must validate: anchor date must be within available data range; reject future dates.

**Output payload:**
```json
{
  "avwap_52wk_high":  [{"date": "...", "value": 185.2}, ...],
  "avwap_52wk_low":   [{"date": "...", "value": 179.4}, ...],
  "avwap_earnings":   [{"date": "...", "value": 181.8}, ...],
  "avwap_custom":     null,
  "anchor_dates": {
    "52wk_high": "2025-11-03",
    "52wk_low":  "2026-01-13",
    "earnings":  "2026-01-30",
    "custom":    null
  },
  "current_price_vs_avwap": {
    "52wk_high": "above | below",
    "52wk_low":  "above | below",
    "earnings":  "above | below"
  }
}
```

**Edge cases:**
- Anchor date is today (anchor = last bar): AVWAP is just the typical price of that single bar — valid but uninformative. Return the value and note "Single-bar anchor."
- Anchor date has zero volume (trading halt, data gap): skip that bar in the weighted sum (treat as missing).
- 52-wk high and 52-wk low fall on the same date (highly unlikely but possible for illiquid names): merge into one "52-wk extreme" line and label accordingly.
- All AVWAP lines are the same when lookback is very short (e.g., 30 days) and all anchors cluster at the edge of the window: this is a data limitation; render all lines, let user observe convergence.

**Important implementation note:** The AVWAP series should only include bars from the anchor date to the current bar. Do not pad with NaN before the anchor date in the JSON output — only include dates from anchor onward.

---

### 4. Volume Profile

**Concept:** A horizontal histogram showing the distribution of volume traded at each price level over a lookback window. The key levels are:
- **POC (Point of Control):** Price bin with the highest total volume — the "fairest" price where most business was transacted.
- **VAH (Value Area High):** Upper boundary of the range containing 70% of total volume.
- **VAL (Value Area Low):** Lower boundary of the range containing 70% of total volume.

**Algorithm:**

Step 1 — Assign volume to price bins:
```
price_min = min(low[-lookback:])
price_max = max(high[-lookback:])
n_bins    = 50   (fixed; adjustable via constant)
bin_size  = (price_max - price_min) / n_bins
bin_edges = linspace(price_min, price_max, n_bins + 1)

For each bar i:
    # Distribute bar's volume uniformly across all bins it touches
    bins_touched = all bins where bin_low <= high[i] AND bin_high >= low[i]
    n_bins_touched = max(1, len(bins_touched))
    For each bin b in bins_touched:
        volume_profile[b] += volume[i] / n_bins_touched
```

This "volume spread across range" approach is the standard approximation for daily-bar volume profile (since we do not know at which price within the bar's range each trade occurred). It is used by `market_profile` Python library and similar daily-resolution tools.

Step 2 — Find POC:
```
POC_bin_index = argmax(volume_profile)
POC_price     = (bin_edges[POC_bin_index] + bin_edges[POC_bin_index + 1]) / 2
```

Step 3 — Compute Value Area (70% rule):
```
total_volume    = sum(volume_profile)
target_volume   = 0.70 * total_volume
sorted_bins     = sort bins by volume descending

accumulated = 0
value_area_bins = []
for bin in sorted_bins:
    value_area_bins.append(bin)
    accumulated += volume_profile[bin]
    if accumulated >= target_volume:
        break

VAH = max price level in value_area_bins
VAL = min price level in value_area_bins
```

**Output payload:**
```json
{
  "poc_price": 183.50,
  "vah_price": 191.20,
  "val_price": 175.80,
  "bins": [
    {"price_low": 170.0, "price_high": 171.4, "volume": 8450000, "in_value_area": false},
    ...
  ],
  "current_price_vs_poc": "above | below | at",
  "price_in_value_area": true
}
```

**Edge cases:**
- Fewer than 20 bars in lookback: reduce `n_bins` to `max(10, len(df) * 2)` to avoid empty bins.
- Single bar or all bars identical OHLC (e.g., data error): return POC = close, VAH = high, VAL = low.
- Very wide price range with few bars (e.g., high-beta stock over 365-day lookback): the 50-bin fixed approach can create thin bins with zero volume. This is expected behavior — sparse profiles are visually correct.
- `n_bins = 50` is the Plotly-side rendering target. The backend can return 50 or fewer bins; frontend renders as a horizontal bar chart.

---

## Table Stakes

Features a recruiter or quant peer will expect to see present. Missing any of these makes the indicator panel feel half-built.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Swing high/low detection with n-bar lookback | Fundamental to SMC / ICT methodology; any trader expects this as the first step | Low-Med | n=5 bars each side is the community default |
| Bullish/Bearish sweep signal label per ticker | The whole point of the Liquidity Sweep panel — missing this makes it just a chart without insight | Low | Derived from sweep detection algorithm above |
| Sweep level price markers on price chart | Visual anchor for the detected levels — without chart markers the signal has no context | Med | Plotly scatter trace with dashed horizontal lines |
| Buy/sell delta bar chart | Standard order flow visualization; visually distinctive and immediately recognizable | Med | Green/red bar chart using formula above |
| At least one AVWAP line on price chart | AVWAP is meaningless without the price line for comparison; must overlay on price chart | Med | Plotly secondary_y or shared axis |
| POC level displayed numerically and on chart | POC without a price makes the volume profile uninterpretable | Low | Horizontal dashed line on volume profile |
| VAH/VAL shown as a shaded zone | The "Value Area" is conventionally a shaded band between VAL and VAH | Low | Plotly `add_hrect` or shape rectangle |
| Composite Bullish/Bearish/Neutral signal per ticker | The whole-panel synthesis signal — required as the "conclusion" of the sub-tab | Low | Rule-based confluence; see composite logic below |
| Lookback selector (30/90/180/365 days) | Without this the indicators are locked to one time horizon, limiting the demo's interactivity | Low | Frontend dropdown, passes `lookback_days` param to backend |
| 2×2 grid layout per ticker | Specified in milestone scope — missing this makes layout feel unfinished | Low | CSS grid; no new framework needed |

---

## Differentiators

Features that elevate the panel from "correct" to "impressive" for an MFE showcase.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Cumulative delta line overlaid on delta bar chart | Shows the running momentum of order flow, not just individual bars — practitioner-level detail | Low (additive) | Running sum of delta array; plotted as secondary line |
| Three distinct AVWAP lines (52-wk high, low, earnings) simultaneously | Multi-anchor AVWAP is used by institutional traders; showing three at once demonstrates depth | Med | Requires earnings date fetch from yfinance.calendar |
| Price-in-value-area badge on volume profile | "Price is currently inside/outside the value area" is an actionable insight; badge makes it scannable | Low | Computed from current_price vs VAH/VAL |
| Composite signal one-line rationale text | Translating signals to plain English ("Price above all three AVWAPs + Bullish Sweep = Bullish bias") is what separates an MFE quant from a coder | Low-Med | Rule-based if/else on signal flags |
| Volume divergence flag with slope values | Showing the actual slope numbers (not just the flag) adds quantitative credibility | Low (additive) | Already in output payload above |
| Custom AVWAP anchor date input | Lets the recruiter interact with the model — very effective live demo feature | Med | Frontend date picker + validation; backend handles optional param |
| Imbalance candle annotations on price chart | Marking imbalance candles directly on the OHLC chart makes Order Flow tangible | Med | Plotly annotations with arrows or colored bar outlines |

---

## Anti-Features

Features to explicitly NOT build in this milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Intraday VWAP (reset at session open) | Requires intraday bars; yfinance intraday data has 30/60-day limits and is unreliable for showcase | Use Anchored VWAP on daily bars; call it AVWAP explicitly |
| True tick-based order flow (Time & Sales) | Requires exchange tick data feed (not available via yfinance); can't be implemented correctly | Use the (Close-Low)/(High-Low) * Volume approximation and document the approximation in the UI |
| Market Profile (TPO-based) | TPO requires intraday bars; fundamentally different from Volume Profile | Implement Volume Profile (volume-based), not Market Profile (time-based) |
| Footprint charts | Requires bid/ask volume split; not available in daily OHLCV | Use delta approximation chart; label it "Estimated Buy/Sell Pressure" |
| Real-time order book depth | WebSocket + exchange API; zero added value for showcase; infrastructure cost high | Static note: "Live L2 data would replace approximation in production" |
| Smart Money Concepts alert system (automated trade signals) | Not appropriate for a demo; creates appearance of a trade recommendation engine, not an educational tool | Composite signal is labeled "Bias Signal" not "Trade Signal"; add disclaimer |
| Multi-timeframe AVWAP confluence | Requires intraday data for lower timeframes; confuses the daily-bar framing | Document that all AVWAPs are daily-bar anchored; one timeframe only |
| Walk-forward backtest of sweep signals | Backtesting sweep signals requires point-in-time correctness and slippage modeling; out of scope for this milestone | Out of scope; note as potential future enhancement |

---

## Composite Signal Logic

The composite Bullish/Bearish/Neutral signal is rule-based, not ML. It counts the number of bullish vs. bearish sub-signals from the four indicator modules and applies a simple majority rule.

**Sub-signals (one per component):**

| Component | Bullish Sub-Signal | Bearish Sub-Signal |
|-----------|-------------------|-------------------|
| Liquidity Sweep | Most recent sweep is Bullish | Most recent sweep is Bearish |
| Order Flow — Delta | Last bar delta > 0 | Last bar delta < 0 |
| Order Flow — Divergence | No divergence (price up, volume up) | Divergence detected |
| Order Flow — Imbalance | Most recent imbalance is Bullish | Most recent imbalance is Bearish |
| AVWAP | Price above all computed AVWAPs | Price below all computed AVWAPs |
| Volume Profile | Price above POC AND inside value area | Price below POC OR outside value area |

**Scoring:**
```
bullish_count = sum(1 for s in sub_signals if s == "Bullish")
bearish_count = sum(1 for s in sub_signals if s == "Bearish")
total         = bullish_count + bearish_count

if bullish_count / total >= 0.67:  composite = "Bullish"
elif bearish_count / total >= 0.67: composite = "Bearish"
else:                               composite = "Neutral"
```

**Rationale text generation (deterministic template, not LLM):**
- "Bullish: Sweep + Order Flow + AVWAP all align to the upside."
- "Bearish: Price below AVWAP and POC; bearish sweep and imbalance detected."
- "Neutral: Mixed signals — [N] bullish, [M] bearish."

---

## Feature Dependencies

```
Volume Profile
    → requires: OHLCV daily bars (already available from TechnicalIndicators module)

Anchored VWAP — earnings anchor
    → requires: last earnings date from yf.Ticker(ticker).earnings_dates or .calendar
    → NEW data fetch not currently performed by existing scraper

Anchored VWAP — 52-wk anchors
    → requires: OHLCV history >= 252 trading days (1 year)
    → if lookback < 252 days, 52-wk anchors should use max available window

Liquidity Sweep
    → requires: OHLCV daily bars
    → swing detection lookback n must be < lookback_days / 4

Order Flow (all three sub-components)
    → requires: OHLCV daily bars only
    → no additional data dependencies

Composite Signal
    → requires: all four indicator modules to have run successfully
    → degrades gracefully: if one module errors, exclude its sub-signal(s) from count

2×2 grid layout
    → requires: all four indicator modules return their chart data
    → each panel must return Plotly-compatible JSON (layout + traces)
    → follows existing pattern from v2.1 deep analysis group (div.deep-analysis-group-{ticker})
```

---

## MVP Recommendation for v2.2

Prioritize in this order:

1. **Volume Profile** — Simplest correct algorithm; no external data dependencies; high visual impact (horizontal histogram is immediately recognizable). Build this first to establish the Flask endpoint + JS panel pattern for the other three.

2. **Anchored VWAP** — Second simplest; pure math on OHLCV; only dependency is the earnings date fetch which can fall back gracefully. Build without the custom anchor first, add the date picker in a second pass.

3. **Order Flow** — Three sub-components but all use the same OHLCV data; the delta formula is O(n) and requires no external data. Build all three sub-components in one phase since they share a single chart panel.

4. **Liquidity Sweep** — Most complex due to the swing detection + sweep matching logic; build last when the other three panels are stable. Swing detection is the trickiest part (off-by-one errors in the n-bar window are common).

5. **Composite Signal** — Build after all four indicator modules are validated; pure Python rule-based logic, no new data fetches.

Defer to a post-v2.2 phase:
- Custom AVWAP anchor date picker (requires frontend date validation and UI state management; not blocking for the demo)
- Imbalance candle annotations on price chart (additive; doesn't block the core delta bar chart)
- Lookback selector UI wiring (can ship with a hardcoded 90-day default initially, add the selector in a cleanup pass)

---

## Confidence Assessment

| Claim | Confidence | Basis |
|-------|------------|-------|
| All four indicators are achievable from daily OHLCV | HIGH | Standard practice in academic quant finance; confirmed by reviewing yfinance data structure in this codebase |
| AVWAP formula (typical price × volume cumsum) | HIGH | Widely documented; used in pandas-ta, vectorbt, TradingView's built-in VWAP |
| Volume profile 70% value area definition | HIGH | Market Profile theory (J. Peter Steidlmayer, 1980s); 70% is the universally cited threshold |
| Order flow delta formula `(Close-Low)/(High-Low) * Vol` | HIGH | Well-documented daily-bar approximation; consistent with Elder Force Index and Kaufman's Money Flow |
| Swing detection n-bar lookback (n=5) | MEDIUM | Community convention; not formally standardized. TradingView Pine Script default is often n=5 for daily; verify acceptable for this codebase |
| 1.5x threshold for imbalance candle detection | MEDIUM | Practitioner heuristic; not peer-reviewed. Adjust empirically after first implementation |
| Composite signal 2/3 majority threshold | MEDIUM | Author's recommendation; not a standard. Alternative: simple majority (>50%) would be less strict |
| Earnings date available via yf.Ticker.earnings_dates | MEDIUM | Available in yfinance as of v0.2.x; confirm version in requirements.txt as behavior changed in v0.2.28+ |

---

## Sources

All algorithm definitions are based on:
- Market Profile theory (Steidlmayer, 1980s) — Volume Profile POC/VAH/VAL definition
- Elder (1993), "Trading for a Living" — Force Index / buying/selling pressure per bar
- Kaufman (2013), "Trading Systems and Methods" — daily-bar volume analysis approximations
- Smart Money Concepts (ICT methodology, public domain) — liquidity sweep / imbalance candle definitions
- pandas-ta library source (public GitHub) — VWAP implementation reference
- Direct inspection of this codebase: `src/indicators/technical_indicators.py`, `src/scrapers/yahoo_scraper.py`, `webapp.py` route patterns
- Phase 13 plan (`13-01-PLAN.md`) — deep-analysis-group architecture reference

**Confidence note on web search:** WebSearch was not available during this research session. All findings are from training knowledge (cutoff August 2025) and codebase inspection. Algorithm definitions for VWAP, Volume Profile, and Order Flow delta are established mathematical definitions unlikely to have changed. The yfinance API section (earnings_dates field name) carries MEDIUM confidence and should be verified against the installed version.
