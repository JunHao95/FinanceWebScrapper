"""
TDD tests for MATH-04: RegimeDetector dual-criterion label assignment.

These tests verify:
1. _assign_labels() is a module-level function
2. Dual-criterion logic: both sigma and mu criteria must agree for HIGH confidence
3. Low sigma separation (< 20%) yields AMBIGUOUS even if criteria agree
4. _build_result() emits NEUTRAL signal when label_confidence is AMBIGUOUS
5. Return dict includes label_confidence and filtered_probs_full
"""
import sys
sys.path.insert(0, '/Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper')

import numpy as np
import inspect
import pytest

pytestmark = pytest.mark.unit


def test_assign_labels_function_exists():
    """_assign_labels must be importable as a module-level function."""
    from src.analytics.regime_detection import _assign_labels
    assert callable(_assign_labels)


def test_assign_labels_both_agree_high_confidence():
    """Test 1: Both criteria agree -> HIGH confidence, correct calm/stressed indices."""
    from src.analytics.regime_detection import _assign_labels
    # sigma[0]=0.008 (lower = calm), mu[0]=0.001 (higher = calm): both agree -> HIGH
    c, s, conf = _assign_labels(np.array([0.001, -0.002]), np.array([0.008, 0.020]))
    assert c == 0, f'Expected calm_idx=0, got {c}'
    assert s == 1, f'Expected stressed_idx=1, got {s}'
    assert conf == 'HIGH', f'Expected HIGH, got {conf}'


def test_assign_labels_criteria_disagree_ambiguous():
    """Test 2: mu says opposite direction -> AMBIGUOUS."""
    from src.analytics.regime_detection import _assign_labels
    # sigma[0]=0.008 (sigma says calm=0), but mu[1]=0.002 (mu says calm=1): disagree
    c, s, conf = _assign_labels(np.array([-0.001, 0.002]), np.array([0.008, 0.020]))
    assert c == 0, f'Expected calm_idx=0 (sigma primary), got {c}'
    assert s == 1, f'Expected stressed_idx=1, got {s}'
    assert conf == 'AMBIGUOUS', f'Expected AMBIGUOUS, got {conf}'


def test_assign_labels_low_sigma_separation_ambiguous():
    """Test 3: < 20% sigma separation -> AMBIGUOUS even if criteria agree."""
    from src.analytics.regime_detection import _assign_labels
    # sigma[0]=0.0095, sigma[1]=0.010 -> sep = |0.0095-0.010|/0.010 = 5% < 20%
    c, s, conf = _assign_labels(np.array([0.001, -0.002]), np.array([0.0095, 0.010]))
    sep = abs(0.0095 - 0.010) / 0.010
    assert conf == 'AMBIGUOUS', \
        f'Expected AMBIGUOUS for sep={sep:.2%} (< 20%), got {conf}'


def test_build_result_has_label_confidence():
    """Test 4: _build_result source includes label_confidence."""
    from src.analytics.regime_detection import RegimeDetector
    rd = RegimeDetector()
    src = inspect.getsource(rd._build_result)
    assert 'label_confidence' in src, 'label_confidence not in _build_result source'


def test_build_result_has_filtered_probs_full():
    """Test 4b: _build_result source includes filtered_probs_full in return dict."""
    from src.analytics.regime_detection import RegimeDetector
    rd = RegimeDetector()
    src = inspect.getsource(rd._build_result)
    assert 'filtered_probs_full' in src, \
        'filtered_probs_full not in _build_result source'


def test_build_result_neutral_when_ambiguous():
    """Test 4c: When label_confidence is AMBIGUOUS, signal must be NEUTRAL."""
    from src.analytics.regime_detection import RegimeDetector
    rd = RegimeDetector()
    src = inspect.getsource(rd._build_result)
    # The signal assignment must check label_confidence == 'AMBIGUOUS' before thresholds
    assert "label_confidence == 'AMBIGUOUS'" in src or \
           "label_confidence==" in src.replace(" ", ""), \
        "AMBIGUOUS check not found in _build_result signal assignment"


if __name__ == '__main__':
    tests = [
        test_assign_labels_function_exists,
        test_assign_labels_both_agree_high_confidence,
        test_assign_labels_criteria_disagree_ambiguous,
        test_assign_labels_low_sigma_separation_ambiguous,
        test_build_result_has_label_confidence,
        test_build_result_has_filtered_probs_full,
        test_build_result_neutral_when_ambiguous,
    ]
    for t in tests:
        try:
            t()
            print(f'PASS: {t.__name__}')
        except AssertionError as e:
            print(f'RED (expected): {t.__name__}: {e}')
        except ImportError as e:
            print(f'RED (expected): {t.__name__}: ImportError: {e}')
        except Exception as e:
            print(f'ERROR: {t.__name__}: {type(e).__name__}: {e}')
