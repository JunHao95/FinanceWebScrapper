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

        const validTabs = ['stocks', 'analytics'];
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

            // Activate clicked button - improved event handling
            if (event) {
                const targetButton = event.target.closest('.main-tab-button');
                if (targetButton) {
                    targetButton.classList.add('active');
                } else if (event.currentTarget) {
                    event.currentTarget.classList.add('active');
                }
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
