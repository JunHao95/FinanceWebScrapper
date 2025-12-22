// ===========================
// Form Handlers and Portfolio Management
// ===========================

const FormManager = {
    /**
     * Toggle portfolio allocation section
     */
    toggleAllocationSection() {
        const checkbox = document.getElementById('customAllocation');
        const section = document.getElementById('allocationSection');
        section.style.display = checkbox.checked ? 'block' : 'none';
        
        if (checkbox.checked) {
            this.updateAllocationInputs();
        }
    },

    /**
     * Update allocation inputs based on current tickers
     */
    updateAllocationInputs() {
        const tickersInput = document.getElementById('tickers').value;
        const tickers = tickersInput
            .split(',')
            .map(t => t.trim().toUpperCase())
            .filter(t => t.length > 0);
        
        const container = document.getElementById('allocationInputs');
        container.innerHTML = '';
        
        if (tickers.length === 0) {
            container.innerHTML = '<p style="color: #666;">Enter tickers first to set allocations</p>';
            return;
        }
        
        tickers.forEach(ticker => {
            const row = document.createElement('div');
            row.className = 'allocation-input-row';
            
            row.innerHTML = `
                <label for="alloc-${ticker}">${ticker}:</label>
                <input 
                    type="number" 
                    id="alloc-${ticker}" 
                    name="alloc-${ticker}"
                    placeholder="e.g., 25"
                    min="0"
                    max="100"
                    step="0.1"
                    oninput="FormManager.calculateAllocationTotal()"
                >
            `;
            
            container.appendChild(row);
        });
        
        this.calculateAllocationTotal();
    },

    /**
     * Calculate and display total allocation
     */
    calculateAllocationTotal() {
        const inputs = document.querySelectorAll('[id^="alloc-"]');
        let total = 0;
        
        inputs.forEach(input => {
            const value = parseFloat(input.value) || 0;
            total += value;
        });
        
        const totalDiv = document.getElementById('allocationTotal');
        totalDiv.textContent = `Total: ${total.toFixed(1)}%`;
        
        // Color code based on validity
        totalDiv.classList.remove('valid', 'invalid');
        if (Math.abs(total - 100) < 0.1 && total > 0) {
            totalDiv.classList.add('valid');
        } else if (total > 0) {
            totalDiv.classList.add('invalid');
        }
    },

    /**
     * Get portfolio allocation from form
     */
    getPortfolioAllocation() {
        const customAllocation = document.getElementById('customAllocation').checked;
        if (!customAllocation) {
            return null;
        }
        
        const tickersInput = document.getElementById('tickers').value;
        const tickers = tickersInput
            .split(',')
            .map(t => t.trim().toUpperCase())
            .filter(t => t.length > 0);
        
        const allocations = {};
        let hasAnyAllocation = false;
        
        tickers.forEach(ticker => {
            const input = document.getElementById(`alloc-${ticker}`);
            if (input && input.value) {
                const value = parseFloat(input.value);
                if (!isNaN(value) && value > 0) {
                    allocations[ticker] = value / 100;
                    hasAnyAllocation = true;
                }
            }
        });
        
        return hasAnyAllocation ? allocations : null;
    },

    /**
     * Clear form
     */
    clearForm() {
        document.getElementById('scrapeForm').reset();
        document.getElementById('source-all').checked = true;
        document.getElementById('resultsSection').classList.remove('active');
        AppState.currentData = null;
        AppState.currentCnnData = null;
        AppState.currentTickers = [];
        AppState.currentAnalytics = {};
        Utils.hideAlert();
    },

    /**
     * Initialize event listeners
     */
    initEventListeners() {
        // Update allocation inputs when tickers change
        document.getElementById('tickers').addEventListener('input', () => {
            const customAllocation = document.getElementById('customAllocation').checked;
            if (customAllocation) {
                this.updateAllocationInputs();
            }
        });

        // Handle source checkboxes
        document.getElementById('source-all').addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.checkbox-item input[type="checkbox"]:not(#source-all)');
            checkboxes.forEach(cb => cb.checked = false);
        });

        document.querySelectorAll('.checkbox-item input[type="checkbox"]:not(#source-all)').forEach(cb => {
            cb.addEventListener('change', function() {
                if (this.checked) {
                    document.getElementById('source-all').checked = false;
                }
            });
        });
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FormManager;
}
