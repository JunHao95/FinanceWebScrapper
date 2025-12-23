// ===========================
// Options Pricing Module
// ===========================

const OptionsPricing = {
    /**
     * Validate numeric input to prevent NaN values
     * @param {*} value - Value to validate
     * @param {string} fieldName - Name of field for error message
     * @param {number} min - Minimum allowed value (optional)
     * @param {number} max - Maximum allowed value (optional)
     * @returns {Object} { valid: boolean, value: number, error: string }
     */
    validateNumericInput(value, fieldName, min = null, max = null) {
        const parsed = parseFloat(value);
        
        if (isNaN(parsed) || !isFinite(parsed)) {
            return {
                valid: false,
                value: null,
                error: `${fieldName} must be a valid number`
            };
        }
        
        if (min !== null && parsed < min) {
            return {
                valid: false,
                value: parsed,
                error: `${fieldName} must be at least ${min}`
            };
        }
        
        if (max !== null && parsed > max) {
            return {
                valid: false,
                value: parsed,
                error: `${fieldName} must be at most ${max}`
            };
        }
        
        return { valid: true, value: parsed, error: null };
    },

    /**
     * Safely get DOM element with error logging
     * @param {string} id - Element ID
     * @returns {HTMLElement|null}
     */
    getElement(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.error(`Required DOM element not found: ${id}`);
        }
        return element;
    },

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
        const calcTypeElement = this.getElement('optionCalcType');
        if (!calcTypeElement) return;
        
        const calcType = calcTypeElement.value;
        
        // Get all calculator elements
        const pricingCalc = this.getElement('pricingCalculator');
        const impliedVolCalc = this.getElement('impliedVolCalculator');
        const greeksCalc = this.getElement('greeksCalculator');
        const comparisonCalc = this.getElement('comparisonCalculator');
        const resultsDiv = this.getElement('optionResults');
        
        // Hide all calculators
        if (pricingCalc) pricingCalc.style.display = 'none';
        if (impliedVolCalc) impliedVolCalc.style.display = 'none';
        if (greeksCalc) greeksCalc.style.display = 'none';
        if (comparisonCalc) comparisonCalc.style.display = 'none';
        
        // Show the selected calculator
        if (calcType === 'pricing' && pricingCalc) {
            pricingCalc.style.display = 'block';
        } else if (calcType === 'implied_vol' && impliedVolCalc) {
            impliedVolCalc.style.display = 'block';
        } else if (calcType === 'greeks' && greeksCalc) {
            greeksCalc.style.display = 'block';
        } else if (calcType === 'comparison' && comparisonCalc) {
            comparisonCalc.style.display = 'block';
        }
        
        // Hide results when switching
        if (resultsDiv) {
            resultsDiv.style.display = 'none';
        }
    },

    /**
     * Calculate option price
     */
    async calculateOptionPrice() {
        // Verify Utils dependency
        if (typeof Utils === 'undefined' || typeof Utils.showAlert !== 'function') {
            console.error('Utils dependency not available');
            alert('Error: Required dependencies not loaded');
            return;
        }

        // Get DOM elements with null checks
        const spotElement = this.getElement('optSpot');
        const strikeElement = this.getElement('optStrike');
        const maturityElement = this.getElement('optMaturity');
        const rateElement = this.getElement('optRate');
        const volatilityElement = this.getElement('optVol');
        const optionTypeElement = this.getElement('optType');
        const stepsElement = this.getElement('optSteps');
        
        if (!spotElement || !strikeElement || !maturityElement || !rateElement || 
            !volatilityElement || !optionTypeElement || !stepsElement) {
            Utils.showAlert('Error: Required form elements not found', 'error');
            return;
        }

        // Validate all numeric inputs
        const spotValidation = this.validateNumericInput(spotElement.value, 'Spot Price', 0.01);
        if (!spotValidation.valid) {
            Utils.showAlert(spotValidation.error, 'error');
            return;
        }

        const strikeValidation = this.validateNumericInput(strikeElement.value, 'Strike Price', 0.01);
        if (!strikeValidation.valid) {
            Utils.showAlert(strikeValidation.error, 'error');
            return;
        }

        const maturityValidation = this.validateNumericInput(maturityElement.value, 'Time to Maturity', 0.001, 50);
        if (!maturityValidation.valid) {
            Utils.showAlert(maturityValidation.error, 'error');
            return;
        }

        const rateValidation = this.validateNumericInput(rateElement.value, 'Risk-Free Rate', -20, 100);
        if (!rateValidation.valid) {
            Utils.showAlert(rateValidation.error, 'error');
            return;
        }

        const volatilityValidation = this.validateNumericInput(volatilityElement.value, 'Volatility', 0.1, 500);
        if (!volatilityValidation.valid) {
            Utils.showAlert(volatilityValidation.error, 'error');
            return;
        }

        const stepsValidation = this.validateNumericInput(stepsElement.value, 'Steps', 1, 1000);
        if (!stepsValidation.valid) {
            Utils.showAlert(stepsValidation.error, 'error');
            return;
        }

        const spot = spotValidation.value;
        const strike = strikeValidation.value;
        const maturity = maturityValidation.value;
        const rate = rateValidation.value / 100;
        const volatility = volatilityValidation.value / 100;
        const optionType = optionTypeElement.value;
        const steps = parseInt(stepsValidation.value);
        
        // Get selected models
        const models = [];
        const modelBS = this.getElement('modelBS');
        const modelBinomial = this.getElement('modelBinomial');
        const modelTrinomial = this.getElement('modelTrinomial');
        
        if (modelBS && modelBS.checked) models.push('black_scholes');
        if (modelBinomial && modelBinomial.checked) models.push('binomial');
        if (modelTrinomial && modelTrinomial.checked) models.push('trinomial');
        
        if (models.length === 0) {
            Utils.showAlert('Please select at least one pricing model', 'error');
            return;
        }
        
        try {
            Utils.showAlert('Calculating option price...', 'info');
            
            // Verify API dependency
            if (typeof API === 'undefined' || typeof API.calculateOptionPrice !== 'function') {
                throw new Error('API dependency not available');
            }

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
                if (typeof OptionsDisplay !== 'undefined' && typeof OptionsDisplay.displayOptionResults === 'function') {
                    OptionsDisplay.displayOptionResults(data.results);
                    Utils.showAlert('Calculation complete!', 'success');
                } else {
                    Utils.showAlert('Error: Display module not available', 'error');
                }
            } else {
                Utils.showAlert(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            Utils.showAlert(`Failed to calculate option price: ${error.message}`, 'error');
        }
    },

    /**
     * Calculate implied volatility
     */
    async calculateImpliedVolatility() {
        // Verify Utils dependency
        if (typeof Utils === 'undefined' || typeof Utils.showAlert !== 'function') {
            console.error('Utils dependency not available');
            alert('Error: Required dependencies not loaded');
            return;
        }

        // Get DOM elements with null checks
        const marketPriceElement = this.getElement('ivMarketPrice');
        const spotElement = this.getElement('ivSpot');
        const strikeElement = this.getElement('ivStrike');
        const maturityElement = this.getElement('ivMaturity');
        const rateElement = this.getElement('ivRate');
        const optionTypeElement = this.getElement('ivType');
        
        if (!marketPriceElement || !spotElement || !strikeElement || 
            !maturityElement || !rateElement || !optionTypeElement) {
            Utils.showAlert('Error: Required form elements not found', 'error');
            return;
        }

        // Validate all numeric inputs
        const marketPriceValidation = this.validateNumericInput(marketPriceElement.value, 'Market Price', 0.01);
        if (!marketPriceValidation.valid) {
            Utils.showAlert(marketPriceValidation.error, 'error');
            return;
        }

        const spotValidation = this.validateNumericInput(spotElement.value, 'Spot Price', 0.01);
        if (!spotValidation.valid) {
            Utils.showAlert(spotValidation.error, 'error');
            return;
        }

        const strikeValidation = this.validateNumericInput(strikeElement.value, 'Strike Price', 0.01);
        if (!strikeValidation.valid) {
            Utils.showAlert(strikeValidation.error, 'error');
            return;
        }

        const maturityValidation = this.validateNumericInput(maturityElement.value, 'Time to Maturity', 0.001, 50);
        if (!maturityValidation.valid) {
            Utils.showAlert(maturityValidation.error, 'error');
            return;
        }

        const rateValidation = this.validateNumericInput(rateElement.value, 'Risk-Free Rate', -20, 100);
        if (!rateValidation.valid) {
            Utils.showAlert(rateValidation.error, 'error');
            return;
        }

        const marketPrice = marketPriceValidation.value;
        const spot = spotValidation.value;
        const strike = strikeValidation.value;
        const maturity = maturityValidation.value;
        const rate = rateValidation.value / 100;
        const optionType = optionTypeElement.value;
        
        try {
            Utils.showAlert('Extracting implied volatility...', 'info');
            
            // Verify API dependency
            if (typeof API === 'undefined' || typeof API.calculateImpliedVolatility !== 'function') {
                throw new Error('API dependency not available');
            }
            
            const data = await API.calculateImpliedVolatility({
                market_price: marketPrice,
                spot: spot,
                strike: strike,
                maturity: maturity,
                risk_free_rate: rate,
                option_type: optionType
            });
            
            if (data.success) {
                if (typeof OptionsDisplay !== 'undefined' && typeof OptionsDisplay.displayImpliedVolResults === 'function') {
                    OptionsDisplay.displayImpliedVolResults(data.result);
                    Utils.showAlert('Implied volatility extracted!', 'success');
                } else {
                    Utils.showAlert('Error: Display module not available', 'error');
                }
            } else {
                Utils.showAlert(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            Utils.showAlert(`Failed to calculate implied volatility: ${error.message}`, 'error');
        }
    },

    /**
     * Calculate Greeks
     */
    async calculateGreeks() {
        // Verify Utils dependency
        if (typeof Utils === 'undefined' || typeof Utils.showAlert !== 'function') {
            console.error('Utils dependency not available');
            alert('Error: Required dependencies not loaded');
            return;
        }

        // Get DOM elements with null checks
        const spotElement = this.getElement('greeksSpot');
        const strikeElement = this.getElement('greeksStrike');
        const maturityElement = this.getElement('greeksMaturity');
        const rateElement = this.getElement('greeksRate');
        const volatilityElement = this.getElement('greeksVol');
        const optionTypeElement = this.getElement('greeksType');
        
        if (!spotElement || !strikeElement || !maturityElement || 
            !rateElement || !volatilityElement || !optionTypeElement) {
            Utils.showAlert('Error: Required form elements not found', 'error');
            return;
        }

        // Validate all numeric inputs
        const spotValidation = this.validateNumericInput(spotElement.value, 'Spot Price', 0.01);
        if (!spotValidation.valid) {
            Utils.showAlert(spotValidation.error, 'error');
            return;
        }

        const strikeValidation = this.validateNumericInput(strikeElement.value, 'Strike Price', 0.01);
        if (!strikeValidation.valid) {
            Utils.showAlert(strikeValidation.error, 'error');
            return;
        }

        const maturityValidation = this.validateNumericInput(maturityElement.value, 'Time to Maturity', 0.001, 50);
        if (!maturityValidation.valid) {
            Utils.showAlert(maturityValidation.error, 'error');
            return;
        }

        const rateValidation = this.validateNumericInput(rateElement.value, 'Risk-Free Rate', -20, 100);
        if (!rateValidation.valid) {
            Utils.showAlert(rateValidation.error, 'error');
            return;
        }

        const volatilityValidation = this.validateNumericInput(volatilityElement.value, 'Volatility', 0.1, 500);
        if (!volatilityValidation.valid) {
            Utils.showAlert(volatilityValidation.error, 'error');
            return;
        }

        const spot = spotValidation.value;
        const strike = strikeValidation.value;
        const maturity = maturityValidation.value;
        const rate = rateValidation.value / 100;
        const volatility = volatilityValidation.value / 100;
        const optionType = optionTypeElement.value;
        
        try {
            Utils.showAlert('Calculating Greeks...', 'info');
            
            // Verify API dependency
            if (typeof API === 'undefined' || typeof API.calculateGreeks !== 'function') {
                throw new Error('API dependency not available');
            }

            const data = await API.calculateGreeks({
                spot: spot,
                strike: strike,
                maturity: maturity,
                risk_free_rate: rate,
                volatility: volatility,
                option_type: optionType
            });
            
            if (data.success) {
                if (typeof OptionsDisplay !== 'undefined' && typeof OptionsDisplay.displayGreeksResults === 'function') {
                    OptionsDisplay.displayGreeksResults(data.greeks);
                    Utils.showAlert('Greeks calculated successfully!', 'success');
                } else {
                    Utils.showAlert('Error: Display module not available', 'error');
                }
            } else {
                Utils.showAlert(data.error || 'Failed to calculate Greeks', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            Utils.showAlert(`Error calculating Greeks: ${error.message}`, 'error');
        }
    },

    /**
     * Calculate model comparison
     */
    async calculateModelComparison() {
        // Verify Utils dependency
        if (typeof Utils === 'undefined' || typeof Utils.showAlert !== 'function') {
            console.error('Utils dependency not available');
            alert('Error: Required dependencies not loaded');
            return;
        }

        // Get DOM elements with null checks
        const spotElement = this.getElement('compSpot');
        const strikeElement = this.getElement('compStrike');
        const maturityElement = this.getElement('compMaturity');
        const rateElement = this.getElement('compRate');
        const volatilityElement = this.getElement('compVol');
        const optionTypeElement = this.getElement('compType');
        const stepsElement = this.getElement('compSteps');
        
        if (!spotElement || !strikeElement || !maturityElement || !rateElement || 
            !volatilityElement || !optionTypeElement || !stepsElement) {
            Utils.showAlert('Error: Required form elements not found', 'error');
            return;
        }

        // Validate all numeric inputs
        const spotValidation = this.validateNumericInput(spotElement.value, 'Spot Price', 0.01);
        if (!spotValidation.valid) {
            Utils.showAlert(spotValidation.error, 'error');
            return;
        }

        const strikeValidation = this.validateNumericInput(strikeElement.value, 'Strike Price', 0.01);
        if (!strikeValidation.valid) {
            Utils.showAlert(strikeValidation.error, 'error');
            return;
        }

        const maturityValidation = this.validateNumericInput(maturityElement.value, 'Time to Maturity', 0.001, 50);
        if (!maturityValidation.valid) {
            Utils.showAlert(maturityValidation.error, 'error');
            return;
        }

        const rateValidation = this.validateNumericInput(rateElement.value, 'Risk-Free Rate', -20, 100);
        if (!rateValidation.valid) {
            Utils.showAlert(rateValidation.error, 'error');
            return;
        }

        const volatilityValidation = this.validateNumericInput(volatilityElement.value, 'Volatility', 0.1, 500);
        if (!volatilityValidation.valid) {
            Utils.showAlert(volatilityValidation.error, 'error');
            return;
        }

        const stepsValidation = this.validateNumericInput(stepsElement.value, 'Steps', 1, 1000);
        if (!stepsValidation.valid) {
            Utils.showAlert(stepsValidation.error, 'error');
            return;
        }

        const spot = spotValidation.value;
        const strike = strikeValidation.value;
        const maturity = maturityValidation.value;
        const rate = rateValidation.value / 100;
        const volatility = volatilityValidation.value / 100;
        const optionType = optionTypeElement.value;
        const steps = parseInt(stepsValidation.value);
        
        try {
            Utils.showAlert('Comparing models...', 'info');
            
            // Verify API dependency
            if (typeof API === 'undefined' || typeof API.calculateModelComparison !== 'function') {
                throw new Error('API dependency not available');
            }

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
                if (typeof OptionsDisplay !== 'undefined' && typeof OptionsDisplay.displayModelComparisonResults === 'function') {
                    OptionsDisplay.displayModelComparisonResults(data.comparison);
                    Utils.showAlert('Model comparison complete!', 'success');
                } else {
                    Utils.showAlert('Error: Display module not available', 'error');
                }
            } else {
                Utils.showAlert(data.error || 'Failed to compare models', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            Utils.showAlert(`Error comparing models: ${error.message}`, 'error');
        }
    }
};

// Export for browser environment
window.OptionsPricing = OptionsPricing;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OptionsPricing;
}
