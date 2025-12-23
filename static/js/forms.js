// ===========================
// Form Handlers and Portfolio Management
// ===========================

const FormManager = {
    /**
     * Parse tickers from input string (helper method)
     * @param {string} tickersInput - Comma-separated ticker string
     * @returns {string[]} Array of uppercase, trimmed ticker symbols
     */
    parseTickersInput(tickersInput) {
        if (!tickersInput || typeof tickersInput !== 'string') {
            return [];
        }
        return tickersInput
            .split(',')
            .map(t => t.trim().toUpperCase())
            .filter(t => t.length > 0);
    },
    /**
     * Toggle portfolio allocation section
     */
    toggleAllocationSection() {
        const checkbox = document.getElementById('customAllocation');
        const section = document.getElementById('allocationSection');
        
        if (!checkbox || !section) {
            console.error('Required DOM elements not found: customAllocation or allocationSection');
            return;
        }
        
        section.style.display = checkbox.checked ? 'block' : 'none';
        
        if (checkbox.checked) {
            this.updateAllocationInputs();
        }
    },

    /**
     * Update allocation inputs based on current tickers
     */
    updateAllocationInputs() {
        const tickersInputElement = document.getElementById('tickers');
        const container = document.getElementById('allocationInputs');
        
        if (!tickersInputElement || !container) {
            console.error('Required DOM elements not found: tickers or allocationInputs');
            return;
        }
        
        const tickers = this.parseTickersInput(tickersInputElement.value);
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
                    class="allocation-input"
                >
            `;
            
            container.appendChild(row);
            
            // Attach event listener instead of inline handler
            const input = row.querySelector('input');
            if (input) {
                input.addEventListener('input', () => this.calculateAllocationTotal());
            }
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
        if (!totalDiv) {
            console.error('Required DOM element not found: allocationTotal');
            return;
        }
        
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
        const customAllocationCheckbox = document.getElementById('customAllocation');
        if (!customAllocationCheckbox || !customAllocationCheckbox.checked) {
            return null;
        }
        
        const tickersInputElement = document.getElementById('tickers');
        if (!tickersInputElement) {
            console.error('Required DOM element not found: tickers');
            return null;
        }
        
        const tickers = this.parseTickersInput(tickersInputElement.value);
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
        const scrapeForm = document.getElementById('scrapeForm');
        const sourceAll = document.getElementById('source-all');
        const resultsSection = document.getElementById('resultsSection');
        
        if (!scrapeForm || !sourceAll || !resultsSection) {
            console.error('Required DOM elements not found for form clearing');
            return;
        }
        
        scrapeForm.reset();
        sourceAll.checked = true;
        resultsSection.classList.remove('active');
        
        // Verify global dependencies exist before accessing
        if (typeof AppState !== 'undefined') {
            AppState.currentData = null;
            AppState.currentCnnData = null;
            AppState.currentTickers = [];
            AppState.currentAnalytics = {};
        }
        
        if (typeof Utils !== 'undefined' && typeof Utils.hideAlert === 'function') {
            Utils.hideAlert();
        }
    },

    /**
     * Initialize event listeners
     */
    initEventListeners() {
        const tickersInput = document.getElementById('tickers');
        const customAllocationCheckbox = document.getElementById('customAllocation');
        const sourceAllCheckbox = document.getElementById('source-all');
        
        // Update allocation inputs when tickers change
        if (tickersInput && customAllocationCheckbox) {
            tickersInput.addEventListener('input', () => {
                if (customAllocationCheckbox.checked) {
                    this.updateAllocationInputs();
                }
            });
        }

        // Handle source checkboxes
        if (sourceAllCheckbox) {
            sourceAllCheckbox.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('.checkbox-item input[type="checkbox"]:not(#source-all)');
                checkboxes.forEach(cb => cb.checked = false);
            });
        }

        const otherCheckboxes = document.querySelectorAll('.checkbox-item input[type="checkbox"]:not(#source-all)');
        if (otherCheckboxes.length > 0 && sourceAllCheckbox) {
            otherCheckboxes.forEach(cb => {
                cb.addEventListener('change', function() {
                    if (this.checked) {
                        sourceAllCheckbox.checked = false;
                    }
                });
            });
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FormManager;
}
