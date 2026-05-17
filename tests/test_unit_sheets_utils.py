"""
Unit tests for src/utils/sheets_utils.py (Phase 31 — Google Sheets export).

Tests cover: serialize_value, get_sheets_client, export_tickers_to_sheets.
At Wave 0 the source module does not exist yet — all tests are skipped via importorskip.
Remove the importorskip guard in Wave 1 once the source module is created.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

pytest.importorskip(
    "src.utils.sheets_utils", reason="sheets_utils not implemented yet (Wave 0)"
)

from src.utils.sheets_utils import (  # noqa: E402
    serialize_value,
    get_sheets_client,
    export_tickers_to_sheets,
)


# ---------------------------------------------------------------------------
# serialize_value — pure function, no mocking required
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
# get_sheets_client — env var and file-existence guards
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_missing_creds_env():
    """Missing env var raises FileNotFoundError."""
    env_without_creds = {
        k: v for k, v in os.environ.items() if k != "GOOGLE_SHEETS_CREDENTIALS_PATH"
    }
    with patch.dict("os.environ", env_without_creds, clear=True):
        with pytest.raises(FileNotFoundError, match="GOOGLE_SHEETS_CREDENTIALS_PATH"):
            get_sheets_client()


@pytest.mark.unit
def test_missing_creds_file():
    """Env var set but file absent raises FileNotFoundError."""
    with patch.dict(
        "os.environ", {"GOOGLE_SHEETS_CREDENTIALS_PATH": "/nonexistent/creds.json"}
    ):
        with patch("os.path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                get_sheets_client()


# ---------------------------------------------------------------------------
# export_tickers_to_sheets — mock gspread entirely
# ---------------------------------------------------------------------------


def _make_mock_gc():
    mock_worksheet = MagicMock()
    mock_sh = MagicMock()
    mock_sh.get_worksheet.return_value = mock_worksheet
    mock_gc = MagicMock()
    mock_gc.open_by_key.return_value = mock_sh
    return mock_gc, mock_worksheet


@pytest.mark.unit
def test_batch_append():
    """export_tickers_to_sheets calls append_rows once (batch) and returns row count."""
    mock_gc, mock_worksheet = _make_mock_gc()
    with patch("gspread.service_account", return_value=mock_gc), patch.dict(
        "os.environ",
        {
            "GOOGLE_SHEETS_CREDENTIALS_PATH": "/fake/creds.json",
            "GOOGLE_SHEETS_SPREADSHEET_ID": "fake-id",
        },
    ), patch("os.path.exists", return_value=True):
        result = export_tickers_to_sheets(
            ["AAPL", "MSFT"],
            {"AAPL": {"Price": "175.00"}, "MSFT": {"RSI": None}},
        )
    assert result == 2
    assert mock_worksheet.append_rows.call_count == 1


@pytest.mark.unit
def test_empty_tickers():
    """Empty tickers list returns 0 and never calls append_rows."""
    mock_gc, mock_worksheet = _make_mock_gc()
    with patch("gspread.service_account", return_value=mock_gc), patch.dict(
        "os.environ",
        {
            "GOOGLE_SHEETS_CREDENTIALS_PATH": "/fake/creds.json",
            "GOOGLE_SHEETS_SPREADSHEET_ID": "fake-id",
        },
    ), patch("os.path.exists", return_value=True):
        result = export_tickers_to_sheets([], {})
    assert result == 0
    assert mock_worksheet.append_rows.call_count == 0


@pytest.mark.unit
def test_row_length():
    """Each exported row has exactly 20 elements."""
    mock_gc, mock_worksheet = _make_mock_gc()
    with patch("gspread.service_account", return_value=mock_gc), patch.dict(
        "os.environ",
        {
            "GOOGLE_SHEETS_CREDENTIALS_PATH": "/fake/creds.json",
            "GOOGLE_SHEETS_SPREADSHEET_ID": "fake-id",
        },
    ), patch("os.path.exists", return_value=True):
        export_tickers_to_sheets(["AAPL"], {"AAPL": {"Price": "175.00"}})
    rows = mock_worksheet.append_rows.call_args[0][0]
    assert len(rows[0]) == 20


@pytest.mark.unit
def test_none_in_row():
    """None value in RSI field (column index 7) serializes to empty string."""
    mock_gc, mock_worksheet = _make_mock_gc()
    with patch("gspread.service_account", return_value=mock_gc), patch.dict(
        "os.environ",
        {
            "GOOGLE_SHEETS_CREDENTIALS_PATH": "/fake/creds.json",
            "GOOGLE_SHEETS_SPREADSHEET_ID": "fake-id",
        },
    ), patch("os.path.exists", return_value=True):
        export_tickers_to_sheets(["AAPL"], {"AAPL": {"RSI": None}})
    rows = mock_worksheet.append_rows.call_args[0][0]
    assert rows[0][7] == ""
