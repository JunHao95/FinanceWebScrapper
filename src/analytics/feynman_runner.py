import os
import threading
import uuid

import openai

FEYNMAN_AVAILABLE = bool(os.getenv("OPENAI_API_KEY"))

_jobs: dict = {}

_SYSTEM_PROMPT = (
    "You are a research assistant that summarises academic literature concisely. "
    "Format your response in markdown: use ## for the title, ### for sections, "
    "a pipe table for key papers (columns: #, Paper, Key Finding), "
    "bullet points for consensus findings, and numbered lists for limitations. "
    "Keep the total response under 600 words."
)

QUERIES = {
    "direction": (
        "Summarise academic literature on random forest classifiers for equity return"
        " direction prediction. Include known limitations and data-snooping risks."
        " Cite 3-5 papers."
    ),
    "pca": (
        "Summarise academic literature on PCA factor decomposition for equity portfolio"
        " risk attribution. Include limitations of linear factor models."
        " Cite 3-5 papers."
    ),
    "regime": (
        "Summarise literature on K-Means and HMM market regime detection in equities."
        " Compare the two approaches. Cite 3-5 papers."
    ),
    "credit": (
        "Summarise literature on ML-based corporate credit risk scoring. Include"
        " limitations of training on synthetic distress labels. Cite 3-5 papers."
    ),
    "lstm": (
        "Summarise academic literature on LSTM models for stock return direction"
        " prediction. Include known pitfalls and leakage risks. Cite 3-5 papers."
    ),
}


def run_feynman_async(section: str, ticker: str) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "result": "", "error": ""}
    query = QUERIES.get(section, "Summarise ML methods used in quantitative finance.")
    threading.Thread(target=_run, args=(job_id, query), daemon=True).start()
    return job_id


def _run(job_id: str, query: str) -> None:
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            max_tokens=1200,
            timeout=90,
        )
        result = response.choices[0].message.content or ""
        if not result.strip():
            _jobs[job_id] = {
                "status": "error",
                "result": "",
                "error": "OpenAI returned empty response.",
            }
        else:
            _jobs[job_id] = {"status": "done", "result": result, "error": ""}
    except openai.AuthenticationError:
        _jobs[job_id] = {
            "status": "error",
            "result": "",
            "error": "Invalid OPENAI_API_KEY — check environment variables.",
        }
    except Exception as exc:  # noqa: BLE001
        _jobs[job_id] = {"status": "error", "result": "", "error": str(exc)}


def get_job_status(job_id: str) -> dict:
    return _jobs.get(job_id, {"status": "error", "error": "unknown job_id"})
