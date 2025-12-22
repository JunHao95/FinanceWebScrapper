// ===========================
// Options Display Module
// ===========================

const OptionsDisplay = {
    /**
     * Display option pricing results
     */
    displayOptionResults(results) {
        const resultsDiv = document.getElementById('optionResults');
        const contentDiv = document.getElementById('optionResultsContent');
        
        let html = '<div class="option-results-grid">';
        
        if (results.black_scholes) {
            html += '<div class="result-card">';
            html += '<h4>Black-Scholes Model</h4>';
            html += `<div class="price-display">$${results.black_scholes.price.toFixed(4)}</div>`;
            html += '<div class="greeks-grid">';
            html += `<div><strong>Delta:</strong> ${results.black_scholes.delta.toFixed(4)}</div>`;
            html += `<div><strong>Gamma:</strong> ${results.black_scholes.gamma.toFixed(4)}</div>`;
            html += `<div><strong>Theta:</strong> ${results.black_scholes.theta.toFixed(4)}</div>`;
            html += `<div><strong>Vega:</strong> ${results.black_scholes.vega.toFixed(4)}</div>`;
            html += `<div><strong>Rho:</strong> ${results.black_scholes.rho.toFixed(4)}</div>`;
            html += '</div></div>';
        }
        
        if (results.binomial) {
            html += '<div class="result-card">';
            html += '<h4>Binomial Tree Model</h4>';
            html += `<div class="price-display">$${results.binomial.price.toFixed(4)}</div>`;
            html += `<div><strong>Steps:</strong> ${results.binomial.steps}</div>`;
            html += `<div><strong>Up Factor (u):</strong> ${results.binomial.u.toFixed(4)}</div>`;
            html += `<div><strong>Down Factor (d):</strong> ${results.binomial.d.toFixed(4)}</div>`;
            html += `<div><strong>Risk-Neutral Prob:</strong> ${results.binomial.p.toFixed(4)}</div>`;
            html += '</div>';
        }
        
        if (results.trinomial) {
            html += '<div class="result-card">';
            html += '<h4>Trinomial Tree Model</h4>';
            html += `<div class="price-display">$${results.trinomial.price.toFixed(4)}</div>`;
            html += `<div><strong>Steps:</strong> ${results.trinomial.steps}</div>`;
            html += `<div><strong>Up Probability:</strong> ${results.trinomial.pu.toFixed(4)}</div>`;
            html += `<div><strong>Down Probability:</strong> ${results.trinomial.pd.toFixed(4)}</div>`;
            html += `<div><strong>Middle Probability:</strong> ${results.trinomial.pm.toFixed(4)}</div>`;
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
        const resultsDiv = document.getElementById('optionResults');
        const contentDiv = document.getElementById('optionResultsContent');
        
        let html = '<div class="result-card">';
        html += '<h4>Implied Volatility Results</h4>';
        html += `<div class="price-display">${(result.implied_volatility * 100).toFixed(2)}%</div>`;
        html += `<div><strong>Converged:</strong> ${result.converged ? '✅ Yes' : '❌ No'}</div>`;
        html += `<div><strong>Iterations:</strong> ${result.num_iterations}</div>`;
        html += `<div><strong>Final Difference:</strong> $${Math.abs(result.final_difference).toFixed(6)}</div>`;
        
        if (result.validation) {
            html += '<hr style="margin: 15px 0;">';
            html += '<h5>Validation</h5>';
            html += `<div><strong>Recalculated Price:</strong> $${result.validation.recalculated_price.toFixed(4)}</div>`;
            html += `<div><strong>Market Price:</strong> $${result.validation.market_price.toFixed(4)}</div>`;
            html += `<div><strong>Percentage Error:</strong> ${result.validation.percentage_error.toFixed(4)}%</div>`;
            html += `<div><strong>Valid:</strong> ${result.validation.is_valid ? '✅ Yes' : '⚠️ Check accuracy'}</div>`;
        }
        
        if (result.iterations && result.iterations.length > 0) {
            html += '<hr style="margin: 15px 0;">';
            html += '<h5>Convergence Details (Last 5 iterations)</h5>';
            html += '<table style="width: 100%; border-collapse: collapse;">';
            html += '<tr><th>Iter</th><th>Sigma</th><th>Price</th><th>Diff</th></tr>';
            const lastIterations = result.iterations.slice(-5);
            for (const iter of lastIterations) {
                html += `<tr>`;
                html += `<td>${iter.iteration}</td>`;
                html += `<td>${(iter.sigma * 100).toFixed(2)}%</td>`;
                html += `<td>$${iter.price.toFixed(4)}</td>`;
                html += `<td>$${iter.abs_diff.toFixed(6)}</td>`;
                html += `</tr>`;
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
        const resultsDiv = document.getElementById('optionResults');
        const contentDiv = document.getElementById('optionResultsContent');
        
        let html = '<div class="result-card">';
        html += '<h4>📐 Option Greeks</h4>';
        html += '<div class="greeks-grid" style="grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 20px;">';
        
        html += '<div style="padding: 15px; background: #e8f5e9; border-radius: 8px;">';
        html += '<h5 style="margin: 0 0 10px 0; color: #2e7d32;">Delta (Δ)</h5>';
        html += `<div style="font-size: 1.5rem; font-weight: bold;">${greeks.delta.toFixed(4)}</div>`;
        html += '<small>Price sensitivity to underlying asset</small>';
        html += '</div>';
        
        html += '<div style="padding: 15px; background: #fff3e0; border-radius: 8px;">';
        html += '<h5 style="margin: 0 0 10px 0; color: #e65100;">Gamma (Γ)</h5>';
        html += `<div style="font-size: 1.5rem; font-weight: bold;">${greeks.gamma.toFixed(4)}</div>`;
        html += '<small>Rate of change of Delta</small>';
        html += '</div>';
        
        html += '<div style="padding: 15px; background: #f3e5f5; border-radius: 8px;">';
        html += '<h5 style="margin: 0 0 10px 0; color: #6a1b9a;">Theta (Θ)</h5>';
        html += `<div style="font-size: 1.5rem; font-weight: bold;">${greeks.theta.toFixed(4)}</div>`;
        html += '<small>Time decay (per day)</small>';
        html += '</div>';
        
        html += '<div style="padding: 15px; background: #e3f2fd; border-radius: 8px;">';
        html += '<h5 style="margin: 0 0 10px 0; color: #1565c0;">Vega (ν)</h5>';
        html += `<div style="font-size: 1.5rem; font-weight: bold;">${greeks.vega.toFixed(4)}</div>`;
        html += '<small>Sensitivity to volatility (per 1%)</small>';
        html += '</div>';
        
        html += '<div style="padding: 15px; background: #fce4ec; border-radius: 8px;">';
        html += '<h5 style="margin: 0 0 10px 0; color: #c2185b;">Rho (ρ)</h5>';
        html += `<div style="font-size: 1.5rem; font-weight: bold;">${greeks.rho.toFixed(4)}</div>`;
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
        const resultsDiv = document.getElementById('optionResults');
        const contentDiv = document.getElementById('optionResultsContent');
        
        const results = {
            black_scholes: comparison.black_scholes,
            binomial: comparison.binomial,
            trinomial: comparison.trinomial
        };
        const differences = comparison.differences;
        
        let html = '<div style="margin-bottom: 20px;">';
        html += '<h4>🔬 Model Comparison</h4>';
        html += '<div class="option-results-grid">';
        
        html += '<div class="result-card">';
        html += '<h4>Black-Scholes (Analytical)</h4>';
        html += `<div class="price-display">$${results.black_scholes.price.toFixed(4)}</div>`;
        html += '<div style="margin-top: 10px; font-size: 0.9rem; color: #666;">';
        html += '<strong>Benchmark Model</strong><br>';
        html += 'Closed-form solution';
        html += '</div></div>';
        
        html += '<div class="result-card">';
        html += '<h4>Binomial Tree</h4>';
        html += `<div class="price-display">$${results.binomial.price.toFixed(4)}</div>`;
        html += `<div style="margin-top: 10px; color: ${Math.abs(differences.binomial_vs_bs) < 0.01 ? '#27ae60' : '#e67e22'};">`;
        html += `<strong>Diff vs BS:</strong> $${differences.binomial_vs_bs.toFixed(6)}`;
        html += `<br><small>(${((differences.binomial_vs_bs / results.black_scholes.price) * 100).toFixed(3)}%)</small>`;
        html += '</div></div>';
        
        html += '<div class="result-card">';
        html += '<h4>Trinomial Tree</h4>';
        html += `<div class="price-display">$${results.trinomial.price.toFixed(4)}</div>`;
        html += `<div style="margin-top: 10px; color: ${Math.abs(differences.trinomial_vs_bs) < 0.01 ? '#27ae60' : '#e67e22'};">`;
        html += `<strong>Diff vs BS:</strong> $${differences.trinomial_vs_bs.toFixed(6)}`;
        html += `<br><small>(${((differences.trinomial_vs_bs / results.black_scholes.price) * 100).toFixed(3)}%)</small>`;
        html += '</div></div>';
        
        html += '</div>';
        
        html += '<div class="result-card" style="margin-top: 20px;">';
        html += '<h5>📊 Analysis Summary</h5>';
        html += `<div><strong>Binomial vs Trinomial:</strong> $${differences.binomial_vs_trinomial.toFixed(6)}</div>`;
        
        const maxDiff = Math.max(
            Math.abs(differences.binomial_vs_bs),
            Math.abs(differences.trinomial_vs_bs)
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

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OptionsDisplay;
}
