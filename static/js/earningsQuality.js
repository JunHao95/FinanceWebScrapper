/**
 * earningsQuality.js — Phase 14
 * Computes and renders the Earnings Quality sub-section inside the Deep Analysis group.
 *
 * Exposed API: window.EarningsQuality = { computeQuality, renderIntoGroup, clearSession }
 */
(function () {
    'use strict';

    // -------------------------------------------------------------------------
    // Helpers (replicated verbatim from healthScore.js closure pattern)
    // -------------------------------------------------------------------------

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

    // -------------------------------------------------------------------------
    // Core computation
    // -------------------------------------------------------------------------

    function computeQuality(data) {
        const ocf        = extractMetric(data, ['Operating Cash Flow', 'OCF', 'Cash from Operations']);
        const netIncome  = extractMetric(data, ['Net Income']);
        const totalAssets = extractMetric(data, ['Total Assets']);

        if (ocf === null || netIncome === null) {
            return {
                label: 'Insufficient Data',
                accrualsRatio: null,
                cashConversionRatio: null,
                consistencyFlag: null,
                consistencyTooltip: null
            };
        }

        // Accruals ratio: (Net Income - OCF) / Total Assets
        let accrualsRatio = null;
        if (totalAssets !== null && totalAssets !== 0) {
            accrualsRatio = (netIncome - ocf) / totalAssets;
        }

        // Cash conversion ratio: OCF / Net Income
        let cashConversionRatio = null;
        if (netIncome !== 0) {
            cashConversionRatio = ocf / netIncome;
        }

        // EPS consistency flag
        const epsGrowthRaw = extractMetric(data, ['EPS Growth This Year', 'EPS Growth QoQ', 'Earnings Growth', 'EPS Growth']);
        let consistencyFlag = null;
        let consistencyTooltip = null;
        if (epsGrowthRaw !== null) {
            // Stored as percent value (e.g. 18.3 from "18.30%") or decimal (0.183 from yfinance)
            // Treat any positive value as Consistent
            const pct = Math.abs(epsGrowthRaw) < 2 ? epsGrowthRaw * 100 : epsGrowthRaw; // normalise
            consistencyFlag = pct > 0 ? 'Consistent' : 'Volatile';
            consistencyTooltip = 'EPS growth: ' + (pct >= 0 ? '+' : '') + pct.toFixed(1) + '%';
        } else {
            consistencyFlag = 'N/A';
            consistencyTooltip = 'EPS growth data not available';
        }

        // Score label
        let score = 0;
        if (accrualsRatio !== null) {
            if (accrualsRatio < 0.05)  score += 1;
            if (accrualsRatio >= 0.10) score -= 1;
        }
        if (cashConversionRatio !== null) {
            if (cashConversionRatio >= 1.0) score += 1;
            if (cashConversionRatio < 0.5)  score -= 1;
        }

        let label;
        if (score >= 2)      label = 'High';
        else if (score === 1) label = 'Medium';
        else                  label = 'Low';

        return { label, accrualsRatio, cashConversionRatio, consistencyFlag, consistencyTooltip };
    }

    // -------------------------------------------------------------------------
    // HTML builder
    // -------------------------------------------------------------------------

    function buildHTML(result) {
        if (result.label === 'Insufficient Data') {
            return '<div class="earnings-quality-section" style="border-top: 1px solid #e8e8e8; margin-top: 8px; padding-top: 8px;">' +
                '<div class="metric-item">' +
                '<span class="metric-label">Earnings Quality</span>' +
                '<span class="metric-value" style="color:#999;">Insufficient Data</span>' +
                '</div>' +
                '</div>';
        }

        const badgeClass = result.label === 'High'   ? 'badge-success' :
                           result.label === 'Medium' ? 'badge-warning'  : 'badge-danger';

        const accrualsDisplay = result.accrualsRatio !== null ? result.accrualsRatio.toFixed(2) : 'N/A';
        const ccrDisplay      = result.cashConversionRatio !== null ? result.cashConversionRatio.toFixed(2) : 'N/A';
        const consistencyDisplay = result.consistencyFlag || 'N/A';
        const tooltipAttr = result.consistencyTooltip
            ? ' title="' + result.consistencyTooltip.replace(/"/g, '&quot;') + '"'
            : '';

        return '<div class="earnings-quality-section" style="border-top: 1px solid #e8e8e8; margin-top: 8px; padding-top: 8px;">' +
            '<div class="metric-group">' +
            '<div class="metric-item">' +
            '<span class="metric-label">Earnings Quality</span>' +
            '<span class="metric-value"><span class="badge ' + badgeClass + '">' + result.label + '</span></span>' +
            '</div>' +
            '<div class="metric-item">' +
            '<span class="metric-label">Accruals Ratio</span>' +
            '<span class="metric-value">' + accrualsDisplay + '</span>' +
            '</div>' +
            '<div class="metric-item">' +
            '<span class="metric-label">Cash Conversion</span>' +
            '<span class="metric-value">' + ccrDisplay + '</span>' +
            '</div>' +
            '<div class="metric-item">' +
            '<span class="metric-label">EPS Consistency</span>' +
            '<span class="metric-value">' + consistencyDisplay +
            (result.consistencyTooltip ? ' <span' + tooltipAttr + ' style="cursor:help; color:#999; font-size:11px;"> (?)</span>' : '') +
            '</span>' +
            '</div>' +
            '</div>' +
            '</div>';
    }

    // -------------------------------------------------------------------------
    // Render into deep-analysis group
    // -------------------------------------------------------------------------

    function renderIntoGroup(ticker, data, cardRoot) {
        const container = cardRoot.querySelector('#deep-analysis-content-' + ticker);
        if (!container) return;

        const result = computeQuality(data);
        const section = document.createElement('div');
        section.innerHTML = buildHTML(result);
        container.appendChild(section);
    }

    // -------------------------------------------------------------------------
    // Session state (none needed; mirrors HealthScore pattern)
    // -------------------------------------------------------------------------

    function clearSession() {
        // No session state to clear for earnings quality
    }

    // -------------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------------

    window.EarningsQuality = { computeQuality, renderIntoGroup, clearSession };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.EarningsQuality;
    }
}());
