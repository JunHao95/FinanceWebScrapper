---
phase: 23-end-to-end-test-suite-design
plan: 03
status: complete
---

# Phase 23-03 Summary — Unit & Regression Tests

## What was built

### Unit test files (4 new files)

| File | Coverage | Tests |
|------|----------|-------|
| `tests/test_unit_options_pricer.py` | black_scholes, binomial_tree, trinomial_tree, heston_price, put-call parity | 16 |
| `tests/test_unit_rl_models.py` | investment_mdp_policy_iteration, gridworld_policy_iteration (happy + edge) | 14 |
| `tests/test_unit_financial_analytics.py` | fundamental_analysis, compute_pct_increase, _parse_numeric_value, _extract_metric, _interpret_regression | 21 |
| `tests/test_unit_ml_models.py` | TEST-03 traceability — import smoke tests + RegimeDetector thin behaviours | 8 |

Total: **59 new unit tests**, all marked `@pytest.mark.unit`, all pass with `make test-unit`.

### Fixture data (3 new files)

| File | Description |
|------|-------------|
| `tests/fixtures/volume_profile_ohlcv.csv` | 150-row synthetic OHLCV (seed=42, asymmetric H/L so delta ≠ 0) |
| `tests/fixtures/order_flow_ohlcv.csv` | Same data used for Order Flow regression |
| `tests/fixtures/heston_market_prices.json` | 15 synthetic option contracts (BS prices, S=100, σ=0.20) |

### Regression test files (2 new files)

| File | Tests | Pinned values |
|------|-------|---------------|
| `tests/test_regression_indicators.py` | Volume Profile POC/VAH/VAL, signal, Order Flow cumulative delta, divergence fields | POC=149.41, VAH=157.26, VAL=145.48, cum_delta=9,667,644.5 |
| `tests/test_regression_stochastic.py` | Heston RMSE < 1.0, HMM March 2020 stressed >60%, determinism, two-regime separation | RMSE < 1.0 (rel=0.10), smoothed_probs.sum == 1.0 |

Total: **17 regression tests**, all pass with `make test-regression`.

### Bug fix

`tests/conftest.py`: Added `.ravel()` to `spy_returns` fixture loading to handle the pre-existing `(N,1)` shape stored in `spy_2017_2021.npy`. This also fixes the pre-existing `test_spy_march_2020_is_stressed` failure in `test_regime_detection.py`.

### Fixture generation script

`scripts/generate_fixtures.py`: Deterministic synthetic OHLCV generator (seed=42) and BS-priced Heston market JSON. Run once; commit outputs.

## Verification

```
pytest tests/test_unit_*.py -m unit -q        → 63 passed
pytest tests/test_regression_*.py -m regression -q → 17 passed
make test-unit                                 → all pass
make test-regression                           → all pass
```

## Requirements satisfied

- TEST-03: `test_unit_ml_models.py` documents ml_models.py absence and verifies RegimeDetector + FinancialAnalytics cover ML functionality
- TEST-05: Regression tests pin Volume Profile, Order Flow, Heston, HMM with appropriate tolerances
- No test makes a live network call
- All fixture files committed to `tests/fixtures/`
