// ===========================
// Global State Management
// ===========================

const AppState = {
    currentData: null,
    currentCnnData: null,
    currentTickers: [],
    currentAnalytics: {},
    keepAliveInterval: null,
    keepAliveEnabled: true,
    pingCount: 0,
    successCount: 0
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AppState;
}
