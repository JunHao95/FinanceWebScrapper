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
    const ticker = (document.getElementById('regimeTicker')?.value || 'SPY').trim().toUpperCase();
    const days   = parseInt(document.getElementById('regimeDays')?.value || 1260, 10);

    const resultsDiv = document.getElementById('regimeResults');
    if (!resultsDiv) return;

    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = `<p style="color:#666;">⏳ Running Hamilton filter HMM on ${ticker} (${days} days of history)…
        <br><small>This usually takes 10–30 seconds.</small></p>`;

    try {
        const resp = await fetch('/api/regime_detection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tickers: [ticker], days })
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

        const r = data.regime;
        if (r.error) {
            resultsDiv.innerHTML = renderAlert(`Error: ${r.error}`);
            return;
        }

        const signalColor = r.signal === 'RISK_OFF' ? '#dc3545'
                          : r.signal === 'RISK_ON'  ? '#28a745'
                          : '#ffc107';

        const currentProbs = r.current_probabilities || {};
        const calmPct   = ((currentProbs.calm   || 0) * 100).toFixed(1);
        const stressedPct = ((currentProbs.stressed || 0) * 100).toFixed(1);

        // Build parameter table
        const params = r.parameters || {};
        let paramsHtml = '';
        for (const [sid, sp] of Object.entries(params)) {
            paramsHtml += `<tr>
                <td>${sp.regime === 'calm' ? '🟢 Calm' : '🔴 Stressed'}</td>
                <td>${(sp.mu_annualized * 100).toFixed(2)}%</td>
                <td>${(sp.sigma_annualized * 100).toFixed(2)}%</td>
            </tr>`;
        }

        // Transition matrix
        const P = r.transition_matrix || {};
        const K = 2;
        let pHtml = '<table style="font-size:12px; border-collapse:collapse; margin-top:8px;">';
        pHtml += '<tr><th></th><th>→ Calm</th><th>→ Stressed</th></tr>';
        const p00 = (P['P(0->0)'] || 0) * 100, p01 = (P['P(0->1)'] || 0) * 100;
        const p10 = (P['P(1->0)'] || 0) * 100, p11 = (P['P(1->1)'] || 0) * 100;
        pHtml += `<tr><td>From Calm</td><td>${p00.toFixed(1)}%</td><td>${p01.toFixed(1)}%</td></tr>`;
        pHtml += `<tr><td>From Stressed</td><td>${p10.toFixed(1)}%</td><td>${p11.toFixed(1)}%</td></tr>`;
        pHtml += '</table>';

        resultsDiv.innerHTML = `
            <div class="result-card">
                <h3>🌡️ Market Regime — ${ticker}</h3>

                <!-- Signal Banner -->
                <div style="background:${signalColor}; color:white; padding:12px 16px;
                    border-radius:6px; margin: 12px 0; font-size:16px; font-weight:bold;">
                    ${r.signal} — ${r.signal_description}
                </div>

                <!-- Current Probabilities -->
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:12px 0;">
                    <div style="background:#d4edda; border-radius:6px; padding:12px; text-align:center;">
                        <div style="font-size:24px; font-weight:bold;">${calmPct}%</div>
                        <div>🟢 Calm Regime</div>
                    </div>
                    <div style="background:#f8d7da; border-radius:6px; padding:12px; text-align:center;">
                        <div style="font-size:24px; font-weight:bold;">${stressedPct}%</div>
                        <div>🔴 Stressed Regime</div>
                    </div>
                </div>

                <!-- Model Parameters -->
                <h4>Regime Parameters</h4>
                <table style="width:100%; border-collapse:collapse; font-size:13px;">
                    <thead>
                        <tr style="background:#f8f9fa;">
                            <th>State</th><th>Ann. Return μ</th><th>Ann. Volatility σ</th>
                        </tr>
                    </thead>
                    <tbody>${paramsHtml}</tbody>
                </table>

                <!-- Transition Matrix -->
                <h4 style="margin-top:12px;">Transition Matrix (daily)</h4>
                ${pHtml}

                <!-- Historical stats -->
                <div style="margin-top:12px; font-size:13px; color:#555;">
                    <strong>Historical stress fraction:</strong>
                    ${((r.stress_fraction_historical || 0) * 100).toFixed(1)}% of observations<br>
                    <strong>Log-likelihood:</strong> ${(r.log_likelihood || 0).toFixed(2)}<br>
                    <strong>Observations:</strong> ${r.n_observations || 'N/A'}
                </div>
            </div>`;

    } catch (err) {
        resultsDiv.innerHTML = renderAlert(`Request failed: ${err.message}`);
    }
}

// ---------------------------------------------------------------------------
// Heston Calibration
// ---------------------------------------------------------------------------
async function runHestonCalibration() {
    const ticker     = (document.getElementById('calTicker')?.value || 'AAPL').trim().toUpperCase();
    const rate       = parseFloat(document.getElementById('calRate')?.value || 5) / 100;
    const optionType = document.getElementById('calOptionType')?.value || 'call';

    const resultsDiv = document.getElementById('calibrationResults');
    if (!resultsDiv) return;

    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = `<p style="color:#666;">⏳ Calibrating Heston parameters for ${ticker}…
        <br><small>Two-stage optimisation (brute grid + Nelder-Mead). May take 30–120s.</small></p>`;

    try {
        const resp = await fetch('/api/calibrate_heston', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, risk_free_rate: rate, option_type: optionType })
        });
        const data = await resp.json();

        if (!data.success) {
            resultsDiv.innerHTML = renderAlert(`Error: ${data.error}`);
            return;
        }

        const cal = data.calibration;
        const p = cal.calibrated_params || {};
        const feller = cal.feller_condition_satisfied;

        const fellerBadge = feller
            ? `<span style="background:#d4edda; color:#155724; padding:2px 8px; border-radius:4px; font-size:12px;">✓ Feller satisfied</span>`
            : `<span style="background:#f8d7da; color:#721c24; padding:2px 8px; border-radius:4px; font-size:12px;">✗ Feller violated (variance may reach 0)</span>`;

        resultsDiv.innerHTML = `
            <div class="result-card">
                <h3>⚙️ Heston Calibration — ${ticker}</h3>
                <p style="color:#666; font-size:13px;">Calibrated to ${cal.n_contracts} options contracts</p>

                ${fellerBadge}
                <br><br>

                <table style="width:100%; border-collapse:collapse; font-size:14px;">
                    <thead><tr style="background:#f8f9fa;">
                        <th>Parameter</th><th>Symbol</th><th>Value</th><th>Interpretation</th>
                    </tr></thead>
                    <tbody>
                        <tr><td>Initial Variance</td><td>ν₀</td>
                            <td>${(p.v0 || 0).toFixed(4)}</td>
                            <td>Implied vol ≈ ${(Math.sqrt(p.v0 || 0) * 100).toFixed(1)}%</td></tr>
                        <tr><td>Mean-Reversion Speed</td><td>κ</td>
                            <td>${(p.kappa || 0).toFixed(4)}</td>
                            <td>Half-life ≈ ${(Math.log(2) / (p.kappa || 1)).toFixed(1)} years</td></tr>
                        <tr><td>Long-Run Variance</td><td>θ</td>
                            <td>${(p.theta || 0).toFixed(4)}</td>
                            <td>LR vol ≈ ${(Math.sqrt(p.theta || 0) * 100).toFixed(1)}%</td></tr>
                        <tr><td>Vol of Variance</td><td>σᵥ</td>
                            <td>${(p.sigma_v || 0).toFixed(4)}</td>
                            <td>Controls smile curvature</td></tr>
                        <tr><td>Correlation</td><td>ρ</td>
                            <td>${(p.rho || 0).toFixed(4)}</td>
                            <td>${(p.rho || 0) < 0 ? 'Negative (leverage effect, skew)' : 'Positive'}</td></tr>
                    </tbody>
                </table>

                <div style="margin-top:12px; padding:10px; background:#f8f9fa; border-radius:4px; font-size:13px;">
                    <strong>Fit quality:</strong>
                    MSE = ${(cal.mse || 0).toFixed(4)} |
                    RMSE = $${(cal.rmse || 0).toFixed(4)} per contract<br>
                    <strong>Spot price:</strong> $${(cal.spot || 0).toFixed(2)} |
                    <strong>Risk-free rate:</strong> ${(cal.risk_free_rate * 100 || 0).toFixed(2)}%
                </div>

                <div style="margin-top:10px; font-size:12px; color:#888;">
                    Use these parameters in the Heston pricing calculator for smile-consistent pricing.
                </div>
            </div>`;

    } catch (err) {
        resultsDiv.innerHTML = renderAlert(`Request failed: ${err.message}`);
    }
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

    const resultsDiv = document.getElementById('cirResults');
    if (!resultsDiv) return;

    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<p style="color:#666;">⏳ Computing CIR yield curve…</p>';

    try {
        const payload = calibrate
            ? { r0, calibrate_to_treasuries: true }
            : { r0, kappa, theta, sigma,
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
            </div>`;

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

        // Term structure table (first 10 entries)
        let termRows = term.slice(0, 10).map(t => {
            const dp = (t.cumulative_default_prob * 100).toFixed(3);
            const color = t.cumulative_default_prob > 0.05 ? '#dc3545'
                        : t.cumulative_default_prob > 0.01 ? '#fd7e14' : '#28a745';
            return `<tr>
                <td>${t.horizon_years}Y</td>
                <td style="color:${color}; font-weight:bold;">${dp}%</td>
            </tr>`;
        }).join('');

        // Survival curve (first 20 years)
        const survival = (ttd.survival_curve || []).slice(0, 21);
        let survRows = survival.map(s =>
            `<tr><td>${s.year}Y</td><td>${(s.survival_prob * 100).toFixed(2)}%</td></tr>`
        ).join('');

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

                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; margin-top:15px;">
                    <!-- Default term structure -->
                    <div>
                        <h4>Default Probability Term Structure</h4>
                        <table style="width:100%; border-collapse:collapse; font-size:13px;">
                            <thead><tr style="background:#f8f9fa;"><th>Horizon</th><th>Cum. Default Prob.</th></tr></thead>
                            <tbody>${termRows}</tbody>
                        </table>
                    </div>

                    <!-- Survival curve -->
                    <div>
                        <h4>Survival Curve (MC)</h4>
                        <table style="width:100%; border-collapse:collapse; font-size:13px;">
                            <thead><tr style="background:#f8f9fa;"><th>Year</th><th>Survival Prob.</th></tr></thead>
                            <tbody>${survRows}</tbody>
                        </table>
                    </div>
                </div>

                <div style="margin-top:12px; font-size:13px; color:#555;">
                    <strong>Bond face value:</strong> $${faceValue.toFixed(0)} |
                    <strong>Coupon:</strong> ${(couponRate * 100).toFixed(1)}% |
                    <strong>Recovery rate:</strong> ${(recoveryRate * 100).toFixed(0)}%<br>
                    <strong>MC simulations:</strong> ${ttd.n_simulations || 'N/A'} |
                    <strong>Model:</strong> ${r.model || 'S&P Markov Chain'}
                </div>
            </div>`;

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
