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


def test_run_feynman_async_happy_path():
    import src.analytics.feynman_runner as fr

    mock_resp = _make_openai_response(
        "## Random Forests in Finance\n\n### Core Idea\nSome content."
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_resp

    with patch("src.analytics.feynman_runner.openai.OpenAI", return_value=mock_client):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = None
        for _ in range(20):
            status = fr.get_job_status(job_id)
            if status["status"] != "pending":
                break
            time.sleep(0.05)
    assert status["status"] == "done"
    assert "Random Forests" in status["result"]


def test_run_feynman_async_timeout():
    import src.analytics.feynman_runner as fr

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("timeout")

    with patch("src.analytics.feynman_runner.openai.OpenAI", return_value=mock_client):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = None
        for _ in range(20):
            status = fr.get_job_status(job_id)
            if status["status"] != "pending":
                break
            time.sleep(0.05)
    assert status["status"] == "error"
    assert "timeout" in status["error"].lower()


def test_empty_output_guard():
    import src.analytics.feynman_runner as fr

    mock_resp = _make_openai_response("")
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_resp

    with patch("src.analytics.feynman_runner.openai.OpenAI", return_value=mock_client):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = None
        for _ in range(20):
            status = fr.get_job_status(job_id)
            if status["status"] != "pending":
                break
            time.sleep(0.05)
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
        status = None
        for _ in range(20):
            status = fr.get_job_status(job_id)
            if status["status"] != "pending":
                break
            time.sleep(0.05)
    assert status["status"] == "error"
    assert "OPENAI_API_KEY" in status["error"]


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
