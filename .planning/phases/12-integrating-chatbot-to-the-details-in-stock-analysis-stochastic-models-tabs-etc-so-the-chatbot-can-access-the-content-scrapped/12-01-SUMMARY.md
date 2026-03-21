---
plan: "12-01"
phase: "12"
status: complete
completed: 2026-03-22
---

# Plan 12-01: TDD Test Scaffold (Context + History Injection)

## What was built

Extended `tests/test_chat_route.py` with three unit tests specifying the backend behaviour for CTX-01, CTX-02, CTX-03. Tests are in TDD RED state — 2/3 fail because the backend hasn't been extended yet.

## Key files

### Modified
- `tests/test_chat_route.py` — added `test_chat_with_context`, `test_chat_no_context`, `test_chat_with_history`

## Test results (expected RED state)

```
PASSED  test_chat_financial_agent
PASSED  test_chat_default_agent_backward_compat
PASSED  test_chat_unknown_agent_fallback
FAILED  test_chat_with_context   (CTX-01 — not yet implemented)
PASSED  test_chat_no_context     (CTX-02 — baseline trivially satisfied)
FAILED  test_chat_with_history   (CTX-03 — not yet implemented)
```

## Commits

- `5058ba7` — test(12-01): add failing unit tests for context + history injection

## Notes

`test_chat_no_context` passes in RED state because the backend currently never appends context, so the assertion "=== Page Context ===" not in system_content is trivially true. This test will continue to pass after Plan 02 implementation (correct baseline behaviour).
