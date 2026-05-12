"""Unit tests for src/utils/exchange_utils.py"""

from src.utils.exchange_utils import get_exchange_info


class TestGetExchangeInfo:
    def test_si_suffix_returns_sgx(self):
        info = get_exchange_info("D05.SI")
        assert info["suffix"] == "SI"
        assert info["exchange"] == "SGX"
        assert info["currency"] == "SGD"
        assert info["currency_symbol"] == "S$"
        assert info["benchmark"] == "^STI"
        assert info["google_exchange"] == "SGX"
        assert info["is_us"] is False

    def test_si_suffix_case_insensitive(self):
        info = get_exchange_info("D05.si")
        assert info["exchange"] == "SGX"
        assert info["is_us"] is False

    def test_us_ticker_no_suffix_returns_defaults(self):
        info = get_exchange_info("AAPL")
        assert info["suffix"] == ""
        assert info["is_us"] is True
        assert info["benchmark"] == "SPY"
        assert info["currency"] == "USD"
        assert info["currency_symbol"] == "$"
        assert info["google_exchange"] is None

    def test_us_ticker_with_unknown_suffix_returns_defaults(self):
        info = get_exchange_info("XYZ.ZZ")
        assert info["is_us"] is True
        assert info["benchmark"] == "SPY"

    def test_msft_returns_us_defaults(self):
        info = get_exchange_info("MSFT")
        assert info["is_us"] is True
        assert info["currency"] == "USD"

    def test_benchmark_is_sti_for_sgx(self):
        for ticker in ["D05.SI", "O39.SI", "U11.SI"]:
            assert get_exchange_info(ticker)["benchmark"] == "^STI"

    def test_returns_dict_with_required_keys(self):
        required = {
            "suffix",
            "exchange",
            "currency",
            "currency_symbol",
            "benchmark",
            "google_exchange",
            "is_us",
        }
        assert required.issubset(get_exchange_info("D05.SI").keys())
        assert required.issubset(get_exchange_info("AAPL").keys())
