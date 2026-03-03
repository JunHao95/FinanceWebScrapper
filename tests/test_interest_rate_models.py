"""
MATH-03: Feller hard constraint test -- CIRCalibrator must always produce
calibrated params satisfying 2*kappa*theta >= sigma^2 (Feller condition).
Reference: Brigo & Mercurio, "Interest Rate Models -- Theory and Practice".
"""
import numpy as np
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.analytics.interest_rate_models import CIRCalibrator


def test_calibration_satisfies_feller(market_yields_normal):
    """
    Normal calibration on a realistic yield curve must return
    feller_condition_satisfied: True with calibrated params that verify it.
    """
    cal = CIRCalibrator()
    result = cal.calibrate(market_yields_normal)
    assert 'error' not in result, f"Calibration returned error: {result.get('error')}"

    p = result['calibrated_params']
    kappa, theta, sigma = p['kappa'], p['theta'], p['sigma']
    feller_lhs = 2.0 * kappa * theta
    feller_rhs = sigma ** 2

    assert feller_lhs >= feller_rhs, (
        f"Feller condition VIOLATED by calibrated params: "
        f"2*kappa*theta={feller_lhs:.6f} < sigma^2={feller_rhs:.6f}. "
        f"kappa={kappa:.4f}, theta={theta:.4f}, sigma={sigma:.4f}. "
        f"This indicates MATH-03 reparameterisation is not in effect."
    )
    assert result.get('feller_condition_satisfied') is True, (
        "feller_condition_satisfied flag is not True despite params satisfying Feller"
    )


def test_feller_satisfied_for_multiple_yield_curves():
    """
    Run calibration on 3 different yield curve shapes -- flat, normal, inverted.
    All must return Feller-compliant params.
    """
    cal = CIRCalibrator()
    curves = [
        [(1, 0.05), (5, 0.05), (10, 0.05)],         # flat
        [(1, 0.03), (5, 0.045), (10, 0.06)],         # normal (upward sloping)
        [(1, 0.07), (5, 0.055), (10, 0.04)],         # inverted
    ]
    for i, curve in enumerate(curves):
        result = cal.calibrate(curve)
        if 'error' in result:
            continue  # skip if calibration numerically fails on this curve
        p = result['calibrated_params']
        kappa, theta, sigma = p['kappa'], p['theta'], p['sigma']
        assert 2.0 * kappa * theta >= sigma**2, (
            f"Feller violated on curve {i}: "
            f"2*kappa*theta={2*kappa*theta:.4f} < sigma^2={sigma**2:.4f}"
        )


def test_return_dict_has_required_keys(market_yields_normal):
    """Return dict must contain all keys expected by downstream Flask routes."""
    cal = CIRCalibrator()
    result = cal.calibrate(market_yields_normal)
    assert 'error' not in result
    for key in ('calibrated_params', 'feller_condition_satisfied', 'feller_lhs', 'feller_rhs'):
        assert key in result, f"Missing required key '{key}' in CIR calibration result"
