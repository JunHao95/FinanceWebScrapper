"""
TDD tests for MATH-03: CIR Feller hard constraint via reparameterisation.

These tests verify:
1. Normal calibration still works and returns feller_condition_satisfied=True
2. Calibrated params always satisfy 2*kappa*theta >= sigma**2 (structural guarantee)
3. _feller_safe_params helper exists and produces Feller-valid params
4. The old soft penalty (feller_penalty = 10.0) is not in the source
5. Source contains the reparameterisation pattern (alpha, theta, sigma)
"""
import sys
sys.path.insert(0, '/Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper')

import inspect
import pytest


def test_normal_calibration_works():
    """Test 1: Normal calibration returns a valid result dict."""
    from src.analytics.interest_rate_models import CIRCalibrator
    cal = CIRCalibrator()
    result = cal.calibrate([(1, 0.05), (2, 0.055), (5, 0.06), (10, 0.065)])
    assert 'error' not in result, f'Calibration failed: {result}'
    assert 'calibrated_params' in result, 'Missing calibrated_params in result'
    p = result['calibrated_params']
    assert 'kappa' in p and 'theta' in p and 'sigma' in p, 'Missing kappa/theta/sigma'


def test_feller_always_satisfied_after_calibration():
    """Test 2: Calibrated params always satisfy Feller: 2*kappa*theta >= sigma**2."""
    from src.analytics.interest_rate_models import CIRCalibrator
    cal = CIRCalibrator()
    result = cal.calibrate([(1, 0.05), (2, 0.055), (5, 0.06), (10, 0.065)])
    assert 'error' not in result, f'Calibration failed: {result}'
    p = result['calibrated_params']
    kappa, theta, sigma = p['kappa'], p['theta'], p['sigma']
    feller_lhs = 2 * kappa * theta
    feller_rhs = sigma ** 2
    assert feller_lhs >= feller_rhs, (
        f"Feller VIOLATED: 2*kappa*theta={feller_lhs:.6f} < sigma^2={feller_rhs:.6f}. "
        f"Reparameterisation must guarantee Feller by construction."
    )
    assert result['feller_condition_satisfied'] is True, (
        f"feller_condition_satisfied must be True, got: {result['feller_condition_satisfied']}"
    )


def test_feller_safe_params_helper_exists():
    """Test 3: _feller_safe_params helper function exists and works correctly."""
    from src.analytics import interest_rate_models
    assert hasattr(interest_rate_models, '_feller_safe_params'), (
        "_feller_safe_params helper not found in interest_rate_models module"
    )
    _feller_safe_params = interest_rate_models._feller_safe_params
    # alpha=0, theta=0.05, sigma=0.1 should produce Feller-valid kappa
    result = _feller_safe_params(0.0, 0.05, 0.1)
    assert result is not None, "_feller_safe_params returned None for valid inputs"
    kappa, theta, sigma = result
    feller_lhs = 2 * kappa * theta
    feller_rhs = sigma ** 2
    assert feller_lhs >= feller_rhs, (
        f"_feller_safe_params output violates Feller: 2*kappa*theta={feller_lhs} < sigma^2={feller_rhs}"
    )


def test_soft_penalty_removed_from_source():
    """Test 4: The old soft penalty (feller_penalty = 10.0) must not be in calibrate source."""
    from src.analytics.interest_rate_models import CIRCalibrator
    src = inspect.getsource(CIRCalibrator.calibrate)
    assert 'feller_penalty = 10.0' not in src, (
        "Old soft penalty 'feller_penalty = 10.0' still found in calibrate source. "
        "Must be replaced with reparameterisation approach."
    )


def test_reparameterisation_pattern_in_source():
    """Test 5: Source code must use reparameterised (alpha, theta, sigma) pattern."""
    from src.analytics.interest_rate_models import CIRCalibrator
    src = inspect.getsource(CIRCalibrator.calibrate)
    assert 'alpha' in src, (
        "Reparameterisation variable 'alpha' not found in calibrate source. "
        "Must optimise over (alpha, theta, sigma) to guarantee Feller by construction."
    )
    assert '_feller_safe_params' in src, (
        "_feller_safe_params not called from calibrate(). "
        "Reparameterisation helper must be used inside mse_fn."
    )


def test_return_dict_shape_unchanged():
    """Test 6: Return dict must contain all original keys."""
    from src.analytics.interest_rate_models import CIRCalibrator
    cal = CIRCalibrator()
    result = cal.calibrate([(1, 0.05), (5, 0.06)])
    required_keys = [
        'model', 'calibrated_params', 'r0', 'feller_condition_satisfied',
        'feller_lhs', 'feller_rhs', 'mse', 'rmse', 'implied_yield_curve'
    ]
    for key in required_keys:
        assert key in result, f"Missing required key '{key}' in calibrate() return dict"


if __name__ == '__main__':
    print("Running RED-phase tests (should FAIL before fix):")
    for fn in [
        test_normal_calibration_works,
        test_feller_always_satisfied_after_calibration,
        test_feller_safe_params_helper_exists,
        test_soft_penalty_removed_from_source,
        test_reparameterisation_pattern_in_source,
        test_return_dict_shape_unchanged,
    ]:
        try:
            fn()
            print(f"  PASS (may already satisfy): {fn.__name__}")
        except AssertionError as e:
            print(f"  RED (expected): {fn.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR: {fn.__name__}: {e}")
