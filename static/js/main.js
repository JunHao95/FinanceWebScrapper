// ===========================
// Main Application Entry Point
// ===========================

// Make FormManager accessible globally for inline event handlers
window.FormManager = FormManager;
window.TabManager = TabManager;
window.Utils = Utils;
window.AppState = AppState;

/**
 * Initialize application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize form event listeners
    FormManager.initEventListeners();
    
    // Initialize stock scraper
    StockScraper.init();
    
    // Initialize options pricing
    OptionsPricing.init();
    
    // Initialize volatility surface
    VolatilitySurface.init();
    
    // Initialize keep-alive
    KeepAlive.start();
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    KeepAlive.stop();
});

// Pause keep-alive when tab is hidden
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        KeepAlive.pause();
    } else {
        KeepAlive.resume();
    }
});

// Export global functions for inline event handlers
window.switchTab = (tabName) => TabManager.switchTab(tabName);
window.switchMainTab = (tabName, event) => TabManager.switchMainTab(tabName, event);
window.clearForm = () => FormManager.clearForm();
window.toggleAllocationSection = () => FormManager.toggleAllocationSection();
window.calculateAllocationTotal = () => FormManager.calculateAllocationTotal();
window.sendEmail = (event) => StockScraper.sendEmail(event);

// Options pricing global functions
window.toggleCalculatorType = () => OptionsPricing.toggleCalculatorType();
window.calculateOptionPrice = () => OptionsPricing.calculateOptionPrice();
window.calculateImpliedVolatility = () => OptionsPricing.calculateImpliedVolatility();
window.calculateGreeks = () => OptionsPricing.calculateGreeks();
window.calculateModelComparison = () => OptionsPricing.calculateModelComparison();

// Volatility surface global functions
window.buildVolatilitySurface = () => VolatilitySurface.buildSurface();
window.showATMTermStructure = () => VolatilitySurface.showATMTermStructure();
