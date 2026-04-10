(function () {
    'use strict';

    // Per-ticker session cache keyed by ticker + '-' + lookback
    var _sessionCache = {};

    function clearSession() {
        Object.keys(_sessionCache).forEach(function (k) { delete _sessionCache[k]; });
    }

    function fetchForTicker(ticker, lookback) {
        var cacheKey = ticker + '-' + lookback;
        if (_sessionCache[cacheKey]) return;
        _sessionCache[cacheKey] = true;

        var container = document.getElementById('tradingIndicatorsTabContent');
        if (!container) return;

        fetch('/api/trading_indicators?ticker=' + encodeURIComponent(ticker) +
              '&lookback=' + encodeURIComponent(lookback))
            .then(function (r) { return r.json(); })
            .then(function (resp) {
                if (resp.error) {
                    console.warn('[TradingIndicators] API error:', resp.error);
                    return;
                }
                _renderTickerCard(container, ticker, lookback, resp);
            })
            .catch(function (err) {
                console.error('[TradingIndicators] fetch failed:', err);
            });
    }

    function _renderTickerCard(container, ticker, lookback, resp) {
        var cardId  = 'tiCard_' + ticker;
        var vpDivId = 'vpChart_' + ticker;
        var badgeId = 'vpBadge_' + ticker;

        var existing = document.getElementById(cardId);
        if (existing) existing.parentNode.removeChild(existing);

        var card = document.createElement('div');
        card.id = cardId;
        card.className = 'ti-ticker-card';
        card.innerHTML =
            '<h3 class="ti-ticker-title">' + ticker + '</h3>' +
            '<div id="' + vpDivId + '" style="width:100%;height:420px;"></div>' +
            '<div id="' + badgeId + '" class="ti-va-badge"></div>';
        container.appendChild(card);

        var vp = resp.volume_profile;
        if (vp && vp.traces && vp.layout) {
            Plotly.newPlot(vpDivId, vp.traces, vp.layout, { staticPlot: true });
            var badgeEl = document.getElementById(badgeId);
            if (badgeEl) {
                var inside = vp.signal === 'inside';
                badgeEl.textContent = inside
                    ? 'Price inside value area'
                    : 'Price outside value area';
                badgeEl.style.color      = inside ? '#2ecc71' : '#e74c3c';
                badgeEl.style.fontWeight = 'bold';
                badgeEl.style.margin     = '8px 0 16px 0';
                badgeEl.style.display    = 'block';
            }
        }
    }

    window.TradingIndicators = { fetchForTicker: fetchForTicker, clearSession: clearSession };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.TradingIndicators;
    }
}());
