# Technology Stack

**Project:** MFE Showcase Web App — v2.2 Trading Indicators Sub-tab
**Researched:** 2026-04-07
**Overall confidence:** HIGH (existing codebase is ground truth; all four indicators are implementable with already-installed numpy/pandas; recommendations derived from direct code analysis and algorithm-level research)

---

## Context: What Already Exists (Do Not Re-research)

The existing codebase has a fully functional `TechnicalIndicators` class in `src/indicators/technical_indicators.py` that already implements:
- Bollinger Bands, RSI, Moving Averages — pure pandas/numpy
- OBV (On-Balance Volume) — manual loop in numpy
- Volume moving averages and signals — pandas rolling()

The existing stack contains everything needed for the four new indicators:

| Layer | Technology | In requirements.txt |
|-------|------------|---------------------|
| Numerical core | numpy >=1.23.0, scipy >=1.9.0 | Yes |
| Data layer | pandas >=1.5.0, yfinance >=0.2.18 | Yes |
| Visualization (frontend) | Plotly.js via CDN | Yes (loaded in templates) |
| Backend runtime | Flask >=2.3.0, gunicorn 21.2.0 | Yes |

---

## Verdict: Zero New Backend Dependencies Required

All four indicators — Volume Profile, Anchored VWAP, Liquidity Sweep, and Order Flow — are implementable using:

```
numpy (already installed)
pandas (already installed)
```

No new packages. No requirements.txt changes. This aligns with the existing codebase's established pattern of hand-rolling indicators rather than using black-box libraries.

---

## Per-Indicator Implementation Analysis

### 1. Volume Profile (POC / VAH / VAL + Histogram)

**What it needs:** Bin OHLCV data into N price levels, sum volume per bin, find the bin with max volume (POC = Point of Control), find upper and lower bounds of bins containing 70% of total volume (VAH/VAL).

**Implementation with pandas/numpy only:**
```python
# Price range into bins
price_range = df['close'].agg(['min', 'max'])
bins = np.linspace(price_range['min'], price_range['max'], num_bins + 1)
df['price_bin'] = pd.cut(df['close'], bins=bins)
volume_profile = df.groupby('price_bin')['volume'].sum()

# POC = bin with most volume
poc_bin = volume_profile.idxmax()

# VAH/VAL = 70% value area
sorted_by_vol = volume_profile.sort_values(ascending=False)
cumsum = sorted_by_vol.cumsum()
value_area_bins = sorted_by_vol[cumsum <= 0.70 * volume_profile.sum()].index
vah = max(b.right for b in value_area_bins)
val = min(b.left for b in value_area_bins)
```

**Visualization:** Plotly horizontal bar chart (barh equivalent) rendered as a subplot alongside the price candlestick. `go.Bar(orientation='h', x=volumes, y=price_levels)`.

**Confidence:** HIGH — this is standard histogram math, no domain library required.

---

### 2. Anchored VWAP (Multiple Anchor Points)

**What it needs:** For each anchor date, compute cumulative (price × volume) / cumulative volume from that date forward to the most recent bar.

**Implementation with pandas only:**
```python
def anchored_vwap(df, anchor_date):
    """df must have columns: open, high, low, close, volume, indexed by date."""
    subset = df.loc[anchor_date:]
    typical_price = (subset['high'] + subset['low'] + subset['close']) / 3
    cum_tp_vol = (typical_price * subset['volume']).cumsum()
    cum_vol = subset['volume'].cumsum()
    return cum_tp_vol / cum_vol  # returns a Series indexed by date
```

**Auto-anchor points to compute:**
- 52-week high date: `df['high'].idxmax()` over trailing 252 trading days
- 52-week low date: `df['low'].idxmin()` over trailing 252 trading days
- Most recent earnings date: yfinance `Ticker.calendar` or `Ticker.earnings_dates` — already available via existing yf import

**Custom anchor:** Accept a date string from the frontend, parse with `pd.Timestamp()`, slice the dataframe.

**Visualization:** One `go.Scatter` trace per anchor, overlaid on the candlestick chart. Use distinct colors per anchor (52wk-high in red, 52wk-low in green, earnings in blue, custom in orange).

**yfinance earnings date availability:** `yf.Ticker(symbol).earnings_dates` returns a DataFrame with past and upcoming earnings. Take the most recent past date. Confidence: MEDIUM — earnings_dates availability varies by ticker; add a fallback that silently omits the earnings anchor if unavailable.

**Confidence:** HIGH for calculation. MEDIUM for earnings anchor availability.

---

### 3. Liquidity Sweep Detection (Swept Swing Highs/Lows)

**What it needs:** Identify local swing highs and lows (price pivots), then detect when a subsequent candle's wick temporarily exceeds a prior swing level before closing back on the opposite side (the "sweep" pattern used in ICT / Smart Money Concepts analysis).

**Swing high/low detection with numpy:**
```python
def find_swing_highs(highs: np.ndarray, order: int = 5) -> np.ndarray:
    """Return boolean mask where index i is a swing high."""
    n = len(highs)
    is_swing = np.zeros(n, dtype=bool)
    for i in range(order, n - order):
        window = highs[i - order:i + order + 1]
        if highs[i] == window.max():
            is_swing[i] = True
    return is_swing

def find_swing_lows(lows: np.ndarray, order: int = 5) -> np.ndarray:
    n = len(lows)
    is_swing = np.zeros(n, dtype=bool)
    for i in range(order, n - order):
        window = lows[i - order:i + order + 1]
        if lows[i] == window.min():
            is_swing[i] = True
    return is_swing
```

**Sweep detection:** For each swing high at index `i`, check if any subsequent candle has `high > swing_high_price` (wick above) but `close < swing_high_price` (close below). That candle is the sweep candle.

**Signal label output:** `"Bullish Sweep"` when a swing low is swept (stop-hunt below support → reversal up), `"Bearish Sweep"` when a swing high is swept (stop-hunt above resistance → reversal down), `"No Recent Sweep"` when none found in the lookback window.

**The `order` parameter:** Controls sensitivity. order=3 finds minor swings; order=5 is standard for daily timeframe. Expose as a configurable default (5) on the backend.

**Visualization:** Annotate the candlestick chart with markers on sweep candles. `go.Scatter(mode='markers', marker_symbol='triangle-up/down')` for sweep points, plus horizontal dashed lines at swept levels.

**Confidence:** HIGH — pure array comparison logic, no library required.

---

### 4. Order Flow (Buy/Sell Pressure Delta, Volume Divergence, Imbalance Candles)

**What it needs:** Three sub-signals, all derivable from OHLCV data:

**4a. Buy/Sell Pressure Delta** — Proxy for net buying vs. selling pressure using close position within the candle range:
```python
# Close position in range: 1.0 = close at high (all buying), 0.0 = close at low (all selling)
candle_range = df['high'] - df['low']
# Avoid division by zero on doji candles
close_position = np.where(
    candle_range > 0,
    (df['close'] - df['low']) / candle_range,
    0.5
)
buy_volume = df['volume'] * close_position
sell_volume = df['volume'] * (1 - close_position)
delta = buy_volume - sell_volume  # positive = net buying, negative = net selling
```

**4b. Volume Divergence** — Price moving in one direction while volume is declining (weakening move):
```python
price_change = df['close'].pct_change()
volume_change = df['volume'].pct_change()
# Divergence: price up + volume down, or price down + volume down
divergence = (price_change > 0) & (volume_change < -0.10)  # >10% volume drop
```

**4c. Imbalance Candles** — Candles where the body is >= N% of the daily ATR (strong directional candle with little shadow relative to body):
```python
atr = (df['high'] - df['low']).rolling(14).mean()
body = abs(df['close'] - df['open'])
# Imbalance = body is at least 70% of ATR, significant one-sided move
imbalance_bull = (df['close'] > df['open']) & (body >= 0.70 * atr)
imbalance_bear = (df['close'] < df['open']) & (body >= 0.70 * atr)
```

**Visualization:** 
- Delta: `go.Bar` chart with positive delta in green, negative in red (below the candlestick)
- Imbalance candles: highlighted with different trace color or marker on the main candlestick chart

**Confidence:** HIGH — all three are standard OHLCV derivations. The close-position buy/sell proxy is a well-established approximation used when tick data is unavailable (which it is in a yfinance-based app).

---

## The "No Black-Box Library" Constraint — Explicit Analysis

The project's showcase context requires implementations to be visible and interpretable. Two libraries are commonly recommended for these indicators — here is why both are rejected:

### pandas_ta — Rejected

**What it offers:** ~130 technical indicators as one-liner pandas method calls including VWAP, ATR, and some swing detection.

**Why not to use it:**
1. **VWAP in pandas_ta is session-VWAP** (resets daily), not anchored VWAP from a custom start date. The anchored VWAP this milestone requires is not in pandas_ta's standard offering.
2. **Volume Profile is not in pandas_ta.** It would still need to be written from scratch.
3. **Liquidity Sweep detection is not in pandas_ta.** The library covers traditional indicators, not SMC/ICT-style pattern detection.
4. **Black-box concern:** A recruiter asking "how did you calculate this?" should be answerable by pointing to 20 lines of visible numpy code, not to a library import.
5. **Dependency risk on Render:** pandas_ta is an additional install; it also pins specific pandas version ranges that can conflict with the existing `>=1.5.0` pin.

**Verdict:** Do NOT add pandas_ta. The indicators it covers are a subset of what this milestone needs, and the ones it does cover are simple enough to implement directly.

### ta (ta-lib Python wrapper) — Rejected

**Why not to use it:**
1. **C binary dependency.** `ta-lib` requires a compiled C library (TA-Lib). This breaks on Render and other PaaS environments without custom buildpacks.
2. The existing STACK.md already explicitly records this rejection: "Do NOT add ta-lib. It has a C binary dependency that frequently breaks on Render."
3. The Python `ta` package (pure Python, different from TA-Lib wrapper) is an option but suffers the same problem as pandas_ta — it does not cover Volume Profile, Anchored VWAP, or Liquidity Sweep patterns.

**Verdict:** Do NOT add ta or ta-lib.

### scipy — Already Installed, Minor Use

scipy is already in requirements.txt. No new use needed for these indicators. The `scipy.signal.argrelextrema` function could simplify swing high/low detection, but the numpy loop implementation is more transparent for a showcase and avoids importing scipy into the indicator module unnecessarily.

---

## What to Add to requirements.txt

**Nothing.** All four indicators use only numpy and pandas, which are already installed.

If the frontend Plotly.js CDN version needs to be current for the horizontal bar chart (Volume Profile), verify the CDN version pinned in the HTML templates — the existing STACK.md suggests `plotly-2.35.0.min.js`. No change required.

---

## Integration Points in the Existing Codebase

| New component | Where it lives | What it calls |
|---------------|----------------|---------------|
| `VolumeProfile` class or functions | `src/indicators/trading_indicators.py` (new file) | `df` from yfinance, returns dict with bins + POC/VAH/VAL |
| `AnchoredVWAP` | same new file | `yf.Ticker(sym).history()` + `Ticker.earnings_dates` |
| `LiquiditySweep` | same new file | `df['high']`, `df['low']`, `df['close']` arrays |
| `OrderFlow` | same new file | full OHLCV dataframe |
| Flask endpoint | `webapp.py` `/api/trading-indicators/<ticker>` | calls all four, returns JSON |
| Frontend | `static/js/tradingIndicators.js` (new file) | Plotly 2×2 grid render |

**Rationale for a new file:** The existing `TechnicalIndicators` class in `src/indicators/technical_indicators.py` is already 1,000+ lines and is tightly coupled to Alpha Vantage API logic. The new indicators use only yfinance (already the existing fallback in that class), so placing them in a clean separate module avoids touching the working class and keeps the new code reviewable.

---

## yfinance Data Requirements

All four indicators need OHLCV daily data. The existing `_fetch_yahoo_finance_data()` method in `TechnicalIndicators` already fetches this. For the new module, call yfinance directly:

```python
import yfinance as yf

def get_ohlcv(ticker: str, days: int) -> pd.DataFrame:
    end = pd.Timestamp.today()
    start = end - pd.Timedelta(days=days)
    df = yf.Ticker(ticker).history(start=start, end=end, interval='1d')
    df.columns = [c.lower() for c in df.columns]
    return df[['open', 'high', 'low', 'close', 'volume']].dropna()
```

**Lookback support (30/90/180/365 days):** Pass `days` as a parameter from the frontend selector. All four calculations are stateless given the dataframe, so changing lookback is just re-fetching and re-computing.

---

## Plotly Chart Types for 2x2 Grid

| Panel | Chart Type | Plotly traces |
|-------|------------|---------------|
| Liquidity Sweep | Candlestick + scatter markers on sweep candles | `go.Candlestick` + `go.Scatter(mode='markers')` |
| Order Flow | Bar chart (delta histogram below price) | `go.Bar(x=dates, y=delta, marker_color=...)` |
| Anchored VWAP | Candlestick + multiple VWAP line overlays | `go.Candlestick` + multiple `go.Scatter` for each anchor |
| Volume Profile | Horizontal bar chart beside candlestick | `go.Bar(orientation='h')` in subplot |

Use `plotly.subplots.make_subplots(rows=2, cols=2)` or equivalent Plotly.js subplot API on the frontend. The 2×2 layout is a Plotly-native pattern.

---

## Alternatives Considered and Rejected

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Swing detection | Manual numpy argmax window | scipy.signal.argrelextrema | Works but adds scipy import to indicator module; numpy loop is more transparent for showcase |
| Volume Profile | Manual pandas cut+groupby | mplfinance volume profile | Adds matplotlib dependency to a Plotly-based app; also a black box for showcase |
| Anchored VWAP | Manual pandas cumsum | pandas_ta VWAP | pandas_ta VWAP is session-reset only, not anchored; still need to write the anchor logic |
| Order Flow delta | Close-position proxy | Tick data / L2 order book | yfinance provides no tick data; the close-position proxy is the industry-standard OHLCV approximation |
| Buy/sell classification | Close-position method | Lee-Ready algorithm | Lee-Ready requires bid-ask spread data not available in yfinance; close-position is the correct fallback |

---

## Sources and Confidence

| Area | Confidence | Basis |
|------|------------|-------|
| numpy/pandas sufficiency for all four indicators | HIGH | Direct algorithm analysis; all operations are array math and groupby |
| Volume Profile algorithm | HIGH | Standard histogram binning — textbook math |
| Anchored VWAP calculation | HIGH | Cumulative TPVOL/CUMVOL — one pandas expression |
| Swing high/low detection | HIGH | Rolling argmax — widely documented, no library needed |
| Order Flow close-position proxy | HIGH | Industry-standard OHLCV approximation when tick data unavailable |
| pandas_ta rejection (no anchored VWAP, no volume profile) | HIGH | pandas_ta documentation confirms session-VWAP only; volume profile absent |
| ta-lib rejection | HIGH | Carried from prior STACK.md research; C binary dep confirmed in prior milestone |
| yfinance earnings_dates availability | MEDIUM | Works for US equities with earnings history; may be absent for some tickers |
| Plotly 2x2 subplot layout | HIGH | Plotly.js subplot API is stable and already used in this codebase |
