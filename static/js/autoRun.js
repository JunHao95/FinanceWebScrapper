// ---------------------------------------------------------------------------
// autoRun.js — Auto-run orchestration after scrape
// Exposes: window.AutoRun.triggerAutoRun(tickers)
// ---------------------------------------------------------------------------

const BADGE_RUNNING = 'background:#6c757d;color:white;border-radius:10px;padding:2px 8px;font-size:11px;margin-left:5px;';
const BADGE_DONE    = 'background:#28a745;color:white;border-radius:10px;padding:2px 8px;font-size:11px;margin-left:5px;';
const BADGE_FAILED  = 'background:#dc3545;color:white;border-radius:10px;padding:2px 8px;font-size:11px;margin-left:5px;';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(d) {
    return d.toISOString().slice(0, 10);
}

// ---------------------------------------------------------------------------
// HTML scaffold builder
// ---------------------------------------------------------------------------

function buildAutoRunHTML(tickers) {
    let tickerBlocks = '';
    tickers.forEach(ticker => {
        tickerBlocks += `
        <div class="autoRegimeBlock" style="margin-bottom:24px;">
            <h4 style="margin-bottom:10px;">
                Regime Detection &mdash; ${ticker}
                <span id="autoRegimeBadge_${ticker}" style="${BADGE_RUNNING}">Rolling...</span>
            </h4>
            <p id="autoRegimePlaceholder_${ticker}" style="color:#555;font-size:13px;">Analyzing regime...</p>
            <div id="autoRegimeProb_${ticker}" style="display:none;margin-bottom:20px;"></div>
            <div id="autoRegimePrice_${ticker}" style="display:none;margin-bottom:20px;"></div>
        </div>`;
    });

    let mdpBlock = '';
    if (tickers.length >= 2) {
        mdpBlock = `
        <div style="margin-bottom:24px;">
            <h4 style="margin-bottom:10px;">
                Portfolio MDP (SPY / IEF)
                <span id="autoMDPBadge" style="${BADGE_RUNNING}">Running...</span>
            </h4>
            <p style="color:#555;font-size:13px;margin:8px 0 12px;">
                This model trains a Markov Decision Process on SPY (equity) and IEF (bonds) using
                historical data. The optimal policy shows which asset to hold in each
                volatility/trend regime &mdash; bull regimes recommend equity, bear regimes recommend
                bonds. The backtest line shows policy performance vs. a 50/50 static benchmark.
            </p>
            <div id="autoMDPResults"></div>
        </div>`;
    }

    return `
    <div id="autoRunSection" style="border-bottom:1px solid #e0e0e0;margin-bottom:24px;padding-bottom:8px;">
        <h3 style="margin-bottom:16px;">Auto Analysis</h3>
        ${tickerBlocks}
        ${mdpBlock}
    </div>`;
}

// ---------------------------------------------------------------------------
// Regime chart renderer — mirrors stochasticModels.js runRegimeDetection()
// lines 88-146, with container IDs namespaced per ticker
// ---------------------------------------------------------------------------

function renderRegimeCharts(ticker, data) {
    // Chart 1: Filtered probability time series
    Plotly.newPlot('autoRegimeProb_' + ticker, [{
        x: data.dates,
        y: data.filtered_probs,
        type: 'scatter',
        mode: 'lines',
        fill: 'tozeroy',
        name: 'P(Stressed)',
        line: { color: '#dc3545' }
    }], {
        title: `Regime Probability \u2014 ${ticker}`,
        xaxis: { title: 'Date' },
        yaxis: { title: 'P(Stressed)', range: [0, 1] },
        height: 300,
        margin: { t: 40, l: 60, r: 20, b: 50 }
    });

    // Chart 2: Price chart with regime shading
    const shapes = [];
    let start = null, prevState = null;
    const dates = data.dates;
    const regSeq = data.regime_sequence;
    dates.forEach((d, i) => {
        const state = regSeq[i];
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
    // Close final stressed block if still open at end
    if (prevState === 1 && start !== null && dates.length > 0) {
        shapes.push({
            type: 'rect', xref: 'x', yref: 'paper',
            x0: start, x1: dates[dates.length - 1], y0: 0, y1: 1,
            fillcolor: 'rgba(220,53,69,0.15)', line: { width: 0 }
        });
    }
    Plotly.newPlot('autoRegimePrice_' + ticker, [{
        x: dates,
        y: data.prices,
        type: 'scatter',
        mode: 'lines',
        name: ticker,
        line: { color: '#667eea', width: 1.5 }
    }], {
        title: `${ticker} Price with Regime Shading`,
        shapes: shapes,
        xaxis: { title: 'Date' },
        yaxis: { title: 'Price' },
        height: 350,
        margin: { t: 40, l: 60, r: 20, b: 50 }
    });
}

// ---------------------------------------------------------------------------
// Per-ticker regime detection — catches all errors internally
// ---------------------------------------------------------------------------

async function runAutoRegime(ticker, startDate, endDate) {
    try {
        const resp = await fetch('/api/regime_detection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, start_date: startDate, end_date: endDate })
        });
        const data = await resp.json();

        if (!resp.ok || !data.success) {
            const errorMsg = data?.error || 'Unknown error';
            const badge = document.getElementById('autoRegimeBadge_' + ticker);
            badge.setAttribute('style', BADGE_FAILED);
            badge.textContent = 'Failed';
            document.getElementById('autoRegimePlaceholder_' + ticker).textContent =
                'Regime detection failed: ' + errorMsg;
            return;
        }

        // Success — hide placeholder, show charts
        document.getElementById('autoRegimePlaceholder_' + ticker).style.display = 'none';
        document.getElementById('autoRegimeProb_' + ticker).style.display = 'block';
        document.getElementById('autoRegimePrice_' + ticker).style.display = 'block';

        renderRegimeCharts(ticker, data);

        const badge = document.getElementById('autoRegimeBadge_' + ticker);
        badge.setAttribute('style', BADGE_DONE);
        badge.textContent = 'Done';

    } catch (err) {
        const badge = document.getElementById('autoRegimeBadge_' + ticker);
        if (badge) {
            badge.setAttribute('style', BADGE_FAILED);
            badge.textContent = 'Failed';
        }
        const placeholder = document.getElementById('autoRegimePlaceholder_' + ticker);
        if (placeholder) {
            placeholder.textContent = 'Regime detection failed: ' + (err?.message || 'Unknown error');
        }
    }
}

// ---------------------------------------------------------------------------
// Portfolio MDP — mirrors rlModels.js runPortfolioMDP() lines 375-465,
// using container IDs autoMDP_line and autoMDP_vbar
// ---------------------------------------------------------------------------

async function runAutoMDP(mdpStart, trainEnd, testStart) {
    try {
        const resp = await fetch('/api/stoch_portfolio_mdp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                equity_ticker: 'SPY',
                bond_ticker:   'IEF',
                start_date:    mdpStart,
                train_end:     trainEnd,
                test_start:    testStart,
                gamma:         0.99,
                cost_bps:      10
            })
        });
        const data = await resp.json();
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
            title: `Portfolio MDP: ${eq} / ${bd} \u2014 Policy Iteration (${iterations} iter)`,
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
            title: 'V* \u2014 Optimal State Values',
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
                        <td style="padding:6px 12px;font-weight:600;">${m.benchmark_label || '50/50'}</td>
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

        document.getElementById('autoMDPResults').innerHTML = `
            <div id="autoMDP_line" style="margin-bottom:10px;"></div>
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
            <div id="autoMDP_vbar" style="margin-top:20px;"></div>`;

        Plotly.newPlot('autoMDP_line', lineData, lineLayout, { responsive: true });
        Plotly.newPlot('autoMDP_vbar', vBarData, vBarLayout, { responsive: true });

        const badge = document.getElementById('autoMDPBadge');
        badge.setAttribute('style', BADGE_DONE);
        badge.textContent = 'Done';

    } catch (err) {
        const badge = document.getElementById('autoMDPBadge');
        if (badge) {
            badge.setAttribute('style', BADGE_FAILED);
            badge.textContent = 'Failed';
        }
        const results = document.getElementById('autoMDPResults');
        if (results) {
            results.innerHTML = rlAlert('Portfolio MDP failed: ' + err.message);
        }
    }
}

// ---------------------------------------------------------------------------
// Main entry point — called by stockScraper.js after scrape completes
// ---------------------------------------------------------------------------

async function triggerAutoRun(tickers) {
    // Compute dates
    const today = new Date();
    const endDate   = formatDate(today);
    const d2y = new Date(today); d2y.setFullYear(d2y.getFullYear() - 2);
    const startDate = formatDate(d2y);
    const d7y = new Date(today); d7y.setFullYear(d7y.getFullYear() - 7);
    const mdpStart  = formatDate(d7y);
    const trainEnd  = startDate;   // same as regime startDate (2y ago)
    const testStart = startDate;

    // Guard: need #analyticsResults container
    const analyticsResults = document.getElementById('analyticsResults');
    if (!analyticsResults) return;

    // Remove any existing autoRunSection to avoid duplication on re-runs
    document.getElementById('autoRunSection')?.remove();

    // Inject HTML scaffold
    analyticsResults.insertAdjacentHTML('afterbegin', buildAutoRunHTML(tickers));

    // Build promise array — regime per ticker + optional MDP
    const regimePromises = tickers.map(t => runAutoRegime(t, startDate, endDate));
    const allPromises = tickers.length >= 2
        ? [...regimePromises, runAutoMDP(mdpStart, trainEnd, testStart)]
        : regimePromises;

    await Promise.allSettled(allPromises);
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

window.AutoRun = { triggerAutoRun };
