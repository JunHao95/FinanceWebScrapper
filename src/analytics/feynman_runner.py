import re
import shutil
import subprocess
import threading
import uuid

FEYNMAN_AVAILABLE = shutil.which("feynman") is not None

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
_jobs: dict = {}

QUERIES = {
    "direction": (
        "Summarise academic literature on random forest classifiers for equity return"
        " direction prediction. Include known limitations and data-snooping risks."
        " Cite 3-5 papers."
    ),
    "pca": (
        "Summarise academic literature on PCA factor decomposition for equity portfolio"
        " risk attribution. Include limitations of linear factor models."
    ),
    "regime": (
        "Summarise literature on K-Means and HMM market regime detection in equities."
        " Compare the two approaches."
    ),
    "credit": (
        "Summarise literature on ML-based corporate credit risk scoring. Include"
        " limitations of training on synthetic distress labels."
    ),
    "lstm": (
        "Summarise academic literature on LSTM models for stock return direction"
        " prediction. Include known pitfalls and leakage risks."
    ),
}


_PREAMBLE_RE = re.compile(r"^.*?(?=^#{1,3} )", re.MULTILINE | re.DOTALL)


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE.sub("", text)


def _strip_preamble(text: str) -> str:
    """Remove CLI preamble lines before the first markdown heading."""
    m = _PREAMBLE_RE.match(text)
    if m and m.end() > 0:
        return text[m.end() :]
    return text


def run_feynman_async(section: str, ticker: str) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "result": "", "error": ""}
    query = QUERIES.get(section, "Summarise ML methods used in quantitative finance.")
    threading.Thread(target=_run, args=(job_id, query), daemon=True).start()
    return job_id


def _run(job_id: str, query: str) -> None:
    try:
        proc = subprocess.run(
            ["feynman", "--prompt", query],
            capture_output=True,
            text=True,
            timeout=120,
        )
        stdout = _strip_preamble(_strip_ansi(proc.stdout))
        stderr = _strip_ansi(proc.stderr)
        if not stdout.strip():
            _jobs[job_id] = {
                "status": "error",
                "result": "",
                "error": (
                    "Feynman returned empty output — check `feynman status`"
                    " and API key configuration."
                ),
            }
        else:
            _jobs[job_id] = {"status": "done", "result": stdout, "error": stderr}
    except subprocess.TimeoutExpired:
        _jobs[job_id] = {"status": "error", "result": "", "error": "timeout"}
    except Exception as exc:  # noqa: BLE001
        _jobs[job_id] = {"status": "error", "result": "", "error": str(exc)}


def get_job_status(job_id: str) -> dict:
    return _jobs.get(job_id, {"status": "error", "error": "unknown job_id"})
