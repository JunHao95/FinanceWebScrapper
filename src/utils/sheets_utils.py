"""
Google Sheets export utilities for FinanceWebScrapper.

Provides serialize_value, get_sheets_client, and export_tickers_to_sheets.
Authentication uses a service account credentials JSON file whose path is
read from GOOGLE_SHEETS_CREDENTIALS_PATH at call time (not at import time).

Tab routing and column mapping
-------------------------------
Trading Indicator (TI) columns are appended inline to each stock tab row
after the intelligence columns. 13 TI cols per row (Lookback through Dissenters).

US Stock  (existing cols A-AG, indices 0-32) + scraper extras starting at AH (33):
  C(2)=Google Quote, D(3)=Google Price, F(5)=EPS, G(6)=P/E Yahoo,
  K(10)=Yahoo Quote, L(11)=Yahoo Price, AC(28)=Price Target (DCF)
  AH(33)=Export Date, AI(34)=Fwd P/E, AJ(35)=P/B, AK(36)=RSI,
  AL(37)=MA10, AM(38)=MA20, AN(39)=MA50, AO(40)=Sentiment,
  AP(41)=Revenue, AQ(42)=Profit Margin, AR(43)=Op Margin,
  AS(44)=Debt/Equity, AT(45)=Health Score, AU(46)=EQ Flag, AV(47)=Peer P/E,
  AW(48)=Ticker Summary, AX(49)=Recommended Action,
  AY(50)=Analysis Methods, AZ(51)=Data Source Credibility,
  BA(52)=Lookback, BB(53)=Vol Profile, BC(54)=AVWAP Signal,
  BD(55)=AVWAP Conv, BE(56)=Order Flow, BF(57)=Order Flow Div,
  BG(58)=Sweep Signal, BH(59)=Sweep Price, BI(60)=Footprint,
  BJ(61)=Footprint Delta, BK(62)=Composite Dir, BL(63)=Composite Score,
  BM(64)=Composite Dissenters

SG Stock  (existing cols A-Z, indices 0-25) + scraper extras starting at AA (26):
  C(2)=Yahoo Quote, D(3)=Yahoo Price, U(20)=P/B, V(21)=Fwd P/E
  AA(26)=Export Date, AB(27)=EPS, AC(28)=RSI, AD(29)=MA10, AE(30)=MA20,
  AF(31)=MA50, AG(32)=Sentiment, AH(33)=Revenue, AI(34)=Profit Margin,
  AJ(35)=Op Margin, AK(36)=Debt/Equity, AL(37)=Health Score,
  AM(38)=EQ Flag, AN(39)=DCF, AO(40)=Peer P/E,
  AP(41)=Ticker Summary, AQ(42)=Recommended Action,
  AR(43)=Analysis Methods, AS(44)=Data Source Credibility,
  AT(45)=Lookback, AU(46)=Vol Profile, AV(47)=AVWAP Signal,
  AW(48)=AVWAP Conv, AX(49)=Order Flow, AY(50)=Order Flow Div,
  AZ(51)=Sweep Signal, BA(52)=Sweep Price, BB(53)=Footprint,
  BC(54)=Footprint Delta, BD(55)=Composite Dir, BE(56)=Composite Score,
  BF(57)=Composite Dissenters

HK Stock  (existing cols A-AA, indices 0-26) + scraper extras starting at AB (27):
  C(2)=Google Quote, D(3)=Google Price, E(4)=Yahoo Quote, F(5)=Yahoo Price,
  W(22)=P/B, X(23)=Fwd P/E
  AB(27)=Export Date, AC(28)=EPS, AD(29)=P/E, AE(30)=RSI, AF(31)=MA10,
  AG(32)=MA20, AH(33)=MA50, AI(34)=Sentiment, AJ(35)=Revenue,
  AK(36)=Profit Margin, AL(37)=Op Margin, AM(38)=Debt/Equity,
  AN(39)=Health Score, AO(40)=EQ Flag, AP(41)=DCF, AQ(42)=Peer P/E,
  AR(43)=Ticker Summary, AS(44)=Recommended Action,
  AT(45)=Analysis Methods, AU(46)=Data Source Credibility,
  AV(47)=Lookback, AW(48)=Vol Profile, AX(49)=AVWAP Signal,
  AY(50)=AVWAP Conv, AZ(51)=Order Flow, BA(52)=Order Flow Div,
  BB(53)=Sweep Signal, BC(54)=Sweep Price, BD(55)=Footprint,
  BE(56)=Footprint Delta, BF(57)=Composite Dir, BG(58)=Composite Score,
  BH(59)=Composite Dissenters

Others Stock  (auto-created, flat 37-column schema including TI cols)
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
    "Ticker Summary",
    "Recommended Action",
    "Analysis Methods",
    "Data Source Credibility",
    "Lookback (days)",
    "Volume Profile Signal",
    "AVWAP Signal",
    "AVWAP Convergence",
    "Order Flow Signal",
    "Order Flow Divergence",
    "Sweep Signal",
    "Sweep Price",
    "Footprint Signal",
    "Footprint Cum Delta",
    "Composite Direction",
    "Composite Score",
    "Composite Dissenters",
]

_TAB_US = "US Stock"
_TAB_SG = "SG Stock"
_TAB_HK = "HK Stock"
_TAB_OTHERS = "Others Stock"

# Column counts for existing tabs (determines where extra scraper cols start)
_US_EXISTING_COLS = 33  # A-AG
_SG_EXISTING_COLS = 26  # A-Z
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
    last_data_row = max(
        (i for i, r in enumerate(existing, start=1) if any(r)), default=0
    )
    next_row = last_data_row + 1
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


def _count_ma_signals(f):
    """Return (bullish_count, available_count) for the three MA signals."""
    keys = ("ma10", "ma20", "ma50")
    available = sum(1 for k in keys if f.get(k) is not None)
    bullish = sum(
        1
        for k in keys
        if f.get(k) and isinstance(f.get(k), str) and "bullish" in f.get(k, "").lower()
    )
    return bullish, available


def _rsi_label(rsi_val):
    try:
        v = float(rsi_val)
        if v < 30:
            return "oversold"
        if v > 70:
            return "overbought"
        return "neutral"
    except (TypeError, ValueError):
        return "neutral"


def _generate_ticker_summary(f):
    """~100-char rule-based sentence: P/E, RSI, MA consensus, Health, DCF gap."""
    parts = []
    if f.get("pe") is not None:
        try:
            parts.append(f"P/E {float(f['pe']):.0f}")
        except (TypeError, ValueError):
            pass
    if f.get("rsi") is not None:
        try:
            parts.append(f"RSI {float(f['rsi']):.0f} {_rsi_label(f['rsi'])}")
        except (TypeError, ValueError):
            pass
    bullish, available = _count_ma_signals(f)
    if available > 0:
        parts.append(f"{bullish}/{available} MA bullish")
    if f.get("health") is not None:
        parts.append(f"Health {f['health']}")
    if f.get("price") is not None and f.get("dcf") is not None:
        try:
            price = float(f["price"])
            dcf = float(f["dcf"])
            if price > 0:
                gap_pct = (dcf - price) / price * 100
                direction = "upside" if gap_pct >= 0 else "downside"
                parts.append(f"{abs(gap_pct):.0f}% DCF {direction}")
        except (TypeError, ValueError):
            pass
    return (", ".join(parts) + ".") if parts else ""


def _generate_recommended_action(f):
    """Buy/Hold/Sell + rationale from available signals; blank if no signals."""
    bullish = []
    bearish = []
    if f.get("rsi") is not None:
        try:
            rsi = float(f["rsi"])
            if rsi < 30:
                bullish.append("RSI oversold")
            elif rsi > 70:
                bearish.append("RSI overbought")
        except (TypeError, ValueError):
            pass
    b_count, avail = _count_ma_signals(f)
    bear_count = avail - b_count
    if avail > 0:
        if b_count >= 2 and b_count > bear_count:
            bullish.append(f"{b_count}/{avail} MA bullish")
        elif bear_count >= 2 and bear_count > b_count:
            bearish.append(f"{bear_count}/{avail} MA bearish")
    if f.get("sentiment") is not None:
        try:
            s = float(f["sentiment"])
            if s > 0.1:
                bullish.append("sentiment positive")
            elif s < -0.1:
                bearish.append("sentiment negative")
        except (TypeError, ValueError):
            pass
    if f.get("price") is not None and f.get("dcf") is not None:
        try:
            price = float(f["price"])
            dcf = float(f["dcf"])
            if price > 0:
                gap_pct = (dcf - price) / price * 100
                if gap_pct > 10:
                    bullish.append(f"{gap_pct:.0f}% DCF upside")
                elif gap_pct < -10:
                    bearish.append(f"{abs(gap_pct):.0f}% DCF downside")
        except (TypeError, ValueError):
            pass
    if not bullish and not bearish:
        return ""
    if len(bullish) > len(bearish):
        return "Buy — " + ", ".join(bullish)
    if len(bearish) > len(bullish):
        return "Sell — " + ", ".join(bearish)
    return "Hold — " + ", ".join(bullish + bearish)


def _generate_analysis_methods(f):
    """Comma-separated list of analysis methods inferred from non-null fields."""
    methods = []
    if f.get("rsi") is not None or f.get("ma10") is not None:
        methods.append("RSI/MA")
    if f.get("sentiment") is not None:
        methods.append("Sentiment")
    if f.get("health") is not None:
        methods.append("Health Score")
    if f.get("eq_flag") is not None:
        methods.append("Earnings Quality")
    if f.get("dcf") is not None:
        methods.append("DCF")
    if f.get("peer_pe") is not None:
        methods.append("Peer Comparison")
    return ", ".join(methods)


def _generate_data_source_credibility(f, ticker_data):
    """Tier + source list based on which source-suffixed keys are non-null."""
    td = ticker_data or {}
    sources = []
    tier_order = {"High": 3, "Medium": 2, "Low": 1}

    if any("Yahoo" in k and td.get(k) is not None for k in td):
        sources.append(("Yahoo", "High"))
    if any("Finviz" in k and td.get(k) is not None for k in td):
        sources.append(("Finviz", "High"))
    if any("Finnhub" in k and td.get(k) is not None for k in td):
        sources.append(("Finnhub", "High"))
    if f.get("sentiment") is not None:
        sources.append(("News", "Medium"))
    if any("Reddit" in k and td.get(k) is not None for k in td):
        sources.append(("Reddit", "Low"))

    if not sources:
        return ""
    top_tier = max(sources, key=lambda s: tier_order[s[1]])[1]
    return f"{top_tier} ({', '.join(s[0] for s in sources)})"


def _intelligence_cols(f, ticker_data):
    """Return the 4 intelligence columns for any tab row."""
    return [
        serialize_value(_generate_ticker_summary(f)),
        serialize_value(_generate_recommended_action(f)),
        serialize_value(_generate_analysis_methods(f)),
        serialize_value(_generate_data_source_credibility(f, ticker_data)),
    ]


TI_INLINE_HEADERS = [
    "Lookback (days)",
    "Volume Profile Signal",
    "AVWAP Signal",
    "AVWAP Convergence",
    "Order Flow Signal",
    "Order Flow Divergence",
    "Sweep Signal",
    "Sweep Price",
    "Footprint Signal",
    "Footprint Cum Delta",
    "Composite Direction",
    "Composite Score",
    "Composite Dissenters",
]


def _ti_cols(ti_data):
    """Return 13 TI column values from ti_data dict; all empty if None or {}."""
    td = ti_data or {}
    dissenters = td.get("composite_dissenters", "")
    if isinstance(dissenters, list):
        dissenters = ", ".join(str(d) for d in dissenters)
    return [
        serialize_value(td.get("lookback")),
        serialize_value(td.get("volume_profile_signal")),
        serialize_value(td.get("avwap_signal")),
        serialize_value(td.get("avwap_convergence")),
        serialize_value(td.get("order_flow_signal")),
        serialize_value(td.get("order_flow_divergence")),
        serialize_value(td.get("sweep_signal")),
        serialize_value(td.get("sweep_price")),
        serialize_value(td.get("footprint_signal")),
        serialize_value(td.get("footprint_cum_delta")),
        serialize_value(td.get("composite_direction")),
        serialize_value(td.get("composite_score")),
        serialize_value(dissenters),
    ]


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


def _build_row_us(ticker, f, export_date, ticker_data=None, ti_data=None):
    """US Stock: map to existing A-AG schema, append scraper extras at AH+, TI cols at BA+."""
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
    # AS(44): Debt/Equity, AT(45): Health Score, AU(46): EQ Flag, AV(47): Peer P/E,
    # AW(48): Ticker Summary, AX(49): Recommended Action,
    # AY(50): Analysis Methods, AZ(51): Data Source Credibility,
    # BA(52)-BM(64): TI cols
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
    row += _intelligence_cols(f, ticker_data)
    row += _ti_cols(ti_data)
    return row  # 65 cols total


def _build_row_sg(ticker, f, export_date, ticker_data=None, ti_data=None):
    """SG Stock: map to existing A-Z schema, append scraper extras at AA+, TI cols at AT+."""
    price = serialize_value(f["price"])
    row = [""] * _SG_EXISTING_COLS
    row[2] = ticker  # C: Yahoo Quote
    row[3] = price  # D: Yahoo Price
    row[20] = serialize_value(f["pb"])  # U: P/B
    row[21] = serialize_value(f["fwd_pe"])  # V: Fwd P/E
    # AA(26): Export Date, AB(27): EPS, AC(28): RSI, AD(29): MA10,
    # AE(30): MA20, AF(31): MA50, AG(32): Sentiment, AH(33): Revenue,
    # AI(34): Profit Margin, AJ(35): Op Margin, AK(36): Debt/Equity,
    # AL(37): Health Score, AM(38): EQ Flag, AN(39): DCF, AO(40): Peer P/E,
    # AP(41): Ticker Summary, AQ(42): Recommended Action,
    # AR(43): Analysis Methods, AS(44): Data Source Credibility,
    # AT(45)-BF(57): TI cols
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
    row += _intelligence_cols(f, ticker_data)
    row += _ti_cols(ti_data)
    return row  # 58 cols total


def _build_row_hk(ticker, f, export_date, ticker_data=None, ti_data=None):
    """HK Stock: map to existing A-AA schema, append scraper extras at AB+, TI cols at AV+."""
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
    # AP(41): DCF, AQ(42): Peer P/E,
    # AR(43): Ticker Summary, AS(44): Recommended Action,
    # AT(45): Analysis Methods, AU(46): Data Source Credibility,
    # AV(47)-BH(59): TI cols
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
    row += _intelligence_cols(f, ticker_data)
    row += _ti_cols(ti_data)
    return row  # 60 cols total


def _build_row_others(ticker, f, export_date, ticker_data=None, ti_data=None):
    """Others Stock: flat 37-column schema including TI cols (tab is auto-created)."""
    row = [
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
    ]
    row += _intelligence_cols(f, ticker_data)
    row += _ti_cols(ti_data)
    return row  # 37 cols total


_TAB_TI = "Trading Indicators"

TI_COLUMN_HEADERS = [
    "Export Date",  # A 0
    "Ticker",  # B 1
    "Lookback (days)",  # C 2
    "Volume Profile Signal",  # D 3
    "AVWAP Signal",  # E 4
    "AVWAP Convergence",  # F 5
    "Order Flow Signal",  # G 6
    "Order Flow Divergence",  # H 7
    "Sweep Signal",  # I 8
    "Sweep Price",  # J 9
    "Footprint Signal",  # K 10
    "Footprint Cum Delta",  # L 11
    "Composite Direction",  # M 12
    "Composite Score",  # N 13
    "Composite Dissenters",  # O 14
]

_ROW_BUILDERS = {
    _TAB_US: _build_row_us,
    _TAB_SG: _build_row_sg,
    _TAB_HK: _build_row_hk,
    _TAB_OTHERS: _build_row_others,
}

# Expected row lengths per tab (used by tests)
ROW_LENGTHS = {
    _TAB_US: 65,
    _TAB_SG: 58,
    _TAB_HK: 60,
    _TAB_OTHERS: 37,
    _TAB_TI: 15,
}

# Column index (0-based) that holds the ticker symbol in each tab
_TICKER_COL = {
    _TAB_US: 2,  # C: Google Quote
    _TAB_SG: 2,  # C: Google Quote
    _TAB_HK: 2,  # C: Google Quote
    _TAB_OTHERS: 1,  # B: Ticker
    _TAB_TI: 1,  # B: Ticker
}

# (col_index, header_label) pairs for scraper-added columns in pre-existing tabs.
# Others tab is excluded — it owns its full schema via COLUMN_HEADERS.
_SCRAPER_HEADERS = {
    _TAB_US: [
        (33, "Export Date"),
        (34, "Fwd P/E"),
        (35, "P/B"),
        (36, "RSI"),
        (37, "MA10 Signal"),
        (38, "MA20 Signal"),
        (39, "MA50 Signal"),
        (40, "Sentiment Score"),
        (41, "Revenue"),
        (42, "Profit Margin"),
        (43, "Operating Margin"),
        (44, "Debt/Equity"),
        (45, "Health Score"),
        (46, "Earnings Quality Flag"),
        (47, "Peer P/E Percentile"),
        (48, "Ticker Summary"),
        (49, "Recommended Action"),
        (50, "Analysis Methods"),
        (51, "Data Source Credibility"),
        (52, "Lookback (days)"),
        (53, "Volume Profile Signal"),
        (54, "AVWAP Signal"),
        (55, "AVWAP Convergence"),
        (56, "Order Flow Signal"),
        (57, "Order Flow Divergence"),
        (58, "Sweep Signal"),
        (59, "Sweep Price"),
        (60, "Footprint Signal"),
        (61, "Footprint Cum Delta"),
        (62, "Composite Direction"),
        (63, "Composite Score"),
        (64, "Composite Dissenters"),
    ],
    _TAB_SG: [
        (26, "Export Date"),
        (27, "EPS"),
        (28, "RSI"),
        (29, "MA10 Signal"),
        (30, "MA20 Signal"),
        (31, "MA50 Signal"),
        (32, "Sentiment Score"),
        (33, "Revenue"),
        (34, "Profit Margin"),
        (35, "Operating Margin"),
        (36, "Debt/Equity"),
        (37, "Health Score"),
        (38, "Earnings Quality Flag"),
        (39, "DCF Intrinsic Value"),
        (40, "Peer P/E Percentile"),
        (41, "Ticker Summary"),
        (42, "Recommended Action"),
        (43, "Analysis Methods"),
        (44, "Data Source Credibility"),
        (45, "Lookback (days)"),
        (46, "Volume Profile Signal"),
        (47, "AVWAP Signal"),
        (48, "AVWAP Convergence"),
        (49, "Order Flow Signal"),
        (50, "Order Flow Divergence"),
        (51, "Sweep Signal"),
        (52, "Sweep Price"),
        (53, "Footprint Signal"),
        (54, "Footprint Cum Delta"),
        (55, "Composite Direction"),
        (56, "Composite Score"),
        (57, "Composite Dissenters"),
    ],
    _TAB_HK: [
        (27, "Export Date"),
        (28, "EPS"),
        (29, "P/E"),
        (30, "RSI"),
        (31, "MA10 Signal"),
        (32, "MA20 Signal"),
        (33, "MA50 Signal"),
        (34, "Sentiment Score"),
        (35, "Revenue"),
        (36, "Profit Margin"),
        (37, "Operating Margin"),
        (38, "Debt/Equity"),
        (39, "Health Score"),
        (40, "Earnings Quality Flag"),
        (41, "DCF Intrinsic Value"),
        (42, "Peer P/E Percentile"),
        (43, "Ticker Summary"),
        (44, "Recommended Action"),
        (45, "Analysis Methods"),
        (46, "Data Source Credibility"),
        (47, "Lookback (days)"),
        (48, "Volume Profile Signal"),
        (49, "AVWAP Signal"),
        (50, "AVWAP Convergence"),
        (51, "Order Flow Signal"),
        (52, "Order Flow Divergence"),
        (53, "Sweep Signal"),
        (54, "Sweep Price"),
        (55, "Footprint Signal"),
        (56, "Footprint Cum Delta"),
        (57, "Composite Direction"),
        (58, "Composite Score"),
        (59, "Composite Dissenters"),
    ],
}


def _col_index_to_letter(idx):
    """Convert 0-based column index to A1 column letter (e.g. 0→A, 26→AA)."""
    result = ""
    n = idx + 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result


def _ensure_min_cols(ws, min_cols):
    """Expand the worksheet grid to at least min_cols columns if it is too narrow."""
    if ws.col_count < min_cols:
        ws.resize(cols=min_cols)


def _ensure_scraper_headers(ws, tab_name):
    """Write column headers for scraper-added columns in row 1 if the cells are empty."""
    header_specs = _SCRAPER_HEADERS.get(tab_name)
    if not header_specs:
        return
    row1 = ws.row_values(1)
    updates = []
    for col_idx, label in header_specs:
        existing = row1[col_idx] if col_idx < len(row1) else ""
        if not existing:
            updates.append(
                {"range": f"{_col_index_to_letter(col_idx)}1", "values": [[label]]}
            )
    if updates:
        ws.batch_update(updates, value_input_option=ValueInputOption.user_entered)


def _upsert_rows(ws, rows, ticker_col_idx):
    """Upsert rows: update existing ticker row in-place (skipping formula cells), else append.

    Uses FORMATTED_VALUE for ticker matching so that =HYPERLINK() cells are
    matched by their display text rather than the raw formula string.
    Uses FORMULA render only for per-cell formula-skip detection.
    """
    # FORMATTED_VALUE: ticker cells with =HYPERLINK() return display text (e.g. "D05.SI")
    existing_fmt = ws.get_all_values()
    # FORMULA: needed to detect formula cells that must not be overwritten
    existing_fml = ws.get_all_values(value_render_option="FORMULA")

    ticker_row_map = {}
    for i, row in enumerate(existing_fmt, start=1):
        if len(row) > ticker_col_idx:
            cell_val = str(row[ticker_col_idx]).strip().upper()
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
            sheet_row_num = ticker_row_map[ticker_in_row]
            existing_row = existing_fml[sheet_row_num - 1]
            for col_idx, new_val in enumerate(row):
                if new_val == "":
                    continue  # never overwrite existing user data with empty string
                existing_val = (
                    existing_row[col_idx] if col_idx < len(existing_row) else ""
                )
                if isinstance(existing_val, str) and existing_val.startswith("="):
                    continue
                batch_updates.append(
                    {
                        "range": f"{_col_index_to_letter(col_idx)}{sheet_row_num}",
                        "values": [[new_val]],
                    }
                )
        else:
            new_rows.append(row)

    if batch_updates:
        ws.batch_update(batch_updates, value_input_option=ValueInputOption.user_entered)
    if new_rows:
        # Find last row with any content — avoids counting empty rows inside the
        # sheet's "used range" that would offset the append position.
        last_data_row = max(
            (i for i, r in enumerate(existing_fmt, start=1) if any(r)), default=0
        )
        next_row = last_data_row + 1
        ws.update(
            f"A{next_row}", new_rows, value_input_option=ValueInputOption.user_entered
        )


def _build_row_ti(ticker, ti_data, export_date):
    """Build a 15-element Trading Indicators row from ti_data dict."""
    dissenters = ti_data.get("composite_dissenters", "")
    if isinstance(dissenters, list):
        dissenters = ", ".join(str(d) for d in dissenters)
    return [
        export_date,
        ticker,
        serialize_value(ti_data.get("lookback")),
        serialize_value(ti_data.get("volume_profile_signal")),
        serialize_value(ti_data.get("avwap_signal")),
        serialize_value(ti_data.get("avwap_convergence")),
        serialize_value(ti_data.get("order_flow_signal")),
        serialize_value(ti_data.get("order_flow_divergence")),
        serialize_value(ti_data.get("sweep_signal")),
        serialize_value(ti_data.get("sweep_price")),
        serialize_value(ti_data.get("footprint_signal")),
        serialize_value(ti_data.get("footprint_cum_delta")),
        serialize_value(ti_data.get("composite_direction")),
        serialize_value(ti_data.get("composite_score")),
        serialize_value(dissenters),
    ]


def export_tickers_to_sheets(tickers, data, trading_indicators_data=None):
    """Export stock data for *tickers* to the configured Google Spreadsheet.

    Routes each ticker to the correct tab:
      - No dot suffix  → "US Stock"
      - Suffix .SI     → "SG Stock"
      - Suffix .HK     → "HK Stock"
      - Everything else → "Others Stock" (auto-created if absent)

    Trading Indicators data is written inline as 13 extra columns appended to
    each stock tab row (after intelligence columns). No separate TI tab is created.

    Args:
        tickers: list of ticker strings (e.g. ["AAPL", "D05.SI"])
        data: dict mapping ticker → dict of field_name → value
        trading_indicators_data: optional dict mapping ticker → TI field dict

    Returns:
        dict: {"rows_added": N}

    Raises:
        ValueError: if GOOGLE_SHEETS_SPREADSHEET_ID is not set
        FileNotFoundError: if credentials are missing (from get_sheets_client)
        gspread.exceptions.SpreadsheetNotFound: if spreadsheet cannot be opened
    """
    if not tickers:
        return {"rows_added": 0}

    spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
    if not spreadsheet_id:
        raise ValueError(
            "GOOGLE_SHEETS_SPREADSHEET_ID is not set in .env. "
            "See README.md 'Google Sheets Setup' for instructions."
        )

    gc = get_sheets_client()
    sh = gc.open_by_key(spreadsheet_id)
    export_date = date.today().strftime("%Y-%m-%d")
    ti_data = trading_indicators_data or {}

    buckets: dict[str, list] = {}
    for ticker in tickers:
        tab = _classify_ticker(ticker)
        ticker_data = data.get(ticker, {})
        fields = _extract_fields(ticker_data)
        ticker_ti = ti_data.get(ticker)
        row = _ROW_BUILDERS[tab](ticker, fields, export_date, ticker_data, ticker_ti)
        buckets.setdefault(tab, []).append(row)

    total = 0
    for tab_name, rows in buckets.items():
        ws = _get_or_create_worksheet(sh, tab_name)
        _ensure_min_cols(ws, ROW_LENGTHS.get(tab_name, 20))
        _ensure_scraper_headers(ws, tab_name)
        _upsert_rows(ws, rows, _TICKER_COL[tab_name])
        logger.info(
            "Upserted %d rows to tab '%s' in sheet %s",
            len(rows),
            tab_name,
            spreadsheet_id,
        )
        total += len(rows)

    return {"rows_added": total}
