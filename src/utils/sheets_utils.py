"""
Google Sheets export utilities for FinanceWebScrapper.

Provides serialize_value, get_sheets_client, and export_tickers_to_sheets.
Authentication uses a service account credentials JSON file whose path is
read from GOOGLE_SHEETS_CREDENTIALS_PATH at call time (not at import time).
"""

import logging
import os
from datetime import date

import gspread
import gspread.exceptions
from dotenv import load_dotenv
from gspread.utils import ValueInputOption

load_dotenv()
logger = logging.getLogger(__name__)

# 20-column export schema — order is fixed and referenced by tests
COLUMN_HEADERS = [
    "Export Date",
    "Ticker",
    "Price",
    "P/E",
    "Forward P/E",
    "P/B",
    "EPS",
    "RSI",
    "MA10 Signal",
    "MA20 Signal",
    "MA50 Signal",
    "Sentiment Score",
    "Revenue",
    "Profit Margin",
    "Operating Margin",
    "Debt/Equity",
    "Health Score",
    "Earnings Quality Flag",
    "DCF Intrinsic Value",
    "Peer P/E Percentile",
]


def serialize_value(v):
    """Coerce a value to a Sheets-safe type (str/int/float/"")."""
    if v is None:
        return ""
    if isinstance(v, bool):  # bool before int — bool is a subclass of int
        return str(v)
    if isinstance(v, (int, float)):
        return v
    return str(v)


def get_sheets_client():
    """Return an authenticated gspread client using service account credentials.

    Reads GOOGLE_SHEETS_CREDENTIALS_PATH from environment at call time.
    Raises FileNotFoundError with a human-readable message if the env var
    is absent or the file does not exist at that path.
    """
    creds_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH", "").strip()
    if not creds_path:
        raise FileNotFoundError(
            "GOOGLE_SHEETS_CREDENTIALS_PATH is not set in .env. "
            "See README.md 'Google Sheets Setup' for instructions."
        )
    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            f"Credentials file not found at: {creds_path!r}. "
            "Check GOOGLE_SHEETS_CREDENTIALS_PATH in .env"
        )
    return gspread.service_account(filename=creds_path)


def export_tickers_to_sheets(tickers, data):
    """Export stock data for *tickers* to the configured Google Spreadsheet.

    Args:
        tickers: list of ticker strings (e.g. ["AAPL", "MSFT"])
        data: dict mapping ticker → dict of field_name → value

    Returns:
        int: number of rows appended (0 if tickers is empty)

    Raises:
        ValueError: if GOOGLE_SHEETS_SPREADSHEET_ID is not set
        FileNotFoundError: if credentials are missing (from get_sheets_client)
        gspread.exceptions.SpreadsheetNotFound: if spreadsheet cannot be opened
    """
    if not tickers:
        return 0

    spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
    if not spreadsheet_id:
        raise ValueError(
            "GOOGLE_SHEETS_SPREADSHEET_ID is not set in .env. "
            "See README.md 'Google Sheets Setup' for instructions."
        )

    gc = get_sheets_client()
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.get_worksheet(0)

    export_date = date.today().strftime("%Y-%m-%d")

    rows = []
    for ticker in tickers:
        ticker_data = data.get(ticker, {})

        # Multi-key fallbacks for fields whose scraper key names vary
        pe = ticker_data.get(
            "P/E Ratio (Yahoo)", ticker_data.get("P/E Ratio", ticker_data.get("P/E"))
        )
        fwd_pe = ticker_data.get("Forward P/E", ticker_data.get("Forward P/E Ratio"))
        pb = ticker_data.get("P/B Ratio", ticker_data.get("P/B"))
        ma10 = ticker_data.get("MA10 Signal", ticker_data.get("10-Day MA Signal"))
        ma20 = ticker_data.get("MA20 Signal", ticker_data.get("20-Day MA Signal"))
        ma50 = ticker_data.get("MA50 Signal", ticker_data.get("50-Day MA Signal"))
        debt_eq = ticker_data.get("Debt/Equity", ticker_data.get("Debt/Equity Ratio"))

        row = [
            export_date,
            ticker,
            serialize_value(ticker_data.get("Price")),
            serialize_value(pe),
            serialize_value(fwd_pe),
            serialize_value(pb),
            serialize_value(ticker_data.get("EPS")),
            serialize_value(ticker_data.get("RSI")),
            serialize_value(ma10),
            serialize_value(ma20),
            serialize_value(ma50),
            serialize_value(ticker_data.get("Sentiment Score")),
            serialize_value(ticker_data.get("Revenue")),
            serialize_value(ticker_data.get("Profit Margin")),
            serialize_value(ticker_data.get("Operating Margin")),
            serialize_value(debt_eq),
            serialize_value(ticker_data.get("Health Score")),
            serialize_value(ticker_data.get("Earnings Quality Flag")),
            serialize_value(ticker_data.get("DCF Intrinsic Value")),
            serialize_value(ticker_data.get("Peer P/E Percentile")),
        ]
        rows.append(row)

    worksheet.append_rows(rows, value_input_option=ValueInputOption.user_entered)
    logger.info("Appended %d rows to Google Sheet %s", len(rows), spreadsheet_id)
    return len(rows)
