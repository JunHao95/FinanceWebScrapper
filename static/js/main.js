// ===========================
// Main Application Entry Point
// ===========================

// Module Loading Strategy:
// All modules are loaded via <script> tags in index.html in dependency order:
// 1. state.js - Global state management (no dependencies)
// 2. utils.js - Utility functions (no dependencies)
// 3. tabs.js - Tab management (depends on: AppState)
// 4. forms.js - Form handlers (depends on: AppState, Utils)
// 5. api.js - API communication (no dependencies)
// 6. displayManager.js - Display rendering (depends on: Utils, AnalyticsRenderer)
// 7. analyticsRenderer.js - Analytics visualization (no dependencies)
// 8. optionsDisplay.js - Options display (no dependencies)
// 9. keepAlive.js - Keep-alive mechanism (depends on: API, AppState)
// 10. stockScraper.js - Stock scraping logic (depends on: API, AppState, Utils, DisplayManager, TabManager, FormManager)
// 11. optionsPricing.js - Options pricing (depends on: API, AppState, OptionsDisplay)
// 12. volatilitySurface.js - Volatility surface (depends on: API, AppState)
// 13. main.js - Application initialization (depends on: all modules)

/**
 * Required modules for application initialization
 */
const REQUIRED_MODULES = [
    { name: 'AppState', object: 'AppState' },
    { name: 'Utils', object: 'Utils' },
    { name: 'TabManager', object: 'TabManager' },
    { name: 'FormManager', object: 'FormManager' },
    { name: 'API', object: 'API' },
    { name: 'DisplayManager', object: 'DisplayManager' },
    { name: 'AnalyticsRenderer', object: 'AnalyticsRenderer' },
    { name: 'OptionsDisplay', object: 'OptionsDisplay' },
    { name: 'KeepAlive', object: 'KeepAlive' },
    { name: 'StockScraper', object: 'StockScraper' },
    { name: 'OptionsPricing', object: 'OptionsPricing' },
    { name: 'VolatilitySurface', object: 'VolatilitySurface' }
];

/**
 * Verify all required modules are loaded
 * @returns {Object} { success: boolean, missing: string[] }
 */
function verifyModuleLoading() {
    const missing = [];
    
    for (const module of REQUIRED_MODULES) {
        if (typeof window[module.object] === 'undefined') {
            missing.push(module.name);
            console.error(`Required module not loaded: ${module.name}`);
        }
    }
    
    if (missing.length > 0) {
        console.error('Module loading verification failed. Missing modules:', missing);
        return { success: false, missing };
    }
    
    console.log('All required modules loaded successfully');
    return { success: true, missing: [] };
}

/**
 * Initialize a module with error handling
 * @param {string} moduleName - Name of the module for logging
 * @param {Function} initFunction - Initialization function to call
 * @returns {boolean} Success status
 */
function safeInitialize(moduleName, initFunction) {
    try {
        if (typeof initFunction !== 'function') {
            console.error(`${moduleName}: initialization function not found or not a function`);
            return false;
        }
        
        initFunction();
        console.log(`${moduleName} initialized successfully`);
        return true;
    } catch (error) {
        console.error(`Failed to initialize ${moduleName}:`, error);
        return false;
    }
}

// Make modules accessible globally for inline event handlers and cross-module communication
window.FormManager = FormManager;
window.TabManager = TabManager;
window.Utils = Utils;
window.AppState = AppState;

/**
 * Initialize application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, starting application initialization...');
    
    // Step 1: Verify all modules are loaded
    const moduleCheck = verifyModuleLoading();
    if (!moduleCheck.success) {
        console.error('Cannot initialize application: missing required modules');
        alert(`Application initialization failed. Missing modules: ${moduleCheck.missing.join(', ')}. Please refresh the page.`);
        return;
    }
    
    // Step 2: Initialize modules in dependency order with error handling
    const initResults = {
        FormManager: false,
        StockScraper: false,
        OptionsPricing: false,
        VolatilitySurface: false,
        KeepAlive: false
    };
    
    // Initialize form event listeners (depends on: AppState, Utils)
    if (typeof FormManager !== 'undefined' && typeof FormManager.initEventListeners === 'function') {
        initResults.FormManager = safeInitialize('FormManager', FormManager.initEventListeners.bind(FormManager));
    } else {
        console.error('FormManager.initEventListeners not available');
    }
    
    // Initialize stock scraper (depends on: API, AppState, Utils, DisplayManager, TabManager, FormManager)
    if (typeof StockScraper !== 'undefined' && typeof StockScraper.init === 'function') {
        initResults.StockScraper = safeInitialize('StockScraper', StockScraper.init.bind(StockScraper));
    } else {
        console.error('StockScraper.init not available');
    }
    
    // Initialize options pricing (depends on: API, AppState, OptionsDisplay)
    if (typeof OptionsPricing !== 'undefined' && typeof OptionsPricing.init === 'function') {
        initResults.OptionsPricing = safeInitialize('OptionsPricing', OptionsPricing.init.bind(OptionsPricing));
    } else {
        console.error('OptionsPricing.init not available');
    }
    
    // Initialize volatility surface (depends on: API, AppState)
    if (typeof VolatilitySurface !== 'undefined' && typeof VolatilitySurface.init === 'function') {
        initResults.VolatilitySurface = safeInitialize('VolatilitySurface', VolatilitySurface.init.bind(VolatilitySurface));
    } else {
        console.error('VolatilitySurface.init not available');
    }
    
    // Initialize keep-alive (depends on: API, AppState)
    if (typeof KeepAlive !== 'undefined' && typeof KeepAlive.start === 'function') {
        initResults.KeepAlive = safeInitialize('KeepAlive', KeepAlive.start.bind(KeepAlive));
    } else {
        console.error('KeepAlive.start not available');
    }
    
    // Step 3: Report initialization status
    const failedModules = Object.entries(initResults)
        .filter(([_, success]) => !success)
        .map(([name, _]) => name);
    
    if (failedModules.length > 0) {
        console.warn('Some modules failed to initialize:', failedModules);
        console.warn('Application may have limited functionality');
    } else {
        console.log('All modules initialized successfully. Application ready.');
    }
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    try {
        if (typeof KeepAlive !== 'undefined' && typeof KeepAlive.stop === 'function') {
            KeepAlive.stop();
        }
    } catch (error) {
        console.error('Error during cleanup on page unload:', error);
    }
});

// Pause keep-alive when tab is hidden
document.addEventListener('visibilitychange', function() {
    try {
        if (typeof KeepAlive === 'undefined') {
            return;
        }
        
        if (document.hidden) {
            if (typeof KeepAlive.pause === 'function') {
                KeepAlive.pause();
            }
        } else {
            if (typeof KeepAlive.resume === 'function') {
                KeepAlive.resume();
            }
        }
    } catch (error) {
        console.error('Error handling visibility change:', error);
    }
});

// Export global functions for inline event handlers with error handling
window.switchTab = (tabName) => {
    try {
        if (typeof TabManager !== 'undefined' && typeof TabManager.switchTab === 'function') {
            return TabManager.switchTab(tabName);
        }
        console.error('TabManager.switchTab not available');
    } catch (error) {
        console.error('Error in switchTab:', error);
    }
};

window.switchMainTab = (tabName, event) => {
    try {
        if (typeof TabManager !== 'undefined' && typeof TabManager.switchMainTab === 'function') {
            return TabManager.switchMainTab(tabName, event);
        }
        console.error('TabManager.switchMainTab not available');
    } catch (error) {
        console.error('Error in switchMainTab:', error);
    }
};

window.clearForm = () => {
    try {
        if (typeof FormManager !== 'undefined' && typeof FormManager.clearForm === 'function') {
            return FormManager.clearForm();
        }
        console.error('FormManager.clearForm not available');
    } catch (error) {
        console.error('Error in clearForm:', error);
    }
};

window.toggleAllocationSection = () => {
    try {
        if (typeof FormManager !== 'undefined' && typeof FormManager.toggleAllocationSection === 'function') {
            return FormManager.toggleAllocationSection();
        }
        console.error('FormManager.toggleAllocationSection not available');
    } catch (error) {
        console.error('Error in toggleAllocationSection:', error);
    }
};

window.calculateAllocationTotal = () => {
    try {
        if (typeof FormManager !== 'undefined' && typeof FormManager.calculateAllocationTotal === 'function') {
            return FormManager.calculateAllocationTotal();
        }
        console.error('FormManager.calculateAllocationTotal not available');
    } catch (error) {
        console.error('Error in calculateAllocationTotal:', error);
    }
};

window.sendEmail = (event) => {
    try {
        if (typeof StockScraper !== 'undefined' && typeof StockScraper.sendEmail === 'function') {
            return StockScraper.sendEmail(event);
        }
        console.error('StockScraper.sendEmail not available');
    } catch (error) {
        console.error('Error in sendEmail:', error);
    }
};

// Options pricing global functions with error handling
window.toggleCalculatorType = () => {
    try {
        if (typeof OptionsPricing !== 'undefined' && typeof OptionsPricing.toggleCalculatorType === 'function') {
            return OptionsPricing.toggleCalculatorType();
        }
        console.error('OptionsPricing.toggleCalculatorType not available');
    } catch (error) {
        console.error('Error in toggleCalculatorType:', error);
    }
};

window.calculateOptionPrice = () => {
    try {
        if (typeof OptionsPricing !== 'undefined' && typeof OptionsPricing.calculateOptionPrice === 'function') {
            return OptionsPricing.calculateOptionPrice();
        }
        console.error('OptionsPricing.calculateOptionPrice not available');
    } catch (error) {
        console.error('Error in calculateOptionPrice:', error);
    }
};

window.calculateImpliedVolatility = () => {
    try {
        if (typeof OptionsPricing !== 'undefined' && typeof OptionsPricing.calculateImpliedVolatility === 'function') {
            return OptionsPricing.calculateImpliedVolatility();
        }
        console.error('OptionsPricing.calculateImpliedVolatility not available');
    } catch (error) {
        console.error('Error in calculateImpliedVolatility:', error);
    }
};

window.calculateGreeks = () => {
    try {
        if (typeof OptionsPricing !== 'undefined' && typeof OptionsPricing.calculateGreeks === 'function') {
            return OptionsPricing.calculateGreeks();
        }
        console.error('OptionsPricing.calculateGreeks not available');
    } catch (error) {
        console.error('Error in calculateGreeks:', error);
    }
};

window.calculateModelComparison = () => {
    try {
        if (typeof OptionsPricing !== 'undefined' && typeof OptionsPricing.calculateModelComparison === 'function') {
            return OptionsPricing.calculateModelComparison();
        }
        console.error('OptionsPricing.calculateModelComparison not available');
    } catch (error) {
        console.error('Error in calculateModelComparison:', error);
    }
};

// Volatility surface global functions with error handling
window.buildVolatilitySurface = () => {
    try {
        if (typeof VolatilitySurface !== 'undefined' && typeof VolatilitySurface.buildSurface === 'function') {
            return VolatilitySurface.buildSurface();
        }
        console.error('VolatilitySurface.buildSurface not available');
    } catch (error) {
        console.error('Error in buildVolatilitySurface:', error);
    }
};

window.showATMTermStructure = () => {
    try {
        if (typeof VolatilitySurface !== 'undefined' && typeof VolatilitySurface.showATMTermStructure === 'function') {
            return VolatilitySurface.showATMTermStructure();
        }
        console.error('VolatilitySurface.showATMTermStructure not available');
    } catch (error) {
        console.error('Error in showATMTermStructure:', error);
    }
};
