/**
 * dcfValuation.js — Phase 15
 * Computes and renders a 2-stage FCF-based DCF valuation inside the Deep Analysis group.
 *
 * Exposed API: window.DCFValuation = { computeValuation, renderIntoGroup, clearSession }
 */
(function () {
    'use strict';

    // -------------------------------------------------------------------------
    // Helpers (replicated from earningsQuality.js, with comma-stripping added)
    // -------------------------------------------------------------------------

    function parseNumeric(val) {
        if (val === null || val === undefined || val === '' || val === 'N/A' || val === 'N/A%') return null;
        if (typeof val === 'number') return isNaN(val) ? null : val;
        let s = String(val).trim();
        // Strip commas — critical for Market Cap (Yahoo) and Free Cash Flow (Yahoo)
        s = s.replace(/,/g, '');
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

    // -------------------------------------------------------------------------
    // Module-level data cache (keyed by ticker)
    // -------------------------------------------------------------------------

    const _dataCache = {};

    // -------------------------------------------------------------------------
    // Core DCF computation
    // -------------------------------------------------------------------------

    /**
     * computeValuation(data, wacc, g1, g2)
     *
     * 2-stage FCF DCF:
     *   Stage 1 — 5-year explicit FCF projection at growth rate g1, discounted at wacc
     *   Stage 2 — Gordon Growth terminal value from year-5 FCF, discounted at wacc
     *
     * Returns an object with:
     *   { intrinsicEquityTotal, intrinsicPerShare, premium, fcfSource }
     * or on error:
     *   { error: <string>, fcfSource }
     */
    function computeValuation(data, wacc, g1, g2) {
        // 1. Extract FCF — AlphaVantage first, Yahoo fallback
        const avFcf  = extractMetric(data, ['Free Cash Flow (AlphaVantage)']);
        const yfFcf  = extractMetric(data, ['Free Cash Flow (Yahoo)']);
        let fcf0, fcfSource;
        if (avFcf !== null && avFcf !== 0) {
            fcf0      = avFcf;
            fcfSource = 'Alpha Vantage';
        } else {
            fcf0      = yfFcf;
            fcfSource = yfFcf !== null ? 'Yahoo' : null;
        }

        // 2. Guard: missing / zero FCF
        if (fcf0 === null || fcf0 === 0) {
            return { error: 'FCF data missing', fcfSource: null };
        }

        // 3. Guard: WACC must exceed terminal growth rate
        if (wacc <= g2) {
            return { error: 'WACC must exceed terminal growth rate', fcfSource };
        }

        // 4. Stage 1 — 5-year explicit projection
        let stage1PV = 0;
        let fcf5     = fcf0;
        for (let t = 1; t <= 5; t++) {
            const fcft = fcf0 * Math.pow(1 + g1, t);
            stage1PV  += fcft / Math.pow(1 + wacc, t);
            if (t === 5) fcf5 = fcft;
        }

        // 5. Stage 2 — Terminal value (Gordon Growth)
        const terminal        = fcf5 * (1 + g2) / (wacc - g2);
        const pvTerminal      = terminal / Math.pow(1 + wacc, 5);
        const intrinsicEquityTotal = stage1PV + pvTerminal;

        // 6. Per-share value (requires Market Cap + Current Price to derive shares)
        const marketCap    = extractMetric(data, ['Market Cap (Yahoo)']);
        const currentPrice = extractMetric(data, ['Current Price (Yahoo)', 'Current Price']);

        let intrinsicPerShare = null;
        let premium           = null;

        if (marketCap !== null && currentPrice !== null && currentPrice !== 0) {
            const sharesOut      = marketCap / currentPrice;
            intrinsicPerShare    = intrinsicEquityTotal / sharesOut;
            premium              = (currentPrice - intrinsicPerShare) / intrinsicPerShare * 100;
        }

        return { intrinsicEquityTotal, intrinsicPerShare, premium, fcfSource };
    }

    // -------------------------------------------------------------------------
    // HTML builder
    // -------------------------------------------------------------------------

    function buildHTML(ticker, result, defaultWacc, defaultG1, defaultG2) {
        if (result.error === 'FCF data missing') {
            return '<div class="dcf-section" style="border-top:1px solid #e8e8e8;margin-top:8px;padding-top:8px;">' +
                '<div class="metric-item">' +
                '<span class="badge badge-warning">DCF unavailable \u2014 FCF data missing</span>' +
                '</div>' +
                '</div>';
        }

        if (result.error) {
            return '<div class="dcf-section" style="border-top:1px solid #e8e8e8;margin-top:8px;padding-top:8px;">' +
                '<div class="metric-item">' +
                '<span class="metric-label">DCF Valuation</span>' +
                '<span class="metric-value" style="color:#c0392b;">' + result.error + '</span>' +
                '</div>' +
                '</div>';
        }

        const equityTotalB = (result.intrinsicEquityTotal / 1e9).toFixed(2);

        // Header label
        let headerLabel;
        if (result.intrinsicPerShare !== null) {
            headerLabel = '\uD83D\uDCB0 DCF Value: $' + result.intrinsicPerShare.toFixed(2) + '  \u25BC';
        } else {
            headerLabel = '\uD83D\uDCB0 DCF Value: ($' + equityTotalB + 'B equity)  \u25BC';
        }

        // Premium / discount badge
        let premiumHTML = '';
        if (result.premium !== null) {
            const isDiscount   = result.premium < 0;
            const badgeClass   = isDiscount ? 'badge-success' : 'badge-danger';
            const sign         = isDiscount ? '' : '+';
            const label        = isDiscount ? 'Discount' : 'Premium';
            premiumHTML =
                '<div class="metric-item">' +
                '<span class="metric-label">vs Current Price</span>' +
                '<span class="metric-value">' +
                '<span class="badge ' + badgeClass + '">' + label + ' ' + sign + result.premium.toFixed(1) + '%</span>' +
                '</span></div>';
        }

        // Intrinsic value row
        let intrinsicRow = '';
        if (result.intrinsicPerShare !== null) {
            intrinsicRow =
                '<div class="metric-item">' +
                '<span class="metric-label">Intrinsic / Share</span>' +
                '<span class="metric-value" id="dcf-result-' + ticker + '">$' + result.intrinsicPerShare.toFixed(2) + '</span>' +
                '</div>';
        } else {
            intrinsicRow =
                '<div class="metric-item">' +
                '<span class="metric-label">Intrinsic Equity</span>' +
                '<span class="metric-value" id="dcf-result-' + ticker + '">$' + equityTotalB + 'B</span>' +
                '</div>';
        }

        const waccPct = (defaultWacc * 100).toFixed(1);
        const g1Pct   = (defaultG1 * 100).toFixed(1);
        const g2Pct   = (defaultG2 * 100).toFixed(1);

        const fcfNote = result.fcfSource
            ? '<div class="metric-item"><span class="metric-label" style="color:#999;font-size:11px;">FCF source: ' + result.fcfSource + '</span></div>'
            : '';

        return '<div class="dcf-section" style="border-top:1px solid #e8e8e8;margin-top:8px;padding-top:8px;">' +
            '<div class="metric-group">' +
            // Collapsed toggle header
            '<div class="metric-item" onclick="this.parentElement.querySelector(\'.dcf-body\').style.display = this.parentElement.querySelector(\'.dcf-body\').style.display===\'none\' ? \'\' : \'none\'; this.querySelector(\'.dcf-toggle\').textContent = this.querySelector(\'.dcf-toggle\').textContent.includes(\'▼\') ? \'' + headerLabel.replace('▼', '▲') + '\' : \'' + headerLabel + '\';" style="cursor:pointer;">' +
            '<span class="metric-label dcf-toggle">' + headerLabel + '</span>' +
            '</div>' +
            // Collapsible body
            '<div class="dcf-body">' +
            intrinsicRow +
            premiumHTML +
            '<div id="dcf-premium-' + ticker + '" style="display:none;"></div>' +
            fcfNote +
            // Assumption inputs
            '<div class="metric-item" style="flex-wrap:wrap;gap:4px;align-items:center;">' +
            '<span class="metric-label">Assumptions</span>' +
            '<span class="metric-value" style="display:flex;gap:6px;font-size:11px;align-items:center;">' +
            'WACC <input id="dcf-wacc-' + ticker + '" type="number" value="' + waccPct + '" step="0.5" style="width:46px;padding:1px 4px;font-size:11px;"> % &nbsp;' +
            'g1 <input id="dcf-g1-' + ticker + '" type="number" value="' + g1Pct + '" step="0.5" style="width:46px;padding:1px 4px;font-size:11px;"> % &nbsp;' +
            'g2 <input id="dcf-g2-' + ticker + '" type="number" value="' + g2Pct + '" step="0.5" style="width:46px;padding:1px 4px;font-size:11px;"> %' +
            '</span>' +
            '</div>' +
            '<div class="metric-item">' +
            '<button onclick="DCFValuation._recalculate(\'' + ticker + '\')" style="font-size:11px;padding:2px 8px;cursor:pointer;">Recalculate</button>' +
            '</div>' +
            '</div>' + // .dcf-body
            '</div>' + // .metric-group
            '</div>';  // .dcf-section
    }

    // -------------------------------------------------------------------------
    // Render into deep-analysis group
    // -------------------------------------------------------------------------

    function renderIntoGroup(ticker, data, cardRoot) {
        const container = cardRoot.querySelector('#deep-analysis-content-' + ticker);
        if (!container) return;

        // Cache data for recalculate
        _dataCache[ticker] = data;

        const result  = computeValuation(data, 0.10, 0.10, 0.03);
        const section = document.createElement('div');
        section.innerHTML = buildHTML(ticker, result, 0.10, 0.10, 0.03);
        container.appendChild(section);
    }

    // -------------------------------------------------------------------------
    // Recalculate (called from inline onclick on Recalculate button)
    // -------------------------------------------------------------------------

    function _recalculate(ticker) {
        const waccEl = document.getElementById('dcf-wacc-' + ticker);
        const g1El   = document.getElementById('dcf-g1-' + ticker);
        const g2El   = document.getElementById('dcf-g2-' + ticker);
        const resEl  = document.getElementById('dcf-result-' + ticker);

        if (!waccEl || !g1El || !g2El || !resEl) return;

        const wacc = parseFloat(waccEl.value) / 100;
        const g1   = parseFloat(g1El.value)   / 100;
        const g2   = parseFloat(g2El.value)   / 100;
        const data = _dataCache[ticker];

        if (!data) return;

        const result = computeValuation(data, wacc, g1, g2);

        if (result.error) {
            resEl.textContent = result.error;
            return;
        }

        const equityTotalB = (result.intrinsicEquityTotal / 1e9).toFixed(2);

        if (result.intrinsicPerShare !== null) {
            resEl.textContent = '$' + result.intrinsicPerShare.toFixed(2);
        } else {
            resEl.textContent = '$' + equityTotalB + 'B';
        }

        // Update premium badge if present
        const premiumEl = document.getElementById('dcf-premium-' + ticker);
        if (premiumEl && result.premium !== null) {
            const isDiscount = result.premium < 0;
            const badgeClass = isDiscount ? 'badge-success' : 'badge-danger';
            const sign       = isDiscount ? '' : '+';
            const label      = isDiscount ? 'Discount' : 'Premium';
            premiumEl.style.display = '';
            premiumEl.innerHTML =
                '<div class="metric-item">' +
                '<span class="metric-label">vs Current Price</span>' +
                '<span class="metric-value"><span class="badge ' + badgeClass + '">' +
                label + ' ' + sign + result.premium.toFixed(1) + '%' +
                '</span></span></div>';
        }
    }

    // -------------------------------------------------------------------------
    // Session state
    // -------------------------------------------------------------------------

    function clearSession() {
        // No persistent session state; _dataCache resets on page reload
    }

    // -------------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------------

    const publicAPI = { computeValuation, renderIntoGroup, clearSession };

    if (typeof window !== 'undefined') {
        window.DCFValuation = publicAPI;
        window.DCFValuation._recalculate = _recalculate;
    }

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = publicAPI;
    }
}());
