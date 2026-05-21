# Phase 31: Integration with GoogleSheets for local Webapp — Context

**Gathered:** 2026-05-17
**Updated:** 2026-05-21
**Status:** Active — new requirement added (Trading Indicators tab export)

<domain>
## Phase Boundary

Add a "Export to Google Sheets" feature to the local webapp. After scraping tickers, the user can manually push a curated set of financial metrics, analytics scores, and trading indicator signals into a Google Sheet they own. Each export upserts rows (one row per ticker, matched by ticker column; new tickers are appended). This is local-only — not deployed to Render. The Sheet is pre-created by the user; the webapp writes rows into it.

**Tabs written:**
- Fundamental data → existing user tabs (`US Stock`, `SG Stock`, `HK Stock`, `Others Stock`)
- Trading indicator signals → new auto-created `Trading Indicators` tab (webapp owns full schema)

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

### Trading Indicators tab export (new — 2026-05-21)

**Source data:** `AppState.tradingIndicatorsData[ticker]` in the browser — populated only when the user opens the Trading Indicators tab for a ticker. The frontend sends this dict as `trading_indicators_data` in the export payload alongside the existing `data` dict.

**Skip rule:** Tickers with no TI data (user never opened the tab) are silently skipped — no row written. Only tickers with a non-empty entry in `trading_indicators_data` appear in the `Trading Indicators` tab.

**Write mode:** Upsert — match by ticker at column B (index 1); update in-place if found, append after last data row if new. Same `_upsert_rows` logic as other tabs.

**Tab:** `"Trading Indicators"` — auto-created if absent (webapp owns full schema via `TI_COLUMN_HEADERS`).

**Schema (A–O, 15 columns — FINAL):**

| Col | Index | Field |
|-----|-------|-------|
| A | 0 | Export Date |
| B | 1 | Ticker |
| C | 2 | Lookback (days) |
| D | 3 | Volume Profile Signal |
| E | 4 | AVWAP Signal |
| F | 5 | AVWAP Convergence |
| G | 6 | Order Flow Signal |
| H | 7 | Order Flow Divergence |
| I | 8 | Sweep Signal |
| J | 9 | Sweep Price |
| K | 10 | Footprint Signal |
| L | 11 | Footprint Cum Delta |
| M | 12 | Composite Direction |
| N | 13 | Composite Score |
| O | 14 | Composite Dissenters |

**Frontend mapping** from `AppState.tradingIndicatorsData[ticker]`:
- `lookback` → Lookback
- `volume_profile_signal` → Volume Profile Signal
- `avwap_signal` → AVWAP Signal
- `avwap_convergence` → AVWAP Convergence
- `avwap_current_price` → not exported (redundant with Price in fundamentals tab)
- `order_flow_signal` → Order Flow Signal
- `order_flow_divergence` → Order Flow Divergence
- `sweep_signal` → Sweep Signal
- `sweep_price` → Sweep Price
- `footprint_signal` → Footprint Signal
- `footprint_cum_delta` → Footprint Cum Delta
- `composite_direction` → Composite Direction
- `composite_score` → Composite Score
- `composite_dissenters` → Composite Dissenters (list joined as comma-separated string, e.g. `"AVWAP, Order Flow"`)

**Changes required (amend existing 3 plans, not a 4th):**
1. `static/js/stockScraper.js` `exportSheets()` — add `trading_indicators_data: AppState.tradingIndicatorsData || {}` to `exportData` *(→ Plan 03)*
2. `webapp.py` `/api/export-sheets` — extract `trading_indicators_data = payload.get("trading_indicators_data", {})` and pass to `export_tickers_to_sheets` *(→ Plan 02)*
3. `src/utils/sheets_utils.py` — add `_TAB_TI`, `TI_COLUMN_HEADERS` (15 cols), `_build_row_ti(ticker, ti_data, export_date)`, `ROW_LENGTHS[_TAB_TI] = 15`, `_TICKER_COL[_TAB_TI] = 1`; update `export_tickers_to_sheets` to accept `trading_indicators_data=None` and route non-empty entries to TI tab after the fundamentals loop *(→ Plan 02)*
4. Tests — new stubs then implementations in `test_unit_sheets_utils.py`: `_build_row_ti` length/columns, skip-empty behavior, TI tab auto-created, upsert routes TI data correctly *(→ Plan 01 stubs, Plan 02 implementations)*
5. README — update Google Sheets export description to mention `Trading Indicators` tab *(→ Plan 03)*

### Partial failure behavior (multi-tab exports)
- **Fundamentals and TI tab are isolated** — a failure in the TI tab does NOT abort fundamentals writes, and vice versa
- **TI tab auto-creation failure** — only blocks TI rows; fundamentals still write
- **Response when TI fails:** `{ "success": true, "rows_added": N, "warning": "Trading Indicators: <reason>" }`
- **Response when TI succeeds:** `{ "success": true, "rows_added": N, "ti_rows_added": M }` (no warning field)
- **Frontend alert on full success:** `"Exported 3 tickers to Google Sheets ✓ (Trading Indicators: 2 tickers)"`
- **Frontend alert on partial success:** `"Exported 3 tickers to Google Sheets ✓ — Warning: <reason>"` (type: `warning`)
- **Frontend alert on full failure:** `"Google Sheets export failed: <reason>"` (type: `error`)

### Upsert behavior (all tabs)
- Each export **upserts** rows — existing ticker row updated in-place, new tickers appended after last data row
- Every row tagged with the export date (`YYYY-MM-DD`) as the first column
- Formula cells (starting with `=`) preserved — never overwritten
- TI tab: ticker matched at column B (index 1); fundamentals tabs: same

### Sheets target
- User pre-creates the Google Sheet manually in their Drive
- User copies the Spreadsheet ID from the URL and sets it in `.env` as `GOOGLE_SHEETS_SPREADSHEET_ID`
- Data written to named tabs (`US Stock`, `SG Stock`, `HK Stock`, `Others Stock`; `Trading Indicators` auto-created)
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
- Success (all tabs): `"Exported 3 tickers to Google Sheets ✓ (Trading Indicators: 2 tickers)"` (type: `success`)
- Partial success (TI failed): `"Exported 3 tickers to Google Sheets ✓ — Warning: Trading Indicators: <reason>"` (type: `warning`)
- Error: `"Google Sheets export failed: <reason>"` (type: `error`)
- While exporting: button shows spinner / disabled state, same UX pattern as email send

### Flask route
- Endpoint: `POST /api/export-sheets`
- Request body: `{ "tickers": ["AAPL", "MSFT"], "data": { ... }, "trading_indicators_data": { ... } }`
- Returns full success: `{ "success": true, "rows_added": N, "ti_rows_added": M }`
- Returns partial success: `{ "success": true, "rows_added": N, "warning": "Trading Indicators: <reason>" }`
- Returns failure: `{ "success": false, "error": "..." }`

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
- `static/js/utils.js:59` — `Utils.showAlert(message, type)` with `alertContainer` — use for success/error feedback; no new toast system needed; supports `"warning"` type for partial success
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
- `static/js/tradingIndicators.js:33–50` — `AppState.tradingIndicatorsData[ticker]` populated with all 14 signal fields when user opens the TI tab

</code_context>

<specifics>
## Specific Ideas

- This feature is explicitly **local-only** — the user noted it's "for local Webapp", so no need to handle Render deployment constraints (no 512MB ceiling concern, no environment var secrets concern beyond .env)
- The service account approach mirrors how many local Python tools (e.g. gspread tutorials) work — user is comfortable with this level of setup given they already configured SMTP, OpenAI keys, and FinHub API keys
- TI tab failure is isolated — fundamentals always write regardless of TI status, to avoid losing fundamental data due to a TI-only problem

</specifics>

<deferred>
## Deferred Ideas

- `avwap_current_price` field not exported — redundant with Price already in fundamentals tab
- AVWAP % deviation column (price vs AVWAP as %) — could be added to TI schema later, but not needed for v1

</deferred>

---

*Phase: 31-integration-with-googlesheets-for-local-webapp*
*Context gathered: 2026-05-17*
*Context updated: 2026-05-21*
