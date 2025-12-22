// ===========================
// Tab Navigation Module
// ===========================

const TabManager = {
    /**
     * Switch between stock details and analytics tabs
     */
    switchTab(tabName) {
        // Remove active class from all tabs and contents
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // Add active class to selected tab and content
        if (tabName === 'stocks') {
            document.getElementById('stocksTab').classList.add('active');
            document.getElementById('stocksTabContent').classList.add('active');
        } else if (tabName === 'analytics') {
            document.getElementById('analyticsTab').classList.add('active');
            document.getElementById('analyticsTabContent').classList.add('active');
        }
    },

    /**
     * Switch between main tabs (Stock Analysis, Options Pricing, Volatility Surface)
     */
    switchMainTab(tabName, event) {
        // Hide all tab contents
        document.querySelectorAll('.main-tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        // Remove active from all buttons
        document.querySelectorAll('.main-tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        // Show selected tab
        document.getElementById(tabName + 'Tab').classList.add('active');
        // Activate clicked button
        if (event && event.target) {
            event.target.classList.add('active');
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TabManager;
}
