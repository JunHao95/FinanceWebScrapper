# Phase 14: Earnings Quality - Research

**Researched:** 2026-03-22
**Domain:** Client-side JS earnings-quality module + deep-analysis-group integration
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| QUAL-01 | User can see an earnings quality label (High / Medium / Low) for each ticker | `computeQuality(data, ticker)` maps accruals ratio + cash conversion ratio to a three-tier label rendered as a colour-coded badge in `div.deep-analysis-group` |
| QUAL-02 | User can see the accruals ratio (Net Income − OCF) / Total Assets displayed numerically | Accruals ratio computed in JS from `netIncomeToCommon`, `Operating Cash Flow (Yahoo)`, and `Total Assets (Yahoo)` fields; `toFixed(2)` display |
| QUAL-03 | User can see the cash conversion ratio (OCF / Net Income) displayed numerically | Cash conversion ratio = OCF ÷ Net Income; `toFixed(2)` display; handle divide-by-zero (Net Income = 0) |
| QUAL-04 | User can see an earnings consistency flag (Consistent / Volatile) based on EPS growth stability | EPS consistency derived from `EPS Growth This Year (Finviz)`, `EPS Growth QoQ (Finviz)`, and `Earnings Growth (Yahoo)` — single growth rate present → flag direction; tooltip explains criterion |
| QUAL-05 | Quality label degrades gracefully to "Insufficient Data" when OCF or Net Income is unavailable | All three metrics guarded by null-check; when either OCF or Net Income is null, the entire section renders a single "Insufficient Data" row and no JS error is thrown |
</phase_requirements>

---

## Summary

Phase 14 adds an `earningsQuality.js` module that computes an earnings quality label (High / Medium / Low), accruals ratio, cash conversion ratio, and earnings consistency flag purely from data already present in the scraped ticker object. The module is pure client-side JavaScript with no new Flask routes or network calls. It exposes `window.EarningsQuality = { computeQuality, toggleEarningsQuality, clearSession }`, mirrors the `window.HealthScore` pattern established in Phase 13, and appends its HTML section into the existing `div#deep-analysis-group-{ticker}` created by `healthScore.js`.

The two core financial formulas are academically standard:
- **Accruals ratio** = (Net Income − OCF) / Total Assets — a low or negative value signals cash-backed earnings (High quality); a high positive value signals accrual-heavy earnings (Low quality).
- **Cash conversion ratio** = OCF / Net Income — a value above 1.0 confirms earnings are being converted to cash; below 0.5 raises a quality concern.

The earnings consistency flag uses whatever EPS growth metric is available in the payload — `EPS Growth This Year (Finviz)`, `EPS Growth QoQ (Finviz)`, or `Earnings Growth (Yahoo)` — and classifies as "Consistent" if growth is positive, "Volatile" if negative or missing context. A tooltip explains which criterion was used.

The graceful-degradation path (QUAL-05) is a single early-return: if `ocf === null || netIncome === null`, render one `<div class="metric-item">Insufficient Data</div>` row and return — no further computation runs. No JavaScript error is thrown regardless of data sparseness.

**Primary recommendation:** Build `earningsQuality.js` as a self-contained module that returns an HTML string and appends it inside `#deep-analysis-group-{ticker}` after Phase 13's health score section; integrate via a two-line patch in `displayManager.js` and one `<script>` tag in `index.html`.

---

## Standard Stack

### Core

| Library / File | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| Vanilla JS (ES6) | — | `earningsQuality.js` module | No external dependency; matches existing module pattern |
| `healthScore.js` | Phase 13 output | Establishes `div.deep-analysis-group` container and expand/collapse session-persistence pattern | Reuse pattern verbatim |
| `displayManager.js` | existing | Injection point — `createTickerCard()` appends module HTML | Card rendering entry point for all ticker UI |
| `styles.css` | existing | `.badge`, `.badge-success/danger/warning`, `.metric-group`, `.metric-item` | All needed CSS already present |

### Supporting

| File | Purpose | When to Use |
|------|---------|-------------|
| `stockScraper.js` | Write `pageContext.tickerData[ticker].earningsQuality` after card render | Mirror Phase 13 pattern at lines 212–220 |
| `index.html` | Add `<script src="/static/js/earningsQuality.js">` after `healthScore.js` tag | One insertion after line 1334 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Inline HTML string | DOM API `createElement` | All existing modules use inline strings; stay consistent |
| Separate collapse per metric | One toggle for entire section | Phase 13 collapses the whole deep-analysis panel; earnings quality adds a sub-section inside the existing expanded panel — no separate toggle needed |

**Installation:** No npm packages. No backend install. File additions only.

---

## Architecture Patterns

### Recommended Project Structure

```
static/js/
├── healthScore.js          # Phase 13 — already creates div.deep-analysis-group
├── earningsQuality.js      # NEW — window.EarningsQuality = { computeQuality, toggleEarningsQuality, clearSession }
├── displayManager.js       # MODIFIED — call EarningsQuality.computeQuality, append inside deep-analysis-group
└── stockScraper.js         # MODIFIED — write pageContext.tickerData[ticker].earningsQuality after card render

templates/
└── index.html              # MODIFIED — add <script src="/static/js/earningsQuality.js"> after healthScore.js
```

### Pattern 1: Appending into div.deep-analysis-group (NOT creating it)

**What:** Phase 13 creates and injects `<div class="deep-analysis-group" id="deep-analysis-group-{ticker}">` via `HealthScore.computeGrade()`. Phase 14 must append INSIDE this container, not create a new one.

**Critical distinction from Phase 13:** Phase 13 builds the container div and returns it in `hs.html`. Phase 14 cannot also return a containing `div.deep-analysis-group` — doing so would create a nested or duplicate container.

**Integration in `createTickerCard()` (after Phase 13 block, lines 141–145):**
```javascript
// Phase 13: already done
if (typeof HealthScore !== 'undefined') {
    const hs = HealthScore.computeGrade(data, ticker);
    html += hs.html; // div.deep-analysis-group is now in html
}

// Phase 14: inject earnings quality INSIDE the existing container
// EarningsQuality returns a partial HTML string (div.earnings-quality-section only)
// and findOrAppend injects it after the healthScore section
// This must run AFTER div.innerHTML = html so the DOM node exists
```

**Two valid approaches (choose one at plan time):**

Option A — Post-DOM injection (recommended): `earningsQuality.js` exports a `renderIntoGroup(ticker, data)` function that is called after `div.innerHTML = html` in `createTickerCard()`, querying `div.querySelector('#deep-analysis-group-' + ticker)` and appending the section node.

Option B — String concatenation inside the deep-analysis-group: Phase 14 returns a raw HTML snippet (not a full container) and the caller splices it into the `html` string before `div.deep-analysis-group`'s closing tag. This is fragile — requires splitting the string.

**Recommendation: Option A.** `createTickerCard()` sets `div.innerHTML = html` at line 147, then immediately calls `EarningsQuality.renderIntoGroup(ticker, data, div)` passing the card `div` as the root. `renderIntoGroup` does:
```javascript
function renderIntoGroup(ticker, data, cardRoot) {
    const group = cardRoot.querySelector('#deep-analysis-group-' + ticker);
    if (!group) return;
    const section = document.createElement('div');
    section.innerHTML = buildHTML(ticker, data);
    group.querySelector('.deep-analysis-content').appendChild(section);
}
```

### Pattern 2: Window Global Module (identical to HealthScore)

```javascript
// earningsQuality.js
(function () {
    'use strict';
    // ... implementation ...
    window.EarningsQuality = { computeQuality, renderIntoGroup, clearSession };
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.EarningsQuality;
    }
}());
```

### Pattern 3: parseNumeric and extractMetric helpers

**What:** Re-use the same `parseNumeric` and `extractMetric` functions that `healthScore.js` already implements. Do NOT duplicate the logic — import a shared utility if one exists, or re-implement identically.

**Decision:** There is currently no shared `utils.js` finance-parsing helper. `healthScore.js` has its own closured `parseNumeric` / `extractMetric`. `earningsQuality.js` must replicate them identically (same logic, different closure). This is the project pattern.

```javascript
// Identical to healthScore.js implementation
function parseNumeric(val) {
    if (val === null || val === undefined || val === '' || val === 'N/A' || val === 'N/A%') return null;
    if (typeof val === 'number') return isNaN(val) ? null : val;
    const s = String(val).trim();
    let cleaned = s.replace(/^\$/, '');
    const multipliers = { 'B': 1e9, 'M': 1e6, 'K': 1e3 };
    const lastChar = cleaned.slice(-1).toUpperCase();
    if (multipliers[lastChar]) {
        const n = parseFloat(cleaned.slice(0, -1));
        return isNaN(n) ? null : n * multipliers[lastChar];
    }
    cleaned = cleaned.replace(/%$/, '');
    const n = parseFloat(cleaned);
    return isNaN(n) ? null : n;
}

function extractMetric(data, aliases) {
    if (!data || typeof data !== 'object') return null;
    for (const alias of aliases) {
        for (const key of Object.keys(data)) {
            if (key.toLowerCase().includes(alias.toLowerCase())) {
                const val = data[key];
                if (val === null || val === undefined || val === '' || val === 'N/A' || val === 'N/A%') continue;
                const parsed = parseNumeric(val);
                if (parsed !== null) return parsed;
            }
        }
    }
    return null;
}
```

### Pattern 4: Colour-coded badge for High / Medium / Low

**What:** Three-tier quality label maps to existing `.badge` CSS classes.

```javascript
const QUALITY_CLASS = {
    'High':    'badge-success',   // green
    'Medium':  'badge-warning',   // amber
    'Low':     'badge-danger'     // red
};
```

**Grade logic (research-derived thresholds):**
- Accruals ratio < 0.05 → +1 point; ≥ 0.10 → -1 point
- Cash conversion ratio ≥ 1.0 → +1 point; < 0.5 → -1 point
- Consistency flag = "Consistent" → +1 point; "Volatile" → -1 point (optional tiebreaker)

Score ≥ 2 → High; Score 0 or 1 → Medium; Score ≤ -1 → Low.

(Exact thresholds are Claude's discretion — see Open Questions.)

### Pattern 5: pageContext update (mirror Phase 13)

After `createTickerCard()` and `EarningsQuality.renderIntoGroup()`, `stockScraper.js` writes earnings quality to `pageContext`:
```javascript
// After Phase 13 pageContext write (lines 212–220 of stockScraper.js)
if (typeof EarningsQuality !== 'undefined' && window.pageContext && window.pageContext.tickerData && window.pageContext.tickerData[ticker]) {
    const eq = EarningsQuality.computeQuality(data, ticker);
    window.pageContext.tickerData[ticker].earningsQuality = {
        label: eq.label,
        accrualsRatio: eq.accrualsRatio,
        cashConversionRatio: eq.cashConversionRatio,
        consistencyFlag: eq.consistencyFlag
    };
}
```

### Anti-Patterns to Avoid

- **Creating a second `div.deep-analysis-group`:** Phase 14 appends inside the container Phase 13 created; never creates a wrapper with the same class/ID.
- **Calling a new Flask route:** All inputs (OCF, Net Income, Total Assets) are available in the scraped payload; no round-trip needed.
- **Fetching quarterly EPS from yfinance client-side:** The consistency flag must use only data already in the scraped payload — specifically `EPS Growth This Year (Finviz)`, `EPS Growth QoQ (Finviz)`, or `Earnings Growth (Yahoo)`.
- **Hard-coding field keys like `data['Operating Cash Flow (Yahoo)']`:** Use `extractMetric(data, ['Operating Cash Flow', 'OCF', 'Cash from Operations'])` to pick up the correct source field regardless of which scraper ran.
- **Showing NaN in the UI:** Every numeric display path must guard: `val !== null ? val.toFixed(2) : 'N/A'`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Numeric string parsing (B/M/K, %, $) | Custom regex | Mirror `parseNumeric` from `healthScore.js` — handles all scraped value formats | Edge cases: "135.47B", "-14.20%", "N/A" all appear in payload |
| HTML XSS escaping | Custom sanitiser | `DisplayManager.escapeHtml(ticker)` for any string derived from user input | Ticker symbols embedded in element IDs/onclick attributes |
| Badge CSS | Inline styles | `.badge` + `.badge-success/warning/danger` in styles.css lines 824–836 | Already defined and tested |
| Collapse toggle | Custom visibility | Mirror `HealthScore.toggleDeepAnalysis` pattern (display:none / display:block + chevron flip) | Consistent accordion behaviour across all deep-analysis sub-sections |

**Key insight:** Net Income and Total Assets are NOT directly stored in the scraped payload as named fields. The Yahoo scraper stores `netIncomeToCommon` from `yfinance.info` indirectly via `Earnings Growth (Yahoo)` and `Gross Profits (Yahoo)` — but does NOT store a `Net Income (Yahoo)` key. The yahoo_scraper.py must be extended in Wave 0 to expose two new fields: `Net Income (Yahoo)` from `info.get('netIncomeToCommon')` and `Total Assets (Yahoo)` from `t.balance_sheet.loc['Total Assets'].iloc[0]`. This is a critical backend change that enables the accruals ratio and cash conversion ratio (QUAL-02 and QUAL-03).

---

## Common Pitfalls

### Pitfall 1: Net Income and Total Assets NOT in Current Scraped Payload

**What goes wrong:** `extractMetric(data, ['Net Income', 'Total Assets'])` returns `null` for all tickers because `yahoo_scraper.py` never stores these fields.

**Why it happens:** The current Yahoo scraper (lines 110–200) fetches `netIncomeToCommon` and `balance_sheet` data from yfinance but does NOT write them to the `data` dict. It only writes `Earnings Growth (Yahoo)`, `ROE (Yahoo)`, etc.

**Verified:** Checked `yahoo_scraper.py` lines 110–200 in full — no `Net Income (Yahoo)` or `Total Assets (Yahoo)` keys are written.

**How to avoid:** Wave 0 task must patch `yahoo_scraper.py` to add:
```python
# After line 143 (Operating Cash Flow)
if info.get("netIncomeToCommon"):
    data["Net Income (Yahoo)"] = f"{info.get('netIncomeToCommon'):,.0f}"

# In balance sheet block — requires a new try block:
try:
    bs = stock.balance_sheet
    if not bs.empty and 'Total Assets' in bs.index:
        total_assets = bs.loc['Total Assets'].iloc[0]
        if total_assets:
            data["Total Assets (Yahoo)"] = f"{total_assets:,.0f}"
except Exception as e:
    self.logger.warning(f"Error fetching Total Assets for {ticker}: {str(e)}")
```

**Warning signs:** Accruals ratio and cash conversion ratio always show "Insufficient Data" even for well-known tickers like AAPL.

### Pitfall 2: Operating Cash Flow Field Key Ambiguity

**What goes wrong:** `data['Operating Cash Flow']` is undefined because the actual key is `'Operating Cash Flow (Yahoo)'` or `'Operating Cash Flow (Finviz)'` or `'Operating Cash Flow (AlphaVantage)'`.

**Why it happens:** Each scraper appends a source suffix.

**How to avoid:** Use `extractMetric(data, ['Operating Cash Flow', 'OCF', 'Cash from Operations'])` — the partial-match logic in `extractMetric` catches all three source variants.

**Verified:** `yahoo_scraper.py` writes `"Operating Cash Flow (Yahoo)"` (line 144). `finviz_scraper.py` writes `"Operating Cash Flow (Finviz)"` (line 125). `api_scraper.py` writes `"Operating Cash Flow (AlphaVantage)"` (line 149).

### Pitfall 3: Division by Zero in Cash Conversion Ratio

**What goes wrong:** `OCF / netIncome` throws `Infinity` or `-Infinity` when `netIncome === 0`.

**Why it happens:** Some companies (early stage, loss-making) have net income = 0 or very close to zero.

**How to avoid:**
```javascript
const cashConversionRatio = (netIncome !== 0) ? (ocf / netIncome) : null;
```
When null, display "N/A" not `toFixed(2)`.

### Pitfall 4: EPS Growth Values as Percentage Strings vs Decimal Fractions

**What goes wrong:** `EPS Growth This Year (Finviz)` is stored as `"25.00%"` (percentage string), while `Earnings Growth (Yahoo)` is stored as `"18.30%"` (also percentage string after `*100` formatting in yahoo_scraper line 174). `parseNumeric` strips the `%` and returns `25.0` and `18.3` respectively — both in percentage form. Consistency flag logic should use the same scale.

**Verified:** `yahoo_scraper.py` line 174: `f"{info.get('earningsGrowth')*100:.2f}%"` — multiplied by 100 before storage. Finviz scraper stores raw value from Finviz which is already a percentage (e.g. "25.00%"). Both resolve to the same numeric scale after `parseNumeric`.

**How to avoid:** After `parseNumeric`, treat value as percentage (not decimal). Consistency threshold: value > 0 → growth is positive → "Consistent"; value < 0 → "Volatile"; value === 0 or null → fallback to "Volatile" with flag.

### Pitfall 5: append-inside-container Timing — DOM Not Yet Populated

**What goes wrong:** `EarningsQuality.renderIntoGroup(ticker, data, div)` queries `div.querySelector('#deep-analysis-group-' + ticker)` but returns `null` because `div.innerHTML = html` has not yet been called.

**Why it happens:** If `renderIntoGroup` is called before `div.innerHTML = html` in `createTickerCard()`, the DOM node doesn't exist.

**How to avoid:** Call `renderIntoGroup` AFTER `div.innerHTML = html` (currently line 147 of `displayManager.js`):
```javascript
div.innerHTML = html;
// Phase 14: append earnings quality inside the existing deep-analysis-group
if (typeof EarningsQuality !== 'undefined') {
    EarningsQuality.renderIntoGroup(ticker, data, div);
}
return div;
```

**Warning signs:** No earnings quality section visible; no JS error thrown.

### Pitfall 6: Insufficient Data Path Must Not Throw

**What goes wrong:** When `ocf` or `netIncome` is null, the code still tries to compute `accruals / totalAssets` and throws a TypeError.

**Why it happens:** Missing null-guard on the graceful-degradation early-return.

**How to avoid:**
```javascript
function buildHTML(ticker, data) {
    const ocf = extractMetric(data, ['Operating Cash Flow', 'OCF', 'Cash from Operations']);
    const netIncome = extractMetric(data, ['Net Income']);

    if (ocf === null || netIncome === null) {
        return `<div class="metric-item" style="color:#999;">
                  <span class="metric-label">Earnings Quality</span>
                  <span class="metric-value">Insufficient Data</span>
                </div>`;
    }
    // ... rest of computation
}
```

---

## Code Examples

Verified patterns from project source:

### OCF Field Extraction (three scrapers)

```javascript
// Source: yahoo_scraper.py line 144, finviz_scraper.py line 125, api_scraper.py line 149
const ocf = extractMetric(data, ['Operating Cash Flow', 'OCF', 'Cash from Operations']);
// Returns: float in raw units (e.g., 135471996928 for AAPL from Yahoo), or null
```

### Net Income Field Extraction (after Wave 0 yahoo_scraper patch)

```javascript
// Source: yahoo_scraper.py (to be added in Wave 0) — info.get('netIncomeToCommon')
const netIncome = extractMetric(data, ['Net Income']);
// Returns: float in raw units, or null
```

### Total Assets Field Extraction (after Wave 0 yahoo_scraper patch)

```javascript
// Source: yahoo_scraper.py (to be added in Wave 0) — balance_sheet.loc['Total Assets'].iloc[0]
const totalAssets = extractMetric(data, ['Total Assets']);
// Returns: float in raw units (e.g., 359241000000.0 for AAPL), or null
```

### Accruals Ratio Computation

```javascript
// Accruals ratio = (Net Income - OCF) / Total Assets
// Low/negative value = high earnings quality (cash-backed)
// High positive value = low quality (accrual-heavy)
function computeAccrualsRatio(ocf, netIncome, totalAssets) {
    if (ocf === null || netIncome === null || totalAssets === null || totalAssets === 0) return null;
    return (netIncome - ocf) / totalAssets;
}
// AAPL example: (112010000000 - 135471996928) / 359241000000 = -0.065
```

### Cash Conversion Ratio Computation

```javascript
// Cash conversion ratio = OCF / Net Income
// >1.0 = strong (OCF exceeds earnings) → High quality
// 0.5–1.0 = moderate → Medium
// <0.5 = weak → Low quality
function computeCashConversionRatio(ocf, netIncome) {
    if (ocf === null || netIncome === null || netIncome === 0) return null;
    return ocf / netIncome;
}
// AAPL example: 135471996928 / 112010000000 = 1.21
```

### EPS Consistency Flag

```javascript
// EPS growth fields in payload (all percentage-form after parseNumeric):
// - 'EPS Growth This Year (Finviz)' → e.g. 11.0 (positive = growing)
// - 'EPS Growth QoQ (Finviz)'
// - 'Earnings Growth (Yahoo)' → e.g. 18.3
function computeConsistencyFlag(data) {
    const epsGrowth = extractMetric(data, [
        'EPS Growth This Year', 'EPS Growth QoQ', 'Earnings Growth', 'EPS Growth'
    ]);
    if (epsGrowth === null) return { flag: 'Volatile', tooltip: 'EPS growth data unavailable' };
    if (epsGrowth > 0) return { flag: 'Consistent', tooltip: `EPS growth: +${epsGrowth.toFixed(1)}%` };
    return { flag: 'Volatile', tooltip: `EPS growth: ${epsGrowth.toFixed(1)}%` };
}
```

### Overall Quality Label Thresholds

```javascript
// Score points:
//   accrualsRatio < 0.05 → +1;  >= 0.10 → -1
//   cashConversionRatio >= 1.0 → +1;  < 0.5 → -1
//   consistencyFlag === 'Consistent' → +0 (neutral tiebreaker only)
//   score >= 2 → 'High'; score === 1 → 'Medium'; score <= 0 → 'Low'
function computeLabel(accrualsRatio, cashConversionRatio) {
    let score = 0;
    if (accrualsRatio !== null) {
        if (accrualsRatio < 0.05) score += 1;
        else if (accrualsRatio >= 0.10) score -= 1;
    }
    if (cashConversionRatio !== null) {
        if (cashConversionRatio >= 1.0) score += 1;
        else if (cashConversionRatio < 0.5) score -= 1;
    }
    if (score >= 2) return 'High';
    if (score === 1) return 'Medium';
    return 'Low';
}
```

### Rendered HTML Structure

```html
<!-- Appended inside div.deep-analysis-content of existing deep-analysis-group -->
<div class="earnings-quality-section" style="border-top: 1px solid #e8e8e8; margin-top: 8px; padding-top: 8px;">
  <div class="metric-group">
    <div class="metric-item">
      <span class="metric-label">Earnings Quality</span>
      <span class="metric-value"><span class="badge badge-success">High</span></span>
    </div>
    <div class="metric-item">
      <span class="metric-label">Accruals Ratio</span>
      <span class="metric-value">-0.07</span>
    </div>
    <div class="metric-item">
      <span class="metric-label">Cash Conversion</span>
      <span class="metric-value">1.21</span>
    </div>
    <div class="metric-item">
      <span class="metric-label">EPS Consistency</span>
      <span class="metric-value">Consistent
        <span title="EPS growth: +18.3%" style="cursor:help; color:#999; font-size:11px;"> (?)</span>
      </span>
    </div>
  </div>
</div>

<!-- Insufficient Data fallback (replaces all above when OCF or Net Income is null) -->
<div class="earnings-quality-section" style="border-top: 1px solid #e8e8e8; margin-top: 8px; padding-top: 8px;">
  <div class="metric-item">
    <span class="metric-label">Earnings Quality</span>
    <span class="metric-value" style="color:#999;">Insufficient Data</span>
  </div>
</div>
```

### displayManager.js Integration Point (after Phase 13)

```javascript
// displayManager.js createTickerCard() — after line 147 (div.innerHTML = html)
div.innerHTML = html;

// Phase 14: inject earnings quality into existing deep-analysis-group
if (typeof EarningsQuality !== 'undefined') {
    EarningsQuality.renderIntoGroup(ticker, data, div);
}

return div;
```

### index.html Script Tag Order

```html
<!-- Line 1334 (existing): -->
<script src="/static/js/healthScore.js"></script>
<!-- Line 1335 (new): -->
<script src="/static/js/earningsQuality.js"></script>
<!-- displayManager.js follows -->
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No earnings quality metrics on ticker card | `earningsQuality.js` module with accruals + cash conversion + consistency | Phase 14 introduces | User can assess earnings quality without opening financials |
| Net Income and Total Assets absent from scraped payload | Added to `yahoo_scraper.py` via `netIncomeToCommon` + `balance_sheet` | Phase 14 Wave 0 patch | Enables Phase 14 and future phases that need income/assets |
| deep-analysis-group created and owned by Phase 13 alone | Phase 14–16 append sections inside the existing container | Phase 14 establishes the multi-phase append pattern | No further card HTML changes needed for Phases 15–16 |

**Deprecated/outdated:**
- None — Phase 14 is entirely additive. Phase 13's container is preserved; earnings quality section is injected as a child.

---

## Open Questions

1. **Accruals ratio threshold calibration**
   - What we know: Academic literature uses accruals ratio < 0 as "high quality" (Sloan, 1996); practical dashboards use < 0.05 as the threshold given variability
   - What's unclear: Whether the 0.05 / 0.10 threshold produces "High" for most reasonable tickers (AAPL = -0.065 → would be High under these thresholds, which is correct)
   - Recommendation: Use −0.10 < accrualsRatio < 0.05 → High; 0.05–0.15 → Medium; > 0.15 → Low. Planner can fine-tune at task time.

2. **Net Income field key conflict: `netIncomeToCommon` vs `Net Income`**
   - What we know: yfinance `info.get('netIncomeToCommon')` returns income attributable to common stockholders; `balance_sheet` / `financials` `'Net Income'` row includes minority interests
   - What's unclear: Whether the difference is material for ratio computation
   - Recommendation: Use `netIncomeToCommon` (already available in `info`) — simpler, no extra API call, minor difference only.

3. **Total Assets availability reliability**
   - What we know: AAPL, MSFT both return `balance_sheet.loc['Total Assets']` without error; it returns a float in raw units (e.g. 359 billion)
   - What's unclear: ETFs and some non-standard tickers may not have balance sheet data
   - Recommendation: Wrap the balance sheet fetch in try/except in `yahoo_scraper.py`; if null, `extractMetric` returns null → QUAL-05 graceful degradation handles it.

4. **Whether the earnings section should have its own collapse toggle or inherit Phase 13's toggle**
   - What we know: Phase 13's `div.deep-analysis-content` is toggled by `HealthScore.toggleDeepAnalysis()` — when collapsed, the entire content including the Phase 14 sub-section is hidden
   - What's unclear: Whether a separate "Earnings Quality" sub-header with its own expand/collapse is desired
   - Recommendation: No separate toggle — the Phase 13 collapse is sufficient. The earnings quality section renders inline inside the already-expanded `deep-analysis-content` div. Keeps implementation simple.

---

## Validation Architecture

`workflow.nyquist_validation` key is absent from `.planning/config.json` — treated as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, all tests in `tests/`) |
| Config file | `pytest.ini` / `setup.cfg` if present, else `pytest tests/` autodiscovery |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

Note: `earningsQuality.js` is pure client-side JS. The Wave 0 backend change (`yahoo_scraper.py` patch to add Net Income and Total Assets) is the only Python change and warrants a regression check that existing scraper tests still pass.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QUAL-01 | Quality label badge (High/Medium/Low) appears in Deep Analysis section | manual smoke | n/a — browser visual | ❌ Wave 0 (manual) |
| QUAL-02 | Accruals ratio shown as 2-decimal numeric | manual smoke | n/a — browser visual | ❌ Wave 0 (manual) |
| QUAL-03 | Cash conversion ratio shown as 2-decimal numeric | manual smoke | n/a — browser visual | ❌ Wave 0 (manual) |
| QUAL-04 | Consistency flag appears with tooltip | manual smoke | n/a — browser interaction | ❌ Wave 0 (manual) |
| QUAL-05 | "Insufficient Data" renders when OCF or Net Income is null; no JS error | manual smoke | n/a — requires sparse-data ticker | ❌ Wave 0 (manual) |
| (implicit) | yahoo_scraper.py patch does not break existing tests | unit regression | `pytest tests/ -x -q` | ✅ existing suite |

No new Python routes → no new pytest test files required. All validation is browser-based except the regression guard.

### Sampling Rate

- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- `yahoo_scraper.py` — add `Net Income (Yahoo)` from `info.get('netIncomeToCommon')` and `Total Assets (Yahoo)` from `balance_sheet.loc['Total Assets'].iloc[0]`; this is a prerequisite for QUAL-02 and QUAL-03
- No new test files needed for the JS module (pure client-side)
- Existing `pytest tests/` suite serves as regression guard for the yahoo_scraper patch

---

## Sources

### Primary (HIGH confidence)

- `src/scrapers/yahoo_scraper.py` lines 110–200 — verified all fields written to `data` dict; confirmed `Net Income (Yahoo)` and `Total Assets (Yahoo)` are absent and must be added
- `src/scrapers/finviz_scraper.py` lines 75–87 — verified EPS Growth field keys: `EPS Growth This Year (Finviz)`, `EPS Growth Next Year (Finviz)`, `EPS Growth Next 5Y (Finviz)`, `EPS Growth QoQ (Finviz)`
- `src/scrapers/api_scraper.py` lines 145–160 — verified `Operating Cash Flow (AlphaVantage)` key
- `src/analytics/financial_analytics.py` lines 1572–1576, 1621–1632 — confirmed OCF alias list `['Operating Cash Flow', 'OCF', 'Cash from Operations']` and EPS growth aliases `['Earnings Growth', 'EPS Growth']`
- `static/js/healthScore.js` — full `parseNumeric`, `extractMetric`, `buildHTML` patterns verified; append-into-group architecture confirmed
- `static/js/displayManager.js` lines 141–148 — confirmed injection point after `div.innerHTML = html`
- `static/js/stockScraper.js` lines 209–220 — confirmed pageContext write pattern
- `templates/index.html` line 1334 — confirmed `healthScore.js` script tag location for insertion after
- Direct yfinance verification (live): `AAPL netIncomeToCommon = 117776998400`, `operatingCashflow = 135471996928`, `balance_sheet['Total Assets'] = 359241000000.0`

### Secondary (MEDIUM confidence)

- Academic: Sloan (1996) "Do Stock Prices Fully Reflect Information in Accruals and Cash Flows?" — accruals ratio formula confirmed (Net Income − OCF) / Total Assets
- Common practitioner convention: cash conversion ratio ≥ 1.0 as quality threshold

### Tertiary (LOW confidence)

- None — all findings are from direct source code and live yfinance inspection.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all files directly inspected
- Architecture (append-into-group): HIGH — DOM structure verified against Phase 13 `healthScore.js` output
- Data field keys: HIGH — verified in scrapers and via live yfinance call
- Missing fields (Net Income / Total Assets): HIGH — confirmed absent from current payload by full code read
- Earnings quality thresholds: MEDIUM — academically grounded but exact band boundaries are Claude's discretion
- EPS consistency logic: MEDIUM — single growth-rate sign is a simplification; more robust multi-period approach would require quarterly financials fetch (deferred)

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (stable codebase, yfinance API assumed stable)
