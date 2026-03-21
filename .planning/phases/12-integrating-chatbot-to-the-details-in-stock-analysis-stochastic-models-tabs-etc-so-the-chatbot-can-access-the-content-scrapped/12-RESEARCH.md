# Phase 12: Chatbot Context Integration - Research

**Researched:** 2026-03-22
**Domain:** Frontend state serialisation, LLM prompt engineering, Flask API extension
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**What context gets sent**
- Scope: Everything available — current tickers, all scraped metrics (P/E, RSI, EPS, sentiment, price, ROE), portfolio analytics (VaR, Sharpe, correlation, PCA), CNN Fear & Greed data, regime detection results, and full `_fundamental_analysis` per ticker
- Non-stock tabs: Yes — stochastic model results (Heston, regime, CIR, Markov, etc.) and RL tab outputs are included when available
- Fundamentals depth: Full `_fundamental_analysis` included
- Context size: Truncate/summarise per ticker when many tickers present — cap per-ticker fields to the most important ones to keep payload manageable regardless of ticker count
- Stochastic capture: Each time a model runs (Heston, Regime, CIR, etc.), store its latest results in a shared `pageContext` object; chatbot gets whatever was last run

**Context trigger & timing**
- Trigger: Always — every message sent includes the latest available page context automatically
- Freshness: Captured fresh on each message send (current page state at send time)
- No-data state: If nothing is scraped yet, chatbot works as a general assistant with no context injected — no error, no warning
- Stochastic/RL capture: Store last-run results per model in a shared context object; accumulated across the session per model type

**How agents use the context**
- Injection point: Context appended to the agent's system prompt per request (not prepended to user message)
- Format: Structured plain text — readable, token-efficient
- Agent split: Both agents receive the same context payload; their system prompt persona determines interpretation
- Chat history: Include last N messages (last 10 messages / 5 turns) — already partially in place from Phase 10.1

**User-visible context awareness**
- Indicator: Subtle text line below the agent pill-tab toggle showing "Context: AAPL, MSFT" (or hidden when nothing loaded)
- Auto-greeting: No
- Context reset on new scrape: Context silently updates; chat history preserved
- Error handling: Generic error with retry offered — same as current

### Claude's Discretion
- Exact field selection for per-ticker truncation (which fields are "most important" when capping)
- Exact plain-text serialisation format/template for the context block
- How stochastic results are stored in the shared context object (data structure)
- Backend field name for context parameter in /api/chat request body

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

## Summary

Phase 12 wires the existing in-memory page state into every `/api/chat` POST request. No new agents, no persistent storage, and no UI redesign are required. The work splits cleanly into three concerns: (1) a shared `pageContext` JS object that accumulates state from AppState plus stochastic model result hooks, (2) a serialiser that converts that object to structured plain text at send-time in `chatbot.js`, and (3) a backend extension in `webapp.py` that reads the new `context` field and appends it to the agent system prompt before the LLM call.

The codebase is already well-suited for this work. `AppState` (state.js) holds all scraped metrics. `PortfolioHealth`, `autoRun.js`, and `stochasticModels.js` produce results that must be captured via callback hooks. The chatbot's `sendMessage()` function is the single integration point on the frontend. The `/api/chat` route at webapp.py:1979-2048 is the single integration point on the backend.

The primary design challenge is token budget management: the Groq default model (`llama3-8b-8192`) has an 8,192-token context window, and a naive full dump of all fields for many tickers could overflow it. The serialiser must apply per-ticker field capping and fundamental truncation when ticker count is high.

**Primary recommendation:** Implement a global `window.pageContext` object, populate it via hooks in existing result handlers, serialise it to structured plain text in `sendMessage()`, and append it to the system prompt in `webapp.py`.

---

## Standard Stack

### Core (all already in the project — no new dependencies)

| Library/API | Version | Purpose | Why Standard |
|-------------|---------|---------|--------------|
| Flask (webapp.py) | existing | Receives and processes context payload | Already the app server |
| Groq API | existing | LLM inference, llama3-8b-8192 | Already configured; GROQ_API_KEY env var |
| Ollama fallback | existing | Local LLM inference | Already implemented in chat route |
| AppState (state.js) | existing | Source for scraped metrics per ticker | Single source of truth for current data |
| chatbot.js | existing | Frontend chat logic, sendMessage() | Already handles fetch to /api/chat |

### No new packages required
This phase is pure wiring — all libraries are already present. No `npm install` or `pip install` steps needed.

---

## Architecture Patterns

### Recommended Project Structure (changes only)

```
static/js/
├── state.js              # Add: window.pageContext = {} declaration
├── chatbot.js            # Add: buildContextSnapshot(), context indicator HTML
├── stochasticModels.js   # Add: pageContext capture hooks after each run*
├── autoRun.js            # Add: pageContext.regimeResults capture hook
└── rlModels.js           # Add: pageContext.rlResults capture hook (optional)

webapp.py
└── chat()                # Extend: read context field, serialise, append to system prompt
```

*stochasticModels.js hooks: after `runRegimeDetection`, `runHestonCalibration`, `runMertonCalibration`, `runCIRModel`, `runCreditRisk`, `runHestonPricing`, `runBCCCalibration`, `runMarkovChain`.

### Pattern 1: Shared `window.pageContext` Object

**What:** A single global object that any module can write to. Lives on `window` so all scripts can access it without explicit imports (matching the existing pattern of `window.AppState`, `window.PortfolioHealth`, `window.AutoRun`).

**When to use:** Any time a model run completes and produces results worth surfacing to the chatbot.

**Data structure (Claude's discretion — recommended):**
```javascript
// Source: existing project patterns (window.AppState, window.PortfolioHealth)
window.pageContext = {
    // Populated immediately from AppState after scrape
    tickers: [],           // ['AAPL', 'MSFT']
    tickerData: {},        // { AAPL: { price, pe, rsi, sentiment, roe, eps, regime, var95, fundamentals } }
    portfolio: {},         // { sharpe, var95, correlation }
    cnnFearGreed: null,    // { score: 61, label: 'Greed' }

    // Populated by model run hooks
    stochasticResults: {}, // { regime_AAPL: {...}, heston_AAPL: {...}, cir: {...}, ... }
    rlResults: {}          // { portfolioMDP: {...} }
};
```

**Initialise in state.js** alongside AppState declaration, so it is available before any module runs.

### Pattern 2: Context Snapshot at Send-Time

**What:** `buildContextSnapshot()` reads `window.pageContext` at the moment the user sends a message. This ensures freshness without polling.

**When to use:** Called at the top of `sendMessage()` before the fetch call.

**Example:**
```javascript
// In chatbot.js sendMessage()
// Source: adapted from AppState access pattern in rlModels.js:70-78
function buildContextSnapshot() {
    const pc = window.pageContext || {};
    const tickers = pc.tickers || [];
    if (tickers.length === 0) return null;  // no data yet — return null, send no context

    const lines = ['=== Page Context ==='];
    lines.push(`Active tickers: ${tickers.join(', ')}`);
    lines.push('');

    const MAX_TICKERS_FULL = 4;  // above this, use abbreviated per-ticker format
    const isAbbrev = tickers.length > MAX_TICKERS_FULL;

    tickers.forEach(t => {
        const d = (pc.tickerData || {})[t] || {};
        if (isAbbrev) {
            // Abbreviated: key metrics only
            lines.push(`${t}: Price $${d.price ?? 'N/A'} | P/E ${d.pe ?? 'N/A'} | RSI ${d.rsi ?? 'N/A'} | Regime ${d.regime ?? 'N/A'}`);
        } else {
            // Full format per CONTEXT.md example
            lines.push(`${t}${d.name ? ` (${d.name})` : ''}:`);
            lines.push(`  Price: $${d.price ?? 'N/A'} | P/E: ${d.pe ?? 'N/A'} | EPS: $${d.eps ?? 'N/A'} | ROE: ${d.roe ?? 'N/A'} | RSI: ${d.rsi ?? 'N/A'}`);
            lines.push(`  Sentiment: Overall ${d.sentimentOverall ?? 'N/A'} | News ${d.sentimentNews ?? 'N/A'} | Reddit ${d.sentimentReddit ?? 'N/A'}`);
            lines.push(`  Regime: ${d.regime ?? 'N/A'} | VaR (95%): ${d.var95 ?? 'N/A'}`);
            if (d.fundamentals) lines.push(`  Fundamentals: ${d.fundamentals}`);
        }
        lines.push('');
    });

    if (pc.portfolio && Object.keys(pc.portfolio).length > 0) {
        const p = pc.portfolio;
        lines.push('Portfolio:');
        if (p.sharpe != null) lines.push(`  Sharpe: ${p.sharpe}`);
        if (p.var95 != null) lines.push(`  VaR (95%): ${p.var95}`);
        if (p.correlation) lines.push(`  Correlation: ${p.correlation}`);
        lines.push('');
    }

    if (pc.cnnFearGreed) {
        lines.push(`CNN Fear & Greed: ${pc.cnnFearGreed.score} (${pc.cnnFearGreed.label})`);
        lines.push('');
    }

    // Stochastic results (whatever was last run)
    const stoch = pc.stochasticResults || {};
    const stochKeys = Object.keys(stoch);
    if (stochKeys.length > 0) {
        lines.push('Stochastic Model Results (last run):');
        stochKeys.forEach(k => {
            const r = stoch[k];
            lines.push(`  ${k}: ${JSON.stringify(r).slice(0, 200)}`);  // cap at 200 chars per model
        });
        lines.push('');
    }

    return lines.join('\n');
}
```

### Pattern 3: Backend Context Injection

**What:** `webapp.py` reads `context` from the POST body and appends it to the system prompt string before passing to the LLM.

**When to use:** Every `/api/chat` request.

**Example:**
```python
# In webapp.py chat() at line ~1991, after reading agent/system_prompt
# Source: existing data.get() pattern at webapp.py:1985-1992
page_context = data.get("context", None)  # plain text string or None

effective_system_prompt = system_prompt
if page_context and isinstance(page_context, str) and page_context.strip():
    effective_system_prompt = system_prompt + "\n\n" + page_context.strip()
```

Then replace `system_prompt` with `effective_system_prompt` in both the Groq and Ollama payload dicts.

### Pattern 4: AppState-to-pageContext Population

**What:** After `AppState` is updated in `stockScraper.js` (line 103-107), populate `window.pageContext` from the same result.

**When to use:** Inside the `if (result.success)` block in `stockScraper.js`.

**Data mapping — recommended field selection (Claude's discretion):**

For each ticker in `result.data[ticker]`:
- `price` — from `Price` or `Current Price`
- `pe` — from `P/E Ratio`
- `eps` — from `EPS`
- `roe` — from `ROE`
- `rsi` — from `RSI` or technical indicators
- `sentimentOverall`, `sentimentNews`, `sentimentReddit` — from sentiment fields
- `fundamentals` — truncated summary string from `_fundamental_analysis` (see below)
- `regime` — initially null; updated by autoRun.js regime hook

For `cnnFearGreed`: map from `AppState.currentCnnData`.

For `portfolio`: populated by `PortfolioHealth` after `_fetchSharpe` resolves (see portfolioHealth.js pattern).

### Pattern 5: Regime Hook in autoRun.js

`runAutoRegime()` already calls `PortfolioHealth.updateRegime(ticker, regimeLabel)` on success (line 165). Add a matching call to update `pageContext`:

```javascript
// After PortfolioHealth.updateRegime call in runAutoRegime()
if (window.pageContext && window.pageContext.tickerData && window.pageContext.tickerData[ticker]) {
    window.pageContext.tickerData[ticker].regime = regimeLabel;
}
```

### Pattern 6: Stochastic Model Result Hooks

Add a result-store call at the end of each `run*` function's success path in `stochasticModels.js`. Example for regime detection (manual tab):

```javascript
// At end of runRegimeDetection() success path
if (window.pageContext) {
    window.pageContext.stochasticResults['regime_' + ticker] = {
        signal: data.signal,
        currentRegime: regimeLabel,
        ticker: ticker
    };
}
```

Example for Heston calibration:
```javascript
// After calibration result displayed
if (window.pageContext && cal) {
    window.pageContext.stochasticResults['heston_' + ticker] = {
        rmse: cal.rmse,
        params: cal.calibrated_params,
        ticker: ticker
    };
}
```

Keep stored objects small — only summary fields, not full arrays.

### Pattern 7: Context Indicator in chatbot.js HTML

Add one line below the `#chatbot-agent-tabs` div in the HTML template:

```javascript
// In chatbot.js injected HTML template, after #chatbot-agent-tabs closing div:
<div id="chatbot-context-indicator" style="
    font-size: 10px;
    color: rgba(255,255,255,0.45);
    padding: 0 18px 6px;
    min-height: 16px;
    letter-spacing: 0.01em;
"></div>
```

Update it in `sendMessage()` and after scrape:
```javascript
function updateContextIndicator() {
    const tickers = (window.pageContext && window.pageContext.tickers) || [];
    const el = document.getElementById('chatbot-context-indicator');
    if (!el) return;
    el.textContent = tickers.length > 0 ? 'Context: ' + tickers.join(', ') : '';
}
```

### Anti-Patterns to Avoid

- **Storing full time-series arrays in pageContext.stochasticResults:** Heston calibration returns `strikes`, `market_ivs`, `fitted_ivs` arrays. Store only summary scalars (rmse, params). Never pass arrays to the LLM context.
- **Serialising pageContext as JSON in the fetch body:** Send it as a pre-serialised plain text string. The backend receives a string and appends it directly — no JSON-parsing logic needed on the backend.
- **Calling `buildContextSnapshot()` outside `sendMessage()`:** Snapshot freshness is guaranteed only by calling at send-time. Do not cache the snapshot.
- **Modifying agentHistories to include context:** History replay (switchAgent) should not re-inject old context. Context is ephemeral per-request, not persisted in history.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token counting | Custom token budget enforcer | Field capping + char truncation | Exact token count requires a tokeniser library; char truncation is sufficient for this payload size |
| Markdown serialisation | Custom formatter | Structured plain text (as per CONTEXT.md decision) | LLMs handle plain text equally well and it is more token-efficient |
| Cross-module event bus | Custom pub/sub system | Direct `window.pageContext` writes | Existing pattern (window.AppState, window.PortfolioHealth) — no event bus needed |
| History in context | Re-sending full history | Already handled: chat route receives `messages` array if needed | History is already tracked in `agentHistories`; N-turn context is already partial per Phase 10.1 |

**Key insight:** The project uses direct `window.*` globals for cross-module communication. No module system, no imports, no event bus. Follow the same pattern for `pageContext`.

---

## Common Pitfalls

### Pitfall 1: Groq Context Window Overflow

**What goes wrong:** `llama3-8b-8192` has an 8,192-token context. A naive full dump for 5+ tickers with full `_fundamental_analysis` text (which can be 500+ words each) plus stochastic results overflows the context, causing a 400/413 error from Groq.

**Why it happens:** `_fundamental_analysis` from `analytics.fundamental_analysis()` returns multi-section analysis text. Per-ticker `_fundamental_analysis` fields are verbose.

**How to avoid:** In `buildContextSnapshot()`, truncate `_fundamental_analysis` to a short summary (e.g., first 300 chars or first paragraph). When `tickers.length > 4`, use the abbreviated per-ticker format. Cap each stochastic result to 200 chars.

**Warning signs:** Groq returns `{"error": {"message": "...", "type": "invalid_request_error"}}` with status 400 when context is too long.

### Pitfall 2: `_fundamental_analysis` Field Shape Unknown at Runtime

**What goes wrong:** `_fundamental_analysis` is only present in `AppState.currentData[ticker]` if the scrape's fundamental analysis step succeeded. The field may be absent entirely.

**Why it happens:** `webapp.py:499-507` wraps `fundamental_analysis()` in a try/except and only sets the field on success.

**How to avoid:** Always use optional chaining / null guard when reading it. Extract a short summary string from it rather than serialising the whole object.

**Recommended extraction:** In `buildContextSnapshot()`, if `_fundamental_analysis` exists:
```javascript
const fa = rawData._fundamental_analysis;
// fa is an object; extract top-level text fields
const summary = fa.summary || fa.overall_assessment || fa.recommendation || '';
d.fundamentals = typeof summary === 'string' ? summary.slice(0, 300) : '';
```

### Pitfall 3: pageContext Populated Before AppState is Set

**What goes wrong:** If `window.pageContext` is initialised in `state.js` but populated in `stockScraper.js`, and a stochastic model tab is used before any scrape, `pageContext.tickers` will be empty. That is correct behaviour per the no-data decision. But if the scraper error path fails silently, `pageContext` may be stale from a prior run.

**Why it happens:** Re-runs — user scrapes new tickers without page reload.

**How to avoid:** In the scrape success path, reset `pageContext.tickers`, `pageContext.tickerData`, `pageContext.portfolio`, `pageContext.cnnFearGreed` fully before populating. Do NOT reset `pageContext.stochasticResults` — these are session-accumulated per the decision.

### Pitfall 4: Chat History Already Partially Implemented — Don't Double-Send

**What goes wrong:** The backend `/api/chat` currently sends only the current `message` to the LLM (no history). The CONTEXT.md says include last 10 messages / 5 turns. If the planner adds history AND this phase adds context, the payload must be assembled carefully to avoid duplication.

**Why it happens:** Phase 10.1 partially set up history tracking (`agentHistories` object) but the backend does not currently consume it.

**How to avoid:** Phase 12 should wire history as a `history` field alongside `context`. The backend assembles messages as: `[system_prompt + context_block, ...last_10_history_messages, current_user_message]`.

Current backend Groq payload (webapp.py:2005-2011):
```python
"messages": [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": message}
]
```

Extended payload:
```python
"messages": [
    {"role": "system", "content": effective_system_prompt},  # system + context appended
    *[{"role": h["sender"], "content": h["text"]} for h in history_slice],  # last N turns
    {"role": "user", "content": message}
]
```

Where `history_slice` maps `sender: 'bot'` to `role: 'assistant'` and `sender: 'user'` to `role: 'user'`.

### Pitfall 5: Context Indicator Flickers on Agent Switch

**What goes wrong:** When the user switches agent tabs, `messagesContainer.innerHTML` is cleared and re-rendered. If the context indicator is inside the messages container it will be wiped.

**How to avoid:** Place `#chatbot-context-indicator` inside `#chatbot-header` (below the pills row), NOT inside `#chatbot-messages`. The header is never cleared during agent switch.

---

## Code Examples

Verified patterns from the existing codebase:

### Reading AppState data (existing pattern)
```javascript
// Source: rlModels.js:70-78 (established AppState access pattern)
const tickers   = (window.AppState && AppState.currentTickers) || [];
const analytics = window.AppState && AppState.currentAnalytics;
const cnnData   = window.AppState && AppState.currentCnnData;
const data      = window.AppState && AppState.currentData;
```

### Extending the fetch body in sendMessage (change target)
```javascript
// Source: chatbot.js:163-167 (current sendMessage fetch call)
body: JSON.stringify({
    message: text,
    agent: activeAgent,
    context: buildContextSnapshot() || '',     // NEW — plain text string or empty string
    history: agentHistories[activeAgent].slice(-10)  // NEW — last 10 messages
})
```

### Backend reading new fields (change target)
```python
# Source: webapp.py:1985-1992 (existing data.get pattern)
data = request.json or {}
message = data.get("message", "").strip()
agent = data.get('agent', 'quant')
page_context = data.get("context", "")    # NEW
history = data.get("history", [])          # NEW
system_prompt = SYSTEM_PROMPTS.get(agent, SYSTEM_PROMPTS['quant'])

effective_system_prompt = system_prompt
if page_context and page_context.strip():
    effective_system_prompt = system_prompt + "\n\n" + page_context.strip()
```

### Groq payload with history (change target)
```python
# Source: webapp.py:2005-2011 (existing Groq payload structure)
# Map frontend history format to OpenAI role format
def _map_role(sender):
    return "assistant" if sender == "bot" else "user"

history_messages = [
    {"role": _map_role(h.get("sender", "user")), "content": h.get("text", "")}
    for h in history[-10:]  # safety cap
    if h.get("text")
]

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": effective_system_prompt},
        *history_messages,
        {"role": "user", "content": message}
    ]
}
```

### stochasticModels.js result capture hook pattern
```javascript
// Add at end of runRegimeDetection() success block (after existing chart rendering)
// Source: adapted from autoRun.js:164-165 (existing PortfolioHealth.updateRegime pattern)
if (window.pageContext) {
    window.pageContext.stochasticResults = window.pageContext.stochasticResults || {};
    window.pageContext.stochasticResults['regime_' + ticker] = {
        ticker,
        signal: data.signal,
        currentRegime: data.filtered_probs?.slice(-1)[0] >= 0.5 ? 'RISK_OFF' : 'RISK_ON'
    };
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No page context in chatbot | Context injected per message | Phase 12 | Agents become aware of what the user is analysing |
| Single-turn chat (system + user only) | Multi-turn with history slice | Phase 12 | Coherent multi-question conversations |
| Context-blind system prompt | System prompt + context block appended | Phase 12 | Agent responses reference actual scraped data |

---

## Open Questions

1. **`_fundamental_analysis` field shape**
   - What we know: It is a dict produced by `analytics.fundamental_analysis(stock_data, ticker)` — defined in `src/analytics/financial_analytics.py:1278`. The route docstring at webapp.py:282-304 shows input fields (P/E, P/B, ROE, EPS, FCF, etc.).
   - What's unclear: The exact keys of the output dict (summary string vs. nested sections vs. ratings).
   - Recommendation: Read `src/analytics/financial_analytics.py` around line 1278 during planning to confirm output shape and select the best 1-2 keys for the summary string.

2. **`AppState.currentData[ticker]` field names**
   - What we know: Fields like `P/E Ratio`, `RSI`, `ROE` come from Yahoo/Finviz scrapers. The exact capitalisation and key names vary per scraper.
   - What's unclear: Exact runtime keys at `AppState.currentData[ticker]` (e.g. is it `"P/E Ratio"` or `"pe_ratio"` or `"PE"`).
   - Recommendation: Add a `console.log(AppState.currentData)` test run during Wave 0 to confirm field names, or grep displayManager.js for the field access patterns.

3. **History sending — Ollama branch**
   - What we know: Ollama's payload structure is `{model, messages: [{role, content}], stream: false}` — same OpenAI format.
   - What's unclear: Whether the local Ollama model handles `role: assistant` history correctly.
   - Recommendation: Use same history logic for both branches; it is standard OpenAI-compatible format.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | tests/conftest.py |
| Quick run command | `pytest tests/test_chat_route.py -x -q` |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CTX-01 | `/api/chat` with `context` field appends context to system prompt | unit | `pytest tests/test_chat_route.py::test_chat_with_context -x` | Wave 0 |
| CTX-02 | `/api/chat` with empty/missing `context` uses base system prompt unchanged | unit | `pytest tests/test_chat_route.py::test_chat_no_context -x` | Wave 0 |
| CTX-03 | `/api/chat` with `history` field sends history turns to LLM | unit | `pytest tests/test_chat_route.py::test_chat_with_history -x` | Wave 0 |
| CTX-04 | Frontend `buildContextSnapshot()` returns null when no tickers loaded | manual | Browser console check | N/A |
| CTX-05 | Context indicator shows "Context: TICKER" when tickers loaded | manual | Visual check | N/A |

### Sampling Rate
- **Per task commit:** `pytest tests/test_chat_route.py -x -q`
- **Per wave merge:** `pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_chat_route.py` — extend with `test_chat_with_context`, `test_chat_no_context`, `test_chat_with_history` (file exists, needs new test functions)
- [ ] No new test files needed — extend existing `test_chat_route.py`

---

## Sources

### Primary (HIGH confidence)
- Direct code reading: `static/js/chatbot.js` — confirmed current sendMessage() structure, agentHistories, fetch payload
- Direct code reading: `webapp.py:1979-2048` — confirmed /api/chat route, SYSTEM_PROMPTS, Groq/Ollama dual path
- Direct code reading: `static/js/state.js` — confirmed AppState fields: currentData, currentCnnData, currentTickers, currentAnalytics
- Direct code reading: `static/js/autoRun.js` — confirmed regime result handling and PortfolioHealth.updateRegime pattern
- Direct code reading: `static/js/stochasticModels.js` — confirmed all 9 run* functions, result structures
- Direct code reading: `static/css/styles.css:1131-1410` — confirmed chatbot dark theme and agent-pill CSS variables
- Direct code reading: `tests/test_chat_route.py` — confirmed test pattern (mock requests.post, monkeypatch GROQ_API_KEY)
- Phase 12 CONTEXT.md — all locked decisions

### Secondary (MEDIUM confidence)
- Groq llama3-8b-8192 context window: 8,192 tokens — well-known from Groq API documentation. Token budget concern is real; char-based truncation is a pragmatic mitigation.

### Tertiary (LOW confidence)
- `_fundamental_analysis` output shape: inferred from input schema docstring at webapp.py:282-304 and analytics module grep. Exact output keys not verified — see Open Questions.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all files read directly, no external dependencies needed
- Architecture: HIGH — patterns derived from existing codebase conventions with direct verification
- Pitfalls: HIGH for token overflow and field presence guards (real code patterns verified); MEDIUM for exact `_fundamental_analysis` output shape (not fully read)

**Research date:** 2026-03-22
**Valid until:** 2026-06-22 (stable codebase, no fast-moving dependencies)
