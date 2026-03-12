// ---------------------------------------------------------------------------
// portfolioHealth.js — Portfolio Health summary card
// Exposes: window.PortfolioHealth = { initCard, updateRegime }
// ---------------------------------------------------------------------------

const BADGE_RUNNING_STYLE = 'background:#6c757d;color:white;border-radius:10px;padding:2px 8px;font-size:11px;';
const BADGE_RISK_ON  = 'background:#28a745;color:white;border-radius:10px;padding:2px 8px;font-size:11px;cursor:pointer;';
const BADGE_RISK_OFF = 'background:#dc3545;color:white;border-radius:10px;padding:2px 8px;font-size:11px;cursor:pointer;';
const BADGE_FAILED_STYLE = 'background:#adb5bd;color:white;border-radius:10px;padding:2px 8px;font-size:11px;';

// ---------------------------------------------------------------------------
// Module-level state
// ---------------------------------------------------------------------------

let _regimeMap  = {};   // { TICKER: 'RISK_ON' | 'RISK_OFF' | null | undefined }
let _tickerList = [];   // copy of tickers passed to initCard

// ---------------------------------------------------------------------------
// Private: VaR extraction from analyticsData
// ---------------------------------------------------------------------------

function _extractVaR(analyticsData, tickers) {
    let mc = null;
    if (tickers.length >= 2 && analyticsData.portfolio_monte_carlo) {
        mc = analyticsData.portfolio_monte_carlo;
    } else if (tickers.length === 1 && analyticsData[tickers[0]] && analyticsData[tickers[0]].monte_carlo) {
        mc = analyticsData[tickers[0]].monte_carlo;
    }
    if (!mc) return null;

    // Primary path: mc.VaR['VaR at 95% confidence'].Percentage / 100
    if (mc.VaR) {
        const key95 = Object.keys(mc.VaR).find(k => k.includes('95'));
        if (key95 && mc.VaR[key95] != null && mc.VaR[key95].Percentage != null) {
            return mc.VaR[key95].Percentage / 100;
        }
    }
    // Fallback: mc.var_95
    if (mc.var_95 != null) return mc.var_95;
    return null;
}

// ---------------------------------------------------------------------------
// Private: Sharpe async fetch
// ---------------------------------------------------------------------------

async function _fetchSharpe(tickers, allocations) {
    try {
        const today = new Date();
        const endDate   = today.toISOString().slice(0, 10);
        const d2y = new Date(today);
        d2y.setFullYear(d2y.getFullYear() - 2);
        const startDate = d2y.toISOString().slice(0, 10);

        const resp = await fetch('/api/portfolio_sharpe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tickers:    tickers,
                weights:    allocations || {},
                start_date: startDate,
                end_date:   endDate
            })
        });
        const data = await resp.json();
        const el = document.getElementById('healthSharpeValue');
        if (!el) return;

        if (!resp.ok || data.error) {
            el.textContent = '\u2014';
        } else {
            el.textContent = Number(data.sharpe).toFixed(2);
        }
    } catch (e) {
        const el = document.getElementById('healthSharpeValue');
        if (el) el.textContent = '\u2014';
    }
}

// ---------------------------------------------------------------------------
// Private: Summary update after all regimes resolve
// ---------------------------------------------------------------------------

function _maybeUpdateSummary() {
    // Return early if any ticker is still pending (undefined = not yet received)
    for (const t of _tickerList) {
        if (_regimeMap[t] === undefined) return;
    }

    // Compute traffic-light
    const labels   = Object.values(_regimeMap).filter(v => v !== null);
    const offCount = labels.filter(l => l === 'RISK_OFF').length;

    let trafficEmoji = '\u26aa'; // grey circle (all failed / no data)
    if (labels.length > 0) {
        if (offCount === 0) {
            trafficEmoji = '\u2705';         // green check
        } else if (offCount === labels.length) {
            trafficEmoji = '\ud83d\udd34';   // red circle
        } else {
            trafficEmoji = '\ud83d\udfe1';   // amber circle
        }
    }
    const trafficEl = document.getElementById('healthTrafficLight');
    if (trafficEl) trafficEl.textContent = trafficEmoji;

    // Build one-line summary
    const riskOff = _tickerList.filter(t => _regimeMap[t] === 'RISK_OFF');
    const riskOn  = _tickerList.filter(t => _regimeMap[t] === 'RISK_ON');

    let summaryText = '';
    if (riskOff.length === 0 && riskOn.length > 0) {
        summaryText = 'All holdings in risk-on regime \u2014 portfolio positioned well.';
    } else if (riskOff.length === _tickerList.length && _tickerList.length > 0) {
        summaryText = 'All holdings in risk-off regime \u2014 consider defensive rebalancing or cash.';
    } else if (riskOff.length > 0) {
        const names = riskOff.join(', ');
        const safe  = riskOn.length > 0 ? ` Rebalancing toward ${riskOn[0]} may reduce exposure.` : '';
        summaryText = `Mixed regime detected \u2014 ${names} in risk-off.${safe}`;
    }

    const summaryEl = document.getElementById('healthSummaryText');
    if (summaryEl) summaryEl.textContent = summaryText;
}

// ---------------------------------------------------------------------------
// Public: initCard — called from stockScraper.js displayResults()
// ---------------------------------------------------------------------------

function initCard(tickers, analyticsData, allocations) {
    // Re-run guard: remove any existing card
    document.getElementById('portfolioHealthCard')?.remove();

    // Reset module state
    _tickerList = [...tickers];
    _regimeMap  = {};
    _tickerList.forEach(t => { _regimeMap[t] = undefined; });

    // Extract VaR synchronously from analytics data already in memory
    const varValue = _extractVaR(analyticsData || {}, tickers);
    const varDisplay = varValue != null
        ? (varValue * 100).toFixed(1) + '%'
        : '\u2014';

    // Build regime badge HTML for each ticker
    let regimeBadgesHTML = '';
    _tickerList.forEach(t => {
        regimeBadgesHTML += `
            <div style="display:flex;flex-direction:column;align-items:flex-start;gap:4px;">
                <span style="font-size:11px;color:#888;font-weight:500;">${t}</span>
                <span
                    id="healthRegimeBadge_${t}"
                    style="${BADGE_RUNNING_STYLE}"
                    onclick="if(window.TabManager)TabManager.switchTab('autoanalysis')"
                >Analyzing...</span>
            </div>`;
    });

    const cardHTML = `
<div id="portfolioHealthCard" style="background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin-bottom:16px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
        <span id="healthTrafficLight" style="font-size:18px;" title="Overall portfolio regime">\u26aa</span>
        <strong style="font-size:15px;color:#333;">Portfolio Health</strong>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start;margin-bottom:10px;">
        <div style="display:flex;flex-direction:column;align-items:flex-start;gap:4px;">
            <span style="font-size:11px;color:#888;font-weight:500;">VaR (95%)</span>
            <span
                id="healthVarValue"
                style="font-size:14px;font-weight:600;color:#333;cursor:pointer;text-decoration:underline dotted;"
                onclick="if(window.TabManager){TabManager.switchTab('analytics');var el=document.getElementById('analyticsVarSection');if(el){el.scrollIntoView({behavior:'smooth'});el.style.transition='box-shadow 0.8s';el.style.boxShadow='0 0 0 3px #667eea';setTimeout(function(){el.style.boxShadow='';},800);}}"
                title="Click to jump to Monte Carlo / VaR section"
            >${varDisplay}</span>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-start;gap:4px;">
            <span style="font-size:11px;color:#888;font-weight:500;">Sharpe (2yr)</span>
            <span
                id="healthSharpeValue"
                style="font-size:14px;font-weight:600;color:#333;cursor:pointer;text-decoration:underline dotted;"
                onclick="if(window.TabManager){TabManager.switchTab('analytics');var el=document.getElementById('analyticsSharpeSection')||document.getElementById('analyticsVarSection')||document.getElementById('analyticsTabContent');if(el){el.scrollIntoView({behavior:'smooth'});el.style.transition='box-shadow 0.8s';el.style.boxShadow='0 0 0 3px #667eea';setTimeout(function(){el.style.boxShadow='';},800);}}"
                title="Click to jump to Sharpe / Correlation section"
            >Computing...</span>
        </div>
        ${regimeBadgesHTML}
    </div>
    <div id="healthSummaryText" style="font-size:12px;color:#555;margin-top:4px;"></div>
</div>`;

    // Insert card immediately before .tabs-container inside #resultsSection
    const resultsSection = document.getElementById('resultsSection');
    if (!resultsSection) return;
    const tabsContainer = resultsSection.querySelector('.tabs-container');
    if (!tabsContainer) return;
    tabsContainer.insertAdjacentHTML('beforebegin', cardHTML);

    // Kick off async Sharpe fetch
    _fetchSharpe(tickers, allocations);
}

// ---------------------------------------------------------------------------
// Public: updateRegime — called from autoRun.js after each runAutoRegime()
// ---------------------------------------------------------------------------

function updateRegime(ticker, label) {
    const badge = document.getElementById('healthRegimeBadge_' + ticker);
    if (!badge) return;

    _regimeMap[ticker] = label;

    if (label === 'RISK_ON') {
        badge.setAttribute('style', BADGE_RISK_ON);
        badge.textContent = 'RISK_ON \ud83d\udfe2';
    } else if (label === 'RISK_OFF') {
        badge.setAttribute('style', BADGE_RISK_OFF);
        badge.textContent = 'RISK_OFF \ud83d\udd34';
    } else {
        badge.setAttribute('style', BADGE_FAILED_STYLE);
        badge.textContent = '\u2014';
    }

    _maybeUpdateSummary();
}

// ---------------------------------------------------------------------------
// Public: getRegimeMap / getTickerList — consumed by RL tab (Phase 10+)
// ---------------------------------------------------------------------------

function getRegimeMap()  { return { ..._regimeMap };  }
function getTickerList() { return [..._tickerList]; }

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

window.PortfolioHealth = { initCard, updateRegime, getRegimeMap, getTickerList };
