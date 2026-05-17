# Phase 31: Integration with Google Sheets for Local Webapp — Research

**Researched:** 2026-05-17
**Domain:** gspread + google-auth, Flask POST endpoint, vanilla JS fetch pattern
**Confidence:** HIGH (all core claims verified against official gspread 6.x docs and PyPI)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Auth:** Service account JSON via `gspread` + `google-auth` (not oauth2client, not browser OAuth)
- **UI placement:** "Export to Sheets" button next to existing email button in `templates/index.html:285–290`
- **Button label:** `📊 Export to Sheets`
- **Route:** `POST /api/export-sheets`
- **Data columns:** Fixed ~20 curated columns — Metadata, Price/valuation, Technical, Sentiment, Fundamentals, Analytics scores
- **Append only:** Each export appends new rows; never overwrites
- **Sheet target:** First sheet tab (index 0); user pre-creates the Sheet
- **Config keys:** `GOOGLE_SHEETS_CREDENTIALS_PATH` + `GOOGLE_SHEETS_SPREADSHEET_ID` in `.env`
- **Feedback:** Use existing `Utils.showAlert(message, type)` pattern
- **Module file:** `src/utils/sheets_utils.py` following `email_utils.py` structure
- **Export date tag:** Every row has `YYYY-MM-DD` as the first column

### Claude's Discretion
- Exact gspread version pin and google-auth version pin
- Whether to validate Spreadsheet ID on Flask startup vs at export time
- Exact column ordering within each category group
- How to handle `None`/`null` values from analytics scores when serializing to Sheets cells

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

## Summary

Phase 31 adds a "Export to Google Sheets" button to the local webapp. The backend uses `gspread 6.2.1` (latest stable) with service account JSON credentials stored at a user-specified path. The flow is: user clicks button → JS collects curated fields from `AppState` → `POST /api/export-sheets` → `sheets_utils.py` authenticates via `gspread.service_account(filename=...)`, opens the spreadsheet by ID, and calls `worksheet.append_rows()` (batch) with one row per ticker. Every row starts with the export date.

The key design insight is that `None` values MUST be serialized to `""` (empty string) before passing to `append_rows()`; passing raw `None` into the values list will not raise an error but the Sheets API may handle it inconsistently, and passing `None` as the outer argument raises `TypeError`. The safe pattern is a `serialize_value()` helper that converts `None` → `""`, booleans → string, and coerces numbers.

**Primary recommendation:** Use `gspread==6.2.1` with `google-auth==2.52.0`, authenticate with `gspread.service_account(filename=path)`, validate credentials at export time (not startup), and always use `append_rows()` (batch, not per-row `append_row()`) for efficiency.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| gspread | 6.2.1 | Google Sheets API client | Dominant Python library, 6.x is current stable, uses google-auth natively |
| google-auth | 2.52.0 | Service account credential handling | Required by gspread 6, replaces deprecated oauth2client |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| google-auth-oauthlib | (not needed) | OAuth browser flow | Skip — service account JSON is the chosen approach |
| oauth2client | (deprecated) | Legacy credential handling | Do NOT use — Google deprecated it, gspread 6 docs explicitly warn against it |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| gspread | Raw google-api-python-client | Much more verbose; gspread is the idiomatic choice for Sheets |
| service account file | service_account_from_dict() | Dict approach avoids file path issues but requires parsing JSON manually; file path is simpler for this use case |

**Installation:**
```bash
pip install "gspread==6.2.1" "google-auth==2.52.0"
```

Add to `requirements.txt`:
```
gspread==6.2.1
google-auth==2.52.0
```

---

## Architecture Patterns

### Recommended Project Structure
```
src/utils/
├── email_utils.py        # existing — model to follow
└── sheets_utils.py       # NEW — follows same module structure

static/js/
├── api.js                # add API.exportSheets() method
└── stockScraper.js       # add StockScraper.exportSheets() method

templates/
└── index.html            # add button at line 285–290

webapp.py                 # add POST /api/export-sheets route
.env.example              # add GOOGLE_SHEETS_* keys with comments
```

### Pattern 1: Service Account Authentication (sheets_utils.py)

**What:** Load credentials from the path specified in `GOOGLE_SHEETS_CREDENTIALS_PATH` env var, authenticate, and return a gspread client.
**When to use:** Called at export time (lazy, not on startup). No module-level gspread client.

```python
# Source: https://docs.gspread.org/en/v6.1.2/oauth2.html
import os
import gspread
from gspread.exceptions import SpreadsheetNotFound, APIError

def get_sheets_client():
    creds_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH", "")
    if not creds_path or not os.path.exists(creds_path):
        raise FileNotFoundError(
            f"Google Sheets credentials file not found: {creds_path!r}. "
            "Set GOOGLE_SHEETS_CREDENTIALS_PATH in .env"
        )
    return gspread.service_account(filename=creds_path)
```

Alternative (more explicit, using google-auth directly — same outcome):
```python
# Source: https://docs.gspread.org/en/v6.1.2/oauth2.html
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

credentials = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
gc = gspread.authorize(credentials)
```

**Recommendation:** Use `gspread.service_account(filename=...)` — it's one line, handles scopes internally, and is the documented idiomatic pattern for gspread 6.

### Pattern 2: Opening Spreadsheet and Worksheet

```python
# Source: https://docs.gspread.org/en/latest/user-guide.html
spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "")
sh = gc.open_by_key(spreadsheet_id)
worksheet = sh.get_worksheet(0)   # index 0 = first tab
```

### Pattern 3: Batch Append Rows

Use `append_rows()` (plural) — one API call for all tickers. Do NOT call `append_row()` (singular) in a loop — that's N API calls and burns quota unnecessarily.

```python
# Source: https://docs.gspread.org/en/v6.1.2/api/models/worksheet.html
from gspread.utils import ValueInputOption

rows = [serialize_ticker_row(ticker, data, export_date) for ticker, data in export_data.items()]
worksheet.append_rows(rows, value_input_option=ValueInputOption.user_entered)
```

**`value_input_option` decision:**
- `ValueInputOption.raw` (default): Values stored exactly as-is — numbers stay numbers, strings stay strings.
- `ValueInputOption.user_entered`: Behaves like typing into UI — Sheets may interpret "2026-05-17" as a date and format it as one.
- **Use `user_entered`** so dates and numbers render correctly in Sheets (user-visible behavior). Downside: Sheets may auto-format floats. The tradeoff favors `user_entered` for a finance export.

### Pattern 4: None/null Serialization

**Critical:** The Sheets API does not accept `None` in cell values. Convert all None values before building the row list.

```python
def serialize_value(v):
    """Convert any Python value to a Sheets-safe string or number."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)          # True/False as strings, not 1/0
    if isinstance(v, (int, float)):
        return v               # Sheets handles numbers natively
    return str(v)              # everything else as string

def serialize_ticker_row(ticker, data, export_date):
    """Return a list of 20 values in fixed column order."""
    s = serialize_value
    return [
        export_date,               # Export Date (YYYY-MM-DD)
        ticker,                    # Ticker
        s(data.get("Price")),
        s(data.get("P/E")),
        s(data.get("Forward P/E")),
        s(data.get("P/B")),
        s(data.get("EPS")),
        s(data.get("RSI")),
        s(data.get("MA10 Signal")),
        s(data.get("MA20 Signal")),
        s(data.get("MA50 Signal")),
        s(data.get("Sentiment Score")),
        s(data.get("Revenue")),
        s(data.get("Profit Margin")),
        s(data.get("Operating Margin")),
        s(data.get("Debt/Equity")),
        s(data.get("Health Score")),
        s(data.get("Earnings Quality Flag")),
        s(data.get("DCF Intrinsic Value")),
        s(data.get("Peer P/E Percentile")),
    ]
```

### Pattern 5: Flask Route (webapp.py)

Follows the existing `send_email_report` pattern at webapp.py line 710:

```python
@app.route("/api/export-sheets", methods=["POST"])
def export_to_sheets():
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        tickers = payload.get("tickers", [])
        data = payload.get("data", {})
        
        if not tickers:
            return jsonify({"success": False, "error": "No tickers provided"}), 400
        
        from src.utils.sheets_utils import export_tickers_to_sheets
        rows_added = export_tickers_to_sheets(tickers, data)
        return jsonify({"success": True, "rows_added": rows_added})
    
    except FileNotFoundError as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except SpreadsheetNotFound:
        return jsonify({"success": False, "error": "Spreadsheet not found or not shared with service account"}), 500
    except APIError as e:
        return jsonify({"success": False, "error": f"Google Sheets API error: {e.response.json().get('error', {}).get('message', str(e))}"}), 500
    except Exception as e:
        logger.error(f"Error in export_to_sheets: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
```

### Pattern 6: Frontend JS (api.js + stockScraper.js)

Follow the `API.sendEmail()` pattern at `static/js/api.js:59`:

```javascript
// In api.js — add after sendEmail()
async exportSheets(exportData) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    try {
        const response = await fetch('/api/export-sheets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(exportData),
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Export failed (${response.status}): ${errorText}`);
        }
        return await response.json();
    } catch (error) {
        if (error.name === 'AbortError') throw new Error('Export timed out. Please try again.');
        throw error;
    }
}
```

```javascript
// In stockScraper.js — add after sendEmail() method
async exportSheets() {
    if (!AppState.currentData) {
        Utils.showAlert('No data to export. Please analyze stocks first.', 'error');
        return;
    }
    const btn = document.getElementById('exportSheetsBtn');
    if (btn) btn.disabled = true;
    try {
        Utils.showAlert('Exporting to Google Sheets...', 'info');
        const exportData = {
            tickers: AppState.currentTickers,
            data: AppState.currentData
        };
        const result = await API.exportSheets(exportData);
        if (result.success) {
            Utils.showAlert(`Exported ${result.rows_added} tickers to Google Sheets`, 'success');
        } else {
            Utils.showAlert('Google Sheets export failed: ' + result.error, 'error');
        }
    } catch (error) {
        Utils.showAlert('Google Sheets export failed: ' + error.message, 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}
```

### Pattern 7: Button HTML (templates/index.html)

Insert immediately after the existing `📧 Send Report` submit button at line 288:

```html
<button type="button"
        id="exportSheetsBtn"
        class="submit-btn"
        onclick="StockScraper.exportSheets()"
        disabled
        title="Configure Google Sheets credentials in .env to enable">
    Export to Sheets
</button>
```

The button starts disabled. JS enables it after scrape completes (same pattern as email button guard).

### Anti-Patterns to Avoid

- **Calling `append_row()` in a loop:** Burns N API calls per export. Use `append_rows()` once with all rows.
- **Passing raw `None` into the row list:** Results in inconsistent behavior across gspread versions. Always serialize to `""` first.
- **Authenticating once at module import time:** If credentials path changes or file is missing, the app crashes at startup. Lazy auth at export time gives a clean user-facing error instead.
- **Using `oauth2client`:** Deprecated. gspread 6 docs explicitly warn against it.
- **Catching bare `Exception` as the only handler:** Always catch `SpreadsheetNotFound`, `APIError`, and `FileNotFoundError` separately to return meaningful messages.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Google Sheets authentication | Custom OAuth2 token refresh | `gspread.service_account()` | Token refresh, scope management, and credential parsing handled automatically |
| Row append to spreadsheet | Direct HTTP calls to Sheets API v4 | `worksheet.append_rows()` | Pagination, auth headers, retry logic, API versioning all handled |
| Rate limit retry | Custom sleep/retry loop | `gspread.BackoffClient` (if needed) | Built-in exponential backoff; quota is 300 req/60s, append_rows counts as 1 request |

**Key insight:** For a local-only tool doing one batch append per user action, hitting rate limits is essentially impossible. `BackoffClient` is available but not needed for this use case.

---

## Common Pitfalls

### Pitfall 1: Spreadsheet Not Shared with Service Account
**What goes wrong:** `gspread.exceptions.SpreadsheetNotFound` raised even if spreadsheet ID is correct
**Why it happens:** The Google Sheets API returns 404 for spreadsheets the service account cannot access — same error as truly nonexistent spreadsheets
**How to avoid:** README must clearly instruct: "Share the spreadsheet with the service account email as Editor"
**Warning signs:** Export button works, spinner shows, then `SpreadsheetNotFound` error returns

### Pitfall 2: None Values in Row List
**What goes wrong:** Inconsistent cell values, potential `TypeError` in some gspread versions
**Why it happens:** `append_row(None)` raises `TypeError: object of type 'NoneType' has no len()`. None inside a list may produce empty cells or API errors.
**How to avoid:** Always run values through `serialize_value()` before building the row. Test with `data.get("NonExistentKey")` returning `None`.
**Warning signs:** Test with a ticker that has no Health Score computed — analytics fields will be `None`.

### Pitfall 3: Button Enable/Disable State Not Managed
**What goes wrong:** User clicks Export multiple times → multiple concurrent requests → duplicate rows appended
**Why it happens:** No disabled guard during export
**How to avoid:** Disable button at start of `exportSheets()`, re-enable in `finally` block (same pattern as `sendEmail()`)

### Pitfall 4: Credentials Path File Not Found vs. Missing Env Var
**What goes wrong:** Cryptic `gspread` error about invalid JSON or NoneType
**Why it happens:** `gspread.service_account(filename=None)` or `filename=""` will fail with a confusing error
**How to avoid:** Explicitly check `os.path.exists(creds_path)` before calling `gspread.service_account()` and raise `FileNotFoundError` with a human-readable message

### Pitfall 5: Spreadsheet ID Includes URL Parts
**What goes wrong:** `SpreadsheetNotFound` even though the sheet exists
**Why it happens:** User copies the full URL instead of just the ID (the alphanumeric string between `/d/` and `/edit`)
**How to avoid:** Add a note in README: "Copy only the spreadsheet ID from the URL (the long alphanumeric string), not the full URL"

### Pitfall 6: APIError Response Parsing
**What goes wrong:** `APIError` is caught but `str(e)` gives unhelpful output
**Why it happens:** `APIError` wraps a `requests.Response` object; the useful message is at `e.response.json()['error']['message']`
**How to avoid:** In the except block: `e.response.json().get('error', {}).get('message', str(e))`

---

## Code Examples

Verified patterns from official sources:

### Complete sheets_utils.py skeleton
```python
# Source: https://docs.gspread.org/en/v6.1.2/oauth2.html and user-guide.html
import os
import logging
from datetime import date
import gspread
from gspread.exceptions import SpreadsheetNotFound, APIError
from gspread.utils import ValueInputOption
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

COLUMN_HEADERS = [
    "Export Date", "Ticker",
    "Price", "P/E", "Forward P/E", "P/B", "EPS",
    "RSI", "MA10 Signal", "MA20 Signal", "MA50 Signal",
    "Sentiment Score",
    "Revenue", "Profit Margin", "Operating Margin", "Debt/Equity",
    "Health Score", "Earnings Quality Flag", "DCF Intrinsic Value", "Peer P/E Percentile",
]

def serialize_value(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int, float)):
        return v
    return str(v)

def get_sheets_client():
    creds_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH", "").strip()
    if not creds_path:
        raise FileNotFoundError(
            "GOOGLE_SHEETS_CREDENTIALS_PATH is not set in .env"
        )
    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            f"Credentials file not found at: {creds_path}"
        )
    return gspread.service_account(filename=creds_path)

def export_tickers_to_sheets(tickers, data):
    """
    Append one row per ticker to the configured Google Sheet.
    Returns the number of rows appended.
    Raises: FileNotFoundError, SpreadsheetNotFound, APIError
    """
    spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
    if not spreadsheet_id:
        raise ValueError("GOOGLE_SHEETS_SPREADSHEET_ID is not set in .env")
    
    gc = get_sheets_client()
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.get_worksheet(0)
    
    export_date = date.today().strftime("%Y-%m-%d")
    s = serialize_value
    rows = []
    for ticker in tickers:
        td = data.get(ticker, {})
        rows.append([
            export_date, ticker,
            s(td.get("Price")), s(td.get("P/E")), s(td.get("Forward P/E")),
            s(td.get("P/B")), s(td.get("EPS")),
            s(td.get("RSI")), s(td.get("MA10 Signal")),
            s(td.get("MA20 Signal")), s(td.get("MA50 Signal")),
            s(td.get("Sentiment Score")),
            s(td.get("Revenue")), s(td.get("Profit Margin")),
            s(td.get("Operating Margin")), s(td.get("Debt/Equity")),
            s(td.get("Health Score")), s(td.get("Earnings Quality Flag")),
            s(td.get("DCF Intrinsic Value")), s(td.get("Peer P/E Percentile")),
        ])
    
    if rows:
        worksheet.append_rows(rows, value_input_option=ValueInputOption.user_entered)
        logger.info(f"Appended {len(rows)} rows to Google Sheet {spreadsheet_id}")
    
    return len(rows)
```

### Checking if Sheets is configured (for button disabled state)
```python
# In webapp.py or a config-check route
def is_sheets_configured():
    creds_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH", "").strip()
    spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
    return bool(creds_path and spreadsheet_id and os.path.exists(creds_path))
```

Alternatively: expose a `GET /api/sheets-status` route that returns `{"configured": true/false}` — JS calls this on page load to toggle button disabled state.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `oauth2client` credentials | `google-auth` (`google.oauth2.service_account`) | gspread 5+ | oauth2client is deprecated; gspread 6 uses google-auth internally; `gspread.service_account()` abstracts this |
| Per-row `append_row()` in loop | Batch `append_rows()` | gspread 3+ | Single API call for multiple rows; avoids rate limits |
| `gspread.authorize(oauth2client_creds)` | `gspread.service_account(filename=...)` | gspread 4+ | Simpler, no manual scope management |

**Deprecated/outdated:**
- `oauth2client`: Do not use. gspread 6.x docs say "Google has deprecated it in favor of google-auth"
- `gspread.authorize()` with oauth2client credentials: Still works as fallback but discouraged

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | `pytest.ini` or inferred from `setup.cfg` |
| Quick run command | `pytest tests/test_unit_sheets_utils.py -x -q` |
| Full suite command | `pytest -m "unit or integration" -q` |

### Phase Requirements → Test Map
| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|-------------|
| `serialize_value(None)` returns `""` | unit | `pytest tests/test_unit_sheets_utils.py::test_serialize_none -x` | ❌ Wave 0 |
| `serialize_value(3.14)` returns `3.14` (number) | unit | `pytest tests/test_unit_sheets_utils.py::test_serialize_number -x` | ❌ Wave 0 |
| `get_sheets_client()` raises `FileNotFoundError` when path missing | unit | `pytest tests/test_unit_sheets_utils.py::test_missing_creds -x` | ❌ Wave 0 |
| `export_tickers_to_sheets()` calls `append_rows()` once (not per-ticker) | unit (mock) | `pytest tests/test_unit_sheets_utils.py::test_batch_append -x` | ❌ Wave 0 |
| `POST /api/export-sheets` returns 200 + `rows_added` on success | integration | `pytest tests/test_integration_routes.py::test_export_sheets_success -x` | ❌ Wave 0 |
| `POST /api/export-sheets` returns 500 + error message when creds missing | integration | `pytest tests/test_integration_routes.py::test_export_sheets_no_creds -x` | ❌ Wave 0 |
| `POST /api/export-sheets` returns 500 when SpreadsheetNotFound | integration | `pytest tests/test_integration_routes.py::test_export_sheets_not_found -x` | ❌ Wave 0 |

### Mock Pattern for sheets_utils Unit Tests

The correct pattern (following `conftest.py` conventions using `unittest.mock`):

```python
from unittest.mock import patch, MagicMock
import pytest

@pytest.mark.unit
def test_batch_append():
    mock_worksheet = MagicMock()
    mock_sh = MagicMock()
    mock_sh.get_worksheet.return_value = mock_worksheet
    mock_gc = MagicMock()
    mock_gc.open_by_key.return_value = mock_sh
    
    with patch("src.utils.sheets_utils.gspread.service_account", return_value=mock_gc), \
         patch.dict("os.environ", {
             "GOOGLE_SHEETS_CREDENTIALS_PATH": "/fake/creds.json",
             "GOOGLE_SHEETS_SPREADSHEET_ID": "fake-id",
         }), \
         patch("os.path.exists", return_value=True):
        
        from src.utils.sheets_utils import export_tickers_to_sheets
        rows_added = export_tickers_to_sheets(["AAPL", "MSFT"], {
            "AAPL": {"Price": "175.00", "RSI": "55.2"},
            "MSFT": {"Price": "420.00", "RSI": None},
        })
    
    assert rows_added == 2
    mock_worksheet.append_rows.assert_called_once()  # batch, not per-row
    call_args = mock_worksheet.append_rows.call_args[0][0]
    assert len(call_args) == 2
    # None serialized to ""
    assert "" in call_args[1]  # RSI for MSFT
```

### Sampling Rate
- **Per task commit:** `pytest tests/test_unit_sheets_utils.py -x -q`
- **Per wave merge:** `pytest -m "unit or integration" -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_unit_sheets_utils.py` — unit tests for `serialize_value`, `get_sheets_client`, `export_tickers_to_sheets`
- [ ] Integration test cases added to `tests/test_integration_routes.py` — covers POST /api/export-sheets success + error paths
- [ ] No new framework install needed — pytest 8.3.4 already present

---

## Open Questions

1. **Button enable/disable on page load — which mechanism?**
   - What we know: Button starts `disabled`. It needs to be enabled after scrape completes (same guard as email) AND only if credentials are configured.
   - What's unclear: Should JS call `GET /api/sheets-status` on page load, or should `webapp.py` inject a JS boolean into the HTML template?
   - Recommendation: Inject via Flask template context (`{{ sheets_configured }}`). Avoids an extra API call on page load. The route reads `os.environ` at request time.

2. **Column header row — does it exist in the user's Sheet?**
   - What we know: User pre-creates the Sheet manually.
   - What's unclear: Should the export auto-detect a header row or always append without checking?
   - Recommendation: Do NOT auto-write a header row. Document in README that the user should add the header row manually (or on first export, check if row 1 is empty and write headers). Keep simple for v1: always append, user is responsible for headers.

3. **Exact data key names from `AppState.currentData`**
   - What we know: The frontend sends `data` from `AppState.currentData`. The backend scraper returns keys like `"P/E Ratio (Yahoo)"` not `"P/E"`.
   - What's unclear: Does the frontend need to map/normalize these keys into the fixed 20 columns before sending to `/api/export-sheets`, or does the backend do the mapping?
   - Recommendation: Frontend sends raw `AppState.currentData` (same pattern as email). Backend `sheets_utils.py` does the key lookup — it already knows the field names from the scraper output. Use `data.get("P/E Ratio (Yahoo)", data.get("P/E Ratio", ""))` pattern to handle multi-source key names.

---

## Sources

### Primary (HIGH confidence)
- [gspread 6.1.2 Authentication docs](https://docs.gspread.org/en/v6.1.2/oauth2.html) — service_account(), Credentials.from_service_account_file(), scopes
- [gspread 6.1.2 Worksheet API](https://docs.gspread.org/en/v6.1.2/api/models/worksheet.html) — append_row(), append_rows() signatures, ValueInputOption
- [gspread Exceptions docs](https://docs.gspread.org/en/latest/api/exceptions.html) — SpreadsheetNotFound, APIError, WorksheetNotFound
- [gspread User Guide](https://docs.gspread.org/en/latest/user-guide.html) — open_by_key(), get_worksheet(0)
- [gspread 6.2.1 on PyPI](https://pypi.org/project/gspread/) — confirmed latest stable version (released May 14, 2025)
- [google-auth 2.52.0 on PyPI](https://pypi.org/project/google-auth/) — confirmed latest stable version (released May 7, 2026)

### Secondary (MEDIUM confidence)
- [gspread GitHub issue #486](https://github.com/burnash/gspread/issues/486) — confirms `append_row(None)` raises TypeError; None inside list → inconsistent behavior
- [gspread GitHub issue #537](https://github.com/burnash/gspread/issues/537) — empty cells in append can cause row indentation shift (avoid by serializing None → "")
- Community: gspread Sheets API v4 quota is 300 req/60s project-wide; single batch `append_rows()` = 1 request

### Tertiary (LOW confidence)
- BackoffClient availability: documented in gspread but not verified against v6.2.1 API — not needed for this phase's use case anyway

---

## Metadata

**Confidence breakdown:**
- Standard stack (gspread 6.2.1 + google-auth 2.52.0): HIGH — verified on PyPI, confirmed current stable
- Authentication patterns: HIGH — verified against official gspread 6.x docs
- append_rows() batch behavior: HIGH — verified in official Worksheet API docs
- None serialization pitfall: HIGH — verified against gspread GitHub issues with direct repro evidence
- Exception names (SpreadsheetNotFound, APIError, WorksheetNotFound): HIGH — verified in official exceptions docs
- Rate limits (300 req/60s): MEDIUM — from community sources, consistent with Google Sheets API v4 public documentation
- BackoffClient: LOW — mentioned in community results but not needed for phase

**Research date:** 2026-05-17
**Valid until:** 2026-08-17 (90 days — gspread 6.x is stable, unlikely to break between patch releases)
