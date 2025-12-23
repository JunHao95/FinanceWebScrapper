// ===========================
// Utility Functions
// ===========================

const Utils = {
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
     * Format display values
     */
    formatValue(value) {
        if (value === null || value === undefined) return '--';
        
        // Escape user input to prevent XSS
        const safeValue = this.escapeHtml(value);
        
        if (typeof value === 'string' && value.toLowerCase().includes('bullish')) {
            return `<span class="badge badge-success">${safeValue}</span>`;
        }
        if (typeof value === 'string' && value.toLowerCase().includes('bearish')) {
            return `<span class="badge badge-danger">${safeValue}</span>`;
        }
        if (typeof value === 'string' && value.toLowerCase().includes('positive')) {
            return `<span class="badge badge-success">${safeValue}</span>`;
        }
        if (typeof value === 'string' && value.toLowerCase().includes('negative')) {
            return `<span class="badge badge-danger">${safeValue}</span>`;
        }
        return safeValue;
    },

    /**
     * Show alert message
     */
    showAlert(message, type) {
        const alertContainer = document.getElementById('alertContainer');
        
        // Add null check to prevent runtime errors
        if (!alertContainer) {
            console.error('alertContainer element not found');
            return;
        }

        const alertClass = type === 'success' ? 'alert-success' : type === 'error' ? 'alert-error' : 'alert-info';
        
        // Critical XSS vulnerability fix: HTML-escape the message
        const safeMessage = this.escapeHtml(message);
        
        alertContainer.innerHTML = `<div class="alert ${alertClass}">${safeMessage}</div>`;
        
        // Auto-hide success and info alerts after 5 seconds
        if (type !== 'error') {
            setTimeout(() => this.hideAlert(), 5000);
        }
    },

    /**
     * Hide alert message
     */
    hideAlert() {
        const alertContainer = document.getElementById('alertContainer');
        if (alertContainer) {
            alertContainer.innerHTML = '';
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
}
