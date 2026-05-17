"""
Google Sheets export utilities for FinanceWebScrapper.

Provides serialize_value, get_sheets_client, and export_tickers_to_sheets.
Authentication uses a service account credentials JSON file whose path is
read from GOOGLE_SHEETS_CREDENTIALS_PATH at call time (not at import time).

Tab routing and column mapping
-------------------------------
US Stock  (existing cols A-AG, indices 0-32) + scraper extras starting at AH (33):
  C(2)=Google Quote, D(3)=Google Price, F(5)=EPS, G(6)=P/E Yahoo,
  K(10)=Yahoo Quote, L(11)=Yahoo Price, AC(28)=Price Target (DCF)
  AH(33)=Export Date, AI(34)=Fwd P/E, AJ(35)=P/B, AK(36)=RSI,
  AL(37)=MA10, AM(38)=MA20, AN(39)=MA50, AO(40)=Sentiment,
  AP(41)=Revenue, AQ(42)=Profit Margin, AR(43)=Op Margin,
  AS(44)=Debt/Equity, AT(45)=Health Score, AU(46)=EQ Flag, AV(47)=Peer P/E

SG Stock  (existing cols A-AC, indices 0-28) + scraper extras starting at AD (29):
  C(2)=Google Quote, D(3)=Google Price, E(4)=P/E, F(5)=Yahoo Quote,
  G(6)=Yahoo Price, X(23)=P/B, Y(24)=Fwd P/E
  AD(29)=Export Date, AE(30)=EPS, AF(31)=RSI, AG(32)=MA10, AH(33)=MA20,
  AI(34)=MA50, AJ(35)=Sentiment, AK(36)=Revenue, AL(37)=Profit Margin,
  AM(38)=Op Margin, AN(39)=Debt/Equity, AO(40)=Health Score,
  AP(41)=EQ Flag, AQ(42)=DCF, AR(43)=Peer P/E

HK Stock  (existing cols A-AA, indices 0-26) + scraper extras starting at AB (27):
  C(2)=Google Quote, D(3)=Google Price, E(4)=Yahoo Quote, F(5)=Yahoo Price,
  W(22)=P/B, X(23)=Fwd P/E
  AB(27)=Export Date, AC(28)=EPS, AD(29)=P/E, AE(30)=RSI, AF(31)=MA10,
  AG(32)=MA20, AH(33)=MA50, AI(34)=Sentiment, AJ(35)=Revenue,
  AK(36)=Profit Margin, AL(37)=Op Margin, AM(38)=Debt/Equity,
  AN(39)=Health Score, AO(40)=EQ Flag, AP(41)=DCF, AQ(42)=Peer P/E

Others Stock  (auto-created, flat 20-column schema)
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

# Used only for auto-created "Others Stock" tab header
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

_TAB_US = "US Stock"
_TAB_SG = "SG Stock"
_TAB_HK = "HK Stock"
_TAB_OTHERS = "Others Stock"

# Column counts for existing tabs (determines where extra scraper cols start)
_US_EXISTING_COLS = 33  # A-AG
_SG_EXISTING_COLS = 29  # A-AC
_HK_EXISTING_COLS = 27  # A-AA


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


def _classify_ticker(ticker):
    """Return destination sheet tab name based on ticker suffix."""
    upper = ticker.upper()
    if upper.endswith(".SI"):
        return _TAB_SG
    if upper.endswith(".HK"):
        return _TAB_HK
    if "." not in ticker:
        return _TAB_US
    return _TAB_OTHERS


def _get_or_create_worksheet(sh, tab_name):
    """Return worksheet by name, creating it with a header row if absent."""
    try:
        return sh.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab_name, rows=1000, cols=len(COLUMN_HEADERS))
        ws.update(
            "A1", [COLUMN_HEADERS], value_input_option=ValueInputOption.user_entered
        )
        logger.info("Created new sheet tab: %s", tab_name)
        return ws


def _append_below_existing(ws, rows):
    """Write rows after the last non-empty row, anchored to column A."""
    existing = ws.get_all_values()
    next_row = len(existing) + 1
    ws.update(f"A{next_row}", rows, value_input_option=ValueInputOption.user_entered)


def _extract_fields(ticker_data):
    """Normalize scraper field names (source-suffixed) into a flat dict."""

    def _first(*keys):
        for k in keys:
            v = ticker_data.get(k)
            if v is not None:
                return v
        return None

    return {
        "price": _first(
            "Price",
            "Current Price (Yahoo)",
            "Current Price (Finviz)",
            "Current Price (Google)",
        ),
        "pe": _first(
            "P/E Ratio (Yahoo)",
            "P/E Ratio (Google)",
            "P/E Ratio (Finviz)",
            "P/E Ratio (AlphaVantage)",
            "P/E Ratio",
            "P/E",
        ),
        "fwd_pe": _first(
            "Forward P/E (Yahoo)",
            "Forward P/E (Finviz)",
            "Forward P/E (AlphaVantage)",
            "Forward P/E",
            "Forward P/E Ratio",
        ),
        "pb": _first(
            "P/B Ratio (Yahoo)",
            "P/B Ratio (Google)",
            "P/B Ratio (Finviz)",
            "P/B Ratio (AlphaVantage)",
            "P/B Ratio",
            "P/B",
        ),
        "eps": _first(
            "EPS (Yahoo)",
            "EPS (Google)",
            "EPS (AlphaVantage)",
            "EPS (TTM) (Finviz)",
            "EPS",
        ),
        "rsi": _first(
            "RSI (14) (Technical)",
            "RSI (Technical)",
            "RSI",
        ),
        "ma10": _first("MA10 Signal (Technical)", "MA10 Signal", "10-Day MA Signal"),
        "ma20": _first("MA20 Signal (Technical)", "MA20 Signal", "20-Day MA Signal"),
        "ma50": _first("MA50 Signal (Technical)", "MA50 Signal", "50-Day MA Signal"),
        "sentiment": _first(
            "Overall Sentiment Score (Enhanced)",
            "Sentiment Score",
        ),
        "revenue": _first(
            "Revenue",
            "Revenue Growth (Yahoo)",
        ),
        "profit_margin": _first(
            "Profit Margin (Yahoo)",
            "Profit Margin (Finviz)",
            "Profit Margin (AlphaVantage)",
            "Profit Margin",
        ),
        "op_margin": _first(
            "Operating Margin (Yahoo)",
            "Operating Margin (Finviz)",
            "Operating Margin (AlphaVantage)",
            "Operating Margin",
        ),
        "debt_eq": _first(
            "Debt to Equity (Yahoo)",
            "Debt/Equity",
            "Debt/Equity Ratio",
        ),
        "health": _first("Health Score"),
        "eq_flag": _first("Earnings Quality Flag"),
        "dcf": _first("DCF Intrinsic Value"),
        "peer_pe": _first("Peer P/E Percentile"),
    }


def _scraper_extras(f, export_date, include_pe=True):
    """Return scraper-specific columns appended after existing tab schema.

    include_pe: False for tabs that already have P/E in their existing columns.
    """
    extras = [
        export_date,
        serialize_value(f["eps"]),
    ]
    if include_pe:
        extras.append(serialize_value(f["pe"]))
    extras += [
        serialize_value(f["rsi"]),
        serialize_value(f["ma10"]),
        serialize_value(f["ma20"]),
        serialize_value(f["ma50"]),
        serialize_value(f["sentiment"]),
        serialize_value(f["revenue"]),
        serialize_value(f["profit_margin"]),
        serialize_value(f["op_margin"]),
        serialize_value(f["debt_eq"]),
        serialize_value(f["health"]),
        serialize_value(f["eq_flag"]),
        serialize_value(f["dcf"]),
        serialize_value(f["peer_pe"]),
    ]
    return extras


def _build_row_us(ticker, f, export_date):
    """US Stock: map to existing A-AG schema, append scraper extras at AH+."""
    price = serialize_value(f["price"])
    row = [""] * _US_EXISTING_COLS
    row[2] = ticker  # C: Google Quote
    row[3] = price  # D: Google Price
    row[5] = serialize_value(f["eps"])  # F: EPS
    row[6] = serialize_value(f["pe"])  # G: P/E YahooFinance
    row[10] = ticker  # K: Yahoo Quote
    row[11] = price  # L: Yahoo Price
    row[28] = serialize_value(f["dcf"])  # AC: Price Target
    # AH(33): Export Date, AI(34): Fwd P/E, AJ(35): P/B, AK(36): RSI,
    # AL(37): MA10, AM(38): MA20, AN(39): MA50, AO(40): Sentiment,
    # AP(41): Revenue, AQ(42): Profit Margin, AR(43): Op Margin,
    # AS(44): Debt/Equity, AT(45): Health Score, AU(46): EQ Flag, AV(47): Peer P/E
    row += [
        export_date,
        serialize_value(f["fwd_pe"]),
        serialize_value(f["pb"]),
        serialize_value(f["rsi"]),
        serialize_value(f["ma10"]),
        serialize_value(f["ma20"]),
        serialize_value(f["ma50"]),
        serialize_value(f["sentiment"]),
        serialize_value(f["revenue"]),
        serialize_value(f["profit_margin"]),
        serialize_value(f["op_margin"]),
        serialize_value(f["debt_eq"]),
        serialize_value(f["health"]),
        serialize_value(f["eq_flag"]),
        serialize_value(f["peer_pe"]),
    ]
    return row  # 48 cols total


def _build_row_sg(ticker, f, export_date):
    """SG Stock: map to existing A-AC schema, append scraper extras at AD+."""
    price = serialize_value(f["price"])
    row = [""] * _SG_EXISTING_COLS
    row[2] = ticker  # C: Google Quote
    row[3] = price  # D: Google Price
    row[4] = serialize_value(f["pe"])  # E: P/E
    row[5] = ticker  # F: Yahoo Quote
    row[6] = price  # G: Yahoo Price
    row[23] = serialize_value(f["pb"])  # X: P/B
    row[24] = serialize_value(f["fwd_pe"])  # Y: Fwd P/E
    # AD(29): Export Date, AE(30): EPS, AF(31): RSI, AG(32): MA10,
    # AH(33): MA20, AI(34): MA50, AJ(35): Sentiment, AK(36): Revenue,
    # AL(37): Profit Margin, AM(38): Op Margin, AN(39): Debt/Equity,
    # AO(40): Health Score, AP(41): EQ Flag, AQ(42): DCF, AR(43): Peer P/E
    row += [
        export_date,
        serialize_value(f["eps"]),
        serialize_value(f["rsi"]),
        serialize_value(f["ma10"]),
        serialize_value(f["ma20"]),
        serialize_value(f["ma50"]),
        serialize_value(f["sentiment"]),
        serialize_value(f["revenue"]),
        serialize_value(f["profit_margin"]),
        serialize_value(f["op_margin"]),
        serialize_value(f["debt_eq"]),
        serialize_value(f["health"]),
        serialize_value(f["eq_flag"]),
        serialize_value(f["dcf"]),
        serialize_value(f["peer_pe"]),
    ]
    return row  # 44 cols total


def _build_row_hk(ticker, f, export_date):
    """HK Stock: map to existing A-AA schema, append scraper extras at AB+."""
    price = serialize_value(f["price"])
    row = [""] * _HK_EXISTING_COLS
    row[2] = ticker  # C: Google Quote
    row[3] = price  # D: Google Price
    row[4] = ticker  # E: Yahoo Quote
    row[5] = price  # F: Yahoo Price
    row[22] = serialize_value(f["pb"])  # W: P/B
    row[23] = serialize_value(f["fwd_pe"])  # X: Fwd P/E
    # AB(27): Export Date, AC(28): EPS, AD(29): P/E, AE(30): RSI,
    # AF(31): MA10, AG(32): MA20, AH(33): MA50, AI(34): Sentiment,
    # AJ(35): Revenue, AK(36): Profit Margin, AL(37): Op Margin,
    # AM(38): Debt/Equity, AN(39): Health Score, AO(40): EQ Flag,
    # AP(41): DCF, AQ(42): Peer P/E
    row += [
        export_date,
        serialize_value(f["eps"]),
        serialize_value(f["pe"]),
        serialize_value(f["rsi"]),
        serialize_value(f["ma10"]),
        serialize_value(f["ma20"]),
        serialize_value(f["ma50"]),
        serialize_value(f["sentiment"]),
        serialize_value(f["revenue"]),
        serialize_value(f["profit_margin"]),
        serialize_value(f["op_margin"]),
        serialize_value(f["debt_eq"]),
        serialize_value(f["health"]),
        serialize_value(f["eq_flag"]),
        serialize_value(f["dcf"]),
        serialize_value(f["peer_pe"]),
    ]
    return row  # 43 cols total


def _build_row_others(ticker, f, export_date):
    """Others Stock: flat 20-column schema (tab is auto-created, we own it)."""
    return [
        export_date,
        ticker,
        serialize_value(f["price"]),
        serialize_value(f["pe"]),
        serialize_value(f["fwd_pe"]),
        serialize_value(f["pb"]),
        serialize_value(f["eps"]),
        serialize_value(f["rsi"]),
        serialize_value(f["ma10"]),
        serialize_value(f["ma20"]),
        serialize_value(f["ma50"]),
        serialize_value(f["sentiment"]),
        serialize_value(f["revenue"]),
        serialize_value(f["profit_margin"]),
        serialize_value(f["op_margin"]),
        serialize_value(f["debt_eq"]),
        serialize_value(f["health"]),
        serialize_value(f["eq_flag"]),
        serialize_value(f["dcf"]),
        serialize_value(f["peer_pe"]),
    ]  # 20 cols total


_ROW_BUILDERS = {
    _TAB_US: _build_row_us,
    _TAB_SG: _build_row_sg,
    _TAB_HK: _build_row_hk,
    _TAB_OTHERS: _build_row_others,
}

# Expected row lengths per tab (used by tests)
ROW_LENGTHS = {
    _TAB_US: 48,
    _TAB_SG: 44,
    _TAB_HK: 43,
    _TAB_OTHERS: 20,
}

# Column index (0-based) that holds the ticker symbol in each tab
_TICKER_COL = {
    _TAB_US: 2,  # C: Google Quote
    _TAB_SG: 2,  # C: Google Quote
    _TAB_HK: 2,  # C: Google Quote
    _TAB_OTHERS: 1,  # B: Ticker
}


def _upsert_rows(ws, rows, ticker_col_idx):
    """Upsert rows: update existing ticker row in-place, else append."""
    existing = ws.get_all_values()
    ticker_row_map = {}
    for i, row in enumerate(existing, start=1):
        if len(row) > ticker_col_idx:
            cell_val = row[ticker_col_idx].strip().upper()
            if cell_val:
                ticker_row_map[cell_val] = i

    batch_updates = []
    new_rows = []
    for row in rows:
        ticker_in_row = (
            str(row[ticker_col_idx]).strip().upper()
            if len(row) > ticker_col_idx
            else ""
        )
        if ticker_in_row and ticker_in_row in ticker_row_map:
            batch_updates.append(
                {"range": f"A{ticker_row_map[ticker_in_row]}", "values": [row]}
            )
        else:
            new_rows.append(row)

    if batch_updates:
        ws.batch_update(batch_updates, value_input_option=ValueInputOption.user_entered)
    if new_rows:
        next_row = len(existing) + 1
        ws.update(
            f"A{next_row}", new_rows, value_input_option=ValueInputOption.user_entered
        )


def export_tickers_to_sheets(tickers, data):
    """Export stock data for *tickers* to the configured Google Spreadsheet.

    Routes each ticker to the correct tab:
      - No dot suffix  → "US Stock"
      - Suffix .SI     → "SG Stock"
      - Suffix .HK     → "HK Stock"
      - Everything else → "Others Stock" (auto-created if absent)

    If a ticker already exists in the tab (matched by ticker column), its row
    is updated in-place. Otherwise a new row is appended.

    Args:
        tickers: list of ticker strings (e.g. ["AAPL", "D05.SI"])
        data: dict mapping ticker → dict of field_name → value

    Returns:
        int: total number of rows upserted across all tabs

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
    export_date = date.today().strftime("%Y-%m-%d")

    buckets: dict[str, list] = {}
    for ticker in tickers:
        tab = _classify_ticker(ticker)
        fields = _extract_fields(data.get(ticker, {}))
        row = _ROW_BUILDERS[tab](ticker, fields, export_date)
        buckets.setdefault(tab, []).append(row)

    total = 0
    for tab_name, rows in buckets.items():
        ws = _get_or_create_worksheet(sh, tab_name)
        _upsert_rows(ws, rows, _TICKER_COL[tab_name])
        logger.info(
            "Upserted %d rows to tab '%s' in sheet %s",
            len(rows),
            tab_name,
            spreadsheet_id,
        )
        total += len(rows)

    return total
