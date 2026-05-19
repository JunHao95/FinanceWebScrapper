# Phase 31: Integration with GoogleSheets for local Webapp — Context

**Gathered:** 2026-05-17
**Updated:** 2026-05-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a "Export to Google Sheets" feature to the local webapp. After scraping tickers, the user can manually push a curated set of financial metrics and analytics scores into a Google Sheet they own. Each export appends timestamped rows (one row per ticker). This is local-only — not deployed to Render. The Sheet is pre-created by the user; the webapp writes rows into it.

Out of scope:
- Pulling data from Sheets into the webapp
- Auto-creating Sheets in the user's Drive
- Portfolio analytics (VaR, Sharpe, PCA) and ML Signals export
- Multi-currency normalization in the exported data

</domain>

<decisions>
## Implementation Decisions

### Data exported
- **Curated key fields only** — not the full ~60-field scrape dump. Fixed column set per row:
  - Metadata: `Export Date`, `Ticker`
  - Price & valuation: `Price`, `P/E`, `Forward P/E`, `P/B`, `EPS`
  - Technical: `RSI`, `MA10 Signal`, `MA20 Signal`, `MA50 Signal`
  - Sentiment: `Sentiment Score`
  - Fundamentals: `Revenue`, `Profit Margin`, `Operating Margin`, `Debt/Equity`
  - Analytics scores (blank if analysis wasn't run): `Health Score`, `Earnings Quality Flag`, `DCF Intrinsic Value`, `Peer P/E Percentile`
  - Intelligence columns (new — see detailed decisions below):
    - `Ticker Summary` — ~100-char rule-based sentence synthesizing price/valuation, technical signal digest, sentiment+health, DCF gap
    - `Recommended Action` — `Buy` / `Hold` / `Sell` + short rationale (e.g. "Buy — RSI oversold, 3/3 MA bullish, sentiment positive"); blank if no signals available
    - `Analysis Methods` — comma-separated labels of methods that ran (e.g. `DCF, Health Score, LSTM, RF, RSI/MA, Sentiment`)
    - `Data Source Credibility` — tier + source list (e.g. `High (Yahoo, Finnhub, Finviz, News)`)
- Columns always present in the sheet header; cells are empty if a particular score wasn't computed for that ticker
- Analytics scores section is NOT a separate button — same single export includes all available data
- Intelligence columns generated server-side in `sheets_utils.py` from existing scraped/analytics data — no new external API calls required

### Recommended Action column
- **Output tiers:** `Buy` / `Hold` / `Sell`
- **Format:** Label + short rationale inline, e.g. `"Buy — RSI oversold, 3/3 MA bullish, sentiment positive"`
- **Signal weights:** Claude's discretion — use all available signals (MA signals, RSI, Sentiment Score, Health Score, DCF gap, ML direction signals) weighted by availability; heavier weight to signals present for the ticker
- **Missing data:** Leave blank (empty cell) — consistent with how analytics scores handle absent data
- **Generated server-side** in `sheets_utils.py` from the export payload fields

### Ticker Summary column
- **Generation:** Rule-based template — fill from scraped fields, no LLM call, no extra API cost
- **Contents:** price/valuation snapshot (Price, P/E, P/B), technical signal digest (RSI level + MA consensus e.g. "2/3 MAs bullish"), sentiment direction + Health Score grade, DCF gap (above/below intrinsic value)
- **Target length:** ~100 chars, 1 sentence — dense, fits visible Sheets cell without row-height expansion
- **Example:** `"P/E 28, RSI 44 neutral, 2/3 MA bullish, Health B+, 8% DCF upside."`
- **Generated server-side** in `sheets_utils.py`; omit sections whose data is blank

### Analysis Methods column
- **Source of truth:** Infer from data presence in export payload — no new tracking plumbing needed:
  - `DCF Intrinsic Value` non-null → `DCF`
  - `Health Score` non-null → `Health Score`
  - `Earnings Quality Flag` non-null → `Earnings Quality`
  - `Peer P/E Percentile` non-null → `Peer Comparison`
  - `RSI` / MA signals non-null → `RSI/MA`
  - `Sentiment Score` non-null → `Sentiment`
  - ML payload `rf_available=True` → `RF`; `lstm_available=True` → `LSTM`
- **Format:** Comma-separated labels, e.g. `"DCF, Health Score, LSTM, RF, RSI/MA, Sentiment"`
- **Omit** any method whose data is blank/unavailable for that ticker

### Data Source Credibility column
- **Tier assignment (pre-fixed):**
  - `High`: Yahoo Finance, Finnhub, Finviz
  - `Medium`: News sentiment
  - `Low`: Reddit sentiment, Google Trends
- **Composite rule:** Highest tier present among sources that contributed non-null data for this ticker
- **Format:** `Tier (source1, source2, ...)` — e.g. `"High (Yahoo, Finnhub, News)"` or `"Medium (News, Reddit)"`
- **Sources detected** from which fields are non-null in the export payload (Yahoo → Price/PE/fundamentals; Finviz → Peer data; Finnhub → supplementary quote; Sentiment → sentiment score + breakdown)

### Append behavior
- Each export **appends** new rows to the Sheet (never overwrites)
- Every row tagged with the export date (`YYYY-MM-DD`) as the first column
- Multiple exports from the same session produce separate rows — user can filter by date in Sheets

### Sheets target
- User pre-creates the Google Sheet manually in their Drive
- User copies the Spreadsheet ID from the URL and sets it in `.env` as `GOOGLE_SHEETS_SPREADSHEET_ID`
- Data written to the first sheet tab (`Sheet1` / index 0)
- ID persists across sessions via `.env` — set once, works forever

### Auth
- **Service account JSON** — user creates a Google Cloud service account, downloads `credentials.json`, and sets `GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/credentials.json` in `.env`
- User must share the target Google Sheet with the service account email (as Editor) — noted in README
- No browser OAuth flow; no interactive prompts
- Python library: `gspread` + `google-auth` (`oauth2client` or `google-auth-oauthlib`) — to be added to `requirements.txt`

### UI placement
- "Export to Sheets" button lives **next to the existing 📧 Send Report button** in the email form area of the Stock Analysis tab (`templates/index.html:285–290`)
- Button label: `📊 Export to Sheets`
- Button is **disabled + tooltip** on page load if `GOOGLE_SHEETS_CREDENTIALS_PATH` or `GOOGLE_SHEETS_SPREADSHEET_ID` is not configured. Tooltip text: `"Configure Google Sheets credentials in .env to enable"`
- Button is also disabled if no scrape has been completed yet (same guard as email button)

### Feedback
- Uses existing `Utils.showAlert(message, type)` pattern (`alertContainer` in `utils.js`)
- Success: `"Exported 3 tickers to Google Sheets ✓"` (type: `success`)
- Error: `"Google Sheets export failed: <reason>"` (type: `error`)
- While exporting: button shows spinner / disabled state, same UX pattern as email send

### Flask route
- New endpoint: `POST /api/export-sheets`
- Request body: `{ "tickers": ["AAPL", "MSFT"], "data": { ... } }` — frontend sends the curated field subset
- Backend authenticates via service account, appends rows to the target Sheet
- Returns `{ "success": true, "rows_added": 3 }` or `{ "success": false, "error": "..." }`

### Setup documentation
- A new **"Google Sheets Setup"** section in `README.md` — step-by-step:
  1. Create Google Cloud project + enable Sheets API
  2. Create service account, download credentials JSON
  3. Share the target Sheet with the service account email (Editor)
  4. Set `GOOGLE_SHEETS_CREDENTIALS_PATH` and `GOOGLE_SHEETS_SPREADSHEET_ID` in `.env`
- No in-app setup modal needed

### Claude's Discretion
- Exact gspread version and auth library choice (`google-auth` vs `oauth2client`)
- Whether to validate the Spreadsheet ID on Flask startup vs at export time
- Exact column ordering within each category group
- How to handle the `None`/`null` values from analytics scores when serializing to Sheets cells
- Signal weights for Recommended Action verdict (use all available signals, heavier weight to those present)
- Exact thresholds for RSI levels (e.g. oversold < 30, overbought > 70) in summary/verdict logic
- Column position of the 4 intelligence columns relative to existing schema (append after `Peer P/E Percentile`)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `static/js/api.js:59` — `API.sendEmail()`: pattern to replicate for `API.exportSheets()` — `fetch('/api/export-sheets', { method: 'POST', body: JSON.stringify(...) })`
- `static/js/utils.js:59` — `Utils.showAlert(message, type)` with `alertContainer` — use for success/error feedback; no new toast system needed
- `static/js/stockScraper.js:287` — `StockScraper.sendEmail()`: model for `StockScraper.exportSheets()` — same guard pattern (check `AppState.currentData` before proceeding)
- `src/utils/email_utils.py` — existing pattern for a utility module handling external service integration; `src/utils/sheets_utils.py` follows the same structure

### Established Patterns
- `.env` keys use `FINANCE_` prefix for email (e.g. `FINANCE_SMTP_SERVER`); Google Sheets keys should use `GOOGLE_SHEETS_` prefix for clarity
- Button disable guard: email button is only enabled after scrape completes — replicate same JS guard for Sheets button
- `webapp.py` POST endpoints: read JSON body via `request.get_json()`, validate required fields, return `{ "success": bool, "error": "..." }` or `{ "success": true, ... }`

### Integration Points
- `templates/index.html:285–290` — add `📊 Export to Sheets` button adjacent to existing email form
- `webapp.py` — add `POST /api/export-sheets` route following pattern of `send_email_report` at line 710
- `requirements.txt` — add `gspread` and `google-auth`
- `.env.example` — add `GOOGLE_SHEETS_CREDENTIALS_PATH` and `GOOGLE_SHEETS_SPREADSHEET_ID` with placeholder values and comments
- `static/js/stockScraper.js` — add `exportSheets()` method; wire to button in `main.js`

</code_context>

<specifics>
## Specific Ideas

- This feature is explicitly **local-only** — the user noted it's "for local Webapp", so no need to handle Render deployment constraints (no 512MB ceiling concern, no environment var secrets concern beyond .env)
- The service account approach mirrors how many local Python tools (e.g. gspread tutorials) work — user is comfortable with this level of setup given they already configured SMTP, OpenAI keys, and FinHub API keys

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 31-integration-with-googlesheets-for-local-webapp*
*Context gathered: 2026-05-17*
