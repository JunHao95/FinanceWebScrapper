---
phase: 31
plan: "02b"
status: complete
completed: "2026-05-21"
tasks_completed: 2
tasks_total: 2
key_files:
  created: []
  modified:
    - src/utils/sheets_utils.py
    - webapp.py
commits:
  - 9565cc5
---

# Plan 31-02b Summary: Complete sheets_utils.py Implementation + webapp Route

Replaced all NotImplementedError stubs with working code: upsert logic with formula preservation, named-tab routing by exchange suffix, 4 intelligence column generators, TI tab support with isolated partial-failure handling, and the full `export_tickers_to_sheets` function. Added `POST /api/export-sheets` route and `is_sheets_configured()` helper to `webapp.py`.

## Tasks

| Task | Name | Commit | Result |
|------|------|--------|--------|
| 1 | Implement sheets_utils.py — upsert, tab routing, intelligence columns, TI tab, export | 9565cc5 | 78 unit tests GREEN |
| 2 | Add POST /api/export-sheets route and is_sheets_configured() to webapp.py | 9565cc5 | 7 integration tests GREEN |

## Must-Have Verification

| Must-Have | Result |
|-----------|--------|
| pytest tests/test_unit_sheets_utils.py passes (78 tests) | ✓ |
| pytest tests/test_integration_routes.py::TestExportSheets passes (7 tests) | ✓ |
| Row length == 24 (with 4 intelligence columns) | ✓ test_row_length_* pass |
| Upsert: existing ticker updated in-place | ✓ test_upsert_updates_existing_ticker |
| Upsert: formula cells preserved | ✓ test_upsert_skips_formula_cells |
| Tab routing .SI → SG Stock | ✓ test_classify_sg |
| Tab routing .HK → HK Stock | ✓ test_classify_hk |
| Tab routing no-dot → US Stock | ✓ test_classify_us |
| Tab routing other-dot → Others Stock | ✓ test_classify_others |
| TI tab: _build_row_ti has 15 columns | ✓ test_build_row_ti_length |
| TI composite_dissenters list → joined string | ✓ test_build_row_ti_composite_dissenters_list_joined |
| export_tickers_to_sheets returns dict with ti_rows_added | ✓ test_export_with_ti_data_returns_ti_rows_added |
| TI partial failure returns warning key | ✓ test_export_ti_failure_returns_warning |
| webapp.py: POST /api/export-sheets present | ✓ grep confirms export_to_sheets at line 2805 |
| webapp.py: is_sheets_configured() present | ✓ grep confirms at line 345 |
| webapp.py: sheets_configured in index route | ✓ grep confirms at line 355 |
| webapp.py: ti_rows_added in response | ✓ grep confirms at line 2837 |

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| src/utils/sheets_utils.py has no NotImplementedError | ✓ |
| webapp.py has export_to_sheets route | ✓ |
| 78 unit tests pass | ✓ |
| 7 integration tests pass | ✓ |
| Commit 9565cc5 present | ✓ |
