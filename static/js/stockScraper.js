// ===========================
// Stock Scraper Module
// ===========================

const StockScraper = {
    _initialized: false,

    /**
     * Initialize stock scraper
     */
    init() {
        // Guard against multiple event listener registrations
        if (this._initialized) {
            console.warn('StockScraper already initialized');
            return;
        }

        const form = document.getElementById('scrapeForm');
        if (!form) {
            console.error('scrapeForm not found');
            return;
        }

        // Handle form submission
        form.addEventListener('submit', async (e) => {
            await this.handleSubmit(e);
        });

        this._initialized = true;
    },

    /**
     * Handle form submission
     */
    async handleSubmit(e) {
        e.preventDefault();
        
        const tickers = document.getElementById('tickers').value
            .split(',')
            .map(t => t.trim().toUpperCase())
            .filter(t => t.length > 0);
        
        if (tickers.length === 0) {
            Utils.showAlert('Please enter at least one ticker symbol', 'error');
            return;
        }

        // Get selected sources — use smart defaults if advanced settings are collapsed
        const advancedDetails = document.getElementById('settings-drawer');
        const advancedOpen = advancedDetails && advancedDetails.classList.contains('drawer-open');

        let sources = [];
        if (advancedOpen) {
            if (document.getElementById('source-all').checked) {
                sources.push('all');
            } else {
                document.querySelectorAll('.checkbox-item input[type="checkbox"]:not(#source-all)').forEach(cb => {
                    if (cb.checked) sources.push(cb.value);
                });
            }
            if (sources.length === 0) {
                Utils.showAlert('Please select at least one data source', 'error');
                return;
            }
        } else {
            // Advanced collapsed: use all free sources as defaults
            sources = ['yahoo', 'finviz', 'google', 'technical'];
        }

        // Get portfolio allocation
        const portfolioAllocation = FormManager.getPortfolioAllocation();

        // Show loading with ticker count info
        const loadingSection = document.getElementById('loadingSection');
        loadingSection.classList.add('active');
        document.getElementById('resultsSection').classList.remove('active');
        
        // Update loading message for large portfolios
        const loadingText = loadingSection.querySelector('.loading-spinner p');
        if (loadingText && tickers.length > 10) {
            loadingText.textContent = `Processing ${tickers.length} tickers... This may take several minutes.`;
        }
        
        Utils.hideAlert();

        try {
            const requestBody = {
                tickers: tickers,
                sources: sources
            };
            
            if (portfolioAllocation) {
                requestBody.portfolio_allocation = portfolioAllocation;
            }

            const result = await API.scrapeStocks(requestBody);

            if (result.success) {
                AppState.currentData = result.data;
                AppState.currentCnnData = result.cnn_data;
                AppState.currentTickers = tickers;
                AppState.currentAnalytics = result.analytics_data || {};

                // Populate pageContext from scrape result
                window.pageContext.tickers = tickers.slice();
                window.pageContext.cnnFearGreed = result.cnn_data
                    ? { score: result.cnn_data.score, label: result.cnn_data.label }
                    : null;
                window.pageContext.tickerData = {};
                tickers.forEach(function(ticker) {
                    const raw = (result.data && result.data[ticker]) || {};
                    const fa = raw['_fundamental_analysis'] || null;
                    let fundamentalSummary = '';
                    if (fa && typeof fa === 'object') {
                        const s = fa.summary || fa.overall_assessment || fa.recommendation || '';
                        fundamentalSummary = typeof s === 'string' ? s.slice(0, 300) : '';
                    }
                    // Find the first raw key that contains the given substring (case-insensitive),
                    // mirroring the substring-match logic used by displayManager.js.
                    function findVal(substring) {
                        const lower = substring.toLowerCase();
                        for (const k of Object.keys(raw)) {
                            if (k.toLowerCase().includes(lower) && raw[k] != null && raw[k] !== '') {
                                return raw[k];
                            }
                        }
                        return null;
                    }
                    window.pageContext.tickerData[ticker] = {
                        name: findVal('Company Name') || findVal('name') || '',
                        price: findVal('Current Price') || findVal('Price') || null,
                        pe: findVal('P/E Ratio') || findVal('P/E') || null,
                        eps: findVal('EPS (ttm)') || findVal('EPS (TTM)') || findVal('EPS') || null,
                        roe: findVal('ROE') || null,
                        rsi: findVal('RSI') || null,
                        sentimentOverall: (raw.sentiment && raw.sentiment.overall) || findVal('Overall Sentiment') || null,
                        sentimentNews: (raw.sentiment && raw.sentiment.news) || null,
                        sentimentReddit: (raw.sentiment && raw.sentiment.reddit) || null,
                        var95: null,
                        regime: null,
                        fundamentals: fundamentalSummary
                    };
                });
                const analytics = result.analytics_data || {};
                window.pageContext.portfolio = {
                    sharpe: analytics.sharpe_ratio || analytics.sharpe || null,
                    var95: analytics.var_95 || analytics.portfolio_var || null,
                    correlation: analytics.top_correlation || null
                };

                this.displayResults(result);
                Utils.showAlert('Data scraped successfully!', 'success');
            } else {
                Utils.showAlert('Error: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            Utils.showAlert('Failed to fetch data: ' + error.message, 'error');
        } finally {
            // Reset loading message to default
            const loadingSection = document.getElementById('loadingSection');
            const loadingText = loadingSection.querySelector('.loading-spinner p');
            if (loadingText) {
                loadingText.textContent = 'Loading...';
            }
            loadingSection.classList.remove('active');
        }
    },

    /**
     * Display scraping results
     */
    displayResults(result) {
        // Update stock count badge
        const stockCount = Object.keys(result.data).length;
        document.getElementById('stocksCount').textContent = stockCount;
        
        // Display CNN metrics
        DisplayManager.displayCnnMetrics(result.cnn_data);

        // Clear deep-analysis module session caches before rebuilding cards (BREAK-01 fix)
        if (typeof HealthScore !== 'undefined')     HealthScore.clearSession();
        if (typeof EarningsQuality !== 'undefined') EarningsQuality.clearSession();
        if (typeof DCFValuation !== 'undefined')    DCFValuation.clearSession();
        if (typeof PeerComparison !== 'undefined')  PeerComparison.clearSession();
        if (typeof TradingIndicators !== 'undefined') TradingIndicators.clearSession();

        // Clear ticker results
        const tickerResultsDiv = document.getElementById('tickerResults');
        tickerResultsDiv.innerHTML = '';

        // Display analytics
        if (result.analytics_data && Object.keys(result.analytics_data).length > 0) {
            DisplayManager.displayAnalytics(result.analytics_data);
            document.getElementById('noAnalyticsMessage').style.display = 'none';
            const analyticsTabBtn = document.getElementById('analyticsTab');
            
            // Check if only info field exists (analytics skipped)
            const hasRealAnalytics = Object.keys(result.analytics_data).some(key => key !== 'info');
            if (hasRealAnalytics) {
                analyticsTabBtn.innerHTML = '📈 Advanced Analytics <span style="background: #28a745; color: white; border-radius: 10px; padding: 2px 8px; font-size: 11px; margin-left: 5px;">✓ Ready</span>';
            } else if (result.analytics_data.info) {
                analyticsTabBtn.innerHTML = '📈 Advanced Analytics <span style="background: #ffc107; color: #333; border-radius: 10px; padding: 2px 8px; font-size: 11px; margin-left: 5px;">⚠ Skipped</span>';
            }
        } else {
            document.getElementById('analyticsResults').innerHTML = '';
            document.getElementById('noAnalyticsMessage').style.display = 'block';
        }

        // Display ticker results
        for (const [ticker, data] of Object.entries(result.data)) {
            const tickerDiv = DisplayManager.createTickerCard(ticker, data);
            tickerResultsDiv.appendChild(tickerDiv);
            // Phase 13: write health score to pageContext
            if (typeof HealthScore !== 'undefined' && window.pageContext && window.pageContext.tickerData && window.pageContext.tickerData[ticker]) {
                const hs = HealthScore.computeGrade(data, ticker);
                window.pageContext.tickerData[ticker].healthScore = {
                    grade: hs.grade,
                    subScores: hs.subScores,
                    explanation: hs.explanation
                };
            }
            // Phase 14: write earnings quality to pageContext
            if (typeof EarningsQuality !== 'undefined' && window.pageContext && window.pageContext.tickerData && window.pageContext.tickerData[ticker]) {
                const eq = EarningsQuality.computeQuality(data, ticker);
                window.pageContext.tickerData[ticker].earningsQuality = {
                    label: eq.label,
                    accrualsRatio: eq.accrualsRatio,
                    cashConversionRatio: eq.cashConversionRatio,
                    consistencyFlag: eq.consistencyFlag
                };
            }
            // Phase 15: write DCF valuation to pageContext
            if (typeof DCFValuation !== 'undefined' && window.pageContext && window.pageContext.tickerData && window.pageContext.tickerData[ticker]) {
                const dcf = DCFValuation.computeValuation(data, 0.10, 0.10, 0.03);
                window.pageContext.tickerData[ticker].dcfValuation = {
                    intrinsicValue: dcf.intrinsicPerShare || null,
                    intrinsicEquityTotal: dcf.intrinsicEquityTotal || null,
                    premium: dcf.premium || null,
                    wacc: 0.10,
                    g1: 0.10,
                    g2: 0.03,
                    fcfSource: dcf.fcfSource || null
                };
            }
        }
        
        // Switch to Auto Analysis tab so auto-run results are immediately visible
        TabManager.switchTab('autoanalysis');

        const autoanalysisCountEl = document.getElementById('autoanalysisCount');
        if (autoanalysisCountEl) {
            autoanalysisCountEl.textContent = AppState.currentTickers.length;
            autoanalysisCountEl.style.display = 'inline-block';
        }

        document.getElementById('resultsSection').classList.add('active');
        document.body.classList.add('results-loaded');

        // Initialize Portfolio Health card (synchronously, before auto-run starts)
        if (window.PortfolioHealth) {
            const allocations = FormManager.getPortfolioAllocation() || {};
            PortfolioHealth.initCard(AppState.currentTickers, AppState.currentAnalytics, allocations);
        }

        // Auto-run extended analysis (regime detection + portfolio MDP)
        if (window.AutoRun) {
            AutoRun.triggerAutoRun(AppState.currentTickers);
        }
    },

    /**
     * Validate email format
     * @param {string} email - Email address to validate
     * @returns {boolean} True if valid
     */
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return email.split(',').map(e => e.trim()).filter(e => e).every(e => emailRegex.test(e));
    },

    /**
     * Send email report
     */
    async sendEmail(event) {
        if (event) event.preventDefault();
        
        const emailInput = document.getElementById('emailInput');
        if (!emailInput) {
            console.error('emailInput element not found');
            return;
        }

        const email = emailInput.value.trim();
        
        if (!email) {
            Utils.showAlert('Please enter your email address', 'error');
            return;
        }

        // Add email format validation
        if (!this.validateEmail(email)) {
            Utils.showAlert('Please enter a valid email address', 'error');
            return;
        }

        if (!AppState.currentData) {
            Utils.showAlert('No data to send. Please analyze stocks first.', 'error');
            return;
        }

        try {
            Utils.showAlert('Sending email...', 'info');

            const emailData = {
                tickers: AppState.currentTickers,
                data: AppState.currentData,
                cnn_data: AppState.currentCnnData,
                analytics_data: AppState.currentAnalytics,
                trading_indicators_data: AppState.tradingIndicatorsData || {},
                email: email
            };

            const result = await API.sendEmail(emailData);

            if (result.success) {
                Utils.showAlert('Email sent successfully! 📧', 'success');
                emailInput.value = '';
            } else {
                Utils.showAlert('Failed to send email: ' + result.error, 'error');
            }
        } catch (error) {
            Utils.showAlert('Failed to send email: ' + error.message, 'error');
        }
    }
};

// Export for browser environment
window.StockScraper = StockScraper;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StockScraper;
}
