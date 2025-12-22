// ===========================
// Options Pricing Module
// ===========================

const OptionsPricing = {
    /**
     * Initialize options pricing
     */
    init() {
        // Event listeners are handled via inline onclick in HTML
    },

    /**
     * Toggle calculator type
     */
    toggleCalculatorType() {
        const calcType = document.getElementById('optionCalcType').value;
        
        // Hide all calculators
        document.getElementById('pricingCalculator').style.display = 'none';
        document.getElementById('impliedVolCalculator').style.display = 'none';
        document.getElementById('greeksCalculator').style.display = 'none';
        document.getElementById('comparisonCalculator').style.display = 'none';
        
        // Show the selected calculator
        if (calcType === 'pricing') {
            document.getElementById('pricingCalculator').style.display = 'block';
        } else if (calcType === 'implied_vol') {
            document.getElementById('impliedVolCalculator').style.display = 'block';
        } else if (calcType === 'greeks') {
            document.getElementById('greeksCalculator').style.display = 'block';
        } else if (calcType === 'comparison') {
            document.getElementById('comparisonCalculator').style.display = 'block';
        }
        
        // Hide results when switching
        document.getElementById('optionResults').style.display = 'none';
    },

    /**
     * Calculate option price
     */
    async calculateOptionPrice() {
        const spot = parseFloat(document.getElementById('optSpot').value);
        const strike = parseFloat(document.getElementById('optStrike').value);
        const maturity = parseFloat(document.getElementById('optMaturity').value);
        const rate = parseFloat(document.getElementById('optRate').value) / 100;
        const volatility = parseFloat(document.getElementById('optVol').value) / 100;
        const optionType = document.getElementById('optType').value;
        const steps = parseInt(document.getElementById('optSteps').value);
        
        const models = [];
        if (document.getElementById('modelBS').checked) models.push('black_scholes');
        if (document.getElementById('modelBinomial').checked) models.push('binomial');
        if (document.getElementById('modelTrinomial').checked) models.push('trinomial');
        
        if (models.length === 0) {
            Utils.showAlert('Please select at least one pricing model', 'error');
            return;
        }
        
        try {
            Utils.showAlert('Calculating option price...', 'info');
            
            const data = await API.calculateOptionPrice({
                spot: spot,
                strike: strike,
                maturity: maturity,
                risk_free_rate: rate,
                volatility: volatility,
                option_type: optionType,
                models: models,
                steps: steps
            });
            
            if (data.success) {
                OptionsDisplay.displayOptionResults(data.results);
                Utils.showAlert('Calculation complete!', 'success');
            } else {
                Utils.showAlert(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            Utils.showAlert('Failed to calculate option price', 'error');
        }
    },

    /**
     * Calculate implied volatility
     */
    async calculateImpliedVolatility() {
        const marketPrice = parseFloat(document.getElementById('ivMarketPrice').value);
        const spot = parseFloat(document.getElementById('ivSpot').value);
        const strike = parseFloat(document.getElementById('ivStrike').value);
        const maturity = parseFloat(document.getElementById('ivMaturity').value);
        const rate = parseFloat(document.getElementById('ivRate').value) / 100;
        const optionType = document.getElementById('ivType').value;
        
        try {
            Utils.showAlert('Extracting implied volatility...', 'info');
            
            const data = await API.calculateImpliedVolatility({
                market_price: marketPrice,
                spot: spot,
                strike: strike,
                maturity: maturity,
                risk_free_rate: rate,
                option_type: optionType
            });
            
            if (data.success) {
                OptionsDisplay.displayImpliedVolResults(data.result);
                Utils.showAlert('Implied volatility extracted!', 'success');
            } else {
                Utils.showAlert(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            Utils.showAlert('Failed to calculate implied volatility', 'error');
        }
    },

    /**
     * Calculate Greeks
     */
    async calculateGreeks() {
        const spot = parseFloat(document.getElementById('greeksSpot').value);
        const strike = parseFloat(document.getElementById('greeksStrike').value);
        const maturity = parseFloat(document.getElementById('greeksMaturity').value);
        const rate = parseFloat(document.getElementById('greeksRate').value) / 100;
        const volatility = parseFloat(document.getElementById('greeksVol').value) / 100;
        const optionType = document.getElementById('greeksType').value;
        
        try {
            const data = await API.calculateGreeks({
                spot: spot,
                strike: strike,
                maturity: maturity,
                risk_free_rate: rate,
                volatility: volatility,
                option_type: optionType
            });
            
            if (data.success) {
                OptionsDisplay.displayGreeksResults(data.greeks);
            } else {
                Utils.showAlert(data.error || 'Failed to calculate Greeks', 'error');
            }
        } catch (error) {
            Utils.showAlert('Error calculating Greeks: ' + error.message, 'error');
        }
    },

    /**
     * Calculate model comparison
     */
    async calculateModelComparison() {
        const spot = parseFloat(document.getElementById('compSpot').value);
        const strike = parseFloat(document.getElementById('compStrike').value);
        const maturity = parseFloat(document.getElementById('compMaturity').value);
        const rate = parseFloat(document.getElementById('compRate').value) / 100;
        const volatility = parseFloat(document.getElementById('compVol').value) / 100;
        const optionType = document.getElementById('compType').value;
        const steps = parseInt(document.getElementById('compSteps').value);
        
        try {
            const data = await API.calculateModelComparison({
                spot: spot,
                strike: strike,
                maturity: maturity,
                risk_free_rate: rate,
                volatility: volatility,
                option_type: optionType,
                steps: steps
            });
            
            if (data.success) {
                OptionsDisplay.displayModelComparisonResults(data.comparison);
            } else {
                Utils.showAlert(data.error || 'Failed to compare models', 'error');
            }
        } catch (error) {
            Utils.showAlert('Error comparing models: ' + error.message, 'error');
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OptionsPricing;
}
