// ===========================
// Utility Functions
// ===========================

const Utils = {
    /**
     * Format display values
     */
    formatValue(value) {
        if (value === null || value === undefined) return '--';
        if (typeof value === 'string' && value.toLowerCase().includes('bullish')) {
            return `<span class="badge badge-success">${value}</span>`;
        }
        if (typeof value === 'string' && value.toLowerCase().includes('bearish')) {
            return `<span class="badge badge-danger">${value}</span>`;
        }
        if (typeof value === 'string' && value.toLowerCase().includes('positive')) {
            return `<span class="badge badge-success">${value}</span>`;
        }
        if (typeof value === 'string' && value.toLowerCase().includes('negative')) {
            return `<span class="badge badge-danger">${value}</span>`;
        }
        return value;
    },

    /**
     * Show alert message
     */
    showAlert(message, type) {
        const alertContainer = document.getElementById('alertContainer');
        const alertClass = type === 'success' ? 'alert-success' : type === 'error' ? 'alert-error' : 'alert-info';
        
        alertContainer.innerHTML = `<div class="alert ${alertClass}">${message}</div>`;
        
        // Auto-hide success and info alerts after 5 seconds
        if (type !== 'error') {
            setTimeout(() => this.hideAlert(), 5000);
        }
    },

    /**
     * Hide alert message
     */
    hideAlert() {
        document.getElementById('alertContainer').innerHTML = '';
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
}
