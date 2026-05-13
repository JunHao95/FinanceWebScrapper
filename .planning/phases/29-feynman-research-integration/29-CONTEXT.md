# Phase 29: Feynman Research Integration — Context

**Drafted:** 2026-05-10
**Status:** Draft — awaiting planning

<domain>
## Phase Boundary

Integrate [Feynman.is](https://www.feynman.is) — an open-source CLI AI research agent — into the ML Signals tab as an optional "go deep" research sidebar. When a user views an ML model result (RF Direction Signal, PCA, K-Means Regime, Credit Risk, LSTM), they can trigger an on-demand academic research fetch that surfaces relevant papers, methodology context, and known limitations for that model.

Phase 29 is **proof-of-concept only**: one ML section (RF Direction Signal), one Flask route, one async job pattern. Subsequent phases may expand to other sections.

**Explicitly out of scope:**
- Integrating Feynman into any tab other than ML Signals
- PCA, regime, credit risk, or LSTM research panels (Phase 29 = RF only)
- Persistent caching of Feynman results across sessions
- User-editable research queries

</domain>

<decisions>
## Implementation Decisions

### Feynman invocation
- Feynman has no REST API. Invocation via `subprocess.run(["feynman", "run", "<query>"], capture_output=True, timeout=120)` from Flask.
- Must run async (background thread or Celery-lite via `threading.Thread`) — Feynman takes 30–120s.
- Flask route returns `{"job_id": "<uuid>"}` immediately; JS polls `/api/feynman_status/<job_id>` every 5s until `status: done | error`.

### Query construction per ML section
- RF Direction Signal: `"Summarise academic literature on random forest classifiers for equity return direction prediction. Include known limitations and data-snooping risks."`
- Query is hardcoded per section (not user-editable) — keeps latency and cost predictable.

### UI placement
- Each ML section card (starting with RF Direction Signal) gets a "Research This Model" button below the signal badge.
- Button click triggers POST to `/api/feynman_research` with `{"section": "direction", "ticker": "<ticker>"}`.
- While pending: spinner + "Searching academic papers…" placeholder.
- On completion: collapsible panel (default collapsed) titled "Academic Context" renders markdown output from Feynman.
- Panel uses existing Catppuccin dark theme — grey card, `#cdd6f4` body text, `#585b70` footnote citations.

### Error handling
- Timeout (>120s): show "Research timed out — Feynman took longer than 2 minutes." with retry button.
- Feynman not installed: backend detects `shutil.which("feynman") is None` at startup → route returns `{"available": false}` → button hidden in UI with no error shown.
- Network errors from upstream APIs (Exa/Perplexity): surface Feynman's stderr in a collapsed "Details" block for debugging.

### Cost & rate limiting
- No server-side rate limit in POC — single-user local tool.
- Feynman invokes Exa/Perplexity/Gemini APIs: user must have `.env` vars set (`EXA_API_KEY`, `PERPLEXITY_API_KEY`, etc.).
- README must document required env vars and warn about per-call cost.

### Environment gating
- `FEYNMAN_AVAILABLE` flag set at app startup via `shutil.which("feynman")` — same pattern as `KERAS_AVAILABLE` in `ml_signals.py`.
- On Render (cloud): Feynman CLI not installed → feature silently hidden. No deploy breakage.

</decisions>

<code_context>
## Existing Code Insights

### Reusable patterns
- `ml_signals.py`: `KERAS_AVAILABLE` startup flag + `is_cloud_environment()` guard — mirror for `FEYNMAN_AVAILABLE`.
- `webapp.py`: async/threading not currently used — introduce `threading.Thread` + in-memory job store (`dict` keyed by UUID) for POC. No Celery required.
- `static/js/mlSignals.js`: existing `_renderTickerCard()` builds RF card HTML — add "Research This Model" button inside this block.
- Existing spinner pattern: `<div class="loading-spinner">` used in `stockScraper.js` — reuse CSS class.
- Catppuccin palette: `#1e1e2e` background, `#313244` card, `#cdd6f4` text, `#585b70` muted.

### New files needed
- `src/analytics/feynman_runner.py`: `run_feynman_async(section, ticker) -> job_id`, `get_job_status(job_id) -> dict`
- No new JS file — extend `mlSignals.js`
- No new HTML template — inject button/panel via JS

### Integration points
- `webapp.py`: two new routes:
  - `POST /api/feynman_research` → starts background job, returns `{"job_id": "..."}` or `{"available": false}`
  - `GET /api/feynman_status/<job_id>` → returns `{"status": "pending|done|error", "result": "...", "error": "..."}`
- `static/js/mlSignals.js`: add `_addResearchButton(cardEl, ticker, section)` helper + `_pollResearchJob(jobId, panelEl)` poller
- `tests/test_unit_feynman_runner.py`: unit tests with mocked subprocess (no live Feynman calls in CI)
- `tests/test_integration_routes.py`: add tests for both new routes covering `available=false` path (Feynman not installed) and mocked happy path

</code_context>

<specifics>
## Specific Implementation Notes

### Job store (in-memory POC)
```python
# feynman_runner.py
import subprocess, threading, uuid, shutil

FEYNMAN_AVAILABLE = shutil.which("feynman") is not None
_jobs = {}  # job_id -> {"status": "pending|done|error", "result": str, "error": str}

QUERIES = {
    "direction": "Summarise academic literature on random forest classifiers for equity return direction prediction. Include known limitations and data-snooping risks. Cite 3-5 papers.",
    "pca":       "Summarise academic literature on PCA factor decomposition for equity portfolio risk attribution. Include limitations of linear factor models.",
    "regime":    "Summarise literature on K-Means and HMM market regime detection in equities. Compare the two approaches.",
    "credit":    "Summarise literature on ML-based corporate credit risk scoring. Include limitations of training on synthetic distress labels.",
    "lstm":      "Summarise academic literature on LSTM models for stock return direction prediction. Include known pitfalls and leakage risks.",
}

def run_feynman_async(section: str, ticker: str) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "result": "", "error": ""}
    query = QUERIES.get(section, "Summarise ML methods used in quantitative finance.")
    threading.Thread(target=_run, args=(job_id, query), daemon=True).start()
    return job_id

def _run(job_id: str, query: str):
    try:
        out = subprocess.run(["feynman", "run", query], capture_output=True, text=True, timeout=120)
        _jobs[job_id] = {"status": "done", "result": out.stdout, "error": out.stderr}
    except subprocess.TimeoutExpired:
        _jobs[job_id] = {"status": "error", "result": "", "error": "timeout"}
    except Exception as e:
        _jobs[job_id] = {"status": "error", "result": "", "error": str(e)}

def get_job_status(job_id: str) -> dict:
    return _jobs.get(job_id, {"status": "error", "error": "unknown job_id"})
```

### Button injection (mlSignals.js)
```javascript
function _addResearchButton(cardEl, ticker, section) {
    var btn = document.createElement('button');
    btn.textContent = 'Research This Model';
    btn.className = 'feynman-research-btn';
    btn.onclick = function () { _startResearch(btn, ticker, section); };
    cardEl.appendChild(btn);
}

function _startResearch(btn, ticker, section) {
    btn.disabled = true;
    btn.textContent = 'Searching academic papers…';
    fetch('/api/feynman_research', { method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({section: section, ticker: ticker}) })
    .then(r => r.json()).then(function(d) {
        if (d.available === false) { btn.textContent = 'Research unavailable'; return; }
        _pollResearchJob(d.job_id, btn);
    });
}

function _pollResearchJob(jobId, btn) {
    var interval = setInterval(function() {
        fetch('/api/feynman_status/' + jobId).then(r => r.json()).then(function(d) {
            if (d.status === 'done') {
                clearInterval(interval);
                btn.textContent = 'Research This Model';
                btn.disabled = false;
                _renderResearchPanel(btn.parentElement, d.result);
            } else if (d.status === 'error') {
                clearInterval(interval);
                btn.textContent = 'Research failed — retry';
                btn.disabled = false;
            }
        });
    }, 5000);
}
```

</specifics>

<deferred>
## Deferred to Later Phases

- PCA, regime, credit risk, LSTM research buttons — expand after POC validated
- Persistent result cache (Redis / file-based) so same section query isn't re-run within a session
- User-editable query input field
- Streaming output (SSE) instead of polling — reduces UX latency but adds server complexity
- Render/cloud deployment of Feynman (requires API keys as env vars in Render dashboard)

</deferred>

---

*Phase: 29-feynman-research-integration*
*Context drafted: 2026-05-10*
