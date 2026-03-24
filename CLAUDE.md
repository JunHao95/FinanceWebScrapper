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
