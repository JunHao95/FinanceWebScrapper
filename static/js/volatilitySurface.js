// ===========================
// Volatility Surface Module
// ===========================

const VolatilitySurface = {
    /**
     * Initialize volatility surface
     */
    init() {
        // Event listeners are handled via inline onclick in HTML
    },

    /**
     * Build volatility surface
     */
    async buildSurface() {
        const ticker = document.getElementById('volSurfTicker').value.trim().toUpperCase();
        const optionType = document.getElementById('volSurfOptionType').value;
        const riskFreeRate = parseFloat(document.getElementById('volSurfRiskFreeRate').value) / 100;
        const minVolume = parseInt(document.getElementById('volSurfMinVolume').value);
        const maxSpread = parseFloat(document.getElementById('volSurfMaxSpread').value) / 100;

        if (!ticker) {
            Utils.showAlert('Please enter a ticker symbol', 'error');
            return;
        }

        try {
            document.getElementById('volSurfaceLoading').style.display = 'block';
            document.getElementById('volSurfaceContainer').style.display = 'none';
            document.getElementById('atmTermStructureContainer').style.display = 'none';
            Utils.hideAlert();

            const data = await API.buildVolatilitySurface({
                ticker: ticker,
                option_type: optionType,
                risk_free_rate: riskFreeRate,
                min_volume: minVolume,
                max_spread_pct: maxSpread
            });

            if (data.success) {
                this.displayVolatilitySurface(data.surface);
                Utils.showAlert(`✅ Volatility surface built successfully! (${data.surface.data_points} options analyzed)`, 'success');
            } else {
                Utils.showAlert(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            Utils.showAlert('Failed to build volatility surface: ' + error.message, 'error');
        } finally {
            document.getElementById('volSurfaceLoading').style.display = 'none';
        }
    },

    /**
     * Display volatility surface
     */
    displayVolatilitySurface(surface) {
        const container = document.getElementById('volSurfaceContainer');
        const plotDiv = document.getElementById('volSurfacePlot');
        const metadataDiv = document.getElementById('volSurfaceMetadata');

        // Display metadata
        let metadataHTML = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">';
        metadataHTML += `<div><strong>Ticker:</strong> ${surface.ticker}</div>`;
        metadataHTML += `<div><strong>Current Price:</strong> $${surface.current_price.toFixed(2)}</div>`;
        metadataHTML += `<div><strong>Option Type:</strong> ${surface.option_type.toUpperCase()}</div>`;
        metadataHTML += `<div><strong>Data Points:</strong> ${surface.data_points}</div>`;
        metadataHTML += `<div><strong>IV Range:</strong> ${(surface.metadata.min_iv * 100).toFixed(1)}% - ${(surface.metadata.max_iv * 100).toFixed(1)}%</div>`;
        metadataHTML += `<div><strong>Avg IV:</strong> ${(surface.metadata.avg_iv * 100).toFixed(1)}%</div>`;
        metadataHTML += '</div>';
        
        if (surface.using_historical_data) {
            metadataHTML += '<div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; margin-top: 15px; border-radius: 4px;">';
            metadataHTML += '<strong>📊 Using Historical Data:</strong> Market is currently closed. ';
            metadataHTML += 'Displaying volatility surface from previous trading day\'s closing prices. ';
            metadataHTML += 'For live quotes, access during market hours (9:30 AM - 4:00 PM ET).';
            metadataHTML += '</div>';
        }
        
        metadataDiv.innerHTML = metadataHTML;

        // Prepare 3D surface data
        const surfaceData = [{
            type: 'surface',
            x: surface.surface_grid.strikes,
            y: surface.surface_grid.maturities,
            z: surface.surface_grid.implied_volatilities.map(row => 
                row.map(val => val !== null ? val * 100 : null)
            ),
            colorscale: [
                [0, 'rgb(0, 0, 255)'],
                [0.25, 'rgb(0, 255, 255)'],
                [0.5, 'rgb(0, 255, 0)'],
                [0.75, 'rgb(255, 255, 0)'],
                [1, 'rgb(255, 0, 0)']
            ],
            colorbar: {
                title: 'IV (%)',
                titleside: 'right',
                titlefont: { size: 14 }
            },
            hovertemplate: '<b>Strike:</b> $%{x:.2f}<br>' +
                           '<b>Maturity:</b> %{y:.3f} years<br>' +
                           '<b>Implied Vol:</b> %{z:.2f}%<br>' +
                           '<extra></extra>',
            contours: {
                z: {
                    show: true,
                    usecolormap: true,
                    highlightcolor: "limegreen",
                    project: {z: true}
                }
            }
        }];

        // Add scatter points for actual data
        const scatterData = {
            type: 'scatter3d',
            mode: 'markers',
            x: surface.raw_data.map(d => d.strike),
            y: surface.raw_data.map(d => d.time_to_maturity),
            z: surface.raw_data.map(d => d.implied_volatility * 100),
            marker: {
                size: 3,
                color: 'black',
                opacity: 0.6
            },
            hovertemplate: '<b>Strike:</b> $%{x:.2f}<br>' +
                           '<b>Maturity:</b> %{y:.3f} years<br>' +
                           '<b>IV:</b> %{z:.2f}%<br>' +
                           '<extra>Market Data</extra>',
            name: 'Market Data Points'
        };

        const layout = {
            title: {
                text: `${surface.ticker} ${surface.option_type.toUpperCase()} Implied Volatility Surface`,
                font: { size: 20, color: '#667eea' }
            },
            scene: {
                xaxis: {
                    title: 'Strike Price ($)',
                    titlefont: { size: 14 },
                    backgroundcolor: 'rgb(230, 230,230)',
                    gridcolor: 'white',
                    showbackground: true
                },
                yaxis: {
                    title: 'Time to Maturity (Years)',
                    titlefont: { size: 14 },
                    backgroundcolor: 'rgb(230, 230,230)',
                    gridcolor: 'white',
                    showbackground: true
                },
                zaxis: {
                    title: 'Implied Volatility (%)',
                    titlefont: { size: 14 },
                    backgroundcolor: 'rgb(230, 230,230)',
                    gridcolor: 'white',
                    showbackground: true
                },
                camera: {
                    eye: { x: 1.5, y: 1.5, z: 1.3 }
                }
            },
            autosize: true,
            margin: { l: 0, r: 0, b: 0, t: 40 },
            paper_bgcolor: 'white',
            plot_bgcolor: 'white'
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['toImage'],
            displaylogo: false
        };

        Plotly.newPlot(plotDiv, [surfaceData[0], scatterData], layout, config);
        container.style.display = 'block';
        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },

    /**
     * Show ATM term structure
     */
    async showATMTermStructure() {
        const ticker = document.getElementById('volSurfTicker').value.trim().toUpperCase();
        const optionType = document.getElementById('volSurfOptionType').value;
        const riskFreeRate = parseFloat(document.getElementById('volSurfRiskFreeRate').value) / 100;

        if (!ticker) {
            Utils.showAlert('Please enter a ticker symbol', 'error');
            return;
        }

        try {
            document.getElementById('volSurfaceLoading').style.display = 'block';
            document.getElementById('atmTermStructureContainer').style.display = 'none';
            Utils.hideAlert();

            const data = await API.getATMTermStructure({
                ticker: ticker,
                option_type: optionType,
                risk_free_rate: riskFreeRate
            });

            if (data.success) {
                this.displayATMTermStructure(data.term_structure, ticker, optionType);
                Utils.showAlert(`✅ ATM term structure extracted! (${data.term_structure.length} maturities)`, 'success');
            } else {
                Utils.showAlert(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            Utils.showAlert('Failed to extract ATM term structure: ' + error.message, 'error');
        } finally {
            document.getElementById('volSurfaceLoading').style.display = 'none';
        }
    },

    /**
     * Display ATM term structure
     */
    displayATMTermStructure(termStructure, ticker, optionType) {
        const container = document.getElementById('atmTermStructureContainer');
        const plotDiv = document.getElementById('atmTermStructurePlot');

        const trace = {
            type: 'scatter',
            mode: 'lines+markers',
            x: termStructure.map(d => d.time_to_maturity),
            y: termStructure.map(d => d.implied_volatility * 100),
            line: {
                color: '#667eea',
                width: 3
            },
            marker: {
                size: 10,
                color: '#764ba2',
                line: {
                    color: 'white',
                    width: 2
                }
            },
            hovertemplate: '<b>Maturity:</b> %{x:.3f} years<br>' +
                           '<b>ATM IV:</strong> %{y:.2f}%<br>' +
                           '<extra></extra>',
            name: 'ATM Volatility'
        };

        const layout = {
            title: {
                text: `${ticker} ${optionType.toUpperCase()} ATM Volatility Term Structure`,
                font: { size: 18, color: '#667eea' }
            },
            xaxis: {
                title: 'Time to Maturity (Years)',
                titlefont: { size: 14 },
                gridcolor: '#e0e0e0'
            },
            yaxis: {
                title: 'At-The-Money Implied Volatility (%)',
                titlefont: { size: 14 },
                gridcolor: '#e0e0e0'
            },
            hovermode: 'closest',
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            margin: { l: 60, r: 40, b: 60, t: 60 }
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false
        };

        Plotly.newPlot(plotDiv, [trace], layout, config);
        container.style.display = 'block';
        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VolatilitySurface;
}
