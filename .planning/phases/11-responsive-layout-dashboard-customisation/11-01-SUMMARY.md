---
phase: 11-responsive-layout-dashboard-customisation
plan: 01
status: complete
---

## What was done

Added three responsive CSS breakpoints and collapse/utility classes to `static/css/styles.css`.

### Changes
- Expanded `@media (max-width: 768px)` block: added pill/icon button `width: auto` resets (`.ticker-badge`, `.mode-btn`, `.chip-remove`, `.drawer-close-btn`, `.settings-gear-btn`) and allocation input row wrap rules
- Added `@media (max-width: 1024px)` block: tightens `.input-section` and `.main-tabs` padding to 20px
- Added `@media (max-width: 480px)` block: phone layout — body padding, header sizing, inner tab bar horizontal scroll + scrollbar hiding, main tab bar scrollbar hiding, chatbot toggle 44px, chatbot window `calc(100vw - 20px)`, allocation rows single column, analysis/option-results grids 1-column
- Added `.section-header`, `.section-chevron`, `.section-body`, `.section-body.collapsed` CSS classes for collapse toggle system (Plans 02 depends on these)
- Added `.table-scroll-wrap` utility class (always-on overflow-x auto wrapper)

## Verification passed
- `@media (max-width: 480px)` present
- `@media (max-width: 1024px)` present
- `.section-body.collapsed` with `max-height: 0` present
- `.table-scroll-wrap` present
