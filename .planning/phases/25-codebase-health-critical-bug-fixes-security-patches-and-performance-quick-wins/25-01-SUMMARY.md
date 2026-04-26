---
phase: 25-codebase-health-critical-bug-fixes-security-patches-and-performance-quick-wins
plan: 01
status: complete
completed: 2026-04-26
---

# Summary: Phase 25-01 — Wave 0 Test Scaffold + Bug Fixes

## What was done

### Task 1: Wave 0 test scaffold
- Created `tests/test_unit_codebase_health.py` with 9 unit tests covering all Phase 25 items.
- Added 3 integration stubs to `tests/test_integration_routes.py` (email allowlist, rate limiting, client API keys).
- Wave 0 RED state confirmed: `test_no_debug_prints` and `test_percentile_rank` pass; 7 remaining tests stay RED pending later plans.

### Task 2: Bug fixes

**BUG-01 — Remove debug print() calls from src/**
Fixed in 8 files:
- `src/indicators/technical_indicators.py`: removed redundant `print(20*"###")` and duplicate print (logger.error already present)
- `src/utils/data_formatter.py`: added module-level logger; CSV/Excel error prints → `logger.error`
- `src/utils/comparison_utils.py`: added module-level logger; metric/operator warning prints → `logger.warning`
- `src/utils/email_utils.py`: sending confirmation prints → `logger.info`
- `src/scrapers/finviz_scraper.py`: analyst/price debug prints → `self.logger.debug` (via BaseScraper)
- `src/scrapers/cnn_scraper.py`: added module-level logger; DEBUG print → `logger.debug`, error print → `logger.error`
- `src/sentiment/sentiment_analyzer.py`: all 6 progress/debug prints → `self.logger.info` / `self.logger.debug`
- `src/analytics/credit_transitions.py`: test assertion print → `logger.debug`

`display_formatter.py` intentionally excluded — its `print()` calls are CLI terminal output, not debug noise.

**BUG-02 — Fix JS advanced-settings drawer reference**
- `static/js/stockScraper.js` line 49: `getElementById('advanced-settings')` → `getElementById('settings-drawer')`
- Line 50: `advancedDetails.open` → `advancedDetails.classList.contains('drawer-open')` (div uses CSS class, not `<details>.open`)

**BUG-03 — Fix percentile_rank in webapp.py**
- Added `import bisect` at top of `webapp.py`
- Fixed both copies of `percentile_rank` (~lines 2089 and 2123): removed broken `if target not in vals: return 50` guard, replaced `vals.index(target)` with `bisect.bisect_left(vals, target)` + clamp
- Result: min→0, median→50, max→100 for a 5-element sorted list

## Verification

```
pytest tests/test_unit_codebase_health.py::test_no_debug_prints tests/test_unit_codebase_health.py::test_percentile_rank -v
# 2 passed

grep -r "^\s*print(" src/ webapp.py --include="*.py" | grep -v display_formatter | wc -l
# 0

grep "settings-drawer" static/js/stockScraper.js
# const advancedDetails = document.getElementById('settings-drawer');

grep "bisect" webapp.py
# import bisect ... bisect.bisect_left (×2)
```

Full suite (excl. E2E): 278 passed, 9 failed (all Wave 0 stubs for plans 25-02 through 25-05 — expected RED).

## Next plan
25-02: Security patches — SECRET_KEY guard, email allowlist, Flask-Limiter rate limiting, remove client API key handling.
