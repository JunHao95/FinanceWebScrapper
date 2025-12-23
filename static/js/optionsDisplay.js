// ===========================
// Options Display Module
// ===========================

const OptionsDisplay = {
    /**
     * Safely format a number with fallback for invalid values
     * @param {*} value - Value to format
     * @param {number} decimals - Number of decimal places
     * @returns {string} Formatted string
     */
    safeFormat(value, decimals = 4) {
        if (value === null || value === undefined || isNaN(value) || !isFinite(value)) {
            return 'N/A';
        }
        return Number(value).toFixed(decimals);
    },

    /**
     * Calculate percentage safely, guarding against division by zero
     * @param {number} numerator - The numerator
     * @param {number} denominator - The denominator
     * @param {number} decimals - Number of decimal places
     * @returns {string} Percentage string or 'N/A'
     */
    safePercentage(numerator, denominator, decimals = 3) {
        if (!denominator || denominator === 0 || isNaN(denominator) || isNaN(numerator)) {
            return 'N/A';
        }
        return ((numerator / denominator) * 100).toFixed(decimals);
    },

    /**
     * Validate input data structure
     * @param {*} data - Data to validate
     * @param {string[]} requiredFields - Required fields
     * @returns {boolean} True if valid
     */
    validateData(data, requiredFields = []) {
        if (!data || typeof data !== 'object') {
            return false;
        }
        for (const field of requiredFields) {
            if (!(field in data)) {
                return false;
            }
        }
        return true;
    },
    /**
     * Display option pricing results
     */
    displayOptionResults(results) {
        // Defensive check for DOM elements
        const resultsDiv = document.getElementById('optionResults');
        const contentDiv = document.getElementById('optionResultsContent');
        
        if (!resultsDiv || !contentDiv) {
            console.error('Required DOM elements not found: optionResults or optionResultsContent');
            return;
        }

        // Input validation
        if (!this.validateData(results)) {
            console.error('Invalid results data provided to displayOptionResults');
            contentDiv.innerHTML = '<div class="error-message">Invalid results data</div>';
            return;
        }
        
        let html = '<div class="option-results-grid">';
        
        if (results.black_scholes && this.validateData(results.black_scholes, ['price', 'delta', 'gamma', 'theta', 'vega', 'rho'])) {
            html += '<div class="result-card">';
            html += '<h4>Black-Scholes Model</h4>';
            html += `<div class="price-display">$${this.safeFormat(results.black_scholes.price)}</div>`;
            html += '<div class="greeks-grid">';
            html += `<div><strong>Delta:</strong> ${this.safeFormat(results.black_scholes.delta)}</div>`;
            html += `<div><strong>Gamma:</strong> ${this.safeFormat(results.black_scholes.gamma)}</div>`;
            html += `<div><strong>Theta:</strong> ${this.safeFormat(results.black_scholes.theta)}</div>`;
            html += `<div><strong>Vega:</strong> ${this.safeFormat(results.black_scholes.vega)}</div>`;
            html += `<div><strong>Rho:</strong> ${this.safeFormat(results.black_scholes.rho)}</div>`;
            html += '</div></div>';
        }
        
        if (results.binomial && this.validateData(results.binomial, ['price', 'steps', 'u', 'd', 'p'])) {
            html += '<div class="result-card">';
            html += '<h4>Binomial Tree Model</h4>';
            html += `<div class="price-display">$${this.safeFormat(results.binomial.price)}</div>`;
            html += `<div><strong>Steps:</strong> ${results.binomial.steps}</div>`;
            html += `<div><strong>Up Factor (u):</strong> ${this.safeFormat(results.binomial.u)}</div>`;
            html += `<div><strong>Down Factor (d):</strong> ${this.safeFormat(results.binomial.d)}</div>`;
            html += `<div><strong>Risk-Neutral Prob:</strong> ${this.safeFormat(results.binomial.p)}</div>`;
            html += '</div>';
        }
        
        if (results.trinomial && this.validateData(results.trinomial, ['price', 'steps', 'pu', 'pd', 'pm'])) {
            html += '<div class="result-card">';
            html += '<h4>Trinomial Tree Model</h4>';
            html += `<div class="price-display">$${this.safeFormat(results.trinomial.price)}</div>`;
            html += `<div><strong>Steps:</strong> ${results.trinomial.steps}</div>`;
            html += `<div><strong>Up Probability:</strong> ${this.safeFormat(results.trinomial.pu)}</div>`;
            html += `<div><strong>Down Probability:</strong> ${this.safeFormat(results.trinomial.pd)}</div>`;
            html += `<div><strong>Middle Probability:</strong> ${this.safeFormat(results.trinomial.pm)}</div>`;
            html += '</div>';
        }
        
        html += '</div>';
        
        contentDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
    },

    /**
     * Display implied volatility results
     */
    displayImpliedVolResults(result) {
        // Defensive check for DOM elements
        const resultsDiv = document.getElementById('optionResults');
        const contentDiv = document.getElementById('optionResultsContent');
        
        if (!resultsDiv || !contentDiv) {
            console.error('Required DOM elements not found: optionResults or optionResultsContent');
            return;
        }

        // Input validation
        if (!this.validateData(result, ['implied_volatility', 'converged', 'num_iterations'])) {
            console.error('Invalid result data provided to displayImpliedVolResults');
            contentDiv.innerHTML = '<div class="error-message">Invalid implied volatility results</div>';
            return;
        }
        
        let html = '<div class="result-card">';
        html += '<h4>Implied Volatility Results</h4>';
        html += `<div class="price-display">${this.safeFormat(result.implied_volatility * 100, 2)}%</div>`;
        html += `<div><strong>Converged:</strong> ${result.converged ? '✅ Yes' : '❌ No'}</div>`;
        html += `<div><strong>Iterations:</strong> ${result.num_iterations}</div>`;
        
        if (result.final_difference !== undefined) {
            html += `<div><strong>Final Difference:</strong> $${this.safeFormat(Math.abs(result.final_difference), 6)}</div>`;
        }
        
        if (result.validation && this.validateData(result.validation, ['recalculated_price', 'market_price'])) {
            html += '<hr style="margin: 15px 0;">';
            html += '<h5>Validation</h5>';
            html += `<div><strong>Recalculated Price:</strong> $${this.safeFormat(result.validation.recalculated_price)}</div>`;
            html += `<div><strong>Market Price:</strong> $${this.safeFormat(result.validation.market_price)}</div>`;
            
            // Guard against division by zero in percentage calculation
            if (result.validation.percentage_error !== undefined) {
                html += `<div><strong>Percentage Error:</strong> ${this.safeFormat(result.validation.percentage_error, 4)}%</div>`;
            } else {
                const percentageError = this.safePercentage(
                    result.validation.recalculated_price - result.validation.market_price,
                    result.validation.market_price,
                    4
                );
                html += `<div><strong>Percentage Error:</strong> ${percentageError}%</div>`;
            }
            
            html += `<div><strong>Valid:</strong> ${result.validation.is_valid ? '✅ Yes' : '⚠️ Check accuracy'}</div>`;
        }
        
        if (result.iterations && Array.isArray(result.iterations) && result.iterations.length > 0) {
            html += '<hr style="margin: 15px 0;">';
            html += '<h5>Convergence Details (Last 5 iterations)</h5>';
            html += '<table style="width: 100%; border-collapse: collapse;">';
            html += '<tr><th>Iter</th><th>Sigma</th><th>Price</th><th>Diff</th></tr>';
            const lastIterations = result.iterations.slice(-5);
            for (const iter of lastIterations) {
                if (this.validateData(iter, ['iteration', 'sigma', 'price', 'abs_diff'])) {
                    html += `<tr>`;
                    html += `<td>${iter.iteration}</td>`;
                    html += `<td>${this.safeFormat(iter.sigma * 100, 2)}%</td>`;
                    html += `<td>$${this.safeFormat(iter.price)}</td>`;
                    html += `<td>$${this.safeFormat(iter.abs_diff, 6)}</td>`;
                    html += `</tr>`;
                }
            }
            html += '</table>';
        }
        
        html += '</div>';
        
        contentDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
    },

    /**
     * Display Greeks results
     */
    displayGreeksResults(greeks) {
        // Defensive check for DOM elements
        const resultsDiv = document.getElementById('optionResults');
        const contentDiv = document.getElementById('optionResultsContent');
        
        if (!resultsDiv || !contentDiv) {
            console.error('Required DOM elements not found: optionResults or optionResultsContent');
            return;
        }

        // Input validation
        if (!this.validateData(greeks, ['delta', 'gamma', 'theta', 'vega', 'rho'])) {
            console.error('Invalid greeks data provided to displayGreeksResults');
            contentDiv.innerHTML = '<div class="error-message">Invalid Greeks data</div>';
            return;
        }
        
        let html = '<div class="result-card">';
        html += '<h4>📐 Option Greeks</h4>';
        html += '<div class="greeks-grid" style="grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 20px;">';
        
        html += '<div style="padding: 15px; background: #e8f5e9; border-radius: 8px;">';
        html += '<h5 style="margin: 0 0 10px 0; color: #2e7d32;">Delta (Δ)</h5>';
        html += `<div style="font-size: 1.5rem; font-weight: bold;">${this.safeFormat(greeks.delta)}</div>`;
        html += '<small>Price sensitivity to underlying asset</small>';
        html += '</div>';
        
        html += '<div style="padding: 15px; background: #fff3e0; border-radius: 8px;">';
        html += '<h5 style="margin: 0 0 10px 0; color: #e65100;">Gamma (Γ)</h5>';
        html += `<div style="font-size: 1.5rem; font-weight: bold;">${this.safeFormat(greeks.gamma)}</div>`;
        html += '<small>Rate of change of Delta</small>';
        html += '</div>';
        
        html += '<div style="padding: 15px; background: #f3e5f5; border-radius: 8px;">';
        html += '<h5 style="margin: 0 0 10px 0; color: #6a1b9a;">Theta (Θ)</h5>';
        html += `<div style="font-size: 1.5rem; font-weight: bold;">${this.safeFormat(greeks.theta)}</div>`;
        html += '<small>Time decay (per day)</small>';
        html += '</div>';
        
        html += '<div style="padding: 15px; background: #e3f2fd; border-radius: 8px;">';
        html += '<h5 style="margin: 0 0 10px 0; color: #1565c0;">Vega (ν)</h5>';
        html += `<div style="font-size: 1.5rem; font-weight: bold;">${this.safeFormat(greeks.vega)}</div>`;
        html += '<small>Sensitivity to volatility (per 1%)</small>';
        html += '</div>';
        
        html += '<div style="padding: 15px; background: #fce4ec; border-radius: 8px;">';
        html += '<h5 style="margin: 0 0 10px 0; color: #c2185b;">Rho (ρ)</h5>';
        html += `<div style="font-size: 1.5rem; font-weight: bold;">${this.safeFormat(greeks.rho)}</div>`;
        html += '<small>Sensitivity to interest rates (per 1%)</small>';
        html += '</div>';
        
        html += '</div></div>';
        
        contentDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
    },

    /**
     * Display model comparison results
     */
    displayModelComparisonResults(comparison) {
        // Defensive check for DOM elements
        const resultsDiv = document.getElementById('optionResults');
        const contentDiv = document.getElementById('optionResultsContent');
        
        if (!resultsDiv || !contentDiv) {
            console.error('Required DOM elements not found: optionResults or optionResultsContent');
            return;
        }

        // Input validation
        if (!this.validateData(comparison, ['black_scholes', 'binomial', 'trinomial', 'differences'])) {
            console.error('Invalid comparison data provided to displayModelComparisonResults');
            contentDiv.innerHTML = '<div class="error-message">Invalid model comparison data</div>';
            return;
        }
        
        const results = {
            black_scholes: comparison.black_scholes,
            binomial: comparison.binomial,
            trinomial: comparison.trinomial
        };
        const differences = comparison.differences;
        
        // Validate nested structures
        if (!this.validateData(results.black_scholes, ['price']) ||
            !this.validateData(results.binomial, ['price']) ||
            !this.validateData(results.trinomial, ['price']) ||
            !this.validateData(differences, ['binomial_vs_bs', 'trinomial_vs_bs', 'binomial_vs_trinomial'])) {
            console.error('Invalid nested data in model comparison');
            contentDiv.innerHTML = '<div class="error-message">Incomplete model comparison data</div>';
            return;
        }
        
        let html = '<div style="margin-bottom: 20px;">';
        html += '<h4>🔬 Model Comparison</h4>';
        html += '<div class="option-results-grid">';
        
        html += '<div class="result-card">';
        html += '<h4>Black-Scholes (Analytical)</h4>';
        html += `<div class="price-display">$${this.safeFormat(results.black_scholes.price)}</div>`;
        html += '<div style="margin-top: 10px; font-size: 0.9rem; color: #666;">';
        html += '<strong>Benchmark Model</strong><br>';
        html += 'Closed-form solution';
        html += '</div></div>';
        
        html += '<div class="result-card">';
        html += '<h4>Binomial Tree</h4>';
        html += `<div class="price-display">$${this.safeFormat(results.binomial.price)}</div>`;
        html += `<div style="margin-top: 10px; color: ${Math.abs(differences.binomial_vs_bs) < 0.01 ? '#27ae60' : '#e67e22'};">`;
        html += `<strong>Diff vs BS:</strong> $${this.safeFormat(differences.binomial_vs_bs, 6)}`;
        
        // Guard against division by zero when calculating percentage
        const binomialPercentage = this.safePercentage(differences.binomial_vs_bs, results.black_scholes.price, 3);
        html += `<br><small>(${binomialPercentage}%)</small>`;
        html += '</div></div>';
        
        html += '<div class="result-card">';
        html += '<h4>Trinomial Tree</h4>';
        html += `<div class="price-display">$${this.safeFormat(results.trinomial.price)}</div>`;
        html += `<div style="margin-top: 10px; color: ${Math.abs(differences.trinomial_vs_bs) < 0.01 ? '#27ae60' : '#e67e22'};">`;
        html += `<strong>Diff vs BS:</strong> $${this.safeFormat(differences.trinomial_vs_bs, 6)}`;
        
        // Guard against division by zero when calculating percentage
        const trinomialPercentage = this.safePercentage(differences.trinomial_vs_bs, results.black_scholes.price, 3);
        html += `<br><small>(${trinomialPercentage}%)</small>`;
        html += '</div></div>';
        
        html += '</div>';
        
        html += '<div class="result-card" style="margin-top: 20px;">';
        html += '<h5>📊 Analysis Summary</h5>';
        html += `<div><strong>Binomial vs Trinomial:</strong> $${this.safeFormat(differences.binomial_vs_trinomial, 6)}</div>`;
        
        const maxDiff = Math.max(
            Math.abs(differences.binomial_vs_bs || 0),
            Math.abs(differences.trinomial_vs_bs || 0)
        );
        
        if (maxDiff < 0.01) {
            html += '<div style="margin-top: 10px; padding: 10px; background: #d4edda; border-radius: 8px; color: #155724;">';
            html += '✅ Excellent convergence! All models agree within $0.01';
        } else if (maxDiff < 0.05) {
            html += '<div style="margin-top: 10px; padding: 10px; background: #fff3cd; border-radius: 8px; color: #856404;">';
            html += '⚠️ Good convergence. Consider increasing tree steps for better accuracy.';
        } else {
            html += '<div style="margin-top: 10px; padding: 10px; background: #f8d7da; border-radius: 8px; color: #721c24;">';
            html += '❌ Poor convergence. Increase tree steps significantly.';
        }
        html += '</div>';
        html += '</div>';
        html += '</div>';
        
        contentDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
    }
};

// Export for browser environment
window.OptionsDisplay = OptionsDisplay;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OptionsDisplay;
}
