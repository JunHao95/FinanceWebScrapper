"""
Unit tests for src/analytics/financial_analytics.py

Covers: fundamental_analysis, _analyze_valuation, _analyze_profitability,
_analyze_financial_health, _analyze_growth, compute_pct_increase,
_parse_numeric_value, _extract_metric, _interpret_regression.

No live network calls — all inputs are synthetic dicts.
"""
import pytest
from src.analytics.financial_analytics import FinancialAnalytics


@pytest.fixture
def fa():
    return FinancialAnalytics()


# ---------------------------------------------------------------------------
# compute_pct_increase — happy path + edge cases
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_pct_increase_basic(fa):
    assert fa.compute_pct_increase(100, 110, 100) == pytest.approx(10.0)


@pytest.mark.unit
def test_pct_increase_loss(fa):
    assert fa.compute_pct_increase(100, 90, 100) == pytest.approx(-10.0)


@pytest.mark.unit
def test_pct_increase_zero_investment_returns_none(fa):
    assert fa.compute_pct_increase(100, 110, 0) is None


@pytest.mark.unit
def test_pct_increase_no_change(fa):
    assert fa.compute_pct_increase(100, 100, 200) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# _parse_numeric_value
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_parse_numeric_int(fa):
    assert fa._parse_numeric_value(42) == pytest.approx(42.0)


@pytest.mark.unit
def test_parse_numeric_float(fa):
    assert fa._parse_numeric_value(3.14) == pytest.approx(3.14)


@pytest.mark.unit
def test_parse_numeric_str_pct(fa):
    assert fa._parse_numeric_value('15.5%') == pytest.approx(15.5)


@pytest.mark.unit
def test_parse_numeric_str_B(fa):
    assert fa._parse_numeric_value('2B') == pytest.approx(2_000_000_000.0)


@pytest.mark.unit
def test_parse_numeric_str_M(fa):
    assert fa._parse_numeric_value('500M') == pytest.approx(500_000_000.0)


@pytest.mark.unit
def test_parse_numeric_str_K(fa):
    assert fa._parse_numeric_value('250K') == pytest.approx(250_000.0)


# ---------------------------------------------------------------------------
# fundamental_analysis — happy path with known metrics
# ---------------------------------------------------------------------------

GOOD_STOCK = {
    'P/E Ratio': 12.0,
    'P/B Ratio': 1.2,
    'ROE': 22.0,
    'Profit Margin': 25.0,
    'Debt to Equity': 0.3,
    'Current Ratio': 2.5,
    'Free Cash Flow': 5_000_000_000,
    'Revenue Growth': 15.0,
    'Earnings Growth': 18.0,
}


@pytest.mark.unit
def test_fundamental_analysis_returns_dict(fa):
    result = fa.fundamental_analysis(GOOD_STOCK, 'GOOD')
    assert isinstance(result, dict)
    assert result.get('ticker') == 'GOOD'


@pytest.mark.unit
def test_fundamental_analysis_good_stock_gets_buy_rating(fa):
    result = fa.fundamental_analysis(GOOD_STOCK, 'GOOD')
    assert result['investment_outlook'] in ('Buy', 'Strong Buy', 'Moderate Buy')


@pytest.mark.unit
def test_fundamental_analysis_overall_score_in_range(fa):
    result = fa.fundamental_analysis(GOOD_STOCK, 'GOOD')
    assert 0 <= result['overall_score'] <= 10


@pytest.mark.unit
def test_fundamental_analysis_has_required_keys(fa):
    result = fa.fundamental_analysis(GOOD_STOCK, 'GOOD')
    for k in ('valuation_score', 'profitability_score', 'financial_health_score',
               'growth_score', 'overall_score', 'investment_outlook',
               'key_strengths', 'key_concerns', 'summary'):
        assert k in result


@pytest.mark.unit
def test_fundamental_analysis_bad_stock_gets_sell_rating(fa):
    bad_stock = {
        'P/E Ratio': 80.0,
        'P/B Ratio': 12.0,
        'ROE': -5.0,
        'Profit Margin': -10.0,
        'Debt to Equity': 5.0,
        'Revenue Growth': -20.0,
    }
    result = fa.fundamental_analysis(bad_stock, 'BAD')
    assert result['investment_outlook'] in ('Sell', 'Moderate Sell')


# ---------------------------------------------------------------------------
# fundamental_analysis — edge case: empty data degrades gracefully
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_fundamental_analysis_empty_data_no_crash(fa):
    result = fa.fundamental_analysis({}, 'EMPTY')
    assert isinstance(result, dict)
    assert 'investment_outlook' in result


@pytest.mark.unit
def test_fundamental_analysis_partial_data_no_crash(fa):
    partial = {'ROE': 18.0}
    result = fa.fundamental_analysis(partial, 'PARTIAL')
    assert isinstance(result, dict)
    assert result['overall_score'] >= 0


# ---------------------------------------------------------------------------
# _interpret_regression
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_interpret_regression_high_beta(fa):
    text = fa._interpret_regression(beta=1.5, alpha=0.001, r_squared=0.8)
    assert 'High volatility' in text or 'amplifies' in text.lower()


@pytest.mark.unit
def test_interpret_regression_negative_beta(fa):
    text = fa._interpret_regression(beta=-0.3, alpha=0.0, r_squared=0.2)
    assert 'Negative' in text or 'negative' in text


# ---------------------------------------------------------------------------
# _extract_metric — nested dict lookup
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_extract_metric_direct_key(fa):
    data = {'P/E Ratio': 20.0}
    val = fa._extract_metric(data, ['P/E Ratio'])
    assert val == pytest.approx(20.0)


@pytest.mark.unit
def test_extract_metric_nested_section(fa):
    data = {'valuation': {'P/E Ratio': 18.0}}
    val = fa._extract_metric(data, ['P/E Ratio'])
    assert val == pytest.approx(18.0)


@pytest.mark.unit
def test_extract_metric_missing_returns_none(fa):
    val = fa._extract_metric({}, ['Nonexistent Metric'])
    assert val is None


@pytest.mark.unit
def test_extract_metric_na_string_returns_none(fa):
    val = fa._extract_metric({'P/E Ratio': 'N/A'}, ['P/E Ratio'])
    assert val is None
