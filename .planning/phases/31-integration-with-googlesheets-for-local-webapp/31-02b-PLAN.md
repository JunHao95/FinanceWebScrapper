---
phase: 31-integration-with-googlesheets-for-local-webapp
plan: "02b"
type: execute
wave: 2
depends_on: [31-02]
files_modified:
  - src/utils/sheets_utils.py
  - webapp.py
autonomous: true
requirements: [SHEETS-BACKEND]
must_haves:
  truths:
    - "pytest tests/test_unit_sheets_utils.py -x -q passes all unit tests (GREEN, not skip)"
    - "pytest tests/test_integration_routes.py::TestExportSheets -x -q passes all 7 integration tests"
    - "Each fundamentals row has exactly 24 elements including 4 populated intelligence columns"
    - "Upsert: existing ticker row updated in-place; formula cells not overwritten"
    - "Named tab routing: .SI suffix → SG Stock, .HK → HK Stock, no/other suffix → US Stock or Others Stock"
    - "TI tab auto-created if absent; TI rows use 15-column schema"
    - "POST /api/export-sheets full success: {success: true, rows_added: N, ti_rows_added: M}"
    - "POST /api/export-sheets TI partial failure: {success: true, rows_added: N, warning: 'Trading Indicators: <reason>'}"
  artifacts:
    - path: "src/utils/sheets_utils.py"
      provides: "Fully implemented _upsert_rows, _build_row (with 4 intelligence generators), _build_row_ti, _tab_for_ticker, _create_tab_if_absent, export_tickers_to_sheets"
      exports: ["export_tickers_to_sheets", "_upsert_rows", "_build_row_ti", "_tab_for_ticker"]
    - path: "webapp.py"
      provides: "POST /api/export-sheets route with partial-failure handling; is_sheets_configured() helper; sheets_configured injected into index template"
      contains: "export_to_sheets, is_sheets_configured, ti_rows_added"
  key_links:
    - from: "webapp.py"
      to: "src/utils/sheets_utils.py"
      via: "local import inside route function"
      pattern: "from src.utils.sheets_utils import export_tickers_to_sheets"
    - from: "src/utils/sheets_utils.py"
      to: "gspread worksheet"
      via: "sh.worksheet(tab_name) then get_all_values() + update() or append_rows()"
      pattern: "sh\\.worksheet"
    - from: "src/utils/sheets_utils.py"
      to: "intelligence column generators"
      via: "_generate_ticker_summary, _generate_recommended_action, _generate_analysis_methods, _generate_data_source_credibility"
      pattern: "_generate_"
---

<objective>
Complete the sheets_utils.py implementation: replace all NotImplementedError stubs with working code for _upsert_rows (fetch-then-upsert with formula preservation), tab routing by ticker suffix, _create_tab_if_absent helper, the 4 intelligence column generators, and the full export_tickers_to_sheets function with TI tab support and isolated partial failure handling.

Also add the POST /api/export-sheets route and is_sheets_configured() helper to webapp.py.

Purpose: Make all unit and integration tests go GREEN. This is the last backend plan before frontend wiring in plan 31-03.
Output: Modified src/utils/sheets_utils.py (stubs replaced with implementations), modified webapp.py
</objective>

<execution_context>
@/Users/junhaotee/.claude/get-shit-done/workflows/execute-plan.md
@/Users/junhaotee/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/31-integration-with-googlesheets-for-local-webapp/31-CONTEXT.md
@.planning/phases/31-integration-with-googlesheets-for-local-webapp/31-RESEARCH.md
@src/utils/sheets_utils.py
@src/utils/email_utils.py
@webapp.py

<interfaces>
<!-- Key contracts established in plan 31-02. Executor implements THESE signatures. -->

From plan 31-02 (src/utils/sheets_utils.py stubs to replace):

def _upsert_rows(existing_rows, new_row, ticker_col=1) -> list:
    # Replace NotImplementedError with:
    # - Scan existing_rows for a row where row[ticker_col] == new_row[ticker_col]
    # - If found: merge new_row into that position — overwrite non-formula cells, preserve cells starting with "="
    # - If not found: append new_row
    # - Return updated list (same reference or new list, caller uses return value)

def export_tickers_to_sheets(tickers, data, trading_indicators_data=None) -> dict:
    # Replace NotImplementedError with full implementation (see Task 1 action)

Tab routing rule (CONTEXT.md locked):
- ticker ends with ".SI"  → _TAB_SG  ("SG Stock")
- ticker ends with ".HK"  → _TAB_HK  ("HK Stock")
- ticker ends with ".SW", ".PA", ".DE", ".L" or any other dot-suffix → _TAB_OTHERS ("Others Stock")
- no dot suffix (e.g. "AAPL", "MSFT", "TSLA") → _TAB_US ("US Stock")

_create_tab_if_absent(sh, tab_name, headers):
- Check sh.worksheets() for a sheet with title == tab_name
- If absent: sh.add_worksheet(title=tab_name, rows=1000, cols=len(headers)); write headers to row 1
- Return the worksheet object

Intelligence column generators (rule-based, no LLM):
- _generate_ticker_summary(td) → str (~100 chars) synthesizing price/valuation, MA consensus, Health, DCF gap
- _generate_recommended_action(td) → str: "Buy/Hold/Sell — <rationale>" or "" if no signals
- _generate_analysis_methods(td) → str: comma-sep labels e.g. "DCF, Health Score, RSI/MA, Sentiment"
- _generate_data_source_credibility(td) → str: "High (Yahoo, Finnhub, News)" or similar

From webapp.py (route pattern to mirror):
```python
@app.route("/api/send-email", methods=["POST"])
def send_email_report():
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"success": False, "error": "No data provided"}), 400
        ...
        from src.utils.email_utils import send_email_report
        ...
        return jsonify({"success": True, ...})
    except Exception as e:
        logger.error(...)
        return jsonify({"success": False, "error": str(e)}), 500
```

Response contracts (CONTEXT.md locked):
Full success:    {"success": True, "rows_added": N, "ti_rows_added": M}
Partial failure: {"success": True, "rows_added": N, "warning": "Trading Indicators: <reason>"}
Full failure:    {"success": False, "error": "..."}
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Implement sheets_utils.py — upsert, tab routing, intelligence columns, TI tab, export function</name>
  <files>src/utils/sheets_utils.py</files>
  <behavior>
    _upsert_rows:
    - test_upsert_existing_ticker: existing AAPL row gets updated; only one AAPL row in result
    - test_upsert_new_ticker: AAPL added after existing MSFT row; result has 2 rows
    - test_formula_cell_preserved: cell starting with "=" in existing row NOT overwritten by new_row value

    _tab_for_ticker:
    - test_tab_routing_sg: "0001.SI" → "SG Stock"
    - test_tab_routing_hk: "0700.HK" → "HK Stock"
    - test_tab_routing_us: "AAPL" → "US Stock"
    - test_tab_routing_others: "NOVN.SW" → "Others Stock"

    _build_row (intelligence columns now populated):
    - test_row_length: row has 24 elements
    - Intelligence columns non-empty when data signals are present

    _build_row_ti:
    - test_build_row_ti_length: 15 elements
    - test_ti_composite_dissenters_joined: list → "AVWAP, Order Flow"

    export_tickers_to_sheets:
    - test_batch_upsert: returns 2 for 2 tickers
    - test_empty_tickers: returns 0, no write calls
    - TI success: returns dict with ti_rows_added key
    - TI partial failure: returns dict with warning key, rows_added still present
  </behavior>
  <action>
    Read src/utils/sheets_utils.py first (from plan 31-02). Replace the two NotImplementedError stubs and add helper functions. Do NOT remove or change anything that already works (serialize_value, get_sheets_client, _build_row stub structure, constants).

    --- Add _tab_for_ticker helper ---
    ```python
    def _tab_for_ticker(ticker):
        """Route ticker to the correct named worksheet tab based on exchange suffix."""
        t = ticker.upper()
        if t.endswith(".SI"):
            return _TAB_SG
        if t.endswith(".HK"):
            return _TAB_HK
        if "." in t:
            # Any other dot-suffix = non-US/SG/HK exchange
            return _TAB_OTHERS
        return _TAB_US
    ```

    --- Add _create_tab_if_absent helper ---
    ```python
    def _create_tab_if_absent(sh, tab_name, headers):
        """Return worksheet for tab_name, creating it with headers if it doesn't exist."""
        existing_titles = [ws.title for ws in sh.worksheets()]
        if tab_name not in existing_titles:
            ws = sh.add_worksheet(title=tab_name, rows=1000, cols=len(headers))
            ws.append_row(headers)
            logger.info(f"Auto-created tab '{tab_name}' in spreadsheet")
        else:
            ws = sh.worksheet(tab_name)
        return ws
    ```

    --- Replace _upsert_rows NotImplementedError ---
    ```python
    def _upsert_rows(existing_rows, new_row, ticker_col=1):
        """
        Upsert new_row into existing_rows.
        - If a row with matching ticker (at ticker_col) found: update non-formula cells in-place.
        - Formula cells (starting with '=') are preserved unchanged.
        - If not found: append new_row.
        Returns updated rows list.
        """
        ticker = new_row[ticker_col] if len(new_row) > ticker_col else None
        if ticker is None:
            return existing_rows + [new_row]

        for i, row in enumerate(existing_rows):
            if len(row) > ticker_col and row[ticker_col] == ticker:
                # Update in-place, preserving formula cells
                merged = list(row)
                for col_idx, new_val in enumerate(new_row):
                    if col_idx < len(merged):
                        existing_val = str(merged[col_idx])
                        if existing_val.startswith("="):
                            continue  # preserve formula
                        merged[col_idx] = new_val
                    else:
                        merged.append(new_val)
                existing_rows[i] = merged
                return existing_rows

        # Ticker not found — append
        existing_rows.append(new_row)
        return existing_rows
    ```

    --- Update _build_row to call intelligence generators ---
    Replace the four "" stubs at the end of _build_row with:
    ```python
    _generate_ticker_summary(td),
    _generate_recommended_action(td),
    _generate_analysis_methods(td),
    _generate_data_source_credibility(td),
    ```

    --- Add 4 intelligence generators (rule-based, no LLM) ---

    _generate_ticker_summary:
    ```python
    def _generate_ticker_summary(td):
        """~100-char rule-based sentence: price/valuation, MA consensus, Health, DCF gap."""
        parts = []
        price = td.get("Price")
        pe = td.get("P/E Ratio (Yahoo)", td.get("P/E Ratio", td.get("P/E")))
        pb = td.get("P/B Ratio", td.get("P/B"))
        if pe:
            parts.append(f"P/E {pe}")
        if pb:
            parts.append(f"P/B {pb}")

        rsi = td.get("RSI")
        if rsi:
            try:
                rsi_v = float(str(rsi))
                rsi_label = "oversold" if rsi_v < 30 else "overbought" if rsi_v > 70 else "neutral"
                parts.append(f"RSI {rsi_v:.0f} {rsi_label}")
            except (ValueError, TypeError):
                pass

        ma_signals = [td.get("MA10 Signal", td.get("10-Day MA Signal")),
                      td.get("MA20 Signal", td.get("20-Day MA Signal")),
                      td.get("MA50 Signal", td.get("50-Day MA Signal"))]
        bullish_mas = sum(1 for s in ma_signals if s and "bullish" in str(s).lower())
        total_mas = sum(1 for s in ma_signals if s)
        if total_mas > 0:
            parts.append(f"{bullish_mas}/{total_mas} MA bullish")

        health = td.get("Health Score")
        if health:
            parts.append(f"Health {health}")

        dcf = td.get("DCF Intrinsic Value")
        if dcf and price:
            try:
                gap_pct = (float(str(dcf)) - float(str(price))) / float(str(price)) * 100
                direction = "upside" if gap_pct > 0 else "downside"
                parts.append(f"{abs(gap_pct):.0f}% DCF {direction}")
            except (ValueError, TypeError, ZeroDivisionError):
                pass

        summary = ", ".join(parts)
        return summary[:120] if summary else ""
    ```

    _generate_recommended_action:
    ```python
    def _generate_recommended_action(td):
        """Buy / Hold / Sell + rationale based on available signals. Blank if no signals."""
        signals = []

        rsi = td.get("RSI")
        if rsi:
            try:
                rsi_v = float(str(rsi))
                if rsi_v < 30:
                    signals.append(("buy", "RSI oversold"))
                elif rsi_v > 70:
                    signals.append(("sell", "RSI overbought"))
                else:
                    signals.append(("hold", "RSI neutral"))
            except (ValueError, TypeError):
                pass

        ma_signals_raw = [td.get("MA10 Signal", td.get("10-Day MA Signal")),
                          td.get("MA20 Signal", td.get("20-Day MA Signal")),
                          td.get("MA50 Signal", td.get("50-Day MA Signal"))]
        bullish_mas = sum(1 for s in ma_signals_raw if s and "bullish" in str(s).lower())
        bearish_mas = sum(1 for s in ma_signals_raw if s and "bearish" in str(s).lower())
        total_mas = sum(1 for s in ma_signals_raw if s)
        if total_mas > 0:
            if bullish_mas >= 2:
                signals.append(("buy", f"{bullish_mas}/{total_mas} MA bullish"))
            elif bearish_mas >= 2:
                signals.append(("sell", f"{bearish_mas}/{total_mas} MA bearish"))

        sentiment = td.get("Sentiment Score")
        if sentiment:
            try:
                sent_v = float(str(sentiment))
                if sent_v > 0.1:
                    signals.append(("buy", "sentiment positive"))
                elif sent_v < -0.1:
                    signals.append(("sell", "sentiment negative"))
            except (ValueError, TypeError):
                pass

        if not signals:
            return ""

        buy_count = sum(1 for direction, _ in signals if direction == "buy")
        sell_count = sum(1 for direction, _ in signals if direction == "sell")
        rationales = [r for _, r in signals]

        if buy_count > sell_count:
            verdict = "Buy"
        elif sell_count > buy_count:
            verdict = "Sell"
        else:
            verdict = "Hold"

        return f"{verdict} — {', '.join(rationales)}"
    ```

    _generate_analysis_methods:
    ```python
    def _generate_analysis_methods(td):
        """Comma-separated labels of methods that ran, inferred from non-null fields."""
        methods = []
        if td.get("DCF Intrinsic Value") not in (None, "", "N/A"):
            methods.append("DCF")
        if td.get("Health Score") not in (None, "", "N/A"):
            methods.append("Health Score")
        if td.get("Earnings Quality Flag") not in (None, "", "N/A"):
            methods.append("Earnings Quality")
        if td.get("Peer P/E Percentile") not in (None, "", "N/A"):
            methods.append("Peer Comparison")
        rsi_present = td.get("RSI") not in (None, "", "N/A")
        ma_present = any(td.get(k) not in (None, "", "N/A") for k in
                         ["MA10 Signal", "MA20 Signal", "MA50 Signal",
                          "10-Day MA Signal", "20-Day MA Signal", "50-Day MA Signal"])
        if rsi_present or ma_present:
            methods.append("RSI/MA")
        if td.get("Sentiment Score") not in (None, "", "N/A"):
            methods.append("Sentiment")
        if td.get("rf_available") is True:
            methods.append("RF")
        if td.get("lstm_available") is True:
            methods.append("LSTM")
        return ", ".join(methods)
    ```

    _generate_data_source_credibility:
    ```python
    def _generate_data_source_credibility(td):
        """Tier (source1, source2, ...) based on non-null field presence."""
        sources = []
        # Yahoo Finance: price and fundamentals
        if td.get("Price") not in (None, ""):
            sources.append(("High", "Yahoo"))
        if td.get("Peer P/E Percentile") not in (None, ""):
            sources.append(("High", "Finviz"))
        # Sentiment
        if td.get("Sentiment Score") not in (None, ""):
            sources.append(("Medium", "News"))

        if not sources:
            return ""

        tier_order = {"High": 0, "Medium": 1, "Low": 2}
        best_tier = min(sources, key=lambda x: tier_order.get(x[0], 99))[0]
        source_names = list(dict.fromkeys(s for _, s in sources))  # deduplicate, preserve order
        return f"{best_tier} ({', '.join(source_names)})"
    ```

    --- Replace export_tickers_to_sheets NotImplementedError ---
    ```python
    def export_tickers_to_sheets(tickers, data, trading_indicators_data=None):
        """
        Upsert one row per ticker to named Google Sheets tabs.
        Routes by exchange suffix (.SI→SG Stock, .HK→HK Stock, others→Others Stock, none→US Stock).
        Also exports Trading Indicators tab if trading_indicators_data provided.

        Returns:
            dict: {"rows_added": N, "ti_rows_added": M} on full success
                  {"rows_added": N, "warning": "Trading Indicators: <reason>"} on TI partial failure
        Raises:
            FileNotFoundError, ValueError: credential / config problems
            gspread.exceptions.SpreadsheetNotFound: spreadsheet not accessible
        """
        from gspread.utils import ValueInputOption

        spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
        if not spreadsheet_id:
            raise ValueError("GOOGLE_SHEETS_SPREADSHEET_ID is not set in .env")

        gc = get_sheets_client()
        sh = gc.open_by_key(spreadsheet_id)
        export_date = date.today().strftime("%Y-%m-%d")

        # --- Fundamentals export (named tabs by exchange) ---
        rows_added = 0
        if tickers:
            # Group tickers by destination tab
            tab_groups = {}
            for ticker in tickers:
                tab_name = _tab_for_ticker(ticker)
                tab_groups.setdefault(tab_name, []).append(ticker)

            for tab_name, tab_tickers in tab_groups.items():
                ws = sh.worksheet(tab_name)
                existing = ws.get_all_values()

                for ticker in tab_tickers:
                    td = data.get(ticker, {})
                    new_row = _build_row(ticker, td, export_date)
                    existing = _upsert_rows(existing, new_row, ticker_col=1)
                    rows_added += 1

                # Write back — skip row 0 (header) if present, update data rows
                # Use update starting at A2 to preserve header row
                if len(existing) > 1:
                    ws.update(range_name="A2", values=existing[1:],
                              value_input_option=ValueInputOption.user_entered)
                elif len(existing) == 1:
                    ws.update(range_name="A2", values=existing,
                              value_input_option=ValueInputOption.user_entered)

            logger.info(f"Upserted {rows_added} rows to Google Sheet {spreadsheet_id}")

        # --- Trading Indicators export (isolated — partial failure allowed) ---
        result = {"rows_added": rows_added}
        ti_data = trading_indicators_data or {}

        if ti_data:
            try:
                ti_ws = _create_tab_if_absent(sh, _TAB_TI, TI_COLUMN_HEADERS)
                existing_ti = ti_ws.get_all_values()

                ti_rows_added = 0
                for ticker, td in ti_data.items():
                    if not td:
                        continue
                    new_ti_row = _build_row_ti(ticker, td, export_date)
                    existing_ti = _upsert_rows(existing_ti, new_ti_row, ticker_col=1)
                    ti_rows_added += 1

                if ti_rows_added > 0:
                    if len(existing_ti) > 1:
                        ti_ws.update(range_name="A2", values=existing_ti[1:],
                                     value_input_option=ValueInputOption.user_entered)
                    elif len(existing_ti) == 1:
                        ti_ws.update(range_name="A2", values=existing_ti,
                                     value_input_option=ValueInputOption.user_entered)

                logger.info(f"Upserted {ti_rows_added} TI rows to '{_TAB_TI}' tab")
                result["ti_rows_added"] = ti_rows_added

            except Exception as ti_err:
                logger.warning(f"TI tab export failed (fundamentals unaffected): {ti_err}")
                result["warning"] = f"Trading Indicators: {ti_err}"

        return result
    ```
  </action>
  <verify>
    <automated>cd /Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper && pytest tests/test_unit_sheets_utils.py -x -q 2>&1 | tail -15</automated>
  </verify>
  <done>All unit tests in test_unit_sheets_utils.py pass GREEN; no xfail or NotImplementedError errors; row_length==24; upsert tests pass; _build_row_ti length==15; tab routing tests pass</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Add POST /api/export-sheets route and is_sheets_configured() to webapp.py</name>
  <files>webapp.py</files>
  <behavior>
    - POST /api/export-sheets with valid payload → 200 + {success: true, rows_added: N, ti_rows_added: M}
    - POST /api/export-sheets when TI partial failure → 200 + {success: true, rows_added: N, warning: "Trading Indicators: ..."}
    - POST /api/export-sheets with no JSON body → 400 + {success: false, error: "No data provided"}
    - POST /api/export-sheets with tickers=[] → 400 + {success: false, error: "No tickers provided"}
    - POST /api/export-sheets when FileNotFoundError → 500 + {success: false, error: contains message}
    - POST /api/export-sheets when SpreadsheetNotFound → 500 + {success: false, error: "Spreadsheet not found or not shared with service account"}
    - GET / renders with sheets_configured boolean in template context
  </behavior>
  <action>
    Read webapp.py first. Make THREE changes:

    Change 1 — Add is_sheets_configured() helper near the top of webapp.py (after the imports section, before the route definitions):
    ```python
    def is_sheets_configured():
        """Return True if Google Sheets credentials and spreadsheet ID are configured."""
        creds_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH", "").strip()
        spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
        return bool(creds_path and spreadsheet_id and os.path.exists(creds_path))
    ```

    Change 2 — Modify the index() route to pass sheets_configured into template context:
    ```python
    @app.route("/")
    def index():
        """Render the main page"""
        return render_template("index.html", sheets_configured=is_sheets_configured())
    ```

    Change 3 — Add POST /api/export-sheets route immediately after the send_email_report route. Follow the exact same try/except pattern. The route extracts trading_indicators_data from payload and handles partial failure via the warning key in the response from export_tickers_to_sheets:

    ```python
    @app.route("/api/export-sheets", methods=["POST"])
    def export_to_sheets():
        """
        Export stock data to Google Sheets using upsert behavior.

        Expected JSON payload:
        {
            "tickers": ["AAPL", "MSFT"],
            "data": {"AAPL": {...}, "MSFT": {...}},
            "trading_indicators_data": {"AAPL": {...}}   # optional
        }

        Returns:
            Full success:    {"success": true, "rows_added": N, "ti_rows_added": M}
            Partial failure: {"success": true, "rows_added": N, "warning": "Trading Indicators: ..."}
            Failure:         {"success": false, "error": "..."}
        """
        try:
            payload = request.get_json()
            if not payload:
                return jsonify({"success": False, "error": "No data provided"}), 400

            tickers = payload.get("tickers", [])
            data = payload.get("data", {})
            trading_indicators_data = payload.get("trading_indicators_data", {})

            if not tickers:
                return jsonify({"success": False, "error": "No tickers provided"}), 400

            from src.utils.sheets_utils import export_tickers_to_sheets
            from gspread.exceptions import SpreadsheetNotFound, APIError

            export_result = export_tickers_to_sheets(
                tickers, data, trading_indicators_data=trading_indicators_data
            )

            # Build response from export_result dict
            response = {"success": True, "rows_added": export_result.get("rows_added", 0)}
            if "ti_rows_added" in export_result:
                response["ti_rows_added"] = export_result["ti_rows_added"]
            if "warning" in export_result:
                response["warning"] = export_result["warning"]

            return jsonify(response)

        except FileNotFoundError as e:
            return jsonify({"success": False, "error": str(e)}), 500
        except SpreadsheetNotFound:
            return jsonify({"success": False,
                            "error": "Spreadsheet not found or not shared with service account"}), 500
        except APIError as e:
            try:
                msg = e.response.json().get("error", {}).get("message", str(e))
            except Exception:
                msg = str(e)
            return jsonify({"success": False, "error": f"Google Sheets API error: {msg}"}), 500
        except Exception as e:
            logger.error(f"Error in export_to_sheets: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500
    ```
  </action>
  <verify>
    <automated>cd /Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper && pytest tests/test_integration_routes.py::TestExportSheets -x -q 2>&1 | tail -15</automated>
  </verify>
  <done>All 7 TestExportSheets integration tests pass; grep shows "export_to_sheets" in webapp.py; grep shows "ti_rows_added" in webapp.py; grep shows "sheets_configured" in webapp.py index route</done>
</task>

</tasks>

<verification>
pytest tests/test_unit_sheets_utils.py -q 2>&1 | tail -5
pytest tests/test_integration_routes.py::TestExportSheets -q 2>&1 | tail -5
grep -n "is_sheets_configured\|export_to_sheets\|ti_rows_added" /Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper/webapp.py | head -20
grep -n "_upsert_rows\|_tab_for_ticker\|_create_tab_if_absent\|export_tickers_to_sheets" /Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper/src/utils/sheets_utils.py | head -20
</verification>

<success_criteria>
- All unit tests in test_unit_sheets_utils.py pass (GREEN, not skip/xfail/NotImplementedError)
- All 7 integration tests in TestExportSheets pass
- row_length test asserts 24 and passes
- _upsert_rows: existing ticker updated in-place, formula cells preserved, new ticker appended
- Tab routing: .SI→SG Stock, .HK→HK Stock, plain→US Stock, other suffix→Others Stock
- TI tab: _build_row_ti produces 15 elements; composite_dissenters joined as string
- export_tickers_to_sheets returns dict with rows_added + (ti_rows_added OR warning)
- webapp.py: POST /api/export-sheets route present, handles partial failure, returns ti_rows_added or warning
- webapp.py: is_sheets_configured() helper present; index() route passes sheets_configured to template
</success_criteria>

<output>
After completion, create .planning/phases/31-integration-with-googlesheets-for-local-webapp/31-02b-SUMMARY.md
</output>
