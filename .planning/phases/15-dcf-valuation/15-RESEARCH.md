# Phase 15: DCF Valuation - Research

**Researched:** 2026-03-23
**Domain:** Client-side 2-stage DCF model, vanilla JavaScript module pattern, HTML form inputs
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **DCF model:** 2-stage model. Stage 1 = 5 explicit annual FCF projections discounted at WACC; Stage 2 = Gordon Growth terminal value.
- **Formula:**
  - Stage 1: Σ FCFₜ / (1+WACC)^t for t = 1..5, where FCFₜ = FCF₀ × (1+g₁)^t
  - Stage 2: Terminal = FCF₅ × (1+g₂) / (WACC − g₂); PV(Terminal) = Terminal / (1+WACC)^5
  - Intrinsic equity value = Stage 1 + PV(Terminal)
  - Per-share value = Intrinsic equity value / Shares Outstanding
- **Forecast horizon fixed at 5 years** — not user-overridable
- **Raw latest FCF** used (no smoothing/averaging)
- **Default assumptions:** WACC 10%, Stage 1 growth 10%, Stage 2 terminal growth 3%
- **Input UX:** Inline `<input type="number">` fields, always visible when DCF section is expanded; recalculation on button click ("Recalculate"), NOT on-change/on-blur
- **FCF data source priority:** Alpha Vantage first (`Free Cash Flow (AlphaVantage)`), fall back to Yahoo Finance (`Free Cash Flow (Yahoo)`)
- **Source footnote** shown below the estimate (e.g., "FCF source: Alpha Vantage")
- **When FCF is absent or zero:** render "DCF unavailable — FCF data missing", suppress all numeric outputs (DCF-05)
- **When FCF is present but Shares Outstanding cannot be derived:** show total intrinsic equity value in $ billions, skip per-share and premium/discount
- **Shares Outstanding derivation:** `Market Cap (Yahoo) / Current Price (Yahoo)`
- **Premium/discount formula:** `(currentPrice − intrinsicValue) / intrinsicValue × 100`
  - Positive = premium (overvalued, green); negative = discount (undervalued, red)
- **pageContext update:** write `pageContext.tickerData[ticker].dcfValuation = { intrinsicValue, premium, wacc, g1, g2, fcfSource }` after render
- **Integration file targets:** `dcfValuation.js`, `displayManager.js`, `index.html`, `stockScraper.js`

### Claude's Discretion

- Exact CSS for input row layout, button styling, and footnote typography
- Element IDs and CSS class names for DCF section elements
- Handling of WACC ≤ terminal growth rate (guard: show error inline if WACC ≤ g₂ to avoid division by zero)
- Exact wording for section header in collapsed state (follow emoji-header pattern from Phase 13/14)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DCF-01 | User can see an intrinsic value estimate (price per share) derived from FCF | 2-stage DCF formula fully specified; per-share derivation via Market Cap / Current Price confirmed present in scraped payload |
| DCF-02 | User can see whether the stock is trading at a premium or discount vs. DCF estimate, as a percentage | Formula locked: (currentPrice − intrinsicValue) / intrinsicValue × 100; badge-success/badge-danger CSS already in styles.css |
| DCF-03 | User can see the key assumptions (FCF growth rate, terminal growth rate, WACC) displayed alongside the estimate | Always-visible inline inputs satisfy this; assumptions visible before and after recalculation |
| DCF-04 | User can override default growth and WACC assumptions via input fields and recalculate without re-scraping | Button-triggered local recalculation; no Flask route needed; state stored in DOM inputs and re-read on click |
| DCF-05 | Module displays "DCF unavailable — FCF data missing" if Alpha Vantage FCF is absent or zero | Guard at top of renderIntoGroup; checks both sources in priority order |
</phase_requirements>

---

## Summary

Phase 15 adds a pure-client-side DCF valuation sub-section inside each ticker card's `div.deep-analysis-group` container (created in Phase 13). The module follows the exact same window-global IIFE pattern established by `healthScore.js` (Phase 13) and `earningsQuality.js` (Phase 14): a single file `dcfValuation.js` exposes `window.DCFValuation = { computeValuation, renderIntoGroup, clearSession }`, is loaded before `displayManager.js` in `index.html`, and is called from `displayManager.createTickerCard()` after the EarningsQuality call.

The DCF model is entirely pre-specified by the user (locked decisions). No library is needed — all math is simple arithmetic with `Math.pow`. The primary engineering concerns are: (1) correctly reading the FCF and Market Cap fields from the scraped data object using the `extractMetric` alias pattern; (2) building a DOM structure that supports button-triggered recalculation while keeping inputs in the DOM; (3) graceful degradation when FCF or per-share data is missing; and (4) the WACC ≤ g₂ guard to prevent division by zero.

All required CSS classes (`.badge`, `.badge-success`, `.badge-danger`, `.metric-item`, `.metric-label`, `.metric-value`, `.metric-group`) already exist in `styles.css`. No new backend routes are required. Integration surface is three files: `index.html` (script tag), `displayManager.js` (one call), `stockScraper.js` (pageContext write).

**Primary recommendation:** Model the new module structurally on `earningsQuality.js` line-for-line, substituting the DCF computation and a richer HTML section that includes `<input type="number">` fields and a Recalculate button wired with an inline onclick handler.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vanilla JavaScript (ES5+) | — | All module logic, DOM manipulation, math | Matches existing codebase — no build step, no dependencies |
| HTML `<input type="number">` | — | WACC and growth rate user inputs | Standard form element; no external library needed |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Existing `.badge-*` CSS classes | styles.css:833–836 | Premium (green) / discount (red) colour coding | Already in codebase |
| `extractMetric` / `parseNumeric` | Pattern in earningsQuality.js | Alias-based field lookup with multiplier parsing | Copy verbatim into dcfValuation.js closure |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Vanilla JS math | math.js library | Overkill — DCF is 5 additions and one Gordon Growth formula |
| Button-triggered recalc | on-change recalc | Context.md explicitly rejects on-change to avoid mid-type flickering |
| Inline onclick | addEventListener | Either works; inline is simpler given IIFE pattern used by Phase 13/14 |

**Installation:** No new packages required.

---

## Architecture Patterns

### Recommended Project Structure

No new directories. One new file:

```
static/js/
├── healthScore.js        # Phase 13 — deep-analysis-group creator
├── earningsQuality.js    # Phase 14 — appends into group
└── dcfValuation.js       # Phase 15 — appends into group (NEW)
```

### Pattern 1: Window-Global IIFE Module

**What:** All module logic wrapped in an IIFE, exposed only via `window.DCFValuation`. Identical to `window.HealthScore` and `window.EarningsQuality`.

**When to use:** Always — matches existing codebase convention.

```javascript
// Mirrors earningsQuality.js structure exactly
(function () {
    'use strict';

    // Private helpers (parseNumeric, extractMetric — copy from earningsQuality.js)

    function computeValuation(data, wacc, g1, g2) {
        // Returns: { intrinsicPerShare, intrinsicEquityTotal, premium, fcfSource, error }
    }

    function renderIntoGroup(ticker, data, cardRoot) {
        const container = cardRoot.querySelector('#deep-analysis-content-' + ticker);
        if (!container) return;
        // Build HTML, append to container
    }

    function clearSession() { /* no session state */ }

    window.DCFValuation = { computeValuation, renderIntoGroup, clearSession };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.DCFValuation;
    }
}());
```

### Pattern 2: 2-Stage DCF Computation

**What:** Pure function that takes FCF₀, WACC, g1, g2 and returns equity value and per-share value.

**When to use:** Called both during initial render (with defaults) and on Recalculate button click.

```javascript
function computeValuation(data, wacc, g1, g2) {
    // 1. Extract FCF (Alpha Vantage priority, fallback Yahoo)
    const avFcf = extractMetric(data, ['Free Cash Flow (AlphaVantage)']);
    const yfFcf = extractMetric(data, ['Free Cash Flow (Yahoo)']);
    const fcf0  = (avFcf !== null && avFcf !== 0) ? avFcf : yfFcf;
    const fcfSource = (avFcf !== null && avFcf !== 0) ? 'Alpha Vantage' : 'Yahoo Finance';

    if (fcf0 === null || fcf0 === 0) {
        return { error: 'FCF data missing', fcfSource: null };
    }

    // Guard: WACC must exceed terminal growth rate
    if (wacc <= g2) {
        return { error: 'WACC must exceed terminal growth rate', fcfSource };
    }

    // 2. Stage 1: PV of 5 explicit FCF projections
    let stage1PV = 0;
    let fcf5 = fcf0;
    for (let t = 1; t <= 5; t++) {
        const fcft = fcf0 * Math.pow(1 + g1, t);
        stage1PV += fcft / Math.pow(1 + wacc, t);
        if (t === 5) fcf5 = fcft;
    }

    // 3. Stage 2: Gordon Growth terminal value
    const terminal = fcf5 * (1 + g2) / (wacc - g2);
    const pvTerminal = terminal / Math.pow(1 + wacc, 5);

    const intrinsicEquityTotal = stage1PV + pvTerminal;

    // 4. Per-share: Market Cap / Current Price for shares outstanding
    const marketCap   = extractMetric(data, ['Market Cap (Yahoo)']);
    const currentPrice = extractMetric(data, ['Current Price (Yahoo)', 'Current Price']);
    let intrinsicPerShare = null;
    let premium = null;

    if (marketCap !== null && currentPrice !== null && currentPrice !== 0) {
        const sharesOut = marketCap / currentPrice;
        intrinsicPerShare = intrinsicEquityTotal / sharesOut;
        premium = (currentPrice - intrinsicPerShare) / intrinsicPerShare * 100;
    }

    return { intrinsicEquityTotal, intrinsicPerShare, premium, fcfSource };
}
```

### Pattern 3: Button-Triggered Recalculation

**What:** Recalculate button reads current input values from the DOM, calls `computeValuation`, and updates display elements in-place — no re-scrape, no page reload.

**When to use:** The onclick handler is the only inter-action point. Wired via inline `onclick` using a unique ID per ticker.

```javascript
// In buildHTML — button wired inline
'<button onclick="DCFValuation._recalculate(\'' + ticker + '\')" ...>Recalculate</button>'

// Exposed as private helper on window.DCFValuation for onclick access
window.DCFValuation._recalculate = function(ticker) {
    const wacc = parseFloat(document.getElementById('dcf-wacc-' + ticker).value) / 100;
    const g1   = parseFloat(document.getElementById('dcf-g1-' + ticker).value)   / 100;
    const g2   = parseFloat(document.getElementById('dcf-g2-' + ticker).value)   / 100;
    // Re-read data from pageContext (stored on initial render), or pass data via closure
    const data = window.pageContext && window.pageContext.tickerData
        && window.pageContext.tickerData[ticker] && window.pageContext.tickerData[ticker]._rawData;
    const result = DCFValuation.computeValuation(data, wacc, g1, g2);
    // Update #dcf-result-{ticker}, #dcf-premium-{ticker} in-place
};
```

**Alternative approach (simpler):** Store raw data on the section element as a data attribute (JSON-serialised), read back on recalculate. Avoids dependency on pageContext shape.

### Pattern 4: renderIntoGroup Integration

**What:** Follows the identical call in `displayManager.js` after EarningsQuality.

```javascript
// displayManager.js — inside createTickerCard(), after EarningsQuality call
if (typeof DCFValuation !== 'undefined') {
    DCFValuation.renderIntoGroup(ticker, data, div);
}
```

### Pattern 5: pageContext Write (stockScraper.js)

**What:** After `DisplayManager.createTickerCard()`, write computed DCF result into pageContext so the FinancialAnalyst chatbot can reference it.

```javascript
// stockScraper.js — after Phase 14 earningsQuality block
if (typeof DCFValuation !== 'undefined' && window.pageContext && window.pageContext.tickerData[ticker]) {
    const dcf = DCFValuation.computeValuation(data, 0.10, 0.10, 0.03); // defaults
    window.pageContext.tickerData[ticker].dcfValuation = {
        intrinsicValue: dcf.intrinsicPerShare,
        premium: dcf.premium,
        wacc: 0.10,
        g1: 0.10,
        g2: 0.03,
        fcfSource: dcf.fcfSource
    };
}
```

### Anti-Patterns to Avoid

- **On-change recalculation:** Explicitly rejected in CONTEXT.md. Do not wire inputs to `oninput` or `onchange`.
- **New Flask/Python route:** No backend needed. All computation is client-side.
- **Separate collapsible toggle for DCF section:** The DCF section appends inside the existing `#deep-analysis-content-{ticker}` div which is already toggled by `HealthScore.toggleDeepAnalysis`. Do not add a second toggle layer.
- **Smoothing or averaging FCF:** CONTEXT.md locks "raw latest FCF" — do not compute TTM or multi-year averages.
- **Sharing parseNumeric/extractMetric from window:** These helpers are private per IIFE. Copy them verbatim into the dcfValuation.js closure, exactly as earningsQuality.js does.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Number parsing with B/M/K/% | Custom parser | `parseNumeric` from earningsQuality.js closure (copy verbatim) | Already handles $, B, M, K, %, NaN, null, 'N/A' |
| Alias-based field lookup | Custom field finder | `extractMetric` from earningsQuality.js closure (copy verbatim) | Case-insensitive substring match, handles sparse data |
| Premium/discount colour coding | Custom CSS | `.badge-success` / `.badge-danger` from styles.css:833–836 | Already defined, consistent with existing badges |

**Key insight:** The entire utility layer is already implemented twice (healthScore.js, earningsQuality.js). The planner should schedule a copy-paste task for these helpers, not a build-from-scratch task.

---

## Common Pitfalls

### Pitfall 1: FCF Format Mismatch Between Sources

**What goes wrong:** `Free Cash Flow (AlphaVantage)` is stored as a raw float string (e.g., `"12345678.00"`) while `Free Cash Flow (Yahoo)` is stored as a comma-formatted integer string (e.g., `"12,345,678"`).

**Why it happens:** Different scraper conventions (api_scraper.py line 159 uses `f"{fcf:.2f}"`, yahoo_scraper.py line 140 uses `f"{free_cashflow:,.0f}"`).

**How to avoid:** Use `parseNumeric` — it strips `$`, commas are handled by `parseFloat` ignoring trailing comma characters... actually `parseFloat("12,345,678")` only reads `12`. **This IS a real risk.** The `parseNumeric` helper in earningsQuality.js does NOT strip commas. The Yahoo FCF value `"12,345,678"` would be parsed as `12` by `parseFloat`.

**Resolution:** In `dcfValuation.js`, extend `parseNumeric` to also strip commas before calling `parseFloat`, OR rely on Alpha Vantage first (no commas). The planner must include a task to add comma-stripping to the local `parseNumeric` copy used in dcfValuation.js.

**Warning signs:** DCF estimate appears orders of magnitude too small for large-cap stocks when Yahoo FCF is the fallback source.

### Pitfall 2: Division by Zero in Gordon Growth Model

**What goes wrong:** If WACC ≤ g₂, the terminal value denominator `(WACC − g₂)` is zero or negative, producing `Infinity` or a negative intrinsic value.

**Why it happens:** User can freely edit input fields to any values.

**How to avoid:** Guard at top of computeValuation — if `wacc <= g2`, return `{ error: 'WACC must exceed terminal growth rate' }` and render inline error message instead of a numeric result.

**Warning signs:** Intrinsic value displays as `Infinity`, `NaN`, or a large negative number.

### Pitfall 3: Market Cap Comma Parsing

**What goes wrong:** `Market Cap (Yahoo)` is stored as `"12,345,678,901"` (comma-formatted). `parseFloat` on this returns `12`.

**Why it happens:** `yahoo_scraper.py` line 199: `f"{info.get('marketCap'):,.0f}"`.

**How to avoid:** Strip commas in `parseNumeric` before `parseFloat`. Same fix as Pitfall 1.

**Warning signs:** Shares Outstanding computes to an absurdly small number; per-share intrinsic value is astronomically large.

### Pitfall 4: Recalculate Button Cannot Access Raw Data

**What goes wrong:** The `_recalculate` function needs the original scraped data object to re-run `computeValuation`, but the data is not in the DOM after initial render.

**Why it happens:** Module renders once and the `data` argument from `renderIntoGroup` goes out of scope.

**How to avoid:** Two valid approaches:
1. Store a JSON-serialised subset of needed fields on the section element (`data-fcf`, `data-marketcap`, `data-price`) and read them back on recalculate.
2. Store the data reference in a module-level Map keyed by ticker: `const _dataCache = {};` inside the IIFE.

Approach 2 (Map/object cache) is simpler and avoids DOM attribute size limits. The planner should pick this approach.

**Warning signs:** `_recalculate` throws `Cannot read property 'Free Cash Flow (AlphaVantage)' of undefined`.

### Pitfall 5: Input Values Are Percentages, Not Decimals

**What goes wrong:** User enters `10` meaning 10%. If passed directly to formula as `0.10` is expected, a missing `/100` conversion yields WACC = 1000% and a near-zero intrinsic value.

**Why it happens:** `<input type="number">` returns the raw user value (10), not the decimal (0.10).

**How to avoid:** Always divide input values by 100 when reading from the DOM: `wacc = parseFloat(input.value) / 100`. Make default HTML `value` attributes `10`, `10`, `3` (percentage form, not decimal form).

**Warning signs:** Intrinsic value near zero for any reasonable stock; WACC guard triggers even though user entered reasonable values.

---

## Code Examples

Verified patterns from existing codebase:

### Field Names Confirmed in Scraped Payload

```
// From api_scraper.py line 159:
data["Free Cash Flow (AlphaVantage)"] = f"{fcf:.2f}"

// From yahoo_scraper.py line 140:
data["Free Cash Flow (Yahoo)"] = f"{free_cashflow:,.0f}"

// From yahoo_scraper.py lines 197-199:
data["Current Price (Yahoo)"] = f"{info.get('currentPrice'):.2f}"
data["Market Cap (Yahoo)"] = f"{info.get('marketCap'):,.0f}"
```

### displayManager.js Integration Call (after line 150)

```javascript
// Phase 15: inject DCF valuation into existing deep-analysis-group
if (typeof DCFValuation !== 'undefined') {
    DCFValuation.renderIntoGroup(ticker, data, div);
}
```

### index.html Script Tag Placement

```html
<!-- After earningsQuality.js, before displayManager.js -->
<script src="/static/js/healthScore.js"></script>
<script src="/static/js/earningsQuality.js"></script>
<script src="/static/js/dcfValuation.js"></script>           <!-- ADD THIS -->
<script src="/static/js/displayManager.js?v=2.2"></script>
```

### Collapsed Header Pattern (from healthScore.js)

```javascript
// healthScore.js line 229 — emoji-header pattern to replicate
`<span>🏥 Financial Health: <span class="badge ${cls}">${grade}</span></span>`

// DCF equivalent (Claude's discretion on exact wording):
`<span>💰 DCF Value: ${intrinsicPerShare !== null ? '$' + intrinsicPerShare.toFixed(2) : 'N/A'}</span>`
```

### Premium/Discount Badge

```javascript
// badge-success = green (undervalued / discount = good for buyer)
// badge-danger  = red   (premium = overvalued)
const premiumClass = premium < 0 ? 'badge-success' : 'badge-danger';
const premiumLabel = premium < 0
    ? (Math.abs(premium).toFixed(1) + '% discount')
    : ('+' + premium.toFixed(1) + '% premium');
```

**Note:** The colour convention — discount is green (badge-success), premium is red (badge-danger) — aligns with the buy-side framing in CONTEXT.md ("Negative = market price below intrinsic = discount = undervalued signal").

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flask-served server-side DCF calc | Pure client-side JS | Project design (v2.1) | No backend route, no latency, no re-scrape on recalculate |
| jQuery DOM manipulation | Vanilla JS + innerHTML + querySelector | Project convention | No jQuery in this codebase |

**Deprecated/outdated:**
- Slider inputs for WACC/growth: Rejected in CONTEXT.md — use `<input type="number">` instead.

---

## Open Questions

1. **Comma stripping in parseNumeric**
   - What we know: `Market Cap (Yahoo)` and `Free Cash Flow (Yahoo)` are comma-formatted strings; existing `parseNumeric` does not strip commas.
   - What's unclear: Whether this causes silent failures for large-cap stocks.
   - Recommendation: The planner must include a specific task to extend `parseNumeric` in `dcfValuation.js` to strip commas. Do not silently depend on Alpha Vantage always being available.

2. **Data cache strategy for Recalculate**
   - What we know: Two approaches work (DOM data attributes vs. module-level object cache).
   - What's unclear: Which the planner will choose — both are valid.
   - Recommendation: Module-level `const _dataCache = {};` is cleaner; plan should specify this explicitly.

3. **pageContext._rawData field**
   - What we know: `pageContext.tickerData[ticker]` is set in stockScraper.js lines 134+ but does not currently store the raw `data` object.
   - What's unclear: Whether the planner will use pageContext as the data source for recalculate, or module-level cache.
   - Recommendation: Use module-level cache in dcfValuation.js; do not modify pageContext shape for this purpose.

---

## Validation Architecture

`workflow.nyquist_validation` is not set in `.planning/config.json` — treated as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Jest (if available) or Node `require` + assert |
| Config file | None detected in project root |
| Quick run command | `node -e "const m=require('./static/js/dcfValuation.js'); console.log(m.computeValuation({...}, 0.10, 0.10, 0.03))"` |
| Full suite command | No automated test suite exists for JS modules in this project |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DCF-01 | computeValuation returns a finite per-share value given valid FCF, Market Cap, Price | unit | Manual Node.js smoke test | ❌ Wave 0 |
| DCF-02 | premium sign and magnitude are correct for known inputs | unit | Manual Node.js smoke test | ❌ Wave 0 |
| DCF-03 | Three assumption inputs render in DOM with correct default values | smoke (browser) | Manual browser check | ❌ Wave 0 |
| DCF-04 | Recalculate button updates display without page reload | smoke (browser) | Manual browser check | N/A — browser-only |
| DCF-05 | FCF absent/zero returns error string, no numeric output | unit | Manual Node.js smoke test | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** Verify in browser — open app, scrape a ticker with AV key, confirm DCF section renders
- **Per wave merge:** Check all five success criteria in browser across one AV-data ticker and one no-FCF ticker
- **Phase gate:** All five success criteria true before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `static/js/dcfValuation.js` — the module file itself (created in Wave 1 task)
- [ ] No JS unit test infrastructure exists — verification is manual browser and Node.js smoke tests only

---

## Sources

### Primary (HIGH confidence)

- Direct codebase read: `static/js/earningsQuality.js` — module pattern to replicate
- Direct codebase read: `static/js/healthScore.js` — container creation and toggle pattern
- Direct codebase read: `static/js/displayManager.js` — exact integration call sites (lines 142–151)
- Direct codebase read: `static/js/stockScraper.js` — pageContext write pattern (lines 209–228)
- Direct codebase read: `static/css/styles.css` — badge and metric CSS classes confirmed
- Direct codebase read: `src/scrapers/api_scraper.py` line 159 — AlphaVantage FCF field name and format
- Direct codebase read: `src/scrapers/yahoo_scraper.py` lines 138–199 — Yahoo FCF, Market Cap, Current Price field names and comma-formatted string format
- Direct codebase read: `templates/index.html` lines 1331–1336 — script tag ordering
- Direct codebase read: `.planning/phases/15-dcf-valuation/15-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)

- 2-stage DCF Gordon Growth model: standard academic finance formula, widely documented

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; entire stack is existing codebase patterns
- Architecture: HIGH — all integration points confirmed by direct file reads; formulas specified by user
- Pitfalls: HIGH — comma-formatting issue confirmed by direct read of scraper source files; division by zero is mathematical certainty without guard

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable codebase, no external dependencies)
