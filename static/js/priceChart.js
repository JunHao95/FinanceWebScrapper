(function () {
    'use strict';
    var _cache = {};      // key: ticker+'-'+period → {traces, layout}
    var _tickerData = {}; // key: ticker → scrape data object (for analyst bar)

    function clearSession() {
        Object.keys(_cache).forEach(function (k) { delete _cache[k]; });
    }

    // Called from createTickerCard (div may not be in DOM yet) — store data only
    function storeData(ticker, data) {
        _tickerData[ticker] = data;
    }

    function fetchIfNeeded(ticker, period) {
        period = period || '3mo';
        var key = ticker + '-' + period;
        if (_cache[key]) {
            _render(ticker, period);
            return;
        }
        var url = '/api/price_history?ticker=' + encodeURIComponent(ticker)
                + '&period=' + encodeURIComponent(period);
        fetch(url)
            .then(function (r) { return r.json(); })
            .then(function (resp) {
                if (resp.error) {
                    _showError(ticker, resp.error);
                    return;
                }
                _cache[key] = { traces: resp.traces, layout: resp.layout };
                _render(ticker, period);
            })
            .catch(function (err) {
                _showError(ticker, 'Failed to load price chart');
                console.error('[PriceChart]', err);
            });
    }

    function switchPeriod(ticker, period) {
        var nav = document.getElementById('priceChart-' + ticker + '-nav');
        if (nav) {
            nav.querySelectorAll('.pc-period-btn').forEach(function (b) {
                b.classList.toggle('active', b.dataset.period === period);
            });
        }
        fetchIfNeeded(ticker, period);
    }

    function _render(ticker, period) {
        var key = ticker + '-' + period;
        var cached = _cache[key];
        if (!cached) return;
        var chartId = 'priceChart-' + ticker;
        var el = document.getElementById(chartId);
        // Skip if container not in DOM or hidden (non-active sub-tab / collapsed card)
        if (!el || el.offsetParent === null) return;
        // Render analyst bar once data is available and pane is visible
        _renderAnalystBar(ticker);
        // Defer Plotly call so browser paints display:block before measuring
        setTimeout(function () {
            var elNow = document.getElementById(chartId);
            if (!elNow || elNow.offsetParent === null) return;
            Plotly.newPlot(chartId, cached.traces, cached.layout,
                { responsive: true, displayModeBar: false, staticPlot: false });
        }, 0);
    }

    function _showError(ticker, msg) {
        var el = document.getElementById('priceChart-' + ticker);
        if (el) el.innerHTML = '<div class="pc-error">' + msg + '</div>';
    }

    function _renderAnalystBar(ticker) {
        var container = document.getElementById('analystRangeBar-' + ticker);
        var data = _tickerData[ticker];
        if (!container || !data) return;
        // Idempotent: skip if already rendered
        if (container.dataset.rendered === '1') return;
        var low  = parseFloat(data['Analyst Price Target Low (Yahoo)'])
                || parseFloat(data['Analyst Price Target Low (Finhub)']) || null;
        var mean = parseFloat(data['Analyst Price Target Mean (Yahoo)'])
                || parseFloat(data['Analyst Price Target Mean (Finhub)']) || null;
        var high = parseFloat(data['Analyst Price Target High (Yahoo)'])
                || parseFloat(data['Analyst Price Target High (Finhub)']) || null;
        var current = parseFloat(data['Current Price']) || null;
        if (!low || !mean || !high || low >= high) { container.style.display = 'none'; return; }
        var recRaw = data['Analyst Recommendation (Yahoo)'] || '';
        var recMap = {
            strong_buy:  { label: 'Strong Buy',  cls: 'rec-buy' },
            buy:         { label: 'Buy',          cls: 'rec-buy' },
            hold:        { label: 'Hold',         cls: 'rec-hold' },
            sell:        { label: 'Sell',         cls: 'rec-sell' },
            strong_sell: { label: 'Strong Sell',  cls: 'rec-sell' }
        };
        var rec = recMap[recRaw.toLowerCase()] || null;
        var recHtml = rec
            ? '<span class="analyst-badge ' + rec.cls + '">' + rec.label + '</span>'
            : '';
        var dotPct = current
            ? Math.min(100, Math.max(0, (current - low) / (high - low) * 100))
            : null;
        var dotCls = (current && mean) ? (current < mean ? 'dot-upside' : 'dot-overvalued') : '';
        var meanPct = (mean - low) / (high - low) * 100;
        container.innerHTML =
            '<div class="analyst-bar-header">' +
              '<span class="analyst-bar-title">Analyst Price Target</span>' + recHtml +
            '</div>' +
            '<div class="analyst-bar-wrap">' +
              '<span class="analyst-bar-label">' + low.toFixed(2) + '</span>' +
              '<div class="analyst-bar-track">' +
                '<div class="analyst-bar-mean" style="left:' + meanPct.toFixed(1) + '%"></div>' +
                (dotPct !== null
                    ? '<div class="analyst-bar-dot ' + dotCls + '" style="left:' + dotPct.toFixed(1) + '%"></div>'
                    : '') +
              '</div>' +
              '<span class="analyst-bar-label">' + high.toFixed(2) + '</span>' +
            '</div>' +
            (current
                ? '<div class="analyst-bar-caption">Current: $' + current.toFixed(2) +
                  ' | Target Mean: $' + mean.toFixed(2) + '</div>'
                : '');
        container.dataset.rendered = '1';
    }

    window.PriceChart = {
        fetchIfNeeded: fetchIfNeeded,
        switchPeriod:  switchPeriod,
        clearSession:  clearSession,
        storeData:     storeData
    };
}());
