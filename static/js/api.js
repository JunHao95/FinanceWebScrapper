// ===========================
// API Communication Module
// ===========================

const API = {
    /**
     * Scrape stock data
     */
    async scrapeStocks(requestBody) {
        const controller = new AbortController();
        
        // Dynamic timeout based on number of tickers
        // Base: 2 minutes, add 5 seconds per ticker after first 5
        const numTickers = requestBody.tickers?.length || 1;
        const baseTimeout = 120000; // 2 minutes
        const additionalTimeout = Math.max(0, (numTickers - 5)) * 5000; // 5 sec per ticker after 5
        const maxTimeout = 600000; // 10 minutes max
        const timeout = Math.min(baseTimeout + additionalTimeout, maxTimeout);
        
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        console.log(`Setting timeout to ${timeout/1000} seconds for ${numTickers} tickers`);

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
                const minutes = Math.floor(timeout / 60000);
                throw new Error(`Request timed out after ${minutes} minute(s). Try with fewer tickers, disable sentiment analysis, or select fewer sources.`);
            }
            throw error;
        }
    },

    /**
     * Send email report
     */
    async sendEmail(emailData) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

        try {
            const response = await fetch('/api/send-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(emailData),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to send email (${response.status}): ${errorText}`);
            }

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Invalid response format from email service');
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Email request timed out. Please try again.');
            }
            throw error;
        }
    },

    /**
     * Calculate option price
     */
    async calculateOptionPrice(params) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

        try {
            const response = await fetch('/api/option_pricing', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Option pricing failed (${response.status}): ${errorText}`);
            }

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Invalid response format from option pricing service');
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Option pricing calculation timed out');
            }
            throw error;
        }
    },

    /**
     * Calculate implied volatility
     */
    async calculateImpliedVolatility(params) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

        try {
            const response = await fetch('/api/implied_volatility', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Implied volatility calculation failed (${response.status}): ${errorText}`);
            }

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Invalid response format from implied volatility service');
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Implied volatility calculation timed out');
            }
            throw error;
        }
    },

    /**
     * Calculate Greeks
     */
    async calculateGreeks(params) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

        try {
            const response = await fetch('/api/greeks', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Greeks calculation failed (${response.status}): ${errorText}`);
            }

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Invalid response format from Greeks service');
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Greeks calculation timed out');
            }
            throw error;
        }
    },

    /**
     * Calculate model comparison
     */
    async calculateModelComparison(params) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

        try {
            const response = await fetch('/api/model_comparison', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Model comparison failed (${response.status}): ${errorText}`);
            }

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Invalid response format from model comparison service');
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Model comparison timed out');
            }
            throw error;
        }
    },

    /**
     * Build volatility surface
     */
    async buildVolatilitySurface(params) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout for complex calculation

        try {
            const response = await fetch('/api/volatility_surface', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Volatility surface build failed (${response.status}): ${errorText}`);
            }

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Invalid response format from volatility surface service');
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Volatility surface calculation timed out');
            }
            throw error;
        }
    },

    /**
     * Get ATM term structure
     */
    async getATMTermStructure(params) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

        try {
            const response = await fetch('/api/atm_term_structure', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`ATM term structure failed (${response.status}): ${errorText}`);
            }

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Invalid response format from ATM term structure service');
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('ATM term structure calculation timed out');
            }
            throw error;
        }
    },

    /**
     * Health check for keep-alive
     * Returns boolean - true if healthy, false otherwise
     * Does not throw errors to avoid disrupting keep-alive mechanism
     */
    async healthCheck() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

            const response = await fetch('/health', {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache'
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            return response.ok;
        } catch (error) {
            // Gracefully handle errors without throwing
            // Keep-alive should continue even if health check fails
            console.warn('[API] Health check failed:', error.message);
            return false;
        }
    }
};

// Export for browser environment (window global)
window.API = API;

// Note: Module exports commented out as this is browser-only code
// CommonJS/Node.js modules are not used in browser context
