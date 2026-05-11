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
# run_feynman_async — OpenAI path (simulating Render environment)
# ---------------------------------------------------------------------------


def test_run_feynman_async_happy_path():
    import src.analytics.feynman_runner as fr

    with patch("src.analytics.feynman_runner._USE_OPENAI", True), patch(
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
    with patch("src.analytics.feynman_runner._USE_OPENAI", True), patch(
        "src.analytics.feynman_runner.openai.OpenAI", return_value=mock_client
    ):
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

    with patch("src.analytics.feynman_runner._USE_OPENAI", True), patch(
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
    with patch("src.analytics.feynman_runner._USE_OPENAI", True), patch(
        "src.analytics.feynman_runner.openai.OpenAI", return_value=mock_client
    ):
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

    with patch("src.analytics.feynman_runner._USE_OPENAI", True), patch(
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
# Error paths — OpenAI mode
# ---------------------------------------------------------------------------


def test_run_feynman_async_api_error():
    import src.analytics.feynman_runner as fr

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("connection error")
    with patch("src.analytics.feynman_runner._USE_OPENAI", True), patch(
        "src.analytics.feynman_runner.openai.OpenAI", return_value=mock_client
    ):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = _wait_job(fr, job_id)
    assert status["status"] == "error"
    assert "connection error" in status["error"]


def test_empty_output_guard():
    import src.analytics.feynman_runner as fr

    with patch("src.analytics.feynman_runner._USE_OPENAI", True), patch(
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
    with patch("src.analytics.feynman_runner._USE_OPENAI", True), patch(
        "src.analytics.feynman_runner.openai.OpenAI", return_value=mock_client
    ):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = _wait_job(fr, job_id)
    assert status["status"] == "error"
    assert "OPENAI_API_KEY" in status["error"]


# ---------------------------------------------------------------------------
# Subprocess path (local mode)
# ---------------------------------------------------------------------------


def test_subprocess_happy_path():
    import src.analytics.feynman_runner as fr

    mock_proc = MagicMock()
    mock_proc.stdout = "## RF Literature\n\nSome content."
    mock_proc.stderr = ""

    with patch("src.analytics.feynman_runner._USE_OPENAI", False), patch(
        "src.analytics.feynman_runner.subprocess.run", return_value=mock_proc
    ):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = _wait_job(fr, job_id)

    assert status["status"] == "done"
    assert "RF Literature" in status["result"]


def test_subprocess_empty_output():
    import src.analytics.feynman_runner as fr

    mock_proc = MagicMock()
    mock_proc.stdout = "   "
    mock_proc.stderr = ""

    with patch("src.analytics.feynman_runner._USE_OPENAI", False), patch(
        "src.analytics.feynman_runner.subprocess.run", return_value=mock_proc
    ):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = _wait_job(fr, job_id)

    assert status["status"] == "error"
    assert "feynman" in status["error"].lower()


def test_subprocess_timeout():
    import subprocess
    import src.analytics.feynman_runner as fr

    with patch("src.analytics.feynman_runner._USE_OPENAI", False), patch(
        "src.analytics.feynman_runner.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="feynman", timeout=120),
    ):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = _wait_job(fr, job_id)

    assert status["status"] == "error"
    assert "timeout" in status["error"]


def test_subprocess_strips_ansi():
    import src.analytics.feynman_runner as fr

    mock_proc = MagicMock()
    mock_proc.stdout = "\x1b[32m## RF Literature\x1b[0m\n\nContent."
    mock_proc.stderr = ""

    with patch("src.analytics.feynman_runner._USE_OPENAI", False), patch(
        "src.analytics.feynman_runner.subprocess.run", return_value=mock_proc
    ):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = _wait_job(fr, job_id)

    assert status["status"] == "done"
    assert "\x1b" not in status["result"]


# ---------------------------------------------------------------------------
# FEYNMAN_AVAILABLE — dual-mode detection
# ---------------------------------------------------------------------------


def test_feynman_available_local_with_cli():
    import src.analytics.feynman_runner as fr

    with patch.dict(os.environ, {}, clear=True), patch(
        "shutil.which", return_value="/usr/local/bin/feynman"
    ):
        importlib.reload(fr)
        assert fr.FEYNMAN_AVAILABLE is True

    importlib.reload(fr)  # restore


def test_feynman_available_local_without_cli():
    import src.analytics.feynman_runner as fr

    with patch.dict(os.environ, {}, clear=True), patch(
        "shutil.which", return_value=None
    ):
        importlib.reload(fr)
        assert fr.FEYNMAN_AVAILABLE is False

    importlib.reload(fr)  # restore


def test_feynman_available_render_with_key():
    import src.analytics.feynman_runner as fr

    with patch.dict(
        os.environ, {"RENDER": "true", "OPENAI_API_KEY": "sk-test"}, clear=True
    ):
        importlib.reload(fr)
        assert fr.FEYNMAN_AVAILABLE is True

    importlib.reload(fr)  # restore


def test_feynman_available_render_without_key():
    import src.analytics.feynman_runner as fr

    with patch.dict(os.environ, {"RENDER": "true"}, clear=True):
        importlib.reload(fr)
        assert fr.FEYNMAN_AVAILABLE is False

    importlib.reload(fr)  # restore


# ---------------------------------------------------------------------------
# System prompt integrity — verify hard constraints present
# ---------------------------------------------------------------------------


def test_research_system_prompt_requires_citation_warning():
    import src.analytics.feynman_runner as fr

    assert "UNVERIFIED" in fr._SYSTEM_PROMPT
    assert "CONSENSUS" in fr._SYSTEM_PROMPT
    assert "CONTESTED" in fr._SYSTEM_PROMPT


def test_pca_system_prompt_forbids_correlation_claim():
    import src.analytics.feynman_runner as fr

    assert "orthogonal" in fr._PCA_SYSTEM.lower()
    assert "methodological" in fr._PCA_SYSTEM.lower()


def test_pca_system_prompt_bans_leverage_language():
    import src.analytics.feynman_runner as fr

    # Prompt must contain the ban instruction, not use the word as a claim
    assert "BANNED LANGUAGE" in fr._PCA_SYSTEM
    assert (
        "leveraged bet" in fr._PCA_SYSTEM.lower()
        or "leveraged'" in fr._PCA_SYSTEM.lower()
    )


def test_pca_system_prompt_requires_var_reconciliation_section():
    import src.analytics.feynman_runner as fr

    assert "VaR Contribution Reconciliation" in fr._PCA_SYSTEM
    assert "METHODOLOGICAL MISMATCH" in fr._PCA_SYSTEM


def test_pca_system_prompt_requires_confidence_labels():
    import src.analytics.feynman_runner as fr

    assert "[COMPUTED]" in fr._PCA_SYSTEM
    assert "[INFERRED]" in fr._PCA_SYSTEM
    assert "[SPECULATIVE]" in fr._PCA_SYSTEM


def test_synthesis_system_prompt_requires_signal_table():
    import src.analytics.feynman_runner as fr

    assert "Signal Agreement Table" in fr._SYNTHESIS_SYSTEM
    assert "[COMPUTED]" in fr._SYNTHESIS_SYSTEM
    assert "[INFERRED]" in fr._SYNTHESIS_SYSTEM
    assert "[SPECULATIVE]" in fr._SYNTHESIS_SYSTEM


def test_synthesis_system_prompt_requires_mandatory_structure():
    import src.analytics.feynman_runner as fr

    assert "MANDATORY OUTPUT STRUCTURE" in fr._SYNTHESIS_SYSTEM
    assert "Conflicts & Caveats" in fr._SYNTHESIS_SYSTEM
    assert "Net Assessment" in fr._SYNTHESIS_SYSTEM


def test_openai_uses_gpt4o_model():
    import src.analytics.feynman_runner as fr

    captured = {}

    def fake_create(**kwargs):
        captured["model"] = kwargs.get("model")
        return _make_openai_response("## Result\n\nContent.")

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = fake_create

    with patch("src.analytics.feynman_runner._USE_OPENAI", True), patch(
        "src.analytics.feynman_runner.openai.OpenAI", return_value=mock_client
    ):
        job_id = fr.run_feynman_async("direction", "AAPL")
        _wait_job(fr, job_id)

    assert captured["model"] == "gpt-4o"


def test_openai_max_tokens_increased():
    import src.analytics.feynman_runner as fr

    captured = {}

    def fake_create(**kwargs):
        captured["max_tokens"] = kwargs.get("max_tokens")
        return _make_openai_response("## Result\n\nContent.")

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = fake_create

    with patch("src.analytics.feynman_runner._USE_OPENAI", True), patch(
        "src.analytics.feynman_runner.openai.OpenAI", return_value=mock_client
    ):
        job_id = fr.run_feynman_async("direction", "AAPL")
        _wait_job(fr, job_id)

    assert captured["max_tokens"] >= 1500
