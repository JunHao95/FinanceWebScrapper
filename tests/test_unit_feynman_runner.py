import time
import importlib
from unittest.mock import MagicMock, patch
import pytest

pytestmark = pytest.mark.unit


def test_run_feynman_async_happy_path():
    import src.analytics.feynman_runner as fr

    mock_proc = MagicMock()
    mock_proc.stdout = "# Random Forests in Finance\n\nSome content."
    mock_proc.stderr = ""
    with patch("src.analytics.feynman_runner.subprocess.run", return_value=mock_proc):
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
    import subprocess
    import src.analytics.feynman_runner as fr

    with patch(
        "src.analytics.feynman_runner.subprocess.run",
        side_effect=subprocess.TimeoutExpired(["feynman"], 120),
    ):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = None
        for _ in range(20):
            status = fr.get_job_status(job_id)
            if status["status"] != "pending":
                break
            time.sleep(0.05)
    assert status["status"] == "error"
    assert status["error"] == "timeout"


def test_empty_output_guard():
    import src.analytics.feynman_runner as fr

    mock_proc = MagicMock()
    mock_proc.stdout = ""
    mock_proc.stderr = "auth error"
    with patch("src.analytics.feynman_runner.subprocess.run", return_value=mock_proc):
        job_id = fr.run_feynman_async("direction", "AAPL")
        status = None
        for _ in range(20):
            status = fr.get_job_status(job_id)
            if status["status"] != "pending":
                break
            time.sleep(0.05)
    assert status["status"] == "error"
    assert "empty output" in status["error"].lower()


def test_ansi_stripping():
    import src.analytics.feynman_runner as fr

    assert fr._strip_ansi("\x1b[38;2;127;187;179mHello\x1b[0m") == "Hello"
    assert fr._strip_ansi("\x1b[1;32mBold Green\x1b[0m") == "Bold Green"
    assert fr._strip_ansi("No ANSI") == "No ANSI"


def test_feynman_available_false():
    import src.analytics.feynman_runner as fr

    with patch("shutil.which", return_value=None):
        importlib.reload(fr)
        assert fr.FEYNMAN_AVAILABLE is False
    importlib.reload(fr)  # restore after test
