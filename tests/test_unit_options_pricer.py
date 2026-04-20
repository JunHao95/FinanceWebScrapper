"""
Unit tests for src/derivatives/options_pricer.py

Covers: black_scholes, binomial_tree, trinomial_tree, heston_price (OptionsPricer),
and the module-level black_scholes convenience wrapper.
"""
import math
import pytest
from src.derivatives.options_pricer import OptionsPricer, black_scholes


@pytest.fixture
def pricer():
    return OptionsPricer()


# ---------------------------------------------------------------------------
# Black-Scholes — happy paths
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_bs_atm_call_price(pricer):
    result = pricer.black_scholes(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call')
    assert result['price'] == pytest.approx(10.4506, rel=1e-2)


@pytest.mark.unit
def test_bs_atm_put_price(pricer):
    result = pricer.black_scholes(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='put')
    assert result['price'] > 0


@pytest.mark.unit
def test_bs_returns_greeks(pricer):
    result = pricer.black_scholes(S=100, K=100, T=1, r=0.05, sigma=0.2)
    for key in ('price', 'delta', 'gamma', 'theta', 'vega', 'rho'):
        assert key in result


@pytest.mark.unit
def test_bs_call_delta_bounds(pricer):
    result = pricer.black_scholes(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='call')
    assert 0 < result['delta'] < 1


@pytest.mark.unit
def test_bs_put_delta_bounds(pricer):
    result = pricer.black_scholes(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type='put')
    assert -1 < result['delta'] < 0


# ---------------------------------------------------------------------------
# Black-Scholes — edge cases
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_bs_deep_itm_call_above_intrinsic(pricer):
    # Deep ITM call: price should be at least the intrinsic value
    result = pricer.black_scholes(S=100, K=50, T=1, r=0.05, sigma=0.2, option_type='call')
    intrinsic = 100 - 50 * math.exp(-0.05 * 1)
    assert result['price'] >= intrinsic * 0.99


@pytest.mark.unit
def test_bs_put_call_parity(pricer):
    S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    call = pricer.black_scholes(S, K, T, r, sigma, 'call')['price']
    put = pricer.black_scholes(S, K, T, r, sigma, 'put')['price']
    # call - put == S - K*exp(-rT)
    expected = S - K * math.exp(-r * T)
    assert call - put == pytest.approx(expected, abs=0.01)


@pytest.mark.unit
def test_bs_invalid_T_raises(pricer):
    with pytest.raises(ValueError):
        pricer.black_scholes(S=100, K=100, T=-1, r=0.05, sigma=0.2)


@pytest.mark.unit
def test_bs_invalid_sigma_raises(pricer):
    with pytest.raises(ValueError):
        pricer.black_scholes(S=100, K=100, T=1, r=0.05, sigma=0)


# ---------------------------------------------------------------------------
# Module-level convenience wrapper
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_module_black_scholes_matches_class():
    cls_price = OptionsPricer().black_scholes(100, 100, 1, 0.05, 0.2)['price']
    mod_price = black_scholes(100, 100, 1, 0.05, 0.2)['price']
    assert cls_price == pytest.approx(mod_price, rel=1e-9)


# ---------------------------------------------------------------------------
# Binomial tree
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_binomial_european_call_close_to_bs(pricer):
    bs = pricer.black_scholes(100, 100, 1, 0.05, 0.2, 'call')['price']
    bt = pricer.binomial_tree(100, 100, 1, 0.05, 0.2, N=200, option_type='call')['price']
    assert bt == pytest.approx(bs, rel=0.02)


@pytest.mark.unit
def test_binomial_returns_valid_probability(pricer):
    result = pricer.binomial_tree(100, 100, 1, 0.05, 0.2, N=100)
    assert 0 < result['p'] < 1


@pytest.mark.unit
def test_binomial_american_put_ge_european(pricer):
    eu = pricer.binomial_tree(100, 100, 1, 0.05, 0.2, option_type='put',
                               exercise_type='european')['price']
    am = pricer.binomial_tree(100, 100, 1, 0.05, 0.2, option_type='put',
                               exercise_type='american')['price']
    assert am >= eu - 1e-10


# ---------------------------------------------------------------------------
# Trinomial tree
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_trinomial_european_call_close_to_bs(pricer):
    bs = pricer.black_scholes(100, 100, 1, 0.05, 0.2, 'call')['price']
    tt = pricer.trinomial_tree(100, 100, 1, 0.05, 0.2, N=100, option_type='call')['price']
    assert tt == pytest.approx(bs, rel=0.03)


@pytest.mark.unit
def test_trinomial_probabilities_sum_to_one(pricer):
    result = pricer.trinomial_tree(100, 100, 1, 0.05, 0.2, N=50)
    assert result['pu'] + result['pd'] + result['pm'] == pytest.approx(1.0, abs=1e-10)


# ---------------------------------------------------------------------------
# Heston price
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_heston_atm_price_in_plausible_range(pricer):
    result = pricer.heston_price(
        S=100, K=100, T=1, r=0.05,
        v0=0.04, kappa=2.0, theta=0.04, sigma_v=0.3, rho=-0.7,
    )
    assert 5 < result['price'] < 20


@pytest.mark.unit
def test_heston_result_contains_feller_key(pricer):
    result = pricer.heston_price(100, 100, 1, 0.05, 0.04, 2.0, 0.04, 0.3, -0.7)
    assert 'feller_condition_satisfied' in result


@pytest.mark.unit
def test_heston_price_is_positive(pricer):
    result = pricer.heston_price(100, 95, 0.5, 0.04, 0.04, 1.5, 0.04, 0.4, -0.5)
    assert result['price'] > 0
