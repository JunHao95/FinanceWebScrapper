/**
 * healthScore.js — Financial Health Score module (Phase 13)
 * Pure client-side scoring. No network calls, no Flask routes.
 * Exposes: window.HealthScore = { computeGrade, toggleDeepAnalysis, clearSession }
 */
(function () {
    'use strict';

    // Session state: tracks which tickers are currently expanded
    const _expandedTickers = new Set();

    // ---------------------------------------------------------------------------
    // Internal helpers
    // ---------------------------------------------------------------------------

    function parseNumeric(val) {
        if (val === null || val === undefined || val === '' || val === 'N/A' || val === 'N/A%') return null;
        if (typeof val === 'number') return isNaN(val) ? null : val;
        const s = String(val).trim();
        // Strip leading $
        let cleaned = s.replace(/^\$/, '');
        // Handle B/M/K multipliers
        const multipliers = { 'B': 1e9, 'M': 1e6, 'K': 1e3 };
        const lastChar = cleaned.slice(-1).toUpperCase();
        if (multipliers[lastChar]) {
            const n = parseFloat(cleaned.slice(0, -1));
            return isNaN(n) ? null : n * multipliers[lastChar];
        }
        // Strip trailing %
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

    function numericToLetter(n) {
        if (n === null || n === undefined) return null;
        const map = { 4: 'A', 3: 'B', 2: 'C', 1: 'D', 0: 'F' };
        return map[Math.max(0, Math.min(4, Math.round(n)))] || null;
    }

    function gradeClass(letter) {
        const map = { 'A': 'badge-success', 'B': 'badge-info', 'C': 'badge-warning', 'D': 'badge-warning', 'F': 'badge-danger' };
        return map[letter] || 'badge-warning';
    }

    // ---------------------------------------------------------------------------
    // Sub-scorers
    // ---------------------------------------------------------------------------

    function scoreLiquidity(data) {
        const currentRatio = extractMetric(data, ['Current Ratio']);
        const quickRatio = extractMetric(data, ['Quick Ratio']);
        if (currentRatio === null && quickRatio === null) {
            return { name: 'Liquidity', letter: null, numericScore: null, rawValues: {}, missing: true };
        }
        let score = 2; // C baseline
        if (currentRatio !== null) {
            if (currentRatio >= 2.0) score += 1;
            else if (currentRatio < 1.0) score -= 1;
        }
        if (quickRatio !== null) {
            if (quickRatio >= 1.5) score += 1;
            else if (quickRatio < 0.5) score -= 1;
        }
        score = Math.max(0, Math.min(4, score));
        const missing = (currentRatio === null || quickRatio === null);
        return {
            name: 'Liquidity',
            letter: numericToLetter(score),
            numericScore: score,
            rawValues: { 'CR': currentRatio, 'QR': quickRatio },
            missing
        };
    }

    function scoreLeverage(data) {
        const debtEquity = extractMetric(data, ['Debt to Equity', 'D/E', 'Debt/Equity', 'Debt-to-Equity', 'Total Debt/Equity']);
        if (debtEquity === null) {
            return { name: 'Leverage', letter: null, numericScore: null, rawValues: {}, missing: true };
        }
        let score;
        if (debtEquity < 0.5) score = 4;
        else if (debtEquity < 1.0) score = 3;
        else if (debtEquity < 2.0) score = 2;
        else if (debtEquity < 3.0) score = 1;
        else score = 0;
        return {
            name: 'Leverage',
            letter: numericToLetter(score),
            numericScore: score,
            rawValues: { 'D/E': debtEquity },
            missing: false
        };
    }

    function scoreProfitability(data) {
        const roe = extractMetric(data, ['ROE', 'Return on Equity', 'Return On Equity', 'ROE %']);
        const profitMargin = extractMetric(data, ['Profit Margin', 'Net Margin', 'Net Profit Margin']);
        const roa = extractMetric(data, ['ROA', 'Return on Assets']);
        if (roe === null && profitMargin === null && roa === null) {
            return { name: 'Profitability', letter: null, numericScore: null, rawValues: {}, missing: true };
        }
        let score = 2; // C baseline
        if (roe !== null) {
            if (roe > 20) score += 1;
            else if (roe < 5) score -= 1;
        }
        if (profitMargin !== null) {
            if (profitMargin > 20) score += 1;
            else if (profitMargin < 0) score -= 1;
        }
        if (roa !== null) {
            if (roa > 10) score += 1;
            else if (roa < 2) score -= 1;
        }
        score = Math.max(0, Math.min(4, score));
        const missing = (roe === null || profitMargin === null || roa === null);
        return {
            name: 'Profitability',
            letter: numericToLetter(score),
            numericScore: score,
            rawValues: { 'ROE': roe, 'Margin': profitMargin, 'ROA': roa },
            missing
        };
    }

    function scoreGrowth(data) {
        const revenueGrowth = extractMetric(data, ['Revenue Growth', 'Sales Growth']);
        const earningsGrowth = extractMetric(data, ['Earnings Growth', 'EPS Growth']);
        if (revenueGrowth === null && earningsGrowth === null) {
            return { name: 'Growth', letter: null, numericScore: null, rawValues: {}, missing: true };
        }
        let score = 2; // C baseline
        if (revenueGrowth !== null) {
            if (revenueGrowth > 20) score += 1;
            else if (revenueGrowth < 0) score -= 1;
        }
        if (earningsGrowth !== null) {
            if (earningsGrowth > 15) score += 1;
            else if (earningsGrowth < 0) score -= 1;
        }
        score = Math.max(0, Math.min(4, score));
        const missing = (revenueGrowth === null || earningsGrowth === null);
        return {
            name: 'Growth',
            letter: numericToLetter(score),
            numericScore: score,
            rawValues: { 'RevG': revenueGrowth, 'EpsG': earningsGrowth },
            missing
        };
    }

    // ---------------------------------------------------------------------------
    // Explanation builder
    // ---------------------------------------------------------------------------

    function buildExplanation(subScores) {
        const available = subScores.filter(s => s.numericScore !== null);
        if (available.length === 0) return 'Insufficient data to generate explanation.';

        const sorted = [...available].sort((a, b) => b.numericScore - a.numericScore);
        const best = sorted[0];
        const worst = sorted[sorted.length - 1];

        if (best.numericScore === worst.numericScore) return 'Balanced financial profile.';

        const positiveDrivers = available.filter(s => s.numericScore >= 3); // B or above
        const negativeDrivers = available.filter(s => s.numericScore <= 1); // D or below

        if (positiveDrivers.length > 0 && negativeDrivers.length > 0) {
            return `Strong ${best.name} offset by weak ${worst.name}.`;
        } else if (positiveDrivers.length > 0) {
            return `Strong financial profile led by ${best.name}.`;
        } else if (negativeDrivers.length > 0) {
            return `Weak ${worst.name} is a key concern.`;
        }
        return 'Moderate financial health across all dimensions.';
    }

    // ---------------------------------------------------------------------------
    // HTML builder
    // ---------------------------------------------------------------------------

    function formatRawValues(rawValues) {
        const pairs = Object.entries(rawValues)
            .filter(([, v]) => v !== null && v !== undefined)
            .slice(0, 2)
            .map(([k, v]) => `${k} ${typeof v === 'number' ? v.toFixed(1) : v}`);
        return pairs.length > 0 ? ' — ' + pairs.join(' / ') : '';
    }

    function buildSubScoreRow(subScore) {
        const { name, letter, missing, rawValues } = subScore;
        const cls = letter ? gradeClass(letter) : 'badge-warning';
        const badge = letter
            ? `<span class="badge ${cls}">${letter}</span>`
            : '<span style="color:#999;">N/A</span>';
        const rawStr = formatRawValues(rawValues || {});
        const label = `${name}${missing ? ' ⚠' : ''}`;
        return `<div class="metric-item">` +
            `<span class="metric-label">${label}</span>` +
            `<span class="metric-value">${badge}${rawStr}</span>` +
            `</div>`;
    }

    function buildHTML(overallLetter, cls, subScores, explanation, ticker, isExpanded) {
        const displayStyle = isExpanded ? 'block' : 'none';
        const chevron = isExpanded ? '▲' : '▼';
        const grade = overallLetter || 'N/A';
        const subRows = subScores.map(buildSubScoreRow).join('');

        return `<div class="deep-analysis-group" id="deep-analysis-group-${ticker}" style="border-top: 1px solid #e0e0e0; margin-top: 12px; padding-top: 10px;">` +
            `<div class="deep-analysis-header" style="display:flex; justify-content:space-between; align-items:center; cursor:pointer; padding:6px 0;" onclick="HealthScore.toggleDeepAnalysis('${ticker}')">` +
            `<span>🏥 Financial Health: <span class="badge ${cls}">${grade}</span></span>` +
            `<span class="deep-analysis-chevron" id="deep-analysis-chevron-${ticker}" style="transition:transform 0.3s;">${chevron}</span>` +
            `</div>` +
            `<div class="deep-analysis-content" id="deep-analysis-content-${ticker}" style="display:${displayStyle}; padding: 8px 0;">` +
            `<div class="metric-group">${subRows}</div>` +
            `<p style="margin:6px 0 0; font-size:13px; color:#555;">${explanation}</p>` +
            `</div>` +
            `</div>`;
    }

    // ---------------------------------------------------------------------------
    // Public API
    // ---------------------------------------------------------------------------

    function computeGrade(data, ticker) {
        ticker = ticker || 'unknown';
        const liq = scoreLiquidity(data);
        const lev = scoreLeverage(data);
        const prof = scoreProfitability(data);
        const growth = scoreGrowth(data);
        const subScores = [liq, lev, prof, growth];

        const available = subScores.filter(s => s.numericScore !== null);
        const overallNumeric = available.length > 0
            ? available.reduce((sum, s) => sum + s.numericScore, 0) / available.length
            : null;
        const overallLetter = overallNumeric !== null ? numericToLetter(Math.round(overallNumeric)) : null;
        const cls = gradeClass(overallLetter);
        const explanation = buildExplanation(subScores);
        const warnings = subScores.filter(s => s.missing).map(s => `${s.name} data incomplete`);
        const isExpanded = _expandedTickers.has(ticker);
        const html = buildHTML(overallLetter, cls, subScores, explanation, ticker, isExpanded);

        return { grade: overallLetter, subScores, explanation, warnings, html };
    }

    function toggleDeepAnalysis(ticker) {
        const content = document.getElementById('deep-analysis-content-' + ticker);
        const chevron = document.getElementById('deep-analysis-chevron-' + ticker);
        if (!content) return;

        if (content.style.display === 'none') {
            content.style.display = 'block';
            _expandedTickers.add(ticker);
            if (chevron) chevron.textContent = '▲';
        } else {
            content.style.display = 'none';
            _expandedTickers.delete(ticker);
            if (chevron) chevron.textContent = '▼';
        }
    }

    function clearSession() {
        _expandedTickers.clear();
    }

    // Attach to window
    window.HealthScore = { computeGrade, toggleDeepAnalysis, clearSession };

    // CommonJS export for testability
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.HealthScore;
    }
}());
