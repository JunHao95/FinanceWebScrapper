// ===========================
// Keep Alive Module
// ===========================

const KeepAlive = {
    intervalId: null,
    checkInterval: 14 * 60 * 1000, // 14 minutes

    /**
     * Start keep-alive mechanism
     */
    start() {
        console.log('Starting keep-alive mechanism...');
        this.pingServer(); // Immediate first ping
        this.intervalId = setInterval(() => {
            if (!AppState.keepAlive.paused) {
                this.pingServer();
            }
        }, this.checkInterval);
    },

    /**
     * Stop keep-alive mechanism
     */
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            console.log('Keep-alive stopped');
        }
    },

    /**
     * Pause keep-alive pings
     */
    pause() {
        AppState.keepAlive.paused = true;
        console.log('Keep-alive paused');
    },

    /**
     * Resume keep-alive pings
     */
    resume() {
        AppState.keepAlive.paused = false;
        console.log('Keep-alive resumed');
    },

    /**
     * Ping the server to keep it alive
     */
    async pingServer() {
        if (AppState.keepAlive.paused) {
            return;
        }

        const now = Date.now();
        
        // Rate limiting: don't ping more than once per minute
        if (now - AppState.keepAlive.lastPing < 60000) {
            console.log('Skipping ping (rate limited)');
            return;
        }

        try {
            const startTime = Date.now();
            const data = await API.healthCheck();
            const responseTime = Date.now() - startTime;
            
            AppState.keepAlive.lastPing = now;
            AppState.keepAlive.failedPings = 0;
            
            console.log(`Keep-alive ping successful (${responseTime}ms)`, data);
        } catch (error) {
            AppState.keepAlive.failedPings++;
            console.error(`Keep-alive ping failed (attempt ${AppState.keepAlive.failedPings}):`, error);
            
            // Stop trying after 3 consecutive failures
            if (AppState.keepAlive.failedPings >= 3) {
                console.warn('Multiple keep-alive failures detected. Pausing keep-alive mechanism.');
                this.pause();
            }
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeepAlive;
}
