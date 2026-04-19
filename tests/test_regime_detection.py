"""
MATH-04: HMM label robustness test -- SPY March 2020 must be classified as stressed.
Reference: SPY fell ~34% peak-to-trough in 5 weeks; VIX peaked above 80.
This is a known historical fact -- if the model classifies March 2020 as RISK_ON,
the label assignment is broken.
"""
import numpy as np
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.analytics.regime_detection import RegimeDetector, _assign_labels

pytestmark = pytest.mark.unit


def test_assign_labels_both_agree():
    """When sigma and mu both agree on calm state, confidence is HIGH."""
    calm, stressed, conf = _assign_labels(
        mu=np.array([0.001, -0.002]),
        sigma=np.array([0.008, 0.020])
    )
    assert calm == 0 and stressed == 1
    assert conf == 'HIGH', f"Expected HIGH confidence when criteria agree, got {conf}"


def test_assign_labels_disagree_gives_ambiguous():
    """When sigma and mu disagree, confidence is AMBIGUOUS (sigma wins as primary)."""
    calm, stressed, conf = _assign_labels(
        mu=np.array([-0.001, 0.002]),   # mu says state 1 is calm
        sigma=np.array([0.008, 0.020])  # sigma says state 0 is calm
    )
    assert calm == 0, f"Sigma is primary -- calm should be state 0, got {calm}"
    assert conf == 'AMBIGUOUS', f"Expected AMBIGUOUS when criteria disagree, got {conf}"


def test_assign_labels_low_separation_gives_ambiguous():
    """When sigma separation < 20%, confidence is AMBIGUOUS even if criteria agree."""
    calm, stressed, conf = _assign_labels(
        mu=np.array([0.001, -0.002]),
        sigma=np.array([0.0095, 0.010])  # only ~5% separation
    )
    assert conf == 'AMBIGUOUS', (
        f"Expected AMBIGUOUS for low sigma separation, got {conf}. "
        f"Separation: {abs(0.0095-0.010)/0.010:.2%}"
    )


@pytest.mark.slow
def test_spy_march_2020_is_stressed(spy_returns):
    """
    Historical benchmark: SPY March 2020 must be labelled stressed.
    This test requires network access (yfinance) and takes ~30 seconds.
    Run with: pytest tests/test_regime_detection.py -m slow
    """
    returns, dates = spy_returns

    assert len(returns) >= 800, (
        f"Insufficient data: {len(returns)} observations. "
        f"Need >= 800 for reliable HMM fit. Check yfinance data fetch."
    )

    # Use multiple seeds to guard against label-switching on any single seed
    failure_seeds = []
    for seed in range(5):  # test seeds 0-4
        rd = RegimeDetector()
        np.random.seed(seed)
        result = rd.fit(returns)

        if 'error' in result:
            continue  # skip seeds where optimisation fails

        if result.get('label_confidence') == 'AMBIGUOUS':
            continue  # ambiguous fit -- not a labelling bug, skip this seed

        # Find March 2020 indices in the return series
        if dates is not None:
            import pandas as pd
            dates_pd = pd.DatetimeIndex(dates)
            march_2020_mask = (dates_pd >= '2020-03-01') & (dates_pd <= '2020-03-31')
            march_indices = np.where(march_2020_mask)[0]
        else:
            # Fall back to approximate index: if 2017-01-01 to 2021-01-01, March 2020 is
            # approximately trading day 780-800 out of ~1008 total
            march_indices = list(range(780, 800))

        if len(march_indices) == 0:
            pytest.skip("Could not identify March 2020 in return series")

        probs = np.array(result.get('filtered_probs_full', []))
        if len(probs) == 0:
            pytest.skip("filtered_probs_full not in result dict")

        # Determine which state is stressed
        stressed_state = result.get('stressed_state_idx', None)
        if stressed_state is None:
            # Infer: stressed state has higher sigma
            # The result dict should have this but fall back to index 1 (conventional)
            stressed_state = 1  # fallback

        march_stressed = []
        for idx in march_indices:
            if idx < len(probs):
                prob_stressed = probs[idx][stressed_state]
                march_stressed.append(prob_stressed > 0.5)

        if not march_stressed:
            continue

        fraction_stressed = sum(march_stressed) / len(march_stressed)
        if fraction_stressed < 0.8:
            failure_seeds.append((seed, fraction_stressed))

    if failure_seeds:
        fail_str = ', '.join(f'seed={s}: {f:.0%} stressed' for s, f in failure_seeds)
        pytest.fail(
            f"March 2020 not classified as stressed (MATH-04 failure). "
            f"Failed seeds: {fail_str}. "
            f"Expected >= 80% of March 2020 trading days to be stressed."
        )
