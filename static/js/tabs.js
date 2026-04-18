// ===========================
// Tab Navigation Module
// ===========================

const TabManager = {
    /**
     * Switch between stock details and analytics tabs
     */
    switchTab(tabName) {
        // Validate tabName parameter
        if (!tabName || typeof tabName !== 'string') {
            console.error('Invalid tabName parameter:', tabName);
            return;
        }

        const validTabs = ['stocks', 'analytics', 'autoanalysis', 'tradingindicators'];
        if (!validTabs.includes(tabName)) {
            console.error('Invalid tab name:', tabName);
            return;
        }

        try {
            // Remove active class from all tabs and contents
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            // Add active class to selected tab and content
            if (tabName === 'stocks') {
                const stocksTab = document.getElementById('stocksTab');
                const stocksContent = document.getElementById('stocksTabContent');
                if (stocksTab && stocksContent) {
                    stocksTab.classList.add('active');
                    stocksContent.classList.add('active');
                } else {
                    console.error('Stocks tab elements not found');
                }
            } else if (tabName === 'analytics') {
                const analyticsTab = document.getElementById('analyticsTab');
                const analyticsContent = document.getElementById('analyticsTabContent');
                if (analyticsTab && analyticsContent) {
                    analyticsTab.classList.add('active');
                    analyticsContent.classList.add('active');
                } else {
                    console.error('Analytics tab elements not found');
                }
            } else if (tabName === 'autoanalysis') {
                const autoanalysisTab = document.getElementById('autoanalysisTab');
                const autoanalysisContent = document.getElementById('autoanalysisTabContent');
                if (autoanalysisTab && autoanalysisContent) {
                    autoanalysisTab.classList.add('active');
                    autoanalysisContent.classList.add('active');
                }
            } else if (tabName === 'tradingindicators') {
                const tiTab = document.getElementById('tradingIndicatorsTab');
                const tiContent = document.getElementById('tradingIndicatorsTabContent');
                if (tiTab && tiContent) {
                    tiTab.classList.add('active');
                    tiContent.classList.add('active');
                    if (typeof TradingIndicators !== 'undefined' &&
                        window.pageContext && window.pageContext.tickers) {
                        var sel = document.getElementById('tiLookbackSelect');
                        var lookback = (sel && parseInt(sel.value, 10)) || 90;
                        TradingIndicators.initLookbackDropdown(window.pageContext.tickers);
                        window.pageContext.tickers.forEach(function (ticker) {
                            TradingIndicators.fetchForTicker(ticker, lookback);
                        });
                    }
                }
            }
        } catch (error) {
            console.error('Error switching tabs:', error);
        }
    },

    /**
     * Switch between main tabs (Stock Analysis, Options Pricing, Volatility Surface)
     */
    switchMainTab(tabName, event) {
        // Validate tabName parameter
        if (!tabName || typeof tabName !== 'string') {
            console.error('Invalid tabName parameter:', tabName);
            return;
        }

        try {
            // Hide all tab contents
            document.querySelectorAll('.main-tab-content').forEach(tab => {
                tab.classList.remove('active');
            });

            // Remove active from all buttons
            document.querySelectorAll('.main-tab-button').forEach(btn => {
                btn.classList.remove('active');
            });

            // Show selected tab
            const selectedTab = document.getElementById(tabName + 'Tab');
            if (selectedTab) {
                selectedTab.classList.add('active');
            } else {
                console.error(`Tab element not found: ${tabName}Tab`);
                return;
            }

            // Activate clicked button and apply per-tab accent colour
            const targetButton = event
                ? (event.target.closest('.main-tab-button') || event.currentTarget)
                : document.querySelector(`.main-tab-button[onclick*="${tabName}"]`);
            if (targetButton) {
                targetButton.classList.add('active');
                const accent = targetButton.getAttribute('data-accent') || '#667eea';
                if (selectedTab) selectedTab.style.setProperty('--tab-accent', accent);
            }
        } catch (error) {
            console.error('Error switching main tabs:', error);
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TabManager;
}
