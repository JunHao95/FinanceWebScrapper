"""
Unit tests for Phase 28 price chart helpers.

TestPeriodMap       — pure data, passes immediately
TestAnalystRangeBar — tests recommendationKey extraction in yahoo_scraper.py
TestColorCoding     — exercises src.analytics.price_chart.color_code_metric
"""

from unittest.mock import patch, MagicMock

PERIOD_MAP = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}


def _make_scraper():
    from src.scrapers.yahoo_scraper import YahooFinanceScraper

    return YahooFinanceScraper()


def _scrape_with_info(info_dict):
    """Call _scrape_data with mocked yfinance info; suppress web-scraping via exception."""
    scraper = _make_scraper()
    mock_ticker = MagicMock()
    mock_ticker.info = info_dict
    with patch(
        "src.scrapers.yahoo_scraper.make_request", side_effect=Exception("no network")
    ), patch("src.scrapers.yahoo_scraper.yf.Ticker", return_value=mock_ticker):
        return scraper._scrape_data("AAPL")


class TestPeriodMap:
    def test_period_map_1mo(self):
        assert PERIOD_MAP["1mo"] == 30

    def test_period_map_3mo(self):
        assert PERIOD_MAP["3mo"] == 90

    def test_period_map_6mo(self):
        assert PERIOD_MAP["6mo"] == 180

    def test_period_map_1y(self):
        assert PERIOD_MAP["1y"] == 365

    def test_unknown_period_defaults_90(self):
        assert PERIOD_MAP.get("bad", 90) == 90


class TestAnalystRangeBar:
    def test_range_bar_with_yahoo_data(self):
        """recommendationKey present → Analyst Recommendation (Yahoo) set."""
        data = _scrape_with_info(
            {
                "targetLowPrice": 120.0,
                "targetMeanPrice": 150.0,
                "targetHighPrice": 180.0,
                "currentPrice": 140.0,
                "recommendationKey": "buy",
            }
        )
        assert data.get("Analyst Recommendation (Yahoo)") == "buy"

    def test_range_bar_missing_data(self):
        """recommendationKey absent → field not present in data dict."""
        data = _scrape_with_info({})
        assert "Analyst Recommendation (Yahoo)" not in data

    def test_range_bar_falls_back_to_finhub(self):
        """recommendationKey = 'strong_buy' → normalised to lowercase."""
        data = _scrape_with_info({"recommendationKey": "STRONG_BUY"})
        assert data.get("Analyst Recommendation (Yahoo)") == "strong_buy"


class TestColorCoding:
    def test_pe_green(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("P/E Ratio", 12) == "metric-value-good"

    def test_pe_red(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("P/E Ratio", 35) == "metric-value-bad"

    def test_pe_neutral(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("P/E Ratio", 20) == ""

    def test_roe_green(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("ROE", 20) == "metric-value-good"

    def test_roe_red(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("ROE", -5) == "metric-value-bad"

    def test_debt_equity_red(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("Debt/Equity", 3) == "metric-value-bad"

    def test_unknown_metric_neutral(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("Some Unknown Metric", 99) == ""
