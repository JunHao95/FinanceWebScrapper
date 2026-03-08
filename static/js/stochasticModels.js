/**
 * Stochastic Models Module
 * Handles UI for: Market Regime Detection, Heston Calibration,
 * CIR Yield Curve, Credit Risk, Heston Pricing, Merton Pricing
 */

// ---------------------------------------------------------------------------
// Sub-tab switching for Stochastic Models tab
// ---------------------------------------------------------------------------
function switchStochasticTab(tabName) {
    document.querySelectorAll('.stoch-content').forEach(el => {
        el.style.display = 'none';
    });
    document.querySelectorAll('[id^="stochTab_"]').forEach(btn => {
        btn.classList.remove('active');
    });

    const content = document.getElementById('stochContent_' + tabName);
    if (content) content.style.display = 'block';

    const btn = document.getElementById('stochTab_' + tabName);
    if (btn) btn.classList.add('active');
}

// ---------------------------------------------------------------------------
// Utility: HTML escaping to prevent XSS from API/user content
// ---------------------------------------------------------------------------
function escapeHTML(str) {
    let s = String(str);
    return s
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ---------------------------------------------------------------------------
// Utility: render a simple key-value table
// ---------------------------------------------------------------------------
function renderKVTable(obj, title) {
    if (!obj || typeof obj !== 'object') return '';
    let rows = '';
    for (const [k, v] of Object.entries(obj)) {
        const display = typeof v === 'number' ? v.toFixed(6) : escapeHTML(String(v));
        rows += `<tr><td><strong>${escapeHTML(k)}</strong></td><td>${display}</td></tr>`;
    }
    return `
        ${title ? `<h4 style="margin: 12px 0 6px;">${escapeHTML(title)}</h4>` : ''}
        <table style="width:100%; border-collapse:collapse; font-size:13px;">
            <tbody>${rows}</tbody>
        </table>`;
}

function renderAlert(msg, type = 'error') {
    const colors = { error: '#f8d7da', info: '#d1ecf1', success: '#d4edda', warning: '#fff3cd' };
    const border = { error: '#f5c6cb', info: '#bee5eb', success: '#c3e6cb', warning: '#ffeeba' };
    return `<div style="background:${colors[type] || colors.error}; border:1px solid ${border[type] || border.error};
        padding:12px; border-radius:4px; margin-top:10px;">${escapeHTML(msg)}</div>`;
}

// ---------------------------------------------------------------------------
// Regime Detection
// ---------------------------------------------------------------------------
async function runRegimeDetection() {
    const ticker = document.getElementById('regimeTicker').value.trim().toUpperCase();
    const startDate = document.getElementById('regimeStartDate').value;
    const endDate = document.getElementById('regimeEndDate').value;
    const resultsDiv = document.getElementById('regimeResults');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<p style="color:#666;">Running HMM regime detection...</p>';
    try {
        const resp = await fetch('/api/regime_detection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, start_date: startDate, end_date: endDate })
        });
        if (!resp.ok) { resultsDiv.innerHTML = renderAlert(`Server error ${resp.status}`); return; }
        const data = await resp.json();
        if (!data.success) { resultsDiv.innerHTML = renderAlert(data.error || 'Unknown error'); return; }

        // Inject chart containers (purge first to avoid double-trace on re-run)
        resultsDiv.innerHTML = `
            <p><strong>Signal:</strong> ${escapeHTML(String(data.signal))}</p>
            <div id="regimeProbChart" style="margin-bottom:20px;"></div>
            <div id="regimePriceChart"></div>`;

        // Chart 1: Filtered probability time series
        Plotly.newPlot('regimeProbChart', [{
            x: data.dates,
            y: data.filtered_probs,
            type: 'scatter',
            mode: 'lines',
            fill: 'tozeroy',
            name: 'P(Stressed)',
            line: { color: '#dc3545' }
        }], {
            title: `Regime Probability — ${ticker}`,
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
        Plotly.newPlot('regimePriceChart', [{
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

    } catch (err) {
        resultsDiv.innerHTML = renderAlert(`Request failed: ${err.message}`);
    }
}

// ---------------------------------------------------------------------------
// Heston Calibration — SSE-driven with live progress and IV comparison chart
// ---------------------------------------------------------------------------
function rmseLabel(rmse) {
    if (rmse < 0.01) return { label: 'Good', color: '#28a745' };
    if (rmse < 0.03) return { label: 'Acceptable', color: '#ffc107' };
    return { label: 'Poor', color: '#dc3545' };
}

async function runHestonCalibration() {
    const ticker     = (document.getElementById('calTicker')?.value || 'AAPL').trim().toUpperCase();
    const rate       = parseFloat(document.getElementById('calRate')?.value || 5) / 100;
    const optionType = document.getElementById('calOptionType')?.value || 'call';

    const resultsDiv  = document.getElementById('calibrationResults');
    const progressDiv = document.getElementById('calibProgress');
    const ivChartDiv  = document.getElementById('calibIVChart');

    if (resultsDiv) { resultsDiv.style.display = 'block'; resultsDiv.innerHTML = '<p style="color:#666;">Starting calibration...</p>'; }
    if (progressDiv) { progressDiv.style.display = 'block'; progressDiv.textContent = 'Connecting...'; }
    if (ivChartDiv) { ivChartDiv.innerHTML = ''; }

    const url = `/api/calibrate_heston_stream?ticker=${encodeURIComponent(ticker)}&risk_free_rate=${rate}&option_type=${encodeURIComponent(optionType)}`;
    const src = new EventSource(url);
    let lastIteration = 0;

    src.onmessage = async (e) => {
        const d = JSON.parse(e.data);
        if (typeof d.error === 'string') {
            src.close();
            if (progressDiv) progressDiv.style.display = 'none';
            if (resultsDiv) resultsDiv.innerHTML = renderAlert(`Calibration error: ${escapeHTML(d.error)}`);
            return;
        }
        if (!d.done) {
            lastIteration = d.iteration;
            if (progressDiv) progressDiv.textContent = `Iteration ${d.iteration} — RMSE: ${(typeof d.error === 'number' ? d.error : 0).toFixed(6)}`;
        } else {
            src.close();
            if (progressDiv) progressDiv.textContent = lastIteration > 0
                ? `Calibration complete after ${lastIteration} iterations.`
                : 'Calibration complete.';

            // Fetch final result from standard route for full chart data
            try {
                const resp = await fetch('/api/calibrate_heston', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ticker, risk_free_rate: rate, option_type: optionType })
                });
                if (!resp.ok) { if (resultsDiv) resultsDiv.innerHTML = renderAlert(`Server error ${resp.status}`); return; }
                const data = await resp.json();
                if (!data.success) { if (resultsDiv) resultsDiv.innerHTML = renderAlert(data.error || 'Calibration failed'); return; }

                const cal = data.calibration;
                const p   = cal.calibrated_params || {};
                const ql  = rmseLabel(cal.rmse || 0);
                const feller = cal.feller_condition_satisfied;

                const fellerBadge = feller
                    ? `<span style="background:#d4edda; color:#155724; padding:2px 8px; border-radius:4px; font-size:12px;">Feller satisfied</span>`
                    : `<span style="background:#f8d7da; color:#721c24; padding:2px 8px; border-radius:4px; font-size:12px;">Feller violated (variance may reach 0)</span>`;

                if (resultsDiv) {
                    resultsDiv.innerHTML = `
                        <div class="result-card">
                            <h3>Heston Calibration — ${escapeHTML(ticker)}</h3>
                            <p style="color:#666; font-size:13px;">Calibrated to ${cal.n_contracts} options contracts</p>
                            ${fellerBadge}
                            <div style="margin:10px 0;">
                                <strong>Relative RMSE: </strong>
                                <span style="background:${ql.color}; color:#fff; padding:3px 10px; border-radius:12px; font-size:13px;">${escapeHTML(ql.label)}</span>
                                <span style="margin-left:8px; font-size:13px;">${((cal.rmse || 0) * 100).toFixed(2)}%</span>
                            </div>
                            <table style="width:100%; border-collapse:collapse; font-size:14px;">
                                <thead><tr style="background:#f8f9fa;">
                                    <th>Parameter</th><th>Symbol</th><th>Value</th><th>Interpretation</th>
                                </tr></thead>
                                <tbody>
                                    <tr><td>Initial Variance</td><td>v0</td>
                                        <td>${(p.v0 || 0).toFixed(4)}</td>
                                        <td>Implied vol ~ ${(Math.sqrt(p.v0 || 0) * 100).toFixed(1)}%</td></tr>
                                    <tr><td>Mean-Reversion Speed</td><td>kappa</td>
                                        <td>${(p.kappa || 0).toFixed(4)}</td>
                                        <td>Half-life ~ ${(Math.log(2) / (p.kappa || 1)).toFixed(1)} years</td></tr>
                                    <tr><td>Long-Run Variance</td><td>theta</td>
                                        <td>${(p.theta || 0).toFixed(4)}</td>
                                        <td>LR vol ~ ${(Math.sqrt(p.theta || 0) * 100).toFixed(1)}%</td></tr>
                                    <tr><td>Vol of Variance</td><td>sigma_v</td>
                                        <td>${(p.sigma_v || 0).toFixed(4)}</td>
                                        <td>Controls smile curvature</td></tr>
                                    <tr><td>Correlation</td><td>rho</td>
                                        <td>${(p.rho || 0).toFixed(4)}</td>
                                        <td>${(p.rho || 0) < 0 ? 'Negative (leverage effect, skew)' : 'Positive'}</td></tr>
                                </tbody>
                            </table>
                            <div style="margin-top:12px; padding:10px; background:#f8f9fa; border-radius:4px; font-size:13px;">
                                <strong>Fit quality:</strong>
                                MSE = ${(cal.mse || 0).toFixed(4)} |
                                RMSE = ${(cal.rmse || 0).toFixed(4)}<br>
                                <strong>Spot price:</strong> $${(cal.spot || 0).toFixed(2)} |
                                <strong>Risk-free rate:</strong> ${((cal.risk_free_rate || 0) * 100).toFixed(2)}%
                            </div>
                            <div style="margin-top:10px; font-size:12px; color:#888;">
                                Use these parameters in the Heston pricing calculator for smile-consistent pricing.
                            </div>
                        </div>`;
                }

                // IV comparison chart
                if (ivChartDiv && cal.strikes && cal.market_ivs && cal.fitted_ivs) {
                    Plotly.newPlot('calibIVChart', [
                        {
                            x: cal.strikes, y: cal.market_ivs,
                            type: 'scatter', mode: 'markers',
                            name: 'Market IV', marker: { color: '#667eea', size: 8 }
                        },
                        {
                            x: cal.strikes, y: cal.fitted_ivs,
                            type: 'scatter', mode: 'markers',
                            name: 'Fitted IV', marker: { color: '#dc3545', size: 8, symbol: 'x' }
                        }
                    ], {
                        title: `Heston Calibration — ${escapeHTML(ticker)}`,
                        xaxis: { title: 'Strike' },
                        yaxis: { title: 'Implied Volatility', tickformat: '.1%' },
                        height: 380,
                        margin: { t: 50, l: 70, r: 20, b: 50 }
                    });
                }
            } catch (err) {
                if (resultsDiv) resultsDiv.innerHTML = renderAlert(`Result fetch failed: ${err.message}`);
            }
        }
    };

    src.onerror = () => {
        src.close();
        if (progressDiv) progressDiv.textContent = 'SSE connection closed.';
    };
}

// ---------------------------------------------------------------------------
// Merton Calibration
// ---------------------------------------------------------------------------
async function runMertonCalibration() {
    const ticker     = (document.getElementById('mertonCalTicker')?.value || 'AAPL').trim().toUpperCase();
    const rate       = parseFloat(document.getElementById('mertonCalRate')?.value || 5) / 100;
    const optionType = document.getElementById('mertonCalOptionType')?.value || 'call';

    const resultsDiv = document.getElementById('mertonCalResults');
    if (!resultsDiv) return;

    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = `<p style="color:#666;">⏳ Calibrating Merton jump-diffusion parameters for ${escapeHTML(ticker)}…
        <br><small>Two-stage optimisation (brute grid + Nelder-Mead). May take 30–90s.</small></p>`;

    try {
        const resp = await fetch('/api/calibrate_merton', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, risk_free_rate: rate, option_type: optionType })
        });
        if (!resp.ok) {
            resultsDiv.innerHTML = renderAlert(`Server error ${resp.status}: ${await resp.text()}`);
            return;
        }
        const data = await resp.json();

        if (!data.success) {
            resultsDiv.innerHTML = renderAlert(`Error: ${data.error}`);
            return;
        }

        const cal = data.calibration;
        const p = cal.calibrated_params || {};

        resultsDiv.innerHTML = `
            <div class="result-card">
                <h3>🦘 Merton Calibration — ${escapeHTML(ticker)}</h3>
                <p style="color:#666; font-size:13px;">Calibrated to ${cal.n_contracts} options contracts</p>

                <table style="width:100%; border-collapse:collapse; font-size:14px;">
                    <thead><tr style="background:#f8f9fa;">
                        <th>Parameter</th><th>Symbol</th><th>Value</th><th>Interpretation</th>
                    </tr></thead>
                    <tbody>
                        <tr><td>Diffusion Volatility</td><td>σ</td>
                            <td>${(p.sigma || 0).toFixed(4)}</td>
                            <td>Continuous vol ≈ ${((p.sigma || 0) * 100).toFixed(1)}%</td></tr>
                        <tr><td>Jump Intensity</td><td>λ</td>
                            <td>${(p.lambda || 0).toFixed(4)}</td>
                            <td>${(p.lambda || 0).toFixed(2)} jumps/year on average</td></tr>
                        <tr><td>Mean Log-Jump</td><td>μⱼ</td>
                            <td>${(p.mu_j || 0).toFixed(4)}</td>
                            <td>${(p.mu_j || 0) < 0 ? 'Negative (downward jump bias)' : 'Positive (upward jump bias)'}</td></tr>
                        <tr><td>Std Log-Jump</td><td>δⱼ</td>
                            <td>${(p.delta_j || 0).toFixed(4)}</td>
                            <td>Controls jump magnitude spread</td></tr>
                        <tr><td>Mean Jump Size</td><td>μ̄ⱼ</td>
                            <td>${(p.mu_bar || 0).toFixed(4)}</td>
                            <td>${((p.mu_bar || 0) * 100).toFixed(2)}% average jump return</td></tr>
                    </tbody>
                </table>

                <div style="margin-top:12px; padding:10px; background:#f8f9fa; border-radius:4px; font-size:13px;">
                    <strong>Fit quality:</strong>
                    MSE = ${(cal.mse || 0).toFixed(4)} |
                    RMSE = $${(cal.rmse || 0).toFixed(4)} per contract<br>
                    <strong>Spot price:</strong> $${(cal.spot || 0).toFixed(2)} |
                    <strong>Risk-free rate:</strong> ${((cal.risk_free_rate || 0) * 100).toFixed(2)}%
                </div>

                <div style="margin-top:10px; font-size:12px; color:#888;">
                    Use these parameters in the Merton pricing calculator for jump-risk-consistent pricing.
                </div>
            </div>`;

    } catch (err) {
        resultsDiv.innerHTML = renderAlert(`Request failed: ${err.message}`);
    }
}

// ---------------------------------------------------------------------------
// CIR Yield Curve
// ---------------------------------------------------------------------------
async function runCIRModel() {
    const r0    = parseFloat(document.getElementById('cirR0')?.value || 5.3) / 100;
    const kappa = parseFloat(document.getElementById('cirKappa')?.value || 1.5);
    const theta = parseFloat(document.getElementById('cirTheta')?.value || 5.0) / 100;
    const sigma = parseFloat(document.getElementById('cirSigma')?.value || 10) / 100;
    const calibrate = document.getElementById('cirCalibrateTreasuries')?.checked || false;
    const model = document.getElementById('cirModel')?.value || 'cir';

    const resultsDiv = document.getElementById('cirResults');
    if (!resultsDiv) return;

    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<p style="color:#666;">⏳ Computing CIR yield curve…</p>';

    try {
        const payload = calibrate
            ? { r0, calibrate_to_treasuries: true }
            : { model, r0, kappa, theta, sigma,
                maturities: [0.083, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30] };

        const resp = await fetch('/api/interest_rate_model', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await resp.json();

        if (!data.success) {
            resultsDiv.innerHTML = renderAlert(`Error: ${data.error}`);
            return;
        }

        const r = data.result;
        const curve = r.implied_yield_curve || r.yield_curve || [];
        const params = r.calibrated_params || r.params || { kappa, theta, sigma };
        const feller = r.feller_condition_satisfied;
        const fellerBadge = feller
            ? `<span style="background:#d4edda; color:#155724; padding:2px 8px; border-radius:4px; font-size:12px;">✓ Feller: 2κθ > σ² satisfied</span>`
            : `<span style="background:#f8d7da; color:#721c24; padding:2px 8px; border-radius:4px; font-size:12px;">✗ Feller violated (rates may go negative)</span>`;

        let tableRows = curve.map(pt => `
            <tr>
                <td>${pt.maturity === 0.083 ? '1M' : pt.maturity <= 0.25 ? '3M' : pt.maturity + 'Y'}</td>
                <td>${pt.maturity.toFixed(3)}</td>
                <td>${(pt.bond_price * 100).toFixed(4)}%</td>
                <td>${(pt.spot_rate * 100).toFixed(4)}%</td>
            </tr>`).join('');

        resultsDiv.innerHTML = `
            <div class="result-card">
                <h3>📐 CIR Yield Curve ${calibrate ? '(Calibrated to US Treasuries)' : ''}</h3>
                ${fellerBadge}
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; margin:12px 0;">
                    <div style="background:#f8f9fa; padding:10px; border-radius:4px; text-align:center;">
                        <div style="font-size:18px; font-weight:bold;">${((params.kappa || kappa)).toFixed(3)}</div>
                        <div style="font-size:12px; color:#666;">κ (mean reversion)</div>
                    </div>
                    <div style="background:#f8f9fa; padding:10px; border-radius:4px; text-align:center;">
                        <div style="font-size:18px; font-weight:bold;">${((params.theta || theta) * 100).toFixed(2)}%</div>
                        <div style="font-size:12px; color:#666;">θ (long-run rate)</div>
                    </div>
                    <div style="background:#f8f9fa; padding:10px; border-radius:4px; text-align:center;">
                        <div style="font-size:18px; font-weight:bold;">${((params.sigma || sigma) * 100).toFixed(2)}%</div>
                        <div style="font-size:12px; color:#666;">σ (rate volatility)</div>
                    </div>
                </div>
                ${r.mse !== undefined ? `<p style="font-size:13px;color:#666;">Calibration RMSE: ${(Math.sqrt(r.mse)*100).toFixed(4)}%</p>` : ''}
                <table style="width:100%; border-collapse:collapse; font-size:13px; margin-top:10px;">
                    <thead><tr style="background:#f8f9fa;">
                        <th>Label</th><th>Maturity (yr)</th><th>B(0,T)</th><th>Spot Rate</th>
                    </tr></thead>
                    <tbody>${tableRows}</tbody>
                </table>
                <p style="font-size:12px; color:#888; margin-top:8px;">
                    B(0,T) = zero-coupon bond price. Spot rate = −ln B(0,T)/T.
                </p>
                <div id="yieldCurveChart" style="margin-top:16px;"></div>
            </div>`;

        if (curve.length > 0) {
            Plotly.newPlot('yieldCurveChart', [{
                x: curve.map(pt => pt.maturity),
                y: curve.map(pt => pt.spot_rate * 100),
                type: 'scatter',
                mode: 'lines+markers',
                name: `${escapeHTML(r.model || 'CIR')} Yield Curve`,
                line: { color: '#667eea', width: 2 }
            }], {
                title: `${escapeHTML(r.model || 'CIR')} Yield Curve`,
                xaxis: { title: 'Maturity (years)' },
                yaxis: { title: 'Yield (%)', tickformat: '.2f' },
                height: 350,
                margin: { t: 40, l: 70, r: 20, b: 50 }
            }, { responsive: true });
        }

    } catch (err) {
        resultsDiv.innerHTML = renderAlert(`Request failed: ${err.message}`);
    }
}

// ---------------------------------------------------------------------------
// Credit Risk
// ---------------------------------------------------------------------------
async function runCreditRisk() {
    const rating       = document.getElementById('creditRating')?.value || 'BBB';
    const horizon      = parseInt(document.getElementById('creditHorizon')?.value || 5, 10);
    const recoveryRate = parseFloat(document.getElementById('creditRecovery')?.value || 40) / 100;
    const faceValue    = parseFloat(document.getElementById('creditFaceValue')?.value || 1000);
    const couponRate   = parseFloat(document.getElementById('creditCoupon')?.value || 5) / 100;

    const resultsDiv = document.getElementById('creditResults');
    if (!resultsDiv) return;

    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = `<p style="color:#666;">⏳ Running Markov chain credit simulation (${rating}, ${horizon}Y)…</p>`;

    try {
        const resp = await fetch('/api/credit_risk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rating, horizon, recovery_rate: recoveryRate,
                                   face_value: faceValue, coupon_rate: couponRate })
        });
        const data = await resp.json();

        if (!data.success) {
            resultsDiv.innerHTML = renderAlert(`Error: ${data.error}`);
            return;
        }

        const r = data.result;
        if (r.error) {
            resultsDiv.innerHTML = renderAlert(`Error: ${r.error}`);
            return;
        }

        const bond = r.bond_analysis || {};
        const ttd  = r.time_to_default || {};
        const term = r.default_probability_term_structure || [];

        // Survival curve data for chart
        const survival = (ttd.survival_curve || []).slice(0, 21);

        resultsDiv.innerHTML = `
            <div class="result-card">
                <h3>💳 Credit Risk — ${rating} (${horizon}-Year Horizon)</h3>

                <!-- Key metrics -->
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; margin:12px 0;">
                    <div style="background:#f8d7da; padding:10px; border-radius:4px; text-align:center;">
                        <div style="font-size:20px; font-weight:bold; color:#dc3545;">
                            ${(bond.default_probability * 100).toFixed(2)}%
                        </div>
                        <div style="font-size:12px; color:#666;">Default Probability (${horizon}Y)</div>
                    </div>
                    <div style="background:#d4edda; padding:10px; border-radius:4px; text-align:center;">
                        <div style="font-size:20px; font-weight:bold; color:#28a745;">
                            $${(bond.expected_bond_value || 0).toFixed(2)}
                        </div>
                        <div style="font-size:12px; color:#666;">Expected Bond Value</div>
                    </div>
                    <div style="background:#d1ecf1; padding:10px; border-radius:4px; text-align:center;">
                        <div style="font-size:20px; font-weight:bold; color:#17a2b8;">
                            ${ttd.median_time_to_default !== null ? ttd.median_time_to_default + 'Y' : 'N/A'}
                        </div>
                        <div style="font-size:12px; color:#666;">Median Time to Default</div>
                    </div>
                </div>

                <div id="defaultProbChart" style="margin-top:16px;"></div>
                <div id="creditSurvivalChart" style="margin-top:8px;"></div>
                <div id="markovHeatmap" style="margin-top:8px;"></div>

                <div style="margin-top:12px; font-size:13px; color:#555;">
                    <strong>Bond face value:</strong> $${faceValue.toFixed(0)} |
                    <strong>Coupon:</strong> ${(couponRate * 100).toFixed(1)}% |
                    <strong>Recovery rate:</strong> ${(recoveryRate * 100).toFixed(0)}%<br>
                    <strong>MC simulations:</strong> ${ttd.n_simulations || 'N/A'} |
                    <strong>Model:</strong> ${r.model || 'S&P Markov Chain'}
                </div>
            </div>`;

        // Default probability term structure line chart
        if (term.length > 0) {
            Plotly.newPlot('defaultProbChart', [{
                x: term.map(t => t.horizon_years),
                y: term.map(t => t.cumulative_default_prob * 100),
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Default Probability',
                line: { color: '#dc3545', width: 2 }
            }], {
                title: 'Default Probability Term Structure',
                xaxis: { title: 'Horizon (years)' },
                yaxis: { title: 'Cumulative Default Prob. (%)', tickformat: '.2f' },
                height: 320,
                margin: { t: 40, l: 70, r: 20, b: 50 }
            }, { responsive: true });
        }

        // Survival curve chart
        if (survival.length > 0) {
            Plotly.newPlot('creditSurvivalChart', [{
                x: survival.map(s => s.year),
                y: survival.map(s => s.survival_prob * 100),
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Survival Probability',
                line: { color: '#28a745', width: 2 },
                fill: 'tozeroy',
                fillcolor: 'rgba(40,167,69,0.1)'
            }], {
                title: 'Survival Curve (Monte Carlo)',
                xaxis: { title: 'Year' },
                yaxis: { title: 'Survival Probability (%)', tickformat: '.1f' },
                height: 320,
                margin: { t: 40, l: 70, r: 20, b: 50 }
            }, { responsive: true });
        }

        // Markov transition matrix heatmap (S&P 1-year matrix via nstep n=1)
        try {
            const mResp = await fetch('/api/markov_chain', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: 'nstep', n: 1, current_rating: rating })
            });
            const mData = await mResp.json();
            if (mData.success) {
                const mr = mData.result;
                const labels = mr.ratings || mr.labels || mr.transition_matrix_n.map((_, i) => `S${i}`);
                Plotly.newPlot('markovHeatmap', [{
                    z: mr.transition_matrix_n,
                    x: labels,
                    y: labels,
                    type: 'heatmap',
                    colorscale: 'Blues',
                    text: mr.transition_matrix_n.map(row => row.map(v => (v * 100).toFixed(1) + '%')),
                    texttemplate: '%{text}',
                    showscale: true
                }], {
                    title: 'S&P 1-Year Rating Transition Matrix',
                    height: 420,
                    margin: { t: 50, l: 80, r: 20, b: 80 }
                }, { responsive: true });
            }
        } catch (_) { /* heatmap is bonus — swallow errors */ }

    } catch (err) {
        resultsDiv.innerHTML = renderAlert(`Request failed: ${err.message}`);
    }
}

// ---------------------------------------------------------------------------
// Heston Pricing (Options Pricing tab)
// ---------------------------------------------------------------------------
async function calculateHestonPrice() {
    const S       = parseFloat(document.getElementById('hestonSpot')?.value);
    const K       = parseFloat(document.getElementById('hestonStrike')?.value);
    const T       = parseFloat(document.getElementById('hestonMaturity')?.value);
    const r       = parseFloat(document.getElementById('hestonRate')?.value) / 100;
    const v0      = parseFloat(document.getElementById('hestonV0')?.value) / 100;    // input in %²
    const kappa   = parseFloat(document.getElementById('hestonKappa')?.value);
    const theta   = parseFloat(document.getElementById('hestonTheta')?.value) / 100;
    const sigma_v = parseFloat(document.getElementById('hestonSigmaV')?.value);
    const rho     = parseFloat(document.getElementById('hestonRho')?.value);
    const optType = document.getElementById('hestonType')?.value || 'call';

    const resultsDiv = document.getElementById('optionResults');
    const contentDiv = document.getElementById('optionResultsContent');
    if (!resultsDiv || !contentDiv) return;

    // Validate all required numeric inputs before sending to API
    const requiredNumerics = { S, K, T, r, v0, kappa, theta, sigma_v, rho };
    const invalidFields = Object.entries(requiredNumerics)
        .filter(([, val]) => !Number.isFinite(val))
        .map(([name]) => name);
    if (invalidFields.length > 0) {
        resultsDiv.style.display = 'block';
        contentDiv.innerHTML = renderAlert(`Invalid or missing numeric inputs: ${invalidFields.join(', ')}`);
        return;
    }

    resultsDiv.style.display = 'block';
    contentDiv.innerHTML = '<p style="color:#666;">⏳ Computing Heston price via Lewis (2001) quadrature…</p>';

    try {
        const resp = await fetch('/api/heston_price', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ spot: S, strike: K, maturity: T, risk_free_rate: r,
                v0, kappa, theta, sigma_v, rho, option_type: optType })
        });
        const data = await resp.json();

        if (!data.success) {
            contentDiv.innerHTML = `<div style="color:red;">Error: ${data.error}</div>`;
            return;
        }

        const h = data.heston;
        const bsPrice = data.black_scholes_comparison?.price;
        const diff = data.price_difference;
        const feller = h.feller_condition_satisfied;

        const fellerBadge = feller
            ? `<span style="background:#d4edda; color:#155724; padding:2px 8px; border-radius:4px;">✓ Feller satisfied</span>`
            : `<span style="background:#f8d7da; color:#721c24; padding:2px 8px; border-radius:4px;">✗ Feller violated</span>`;

        contentDiv.innerHTML = `
            <div class="result-card">
                <h3>⚡ Heston Model Price — ${optType.toUpperCase()}</h3>
                ${fellerBadge}
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin:15px 0;">
                    <div style="background:#e8f5e9; padding:15px; border-radius:6px; text-align:center;">
                        <div style="font-size:28px; font-weight:bold; color:#2e7d32;">
                            $${(h.price || 0).toFixed(4)}
                        </div>
                        <div style="color:#555;">Heston Price (Lewis 2001)</div>
                    </div>
                    <div style="background:#f8f9fa; padding:15px; border-radius:6px; text-align:center;">
                        <div style="font-size:28px; font-weight:bold; color:#555;">
                            $${(bsPrice || 0).toFixed(4)}
                        </div>
                        <div style="color:#555;">Black-Scholes (σ = √ν₀)</div>
                    </div>
                </div>
                <p style="font-size:13px; color:#666;">
                    Price difference |Heston − BS| = <strong>$${(diff || 0).toFixed(4)}</strong>
                    ${diff > 0.01 ? '← Heston captures smile premium' : '← Models agree closely'}
                </p>
                <div style="font-size:12px; margin-top:10px; color:#888;">
                    <strong>Feller condition:</strong> 2κθ = ${(h.feller_lhs || 0).toFixed(4)},
                    σᵥ² = ${(h.feller_rhs || 0).toFixed(4)}
                </div>
            </div>`;

    } catch (err) {
        contentDiv.innerHTML = `<div style="color:red;">Request failed: ${err.message}</div>`;
    }
}

// ---------------------------------------------------------------------------
// Heston Pricing sub-tab (Stochastic Models tab)
// ---------------------------------------------------------------------------
async function runHestonPricing() {
    const params = {
        S: parseFloat(document.getElementById('hestonS').value),
        K: parseFloat(document.getElementById('hestonK').value),
        T: parseFloat(document.getElementById('hestonT').value),
        r: parseFloat(document.getElementById('hestonR').value),
        v0: parseFloat(document.getElementById('hestonPriceV0').value),
        kappa: parseFloat(document.getElementById('hestonPriceKappa').value),
        theta: parseFloat(document.getElementById('hestonPriceTheta').value),
        sigma_v: parseFloat(document.getElementById('hestonPriceSigmaV').value),
        rho: parseFloat(document.getElementById('hestonPriceRho').value),
        option_type: document.getElementById('hestonOptionType').value
    };
    const resultsDiv = document.getElementById('hestonPriceResults');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<p style="color:#666;">Pricing...</p>';

    try {
        // Map to field names expected by /api/heston_price route
        const priceResp = await fetch('/api/heston_price', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                spot: params.S,
                strike: params.K,
                maturity: params.T,
                risk_free_rate: params.r,
                v0: params.v0,
                kappa: params.kappa,
                theta: params.theta,
                sigma_v: params.sigma_v,
                rho: params.rho,
                option_type: params.option_type
            })
        });
        if (!priceResp.ok) { resultsDiv.innerHTML = renderAlert(`Server error ${priceResp.status}`); return; }
        const priceData = await priceResp.json();
        if (!priceData.success) { resultsDiv.innerHTML = renderAlert(priceData.error || 'Pricing error'); return; }

        const hestonPrice = priceData.heston.price;
        const bsPrice = priceData.black_scholes_comparison.price;

        resultsDiv.innerHTML = `
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px; margin-bottom:20px;">
                <div style="background:#d4edda; border-radius:8px; padding:16px; text-align:center;">
                    <div style="font-size:12px; color:#666;">Heston Price</div>
                    <div style="font-size:28px; font-weight:bold; color:#155724;">$${escapeHTML(hestonPrice.toFixed(4))}</div>
                </div>
                <div style="background:#cce5ff; border-radius:8px; padding:16px; text-align:center;">
                    <div style="font-size:12px; color:#666;">Black-Scholes Price</div>
                    <div style="font-size:28px; font-weight:bold; color:#004085;">$${escapeHTML(bsPrice.toFixed(4))}</div>
                </div>
            </div>
            <p style="color:#666; font-size:13px;">Loading IV surface...</p>
            <div id="hestonIVSurface"></div>`;

        // Fetch IV surface
        const surfaceResp = await fetch('/api/heston_iv_surface', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                S: params.S, r: params.r, v0: params.v0, kappa: params.kappa,
                theta: params.theta, sigma_v: params.sigma_v, rho: params.rho,
                option_type: params.option_type,
                K_min: params.S * 0.8, K_max: params.S * 1.2, K_steps: 10,
                T_min: 0.1, T_max: 2.0, T_steps: 8
            })
        });
        if (!surfaceResp.ok) { return; }
        const surfaceData = await surfaceResp.json();
        if (!surfaceData.success) { return; }

        // Clear loading text
        const surfaceContainer = document.getElementById('hestonIVSurface');
        if (!surfaceContainer) return;
        const prevP = surfaceContainer.previousElementSibling;
        if (prevP && prevP.tagName === 'P') prevP.remove();

        Plotly.newPlot('hestonIVSurface', [{
            type: 'surface',
            x: surfaceData.strikes,
            y: surfaceData.maturities,
            z: surfaceData.iv_grid,
            colorscale: 'Viridis',
            colorbar: { title: 'IV' }
        }], {
            title: 'Heston Implied Volatility Surface',
            scene: {
                xaxis: { title: 'Strike' },
                yaxis: { title: 'Maturity (yrs)' },
                zaxis: { title: 'Implied Vol' }
            },
            height: 450,
            margin: { t: 50, l: 0, r: 0, b: 0 }
        });

    } catch (err) {
        resultsDiv.innerHTML = renderAlert(`Request failed: ${err.message}`);
    }
}

// ---------------------------------------------------------------------------
// BCC Calibration
// ---------------------------------------------------------------------------
async function runBCCCalibration() {
    const ticker = document.getElementById('bccTicker').value.trim().toUpperCase();
    const rate = parseFloat(document.getElementById('bccRate').value) || 0.05;
    const optionType = document.getElementById('bccOptionType').value;
    const resultsDiv = document.getElementById('bccResults');
    const ivChartDiv = document.getElementById('bccIVChart');

    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<p style="color:#666;">Calibrating BCC model... (may take 30–90 seconds)</p>';
    if (ivChartDiv) ivChartDiv.innerHTML = '';

    try {
        const resp = await fetch('/api/calibrate_bcc', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, risk_free_rate: rate, option_type: optionType })
        });
        if (!resp.ok) { resultsDiv.innerHTML = renderAlert(`Server error ${resp.status}`); return; }
        const data = await resp.json();
        if (!data.success) { resultsDiv.innerHTML = renderAlert(data.error || 'BCC calibration failed'); return; }

        const rmse = data.rmse || 0;
        const ql = {
            label: (rmse < 0.01 ? 'Good' : rmse < 0.03 ? 'Acceptable' : 'Poor'),
            color: (rmse < 0.01 ? '#28a745' : rmse < 0.03 ? '#ffc107' : '#dc3545')
        };
        const paramsHtml = Object.entries(data.params || {})
            .map(([k, v]) => `<tr><td style="padding:4px 12px;">${escapeHTML(k)}</td><td style="padding:4px 12px;">${typeof v === 'number' ? v.toFixed(4) : escapeHTML(String(v))}</td></tr>`)
            .join('');

        resultsDiv.innerHTML = `
            <div style="margin-bottom:15px;">
                <strong>Relative RMSE: </strong>
                <span style="background:${ql.color}; color:#fff; padding:3px 10px; border-radius:12px; font-size:13px;">${escapeHTML(ql.label)}</span>
                <span style="margin-left:8px; font-size:13px;">${(rmse * 100).toFixed(2)}%</span>
            </div>
            <table style="border-collapse:collapse; font-size:13px;">
                <thead><tr><th style="text-align:left; padding:4px 12px; border-bottom:1px solid #dee2e6;">Parameter</th><th style="padding:4px 12px; border-bottom:1px solid #dee2e6;">Value</th></tr></thead>
                <tbody>${paramsHtml}</tbody>
            </table>`;

        // IV comparison chart
        if (ivChartDiv && data.strikes && data.market_ivs && data.fitted_ivs) {
            Plotly.newPlot('bccIVChart', [
                {
                    x: data.strikes, y: data.market_ivs,
                    type: 'scatter', mode: 'markers',
                    name: 'Market IV', marker: { color: '#667eea', size: 8 }
                },
                {
                    x: data.strikes, y: data.fitted_ivs,
                    type: 'scatter', mode: 'markers',
                    name: 'BCC Fitted IV', marker: { color: '#fd7e14', size: 8, symbol: 'x' }
                }
            ], {
                title: `BCC Calibration — ${escapeHTML(ticker)}`,
                xaxis: { title: 'Strike' },
                yaxis: { title: 'Implied Volatility', tickformat: '.1%' },
                height: 380,
                margin: { t: 50, l: 70, r: 20, b: 50 }
            });
        }

    } catch (err) {
        resultsDiv.innerHTML = renderAlert(`Request failed: ${err.message}`);
    }
}

// ---------------------------------------------------------------------------
// Merton Jump-Diffusion Pricing (Options Pricing tab)
// ---------------------------------------------------------------------------
async function calculateMertonPrice() {
    const S       = parseFloat(document.getElementById('mertonSpot')?.value);
    const K       = parseFloat(document.getElementById('mertonStrike')?.value);
    const T       = parseFloat(document.getElementById('mertonMaturity')?.value);
    const r       = parseFloat(document.getElementById('mertonRate')?.value) / 100;
    const sigma   = parseFloat(document.getElementById('mertonSigma')?.value) / 100;
    const lam     = parseFloat(document.getElementById('mertonLambda')?.value);
    const mu_j    = parseFloat(document.getElementById('mertonMuJ')?.value);
    const delta_j = parseFloat(document.getElementById('mertonDeltaJ')?.value);
    const optType = document.getElementById('mertonType')?.value || 'call';

    const resultsDiv = document.getElementById('optionResults');
    const contentDiv = document.getElementById('optionResultsContent');
    if (!resultsDiv || !contentDiv) return;

    resultsDiv.style.display = 'block';
    contentDiv.innerHTML = '<p style="color:#666;">⏳ Computing Merton jump-diffusion price…</p>';

    try {
        const resp = await fetch('/api/merton_price', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ spot: S, strike: K, maturity: T, risk_free_rate: r,
                sigma, lambda: lam, mu_j, delta_j, option_type: optType })
        });
        const data = await resp.json();

        if (!data.success) {
            contentDiv.innerHTML = `<div style="color:red;">Error: ${data.error}</div>`;
            return;
        }

        const res = data.result;
        const muBar = Math.exp(mu_j + 0.5 * delta_j * delta_j) - 1;

        contentDiv.innerHTML = `
            <div class="result-card">
                <h3>🦘 Merton Jump-Diffusion Price — ${optType.toUpperCase()}</h3>
                <div style="background:#e3f2fd; padding:15px; border-radius:6px; text-align:center; margin:15px 0;">
                    <div style="font-size:32px; font-weight:bold; color:#1565c0;">
                        $${(res.price || 0).toFixed(4)}
                    </div>
                    <div style="color:#555;">Merton (1976) Price via Lewis (2001)</div>
                </div>
                <table style="width:100%; border-collapse:collapse; font-size:13px;">
                    <tbody>
                        <tr><td><strong>Jump intensity λ</strong></td><td>${lam.toFixed(2)} jumps/year</td></tr>
                        <tr><td><strong>Mean log-jump μⱼ</strong></td><td>${mu_j.toFixed(4)}</td></tr>
                        <tr><td><strong>Std log-jump δⱼ</strong></td><td>${delta_j.toFixed(4)}</td></tr>
                        <tr><td><strong>Mean jump size μ̄ⱼ</strong></td><td>${(muBar * 100).toFixed(2)}%</td></tr>
                        <tr><td><strong>Diffusion vol σ</strong></td><td>${(sigma * 100).toFixed(2)}%</td></tr>
                    </tbody>
                </table>
                <p style="font-size:12px; color:#888; margin-top:10px;">
                    Higher λ or more negative μⱼ → fatter left tails → higher put prices.
                </p>
            </div>`;

    } catch (err) {
        contentDiv.innerHTML = `<div style="color:red;">Request failed: ${err.message}</div>`;
    }
}

// ---------------------------------------------------------------------------
// Markov Chain Analysis (steady-state, absorption, MDP)
// ---------------------------------------------------------------------------
function showMarkovForm(mode) {
    ['steady_state', 'absorption', 'mdp'].forEach(function(m) {
        const el = document.getElementById('markovForm_' + m);
        if (el) el.style.display = m === mode ? 'block' : 'none';
    });
}

async function runMarkovChain() {
    const mode = document.getElementById('markovMode')?.value || 'steady_state';
    const resultsDiv = document.getElementById('markovResults');
    if (!resultsDiv) return;
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<p style="color:#666;">&#9203; Computing&#8230;</p>';

    const transitionDiv = document.getElementById('markovTransitionHeatmap');
    if (transitionDiv) transitionDiv.style.display = 'none';

    try {
        let payload = { mode };
        let userMatrix = null;

        if (mode === 'steady_state') {
            const raw = document.getElementById('markovMatrixSS')?.value.trim();
            if (raw) {
                try { payload.transition_matrix = JSON.parse(raw); userMatrix = payload.transition_matrix; }
                catch (e) { resultsDiv.innerHTML = renderAlert('Invalid JSON in transition matrix: ' + e.message); return; }
            }
        } else if (mode === 'absorption') {
            const raw = document.getElementById('markovMatrixAbs')?.value.trim();
            if (raw) {
                try { payload.transition_matrix = JSON.parse(raw); }
                catch (e) { resultsDiv.innerHTML = renderAlert('Invalid JSON in transition matrix: ' + e.message); return; }
            }
        } else if (mode === 'mdp') {
            payload.gamma    = parseFloat(document.getElementById('markovGamma')?.value || 0.95);
            payload.n_periods = parseInt(document.getElementById('markovNPeriods')?.value || 1000, 10);
        }

        const resp = await fetch('/api/markov_chain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await resp.json();

        if (!data.success) {
            resultsDiv.innerHTML = renderAlert('Error: ' + (data.error || 'Unknown error'));
            return;
        }

        const r = data.result;

        if (r.error) {
            resultsDiv.innerHTML = renderAlert(r.error, 'warning');
            return;
        }

        if (mode === 'steady_state') {
            const labels  = r.ratings || r.steady_state.map((_, i) => 'State ' + i);
            const values  = (r.steady_state || []).map(v => +(v * 100).toFixed(4));
            resultsDiv.innerHTML = `
                <div class="result-card">
                    <h3>&#128200; Steady-State Distribution</h3>
                    <p style="font-size:13px; color:#666;">Long-run fraction of time spent in each state.</p>
                    <div id="markovSteadyChart" style="margin-top:12px;"></div>
                </div>`;
            Plotly.newPlot('markovSteadyChart', [{
                x: labels,
                y: values,
                type: 'bar',
                marker: { color: '#667eea' }
            }], {
                title: 'Steady-State Distribution',
                xaxis: { title: 'State' },
                yaxis: { title: 'Probability (%)', tickformat: '.2f' },
                height: 350,
                margin: { t: 40, l: 70, r: 20, b: 60 }
            }, { responsive: true });

            try {
                const nstepPayload = { mode: 'nstep', n: 1 };
                if (userMatrix) nstepPayload.transition_matrix = userMatrix;
                const nstepResp = await fetch('/api/markov_chain', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(nstepPayload)
                });
                const nstepData = await nstepResp.json();
                if (nstepData.success && nstepData.result && nstepData.result.transition_matrix_n) {
                    const tm = nstepData.result.transition_matrix_n;
                    const tmLabels = nstepData.result.ratings || tm.map((_, i) => 'State ' + i);
                    if (transitionDiv) {
                        transitionDiv.style.display = 'block';
                        transitionDiv.innerHTML = '<div class="result-card"><h3>&#127758; Transition Matrix</h3><p style="font-size:13px; color:#666;">1-step transition probabilities between states.</p><div id="markovTransitionHeatmapPlot" style="margin-top:12px;"></div></div>';
                        Plotly.newPlot('markovTransitionHeatmapPlot', [{
                            z: tm,
                            x: tmLabels,
                            y: tmLabels,
                            type: 'heatmap',
                            colorscale: 'Blues',
                            text: tm.map(function(row) { return row.map(function(v) { return (v * 100).toFixed(1) + '%'; }); }),
                            texttemplate: '%{text}',
                            showscale: true
                        }], {
                            title: 'S&P 1-Year Rating Transition Matrix',
                            height: 420,
                            margin: { t: 50, l: 80, r: 20, b: 80 }
                        }, { responsive: true });
                    }
                }
            } catch (nstepErr) {
                console.warn('Transition matrix heatmap fetch failed:', nstepErr.message);
            }

        } else if (mode === 'absorption') {
            const tIdx  = r.transient_indices  || [];
            const aIdx  = r.absorbing_indices  || [];
            const absM  = r.absorption_matrix  || [];
            const rowLabels = tIdx.map(i => 'S' + i + ' (transient)');
            const colLabels = aIdx.map(i => 'S' + i + ' (absorbing)');

            resultsDiv.innerHTML = `
                <div class="result-card">
                    <h3>&#128257; Absorption Probabilities</h3>
                    <p style="font-size:13px; color:#666;">
                        Probability that a chain starting in transient state i is absorbed by absorbing state j.
                        Transient states: [${tIdx.join(', ')}] &nbsp; Absorbing states: [${aIdx.join(', ')}]
                    </p>
                    <div id="markovAbsorptionHeatmap" style="margin-top:12px;"></div>
                </div>`;
            Plotly.newPlot('markovAbsorptionHeatmap', [{
                z: absM,
                x: colLabels,
                y: rowLabels,
                type: 'heatmap',
                colorscale: 'Blues',
                text: absM.map(row => row.map(v => (v * 100).toFixed(1) + '%')),
                texttemplate: '%{text}',
                showscale: true
            }], {
                title: 'Absorption Probability Matrix',
                height: 400,
                margin: { t: 50, l: 120, r: 20, b: 80 }
            }, { responsive: true });

        } else if (mode === 'mdp') {
            const states  = r.states  || [];
            const actions = r.actions || [];
            const policy  = r.optimal_policy  || [];
            const vf      = r.value_function  || [];

            const policyCards = states.map(function(state, i) {
                return `<div style="background:#f8f9fa; padding:10px; border-radius:4px; text-align:center; min-width:120px;">
                    <div style="font-weight:bold; font-size:13px;">${escapeHTML(state)}</div>
                    <div style="font-size:11px; color:#667eea; margin-top:4px;">${escapeHTML(actions[policy[i]] || '?')}</div>
                </div>`;
            }).join('');

            const convNote = r.converged
                ? `Converged in ${r.convergence_iterations} iterations (&#947; = ${(r.gamma || 0.95).toFixed(2)})`
                : `Did not converge in ${r.convergence_iterations} iterations`;

            resultsDiv.innerHTML = `
                <div class="result-card">
                    <h3>&#127919; MDP — Optimal Portfolio Policy</h3>
                    <p style="font-size:13px; color:#666; margin-bottom:8px;">${escapeHTML(convNote)}</p>
                    <p style="font-size:12px; color:#555; margin-bottom:10px;"><strong>Optimal Policy:</strong></p>
                    <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px;">${policyCards}</div>
                    <div id="markovMDPChart" style="margin-top:12px;"></div>
                </div>`;
            Plotly.newPlot('markovMDPChart', [{
                x: states,
                y: vf,
                type: 'bar',
                marker: { color: '#28a745' }
            }], {
                title: 'V* — Optimal Value Function',
                xaxis: { title: 'State' },
                yaxis: { title: 'V*(s)', tickformat: '.2f' },
                height: 320,
                margin: { t: 40, l: 70, r: 20, b: 50 }
            }, { responsive: true });
        }

    } catch (err) {
        resultsDiv.innerHTML = renderAlert('Request failed: ' + err.message);
    }
}

// ---------------------------------------------------------------------------
// CIR/Vasicek model selector — swap default parameter values on model change
// ---------------------------------------------------------------------------
function updateCIRDefaults(model) {
    const defaults = {
        cir:     { kappa: '1.5', theta: '5.0', sigma: '10',  r0: '5.3' },
        vasicek: { kappa: '0.5', theta: '6.0', sigma: '2.0', r0: '5.3' }
    };
    const d = defaults[model] || defaults.cir;
    const set = function(id, val) { const el = document.getElementById(id); if (el) el.value = val; };
    set('cirKappa', d.kappa);
    set('cirTheta', d.theta);
    set('cirSigma', d.sigma);
    set('cirR0',    d.r0);
}
