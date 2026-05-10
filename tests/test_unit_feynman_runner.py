import os
import time
import importlib
from unittest.mock import MagicMock, patch
import pytest

pytestmark = pytest.mark.unit


def _make_openai_response(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _mock_client(content: str):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_openai_response(content)
    return mock_client


def _wait_job(fr, job_id, retries=20, delay=0.05):
    status = None
    for _ in range(retries):
        status = fr.get_job_status(job_id)
        if status["status"] != "pending":
            break
        time.sleep(delay)
    return status


# ---------------------------------------------------------------------------
# run_feynman_async — happy path
# ---------------------------------------------------------------------------


def test_run_feynman_async_happy_path():
    import src.analytics.feynman_runner as fr

    with patch(
        "src.analytics.feynman_runner.openai.OpenAI",
        return_value=_mock_client("## RF Literature\n\nSome content."),
    ):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = _wait_job(fr, job_id)
    assert status["status"] == "done"
    assert "RF Literature" in status["result"]


def test_run_feynman_async_with_signals_enriches_query():
    import src.analytics.feynman_runner as fr

    captured = {}

    def fake_create(**kwargs):
        captured["messages"] = kwargs["messages"]
        return _make_openai_response("## Result\n\nContent.")

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = fake_create

    signals = {"signal": "Bullish", "confidence": 0.73, "top_feature": "Ret120"}
    with patch("src.analytics.feynman_runner.openai.OpenAI", return_value=mock_client):
        job_id = fr.run_feynman_async("direction", "AAPL", signals)
        status = _wait_job(fr, job_id)

    assert status["status"] == "done"
    user_msg = captured["messages"][-1]["content"]
    assert "AAPL" in user_msg
    assert "73%" in user_msg or "Bullish" in user_msg


# ---------------------------------------------------------------------------
# run_synthesis_async
# ---------------------------------------------------------------------------


def test_run_synthesis_async_happy_path():
    import src.analytics.feynman_runner as fr

    with patch(
        "src.analytics.feynman_runner.openai.OpenAI",
        return_value=_mock_client("## Thesis\n\n### Bull Case\nStrong momentum."),
    ):
        signals = {
            "direction": {"signal": "Bullish", "confidence": 0.73},
            "regime": {"hmm": "Bull", "kmeans": "Bull", "agree": True},
            "credit": {"p_distress": 0.12},
            "lstm": {"signal": "Bullish", "confidence": 0.68},
        }
        job_id = fr.run_synthesis_async("AAPL", signals)
        status = _wait_job(fr, job_id)
    assert status["status"] == "done"
    assert "Thesis" in status["result"]


def test_run_synthesis_async_includes_all_signals_in_query():
    import src.analytics.feynman_runner as fr

    captured = {}

    def fake_create(**kwargs):
        captured["messages"] = kwargs["messages"]
        return _make_openai_response("## Thesis\nContent.")

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = fake_create

    signals = {
        "direction": {"signal": "Bullish", "confidence": 0.73},
        "regime": {"hmm": "Bear", "kmeans": "Bull", "agree": False},
        "credit": {"p_distress": 0.45},
        "lstm": {"signal": "Bearish", "confidence": 0.60},
    }
    with patch("src.analytics.feynman_runner.openai.OpenAI", return_value=mock_client):
        job_id = fr.run_synthesis_async("MSFT", signals)
        _wait_job(fr, job_id)

    user_msg = captured["messages"][-1]["content"]
    assert "MSFT" in user_msg
    assert "Bullish" in user_msg
    assert "Bear" in user_msg
    assert "45%" in user_msg


# ---------------------------------------------------------------------------
# run_pca_interpret_async
# ---------------------------------------------------------------------------


def test_run_pca_interpret_async_happy_path():
    import src.analytics.feynman_runner as fr

    with patch(
        "src.analytics.feynman_runner.openai.OpenAI",
        return_value=_mock_client(
            "## Portfolio Risk Interpretation\n\n### Concentration\nHigh."
        ),
    ):
        pca_data = {
            "port_daily_std_pct": 1.8,
            "var_99_1d_pct": 4.2,
            "var_95_1d_pct": 2.9,
            "hist_var_99_1d_pct": 3.8,
            "pc_contributions": [
                {
                    "name": "Market Factor",
                    "variance_share_pct": 78.0,
                    "var_99_contribution_pct": 0.032,
                }
            ],
        }
        job_id = fr.run_pca_interpret_async(pca_data)
        status = _wait_job(fr, job_id)
    assert status["status"] == "done"
    assert "Portfolio Risk" in status["result"]


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


def test_run_feynman_async_api_error():
    import src.analytics.feynman_runner as fr

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("connection error")
    with patch("src.analytics.feynman_runner.openai.OpenAI", return_value=mock_client):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = _wait_job(fr, job_id)
    assert status["status"] == "error"
    assert "connection error" in status["error"]


def test_empty_output_guard():
    import src.analytics.feynman_runner as fr

    with patch(
        "src.analytics.feynman_runner.openai.OpenAI", return_value=_mock_client("")
    ):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = _wait_job(fr, job_id)
    assert status["status"] == "error"
    assert "empty" in status["error"].lower()


def test_auth_error_returns_helpful_message():
    import openai as _openai
    import src.analytics.feynman_runner as fr

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = _openai.AuthenticationError(
        "invalid key", response=MagicMock(), body={}
    )
    with patch("src.analytics.feynman_runner.openai.OpenAI", return_value=mock_client):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = _wait_job(fr, job_id)
    assert status["status"] == "error"
    assert "OPENAI_API_KEY" in status["error"]


# ---------------------------------------------------------------------------
# FEYNMAN_AVAILABLE
# ---------------------------------------------------------------------------


def test_feynman_available_reflects_env_var():
    import src.analytics.feynman_runner as fr

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("OPENAI_API_KEY", None)
        importlib.reload(fr)
        assert fr.FEYNMAN_AVAILABLE is False

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
        importlib.reload(fr)
        assert fr.FEYNMAN_AVAILABLE is True

    importlib.reload(fr)  # restore
