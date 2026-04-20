# Project Instructions

## Git Workflow

- All feature work is done on a dedicated branch (e.g. `feature/phase-X-slug`).
- **Before executing any phase or feature work, ask the user:**
  "What branch name should I use for this work? (e.g. `feature/phase-15-dcf-valuation`)"
  Then run: `git checkout -b <branch-name>` (or `git checkout <branch-name>` if it already exists).
  Do NOT begin any code changes until the branch is confirmed.
- When a phase is complete, **do NOT merge the feature branch into `main` automatically.**
  - Stop and ask: "Phase work is complete on `<branch-name>`. Please review the changes in VSCode Source Control (or run `git diff main..<branch-name>`), then give the green light to merge into `main`."
  - Only run `git checkout main && git merge <branch-name>` after the user explicitly confirms.
- **Do NOT push to `origin main` without explicit approval from the user.**
  - After merging to local `main`, stop and ask: "Merged into local `main` — please confirm you're ready to push to `origin/main`."
  - Only run `git push origin main` after the user confirms.

## Test Requirements

- **Every new feature or bug fix must include corresponding tests committed in the same PR/branch.**
  - For new analytics functions: add unit tests in `tests/test_unit_<module>.py` covering at least one happy-path and one edge-case with deterministic (non-network) inputs.
  - For new Flask routes: add integration tests in `tests/test_integration_routes.py` verifying HTTP status, response schema, and error handling for invalid inputs.
  - For indicator logic changes: add or update regression tests in `tests/test_regression_indicators.py` or `tests/test_regression_stochastic.py` with pinned expected values.
  - Run `pytest` (or `make test`) before committing and confirm all tests pass.
- Do NOT commit feature/fix code without the accompanying tests staged alongside it.

## README Updates

- **Before every commit that introduces a new feature or bug fix, update `README.md`** to reflect the change.
  - For new features: add a brief description under the relevant section (e.g. Features, Usage) capturing what was added and why it matters.
  - For bug fixes: update any affected documentation (e.g. known limitations, usage notes) if the fix changes observable behavior.
  - Keep updates concise — one to three sentences is usually enough to capture the essence.
- Do NOT commit feature/fix code without first staging the `README.md` update alongside it.
