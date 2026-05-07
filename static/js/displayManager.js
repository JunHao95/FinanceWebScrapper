// ===========================
// Display Manager Module
// Handles rendering of results and analytics
// ===========================

// ---------------------------------------------------------------------------
// SectionCollapse — per-section collapse toggles backed by sessionStorage
// Keys: collapse-{ticker}-{sectionName}
// Section name tokens: healthCard, deepAnalysis, regimeDetection, tradingIndicators
// ---------------------------------------------------------------------------
const SectionCollapse = {
    KEY_PREFIX: 'collapse-',

    getKey(ticker, section) {
        return `${this.KEY_PREFIX}${ticker}-${section}`;
    },

    isCollapsed(ticker, section) {
        return sessionStorage.getItem(this.getKey(ticker, section)) === '1';
    },

    setCollapsed(ticker, section, collapsed) {
        if (collapsed) {
            sessionStorage.setItem(this.getKey(ticker, section), '1');
        } else {
            sessionStorage.removeItem(this.getKey(ticker, section));
        }
    },

    toggle(bodyEl, chevronEl, ticker, section) {
        if (!bodyEl) return;
        const nowCollapsed = !bodyEl.classList.contains('collapsed');
        bodyEl.classList.toggle('collapsed', nowCollapsed);
        if (chevronEl) {
            chevronEl.style.transform = nowCollapsed ? 'rotate(-90deg)' : '';
        }
        this.setCollapsed(ticker, section, nowCollapsed);
    },

    applyInitialState(bodyEl, chevronEl, ticker, section) {
        const collapsed = this.isCollapsed(ticker, section);
        bodyEl.classList.toggle('collapsed', collapsed);
        if (chevronEl) {
            chevronEl.style.transform = collapsed ? 'rotate(-90deg)' : '';
        }
    }
};

const DisplayManager = {
    /**
     * Escape HTML to prevent XSS attacks
     */
    escapeHtml(text) {
        if (text === null || text === undefined) {
            return '';
        }
        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML;
    },

    /**
     * Display CNN Fear & Greed metrics
     */
    displayCnnMetrics(cnnData) {
        const cnnDiv = document.getElementById('cnnMetrics');
        if (!cnnDiv) {
            console.error('Required DOM element not found: cnnMetrics');
            return;
        }
        
        if (!cnnData || typeof cnnData !== 'object') {
            console.error('Invalid cnnData provided');
            return;
        }
        
        let html = '<div class="cnn-metrics">';
        html += '<h3>📊 CNN Fear & Greed Index</h3>';
        
        for (const [metric, values] of Object.entries(cnnData)) {
            const displayName = this.escapeHtml(metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()));
            const score = this.escapeHtml(values.score || '--');
            const rating = this.escapeHtml(values.rating || '--');
            
            html += '<div class="metric-card">';
            html += `<strong>${displayName}:</strong> `;
            html += `Score: ${score} | `;
            html += `Rating: ${rating}`;
            html += '</div>';
        }
        
        html += '</div>';
        cnnDiv.innerHTML = html;
    },

    /**
     * Create ticker card with five sub-tab layout (Phase 28)
     */
    createTickerCard(ticker, data) {
        if (!ticker || !data || typeof data !== 'object') {
            console.error('Invalid ticker or data provided to createTickerCard');
            return null;
        }

        if (typeof Utils === 'undefined' || typeof Utils.formatValue !== 'function') {
            console.error('Required dependency not found: Utils.formatValue');
            return null;
        }

        const div = document.createElement('div');
        div.className = 'ticker-results';

        const groups = {
            'Basic Info': ['Current Price', 'Market Cap', 'Company Name', 'Sector', 'Industry', 'Exchange', 'Website', 'Description'],
            'Valuation': ['P/E Ratio', 'Forward P/E', 'P/B Ratio', 'P/S Ratio', 'PEG Ratio', 'EV/EBITDA'],
            'Profitability': ['ROE', 'ROA', 'ROIC', 'Profit Margin', 'Operating Margin'],
            'Earnings': ['EPS', 'EPS Growth', 'Earnings Growth'],
            'Financial Metrics': ['Gross Profit', 'Total Debt', 'EBITDA'],
            'Cash/CashFlow': ['Cash', 'Cash Per Share', 'Operating Cash Flow', 'Capital Expenditure', 'Free Cash Flow', 'Cash & Equivalents', 'Cash & ST Investments'],
            'Technical': ['RSI', 'MA10', 'MA20', 'MA50', 'BB Signal'],
            'Sentiment Analysis': [
                'Overall Sentiment Score', 'Overall Sentiment Label', 'Sentiment Confidence', 'Active Data Sources',
                'Google Trends Interest', 'Trends Direction', 'Avg Interest',
                'News Articles Analyzed', 'News Sentiment Score', 'Positive News Articles', 'Negative News Articles', 'FinBERT News Score',
                'Reddit Posts Analyzed', 'Reddit Sentiment Score', 'Reddit Avg Score', 'Reddit Avg Comments', 'Positive Reddit Posts',
                'Top Topic 1 Keywords', 'Top Topic 2 Keywords', 'Top Topic 3 Keywords', 'Document Similarity'
            ]
        };

        const tabGroupNames = {
            overview: ['Basic Info'],
            financials: ['Valuation', 'Profitability', 'Earnings', 'Financial Metrics', 'Cash/CashFlow'],
            technical: ['Technical'],
            sentiment: ['Sentiment Analysis']
        };

        const self = this;

        const METRIC_TOOLTIPS = {
            'p/e ratio':        'Price-to-Earnings: share price divided by EPS. Lower = potentially cheaper.',
            'forward p/e':      'Forward P/E uses estimated next-year earnings.',
            'p/b ratio':        'Price-to-Book: share price vs. net assets. < 1.5 may indicate undervaluation.',
            'p/s ratio':        'Price-to-Sales: market cap divided by revenue.',
            'peg ratio':        'P/E relative to growth rate. < 1 may indicate undervalued given growth.',
            'ev/ebitda':        'Enterprise Value / EBITDA. Lower values suggest cheaper valuation.',
            'roe':              'Return on Equity: net income as % of shareholder equity. > 15% is strong.',
            'roa':              'Return on Assets: net income as % of total assets. > 5% is efficient.',
            'roic':             'Return on Invested Capital. > 10% is strong.',
            'profit margin':    'Net income as % of revenue.',
            'operating margin': 'Operating income as % of revenue before interest/taxes.',
            'debt/equity':      'Total debt / shareholder equity. > 2 = high leverage.',
            'current ratio':    'Current assets / current liabilities. > 2 healthy; < 1 = liquidity risk.'
        };

        function buildPaneMetrics(tabName) {
            const groupNamesList = tabGroupNames[tabName] || [];
            let paneHtml = '<div class="metrics-grid">';
            for (const groupName of groupNamesList) {
                const keywords = groups[groupName];
                if (!keywords) continue;
                const groupMetrics = {};
                for (const [key, value] of Object.entries(data)) {
                    if (key === 'error' || key === 'Ticker' || key === 'Data Timestamp' || key === '_fundamental_analysis') continue;
                    const keyLower = key.toLowerCase();
                    if (keywords.some(kw => keyLower.includes(kw.toLowerCase()))) {
                        groupMetrics[key] = value;
                    }
                }
                if (Object.keys(groupMetrics).length > 0) {
                    paneHtml += '<div class="metric-group">';
                    paneHtml += `<h4>${self.escapeHtml(groupName)}</h4>`;
                    for (const [key, value] of Object.entries(groupMetrics)) {
                        paneHtml += '<div class="metric-item">';
                        const cleanKey = self.escapeHtml(key.replace(/\s*\(Enhanced\)\s*$/i, ''));
                        const keyLc = cleanKey.toLowerCase();
                        const tooltipText = METRIC_TOOLTIPS[keyLc] || '';
                        const tooltipAttr = tooltipText ? ` data-tooltip="${tooltipText.replace(/"/g, '&quot;')}"` : '';
                        paneHtml += `<span class="metric-label"${tooltipAttr}>${cleanKey}</span>`;
                        const numericVal = (typeof Utils.parseNumeric === 'function') ? Utils.parseNumeric(value) : null;
                        const colorClass = (typeof Utils.colorCodeMetric === 'function') ? Utils.colorCodeMetric(key, numericVal) : '';
                        const colorAttr = colorClass ? ` class="metric-value ${colorClass}"` : ' class="metric-value"';
                        paneHtml += `<span${colorAttr}>${Utils.formatValue(value)}</span>`;
                        paneHtml += '</div>';
                    }
                    paneHtml += '</div>'; // metric-group
                }
            }
            paneHtml += '</div>'; // metrics-grid
            return paneHtml;
        }

        const tickerContentId = `ticker-content-${ticker}`;
        const esc = this.escapeHtml.bind(this);
        const savedTab = (typeof sessionStorage !== 'undefined' && sessionStorage.getItem('subtab-' + ticker)) || 'overview';

        const tabDefs = [
            { id: 'overview',   label: 'Overview' },
            { id: 'financials', label: 'Financials' },
            { id: 'technical',  label: 'Technical' },
            { id: 'sentiment',  label: 'Sentiment' },
            { id: 'deep',       label: 'Deep Analysis' }
        ];

        let html = `<div class="ticker-header collapsed" onclick="DisplayManager.toggleTicker('${tickerContentId}')">`;
        html += '<div style="display: flex; align-items: center;">';
        html += `<h3>${esc(ticker)}</h3>`;
        html += '<span class="ticker-collapse-icon">▼</span>';
        html += '</div>';
        html += `<span>${esc(data['Data Timestamp'] || '')}</span>`;
        html += '</div>';

        html += `<div class="ticker-content collapsed" id="${tickerContentId}">`;
        html += '<div class="ticker-subtabs">';

        // Sub-tab navigation
        html += '<div class="ticker-subtab-nav">';
        for (const { id, label } of tabDefs) {
            const activeClass = id === savedTab ? ' active' : '';
            html += `<button class="ticker-subtab-btn${activeClass}" data-ticker="${esc(ticker)}" data-tab="${id}" onclick="DisplayManager.switchSubTab('${esc(ticker)}','${id}')">${label}</button>`;
        }
        html += '</div>'; // ticker-subtab-nav

        // Overview pane
        html += `<div id="subtab-${esc(ticker)}-overview" class="ticker-subtab-content${'overview' === savedTab ? ' active' : ''}">`;
        html += `<div id="priceChart-${esc(ticker)}" class="price-chart-container"></div>`;
        html += `<div id="analystRangeBar-${esc(ticker)}" class="analyst-range-bar-container"></div>`;
        html += buildPaneMetrics('overview');
        html += '</div>'; // subtab-overview

        // Financials pane
        html += `<div id="subtab-${esc(ticker)}-financials" class="ticker-subtab-content${'financials' === savedTab ? ' active' : ''}">`;
        html += buildPaneMetrics('financials');
        html += '</div>'; // subtab-financials

        // Technical pane
        html += `<div id="subtab-${esc(ticker)}-technical" class="ticker-subtab-content${'technical' === savedTab ? ' active' : ''}">`;
        html += buildPaneMetrics('technical');
        html += '</div>'; // subtab-technical

        // Sentiment pane
        html += `<div id="subtab-${esc(ticker)}-sentiment" class="ticker-subtab-content${'sentiment' === savedTab ? ' active' : ''}">`;
        html += buildPaneMetrics('sentiment');
        html += '</div>'; // subtab-sentiment

        // Deep Analysis pane — renderFundamental + HealthScore (creates deep-analysis-group)
        html += `<div id="subtab-${esc(ticker)}-deep" class="ticker-subtab-content${'deep' === savedTab ? ' active' : ''}">`;
        if (data._fundamental_analysis && typeof AnalyticsRenderer !== 'undefined' && typeof AnalyticsRenderer.renderFundamental === 'function') {
            html += AnalyticsRenderer.renderFundamental(data._fundamental_analysis);
        }
        if (typeof HealthScore !== 'undefined') {
            const hs = HealthScore.computeGrade(data, ticker);
            html += hs.html;
        }
        html += '</div>'; // subtab-deep

        html += '</div>'; // ticker-subtabs
        html += '</div>'; // ticker-content

        div.innerHTML = html;

        if (typeof EarningsQuality !== 'undefined') {
            EarningsQuality.renderIntoGroup(ticker, data, div);
        }
        if (typeof DCFValuation !== 'undefined') {
            DCFValuation.renderIntoGroup(ticker, data, div);
        }
        if (typeof PeerComparison !== 'undefined') {
            PeerComparison.renderIntoGroup(ticker, data, div);
        }
        if (typeof PriceChart !== 'undefined') {
            PriceChart.initCard(ticker, data);
        }
        return div;
    },

    /**
     * Switch active sub-tab for a specific ticker card (Phase 28)
     * Ticker-scoped: multiple open cards do not interfere with each other.
     */
    switchSubTab(ticker, tabName) {
        document.querySelectorAll(`[id^="subtab-${ticker}-"]`).forEach(function(el) {
            el.classList.remove('active');
        });
        document.querySelectorAll(`.ticker-subtab-btn[data-ticker="${ticker}"]`).forEach(function(btn) {
            btn.classList.remove('active');
        });
        var pane = document.getElementById('subtab-' + ticker + '-' + tabName);
        if (pane) pane.classList.add('active');
        var btn = document.querySelector(`.ticker-subtab-btn[data-ticker="${ticker}"][data-tab="${tabName}"]`);
        if (btn) btn.classList.add('active');
        if (typeof sessionStorage !== 'undefined') {
            sessionStorage.setItem('subtab-' + ticker, tabName);
        }
        if (tabName === 'overview' && typeof PriceChart !== 'undefined') {
            PriceChart.fetchIfNeeded(ticker, '3mo');
        }
    },

    /**
     * Display advanced analytics
     * This function handles correlation, PCA, regression, and Monte Carlo results
     */
    displayAnalytics(analyticsData) {
        const analyticsResultsDiv = document.getElementById('analyticsResults');
        if (!analyticsResultsDiv) {
            console.error('Required DOM element not found: analyticsResults');
            return;
        }

        if (!analyticsData || typeof analyticsData !== 'object') {
            console.error('Invalid analyticsData provided');
            return;
        }

        // Verify AnalyticsRenderer dependency exists
        if (typeof AnalyticsRenderer === 'undefined') {
            console.error('Required dependency not found: AnalyticsRenderer');
            return;
        }
        
        const analyticsDiv = document.createElement('div');
        analyticsDiv.className = 'analytics-section';
        analyticsDiv.style.marginBottom = '30px';
        
        let html = '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 20px;">';
        html += '<h2 style="margin: 0 0 20px 0; font-size: 1.8rem; color: white;">📈 Advanced Financial Analytics</h2>';
        html += '<p style="margin: 0; opacity: 0.9;">Portfolio-level risk metrics and statistical analysis</p>';
        html += '</div>';
        
        // Check if analytics were skipped (info message present)
        if (analyticsData.info && analyticsData.info.message) {
            html += '<div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 10px; padding: 20px; margin-bottom: 20px;">';
            html += '<h3 style="color: #856404; margin: 0 0 10px 0;">ℹ️ Analytics Status</h3>';
            html += `<p style="color: #856404; margin: 0 0 10px 0; font-size: 1rem;">${this.escapeHtml(analyticsData.info.message)}</p>`;
            if (analyticsData.info.recommendation) {
                html += `<p style="color: #856404; margin: 0; font-size: 0.9rem;"><strong>Recommendation:</strong> ${this.escapeHtml(analyticsData.info.recommendation)}</p>`;
            }
            html += '</div>';
        }
        
        let hasAnalytics = false;
        
        // Add correlation analysis
        if (analyticsData.correlation && typeof AnalyticsRenderer.renderCorrelation === 'function') {
            html += AnalyticsRenderer.renderCorrelation(analyticsData.correlation);
            hasAnalytics = true;
        }
        
        // Add PCA analysis
        if (analyticsData.pca && typeof AnalyticsRenderer.renderPCA === 'function') {
            html += AnalyticsRenderer.renderPCA(analyticsData.pca);
            hasAnalytics = true;
        }
        
        // Add portfolio-level Monte Carlo (includes stress test for multi-asset portfolios)
        if (analyticsData.portfolio_monte_carlo && typeof AnalyticsRenderer.renderMonteCarlo === 'function') {
            html += '<div id="analyticsVarSection" style="background: #ffffff; border-radius: 12px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-top: 4px solid #9b59b6;">';
            html += '<h3 style="color: #9b59b6; margin: 0 0 20px 0; font-size: 1.6rem; display: flex; align-items: center; gap: 10px;">';
            html += '<span style="font-size: 1.8rem;">📊</span>';
            html += '<span>Portfolio Risk Analysis</span>';
            html += '</h3>';
            html += AnalyticsRenderer.renderMonteCarlo(analyticsData.portfolio_monte_carlo);
            html += '</div>';
            hasAnalytics = true;
        }
        
        // Add individual ticker analytics (includes fundamental analysis)
        if (typeof AnalyticsRenderer.renderTickerAnalytics === 'function') {
            for (const [ticker, tickerAnalytics] of Object.entries(analyticsData)) {
                // Skip portfolio-level analytics keys to focus on individual tickers
                if (ticker === 'correlation' || ticker === 'pca' || ticker === 'info' || ticker === 'portfolio_monte_carlo') continue;
                
                // Render ticker-specific analytics including fundamental analysis
                const tickerHtml = AnalyticsRenderer.renderTickerAnalytics(ticker, tickerAnalytics);
                if (tickerHtml) {
                    html += tickerHtml;
                    hasAnalytics = true;
                }
            }
        }
        
        // If no analytics were rendered and no info message, show empty state
        if (!hasAnalytics && !analyticsData.info) {
            html += '<div style="background: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 10px; padding: 30px; text-align: center;">';
            html += '<p style="color: #6c757d; margin: 0; font-size: 1.1rem;">No analytics data available. This may occur if:</p>';
            html += '<ul style="color: #6c757d; text-align: left; display: inline-block; margin-top: 10px;">';
            html += '<li>Portfolio has fewer than 2 tickers (required for correlation)</li>';
            html += '<li>Unable to fetch historical data for the tickers</li>';
            html += '<li>Analytics computation encountered an error</li>';
            html += '</ul>';
            html += '</div>';
        }
        
        analyticsDiv.innerHTML = html;

        // Use replaceChildren() for clarity instead of innerHTML = '' + appendChild
        analyticsResultsDiv.replaceChildren(analyticsDiv);
        document.body.classList.add('results-loaded');
    },

    /**
     * Toggle ticker collapse/expand; restores persisted sub-tab on expand (Phase 28)
     */
    toggleTicker(contentId) {
        const content = document.getElementById(contentId);
        const header = content?.previousElementSibling;

        if (!content || !header) return;

        const isCollapsed = content.classList.contains('collapsed');

        if (isCollapsed) {
            content.classList.remove('collapsed');
            header.classList.remove('collapsed');
            // Restore persisted sub-tab and trigger price chart
            var ticker = contentId.replace('ticker-content-', '');
            var savedTab = (typeof sessionStorage !== 'undefined' && sessionStorage.getItem('subtab-' + ticker)) || 'overview';
            DisplayManager.switchSubTab(ticker, savedTab);
        } else {
            content.classList.add('collapsed');
            header.classList.add('collapsed');
        }
    }
};

// Export for browser environment
window.DisplayManager = DisplayManager;
window.SectionCollapse = SectionCollapse;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DisplayManager, SectionCollapse };
}
