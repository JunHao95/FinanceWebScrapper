# Phase 13: Financial Health Score - Research

**Researched:** 2026-03-22
**Domain:** Client-side JS scoring module + displayManager.js integration
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Deep Analysis section starts **collapsed** — only the section header with letter grade is visible inline (e.g., "🏥 Financial Health: B  ▼")
- User clicks to expand and see four sub-scores + one-sentence explanation
- Collapsed state shows: letter grade + section label (no sub-scores visible)
- Expand/collapse state is **persisted per session** — if a user expanded AAPL's Deep Analysis, it stays expanded until a new scrape runs
- Card placement: `div.deep-analysis-group` appended **inside** the existing `.ticker-content` div, after the metrics grid, at the bottom of each ticker card
- Score is computed **synchronously inside `createTickerCard()`** (displayManager.js) — no async, no loading placeholder
- All required fields are available in the scraped data object at render time
- Health score results (grade, sub-scores, explanation) are **also added to `pageContext`** so the FinancialAnalyst chatbot (Phase 12) can reference them
- New **`healthScore.js`** module — pure JS, client-side, no backend round-trip
- Exposed as `window.HealthScore = { computeGrade }` — consistent with DisplayManager, AutoRun, PortfolioHealth pattern
- **No new Flask route needed** for Phase 13
- Four equal-weight sub-scores (25% each): **Liquidity, Leverage, Profitability, Growth**
- Each sub-score maps to a letter (A=4, B=3, C=2, D=1, F=0)
- Overall grade = average of four numeric scores, mapped back to A–F
- Use same scoring thresholds as `financial_analytics.py` for consistency (lines ~1457–1632)
- When a field is missing: sub-score still computed from available metrics with a warning flag (FHLTH-04)

### Claude's Discretion

- Exact numeric thresholds for each sub-score band (mirror `financial_analytics.py` logic)
- Raw metric value display within each sub-score row (whether to show "Liquidity: B — Current Ratio 1.8" or just "Liquidity: B")
- Exact CSS for the collapsed header and expanded panel (reuse `.badge` and `.metric-group` patterns)
- Element IDs and CSS class names for the deep-analysis-group and its children
- Exact wording template for the one-sentence explanation (e.g., "Strong {positive factor} offset by {negative factor}")

### Deferred Ideas (OUT OF SCOPE)

- User-adjustable sub-score weights (sliders) — future phase or v2.2 enhancement
- Historical grade trend (how the grade changed over multiple scrapes) — requires persistence, out of scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FHLTH-01 | User can see a composite financial health grade (A–F) for each ticker on its stock card | `computeGrade(data)` returns `{ grade, subScores, explanation, warnings }` — letter grade badge rendered in collapsed header of `div.deep-analysis-group` |
| FHLTH-02 | User can see the four component sub-scores (liquidity, leverage, profitability, growth) that make up the overall grade | Expandable panel reveals four `.metric-group`-style rows, each showing sub-score letter and contributing raw values |
| FHLTH-03 | User can see a brief explanation of what drove the grade (e.g., "strong ROE offset by high debt/equity") | `computeGrade` collects the top positive driver and top negative driver during scoring; explanation string assembled from those |
| FHLTH-04 | Score degrades gracefully when any single component is missing — partial score shown with a warning flag | Per-sub-score null handling: if no metrics found for a dimension, sub-score = null, grade computed from available dimensions only, warning flag `⚠` appended to affected row label |
</phase_requirements>

---

## Summary

Phase 13 adds a `healthScore.js` module that computes a composite A–F grade purely from data already present in the scraped ticker object. The module is pure client-side JavaScript with no new Flask routes or network calls. It exposes `window.HealthScore = { computeGrade }`, which `displayManager.js` calls synchronously inside `createTickerCard()`. The returned HTML string is wrapped in a `div.deep-analysis-group` container that is appended after the metrics grid inside `.ticker-content`; Phases 14–16 will append their own sections to this same container.

The scoring algorithm mirrors the thresholds already present in `src/analytics/financial_analytics.py` (`_analyze_profitability`, `_analyze_financial_health`, `_analyze_growth`). Each of the four sub-scores (Liquidity, Leverage, Profitability, Growth) maps to a numeric value (A=4, B=3, C=2, D=1, F=0); the overall grade is the floor-average of available dimensions. All badge styling reuses `.badge`, `.badge-success`, `.badge-danger`, `.badge-warning`, and `.badge-info` classes already defined in `styles.css` lines 824–836. The expand/collapse pattern follows the same `collapsed` CSS class toggle used by the ticker card header in `DisplayManager.toggleTicker()`.

The `pageContext.healthScores[ticker]` field is written in `stockScraper.js` after `createTickerCard()` completes, carrying `{ grade, subScores, explanation }` for chatbot consumption.

**Primary recommendation:** Build `healthScore.js` as a self-contained scoring module that returns an HTML string; integrate via a two-line change in `displayManager.js` and a one-line `<script>` tag in `index.html`.

---

## Standard Stack

### Core

| Library / File | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| Vanilla JS (ES6) | — | `healthScore.js` module | No external dependency needed; pattern matches existing modules |
| `displayManager.js` | existing | Injection point for `div.deep-analysis-group` | Card rendering entry point for all ticker UI |
| `styles.css` | existing | `.badge`, `.badge-success/danger/warning/info`, `.metric-group` | All needed CSS already present |
| `financial_analytics.py` | existing | Source of truth for scoring thresholds | Ensures frontend grade matches backend fundamental analysis |

### Supporting

| File | Purpose | When to Use |
|------|---------|-------------|
| `stockScraper.js` | Write `pageContext.healthScores[ticker]` after card render | After `createTickerCard()` call in `displayResults()` |
| `index.html` | Add `<script src="/static/js/healthScore.js">` | One insertion before `displayManager.js` script tag |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Inline HTML string construction | DOM API (`createElement`) | Existing `displayManager.js` uses inline strings; stay consistent |
| Separate CSS file | Inline styles | Existing badge/metric classes are sufficient; no new CSS file needed |

**Installation:** No npm packages. No backend install. File additions only.

---

## Architecture Patterns

### Recommended Project Structure

```
static/js/
├── healthScore.js          # NEW — window.HealthScore = { computeGrade }
├── displayManager.js       # MODIFIED — call HealthScore.computeGrade, append div.deep-analysis-group
└── stockScraper.js         # MODIFIED — write pageContext.healthScores after card render

templates/
└── index.html              # MODIFIED — add <script src="/static/js/healthScore.js"> before displayManager.js
```

### Pattern 1: Window Global Module

**What:** Pure-object literal assigned to `window.HealthScore` — identical to `window.PortfolioHealth`, `window.AutoRun`, `window.DisplayManager`.

**When to use:** Always for new client-side modules in this project.

**Example (from portfolioHealth.js lines 1–3, 234–235):**
```javascript
// portfolioHealth.js — established pattern
// Exposes: window.PortfolioHealth = { initCard, updateRegime }
...
window.PortfolioHealth = { initCard, updateRegime, getRegimeMap, getTickerList };
```

`healthScore.js` must follow the identical structure:
```javascript
// healthScore.js
// Exposes: window.HealthScore = { computeGrade }
const HealthScore = {
    computeGrade(data) { ... }
};
window.HealthScore = HealthScore;
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HealthScore;
}
```

### Pattern 2: Inline HTML String Construction

**What:** `displayManager.js` builds card HTML as a string concatenation then assigns to `div.innerHTML`. `healthScore.js` returns a self-contained HTML string that the caller appends.

**When to use:** When integrating new sections into `createTickerCard()`.

**Example (from displayManager.js lines 106–141):**
```javascript
html += '<div class="metrics-grid">';
// ... group loops ...
html += '</div>';
div.innerHTML = html;
```

Integration change in `createTickerCard()`:
```javascript
html += '</div>'; // closes metrics-grid

// Phase 13: append deep-analysis-group
if (typeof HealthScore !== 'undefined') {
    const healthResult = HealthScore.computeGrade(data);
    html += healthResult.html; // div.deep-analysis-group included
}

div.innerHTML = html;
```

### Pattern 3: Collapsed Section with Per-Section Toggle

**What:** Section header is clickable; an `onclick` calls a toggle function that adds/removes `'collapsed'` on the sibling content div. Session persistence is achieved by storing expanded state in a `Map` or plain object keyed by `ticker + sectionName`.

**When to use:** For the Deep Analysis collapsed header and all sub-sections in Phases 13–16.

**Existing toggle in displayManager.js (lines 249–263):**
```javascript
toggleTicker(contentId) {
    const content = document.getElementById(contentId);
    const header = content?.previousElementSibling;
    if (!content || !header) return;
    const isCollapsed = content.classList.contains('collapsed');
    if (isCollapsed) {
        content.classList.remove('collapsed');
        header.classList.remove('collapsed');
    } else {
        content.classList.add('collapsed');
        header.classList.add('collapsed');
    }
}
```

The deep-analysis toggle needs its own version (or reuse of the same class-toggle logic) with a unique content ID per ticker, e.g., `deep-analysis-content-AAPL`.

**Session persistence approach:** Store expanded tickers in a module-level `Set` inside `healthScore.js`. On re-render (new scrape), clear the set. On toggle, add/remove ticker from set. On initial render, check set to decide whether to add `'collapsed'` class.

### Pattern 4: Badge Grade Colour Mapping

**What:** Map A–F letter grade to the existing CSS badge variant.

**CSS already in styles.css (lines 824–836):**
```css
.badge           { display:inline-block; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:bold; color:white; }
.badge-success   { background: #27ae60; }  /* A — green */
.badge-danger    { background: #e74c3c; }  /* F — red */
.badge-warning   { background: #f39c12; }  /* C/D — amber/orange */
.badge-info      { background: #3498db; }  /* B — blue */
```

Grade-to-class mapping (Claude's discretion):
```javascript
const GRADE_CLASS = {
    'A': 'badge-success',
    'B': 'badge-info',
    'C': 'badge-warning',
    'D': 'badge-warning',  // orange styling can be applied inline
    'F': 'badge-danger'
};
```

### Pattern 5: pageContext Update

**What:** After `createTickerCard()` is called for each ticker, `stockScraper.js` writes additional computed fields to `pageContext.tickerData[ticker]`. Health score follows the same pattern as `fundamentals` which is written at lines 134–147 of `stockScraper.js`.

**Integration in stockScraper.js `displayResults()`:**
```javascript
// After the createTickerCard loop
for (const [ticker, data] of Object.entries(result.data)) {
    const tickerDiv = DisplayManager.createTickerCard(ticker, data);
    tickerResultsDiv.appendChild(tickerDiv);
    // Phase 13: write health score to pageContext
    if (typeof HealthScore !== 'undefined' && window.pageContext && window.pageContext.tickerData) {
        const hs = HealthScore.computeGrade(data);
        window.pageContext.tickerData[ticker].healthScore = {
            grade: hs.grade,
            subScores: hs.subScores,
            explanation: hs.explanation
        };
    }
}
```

### Anti-Patterns to Avoid

- **Calling `computeGrade` async or with a loading placeholder:** The scoring is synchronous — no placeholders needed.
- **Creating a new Flask route:** All data is already in the browser payload. No round-trip needed.
- **New CSS classes for badge colours:** Existing `.badge-success/danger/warning/info` cover A–F. Avoid adding duplicates.
- **Hardcoding ticker symbol inside `healthScore.js`:** The module is stateless for computation — ticker context lives in `displayManager.js`.
- **Writing to `pageContext` inside `healthScore.js`:** Keep the module pure. The caller (`stockScraper.js`) writes pageContext.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Numeric metric parsing | Custom string-to-float | Mirror `_parse_numeric_value` logic from `financial_analytics.py` — handle %, $, B/M/K suffixes | Edge cases: "1.5B", "25.3%", "N/A" all appear in scraped data |
| HTML escaping | None needed for computed values | Metric display values are floats or null; only string labels need escaping — use `DisplayManager.escapeHtml()` if needed | XSS risk with user-entered ticker strings |
| Badge CSS | Inline background styles | `.badge` + `.badge-success/danger/warning/info` in styles.css:824–836 | Already defined and tested |
| Collapse behaviour | Custom visibility toggle | Same `collapsed` CSS class toggle used by `DisplayManager.toggleTicker()` | Consistent with existing accordion pattern |

**Key insight:** The hardest part of this module is field key aliasing — the scraped payload uses display-friendly names like "Current Ratio", "Debt/Equity", "ROE". The `_extract_metric` pattern in `financial_analytics.py` (partial lowercase match across all data keys) is the safest approach to replicate in JS.

---

## Common Pitfalls

### Pitfall 1: Field Key Name Mismatches

**What goes wrong:** `data['Current Ratio']` returns `undefined` because the scraper writes the field under a slightly different key (e.g., "Current Ratio (MRQ)" or "Current Ratio %" from different sources).

**Why it happens:** Data is aggregated from multiple sources (Yahoo Finance, Finviz, Google). Each uses different labelling.

**How to avoid:** Use a multi-alias lookup identical to `financial_analytics.py`'s `_extract_metric`. For each metric, provide an array of possible key substrings and do a case-insensitive partial match across all keys in the data object.

```javascript
function extractMetric(data, aliases) {
    for (const alias of aliases) {
        const lower = alias.toLowerCase();
        for (const key of Object.keys(data)) {
            if (key.toLowerCase().includes(lower)) {
                const val = data[key];
                if (val !== null && val !== undefined && val !== 'N/A' && val !== 'N/A%') {
                    return parseNumeric(val); // returns float or null
                }
            }
        }
    }
    return null;
}
```

**Warning signs:** Sub-scores all showing N/A for real tickers with known data.

### Pitfall 2: Division by Zero / Empty Sub-Score Average

**What goes wrong:** If all four sub-scores are null (very sparse data), the average computation divides by zero.

**Why it happens:** Graceful degradation path not fully handled — checking `subScores.length > 0` before division is required.

**How to avoid:**
```javascript
const available = subScores.filter(s => s.numericScore !== null);
const overallNumeric = available.length > 0
    ? available.reduce((sum, s) => sum + s.numericScore, 0) / available.length
    : null;
```

When `overallNumeric` is null, render "N/A" for the grade with a `⚠` warning on every row.

**Warning signs:** "NaN" appearing in the grade badge or sub-score rows.

### Pitfall 3: Container ID Collision Across Tickers

**What goes wrong:** Phases 14–16 use `document.querySelector('.deep-analysis-group')` and pick up the wrong ticker's container.

**Why it happens:** Phase 13 must create a per-ticker unique ID on `div.deep-analysis-group` so later phases can target `#deep-analysis-group-AAPL` specifically.

**How to avoid:** Use `id="deep-analysis-group-${ticker}"` on the container div. The `div.deep-analysis-group` class is used for styling; the ID is used for targeting.

**Warning signs:** Phase 14 earnings section appearing inside the wrong ticker card.

### Pitfall 4: Session State Lost on Re-Scrape

**What goes wrong:** User expands AAPL Deep Analysis, re-scrapes, the section re-renders collapsed (losing session state).

**Why it happens:** `createTickerCard()` rebuilds HTML from scratch on each scrape.

**How to avoid:** Store the set of expanded tickers in a module-level variable inside `healthScore.js`. Check it during HTML generation to conditionally omit `'collapsed'` from the content div. Clear the set when a new scrape starts (hook into `stockScraper.js` before `displayResults()`).

**Warning signs:** Expanded section always resets to collapsed after scrape.

### Pitfall 5: Percentage vs Raw Values in Scraped Data

**What goes wrong:** ROE is stored as `"25.3"` (percentage already) or `"0.253"` (decimal fraction) depending on the source. Applying the `> 20` threshold to `0.253` gives wrong grade.

**Why it happens:** Yahoo Finance returns some ratios as decimals; Finviz returns them as percentage strings.

**How to avoid:** The `parseNumeric` helper strips `%` and `$` but cannot distinguish decimal-vs-percentage. Mirror `financial_analytics.py` behaviour: the `_parse_numeric_value` method strips `%` then returns the raw float. Thresholds in `_analyze_profitability` use `> 20` for ROE which implies the value is already in percentage form (e.g., 25.3 not 0.253). Accept the same assumption — the scraper normalises to percentage before storing.

**Warning signs:** All tickers getting grade A or grade F uniformly.

---

## Code Examples

Verified patterns from project source:

### Scoring Thresholds (from financial_analytics.py — verified)

**Liquidity sub-score inputs:**
- `_extract_metric(data, ['Current Ratio'])` — threshold: > 2.0 → strong, < 1.0 → concern
- `_extract_metric(data, ['Quick Ratio'])` — threshold: > 1.5 → strong, < 0.5 → concern

**Leverage sub-score inputs:**
- `_extract_metric(data, ['Debt to Equity', 'D/E', 'Debt/Equity', 'Debt-to-Equity', 'Total Debt/Equity'])` — threshold: < 0.5 → strong, > 2.0 → concern

**Profitability sub-score inputs:**
- `_extract_metric(data, ['ROE', 'Return on Equity', 'Return On Equity', 'ROE %'])` — threshold: > 20 → excellent, > 15 → strong, < 5 → low
- `_extract_metric(data, ['Profit Margin', 'Net Margin', 'Net Profit Margin'])` — threshold: > 20 → high, < 0 → unprofitable
- `_extract_metric(data, ['ROA', 'Return on Assets'])` — threshold: > 10 → strong, < 2 → concern

**Growth sub-score inputs:**
- `_extract_metric(data, ['Revenue Growth', 'Sales Growth'])` — threshold: > 20 → exceptional, > 10 → strong, < 0 → declining
- `_extract_metric(data, ['Earnings Growth', 'EPS Growth'])` — threshold: > 15 → strong, < 0 → declining

### Sub-Score to Letter Grade Mapping

A–F bands (Claude's discretion — mapping 0–10 score range to A–F):

```javascript
// Source: financial_analytics.py uses 0–10 scale; A–F boundary choice is discretionary
function scoreToLetter(score) {
    if (score === null) return null;
    if (score >= 8.0) return 'A';
    if (score >= 6.5) return 'B';
    if (score >= 5.0) return 'C';
    if (score >= 3.5) return 'D';
    return 'F';
}
```

Overall numeric score = average of available sub-score numeric values (0–4 scale):
```
A=4, B=3, C=2, D=1, F=0
```
Map average back to letter using same band boundaries.

### createTickerCard Integration Point

Current end of card HTML construction in `displayManager.js` (lines 135–141):
```javascript
        html += '</div>'; // closes metrics-grid
        div.innerHTML = html;
        return div;
```

After Phase 13, the injection becomes:
```javascript
        html += '</div>'; // closes metrics-grid

        if (typeof HealthScore !== 'undefined') {
            const hs = HealthScore.computeGrade(data);
            html += hs.html; // injects div.deep-analysis-group
        }

        div.innerHTML = html;
        return div;
```

### div.deep-analysis-group HTML Structure

```html
<div class="deep-analysis-group" id="deep-analysis-group-AAPL">
  <!-- Collapsed header -->
  <div class="deep-analysis-header collapsed"
       onclick="HealthScore.toggleDeepAnalysis('AAPL')">
    <span>🏥 Financial Health: <span class="badge badge-info">B</span></span>
    <span class="collapse-icon">▼</span>
  </div>
  <!-- Expandable panel -->
  <div class="deep-analysis-content collapsed" id="deep-analysis-content-AAPL">
    <div class="metric-group">
      <div class="metric-item">
        <span class="metric-label">Liquidity</span>
        <span class="metric-value"><span class="badge badge-success">A</span> — CR 2.1 / QR 1.6</span>
      </div>
      <div class="metric-item">
        <span class="metric-label">Leverage</span>
        <span class="metric-value"><span class="badge badge-warning">C</span> — D/E 1.8</span>
      </div>
      <div class="metric-item">
        <span class="metric-label">Profitability</span>
        <span class="metric-value"><span class="badge badge-success">A</span> — ROE 26% / Margin 25%</span>
      </div>
      <div class="metric-item">
        <span class="metric-label">Growth ⚠</span>
        <span class="metric-value"><span class="badge badge-info">B</span></span>
      </div>
    </div>
    <p class="deep-analysis-explanation">Strong ROE offset by high debt/equity.</p>
  </div>
</div>
```

### window.HealthScore Public API

```javascript
// computeGrade(data) → {
//   grade: 'A'|'B'|'C'|'D'|'F'|null,
//   subScores: [
//     { name: 'Liquidity', letter: 'A', numericScore: 4, rawValues: { currentRatio: 2.1, quickRatio: 1.6 }, missing: false },
//     { name: 'Leverage',  letter: 'C', numericScore: 2, rawValues: { debtEquity: 1.8 }, missing: false },
//     { name: 'Profitability', letter: 'A', numericScore: 4, rawValues: { roe: 26, profitMargin: 25 }, missing: false },
//     { name: 'Growth',    letter: 'B', numericScore: 3, rawValues: { revenueGrowth: 12 }, missing: true },
//   ],
//   explanation: 'Strong ROE offset by high debt/equity.',
//   warnings: ['Growth data incomplete'],
//   html: '<div class="deep-analysis-group" ...>...</div>'
// }
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No per-ticker deep analysis UI | `div.deep-analysis-group` container pattern | Phase 13 introduces | Phases 14–16 can append without touching card HTML |
| Fundamental analysis only in backend (Flask) | Client-side scoring in `healthScore.js` | Phase 13 | Zero latency, no network call |
| pageContext only has sentiment + fundamentals summary | pageContext gets `healthScores[ticker]` | Phase 13 | Chatbot can cite health grade in responses |

**Deprecated/outdated:**
- None — Phase 13 is entirely additive.

---

## Open Questions

1. **Exact D/E ratio scale in scraped data**
   - What we know: `financial_analytics.py` thresholds treat D/E as a ratio (e.g., 1.8 means 1.8x debt-to-equity, not 180%)
   - What's unclear: Whether Finviz/Yahoo returns it as a ratio or percentage in the scraped payload for this project
   - Recommendation: At plan time, verify by inspecting a live scrape of a known ticker (e.g., AAPL D/E ~1.7) — if the raw value is ~1.7, use ratio thresholds; if ~170, convert.

2. **`ticker-content collapsed` CSS — does `.collapsed` hide content?**
   - What we know: `displayManager.js` adds/removes `'collapsed'` class on both header and content divs; the `ticker-header.collapsed` and `ticker-content.collapsed` selectors must have CSS rules.
   - What's unclear: Exact CSS for `.ticker-content.collapsed { display: none }` or similar — not checked in styles.css.
   - Recommendation: Reuse the same `collapsed` class and CSS rule for `.deep-analysis-content.collapsed`. If the existing CSS already hides `.collapsed` elements, no new CSS is needed.

---

## Validation Architecture

`workflow.nyquist_validation` is not present in `.planning/config.json` (key absent) — treated as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, all tests in `tests/`) |
| Config file | `setup.py` (setuptools-based; pytest configured via `pytest.ini` or `setup.cfg` if present) |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

Note: `healthScore.js` is pure client-side JS. No Python backend is added in Phase 13. Unit tests for the scoring logic would require a JS test framework (none currently present). The practical validation approach is:

1. **Manual smoke test:** Scrape AAPL → verify grade badge appears in card, sub-scores expand, explanation text renders.
2. **Missing-data test:** Scrape a ticker known to have sparse data → verify `⚠` flag appears and grade still renders.
3. **pageContext test:** After scrape, open browser console → `window.pageContext.tickerData['AAPL'].healthScore` should be `{ grade, subScores, explanation }`.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FHLTH-01 | Grade badge appears in ticker card | manual smoke | n/a — browser visual | ❌ Wave 0 (manual) |
| FHLTH-02 | Four sub-scores expand when clicked | manual smoke | n/a — browser interaction | ❌ Wave 0 (manual) |
| FHLTH-03 | Explanation sentence appears in expanded panel | manual smoke | n/a — browser visual | ❌ Wave 0 (manual) |
| FHLTH-04 | Missing-data warning flag `⚠` shown; grade still renders | manual smoke | n/a — requires live scrape | ❌ Wave 0 (manual) |

No new Python routes → no new pytest test files required for Phase 13. All validation is browser-based.

### Sampling Rate

- **Per task commit:** `pytest tests/ -x -q` (existing suite, guards against regressions)
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- No new test files needed (pure JS, no backend changes)
- Existing `pytest tests/` suite serves as regression guard only

---

## Sources

### Primary (HIGH confidence)

- `src/analytics/financial_analytics.py` lines 1457–1641 — scoring thresholds for all four dimensions verified directly
- `static/js/displayManager.js` — `createTickerCard()` structure, HTML injection point, `toggleTicker()` collapse pattern
- `static/js/portfolioHealth.js` lines 1–5, 234–235 — `window.PortfolioHealth` exposure pattern
- `static/js/stockScraper.js` lines 109–154 — `pageContext` write pattern
- `static/css/styles.css` lines 654–673, 824–836 — `.metric-group`, `.metric-item`, `.badge` classes
- `templates/index.html` lines 1330–1346 — existing `<script>` load order

### Secondary (MEDIUM confidence)

- `.planning/phases/13-financial-health-score/13-CONTEXT.md` — all implementation decisions confirmed from user discussion

### Tertiary (LOW confidence)

- None — all findings are from direct source code inspection.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all files directly inspected
- Architecture patterns: HIGH — verified against existing module conventions
- Pitfalls: HIGH — derived from direct code inspection (field name aliasing, null handling, ID uniqueness)
- Scoring thresholds: HIGH — copied verbatim from `financial_analytics.py`

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (stable codebase, no external dependencies)
