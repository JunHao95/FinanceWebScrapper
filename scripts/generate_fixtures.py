"""
Fixture generator for Phase 23-03 regression tests.

Creates:
  tests/fixtures/volume_profile_ohlcv.csv
  tests/fixtures/order_flow_ohlcv.csv
  tests/fixtures/heston_market_prices.json

Run once to generate frozen fixture files; commit them to git.
Prints computed expected values for hardcoding in regression tests.
"""

import sys
import os
import json
import numpy as np
import pandas as pd
from scipy.stats import norm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'tests', 'fixtures')
os.makedirs(FIXTURES_DIR, exist_ok=True)


def make_ohlcv(n: int = 150, base: float = 150.0, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range('2023-01-02', periods=n, freq='B')
    returns = rng.normal(0.0003, 0.008, n)  # slight upward drift
    closes = base * np.cumprod(1 + returns)
    # Asymmetric highs/lows: upper_spread != lower_spread → non-trivial buy_ratio
    upper = rng.uniform(0.2, 1.8, n)
    lower = rng.uniform(0.2, 1.8, n)
    highs = closes + upper
    lows = closes - lower
    opens = lows + rng.uniform(0, 1, n) * (highs - lows)
    volumes = (rng.exponential(1_500_000, n) + 500_000).astype(int)
    df = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volumes,
    }, index=dates)
    df.index.name = 'Date'
    return df


def _bs_call(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)


def make_heston_market_prices():
    S, r, sigma = 100.0, 0.05, 0.20
    contracts = [
        {'K': K, 'T': T}
        for T in [0.25, 0.50, 1.00]
        for K in [90, 95, 100, 105, 110]
    ]
    out = []
    for c in contracts:
        mid = round(float(_bs_call(S, c['K'], c['T'], r, sigma)), 4)
        out.append({'S': S, 'K': c['K'], 'T': c['T'], 'r': r, 'mid_price': mid})
    return out


def main():
    # -- OHLCV fixtures --
    df = make_ohlcv()
    vp_path = os.path.join(FIXTURES_DIR, 'volume_profile_ohlcv.csv')
    of_path = os.path.join(FIXTURES_DIR, 'order_flow_ohlcv.csv')
    df.to_csv(vp_path)
    df.to_csv(of_path)
    print(f"Saved {vp_path}")
    print(f"Saved {of_path}")

    # Compute expected Volume Profile values
    from src.analytics.trading_indicators import compute_volume_profile, compute_order_flow
    vp = compute_volume_profile(df)
    print(f"\nVolume Profile expected values:")
    print(f"  POC = {vp['poc']}")
    print(f"  VAH = {vp['vah']}")
    print(f"  VAL = {vp['val']}")
    print(f"  signal = '{vp['signal']}'")

    # Compute expected Order Flow values
    of = compute_order_flow(df)
    ranges = (df['High'] - df['Low']).clip(lower=1e-9)
    buy_ratio = (df['Close'] - df['Low']) / ranges
    delta = (2 * buy_ratio - 1) * df['Volume']
    cum_delta_last = float(delta.cumsum().iloc[-1])
    print(f"\nOrder Flow expected values:")
    print(f"  last cumulative delta = {cum_delta_last}")
    print(f"  signal = '{of['signal']}'")

    # -- Heston market prices fixture --
    contracts = make_heston_market_prices()
    hp_path = os.path.join(FIXTURES_DIR, 'heston_market_prices.json')
    with open(hp_path, 'w') as f:
        json.dump(contracts, f, indent=2)
    print(f"\nSaved {hp_path}")
    print(f"  {len(contracts)} contracts: K in [90,95,100,105,110], T in [0.25,0.50,1.00]")
    print("\nDone. Hardcode the printed values into test_regression_indicators.py.")


if __name__ == '__main__':
    main()
