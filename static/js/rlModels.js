/**
 * Reinforcement Learning Models Module  (M6)
 * Sub-tabs: Investment MDP · Gridworld · Portfolio Rotation PI · Portfolio Rotation QL
 */

// ---------------------------------------------------------------------------
// Sub-tab switching
// ---------------------------------------------------------------------------
function switchRLTab(tabName) {
    document.querySelectorAll('.rl-content').forEach(el => { el.style.display = 'none'; });
    document.querySelectorAll('[id^="rlTab_"]').forEach(btn => { btn.classList.remove('active'); });
    const content = document.getElementById('rlContent_' + tabName);
    if (content) content.style.display = 'block';
    const btn = document.getElementById('rlTab_' + tabName);
    if (btn) btn.classList.add('active');
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------
function rlEscapeHTML(str) {
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function rlAlert(msg, type = 'error') {
    const bg = { error: '#f8d7da', info: '#d1ecf1', success: '#d4edda', warning: '#fff3cd' }[type] || '#f8d7da';
    const br = { error: '#f5c6cb', info: '#bee5eb', success: '#c3e6cb', warning: '#ffeeba' }[type] || '#f5c6cb';
    return `<div style="background:${bg};border:1px solid ${br};padding:12px;border-radius:4px;margin-top:10px;">${rlEscapeHTML(msg)}</div>`;
}

function rlSpinner(containerId) {
    document.getElementById(containerId).innerHTML =
        '<div style="text-align:center;padding:20px;"><div class="spinner" style="display:inline-block;width:30px;height:30px;border:4px solid #f3f3f3;border-top:4px solid #667eea;border-radius:50%;animation:spin 1s linear infinite;"></div><p style="margin-top:10px;color:#666;">Computing…</p></div>';
    document.getElementById(containerId).style.display = 'block';
}

function rlKVTable(obj) {
    let rows = Object.entries(obj).map(([k, v]) => {
        const val = typeof v === 'number' ? v.toFixed(4) : rlEscapeHTML(String(v));
        return `<tr><td style="padding:4px 10px;font-weight:600;">${rlEscapeHTML(k)}</td><td style="padding:4px 10px;">${val}</td></tr>`;
    }).join('');
    return `<table style="border-collapse:collapse;font-size:13px;width:100%"><tbody>${rows}</tbody></table>`;
}

async function rlPost(url, body) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

// ---------------------------------------------------------------------------
// Phase 10 — RL Portfolio Context: banner + summary
// ---------------------------------------------------------------------------

let _rlSummaryRows = {};  // { ticker: { regime, action, vstar, confidence } }

function _regimeToMDPState(regime) {
    if (regime === 'RISK_ON')  return 'Bull';
    if (regime === 'RISK_OFF') return 'Bear';
    return 'Crash';
}

function updateRLPortfolioBanner() {
    const tickers   = (window.AppState && AppState.currentTickers) || [];
    const bannerEl  = document.getElementById('rlPortfolioBanner');
    if (!bannerEl) return;

    if (!tickers.length) { bannerEl.style.display = 'none'; return; }

    const regimeMap   = (window.PortfolioHealth && PortfolioHealth.getRegimeMap)
        ? PortfolioHealth.getRegimeMap() : {};
    const allocations = (window.FormManager && FormManager.getPortfolioAllocation)
        ? (FormManager.getPortfolioAllocation() || {}) : {};

    const cards = tickers.map(t => {
        const regime = regimeMap[t];
        const wt     = allocations[t] != null ? (allocations[t] * 100).toFixed(0) + '%' : '\u2014';
        const regCol = regime === 'RISK_ON' ? '#28a745' : regime === 'RISK_OFF' ? '#dc3545' : '#6c757d';
        const regLbl = regime || 'Analyzing\u2026';
        return `<div style="display:inline-flex;flex-direction:column;align-items:center;
                            background:#f8f9fa;border:1px solid #e0e0e0;border-radius:8px;
                            padding:8px 14px;min-width:90px;gap:3px;">
            <span style="font-weight:700;font-size:13px;color:#333;">${rlEscapeHTML(t)}</span>
            <span style="font-size:10px;color:#888;">${rlEscapeHTML(wt)}</span>
            <span style="font-size:11px;font-weight:600;color:${regCol};">${rlEscapeHTML(regLbl)}</span>
        </div>`;
    }).join('');

    bannerEl.innerHTML = `
        <div style="background:linear-gradient(135deg,rgba(102,126,234,0.08),rgba(118,75,162,0.08));
                    border:1px solid rgba(102,126,234,0.25);border-radius:8px;
                    padding:12px 16px;margin-bottom:12px;">
            <div style="font-size:11px;font-weight:700;color:#667eea;letter-spacing:0.6px;margin-bottom:8px;">
                YOUR PORTFOLIO \u2014 Context for RL Models
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:8px;">${cards}</div>
        </div>`;
    bannerEl.style.display = 'block';

    // Auto-populate PI / QL equity ticker inputs (RLPI-01, RLQL-01)
    const firstTicker = tickers[0] || 'SPY';
    ['rlPIEquityTicker', 'rlQLEquityTicker'].forEach(id => {
        const el = document.getElementById(id);
        if (el && !el._userEdited) el.value = firstTicker;
    });

    // Render (possibly empty) summary table
    _renderRLSummaryTable();
}

function _renderRLSummaryTable() {
    const tickers   = (window.AppState && AppState.currentTickers) || [];
    const summaryEl = document.getElementById('rlSummarySection');
    if (!summaryEl || !tickers.length) return;

    const regimeMap = (window.PortfolioHealth && PortfolioHealth.getRegimeMap)
        ? PortfolioHealth.getRegimeMap() : {};

    const rows = tickers.map(t => {
        const regime = regimeMap[t] || '\u2014';
        const cached = _rlSummaryRows[t] || {};
        const action = cached.action || '\u2014';
        const conf   = cached.confidence || '\u2014';
        const regCol = regime === 'RISK_ON' ? '#28a745' : regime === 'RISK_OFF' ? '#dc3545' : '#888';
        const actCol = action === 'Buy' ? '#28a745' : action === 'Sell' ? '#dc3545' : action === '\u2014' ? '#888' : '#fd7e14';
        return `<tr>
            <td style="padding:6px 12px;font-weight:600;">${rlEscapeHTML(t)}</td>
            <td style="padding:6px 12px;color:${regCol};">${rlEscapeHTML(regime)}</td>
            <td style="padding:6px 12px;font-weight:600;color:${actCol};">${rlEscapeHTML(action)}</td>
            <td style="padding:6px 12px;color:#888;">${rlEscapeHTML(conf)}</td>
        </tr>`;
    }).join('');

    const actions = tickers.map(t => (_rlSummaryRows[t] || {}).action).filter(Boolean);
    let verdict = '';
    if (actions.length) {
        const sells = actions.filter(a => a === 'Sell').length;
        const buys  = actions.filter(a => a === 'Buy').length;
        verdict = sells > actions.length / 2 ? 'Reduce equity exposure'
                : buys  > actions.length / 2 ? 'Increase equity exposure'
                : 'Hold \u2014 mixed signals across portfolio';
    }

    summaryEl.innerHTML = `
        <div style="background:#fff;border:1px solid #e0e0e0;border-radius:8px;
                    padding:14px;margin-bottom:14px;">
            <div style="font-size:13px;font-weight:600;color:#333;margin-bottom:10px;">
                RL Recommendations
            </div>
            <table style="border-collapse:collapse;font-size:13px;width:100%;">
                <thead>
                    <tr style="background:#f8f9fa;">
                        <th style="padding:6px 12px;text-align:left;">Ticker</th>
                        <th style="padding:6px 12px;text-align:left;">Regime</th>
                        <th style="padding:6px 12px;text-align:left;">MDP Action</th>
                        <th style="padding:6px 12px;text-align:left;">Confidence</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
            ${verdict ? `<div style="margin-top:10px;padding:8px 12px;background:#f8f9fa;
                                     border-radius:6px;font-size:13px;font-weight:600;color:#495057;">
                Verdict: ${rlEscapeHTML(verdict)}
            </div>` : ''}
        </div>`;
    summaryEl.style.display = 'block';
}

// ---------------------------------------------------------------------------
// L1: Investment MDP
// ---------------------------------------------------------------------------
async function runInvestmentMDP() {
    const containerId = 'rlMDPResults';
    rlSpinner(containerId);
    try {
        const gamma = parseFloat(document.getElementById('rlMDPGamma').value) || 0.95;
        const data  = await rlPost('/api/rl_investment_mdp', { gamma });

        if (data.error) throw new Error(data.error);

        const { states, actions, optimal_policy, v_star, q_matrix, iterations } = data;

        // Policy cards
        const policyCards = states.map((s, i) => `
            <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border-radius:10px;
                        padding:15px;text-align:center;min-width:120px;">
                <div style="font-size:13px;opacity:0.85;">${rlEscapeHTML(s)}</div>
                <div style="font-size:22px;font-weight:700;margin:6px 0;">${rlEscapeHTML(optimal_policy[i])}</div>
            </div>`).join('');

        // V* bar chart
        const vBarData = [{
            type: 'bar', x: states, y: v_star,
            marker: { color: ['#667eea', '#f093fb', '#f5576c'] },
            text: v_star.map(v => v.toFixed(2)), textposition: 'outside',
        }];
        const vBarLayout = {
            title: 'V* — Optimal State Values',
            xaxis: { title: 'State' }, yaxis: { title: 'V*(s)' },
            height: 320, margin: { t: 45, b: 50 },
        };

        // Q heatmap
        const qHeatData = [{
            type: 'heatmap', z: q_matrix, x: actions, y: states,
            colorscale: 'RdBu', reversescale: false,
            text: q_matrix.map(row => row.map(v => v.toFixed(2))),
            texttemplate: '%{text}', showscale: true,
        }];
        const qHeatLayout = {
            title: 'Q-Values: Q(s, a)',
            xaxis: { title: 'Action' }, yaxis: { title: 'State' },
            height: 300, margin: { t: 45, b: 50 },
        };

        document.getElementById(containerId).innerHTML = `
            <div style="margin-bottom:15px;">
                <h4 style="margin-bottom:8px;">Optimal Policy (converged in ${iterations} iteration${iterations>1?'s':''})</h4>
                <div style="display:flex;gap:15px;flex-wrap:wrap;">${policyCards}</div>
            </div>
            <div id="rl_vbar" style="margin-bottom:20px;"></div>
            <div id="rl_qheat"></div>`;

        Plotly.newPlot('rl_vbar',  vBarData,  vBarLayout,  { responsive: true });
        Plotly.newPlot('rl_qheat', qHeatData, qHeatLayout, { responsive: true });

        // Phase 11 — per-ticker MDP action cards (RLMDP-01, RLMDP-02, RLMDP-03)
        const tickers = (window.AppState && AppState.currentTickers) || [];
        if (tickers.length && window.PortfolioHealth && PortfolioHealth.getRegimeMap) {
            const regimeMap = PortfolioHealth.getRegimeMap();
            const vStarMax  = Math.max(...v_star.map(Math.abs)) || 1;

            const tickerCards = tickers.map(t => {
                const regime    = regimeMap[t];
                const mdpState  = _regimeToMDPState(regime);
                const stateIdx  = states.indexOf(mdpState);
                const action    = stateIdx >= 0 ? optimal_policy[stateIdx] : '\u2014';
                const vstarVal  = stateIdx >= 0 ? v_star[stateIdx] : null;
                const confidence = vstarVal != null
                    ? (Math.abs(vstarVal) / vStarMax * 100).toFixed(0) + '%' : '\u2014';

                // Update summary cache
                _rlSummaryRows[t] = { regime, action, vstar: vstarVal, confidence };

                const actBg  = action === 'Buy'  ? '#d4edda' : action === 'Sell' ? '#f8d7da' : '#fff3cd';
                const actCol = action === 'Buy'  ? '#28a745' : action === 'Sell' ? '#dc3545' : '#fd7e14';
                const regCol = regime === 'RISK_ON' ? '#28a745' : regime === 'RISK_OFF' ? '#dc3545' : '#6c757d';

                return `<div style="background:#fff;border:1px solid #e0e0e0;border-radius:10px;
                                    padding:14px;min-width:140px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
                    <div style="font-size:14px;font-weight:700;color:#333;">${rlEscapeHTML(t)}</div>
                    <div style="font-size:11px;color:${regCol};margin:3px 0;">
                        ${rlEscapeHTML(regime || '\u2014')} \u2192 ${rlEscapeHTML(mdpState)}
                    </div>
                    <div style="display:inline-block;background:${actBg};color:${actCol};
                                border-radius:6px;padding:4px 14px;font-weight:700;
                                font-size:16px;margin:6px 0;">
                        ${rlEscapeHTML(action)}
                    </div>
                    <div style="font-size:11px;color:#888;">
                        V* = ${vstarVal != null ? vstarVal.toFixed(3) : '\u2014'}
                    </div>
                </div>`;
            }).join('');

            document.getElementById(containerId).insertAdjacentHTML('beforeend', `
                <div style="margin-top:20px;border-top:1px solid #e0e0e0;padding-top:16px;">
                    <h4 style="margin-bottom:12px;color:#333;">
                        Your Portfolio \u2014 MDP Action Recommendations
                    </h4>
                    <div style="display:flex;flex-wrap:wrap;gap:12px;">${tickerCards}</div>
                </div>`);

            // Refresh summary table with populated rows
            _renderRLSummaryTable();
        }

    } catch (err) {
        document.getElementById(containerId).innerHTML = rlAlert('Error: ' + err.message);
    }
}

// ---------------------------------------------------------------------------
// L2: Gridworld
// ---------------------------------------------------------------------------
async function runGridworld() {
    const containerId = 'rlGridResults';
    rlSpinner(containerId);
    try {
        const use_wind = document.getElementById('rlGridWind').checked;
        const gamma    = parseFloat(document.getElementById('rlGridGamma').value) || 0.95;
        const data     = await rlPost('/api/rl_gridworld', { use_wind, gamma });

        if (data.error) throw new Error(data.error);

        const { policy, v_grid, iterations } = data;

        // Build 4x4 arrays for Plotly heatmaps
        const gridRows = 4, gridCols = 4;
        const policyGrid = [];
        const vFlat = v_grid.flat();
        const vGrid4 = [];
        for (let r = 0; r < gridRows; r++) {
            policyGrid.push(policy.slice(r * gridCols, (r + 1) * gridCols));
            vGrid4.push(v_grid[r]);
        }

        // Policy heatmap — color by V* value, annotated with arrows
        const zPol   = vGrid4.map(row => [...row]);
        const textPol = policyGrid;

        const polData = [{
            type: 'heatmap', z: zPol,
            text: textPol, texttemplate: '<b>%{text}</b>',
            colorscale: 'Blues', showscale: false,
            xgap: 2, ygap: 2,
        }];
        const polLayout = {
            title: `Policy Grid (wind=${use_wind}, γ=${gamma}, iters=${iterations})`,
            xaxis: { showticklabels: false, scaleanchor: 'y' },
            yaxis: { showticklabels: false, autorange: 'reversed' },
            height: 360, margin: { t: 50, b: 20, l: 20, r: 20 },
            font: { size: 18 },
        };

        // V* heatmap
        const vData = [{
            type: 'heatmap', z: vGrid4,
            colorscale: 'Viridis', showscale: true,
            text: vGrid4.map(row => row.map(v => v.toFixed(2))),
            texttemplate: '%{text}',
            xgap: 2, ygap: 2,
        }];
        const vLayout = {
            title: 'V* Value Grid',
            xaxis: { showticklabels: false, scaleanchor: 'y' },
            yaxis: { showticklabels: false, autorange: 'reversed' },
            height: 340, margin: { t: 50, b: 20, l: 20, r: 20 },
        };

        document.getElementById(containerId).innerHTML = `
            <div id="rl_grid_pol" style="margin-bottom:20px;"></div>
            <div id="rl_grid_v"></div>`;

        Plotly.newPlot('rl_grid_pol', polData, polLayout, { responsive: true });
        Plotly.newPlot('rl_grid_v',   vData,   vLayout,   { responsive: true });

        // Phase 13 — Portfolio Risk Navigation panel (RLGRID-01, RLGRID-02)
        _renderGridworldRiskPanel(containerId);

    } catch (err) {
        document.getElementById(containerId).innerHTML = rlAlert('Error: ' + err.message);
    }
}

function _renderGridworldRiskPanel(containerId) {
    const tickers = (window.AppState && AppState.currentTickers) || [];
    if (!tickers.length) return;

    const regimeMap = (window.PortfolioHealth && PortfolioHealth.getRegimeMap)
        ? PortfolioHealth.getRegimeMap() : {};

    // Determine momentum from majority regime vote
    const regimes     = tickers.map(t => regimeMap[t]).filter(Boolean);
    const riskOffCnt  = regimes.filter(r => r === 'RISK_OFF').length;
    const momentum    = riskOffCnt > regimes.length / 2 ? 'Negative'
                      : riskOffCnt > 0                  ? 'Flat'
                      : 'Positive';

    // Estimate annualised vol from VaR in currentAnalytics
    let volLevel = 'Mid';
    const analytics = window.AppState && AppState.currentAnalytics;
    if (analytics) {
        let varPct = null;
        const tryExtract = mc => {
            if (!mc || !mc.VaR) return null;
            const k95 = Object.keys(mc.VaR).find(k => k.includes('95'));
            return k95 ? Math.abs(mc.VaR[k95].Percentage || 0) : null;
        };
        varPct = tryExtract(analytics.portfolio_monte_carlo);
        if (varPct == null && tickers.length) {
            const t = tickers[0];
            varPct = tryExtract(analytics[t] && analytics[t].monte_carlo);
        }
        if (varPct != null) {
            const sigmaAnn = (varPct / 1.645 / 100) * Math.sqrt(252) * 100;
            volLevel = sigmaAnn > 30 ? 'High' : sigmaAnn > 15 ? 'Mid' : 'Low';
        }
    }

    const narratives = {
        'High_Negative': 'High volatility + negative momentum \u2192 reduce equity exposure, move toward lower-risk allocation.',
        'High_Flat':     'High volatility + flat momentum \u2192 cautious positioning; consider partial defensive rebalancing.',
        'High_Positive': 'High volatility + positive momentum \u2192 strong trend but elevated risk; size positions carefully.',
        'Mid_Negative':  'Moderate volatility + negative momentum \u2192 defensive tilt; reduce aggressive exposure.',
        'Mid_Flat':      'Moderate volatility + flat momentum \u2192 hold current allocation; monitor for direction change.',
        'Mid_Positive':  'Moderate volatility + positive momentum \u2192 maintain equity exposure; trend is supportive.',
        'Low_Negative':  'Low volatility + negative momentum \u2192 counter-trend signal; assess fundamental drivers.',
        'Low_Flat':      'Low volatility + flat momentum \u2192 stable conditions; equal-weight allocation reasonable.',
        'Low_Positive':  'Low volatility + positive momentum \u2192 favourable conditions; maintain or increase equity exposure.',
    };
    const narrative = narratives[`${volLevel}_${momentum}`] || 'Insufficient data to determine risk profile.';

    const VOL_LEVELS = ['High', 'Mid', 'Low'];
    const MOM_LEVELS = ['Negative', 'Flat', 'Positive'];

    let tableRows = '';
    VOL_LEVELS.forEach(v => {
        tableRows += '<tr>';
        tableRows += `<td style="padding:6px 10px;font-weight:600;font-size:12px;
                                  background:#f8f9fa;border:1px solid #dee2e6;">${v} Vol</td>`;
        MOM_LEVELS.forEach(m => {
            const active = (v === volLevel && m === momentum);
            const bg     = active ? '#667eea' : '#fff';
            const col    = active ? '#fff' : '#ccc';
            tableRows += `<td style="padding:10px 14px;text-align:center;border:1px solid #dee2e6;
                                      background:${bg};color:${col};font-weight:${active ? '700' : 'normal'};
                                      font-size:${active ? '14' : '12'}px;">
                ${active ? '\u25cf HERE' : '&nbsp;'}
            </td>`;
        });
        tableRows += '</tr>';
    });

    document.getElementById(containerId).insertAdjacentHTML('beforeend', `
        <div style="margin-top:20px;border-top:1px solid #e0e0e0;padding-top:16px;">
            <h4 style="margin-bottom:12px;color:#333;">Portfolio Risk Profile</h4>
            <table style="border-collapse:collapse;font-size:12px;margin-bottom:12px;">
                <thead>
                    <tr>
                        <th style="padding:6px 10px;border:1px solid #dee2e6;background:#f8f9fa;"></th>
                        <th style="padding:6px 10px;border:1px solid #dee2e6;background:#f8f9fa;">Negative</th>
                        <th style="padding:6px 10px;border:1px solid #dee2e6;background:#f8f9fa;">Flat</th>
                        <th style="padding:6px 10px;border:1px solid #dee2e6;background:#f8f9fa;">Positive</th>
                    </tr>
                </thead>
                <tbody>${tableRows}</tbody>
            </table>
            <div style="background:#f8f9fa;border-radius:6px;padding:10px 14px;
                        font-size:13px;color:#495057;font-style:italic;">
                ${rlEscapeHTML(narrative)}
            </div>
        </div>`);
}

// ---------------------------------------------------------------------------
// L3: Portfolio Rotation — Policy Iteration
// ---------------------------------------------------------------------------
async function runPortfolioRotationPI() {
    const containerId = 'rlPIResults';
    rlSpinner(containerId);
    try {
        const body = {
            train_end:  document.getElementById('rlPITrainEnd').value  || '2016-12-31',
            test_start: document.getElementById('rlPITestStart').value || '2017-01-01',
            gamma:      parseFloat(document.getElementById('rlPIGamma').value)    || 0.99,
            cost_bps:   parseInt(document.getElementById('rlPICostBps').value)   || 10,
        };
        const data = await rlPost('/api/rl_portfolio_rotation_pi', body);
        if (data.error) throw new Error(data.error);
        _renderPortfolioResults(containerId, data, 'PI', 'rl_pi');

        // Phase 12 — current-state recommendation (RLPI-02, RLPI-03)
        _appendPICurrentState(containerId, data);

    } catch (err) {
        document.getElementById(containerId).innerHTML = rlAlert('Error: ' + err.message);
    }
}

function _appendPICurrentState(containerId, data) {
    const tickers = (window.AppState && AppState.currentTickers) || [];
    if (!tickers.length || !data.optimal_policy_table) return;

    const regimeMap   = (window.PortfolioHealth && PortfolioHealth.getRegimeMap)
        ? PortfolioHealth.getRegimeMap() : {};
    const firstTicker = tickers[0];
    const regime      = regimeMap[firstTicker];

    const stateNames = Object.keys(data.optimal_policy_table);
    const searchKey  = regime === 'RISK_ON' ? 'bull' : 'bear';
    let currentStateIdx = stateNames.findIndex(s => s.toLowerCase().includes(searchKey));
    if (currentStateIdx === -1) {
        currentStateIdx = regime === 'RISK_ON' ? 0 : stateNames.length - 1;
    }
    const currentState = stateNames[currentStateIdx];
    const action = data.optimal_policy_table[currentState] || '\u2014';

    // Highlight the matching row in the policy table
    const policyTbody = document.querySelector(`#${containerId} details table tbody`);
    if (policyTbody) {
        policyTbody.querySelectorAll('tr').forEach(row => {
            const cell = row.querySelector('td:first-child');
            if (cell && cell.textContent.trim() === currentState) {
                row.style.background = 'rgba(102,126,234,0.12)';
                row.style.fontWeight = '600';
                row.insertAdjacentHTML('beforeend',
                    '<td style="padding:3px 10px;color:#667eea;font-size:11px;">\u25b6 Current</td>');
            }
        });
    }

    // Plain-English allocation card
    const match    = action.match(/(\d+)\/(\d+)/);
    const allocTxt = match ? `Hold ${match[1]}% equity / ${match[2]}% bonds` : action;
    const tickerLbl = (document.getElementById('rlPIEquityTicker') || {}).value || firstTicker;

    document.getElementById(containerId).insertAdjacentHTML('beforeend', `
        <div style="margin-top:14px;background:linear-gradient(135deg,rgba(102,126,234,0.08),rgba(118,75,162,0.08));
                    border:1px solid rgba(102,126,234,0.25);border-radius:8px;padding:14px;">
            <div style="font-size:11px;font-weight:700;color:#667eea;letter-spacing:0.5px;margin-bottom:6px;">
                CURRENT STATE &amp; RECOMMENDATION (${rlEscapeHTML(tickerLbl)})
            </div>
            <div style="font-size:13px;color:#555;margin-bottom:4px;">
                State: <strong>${rlEscapeHTML(currentState)}</strong>
                <span style="color:#888;">&nbsp;(regime: ${rlEscapeHTML(regime || '\u2014')})</span>
            </div>
            <div style="font-size:16px;font-weight:700;color:#495057;">${rlEscapeHTML(allocTxt)}</div>
        </div>`);
}

// ---------------------------------------------------------------------------
// L4: Portfolio Rotation — Q-Learning
// ---------------------------------------------------------------------------
async function runPortfolioRotationQL() {
    const containerId = 'rlQLResults';
    rlSpinner(containerId);
    try {
        const body = {
            alpha:      parseFloat(document.getElementById('rlQLAlpha').value)     || 0.10,
            epochs:     parseInt(document.getElementById('rlQLEpochs').value)      || 200,
            eps_start:  parseFloat(document.getElementById('rlQLEpsStart').value)  || 0.15,
            eps_end:    parseFloat(document.getElementById('rlQLEpsEnd').value)    || 0.01,
            optimistic: parseFloat(document.getElementById('rlQLOptimistic').value)|| 0.005,
            gamma:      parseFloat(document.getElementById('rlQLGamma').value)     || 0.99,
            cost_bps:   parseInt(document.getElementById('rlQLCostBps').value)     || 10,
        };
        const data = await rlPost('/api/rl_portfolio_rotation_ql', body);
        if (data.error) throw new Error(data.error);

        // Render cumret line chart + metrics (shared helper)
        _renderPortfolioResults(containerId, data, 'QL', 'rl_ql');

        // Additionally render Q-table heatmap with current-state highlight (RLQL-02)
        if (data.q_table && data.state_names && data.action_names) {
            const qDiv = document.createElement('div');
            qDiv.id = 'rl_ql_qtable';
            document.getElementById(containerId).appendChild(qDiv);

            // Phase 12 — detect current state
            const tickers   = (window.AppState && AppState.currentTickers) || [];
            const regimeMap = (window.PortfolioHealth && PortfolioHealth.getRegimeMap)
                ? PortfolioHealth.getRegimeMap() : {};
            const firstTicker = tickers[0];
            const regime      = firstTicker ? regimeMap[firstTicker] : null;

            let curStateIdx = -1;
            if (regime) {
                const searchKey = regime === 'RISK_ON' ? 'bull' : 'bear';
                curStateIdx = data.state_names.findIndex(s => s.toLowerCase().includes(searchKey));
                if (curStateIdx === -1) {
                    curStateIdx = regime === 'RISK_ON' ? 0 : data.state_names.length - 1;
                }
            }

            // Build text matrix — annotate greedy action cell in current state row
            let greedyColIdx = -1;
            const textMatrix = data.q_table.map((row, ri) => {
                let maxVal = -Infinity, maxCI = 0;
                row.forEach((v, ci) => { if (v > maxVal) { maxVal = v; maxCI = ci; } });
                if (ri === curStateIdx) greedyColIdx = maxCI;
                return row.map((v, ci) => {
                    let t = v.toFixed(4);
                    if (ri === curStateIdx && ci === maxCI) t += '\n\u25b6 Now';
                    return t;
                });
            });

            // Shape to highlight current state row
            const shapes = curStateIdx >= 0 ? [{
                type: 'rect', xref: 'paper', yref: 'y',
                x0: 0, x1: 1,
                y0: curStateIdx - 0.5, y1: curStateIdx + 0.5,
                fillcolor: 'rgba(102,126,234,0.15)',
                line: { color: '#667eea', width: 2 },
            }] : [];

            const qData = [{
                type: 'heatmap',
                z: data.q_table,
                x: data.action_names,
                y: data.state_names,
                colorscale: 'RdBu', reversescale: false,
                text: textMatrix,
                texttemplate: '%{text}',
                showscale: true,
            }];
            const qLayout = {
                title: curStateIdx >= 0
                    ? 'Q-Table \u2014 current state highlighted'
                    : 'Q-Table (12 states \u00d7 5 actions)',
                xaxis: { title: 'Action (Equity/Bond%)' },
                yaxis: { title: 'State', autorange: 'reversed' },
                height: 500, margin: { t: 50, b: 60, l: 160, r: 20 },
                font: { size: 10 },
                shapes,
            };
            Plotly.newPlot('rl_ql_qtable', qData, qLayout, { responsive: true });

            // Phase 12 — Current Recommendation card (RLQL-03)
            if (curStateIdx >= 0 && greedyColIdx >= 0) {
                const greedyAction = data.action_names[greedyColIdx];
                const qScore       = data.q_table[curStateIdx][greedyColIdx];
                const match        = greedyAction && greedyAction.match(/(\d+)\/(\d+)/);
                const allocTxt     = match
                    ? `Hold ${match[1]}% equity / ${match[2]}% bonds`
                    : greedyAction;
                const tickerLbl = (document.getElementById('rlQLEquityTicker') || {}).value || firstTicker || 'Portfolio';

                document.getElementById(containerId).insertAdjacentHTML('beforeend', `
                    <div style="margin-top:12px;background:linear-gradient(135deg,rgba(102,126,234,0.08),rgba(118,75,162,0.08));
                                border:1px solid rgba(102,126,234,0.25);border-radius:8px;padding:14px;">
                        <div style="font-size:11px;font-weight:700;color:#667eea;letter-spacing:0.5px;margin-bottom:6px;">
                            CURRENT RECOMMENDATION (${rlEscapeHTML(tickerLbl)})
                        </div>
                        <div style="font-size:16px;font-weight:700;color:#495057;margin-bottom:4px;">
                            ${rlEscapeHTML(allocTxt)}
                        </div>
                        <div style="font-size:11px;color:#888;">
                            Q-value: ${qScore.toFixed(4)}
                            &nbsp;&middot;&nbsp;
                            State: ${rlEscapeHTML(data.state_names[curStateIdx])}
                            &nbsp;&middot;&nbsp;
                            Regime: ${rlEscapeHTML(regime || '\u2014')}
                        </div>
                    </div>`);
            }
        }
    } catch (err) {
        document.getElementById(containerId).innerHTML = rlAlert('Error: ' + err.message);
    }
}

// ---------------------------------------------------------------------------
// Shared: cumulative return chart + metrics table
// ---------------------------------------------------------------------------
function _renderPortfolioResults(containerId, data, label, chartPrefix) {
    const { test_dates, rl_cumret, benchmark_cumret, perf_metrics } = data;
    const policyKey = label === 'PI' ? 'optimal_policy_table' : 'greedy_policy';
    const policyData = data[policyKey] || {};

    // Cumulative return (in %)
    const rlPct   = rl_cumret.map(v => (v * 100).toFixed(2));
    const bmPct   = benchmark_cumret.map(v => (v * 100).toFixed(2));

    const lineData = [
        {
            type: 'scatter', mode: 'lines', name: `RL (${label})`,
            x: test_dates, y: rlPct,
            line: { color: '#667eea', width: 2.5 },
        },
        {
            type: 'scatter', mode: 'lines', name: '60/40 Benchmark',
            x: test_dates, y: bmPct,
            line: { color: '#f5576c', width: 2, dash: 'dash' },
        },
    ];
    const lineLayout = {
        title: `Portfolio Rotation (${label}) vs 60/40 Benchmark`,
        xaxis: { title: 'Date', type: 'category', tickangle: -45, nticks: 12 },
        yaxis: { title: 'Cumulative Return (%)' },
        legend: { x: 0.01, y: 0.99 },
        height: 380, margin: { t: 50, b: 80 },
    };

    // Metrics table
    const m = perf_metrics || {};
    const metricsHTML = `
        <table style="border-collapse:collapse;font-size:13px;width:100%;margin-top:10px;">
            <thead>
                <tr style="background:#f8f9fa;">
                    <th style="padding:6px 12px;text-align:left;"></th>
                    <th style="padding:6px 12px;">CAGR</th>
                    <th style="padding:6px 12px;">Volatility</th>
                    <th style="padding:6px 12px;">Sharpe</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding:6px 12px;font-weight:600;">RL (${label})</td>
                    <td style="padding:6px 12px;">${((m.rl_cagr||0)*100).toFixed(2)}%</td>
                    <td style="padding:6px 12px;">${((m.rl_vol||0)*100).toFixed(2)}%</td>
                    <td style="padding:6px 12px;">${(m.rl_sharpe||0).toFixed(3)}</td>
                </tr>
                <tr style="background:#f8f9fa;">
                    <td style="padding:6px 12px;font-weight:600;">60/40</td>
                    <td style="padding:6px 12px;">${((m.bench_cagr||0)*100).toFixed(2)}%</td>
                    <td style="padding:6px 12px;">${((m.bench_vol||0)*100).toFixed(2)}%</td>
                    <td style="padding:6px 12px;">${(m.bench_sharpe||0).toFixed(3)}</td>
                </tr>
            </tbody>
        </table>`;

    // Policy table (collapsible)
    const policyRows = Object.entries(policyData).map(([state, action]) =>
        `<tr><td style="padding:3px 10px;">${rlEscapeHTML(state)}</td>
              <td style="padding:3px 10px;font-weight:600;">${rlEscapeHTML(action)}</td></tr>`
    ).join('');
    const policyHTML = policyRows ? `
        <details style="margin-top:15px;">
            <summary style="cursor:pointer;font-weight:600;color:#667eea;">Optimal Policy Table</summary>
            <table style="border-collapse:collapse;font-size:12px;margin-top:8px;width:100%">
                <thead><tr style="background:#f8f9fa;">
                    <th style="padding:4px 10px;text-align:left;">State</th>
                    <th style="padding:4px 10px;text-align:left;">Action (Eq/Bond%)</th>
                </tr></thead>
                <tbody>${policyRows}</tbody>
            </table>
        </details>` : '';

    document.getElementById(containerId).innerHTML = `
        <div id="${chartPrefix}_line" style="margin-bottom:10px;"></div>
        ${metricsHTML}
        ${policyHTML}`;

    Plotly.newPlot(`${chartPrefix}_line`, lineData, lineLayout, { responsive: true });
}

// ---------------------------------------------------------------------------
// Stochastic Models tab — Portfolio MDP (user-input stocks)
// ---------------------------------------------------------------------------
async function runPortfolioMDP() {
    const containerId = 'stochPortfolioMDPResults';
    rlSpinner(containerId);
    try {
        const body = {
            equity_ticker: (document.getElementById('mdpEquityTicker').value || 'SPY').trim().toUpperCase(),
            bond_ticker:   (document.getElementById('mdpBondTicker').value   || 'IEF').trim().toUpperCase(),
            start_date:    document.getElementById('mdpStartDate').value  || '2010-01-01',
            train_end:     document.getElementById('mdpTrainEnd').value   || '2020-12-31',
            test_start:    document.getElementById('mdpTestStart').value  || '2021-01-01',
            gamma:         parseFloat(document.getElementById('mdpGamma').value)    || 0.99,
            cost_bps:      parseInt(document.getElementById('mdpCostBps').value)    || 10,
        };
        const data = await rlPost('/api/stoch_portfolio_mdp', body);
        if (data.error) throw new Error(data.error);

        const {
            equity_ticker, bond_ticker, optimal_policy, state_names, action_names,
            v_star, q_matrix, state_counts, iterations,
            test_dates, rl_cumret, benchmark_cumret, perf_metrics,
        } = data;

        const eq = equity_ticker, bd = bond_ticker;

        // Cumulative return line chart
        const lineData = [
            {
                type: 'scatter', mode: 'lines', name: 'MDP Policy',
                x: test_dates, y: rl_cumret.map(v => (v * 100).toFixed(2)),
                line: { color: '#667eea', width: 2.5 },
            },
            {
                type: 'scatter', mode: 'lines',
                name: perf_metrics.benchmark_label || `50/50 ${eq}/${bd}`,
                x: test_dates, y: benchmark_cumret.map(v => (v * 100).toFixed(2)),
                line: { color: '#f5576c', width: 2, dash: 'dash' },
            },
        ];
        const lineLayout = {
            title: `Portfolio MDP: ${eq} / ${bd} — Policy Iteration (${iterations} iter)`,
            xaxis: { title: 'Date', type: 'category', tickangle: -45, nticks: 12 },
            yaxis: { title: 'Cumulative Return (%)' },
            legend: { x: 0.01, y: 0.99 },
            height: 380, margin: { t: 55, b: 80 },
        };

        // V* bar chart
        const vBarData = [{
            type: 'bar', x: state_names, y: v_star,
            marker: { color: v_star.map(v => v >= 0 ? '#667eea' : '#f5576c') },
            text: v_star.map(v => v.toFixed(3)), textposition: 'outside',
        }];
        const vBarLayout = {
            title: 'V* — Optimal State Values',
            xaxis: { tickangle: -45, automargin: true },
            yaxis: { title: 'V*(s)' },
            height: 380, margin: { t: 50, b: 160 },
        };

        // Metrics table
        const m = perf_metrics || {};
        const metricsHTML = `
            <table style="border-collapse:collapse;font-size:13px;width:100%;margin:12px 0;">
                <thead>
                    <tr style="background:#f8f9fa;">
                        <th style="padding:6px 12px;text-align:left;"></th>
                        <th style="padding:6px 12px;">CAGR</th>
                        <th style="padding:6px 12px;">Volatility</th>
                        <th style="padding:6px 12px;">Sharpe</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding:6px 12px;font-weight:600;">MDP Policy</td>
                        <td style="padding:6px 12px;">${((m.rl_cagr||0)*100).toFixed(2)}%</td>
                        <td style="padding:6px 12px;">${((m.rl_vol||0)*100).toFixed(2)}%</td>
                        <td style="padding:6px 12px;">${(m.rl_sharpe||0).toFixed(3)}</td>
                    </tr>
                    <tr style="background:#f8f9fa;">
                        <td style="padding:6px 12px;font-weight:600;">${m.benchmark_label || `50/50`}</td>
                        <td style="padding:6px 12px;">${((m.bench_cagr||0)*100).toFixed(2)}%</td>
                        <td style="padding:6px 12px;">${((m.bench_vol||0)*100).toFixed(2)}%</td>
                        <td style="padding:6px 12px;">${(m.bench_sharpe||0).toFixed(3)}</td>
                    </tr>
                </tbody>
            </table>`;

        // Policy table
        const policyRows = Object.entries(optimal_policy).map(([state, action]) => {
            const count = (state_counts || {})[state] || 0;
            return `<tr>
                <td style="padding:3px 10px;font-size:12px;">${rlEscapeHTML(state)}</td>
                <td style="padding:3px 10px;font-weight:600;color:#667eea;">${rlEscapeHTML(action)}</td>
                <td style="padding:3px 10px;color:#888;">${count} months</td>
            </tr>`;
        }).join('');

        document.getElementById(containerId).innerHTML = `
            <div id="mdp_line" style="margin-bottom:10px;"></div>
            ${metricsHTML}
            <details style="margin-top:15px;" open>
                <summary style="cursor:pointer;font-weight:600;color:#667eea;margin-bottom:8px;">Optimal Policy Table</summary>
                <table style="border-collapse:collapse;width:100%;font-size:12px;">
                    <thead><tr style="background:#f8f9fa;">
                        <th style="padding:4px 10px;text-align:left;">State</th>
                        <th style="padding:4px 10px;text-align:left;">${rlEscapeHTML(eq)}/${rlEscapeHTML(bd)} Allocation</th>
                        <th style="padding:4px 10px;text-align:left;">Test Visits</th>
                    </tr></thead>
                    <tbody>${policyRows}</tbody>
                </table>
            </details>
            <div id="mdp_vbar" style="margin-top:20px;"></div>`;

        Plotly.newPlot('mdp_line',  lineData, lineLayout, { responsive: true });
        Plotly.newPlot('mdp_vbar',  vBarData, vBarLayout, { responsive: true });

    } catch (err) {
        document.getElementById(containerId).innerHTML = rlAlert('Error: ' + err.message);
    }
}

// ---------------------------------------------------------------------------
// Stochastic Models tab — Grid-world PI (reuses gridworld_policy_iteration)
// ---------------------------------------------------------------------------
async function runStochGridworld() {
    const containerId = 'stochGridResults';
    rlSpinner(containerId);
    try {
        const use_wind = document.getElementById('stochGridWind').checked;
        const gamma    = parseFloat(document.getElementById('stochGridGamma').value) || 0.95;
        const data     = await rlPost('/api/rl_gridworld', { use_wind, gamma });
        if (data.error) throw new Error(data.error);

        const { policy, v_grid, iterations } = data;
        const gridRows = 4;

        const polData = [{
            type: 'heatmap',
            z: v_grid,
            text: Array.from({ length: gridRows }, (_, r) => policy.slice(r * 4, r * 4 + 4)),
            texttemplate: '<b>%{text}</b>',
            colorscale: 'Blues', showscale: false,
            xgap: 2, ygap: 2,
        }];
        const polLayout = {
            title: `Policy Grid (wind=${use_wind}, γ=${gamma}, ${iterations} iter)`,
            xaxis: { showticklabels: false, scaleanchor: 'y' },
            yaxis: { showticklabels: false, autorange: 'reversed' },
            height: 380, margin: { t: 55, b: 20, l: 20, r: 20 },
            font: { size: 20 },
        };

        const vData = [{
            type: 'heatmap', z: v_grid,
            colorscale: 'Viridis', showscale: true,
            text: v_grid.map(row => row.map(v => v.toFixed(2))),
            texttemplate: '%{text}',
            xgap: 2, ygap: 2,
        }];
        const vLayout = {
            title: 'V* Value Grid',
            xaxis: { showticklabels: false, scaleanchor: 'y' },
            yaxis: { showticklabels: false, autorange: 'reversed' },
            height: 360, margin: { t: 50, b: 20, l: 20, r: 20 },
        };

        document.getElementById(containerId).innerHTML =
            `<div id="stoch_grid_pol" style="margin-bottom:20px;"></div>
             <div id="stoch_grid_v"></div>`;

        Plotly.newPlot('stoch_grid_pol', polData, polLayout, { responsive: true });
        Plotly.newPlot('stoch_grid_v',   vData,   vLayout,   { responsive: true });

    } catch (err) {
        document.getElementById(containerId).innerHTML = rlAlert('Error: ' + err.message);
    }
}

// ---------------------------------------------------------------------------
// Expose shared helpers and RL portfolio functions for cross-script access
// ---------------------------------------------------------------------------
window.rlEscapeHTML            = rlEscapeHTML;
window.rlAlert                 = rlAlert;
window.updateRLPortfolioBanner = updateRLPortfolioBanner;
window._renderRLSummaryTable   = _renderRLSummaryTable;
