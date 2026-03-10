# Phase 8: Portfolio Health Summary Card - Research

**Researched:** 2026-03-10
**Domain:** Vanilla JS UI component wiring, Flask endpoint addition, progressive async state management
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Card appears immediately after scrape completes (progressive reveal) — VaR and Sharpe are populated right away from analytics data
- Regime slots show "Analyzing..." while auto-run is in progress, then update in-place as each ticker's regime detection completes
- No explicit "fully loaded" signal needed — slots just transition naturally from "Analyzing..." to their final colored badges
- On re-run: card is cleared and rebuilt fresh (same pattern as `#autoRunSection` removal in autoRun.js)
- Compact single-row layout: `[VaR 95%: 12.3%] | [Sharpe: 1.42] | [AAPL: RISK_ON] [MSFT: RISK_OFF]`
- Card sits above `.tabs-container` inside `#resultsSection`, below the `<h2>` heading
- Regime labels are color-coded badges: RISK_ON = green, RISK_OFF = red/amber
- Overall traffic-light status icon: all RISK_ON = green; mixed = amber; majority RISK_OFF = red
- One-line action-oriented summary below the metric row
- Single-ticker mode: card shows VaR, Sharpe, and that ticker's regime — no correlation/PCA entries
- New backend endpoint: `/api/portfolio_sharpe` — accepts tickers + allocation weights + date range, returns `{ sharpe: float, rf_rate: float, period: string }`
- Risk-free rate: fetch current 3-month T-bill rate via Yahoo Finance (`^IRX`); fallback to rf=0% silently if fetch fails
- Called once after scrape completes, in parallel with auto-run regime calls
- Metric click: use existing `switchTab()` — no custom scroll-to-anchor for MVP

### Claude's Discretion
- Exact HTML/CSS for the compact card (reuse existing badge and card styles from the app)
- Exact wording of the one-line summary signals per regime combination
- Element ID for the health card (`#portfolioHealthCard`)
- Whether the Sharpe metric has a loading state ("Computing...") while the endpoint responds, or shows a spinner inline
- T-bill fetch fallback: if `^IRX` fetch fails, fall back to rf=0% silently

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| HEALTH-01 | A "Portfolio Health" card appears above the tab nav in results showing VaR (95%), Sharpe ratio, and regime per ticker | VaR extraction path from `AppState.currentAnalytics` confirmed; `/api/portfolio_sharpe` endpoint needed; regime label derivation from `/api/regime_detection` response confirmed |
| HEALTH-02 | Each metric in the health card links/jumps to its relevant analytics tab section | `TabManager.switchTab()` already accepts 'analytics' and 'autoanalysis' as valid tab names; no new function needed |
| HEALTH-03 | Health card shows available metrics only when fewer tickers are submitted (no correlation/PCA for single ticker) | Conditional rendering by `tickers.length` — same pattern as MDP block conditional in `autoRun.js` |
</phase_requirements>

---

## Summary

Phase 8 is a pure UI/wiring phase — no new ML models or analytics pipelines. It adds one new Flask route (`/api/portfolio_sharpe`) and one new JavaScript module (`portfolioHealth.js`) that mounts a compact summary card above the tab navigation in `#resultsSection`.

The card has two temporal layers: (1) VaR (from the synchronous scrape response already in `AppState.currentAnalytics`) and Sharpe (from a parallel async call to `/api/portfolio_sharpe`) are populated immediately on card creation; (2) regime slots are created with "Analyzing..." placeholders and updated in-place as `autoRun.js` resolves each ticker's `/api/regime_detection` call.

The coordination pattern is already established by Phase 7: `autoRun.js` drives all post-scrape async work. Phase 8 extends this by: (a) calling `PortfolioHealth.initCard(tickers, analyticsData)` in `stockScraper.js displayResults()` before `AutoRun.triggerAutoRun()`; (b) having `autoRun.js` call `PortfolioHealth.updateRegime(ticker, regimeLabel)` after each regime call completes.

**Primary recommendation:** Create `portfolioHealth.js` as the single new JS module. Expose `window.PortfolioHealth = { initCard, updateRegime }`. Wire into two existing callsites: `stockScraper.js displayResults()` (card initialization + Sharpe fetch) and `autoRun.js runAutoRegime()` (regime slot update on success/failure).

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vanilla JS (ES2020) | — | Card construction, DOM mutation, fetch | All existing JS modules use no framework |
| Flask | installed | `/api/portfolio_sharpe` route | All routes use Flask; already in webapp.py |
| yfinance | installed | `^IRX` T-bill fetch inside Sharpe route | Already used throughout financial_analytics.py |
| numpy/pandas | installed | Weighted return calculation for Sharpe | Already imported in financial_analytics.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| AppState (state.js) | — | `currentAnalytics` — source of VaR data | Used at card init time |
| TabManager (tabs.js) | — | `switchTab()` for metric click navigation | Used in click handlers on health card metrics |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Vanilla JS card construction | React/template literal library | No framework in use — adding one is out of scope |
| `^IRX` for rf rate | hardcoded 0.05 | `^IRX` is live and accurate; fallback to 0% on failure is already decided |

---

## Architecture Patterns

### Recommended File Layout

```
static/js/
├── portfolioHealth.js     # NEW — all card logic
├── autoRun.js             # MODIFIED — call PortfolioHealth.updateRegime() after each regime resolves
├── stockScraper.js        # MODIFIED — call PortfolioHealth.initCard() in displayResults()
webapp.py                  # MODIFIED — add /api/portfolio_sharpe route
templates/index.html       # MODIFIED — add <script> tag for portfolioHealth.js
```

### Pattern 1: Two-Phase Progressive Reveal

**What:** Card is created synchronously with VaR already populated. Sharpe slot shows "Computing..." while awaiting the Sharpe endpoint. Regime slots show "Analyzing..." while awaiting per-ticker regime calls.

**When to use:** When some data is immediately available (VaR from scrape response) and other data is async (Sharpe, regimes).

```javascript
// portfolioHealth.js — card initialization called from stockScraper.js displayResults()
function initCard(tickers, analyticsData, allocations) {
    // Remove old card on re-run
    document.getElementById('portfolioHealthCard')?.remove();

    // Extract VaR immediately from analyticsData
    const varValue = extractVaR(analyticsData, tickers);

    // Build card HTML with placeholder slots for Sharpe and regimes
    const card = buildCardHTML(tickers, varValue);

    // Insert above .tabs-container in #resultsSection
    const resultsSection = document.getElementById('resultsSection');
    const tabsContainer = resultsSection.querySelector('.tabs-container');
    tabsContainer.insertAdjacentHTML('beforebegin', card);

    // Fetch Sharpe in background — updates slot when resolved
    fetchSharpe(tickers, allocations);
}
```

### Pattern 2: In-Place Badge Update (mirrors autoRun.js regime badge pattern)

**What:** Each regime slot has a stable DOM ID (`healthRegimeBadge_TICKER`). `autoRun.js` calls `PortfolioHealth.updateRegime(ticker, label)` after its regime fetch resolves.

**When to use:** Any time an async result needs to update a pre-rendered placeholder.

```javascript
// portfolioHealth.js — called by autoRun.js after each runAutoRegime() resolves
function updateRegime(ticker, label) {
    // label: 'RISK_ON' | 'RISK_OFF' | null (null = failed)
    const badge = document.getElementById('healthRegimeBadge_' + ticker);
    if (!badge) return;

    if (label === 'RISK_ON') {
        badge.textContent = 'RISK_ON';
        badge.setAttribute('style', BADGE_RISK_ON);
    } else if (label === 'RISK_OFF') {
        badge.textContent = 'RISK_OFF';
        badge.setAttribute('style', BADGE_RISK_OFF);
    } else {
        badge.textContent = 'Failed';
        badge.setAttribute('style', BADGE_FAILED_STYLE);
    }

    // After all regimes resolved, recompute traffic-light and one-line summary
    maybeUpdateSummary();
}
```

### Pattern 3: VaR Extraction from analyticsData

**What:** `AppState.currentAnalytics` is set before `displayResults()` is called. For multi-ticker, VaR lives in `analytics_data.portfolio_monte_carlo.VaR`. For single-ticker, VaR lives in `analytics_data[ticker].monte_carlo.VaR`.

**Source:** Confirmed in `analyticsRenderer.js` lines 371-374 and `displayManager.js` lines 200-209.

```javascript
// Extract VaR (95%) percentage from analytics data
function extractVaR(analyticsData, tickers) {
    let mc = null;
    if (tickers.length >= 2 && analyticsData.portfolio_monte_carlo) {
        mc = analyticsData.portfolio_monte_carlo;
    } else if (tickers.length === 1 && analyticsData[tickers[0]]?.monte_carlo) {
        mc = analyticsData[tickers[0]].monte_carlo;
    }
    if (!mc) return null;

    // Primary path: mc.VaR['VaR at 95% confidence'].Percentage / 100
    if (mc.VaR) {
        const key95 = Object.keys(mc.VaR).find(k => k.includes('95'));
        if (key95 && mc.VaR[key95]?.Percentage != null) {
            return mc.VaR[key95].Percentage / 100;
        }
    }
    // Fallback: mc.var_95
    if (mc.var_95 != null) return mc.var_95;
    return null;
}
```

### Pattern 4: Regime Label Derivation

**What:** From `/api/regime_detection` response, derive RISK_ON/RISK_OFF from `data.filtered_probs` last value.

**Source:** Confirmed in CONTEXT.md and Phase 7 decision log `[Phase 03-01]`.

```javascript
// Derive regime label from regime_detection API response
function deriveRegimeLabel(data) {
    const probs = data.filtered_probs;
    if (!probs || probs.length === 0) return null;
    const lastProb = probs[probs.length - 1];
    return lastProb >= 0.5 ? 'RISK_OFF' : 'RISK_ON';
}
```

This derivation must happen inside `autoRun.js runAutoRegime()` success branch, then passed to `PortfolioHealth.updateRegime(ticker, label)`.

### Pattern 5: Flask Sharpe Endpoint

**What:** New `POST /api/portfolio_sharpe` route. Fetches `^IRX` for rf rate, downloads 2-year daily closes for input tickers, computes weighted log-returns, annualizes, divides by annualized vol.

**Location:** `webapp.py` — append after `/api/regime_detection` route block.

```python
@app.route('/api/portfolio_sharpe', methods=['POST'])
def portfolio_sharpe():
    """
    Compute annualized portfolio Sharpe ratio.
    Body: { "tickers": [...], "weights": {...}, "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }
    Returns: { "sharpe": float, "rf_rate": float, "period": "YYYY-MM-DD to YYYY-MM-DD" }
    """
    data = request.json or {}
    tickers   = data.get('tickers', [])
    weights   = data.get('weights', {})   # dict ticker->float; falls back to equal-weight
    start_date = data.get('start_date')
    end_date   = data.get('end_date')

    try:
        import yfinance as yf
        import numpy as np

        # Fetch risk-free rate (annualized %)
        rf_rate = 0.0
        try:
            irx = yf.Ticker('^IRX').history(period='5d')
            if not irx.empty:
                rf_rate = float(irx['Close'].iloc[-1]) / 100.0  # ^IRX in % already
        except Exception:
            rf_rate = 0.0  # silent fallback per decision

        # Fetch price data
        prices = yf.download(tickers, start=start_date, end=end_date,
                             auto_adjust=True, progress=False)['Close']
        if isinstance(prices, pd.Series):
            prices = prices.to_frame(tickers[0])
        prices = prices.dropna()

        # Build weight vector
        n = len(tickers)
        w = np.array([weights.get(t, 1.0/n) for t in tickers])
        w = w / w.sum()  # normalize

        # Weighted daily returns
        daily_log = np.log(prices / prices.shift(1)).dropna()
        port_ret = (daily_log * w).sum(axis=1)

        ann_ret = port_ret.mean() * 252
        ann_vol = port_ret.std() * np.sqrt(252)
        sharpe  = (ann_ret - rf_rate) / ann_vol if ann_vol > 0 else 0.0

        return jsonify({
            'sharpe':   round(float(sharpe), 4),
            'rf_rate':  round(float(rf_rate), 4),
            'period':   f'{start_date} to {end_date}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Pattern 6: Traffic-Light Colour Logic

**What:** After all regime slots resolve, compute overall traffic-light from collected RISK_ON/RISK_OFF states.

```javascript
function computeTrafficLight(regimeMap) {
    // regimeMap: { TICKER: 'RISK_ON' | 'RISK_OFF' | null }
    const labels = Object.values(regimeMap).filter(v => v !== null);
    if (labels.length === 0) return 'grey';
    const offCount = labels.filter(l => l === 'RISK_OFF').length;
    if (offCount === 0) return 'green';
    if (offCount === labels.length) return 'red';
    return 'amber';   // mixed
}
```

### Pattern 7: Summary Signal Text

```javascript
function buildSummaryText(tickers, regimeMap) {
    const riskOff = tickers.filter(t => regimeMap[t] === 'RISK_OFF');
    const riskOn  = tickers.filter(t => regimeMap[t] === 'RISK_ON');

    if (riskOff.length === 0 && riskOn.length > 0) {
        return 'All holdings in risk-on regime — portfolio positioned well.';
    }
    if (riskOff.length === tickers.length) {
        return 'All holdings in risk-off regime — consider defensive rebalancing or cash.';
    }
    // Mixed
    const names = riskOff.join(', ');
    const safe  = riskOn.length > 0 ? ` Rebalancing toward ${riskOn[0]} may reduce exposure.` : '';
    return `Mixed regime detected — ${names} in risk-off.${safe}`;
}
```

### Anti-Patterns to Avoid

- **Reading regime from auto-run HTML badges:** The badge DOM may not exist yet. Pass the label as a parameter from `runAutoRegime()` return value instead.
- **Fetching VaR from the backend again:** VaR is already in `AppState.currentAnalytics` from the scrape response. No second network call needed.
- **Inserting card after `#tabContents`:** The card must be between `<h2>` and `.tabs-container`, not after the tabs. Use `tabsContainer.insertAdjacentHTML('beforebegin', html)`.
- **Overwriting `autoRun.js triggerAutoRun()` signature:** Do not change the public API. Coordinate by passing a callback or by calling `PortfolioHealth.updateRegime` inside `runAutoRegime()` at the point where it already has the result.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Risk-free rate lookup | Manual treasury API call | `yf.Ticker('^IRX').history()` | Already used pattern throughout webapp.py |
| Tab navigation on click | Custom scroll/anchor | `TabManager.switchTab()` | Already handles all three tab names; no changes needed |
| Badge inline styles | New CSS classes | Reuse `BADGE_RUNNING`/`BADGE_DONE`/`BADGE_FAILED` constants from autoRun.js | Already defined and consistent with app style |
| CSS card styles | New stylesheet rules | Inline styles matching existing pattern | All existing cards (autoRun.js, analyticsRenderer.js) use inline styles; no external CSS file to modify |

---

## Common Pitfalls

### Pitfall 1: VaR path differs for single vs. multi-ticker

**What goes wrong:** For a single ticker, `analytics_data.portfolio_monte_carlo` does not exist — VaR is at `analytics_data[ticker].monte_carlo.VaR`. Hardcoding the multi-ticker path silently returns `null` for single-ticker runs.

**Why it happens:** The scrape route computes portfolio-level Monte Carlo only for 2+ tickers (webapp.py line 518).

**How to avoid:** Use the `tickers.length >= 2` branch switch shown in Pattern 3. Always test with a single ticker explicitly.

**Warning signs:** VaR reads "—" in the card for every single-ticker run.

### Pitfall 2: Card survives re-runs and duplicates itself

**What goes wrong:** On a second scrape, `displayResults()` runs again, creating a second `#portfolioHealthCard` above the first.

**Why it happens:** The card is inserted into the DOM but never removed on re-run unless explicitly guarded.

**How to avoid:** `document.getElementById('portfolioHealthCard')?.remove()` at the top of `initCard()`, mirroring the `autoRunSection` removal in `triggerAutoRun()`.

**Warning signs:** Two stacked health cards after back-to-back analyses.

### Pitfall 3: Regime update called before card exists

**What goes wrong:** `autoRun.js` calls `PortfolioHealth.updateRegime(ticker, label)` but the card hasn't been mounted yet (e.g., `initCard` errored silently).

**Why it happens:** Race between `initCard` and the first fast regime response if `^IRX` fetch is slow.

**How to avoid:** `updateRegime()` must guard with `if (!badge) return;` — already shown in Pattern 2. `initCard` should be called synchronously before `AutoRun.triggerAutoRun()` in `displayResults()`.

**Warning signs:** Console errors about `healthRegimeBadge_TICKER` being null.

### Pitfall 4: `^IRX` returns annualized percent, not decimal

**What goes wrong:** `^IRX` closes at ~5.3 (meaning 5.3%). Treating it as a decimal (0.053) is correct, but raw value 5.3 used as rf makes Sharpe wildly negative.

**Why it happens:** `^IRX` price IS the annualized yield in percent (not bps, not decimal).

**How to avoid:** Divide by 100: `rf_rate = float(irx['Close'].iloc[-1]) / 100.0`.

**Warning signs:** Sharpe values of -4 to -50 when rf is not divided.

### Pitfall 5: `yf.download` single-ticker returns Series not DataFrame

**What goes wrong:** `yf.download(['AAPL'], ...)['Close']` for a single ticker may return a `pd.Series` instead of a `pd.DataFrame`, causing `.sum(axis=1)` to fail.

**Why it happens:** yfinance collapses the ticker level for single-ticker downloads.

**How to avoid:** `if isinstance(prices, pd.Series): prices = prices.to_frame(tickers[0])` — shown in Pattern 5.

**Warning signs:** `AttributeError: 'Series' object has no attribute 'columns'`.

### Pitfall 6: Card DOM IDs conflict with autoRun IDs

**What goes wrong:** Both health card and autoRun section might use `autoRegimeBadge_TICKER`. If health card uses the same ID prefix, `autoRun.js` updates the wrong element.

**Why it happens:** Namespace collision if not prefixed distinctly.

**How to avoid:** Health card regime badges use `healthRegimeBadge_TICKER`, not `autoRegimeBadge_TICKER`. All health card IDs prefixed with `health`.

---

## Code Examples

### Card insertion point in HTML (verified from index.html lines 805-823)

```
#resultsSection
  <h2>📈 Analysis Results</h2>
  ← INSERT #portfolioHealthCard HERE (before .tabs-container)
  <div class="tabs-container">
    <div class="tabs">...</div>
  </div>
  <div id="tabContents">...</div>
```

Insertion call: `tabsContainer.insertAdjacentHTML('beforebegin', cardHTML)`

### switchTab call for metric navigation (verified from tabs.js lines 9-57)

Valid tab names: `'stocks'`, `'analytics'`, `'autoanalysis'`

```javascript
// VaR metric click → analytics tab
varEl.onclick = () => TabManager.switchTab('analytics');

// Regime metric click → autoanalysis tab
regimeEl.onclick = () => TabManager.switchTab('autoanalysis');

// Sharpe metric click → analytics tab (if present there) or autoanalysis
sharpeEl.onclick = () => TabManager.switchTab('analytics');
```

### BADGE constants reuse pattern (from autoRun.js lines 6-8)

```javascript
// Reuse from autoRun.js (already defined globally)
// BADGE_RUNNING — grey, "Analyzing..."
// BADGE_DONE    — green, for RISK_ON
// BADGE_FAILED  — red, for RISK_OFF or failed

// Additional colours needed for health card:
const BADGE_RISK_ON  = 'background:#28a745;color:white;border-radius:10px;padding:2px 8px;font-size:11px;margin-left:4px;';
const BADGE_RISK_OFF = 'background:#dc3545;color:white;border-radius:10px;padding:2px 8px;font-size:11px;margin-left:4px;';
const BADGE_AMBER    = 'background:#ffc107;color:#333;border-radius:10px;padding:2px 8px;font-size:11px;margin-left:4px;';
```

### Sharpe fetch from frontend (portfolioHealth.js)

```javascript
async function fetchSharpe(tickers, allocations, startDate, endDate) {
    const sharpeSlot = document.getElementById('healthSharpeValue');
    try {
        const resp = await fetch('/api/portfolio_sharpe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tickers, weights: allocations, start_date: startDate, end_date: endDate })
        });
        const data = await resp.json();
        if (resp.ok && data.sharpe != null && sharpeSlot) {
            sharpeSlot.textContent = data.sharpe.toFixed(2);
        } else if (sharpeSlot) {
            sharpeSlot.textContent = '—';
        }
    } catch (_) {
        if (sharpeSlot) sharpeSlot.textContent = '—';
    }
}
```

### Allocation extraction from FormManager (existing, forms.js)

The `portfolioAllocation` object is already available as `AppState.currentAnalytics` config; the raw weights used by analytics are in `result.portfolio_allocation` passed through the scrape response. The Sharpe endpoint needs weights as a `{ ticker: float }` dict — the same format used by `analytics_config.portfolio.allocations` in webapp.py (line 465).

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual re-render on each update | In-place DOM badge mutation via stable ID | Phase 7 pattern | No full re-render needed; matches existing autoRun pattern |
| Separate scrape + analytics calls | Analytics computed inside `/api/scrape`, returned in one response | v2.0 start | VaR is already in scrape response — no extra call needed |

---

## Open Questions

1. **Does `portfolioAllocation` reach `displayResults()` in a usable format for the Sharpe call?**
   - What we know: `FormManager.getPortfolioAllocation()` returns a dict, stored in `requestBody.portfolio_allocation`, passed to backend, but NOT explicitly stored in `AppState` after the response.
   - What's unclear: The scrape response does not echo back the allocation dict. `AppState.currentAnalytics` contains computed analytics, not the raw weights.
   - Recommendation: Store `portfolio_allocation` in `AppState` when setting `AppState.currentTickers` in `stockScraper.js handleSubmit()`. Alternatively, re-read `FormManager.getPortfolioAllocation()` at card init time (form values are still present).

2. **Does `autoRun.js runAutoRegime()` need to return the label, or should it call `PortfolioHealth.updateRegime()` directly?**
   - What we know: `runAutoRegime()` currently has no return value and updates DOM directly. `PortfolioHealth` must be notified after each regime resolves.
   - What's unclear: Whether to add a return value (coupling) or a direct call (tight coupling but simpler).
   - Recommendation: Direct call `if (window.PortfolioHealth) PortfolioHealth.updateRegime(ticker, label)` inside the success and failure branches of `runAutoRegime()`. This is the simplest change and mirrors the `if (window.AutoRun)` guard in `stockScraper.js`.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (confirmed from venv: pluggy installed, pytest present) |
| Config file | none detected — run from project root |
| Quick run command | `pytest tests/ -x -q 2>/dev/null || echo "no tests yet"` |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HEALTH-01 | `/api/portfolio_sharpe` returns `sharpe`, `rf_rate`, `period` keys | unit (Flask test client) | `pytest tests/test_portfolio_sharpe.py -x` | Wave 0 |
| HEALTH-01 | VaR extraction function handles multi-ticker and single-ticker paths | unit (JS logic ported to Python or manual) | manual | — |
| HEALTH-02 | Card metric click calls `TabManager.switchTab` with correct tab name | manual browser test | n/a | — |
| HEALTH-03 | Single-ticker: card renders without correlation/PCA entries | manual browser test | n/a | — |

Note: HEALTH-02 and HEALTH-03 are UI interaction tests — no automated runner covers them without a browser automation layer (Playwright/Selenium), which is out of scope for this showcase app. The backend route (HEALTH-01) is the only automatable test.

### Sampling Rate
- **Per task commit:** `pytest tests/test_portfolio_sharpe.py -x -q` (if file exists)
- **Per wave merge:** `pytest tests/ -q`
- **Phase gate:** Flask route returns valid JSON and frontend card mounts without JS errors before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_portfolio_sharpe.py` — covers HEALTH-01 backend route
- [ ] `tests/conftest.py` — Flask test client fixture (check if already exists)

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection — `autoRun.js`, `stockScraper.js`, `tabs.js`, `analyticsRenderer.js`, `displayManager.js`, `webapp.py`, `templates/index.html` — all read in full during this research session
- `src/analytics/financial_analytics.py` — yfinance usage and weight patterns confirmed

### Secondary (MEDIUM confidence)
- `^IRX` as 3-month T-bill rate in yfinance: standard usage, confirmed by yfinance docs pattern (percent units)
- yfinance single-ticker Series collapse behaviour: confirmed by widespread community knowledge and consistent with financial_analytics.py defensive handling

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use in the project
- Architecture: HIGH — patterns directly observed in Phase 7 code
- Pitfalls: HIGH — VaR path and `^IRX` unit issues verified from source code
- Backend Sharpe route: HIGH — uses existing yfinance pattern; only new code is the computation

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable stack; yfinance API changes occasionally but not weekly)
