"""
MATH-01: Par bond test -- expected_bond_value() with correct coupon discounting.
Benchmark: A par bond (coupon = yield) priced at face value at issuance must return
exactly face value when default probability is zero.
Reference: Standard fixed-income mathematics (Fabozzi).
"""
import numpy as np
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.analytics.credit_transitions import expected_bond_value, RATINGS

pytestmark = pytest.mark.unit


def test_par_bond_aaa_1yr(zero_default_matrix):
    """Par bond: AAA, horizon=1, coupon=5%, face=1000 -> expected_value within 0.01 of 1000."""
    result = expected_bond_value(
        current_rating='AAA',
        horizon=1,
        coupon_rate=0.05,
        face_value=1000.0,
        P=zero_default_matrix,
    )
    # The function returns 'expected_bond_value' key
    val = result.get('expected_bond_value', result.get('expected_value'))
    assert val is not None, "Result dict missing 'expected_bond_value' key"
    assert abs(val - 1000.0) < 0.01, (
        f"Par bond test FAILED: expected ~1000.0, got {val:.4f}. "
        f"Difference {abs(val - 1000.0):.4f} exceeds tolerance 0.01. "
        f"This indicates coupon discounting is still incorrect (MATH-01)."
    )


def test_discounted_coupons_less_than_undiscounted(zero_default_matrix):
    """
    Sanity: PV of coupons (with discounting) must be less than undiscounted sum.
    With T=5 and r=5%, PV annuity = 5% * 1000 * (1 - exp(-0.25)) / 0.05 = ~220.
    Undiscounted sum = 5% * 1000 * 5 = 250.
    """
    result_h5 = expected_bond_value('AAA', 5, coupon_rate=0.05, face_value=1000.0,
                                     P=zero_default_matrix)
    # At horizon=5 the expected value should still be ~1000 (par bond stays at par)
    # but must be less than face + undiscounted coupons (1000 + 250 = 1250)
    val_h5 = result_h5.get('expected_bond_value', result_h5.get('expected_value'))
    assert val_h5 is not None, "Result dict missing 'expected_bond_value' key"
    undiscounted_upper = 1000.0 + 0.05 * 1000.0 * 5  # 1250
    assert val_h5 < undiscounted_upper, (
        f"Horizon=5 value {val_h5:.2f} >= undiscounted upper bound {undiscounted_upper:.2f}. "
        f"Time-value of money is not being applied."
    )


def test_degenerate_inputs_do_not_raise(zero_default_matrix):
    """Zero horizon and zero coupon should not raise -- test fallback path."""
    result = expected_bond_value('AAA', 0, coupon_rate=0.0, face_value=1000.0,
                                  P=zero_default_matrix)
    val = result.get('expected_bond_value', result.get('expected_value'))
    assert val is not None, "Missing 'expected_bond_value' key with zero inputs"
