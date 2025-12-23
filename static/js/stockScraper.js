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

        // Get selected sources
        const sources = [];
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

        const alphaKey = document.getElementById('alphaKey').value.trim();
        const finhubKey = document.getElementById('finhubKey').value.trim();

        // Get portfolio allocation
        const portfolioAllocation = FormManager.getPortfolioAllocation();
        
        // Validate allocation if provided
        if (portfolioAllocation) {
            let total = 0;
            for (const weight of Object.values(portfolioAllocation)) {
                total += weight;
            }
            
            if (Math.abs(total - 1.0) > 0.01) {
                Utils.showAlert('Portfolio allocation must sum to 100%. Current total: ' + (total * 100).toFixed(1) + '%', 'error');
                return;
            }
        }

        // Show loading
        document.getElementById('loadingSection').classList.add('active');
        document.getElementById('resultsSection').classList.remove('active');
        Utils.hideAlert();

        try {
            const requestBody = {
                tickers: tickers,
                sources: sources,
                alpha_key: alphaKey || undefined,
                finhub_key: finhubKey || undefined
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
                
                this.displayResults(result);
                Utils.showAlert('Data scraped successfully!', 'success');
            } else {
                Utils.showAlert('Error: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Fetch error:', error);
            Utils.showAlert('Failed to fetch data: ' + error.message, 'error');
        } finally {
            document.getElementById('loadingSection').classList.remove('active');
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

        // Clear ticker results
        const tickerResultsDiv = document.getElementById('tickerResults');
        tickerResultsDiv.innerHTML = '';

        // Display analytics
        if (result.analytics_data && Object.keys(result.analytics_data).length > 0) {
            DisplayManager.displayAnalytics(result.analytics_data);
            document.getElementById('noAnalyticsMessage').style.display = 'none';
            const analyticsTabBtn = document.getElementById('analyticsTab');
            analyticsTabBtn.innerHTML = '📈 Advanced Analytics <span style="background: #28a745; color: white; border-radius: 10px; padding: 2px 8px; font-size: 11px; margin-left: 5px;">✓ Ready</span>';
        } else {
            document.getElementById('analyticsResults').innerHTML = '';
            document.getElementById('noAnalyticsMessage').style.display = 'block';
        }

        // Display ticker results
        for (const [ticker, data] of Object.entries(result.data)) {
            const tickerDiv = DisplayManager.createTickerCard(ticker, data);
            tickerResultsDiv.appendChild(tickerDiv);
        }
        
        // Switch to stocks tab by default
        TabManager.switchTab('stocks');
        
        document.getElementById('resultsSection').classList.add('active');
    },

    /**
     * Validate email format
     * @param {string} email - Email address to validate
     * @returns {boolean} True if valid
     */
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
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
