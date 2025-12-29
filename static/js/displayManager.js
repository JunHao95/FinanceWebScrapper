// ===========================
// Display Manager Module
// Handles rendering of results and analytics
// ===========================

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
     * Create ticker card with metrics
     */
    createTickerCard(ticker, data) {
        if (!ticker || !data || typeof data !== 'object') {
            console.error('Invalid ticker or data provided to createTickerCard');
            return null;
        }

        // Verify Utils dependency exists
        if (typeof Utils === 'undefined' || typeof Utils.formatValue !== 'function') {
            console.error('Required dependency not found: Utils.formatValue');
            return null;
        }

        const div = document.createElement('div');
        div.className = 'ticker-results';

        // Group metrics
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

        const tickerContentId = `ticker-content-${ticker}`;
        
        let html = `<div class="ticker-header collapsed" onclick="DisplayManager.toggleTicker('${tickerContentId}')">`;
        html += '<div style="display: flex; align-items: center;">';
        html += `<h3>${this.escapeHtml(ticker)}</h3>`;
        html += '<span class="ticker-collapse-icon">▼</span>';
        html += '</div>';
        html += `<span>${this.escapeHtml(data['Data Timestamp'] || '')}</span>`;
        html += '</div>';

        html += `<div class="ticker-content collapsed" id="${tickerContentId}">`;

        // Add fundamental analysis if available
        if (data._fundamental_analysis && typeof AnalyticsRenderer !== 'undefined' && typeof AnalyticsRenderer.renderFundamental === 'function') {
            html += AnalyticsRenderer.renderFundamental(data._fundamental_analysis);
        }

        html += '<div class="metrics-grid">';

        for (const [groupName, keywords] of Object.entries(groups)) {
            const groupMetrics = {};
            
            for (const [key, value] of Object.entries(data)) {
                // Skip internal fields, errors, and metadata
                if (key === 'error' || key === 'Ticker' || key === 'Data Timestamp' || key === '_fundamental_analysis') continue;
                
                const keyLower = key.toLowerCase();
                const matchesKeyword = keywords.some(kw => keyLower.includes(kw.toLowerCase()));
                
                if (matchesKeyword) {
                    groupMetrics[key] = value;
                }
            }

            if (Object.keys(groupMetrics).length > 0) {
                html += '<div class="metric-group">';
                html += `<h4>${this.escapeHtml(groupName)}</h4>`;
                
                for (const [key, value] of Object.entries(groupMetrics)) {
                    html += '<div class="metric-item">';
                    const cleanKey = this.escapeHtml(key.replace(/\s*\(Enhanced\)\s*$/i, ''));
                    html += `<span class="metric-label">${cleanKey}</span>`;
                    html += `<span class="metric-value">${Utils.formatValue(value)}</span>`;
                    html += '</div>';
                }
                
                html += '</div>';
            }
        }

        html += '</div>';
        div.innerHTML = html;
        return div;
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
        html += '<h2 style="margin: 0 0 20px 0; font-size: 1.8rem;">📈 Advanced Financial Analytics</h2>';
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
        
        // Add individual ticker analytics (includes fundamental analysis)
        if (typeof AnalyticsRenderer.renderTickerAnalytics === 'function') {
            for (const [ticker, tickerAnalytics] of Object.entries(analyticsData)) {
                // Skip portfolio-level analytics keys to focus on individual tickers
                if (ticker === 'correlation' || ticker === 'pca' || ticker === 'info') continue;
                
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
    },

    /**
     * Toggle ticker collapse/expand
     */
    toggleTicker(contentId) {
        const content = document.getElementById(contentId);
        const header = content?.previousElementSibling;
        
        if (!content || !header) return;
        
        const isCollapsed = content.classList.contains('collapsed');
        
        if (isCollapsed) {
            content.classList.remove('collapsed');
            header.classList.remove('collapsed');
        } else {
            content.classList.add('collapsed');
            header.classList.add('collapsed');
        }
    }
};

// Export for browser environment
window.DisplayManager = DisplayManager;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DisplayManager;
}
