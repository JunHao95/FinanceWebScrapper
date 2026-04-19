"""
Unit tests for src/analytics/rl_models.py

Covers: investment_mdp_policy_iteration, gridworld_policy_iteration.
L3/L4 functions require live yfinance data — excluded from unit tests.
"""
import pytest
from src.analytics.rl_models import investment_mdp_policy_iteration, gridworld_policy_iteration


# ---------------------------------------------------------------------------
# investment_mdp_policy_iteration — happy paths
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_investment_mdp_returns_expected_policy():
    result = investment_mdp_policy_iteration(gamma=0.95)
    assert result['optimal_policy'] == ['Buy', 'Sell', 'Sell']


@pytest.mark.unit
def test_investment_mdp_v_star_approximately_known():
    result = investment_mdp_policy_iteration(gamma=0.95)
    v = result['v_star']
    assert v[0] == pytest.approx(36.98, rel=0.02)
    assert v[1] == pytest.approx(35.68, rel=0.02)
    assert v[2] == pytest.approx(37.99, rel=0.02)


@pytest.mark.unit
def test_investment_mdp_keys():
    result = investment_mdp_policy_iteration()
    for k in ('states', 'actions', 'optimal_policy', 'v_star', 'q_matrix', 'iterations'):
        assert k in result


@pytest.mark.unit
def test_investment_mdp_converges_quickly():
    result = investment_mdp_policy_iteration()
    assert result['iterations'] <= 50


# ---------------------------------------------------------------------------
# investment_mdp_policy_iteration — edge cases
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_investment_mdp_gamma_near_zero_converges():
    # Very low discount — greedy; should still converge
    result = investment_mdp_policy_iteration(gamma=0.01)
    assert result['optimal_policy'] is not None
    assert len(result['optimal_policy']) == 3


@pytest.mark.unit
def test_investment_mdp_gamma_near_one_converges():
    result = investment_mdp_policy_iteration(gamma=0.999)
    assert isinstance(result['optimal_policy'], list)


# ---------------------------------------------------------------------------
# gridworld_policy_iteration — happy paths
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_gridworld_terminal_states_marked():
    result = gridworld_policy_iteration(use_wind=False)
    policy = result['policy']
    assert policy[0] == 'T'
    assert policy[15] == 'T'


@pytest.mark.unit
def test_gridworld_policy_length():
    result = gridworld_policy_iteration()
    assert len(result['policy']) == 16


@pytest.mark.unit
def test_gridworld_v_grid_shape():
    result = gridworld_policy_iteration()
    v = result['v_grid']
    assert len(v) == 4
    assert all(len(row) == 4 for row in v)


@pytest.mark.unit
def test_gridworld_terminal_values_zero():
    result = gridworld_policy_iteration()
    v = result['v_grid']
    assert v[0][0] == pytest.approx(0.0, abs=1e-6)
    assert v[3][3] == pytest.approx(0.0, abs=1e-6)


@pytest.mark.unit
def test_gridworld_non_terminal_values_negative():
    result = gridworld_policy_iteration()
    v = result['v_grid']
    for r in range(4):
        for c in range(4):
            if (r, c) not in ((0, 0), (3, 3)):
                assert v[r][c] < 0


@pytest.mark.unit
def test_gridworld_iterations_key_present():
    result = gridworld_policy_iteration()
    assert 'iterations' in result
    assert result['iterations'] >= 1


# ---------------------------------------------------------------------------
# gridworld — edge case: windy variant
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_gridworld_wind_variant_converges():
    result = gridworld_policy_iteration(use_wind=True)
    assert result['policy'][0] == 'T'
    assert result['policy'][15] == 'T'


@pytest.mark.unit
def test_gridworld_wind_policy_differs_or_same():
    # Wind may or may not change the policy — just ensure it runs without error
    r_no_wind = gridworld_policy_iteration(use_wind=False)
    r_wind = gridworld_policy_iteration(use_wind=True)
    assert len(r_wind['policy']) == len(r_no_wind['policy'])
