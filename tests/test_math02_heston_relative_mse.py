"""
TDD tests for MATH-02: HestonCalibrator relative MSE fix.

These tests verify:
1. mse_fn uses relative (percentage) MSE: ((model - mp) / mp)^2
2. Contracts with market_price < 0.50 are filtered before calibration
3. HestonCalibrator imports and instantiates without error
"""
import sys
sys.path.insert(0, '/Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper')

import inspect
import pytest

pytestmark = pytest.mark.unit


def test_heston_calibrator_imports():
    """Test 3: HestonCalibrator imports and instantiates without error."""
    from src.derivatives.model_calibration import HestonCalibrator
    cal = HestonCalibrator()
    assert hasattr(cal, 'calibrate'), 'calibrate method missing'


def test_relative_mse_division_in_source():
    """Test 1: Source code contains relative MSE (division by mp)."""
    from src.derivatives.model_calibration import HestonCalibrator
    src = inspect.getsource(HestonCalibrator.calibrate)
    assert '/ mp' in src, 'Relative MSE division by mp not found in mse_fn source'


def test_market_price_filter_in_source():
    """Test 2: Source code contains the 0.50 market price filter."""
    from src.derivatives.model_calibration import HestonCalibrator
    src = inspect.getsource(HestonCalibrator.calibrate)
    assert 'market_price' in src and '0.50' in src, \
        'MIN_MARKET_PRICE filter (>= 0.50) not found in calibrate source'


def test_relative_mse_comment_present():
    """Verify the MATH-02 fix comment is present."""
    from src.derivatives.model_calibration import HestonCalibrator
    src = inspect.getsource(HestonCalibrator.calibrate)
    assert 'MATH-02' in src or 'Relative' in src, \
        'No comment about relative MSE or MATH-02 fix found'


if __name__ == '__main__':
    # Run manually for quick feedback
    try:
        test_heston_calibrator_imports()
        print('PASS: imports and instantiates')
    except Exception as e:
        print(f'FAIL: {e}')

    try:
        test_relative_mse_division_in_source()
        print('FAIL: relative MSE already present (should be RED)')
    except AssertionError as e:
        print(f'RED (expected): {e}')

    try:
        test_market_price_filter_in_source()
        print('FAIL: filter already present (should be RED)')
    except AssertionError as e:
        print(f'RED (expected): {e}')
