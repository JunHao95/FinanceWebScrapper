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
        var cardId = 'tiCard_' + ticker;

        var existing = document.getElementById(cardId);
        if (existing) existing.parentNode.removeChild(existing);

        var placeholder = document.getElementById('tiLoading_' + ticker);
        if (placeholder) placeholder.parentNode.removeChild(placeholder);

        // --- VP legend ---
        var vpLegendHtml =
            '<div class="ti-legend">' +
              '<div class="ti-legend-title">How to read this chart</div>' +
              '<div class="ti-legend-grid">' +
                '<div class="ti-legend-item">' +
                  '<span class="ti-swatch" style="background:#ff6b35;height:3px;"></span>' +
                  '<div><strong>POC</strong> \u2014 Point of Control<br>' +
                  '<span class="ti-legend-desc">Price level with the highest traded volume. Strong support/resistance.</span></div>' +
                '</div>' +
                '<div class="ti-legend-item">' +
                  '<span class="ti-swatch" style="background:#2ecc71;border-top:2px dashed #2ecc71;height:0;"></span>' +
                  '<div><strong>VAH</strong> \u2014 Value Area High<br>' +
                  '<span class="ti-legend-desc">Upper edge of the 70% value area. Acts as resistance when price is below.</span></div>' +
                '</div>' +
                '<div class="ti-legend-item">' +
                  '<span class="ti-swatch" style="background:#e74c3c;border-top:2px dashed #e74c3c;height:0;"></span>' +
                  '<div><strong>VAL</strong> \u2014 Value Area Low<br>' +
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
                '<span style="color:#2ecc71">Inside value area</span> \u2014 price is in a high-acceptance zone, trend continuation likely. &nbsp;|&nbsp; ' +
                '<span style="color:#e74c3c">Outside value area</span> \u2014 price is extended, watch for rejection or breakout confirmation.' +
              '</div>' +
            '</div>';

        // --- Build card shell with composite badge + 2x2 grid ---
        var card = document.createElement('div');
        card.id = cardId;
        card.className = 'ti-ticker-card';
        card.innerHTML =
            '<h3 class="ti-ticker-title">' + ticker + '</h3>' +
            '<span class="ti-composite-badge" id="cBadge_' + ticker + '"></span>' +
            '<span class="ti-composite-caveat">Trend-following bias \u2014 all indicators share the same OHLCV data source.</span>' +
            '<div class="ti-2x2-grid">' +
              '<div class="ti-grid-cell" id="tiCell_vp_' + ticker + '">' +
                '<div id="vpChart_' + ticker + '" style="width:100%;height:500px;"></div>' +
                '<div id="vpBadge_' + ticker + '" class="ti-va-badge"></div>' +
                vpLegendHtml +
              '</div>' +
              '<div class="ti-grid-cell" id="tiCell_avwap_' + ticker + '">' +
                '<div id="avwapChart_' + ticker + '" style="width:100%;height:500px;"></div>' +
                '<div id="avwapBadge_' + ticker + '" class="ti-va-badge"></div>' +
                '<div id="avwapNote_' + ticker + '" style="color:#7f849c;font-size:12px;margin:4px 0 8px 0;"></div>' +
              '</div>' +
              '<div class="ti-grid-cell" id="tiCell_of_' + ticker + '">' +
                '<div id="ofChart_' + ticker + '" style="width:100%;height:500px;"></div>' +
                '<div id="ofBadge_' + ticker + '" class="ti-va-badge"></div>' +
              '</div>' +
              '<div class="ti-grid-cell" id="tiCell_sweep_' + ticker + '">' +
                '<div id="sweepChart_' + ticker + '" style="width:100%;height:500px;"></div>' +
                '<div id="sweepBadge_' + ticker + '" class="ti-va-badge"></div>' +
              '</div>' +
            '</div>';
        container.appendChild(card);

        // --- Volume Profile panel ---
        var vp = resp.volume_profile;
        if (vp && vp.traces && vp.layout) {
            Plotly.newPlot('vpChart_' + ticker, vp.traces, vp.layout, { responsive: true, displayModeBar: true, scrollZoom: true });
            var vpBadgeEl = document.getElementById('vpBadge_' + ticker);
            if (vpBadgeEl) {
                var inside = vp.signal === 'inside';
                vpBadgeEl.textContent = inside
                    ? '\u2714 Price inside value area'
                    : '\u26a0 Price outside value area';
                vpBadgeEl.style.color      = inside ? '#2ecc71' : '#e74c3c';
                vpBadgeEl.style.fontWeight = 'bold';
                vpBadgeEl.style.fontSize   = '14px';
                vpBadgeEl.style.margin     = '8px 0 4px 0';
                vpBadgeEl.style.display    = 'block';
            }
        } else {
            var vpEl = document.getElementById('vpChart_' + ticker);
            if (vpEl) {
                vpEl.className = 'ti-unavailable-placeholder';
                vpEl.textContent = 'Volume Profile unavailable';
            }
        }

        // --- Anchored VWAP panel ---
        var av = resp.anchored_vwap;
        if (av && av.traces && av.layout) {
            Plotly.newPlot('avwapChart_' + ticker, av.traces, av.layout, { responsive: true, displayModeBar: true, scrollZoom: true });
        } else {
            var avEl = document.getElementById('avwapChart_' + ticker);
            if (avEl) {
                avEl.className = 'ti-unavailable-placeholder';
                avEl.textContent = 'Anchored VWAP unavailable';
            }
        }
        var avwapBadgeEl = document.getElementById('avwapBadge_' + ticker);
        if (av && av.convergence !== undefined && avwapBadgeEl) {
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
        var avwapNoteEl = document.getElementById('avwapNote_' + ticker);
        if (av && av.earnings_unavailable === true && avwapNoteEl) {
            avwapNoteEl.textContent = 'Earnings anchor unavailable \u2014 only 52-wk high & low lines shown.';
        }

        // AVWAP legend (appended to grid cell)
        var avwapCell = document.getElementById('tiCell_avwap_' + ticker);
        if (avwapCell) {
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
            avwapCell.appendChild(avwapLegendEl);
        }

        // --- Order Flow panel ---
        var of = resp.order_flow;
        if (of && of.traces && of.layout) {
            Plotly.newPlot('ofChart_' + ticker, of.traces, of.layout, { responsive: true, displayModeBar: true, scrollZoom: true });
        } else {
            var ofEl = document.getElementById('ofChart_' + ticker);
            if (ofEl) {
                ofEl.className = 'ti-unavailable-placeholder';
                ofEl.textContent = 'Order Flow unavailable';
            }
        }
        var ofBadgeEl = document.getElementById('ofBadge_' + ticker);
        if (of && of.divergence !== undefined && ofBadgeEl) {
            var hasDivergence = of.divergence.detected;
            ofBadgeEl.textContent = hasDivergence
                ? '\u26a0 Volume Divergence \u2014 price slope: ' + of.divergence.price_slope.toFixed(4)
                  + ', vol slope: ' + of.divergence.vol_slope.toFixed(4)
                : '\u2714 No divergence';
            ofBadgeEl.style.color      = hasDivergence ? '#e74c3c' : '#7f849c';
            ofBadgeEl.style.fontWeight = 'bold';
            ofBadgeEl.style.fontSize   = '14px';
            ofBadgeEl.style.display    = 'block';
        }

        var ofCell = document.getElementById('tiCell_of_' + ticker);
        if (ofCell) {
            var ofLegendEl = document.createElement('div');
            ofLegendEl.className = 'ti-legend';
            ofLegendEl.innerHTML =
                '<div class="ti-legend-title">How to read this chart</div>' +
                '<div class="ti-legend-grid">' +
                  '<div class="ti-legend-item">' +
                    '<span class="ti-swatch" style="background:#2ecc71;height:12px;width:12px;border-radius:2px;"></span>' +
                    '<div><strong>Green bars</strong> \u2014 Buy pressure (close nearer to high)<br>' +
                    '<span class="ti-legend-desc">Computed as (Close\u2212Low)/(High\u2212Low)\u00d7Volume. Taller green bars mean more aggressive buying that session.</span></div>' +
                  '</div>' +
                  '<div class="ti-legend-item">' +
                    '<span class="ti-swatch" style="background:#e74c3c;height:12px;width:12px;border-radius:2px;"></span>' +
                    '<div><strong>Red bars</strong> \u2014 Sell pressure (close nearer to low)<br>' +
                    '<span class="ti-legend-desc">Negative delta values. Persistent red bars signal supply overpowering demand.</span></div>' +
                  '</div>' +
                  '<div class="ti-legend-item">' +
                    '<span class="ti-swatch" style="background:#cdd6f4;height:3px;"></span>' +
                    '<div><strong>White line</strong> \u2014 Cumulative delta (right axis)<br>' +
                    '<span class="ti-legend-desc">Running sum of all delta bars. A rising line means buyers are accumulating; a falling line signals sustained selling pressure.</span></div>' +
                  '</div>' +
                  '<div class="ti-legend-item">' +
                    '<span style="font-size:14px;color:#2ecc71;margin-right:6px;">\u25b2</span>' +
                    '<span style="font-size:14px;color:#e74c3c;margin-right:10px;">\u25bc</span>' +
                    '<div><strong>Imbalance candles</strong> \u2014 body &gt;70% of range AND volume &gt;1.2\u00d7 20-day avg<br>' +
                    '<span class="ti-legend-desc">High-conviction directional bars. \u25b2 (bullish) appears above the bar; \u25bc (bearish) below. These often mark short-term exhaustion or continuation points.</span></div>' +
                  '</div>' +
                '</div>' +
                '<div class="ti-signal-guide">' +
                  '<strong>Volume Divergence</strong>: fires when price slope and volume slope have opposite signs over the last 10 bars \u2014 ' +
                  'price rising on falling volume signals weakening momentum; price falling on rising volume signals distribution.' +
                '</div>';
            ofCell.appendChild(ofLegendEl);
        }

        // --- Liquidity Sweep panel ---
        var sw = resp.liquidity_sweep;
        if (sw && sw.traces && sw.layout) {
            Plotly.newPlot('sweepChart_' + ticker, sw.traces, sw.layout, { responsive: true, displayModeBar: true, scrollZoom: true });
        } else {
            var sweepEl = document.getElementById('sweepChart_' + ticker);
            if (sweepEl) {
                sweepEl.className = 'ti-unavailable-placeholder';
                sweepEl.textContent = 'Liquidity Sweep unavailable';
            }
        }
        var sweepBadgeEl = document.getElementById('sweepBadge_' + ticker);
        if (sw && sweepBadgeEl) {
            var sig = sw.signal;
            if (sig === 'bullish') {
                sweepBadgeEl.textContent = '\u2714 Bullish Sweep \u2014 last confirmed sweep at $' + (sw.swept_price ? sw.swept_price.toFixed(2) : '?');
                sweepBadgeEl.style.color = '#2ecc71';
            } else if (sig === 'bearish') {
                sweepBadgeEl.textContent = '\u26a0 Bearish Sweep \u2014 last confirmed sweep at $' + (sw.swept_price ? sw.swept_price.toFixed(2) : '?');
                sweepBadgeEl.style.color = '#e74c3c';
            } else if (sig === 'no_swings') {
                sweepBadgeEl.textContent = '\u2014 No confirmed swings in selected window (n=' + (sw.n || '?') + ')';
                sweepBadgeEl.style.color = '#7f849c';
            } else {
                sweepBadgeEl.textContent = '\u2014 No Sweep in selected window (n=' + (sw.n || '?') + ')';
                sweepBadgeEl.style.color = '#7f849c';
            }
            sweepBadgeEl.style.fontWeight = 'bold';
            sweepBadgeEl.style.fontSize   = '14px';
            sweepBadgeEl.style.display    = 'block';
        }

        var sweepCell = document.getElementById('tiCell_sweep_' + ticker);
        if (sweepCell) {
            var sweepLegendEl = document.createElement('div');
            sweepLegendEl.className = 'ti-legend';
            sweepLegendEl.innerHTML =
                '<div class="ti-legend-title">How to read this chart</div>' +
                '<div class="ti-legend-grid">' +
                  '<div class="ti-legend-item">' +
                    '<span style="font-size:14px;color:#2ecc71;margin-right:6px;">\u25b2</span>' +
                    '<div><strong>Bullish Sweep (\u25b2)</strong> \u2014 price closed above a confirmed swing high<br>' +
                    '<span class="ti-legend-desc">Liquidity above the prior high was taken. Bullish momentum signal.</span></div>' +
                  '</div>' +
                  '<div class="ti-legend-item">' +
                    '<span style="font-size:14px;color:#e74c3c;margin-right:6px;">\u25bc</span>' +
                    '<div><strong>Bearish Sweep (\u25bc)</strong> \u2014 price closed below a confirmed swing low<br>' +
                    '<span class="ti-legend-desc">Stop-loss liquidity below the prior low was triggered. Bearish pressure signal.</span></div>' +
                  '</div>' +
                  '<div class="ti-legend-item">' +
                    '<span class="ti-swatch" style="background:none;border-top:2px dashed #7f849c;height:0;width:24px;margin-right:6px;"></span>' +
                    '<div><strong>Dashed line</strong> \u2014 swept price level<br>' +
                    '<span class="ti-legend-desc">Horizontal line at the price that was swept. Can act as support or resistance after the event.</span></div>' +
                  '</div>' +
                '</div>';
            sweepCell.appendChild(sweepLegendEl);
        }

        // --- Composite bias badge ---
        var cb = resp.composite_bias;
        var badgeEl = document.getElementById('cBadge_' + ticker);
        if (cb && badgeEl) {
            var dotColor = cb.direction === 'bullish' ? '#2ecc71'
                         : cb.direction === 'bearish' ? '#e74c3c' : '#7f849c';
            var dissenterText = cb.dissenters && cb.dissenters.length > 0
                ? ' \u2014 ' + cb.dissenters.join(', ') + ' dissent' + (cb.dissenters.length > 1 ? '' : 's')
                : (cb.unavailable && cb.unavailable.length > 0 ? ' \u2014 ' + cb.unavailable.join(', ') + ' unavailable' : '');
            badgeEl.textContent = '\u25cf '
                + (cb.direction.charAt(0).toUpperCase() + cb.direction.slice(1))
                + ' (' + (cb.score || '0/0') + ')' + dissenterText;
            badgeEl.style.color = dotColor;
        }
    }

    function _initLookbackDropdown(tickers) {
        var bar = document.getElementById('tiLookbackBar');
        if (bar) bar.style.display = 'flex';
        var sel = document.getElementById('tiLookbackSelect');
        if (!sel) return;
        var newSel = sel.cloneNode(true);
        sel.parentNode.replaceChild(newSel, sel);
        newSel.addEventListener('change', function () {
            var newLookback = parseInt(newSel.value, 10);
            clearSession();
            var container = document.getElementById('tradingIndicatorsTabContent');
            if (!container) return;
            tickers.forEach(function (t) {
                var card = document.getElementById('tiCard_' + t);
                if (card) card.parentNode.removeChild(card);
                var ph = document.createElement('div');
                ph.id = 'tiLoading_' + t;
                ph.className = 'ti-unavailable-placeholder';
                ph.style.height = '120px';
                ph.textContent = 'Loading ' + t + '\u2026';
                container.appendChild(ph);
            });
            tickers.forEach(function (t) { fetchForTicker(t, newLookback); });
        });
    }

    window.TradingIndicators = {
        fetchForTicker:       fetchForTicker,
        clearSession:         clearSession,
        initLookbackDropdown: _initLookbackDropdown,
    };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.TradingIndicators;
    }
}());
