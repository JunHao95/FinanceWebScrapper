---
phase: 31
slug: integration-with-googlesheets-for-local-webapp
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-17
---

# Phase 31 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.4 |
| **Config file** | `pytest.ini` (existing) |
| **Quick run command** | `pytest tests/test_unit_sheets_utils.py -x -q` |
| **Full suite command** | `pytest -m "unit or integration" -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_unit_sheets_utils.py -x -q`
- **After every plan wave:** Run `pytest -m "unit or integration" -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 31-01-01 | 01 | 1 | sheets_utils module | unit | `pytest tests/test_unit_sheets_utils.py::test_serialize_none -x` | ❌ W0 | ⬜ pending |
| 31-01-02 | 01 | 1 | serialize_value numbers | unit | `pytest tests/test_unit_sheets_utils.py::test_serialize_number -x` | ❌ W0 | ⬜ pending |
| 31-01-03 | 01 | 1 | missing credentials error | unit | `pytest tests/test_unit_sheets_utils.py::test_missing_creds -x` | ❌ W0 | ⬜ pending |
| 31-01-04 | 01 | 1 | batch append (not per-row) | unit | `pytest tests/test_unit_sheets_utils.py::test_batch_append -x` | ❌ W0 | ⬜ pending |
| 31-02-01 | 02 | 2 | POST /api/export-sheets 200 | integration | `pytest tests/test_integration_routes.py::test_export_sheets_success -x` | ❌ W0 | ⬜ pending |
| 31-02-02 | 02 | 2 | POST /api/export-sheets no creds | integration | `pytest tests/test_integration_routes.py::test_export_sheets_no_creds -x` | ❌ W0 | ⬜ pending |
| 31-02-03 | 02 | 2 | POST /api/export-sheets SpreadsheetNotFound | integration | `pytest tests/test_integration_routes.py::test_export_sheets_not_found -x` | ❌ W0 | ⬜ pending |
| 31-03-01 | 03 | 2 | button markup + data-sheets-unconfigured attribute | grep | `grep -n "data-sheets-unconfigured\|📊 Export to Sheets" templates/index.html` | ✅ | ⬜ pending |
| 31-03-02 | 03 | 2 | API.exportSheets() method in api.js | grep | `grep -n "exportSheets\|export-sheets" static/js/api.js` | ✅ | ⬜ pending |
| 31-03-03 | 03 | 2 | StockScraper.exportSheets() + sheetsUnconfigured guard | grep | `grep -n "exportSheets\|sheetsUnconfigured" static/js/stockScraper.js` | ✅ | ⬜ pending |
| 31-03-04 | 03 | 2 | README Google Sheets Setup section | grep | `grep -c "Google Sheets Setup" README.md` | ✅ | ⬜ pending |
| 31-03-05 | 03 | 2 | human checkpoint — button render + UX flow | manual-only | N/A — covered by Task 4 human checkpoint | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_unit_sheets_utils.py` — stubs for serialize_value, get_sheets_client, export_tickers_to_sheets
- [ ] Integration test cases in `tests/test_integration_routes.py` — POST /api/export-sheets success + error paths
- [ ] No new framework install needed — pytest 8.3.4 already present

*Existing infrastructure covers pytest setup; only new test files needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| UI button disabled when creds not configured | UI placement | Browser UI state not easily automatable | Load app without GOOGLE_SHEETS env vars; verify button disabled with tooltip |
| UI button disabled before scrape, enabled after scrape (when configured) | UI guard | Requires browser session state | Load app, verify button disabled; run scrape, verify button enabled (only when creds configured) |
| Success alert shown after export with rows count | UI feedback | Browser DOM assertion | Click export after scrape; verify green alert with "Exported N tickers" |
| Data appears correctly in actual Google Sheet | E2E | Requires real Google API credentials | Configure real creds + sheet ID, run export, verify rows in Sheet |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
