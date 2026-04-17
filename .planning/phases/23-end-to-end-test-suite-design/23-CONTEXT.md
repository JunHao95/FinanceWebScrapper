# Phase 23: End-to-End Test Suite Design - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Comprehensive test suite covering unit, integration, regression, and E2E tests. Critical user flows are documented, a testing framework (pytest + Playwright) is configured, all analytics modules have unit test coverage, all API routes have integration tests, indicator correctness has regression tests with pinned expected values, and the full scrape-to-display pipeline is validated by an E2E browser test.

</domain>

<decisions>
## Implementation Decisions

### Browser Automation
- Use Playwright (Python SDK via pytest-playwright) for E2E browser tests
- Test harness spins up Flask server on a random port via pytest fixture — no manual server start
- Headless by default; add --headed flag for debugging
- Chromium only — no cross-browser matrix needed

### Test Data Strategy
- Frozen CSV/JSON fixture files in tests/fixtures/, committed to git
- Mock all external API calls (yfinance, OpenAI) using monkeypatch/responses — no live network calls in any test
- Fixture files are version-controlled for reproducibility (follows existing spy_2017_2021.npy precedent)

### Coverage Gaps & Priority
- **Priority order:** Integration tests first → regression tests → unit gap fill → E2E
- **Integration:** All ~30 API routes get tests — each with happy-path and invalid-input coverage
- **Unit gaps:** Cover options_pricer, ml_models, rl_models, financial_analytics — happy path + one edge case per function
- **Regression:** Pin expected outputs for Volume Profile POC/VAH/VAL, Order Flow cumulative delta, Heston calibration convergence, HMM regime detection on frozen fixtures
- **E2E:** One golden path flow — enter ticker → Run Analysis → verify all 4 tabs render populated content without console errors

### Test Runner & Entry Point
- Makefile targets: `make test` (all), `make test-unit`, `make test-integration`, `make test-regression`, `make test-e2e`
- pytest markers registered in conftest.py: unit, integration, regression, e2e — Makefile wraps these
- `make test` runs all tiers including E2E
- Flat test directory layout with naming convention (test_unit_*, test_integration_*, test_regression_*, test_e2e_*) — no subdirectories
- Existing 19 test files remain in place; new tests follow the naming convention

### Regression Tolerance
- Claude's discretion: pick appropriate tolerance per computation type — tighter for pure math, looser for stochastic outputs

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/conftest.py`: Shared fixtures (zero_default_matrix, standard_heston_params, spy_returns, market_yields_normal)
- `tests/fixtures/spy_2017_2021.npy`: Existing frozen SPY returns fixture — pattern to follow for new fixtures
- 19 existing test files (~2,175 lines): trading_indicators, markov_chains, interest_rate_models, regime_detection, credit_transitions, fourier_pricer, heston_calibration, vasicek_model, portfolio_sharpe, earnings_quality, peer_comparison, bcc_route, chat_route, markov_route, math correctness benchmarks

### Established Patterns
- pytest with conftest.py fixtures (session-scoped and function-scoped)
- `pytest.mark.slow` marker already registered for network/long tests
- Route tests use Flask test client pattern (see test_bcc_route.py, test_chat_route.py, test_markov_route.py)

### Integration Points
- `webapp.py`: ~30 Flask routes to test (all @app.route decorators)
- `src/analytics/`: 8 analytics modules — trading_indicators, options_pricer, markov_chains, interest_rate_models, ml_models, rl_models, regime_detection, credit_transitions, financial_analytics
- `templates/index.html` + `static/js/`: Browser UI for E2E tests
- Existing test files need marker annotations added (unit/integration) to fit new tier system

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 23-end-to-end-test-suite-design*
*Context gathered: 2026-04-17*
