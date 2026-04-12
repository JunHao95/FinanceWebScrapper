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

        // --- Anchored VWAP panel ---
        var avwapDivId   = 'avwapChart_' + ticker;
        var avwapBadgeId = 'avwapBadge_' + ticker;
        var avwapNoteId  = 'avwapNote_'  + ticker;

        var avwapChartEl = document.createElement('div');
        avwapChartEl.id = avwapDivId;
        avwapChartEl.style.cssText = 'width:100%;height:500px;margin-top:24px;';
        card.appendChild(avwapChartEl);

        var avwapBadgeEl = document.createElement('div');
        avwapBadgeEl.id = avwapBadgeId;
        avwapBadgeEl.className = 'ti-va-badge';
        card.appendChild(avwapBadgeEl);

        var avwapNoteEl = document.createElement('div');
        avwapNoteEl.id = avwapNoteId;
        avwapNoteEl.style.cssText = 'color:#7f849c;font-size:12px;margin:4px 0 8px 0;';
        card.appendChild(avwapNoteEl);

        var av = resp.anchored_vwap;
        if (av && av.traces && av.layout) {
            Plotly.newPlot(avwapDivId, av.traces, av.layout, { staticPlot: true, responsive: true });
        }

        if (av && av.convergence !== undefined) {
            var conv = av.convergence;
            if (conv.length > 0) {
                avwapBadgeEl.textContent = '\u26a0 Convergence: ' + conv.join(', ') + ' AVWAP within 0.3% of current price at $' + av.current_price.toFixed(2);
                avwapBadgeEl.style.color = '#e74c3c';
            } else {
                avwapBadgeEl.textContent = '\u2714 No AVWAP convergence';
                avwapBadgeEl.style.color = '#7f849c';
            }
            avwapBadgeEl.style.fontWeight = 'bold';
            avwapBadgeEl.style.fontSize   = '14px';
            avwapBadgeEl.style.display    = 'block';
        }

        if (av && av.earnings_unavailable === true) {
            avwapNoteEl.textContent = 'Earnings anchor unavailable \u2014 only 52-wk high & low lines shown.';
        }

        // AVWAP legend
        var avwapLegendEl = document.createElement('div');
        avwapLegendEl.className = 'ti-legend';
        avwapLegendEl.innerHTML =
            '<div class="ti-legend-title">How to read this chart</div>' +
            '<div class="ti-legend-grid">' +
              '<div class="ti-legend-item">' +
                '<span class="ti-swatch" style="background:#4c9be8;height:3px;"></span>' +
                '<div><strong>52-wk High AVWAP</strong> \u2014 VWAP anchored to the 52-week high date<br>' +
                '<span class="ti-legend-desc">Price trading below this line means sellers who bought near the yearly peak are still underwater on average. A reclaim signals bullish recovery.</span></div>' +
              '</div>' +
              '<div class="ti-legend-item">' +
                '<span class="ti-swatch" style="background:#fe8019;height:3px;"></span>' +
                '<div><strong>52-wk Low AVWAP</strong> \u2014 VWAP anchored to the 52-week low date<br>' +
                '<span class="ti-legend-desc">Price above this line means buyers who stepped in at the yearly low are in profit on average. Losing this level signals deteriorating demand.</span></div>' +
              '</div>' +
              '<div class="ti-legend-item">' +
                '<span class="ti-swatch" style="background:#cba6f7;height:3px;"></span>' +
                '<div><strong>Earnings AVWAP</strong> \u2014 VWAP anchored to the most recent earnings date<br>' +
                '<span class="ti-legend-desc">Tracks the average cost basis of traders who positioned around the last earnings event. Acts as a key support/resistance since the report.</span></div>' +
              '</div>' +
              '<div class="ti-legend-item">' +
                '<span class="ti-swatch" style="background:rgba(205,214,244,0.35);border-top:1px dashed rgba(205,214,244,0.5);height:0;"></span>' +
                '<div><strong>Current Price</strong> \u2014 dashed reference line<br>' +
                '<span class="ti-legend-desc">Shows where price sits relative to all three AVWAP anchors at a glance.</span></div>' +
              '</div>' +
            '</div>' +
            '<div class="ti-signal-guide">' +
              '<strong>Right-edge labels</strong> show the signed % distance between current price and each AVWAP line \u2014 positive means price is above that anchor\'s average cost basis, negative means below. ' +
              '&nbsp;|&nbsp; ' +
              '<strong>Convergence</strong>: when price comes within 0.3% of any AVWAP line, that line acts as a high-probability inflection point \u2014 watch for a bounce or breakdown.' +
            '</div>';
        card.appendChild(avwapLegendEl);
    }

    window.TradingIndicators = { fetchForTicker: fetchForTicker, clearSession: clearSession };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.TradingIndicators;
    }
}());
