(function () {
    'use strict';
    var _cache = {};  // key: ticker+'-'+period → {traces, layout}

    function clearSession() {
        Object.keys(_cache).forEach(function (k) { delete _cache[k]; });
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
        // Skip if container is hidden (non-active sub-tab); switchSubTab will retry
        if (!el || el.offsetParent === null) return;
        Plotly.newPlot(chartId, cached.traces, cached.layout,
            { responsive: true, displayModeBar: false, staticPlot: false });
    }

    function _showError(ticker, msg) {
        var el = document.getElementById('priceChart-' + ticker);
        if (el) el.innerHTML = '<div class="pc-error">' + msg + '</div>';
    }

    function _injectPeriodNav(ticker) {
        var chartEl = document.getElementById('priceChart-' + ticker);
        if (!chartEl || document.getElementById('priceChart-' + ticker + '-nav')) return;
        var nav = document.createElement('div');
        nav.id = 'priceChart-' + ticker + '-nav';
        nav.className = 'pc-period-nav';
        ['1mo', '3mo', '6mo', '1y'].forEach(function (p, i) {
            var btn = document.createElement('button');
            btn.className = 'pc-period-btn' + (i === 1 ? ' active' : '');
            btn.dataset.period = p;
            btn.textContent = p === '1mo' ? '1M' : p === '3mo' ? '3M' : p === '6mo' ? '6M' : '1Y';
            btn.onclick = function () { PriceChart.switchPeriod(ticker, p); };
            nav.appendChild(btn);
        });
        chartEl.parentNode.insertBefore(nav, chartEl);
    }

    function _renderAnalystBar(ticker, data) {
        var container = document.getElementById('analystRangeBar-' + ticker);
        if (!container || !data) return;
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
            strong_buy: { label: 'Strong Buy', cls: 'rec-buy' },
            buy:        { label: 'Buy',         cls: 'rec-buy' },
            hold:       { label: 'Hold',        cls: 'rec-hold' },
            sell:       { label: 'Sell',        cls: 'rec-sell' },
            strong_sell:{ label: 'Strong Sell', cls: 'rec-sell' }
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
    }

    // Called by displayManager.js createTickerCard after div.innerHTML is set
    function initCard(ticker, data) {
        _injectPeriodNav(ticker);
        _renderAnalystBar(ticker, data);
        fetchIfNeeded(ticker, '3mo');
    }

    window.PriceChart = {
        fetchIfNeeded: fetchIfNeeded,
        switchPeriod:  switchPeriod,
        clearSession:  clearSession,
        initCard:      initCard
    };
}());
