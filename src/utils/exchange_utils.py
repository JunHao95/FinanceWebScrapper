"""
Exchange detection utility.

Extension point for international markets: add a new entry to _EXCHANGE_MAP
to support additional suffixes (e.g. ".HK" for HKEX, ".L" for LSE).
"""

_EXCHANGE_MAP = {
    "SI": {
        "exchange": "SGX",
        "currency": "SGD",
        "currency_symbol": "S$",
        "benchmark": "^STI",
        "google_exchange": "SGX",
        "is_us": False,
    },
    # Future entries (one dict per suffix):
    # "HK": {"exchange": "HKEX", "currency": "HKD", "currency_symbol": "HK$",
    #        "benchmark": "^HSI", "google_exchange": "HKEX", "is_us": False},
    # "L":  {"exchange": "LSE",  "currency": "GBP", "currency_symbol": "£",
    #        "benchmark": "^FTSE", "google_exchange": "LON", "is_us": False},
    # "AX": {"exchange": "ASX",  "currency": "AUD", "currency_symbol": "A$",
    #        "benchmark": "^AXJO", "google_exchange": "ASX", "is_us": False},
    # "T":  {"exchange": "TSE",  "currency": "JPY", "currency_symbol": "¥",
    #        "benchmark": "^N225", "google_exchange": "TYO", "is_us": False},
}

_US_DEFAULTS = {
    "exchange": "US",
    "currency": "USD",
    "currency_symbol": "$",
    "benchmark": "SPY",
    "google_exchange": None,
    "is_us": True,
}


def get_exchange_info(ticker: str) -> dict:
    """Return exchange metadata for a ticker symbol.

    Args:
        ticker: Yahoo Finance ticker (e.g. "D05.SI", "AAPL")

    Returns:
        dict with keys: suffix, exchange, currency, currency_symbol,
        benchmark, google_exchange, is_us
    """
    if "." in ticker:
        suffix = ticker.rsplit(".", 1)[-1].upper()
        info = _EXCHANGE_MAP.get(suffix)
        if info:
            return {"suffix": suffix, **info}
    return {"suffix": "", **_US_DEFAULTS}
