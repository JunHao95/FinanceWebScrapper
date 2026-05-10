(function () {
    'use strict';

    var _sessionCache = {};

    function clearSession() {
        Object.keys(_sessionCache).forEach(function (k) { delete _sessionCache[k]; });
    }

    function _createTickerShell(ticker) {
        var container = document.getElementById('mlSignalsTabContent');
        if (!container) return null;
        var cardId = 'ml-card-' + ticker;
        var existing = document.getElementById(cardId);
        if (existing) return existing;
        var card = document.createElement('div');
        card.id = cardId;
        card.className = 'ml-ticker-card';
        card.innerHTML = '<div class="ml-ticker-header"><h3>' + ticker + '</h3></div>' +
            '<p class="ml-loading" style="color:#7f849c;">Training ML models — this may take a few seconds…</p>';
        container.appendChild(card);
        return card;
    }

    function fetchForTicker(ticker) {
        if (_sessionCache[ticker]) return;
        _sessionCache[ticker] = true;
        _createTickerShell(ticker);

        var base = '/api/ml_signals?ticker=' + encodeURIComponent(ticker) + '&feature=';
        Promise.all([
            fetch(base + 'direction').then(function (r) { return r.json(); }),
            fetch(base + 'regime').then(function (r) { return r.json(); }),
            fetch(base + 'credit').then(function (r) { return r.json(); }),
            fetch(base + 'lstm').then(function (r) { return r.json(); }),
        ]).then(function (results) {
            _renderTickerCard(ticker, results[0], results[1], results[2], results[3]);
        }).catch(function (err) {
            _renderError(ticker, err.toString());
        });
    }

    function fetchPCA(tickers) {
        var pcaCacheKey = 'pca:' + tickers.slice().sort().join(',');
        if (_sessionCache[pcaCacheKey]) return;
        _sessionCache[pcaCacheKey] = true;
        var container = document.getElementById('mlSignalsTabContent');
        if (!container) return;
        var pcaId = 'mlSignalsPcaSection';
        var section = document.getElementById(pcaId);
        if (!section) {
            section = document.createElement('div');
            section.id = pcaId;
            var firstCard = container.querySelector('.ml-ticker-card');
            if (firstCard) {
                container.insertBefore(section, firstCard);
            } else {
                container.appendChild(section);
            }
        }
        section.innerHTML = '<p style="color:#7f849c;font-style:italic;">Computing PCA…</p>';
        var url = '/api/ml_signals?feature=pca&' +
            tickers.map(function (t) { return 'tickers=' + encodeURIComponent(t); }).join('&');
        fetch(url).then(function (r) { return r.json(); }).then(function (result) {
            if (!result.pca_available) {
                section.innerHTML = '<p style="color:#7f849c;font-style:italic;">Add more tickers to enable PCA decomposition.</p>';
                return;
            }
            section.innerHTML =
                '<h3 style="margin-bottom:8px;">PCA Portfolio Decomposition</h3>' +
                '<div id="ml-pca-scree" style="width:100%;height:300px;"></div>' +
                '<div id="ml-pca-heatmap" style="width:100%;height:300px;margin-top:12px;"></div>' +
                '<div id="ml-pca-var" style="margin-top:12px;"></div>';
            if (typeof Plotly !== 'undefined') {
                if (result.scree_traces && result.scree_traces.length) {
                    Plotly.newPlot('ml-pca-scree', result.scree_traces, result.layout || {}, { staticPlot: true, responsive: true });
                }
                if (result.heatmap_traces && result.heatmap_traces.length) {
                    Plotly.newPlot('ml-pca-heatmap', result.heatmap_traces, result.layout || {}, { staticPlot: true, responsive: true });
                }
            }
            if (result.portfolio_var) {
                var pv = result.portfolio_var;

                function _varSeverity(pct) {
                    if (pct >= 5) return { color: '#e74c3c', label: 'High', tip: 'Tail risk is elevated — portfolio could lose over 5% in a single day at this confidence level.' };
                    if (pct >= 2.5) return { color: '#f39c12', label: 'Moderate', tip: 'Tail risk is moderate. Normal for diversified equity portfolios.' };
                    return { color: '#a6e3a1', label: 'Low', tip: 'Tail risk is contained. Portfolio volatility is below average.' };
                }

                var sv99 = _varSeverity(pv.var_99_1d_pct);
                var sv95 = _varSeverity(pv.var_95_1d_pct);
                var hv99 = _varSeverity(pv.hist_var_99_1d_pct);
                var hv95 = _varSeverity(pv.hist_var_95_1d_pct);

                function _badge(s) {
                    return '<span title="' + s.tip + '" style="margin-left:8px;padding:1px 7px;border-radius:10px;font-size:11px;background:' + s.color + '22;color:' + s.color + ';border:1px solid ' + s.color + '44;">' + s.label + '</span>';
                }

                var varHtml =
                    '<h4 style="color:#cdd6f4;margin:0 0 4px;">Portfolio VaR — Equal Weight, 1-Day</h4>' +
                    '<p style="font-size:11px;color:#585b70;margin:0 0 10px;">Assumes equal-weight long position across all tickers. <strong style="color:#7f849c;">Parametric</strong> uses normal distribution (σ × z-score). <strong style="color:#7f849c;">Historical</strong> uses actual return quantile — no distribution assumption.</p>' +
                    '<table style="width:100%;border-collapse:collapse;color:#cdd6f4;font-size:13px;">' +
                    '<tr style="border-bottom:1px solid #313244;">' +
                        '<td style="padding:6px 8px;color:#7f849c;">Daily Std Dev</td>' +
                        '<td style="padding:6px 8px;">' + pv.port_daily_std_pct.toFixed(2) + '%</td>' +
                        '<td style="padding:6px 8px;font-size:11px;color:#585b70;">Average daily return volatility of equal-weight portfolio</td>' +
                    '</tr>' +
                    '<tr style="border-bottom:1px solid #313244;">' +
                        '<td style="padding:6px 8px;color:#7f849c;">Parametric VaR 99%</td>' +
                        '<td style="padding:6px 8px;color:' + sv99.color + ';">' + pv.var_99_1d_pct.toFixed(2) + '%' + _badge(sv99) + '</td>' +
                        '<td style="padding:6px 8px;font-size:11px;color:#585b70;">1-in-100 chance of losing more than this in one day</td>' +
                    '</tr>' +
                    '<tr style="border-bottom:1px solid #313244;">' +
                        '<td style="padding:6px 8px;color:#7f849c;">Parametric VaR 95%</td>' +
                        '<td style="padding:6px 8px;color:' + sv95.color + ';">' + pv.var_95_1d_pct.toFixed(2) + '%' + _badge(sv95) + '</td>' +
                        '<td style="padding:6px 8px;font-size:11px;color:#585b70;">1-in-20 chance of losing more than this in one day</td>' +
                    '</tr>' +
                    '<tr style="border-bottom:1px solid #313244;">' +
                        '<td style="padding:6px 8px;color:#7f849c;">Historical VaR 99%</td>' +
                        '<td style="padding:6px 8px;color:' + hv99.color + ';">' + pv.hist_var_99_1d_pct.toFixed(2) + '%' + _badge(hv99) + '</td>' +
                        '<td style="padding:6px 8px;font-size:11px;color:#585b70;">Worst 1% of actual past daily losses (no distribution assumed)</td>' +
                    '</tr>' +
                    '<tr>' +
                        '<td style="padding:6px 8px;color:#7f849c;">Historical VaR 95%</td>' +
                        '<td style="padding:6px 8px;color:' + hv95.color + ';">' + pv.hist_var_95_1d_pct.toFixed(2) + '%' + _badge(hv95) + '</td>' +
                        '<td style="padding:6px 8px;font-size:11px;color:#585b70;">Worst 5% of actual past daily losses</td>' +
                    '</tr>' +
                    '</table>';

                if (pv.pc_contributions && pv.pc_contributions.length) {
                    varHtml += '<div style="margin-top:12px;">' +
                        '<p style="font-size:12px;color:#7f849c;margin:0 0 6px;font-weight:600;">PC Factor Decomposition</p>' +
                        '<p style="font-size:11px;color:#585b70;margin:0 0 8px;">How much of portfolio variance (and VaR) each principal component drives. Market Factor dominates in correlated selloffs.</p>' +
                        '<table style="width:100%;border-collapse:collapse;font-size:12px;color:#cdd6f4;">' +
                        '<tr style="color:#585b70;font-size:11px;">' +
                            '<th style="padding:3px 8px;text-align:left;font-weight:normal;">Factor</th>' +
                            '<th style="padding:3px 8px;text-align:right;font-weight:normal;">Variance Share</th>' +
                            '<th style="padding:3px 8px;text-align:right;font-weight:normal;">VaR 99% Contrib</th>' +
                            '<th style="padding:3px 8px;text-align:left;font-weight:normal;">Interpretation</th>' +
                        '</tr>' +
                        pv.pc_contributions.map(function (pc, i) {
                            var interp = i === 0
                                ? 'Broad market moves — correlation rises sharply in downturns'
                                : i === 1
                                ? 'Sector rotation risk — winners vs. losers within portfolio'
                                : 'Convexity / idiosyncratic spread — stock-specific divergence';
                            var shareColor = pc.variance_share_pct >= 60 ? '#e74c3c' : pc.variance_share_pct >= 20 ? '#f39c12' : '#a6e3a1';
                            return '<tr style="border-top:1px solid #313244;">' +
                                '<td style="padding:5px 8px;color:#cdd6f4;">' + pc.name + '</td>' +
                                '<td style="padding:5px 8px;text-align:right;color:' + shareColor + ';">' + pc.variance_share_pct.toFixed(1) + '%</td>' +
                                '<td style="padding:5px 8px;text-align:right;color:#7f849c;">' + pc.var_99_contribution_pct.toFixed(4) + '%</td>' +
                                '<td style="padding:5px 8px;color:#585b70;font-size:11px;">' + interp + '</td>' +
                            '</tr>';
                        }).join('') +
                        '</table></div>';
                }

                var varContainer = document.getElementById('ml-pca-var');
                if (varContainer) { varContainer.innerHTML = varHtml; }
            }
        }).catch(function (err) {
            section.innerHTML = '<p style="color:#e74c3c;">PCA error: ' + err.toString() + '</p>';
        });
    }

    function _renderTickerCard(ticker, dirData, regData, credData, lstmData) {
        var card = document.getElementById('ml-card-' + ticker);
        if (!card) return;

        var html = '<div class="ml-ticker-header"><h3>' + ticker + '</h3></div>';

        // Section A — Direction Signal (RF)
        html += '<div class="ml-section"><h4>RF Direction Signal</h4>';
        if (dirData.insufficient_data) {
            html += '<p style="color:#7f849c;">Insufficient history (&lt; 265 trading days) — cannot train direction signal.</p>';
        } else {
            var dirConf = Math.round((dirData.confidence || 0) * 100);
            var dirColor = (dirData.signal === 'Bullish') ? '#2ecc71' : '#e74c3c';
            html += '<span class="ml-badge" style="background:' + dirColor + ';color:#fff;padding:3px 8px;border-radius:4px;">' +
                dirConf + '% ' + (dirData.signal || '') + '</span>';
            html += '<div id="ml-dir-chart-' + ticker + '" style="width:100%;height:250px;margin-top:10px;"></div>';
        }
        html += '</div>';

        // Section B — K-Means Regime
        html += '<div class="ml-section"><h4>Market Regime</h4>';
        html += '<span class="ml-badge" style="background:#2c2e3b;color:#cdd6f4;padding:3px 8px;border-radius:4px;margin-right:6px;">HMM: ' +
            (regData.hmm_regime || 'N/A') + '</span>';
        html += '<span class="ml-badge" style="background:#2c2e3b;color:#cdd6f4;padding:3px 8px;border-radius:4px;">K-Means: ' +
            (regData.current_regime || 'N/A') + '</span>';
        if (regData.models_agree === true) {
            html += ' <small style="color:#2ecc71;">Models agree</small>';
        } else if (regData.models_agree === false) {
            html += ' <small style="color:#f39c12;">Models diverge</small>';
        }
        html += '<div id="ml-reg-chart-' + ticker + '" style="width:100%;height:200px;margin-top:10px;"></div>';
        html += '</div>';

        // Section C — Credit Risk Score
        html += '<div class="ml-section"><h4>Credit Risk</h4>';
        if (credData.degenerate_labels || credData.insufficient_data) {
            html += '<p style="color:#7f849c;">Credit model could not train (insufficient label variation for this ticker).</p>';
        } else {
            var distressPct = Math.round((credData.p_distress || 0) * 100);
            var credColor = distressPct < 30 ? '#2ecc71' : (distressPct < 60 ? '#f39c12' : '#e74c3c');
            html += '<p style="color:' + credColor + ';font-weight:bold;">' + distressPct + '% probability of financial distress</p>';
            if (credData.top_factors && credData.top_factors.length) {
                html += '<ul style="margin:6px 0 6px 18px;">';
                credData.top_factors.slice(0, 3).forEach(function (f) {
                    var label = (f && typeof f === 'object') ? f.name : f;
                    html += '<li>' + label + '</li>';
                });
                html += '</ul>';
            }
            if (credData.caveat) {
                html += '<p><small style="color:#7f849c;font-style:italic;">' + credData.caveat + '</small></p>';
            }
        }
        html += '</div>';

        // Section D — LSTM Direction Signal
        html += '<div class="ml-section"><h4>LSTM Direction Signal</h4>';
        if (lstmData.lstm_available === false) {
            html += '<p style="color:#7f849c;">Deep learning disabled on cloud — run locally to enable.</p>';
        } else {
            var lstmConf = Math.round((lstmData.confidence || 0) * 100);
            var lstmColor = (lstmData.signal === 'Bullish') ? '#2ecc71' : '#e74c3c';
            html += '<span class="ml-badge" style="background:' + lstmColor + ';color:#fff;padding:3px 8px;border-radius:4px;">' +
                lstmConf + '% ' + (lstmData.signal || '') + '</span>';
            if (dirData.signal && lstmData.signal) {
                if (dirData.signal === lstmData.signal) {
                    html += ' <small style="color:#2ecc71;">RF and LSTM agree: ' + dirData.signal + '</small>';
                } else {
                    html += ' <small style="color:#f39c12;">RF: ' + dirData.signal + ' | LSTM: ' + lstmData.signal + ' — signals diverge</small>';
                }
            }
            html += '<div id="ml-lstm-chart-' + ticker + '" style="width:100%;height:200px;margin-top:10px;"></div>';
        }
        html += '</div>';

        card.innerHTML = html;

        if (typeof Plotly !== 'undefined') {
            if (!dirData.insufficient_data && dirData.traces && dirData.traces.length) {
                Plotly.newPlot('ml-dir-chart-' + ticker, dirData.traces, dirData.layout || {}, { staticPlot: true, responsive: true });
            }
            if (regData.regime_timeline_traces && regData.regime_timeline_traces.length) {
                Plotly.newPlot('ml-reg-chart-' + ticker, regData.regime_timeline_traces, regData.layout || {}, { staticPlot: true, responsive: true });
            }
            if (lstmData.lstm_available !== false && lstmData.loss_curve_traces && lstmData.loss_curve_traces.length) {
                Plotly.newPlot('ml-lstm-chart-' + ticker, lstmData.loss_curve_traces, lstmData.layout || {}, { staticPlot: true, responsive: true });
            }
        }
    }

    function _renderError(ticker, message) {
        var card = document.getElementById('ml-card-' + ticker);
        if (!card) return;
        card.innerHTML = '<p style="color:#e74c3c;">Error loading ML signals: ' + message + '</p>';
    }

    window.MLSignals = { fetchForTicker: fetchForTicker, clearSession: clearSession, fetchPCA: fetchPCA };
})();
