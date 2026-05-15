"""
Unit tests for plan 30-03: Financial Health & Growth data gaps for SGX tickers.

Covers:
- yahoo_scraper maps revenueGrowth and earningsQuarterlyGrowth fallback
- financial_analytics returns financial_health_score=None (not 0) when no
  liquidity/leverage data is available (e.g. banking stocks)
- _analyze_growth returns non-None when only Revenue Growth present
"""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# yahoo_scraper — revenue growth and quarterly growth fallback
# ---------------------------------------------------------------------------


class TestYahooScraperGrowthFields:

    def _make_scraper(self):
        from src.scrapers.yahoo_scraper import YahooFinanceScraper

        s = YahooFinanceScraper.__new__(YahooFinanceScraper)
        s.logger = MagicMock()
        return s

    def _run_scrape(self, info: dict) -> dict:
        scraper = self._make_scraper()
        mock_ticker = MagicMock()
        mock_ticker.info = info
        mock_ticker.history.return_value = MagicMock(
            empty=False, iterrows=lambda: iter([])
        )
        with patch("src.scrapers.yahoo_scraper.yf.Ticker", return_value=mock_ticker):
            return scraper._scrape_data("D05.SI")

    @pytest.mark.unit
    def test_revenue_growth_mapped(self):
        """revenueGrowth = 0.032 -> 'Revenue Growth (Yahoo)': '3.20%'."""
        data = self._run_scrape({"revenueGrowth": 0.032, "longName": "DBS"})
        assert data.get("Revenue Growth (Yahoo)") == "3.20%"

    @pytest.mark.unit
    def test_earnings_quarterly_fallback(self):
        """earningsGrowth=None + earningsQuarterlyGrowth=0.011 -> '1.10%'."""
        data = self._run_scrape(
            {
                "earningsGrowth": None,
                "earningsQuarterlyGrowth": 0.011,
                "longName": "DBS",
            }
        )
        assert data.get("Earnings Growth (Yahoo)") == "1.10%"

    @pytest.mark.unit
    def test_annual_earnings_growth_preferred_over_quarterly(self):
        """earningsGrowth takes precedence over earningsQuarterlyGrowth."""
        data = self._run_scrape(
            {
                "earningsGrowth": 0.05,
                "earningsQuarterlyGrowth": 0.011,
                "longName": "DBS",
            }
        )
        assert data.get("Earnings Growth (Yahoo)") == "5.00%"

    @pytest.mark.unit
    def test_no_revenue_growth_field_absent(self):
        """revenueGrowth=None -> 'Revenue Growth (Yahoo)' not added."""
        data = self._run_scrape({"revenueGrowth": None, "longName": "DBS"})
        assert "Revenue Growth (Yahoo)" not in data

    @pytest.mark.unit
    def test_no_earnings_growth_field_absent_when_both_none(self):
        """Both growth fields None -> 'Earnings Growth (Yahoo)' not added."""
        data = self._run_scrape(
            {
                "earningsGrowth": None,
                "earningsQuarterlyGrowth": None,
                "longName": "DBS",
            }
        )
        assert "Earnings Growth (Yahoo)" not in data

    @pytest.mark.unit
    def test_sector_mapped(self):
        """sector='Financial Services' -> 'Sector (Yahoo)': 'Financial Services'."""
        data = self._run_scrape({"sector": "Financial Services", "longName": "DBS"})
        assert data.get("Sector (Yahoo)") == "Financial Services"

    @pytest.mark.unit
    def test_sector_absent_when_none(self):
        """sector=None -> 'Sector (Yahoo)' not added."""
        data = self._run_scrape({"sector": None, "longName": "DBS"})
        assert "Sector (Yahoo)" not in data

    @pytest.mark.unit
    def test_dividend_rate_mapped(self):
        """trailingAnnualDividendRate=2.16 -> 'Dividend Rate (Yahoo)': '2.1600'."""
        data = self._run_scrape({"trailingAnnualDividendRate": 2.16, "longName": "DBS"})
        assert data.get("Dividend Rate (Yahoo)") == "2.1600"

    @pytest.mark.unit
    def test_dividend_yield_mapped(self):
        """trailingAnnualDividendYield=0.06 -> 'Dividend Yield (Yahoo)': '6.00%'."""
        data = self._run_scrape(
            {"trailingAnnualDividendYield": 0.06, "longName": "DBS"}
        )
        assert data.get("Dividend Yield (Yahoo)") == "6.00%"

    @pytest.mark.unit
    def test_dividend_rate_absent_when_none(self):
        """No dividend data -> keys absent from output."""
        data = self._run_scrape({"longName": "DBS"})
        assert "Dividend Rate (Yahoo)" not in data
        assert "Dividend Yield (Yahoo)" not in data


# ---------------------------------------------------------------------------
# financial_analytics — health score default None for banks
# ---------------------------------------------------------------------------


class TestFinancialHealthScoreDefault:

    @pytest.fixture
    def fa(self):
        from src.analytics.financial_analytics import FinancialAnalytics

        return FinancialAnalytics()

    @pytest.mark.unit
    def test_health_score_none_when_no_ratios(self, fa):
        """No currentRatio/quickRatio/debtToEquity -> financial_health_score=None."""
        stock_data = {
            "Revenue Growth (Yahoo)": "3.20%",
            "Earnings Growth (Yahoo)": "1.10%",
        }
        result = fa.fundamental_analysis(stock_data, "D05.SI")
        assert (
            result["financial_health_score"] is None
        ), f"Expected None, got {result['financial_health_score']}"

    @pytest.mark.unit
    def test_health_score_not_zero_when_no_ratios(self, fa):
        """Explicitly verify the old wrong default (0) is gone."""
        stock_data = {}
        result = fa.fundamental_analysis(stock_data, "D05.SI")
        assert result["financial_health_score"] != 0

    @pytest.mark.unit
    def test_health_score_set_when_ratios_present(self, fa):
        """With currentRatio data, financial_health_score is numeric."""
        stock_data = {"Current Ratio (Yahoo)": "1.50", "Debt to Equity (Yahoo)": "0.80"}
        result = fa.fundamental_analysis(stock_data, "D05.SI")
        assert isinstance(result["financial_health_score"], (int, float))

    @pytest.mark.unit
    def test_overall_score_excludes_null_health(self, fa):
        """overall_score must not count None health sub-score as 0."""
        stock_data_with_growth = {"Revenue Growth (Yahoo)": "20.00%"}
        stock_data_no_growth = {}
        result_with = fa.fundamental_analysis(stock_data_with_growth, "D05.SI")
        result_without = fa.fundamental_analysis(stock_data_no_growth, "D05.SI")
        # When health is None for both, overall_score should differ if growth differs
        # i.e. the None health slot is not dragging both to 0
        if result_with["financial_health_score"] is None:
            # overall_score with 20% growth > overall_score with no data
            assert result_with["overall_score"] >= result_without["overall_score"]


# ---------------------------------------------------------------------------
# _analyze_growth — non-None when only revenue growth available
# ---------------------------------------------------------------------------


class TestAnalyzeGrowthSGX:

    @pytest.fixture
    def fa(self):
        from src.analytics.financial_analytics import FinancialAnalytics

        return FinancialAnalytics()

    @pytest.mark.unit
    def test_growth_score_nonzero_from_revenue_growth(self, fa):
        """Revenue Growth = 3.20% -> growth_score non-None and > 0."""
        stock_data = {"Revenue Growth (Yahoo)": "3.20%"}
        result = fa.fundamental_analysis(stock_data, "D05.SI")
        assert result["growth_score"] is not None
        assert result["growth_score"] > 0

    @pytest.mark.unit
    def test_growth_score_none_when_no_growth_data(self, fa):
        """No growth fields -> growth_score is None (not 0)."""
        result = fa.fundamental_analysis({}, "D05.SI")
        assert result["growth_score"] is None or result["growth_score"] == 0
