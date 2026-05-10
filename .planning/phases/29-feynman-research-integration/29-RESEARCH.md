# Phase 29: Feynman Research Integration - Research

**Researched:** 2026-05-10
**Domain:** Subprocess async job pattern, Flask background threading, Feynman CLI invocation, in-memory job store
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Feynman invocation:** `subprocess.run(["feynman", "--prompt", "<query>"], capture_output=True, timeout=120)` from Flask background thread. Must run async — Feynman takes 30–120s. Flask route returns `{"job_id": "<uuid>"}` immediately; JS polls `/api/feynman_status/<job_id>` every 5s until `status: done | error`.

**Query per section (hardcoded, not user-editable):**
- `direction`: "Summarise academic literature on random forest classifiers for equity return direction prediction. Include known limitations and data-snooping risks. Cite 3-5 papers."
- `pca`, `regime`, `credit`, `lstm` queries are also pre-defined in the QUERIES dict.

**UI placement:** "Research This Model" button below the RF Direction Signal badge inside the existing `_renderTickerCard()` HTML block. Spinner + text while pending. Collapsible panel titled "Academic Context" on completion.

**Panel styling:** Catppuccin dark — `#1e1e2e` background, `#313244` card, `#cdd6f4` text, `#585b70` muted/footnote text.

**Error handling:**
- Timeout (>120s): "Research timed out — Feynman took longer than 2 minutes." with retry button.
- Feynman not installed: `shutil.which("feynman") is None` at startup → route returns `{"available": false}` → button hidden silently.
- Upstream API errors: surface `stderr` in a collapsed "Details" block.

**Environment gating:** `FEYNMAN_AVAILABLE = shutil.which("feynman") is not None` at module import time — same pattern as `KERAS_AVAILABLE` in `ml_signals.py`. Silently hidden on Render cloud.

**POC scope:** RF Direction Signal section only (section key `"direction"`). One Flask module `feynman_runner.py`, two new routes in `webapp.py`, extend `mlSignals.js` only.

### Claude's Discretion

- CSS class naming for `.feynman-research-btn` and the "Academic Context" collapsible panel
- Whether `_renderResearchPanel` uses a `<details>/<summary>` native element or custom JS toggle
- ANSI escape code stripping from Feynman stdout (needed — CLI outputs color codes)
- Poll interval jitter if desired (5s fixed is fine)

### Deferred Ideas (OUT OF SCOPE)

- PCA, regime, credit risk, LSTM research buttons
- Persistent result cache (Redis / file-based)
- User-editable query input
- SSE streaming instead of polling
- Render/cloud deployment of Feynman
</user_constraints>

---

## Summary

Phase 29 is a narrowly scoped POC that wires one external CLI tool (Feynman) into one existing UI section (RF Direction Signal in the ML Signals tab). The primary technical challenge is the subprocess-backed async job pattern: Feynman runs for 30–120 seconds, so Flask cannot block a request thread. The existing codebase already imports `threading` at the top level and uses `threading.Lock()` for parallel scrapes, so introducing `threading.Thread` for background jobs is low-risk and consistent.

The second challenge is the correct Feynman invocation. CONTEXT.md uses `["feynman", "run", "<query>"]` but the installed Feynman 0.2.40 has no `run` subcommand. The documented non-interactive flag is `--prompt "<text>"`, listed under "Legacy Flags" with description "Run one prompt and exit." All other subcommands (`lit`, `deepresearch`, etc.) launch an interactive REPL. The implementation MUST use `feynman --prompt "<query>"` not `feynman run "<query>"`.

A third practical concern is Feynman's ANSI-colored terminal output. `subprocess.run` with `capture_output=True` captures raw bytes including ANSI escape sequences. The Flask route must strip these before storing `result` in the job store, otherwise the JS markdown renderer will display garbage characters. A simple `re.sub(r'\x1b\[[0-9;]*m', '', text)` handles this.

**Primary recommendation:** Use `feynman --prompt "<query>"` (not `feynman run`), strip ANSI from stdout before storing, and re-use the existing `renderMarkdown()` function already present in `chatbot.js` by exposing it on `window.Utils` or duplicating the minimal regex locally in `mlSignals.js`.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `threading` (stdlib) | stdlib | Background thread for Feynman subprocess | Already imported in webapp.py; zero new deps |
| `subprocess` (stdlib) | stdlib | Spawn feynman CLI process | Standard pattern for CLI tool invocation from Flask |
| `uuid` (stdlib) | stdlib | Generate unique job IDs | Zero-collision, stateless |
| `shutil` (stdlib) | stdlib | `shutil.which("feynman")` availability check | Mirrors existing `KERAS_AVAILABLE` guard pattern |
| `re` (stdlib) | stdlib | ANSI escape code stripping | Feynman CLI outputs color codes to stdout |

### No New Python Packages Required
All libraries are stdlib. Feynman v0.2.40 is already installed at `/Users/junhaotee/.local/bin/feynman`.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `threading.Thread` | Celery + Redis | Celery requires broker setup; threading is sufficient for single-user local POC |
| In-memory `_jobs` dict | Redis/SQLite | Persistent store overkill for POC; dict is simpler and resets on server restart (acceptable) |
| `feynman --prompt` | `feynman lit` / `feynman deepresearch` | `lit` and `deepresearch` launch interactive REPL — cannot be used non-interactively |
| `feynman --prompt` | `feynman chat <query>` | `chat` also appears to launch REPL; `--prompt` is the only documented "run and exit" flag |

---

## Architecture Patterns

### Recommended File Structure (additions only)
```
src/analytics/
└── feynman_runner.py        # FEYNMAN_AVAILABLE flag, job store, run_feynman_async(), get_job_status()

tests/
├── test_unit_feynman_runner.py    # unit tests, subprocess mocked
└── test_integration_routes.py    # extend existing file — 2 new route tests

static/js/
└── mlSignals.js             # extend _renderTickerCard(), add button/poller helpers

static/css/
└── styles.css               # add .feynman-research-btn, .feynman-panel CSS rules
```

### Pattern 1: FEYNMAN_AVAILABLE Startup Flag
**What:** Module-level shutil check mirrors the `KERAS_AVAILABLE` pattern in `ml_signals.py`.
**When to use:** Any optional CLI dependency that may be absent in cloud deployments.
**Example:**
```python
# src/analytics/feynman_runner.py
import shutil, subprocess, threading, uuid, re

FEYNMAN_AVAILABLE: bool = shutil.which("feynman") is not None

_ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE.sub('', text)
```

### Pattern 2: In-Memory Job Store with daemon Thread
**What:** UUID-keyed dict stores job state. Background thread runs subprocess and updates dict atomically.
**When to use:** Single-user local tool, no persistence requirement, runtime < 2min per job.
**Example:**
```python
# Source: webapp.py threading.Lock pattern (line 228); adapted here
_jobs: dict = {}  # job_id -> {"status": "pending|done|error", "result": str, "error": str}

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
            capture_output=True, text=True, timeout=120
        )
        _jobs[job_id] = {
            "status": "done",
            "result": _strip_ansi(proc.stdout),
            "error": _strip_ansi(proc.stderr),
        }
    except subprocess.TimeoutExpired:
        _jobs[job_id] = {"status": "error", "result": "", "error": "timeout"}
    except Exception as e:
        _jobs[job_id] = {"status": "error", "result": "", "error": str(e)}
```

### Pattern 3: Flask Routes (POST trigger + GET poll)
**What:** Two routes — POST starts job and returns job_id, GET returns current status.
**When to use:** Any long-running task initiated from the browser that must not block the HTTP response.
**Example:**
```python
# webapp.py additions
@app.route("/api/feynman_research", methods=["POST"])
def post_feynman_research():
    from src.analytics.feynman_runner import FEYNMAN_AVAILABLE, run_feynman_async
    if not FEYNMAN_AVAILABLE:
        return jsonify({"available": False})
    data = request.get_json(force=True) or {}
    section = data.get("section", "direction")
    ticker = data.get("ticker", "")
    job_id = run_feynman_async(section, ticker)
    return jsonify({"job_id": job_id})

@app.route("/api/feynman_status/<job_id>", methods=["GET"])
def get_feynman_status(job_id):
    from src.analytics.feynman_runner import get_job_status
    return jsonify(get_job_status(job_id))
```

### Pattern 4: JS Button Injection (Post-Card-Render)
**What:** After `_renderTickerCard()` sets `card.innerHTML`, call `_addResearchButton(card, ticker, 'direction')` to append the button imperatively (avoids touching the large HTML string).
**When to use:** Adding an interactive element to an existing card without restructuring the render function.

**IMPORTANT:** `card.innerHTML = html` destroys all DOM children. `_addResearchButton` must be called **after** `card.innerHTML = html` is set, and after Plotly charts are rendered.

```javascript
// mlSignals.js — append after existing Plotly block in _renderTickerCard
function _renderTickerCard(ticker, dirData, regData, credData, lstmData) {
    var card = document.getElementById('ml-card-' + ticker);
    // ... existing html building and card.innerHTML = html ...
    // ... existing Plotly calls ...

    // Inject Feynman button into RF Direction Signal section
    var dirSection = card.querySelector('.ml-section');  // first section = Direction
    if (dirSection && !dirData.insufficient_data) {
        _addResearchButton(dirSection, ticker, 'direction');
    }
}
```

### Pattern 5: Markdown Rendering for Feynman Output
**What:** Feynman outputs markdown text. `chatbot.js` already has a `renderMarkdown()` function at line 70. However, it is inside an IIFE and not exported. The simplest approach for mlSignals.js is to duplicate the same minimal regex pattern.
**When to use:** Rendering AI-generated markdown in a new JS module that does not share scope with chatbot.js.

```javascript
function _renderMarkdown(text) {
    return text
        .replace(/```(\w*)\n?([\s\S]*?)```/g, function(_, lang, code) {
            return '<pre><code>' + _escHtml(code.trim()) + '</code></pre>';
        })
        .replace(/`([^`]+)`/g, function(_, c) { return '<code>' + _escHtml(c) + '</code>'; })
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
        .replace(/\n{2,}/g, '</p><p>')
        .replace(/\n/g, '<br>');
}
function _escHtml(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
```

### Pattern 6: Collapsible Panel with Native `<details>`
**What:** Use HTML `<details>/<summary>` for the "Academic Context" collapsible — zero JS toggle logic required, default collapsed via `open` attribute absence.
**When to use:** Simple accordion-style disclosure; browser handles collapse/expand natively.

```javascript
function _renderResearchPanel(cardEl, markdownText) {
    var existing = cardEl.querySelector('.feynman-panel');
    if (existing) existing.remove();
    var panel = document.createElement('details');
    panel.className = 'feynman-panel';
    panel.innerHTML = '<summary style="color:#cdd6f4;cursor:pointer;font-weight:600;">Academic Context</summary>' +
        '<div class="feynman-panel-body">' + _renderMarkdown(markdownText) + '</div>';
    cardEl.appendChild(panel);
}
```

### Anti-Patterns to Avoid
- **`feynman run "<query>"`:** No `run` subcommand exists in v0.2.40. Use `feynman --prompt "<query>"`.
- **`feynman lit "<query>"` from subprocess:** `lit` launches interactive REPL — subprocess.run will hang until timeout.
- **Storing raw stdout without ANSI stripping:** Feynman outputs ANSI color codes; they render as garbage in HTML.
- **Calling `_addResearchButton` before `card.innerHTML = html`:** innerHTML wipe destroys appended DOM nodes.
- **`_jobs` dict access without consideration for GC:** For POC, the dict grows unboundedly. Document this limitation; acceptable for single-user local tool.
- **Using `threading.Lock` for the `_jobs` dict in POC:** CPython's GIL makes dict `__setitem__` effectively atomic for simple updates; a lock adds complexity with negligible benefit at POC scale. Omit for now.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Non-interactive CLI invocation | Custom PTY wrapper | `subprocess.run(["feynman", "--prompt", query], ...)` | `--prompt` flag is documented "run one prompt and exit" |
| ANSI stripping | Full ANSI parser | `re.sub(r'\x1b\[[0-9;]*m', '', text)` | Only SGR sequences appear in Feynman stdout; full parser is overkill |
| Markdown rendering | Custom parser | Duplicate `chatbot.js` regex pattern in mlSignals.js | Already proven in production; no external dep needed |
| Job ID generation | Incrementing int counter | `str(uuid.uuid4())` | UUIDs are collision-proof across requests without shared state |
| Background execution | Celery/RQ | `threading.Thread(daemon=True)` | Zero broker setup; sufficient for single-user POC |

**Key insight:** The entire backend is 4 functions (~40 lines) and 2 Flask routes (~20 lines). Nothing in this phase warrants a framework beyond stdlib.

---

## Common Pitfalls

### Pitfall 1: Wrong Feynman Subcommand
**What goes wrong:** `subprocess.run(["feynman", "run", query])` exits immediately with non-zero returncode because `run` is not a valid subcommand. The job `result` is empty, `error` contains Feynman's help text.
**Why it happens:** CONTEXT.md spec was written before verifying the installed CLI's exact command surface.
**How to avoid:** Use `["feynman", "--prompt", query]` — verified against v0.2.40 help output which says "Run one prompt and exit."
**Warning signs:** `proc.returncode != 0`, `proc.stderr` contains the Feynman ASCII logo and help text.

### Pitfall 2: ANSI Escape Codes in stdout
**What goes wrong:** `result` stored in `_jobs` contains `\x1b[38;2;127;187;179m` and similar sequences. The JS panel shows raw escape codes mixed with text.
**Why it happens:** Feynman is a terminal application; it outputs ANSI color even when `capture_output=True` because it doesn't check for TTY.
**How to avoid:** Always call `_strip_ansi(proc.stdout)` before storing result.
**Warning signs:** Panel body contains `[38;2;` patterns or garbled characters.

### Pitfall 3: Button DOM Node Wiped by innerHTML Reset
**What goes wrong:** User clicks "Research This Model", result arrives, but then the user triggers a re-fetch of ML signals — `card.innerHTML = html` wipes the appended button and panel.
**Why it happens:** `_renderTickerCard` always rebuilds the entire card innerHTML.
**How to avoid:** `_addResearchButton` is called at the end of `_renderTickerCard`, after `card.innerHTML = html`. Any re-render naturally re-adds the button. The panel result disappears on re-render (acceptable POC behavior — no persistence requirement).
**Warning signs:** Button disappears after ML data reloads.

### Pitfall 4: Feynman Output Is Empty (Auth Not Configured)
**What goes wrong:** `proc.returncode == 0`, `proc.stdout == ""`, `proc.stderr` contains "Model valid: no" or auth errors.
**Why it happens:** Feynman uses Pi runtime authentication. If the model is invalid or API key is not set up, the run exits cleanly but produces no output.
**How to avoid:** Check `proc.stdout.strip() == ""` after a successful run and treat as error: `{"status": "error", "error": "Feynman returned empty output — check `feynman status` and API key configuration."}`.
**Warning signs:** `feynman status` shows `Model valid: no`.

### Pitfall 5: Dangling Intervals on Navigation
**What goes wrong:** User navigates away from ML Signals tab while a job is pending. The `setInterval` poller keeps firing, accumulating dead intervals.
**Why it happens:** JavaScript `setInterval` runs regardless of DOM visibility.
**How to avoid:** Expose a `clearSession()` cleanup function on `window.MLSignals` and call `clearInterval` on all active intervals when `MLSignals.clearSession()` is invoked (already called on re-scrape). Store active intervals in a module-level array.
**Warning signs:** Network tab shows `/api/feynman_status/` calls continuing long after tab navigation.

### Pitfall 6: Thread Safety of `_jobs` Dict on Large Payloads
**What goes wrong:** At Python 3.14, the GIL behaviour around list/dict operations may differ in free-threaded mode.
**Why it happens:** Future Python versions may enable free-threaded mode by default.
**How to avoid:** For POC: document the limitation. For production: add `threading.Lock` around `_jobs` writes.
**Warning signs:** Intermittent KeyError or partial state reads on `_jobs`.

---

## Code Examples

### feynman_runner.py — Complete Module
```python
# Source: CONTEXT.md spec + verified Feynman v0.2.40 --prompt flag
import re
import shutil
import subprocess
import threading
import uuid

FEYNMAN_AVAILABLE: bool = shutil.which("feynman") is not None

_ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')
_jobs: dict = {}

QUERIES: dict = {
    "direction": (
        "Summarise academic literature on random forest classifiers for equity return "
        "direction prediction. Include known limitations and data-snooping risks. Cite 3-5 papers."
    ),
    "pca": (
        "Summarise academic literature on PCA factor decomposition for equity portfolio "
        "risk attribution. Include limitations of linear factor models."
    ),
    "regime": (
        "Summarise literature on K-Means and HMM market regime detection in equities. "
        "Compare the two approaches."
    ),
    "credit": (
        "Summarise literature on ML-based corporate credit risk scoring. Include "
        "limitations of training on synthetic distress labels."
    ),
    "lstm": (
        "Summarise academic literature on LSTM models for stock return direction prediction. "
        "Include known pitfalls and leakage risks."
    ),
}


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE.sub("", text)


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
        result = _strip_ansi(proc.stdout)
        error = _strip_ansi(proc.stderr)
        if not result.strip():
            _jobs[job_id] = {
                "status": "error",
                "result": "",
                "error": error or "Feynman returned empty output — check `feynman status`.",
            }
        else:
            _jobs[job_id] = {"status": "done", "result": result, "error": error}
    except subprocess.TimeoutExpired:
        _jobs[job_id] = {"status": "error", "result": "", "error": "timeout"}
    except Exception as exc:
        _jobs[job_id] = {"status": "error", "result": "", "error": str(exc)}


def get_job_status(job_id: str) -> dict:
    return _jobs.get(job_id, {"status": "error", "error": "unknown job_id"})
```

### Unit Test Pattern (mocked subprocess)
```python
# tests/test_unit_feynman_runner.py
import time
from unittest.mock import MagicMock, patch
import pytest

pytestmark = pytest.mark.unit


def test_run_feynman_async_happy_path():
    mock_proc = MagicMock()
    mock_proc.stdout = "# Random Forests in Finance\n\nSome content."
    mock_proc.stderr = ""
    with patch("src.analytics.feynman_runner.subprocess.run", return_value=mock_proc):
        from src.analytics.feynman_runner import run_feynman_async, get_job_status
        job_id = run_feynman_async("direction", "AAPL")
        # Poll briefly for thread to complete
        for _ in range(20):
            status = get_job_status(job_id)
            if status["status"] != "pending":
                break
            time.sleep(0.05)
        assert status["status"] == "done"
        assert "Random Forests" in status["result"]


def test_run_feynman_async_timeout():
    with patch("src.analytics.feynman_runner.subprocess.run",
               side_effect=__import__("subprocess").TimeoutExpired(["feynman"], 120)):
        from src.analytics.feynman_runner import run_feynman_async, get_job_status
        job_id = run_feynman_async("direction", "AAPL")
        for _ in range(20):
            status = get_job_status(job_id)
            if status["status"] != "pending":
                break
            time.sleep(0.05)
        assert status["status"] == "error"
        assert status["error"] == "timeout"


def test_feynman_available_false_when_not_installed():
    with patch("shutil.which", return_value=None):
        import importlib
        import src.analytics.feynman_runner as fr
        importlib.reload(fr)
        assert fr.FEYNMAN_AVAILABLE is False
```

### Integration Route Test Pattern
```python
# tests/test_integration_routes.py — add to existing file
def test_feynman_research_unavailable(client):
    """When Feynman not installed, route returns available: false."""
    with patch("src.analytics.feynman_runner.FEYNMAN_AVAILABLE", False):
        resp = client.post("/api/feynman_research",
                           json={"section": "direction", "ticker": "AAPL"},
                           content_type="application/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["available"] is False


def test_feynman_research_returns_job_id(client):
    """When Feynman is available, returns a job_id immediately."""
    with patch("src.analytics.feynman_runner.FEYNMAN_AVAILABLE", True), \
         patch("src.analytics.feynman_runner.run_feynman_async", return_value="test-uuid-123"):
        resp = client.post("/api/feynman_research",
                           json={"section": "direction", "ticker": "AAPL"},
                           content_type="application/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["job_id"] == "test-uuid-123"


def test_feynman_status_unknown_job(client):
    resp = client.get("/api/feynman_status/nonexistent-job-id")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "error"
    assert "unknown job_id" in data["error"]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `feynman run "<query>"` (spec) | `feynman --prompt "<query>"` (actual) | v0.2.40 (installed) | `run` subcommand does not exist; `--prompt` is the correct non-interactive flag |
| No background jobs in Flask | `threading.Thread` in-memory job store | Phase 29 (new) | First async pattern in webapp.py; sets precedent for future long-running tasks |
| Markdown rendering in chatbot.js only | Minimal regex duplicated in mlSignals.js | Phase 29 (new) | Avoids cross-module dependency in IIFEs |

**Deprecated/outdated:**
- `feynman run <query>`: Does not exist in v0.2.40. Not a valid subcommand.
- CONTEXT.md shows `["feynman", "run", query]` — this is the one spec deviation that must be corrected.

---

## Open Questions

1. **Feynman output format under `--prompt` flag**
   - What we know: `--prompt` is documented as "Run one prompt and exit" (Legacy Flags section).
   - What's unclear: Whether `--prompt` activates the same research pipeline as `feynman chat` or behaves like a simple one-shot completion. Also unclear whether it invokes Exa/alphaXiv paper search or just sends to the configured LLM.
   - Recommendation: Plan a manual smoke test as Wave 0: `feynman --prompt "test: return exactly the word SUCCESS"` and inspect stdout/stderr before wiring into Flask.

2. **Empty output on valid `--prompt` invocation**
   - What we know: `feynman status` shows `Model valid: no` for the current machine; the installed model is `anthropic/claude-opus-4-6`.
   - What's unclear: Whether `--prompt` will produce output or silently return empty stdout when Pi authentication is configured but the model validity check fails.
   - Recommendation: The `_run()` function already handles empty stdout by setting status to error. Add specific guidance in README about running `feynman setup` before using this feature.

3. **Process environment for subprocess**
   - What we know: Flask inherits the shell environment at startup. Feynman reads its own config (Pi auth storage at `~/.local/bin/feynman` path area).
   - What's unclear: Whether Feynman reads API keys from `.env` or its own config store. The project `.env` contains `OPENAI_API_KEY` but not `EXA_API_KEY` or `PERPLEXITY_API_KEY`.
   - Recommendation: Document in README that Feynman uses its own Pi authentication (configured via `feynman setup`), separate from the project `.env`. No additional env vars needed in the project `.env` for Feynman invocation.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | `Makefile` (pytest marks via `pytest -m unit`) |
| Quick run command | `pytest -m unit tests/test_unit_feynman_runner.py -q` |
| Full suite command | `make test-unit && make test-integration` |

### Phase Requirements → Test Map

This is a POC phase with no formal REQ-IDs. The functional requirements map as follows:

| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|-------------|
| `run_feynman_async` returns job_id immediately | unit | `pytest -m unit tests/test_unit_feynman_runner.py -q` | ❌ Wave 0 |
| Background thread sets status to `done` on success | unit | same | ❌ Wave 0 |
| Background thread sets status to `error` on timeout | unit | same | ❌ Wave 0 |
| `FEYNMAN_AVAILABLE=False` when feynman not on PATH | unit | same | ❌ Wave 0 |
| POST `/api/feynman_research` returns `{available: false}` when not installed | integration | `pytest -m integration tests/test_integration_routes.py -q` | ❌ Wave 0 |
| POST `/api/feynman_research` returns `{job_id: ...}` when available | integration | same | ❌ Wave 0 |
| GET `/api/feynman_status/<unknown>` returns `{status: error}` | integration | same | ❌ Wave 0 |
| ANSI codes stripped from Feynman stdout | unit | same | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest -m unit tests/test_unit_feynman_runner.py -q`
- **Per wave merge:** `make test-unit && make test-integration`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_unit_feynman_runner.py` — all unit tests for feynman_runner module
- [ ] Two new test functions in `tests/test_integration_routes.py` — route coverage

*(Existing `conftest.py` `client` fixture is reusable for integration tests — no new conftest changes needed)*

---

## Sources

### Primary (HIGH confidence)
- Feynman v0.2.40 — `feynman --help` output, verified locally — CLI commands and `--prompt` flag
- `webapp.py` — direct code inspection lines 21, 228 — threading pattern already in use
- `src/analytics/ml_signals.py` lines 26–32 — `KERAS_AVAILABLE` guard pattern
- `static/js/mlSignals.js` lines 167–255 — `_renderTickerCard` structure and injection point
- `static/js/chatbot.js` lines 70–83 — existing `renderMarkdown` regex pattern
- `tests/conftest.py` — `client` fixture and test marker conventions
- `.planning/phases/29-feynman-research-integration/29-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)
- [Feynman GitHub README](https://github.com/getcompanion-ai/feynman) — subcommand listing, install method
- [Feynman.is website](https://www.feynman.is) — overview description

### Tertiary (LOW confidence)
- `feynman status` output showing `Model valid: no` — current auth state may affect `--prompt` behavior; no documented guarantee of output when model is invalid

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all stdlib, verified locally installed Feynman
- Architecture: HIGH — direct code inspection of existing patterns to mirror
- Feynman CLI invocation: HIGH — verified against installed v0.2.40 help output
- Feynman output behavior under `--prompt`: MEDIUM — documented as "run and exit" but live behavior with current auth not smoke-tested
- Pitfalls: HIGH — ANSI issue and wrong subcommand verified against actual CLI output

**Research date:** 2026-05-10
**Valid until:** 2026-06-10 (stable stdlib patterns; Feynman CLI version may update)
