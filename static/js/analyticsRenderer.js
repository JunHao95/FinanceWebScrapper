// ===========================
// Analytics Renderer Module
// Handles complex analytics HTML generation
// ===========================

const AnalyticsRenderer = {
    /**
     * Render correlation analysis
     */
    renderCorrelation(corrData) {
        let html = '<div style="background: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 20px; border-left: 4px solid #667eea;">';
        html += '<h3 style="color: #667eea; margin-bottom: 15px;">📊 Correlation Analysis</h3>';
        
        const corrMatrix = corrData["Correlation Matrix"] || corrData.correlation_matrix;
        
        if (corrMatrix) {
            html += '<div style="margin-bottom: 15px;">';
            html += '<h4 style="color: #555; margin-bottom: 10px;">Correlation Matrix:</h4>';
            html += '<div style="overflow-x: auto;">';
            html += '<table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">';
            
            const tickers = Object.keys(corrMatrix);
            html += '<tr><th style="padding: 12px; background: #667eea; color: white; border: 1px solid #ddd;"></th>';
            tickers.forEach(t => {
                html += `<th style="padding: 12px; background: #667eea; color: white; border: 1px solid #ddd;">${t}</th>`;
            });
            html += '</tr>';
            
            tickers.forEach(ticker1 => {
                html += `<tr><th style="padding: 12px; background: #667eea; color: white; border: 1px solid #ddd;">${ticker1}</th>`;
                tickers.forEach(ticker2 => {
                    const value = corrMatrix[ticker1][ticker2];
                    const color = value > 0.7 ? '#27ae60' : value < 0.3 ? '#e74c3c' : '#3498db';
                    html += `<td style="padding: 12px; text-align: center; border: 1px solid #ddd; background: ${color}20; color: ${color}; font-weight: bold;">${value ? value.toFixed(3) : '--'}</td>`;
                });
                html += '</tr>';
            });
            html += '</table></div></div>';
        }
        
        const summaryStats = corrData["Summary Statistics"] || corrData.summary;
        
        if (summaryStats) {
            html += '<div style="background: white; padding: 15px; border-radius: 8px;">';
            html += '<h4 style="color: #555; margin-bottom: 10px;">Summary Statistics:</h4>';
            html += `<p><strong>Average Correlation:</strong> ${summaryStats["Average Correlation"] ? summaryStats["Average Correlation"].toFixed(3) : (summaryStats.average_correlation ? summaryStats.average_correlation.toFixed(3) : '--')}</p>`;
            html += `<p><strong>Diversification Score:</strong> ${summaryStats["Diversification Score"] ? summaryStats["Diversification Score"].toFixed(3) : (summaryStats.diversification_score ? summaryStats.diversification_score.toFixed(3) : '--')}</p>`;
            html += `<p><strong>Number of Assets:</strong> ${summaryStats["Number of Assets"] || summaryStats.number_of_assets || '--'}</p>`;
            html += `<p><strong>Method:</strong> ${summaryStats["Method"] || summaryStats.method || '--'}</p>`;
            html += '</div>';
        }
        
        if (corrData["Interpretation"]) {
            html += '<div style="background: #e8f4fd; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 3px solid #3498db;">';
            html += `<p style="margin: 0; color: #2c3e50;"><strong>💡 Analysis:</strong> ${corrData["Interpretation"]}</p>`;
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    },

    /**
     * Render PCA analysis
     */
    renderPCA(pcaData) {
        let html = '<div style="background: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 20px; border-left: 4px solid #764ba2;">';
        html += '<h3 style="color: #764ba2; margin-bottom: 15px;">🔬 Principal Component Analysis (PCA)</h3>';
        
        const explainedVariance = pcaData["Explained Variance Ratio"];
        if (explainedVariance) {
            html += '<div style="margin-bottom: 15px; background: white; padding: 15px; border-radius: 8px;">';
            html += '<h4 style="color: #555; margin-bottom: 10px;">Explained Variance by Component:</h4>';
            
            const variances = Object.values(explainedVariance);
            variances.forEach((variance, idx) => {
                const percentage = (variance * 100).toFixed(2);
                html += `<div style="margin-bottom: 10px;">`;
                html += `<div style="display: flex; justify-content: space-between; margin-bottom: 5px;">`;
                html += `<span><strong>PC${idx + 1}:</strong></span>`;
                html += `<span><strong>${percentage}%</strong></span>`;
                html += `</div>`;
                html += `<div style="background: #e0e0e0; border-radius: 10px; height: 20px; overflow: hidden;">`;
                html += `<div style="background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; width: ${percentage}%;"></div>`;
                html += `</div>`;
                html += `</div>`;
            });
            html += '</div>';
        }
        
        const cumulativeVariance = pcaData["Cumulative Variance Explained"];
        if (cumulativeVariance) {
            html += '<div style="margin-bottom: 15px; background: white; padding: 15px; border-radius: 8px;">';
            html += '<h4 style="color: #555; margin-bottom: 10px;">Cumulative Variance:</h4>';
            const cumValues = Object.values(cumulativeVariance);
            const totalVariance = (cumValues[cumValues.length - 1] * 100).toFixed(2);
            html += `<p><strong>Total Variance Explained:</strong> ${totalVariance}%</p>`;
            html += '</div>';
        }
        
        const loadings = pcaData["Component Loadings"];
        if (loadings) {
            html += '<div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">';
            html += '<h4 style="color: #555; margin-bottom: 10px;">Component Loadings:</h4>';
            html += '<div style="overflow-x: auto;">';
            html += '<table style="width: 100%; border-collapse: collapse;">';
            html += '<thead><tr style="background: #f8f9fa;">';
            html += '<th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Component</th>';
            
            const firstPC = Object.keys(loadings)[0];
            const tickers = Object.keys(loadings[firstPC]);
            tickers.forEach(ticker => {
                html += `<th style="padding: 10px; text-align: center; border-bottom: 2px solid #dee2e6;">${ticker}</th>`;
            });
            html += '</tr></thead><tbody>';
            
            Object.entries(loadings).forEach(([pc, tickerLoadings]) => {
                html += `<tr>`;
                html += `<td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #dee2e6;">${pc}</td>`;
                Object.values(tickerLoadings).forEach(loading => {
                    const color = loading > 0 ? '#00b894' : '#d63031';
                    html += `<td style="padding: 10px; text-align: center; border-bottom: 1px solid #dee2e6; color: ${color};">${loading.toFixed(3)}</td>`;
                });
                html += `</tr>`;
            });
            html += '</tbody></table></div></div>';
        }
        
        const summary = pcaData["Summary"];
        if (summary) {
            html += '<div style="background: white; padding: 15px; border-radius: 8px;">';
            html += '<h4 style="color: #555; margin-bottom: 10px;">Summary:</h4>';
            html += `<p><strong>Tickers Analyzed:</strong> ${summary["Tickers Analyzed"].join(', ')}</p>`;
            html += `<p><strong>Total Variance Explained:</strong> ${(summary["Total Variance Explained"] * 100).toFixed(2)}%</p>`;
            html += `<p><strong>Components for 90% Variance:</strong> ${summary["Components for 90% Variance"]}</p>`;
            html += `<p><strong>Components for 95% Variance:</strong> ${summary["Components for 95% Variance"]}</p>`;
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    },

    /**
     * Render individual ticker analytics (regression and Monte Carlo)
     */
    renderTickerAnalytics(ticker, tickerAnalytics) {
        let html = `<div style="background: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 20px; border-left: 4px solid #00b894;">`;
        html += `<h3 style="color: #00b894; margin-bottom: 15px;">📍 ${ticker} Analytics</h3>`;
        
        if (tickerAnalytics.regression) {
            html += this.renderRegression(ticker, tickerAnalytics.regression);
        }
        
        if (tickerAnalytics.monte_carlo) {
            html += this.renderMonteCarlo(tickerAnalytics.monte_carlo);
        }
        
        html += '</div>';
        return html;
    },

    /**
     * Render regression analysis
     */
    renderRegression(ticker, reg) {
        const tickerReg = reg[ticker] || reg;
        
        let html = '<div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">';
        html += '<h4 style="color: #555; margin-bottom: 10px;">📈 Regression vs SPY:</h4>';
        html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">';
        
        const beta = tickerReg.Beta || tickerReg.beta;
        if (beta !== undefined) {
            const betaColor = beta > 1 ? '#e74c3c' : beta < 0.8 ? '#27ae60' : '#3498db';
            html += `<div style="padding: 12px; background: ${betaColor}15; border-radius: 8px; border: 2px solid ${betaColor};">`;
            html += `<div style="color: #666; font-size: 0.9rem; margin-bottom: 5px;">Beta</div>`;
            html += `<div style="color: ${betaColor}; font-size: 1.5rem; font-weight: bold;">${beta.toFixed(3)}</div>`;
            html += `<div style="color: #666; font-size: 0.8rem; margin-top: 5px;">${beta > 1 ? 'More volatile' : beta < 1 ? 'Less volatile' : 'Similar to'} SPY</div>`;
            html += `</div>`;
        }
        
        const alpha = tickerReg["Alpha (Annualized)"] || tickerReg["Alpha (Daily)"] || tickerReg.alpha;
        if (alpha !== undefined) {
            const alphaColor = alpha > 0 ? '#27ae60' : '#e74c3c';
            html += `<div style="padding: 12px; background: ${alphaColor}15; border-radius: 8px; border: 2px solid ${alphaColor};">`;
            html += `<div style="color: #666; font-size: 0.9rem; margin-bottom: 5px;">Alpha (Annual)</div>`;
            html += `<div style="color: ${alphaColor}; font-size: 1.5rem; font-weight: bold;">${(alpha * 100).toFixed(2)}%</div>`;
            html += `<div style="color: #666; font-size: 0.8rem; margin-top: 5px;">${alpha > 0 ? 'Outperforming' : 'Underperforming'}</div>`;
            html += `</div>`;
        }
        
        const rSquared = tickerReg["R-Squared"] || tickerReg.r_squared || tickerReg.R_Squared;
        if (rSquared !== undefined) {
            html += `<div style="padding: 12px; background: #3498db15; border-radius: 8px; border: 2px solid #3498db;">`;
            html += `<div style="color: #666; font-size: 0.9rem; margin-bottom: 5px;">R²</div>`;
            html += `<div style="color: #3498db; font-size: 1.5rem; font-weight: bold;">${(rSquared * 100).toFixed(1)}%</div>`;
            html += `<div style="color: #666; font-size: 0.8rem; margin-top: 5px;">Fit quality</div>`;
            html += `</div>`;
        }
        
        const correlation = tickerReg.Correlation || tickerReg.correlation;
        if (correlation !== undefined) {
            const corrColor = Math.abs(correlation) > 0.7 ? '#27ae60' : Math.abs(correlation) < 0.3 ? '#e74c3c' : '#3498db';
            html += `<div style="padding: 12px; background: ${corrColor}15; border-radius: 8px; border: 2px solid ${corrColor};">`;
            html += `<div style="color: #666; font-size: 0.9rem; margin-bottom: 5px;">Correlation</div>`;
            html += `<div style="color: ${corrColor}; font-size: 1.5rem; font-weight: bold;">${correlation.toFixed(3)}</div>`;
            html += `<div style="color: #666; font-size: 0.8rem; margin-top: 5px;">vs SPY</div>`;
            html += `</div>`;
        }
        
        html += '</div>';
        
        const interpretation = tickerReg.Interpretation || reg.Interpretation;
        if (interpretation) {
            html += '<div style="background: #e8f4fd; padding: 12px; border-radius: 8px; margin-top: 15px; border-left: 3px solid #3498db;">';
            html += `<p style="margin: 0; color: #2c3e50; font-size: 0.9rem;"><strong>💡 Analysis:</strong> ${interpretation}</p>`;
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    },

    /**
     * Render Monte Carlo analysis
     */
    renderMonteCarlo(mc) {
        let html = '<div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">';
        html += '<h4 style="color: #555; margin-bottom: 10px;">🎲 Monte Carlo (5000 Simulations) Risk Metrics (1-Year Forecast):</h4>';
        html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">';
        
        // Extract VaR values
        let var95Value = null;
        let es95Value = null;
        let var99Value = null;
        
        if (mc.VaR) {
            const var95Key = Object.keys(mc.VaR).find(k => k.includes('95'));
            if (var95Key && mc.VaR[var95Key]) {
                var95Value = mc.VaR[var95Key].Percentage / 100;
            }
        }
        
        if (mc["Expected Shortfall"]) {
            const es95Key = Object.keys(mc["Expected Shortfall"]).find(k => k.includes('95'));
            if (es95Key && mc["Expected Shortfall"][es95Key]) {
                es95Value = mc["Expected Shortfall"][es95Key].Percentage / 100;
            }
        }
        
        if (!var95Value && mc.var_95 !== undefined) var95Value = mc.var_95;
        if (!es95Value && mc.es_95 !== undefined) es95Value = mc.es_95;
        if (mc.var_99 !== undefined) var99Value = mc.var_99;
        
        if (var95Value !== null) {
            html += `<div style="padding: 12px; background: #e74c3c15; border-radius: 8px; border: 2px solid #e74c3c;">`;
            html += `<div style="color: #666; font-size: 0.9rem; margin-bottom: 5px;">VaR (95%), SPY : 15-20%</div>`;
            html += `<div style="color: #e74c3c; font-size: 1.5rem; font-weight: bold;">${(var95Value * 100).toFixed(2)}%</div>`;
            html += `<div style="color: #666; font-size: 0.8rem; margin-top: 5px;">Max loss (1 day)</div>`;
            html += `</div>`;
        }
        
        if (es95Value !== null) {
            html += `<div style="padding: 12px; background: #c0392b15; border-radius: 8px; border: 2px solid #c0392b;">`;
            html += `<div style="color: #666; font-size: 0.9rem; margin-bottom: 5px;">ES (95%)</div>`;
            html += `<div style="color: #c0392b; font-size: 1.5rem; font-weight: bold;">${(es95Value * 100).toFixed(2)}%</div>`;
            html += `<div style="color: #666; font-size: 0.8rem; margin-top: 5px;">Expected loss beyond VaR</div>`;
            html += `</div>`;
        }
        
        if (var99Value !== null) {
            html += `<div style="padding: 12px; background: #8e44ad15; border-radius: 8px; border: 2px solid #8e44ad;">`;
            html += `<div style="color: #666; font-size: 0.9rem; margin-bottom: 5px;">VaR (99%)</div>`;
            html += `<div style="color: #8e44ad; font-size: 1.5rem; font-weight: bold;">${(var99Value * 100).toFixed(2)}%</div>`;
            html += `<div style="color: #666; font-size: 0.8rem; margin-top: 5px;">Extreme scenario</div>`;
            html += `</div>`;
        }
        
        if (mc["Portfolio Statistics"]) {
            const stats = mc["Portfolio Statistics"];
            if (stats["Annualized Return"] !== undefined) {
                const returnColor = stats["Annualized Return"] > 0 ? '#27ae60' : '#e74c3c';
                html += `<div style="padding: 12px; background: ${returnColor}15; border-radius: 8px; border: 2px solid ${returnColor};">`;
                html += `<div style="color: #666; font-size: 0.9rem; margin-bottom: 5px;">Expected Return (SPY: 10-12%)</div>`;
                html += `<div style="color: ${returnColor}; font-size: 1.5rem; font-weight: bold;">${stats["Annualized Return"].toFixed(2)}%</div>`;
                html += `<div style="color: #666; font-size: 0.8rem; margin-top: 5px;">Annualized</div>`;
                html += `</div>`;
            }
            
            if (stats["Annualized Volatility"] !== undefined) {
                html += `<div style="padding: 12px; background: #f39c1215; border-radius: 8px; border: 2px solid #f39c12;">`;
                html += `<div style="color: #666; font-size: 0.9rem; margin-bottom: 5px;">Volatility (SPY: 15-20%)</div>`;
                html += `<div style="color: #f39c12; font-size: 1.5rem; font-weight: bold;">${stats["Annualized Volatility"].toFixed(2)}%</div>`;
                html += `<div style="color: #666; font-size: 0.8rem; margin-top: 5px;">Annualized</div>`;
                html += `</div>`;
            }
        }
        
        html += '</div>';
        
        if (mc["Scenario Analysis"]) {
            const scenario = mc["Scenario Analysis"];
            html += '<div style="background: #e8f4fd; padding: 12px; border-radius: 8px; margin-top: 15px; border-left: 3px solid #3498db;">';
            html += '<h5 style="color: #2c3e50; margin: 0 0 10px 0;">Scenario Analysis with $100,000 investment initial capital:</h5>';
            html += '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 0.85rem;">';
            if (scenario["Probability of Loss"] !== undefined) {
                html += `<div><strong>Probability of Loss:</strong> ${scenario["Probability of Loss"].toFixed(1)}%</div>`;
            }
            if (scenario["Best Case"] !== undefined) {
                html += `<div><strong>Best Case (1 in 5000 best outcome):</strong> $${scenario["Best Case"].toLocaleString()}</div>`;
            }
            if (scenario["Worst Case"] !== undefined) {
                html += `<div><strong>Worst Case (1 in 5000 worst outcome):</strong> $${scenario["Worst Case"].toLocaleString()}</div>`;
            }
            if (scenario["Expected Value"] !== undefined) {
                html += `<div><strong>Expected Value (Average value):</strong> $${scenario["Expected Value"].toLocaleString()}</div>`;
            }
            html += '</div></div>';
        }
        
        html += '</div>';
        return html;
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnalyticsRenderer;
}
