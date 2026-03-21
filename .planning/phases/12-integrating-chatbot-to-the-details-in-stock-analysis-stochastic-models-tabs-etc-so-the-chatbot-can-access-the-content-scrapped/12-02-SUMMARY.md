---
plan: "12-02"
phase: "12"
status: complete
completed: 2026-03-22
---

# Plan 12-02: Extend /api/chat with Context + History

## What was built

Extended `webapp.py /api/chat` to read `context` and `history` from the POST body, assemble an `effective_system_prompt` with context appended, and inject history turns between the system message and current user message in both Groq and Ollama branches. All 6 tests pass (TDD GREEN).

## Key files

### Modified
- `webapp.py` — `/api/chat` route now reads `page_context`, `history`; builds `effective_system_prompt` and `history_messages`

## Test results (GREEN)

```
PASSED  test_chat_financial_agent
PASSED  test_chat_default_agent_backward_compat
PASSED  test_chat_unknown_agent_fallback
PASSED  test_chat_with_context   (CTX-01 ✓)
PASSED  test_chat_no_context     (CTX-02 ✓)
PASSED  test_chat_with_history   (CTX-03 ✓)
```

## Commits

- `92e80e6` — feat(12-02): extend /api/chat with context + history injection

## Decisions

- Used inline role mapping `("assistant" if sender == "bot" else "user")` over a helper function to minimise diff
- Capped history at last 10 turns as safety measure
- Applied same change to both Groq and Ollama branches
