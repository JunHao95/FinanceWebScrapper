"""
Trading Indicators — canonical OHLCV fetch + stub indicator functions.
Phases 19–22 replace stub bodies with real compute.

IMPORTANT: Uses yf.Ticker().history() — NOT yf.download() — to avoid
concurrent-call 2D/1D shape corruption (Phase 09-01 decision).
"""
import yfinance as yf
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime, timedelta


def fetch_ohlcv(ticker: str, days: int, auto_adjust: bool = True) -> pd.DataFrame:
    """
    Canonical OHLCV fetch for all trading indicator modules.

    Uses yf.Ticker().history() — NOT yf.download() — to avoid concurrent-call
    2D/1D shape corruption (Phase 09-01 project decision).

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume
        Index: timezone-naive DatetimeIndex
    """
    end = datetime.now()
    start = end - timedelta(days=int(days * 1.4))  # 40% buffer for non-trading days
    df = yf.Ticker(ticker).history(
        start=start.strftime('%Y-%m-%d'),
        end=end.strftime('%Y-%m-%d'),
        auto_adjust=auto_adjust,
    )
    if df.empty:
        raise ValueError(f"No OHLCV data returned for {ticker}")
    df.index = df.index.tz_localize(None) if df.index.tz is not None else df.index
    return df[['Open', 'High', 'Low', 'Close', 'Volume']]


# ---------------------------------------------------------------------------
# Stub compute functions — replaced by real logic in Phases 19–22
# ---------------------------------------------------------------------------

def compute_volume_profile(df: pd.DataFrame, ticker: str = '', lookback: int = 0) -> dict:
    """
    Compute Volume Profile (POC, VAH, VAL, 70% value area) and return a
    Plotly subplot payload {traces, layout, signal, bin_width_usd, poc, vah, val}.
    """
    highs = df['High'].values.astype(float)
    lows = df['Low'].values.astype(float)
    closes = df['Close'].values.astype(float)
    volumes = df['Volume'].values.astype(float)

    price_min = lows.min()
    price_max = highs.max()
    price_range = price_max - price_min
    mid_price = (price_min + price_max) / 2.0

    if price_range > 1e-10:
        n_bins = max(20, min(200, int(price_range / (mid_price * 0.002))))
    else:
        n_bins = 20

    bin_edges = np.linspace(price_min, price_max, n_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
    bin_lo = bin_edges[:-1]
    bin_hi = bin_edges[1:]
    bin_width = float(bin_edges[1] - bin_edges[0])

    volume_by_bin = np.zeros(n_bins, dtype=float)

    for i in range(len(df)):
        bar_lo = lows[i]
        bar_hi = highs[i]
        bar_vol = volumes[i]
        bar_range = bar_hi - bar_lo

        if bar_range < 1e-10:
            idx = np.searchsorted(bin_edges, bar_lo, side='right') - 1
            idx = max(0, min(n_bins - 1, idx))
            volume_by_bin[idx] += bar_vol
        else:
            overlaps = np.maximum(0.0, np.minimum(bin_hi, bar_hi) - np.maximum(bin_lo, bar_lo))
            total_overlap = overlaps.sum()
            if total_overlap > 1e-10:
                volume_by_bin += bar_vol * overlaps / total_overlap

    # POC
    poc_idx = int(np.argmax(volume_by_bin))
    poc = float(bin_centers[poc_idx])

    # Value area (greedy expansion from POC until >= 70% of total volume)
    total_volume = volume_by_bin.sum()
    target = 0.70 * total_volume

    sorted_idx = np.argsort(volume_by_bin)[::-1]
    accumulated = 0.0
    va_set = set()
    for idx in sorted_idx:
        va_set.add(idx)
        accumulated += volume_by_bin[idx]
        if accumulated >= target:
            break

    va_indices = sorted(va_set)
    vah = float(bin_centers[max(va_indices)])
    val = float(bin_centers[min(va_indices)])

    current_price = float(closes[-1])
    signal = 'inside' if val <= current_price <= vah else 'outside'

    # Build Plotly figure
    fig = make_subplots(
        rows=1, cols=2,
        shared_yaxes=True,
        column_widths=[0.75, 0.25],
        horizontal_spacing=0.02,
    )

    # Candlestick on col 1
    fig.add_trace(go.Candlestick(
        x=df.index.astype(str).tolist(),
        open=df['Open'].tolist(),
        high=df['High'].tolist(),
        low=df['Low'].tolist(),
        close=df['Close'].tolist(),
        name=ticker or 'Price',
        showlegend=False,
    ), row=1, col=1)

    # Horizontal bar histogram on col 2
    bar_colors = [
        'rgba(70,130,180,0.7)' if i in va_set else 'rgba(150,150,150,0.4)'
        for i in range(n_bins)
    ]
    fig.add_trace(go.Bar(
        x=volume_by_bin.tolist(),
        y=bin_centers.tolist(),
        orientation='h',
        marker_color=bar_colors,
        name='Volume',
        showlegend=False,
    ), row=1, col=2)

    # Shapes on histogram subplot (xref='x2', yref='y2')
    max_vol = float(volume_by_bin.max())
    shapes = [
        # Value area fill
        dict(type='rect', xref='x2', yref='y2',
             x0=0, x1=max_vol, y0=val, y1=vah,
             fillcolor='rgba(70,130,180,0.15)', line_width=0),
        # POC line
        dict(type='line', xref='x2', yref='y2',
             x0=0, x1=max_vol, y0=poc, y1=poc,
             line=dict(color='#ff6b35', width=3)),
        # VAH dashed
        dict(type='line', xref='x2', yref='y2',
             x0=0, x1=max_vol, y0=vah, y1=vah,
             line=dict(color='#2ecc71', width=1, dash='dash')),
        # VAL dashed
        dict(type='line', xref='x2', yref='y2',
             x0=0, x1=max_vol, y0=val, y1=val,
             line=dict(color='#e74c3c', width=1, dash='dash')),
    ]

    fig.update_layout(
        title=dict(
            text=(f'{ticker} — Volume Profile ({lookback}d)<br>'
                  f'<sup>Bin width: ${bin_width:.2f} | POC: ${poc:.2f} | '
                  f'VAH: ${vah:.2f} | VAL: ${val:.2f}</sup>'),
        ),
        height=500,
        shapes=shapes,
        paper_bgcolor='#1e1e2e',
        plot_bgcolor='#1e1e2e',
        font=dict(color='#cdd6f4'),
        xaxis_rangeslider_visible=False,
        xaxis=dict(automargin=True),
        yaxis=dict(automargin=True),
        xaxis2=dict(showticklabels=False, automargin=True),
        margin=dict(l=70, r=20, t=70, b=50),
    )

    d = fig.to_dict()
    d['layout'].pop('template', None)

    return {
        'traces': d['data'],
        'layout': d['layout'],
        'signal': signal,
        'bin_width_usd': round(bin_width, 6),
        'poc': round(poc, 4),
        'vah': round(vah, 4),
        'val': round(val, 4),
    }


PAPER_BG = '#1e1e2e'
PLOT_BG  = '#1e1e2e'
FONT_CLR = '#cdd6f4'
AVWAP_COLORS = {
    'high':     '#4c9be8',
    'low':      '#fe8019',
    'earnings': '#cba6f7',
    'ref_line': 'rgba(205,214,244,0.35)',
}


def _get_last_earnings_date(ticker: str):
    """Return the most recent past earnings date (tz-naive) or None."""
    try:
        ed = yf.Ticker(ticker).earnings_dates
        if ed is None or ed.empty:
            return None
        if 'Reported EPS' not in ed.columns:
            return None
        past = ed[ed['Reported EPS'].notna()]
        if past.empty:
            return None
        last = past.index.max()
        return last.tz_localize(None) if last.tzinfo is not None else last
    except Exception:
        return None


def _avwap_series(df_full: pd.DataFrame, anchor_date, display_index: pd.DatetimeIndex) -> pd.Series:
    """Compute AVWAP from anchor_date forward, reindexed to display_index."""
    subset = df_full.loc[anchor_date:]
    if subset.empty:
        return pd.Series(index=display_index, dtype=float)
    tp = (subset['High'] + subset['Low'] + subset['Close']) / 3.0
    cum_v = subset['Volume'].cumsum().replace(0, np.nan)
    cum_tpv = (tp * subset['Volume']).cumsum()
    return (cum_tpv / cum_v).reindex(display_index)


def _safe_list(series: pd.Series) -> list:
    """Convert series to list, replacing NaN with None for JSON safety."""
    return [None if pd.isna(v) else float(v) for v in series]


def compute_anchored_vwap(df: pd.DataFrame, ticker: str, lookback: int) -> dict:
    """
    Compute Anchored VWAP for 52-wk High, 52-wk Low, and most recent earnings date.

    Args:
        df: 365-day OHLCV DataFrame (caller provides full history)
        ticker: ticker symbol (for earnings date lookup)
        lookback: display window size (last N rows of df)

    Returns dict with keys: traces, layout, signal, convergence, current_price,
    earnings_unavailable, labels
    """
    df_display = df.iloc[-lookback:] if len(df) >= lookback else df
    display_index = df_display.index

    wk52_high_date = df['High'].idxmax()
    wk52_low_date  = df['Low'].idxmin()

    earnings_ts = _get_last_earnings_date(ticker)
    earnings_unavailable = True
    if earnings_ts is not None:
        if earnings_ts < df.index[0]:
            earnings_unavailable = True
            earnings_ts = None
        else:
            earnings_unavailable = False

    avwap_high = _avwap_series(df, wk52_high_date, display_index)
    avwap_low  = _avwap_series(df, wk52_low_date,  display_index)
    avwap_earn = _avwap_series(df, earnings_ts, display_index) if earnings_ts is not None else None

    current_price = float(df_display['Close'].iloc[-1])

    avwap_high_val = float(avwap_high.iloc[-1]) if not pd.isna(avwap_high.iloc[-1]) else None
    avwap_low_val  = float(avwap_low.iloc[-1])  if not pd.isna(avwap_low.iloc[-1])  else None
    avwap_earn_val = float(avwap_earn.iloc[-1]) if (avwap_earn is not None and not pd.isna(avwap_earn.iloc[-1])) else None

    # Convergence check (within 0.3%)
    converging = []
    for name, val in [('52-wk High', avwap_high_val), ('52-wk Low', avwap_low_val), ('Earnings', avwap_earn_val)]:
        if val is not None and abs(current_price - val) / current_price <= 0.003:
            converging.append(name)

    # Signal
    if avwap_high_val is not None and current_price > avwap_high_val:
        signal = 'above'
    elif avwap_low_val is not None and current_price < avwap_low_val:
        signal = 'below'
    else:
        signal = 'between'

    # Labels
    def _pct_label(prefix, avwap_val):
        if avwap_val is None:
            return None
        pct = (current_price - avwap_val) / avwap_val * 100
        return f'{prefix}: {pct:+.1f}%'

    label_high     = _pct_label('52-wk High', avwap_high_val)
    label_low      = _pct_label('52-wk Low',  avwap_low_val)
    label_earnings = _pct_label('Earnings',   avwap_earn_val)

    x_dates = display_index.astype(str).tolist()

    # Build figure
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=x_dates,
        open=df_display['Open'].tolist(),
        high=df_display['High'].tolist(),
        low=df_display['Low'].tolist(),
        close=df_display['Close'].tolist(),
        name=ticker,
        showlegend=False,
    ))

    fig.add_trace(go.Scatter(
        x=x_dates, y=_safe_list(avwap_high),
        mode='lines', name='52-wk High',
        line=dict(color=AVWAP_COLORS['high'], width=1.5),
        connectgaps=True,
    ))

    fig.add_trace(go.Scatter(
        x=x_dates, y=_safe_list(avwap_low),
        mode='lines', name='52-wk Low',
        line=dict(color=AVWAP_COLORS['low'], width=1.5),
        connectgaps=True,
    ))

    if avwap_earn is not None:
        fig.add_trace(go.Scatter(
            x=x_dates, y=_safe_list(avwap_earn),
            mode='lines', name='Earnings',
            line=dict(color=AVWAP_COLORS['earnings'], width=1.5),
            connectgaps=True,
        ))

    shapes = [dict(
        type='line', xref='paper', x0=0, x1=1,
        yref='y', y0=current_price, y1=current_price,
        line=dict(color=AVWAP_COLORS['ref_line'], width=1, dash='dash'),
    )]

    annotations = []
    for label_text, color in [
        (label_high,     AVWAP_COLORS['high']),
        (label_low,      AVWAP_COLORS['low']),
        (label_earnings, AVWAP_COLORS['earnings']),
    ]:
        if label_text is None:
            continue
        # Find y value for annotation
        if label_text.startswith('52-wk High') and avwap_high_val is not None:
            y_val = avwap_high_val
        elif label_text.startswith('52-wk Low') and avwap_low_val is not None:
            y_val = avwap_low_val
        elif label_text.startswith('Earnings') and avwap_earn_val is not None:
            y_val = avwap_earn_val
        else:
            continue
        annotations.append(dict(
            xref='paper', x=1.0, xanchor='left',
            yref='y', y=y_val,
            text=label_text,
            showarrow=False,
            font=dict(size=10, color=color),
        ))

    fig.update_layout(
        title=f'{ticker} — Anchored VWAP ({lookback}d)',
        height=500,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=FONT_CLR),
        xaxis_rangeslider_visible=False,
        shapes=shapes,
        annotations=annotations,
        margin=dict(l=70, r=120, t=70, b=50),
    )

    d = fig.to_dict()
    d['layout'].pop('template', None)

    return {
        'traces': d['data'],
        'layout': d['layout'],
        'signal': signal,
        'convergence': converging,
        'current_price': current_price,
        'earnings_unavailable': earnings_unavailable,
        'labels': {
            'high':     label_high,
            'low':      label_low,
            'earnings': label_earnings,
        },
    }


def compute_order_flow(df: pd.DataFrame, ticker: str = '', lookback: int = 0) -> dict:
    """
    Compute Order Flow delta chart, volume divergence signal, and imbalance candle annotations.

    Returns:
        dict with keys: traces, layout, signal, divergence
    """
    if df is None or df.empty:
        return {'status': 'error', 'message': 'empty dataframe'}

    # 1. Epsilon guard: clip zero-range bars to avoid divide-by-zero
    ranges = (df['High'] - df['Low']).clip(lower=1e-9)

    # 2. Per-bar delta: buy_ratio in [0,1], mapped to [-vol, +vol]
    buy_ratio = (df['Close'] - df['Low']) / ranges
    delta = (2 * buy_ratio - 1) * df['Volume']

    # 3. Cumulative delta
    cumulative_delta = delta.cumsum()

    # 4. Bar colours
    bar_colors = ['#2ecc71' if v >= 0 else '#e74c3c' for v in delta]

    # 5. Rolling slope helper (last 10 bars)
    def _last_slope(series: pd.Series) -> float:
        vals = series.dropna().values[-10:]
        if len(vals) < 2:
            return 0.0
        x = np.arange(len(vals), dtype=float)
        return float(np.polyfit(x, vals, 1)[0])

    # 6. Divergence detection
    price_slope = _last_slope(df['Close'])
    vol_slope   = _last_slope(df['Volume'])
    divergence_detected = bool((price_slope * vol_slope < 0) and (len(df) >= 10))

    # 7. Imbalance candle detection
    body = (df['Close'] - df['Open']).abs()
    body_ratio = body / ranges
    avg_vol_20 = df['Volume'].rolling(20, min_periods=1).mean()
    is_imbalance = (body_ratio > 0.70) & (df['Volume'] > 1.2 * avg_vol_20)

    # 8. Build Plotly figure (dual-axis)
    fig = go.Figure()

    # Delta bars on primary y-axis
    delta_vals = _safe_list(delta)
    fig.add_trace(go.Bar(
        x=list(df.index.astype(str)),
        y=delta_vals,
        marker_color=bar_colors,
        name='Delta',
        yaxis='y',
    ))

    # Cumulative delta line on secondary y-axis
    cum_vals = _safe_list(cumulative_delta)
    fig.add_trace(go.Scatter(
        x=list(df.index.astype(str)),
        y=cum_vals,
        mode='lines',
        line=dict(color='#cdd6f4', width=1.5),
        name='Cumulative Delta',
        yaxis='y2',
    ))

    # 9. Imbalance annotations (yref='y', the delta bar axis)
    annotations = []
    delta_arr = delta.values
    for i, flag in enumerate(is_imbalance):
        if not flag:
            continue
        bar_val = delta_arr[i]
        offset = abs(bar_val) * 0.05 if abs(bar_val) > 0 else 1.0
        is_bullish = df['Close'].iloc[i] >= df['Open'].iloc[i]
        annotations.append(dict(
            x=str(df.index[i]),
            y=float(bar_val) + offset if is_bullish else float(bar_val) - offset,
            xref='x',
            yref='y',
            text='\u25b2' if is_bullish else '\u25bc',
            showarrow=False,
            font=dict(color='#2ecc71' if is_bullish else '#e74c3c', size=12),
        ))

    # 10. Zero-line shape
    fig.update_layout(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=FONT_CLR),
        title=f'Order Flow — {ticker}' if ticker else 'Order Flow',
        yaxis=dict(title='Delta', gridcolor='#313244'),
        yaxis2=dict(
            title='Cumulative Delta',
            overlaying='y',
            side='right',
            gridcolor='#313244',
        ),
        xaxis=dict(gridcolor='#313244'),
        shapes=[dict(
            type='line',
            xref='paper', x0=0, x1=1,
            yref='y', y0=0, y1=0,
            line=dict(color='#7f849c', width=1, dash='dash'),
        )],
        annotations=annotations,
        showlegend=True,
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color=FONT_CLR)),
    )

    # 11. Determine overall signal from last cumulative delta slope
    cum_slope = _last_slope(cumulative_delta)
    if cum_slope > 0:
        signal = 'bullish'
    elif cum_slope < 0:
        signal = 'bearish'
    else:
        signal = 'neutral'

    # 12. Serialise
    d = fig.to_dict()
    d['layout'].pop('template', None)

    return {
        'traces':     d['data'],
        'layout':     d['layout'],
        'signal':     signal,
        'divergence': {
            'detected':    divergence_detected,
            'price_slope': round(price_slope, 6),
            'vol_slope':   round(vol_slope, 6),
        },
    }


def _adaptive_n(lookback: int) -> int:
    if lookback <= 30:
        return 2
    elif lookback <= 90:
        return 3
    return 5


def compute_liquidity_sweep(df: pd.DataFrame, lookback: int = 90) -> dict:
    n = _adaptive_n(lookback)
    min_bars = 2 * n + 1
    if len(df) < min_bars:
        return {'status': 'no_swings', 'n': n, 'signal': 'no_swings', 'swept_price': None, 'sweep_count': 0,
                'traces': [], 'layout': {}}

    highs  = df['High'].values
    lows   = df['Low'].values
    closes = df['Close'].values
    dates  = list(df.index.astype(str))

    swing_high_indices = []
    swing_low_indices  = []

    # range(n, len-n) prevents look-ahead bias (SWEEP-02)
    for i in range(n, len(highs) - n):
        if all(highs[i] > highs[i - j] for j in range(1, n + 1)) and \
           all(highs[i] > highs[i + j] for j in range(1, n + 1)):
            swing_high_indices.append(i)
        if all(lows[i] < lows[i - j] for j in range(1, n + 1)) and \
           all(lows[i] < lows[i + j] for j in range(1, n + 1)):
            swing_low_indices.append(i)

    if not swing_high_indices and not swing_low_indices:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=dates, open=df['Open'].tolist(), high=df['High'].tolist(),
            low=df['Low'].tolist(), close=df['Close'].tolist(),
            increasing_line_color='#2ecc71', decreasing_line_color='#e74c3c', name='Price',
        ))
        fig.update_layout(
            paper_bgcolor='#1e1e2e', plot_bgcolor='#1e1e2e',
            font=dict(color='#cdd6f4'), xaxis_rangeslider_visible=False,
            title=dict(text=f'Liquidity Sweep — No confirmed swings (n={n})', font=dict(size=14)),
            margin=dict(l=40, r=40, t=50, b=30),
        )
        d = fig.to_dict()
        return {
            'traces': d['data'], 'layout': d['layout'],
            'signal': 'no_swings', 'n': n, 'swept_price': None, 'sweep_count': 0,
        }

    sweep_events = []
    annotations  = []
    shapes       = []

    last_swing_high = highs[swing_high_indices[-1]] if swing_high_indices else None
    last_swing_low  = lows[swing_low_indices[-1]]   if swing_low_indices  else None

    if last_swing_high is not None:
        ref_idx = swing_high_indices[-1]
        for i in range(ref_idx + 1, len(closes)):
            if closes[i] > last_swing_high:
                sweep_events.append((i, 'bullish', last_swing_high))
                annotations.append(dict(
                    x=dates[i], y=highs[i] * 1.002,
                    text='▲', showarrow=False,
                    font=dict(size=14, color='#2ecc71'),
                    xanchor='center', yanchor='bottom',
                ))
                shapes.append(dict(
                    type='line', xref='paper', yref='y',
                    x0=0, x1=1, y0=last_swing_high, y1=last_swing_high,
                    line=dict(dash='dash', color='#2ecc71', width=1),
                ))

    if last_swing_low is not None:
        ref_idx = swing_low_indices[-1]
        for i in range(ref_idx + 1, len(closes)):
            if closes[i] < last_swing_low:
                sweep_events.append((i, 'bearish', last_swing_low))
                annotations.append(dict(
                    x=dates[i], y=lows[i] * 0.998,
                    text='▼', showarrow=False,
                    font=dict(size=14, color='#e74c3c'),
                    xanchor='center', yanchor='top',
                ))
                shapes.append(dict(
                    type='line', xref='paper', yref='y',
                    x0=0, x1=1, y0=last_swing_low, y1=last_swing_low,
                    line=dict(dash='dash', color='#e74c3c', width=1),
                ))

    if sweep_events:
        sweep_events.sort(key=lambda e: e[0])
        last_event  = sweep_events[-1]
        signal      = last_event[1]
        swept_price = float(last_event[2])
    else:
        signal      = 'none'
        swept_price = None

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=dates, open=df['Open'].tolist(), high=df['High'].tolist(),
        low=df['Low'].tolist(), close=df['Close'].tolist(),
        increasing_line_color='#2ecc71', decreasing_line_color='#e74c3c', name='Price',
    ))
    fig.update_layout(
        paper_bgcolor='#1e1e2e', plot_bgcolor='#1e1e2e',
        font=dict(color='#cdd6f4'), xaxis_rangeslider_visible=False,
        title=dict(text=f'Liquidity Sweep (n={n})', font=dict(size=14)),
        margin=dict(l=40, r=40, t=50, b=30),
        annotations=annotations,
        shapes=shapes,
    )
    d = fig.to_dict()
    return {
        'traces':      d['data'],
        'layout':      d['layout'],
        'signal':      signal,
        'n':           n,
        'swept_price': swept_price,
        'sweep_count': len(sweep_events),
    }


def compute_composite_bias(results: dict, footprint_result: dict = None) -> dict:
    sub_map = {
        'volume_profile':  results.get('volume_profile',  {}),
        'anchored_vwap':   results.get('anchored_vwap',   {}),
        'order_flow':      results.get('order_flow',      {}),
        'liquidity_sweep': results.get('liquidity_sweep', {}),
    }
    labels = {
        'volume_profile':  'Volume Profile',
        'anchored_vwap':   'AVWAP',
        'order_flow':      'Order Flow',
        'liquidity_sweep': 'Sweep',
    }
    sub_map['footprint'] = footprint_result if isinstance(footprint_result, dict) else {}
    labels['footprint'] = 'Footprint'
    _to_direction = {
        'bullish': 'bullish', 'bearish': 'bearish', 'neutral': 'neutral',
        'inside':  'bullish', 'outside': 'bearish',
        'above':   'bullish', 'below':   'bearish', 'between': 'neutral',
    }

    available   = {}
    unavailable = []

    for key, sub in sub_map.items():
        raw_signal = sub.get('signal') if isinstance(sub, dict) else None
        is_stub    = isinstance(sub, dict) and sub.get('status') in ('stub', 'error', 'no_swings')
        if is_stub or not raw_signal or raw_signal not in _to_direction:
            unavailable.append(labels[key])
        else:
            available[labels[key]] = _to_direction[raw_signal]

    n_total   = len(available)
    n_bullish = sum(1 for v in available.values() if v == 'bullish')
    n_bearish = sum(1 for v in available.values() if v == 'bearish')

    if n_total == 0:
        direction  = 'neutral'
        score_str  = '0/0'
        dissenters = []
    elif n_bullish > n_total / 2:
        direction  = 'bullish'
        score_str  = f'{n_bullish}/{n_total}'
        dissenters = [k for k, v in available.items() if v != 'bullish']
    elif n_bearish > n_total / 2:
        direction  = 'bearish'
        score_str  = f'{n_bearish}/{n_total}'
        dissenters = [k for k, v in available.items() if v != 'bearish']
    else:
        direction  = 'neutral'
        score_str  = f'{max(n_bullish, n_bearish)}/{n_total}'
        dissenters = []

    return {
        'direction':   direction,
        'score':       score_str,
        'dissenters':  dissenters,
        'unavailable': unavailable,
    }


def fetch_intraday(ticker: str, days: int = 60) -> pd.DataFrame:
    # yfinance hard-limits 15m intraday data to the last 60 days — no buffer applied
    days = min(int(days), 59)
    end = datetime.now()
    start = end - timedelta(days=days)
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


def compute_footprint(df_15m: pd.DataFrame, ticker: str = '') -> dict:
    if df_15m is None or df_15m.empty:
        return {'signal': None, 'error': 'No intraday data', 'traces': [], 'layout': {}}

    df = df_15m.copy()
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    ranges = (df['High'] - df['Low']).clip(lower=1e-10)
    buy_volume = (df['Close'] - df['Low']) / ranges * df['Volume']
    sell_volume = df['Volume'] - buy_volume
    df['delta'] = buy_volume - sell_volume

    price_min = df['Low'].min()
    price_max = df['High'].max()
    price_range = price_max - price_min
    mid_price = (price_min + price_max) / 2.0
    n_bins = max(20, min(200, int(price_range / (mid_price * 0.002))))
    bin_edges = np.linspace(price_min, price_max, n_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    df['bin_idx'] = np.digitize(df['Close'], bin_edges) - 1
    df['bin_idx'] = df['bin_idx'].clip(0, n_bins - 1)
    df['date'] = df.index.date

    unique_dates = sorted(df['date'].unique())
    date_strings = [str(d) for d in unique_dates]

    delta_matrix = np.zeros((len(unique_dates), n_bins))
    vol_matrix = np.zeros((len(unique_dates), n_bins))
    for i, d in enumerate(unique_dates):
        day_df = df[df['date'] == d]
        for _, row in day_df.iterrows():
            b = int(row['bin_idx'])
            delta_matrix[i, b] += row['delta']
            vol_matrix[i, b] += row['Volume']

    heatmap = go.Heatmap(
        z=delta_matrix.tolist(),
        x=date_strings,
        y=bin_centers.tolist(),
        colorscale=[[0.0, '#e74c3c'], [0.5, '#1e1e2e'], [1.0, '#2ecc71']],
        zmid=0,
        showscale=True,
        hovertemplate='Date: %{x}<br>Price: %{y:.2f}<br>Delta: %{z:.0f}<extra></extra>',
    )

    poc_x, poc_y = [], []
    for i, d in enumerate(unique_dates):
        best_bin = int(np.argmax(vol_matrix[i]))
        poc_x.append(date_strings[i])
        poc_y.append(float(bin_centers[best_bin]))
    poc_scatter = go.Scatter(
        x=poc_x, y=poc_y, mode='markers',
        marker=dict(symbol='circle', size=6, color='#f9e2af', opacity=0.85),
        name='POC',
    )

    current_close = float(df['Close'].iloc[-1])
    fig = go.Figure(data=[heatmap, poc_scatter])
    fig.add_shape(
        type='line',
        x0=date_strings[0], x1=date_strings[-1],
        y0=current_close, y1=current_close,
        line=dict(color='#cdd6f4', width=1, dash='dash'),
    )
    fig.update_layout(
        title=f'Footprint Delta Heatmap — {ticker}',
        paper_bgcolor='#1e1e2e',
        plot_bgcolor='#1e1e2e',
        font=dict(color='#cdd6f4'),
        height=500,
        xaxis=dict(gridcolor='#313244'),
        yaxis=dict(gridcolor='#313244'),
    )

    cum_delta = float(df['delta'].sum())
    total_volume = float(df['Volume'].sum())
    threshold = 0.05 * total_volume
    if cum_delta > threshold:
        signal = 'bullish'
    elif cum_delta < -threshold:
        signal = 'bearish'
    else:
        signal = 'neutral'

    return {
        'traces': fig.to_dict()['data'],
        'layout': fig.to_dict()['layout'],
        'signal': signal,
        'cum_delta': cum_delta,
        'total_volume': total_volume,
    }
