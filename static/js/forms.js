// ===========================
// Form Handlers and Portfolio Management
// ===========================

const FormManager = {
    _allocationMode: 'percent',  // 'percent' | 'value'

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
     * Switch allocation mode between 'percent' and 'value'
     */
    switchAllocationMode(mode) {
        this._allocationMode = mode;
        document.getElementById('modePercentBtn').classList.toggle('active', mode === 'percent');
        document.getElementById('modeValueBtn').classList.toggle('active', mode === 'value');
        const currSel = document.getElementById('currencySelect');
        if (currSel) currSel.style.display = mode === 'value' ? 'inline-block' : 'none';
        const hint = document.getElementById('allocationHint');
        if (hint) hint.textContent = mode === 'percent'
            ? 'Enter the percentage allocation for each ticker (total should equal 100%). Leave blank for equal weights.'
            : 'Enter the total value held per ticker. Leave blank for equal weights.';
        this.updateAllocationInputs();
    },

    /**
     * Auto-show/hide allocation section based on ticker count
     */
    syncAllocationSection() {
        const tickers = this.parseTickersInput(document.getElementById('tickers').value);
        const section = document.getElementById('allocationSection');
        if (!section) return;
        if (tickers.length >= 2) {
            section.style.display = 'block';
            this.updateAllocationInputs();
        } else {
            section.style.display = 'none';
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

            if (this._allocationMode === 'value') {
                row.innerHTML = `
                    <label for="alloc-${ticker}">${ticker}:</label>
                    <input type="number" id="alloc-${ticker}" name="alloc-${ticker}"
                           placeholder="e.g., 10000" min="0" step="1" class="allocation-input">
                    <span id="alloc-pct-${ticker}" class="allocation-pct-label"></span>
                `;
            } else {
                row.innerHTML = `
                    <label for="alloc-${ticker}">${ticker}:</label>
                    <input type="number" id="alloc-${ticker}" name="alloc-${ticker}"
                           placeholder="e.g., 25" min="0" max="100" step="0.1" class="allocation-input">
                `;
            }

            container.appendChild(row);

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
        const totalDiv = document.getElementById('allocationTotal');
        if (!totalDiv) {
            console.error('Required DOM element not found: allocationTotal');
            return;
        }

        if (this._allocationMode === 'value') {
            const tickers = this.parseTickersInput(document.getElementById('tickers').value);
            let totalValue = 0;
            const values = {};
            tickers.forEach(ticker => {
                const input = document.getElementById(`alloc-${ticker}`);
                const v = input ? (parseFloat(input.value) || 0) : 0;
                values[ticker] = v;
                totalValue += v;
            });

            // Update per-ticker percentage labels
            tickers.forEach(ticker => {
                const pctSpan = document.getElementById(`alloc-pct-${ticker}`);
                if (pctSpan) {
                    pctSpan.textContent = totalValue > 0
                        ? `→ ${(values[ticker] / totalValue * 100).toFixed(1)}%`
                        : '';
                }
            });

            const currSel = document.getElementById('currencySelect');
            const currency = currSel ? currSel.value : 'USD';
            totalDiv.textContent = `Total: ${totalValue.toLocaleString()} ${currency}`;
            totalDiv.classList.remove('valid', 'invalid');
            const equalWeightsHint = document.getElementById('equalWeightsHint');
            if (equalWeightsHint) {
                equalWeightsHint.style.display = (totalValue === 0) ? 'block' : 'none';
            }
        } else {
            const inputs = document.querySelectorAll('[id^="alloc-"]');
            let total = 0;
            inputs.forEach(input => {
                total += parseFloat(input.value) || 0;
            });

            totalDiv.textContent = `Total: ${total.toFixed(1)}%`;
            totalDiv.classList.remove('valid', 'invalid');
            const equalWeightsHint = document.getElementById('equalWeightsHint');
            if (equalWeightsHint) equalWeightsHint.style.display = 'none';
            if (Math.abs(total - 100) < 0.1 && total > 0) {
                totalDiv.classList.add('valid');
            } else if (total > 0) {
                totalDiv.classList.add('invalid');
            }
        }
    },

    /**
     * Get portfolio allocation from form
     */
    getPortfolioAllocation() {
        const section = document.getElementById('allocationSection');
        if (!section || section.style.display === 'none') return null;

        const tickers = this.parseTickersInput(document.getElementById('tickers').value);
        const allocations = {};
        let hasAnyAllocation = false;

        if (this._allocationMode === 'value') {
            let totalValue = 0;
            const values = {};
            tickers.forEach(ticker => {
                const input = document.getElementById(`alloc-${ticker}`);
                const v = input ? (parseFloat(input.value) || 0) : 0;
                values[ticker] = v;
                totalValue += v;
            });
            if (totalValue === 0) return null;  // fall back to equal-weight
            tickers.forEach(ticker => {
                if (values[ticker] > 0) {
                    allocations[ticker] = values[ticker] / totalValue;
                    hasAnyAllocation = true;
                }
            });
        } else {
            tickers.forEach(ticker => {
                const input = document.getElementById(`alloc-${ticker}`);
                if (input && input.value) {
                    const v = parseFloat(input.value);
                    if (!isNaN(v) && v > 0) {
                        allocations[ticker] = v / 100;
                        hasAnyAllocation = true;
                    }
                }
            });
        }
        return hasAnyAllocation ? allocations : null;
    },

    /**
     * Initialize chip input widget
     */
    initChipInput() {
        const rawInput = document.getElementById('ticker-input-raw');
        const chipList = document.getElementById('chip-list');
        const hiddenInput = document.getElementById('tickers');
        if (!rawInput || !chipList || !hiddenInput) return;

        const syncHidden = () => {
            hiddenInput.value = Array.from(chipList.querySelectorAll('.chip'))
                .map(c => c.dataset.ticker).join(',');
        };

        const addChip = (value) => {
            const ticker = value.trim().toUpperCase().replace(/[^A-Z0-9.]/g, '');
            if (!ticker) return;
            if (Array.from(chipList.querySelectorAll('.chip')).some(c => c.dataset.ticker === ticker)) return;
            const chip = document.createElement('span');
            chip.className = 'chip';
            chip.dataset.ticker = ticker;
            chip.innerHTML = `<span class="mono">${ticker}</span><button type="button" class="chip-remove" aria-label="Remove ${ticker}">×</button>`;
            chip.querySelector('.chip-remove').addEventListener('click', () => {
                chip.remove(); syncHidden(); this.syncAllocationSection();
            });
            chipList.appendChild(chip);
            syncHidden();
            this.syncAllocationSection();
            rawInput.value = '';
            const tooltip = document.getElementById('ticker-validation-tooltip');
            if (tooltip) { tooltip.textContent = ''; tooltip.className = 'ticker-tooltip'; }
        };

        rawInput.addEventListener('keydown', (e) => {
            if (e.key === ',' || e.key === 'Enter') {
                e.preventDefault();
                addChip(rawInput.value);
            } else if (e.key === 'Backspace' && rawInput.value === '') {
                const chips = chipList.querySelectorAll('.chip');
                if (chips.length) { chips[chips.length - 1].remove(); syncHidden(); this.syncAllocationSection(); }
            }
        });

        rawInput.addEventListener('paste', () => {
            setTimeout(() => {
                if (rawInput.value.includes(',')) {
                    rawInput.value.split(',').forEach(t => addChip(t));
                    rawInput.value = '';
                }
            }, 10);
        });

        // Popular ticker badges
        document.querySelectorAll('.ticker-badge').forEach(btn => {
            btn.addEventListener('click', () => addChip(btn.dataset.ticker));
        });

        // Live validation — debounced 300 ms
        let _valTimer = null;
        rawInput.addEventListener('input', () => {
            clearTimeout(_valTimer);
            const tooltip = document.getElementById('ticker-validation-tooltip');
            if (!tooltip) return;
            const sym = rawInput.value.trim().toUpperCase();
            if (!sym) { tooltip.textContent = ''; tooltip.className = 'ticker-tooltip'; return; }
            _valTimer = setTimeout(async () => {
                try {
                    const res = await fetch(`/api/validate_ticker?symbol=${encodeURIComponent(sym)}`);
                    if (!res.ok) return;
                    const data = await res.json();
                    tooltip.textContent = data.valid ? `✓ ${data.name}` : '✗ Unknown symbol';
                    tooltip.className = `ticker-tooltip ${data.valid ? 'valid' : 'invalid'}`;
                } catch (_) { /* network error — stay silent */ }
            }, 300);
        });

        this._addChip = addChip;
    },

    /**
     * Toggle settings drawer open/closed
     */
    toggleSettingsDrawer() {
        const drawer = document.getElementById('settings-drawer');
        const backdrop = document.getElementById('drawer-backdrop');
        if (!drawer || !backdrop) return;
        const opening = !drawer.classList.contains('drawer-open');
        drawer.classList.toggle('drawer-open', opening);
        backdrop.classList.toggle('active', opening);
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
        document.body.classList.remove('results-loaded');

        // Clear chip UI
        const chipList = document.getElementById('chip-list');
        if (chipList) chipList.innerHTML = '';
        const rawInput = document.getElementById('ticker-input-raw');
        if (rawInput) rawInput.value = '';
        const tooltip = document.getElementById('ticker-validation-tooltip');
        if (tooltip) { tooltip.textContent = ''; tooltip.className = 'ticker-tooltip'; }

        if (typeof AppState !== 'undefined') {
            AppState.currentData = null;
            AppState.currentCnnData = null;
            AppState.currentTickers = [];
            AppState.currentAnalytics = {};
        }

        if (typeof Utils !== 'undefined' && typeof Utils.hideAlert === 'function') {
            Utils.hideAlert();
        }

        this.syncAllocationSection();
    },

    /**
     * Initialize event listeners
     */
    initEventListeners() {
        const tickersInput = document.getElementById('tickers');
        const sourceAllCheckbox = document.getElementById('source-all');

        // Auto-show/hide allocation section when tickers change
        if (tickersInput) {
            tickersInput.addEventListener('input', () => {
                this.syncAllocationSection();
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

        // Drawer backdrop + ESC key close
        const backdrop = document.getElementById('drawer-backdrop');
        if (backdrop) backdrop.addEventListener('click', () => this.toggleSettingsDrawer());
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const drawer = document.getElementById('settings-drawer');
                if (drawer && drawer.classList.contains('drawer-open')) this.toggleSettingsDrawer();
            }
        });
        const drawerClose = document.getElementById('drawer-close-btn');
        if (drawerClose) drawerClose.addEventListener('click', () => this.toggleSettingsDrawer());
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FormManager;
}
