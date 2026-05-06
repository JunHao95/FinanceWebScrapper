"""
Unit test stubs for Phase 28 price chart helpers.

TestPeriodMap   — pure data, passes immediately (RED→GREEN on creation)
TestAnalystRangeBar — stubs, xfail until build_analyst_range_bar exists
TestColorCoding     — stubs, xfail until color_code_metric exists
"""

import pytest

PERIOD_MAP = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}


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
    @pytest.mark.xfail(
        reason="build_analyst_range_bar not yet implemented", strict=False
    )
    def test_range_bar_with_yahoo_data(self):
        from src.analytics.price_chart import build_analyst_range_bar

        data = {
            "targetLowPrice": 120,
            "targetMeanPrice": 150,
            "targetHighPrice": 180,
            "currentPrice": 140,
        }
        result = build_analyst_range_bar(data)
        assert result is not None
        assert set(result.keys()) >= {"low", "mean", "high", "current"}

    @pytest.mark.xfail(
        reason="build_analyst_range_bar not yet implemented", strict=False
    )
    def test_range_bar_missing_data(self):
        from src.analytics.price_chart import build_analyst_range_bar

        result = build_analyst_range_bar({})
        assert result is None

    @pytest.mark.xfail(
        reason="build_analyst_range_bar not yet implemented", strict=False
    )
    def test_range_bar_falls_back_to_finhub(self):
        from src.analytics.price_chart import build_analyst_range_bar

        data = {
            "priceTargetLow": 120,
            "priceTargetAverage": 150,
            "priceTargetHigh": 180,
            "currentPrice": 140,
        }
        result = build_analyst_range_bar(data)
        assert result is not None
        assert result["low"] == 120


class TestColorCoding:
    @pytest.mark.xfail(reason="color_code_metric not yet implemented", strict=False)
    def test_pe_green(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("P/E Ratio", 12) == "metric-value-good"

    @pytest.mark.xfail(reason="color_code_metric not yet implemented", strict=False)
    def test_pe_red(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("P/E Ratio", 35) == "metric-value-bad"

    @pytest.mark.xfail(reason="color_code_metric not yet implemented", strict=False)
    def test_pe_neutral(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("P/E Ratio", 20) == ""

    @pytest.mark.xfail(reason="color_code_metric not yet implemented", strict=False)
    def test_roe_green(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("ROE", 20) == "metric-value-good"

    @pytest.mark.xfail(reason="color_code_metric not yet implemented", strict=False)
    def test_roe_red(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("ROE", -5) == "metric-value-bad"

    @pytest.mark.xfail(reason="color_code_metric not yet implemented", strict=False)
    def test_debt_equity_red(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("Debt/Equity", 3) == "metric-value-bad"

    @pytest.mark.xfail(reason="color_code_metric not yet implemented", strict=False)
    def test_unknown_metric_neutral(self):
        from src.analytics.price_chart import color_code_metric

        assert color_code_metric("Some Unknown Metric", 99) == ""
