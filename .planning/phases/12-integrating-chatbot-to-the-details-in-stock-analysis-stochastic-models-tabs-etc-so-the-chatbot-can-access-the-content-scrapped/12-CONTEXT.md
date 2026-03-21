# Phase 12: Chatbot Context Integration - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

The chatbot agents (QuantAssistant & FinancialAnalyst) gain awareness of what data the user is viewing — scraped metrics, analytics, regime results, stochastic model outputs — so they can give contextually grounded answers. This phase wires the existing page state into the /api/chat request on every message. New agents, persistent cross-session history, and new chat UI capabilities are out of scope.

</domain>

<decisions>
## Implementation Decisions

### What context gets sent
- **Scope**: Everything available — current tickers, all scraped metrics (P/E, RSI, EPS, sentiment, price, ROE), portfolio analytics (VaR, Sharpe, correlation, PCA), CNN Fear & Greed data, regime detection results, and full `_fundamental_analysis` per ticker
- **Non-stock tabs**: Yes — stochastic model results (Heston, regime, CIR, Markov, etc.) and RL tab outputs are included when available
- **Fundamentals depth**: Full `_fundamental_analysis` included — FinancialAnalyst especially benefits from earnings quality, revenue trends, and valuation analysis
- **Context size**: Truncate/summarise per ticker when many tickers present — cap per-ticker fields to the most important ones to keep payload manageable regardless of ticker count
- **Stochastic capture**: Each time a model runs (Heston, Regime, CIR, etc.), store its latest results in a shared `pageContext` object; chatbot gets whatever was last run

### Context trigger & timing
- **Trigger**: Always — every message sent includes the latest available page context automatically, no user action needed
- **Freshness**: Captured fresh on each message send (current page state at send time)
- **No-data state**: If nothing is scraped yet, chatbot works as a general assistant with no context injected — no error, no warning
- **Stochastic/RL capture**: Store last-run results per model in a shared context object; accumulated across the session per model type

### How agents use the context
- **Injection point**: Context appended to the agent's system prompt per request (not prepended to user message)
- **Format**: Structured plain text — readable, token-efficient (e.g., "Tickers: AAPL, MSFT\nAAPL: Price $185, P/E 28.4, RSI 62, Sentiment 0.72\n...")
- **Agent split**: Both agents receive the same context payload; their system prompt persona determines interpretation — Quant focuses on risk/models, FinancialAnalyst on fundamentals/macro
- **Chat history**: Include last N messages (last 10 messages / 5 turns) for multi-turn coherence — already partially in place from Phase 10.1

### User-visible context awareness
- **Indicator**: Subtle text line below the agent pill-tab toggle showing "Context: AAPL, MSFT" (or hidden when nothing loaded)
  ```
  [ QuantAssistant ] [ FinancialAnalyst ]
  Context: AAPL, MSFT
  ─────────────────────────────────
  [chat messages...]
  ```
- **Auto-greeting**: No — widget opens to existing history or default greeting; agent doesn't announce context unprompted
- **Context reset on new scrape**: Context silently updates when new scrape runs; chat history preserved
- **Error handling**: Generic error with retry offered ("Something went wrong. Please try again.") — same as current error handling, no change needed

### Claude's Discretion
- Exact field selection for per-ticker truncation (which fields are "most important" when capping)
- Exact plain-text serialisation format/template for the context block
- How stochastic results are stored in the shared context object (data structure)
- Backend field name for context parameter in /api/chat request body

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `static/js/chatbot.js`: `fetch('/api/chat', { method: 'POST', body: JSON.stringify({ message, agent }) })` — extend to include `context` field captured from page state
- `appendMessage()`, `appendTypingIndicator()`, `removeMessage()`, `renderMarkdown()`: All reusable as-is, no changes needed
- `static/js/state.js` AppState: `currentData` (ticker metrics), `currentCnnData`, `currentTickers`, `currentAnalytics` — primary source for stock analysis context
- `static/js/autoRun.js`: Regime detection results are stored in memory after auto-run — need to capture and expose on the shared context object
- `static/js/portfolioHealth.js`: Portfolio summary (VaR, Sharpe, regime labels) — accessible for context
- `static/js/stochasticModels.js`: Model run results (Heston IV, CIR yield curve, etc.) — need a "last result" store per model

### Established Patterns
- All widget/page state is in-memory JS variables (no localStorage, no server state) — same pattern for pageContext object
- Chat history already tracked per agent in `agentHistories` object — extend this pattern for context capture
- `/api/chat` at `webapp.py:1979-2048`: reads `data.get("message")` and `data.get("agent", "quant")` — extend to read `data.get("context", {})`

### Integration Points
- `webapp.py` `/api/chat` route: receives context payload, serialises to structured plain text, appends to system prompt before LLM call
- `chatbot.js` `sendMessage()` function: collects context snapshot from AppState + stochastic results store before each fetch call
- `chatbot.js` widget HTML template: add context indicator line below pill tabs (visible only when `currentTickers.length > 0`)
- `stochasticModels.js` + `autoRun.js`: add result capture hooks that write to shared `pageContext.stochasticResults` object on each model run

</code_context>

<specifics>
## Specific Ideas

- Context indicator line matches the widget's dark theme — muted/secondary text colour, not prominent
- Structured plain text format example:
  ```
  === Page Context ===
  Active tickers: AAPL, MSFT

  AAPL (Apple Inc.):
    Price: $185.20 | P/E: 28.4 | EPS: $6.52 | ROE: 147% | RSI: 62
    Sentiment: Overall 0.72 | News 0.68 | Reddit 0.58
    Regime: Bull | VaR (95%): -2.3%
    Fundamentals: [key points from _fundamental_analysis]

  MSFT (Microsoft Corp.):
    ...

  Portfolio:
    Sharpe: 1.42 | Correlation (AAPL↔MSFT): 0.78
    ...

  CNN Fear & Greed: 61 (Greed)
  ```

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-integrating-chatbot-to-the-details-in-stock-analysis-stochastic-models-tabs-etc-so-the-chatbot-can-access-the-content-scrapped*
*Context gathered: 2026-03-22*
