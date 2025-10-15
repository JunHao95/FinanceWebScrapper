# Advanced Financial Analytics Guide

This guide explains the four new advanced analytics features added to the FinanceWebScraper project.

## 📊 Overview

The new analytics module provides four sophisticated financial analysis capabilities:

1. **Linear Regression on Asset Returns** - Analyze relationship between stock returns and market benchmark
2. **Principal Component Analysis (PCA)** - Identify portfolio structure with data standardization
3. **Monte Carlo Simulation** - Estimate Value at Risk (VaR) and Expected Shortfall (ES)
4. **Correlation Analysis** - Understand relationships between assets

---

## 🚀 Quick Start

### Installation

First, install the required dependencies:

```bash
pip install -r requirements.txt
```

### Basic Usage

Run a comprehensive analysis on multiple stocks:

```bash
python analytics_demo.py --tickers AAPL,MSFT,GOOG,AMZN --all
```

---

## 📈 1. Linear Regression on Asset Returns

### What it does

Performs linear regression analysis using **returns** (not prices) to measure:
- **Beta**: Sensitivity to market movements
- **Alpha**: Excess return over market prediction
- **R-squared**: How well market explains stock movement
- **Information Ratio**: Risk-adjusted excess return

### Why Returns vs Prices?

- **Returns are stationary**: Prices have trends, returns don't
- **Comparability**: Returns are scale-independent
- **Statistical validity**: Regression assumptions hold better with returns
- **Economic meaning**: Investment decisions based on returns

### Usage

```bash
# Single analysis
python analytics_demo.py --tickers AAPL,MSFT,GOOG --regression

# Custom benchmark and period
python analytics_demo.py --tickers AAPL,MSFT --regression \
  --benchmark ^DJI --days 500
```

### Output Interpretation

```
AAPL:
  Beta........................... 1.2500
  Alpha (Annualized)............. 0.0523
  R-Squared...................... 0.7234
  Information Ratio.............. 0.4521
```

- **Beta > 1**: Stock amplifies market movements (more volatile)
- **Beta < 1**: Stock dampens market movements (less volatile)
- **Positive Alpha**: Outperforms market prediction
- **R-squared > 0.7**: Strong market correlation
- **Higher IR**: Better risk-adjusted excess returns

### Mathematical Details

The regression model is:

```
R_stock = α + β × R_market + ε

Where:
- R_stock: Daily stock returns
- R_market: Daily market returns
- α: Alpha (excess return)
- β: Beta (market sensitivity)
- ε: Residual (unexplained variation)
```

---

## 🔍 2. Principal Component Analysis (PCA)

### What it does

Reduces portfolio dimensionality to identify:
- **Main drivers** of portfolio variance
- **Component structure** showing which stocks move together
- **Diversification effectiveness**
- **Risk concentration**

### Data Standardization

**Critical step**: All returns are standardized to zero mean and unit variance before PCA:

```python
standardized_return = (return - mean) / std_dev
```

**Why standardize?**
- Makes stocks comparable regardless of price/volatility
- Prevents high-volatility stocks from dominating
- Required for PCA mathematical validity
- Standard practice in multivariate analysis

### Usage

```bash
# Basic PCA
python analytics_demo.py --tickers AAPL,MSFT,GOOG,AMZN,TSLA --pca

# With specific number of components
python analytics_demo.py --tickers AAPL,MSFT,GOOG,AMZN,TSLA,NVDA,META --pca --days 500
```

### Output Interpretation

```
Data Standardization:
  AAPL: Mean=0.001234, Std Dev=0.023456
  MSFT: Mean=0.001567, Std Dev=0.019876

Variance Explained by Components:
  PC1: 45.23% (Cumulative: 45.23%)
  PC2: 23.45% (Cumulative: 68.68%)
  PC3: 15.32% (Cumulative: 84.00%)

Component Interpretations:
PC1: Explains 45.23% of variance. 
     Top contributors: AAPL (positive, 0.456), MSFT (positive, 0.423), GOOG (positive, 0.398)
```

**Understanding Results:**
- **PC1 (First component)**: Usually represents "market factor" - overall market direction
- **PC2 (Second component)**: Often sector-specific movements
- **PC3+**: Idiosyncratic factors, company-specific events

**Practical Use:**
- If PC1 explains >70%: High correlation, poor diversification
- If need 5+ PCs for 90%: Good diversification
- Components with negative loadings: Natural hedges

### Mathematical Details

PCA solves the eigenvalue problem:

```
Σ × v = λ × v

Where:
- Σ: Covariance matrix of standardized returns
- v: Eigenvector (principal component direction)
- λ: Eigenvalue (variance explained)
```

---

## 🎲 3. Monte Carlo Simulation - VaR & Expected Shortfall

### What it does

Runs thousands of simulations to estimate:
- **Value at Risk (VaR)**: Maximum expected loss at confidence level
- **Expected Shortfall (ES)**: Average loss beyond VaR threshold
- **Probability distributions** of portfolio outcomes
- **Best/worst case scenarios**

### Usage

```bash
# Basic Monte Carlo
python analytics_demo.py --tickers AAPL,MSFT,GOOG --montecarlo

# Custom parameters
python analytics_demo.py --tickers AAPL,MSFT,GOOG --montecarlo \
  --simulations 50000 \
  --investment 500000 \
  --days 500
```

### Output Interpretation

```
Value at Risk (VaR):
VaR at 95% confidence:
  Value: $8,234.56
  Percentage: 8.23%
  Interpretation: With 95% confidence, the portfolio will not lose 
                  more than $8,234.56 (8.23%) over 252 days

Expected Shortfall (ES):
ES at 95% confidence:
  Value: $12,456.78
  Percentage: 12.46%
  Interpretation: If losses exceed VaR threshold, expected loss is 
                  $12,456.78 (12.46%)

Scenario Analysis:
  Expected Value................ $108,234.56
  Probability of Loss........... 42.34%
  Best Case..................... $145,678.90
  Worst Case.................... $67,890.12
```

**Key Metrics:**
- **VaR**: "I'm 95% confident I won't lose more than X"
- **ES**: "If I do lose more than VaR, I expect to lose Y on average"
- **ES > VaR**: Always true; ES accounts for tail risk
- **Lower confidence = Higher VaR**: 99% VaR > 95% VaR

### Why ES is Better than VaR

1. **VaR limitation**: Only tells threshold, not magnitude beyond it
2. **ES advantage**: Captures tail risk (extreme losses)
3. **Regulatory preference**: Basel III requires ES reporting
4. **Risk management**: ES is coherent risk measure, VaR is not

### Mathematical Details

Monte Carlo process:

```
For each simulation i in 1...N:
  For each day t in 1...T:
    r_t ~ N(μ, σ²)  # Sample from normal distribution
    V_t = V_{t-1} × (1 + r_t)  # Update portfolio value
  
  final_values[i] = V_T

VaR_α = Percentile(final_values, 1-α)
ES_α = Mean(final_values[final_values < VaR_α])
```

---

## 🔗 4. Correlation Analysis

### What it does

Calculates pairwise correlations between all assets:
- **Correlation matrix**: Complete correlation structure
- **High correlation pairs**: Assets moving together (>0.7)
- **Negative correlations**: Natural hedging opportunities (<-0.5)
- **Diversification score**: Overall portfolio diversification

### Usage

```bash
# Basic correlation
python analytics_demo.py --tickers AAPL,MSFT,GOOG,AMZN,TSLA --correlation

# Extended period
python analytics_demo.py --tickers AAPL,MSFT,GOOG,AMZN,TSLA --correlation --days 500
```

### Output Interpretation

```
Correlation Matrix:
Ticker      AAPL      MSFT      GOOG      AMZN      TSLA
AAPL      1.0000    0.7234    0.6543    0.5432    0.3456
MSFT      0.7234    1.0000    0.7890    0.6123    0.2987
GOOG      0.6543    0.7890    1.0000    0.6789    0.3123
AMZN      0.5432    0.6123    0.6789    1.0000    0.4567
TSLA      0.3456    0.2987    0.3123    0.4567    1.0000

Summary Statistics:
  Average Correlation........... 0.5234
  Diversification Score......... 0.4766
  Number of Assets.............. 5

Highly Correlated Pairs (> 0.7):
  MSFT-GOOG: 0.7890 - Strong positive correlation
  AAPL-MSFT: 0.7234 - Strong positive correlation

Interpretation: Moderate diversification. Correlation levels are acceptable. 
                No significant negative correlations found.
```

**Understanding Correlation Values:**
- **1.0**: Perfect positive correlation (move identically)
- **0.7-0.9**: Strong positive correlation
- **0.4-0.7**: Moderate correlation
- **0.0-0.4**: Weak correlation
- **-0.4-0.0**: Weak negative correlation
- **-0.7--0.4**: Moderate negative correlation
- **-1.0--0.7**: Strong negative correlation
- **-1.0**: Perfect negative correlation (move oppositely)

**Portfolio Implications:**
- **High average correlation**: Concentrated risk, poor diversification
- **Low average correlation**: Good diversification
- **Negative correlations**: Natural hedging, reduces overall risk
- **All positive correlations**: Portfolio vulnerable to market crashes

### Diversification Score

```
Diversification Score = 1 - |Average Correlation|

Score > 0.6: Excellent diversification
Score 0.4-0.6: Good diversification
Score 0.2-0.4: Moderate diversification
Score < 0.2: Poor diversification
```

---

## 🎯 Complete Analysis Example

Run all analyses together:

```bash
python analytics_demo.py \
  --tickers AAPL,MSFT,GOOG,AMZN,TSLA,NVDA \
  --all \
  --benchmark ^GSPC \
  --days 500 \
  --simulations 20000 \
  --investment 250000 \
  --save \
  --format json \
  --output-dir my_analysis
```

This will:
1. Run linear regression against S&P 500
2. Perform correlation analysis
3. Run PCA with 6 stocks
4. Simulate 20,000 Monte Carlo scenarios
5. Save all results to `my_analysis/` directory

---

## 💡 Practical Use Cases

### Use Case 1: Portfolio Risk Assessment

**Goal**: Understand total portfolio risk

```bash
# Your portfolio
python analytics_demo.py \
  --tickers AAPL,MSFT,GOOGL,AMZN,TSLA \
  --montecarlo \
  --investment 100000 \
  --simulations 50000
```

**Actions based on results:**
- High VaR/ES → Reduce position sizes or add hedges
- Low correlation → Portfolio is well diversified
- High correlation → Consider rebalancing

### Use Case 2: Stock Selection for Diversification

**Goal**: Add stocks that improve diversification

```bash
# Current portfolio + candidate stocks
python analytics_demo.py \
  --tickers AAPL,MSFT,GOOG,XOM,JPM,PFE \
  --correlation \
  --pca
```

**Look for:**
- Stocks with low correlation to existing holdings
- PCA showing stocks in different components
- Negative correlations for hedging

### Use Case 3: Beta Analysis for Market Timing

**Goal**: Understand market exposure

```bash
python analytics_demo.py \
  --tickers AAPL,TSLA,AMZN \
  --regression \
  --benchmark ^GSPC
```

**Interpretation:**
- High beta stocks (>1.2): Benefit in bull markets, hurt in bear markets
- Low beta stocks (<0.8): Defensive positions
- Mix betas based on market outlook

### Use Case 4: Regulatory Compliance

**Goal**: Calculate VaR and ES for regulatory reporting

```bash
python analytics_demo.py \
  --tickers YOUR_PORTFOLIO_TICKERS \
  --montecarlo \
  --simulations 100000 \
  --investment ACTUAL_PORTFOLIO_VALUE \
  --save \
  --format json
```

**For compliance:**
- Use 99% confidence level for Basel III
- Run daily for trading books
- Document methodology in saved results

---

## 📊 Integration with Existing Scrapers

The analytics module works seamlessly with existing scrapers:

### Example: Analyze Scraped Tickers

```python
# In main.py or custom script
from src.analytics.financial_analytics import FinancialAnalytics

# After scraping tickers
tickers = ['AAPL', 'MSFT', 'GOOG']

# Run comprehensive analysis
analytics = FinancialAnalytics()
results = analytics.comprehensive_analysis(
    tickers=tickers,
    benchmark='^GSPC',
    days=252,
    simulations=10000,
    initial_investment=100000
)

# Access individual analyses
regression = results['1. Linear Regression Analysis']
correlation = results['2. Correlation Analysis']
pca = results['3. PCA Analysis']
monte_carlo = results['4. Monte Carlo VaR & ES']
```

---

## 🔧 Advanced Configuration

### Custom Portfolio Weights for Monte Carlo

```python
from src.analytics.financial_analytics import FinancialAnalytics

analytics = FinancialAnalytics()

# Define custom weights (must sum to 1.0)
portfolio_weights = {
    'AAPL': 0.30,
    'MSFT': 0.25,
    'GOOG': 0.25,
    'AMZN': 0.20
}

results = analytics.monte_carlo_var_es(
    tickers=['AAPL', 'MSFT', 'GOOG', 'AMZN'],
    portfolio_weights=portfolio_weights,
    days=252,
    simulations=50000,
    initial_investment=500000
)
```

### Different Correlation Methods

```python
# Pearson (default) - assumes linear relationships
correlation_pearson = analytics.correlation_analysis(
    tickers=['AAPL', 'MSFT', 'GOOG'],
    method='pearson'
)

# Spearman - better for non-linear relationships
correlation_spearman = analytics.correlation_analysis(
    tickers=['AAPL', 'MSFT', 'GOOG'],
    method='spearman'
)

# Kendall - robust to outliers
correlation_kendall = analytics.correlation_analysis(
    tickers=['AAPL', 'MSFT', 'GOOG'],
    method='kendall'
)
```

---

## 📚 Technical Background

### Why These Four Analyses?

1. **Linear Regression**: Foundation of modern portfolio theory (CAPM model)
2. **PCA**: Reduces complexity, identifies risk factors (Fama-French models)
3. **Monte Carlo**: Industry standard for risk management (Basel accords)
4. **Correlation**: Core of diversification theory (Markowitz portfolio)

### Data Requirements

- **Minimum tickers**: 2 (for correlation, PCA)
- **Minimum history**: 30 days (preferably 252+ for annual cycle)
- **Recommended**: 252-500 trading days (1-2 years)
- **Data source**: Yahoo Finance via yfinance library

### Limitations & Considerations

1. **Historical Data Assumption**: Past ≠ future
2. **Normal Distribution**: Monte Carlo assumes normal returns (not always true)
3. **Linear Relationships**: Regression assumes linearity
4. **Stationarity**: Returns assumed stationary (constant statistics)
5. **No Transaction Costs**: Analysis ignores trading costs

### Best Practices

1. **Use returns, not prices** for all analyses
2. **Standardize data** before PCA
3. **Run enough simulations** (10,000+ for Monte Carlo)
4. **Use appropriate time horizon** (1 year minimum for annual patterns)
5. **Validate with different benchmarks** for robustness
6. **Combine multiple analyses** for comprehensive view
7. **Update regularly** as market conditions change

---

## 🐛 Troubleshooting

### Issue: "Insufficient data for analysis"

**Solution**: 
- Ensure tickers are valid and have sufficient history
- Try increasing `--days` parameter
- Check if market was open during selected period

### Issue: Monte Carlo simulations too slow

**Solution**:
- Reduce `--simulations` (10,000 is usually sufficient)
- Use fewer tickers
- Shorter forecast period

### Issue: PCA returns error "Need at least 2 assets"

**Solution**:
- Provide at least 2 tickers
- Check that all tickers have valid data
- Ensure no NaN values in returns

---

## 📖 References

### Academic Papers
- Markowitz, H. (1952). "Portfolio Selection"
- Sharpe, W. (1964). "Capital Asset Pricing Model"
- Jorion, P. (2007). "Value at Risk"

### Books
- "The Econometrics of Financial Markets" - Campbell, Lo, MacKinlay
- "Risk Management and Financial Institutions" - Hull
- "Quantitative Risk Management" - McNeil, Frey, Embrechts

### Online Resources
- [sklearn PCA documentation](https://scikit-learn.org/stable/modules/decomposition.html#pca)
- [NumPy statistical functions](https://numpy.org/doc/stable/reference/routines.statistics.html)
- [pandas correlation methods](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.corr.html)

---

## 🤝 Contributing

Contributions welcome! Possible enhancements:
- GARCH models for volatility forecasting
- Copula-based correlation analysis
- Factor models (Fama-French, Carhart)
- Time-varying correlation (DCC-GARCH)
- Portfolio optimization (efficient frontier)

---

## 📄 License

Same as main project - for educational purposes only.

---

**Happy Analyzing! 📊💹**
