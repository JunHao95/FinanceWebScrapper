---
phase: 11-responsive-layout-dashboard-customisation
plan: 03
status: complete
---

## What was done

Added `scrollIntoView` to tabs.js, wrapped multi-column tables in peerComparison.js and optionsDisplay.js, updated README.md.

### Changes

**tabs.js**
- `switchTab`: added `scrollIntoView({ behavior: 'smooth', inline: 'nearest', block: 'nearest' })` after `classList.add('active')` for each of 4 tab branches (stocks, analytics, autoanalysis, tradingindicators)
- `switchMainTab`: added same `scrollIntoView` call after `targetButton.classList.add('active')` inside `if (targetButton)` guard
- Total: 5 `scrollIntoView` calls added

**peerComparison.js**
- `rawTable` string wrapped in `<div class="table-scroll-wrap">...</div>`
- `display:none` remains on the inner `<table>` — `toggleRawPeers` uses `querySelector('.peer-raw-table')` which still works

**optionsDisplay.js**
- Convergence details `<table>` wrapped in `<div class="table-scroll-wrap">...</div>`

**README.md**
- Added "Responsive Layout & Dashboard Customisation (Phase 11)" section under Features

## Verification passed
- `scrollIntoView` count in tabs.js = 5
- `table-scroll-wrap` in peerComparison.js = 1
- `table-scroll-wrap` in optionsDisplay.js = 1
- README.md references "responsive" and "Phase 11"
