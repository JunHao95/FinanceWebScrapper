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

    parseNumeric(val) {
        if (val === null || val === undefined || val === '' || val === 'N/A' || val === 'N/A%') return null;
        if (typeof val === 'number') return isNaN(val) ? null : val;
        let s = String(val).trim().replace(/,/g, '');
        let cleaned = s.replace(/^\$/, '');
        const multipliers = { 'B': 1e9, 'M': 1e6, 'K': 1e3 };
        const lastChar = cleaned.slice(-1).toUpperCase();
        if (multipliers[lastChar]) {
            const n = parseFloat(cleaned.slice(0, -1));
            return isNaN(n) ? null : n * multipliers[lastChar];
        }
        cleaned = cleaned.replace(/%$/, '');
        const n = parseFloat(cleaned);
        return isNaN(n) ? null : n;
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
    },

    colorCodeMetric: function(key, value) {
        if (value === null || value === undefined || isNaN(value)) return '';
        var k = key.toLowerCase();
        var rules = [
            { match: ['p/e ratio', 'forward p/e'],
              green: function(v) { return v < 15; }, red: function(v) { return v > 30; } },
            { match: ['p/b ratio'],
              green: function(v) { return v < 1.5; }, red: function(v) { return v > 4; } },
            { match: ['p/s ratio'],
              green: function(v) { return v < 2; }, red: function(v) { return v > 8; } },
            { match: ['peg ratio'],
              green: function(v) { return v < 1; }, red: function(v) { return v > 2; } },
            { match: ['ev/ebitda'],
              green: function(v) { return v < 10; }, red: function(v) { return v > 25; } },
            { match: ['roe'],
              green: function(v) { return v > 15; }, red: function(v) { return v < 0; } },
            { match: ['roa'],
              green: function(v) { return v > 5; }, red: function(v) { return v < 0; } },
            { match: ['roic'],
              green: function(v) { return v > 10; }, red: function(v) { return v < 0; } },
            { match: ['profit margin'],
              green: function(v) { return v > 10; }, red: function(v) { return v < 0; } },
            { match: ['operating margin'],
              green: function(v) { return v > 10; }, red: function(v) { return v < 0; } },
            { match: ['debt/equity', 'debt to equity'],
              green: function(v) { return v < 0.5; }, red: function(v) { return v > 2; } },
            { match: ['current ratio'],
              green: function(v) { return v > 2; }, red: function(v) { return v < 1; } }
        ];
        for (var i = 0; i < rules.length; i++) {
            var r = rules[i];
            if (r.match.some(function(m) { return k.indexOf(m) !== -1; })) {
                if (r.green(value)) return 'metric-value-good';
                if (r.red(value))   return 'metric-value-bad';
                return '';
            }
        }
        return '';
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
}
