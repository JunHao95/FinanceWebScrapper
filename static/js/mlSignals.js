(function () {
    'use strict';

    var _sessionCache = {};
    var _activeIntervals = [];
    var _tickerSignals = {};

    function clearSession() {
        Object.keys(_sessionCache).forEach(function (k) { delete _sessionCache[k]; });
        _activeIntervals.forEach(function (id) { clearInterval(id); });
        _activeIntervals = [];
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
                if (varContainer) {
                    varContainer.innerHTML = varHtml;
                    if (pv) { _addPcaInterpretButton(varContainer, pv); }
                }
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

        // Store signals for synthesis
        _tickerSignals[ticker] = {
            direction: dirData.insufficient_data ? null : {
                signal: dirData.signal,
                confidence: dirData.confidence
            },
            regime: {
                hmm: regData.hmm_regime,
                kmeans: regData.current_regime,
                agree: regData.models_agree
            },
            credit: credData.degenerate_labels || credData.insufficient_data ? null : {
                p_distress: credData.p_distress,
                top_factors: (credData.top_factors || []).slice(0, 3).map(function (f) {
                    return typeof f === 'object' ? f.name : f;
                })
            },
            lstm: lstmData.lstm_available === false ? null : {
                signal: lstmData.signal,
                confidence: lstmData.confidence
            }
        };

        // Inject Feynman research button per section
        var mlSections = card.querySelectorAll('.ml-section');
        var sectionKeys = ['direction', 'regime', 'credit', 'lstm'];
        mlSections.forEach(function (sec, i) {
            var key = sectionKeys[i];
            if (!key) return;
            if (key === 'direction' && dirData.insufficient_data) return;
            if (key === 'credit' && (credData.degenerate_labels || credData.insufficient_data)) return;
            if (key === 'lstm' && lstmData.lstm_available === false) return;
            var sigs = (_tickerSignals[ticker] || {})[key];
            _addResearchButton(sec, ticker, key, sigs);
        });

        // Synthesis button at card bottom
        _addSynthesisButton(card, ticker);
    }

    // ---- Feynman Research helpers ----

    function _escHtml(s) {
        return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function _applyInline(t) {
        // Extract inline code first to protect it from other replacements
        var codes = [];
        t = t.replace(/`([^`]+)`/g, function (_, c) {
            codes.push('<code>' + _escHtml(c) + '</code>');
            return '\x00' + (codes.length - 1) + '\x00';
        });
        t = t
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/_(.+?)_/g, '<em>$1</em>');
        t = t.replace(/\x00(\d+)\x00/g, function (_, i) { return codes[+i]; });
        return t;
    }

    function _renderMarkdown(text) {
        // Extract fenced code blocks to protect them
        var blocks = [];
        text = text.replace(/```(\w*)\n?([\s\S]*?)```/g, function (_, lang, code) {
            var tag = lang ? '<pre><code class="lang-' + lang + '">' : '<pre><code>';
            blocks.push(tag + _escHtml(code.trim()) + '</code></pre>');
            return '\x01' + (blocks.length - 1) + '\x01';
        });

        var lines = text.split('\n');
        var out = [];
        var inUl = false, inOl = false, inTbl = false, tblHead = true;

        function closeList() {
            if (inUl) { out.push('</ul>'); inUl = false; }
            if (inOl) { out.push('</ol>'); inOl = false; }
        }
        function closeTable() {
            if (inTbl) { out.push('</tbody></table>'); inTbl = false; tblHead = true; }
        }

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];

            // Restore code blocks inline
            if (/\x01\d+\x01/.test(line)) {
                closeList(); closeTable();
                out.push(line.replace(/\x01(\d+)\x01/g, function (_, n) { return blocks[+n]; }));
                continue;
            }

            // Headings
            var hm = line.match(/^(#{1,4}) (.+)/);
            if (hm) {
                closeList(); closeTable();
                var lvl = Math.min(hm[1].length + 2, 6); // ## → h4, ### → h5
                out.push('<h' + lvl + '>' + _applyInline(hm[2]) + '</h' + lvl + '>');
                continue;
            }

            // Horizontal rule
            if (/^---+$/.test(line.trim())) {
                closeList(); closeTable();
                out.push('<hr>');
                continue;
            }

            // Table row
            if (/^\|/.test(line)) {
                closeList();
                if (!inTbl) {
                    out.push('<table class="feynman-table"><thead>');
                    inTbl = true; tblHead = true;
                }
                // Skip separator row |---|---|
                if (/^\|[-| :]+\|$/.test(line)) {
                    out.push('</thead><tbody>');
                    tblHead = false;
                    continue;
                }
                var cells = line.split('|').slice(1, -1);
                var tag = tblHead ? 'th' : 'td';
                out.push('<tr>' + cells.map(function (c) {
                    return '<' + tag + '>' + _applyInline(c.trim()) + '</' + tag + '>';
                }).join('') + '</tr>');
                continue;
            } else {
                closeTable();
            }

            // Unordered list
            var ulm = line.match(/^[-*] (.+)/);
            if (ulm) {
                if (inOl) { out.push('</ol>'); inOl = false; }
                if (!inUl) { out.push('<ul>'); inUl = true; }
                out.push('<li>' + _applyInline(ulm[1]) + '</li>');
                continue;
            }

            // Ordered list
            var olm = line.match(/^\d+\. (.+)/);
            if (olm) {
                if (inUl) { out.push('</ul>'); inUl = false; }
                if (!inOl) { out.push('<ol>'); inOl = true; }
                out.push('<li>' + _applyInline(olm[1]) + '</li>');
                continue;
            }

            // Close open lists on non-list line
            closeList();

            // Empty line = paragraph break (skip)
            if (line.trim() === '') {
                continue;
            }

            out.push('<p>' + _applyInline(line) + '</p>');
        }

        closeList();
        closeTable();

        return out.join('\n');
    }

    function _renderResearchPanel(sectionEl, markdownText) {
        var existing = sectionEl.querySelector('.feynman-panel');
        if (existing) existing.remove();
        var panel = document.createElement('details');
        panel.className = 'feynman-panel';
        panel.innerHTML =
            '<summary class="feynman-panel-summary">Academic Context</summary>' +
            '<div class="feynman-panel-body"><p>' + _renderMarkdown(markdownText) + '</p></div>';
        sectionEl.appendChild(panel);
    }

    function _renderResearchError(sectionEl, errorText) {
        var isTimeout = errorText === 'timeout';
        var msg = isTimeout
            ? 'Research timed out — Feynman took longer than 5 minutes.'
            : ('Research error: ' + _escHtml(errorText));
        var existing = sectionEl.querySelector('.feynman-error');
        if (existing) existing.remove();
        var errEl = document.createElement('p');
        errEl.className = 'feynman-error';
        errEl.style.color = '#e74c3c';
        errEl.style.fontSize = '0.85em';
        errEl.textContent = msg;
        sectionEl.appendChild(errEl);
    }

    function _pollResearchJob(jobId, btn, sectionEl, resetText) {
        var label = resetText || 'Research This Model';
        var elapsed = 0;
        var maxPolls = 60; // 5 min cap (60 × 5s)
        var polls = 0;

        var interval = setInterval(function () {
            elapsed += 5;
            polls += 1;
            btn.textContent = 'Searching… (' + elapsed + 's)';

            if (polls >= maxPolls) {
                clearInterval(interval);
                _activeIntervals = _activeIntervals.filter(function (id) { return id !== interval; });
                btn.textContent = label;
                btn.disabled = false;
                _renderResearchError(sectionEl, 'timeout');
                return;
            }

            fetch('/api/feynman_status/' + jobId)
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    if (d.status === 'done') {
                        clearInterval(interval);
                        _activeIntervals = _activeIntervals.filter(function (id) { return id !== interval; });
                        btn.textContent = label;
                        btn.disabled = false;
                        _renderResearchPanel(sectionEl, d.result);
                    } else if (d.status === 'error') {
                        clearInterval(interval);
                        _activeIntervals = _activeIntervals.filter(function (id) { return id !== interval; });
                        btn.textContent = label;
                        btn.disabled = false;
                        _renderResearchError(sectionEl, d.error || 'Unknown error');
                    }
                })
                .catch(function () {
                    clearInterval(interval);
                    _activeIntervals = _activeIntervals.filter(function (id) { return id !== interval; });
                    btn.textContent = label;
                    btn.disabled = false;
                });
        }, 5000);
        _activeIntervals.push(interval);
    }

    function _startResearch(btn, sectionEl, ticker, section, signals, endpoint, loadingText, resetText) {
        btn.disabled = true;
        btn.textContent = loadingText || 'Searching academic papers…';
        var body = endpoint === '/api/feynman_synthesis'
            ? { ticker: ticker, signals: signals }
            : endpoint === '/api/feynman_pca_interpret'
            ? { pca_data: signals }
            : { section: section, ticker: ticker, signals: signals };
        fetch(endpoint || '/api/feynman_research', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.available === false) {
                    btn.textContent = 'Research unavailable';
                    btn.disabled = true;
                    return;
                }
                _pollResearchJob(d.job_id, btn, sectionEl, resetText);
            })
            .catch(function () {
                btn.textContent = resetText || 'Research This Model';
                btn.disabled = false;
            });
    }

    function _pollResearchJobExt(jobId, btn, sectionEl, resetText) {
        return _pollResearchJob(jobId, btn, sectionEl, resetText);
    }

    function _addResearchButton(sectionEl, ticker, section, signals) {
        var btn = document.createElement('button');
        btn.textContent = 'Research This Model';
        btn.className = 'feynman-research-btn';
        btn.onclick = function () {
            _startResearch(btn, sectionEl, ticker, section, signals || null,
                '/api/feynman_research', 'Searching academic papers…', 'Research This Model');
        };
        sectionEl.appendChild(btn);
    }

    function _addSynthesisButton(cardEl, ticker) {
        var wrap = document.createElement('div');
        wrap.className = 'feynman-synthesis-wrap';
        var btn = document.createElement('button');
        btn.textContent = 'Synthesise Signals';
        btn.className = 'feynman-synthesis-btn';
        btn.onclick = function () {
            var sigs = _tickerSignals[ticker] || {};
            _startResearch(btn, wrap, ticker, null, sigs,
                '/api/feynman_synthesis', 'Synthesising signals…', 'Synthesise Signals');
        };
        wrap.appendChild(btn);
        cardEl.appendChild(wrap);
    }

    function _addPcaInterpretButton(sectionEl, pcaData) {
        var btn = document.createElement('button');
        btn.textContent = 'Interpret Portfolio Risk';
        btn.className = 'feynman-research-btn';
        btn.onclick = function () {
            _startResearch(btn, sectionEl, null, null, pcaData,
                '/api/feynman_pca_interpret', 'Interpreting risk…', 'Interpret Portfolio Risk');
        };
        sectionEl.appendChild(btn);
    }

    function _renderError(ticker, message) {
        var card = document.getElementById('ml-card-' + ticker);
        if (!card) return;
        card.innerHTML = '<p style="color:#e74c3c;">Error loading ML signals: ' + message + '</p>';
    }

    window.MLSignals = { fetchForTicker: fetchForTicker, clearSession: clearSession, fetchPCA: fetchPCA };
})();
