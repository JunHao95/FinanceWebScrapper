"""
TEST-03 traceability: ml_models ROADMAP requirement.

ml_models.py does not exist as a standalone module in src/.
ML functionality is covered by:
  - test_regime_detection.py  → HMM (RegimeDetector class)
  - test_unit_financial_analytics.py → scoring / fundamentals

This file verifies those modules are importable and their key ML classes/functions
are accessible, satisfying the TEST-03 requirement for ml_models coverage.
"""
import pytest


# ---------------------------------------------------------------------------
# Import smoke tests — verify ML modules are importable
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_regime_detector_importable():
    from src.analytics.regime_detection import RegimeDetector
    rd = RegimeDetector()
    assert rd is not None


@pytest.mark.unit
def test_regime_detector_has_fit_method():
    from src.analytics.regime_detection import RegimeDetector
    assert callable(getattr(RegimeDetector, 'fit', None))


@pytest.mark.unit
def test_financial_analytics_importable():
    from src.analytics.financial_analytics import FinancialAnalytics
    fa = FinancialAnalytics()
    assert fa is not None


@pytest.mark.unit
def test_financial_analytics_has_fundamental_analysis():
    from src.analytics.financial_analytics import FinancialAnalytics
    assert callable(getattr(FinancialAnalytics, 'fundamental_analysis', None))


# ---------------------------------------------------------------------------
# Thin ML behaviour tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_regime_detector_rejects_non_two_states():
    from src.analytics.regime_detection import RegimeDetector
    with pytest.raises(ValueError):
        RegimeDetector(n_states=3)


@pytest.mark.unit
def test_regime_detector_fit_rejects_empty_array():
    import numpy as np
    from src.analytics.regime_detection import RegimeDetector
    rd = RegimeDetector()
    with pytest.raises((ValueError, RuntimeError)):
        rd.fit(np.array([]))


@pytest.mark.unit
def test_regime_detector_fit_rejects_nan():
    import numpy as np
    from src.analytics.regime_detection import RegimeDetector
    rd = RegimeDetector()
    with pytest.raises((ValueError, RuntimeError)):
        rd.fit(np.array([0.01, np.nan, -0.02]))


@pytest.mark.unit
def test_regime_detector_fit_synthetic_returns():
    import numpy as np
    from src.analytics.regime_detection import RegimeDetector
    rng = np.random.default_rng(99)
    returns = np.concatenate([
        rng.normal(0.001, 0.005, 200),   # calm
        rng.normal(-0.002, 0.020, 100),  # stressed
    ])
    rd = RegimeDetector()
    result = rd.fit(returns)
    assert isinstance(result, dict)
    assert rd.mu is not None
    assert rd.sigma is not None
    assert len(rd.sigma) == 2
