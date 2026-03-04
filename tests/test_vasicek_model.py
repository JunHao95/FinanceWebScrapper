"""
Tests for Vasicek (1977) closed-form interest rate model.

Covers:
  - vasicek_bond_price: boundary condition and value range
  - vasicek_yield_curve: shape and key structure
  - /api/interest_rate_model: Vasicek route, CIR feller_ratio, backward compat
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from src.analytics.interest_rate_models import vasicek_bond_price, vasicek_yield_curve


@pytest.fixture
def client():
    import webapp
    webapp.app.config['TESTING'] = True
    with webapp.app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Unit tests — pure functions
# ---------------------------------------------------------------------------

def test_vasicek_bond_price_at_zero():
    """T=0 boundary: bond price must equal exactly 1.0."""
    assert vasicek_bond_price(0.05, 0.0, 0.5, 0.06, 0.02) == 1.0


def test_vasicek_yield_curve_shape():
    """vasicek_yield_curve returns correct structure: list of dicts with expected keys."""
    curve = vasicek_yield_curve(0.05, [0.25, 1, 5, 10], 0.5, 0.06, 0.02)
    assert isinstance(curve, list)
    assert len(curve) == 4
    for point in curve:
        assert 'maturity' in point
        assert 'bond_price' in point
        assert 'spot_rate' in point


# ---------------------------------------------------------------------------
# Route integration tests
# ---------------------------------------------------------------------------

def test_vasicek_route(client):
    """POST /api/interest_rate_model with model=vasicek returns 200 with correct fields."""
    response = client.post('/api/interest_rate_model', json={'model': 'vasicek'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    result = data['result']
    assert isinstance(result['yield_curve'], list)
    assert len(result['yield_curve']) > 0
    assert result['feller_condition_satisfied'] is True
    assert result['feller_ratio'] is None


def test_cir_route_has_feller_ratio(client):
    """POST /api/interest_rate_model with no model field returns feller_ratio as a positive float."""
    response = client.post('/api/interest_rate_model', json={})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    result = data['result']
    assert 'feller_ratio' in result
    assert isinstance(result['feller_ratio'], float)
    assert result['feller_ratio'] > 0


def test_existing_cir_keys_preserved(client):
    """POST /api/interest_rate_model still returns all original CIR keys (backward compat)."""
    response = client.post('/api/interest_rate_model', json={})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    result = data['result']
    assert 'model' in result
    assert 'params' in result
    assert 'feller_condition_satisfied' in result
    assert 'yield_curve' in result
