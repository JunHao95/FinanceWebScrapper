// ===========================
// API Communication Module
// ===========================

const API = {
    /**
     * Scrape stock data
     */
    async scrapeStocks(requestBody) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout

        try {
            const response = await fetch('/api/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server error (${response.status}): ${errorText}`);
            }

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`Expected JSON response but got: ${text.substring(0, 100)}`);
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timed out after 2 minutes. Try with fewer tickers or simpler analysis.');
            }
            throw error;
        }
    },

    /**
     * Send email report
     */
    async sendEmail(emailData) {
        const response = await fetch('/api/send-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(emailData)
        });

        return await response.json();
    },

    /**
     * Calculate option price
     */
    async calculateOptionPrice(params) {
        const response = await fetch('/api/option_pricing', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        return await response.json();
    },

    /**
     * Calculate implied volatility
     */
    async calculateImpliedVolatility(params) {
        const response = await fetch('/api/implied_volatility', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        return await response.json();
    },

    /**
     * Calculate Greeks
     */
    async calculateGreeks(params) {
        const response = await fetch('/api/greeks', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        return await response.json();
    },

    /**
     * Calculate model comparison
     */
    async calculateModelComparison(params) {
        const response = await fetch('/api/model_comparison', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        return await response.json();
    },

    /**
     * Build volatility surface
     */
    async buildVolatilitySurface(params) {
        const response = await fetch('/api/volatility_surface', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        return await response.json();
    },

    /**
     * Get ATM term structure
     */
    async getATMTermStructure(params) {
        const response = await fetch('/api/atm_term_structure', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        return await response.json();
    },

    /**
     * Health check for keep-alive
     */
    async healthCheck() {
        const response = await fetch('/health', {
            method: 'GET',
            headers: {
                'Cache-Control': 'no-cache'
            }
        });
        
        return response.ok;
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
}
