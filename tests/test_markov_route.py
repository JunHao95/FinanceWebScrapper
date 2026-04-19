"""
Integration tests for POST /api/markov_chain route.

These tests use the Flask test client. No mocking — tests exercise
in-process functions via the HTTP layer.

Tests fail until Task 2 registers the /api/markov_chain route in webapp.py.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    import webapp
    webapp.app.config['TESTING'] = True
    with webapp.app.test_client() as c:
        yield c


def post_markov(client, payload):
    """Helper: POST JSON to /api/markov_chain, return (status_code, parsed_json)."""
    resp = client.post(
        '/api/markov_chain',
        data=json.dumps(payload),
        content_type='application/json',
    )
    return resp.status_code, resp.get_json()


# ---------------------------------------------------------------------------
# Test 1: steady_state mode
# ---------------------------------------------------------------------------

def test_steady_state_mode(client):
    """mode=steady_state returns 200, steady_state is 8 floats summing to 1.0."""
    status, data = post_markov(client, {'mode': 'steady_state'})
    assert status == 200
    assert data['success'] is True
    result = data['result']
    pi = result['steady_state']
    assert isinstance(pi, list), "steady_state must be a list"
    assert len(pi) == 8, f"Expected 8 S&P ratings, got {len(pi)}"
    assert abs(sum(pi) - 1.0) < 1e-4, f"steady_state must sum to 1.0, got {sum(pi)}"


# ---------------------------------------------------------------------------
# Test 2: absorption mode
# ---------------------------------------------------------------------------

def test_absorption_mode(client):
    """mode=absorption returns 200, absorption_matrix is list-of-lists."""
    status, data = post_markov(client, {'mode': 'absorption'})
    assert status == 200
    assert data['success'] is True
    result = data['result']
    # S&P matrix has D as absorbing state — absorption_matrix must be present
    assert 'absorption_matrix' in result, "result must contain absorption_matrix"
    mat = result['absorption_matrix']
    assert isinstance(mat, list), "absorption_matrix must be a list"
    assert len(mat) > 0, "absorption_matrix must be non-empty"
    assert isinstance(mat[0], list), "absorption_matrix must be list-of-lists"


# ---------------------------------------------------------------------------
# Test 3: nstep mode
# ---------------------------------------------------------------------------

def test_nstep_mode(client):
    """mode=nstep with n=3 returns transition_matrix_n (8x8) AND term_structure."""
    status, data = post_markov(client, {'mode': 'nstep', 'n': 3, 'current_rating': 'BBB'})
    assert status == 200
    assert data['success'] is True
    result = data['result']

    # transition_matrix_n must be 8x8
    assert 'transition_matrix_n' in result, "result must contain transition_matrix_n"
    Pn = result['transition_matrix_n']
    assert isinstance(Pn, list), "transition_matrix_n must be a list"
    assert len(Pn) == 8, f"Expected 8 rows, got {len(Pn)}"
    assert len(Pn[0]) == 8, f"Expected 8 cols, got {len(Pn[0])}"

    # term_structure must be present
    assert 'term_structure' in result, "result must contain term_structure"
    ts = result['term_structure']
    assert isinstance(ts, list), "term_structure must be a list"
    assert len(ts) > 0, "term_structure must be non-empty"


# ---------------------------------------------------------------------------
# Test 4: term_structure mode
# ---------------------------------------------------------------------------

def test_term_structure_mode(client):
    """mode=term_structure returns non-empty list with horizon and default_probability."""
    status, data = post_markov(client, {'mode': 'term_structure', 'current_rating': 'BBB'})
    assert status == 200
    assert data['success'] is True
    result = data['result']

    assert 'term_structure' in result, "result must contain term_structure"
    ts = result['term_structure']
    assert isinstance(ts, list), "term_structure must be a list"
    assert len(ts) > 0, "term_structure must be non-empty"

    first = ts[0]
    # default_probability_term_structure returns 'horizon_years' and 'cumulative_default_prob'
    assert 'horizon_years' in first, "Each term_structure entry must have 'horizon_years'"
    assert 'cumulative_default_prob' in first, "Each entry must have 'cumulative_default_prob'"


# ---------------------------------------------------------------------------
# Test 5: mdp mode
# ---------------------------------------------------------------------------

def test_mdp_mode(client):
    """mode=mdp returns optimal_policy (3 ints) and value_function (3 floats)."""
    status, data = post_markov(client, {'mode': 'mdp'})
    assert status == 200
    assert data['success'] is True
    result = data['result']

    assert 'optimal_policy' in result, "result must contain optimal_policy"
    policy = result['optimal_policy']
    assert isinstance(policy, list), "optimal_policy must be a list"
    assert len(policy) == 3, f"Expected 3 policy entries, got {len(policy)}"
    assert all(isinstance(p, int) for p in policy), "optimal_policy entries must be ints"

    assert 'value_function' in result, "result must contain value_function"
    vf = result['value_function']
    assert isinstance(vf, list), "value_function must be a list"
    assert len(vf) == 3, f"Expected 3 value_function entries, got {len(vf)}"
    assert all(isinstance(v, float) for v in vf), "value_function entries must be floats"


# ---------------------------------------------------------------------------
# Test 6: default S&P matrix used when no transition_matrix supplied
# ---------------------------------------------------------------------------

def test_default_matrix_used(client):
    """mode=steady_state with no transition_matrix field uses SP_TRANSITION_MATRIX."""
    status, data = post_markov(client, {'mode': 'steady_state'})
    assert status == 200
    assert data['success'] is True
    result = data['result']
    # Result should have 8 elements (S&P 8-rating matrix)
    assert len(result['steady_state']) == 8


# ---------------------------------------------------------------------------
# Test 7: unknown mode returns 400
# ---------------------------------------------------------------------------

def test_unknown_mode_returns_400(client):
    """mode=nonexistent_mode returns 400 with success:false."""
    status, data = post_markov(client, {'mode': 'nonexistent_mode'})
    assert status == 400
    assert data['success'] is False
