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

        var legendHtml =
            '<div class="ti-legend">' +
              '<div class="ti-legend-title">How to read this chart</div>' +
              '<div class="ti-legend-grid">' +
                '<div class="ti-legend-item">' +
                  '<span class="ti-swatch" style="background:#ff6b35;height:3px;"></span>' +
                  '<div><strong>POC</strong> — Point of Control<br>' +
                  '<span class="ti-legend-desc">Price level with the highest traded volume. Strong support/resistance.</span></div>' +
                '</div>' +
                '<div class="ti-legend-item">' +
                  '<span class="ti-swatch" style="background:#2ecc71;border-top:2px dashed #2ecc71;height:0;"></span>' +
                  '<div><strong>VAH</strong> — Value Area High<br>' +
                  '<span class="ti-legend-desc">Upper edge of the 70% value area. Acts as resistance when price is below.</span></div>' +
                '</div>' +
                '<div class="ti-legend-item">' +
                  '<span class="ti-swatch" style="background:#e74c3c;border-top:2px dashed #e74c3c;height:0;"></span>' +
                  '<div><strong>VAL</strong> — Value Area Low<br>' +
                  '<span class="ti-legend-desc">Lower edge of the 70% value area. Acts as support when price is above.</span></div>' +
                '</div>' +
                '<div class="ti-legend-item">' +
                  '<span class="ti-swatch" style="background:rgba(70,130,180,0.35);border:1px solid rgba(70,130,180,0.6);"></span>' +
                  '<div><strong>Value Area (70%)</strong><br>' +
                  '<span class="ti-legend-desc">Zone where 70% of volume traded. Price inside = fair value; outside = potential mean-reversion opportunity.</span></div>' +
                '</div>' +
              '</div>' +
              '<div class="ti-signal-guide">' +
                '<strong>Signal:</strong> ' +
                '<span style="color:#2ecc71">Inside value area</span> — price is in a high-acceptance zone, trend continuation likely. &nbsp;|&nbsp; ' +
                '<span style="color:#e74c3c">Outside value area</span> — price is extended, watch for rejection or breakout confirmation.' +
              '</div>' +
            '</div>';

        var card = document.createElement('div');
        card.id = cardId;
        card.className = 'ti-ticker-card';
        card.innerHTML =
            '<h3 class="ti-ticker-title">' + ticker + '</h3>' +
            '<div id="' + vpDivId + '" style="width:100%;height:500px;"></div>' +
            '<div id="' + badgeId + '" class="ti-va-badge"></div>' +
            legendHtml;
        container.appendChild(card);

        var vp = resp.volume_profile;
        if (vp && vp.traces && vp.layout) {
            Plotly.newPlot(vpDivId, vp.traces, vp.layout, {
                responsive: true,
                displayModeBar: true,
                scrollZoom: true,
            });
            var badgeEl = document.getElementById(badgeId);
            if (badgeEl) {
                var inside = vp.signal === 'inside';
                badgeEl.textContent = inside
                    ? '\u2714 Price inside value area'
                    : '\u26a0 Price outside value area';
                badgeEl.style.color      = inside ? '#2ecc71' : '#e74c3c';
                badgeEl.style.fontWeight = 'bold';
                badgeEl.style.fontSize   = '14px';
                badgeEl.style.margin     = '8px 0 4px 0';
                badgeEl.style.display    = 'block';
            }
        }
    }

    window.TradingIndicators = { fetchForTicker: fetchForTicker, clearSession: clearSession };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.TradingIndicators;
    }
}());
