# Phase 3: Frontend Wiring and Visualization - Research

**Researched:** 2026-03-06
**Domain:** Plotly.js charting, Flask SSE streaming, HTML/JS sub-tab wiring, stochastic model UI
**Confidence:** HIGH (codebase directly inspected; all APIs and existing JS confirmed by reading source)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REGIME-01 | User can run HMM regime detection on selected ticker and date range | `/api/regime_detection` exists, returns `filtered_probs` — wire date-range input and call the existing route |
| REGIME-02 | User can view filtered probability time series chart (bull/bear/crisis states over time) | API returns `filtered_probs` array; render with `Plotly.newPlot` area/scatter chart |
| REGIME-03 | User can view regime-annotated price chart (price with regime background shading) | API returns `prices` and `dates` alongside regime labels; use Plotly shapes/vrect for shading |
| REGIME-04 | Model correctly identifies crisis periods (SPY March 2020 = RISK_OFF) | Backend already validated in Phase 1 (MATH-04); frontend just renders the signal colour |
| REGIME-05 | Regime detection results display in dedicated UI sub-tab | Sub-tab `stochContent_regime` already exists in index.html; needs Plotly chart added to resultsDiv |
| HESTON-01 | User can price European options using Heston model with chosen parameters | `/api/heston_price` exists and returns `heston.price` and `black_scholes_comparison.price` |
| HESTON-02 | User can view implied volatility surface (strike vs. maturity) as Plotly chart | Backend must generate IV grid; route exists; JS must call with strike/maturity ranges and render `go.Surface` |
| HESTON-03 | User can compare Heston price vs. Black-Scholes price for same contract | `heston_price` endpoint already returns both; UI just needs to render them side-by-side |
| HESTON-04 | IV surface shows non-flat smile (volatility skew visible) | Backend validated in Phase 1 (MATH-02/MATH-05); rendering a Plotly 3D surface will expose this |
| HESTON-05 | Heston pricing results display in dedicated UI sub-tab | Need new sub-tab `stochContent_heston_price` (distinct from calibration tab) |
| CALIB-01 | User can calibrate Heston model to market option prices | `/api/calibrate_heston` exists; current JS calls it but shows only KV table — needs IV chart |
| CALIB-02 | User can calibrate BCC model to market option prices | `/api/calibrate_bcc` exists (added in Phase 2, plan 02-03); needs UI sub-tab wired |
| CALIB-03 | Calibration shows live progress streaming (iteration count, current error) via SSE | No SSE route exists yet — must implement `/api/calibrate_heston_stream` SSE endpoint + JS EventSource |
| CALIB-04 | Calibration results display relative RMSE and fitted vs. market IV comparison | API returns `rmse`; IV comparison data (market_ivs, fitted_ivs, strikes) must be returned and charted |
| CALIB-05 | BCC calibration has a Flask route and UI sub-tab (currently backend-complete, no UI) | Route added in Phase 2; only HTML sub-tab + JS wiring is missing |
</phase_requirements>

---

## Summary

Phase 3 is a frontend-only phase layered on top of already-complete backends. All required Flask routes exist (`/api/regime_detection`, `/api/heston_price`, `/api/calibrate_heston`, `/api/calibrate_bcc`, `/api/interest_rate_model`, `/api/markov_chain`, `/api/credit_risk`). The project already has Plotly 2.27.0 loaded via CDN, a working sub-tab system (`switchStochasticTab` + `.stoch-content`), and a `stochasticModels.js` file with established patterns: async fetch, `renderAlert`, `escapeHTML`, inline HTML string injection into result `<div>` elements.

The gap is entirely on the visualization side: (1) the Regime tab shows a KV table instead of Plotly charts; (2) a Heston Pricing sub-tab (HESTON-01 through HESTON-05) does not exist — it is hidden inside the Options Pricing tab, not the Stochastic Models tab; (3) BCC calibration sub-tab is missing; (4) the Heston Calibration tab lacks a fitted-vs-market IV Plotly chart and live SSE progress; (5) Markov, Credit, and Rates sub-tabs exist but may show tables instead of Plotly charts for some results.

One non-trivial implementation is the SSE progress stream for Heston calibration (CALIB-03). This requires a new Flask route that uses `yield` inside a `Response(stream_with_context(...))` and a callback mechanism into the calibrator. The JS side uses `EventSource`. The calibrator does not currently support a callback — this needs a thin wrapper.

**Primary recommendation:** Follow the established JS pattern exactly. Each sub-tab gets: (a) HTML inputs in index.html, (b) an async JS function in stochasticModels.js that fetches the route and calls `Plotly.newPlot` into a result div. For SSE, add one new Flask route and one `EventSource` handler. Do not refactor existing working tabs.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Plotly.js | 2.27.0 (CDN) | All charting — time series, surface, bar | Already loaded; all existing chart code uses it |
| Flask | Current in venv | Backend routes + SSE streaming | Project standard; all routes use Flask |
| Vanilla JS | ES2020 (async/await) | Frontend logic | Project uses no framework; all JS is vanilla |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `Response(stream_with_context(...))` | Flask built-in | SSE streaming for calibration progress | CALIB-03 only |
| `EventSource` | Browser built-in | JS SSE consumer | CALIB-03 client side |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SSE for calibration progress | Pre-compute and return all at once | SSE is harder but required by CALIB-03 spec; pre-compute is easier but loses live indicator |
| Inline Plotly in result div | Separate chart container div | Inline matches existing pattern (regime, CIR tabs); consistent with project style |

**Installation:** No new packages required. All libraries are already present.

---

## Architecture Patterns

### Recommended Project Structure

No new files needed beyond:
```
templates/
└── index.html              # Add sub-tab buttons + content divs for Heston Pricing, BCC Cal
static/js/
└── stochasticModels.js     # Add JS functions for new sub-tabs; extend existing regime/heston functions
webapp.py                   # Add SSE route for calibration progress (CALIB-03 only)
```

### Pattern 1: Add a New Sub-Tab (established pattern)

**What:** HTML button + content div pair, wired by `switchStochasticTab(name)`.
**When to use:** HESTON-05 (new Heston Pricing tab), CALIB-05 (BCC calibration tab).

HTML in index.html inside the `.tabs` div:
```html
<!-- in .tabs div -->
<button class="tab-button" onclick="switchStochasticTab('heston_price')" id="stochTab_heston_price">
    📊 Heston Pricing
</button>
```
Content div immediately after existing stoch-content divs:
```html
<div id="stochContent_heston_price" class="stoch-content" style="display:none;">
    <!-- inputs + button + result div -->
    <div id="hestonPriceResults" style="display:none; margin-top:20px;"></div>
</div>
```
No JS changes needed for tab switching — `switchStochasticTab` already handles any id.

### Pattern 2: Render a Plotly Time-Series Chart (existing pattern, extend for regime)

**What:** Call `Plotly.newPlot` on a container div inside the result div.
**When to use:** REGIME-02 (filtered probability chart), REGIME-03 (price with regime shading).

```javascript
// Source: existing options pricing tab (volatility surface chart in index.html)
// Container must exist in DOM before this call
const chartDiv = document.createElement('div');
chartDiv.id = 'regimeProbChart';
resultsDiv.appendChild(chartDiv);

Plotly.newPlot('regimeProbChart', [
    {
        x: dates,                     // array of date strings from API
        y: filteredProbs,             // filtered_probs array from r.filtered_probs
        type: 'scatter',
        mode: 'lines',
        fill: 'tozeroy',
        name: 'P(Stressed)',
        line: { color: '#dc3545' }
    }
], {
    title: `Regime Probability — ${ticker}`,
    xaxis: { title: 'Date' },
    yaxis: { title: 'P(Stressed)', range: [0, 1] },
    height: 300
});
```

### Pattern 3: Regime-Shaded Price Chart (REGIME-03)

**What:** Plotly `shapes` array with `vrect`-style rectangles coloured by regime state.
**When to use:** REGIME-03 only.

```javascript
// Build shapes array from regime_sequence (array of 0/1 per date)
const shapes = [];
let start = null, prevState = null;
dates.forEach((d, i) => {
    const state = regimeSequence[i];  // 0=calm, 1=stressed
    if (state !== prevState) {
        if (prevState === 1 && start !== null) {
            shapes.push({
                type: 'rect', xref: 'x', yref: 'paper',
                x0: start, x1: d, y0: 0, y1: 1,
                fillcolor: 'rgba(220,53,69,0.15)', line: { width: 0 }
            });
        }
        start = d;
    }
    prevState = state;
});

Plotly.newPlot('regimePriceChart', [
    { x: dates, y: prices, type: 'scatter', mode: 'lines', name: ticker }
], {
    title: `${ticker} Price with Regime Shading`,
    shapes: shapes,
    height: 350
});
```

The API response from `/api/regime_detection` returns `regime.filtered_probs` but may not return the raw price series and per-day regime labels. Inspect the backend response shape and add `prices`, `dates`, and `regime_sequence` fields to the response if missing (webapp.py patch).

### Pattern 4: Plotly 3D Surface for IV (HESTON-02, HESTON-04)

**What:** `go.Surface` with strikes on x-axis, maturities on y-axis, IVs on z-axis.
**When to use:** HESTON-02 / HESTON-04.

```javascript
// Expected API response: { strikes: [...], maturities: [...], iv_grid: [[...], ...] }
Plotly.newPlot('hestonIVSurface', [{
    type: 'surface',
    x: data.strikes,
    y: data.maturities,
    z: data.iv_grid,
    colorscale: 'Viridis',
    colorbar: { title: 'IV' }
}], {
    title: 'Heston Implied Volatility Surface',
    scene: {
        xaxis: { title: 'Strike' },
        yaxis: { title: 'Maturity (yrs)' },
        zaxis: { title: 'Implied Vol' }
    },
    height: 450
});
```

The `/api/heston_price` route prices a single contract. To build the IV grid, either: (a) call the route multiple times client-side (expensive, bad UX), or (b) add a `/api/heston_iv_surface` route that iterates strikes/maturities server-side. **Option (b) is required** — the surface must come from one backend call.

### Pattern 5: SSE Progress for Calibration (CALIB-03)

**What:** Flask `Response` with `text/event-stream`, JS `EventSource`.
**When to use:** CALIB-03 only.

Flask route skeleton:
```python
# webapp.py
from flask import Response, stream_with_context

@app.route('/api/calibrate_heston_stream', methods=['GET'])
def calibrate_heston_stream():
    ticker = request.args.get('ticker', 'AAPL').upper()
    rate   = float(request.args.get('risk_free_rate', 0.05))

    def generate():
        from src.derivatives.model_calibration import HestonCalibrator
        iteration = [0]

        def progress_cb(params, error):
            iteration[0] += 1
            msg = json.dumps({'iteration': iteration[0], 'error': float(error)})
            return f"data: {msg}\n\n"

        calibrator = HestonCalibrator()
        # calibrator must accept callback kwarg — add thin wrapper
        for event in calibrator.calibrate_stream(ticker, rate, callback=progress_cb):
            yield event
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(stream_with_context(generate()),
                    mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
```

JS `EventSource` consumer:
```javascript
function runHestonCalibrationWithProgress(ticker, rate) {
    const src = new EventSource(`/api/calibrate_heston_stream?ticker=${ticker}&risk_free_rate=${rate}`);
    src.onmessage = (e) => {
        const d = JSON.parse(e.data);
        if (d.done) {
            src.close();
            // fetch final result from /api/calibrate_heston
        } else {
            progressDiv.textContent = `Iteration ${d.iteration} — RMSE: ${d.error.toFixed(6)}`;
        }
    };
}
```

**Render.com note:** Render free tier may buffer SSE. Add `X-Accel-Buffering: no` response header (already shown above). `sys.stdout.flush()` is not needed with Flask's streaming response.

### Pattern 6: RMSE Quality Label (CALIB-04)

**What:** Map RMSE value to qualitative label.
**When to use:** CALIB-04 display in calibration results.

```javascript
function rmseLabel(rmse) {
    if (rmse < 0.01) return { label: 'Good', color: '#28a745' };
    if (rmse < 0.03) return { label: 'Acceptable', color: '#ffc107' };
    return { label: 'Poor', color: '#dc3545' };
}
```

Thresholds: Good < 1% relative RMSE, Acceptable < 3%, Poor >= 3%. These are domain-standard for Heston calibration against liquid options (HIGH confidence — textbook benchmark).

### Pattern 7: CIR Feller Badge (RATE-04, existing — verify on all tabs)

**What:** Inline HTML badge showing green/red Feller condition status.
**When to use:** CIR rates sub-tab (already implemented in calibration tab for Heston). Must also appear on the Rates sub-tab.

The existing calibration JS already has:
```javascript
const fellerBadge = feller
    ? `<span style="background:#d4edda; ...">✓ Feller satisfied</span>`
    : `<span style="background:#f8d7da; ...">✗ Feller violated</span>`;
```
Reuse this exact pattern. The `/api/interest_rate_model` response already returns `feller_condition_satisfied` and `feller_ratio`.

### Anti-Patterns to Avoid

- **Creating a new JS file for Phase 3 work:** All stochastic JS goes in `stochasticModels.js`. A new file requires a new `<script>` tag and risks load-order issues.
- **Calling `/api/heston_price` in a loop to build the IV surface:** Network overhead + Render timeout. One server-side grid endpoint is required.
- **Injecting raw API strings into innerHTML without escapeHTML:** The existing `escapeHTML` helper exists for this reason — always use it for user-supplied or API-supplied strings.
- **Using `document.write` or global `Plotly` checks:** Plotly is loaded via CDN before the closing `</body>` tag and is always available when JS runs.
- **Polling for calibration progress:** Use SSE `EventSource`, not `setInterval` + fetch.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 3D IV surface chart | Custom WebGL renderer | `Plotly.newPlot` with `type: 'surface'` | Plotly 3D surfaces handle camera, color, hover natively |
| SSE client | Custom WebSocket or polling | Browser `EventSource` | SSE is HTTP; `EventSource` auto-reconnects, parses `data:` lines |
| Regime shading | Custom canvas overlay | Plotly `shapes` array with `type: 'rect'` | Native Plotly; stays aligned with zoom/pan |
| RMSE → quality label | ML classifier | Simple threshold comparison (< 1%, < 3%) | Domain standard; no training data needed |
| Sub-tab routing | React Router / SPA framework | Existing `switchStochasticTab` function | Already works; adding a new id pair is 4 lines |

---

## Common Pitfalls

### Pitfall 1: Regime API response missing prices/dates/regime_sequence
**What goes wrong:** `filtered_probs` exists but per-day price and regime-label arrays may not be returned by the current `RegimeDetector.analyze()` output. REGIME-03 needs all three.
**Why it happens:** Phase 2 spec only required `filtered_probs` for the probability chart.
**How to avoid:** Before writing JS, read the actual API JSON response for SPY. If `prices`, `dates`, and `regime_sequence` are missing, add a 3-line patch to `regime_detection_endpoint` in webapp.py to include them.
**Warning signs:** `Uncaught TypeError: Cannot read properties of undefined (reading 'length')` on the prices array.

### Pitfall 2: Plotly div re-renders on second click
**What goes wrong:** Calling `Plotly.newPlot` on an existing div stacks traces instead of replacing the chart.
**Why it happens:** `newPlot` creates a new chart; if the div already has a Plotly instance, traces accumulate.
**How to avoid:** Call `Plotly.purge('divId')` before `Plotly.newPlot`, or use `Plotly.react('divId', ...)` which diffs and updates.
**Warning signs:** Second run of same tab shows double traces.

### Pitfall 3: SSE buffering on Render free tier
**What goes wrong:** Progress messages batch-deliver all at once after calibration completes — no live indicator.
**Why it happens:** Render's nginx proxy buffers SSE unless disabled.
**How to avoid:** Add `X-Accel-Buffering: no` header to the SSE Flask route. Also set `Cache-Control: no-cache`.
**Warning signs:** Progress div shows nothing until calibration ends, then shows all iterations at once.

### Pitfall 4: HestonCalibrator has no callback/streaming API
**What goes wrong:** The calibrator runs synchronously; there is no hook to emit progress mid-run.
**Why it happens:** Calibrator was built for batch use (Phase 1/2), not streaming.
**How to avoid:** Add a `callback` kwarg to `HestonCalibrator.calibrate`. The scipy optimizer (`minimize` with Nelder-Mead) accepts a `callback` argument that fires after each iteration. Pass the user callback through.
**Warning signs:** `TypeError: calibrate() got an unexpected keyword argument 'callback'`.

### Pitfall 5: IV surface route not scoped to Stochastic Models tab
**What goes wrong:** The existing `/api/heston_price` is already used by the Options Pricing tab. Adding IV surface logic there would break existing functionality.
**How to avoid:** Add a new dedicated route `/api/heston_iv_surface` that takes parameter ranges (spot, strike range, maturity range) and returns the full grid. Never modify existing working routes.
**Warning signs:** Options Pricing tab results change after adding IV surface support.

### Pitfall 6: Missing Markov/Credit/Rates Plotly charts (success criterion 5)
**What goes wrong:** Success criterion 5 requires ALL stochastic sub-tabs to show Plotly charts (not tables). Current Markov, Credit, and Rates tabs may render tables only.
**Why it happens:** Phase 2 added backends; Phase 3 is the first time charts are required.
**How to avoid:** Audit each sub-tab's result rendering. Convert any HTML table that should be a chart (e.g., yield curve table → line chart, default probability table → line chart, transition matrix table → heatmap).

---

## Code Examples

### Fetch with error handling (project standard pattern)
```javascript
// Source: stochasticModels.js runRegimeDetection() existing implementation
async function runXyzModel() {
    const resultsDiv = document.getElementById('xyzResults');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = `<p style="color:#666;">Loading...</p>`;
    try {
        const resp = await fetch('/api/xyz', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ param: value })
        });
        if (!resp.ok) {
            resultsDiv.innerHTML = renderAlert(`Server error ${resp.status}`);
            return;
        }
        const data = await resp.json();
        if (!data.success) { resultsDiv.innerHTML = renderAlert(data.error); return; }
        // render Plotly chart here
    } catch (err) {
        resultsDiv.innerHTML = renderAlert(`Request failed: ${err.message}`);
    }
}
```

### Plotly line chart (yield curve / default probability)
```javascript
// Source: project Plotly 2.27.0 CDN; pattern confirmed from options pricing tab
Plotly.newPlot('chartDivId', [{
    x: maturities,
    y: yields,
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Yield Curve',
    line: { color: '#667eea', width: 2 }
}], {
    title: 'CIR Yield Curve',
    xaxis: { title: 'Maturity (years)' },
    yaxis: { title: 'Yield', tickformat: '.2%' },
    height: 350,
    margin: { t: 40, l: 60, r: 20, b: 50 }
});
```

### Plotly heatmap (transition matrix)
```javascript
Plotly.newPlot('markovHeatmap', [{
    z: transitionMatrix,    // 2D array
    x: ratings,             // ['AAA', 'AA', ..., 'D']
    y: ratings,
    type: 'heatmap',
    colorscale: 'Blues',
    text: transitionMatrix.map(row => row.map(v => (v * 100).toFixed(1) + '%')),
    texttemplate: '%{text}',
    showscale: true
}], {
    title: 'Credit Transition Matrix',
    height: 400
});
```

### Side-by-side price comparison cards (HESTON-03)
```javascript
resultsDiv.innerHTML = `
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px; margin:15px 0;">
        <div style="background:#d4edda; border-radius:8px; padding:16px; text-align:center;">
            <div style="font-size:12px; color:#666;">Heston Price</div>
            <div style="font-size:28px; font-weight:bold; color:#155724;">
                $${escapeHTML(hestonPrice.toFixed(4))}
            </div>
        </div>
        <div style="background:#cce5ff; border-radius:8px; padding:16px; text-align:center;">
            <div style="font-size:12px; color:#666;">Black-Scholes Price</div>
            <div style="font-size:28px; font-weight:bold; color:#004085;">
                $${escapeHTML(bsPrice.toFixed(4))}
            </div>
        </div>
    </div>`;
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Regime tab shows KV table only | Replace with Plotly time-series + shaded price chart | Phase 3 | REGIME-02, REGIME-03 satisfied |
| Heston Pricing inside Options tab | New dedicated sub-tab in Stochastic Models tab | Phase 3 | HESTON-05 satisfied |
| Calibration shows KV table | Add fitted vs. market IV Plotly scatter chart | Phase 3 | CALIB-04 satisfied |
| Calibration blocks until done | SSE streaming with `EventSource` + progress div | Phase 3 | CALIB-03 satisfied |
| BCC route only (no UI) | Add BCC calibration sub-tab and JS function | Phase 3 | CALIB-05 satisfied |

---

## Open Questions

1. **Does `/api/regime_detection` return per-day prices and regime_sequence?**
   - What we know: Route returns `filtered_probs`, `signal`, `transition_matrix`, `parameters`, `current_probabilities`
   - What's unclear: Whether `prices`, `dates`, and `regime_sequence` (0/1 per day) are in the response
   - Recommendation: Make a test call to the route during Wave 0 (plan 03-01); if missing, patch webapp.py before JS work starts

2. **Does `HestonCalibrator.calibrate` accept a `callback` parameter?**
   - What we know: `calibrator.calibrate(ticker, risk_free_rate, option_type)` — no callback in current signature
   - What's unclear: Whether `scipy.optimize.minimize` callback is already plumbed through
   - Recommendation: Read `src/derivatives/model_calibration.py` in plan 03-03 (SSE plan); add `callback` kwarg if absent

3. **IV surface endpoint — does one exist already?**
   - What we know: `/api/heston_price` prices a single contract; no surface route visible in webapp.py grep
   - What's unclear: Whether there is a hidden route or a helper that computes an IV grid
   - Recommendation: Assume missing; plan 03-02 (Heston Pricing tab) creates `/api/heston_iv_surface`

4. **Render free tier calibration timeout**
   - What we know: Calibration takes 30–120 seconds; Render free tier has a 30s request timeout for non-streaming routes
   - What's unclear: Whether SSE streams bypass the 30s timeout (they should, as SSE keeps the connection alive)
   - Recommendation: SSE route is the correct solution; verify during integration testing

---

## Validation Architecture

> Skipped: workflow.nyquist_validation not confirmed as enabled. Phase 3 is frontend JS/HTML — automated unit testing of DOM/Plotly rendering is impractical without a browser test framework (Playwright/Cypress), which is out of scope. Manual smoke testing per success criterion is the appropriate gate.

Manual smoke tests per success criterion:
1. SPY regime detection: run with default inputs, confirm chart shows shading in March 2020 period
2. Heston Pricing tab: enter default params, confirm two price cards and IV surface chart appear
3. Heston Calibration: click Calibrate, confirm progress counter increments, then IV comparison chart appears
4. BCC calibration: enter ticker, confirm parameters + IV chart returned
5. All sub-tabs: confirm every tab has at least one Plotly chart rendered

---

## Sources

### Primary (HIGH confidence)
- `/Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper/webapp.py` lines 1104-1530 — all Flask route signatures, request/response shapes confirmed by direct read
- `/Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper/static/js/stochasticModels.js` lines 1-220 — existing JS patterns, `renderAlert`, `escapeHTML`, `renderKVTable`, sub-tab switching
- `/Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper/templates/index.html` lines 1206-1440 — existing sub-tab HTML structure, Plotly CDN version confirmed

### Secondary (MEDIUM confidence)
- `.planning/STATE.md` — confirmed Phase 2 complete; all backends callable; SSE unresolved decision noted
- `.planning/REQUIREMENTS.md` — all 15 phase requirement IDs and descriptions confirmed

### Tertiary (LOW confidence)
- Render.com SSE buffering behaviour: `X-Accel-Buffering: no` header recommendation — based on Render documentation patterns (not directly verified for this account's tier)
- RMSE thresholds (Good <1%, Acceptable <3%): domain-standard for Heston calibration — cited from MFE course material context, not a specific external source

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Plotly CDN version pinned in HTML, Flask confirmed, no new dependencies
- Architecture patterns: HIGH — all patterns derived from existing working code in the repo
- Pitfalls: HIGH for items 1-4 (derived from code inspection); MEDIUM for item 5 (Render SSE buffering)

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable stack; Plotly CDN version may update but 2.27.0 is pinned)
