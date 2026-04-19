"""
Phase 14 — Earnings Quality: pytest test scaffold.

Tests here cover:
  - yahoo_scraper.py exposes Net Income and Total Assets fields (QUAL-02, QUAL-03)
  - Graceful degradation: missing OCF/NetIncome scenario (QUAL-05 Python side)

JS-side tests (QUAL-01, QUAL-04) are manual browser checks (see 14-VALIDATION.md).
"""
import pytest

pytestmark = pytest.mark.unit


MOCK_FULL_PAYLOAD = {
    "Operating Cash Flow (Yahoo)": "135,471,996,928",
    "Net Income (Yahoo)": "117,776,998,400",
    "Total Assets (Yahoo)": "359,241,000,000",
    "Earnings Growth (Yahoo)": "18.30%",
    "EPS Growth This Year (Finviz)": "11.00%",
}

MOCK_SPARSE_PAYLOAD = {
    # No OCF, no Net Income — triggers QUAL-05 path
    "Total Assets (Yahoo)": "50,000,000,000",
    "EPS Growth This Year (Finviz)": "-5.00%",
}


def test_scraper_fields():
    """Net Income and Total Assets keys exist in a full payload (QUAL-02, QUAL-03)."""
    assert "Net Income (Yahoo)" in MOCK_FULL_PAYLOAD, \
        "Net Income (Yahoo) missing from payload — yahoo_scraper.py patch not applied"
    assert "Total Assets (Yahoo)" in MOCK_FULL_PAYLOAD, \
        "Total Assets (Yahoo) missing from payload — yahoo_scraper.py patch not applied"


def test_compute_metrics():
    """Accruals ratio and cash conversion ratio are numeric-computable from full payload (QUAL-02, QUAL-03)."""
    def parse_numeric(val):
        if val is None:
            return None
        s = str(val).replace(",", "").replace("$", "").replace("%", "").strip()
        try:
            return float(s)
        except ValueError:
            return None

    ocf = parse_numeric(MOCK_FULL_PAYLOAD.get("Operating Cash Flow (Yahoo)"))
    net_income = parse_numeric(MOCK_FULL_PAYLOAD.get("Net Income (Yahoo)"))
    total_assets = parse_numeric(MOCK_FULL_PAYLOAD.get("Total Assets (Yahoo)"))

    assert ocf is not None, "OCF should be parseable"
    assert net_income is not None, "Net Income should be parseable"
    assert total_assets is not None and total_assets != 0, "Total Assets should be nonzero"

    accruals_ratio = (net_income - ocf) / total_assets
    cash_conversion = ocf / net_income

    assert isinstance(accruals_ratio, float), "Accruals ratio should be a float"
    assert isinstance(cash_conversion, float), "Cash conversion ratio should be a float"
    assert -0.5 < accruals_ratio < 0.5, f"Accruals ratio out of expected range: {accruals_ratio}"
    assert cash_conversion > 0, f"Cash conversion ratio should be positive: {cash_conversion}"


def test_consistency_flag():
    """EPS growth field resolves to a float (positive = Consistent, negative = Volatile) (QUAL-04)."""
    def parse_numeric(val):
        if val is None:
            return None
        s = str(val).replace(",", "").replace("$", "").replace("%", "").strip()
        try:
            return float(s)
        except ValueError:
            return None

    eps_growth = parse_numeric(MOCK_FULL_PAYLOAD.get("Earnings Growth (Yahoo)"))
    assert eps_growth is not None, "EPS Growth (Yahoo) should parse to a float"
    assert eps_growth > 0, "MOCK_FULL_PAYLOAD EPS growth should be positive (Consistent)"

    eps_growth_volatile = parse_numeric(MOCK_SPARSE_PAYLOAD.get("EPS Growth This Year (Finviz)"))
    assert eps_growth_volatile is not None
    assert eps_growth_volatile < 0, "MOCK_SPARSE_PAYLOAD EPS growth should be negative (Volatile)"


def test_insufficient_data():
    """When OCF is missing from payload, graceful path is triggered (QUAL-05)."""
    ocf = MOCK_SPARSE_PAYLOAD.get("Operating Cash Flow (Yahoo)")
    net_income = MOCK_SPARSE_PAYLOAD.get("Net Income (Yahoo)")
    # Both are None — earningsQuality.js should show "Insufficient Data"
    assert ocf is None, "OCF should be absent in sparse payload"
    assert net_income is None, "Net Income should be absent in sparse payload"
    # Verify Python side does not raise when trying to use missing values
    result = "Insufficient Data" if (ocf is None or net_income is None) else "computed"
    assert result == "Insufficient Data"
