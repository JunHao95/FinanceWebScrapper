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
        height=420,
        shapes=shapes,
        paper_bgcolor='#1e1e2e',
        plot_bgcolor='#1e1e2e',
        font=dict(color='#cdd6f4'),
        xaxis_rangeslider_visible=False,
        xaxis2=dict(showticklabels=False),
        margin=dict(l=10, r=10, t=60, b=10),
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


def compute_anchored_vwap(df: pd.DataFrame) -> dict:
    return {'status': 'stub'}


def compute_order_flow(df: pd.DataFrame) -> dict:
    return {'status': 'stub'}


def compute_liquidity_sweep(df: pd.DataFrame) -> dict:
    return {'status': 'stub'}


def compute_composite_bias(results: dict) -> dict:
    return {'status': 'stub'}
