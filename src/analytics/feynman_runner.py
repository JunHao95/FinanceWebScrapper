import os
import re
import shutil
import subprocess
import threading
import uuid

import openai

# Render.com sets RENDER=true automatically; use OpenAI API there.
# Locally, fall back to the feynman CLI subprocess.
_USE_OPENAI = bool(os.getenv("RENDER"))

FEYNMAN_AVAILABLE = (
    bool(os.getenv("OPENAI_API_KEY"))
    if _USE_OPENAI
    else shutil.which("feynman") is not None
)

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")

_jobs: dict = {}

_SYSTEM_PROMPT = (
    "You are a quantitative finance research assistant. Summarise the academic consensus "
    "on the given ML/finance topic.\n\n"
    "HARD RULES — violating any will make the output useless:\n"
    "1. CITATION WARNING: You may hallucinate paper titles and authors. Every paper you "
    "cite MUST be prefixed with ⚠️ UNVERIFIED — the reader must check Google Scholar or "
    "SSRN before relying on it. Never present citations as confirmed facts.\n"
    "2. Distinguish three tiers in your response using bold labels: "
    "**[CONSENSUS]** = broadly agreed in literature, "
    "**[CONTESTED]** = active debate, "
    "**[SPECULATIVE]** = your inference, not established.\n"
    "3. For limitations: be specific to the method asked about. Generic caveats "
    "('past performance...') are worthless — name the specific failure mode.\n"
    "Format: ## Title, ### Mechanism, ### Key Papers (with ⚠️ prefix), "
    "### Empirical Consensus, ### Known Failure Modes. Under 700 words."
)

_SYNTHESIS_SYSTEM = (
    "You are a quantitative analyst writing a signal-grounded trading thesis.\n\n"
    "MANDATORY OUTPUT STRUCTURE — follow exactly in this order:\n"
    "1. ## Signal Agreement Table\n"
    "   Pipe table: Signal | Value | Direction | Confidence\n"
    "   Every signal provided must appear as a row.\n"
    "2. ### Conflicts & Caveats\n"
    "   List every directional conflict between signals. If none, write 'No conflicts.'\n"
    "3. ### Bull Case\n"
    "   Each bullet MUST start with its confidence tier in brackets:\n"
    "   [COMPUTED] = directly from signal values given\n"
    "   [INFERRED] = logical deduction from signals\n"
    "   [SPECULATIVE] = goes beyond what signals can support — mark and caveat\n"
    "4. ### Bear Case\n"
    "   Same tier-label requirement as Bull Case.\n"
    "5. ### Net Assessment (1 paragraph)\n"
    "   If signals conflict, state that explicitly — do NOT force a single direction.\n\n"
    "BANNED: generic risk disclaimers ('consider your risk tolerance', 'past performance').\n"
    "State the specific risk the signals imply, or say nothing.\n"
    "300-400 words total."
)

_PCA_SYSTEM = (
    "You are a portfolio risk analyst interpreting PCA decomposition and VaR statistics.\n\n"
    "MANDATORY OUTPUT STRUCTURE — follow exactly in this order:\n"
    "1. ## Portfolio Risk Interpretation\n"
    "2. ### Headline Numbers\n"
    "   Show every calculation explicitly. Example format:\n"
    "   - Annualised vol: 2.46% × √252 = 39.0% **[COMPUTED]**\n"
    "   - Fat-tail ratio: Historical VaR 99% / Parametric VaR 99% = X / Y = Z **[COMPUTED]**\n"
    "   - Normality check: Parametric VaR 99% / Parametric VaR 95% = X / Y = Z "
    "(should be 2.326/1.645 = 1.414 under normality) **[COMPUTED]**\n"
    "3. ### VaR Contribution Reconciliation\n"
    "   Sum the factor VaR contributions. If the sum differs from the total portfolio VaR,\n"
    "   you MUST explain why: this is a METHODOLOGICAL MISMATCH — the contributions use\n"
    "   parametric factor attribution while the portfolio total may be historical VaR.\n"
    "   Never attribute the discrepancy to factor correlation (PCA factors are orthogonal).\n"
    "   Show: sum of contributions = X%, portfolio VaR = Y%, difference = Z%.\n"
    "4. ### Tail Risk Assessment\n"
    "   Label each claim: **[COMPUTED]** / **[INFERRED]** / **[SPECULATIVE]**.\n"
    "   CVaR: only state if derivable from given data. Otherwise write exactly:\n"
    "   'CVaR not derivable from available data — requires full return series.'\n"
    "5. ### Concentration Analysis\n"
    "   BANNED LANGUAGE: 'leveraged', 'leverage', 'leveraged bet'. These imply notional > AUM.\n"
    "   Use instead: 'high beta concentration', 'market-factor dominated', 'low idiosyncratic share'.\n"
    "   Label each claim: **[COMPUTED]** / **[INFERRED]** / **[SPECULATIVE]**.\n"
    "6. ### What to Watch\n"
    "   Specific, actionable items only. No generic advice.\n\n"
    "400-500 words total."
)

_BASE_QUERIES: dict[str, str] = {
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


def _build_research_query(section: str, ticker: str, signals: dict | None) -> str:
    base = _BASE_QUERIES.get(
        section, "Summarise ML methods used in quantitative finance."
    )
    if not signals:
        return base

    ctx_parts = [f"Ticker: {ticker}"]
    if section == "direction":
        sig = signals.get("signal", "")
        conf = signals.get("confidence")
        feat = signals.get("top_feature", "")
        if sig:
            ctx_parts.append(
                f"Current RF signal: {conf:.0%} {sig}" if conf else f"RF signal: {sig}"
            )
        if feat:
            ctx_parts.append(f"Top feature: {feat}")
    elif section == "regime":
        hmm = signals.get("hmm")
        kmeans = signals.get("kmeans")
        agree = signals.get("agree")
        if hmm:
            ctx_parts.append(f"HMM regime: {hmm}")
        if kmeans:
            ctx_parts.append(f"K-Means regime: {kmeans}")
        if agree is not None:
            ctx_parts.append("Models agree" if agree else "Models diverge")
    elif section == "credit":
        pd = signals.get("p_distress")
        if pd is not None:
            ctx_parts.append(f"P(distress): {pd:.0%}")
        factors = signals.get("top_factors", [])
        if factors:
            ctx_parts.append(
                "Top risk factors: " + ", ".join(str(f) for f in factors[:3])
            )
    elif section == "lstm":
        sig = signals.get("signal", "")
        conf = signals.get("confidence")
        if sig:
            ctx_parts.append(
                f"LSTM signal: {conf:.0%} {sig}" if conf else f"LSTM signal: {sig}"
            )

    context = ". ".join(ctx_parts)
    return f"Context for {ticker}: {context}.\n\n{base}"


def _build_synthesis_query(ticker: str, signals: dict) -> str:
    parts = [f"Stock: {ticker}"]
    d = signals.get("direction")
    if d:
        parts.append(
            f"RF Direction: {d.get('confidence', 0):.0%} {d.get('signal', 'N/A')}"
        )
    r = signals.get("regime")
    if r:
        _agree = r.get("agree")
        agree_str = (
            "agree"
            if _agree is True
            else (
                "inconclusive — K-Means shows Ranging" if _agree is None else "diverge"
            )
        )
        parts.append(
            f"Market Regime: HMM={r.get('hmm', 'N/A')}, K-Means={r.get('kmeans', 'N/A')} (models {agree_str})"
        )
    c = signals.get("credit")
    if c is not None:
        parts.append(f"Credit Risk P(distress)={c.get('p_distress', 0):.0%}")
    lstm = signals.get("lstm")
    if lstm:
        parts.append(
            f"LSTM Direction: {lstm.get('confidence', 0):.0%} {lstm.get('signal', 'N/A')}"
        )
    signal_block = "\n".join(parts)
    return (
        f"Given these ML signals:\n{signal_block}\n\n"
        "Write a concise bull/bear thesis. What do the signals collectively say? "
        "Where do they agree or conflict? What are the main risks to the thesis?"
    )


def _build_pca_query(pca_data: dict) -> str:
    std = pca_data.get("port_daily_std_pct", 0)
    var99 = pca_data.get("var_99_1d_pct", 0)
    var95 = pca_data.get("var_95_1d_pct", 0)
    hvar99 = pca_data.get("hist_var_99_1d_pct", 0)
    contribs = pca_data.get("pc_contributions", [])

    parts = [
        f"Daily std dev: {std:.2f}%",
        f"Parametric VaR 99%: {var99:.2f}%",
        f"Parametric VaR 95%: {var95:.2f}%",
        f"Historical VaR 99%: {hvar99:.2f}%",
    ]
    for pc in contribs[:3]:
        parts.append(
            f"{pc.get('name', 'PC')}: {pc.get('variance_share_pct', 0):.1f}% variance share, "
            f"{pc.get('var_99_contribution_pct', 0):.4f}% VaR contribution"
        )
    return (
        "Portfolio risk statistics (equal-weight, 1-day horizon):\n"
        + "\n".join(parts)
        + "\n\nInterpret these numbers for an equity investor. "
        "Is the concentration risk high? Is the tail risk elevated? What should the investor watch?"
    )


def run_feynman_async(section: str, ticker: str, signals: dict | None = None) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "result": "", "error": ""}
    query = _build_research_query(section, ticker, signals)
    threading.Thread(
        target=_run, args=(job_id, query, _SYSTEM_PROMPT), daemon=True
    ).start()
    return job_id


def run_synthesis_async(ticker: str, signals: dict) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "result": "", "error": ""}
    query = _build_synthesis_query(ticker, signals)
    threading.Thread(
        target=_run, args=(job_id, query, _SYNTHESIS_SYSTEM), daemon=True
    ).start()
    return job_id


def run_pca_interpret_async(pca_data: dict) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "result": "", "error": ""}
    query = _build_pca_query(pca_data)
    threading.Thread(
        target=_run, args=(job_id, query, _PCA_SYSTEM), daemon=True
    ).start()
    return job_id


def _run(job_id: str, query: str, system_prompt: str) -> None:
    if _USE_OPENAI:
        _run_openai(job_id, query, system_prompt)
    else:
        _run_subprocess(job_id, query)


def _run_openai(job_id: str, query: str, system_prompt: str) -> None:
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            max_tokens=1800,
            timeout=120,
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


def _run_subprocess(job_id: str, query: str) -> None:
    try:
        proc = subprocess.run(
            ["feynman", "--prompt", query],
            capture_output=True,
            text=True,
            timeout=300,
        )
        stdout = _ANSI_ESCAPE.sub("", proc.stdout)
        stderr = _ANSI_ESCAPE.sub("", proc.stderr)
        if not stdout.strip():
            _jobs[job_id] = {
                "status": "error",
                "result": "",
                "error": (
                    "feynman returned empty output — check `feynman status`"
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
