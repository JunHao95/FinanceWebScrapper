# Domain Pitfalls

**Domain:** Trading Indicators sub-tab — Liquidity Sweep, Order Flow, Anchored VWAP, Volume Profile, Composite Bias
**Researched:** 2026-04-07
**Confidence:** HIGH (derived from indicator mathematics, OHLCV constraints, existing codebase patterns, and Plotly rendering characteristics specific to this system)

---

## Critical Pitfalls

Mistakes that cause misleading signals, silent wrong outputs, or rewrites.

---

### Pitfall 1: Look-Ahead Bias in Swing High/Low Detection (Liquidity Sweep)

**What goes wrong:** The standard n-bar swing detection algorithm marks a candle as a swing high if it is the highest close (or high) among the N bars before AND after it. On historical data this is fine — the "N bars after" are already known. But when this same function is called on live/current data (or the tail of a lookback window), the current bar does not yet have N confirmed bars after it. The swing point is only confirmed N bars later, but the code may flag it as confirmed on the current bar.

**Why it happens:** A typical implementation is:
```python
for i in range(n, len(highs) - n):
    if highs[i] == max(highs[i-n:i+n+1]):
        swing_highs.append(i)
```
When called on data that includes today (`i = len-1-n` to `len-1`), the last `n` bars cannot form confirmed swings — but if the loop boundary is written as `range(n, len(highs))` instead, the last bar is evaluated as a swing high using only past data. The result looks confirmed but isn't.

**Consequences:** A "swept" liquidity zone may be reported as confirmed when the sweep candle is actually the most recent candle — the very candle we are trying to signal on. This is not a display artifact; it means the signal is generated using future information in any backtesting context, and in a live display the swing is not yet confirmed. The composite bias signal will misfire.

**Detection:** Check whether `swing_detection` loop upper bound is `len(data)` (wrong — look-ahead on tail) or `len(data) - n` (correct — only n-confirmed swings).

**Prevention:**
- Enforce `range(n, len(highs) - n)` as the loop range so the last `n` bars are never flagged as swings.
- Treat the most recent n bars as "pending confirmation" — do not include any bar in `swing_highs` or `swing_lows` unless there are at least `n` confirmed bars after it.
- In the UI, display the "last confirmed swing" date separately from the current date. If the last confirmed swing is more than `n` bars old, state "no recent confirmed swing."
- Add a test: fetch 90 days of data, detect swings, then fetch 91 days. No swing index should shift backward on the original 90 bars. If it does, look-ahead is present.

**Phase:** Backend swing detection implementation — validate before wiring to composite signal.

---

### Pitfall 2: "Swept" vs. "Approaching" Liquidity Zones Are Not Distinguished (Liquidity Sweep)

**What goes wrong:** A liquidity sweep is not just the price reaching a prior swing level — it requires a close *beyond* the swing level followed by a reversal. A common implementation only checks whether the current high exceeded the prior swing high, marking it as "swept." But a candle that closes above the swing high and continues higher is a breakout, not a sweep. A sweep requires the close to return below the swing high by candle close (on daily data).

**Why it happens:** The sweep condition check is written as `current_high > prior_swing_high` rather than `current_high > prior_swing_high AND current_close < prior_swing_high`.

**Consequences:** Breakout candles are flagged as sweeps. The signal fires on every momentum breakout and produces false bullish-reversal signals during trending markets. A viewer comparing the chart to price action will immediately see sweep labels on straight-up rallies.

**Prevention:**
- For a bullish sweep (sweep of lows, then reversal): `current_low < prior_swing_low AND current_close > prior_swing_low`.
- For a bearish sweep (sweep of highs, then reversal): `current_high > prior_swing_high AND current_close < prior_swing_high`.
- Display the sweep candle with a distinct label ("Swept High" / "Swept Low") and the prior swing level as a horizontal reference line on the chart, so the user can visually verify the close-back-below condition.

**Phase:** Backend liquidity sweep logic — core correctness check before any UI wiring.

---

### Pitfall 3: Order Flow Proxy Direction Is Ambiguous Without Tick Data (Order Flow)

**What goes wrong:** On daily OHLCV data there is no bid/ask split and no trade direction. The system must use proxy formulas. The most common proxy is the "close location" or a variant: `delta = (close - low) / (high - low) * volume - (high - close) / (high - close) * volume`. When `high == low` (a doji or halted-session bar), this formula produces a division-by-zero or NaN. If NaN propagates unchecked, cumulative delta calculations silently become NaN for all subsequent bars — the entire order flow chart appears empty with no error message.

**Why it happens:** The edge case `high == low` is rare in large-cap US equities but occurs routinely for: newly listed tickers, tickers that hit circuit breakers, halted trading sessions, and any ticker on a day with zero intraday range (theoretical but possible in thin markets). A single NaN in a cumulative sum contaminates all downstream values.

**Consequences:** The order flow panel renders empty (or shows a flat zero line) with no user-facing explanation. The composite bias signal component from order flow defaults to neutral, silently. The user sees nothing and has no idea whether the data is missing or the calculation failed.

**Prevention:**
- Guard against zero range: `delta = ((close - low) / (high - low + 1e-10)) * volume * 2 - volume` — the epsilon avoids division by zero while keeping the formula meaningful.
- After computing any rolling or cumulative series, assert `not np.isnan(series).any()`. If NaN is found, log the offending bar index and replace with forward-fill or zero, then surface a UI warning: "X bars with zero range were estimated as neutral."
- Display the number of bars used and the number of bars where range = 0 in a tooltip or footnote.

**Phase:** Backend order flow calculation — add NaN guard before cumulative sum and divergence logic.

---

### Pitfall 4: Volume Divergence Definition Is Ambiguous — Silent Wrong Signal (Order Flow)

**What goes wrong:** "Divergence" between price and order flow can mean (a) price makes a new high while cumulative delta is declining, (b) price makes a new high while the current bar's delta is negative, or (c) the rolling correlation of price and delta has changed sign. These produce very different signals on the same data. Implementing (b) is the easiest but most noisy; it will flag nearly every red bar on an up-trending stock as "divergence." The signal name "divergence" will be misleading to any trader who expects the classic definition (a).

**Why it happens:** The implementation defaults to the simplest per-bar check rather than the multi-bar divergence structure that the indicator name implies.

**Consequences:** The divergence signal fires on a large fraction of candles, diluting its value. The composite bias score will be noisy. A user familiar with order flow concepts will immediately notice that "divergence" fires on every single down-close day.

**Prevention:**
- Use rolling window divergence: detect whether price made a N-bar high while cumulative delta over the same N bars is below its N-bar average. Window size should be parameterised (default: 5 bars).
- Clearly document and label which definition is in use in the UI tooltip: "Divergence: price N-bar high with declining cumulative delta over same window."
- Cap divergence signals at no more than one per lookback/5 (i.e., for a 90-day lookback, at most 18 divergence flags). If the algorithm produces more, the definition is too loose.

**Phase:** Order flow divergence definition — design decision needed before implementation.

---

### Pitfall 5: Anchored VWAP With Insufficient History Produces Meaningless or Misleading Values (Anchored VWAP)

**What goes wrong:** Anchored VWAP is only meaningful when sufficient bars exist after the anchor. If the user requests a 30-day lookback and the anchor is the 52-week high, but the 52-week high occurred 200 trading days ago, the VWAP anchor date is outside the lookback window — no data is fetched for the anchor period, the VWAP starts at an arbitrary point near the left edge of the chart, and it purports to represent "VWAP since 52-week high" when it actually represents "VWAP since the start of the downloaded data."

This produces two sub-failures:
1. **Silent truncation:** The anchor date is older than the fetched data; the VWAP is computed from the oldest available bar, not the true anchor.
2. **Missing anchor entirely:** The 52-week high is within the fetched window but falls on a day with no volume data (e.g., a split-adjusted data artifact), causing the anchor to silently shift to the next available bar.

**Why it happens:** The data fetch uses the user-selected lookback (`30/90/180/365 days`) rather than fetching from the anchor date regardless of lookback. The anchor date is derived from yfinance `history()` which is already truncated to the lookback window.

**Consequences:** VWAP from a truncated anchor drifts toward the current close because it accumulates fewer bars. It gives the appearance of a strong support/resistance level that doesn't actually reflect volume-weighted price since the true anchor. The signal label says "VWAP from 52-wk High" but the number is wrong.

**Prevention:**
- Always fetch data from `max(anchor_date - 5 trading days, lookback_start_date)` as a minimum, but for VWAP anchors specifically, fetch from `min(anchor_date, today - 365)` regardless of the user's lookback selection. The chart can still display only the selected lookback window, but VWAP computation must start from the true anchor.
- After computing VWAP, emit metadata: `{"anchor_date": "2024-03-15", "anchor_bar_index": 47, "bars_used_for_vwap": 183}`. If `anchor_bar_index == 0` (anchor fell on or before the first downloaded bar), surface a warning: "52-wk High anchor pre-dates available history. VWAP starts from earliest available date."
- If the anchor date cannot be found in the fetched data (because it predates the history), explicitly state "Anchor outside selected window" rather than silently computing from an incorrect starting point.

**Phase:** Backend VWAP anchor resolution — requires separate data fetch logic before computation.

---

### Pitfall 6: Multiple VWAP Lines Collide Visually and All Show As Identical Near Current Price (Anchored VWAP)

**What goes wrong:** When three VWAP anchors (52-wk high, 52-wk low, earnings date) are all plotted on the same Plotly chart with a 30-day lookback, all three VWAPs will converge toward the current close price at the right edge of the chart. This is mathematically expected — VWAP computed over the last 30 bars will accumulate similarly regardless of which anchor it started from (if the anchor predates the window). The chart shows three nearly-identical lines on top of the price series, which looks broken to the user.

**Why it happens:** The convergence is a feature of VWAP mathematics when the anchor is far in the past relative to the chart window. But the UI renders all three lines without explaining the convergence.

**Consequences:** The user sees three overlapping VWAP lines, cannot distinguish them, and concludes the implementation is wrong or the chart is broken. The visual adds noise rather than insight.

**Prevention:**
- Differentiate lines with distinct colors and dashed/dotted/solid styles, not just color alone.
- Add a `distance_from_vwap_pct` label next to each line at the right edge: "52wk High VWAP: $183.40 (+2.1%)".
- If two VWAP lines are within 0.3% of each other at the current price, show a note: "52-wk High and Earnings VWAPs are converged — treating as single level." This turns a visual bug into an informative observation.
- For the 30-day lookback, hide anchors whose date precedes the lookback window start entirely, with a label: "Earnings VWAP: anchor outside 30-day window."

**Phase:** Frontend VWAP chart rendering — line differentiation and convergence handling.

---

### Pitfall 7: Volume Profile Bin Count Sensitivity — Results Differ Dramatically Across Bin Counts (Volume Profile)

**What goes wrong:** The Point of Control (POC) — the price level with the highest traded volume — is highly sensitive to bin count. With 20 bins on a $50 price range, each bin covers $2.50. With 100 bins, each covers $0.50. The POC can shift by several dollars depending on bin count because volume concentrations look different at different resolutions. A 30-day POC at 20 bins might be $183 but at 100 bins might be $185. Neither is "wrong" but they are not equivalent, and presenting one without context misleads the user.

**Why it happens:** Bin count is often hardcoded to a round number. On a 30-day lookback the price range may be $20 (for a $200 stock) — a fixed 50 bins gives $0.40/bin which is reasonable. On a 365-day lookback the range may be $80 — the same 50 bins gives $1.60/bin, dramatically coarser.

**Consequences:** POC/VAH/VAL levels jump when the user changes the lookback from 30 to 90 days — not because the market structure changed, but because the bin width changed. This looks like a bug.

**Prevention:**
- Use adaptive bin count: `bins = max(20, min(100, int((price_range / current_price) * 500)))`. This keeps bin width at approximately 0.2% of current price regardless of range.
- Document the bin width in the output: `{"poc": 183.40, "bin_width_usd": 0.42, "n_bins": 47}`.
- Display the bin width visually: the horizontal histogram bars should visually represent the price granularity, not be invisible thin lines.
- For the showcase: fix at 50 bins with a note in the UI — "Volume Profile uses 50 price bins." Consistency across lookbacks is more important for a demo than adaptive precision.

**Phase:** Backend volume profile computation — bin count decision must be made before any validation.

---

### Pitfall 8: POC/VAH/VAL Are Rendered as Points, Not Zones — Misleads Users (Volume Profile)

**What goes wrong:** POC, VAH, and VAL are typically displayed as horizontal lines on a price chart. Plotly `add_shape` or a scatter trace at a single y-value renders these as hair-thin lines. At normal zoom levels on a 90-day daily chart, these lines are essentially invisible against candlestick bars. Users cannot see the levels that are supposed to be the primary output of the indicator.

**Why it happens:** The natural implementation draws a horizontal line at `y = poc_price` with `line_width=1`, which renders at 1-2 pixels in most browsers.

**Consequences:** The Volume Profile panel appears to have no visible output. A recruiter who doesn't know to zoom in will see only the histogram and wonder why there are no level markers.

**Prevention:**
- Use filled rectangles (`add_shape` with `type='rect'`, height = ±0.25% of the POC price) rather than lines. This gives the level visual thickness.
- Alternatively, use Plotly `add_hline` with `line_width=2` and `annotation_text="POC"` — the annotation ensures the level is always labeled.
- Use distinct colors: POC = red, VAH = green, VAL = blue, consistent across the app.
- Ensure the horizontal histogram is rendered as a separate Plotly subplot axis (not overlaid on the price axis) — overlaying a horizontal histogram on a vertical price axis is a common Plotly layout mistake that causes the histogram to appear rotated incorrectly.

**Phase:** Frontend Volume Profile chart layout — Plotly subplot configuration.

---

### Pitfall 9: Horizontal Volume Histogram Requires a Second X-Axis, Not a Second Y-Axis (Volume Profile)

**What goes wrong:** A volume profile histogram is a horizontal bar chart where price is on the Y axis and volume is on the X axis. Rendering it alongside a price chart in the same Plotly subplot is non-trivial because the price chart uses date as X and price as Y. The naive approach adds volume as a second Y-axis trace, producing a vertical bar chart (volume vs. date) rather than a horizontal histogram (price vs. volume).

**Why it happens:** Plotly's default multi-axis support is `yaxis2` for a second Y axis. Adding a trace with `yaxis='y2'` and expecting it to behave as a horizontal histogram requires explicit use of `type='bar'` with `orientation='h'` and a dedicated `xaxis2` pointing right-to-left. This is non-obvious and undocumented in most tutorial examples.

**Consequences:** The volume profile appears as a standard vertical volume bar chart at the bottom of the price chart — indistinguishable from the regular volume subplot every charting package shows. The "horizontal histogram" feature of the volume profile (which is its defining visual) is absent.

**Prevention:**
- Render the volume profile as a completely separate Plotly subplot using `make_subplots(rows=1, cols=2, column_widths=[0.75, 0.25])`. Price+VWAP on col 1, horizontal histogram on col 2 with `orientation='h'`.
- Pass `shared_yaxes=True` to `make_subplots` so the price level on the histogram aligns with the price axis on the chart.
- In the 2×2 grid layout, the Volume Profile quadrant occupies one full cell — use `make_subplots` within that cell or pre-render the combined chart as a single Plotly figure.
- Test alignment: the POC bar in the histogram must fall at exactly the same Y coordinate as the POC horizontal line on the price chart. Misalignment by even one bin is visually obvious.

**Phase:** Volume Profile Plotly layout — this is a layout architecture decision, not a minor styling fix.

---

### Pitfall 10: Composite Bias Signal Is Overconfident When Indicators Are Computed on the Same Underlying Data (Composite Signal)

**What goes wrong:** The composite bias is presented as "Bullish (3/4 indicators agree)" with the implication that independent evidence is converging. However, Liquidity Sweep, Order Flow, Anchored VWAP, and Volume Profile are all derived from the same OHLCV data for the same ticker over the same lookback window. Their signals are not independent: a strong uptrend will push close > VWAP (VWAP bullish), concentrate volume at higher prices (POC above midpoint = bullish), reduce sell-delta proxies (order flow bullish), and eliminate recent swept lows (liquidity sweep bullish). All four indicators agree in strong trends for the same mechanical reason — not because four separate information sources confirm the same view.

**Why it happens:** The composite signal correctly aggregates the four sub-scores but incorrectly treats agreement as independent confirmation. The design of the composite bias scoring does not account for shared-factor exposure.

**Consequences:** The composite signal will show 4/4 bullish on any strongly trending stock and 4/4 bearish on any strongly declining stock, almost always. This makes the signal a lagging trend-follower dressed up as a multi-indicator confirmation system. A viewer who tests it on a few tickers will notice it is always 4/4 in whatever direction the trend has been going.

**Prevention:**
- Do not present composite agreement as "probability" or "confidence." Instead label it: "Trend-following bias: X/4 indicators in agreement."
- Add an explicit caveat in the UI: "All indicators are computed from the same daily OHLCV data. Agreement does not imply independent confirmation."
- Consider including a counter-signal metric: compute how many indicators are at an extreme (e.g., VWAP distance > 2 standard deviations) and flag "potential mean reversion signal" when all four are at extremes in the same direction.
- The composite signal is appropriate for demonstrating indicator mechanics; frame it as a teaching tool, not a trading system.

**Phase:** Composite signal design and UI copy — framing decision needed before frontend implementation.

---

### Pitfall 11: Composite Bias Score Defaults to Neutral When Any Indicator Errors, Masking the Failure (Composite Signal)

**What goes wrong:** If Volume Profile computation fails for a ticker (e.g., insufficient data, zero-volume days, yfinance returning a partial series), the composite signal computation receives `None` or an exception for that indicator's score. A defensive implementation replaces the missing score with 0 (neutral). The composite then shows "2/3 bullish" rather than "3/4 bullish" — but does not tell the user that one indicator failed to compute. The composite bias card renders without any warning.

**Why it happens:** Error handling in the backend returns `{"bias": "neutral", "score": 0}` for failed sub-indicators so that the frontend always receives a response. The aggregation logic in the composite function counts non-None scores and computes the ratio, silently ignoring failures.

**Consequences:** A user who notices the composite says "2/3" instead of "3/4" has no way to know whether this means one indicator genuinely disagrees or one indicator errored. For a showcase demo, a mysteriously silent failure is worse than a visible error — it looks like the code is hiding something.

**Prevention:**
- Return a structured sub-indicator status in the API response: `{"sub_indicators": {"liquidity_sweep": {"bias": "bullish", "ok": true}, "volume_profile": {"bias": null, "ok": false, "reason": "Insufficient data: 8 bars"}, ...}}`.
- In the frontend composite card, render a distinct "unavailable" state for failed sub-indicators (e.g., grey dashes instead of a color-coded pill).
- The composite ratio denominator should only count indicators where `ok == true`. If fewer than 3 of 4 indicators succeed, show a warning: "Composite based on X/4 indicators (Y unavailable)."

**Phase:** Backend error propagation and frontend composite card rendering — must be designed as a system, not patched after the fact.

---

### Pitfall 12: 2x2 Plotly Grid Per Ticker Creates DOM and Memory Pressure for Multi-Ticker Analysis (Plotly Performance)

**What goes wrong:** The existing analysis flow scrapes multiple tickers (the user enters 2-5 typically). For each ticker, a 2×2 Plotly grid is rendered: 4 subplots per ticker, 4 traces minimum per subplot = 16-20 Plotly traces per ticker. For 5 tickers, this is 80-100 traces and 10 separate `Plotly.newPlot` calls writing to 10 separate DOM containers. Plotly.js holds all trace data in JavaScript heap memory for interactive hover/zoom. On a mid-range laptop, this can consume 400-600 MB of RAM, making the browser tab noticeably sluggish or triggering a tab crash.

**Why it happens:** The existing modules (DCF, Health Score, Peer Comparison) each render one small card per ticker. The trading indicators module multiplies the Plotly footprint by a factor of 4-8 per ticker compared to any existing module.

**Consequences:** The tab becomes unresponsive after rendering 3-4 tickers. Scrolling through the analysis results page lags. In the worst case, the browser tab crashes and all prior analysis results are lost. This is the kind of demo failure that is visible and embarrassing.

**Prevention:**
- Use `Plotly.react()` instead of `Plotly.newPlot()` for any re-render (e.g., when the user changes lookback). `Plotly.react()` diffs traces in place and avoids full DOM teardown/rebuild.
- Limit interactive mode: set `config: {staticPlot: true}` for all 4 subplots in the grid. This disables hover/zoom on the indicators grid (which are analytical reference charts, not interactive exploration tools). Static plots use dramatically less memory — approximately 10x reduction.
- Implement deferred rendering: only render the trading indicators panel for the currently-visible ticker card. Lazy-render when the user scrolls to a ticker. A `IntersectionObserver` on the chart container div is the correct mechanism.
- Cap the number of rendered ticker grids at 5. If more tickers are present, show a "Show Trading Indicators" button per ticker rather than auto-rendering all of them.

**Phase:** Frontend rendering architecture — must be designed before any `Plotly.newPlot` calls are written.

---

### Pitfall 13: yfinance Returns Adjusted Close But Raw OHLCV for Volume Profile — Price/Volume Mismatch (Data Layer)

**What goes wrong:** When yfinance `Ticker.history()` is called with `auto_adjust=True` (the default since yfinance 0.2.x), it returns split- and dividend-adjusted Close, Open, High, Low values. Volume is also adjusted (scaled by the inverse split ratio). However, the Volume Profile computation accumulates volume at each price level using the raw price values from the OHLCV frame. If some modules in the existing codebase fetch with `auto_adjust=False` (for other reasons), while the Volume Profile module fetches with `auto_adjust=True`, the POC price level will correspond to the adjusted price but may be labeled against the unadjusted price axis from another chart on the same panel.

**Why it happens:** yfinance's `auto_adjust` default changed in version 0.2.x. Existing code in `technical_indicators.py` and `regime_detection.py` may use different default or explicit settings, creating inconsistency within the same codebase.

**Prevention:**
- Establish one canonical data fetching function for all Trading Indicators modules: `fetch_ohlcv(ticker, period_days, auto_adjust=True)`. All four indicator backends call this single function — never call yfinance directly in individual indicator modules.
- Assert consistency: `assert df.index.tzinfo is None or df.index.tz is not None` to catch timezone-naive vs. timezone-aware index mismatches (a common yfinance 0.2.x issue).
- Document the adjustment policy in a module-level comment: "All prices are split/dividend-adjusted. Volume is proportionally adjusted. Levels are expressed in adjusted-price terms."

**Phase:** Data fetch abstraction layer — must be built before any individual indicator module.

---

### Pitfall 14: Lookback Window Changes Don't Invalidate Cached Anchor Dates (Anchored VWAP)

**What goes wrong:** The 52-week high and 52-week low anchor dates are computed from a 365-day window. If the user runs analysis with a 365-day lookback, the 52-week high is correctly found. The user then changes the lookback to 30 days and re-runs. Now the 52-week high computed from the 365-day window is reused (because it was cached from the prior run or passed as a parameter), but the OHLCV data available for VWAP computation only covers 30 days. The anchor predates the data, triggering the silent truncation described in Pitfall 5 — but now it happens on a user-initiated re-run, not just on the first call.

**Why it happens:** The anchor date lookup and the OHLCV fetch may be called with different lookback parameters if the frontend passes them as separate inputs, or if the backend memoizes the 52-week high lookup independently.

**Prevention:**
- The anchor date computation must always use the maximum lookback (365 days) regardless of the user's selected display lookback. The API endpoint should accept `display_lookback_days` (30/90/180/365) separately from the data fetch period, which is always 365 days for anchor resolution.
- Never cache anchor dates between requests with different display_lookback values.
- In the response, include `anchor_within_display_window: true/false` so the frontend can display the appropriate warning.

**Phase:** Backend API parameter design — requires explicit lookback separation at the route level.

---

## Moderate Pitfalls

---

### Pitfall 15: Imbalance Candle Detection Is Undefined Without an Explicit Threshold (Order Flow)

**What goes wrong:** An "imbalance candle" has no universally accepted quantitative definition. Common definitions include: (a) candle body > 70% of total range, (b) close in top/bottom 25% of range with above-average volume, (c) the candle's body "gaps" into the prior candle's body (the ICT definition). Implementing one without documenting which definition was used leads to a showcase where a viewer asks "what counts as an imbalance?" and the answer is buried in backend code.

**Prevention:**
- Choose one definition (recommended: body > 70% of high-low range with volume > 1.2× 20-day average volume) and display it as a tooltip: "Imbalance: body spans >70% of candle range with above-average volume."
- The threshold (70%, 1.2×) should be a named constant, not a magic number.

**Phase:** Order flow imbalance definition — document the decision before implementation.

---

### Pitfall 16: Swing Detection N-Bar Parameter Has No Validated Default (Liquidity Sweep)

**What goes wrong:** The n-bar lookback for swing detection (how many bars on each side of a local high/low must be lower) has no standard value. Common values range from 2 to 10. On daily OHLCV data: n=2 produces hundreds of micro-swings; n=10 produces very few, and on a 30-day lookback may produce zero confirmed swings (since the last 10 bars are excluded from confirmation). If the default n is too large relative to the lookback, the UI shows "No liquidity sweeps detected" for most tickers, making the feature appear broken.

**Prevention:**
- Default to n=3 for daily data with lookbacks of 30-90 days. For 180-365 day lookbacks, n=5 is more appropriate.
- Make n adaptive: `n = max(2, min(5, lookback_days // 30))`.
- If zero swings are detected, display "No confirmed swing highs/lows in selected window (n=3)" rather than a blank chart.
- Show the swing count in the indicator metadata: "4 swing highs, 3 swing lows detected."

**Phase:** Swing detection parameter tuning — validate defaults against AAPL/SPY over multiple lookback windows.

---

### Pitfall 17: Volume Profile Uses "Close Price" for Volume Attribution Instead of "Bar Midpoint" (Volume Profile)

**What goes wrong:** To build a volume profile from OHLCV daily data, volume must be attributed to a price level. Two approaches: (a) attribute all bar volume to the close price, (b) attribute volume uniformly across the bar's high-low range. Approach (a) is simpler but produces artificial spikes at round-number close prices (e.g., a stock that closed at $190.00, $190.50, $190.25 three days in a row will show a massive volume spike at $190 even if price traded across a $5 range each day). Approach (b) better represents the actual traded range.

**Prevention:**
- Use approach (b): distribute volume uniformly across the high-low range by incrementing all bins between `low_bin` and `high_bin` by `volume / n_bins_in_range`. This is more representative and smoother.
- If approach (a) is used for simplicity, note it in the UI: "Volume attributed to daily close price (simplified). Actual traded range: $X–$Y."

**Phase:** Volume profile bin attribution logic — decision affects POC/VAH/VAL accuracy.

---

## Minor Pitfalls

---

### Pitfall 18: The 2×2 Grid Quad Labels Are Ambiguous Without Per-Chart Titles

**What goes wrong:** A 2×2 Plotly grid with four subplots is visually complex. If the only title is the ticker symbol at the top, a viewer needs to read the axis labels to determine which quadrant is Liquidity Sweep vs. Volume Profile. In a demo context where reviewers are scanning quickly, this creates unnecessary cognitive load.

**Prevention:**
- Add a `title` to each subplot in `make_subplots(subplot_titles=["Liquidity Sweep", "Order Flow Delta", "Anchored VWAP", "Volume Profile"])`.
- These become the `annotations` in the Plotly layout and appear above each quadrant automatically.

**Phase:** Frontend grid layout — one-line fix in `make_subplots` call.

---

### Pitfall 19: Earnings Date Anchor Is Unavailable for Many Tickers (Anchored VWAP)

**What goes wrong:** The auto-anchor to earnings date requires fetching the most recent earnings date from yfinance (`Ticker.calendar`). For many tickers (ETFs, non-US ADRs, recently listed companies), `.calendar` returns an empty DataFrame or raises a KeyError. If the backend raises an unhandled exception here, the entire VWAP computation for that ticker fails, including the 52-wk high/low anchors that had no issue.

**Prevention:**
- Wrap each anchor date lookup in a try/except independently. If the earnings anchor is unavailable, skip it gracefully and render only the 52-wk high/low VWAPs.
- Return `{"earnings_anchor": null, "earnings_anchor_reason": "Not available for ETFs"}` in the API response so the frontend can label the missing line appropriately rather than just not rendering it.

**Phase:** Backend anchor date resolution — independent error handling per anchor type.

---

### Pitfall 20: Composite Signal Card Duplicates the Per-Indicator Signals Without Adding New Information

**What goes wrong:** If the composite bias card says "Bullish" and the four individual panels each already show their own bullish/bearish label, the composite card adds no new information. It becomes visual clutter. A viewer who sees "Bullish (3/4)" and then looks at the four charts to find which one is bearish has to cross-reference manually.

**Prevention:**
- The composite card must identify *which* indicator is the dissenting signal: "Bearish divergence: Volume Profile is bearish while the other three indicators are bullish. POC at $183 is below current price $189."
- This turns the composite from a dumb aggregation into an interpretive layer with actual insight value.

**Phase:** Composite card design — define the card's purpose before building the UI component.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| Swing detection backend | Look-ahead bias on tail bars (Pitfall 1) | Loop bound must be `len - n`, not `len`; add regression test |
| Sweep signal definition | Breakouts flagged as sweeps (Pitfall 2) | Require close-back-below condition before flagging sweep |
| Order flow NaN propagation | Zero high-low range division (Pitfall 3) | Add epsilon guard before cumulative delta; assert no NaN |
| Order flow divergence | Ambiguous definition fires on every red bar (Pitfall 4) | Define and document rolling-window divergence; cap signal frequency |
| VWAP anchor resolution | Anchor predates fetched data, silent truncation (Pitfall 5) | Always fetch 365 days for anchor resolution regardless of display lookback |
| VWAP anchor resolution | Lookback change reuses stale anchor (Pitfall 14) | Separate `display_lookback` from `data_fetch_period` at API design level |
| VWAP chart rendering | Three converging lines look broken (Pitfall 6) | Distinct line styles + right-edge labels + convergence warning |
| Volume profile bin count | POC shifts with lookback, looks like bug (Pitfall 7) | Adaptive bin width or fixed bins with documentation |
| Volume profile chart | POC/VAH/VAL invisible as hairline (Pitfall 8) | Use filled rectangles or `add_hline` with annotation |
| Volume profile chart | Horizontal histogram rendered as vertical (Pitfall 9) | Use `make_subplots` with `shared_yaxes=True`, `orientation='h'` |
| Composite signal | False multi-source confidence (Pitfall 10) | Frame as "trend-following bias"; add extreme-reading counter-signal |
| Composite signal | Silent indicator failure masked as neutral (Pitfall 11) | Structured sub-indicator status in API response; denominator tracks availability |
| Multi-ticker rendering | DOM/memory pressure from 80+ Plotly traces (Pitfall 12) | `staticPlot: true` + lazy render + cap at 5 tickers |
| Data fetch layer | Adjusted/unadjusted price mismatch (Pitfall 13) | Single canonical fetch function; explicit `auto_adjust=True` everywhere |
| Earnings anchor | Unhandled KeyError crashes all VWAP (Pitfall 19) | Per-anchor try/except; return null anchor with reason field |

---

## Sources

- Direct code review: `src/indicators/technical_indicators.py`, `static/js/stochasticModels.js`, `static/js/analyticsRenderer.js`, `webapp.py`
- Existing PITFALLS.md (prior milestone) — patterns: silent NaN propagation (Pitfall 3 here mirrors yfinance partial data Pitfall 12 prior), look-ahead (mirrors HMM smoothed_probs Pitfall 9 prior)
- Plotly.js documentation on `make_subplots`, `shared_yaxes`, `staticPlot`, `Plotly.react()` — configuration patterns for multi-panel performance
- OHLCV order flow proxy literature: Corwin & Schultz (2012) high-low spread estimator; Easley, Lopez de Prado & O'Hara (2012) VPIN — basis for understanding daily-data limitations of order flow proxies
- yfinance 0.2.x changelog — `auto_adjust=True` default change and `.calendar` DataFrame structure
- Volume Profile construction methodology: standard TPO/fixed range volume profile literature (CME Group education materials)
- Confidence: HIGH for Plotly/data layer pitfalls (direct code inspection); HIGH for indicator math pitfalls (domain expertise + standard references); MEDIUM for exact yfinance version behavior (training data knowledge, not live verification)
