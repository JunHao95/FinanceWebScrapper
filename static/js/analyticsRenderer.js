// ===========================
// Analytics Renderer Module
// Handles complex analytics HTML generation
// ===========================

const AnalyticsRenderer = {
    /**
     * Escape HTML to prevent XSS attacks via output encoding, a strategy to neutralize malicious code
     */
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    },
    /**
     * Render fundamental analysis
     */
    renderFundamental(fundamentalData) {
        const ticker = fundamentalData.ticker || 'Stock';
        const outlook = fundamentalData.investment_outlook || 'N/A';
        const score = typeof fundamentalData.overall_score === 'number' ? fundamentalData.overall_score : 0;
        
        // Determine color based on outlook with improved matching
        let outlookColor = '#6c757d';
        const outlookLower = String(outlook).toLowerCase();
        if (outlookLower.includes('buy') && !outlookLower.includes('sell')) {
            outlookColor = '#28a745';
        } else if (outlookLower.includes('sell')) {
            outlookColor = '#dc3545';
        } else if (outlookLower === 'hold') {
            outlookColor = '#ffc107';
        }
        
        let html = '<div style="background: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 20px; border-left: 4px solid #17a2b8;">';
        html += '<h3 style="color: #17a2b8; margin-bottom: 15px;">💼 Fundamental Analysis</h3>';
        
        // Investment Outlook Header
        html += '<div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 15px; text-align: center;">';
        html += `<div style="display: inline-block; background: ${outlookColor}; color: white; padding: 10px 30px; border-radius: 25px; font-size: 1.3rem; font-weight: bold; margin-bottom: 10px;">`;
        html += `${this.escapeHtml(outlook)}</div>`;
        html += `<div style="font-size: 2rem; font-weight: bold; color: #333; margin-top: 10px;">`;
        html += `Overall Score: ${score.toFixed(1)}/10</div>`;
        html += '</div>';
        
        // Score Breakdown
        html += '<div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 15px;">';
        html += '<h4 style="color: #555; margin-bottom: 15px;">Score Breakdown:</h4>';
        html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">';
        
        const scores = [
            { label: 'Valuation', value: fundamentalData.valuation_score, icon: '💰' },
            { label: 'Profitability', value: fundamentalData.profitability_score, icon: '📈' },
            { label: 'Financial Health', value: fundamentalData.financial_health_score, icon: '🏥' },
            { label: 'Growth', value: fundamentalData.growth_score, icon: '🚀' }
        ];
        
        scores.forEach(({ label, value, icon }) => {
            // Validate value is a number and greater than 0
            if (typeof value === 'number' && !isNaN(value) && value >= 0) {
                const percentage = (value / 10) * 100;
                const color = value >= 7 ? '#28a745' : value >= 5 ? '#ffc107' : '#dc3545';
                html += '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">';
                html += `<div style="font-size: 1.5rem; margin-bottom: 5px;">${icon}</div>`;
                html += `<div style="font-weight: bold; margin-bottom: 8px;">${this.escapeHtml(label)}</div>`;
                html += `<div style="font-size: 1.2rem; font-weight: bold; color: ${color}; margin-bottom: 5px;">${value.toFixed(1)}/10</div>`;
                html += `<div style="background: #e0e0e0; border-radius: 10px; height: 8px; overflow: hidden;">`;
                html += `<div style="background: ${color}; height: 100%; width: ${percentage}%; transition: width 0.3s;"></div>`;
                html += '</div></div>';
            }
        });
        html += '</div></div>';;
        
        // Key Strengths
        if (fundamentalData.key_strengths && fundamentalData.key_strengths.length > 0) {
            html += '<div style="background: #d4edda; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 3px solid #28a745;">';
            html += '<h4 style="color: #155724; margin-bottom: 10px;">✅ Key Strengths:</h4>';
            html += '<ul style="margin: 0; padding-left: 20px; color: #155724;">';
            fundamentalData.key_strengths.forEach(strength => {
                html += `<li style="margin-bottom: 5px;">${this.escapeHtml(strength)}</li>`;
            });
            html += '</ul></div>';
        }
        
        // Key Concerns
        if (fundamentalData.key_concerns && fundamentalData.key_concerns.length > 0) {
            html += '<div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 3px solid #dc3545;">';
            html += '<h4 style="color: #721c24; margin-bottom: 10px;">⚠️ Key Concerns:</h4>';
            html += '<ul style="margin: 0; padding-left: 20px; color: #721c24;">';
            fundamentalData.key_concerns.forEach(concern => {
                html += `<li style="margin-bottom: 5px;">${this.escapeHtml(concern)}</li>`;
            });
            html += '</ul></div>';
        }
        
        // Summary
        if (fundamentalData.summary) {
            html += '<div style="background: #e7f3ff; padding: 15px; border-radius: 8px; border-left: 3px solid #0066cc;">';
            html += '<h4 style="color: #004085; margin-bottom: 10px;">📝 Investment Summary:</h4>';
            html += `<p style="margin: 0; color: #004085; line-height: 1.6;">${this.escapeHtml(fundamentalData.summary)}</p>`;
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    },

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
                html += `<th style="padding: 12px; background: #667eea; color: white; border: 1px solid #ddd;">${this.escapeHtml(t)}</th>`;
            });
            html += '</tr>';
            
            tickers.forEach(ticker1 => {
                html += `<tr><th style="padding: 12px; background: #667eea; color: white; border: 1px solid #ddd;">${this.escapeHtml(ticker1)}</th>`;
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
            html += `<p style="margin: 0; color: #2c3e50;"><strong>💡 Analysis:</strong> ${this.escapeHtml(corrData["Interpretation"])}</p>`;
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
            if (!firstPC || !loadings[firstPC]) {
                html += '</thead></table></div></div>';
            } else {
                const tickers = Object.keys(loadings[firstPC]);
                tickers.forEach(ticker => {
                    html += `<th style="padding: 10px; text-align: center; border-bottom: 2px solid #dee2e6;">${this.escapeHtml(ticker)}</th>`;
                });
                html += '</tr></thead><tbody>';
                
                Object.entries(loadings).forEach(([pc, tickerLoadings]) => {
                    html += `<tr>`;
                    html += `<td style="padding: 10px; font-weight: bold; border-bottom: 1px solid #dee2e6;">${this.escapeHtml(pc)}</td>`;
                    Object.values(tickerLoadings).forEach(loading => {
                        const color = loading > 0 ? '#00b894' : '#d63031';
                        const safeLoading = (typeof loading === 'number' && !isNaN(loading)) ? loading.toFixed(3) : '--';
                        html += `<td style="padding: 10px; text-align: center; border-bottom: 1px solid #dee2e6; color: ${color};">${safeLoading}</td>`;
                    });
                    html += `</tr>`;
                });
                html += '</tbody></table></div></div>';
            }
        }
        
        const summary = pcaData["Summary"];
        if (summary) {
            html += '<div style="background: white; padding: 15px; border-radius: 8px;">';
            html += '<h4 style="color: #555; margin-bottom: 10px;">Summary:</h4>';
            
            const tickersAnalyzed = summary["Tickers Analyzed"];
            if (Array.isArray(tickersAnalyzed)) {
                const escapedTickers = tickersAnalyzed.map(t => this.escapeHtml(t)).join(', ');
                html += `<p><strong>Tickers Analyzed:</strong> ${escapedTickers}</p>`;
            }
            
            const totalVariance = summary["Total Variance Explained"];
            if (typeof totalVariance === 'number' && !isNaN(totalVariance)) {
                html += `<p><strong>Total Variance Explained:</strong> ${(totalVariance * 100).toFixed(2)}%</p>`;
            }
            
            const comp90 = summary["Components for 90% Variance"];
            if (comp90 !== null && comp90 !== undefined) {
                html += `<p><strong>Components for 90% Variance:</strong> ${this.escapeHtml(comp90)}</p>`;
            }
            
            const comp95 = summary["Components for 95% Variance"];
            if (comp95 !== null && comp95 !== undefined) {
                html += `<p><strong>Components for 95% Variance:</strong> ${this.escapeHtml(comp95)}</p>`;
            }
            
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    },

    /**
     * Render individual ticker analytics (includes fundamental, regression, and Monte Carlo)
     */
    renderTickerAnalytics(ticker, tickerAnalytics) {
        let html = `<div style="background: #ffffff; border-radius: 12px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-top: 4px solid #00b894;">`;
        html += `<h3 style="color: #00b894; margin: 0 0 20px 0; font-size: 1.6rem; display: flex; align-items: center; gap: 10px;">`;
        html += `<span style="font-size: 1.8rem;">📊</span>`;
        html += `<span>${this.escapeHtml(ticker)} - Advanced Analysis</span>`;
        html += `</h3>`;
        
        
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
            html += `<p style="margin: 0; color: #2c3e50; font-size: 0.9rem;"><strong>💡 Analysis:</strong> ${this.escapeHtml(interpretation)}</p>`;
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
            if (scenario["Best Case (75th percentile)"] !== undefined) {
                html += `<div><strong>Best Case (75th percentile - better than 75% of outcomes):</strong> $${scenario["Best Case (75th percentile)"].toLocaleString()}</div>`;
            }
            if (scenario["Worst Case (10th percentile)"] !== undefined) {
                html += `<div><strong>Worst Case (10th percentile - worse than 90% of outcomes):</strong> $${scenario["Worst Case (10th percentile)"].toLocaleString()}</div>`;
            }
            if (scenario["Expected Value"] !== undefined) {
                html += `<div><strong>Expected Value (Average value):</strong> $${scenario["Expected Value"].toLocaleString()}</div>`;
            }
            html += '</div></div>';
        }
        
        // Stress Test Section   
        if (mc["Stress Test"]) {
            const stressTest = mc["Stress Test"];
            html += '<div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 3px solid #ffc107;">';
            html += '<h5 style="color: #856404; margin: 0 0 12px 0;">⚠️ Leptokurtic Stress Test Analysis</h5>';
            html += '<p style="color: #856404; font-size: 0.85rem; margin-bottom: 12px;">Enhanced stress test using <strong>Student-t distribution</strong> (fat tails) to capture extreme "Black Swan" events, correlation breakdown, asymmetric downside risk, and liquidity haircuts</p>';
            
            // Parameters display
            if (stressTest["Parameters"]) {
                const params = stressTest["Parameters"];
                html += '<div style="background: #fff; padding: 10px; border-radius: 5px; margin-bottom: 12px; font-size: 0.8rem; color: #666;">';
                html += `<strong>Stress Model:</strong> ${this.escapeHtml(params["Fat Tails (Student-t)"])} (df=${this.escapeHtml(params["Degrees of Freedom"])}), `;
                html += `${params.Simulations?.toLocaleString() ?? 'N/A'} simulations, `;
                html += `${params["Confidence Level"] ? (params["Confidence Level"] * 100) : 'N/A'}% confidence<br>`;
                html += `<strong>Crisis Parameters:</strong> ${this.escapeHtml(params["Volatility Multiplier"])}x vol, `;
                html += `${this.escapeHtml(params["Stress Correlation"])} correlation spike, `;
                html += `${this.escapeHtml(params["Liquidity Haircut"])} liquidity cost, `;
                html += `${this.escapeHtml(params["Downside Asymmetry"])} downside bias`;
                html += '</div>';
            }
            
            // Base Case vs Stress Case Comparison
            if (stressTest["Base Case"] && stressTest["Stress Case"]) {
                const baseCase = stressTest["Base Case"];
                const stressCase = stressTest["Stress Case"];
                const impact = stressTest["Stress Impact"];
                
                html += '<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 12px;">';
                
                // Base Case Card
                html += '<div style="background: #d4edda; padding: 12px; border-radius: 8px; border: 2px solid #28a745;">';
                html += '<h6 style="color: #155724; margin: 0 0 10px 0; font-size: 0.9rem;">📊 Base Case (Normal)</h6>';
                html += `<div style="font-size: 0.8rem; color: #155724; margin-bottom: 5px;"><strong>VaR:</strong> $${baseCase.VaR?.toLocaleString()} (${baseCase["VaR %"]}%)</div>`;
                html += `<div style="font-size: 0.8rem; color: #155724; margin-bottom: 5px;"><strong>ES:</strong> $${baseCase["Expected Shortfall"]?.toLocaleString()} (${baseCase["ES %"]}%)</div>`;
                html += `<div style="font-size: 0.8rem; color: #155724; margin-bottom: 5px;"><strong>Vol:</strong> ${baseCase["Avg Volatility"]}%</div>`;
                html += `<div style="font-size: 0.8rem; color: #155724; margin-bottom: 5px;"><strong>Corr:</strong> ${baseCase["Avg Correlation"]}</div>`;
                html += `<div style="font-size: 0.8rem; color: #155724;"><strong>P(Loss):</strong> ${baseCase["Probability of Loss"]}%</div>`;
                html += '</div>';
                
                // Stress Case Card
                html += '<div style="background: #f8d7da; padding: 12px; border-radius: 8px; border: 2px solid #dc3545;">';
                html += '<h6 style="color: #721c24; margin: 0 0 10px 0; font-size: 0.9rem;">🔥 Stress Case (Crisis)</h6>';
                html += `<div style="font-size: 0.8rem; color: #721c24; margin-bottom: 5px;"><strong>VaR (95%):</strong> $${stressCase.VaR?.toLocaleString()} (${stressCase["VaR %"]}%)</div>`;
                if (stressCase["VaR 99%"]) {
                    html += `<div style="font-size: 0.8rem; color: #721c24; margin-bottom: 5px;"><strong>VaR (99%):</strong> $${stressCase["VaR 99%"]?.toLocaleString()} (${stressCase["VaR 99% %"]}%)</div>`;
                }
                html += `<div style="font-size: 0.8rem; color: #721c24; margin-bottom: 5px;"><strong>ES (95%):</strong> $${stressCase["Expected Shortfall"]?.toLocaleString()} (${stressCase["ES %"]}%)</div>`;
                if (stressCase["ES 99%"]) {
                    html += `<div style="font-size: 0.8rem; color: #721c24; margin-bottom: 5px;"><strong>ES (99%):</strong> $${stressCase["ES 99%"]?.toLocaleString()} (${stressCase["ES 99% %"]}%)</div>`;
                }
                html += `<div style="font-size: 0.8rem; color: #721c24; margin-bottom: 5px;"><strong>Vol:</strong> ${stressCase["Avg Volatility"]}%</div>`;
                html += `<div style="font-size: 0.8rem; color: #721c24; margin-bottom: 5px;"><strong>Corr:</strong> ${stressCase["Avg Correlation"]}</div>`;
                html += `<div style="font-size: 0.8rem; color: #721c24; margin-bottom: 5px;"><strong>P(Loss):</strong> ${stressCase["Probability of Loss"]}%</div>`;
                if (stressCase["Distribution"]) {
                    html += `<div style="font-size: 0.8rem; color: #721c24; margin-bottom: 5px;"><strong>Distribution:</strong> ${this.escapeHtml(stressCase["Distribution"])}</div>`;
                }
                if (stressCase["Liquidity Haircut"]) {
                    html += `<div style="font-size: 0.8rem; color: #721c24;"><strong>Liquidity Haircut:</strong> ${this.escapeHtml(stressCase["Liquidity Haircut"])}</div>`;
                }
                html += '</div>';
                
                // Impact Card
                if (impact) {
                    html += '<div style="background: #fff3cd; padding: 12px; border-radius: 8px; border: 2px solid #ffc107;">';
                    html += '<h6 style="color: #856404; margin: 0 0 10px 0; font-size: 0.9rem;">📈 Stress Impact</h6>';
                    html += `<div style="font-size: 0.8rem; color: #856404; margin-bottom: 5px;"><strong>VaR ↑:</strong> $${impact["VaR Increase"]?.toLocaleString()} (${impact["VaR Increase %"]}%)</div>`;
                    if (impact["VaR 99% Increase"]) {
                        html += `<div style="font-size: 0.8rem; color: #856404; margin-bottom: 5px;"><strong>VaR 99% ↑:</strong> $${impact["VaR 99% Increase"]?.toLocaleString()}</div>`;
                    }
                    html += `<div style="font-size: 0.8rem; color: #856404; margin-bottom: 5px;"><strong>ES ↑:</strong> $${impact["ES Increase"]?.toLocaleString()} (${impact["ES Increase %"]}%)</div>`;
                    html += `<div style="font-size: 0.8rem; color: #856404;"><strong>P(Loss) ↑:</strong> ${impact["Prob Loss Increase"]}%</div>`;
                    html += '</div>';
                }
                
                html += '</div>';
                
                // Interpretations
                if (baseCase.Interpretation) {
                    html += `<div style="background: #d4edda; padding: 10px; border-radius: 5px; margin-bottom: 8px; font-size: 0.8rem; color: #155724;">`;
                    html += `<strong>Base Case:</strong> ${this.escapeHtml(baseCase.Interpretation)}`;
                    html += `</div>`;
                }
                if (stressCase.Interpretation) {
                    html += `<div style="background: #f8d7da; padding: 10px; border-radius: 5px; margin-bottom: 8px; font-size: 0.8rem; color: #721c24;">`;
                    html += `<strong>Stress Case:</strong> ${this.escapeHtml(stressCase.Interpretation)}`;
                    html += `</div>`;
                }
                if (impact && impact.Interpretation) {
                    html += `<div style="background: #fff3cd; padding: 10px; border-radius: 5px; font-size: 0.8rem; color: #856404;">`;
                    html += `<strong>Impact:</strong> ${this.escapeHtml(impact.Interpretation)}`;
                    html += `</div>`;
                }
            }
            
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    }
};

// Export for browser environment
window.AnalyticsRenderer = AnalyticsRenderer;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnalyticsRenderer;
}
