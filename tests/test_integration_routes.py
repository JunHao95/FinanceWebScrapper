"""
Integration tests for all Flask API routes not covered by existing test files.

Existing coverage (excluded here):
  /api/calibrate_bcc      → test_bcc_route.py
  /api/chat               → test_chat_route.py
  /api/markov_chain       → test_markov_route.py
  /api/peers              → test_peer_comparison.py
  /api/portfolio_sharpe   → test_portfolio_sharpe.py
  /api/trading_indicators → test_trading_indicators.py
  /api/interest_rate_model → test_vasicek_model.py

All tests here use the shared `client` fixture from conftest.py.
External I/O (yfinance, OpenAI, calibrators) is mocked via unittest.mock.patch.
"""

import json
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_OPTION_PARAMS = {
    "spot": 100.0,
    "strike": 105.0,
    "maturity": 0.25,
    "risk_free_rate": 0.05,
    "volatility": 0.20,
}

_HESTON_PARAMS = {
    "spot": 100.0,
    "strike": 100.0,
    "maturity": 1.0,
    "risk_free_rate": 0.05,
    "v0": 0.04,
    "kappa": 2.0,
    "theta": 0.04,
    "sigma_v": 0.30,
    "rho": -0.70,
    "option_type": "call",
}

_MERTON_PARAMS = {
    "spot": 100.0,
    "strike": 105.0,
    "maturity": 0.25,
    "risk_free_rate": 0.05,
    "sigma": 0.20,
    "lambda": 2.0,
    "mu_j": -0.05,
    "delta_j": 0.10,
    "option_type": "call",
}


def _make_price_history(n=60):
    """Minimal yfinance-style DataFrame with Close prices."""
    idx = pd.date_range("2020-01-01", periods=n, freq="B", tz="America/New_York")
    closes = 100.0 + np.linspace(0, 10, n)
    return pd.DataFrame(
        {
            "Close": closes,
            "Open": closes - 0.5,
            "High": closes + 1.0,
            "Low": closes - 1.0,
            "Volume": 1_000_000.0,
        },
        index=idx,
    )


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


class TestHealthRoute:

    def test_health_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_has_timestamp(self, client):
        resp = client.get("/health")
        data = resp.get_json()
        assert "timestamp" in data


# ---------------------------------------------------------------------------
# GET /api/validate_ticker
# ---------------------------------------------------------------------------


class TestValidateTicker:

    def test_valid_symbol(self, client):
        mock_ticker = MagicMock()
        mock_ticker.fast_info.display_name = "Apple Inc."
        with patch("yfinance.Ticker", return_value=mock_ticker):
            resp = client.get("/api/validate_ticker?symbol=AAPL")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["valid"] is True
        assert "name" in data

    def test_missing_symbol_returns_invalid(self, client):
        resp = client.get("/api/validate_ticker")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["valid"] is False


# ---------------------------------------------------------------------------
# POST /api/fundamental-analysis
# ---------------------------------------------------------------------------


class TestFundamentalAnalysis:

    _stock_data = {
        "P/E Ratio": 28.5,
        "P/B Ratio": 5.2,
        "P/S Ratio": 7.8,
        "ROE": 25.3,
        "ROA": 12.1,
        "Operating Margin": 30.2,
        "EPS": 6.15,
        "EBITDA": 125_000_000_000,
        "Free Cash Flow": 95_000_000_000,
        "Operating Cash Flow": 110_000_000_000,
    }

    def test_happy_path(self, client):
        mock_analytics = MagicMock()
        mock_analytics.fundamental_analysis.return_value = {
            "score": 75,
            "recommendation": "BUY",
            "strengths": [],
            "weaknesses": [],
        }
        with patch("webapp.get_financial_analytics", return_value=mock_analytics):
            resp = client.post(
                "/api/fundamental-analysis",
                json={"ticker": "AAPL", "data": self._stock_data},
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "analysis" in data

    def test_missing_ticker_returns_400(self, client):
        resp = client.post("/api/fundamental-analysis", json={"data": self._stock_data})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_no_body_returns_400(self, client):
        resp = client.post("/api/fundamental-analysis", json={})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/scrape
# ---------------------------------------------------------------------------


class TestScrapeRoute:

    def test_happy_path(self, client):
        mock_cnn = MagicMock()
        mock_cnn.scrape_data.return_value = {"fear_greed": 50}
        with patch("webapp.CNNFearGreedScraper", return_value=mock_cnn), patch(
            "webapp.run_scrapers_for_ticker", return_value={"P/E Ratio": "28.5"}
        ):
            resp = client.post(
                "/api/scrape", json={"tickers": ["AAPL"], "sources": ["yahoo"]}
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("success") is True

    def test_missing_tickers_returns_400(self, client):
        resp = client.post("/api/scrape", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_enhanced_sentiment_source_accepted(self, client):
        mock_cnn = MagicMock()
        mock_cnn.scrape_data.return_value = {"fear_greed": 50}
        sentiment_data = {
            "Overall Sentiment Score (Enhanced)": "0.120",
            "Overall Sentiment Label (Enhanced)": "Positive",
        }
        with patch("webapp.CNNFearGreedScraper", return_value=mock_cnn), patch(
            "webapp.run_scrapers_for_ticker", return_value=sentiment_data
        ):
            resp = client.post(
                "/api/scrape",
                json={"tickers": ["AAPL"], "sources": ["enhanced_sentiment"]},
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("success") is True
        assert "Overall Sentiment Score (Enhanced)" in data["data"]["AAPL"]


# ---------------------------------------------------------------------------
# POST /api/send-email
# ---------------------------------------------------------------------------


class TestSendEmail:

    def test_happy_path(self, client):
        with patch("webapp.send_consolidated_report", return_value=True), patch.dict(
            "webapp.config", {"email_allowlist": []}, clear=False
        ), patch.dict("os.environ", {"EMAIL_ALLOWLIST": ""}, clear=False):
            resp = client.post(
                "/api/send-email",
                json={
                    "tickers": ["AAPL"],
                    "data": {"AAPL": {"P/E Ratio": "28.5"}},
                    "cnn_data": {},
                    "email": "test@example.com",
                },
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_missing_email_returns_400(self, client):
        with patch.dict(
            "webapp.config", {"email_allowlist": []}, clear=False
        ), patch.dict("os.environ", {"EMAIL_ALLOWLIST": ""}, clear=False):
            resp = client.post(
                "/api/send-email",
                json={
                    "tickers": ["AAPL"],
                    "data": {},
                    "cnn_data": {},
                },
            )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False


# ---------------------------------------------------------------------------
# POST /api/option_pricing
# ---------------------------------------------------------------------------


class TestOptionPricing:

    def test_happy_path(self, client):
        resp = client.post(
            "/api/option_pricing", json={**_OPTION_PARAMS, "models": ["black_scholes"]}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "results" in data
        assert "black_scholes" in data["results"]

    def test_missing_spot_returns_400(self, client):
        body = {k: v for k, v in _OPTION_PARAMS.items() if k != "spot"}
        resp = client.post("/api/option_pricing", json=body)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/implied_volatility
# ---------------------------------------------------------------------------


class TestImpliedVolatility:

    def test_happy_path(self, client):
        resp = client.post(
            "/api/implied_volatility",
            json={
                **_OPTION_PARAMS,
                "market_price": 5.50,
                "option_type": "call",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "result" in data

    def test_missing_market_price_returns_400(self, client):
        resp = client.post("/api/implied_volatility", json=_OPTION_PARAMS)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/greeks
# ---------------------------------------------------------------------------


class TestGreeks:

    def test_happy_path(self, client):
        resp = client.post("/api/greeks", json=_OPTION_PARAMS)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "greeks" in data
        greeks = data["greeks"]
        for key in ("delta", "gamma", "theta", "vega"):
            assert key in greeks, f"Missing greek: {key}"

    def test_missing_volatility_returns_400(self, client):
        body = {k: v for k, v in _OPTION_PARAMS.items() if k != "volatility"}
        resp = client.post("/api/greeks", json=body)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/model_comparison
# ---------------------------------------------------------------------------


class TestModelComparison:

    def test_happy_path(self, client):
        resp = client.post(
            "/api/model_comparison", json={**_OPTION_PARAMS, "steps": 10}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "comparison" in data

    def test_missing_required_field_returns_400(self, client):
        resp = client.post("/api/model_comparison", json={})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/convergence_analysis
# ---------------------------------------------------------------------------


class TestConvergenceAnalysis:

    def test_happy_path(self, client):
        resp = client.post(
            "/api/convergence_analysis",
            json={
                **_OPTION_PARAMS,
                "min_steps": 10,
                "max_steps": 20,
                "step_increment": 10,
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "convergence_data" in data

    def test_missing_spot_returns_400(self, client):
        body = {k: v for k, v in _OPTION_PARAMS.items() if k != "spot"}
        resp = client.post("/api/convergence_analysis", json=body)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/volatility_surface
# ---------------------------------------------------------------------------


class TestVolatilitySurface:

    def test_happy_path(self, client):
        mock_surface = {
            "strikes": [100, 105],
            "maturities": [0.25],
            "iv_grid": [[0.2, 0.21]],
        }
        with patch(
            "src.derivatives.volatility_surface.VolatilitySurfaceBuilder"
        ) as MockVSB:
            MockVSB.return_value.build_surface.return_value = mock_surface
            resp = client.post(
                "/api/volatility_surface",
                json={"ticker": "AAPL", "option_type": "call"},
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "surface" in data

    def test_missing_ticker_returns_400(self, client):
        resp = client.post("/api/volatility_surface", json={"option_type": "call"})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/atm_term_structure
# ---------------------------------------------------------------------------


class TestAtmTermStructure:

    def test_happy_path(self, client):
        mock_ts = [{"maturity": 0.25, "atm_iv": 0.2}]
        with patch(
            "src.derivatives.volatility_surface.VolatilitySurfaceBuilder"
        ) as MockVSB:
            MockVSB.return_value.get_atm_volatility_term_structure.return_value = (
                mock_ts
            )
            resp = client.post(
                "/api/atm_term_structure",
                json={"ticker": "AAPL", "option_type": "call"},
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "term_structure" in data

    def test_missing_ticker_returns_400(self, client):
        resp = client.post("/api/atm_term_structure", json={})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/heston_price
# ---------------------------------------------------------------------------


class TestHestonPrice:

    def test_happy_path(self, client):
        resp = client.post("/api/heston_price", json=_HESTON_PARAMS)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "heston" in data
        assert "price" in data["heston"]

    def test_missing_v0_returns_400(self, client):
        body = {k: v for k, v in _HESTON_PARAMS.items() if k != "v0"}
        resp = client.post("/api/heston_price", json=body)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/heston_iv_surface
# ---------------------------------------------------------------------------


class TestHestonIvSurface:

    def test_happy_path(self, client):
        resp = client.post(
            "/api/heston_iv_surface",
            json={
                "S": 100,
                "r": 0.05,
                "v0": 0.04,
                "kappa": 2.0,
                "theta": 0.04,
                "sigma_v": 0.3,
                "rho": -0.7,
                "K_min": 95,
                "K_max": 105,
                "K_steps": 3,
                "T_min": 0.25,
                "T_max": 0.5,
                "T_steps": 2,
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "iv_grid" in data
        assert "strikes" in data
        assert "maturities" in data

    def test_empty_body_uses_defaults(self, client):
        resp = client.post(
            "/api/heston_iv_surface",
            json={
                "K_min": 98,
                "K_max": 102,
                "K_steps": 2,
                "T_min": 0.25,
                "T_max": 0.5,
                "T_steps": 2,
            },
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/merton_price
# ---------------------------------------------------------------------------


class TestMertonPrice:

    def test_happy_path(self, client):
        resp = client.post("/api/merton_price", json=_MERTON_PARAMS)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "result" in data

    def test_missing_lambda_returns_400(self, client):
        body = {k: v for k, v in _MERTON_PARAMS.items() if k != "lambda"}
        resp = client.post("/api/merton_price", json=body)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/regime_detection
# ---------------------------------------------------------------------------


class TestRegimeDetection:

    def _mock_yf_ticker(self):
        hist = _make_price_history(200)
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = hist
        return mock_ticker

    def test_happy_path(self, client):
        mock_result = {
            "signal": "RISK_ON",
            "transition_matrix": [[0.9, 0.1], [0.2, 0.8]],
            "parameters": {},
            "current_probabilities": {"stressed": 0.1, "calm": 0.9},
            "filtered_probs_full": np.zeros((199, 2)).tolist(),
            "label_confidence": "HIGH",
        }
        with patch("yfinance.Ticker", return_value=self._mock_yf_ticker()), patch(
            "src.analytics.regime_detection.RegimeDetector"
        ) as MockRD:
            MockRD.return_value.fit.return_value = mock_result
            resp = client.post(
                "/api/regime_detection",
                json={
                    "ticker": "SPY",
                    "start_date": "2020-01-01",
                    "end_date": "2020-12-31",
                },
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_no_data_ticker_returns_400(self, client):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        with patch("yfinance.Ticker", return_value=mock_ticker):
            resp = client.post(
                "/api/regime_detection", json={"ticker": "INVALID_XYZ_123"}
            )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/calibrate_heston
# ---------------------------------------------------------------------------


class TestCalibrateHeston:

    def test_happy_path(self, client):
        mock_result = {"calibrated_params": {"kappa": 2.0}, "rmse": 0.05}
        with patch("src.derivatives.model_calibration.HestonCalibrator") as MockHC:
            MockHC.return_value.calibrate.return_value = mock_result
            resp = client.post(
                "/api/calibrate_heston", json={"ticker": "AAPL", "risk_free_rate": 0.05}
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "calibration" in data

    def test_calibrator_error_returns_500(self, client):
        with patch("src.derivatives.model_calibration.HestonCalibrator") as MockHC:
            MockHC.return_value.calibrate.side_effect = RuntimeError("No market data")
            resp = client.post("/api/calibrate_heston", json={"ticker": "FAKE"})
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/calibrate_heston_stream
# ---------------------------------------------------------------------------


class TestCalibrateHestonStream:

    def test_returns_event_stream_content_type(self, client):
        def mock_stream(*args, **kwargs):
            yield 'data: {"iteration": 1, "error": 0.05}\n\n'
            yield 'data: {"done": true}\n\n'

        with patch("src.derivatives.model_calibration.HestonCalibrator") as MockHC:
            MockHC.return_value.calibrate_stream.side_effect = mock_stream
            resp = client.get("/api/calibrate_heston_stream?ticker=AAPL")
        assert "text/event-stream" in resp.content_type

    def test_stream_error_still_returns_event_stream(self, client):
        with patch("src.derivatives.model_calibration.HestonCalibrator") as MockHC:
            MockHC.return_value.calibrate_stream.side_effect = RuntimeError("fail")
            resp = client.get("/api/calibrate_heston_stream?ticker=FAKE")
        assert "text/event-stream" in resp.content_type


# ---------------------------------------------------------------------------
# POST /api/calibrate_merton
# ---------------------------------------------------------------------------


class TestCalibrateMerton:

    def test_happy_path(self, client):
        mock_result = {"calibrated_params": {"lam": 2.0}, "rmse": 0.03}
        with patch("src.derivatives.model_calibration.MertonCalibrator") as MockMC:
            MockMC.return_value.calibrate.return_value = mock_result
            resp = client.post(
                "/api/calibrate_merton", json={"ticker": "AAPL", "risk_free_rate": 0.05}
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_calibrator_error_returns_500(self, client):
        with patch("src.derivatives.model_calibration.MertonCalibrator") as MockMC:
            MockMC.return_value.calibrate.side_effect = RuntimeError("No data")
            resp = client.post("/api/calibrate_merton", json={"ticker": "FAKE"})
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/credit_risk
# ---------------------------------------------------------------------------


class TestCreditRisk:

    def test_happy_path(self, client):
        resp = client.post(
            "/api/credit_risk",
            json={
                "rating": "BBB",
                "horizon": 3,
                "recovery_rate": 0.40,
                "face_value": 1000.0,
                "coupon_rate": 0.05,
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "result" in data

    def test_invalid_horizon_type_returns_500(self, client):
        resp = client.post(
            "/api/credit_risk",
            json={
                "rating": "BBB",
                "horizon": "not_a_number",
            },
        )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/rl_investment_mdp
# ---------------------------------------------------------------------------


class TestRlInvestmentMdp:

    def test_happy_path(self, client):
        resp = client.post("/api/rl_investment_mdp", json={"gamma": 0.95})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "optimal_policy" in data or "error" not in data

    def test_bad_gamma_returns_500(self, client):
        resp = client.post("/api/rl_investment_mdp", json={"gamma": "bad"})
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/rl_gridworld
# ---------------------------------------------------------------------------


class TestRlGridworld:

    def test_happy_path(self, client):
        resp = client.post("/api/rl_gridworld", json={"gamma": 0.95, "use_wind": False})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "policy" in data or "optimal_policy" in data or "error" not in data

    def test_bad_gamma_returns_500(self, client):
        resp = client.post("/api/rl_gridworld", json={"gamma": "invalid"})
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/rl_portfolio_rotation_pi
# ---------------------------------------------------------------------------


class TestRlPortfolioRotationPi:

    def test_happy_path(self, client):
        mock_result = {"policy": [0, 1, 2], "returns": {"test": 0.10}}
        with patch(
            "src.analytics.rl_models.portfolio_rotation_policy_iteration",
            return_value=mock_result,
        ):
            resp = client.post(
                "/api/rl_portfolio_rotation_pi",
                json={
                    "train_end": "2016-12-31",
                    "test_start": "2017-01-01",
                    "gamma": 0.99,
                    "cost_bps": 10,
                },
            )
        assert resp.status_code == 200

    def test_bad_gamma_returns_500(self, client):
        resp = client.post("/api/rl_portfolio_rotation_pi", json={"gamma": "bad"})
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/stoch_portfolio_mdp
# ---------------------------------------------------------------------------


class TestStochPortfolioMdp:

    def test_happy_path(self, client):
        mock_result = {"policy": [0, 1], "test_sharpe": 1.2}
        with patch(
            "src.analytics.rl_models.portfolio_mdp_user_stocks",
            return_value=mock_result,
        ):
            resp = client.post(
                "/api/stoch_portfolio_mdp",
                json={
                    "equity_ticker": "SPY",
                    "bond_ticker": "IEF",
                    "start_date": "2010-01-01",
                    "train_end": "2020-12-31",
                    "test_start": "2021-01-01",
                    "gamma": 0.99,
                    "cost_bps": 10,
                },
            )
        assert resp.status_code == 200

    def test_bad_gamma_returns_500(self, client):
        resp = client.post("/api/stoch_portfolio_mdp", json={"gamma": "bad"})
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/rl_portfolio_rotation_ql
# ---------------------------------------------------------------------------


class TestRlPortfolioRotationQl:

    def test_happy_path(self, client):
        mock_result = {"q_table": [[0, 1], [1, 0]], "test_returns": 0.08}
        with patch(
            "src.analytics.rl_models.portfolio_rotation_qlearning",
            return_value=mock_result,
        ):
            resp = client.post(
                "/api/rl_portfolio_rotation_ql",
                json={
                    "alpha": 0.1,
                    "epochs": 5,
                    "gamma": 0.99,
                    "cost_bps": 10,
                },
            )
        assert resp.status_code == 200

    def test_bad_alpha_returns_500(self, client):
        resp = client.post("/api/rl_portfolio_rotation_ql", json={"alpha": "bad"})
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/footprint (Phase 24)
# ---------------------------------------------------------------------------


def _make_mini_15m_df(n=10):
    idx = pd.date_range("2024-01-02 09:30", periods=n, freq="15min")
    return pd.DataFrame(
        {
            "Open": [150.0] * n,
            "High": [152.0] * n,
            "Low": [149.0] * n,
            "Close": [151.0] * n,
            "Volume": [100000] * n,
        },
        index=idx,
    )


class TestFootprintRoute:

    @patch("src.analytics.trading_indicators.compute_footprint")
    @patch("src.analytics.trading_indicators.fetch_intraday")
    def test_footprint_route_200(self, mock_fetch, mock_compute, client):
        """GET /api/footprint returns 200 with required schema keys."""
        mock_fetch.return_value = _make_mini_15m_df()
        mock_compute.return_value = {
            "traces": [{"type": "heatmap"}],
            "layout": {},
            "signal": "bullish",
            "cum_delta": 500000.0,
            "total_volume": 10000000.0,
        }
        resp = client.get("/api/footprint?ticker=AAPL&days=60")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data.get("ticker") == "AAPL"
        assert "signal" in data
        assert "cum_delta" in data
        assert "traces" in data

    def test_footprint_route_missing_ticker(self, client):
        """GET /api/footprint with no ticker returns JSON error (not HTTP 500)."""
        resp = client.get("/api/footprint")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "error" in data

    @patch(
        "src.analytics.trading_indicators.fetch_intraday",
        side_effect=ValueError("No 15m intraday data returned for FAKE"),
    )
    def test_footprint_route_invalid_ticker(self, mock_fetch, client):
        """GET /api/footprint for invalid ticker returns 500 with error key."""
        resp = client.get("/api/footprint?ticker=FAKE")
        assert resp.status_code == 500
        data = json.loads(resp.data)
        assert "error" in data


# ---------------------------------------------------------------------------
# Phase 25 security tests (SEC-02, SEC-03, SEC-04)
# ---------------------------------------------------------------------------


class TestEmailAllowlist:
    """SEC-02: /api/send-email must reject addresses not in the allowlist."""

    def test_email_not_in_allowlist_returns_403(self, client):
        resp = client.post(
            "/api/send-email",
            json={
                "email": "attacker@evil.com",
                "tickers": ["AAPL"],
                "data": {},
                "cnn_data": {},
            },
        )
        assert (
            resp.status_code == 403
        ), "POST /api/send-email with non-allowlisted email must return 403 (SEC-02)"


class TestRateLimiting:
    """SEC-03: scrape route must be rate-limited."""

    def test_scrape_rate_limit(self, client):
        import webapp

        webapp.limiter.reset()
        statuses = []
        for _ in range(12):
            r = client.post(
                "/api/scrape", json={"tickers": ["AAPL"], "sources": ["yahoo"]}
            )
            statuses.append(r.status_code)
        assert (
            429 in statuses
        ), "POST /api/scrape must return 429 after rate limit exceeded (SEC-03)"


class TestNoClientApiKeys:
    """SEC-04: /api/scrape must ignore API keys sent in the request body."""

    def test_client_api_key_ignored(self, client):
        import webapp

        webapp.limiter.reset()
        mock_cnn = MagicMock()
        mock_cnn.scrape_data.return_value = {}
        with patch("webapp.CNNFearGreedScraper", return_value=mock_cnn), patch(
            "webapp.run_scrapers_for_ticker", return_value={}
        ) as mock_run:
            resp = client.post(
                "/api/scrape",
                json={
                    "tickers": ["AAPL"],
                    "alpha_key": "FAKE_KEY_FROM_CLIENT",
                },
            )
        assert resp.status_code in (
            200,
            400,
        ), "Route must not crash; client-supplied API key must be ignored (SEC-04)"
        if mock_run.called:
            call_args = mock_run.call_args[0]
            assert "FAKE_KEY_FROM_CLIENT" not in str(
                call_args
            ), "run_scrapers_for_ticker must not receive client-supplied alpha_key"


# ---------------------------------------------------------------------------
# Standalone functions matching plan 25-02 pytest node IDs
# ---------------------------------------------------------------------------


def test_email_allowlist(client):
    """SEC-02: unlisted recipient returns 403."""
    resp = client.post(
        "/api/send-email",
        json={
            "email": "attacker@evil.com",
            "tickers": ["AAPL"],
            "data": {},
            "cnn_data": {},
        },
    )
    assert resp.status_code == 403


def test_rate_limiting(client):
    """SEC-03: /api/scrape returns 429 after exceeding 10/min limit."""
    import webapp

    webapp.limiter.reset()
    statuses = []
    for _ in range(12):
        r = client.post("/api/scrape", json={"tickers": ["AAPL"], "sources": ["yahoo"]})
        statuses.append(r.status_code)
    assert 429 in statuses


def test_no_client_api_keys(client):
    """SEC-04: alpha_key in request body is ignored; route does not crash."""
    import webapp

    webapp.limiter.reset()
    mock_cnn = MagicMock()
    mock_cnn.scrape_data.return_value = {}
    with patch("webapp.CNNFearGreedScraper", return_value=mock_cnn), patch(
        "webapp.run_scrapers_for_ticker", return_value={}
    ) as mock_run:
        resp = client.post(
            "/api/scrape",
            json={
                "tickers": ["AAPL"],
                "alpha_key": "FAKE_KEY_FROM_CLIENT",
            },
        )
    assert resp.status_code in (200, 400)
    if mock_run.called:
        call_args = mock_run.call_args[0]
        assert "FAKE_KEY_FROM_CLIENT" not in str(call_args)


# ---------------------------------------------------------------------------
# Phase 26 ML Signals route stubs
# ---------------------------------------------------------------------------


def test_ml_signals_direction_route(client):
    """GET /api/ml_signals?ticker=AAPL&feature=direction → Bullish or Bearish signal."""
    mock_result = {
        "signal": "Bullish",
        "confidence": 0.67,
        "traces": [],
        "layout": {},
    }
    with patch(
        "webapp.compute_ml_direction_signal", return_value=mock_result, create=True
    ):
        resp = client.get("/api/ml_signals?ticker=AAPL&feature=direction")

    if resp.status_code == 404:
        pytest.skip("route not yet registered")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ticker"] == "AAPL"
    assert data["signal"] in ("Bullish", "Bearish")


def test_ml_signals_missing_ticker(client):
    """GET /api/ml_signals?feature=direction with no ticker → error in response."""
    resp = client.get("/api/ml_signals?feature=direction")

    if resp.status_code == 404:
        pytest.skip("route not yet registered")

    assert resp.status_code == 200
    data = resp.get_json()
    assert "error" in data


# ---------------------------------------------------------------------------
# Phase 28 Price History route
# ---------------------------------------------------------------------------


def _stub_ohlcv_ph():
    """Minimal 90-row OHLCV DataFrame for price_history route tests."""
    import pandas as pd

    idx = pd.date_range("2024-01-01", periods=90, freq="B")
    return pd.DataFrame(
        {
            "Open": 1.0,
            "High": 2.0,
            "Low": 0.5,
            "Close": 1.5,
            "Volume": 1000.0,
        },
        index=idx,
    )


class TestPriceHistory:
    def test_price_history_200_shape(self, client):
        """GET /api/price_history?ticker=AAPL&period=3mo → 200 with traces+layout keys."""
        with patch(
            "src.analytics.trading_indicators.fetch_ohlcv",
            return_value=_stub_ohlcv_ph(),
        ):
            resp = client.get("/api/price_history?ticker=AAPL&period=3mo")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "traces" in data
        assert "layout" in data

    def test_price_history_missing_ticker(self, client):
        """GET /api/price_history (no ticker) → response contains 'error' key."""
        resp = client.get("/api/price_history")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data


class TestFeynmanRoutes:
    def test_feynman_research_unavailable(self, client):
        """POST /api/feynman_research when Feynman not installed → {available: false}."""
        from unittest.mock import patch

        with patch("src.analytics.feynman_runner.FEYNMAN_AVAILABLE", False):
            resp = client.post(
                "/api/feynman_research",
                json={"section": "direction", "ticker": "AAPL"},
                content_type="application/json",
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["available"] is False

    def test_feynman_research_returns_job_id(self, client):
        """POST /api/feynman_research when available → returns {job_id: ...} immediately."""
        from unittest.mock import patch

        with patch("src.analytics.feynman_runner.FEYNMAN_AVAILABLE", True), patch(
            "src.analytics.feynman_runner.run_feynman_async",
            return_value="test-uuid-123",
        ):
            resp = client.post(
                "/api/feynman_research",
                json={"section": "direction", "ticker": "AAPL"},
                content_type="application/json",
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["job_id"] == "test-uuid-123"

    def test_feynman_status_unknown_job(self, client):
        """GET /api/feynman_status/<unknown> → {status: error, error: unknown job_id}."""
        resp = client.get("/api/feynman_status/nonexistent-job-id")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "error"
        assert "unknown job_id" in data.get("error", "")

    def test_feynman_research_passes_signals_to_runner(self, client):
        """POST /api/feynman_research with signals → runner receives signals kwarg."""
        from unittest.mock import patch

        with patch("src.analytics.feynman_runner.FEYNMAN_AVAILABLE", True), patch(
            "src.analytics.feynman_runner.run_feynman_async",
            return_value="job-sig-123",
        ) as mock_run:
            signals = {"signal": "Bullish", "confidence": 0.73}
            resp = client.post(
                "/api/feynman_research",
                json={"section": "direction", "ticker": "AAPL", "signals": signals},
            )
            assert resp.status_code == 200
            assert resp.get_json()["job_id"] == "job-sig-123"
            mock_run.assert_called_once_with("direction", "AAPL", signals)

    def test_feynman_synthesis_returns_job_id(self, client):
        """POST /api/feynman_synthesis → {job_id: ...}."""
        from unittest.mock import patch

        with patch("src.analytics.feynman_runner.FEYNMAN_AVAILABLE", True), patch(
            "src.analytics.feynman_runner.run_synthesis_async",
            return_value="synth-uuid-456",
        ):
            resp = client.post(
                "/api/feynman_synthesis",
                json={
                    "ticker": "AAPL",
                    "signals": {"direction": {"signal": "Bullish", "confidence": 0.73}},
                },
            )
            assert resp.status_code == 200
            assert resp.get_json()["job_id"] == "synth-uuid-456"

    def test_feynman_synthesis_unavailable(self, client):
        """POST /api/feynman_synthesis when unavailable → {available: false}."""
        from unittest.mock import patch

        with patch("src.analytics.feynman_runner.FEYNMAN_AVAILABLE", False):
            resp = client.post(
                "/api/feynman_synthesis", json={"ticker": "AAPL", "signals": {}}
            )
            assert resp.status_code == 200
            assert resp.get_json()["available"] is False

    def test_feynman_pca_interpret_returns_job_id(self, client):
        """POST /api/feynman_pca_interpret → {job_id: ...}."""
        from unittest.mock import patch

        with patch("src.analytics.feynman_runner.FEYNMAN_AVAILABLE", True), patch(
            "src.analytics.feynman_runner.run_pca_interpret_async",
            return_value="pca-uuid-789",
        ):
            resp = client.post(
                "/api/feynman_pca_interpret",
                json={"pca_data": {"port_daily_std_pct": 1.8, "var_99_1d_pct": 4.2}},
            )
            assert resp.status_code == 200
            assert resp.get_json()["job_id"] == "pca-uuid-789"

    def test_feynman_pca_interpret_unavailable(self, client):
        """POST /api/feynman_pca_interpret when unavailable → {available: false}."""
        from unittest.mock import patch

        with patch("src.analytics.feynman_runner.FEYNMAN_AVAILABLE", False):
            resp = client.post("/api/feynman_pca_interpret", json={"pca_data": {}})
            assert resp.status_code == 200
            assert resp.get_json()["available"] is False


# ---------------------------------------------------------------------------
# Phase 31 — POST /api/export-sheets integration tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestExportSheets:
    """Integration tests for POST /api/export-sheets (Phase 31)."""

    _EXPORT_PAYLOAD = {
        "tickers": ["AAPL", "MSFT"],
        "data": {
            "AAPL": {"Price": "175.00", "RSI": "55.2"},
            "MSFT": {"Price": "420.00", "RSI": None},
        },
    }

    def test_export_sheets_success(self, client):
        """Valid payload → 200 + {success: true, rows_added: 2}."""
        from unittest.mock import patch

        with patch(
            "src.utils.sheets_utils.export_tickers_to_sheets", return_value=2
        ), patch("os.path.exists", return_value=True), patch.dict(
            "os.environ",
            {
                "GOOGLE_SHEETS_CREDENTIALS_PATH": "/fake/creds.json",
                "GOOGLE_SHEETS_SPREADSHEET_ID": "fake-id",
            },
        ):
            resp = client.post("/api/export-sheets", json=self._EXPORT_PAYLOAD)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["rows_added"] == 2

    def test_export_sheets_no_body(self, client):
        """No JSON body → 400."""
        resp = client.post(
            "/api/export-sheets", content_type="application/json", data=None
        )
        assert resp.status_code == 400

    def test_export_sheets_empty_tickers(self, client):
        """Empty tickers list → 400."""
        resp = client.post("/api/export-sheets", json={"tickers": [], "data": {}})
        assert resp.status_code == 400

    def test_export_sheets_no_creds(self, client):
        """Missing credentials → 500 + {success: false, error includes message}."""
        from unittest.mock import patch

        with patch(
            "src.utils.sheets_utils.export_tickers_to_sheets",
            side_effect=FileNotFoundError("Credentials file not found"),
        ):
            resp = client.post("/api/export-sheets", json=self._EXPORT_PAYLOAD)
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["success"] is False

    def test_export_sheets_not_found(self, client):
        """Spreadsheet not found → 500 + {success: false}."""
        from unittest.mock import patch

        try:
            import gspread

            exc = gspread.exceptions.SpreadsheetNotFound()
        except ImportError:
            pytest.skip("gspread not installed")
        with patch("src.utils.sheets_utils.export_tickers_to_sheets", side_effect=exc):
            resp = client.post("/api/export-sheets", json=self._EXPORT_PAYLOAD)
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["success"] is False

    def test_export_sheets_api_error(self, client):
        """Unexpected error → 4xx or 5xx + {success: false}."""
        from unittest.mock import patch

        with patch(
            "src.utils.sheets_utils.export_tickers_to_sheets",
            side_effect=ValueError("Sheets API error"),
        ):
            resp = client.post("/api/export-sheets", json=self._EXPORT_PAYLOAD)
        assert resp.status_code in (400, 500)
        data = resp.get_json()
        assert data["success"] is False
