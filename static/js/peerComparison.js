/**
 * peerComparison.js — Phase 16
 * Fetches and renders the Peer Comparison sub-section inside the Deep Analysis group.
 *
 * Exposed API: window.PeerComparison = { renderIntoGroup, clearSession }
 *
 * /api/peers response shape:
 *   Success: { sector, peers, peer_data: [{ticker, pe, pb, roe, op_margin}],
 *              percentiles: {pe:{value,rank}, pb:{value,rank}, roe:{value,rank}, op_margin:{value,rank}} }
 *   Failure: { error: string }
 *   rank values are 0-100 integers; rank >= 50 => above median
 */
(function () {
    'use strict';

    // Tracks tickers already rendered (prevents double-render on re-search)
    var _sessionCache = {};

    // -------------------------------------------------------------------------
    // HTML builders
    // -------------------------------------------------------------------------

    function buildLoadingHTML() {
        return '<div class="deep-analysis-section" style="padding:6px 0;">' +
            '<div class="deep-analysis-header" style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;">' +
            '<span>Peer Comparison &nbsp;<span style="display:inline-block;animation:none;">&#8987;</span></span>' +
            '</div>' +
            '</div>';
    }

    function buildFailureHTML() {
        return '<div class="deep-analysis-section" style="padding:6px 0;opacity:0.55;">' +
            '<div class="deep-analysis-header" style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;">' +
            '<span>Peer Comparison: Unavailable</span>' +
            '</div>' +
            '</div>';
    }

    var METRIC_LABELS = {
        pe:         'P/E Ratio',
        pb:         'P/B Ratio',
        roe:        'ROE',
        op_margin:  'Op. Margin'
    };

    var METRIC_ORDER = ['pe', 'pb', 'roe', 'op_margin'];

    // Valuation multiples: higher rank = more expensive relative to peers = negative signal.
    // Quality metrics: higher rank = better performance = positive signal.
    var LOWER_IS_BETTER = { pe: true, pb: true };

    function _ordinalSuffix(n) {
        var s = ['th', 'st', 'nd', 'rd'];
        var v = n % 100;
        return n + (s[(v - 20) % 10] || s[v] || s[0]);
    }

    function buildSuccessHTML(ticker, resp) {
        var percentiles = resp.percentiles || {};
        var favourableCount = 0;

        // Count metrics with a favourable signal (cheap valuation or strong quality)
        METRIC_ORDER.forEach(function (key) {
            var p = percentiles[key];
            if (p && p.rank != null) {
                var isFavourable = LOWER_IS_BETTER[key] ? p.rank < 50 : p.rank >= 50;
                if (isFavourable) favourableCount++;
            }
        });

        var headerLabel = favourableCount + '/4 favourable';

        // Metric rows
        var rowsHTML = METRIC_ORDER.map(function (key) {
            var p = percentiles[key];
            var rankVal = (p && p.rank != null) ? p.rank : null;
            var rankText = rankVal !== null ? _ordinalSuffix(rankVal) + ' percentile' : '-- percentile';
            var badgeHTML = '';
            if (rankVal !== null) {
                var isFavourable = LOWER_IS_BETTER[key] ? rankVal < 50 : rankVal >= 50;
                if (isFavourable) {
                    badgeHTML = ' <span class="badge badge-success" style="font-size:10px;">FAVOURABLE</span>';
                } else {
                    badgeHTML = ' <span class="badge badge-danger" style="font-size:10px;">UNFAVOURABLE</span>';
                }
            }
            return '<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;font-size:13px;">' +
                '<span>' + METRIC_LABELS[key] + '</span>' +
                '<span>' + rankText + badgeHTML + '</span>' +
                '</div>';
        }).join('');

        // Peer group label
        var peers = resp.peers || [];
        var peerGroupHTML = '<div style="font-size:11px;color:#718096;margin-top:8px;">' +
            'Comparable group: ' + (peers.join(', ') || '—') +
            '</div>';

        // Show peers toggle button
        var toggleBtn = '<button class="peer-toggle-btn" style="margin-top:8px;font-size:11px;padding:2px 8px;cursor:pointer;">Show peers</button>';

        // Peer raw table
        var peerData = resp.peer_data || [];
        var tableRows = peerData.map(function (p) {
            return '<tr>' +
                '<td style="padding:3px 6px;">' + (p.ticker || '—') + '</td>' +
                '<td style="padding:3px 6px;text-align:right;">' + (p.pe != null ? p.pe : '—') + '</td>' +
                '<td style="padding:3px 6px;text-align:right;">' + (p.pb != null ? p.pb : '—') + '</td>' +
                '<td style="padding:3px 6px;text-align:right;">' + (p.roe != null ? p.roe : '—') + '</td>' +
                '<td style="padding:3px 6px;text-align:right;">' + (p.op_margin != null ? p.op_margin : '—') + '</td>' +
                '</tr>';
        }).join('');

        var rawTable = '<table class="peer-raw-table" style="display:none;width:100%;border-collapse:collapse;margin-top:8px;font-size:12px;">' +
            '<thead><tr>' +
            '<th style="text-align:left;padding:3px 6px;border-bottom:1px solid #e2e8f0;">Ticker</th>' +
            '<th style="text-align:right;padding:3px 6px;border-bottom:1px solid #e2e8f0;">P/E</th>' +
            '<th style="text-align:right;padding:3px 6px;border-bottom:1px solid #e2e8f0;">P/B</th>' +
            '<th style="text-align:right;padding:3px 6px;border-bottom:1px solid #e2e8f0;">ROE</th>' +
            '<th style="text-align:right;padding:3px 6px;border-bottom:1px solid #e2e8f0;">Op. Margin</th>' +
            '</tr></thead>' +
            '<tbody>' + tableRows + '</tbody>' +
            '</table>';

        var contentId = 'peer-content-' + ticker;

        return '<div class="deep-analysis-section" style="padding:6px 0;">' +
            '<div class="deep-analysis-header" style="display:flex;justify-content:space-between;align-items:center;cursor:pointer;padding:6px 0;" ' +
            'onclick="var c=document.getElementById(\'' + contentId + '\');' +
            'var arrow=this.querySelector(\'.peer-arrow\');' +
            'if(c.style.display===\'none\'){c.style.display=\'\';arrow.textContent=\'▲\';}' +
            'else{c.style.display=\'none\';arrow.textContent=\'▼\';}">' +
            '<span>Peer Comparison: ' + headerLabel + '</span>' +
            '<span class="peer-arrow">▼</span>' +
            '</div>' +
            '<div id="' + contentId + '" style="display:none;padding:4px 0 8px 0;">' +
            rowsHTML +
            peerGroupHTML +
            toggleBtn +
            rawTable +
            '</div>' +
            '</div>';
    }

    // -------------------------------------------------------------------------
    // Toggle wiring
    // -------------------------------------------------------------------------

    function _wireToggle(sectionEl) {
        var btn = sectionEl.querySelector('.peer-toggle-btn');
        var table = sectionEl.querySelector('.peer-raw-table');
        if (!btn || !table) return;
        btn.addEventListener('click', function () {
            if (table.style.display === 'none') {
                table.style.display = '';
                btn.textContent = 'Hide peers';
            } else {
                table.style.display = 'none';
                btn.textContent = 'Show peers';
            }
        });
    }

    // -------------------------------------------------------------------------
    // Fetch and render
    // -------------------------------------------------------------------------

    function _fetchAndRender(ticker, sectionEl) {
        fetch('/api/peers?ticker=' + encodeURIComponent(ticker))
            .then(function (r) { return r.json(); })
            .then(function (resp) {
                if (resp.error || !resp.peer_data || resp.peer_data.length < 2) {
                    sectionEl.innerHTML = buildFailureHTML();
                    return;
                }
                sectionEl.innerHTML = buildSuccessHTML(ticker, resp);
                _wireToggle(sectionEl);

                // Write to pageContext for downstream consumers
                if (window.pageContext &&
                    window.pageContext.tickerData &&
                    window.pageContext.tickerData[ticker]) {
                    window.pageContext.tickerData[ticker].peerComparison = {
                        sector:      resp.sector,
                        peers:       resp.peers,
                        percentiles: resp.percentiles
                    };
                }
            })
            .catch(function () {
                sectionEl.innerHTML = buildFailureHTML();
            });
    }

    // -------------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------------

    function renderIntoGroup(ticker, data, cardRoot) {
        // Guard against double-render
        if (_sessionCache[ticker]) return;
        _sessionCache[ticker] = true;

        var container = cardRoot.querySelector('#deep-analysis-content-' + ticker);
        if (!container) return;

        var section = document.createElement('div');
        section.innerHTML = buildLoadingHTML();
        container.appendChild(section);

        // Fire-and-forget: no await
        _fetchAndRender(ticker, section);
    }

    function clearSession() {
        Object.keys(_sessionCache).forEach(function (k) {
            delete _sessionCache[k];
        });
    }

    // -------------------------------------------------------------------------
    // Expose
    // -------------------------------------------------------------------------

    window.PeerComparison = { renderIntoGroup: renderIntoGroup, clearSession: clearSession };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.PeerComparison;
    }
}());
