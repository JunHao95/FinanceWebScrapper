// ===========================
// Display Manager Module
// Handles rendering of results and analytics
// ===========================

const DisplayManager = {
    /**
     * Display CNN Fear & Greed metrics
     */
    displayCnnMetrics(cnnData) {
        const cnnDiv = document.getElementById('cnnMetrics');
        
        let html = '<div class="cnn-metrics">';
        html += '<h3>📊 CNN Fear & Greed Index</h3>';
        
        for (const [metric, values] of Object.entries(cnnData)) {
            const displayName = metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            html += '<div class="metric-card">';
            html += `<strong>${displayName}:</strong> `;
            html += `Score: ${values.score || '--'} | `;
            html += `Rating: ${values.rating || '--'}`;
            html += '</div>';
        }
        
        html += '</div>';
        cnnDiv.innerHTML = html;
    },

    /**
     * Create ticker card with metrics
     */
    createTickerCard(ticker, data) {
        const div = document.createElement('div');
        div.className = 'ticker-results';

        // Group metrics
        const groups = {
            'Basic Info': ['Current Price', 'Market Cap', 'Company Name'],
            'Valuation': ['P/E Ratio', 'Forward P/E', 'P/B Ratio', 'P/S Ratio', 'PEG Ratio', 'EV/EBITDA'],
            'Profitability': ['ROE', 'ROA', 'ROIC', 'Profit Margin', 'Operating Margin'],
            'Earnings': ['EPS', 'EPS Growth'],
            'Technical': ['RSI', 'MA10', 'MA20', 'MA50', 'BB Signal'],
            'Sentiment Analysis': [
                'Overall Sentiment Score', 'Overall Sentiment Label', 'Sentiment Confidence', 'Active Data Sources',
                'Google Trends Interest', 'Trends Direction', 'Avg Interest',
                'News Articles Analyzed', 'News Sentiment Score', 'Positive News Articles', 'Negative News Articles', 'FinBERT News Score',
                'Reddit Posts Analyzed', 'Reddit Sentiment Score', 'Reddit Avg Score', 'Reddit Avg Comments', 'Positive Reddit Posts',
                'Top Topic 1 Keywords', 'Top Topic 2 Keywords', 'Top Topic 3 Keywords', 'Document Similarity'
            ]
        };

        let html = '<div class="ticker-header">';
        html += `<h3>${ticker}</h3>`;
        html += `<span>${data['Data Timestamp'] || ''}</span>`;
        html += '</div>';

        html += '<div class="metrics-grid">';

        for (const [groupName, keywords] of Object.entries(groups)) {
            const groupMetrics = {};
            
            for (const [key, value] of Object.entries(data)) {
                if (key === 'error' || key === 'Ticker' || key === 'Data Timestamp') continue;
                
                const keyLower = key.toLowerCase();
                const matchesKeyword = keywords.some(kw => keyLower.includes(kw.toLowerCase()));
                
                if (matchesKeyword) {
                    groupMetrics[key] = value;
                }
            }

            if (Object.keys(groupMetrics).length > 0) {
                html += '<div class="metric-group">';
                html += `<h4>${groupName}</h4>`;
                
                for (const [key, value] of Object.entries(groupMetrics)) {
                    html += '<div class="metric-item">';
                    const cleanKey = key.replace(/\s*\(Enhanced\)\s*$/i, '');
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
        
        const analyticsDiv = document.createElement('div');
        analyticsDiv.className = 'analytics-section';
        analyticsDiv.style.marginBottom = '30px';
        
        let html = '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 20px;">';
        html += '<h2 style="margin: 0 0 20px 0; font-size: 1.8rem;">📈 Advanced Financial Analytics</h2>';
        html += '<p style="margin: 0; opacity: 0.9;">Portfolio-level risk metrics and statistical analysis</p>';
        html += '</div>';
        
        // Add correlation analysis
        if (analyticsData.correlation) {
            html += AnalyticsRenderer.renderCorrelation(analyticsData.correlation);
        }
        
        // Add PCA analysis
        if (analyticsData.pca) {
            html += AnalyticsRenderer.renderPCA(analyticsData.pca);
        }
        
        // Add individual ticker analytics
        for (const [ticker, tickerAnalytics] of Object.entries(analyticsData)) {
            if (ticker === 'correlation' || ticker === 'pca') continue;
            html += AnalyticsRenderer.renderTickerAnalytics(ticker, tickerAnalytics);
        }
        
        analyticsDiv.innerHTML = html;
        analyticsResultsDiv.innerHTML = '';
        analyticsResultsDiv.appendChild(analyticsDiv);
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DisplayManager;
}
