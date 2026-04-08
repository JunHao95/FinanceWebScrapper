"""
Trading Indicators — canonical OHLCV fetch + stub indicator functions.
Phases 19–22 replace stub bodies with real compute.

IMPORTANT: Uses yf.Ticker().history() — NOT yf.download() — to avoid
concurrent-call 2D/1D shape corruption (Phase 09-01 decision).
"""
import yfinance as yf
import pandas as pd
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

def compute_volume_profile(df: pd.DataFrame) -> dict:
    return {'status': 'stub'}


def compute_anchored_vwap(df: pd.DataFrame) -> dict:
    return {'status': 'stub'}


def compute_order_flow(df: pd.DataFrame) -> dict:
    return {'status': 'stub'}


def compute_liquidity_sweep(df: pd.DataFrame) -> dict:
    return {'status': 'stub'}


def compute_composite_bias(results: dict) -> dict:
    return {'status': 'stub'}
