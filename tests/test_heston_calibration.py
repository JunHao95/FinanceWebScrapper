"""
MATH-02: Relative MSE smoke test -- verifies the fix is in place without
requiring live market data (which would make the test slow and flaky).
Full integration test (calibrate on SPY) is done manually during Phase 1 sign-off.
"""
import sys
import os
import inspect
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from src.derivatives.model_calibration import HestonCalibrator

pytestmark = pytest.mark.unit


def test_relative_mse_in_source():
    """
    Source code of HestonCalibrator.calibrate must contain the relative MSE pattern.
    This is a fast structural check -- avoids live market data dependency.
    """
    src = inspect.getsource(HestonCalibrator.calibrate)
    assert '/ mp' in src, (
        "Relative MSE (/ mp) not found in HestonCalibrator.calibrate source. "
        "Dollar MSE may still be in use (MATH-02 fix not applied)."
    )


def test_market_price_filter_in_source():
    """
    Source code must contain the minimum price filter that excludes near-zero options.
    """
    src = inspect.getsource(HestonCalibrator.calibrate)
    assert 'market_price' in src and ('0.50' in src or 'MIN_MARKET_PRICE' in src), (
        "Minimum market price filter (>= 0.50) not found in HestonCalibrator.calibrate. "
        "Near-zero OTM options may dominate the relative MSE objective (MATH-02 pitfall)."
    )


def test_heston_calibrator_instantiates():
    """HestonCalibrator must instantiate without error and have a calibrate method."""
    cal = HestonCalibrator()
    assert callable(getattr(cal, 'calibrate', None)), "calibrate method not callable"
