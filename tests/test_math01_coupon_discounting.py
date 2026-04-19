"""
TDD tests for MATH-01: credit_transitions.py coupon discounting fix.

These tests verify:
1. Par bond test: expected_bond_value('AAA', 1, coupon_rate=0.05, face_value=1000)
   with zero-default matrix returns within 0.01 of 1000.0
2. Time-value test: 5-year result < 1250 (undiscounted upper bound)
3. Regression guard: discount_rate=0 or horizon=0 does not raise
4. Source code uses continuous-discounting annuity formula (1 - exp(-r*T)/r)
"""
import sys
sys.path.insert(0, '/Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper')

import numpy as np
import pytest

pytestmark = pytest.mark.unit


def _zero_default_matrix():
    """Identity matrix: every rating stays put, no defaults, no migrations."""
    from src.analytics.credit_transitions import RATINGS
    return np.eye(len(RATINGS))


def test_par_bond_returns_face_value():
    """Test 1: Zero-default matrix, 1-year AAA par bond should equal ~1000.0."""
    from src.analytics.credit_transitions import expected_bond_value
    P_test = _zero_default_matrix()
    result = expected_bond_value('AAA', 1, coupon_rate=0.05, face_value=1000.0, P=P_test)
    val = result['expected_value'] if 'expected_value' in result else result['expected_bond_value']
    assert abs(val - 1000.0) < 0.01, (
        f"Par bond test failed: returned {val:.4f}, expected ~1000.0 (within 0.01). "
        f"Undiscounted coupons would return ~1050."
    )


def test_time_value_applied_over_5_years():
    """Test 2: 5-year value must be less than face + undiscounted coupons (1250)."""
    from src.analytics.credit_transitions import expected_bond_value
    P_test = _zero_default_matrix()
    result = expected_bond_value('AAA', 5, coupon_rate=0.05, face_value=1000.0, P=P_test)
    val = result['expected_value'] if 'expected_value' in result else result['expected_bond_value']
    undiscounted_upper = 1000.0 + 5 * 50.0  # 1250
    assert val < undiscounted_upper, (
        f"Time-value not applied: returned {val:.4f}, must be < {undiscounted_upper} (undiscounted sum)"
    )


def test_degenerate_inputs_no_raise():
    """Test 3: horizon=0 and coupon_rate=0 should not raise."""
    from src.analytics.credit_transitions import expected_bond_value
    P_test = _zero_default_matrix()
    # Should not raise
    result1 = expected_bond_value('AAA', 0, coupon_rate=0.00, face_value=1000.0, P=P_test)
    result2 = expected_bond_value('AAA', 1, coupon_rate=0.00, face_value=1000.0, P=P_test)
    assert result1 is not None, "horizon=0, coupon=0 returned None"
    assert result2 is not None, "coupon=0 returned None"


def test_continuous_discounting_formula_in_source():
    """Test 4: Source code must use continuous-discounting annuity formula."""
    import inspect
    from src.analytics import credit_transitions
    src = inspect.getsource(credit_transitions.expected_bond_value)
    assert '1 - np.exp' in src or '1.0 - np.exp' in src, (
        "Continuous-discounting formula (1 - exp(-r*T)) not found in expected_bond_value source. "
        "Undiscounted formula 'coupon_rate * face_value * horizon' still in place."
    )


if __name__ == '__main__':
    print("Running RED-phase tests (all should FAIL before fix):")

    for fn in [
        test_par_bond_returns_face_value,
        test_time_value_applied_over_5_years,
        test_degenerate_inputs_no_raise,
        test_continuous_discounting_formula_in_source,
    ]:
        try:
            fn()
            print(f"  UNEXPECTED PASS: {fn.__name__}")
        except AssertionError as e:
            print(f"  RED (expected): {fn.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR: {fn.__name__}: {e}")
