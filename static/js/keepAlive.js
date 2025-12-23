// ===========================
// Keep Alive Module
// ===========================

const KeepAlive = {
    intervalId: null,
    checkInterval: 14 * 60 * 1000, // 14 minutes
    recoveryIntervalId: null,
    recoveryCheckInterval: 5 * 60 * 1000, // 5 minutes for recovery attempts

    /**
     * Validate required dependencies
     */
    validateDependencies() {
        if (typeof API === 'undefined' || typeof API.healthCheck !== 'function') {
            console.error('Required dependency not found: API.healthCheck');
            return false;
        }
        if (typeof AppState === 'undefined' || !AppState.keepAlive) {
            console.error('Required dependency not found: AppState.keepAlive');
            return false;
        }
        return true;
    },

    /**
     * Start keep-alive mechanism
     */
    start() {
        if (!this.validateDependencies()) {
            console.error('Cannot start keep-alive: missing dependencies');
            return;
        }

        // Prevent multiple intervals from being created
        if (this.intervalId) {
            console.warn('Keep-alive is already running. Stopping existing interval first.');
            this.stop();
        }

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
        if (this.recoveryIntervalId) {
            clearInterval(this.recoveryIntervalId);
            this.recoveryIntervalId = null;
            console.log('Recovery mechanism stopped');
        }
    },

    /**
     * Pause keep-alive pings
     */
    pause() {
        if (!this.validateDependencies()) {
            return;
        }
        AppState.keepAlive.paused = true;
        console.log('Keep-alive paused');
    },

    /**
     * Resume keep-alive pings
     */
    resume() {
        if (!this.validateDependencies()) {
            return;
        }
        AppState.keepAlive.paused = false;
        console.log('Keep-alive resumed');
        
        // Stop recovery mechanism if it was running
        if (this.recoveryIntervalId) {
            clearInterval(this.recoveryIntervalId);
            this.recoveryIntervalId = null;
        }
    },

    /**
     * Ping the server to keep it alive
     */
    async pingServer() {
        if (!this.validateDependencies()) {
            return;
        }

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
            
            // If we were in recovery mode, resume normal operation
            if (this.recoveryIntervalId) {
                console.log('Server recovered! Resuming normal keep-alive operation.');
                this.resume();
            }
        } catch (error) {
            AppState.keepAlive.failedPings++;
            console.error(`Keep-alive ping failed (attempt ${AppState.keepAlive.failedPings}):`, error);
            
            // Stop trying after 3 consecutive failures and start recovery mechanism
            if (AppState.keepAlive.failedPings >= 3) {
                console.warn('Multiple keep-alive failures detected. Starting recovery mechanism.');
                this.startRecovery();
            }
        }
    },

    /**
     * Start automatic recovery mechanism
     * Attempts to reconnect every 5 minutes after failures
     */
    startRecovery() {
        if (!this.validateDependencies()) {
            return;
        }

        // Pause normal keep-alive
        this.pause();
        
        // Prevent multiple recovery intervals
        if (this.recoveryIntervalId) {
            console.log('Recovery mechanism already running');
            return;
        }
        
        console.log('Starting automatic recovery mechanism (checking every 5 minutes)...');
        
        // Try to recover every 5 minutes
        this.recoveryIntervalId = setInterval(async () => {
            console.log('Attempting automatic recovery ping...');
            
            try {
                const data = await API.healthCheck();
                console.log('Recovery ping successful! Server is back online.', data);
                
                // Reset failure count and resume normal operation
                AppState.keepAlive.failedPings = 0;
                AppState.keepAlive.lastPing = Date.now();
                this.resume();
            } catch (error) {
                console.warn('Recovery ping failed. Will retry in 5 minutes.', error);
            }
        }, this.recoveryCheckInterval);
    }
};

// Export for browser environment
window.KeepAlive = KeepAlive;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeepAlive;
}
