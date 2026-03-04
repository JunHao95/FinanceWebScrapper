"""
Tests for POST /api/calibrate_bcc route.

Structure and error handling tests only — no live market calls.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    import webapp

    webapp.app.config["TESTING"] = True
    with webapp.app.test_client() as c:
        yield c


# Mock return dict that BCCCalibrator.calibrate() would return on success.
# Field names match the actual BCCCalibrator output (lam, delta_j — not lambda_j/sigma_j).
MOCK_BCC_RESULT = {
    "calibrated_params": {
        "kappa": 1.2,
        "theta": 0.04,
        "sigma_v": 0.3,
        "rho": -0.7,
        "v0": 0.04,
        "jump": {"lam": 0.5, "mu_j": -0.02, "delta_j": 0.1},
    },
    "rmse": 0.05,
    "mse": 0.0025,
    "spot": 185.0,
}


def test_bcc_route_exists(client):
    """POST /api/calibrate_bcc returns non-404 (route is registered)."""
    with patch(
        "src.derivatives.model_calibration.BCCCalibrator"
    ) as mock_cls:
        mock_inst = MagicMock()
        mock_cls.return_value = mock_inst
        mock_inst.calibrate.return_value = MOCK_BCC_RESULT
        response = client.post("/api/calibrate_bcc", json={"ticker": "AAPL"})
    assert response.status_code != 404, (
        f"Expected non-404 but got {response.status_code} — route not registered"
    )


def test_bcc_route_returns_success_structure(client):
    """Mock BCCCalibrator.calibrate returns valid dict; response has success:true, result.calibrated_params, result.rmse, result.jump_params."""
    with patch(
        "src.derivatives.model_calibration.BCCCalibrator"
    ) as mock_cls:
        mock_inst = MagicMock()
        mock_cls.return_value = mock_inst
        mock_inst.calibrate.return_value = MOCK_BCC_RESULT
        response = client.post("/api/calibrate_bcc", json={"ticker": "AAPL"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True, f"Expected success:true, got: {data}"
    assert "result" in data, f"Expected 'result' key in response, got: {list(data.keys())}"
    result = data["result"]
    assert "calibrated_params" in result, f"Missing 'calibrated_params' in result: {list(result.keys())}"
    assert "rmse" in result, f"Missing 'rmse' in result: {list(result.keys())}"
    assert "jump_params" in result, f"Missing 'jump_params' in result: {list(result.keys())}"


def test_bcc_route_jump_params_keys(client):
    """Mock returns dict with jump sub-dict; response result.jump_params has keys lambda_j, mu_j, sigma_j."""
    with patch(
        "src.derivatives.model_calibration.BCCCalibrator"
    ) as mock_cls:
        mock_inst = MagicMock()
        mock_cls.return_value = mock_inst
        mock_inst.calibrate.return_value = MOCK_BCC_RESULT
        response = client.post("/api/calibrate_bcc", json={"ticker": "AAPL"})

    assert response.status_code == 200
    data = response.get_json()
    jump_params = data["result"]["jump_params"]
    assert "lambda_j" in jump_params, f"Missing 'lambda_j' in jump_params: {jump_params}"
    assert "mu_j" in jump_params, f"Missing 'mu_j' in jump_params: {jump_params}"
    assert "sigma_j" in jump_params, f"Missing 'sigma_j' in jump_params: {jump_params}"
    # Values should be non-None (normalized from lam/delta_j)
    assert jump_params["lambda_j"] is not None
    assert jump_params["mu_j"] is not None
    assert jump_params["sigma_j"] is not None


def test_bcc_route_error_propagation(client):
    """Mock calibrate() returns {'error': ...}; response is success:false with error field, HTTP 500."""
    with patch(
        "src.derivatives.model_calibration.BCCCalibrator"
    ) as mock_cls:
        mock_inst = MagicMock()
        mock_cls.return_value = mock_inst
        mock_inst.calibrate.return_value = {"error": "No market data for TEST"}
        response = client.post("/api/calibrate_bcc", json={"ticker": "TEST"})

    assert response.status_code == 500, (
        f"Expected HTTP 500 for error propagation, got {response.status_code}"
    )
    data = response.get_json()
    assert data["success"] is False, f"Expected success:false, got: {data}"
    assert "error" in data, f"Expected 'error' key in response, got: {list(data.keys())}"
