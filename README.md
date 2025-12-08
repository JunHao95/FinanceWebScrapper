# Stock Financial Metrics Scraper

A high-performance Python application for scraping and analyzing financial metrics from multiple sources. Available as both a **CLI tool** and a **web application** with **advanced analytics**.

![Finance Data Platform Architecture](finance_data_platform.png)

> **🔗 Live Demo**: [https://finance-web-scrapper.onrender.com](https://finance-web-scrapper.onrender.com)  
> **⚡ Keep-Alive**: Automatic ping system prevents Render.com free tier spin-down. See [KEEP_ALIVE.md](KEEP_ALIVE.md)

---

## 🌟 Key Features

### Dual Interface
- **CLI Mode**: Automated analysis for scheduled runs
- **Web Interface**: Interactive browser-based analysis with tabbed layout

### Multi-Source Data Collection
- **Scrapers**: Yahoo Finance, Finviz, Google Finance
- **APIs**: Alpha Vantage, Finhub (API keys required)
- **Sentiment**: News, Reddit, Google Trends analysis
- **Indicators**: RSI, Moving Averages, Bollinger Bands, MACD

### Advanced Analytics
- **Linear Regression**: Beta/Alpha vs SPY benchmark
- **Correlation Analysis**: Diversification metrics
- **Monte Carlo**: Value at Risk (VaR) and Expected Shortfall (ES)
- **PCA**: Portfolio structure analysis (3+ stocks)

### Derivative Pricing
- **Options Models**: Black-Scholes, Binomial, Trinomial
- **Implied Volatility**: Newton-Raphson extraction
- **Greeks**: Delta, Gamma, Theta, Vega, Rho
- **Model Comparison**: Side-by-side convergence analysis

### Performance & Storage
- **Parallel Processing**: ThreadPoolExecutor with connection pooling
- **Fast Mode**: 90% speed boost
- **MongoDB**: Time series storage (CLI only)
- **Formats**: CSV, Excel, Text, HTML email reports

---

## 📦 Installation

```bash
# Clone and setup
git clone https://github.com/yourusername/stock-scraper.git
cd stock-scraper
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Optional: MongoDB (CLI only)
brew install mongodb-community
brew services start mongodb-community
python check_mongodb.py

# Configure
cp config.json.example config.json  # For CLI
# Or create .env file for web app
```

### Configuration Files

**`.env` (Web Mode)**:
```bash
ALPHA_VANTAGE_API_KEY=your_key
FINHUB_API_KEY=your_key
FINANCE_SENDER_EMAIL=your-email@gmail.com
FINANCE_SENDER_PASSWORD=your-app-password
SECRET_KEY=your-secret-key
PORT=5173
```

**`config.json` (CLI Mode)**: See `config.json.example`

---

## 🚀 Quick Start

### Web Application

```bash
./start_webapp.sh  # Unix/macOS
# Or: python webapp.py
# Windows: start_webapp.bat
```

**Usage**:
1. Enter tickers (e.g., `AAPL, MSFT, GOOG`)
2. Select data sources and enable indicators
3. Click **"🔍 Analyze Stocks"**
4. View results in **Tab 1: Stock Details** (CNN Fear & Greed, individual metrics)
5. Switch to **Tab 2: Advanced Analytics** for portfolio analysis
6. Optional: Email report

### CLI Mode

```bash
# Basic usage
python main.py --tickers AAPL,MSFT,GOOG

# With analytics
python main.py --tickers AAPL,MSFT --all --format excel

# Fast mode
python main.py --tickers AAPL,MSFT,GOOG --fast-mode --parallel --max-workers 8

# Email report
python main.py --tickers AAPL,MSFT --email recipient@example.com

# Automated runs
./run_scraper.sh        # Production
./uat_run_scraper.sh    # UAT/Testing
```

---

## 📊 Understanding the Interface

### Tab 1: Stock Details
- CNN Fear & Greed Index
- Individual stock cards with metrics
- Technical indicators and sentiment
- Stock count badge

### Tab 2: Advanced Analytics
Requires **2+ stocks** for portfolio analytics:
- **Correlation Matrix**: Diversification analysis
- **PCA**: Portfolio structure (3+ stocks required)
- **Regression vs SPY**: Beta, Alpha, R-Squared per ticker
- **Monte Carlo**: VaR, Expected Shortfall per ticker

**Visual Indicators**:
- Green "✓ Ready" badge when analytics available
- "No Analytics Available" if < 2 stocks analyzed

---

## 💹 Derivative Pricing

Access via web interface under **"💹 Options Pricing Calculator"**:

1. **Option Pricing**: Multi-model pricing (BS, Binomial, Trinomial)
2. **Implied Volatility**: Extract IV from market prices
3. **Greeks Calculator**: All sensitivities
4. **Model Comparison**: Compare all models

**Example Call Option**:
```
Spot: 100, Strike: 105, Maturity: 0.25 (3M)
Rate: 5%, Vol: 20%
Result: ~$4.00, Delta ≈ 0.55
```

---

## 🏗️ Project Structure

```
stock_scraper/
├── webapp.py              # Flask web app
├── main.py                # CLI entry point
├── requirements.txt
├── config.json            # CLI config
├── .env                   # Web config
├── templates/
│   └── index.html         # Tabbed interface
├── src/
│   ├── scrapers/          # Data collectors
│   ├── analytics/         # Advanced analytics
│   ├── derivatives/       # Options pricing
│   ├── indicators/        # Technical indicators
│   ├── sentiment/         # Sentiment analysis
│   └── utils/             # Utilities
├── logs/                  # Application logs
└── output/                # Generated reports
```

---

## 🔧 Advanced Analytics Explained

### Linear Regression vs SPY
- **Beta**: Market sensitivity (>1 = more volatile)
- **Alpha**: Excess returns above market
- **R-Squared**: Correlation strength with SPY
- **Interpretation**: High Beta + Positive Alpha = Aggressive growth

### Monte Carlo Simulation
- **VaR (95%)**: Max expected loss at 95% confidence
- **Expected Shortfall**: Average loss beyond VaR
- **Use**: Risk management and position sizing

### Correlation Analysis
- **Matrix**: Pairwise correlations
- **Diversification**: <0.7 = good diversification
- **Interpretation**: Near +1 = moves together, near 0 = independent

### PCA
- **Components**: Main drivers of portfolio variance
- **PC1 > 50%**: Single factor dominance
- **PC1 < 40%**: Well-diversified

---

## 🐛 Troubleshooting

**No analytics visible?**
- Click **"📈 Advanced Analytics"** tab
- Check for green "✓ Ready" badge
- Need 2+ stocks for analytics

**MongoDB connection failed?**
```bash
brew services list | grep mongodb
python check_mongodb.py
# Or disable in config.json
```

**API rate limits?**
- Alpha Vantage: 25 requests/day, 5/min
- Use `--sources yahoo finviz` instead

**Web app won't start?**
```bash
lsof -i :5173  # Check port
export PORT=8000  # Try different port
```

---

## 📊 Performance Benchmarks

- **Connection Pooling**: 30-40% faster
- **Parallel Processing**: 2-3x faster
- **Fast Mode**: Up to 90% reduction in time
- **Combined**: 5-10x faster than sequential

---

## 💡 Best Practices

### CLI Users
- Use ticker files for bulk: `--ticker-file tickers.txt`
- Enable fast mode: `--fast-mode --parallel`
- Schedule with cron for regular updates

### Web Users
- Set API keys in `.env` to avoid re-entering
- Analyze 2+ stocks for portfolio analytics
- Use "All Sources" for comprehensive data

### Analytics
- **2+ stocks** for correlation/regression
- **3+ stocks** for PCA analysis
- Beta >1 = more volatile than market
- Correlation <0.7 = good diversification

---

## 🎯 Use Cases

| Mode | Best For |
|------|----------|
| **CLI** | Scheduled runs, bulk analysis, MongoDB storage, scripting |
| **Web** | Interactive analysis, ad-hoc queries, visualization, sharing |
| **Analytics** | Portfolio risk, Beta/Alpha, diversification, Monte Carlo |

---

## 📝 Changelog

### Latest (Derivative Pricing Release)
- Derivative pricing: Black-Scholes, Binomial, Trinomial
- Implied volatility extraction with iteration tracking
- Greeks calculator (Delta, Gamma, Theta, Vega, Rho)
- Model comparison with convergence analysis

### Previous (Advanced Analytics)
- Linear regression vs SPY benchmark
- PCA, correlation, Monte Carlo VaR/ES
- Returns-based analysis throughout
- Tabbed web interface
- MongoDB CLI storage

---

## 📄 License

Educational purposes only. Check website terms before scraping.

---

## 📞 Support

- Open GitHub issue
- Check logs: `logs/webapp.log` or `logs/stock_scraper.log`
- Review troubleshooting section
- Browser console (F12) for frontend errors

---

**Happy Analyzing! 📈💹**