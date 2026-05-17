"""
Unit tests for src/utils/sheets_utils.py — Google Sheets export.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
import gspread.exceptions

pytest.importorskip(
    "src.utils.sheets_utils", reason="sheets_utils not implemented yet (Wave 0)"
)

from src.utils.sheets_utils import (  # noqa: E402
    serialize_value,
    get_sheets_client,
    export_tickers_to_sheets,
    _classify_ticker,
    _extract_fields,
    _append_below_existing,
    _upsert_rows,
    _build_row_us,
    _build_row_sg,
    _build_row_hk,
    _build_row_others,
    ROW_LENGTHS,
    _TAB_US,
    _TAB_SG,
    _TAB_HK,
    _TAB_OTHERS,
)


# ---------------------------------------------------------------------------
# serialize_value
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_serialize_none():
    assert serialize_value(None) == ""


@pytest.mark.unit
def test_serialize_number_int():
    assert serialize_value(42) == 42


@pytest.mark.unit
def test_serialize_number_float():
    assert serialize_value(3.14) == 3.14


@pytest.mark.unit
def test_serialize_bool_true():
    assert serialize_value(True) == "True"


@pytest.mark.unit
def test_serialize_bool_false():
    assert serialize_value(False) == "False"


@pytest.mark.unit
def test_serialize_string():
    assert serialize_value("hello") == "hello"


# ---------------------------------------------------------------------------
# _classify_ticker
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "TSLA", "NVDA"])
def test_classify_us(ticker):
    assert _classify_ticker(ticker) == _TAB_US


@pytest.mark.unit
@pytest.mark.parametrize("ticker", ["D05.SI", "C6L.SI", "U11.SI"])
def test_classify_sg(ticker):
    assert _classify_ticker(ticker) == _TAB_SG


@pytest.mark.unit
@pytest.mark.parametrize("ticker", ["0700.HK", "9988.HK"])
def test_classify_hk(ticker):
    assert _classify_ticker(ticker) == _TAB_HK


@pytest.mark.unit
@pytest.mark.parametrize("ticker", ["BRK.B", "BF.A", "UNKNOWN.XX"])
def test_classify_others(ticker):
    assert _classify_ticker(ticker) == _TAB_OTHERS


# ---------------------------------------------------------------------------
# _extract_fields
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_extract_fields_pe_fallback():
    """P/E key fallback: P/E Ratio (Yahoo) > P/E Ratio > P/E."""
    assert _extract_fields({"P/E Ratio (Yahoo)": 20})["pe"] == 20
    assert _extract_fields({"P/E Ratio": 21})["pe"] == 21
    assert _extract_fields({"P/E": 22})["pe"] == 22


@pytest.mark.unit
def test_extract_fields_missing_keys():
    """All fields default to None when ticker_data is empty."""
    f = _extract_fields({})
    assert all(v is None for v in f.values())


# ---------------------------------------------------------------------------
# Per-tab row builders — length and spot-check key columns
# ---------------------------------------------------------------------------


_SAMPLE_FIELDS = _extract_fields(
    {
        "Price": 100.0,
        "P/E Ratio (Yahoo)": 20.0,
        "Forward P/E": 18.0,
        "P/B Ratio": 3.0,
        "EPS": 5.0,
        "RSI": 55.0,
        "MA10 Signal": "Bullish",
        "MA20 Signal": "Neutral",
        "MA50 Signal": "Bullish",
        "Sentiment Score": 0.7,
        "Revenue": 1e9,
        "Profit Margin": 0.25,
        "Operating Margin": 0.20,
        "Debt/Equity": 0.5,
        "Health Score": 8,
        "Earnings Quality Flag": "Pass",
        "DCF Intrinsic Value": 120.0,
        "Peer P/E Percentile": 75,
    }
)


@pytest.mark.unit
def test_row_length_us():
    row = _build_row_us("AAPL", _SAMPLE_FIELDS, "2026-05-17")
    assert len(row) == ROW_LENGTHS[_TAB_US]  # 48


@pytest.mark.unit
def test_row_length_sg():
    row = _build_row_sg("D05.SI", _SAMPLE_FIELDS, "2026-05-17")
    assert len(row) == ROW_LENGTHS[_TAB_SG]  # 44


@pytest.mark.unit
def test_row_length_hk():
    row = _build_row_hk("0700.HK", _SAMPLE_FIELDS, "2026-05-17")
    assert len(row) == ROW_LENGTHS[_TAB_HK]  # 43


@pytest.mark.unit
def test_row_length_others():
    row = _build_row_others("BRK.B", _SAMPLE_FIELDS, "2026-05-17")
    assert len(row) == ROW_LENGTHS[_TAB_OTHERS]  # 20


@pytest.mark.unit
def test_us_row_ticker_at_c_and_k():
    row = _build_row_us("AAPL", _SAMPLE_FIELDS, "2026-05-17")
    assert row[2] == "AAPL"  # C: Google Quote
    assert row[10] == "AAPL"  # K: Yahoo Quote


@pytest.mark.unit
def test_us_row_price_at_d_and_l():
    row = _build_row_us("AAPL", _SAMPLE_FIELDS, "2026-05-17")
    assert row[3] == 100.0  # D: Google Price
    assert row[11] == 100.0  # L: Yahoo Price


@pytest.mark.unit
def test_us_row_pe_at_g():
    row = _build_row_us("AAPL", _SAMPLE_FIELDS, "2026-05-17")
    assert row[6] == 20.0  # G: P/E YahooFinance


@pytest.mark.unit
def test_us_row_dcf_at_ac():
    row = _build_row_us("AAPL", _SAMPLE_FIELDS, "2026-05-17")
    assert row[28] == 120.0  # AC: Price Target


@pytest.mark.unit
def test_us_row_export_date_at_ah():
    row = _build_row_us("AAPL", _SAMPLE_FIELDS, "2026-05-17")
    assert row[33] == "2026-05-17"  # AH: Export Date


@pytest.mark.unit
def test_sg_row_pe_at_e():
    row = _build_row_sg("D05.SI", _SAMPLE_FIELDS, "2026-05-17")
    assert row[4] == 20.0  # E: P/E


@pytest.mark.unit
def test_sg_row_pb_at_x():
    row = _build_row_sg("D05.SI", _SAMPLE_FIELDS, "2026-05-17")
    assert row[23] == 3.0  # X: P/B


@pytest.mark.unit
def test_sg_row_fwd_pe_at_y():
    row = _build_row_sg("D05.SI", _SAMPLE_FIELDS, "2026-05-17")
    assert row[24] == 18.0  # Y: Fwd P/E


@pytest.mark.unit
def test_hk_row_pb_at_w():
    row = _build_row_hk("0700.HK", _SAMPLE_FIELDS, "2026-05-17")
    assert row[22] == 3.0  # W: P/B


@pytest.mark.unit
def test_hk_row_fwd_pe_at_x():
    row = _build_row_hk("0700.HK", _SAMPLE_FIELDS, "2026-05-17")
    assert row[23] == 18.0  # X: Fwd P/E


@pytest.mark.unit
def test_none_fields_serialize_to_empty():
    empty = _extract_fields({})
    row = _build_row_us("AAPL", empty, "2026-05-17")
    # Price at D(3), P/E at G(6), RSI at AK(36) — all should be ""
    assert row[3] == ""
    assert row[6] == ""
    assert row[36] == ""


# ---------------------------------------------------------------------------
# _append_below_existing — row anchor
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_append_below_existing_anchors_to_next_row():
    ws = MagicMock()
    ws.get_all_values.return_value = [["h1", "h2"], ["v1", "v2"]]  # 2 existing rows
    _append_below_existing(ws, [["2026-05-17", "AAPL"]])
    assert ws.update.call_args[0][0] == "A3"


# ---------------------------------------------------------------------------
# _upsert_rows — upsert behavior
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_upsert_updates_existing_ticker():
    """Ticker already in sheet → batch_update in-place, no append."""
    ws = MagicMock()
    ws.get_all_values.return_value = [
        ["h1", "h2", "Ticker"],
        ["", "", "AAPL", "100.0"],
    ]
    _upsert_rows(ws, [["", "", "AAPL", "150.0"]], ticker_col_idx=2)
    ws.batch_update.assert_called_once()
    ws.update.assert_not_called()


@pytest.mark.unit
def test_upsert_updates_correct_row_number():
    """batch_update range must point at the row containing the ticker."""
    ws = MagicMock()
    ws.get_all_values.return_value = [
        ["h1", "h2", "Ticker"],
        ["", "", "AAPL", "100.0"],
        ["", "", "MSFT", "300.0"],
    ]
    _upsert_rows(ws, [["", "", "MSFT", "350.0"]], ticker_col_idx=2)
    call_data = ws.batch_update.call_args[0][0]
    assert call_data[0]["range"] == "A3"


@pytest.mark.unit
def test_upsert_appends_new_ticker():
    """Ticker not in sheet → append via update, no batch_update."""
    ws = MagicMock()
    ws.get_all_values.return_value = [["h1", "h2", "Ticker"]]
    _upsert_rows(ws, [["", "", "TSLA", "400.0"]], ticker_col_idx=2)
    ws.update.assert_called_once()
    assert ws.update.call_args[0][0] == "A2"
    ws.batch_update.assert_not_called()


@pytest.mark.unit
def test_upsert_mixed_existing_and_new():
    """Existing ticker updated in-place; new ticker appended."""
    ws = MagicMock()
    ws.get_all_values.return_value = [
        ["h1", "h2", "Ticker"],
        ["", "", "AAPL", "100.0"],
    ]
    _upsert_rows(
        ws,
        [["", "", "AAPL", "150.0"], ["", "", "TSLA", "400.0"]],
        ticker_col_idx=2,
    )
    ws.batch_update.assert_called_once()
    ws.update.assert_called_once()
    assert ws.update.call_args[0][0] == "A3"


# ---------------------------------------------------------------------------
# get_sheets_client
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_missing_creds_env():
    env_without_creds = {
        k: v for k, v in os.environ.items() if k != "GOOGLE_SHEETS_CREDENTIALS_PATH"
    }
    with patch.dict("os.environ", env_without_creds, clear=True):
        with pytest.raises(FileNotFoundError, match="GOOGLE_SHEETS_CREDENTIALS_PATH"):
            get_sheets_client()


@pytest.mark.unit
def test_missing_creds_file():
    with patch.dict(
        "os.environ", {"GOOGLE_SHEETS_CREDENTIALS_PATH": "/nonexistent/creds.json"}
    ):
        with patch("os.path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                get_sheets_client()


# ---------------------------------------------------------------------------
# export_tickers_to_sheets — mock gspread
# ---------------------------------------------------------------------------


def _make_mock_ws():
    ws = MagicMock()
    ws.get_all_values.return_value = [["header row"]]
    return ws


def _make_mock_gc(existing_tabs=None):
    if existing_tabs is None:
        existing_tabs = {_TAB_US, _TAB_SG, _TAB_HK, _TAB_OTHERS}

    worksheets = {name: _make_mock_ws() for name in existing_tabs}

    def fake_worksheet(name):
        if name in worksheets:
            return worksheets[name]
        raise gspread.exceptions.WorksheetNotFound(name)

    mock_sh = MagicMock()
    mock_sh.worksheet.side_effect = fake_worksheet
    mock_sh.add_worksheet.side_effect = (
        lambda title, rows, cols: worksheets.setdefault(title, _make_mock_ws())
        or worksheets[title]
    )

    mock_gc = MagicMock()
    mock_gc.open_by_key.return_value = mock_sh
    return mock_gc, worksheets, mock_sh


_ENV = {
    "GOOGLE_SHEETS_CREDENTIALS_PATH": "/fake/creds.json",
    "GOOGLE_SHEETS_SPREADSHEET_ID": "fake-id",
}


@pytest.mark.unit
def test_us_tickers_go_to_us_tab():
    mock_gc, worksheets, _ = _make_mock_gc()
    with patch("gspread.service_account", return_value=mock_gc), patch.dict(
        "os.environ", _ENV
    ), patch("os.path.exists", return_value=True):
        result = export_tickers_to_sheets(
            ["AAPL", "MSFT"],
            {"AAPL": {"Price": "175.00"}, "MSFT": {"RSI": None}},
        )
    assert result == 2
    assert worksheets[_TAB_US].update.call_count == 1
    for tab in [_TAB_SG, _TAB_HK]:
        assert worksheets[tab].update.call_count == 0


@pytest.mark.unit
def test_sg_tickers_go_to_sg_tab():
    mock_gc, worksheets, _ = _make_mock_gc()
    with patch("gspread.service_account", return_value=mock_gc), patch.dict(
        "os.environ", _ENV
    ), patch("os.path.exists", return_value=True):
        result = export_tickers_to_sheets(
            ["D05.SI", "C6L.SI"],
            {"D05.SI": {"Price": 37.5}, "C6L.SI": {"Price": 6.1}},
        )
    assert result == 2
    assert worksheets[_TAB_SG].update.call_count == 1
    assert worksheets[_TAB_US].update.call_count == 0


@pytest.mark.unit
def test_hk_tickers_go_to_hk_tab():
    mock_gc, worksheets, _ = _make_mock_gc()
    with patch("gspread.service_account", return_value=mock_gc), patch.dict(
        "os.environ", _ENV
    ), patch("os.path.exists", return_value=True):
        result = export_tickers_to_sheets(
            ["0700.HK"],
            {"0700.HK": {"Price": 320.0}},
        )
    assert result == 1
    assert worksheets[_TAB_HK].update.call_count == 1


@pytest.mark.unit
def test_multi_region_routes_to_separate_tabs():
    mock_gc, worksheets, _ = _make_mock_gc()
    with patch("gspread.service_account", return_value=mock_gc), patch.dict(
        "os.environ", _ENV
    ), patch("os.path.exists", return_value=True):
        result = export_tickers_to_sheets(
            ["TSLA", "D05.SI", "0700.HK"],
            {
                "TSLA": {"Price": 420.0},
                "D05.SI": {"Price": 37.5},
                "0700.HK": {"Price": 320.0},
            },
        )
    assert result == 3
    assert worksheets[_TAB_US].update.call_count == 1
    assert worksheets[_TAB_SG].update.call_count == 1
    assert worksheets[_TAB_HK].update.call_count == 1


@pytest.mark.unit
def test_others_tab_auto_created():
    mock_gc, worksheets, mock_sh = _make_mock_gc(
        existing_tabs={_TAB_US, _TAB_SG, _TAB_HK}
    )
    with patch("gspread.service_account", return_value=mock_gc), patch.dict(
        "os.environ", _ENV
    ), patch("os.path.exists", return_value=True):
        result = export_tickers_to_sheets(["BRK.B"], {"BRK.B": {"Price": 500.0}})
    assert result == 1
    mock_sh.add_worksheet.assert_called_once_with(title=_TAB_OTHERS, rows=1000, cols=20)


@pytest.mark.unit
def test_empty_tickers():
    mock_gc, worksheets, _ = _make_mock_gc()
    with patch("gspread.service_account", return_value=mock_gc), patch.dict(
        "os.environ", _ENV
    ), patch("os.path.exists", return_value=True):
        result = export_tickers_to_sheets([], {})
    assert result == 0
    for ws in worksheets.values():
        assert ws.update.call_count == 0


@pytest.mark.unit
def test_export_updates_existing_ticker_in_us_tab():
    """AAPL already in US tab → batch_update called, no append (update not called)."""
    mock_gc, worksheets, _ = _make_mock_gc()
    # Ticker at col C (index 2) in row 2
    worksheets[_TAB_US].get_all_values.return_value = [
        ["h1", "h2", "Ticker"],
        ["", "", "AAPL", "100.0"],
    ]
    with patch("gspread.service_account", return_value=mock_gc), patch.dict(
        "os.environ", _ENV
    ), patch("os.path.exists", return_value=True):
        result = export_tickers_to_sheets(["AAPL"], {"AAPL": {"Price": "175.00"}})
    assert result == 1
    worksheets[_TAB_US].batch_update.assert_called_once()
    worksheets[_TAB_US].update.assert_not_called()


@pytest.mark.unit
def test_export_upsert_mixed_new_and_existing():
    """AAPL exists (update) + MSFT new (append) → both batch_update and update called."""
    mock_gc, worksheets, _ = _make_mock_gc()
    worksheets[_TAB_US].get_all_values.return_value = [
        ["h1", "h2", "Ticker"],
        ["", "", "AAPL", "100.0"],
    ]
    with patch("gspread.service_account", return_value=mock_gc), patch.dict(
        "os.environ", _ENV
    ), patch("os.path.exists", return_value=True):
        result = export_tickers_to_sheets(
            ["AAPL", "MSFT"],
            {"AAPL": {"Price": "175.00"}, "MSFT": {"Price": "400.00"}},
        )
    assert result == 2
    worksheets[_TAB_US].batch_update.assert_called_once()
    worksheets[_TAB_US].update.assert_called_once()
