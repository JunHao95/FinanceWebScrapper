# Stock Financial Metrics Scraper

A high-performance Python application for scraping and analyzing financial metrics from multiple sources. Available as both a **CLI tool** and a **web application** with **advanced analytics**.

## 📊 System Architecture

![Finance Data Platform Architecture](finance_data_platform.png)

> **🔗 Live Demo**: [https://finance-web-scrapper.onrender.com](https://finance-web-scrapper.onrender.com)  
> **⚡ Keep-Alive**: Automatic ping system prevents Render.com free tier spin-down. See [KEEP_ALIVE.md](KEEP_ALIVE.md) for details.

## 🌟 Key Features

### Dual Interface
- **🖥️ CLI Mode**: Scriptable, automated analysis for scheduled runs
- **🌐 Web Interface**: Interactive browser-based analysis with tabbed interface

### Tabbed Web Interface
- **Tab 1 - Stock Details**: Individual stock metrics, technical indicators, CNN Fear & Greed Index
- **Tab 2 - Advanced Analytics**: Portfolio-level analytics with visual indicators showing when data is ready
- **Smart Organization**: Clean separation of individual stock data vs. portfolio analysis
- **Stock Count Badge**: Shows number of analyzed stocks at a glance

### High-Performance Architecture
- ⚡ **Parallel Processing**: Concurrent data fetching with ThreadPoolExecutor
- 🔄 **Connection Pooling**: HTTP connection reuse for faster execution
- 🚀 **Fast Mode**: 90% speed boost with optimized concurrent processing
- 📈 **Scalable**: Handles multiple tickers efficiently

### Multi-Source Data Collection
- **Scrapers**: Yahoo Finance, Finviz, Google Finance
- **APIs**: Alpha Vantage, Finhub (API keys required)
- **Sentiment**: News, Reddit, Google Trends analysis
- **Indicators**: RSI, Moving Averages, Bollinger Bands, MACD

### Advanced Financial Analytics
- **Linear Regression**: Beta, Alpha analysis vs SPY benchmark (returns-based)
- **Correlation Analysis**: Correlation matrix and diversification metrics
- **Monte Carlo Simulation**: Value at Risk (VaR) and Expected Shortfall (ES)
- **PCA Analysis**: Portfolio structure with data standardization (3+ stocks)

### Fundamental Analysis & Investment Rating
- **4-Category Scoring**: Valuation (P/E, P/B, P/S), Profitability (ROE, ROA, margins), Financial Health (debt ratios, liquidity), Growth (revenue/earnings trends)
- **Investment Outlook**: 0-10 scale with 6 ratings: Strong Buy (≥8.0), Buy (≥7.0), Moderate Buy (≥6.0), Hold (≥5.0), Moderate Sell (≥4.0), Sell (<4.0)
- **Smart Parsing**: Handles financial notation (125.82B, 99.58M) and flexible metric extraction
- **Actionable Insights**: Automated strengths/concerns identification and investment summary

### Derivative Pricing
- **Options Pricing Calculator**: Black-Scholes, Binomial, Trinomial models
- **Implied Volatility Engine**: Newton-Raphson IV extraction with validation
- **Greeks Calculator**: Delta, Gamma, Theta, Vega, Rho
- **Model Comparison**: Side-by-side pricing with convergence analysis
- **Volatility Surface Viewer**: Interactive 3D Plotly visualization
  - Real-time options data from Yahoo Finance (auto-fallback to historical when market closed)
  - 3D surface with rotation/zoom, color-coded IV heatmap
  - ATM volatility term structure charts
  - Data quality filters: moneyness, volume, bid-ask spread
  - Works 24/7 with automatic live/historical data switching

### Data Persistence
- 💾 **MongoDB Integration**: Automatic local storage of time series data (CLI only)
- 🔍 **Queryable History**: Fast retrieval with indexed fields
- 🚫 **Deduplication**: Unique indexes prevent duplicate records
- 📊 **Analytics Ready**: Data structured for analysis

### Output & Reporting
- Multiple formats: CSV, Excel, Text reports
- Email reports with HTML formatting
- Summary comparison reports
- Interactive web visualizations

---

## 📦 Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/stock-scraper.git
cd stock-scraper
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure MongoDB (Optional for CLI)
```bash
# Install MongoDB (macOS with Homebrew)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Or use Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Verify MongoDB is running
python check_mongodb.py
```

### 5. Set Up Configuration

#### For CLI Mode
Copy and configure `config.json`:
```bash
cp config.json.example config.json
# Edit config.json with your settings
```

#### For Web Mode
Create a `.env` file:
```bash
# API Keys (optional but recommended)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINHUB_API_KEY=your_finhub_key

# Email Configuration (required for email feature)
FINANCE_SENDER_EMAIL=your-email@gmail.com
FINANCE_SENDER_PASSWORD=your-app-password
FINANCE_SMTP_SERVER=smtp.gmail.com
FINANCE_SMTP_PORT=587
FINANCE_USE_TLS=True

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=False
PORT=5173
```

**Gmail Users**: Use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

---

## 🚀 Quick Start

### Web Application (Recommended for Interactive Use)

#### Starting the Web App

**Unix/macOS/Linux:**
```bash
chmod +x start_webapp.sh
./start_webapp.sh
```

**Windows:**
```cmd
start_webapp.bat
```

**Direct Python:**
```bash
python webapp.py
```

The web app will start on `http://localhost:5173`

#### Using the Tabbed Web Interface

1. **Enter Ticker Symbols**
   - Type stock ticker symbols separated by commas
   - Example: `AAPL, MSFT, GOOG, TSLA`

2. **Select Data Sources**
   - Choose "All Sources" for comprehensive analysis, or
   - Select specific sources (Yahoo Finance, Finviz, etc.)
   - Enable "Technical Indicators" and "Sentiment Analysis"

3. **Add API Keys** (Optional)
   - Enter Alpha Vantage API key for technical indicators
   - Enter Finhub API key for additional data
   - Or set them in `.env` file

4. **Analyze & View Results**
   - Click "🔍 Analyze Stocks"
   - Results appear in **Tab 1: Stock Details** (default view)
     - Shows CNN Fear & Greed Index
     - Individual stock cards with all metrics
     - Stock count badge shows number of analyzed stocks
   
5. **View Advanced Analytics**
   - Click **"� Advanced Analytics"** tab to see:
     - Correlation Analysis (2+ stocks)
     - PCA Analysis (3+ stocks)
     - Linear Regression vs SPY (per ticker)
     - Monte Carlo VaR/ES Analysis (per ticker)
   - Green "✓ Ready" badge appears when analytics are available

6. **Email Report** (Optional)
   - Enter email address
   - Add CC/BCC recipients if needed
   - Click "📨 Send Email Report"

### CLI Mode (For Automation & Scripting)

#### Basic Usage
```bash
# Single ticker
python main.py --tickers AAPL

# Multiple tickers
python main.py --tickers AAPL,MSFT,GOOG

# From file
python main.py --ticker-file tickers.txt

# With analytics
python main.py --tickers AAPL,MSFT,GOOG --all

# Email report
python main.py --tickers AAPL,MSFT --email recipient@example.com
```

#### Performance Mode
```bash
# Fast mode with parallel processing
python main.py --tickers AAPL,MSFT,GOOG --fast-mode --parallel

# High-performance with custom workers
python main.py --tickers AAPL,MSFT,GOOG,AMZN,TSLA,NVDA,META,NFLX \
  --fast-mode --parallel --max-workers 8 --format excel --summary
```

#### Automated Runs
```bash
./run_scraper.sh        # Production run
./uat_run_scraper.sh    # UAT/Testing run
```

---

## 🎯 Understanding the Tabbed Interface

### Tab 1: 📊 Stock Details (Default View)
**Shows individual stock information:**
- CNN Fear & Greed Index (market sentiment)
- Stock count badge (e.g., "2" for 2 stocks)
- Individual stock cards with:
  - Basic info (price, market cap, company name)
  - Valuation metrics (P/E, P/B, PEG, etc.)
  - Technical indicators (RSI, Moving Averages, MACD)
  - Sentiment analysis
  - Performance metrics

### Tab 2: 📈 Advanced Analytics
**Shows portfolio-level analytics:**
- **Correlation Analysis**: How stocks move together
- **PCA Analysis**: Portfolio structure (requires 3+ stocks)
- **Per-Ticker Analytics**:
  - **Regression vs SPY**: Beta, Alpha, R-Squared, Correlation
  - **Monte Carlo Analysis**: VaR, Expected Shortfall, scenarios

**Visual Indicators:**
- **Green "✓ Ready" badge**: Appears when analytics are available
- **"No Analytics Available" message**: Shows when:
  - Only 1 stock analyzed (need 2+ for portfolio analytics)
  - Analytics computation failed
  - No data available

### Navigation Tips
- **Default view**: Tab 1 (Stock Details) loads first
- **Quick switching**: Click tab buttons to switch views
- **Active tab indicator**: Purple bottom border and text
- **Stock count**: Badge on Tab 1 shows number of analyzed stocks
- **Smooth animations**: Content fades in when switching tabs

---

## 🔧 Advanced Analytics Explained

### Linear Regression vs SPY
**Purpose**: Understand how each stock moves relative to the S&P 500 benchmark

**Key Metrics:**
- **Beta**: Market sensitivity (Beta > 1 = more volatile than market)
- **Alpha**: Excess returns above market (positive = outperforming)
- **R-Squared**: How well returns correlate with SPY (higher = stronger relationship)
- **Correlation**: Direction of relationship (-1 to +1)

**Interpretation**:
- High Beta + Positive Alpha = Aggressive growth stock
- Low Beta + Positive Alpha = Stable outperformer
- High Beta + Negative Alpha = Volatile underperformer

### Monte Carlo Simulation
**Purpose**: Estimate potential losses under adverse market conditions

**Key Metrics:**
- **VaR (95%)**: Maximum expected loss at 95% confidence over 1 day
- **Expected Shortfall (ES)**: Average loss beyond VaR threshold
- **Best/Worst Case**: Potential outcomes in simulations

**Interpretation**:
- VaR: "95% confident we won't lose more than X% tomorrow"
- ES: "If we exceed VaR, average additional loss is Y%"
- Use for risk management and position sizing

### Correlation Analysis
**Purpose**: Measure diversification and portfolio risk

**Key Metrics:**
- **Correlation Matrix**: Pairwise correlations between stocks
- **Diversification Score**: Portfolio diversification quality

**Interpretation**:
- Correlation near +1: Stocks move together (low diversification)
- Correlation near 0: Independent movements (good diversification)
- Correlation near -1: Opposite movements (excellent hedge)

### PCA (Principal Component Analysis)
**Purpose**: Identify main drivers of portfolio variation

**Key Metrics:**
- **PC1, PC2, PC3**: Principal components explaining portfolio variance
- **Explained Variance**: How much variation each component captures

**Interpretation**:
- PC1 > 50%: Portfolio driven by single factor (market beta)
- PC1 < 40%: Well-diversified with multiple factors
- Use to understand portfolio concentration risk

---

## � Deployment & Keep-Alive

### Render.com Deployment

This app is deployed on Render.com free tier at: **https://finance-web-scrapper.onrender.com**

### Keep-Alive Solutions ⚡

Render.com free tier spins down after 15 minutes of inactivity. We've implemented **3 keep-alive solutions**:

#### 1. **Client-Side Keep-Alive** (Built-in) ✅
- Automatically pings server every 10 minutes when web page is open
- No setup required - works out of the box
- Pauses when tab is hidden to save resources

#### 2. **GitHub Actions Keep-Alive** (Recommended for 24/7) ⭐
- Automated workflow pings server every 10 minutes
- Completely free (GitHub Actions free tier)
- Works even when no one is using the website
- Setup: Just enable GitHub Actions in your repo

#### 3. **Python Keep-Alive Script**
- Standalone script for custom hosting
- Run on any always-on server
- Full control over ping intervals

**For detailed setup instructions, see**: [KEEP_ALIVE.md](KEEP_ALIVE.md)

---

## �🐛 Troubleshooting

### Common Issues

#### 1. "I don't see analytics!"
**Solution**: Click the **"📈 Advanced Analytics"** tab at the top of results

**Why**: Analytics are in Tab 2, which is hidden by default. Tab 1 (Stock Details) shows first.

**Check for**: Green "✓ Ready" badge on Advanced Analytics tab - if present, analytics are loaded and ready to view.

#### 2. "Analytics tab says 'No Analytics Available'"
**Causes**:
- Only 1 stock analyzed (need 2+ for portfolio analytics)
- Backend couldn't compute analytics (check logs)
- Analytics data empty in API response

**Solution**:
```bash
# Check backend logs
tail -50 logs/webapp.log | grep -i "analytics"

# Should see: "Analytics computed: ['correlation', ...]"
```

#### 3. MongoDB Connection Failed (CLI)
```bash
# Check if MongoDB is running
brew services list | grep mongodb
# Or
docker ps | grep mongo

# Verify connection
python check_mongodb.py

# Disable MongoDB if not needed
# In config.json, set "mongodb.enabled" to false
```

#### 4. Web App Won't Start
```bash
# Check if port is in use
lsof -i :5173

# Try different port
export PORT=8000
python webapp.py

# Check Flask is installed
pip install flask
```

#### 5. API Rate Limits
- **Alpha Vantage**: Free tier = 25 requests/day, 5 calls/minute
- **Solution**: Use `--sources yahoo finviz` instead
- **Or**: Enable `fallback_to_yahoo` in config.json

#### 6. Email Not Sending
```bash
# Check .env file exists
ls -la .env

# For Gmail, use App Password, not regular password
# Enable "Less secure app access" if needed

# Test email configuration
python -c "from src.utils.email_utils import send_consolidated_report; print('Email module loaded successfully')"
```

#### 7. Volatility Surface Issues

**"Could not calculate IV for any options"**
- **Market Closed**: Normal behavior outside trading hours (9:30 AM - 4:00 PM ET)
- **Solution**: Feature automatically uses historical data (previous day's lastPrice)
- **Yellow Banner**: Appears when using historical data, explains data source
- **Test During Market Hours**: For live quotes, access during trading hours

**"No options with valid quotes"**
- **Cause**: All bid/ask prices are $0.00 (market makers not posting quotes)
- **Solution**: Wait for market hours or use more liquid tickers (SPY, QQQ, AAPL)
- **Check Filters**: Try `min_volume: 0` and `max_spread_pct: 0.50` for maximum coverage

**"JSON.parse error" or blank surface**
- **Fixed**: NaN/Inf values now converted to null for valid JSON
- **Solution**: Update to latest version with enhanced `convert_numpy_types()`
- **Verify**: `webapp.py` should handle NaN/Inf in float conversion

**Surface looks sparse or incomplete**
- **Cause**: Not enough options data points (illiquid ticker or extreme filters)
- **Solution**: 
  - Use liquid tickers: SPY (best), QQQ, AAPL, MSFT, TSLA
  - Reduce `min_volume` to 0
  - Increase `max_spread_pct` to 50%
- **Expected**: 200-500+ data points for quality surface

**Deep ITM options pricing errors**
- **Normal**: Some deep ITM options have market_price < intrinsic_value
- **Handled**: Skipped with 5% tolerance, logged as debug (not errors)
- **Impact**: Minimal, surface built from remaining valid options

---

## 🏗️ Project Structure

```
stock_scraper/
│
├── webapp.py                         # Flask web application
├── main.py                           # CLI application
├── requirements.txt                  # Python dependencies
├── config.json                       # CLI configuration
├── .env                              # Web app environment variables
├── start_webapp.sh                   # Unix/macOS startup script
├── start_webapp.bat                  # Windows startup script
├── run_scraper.sh                    # Production CLI script
├── uat_run_scraper.sh                # UAT CLI script
├── diagnose_volatility_surface.py    # Volatility surface diagnostics
├── validate_volatility_surface.py    # Volatility surface validation
│
├── templates/                        # Web application templates
│   └── index.html                    # Main web interface (with volatility surface viewer)
│
├── src/                              # Source code
│   ├── derivatives/                  # Derivative pricing modules
│   │   ├── options_pricer.py         # Black-Scholes, Binomial, Trinomial
│   │   ├── implied_volatility.py     # IV extraction engine
│   │   ├── volatility_surface.py     # 3D surface builder (445 lines)
│   │   └── trinomial_model.py        # Trinomial tree implementation
│   ├── scrapers/                     # Web scraper modules
│   ├── analytics/                    # Financial analytics
│   ├── indicators/                   # Technical indicators
│   ├── sentiment/                    # Sentiment analysis
│   └── utils/                        # Utility functions
│
├── data/                             # Data storage
├── output/                           # Output files
├── logs/                             # Log files
└── tests/                            # Test modules
```

---

## 📊 Performance Benchmarks

### Speed Improvements
- **Connection Pooling**: 30-40% faster
- **Parallel Processing**: 2-3x faster for multiple tickers
- **Fast Mode**: Up to 90% reduction in execution time
- **Combined**: 5-10x faster than sequential without pooling

### Scalability
- **Concurrent Workers**: Supports 8-12 parallel workers efficiently
- **Memory Efficient**: Connection reuse reduces overhead

---

## 💡 Tips & Best Practices

### For Web Users
1. **Analyze 2+ stocks** to see portfolio analytics in Tab 2
2. **Look for "✓ Ready" badge** on Analytics tab when data is available
3. **Click Analytics tab** to view advanced metrics (hidden by default)
4. **Set API keys in .env** to avoid entering each time
5. **Use stock count badge** to verify all tickers processed

### For CLI Users
1. **Use ticker files** for large batches: `--ticker-file tickers.txt`
2. **Enable fast mode** for speed: `--fast-mode --parallel`
3. **Save bandwidth** with selective sources: `--sources yahoo finviz`
4. **Schedule runs** with cron for regular updates
5. **Monitor MongoDB** with `check_mongodb.py` after runs

### For Analytics
1. **Minimum 2 stocks** required for correlation and portfolio analytics
2. **3+ stocks** recommended for PCA analysis
3. **Beta interpretation**: >1 = more volatile, <1 = less volatile than market
4. **VaR use case**: Risk management and position sizing
5. **Correlation insights**: <0.7 = good diversification

### For Volatility Surface
1. **Use liquid tickers** for best results: SPY, QQQ, AAPL, MSFT, TSLA
2. **Set min_volume: 0** for maximum data coverage (recommended)
3. **Set max_spread_pct: 0.50** (50%) for realistic options filtering
4. **Expect 30-60 seconds** processing time for data fetching and interpolation
5. **Market hours**: Access during 9:30 AM - 4:00 PM ET for live quotes
6. **Historical fallback**: Feature works 24/7, auto-switches to previous day data when market closed
7. **Interpret patterns**: Look for volatility smile, term structure, and skew

---

## 🎯 Use Cases

### CLI Mode Best For:
- Scheduled/automated runs (cron jobs)
- Bulk analysis (large ticker lists)
- Data collection with MongoDB
- Batch reports
- Scripting and integration

### Web Mode Best For:
- Interactive analysis
- Ad-hoc queries
- Tabbed visualization
- Sharing with non-technical users
- Quick email reports

### Analytics Mode Best For:
- Portfolio risk assessment
- Beta/Alpha analysis
- Diversification analysis
- Monte Carlo simulations
- Quantitative research

---

## 📄 License

This project is for educational purposes. Web scraping may violate terms of service of some websites. Use responsibly and check each website's terms before scraping.

---

## 📝 Changelog

### Latest Updates (Volatility Surface Release - December 2025)
- 🆕 **Interactive Volatility Surface Viewer**: 3D Plotly visualization with rotation/zoom
- 🆕 **Real-Time Options Data**: Yahoo Finance integration with live options chain
- 🆕 **Historical Data Fallback**: Auto-detects market closure, uses previous day's lastPrice
- 🆕 **Data Quality Filters**: Moneyness (70%-130%), bid/ask validation, spread filtering
- 🆕 **ATM Term Structure**: Extract at-the-money volatility across maturities
- 🆕 **NaN-Safe JSON Serialization**: Handles scipy interpolation edge cases (NaN/Inf → null)
- 🆕 **Market Status Warnings**: Yellow banner when using historical data
- ✅ **Production-Ready**: Works 24/7 with automatic live/historical data switching
- ✅ **Comprehensive Testing**: Diagnostics and validation tools included

### Previous Updates (Derivative Pricing Release)
- 🆕 **Options Pricing Calculator**: Black-Scholes, Binomial, Trinomial models
- 🆕 **Implied Volatility Engine**: Newton-Raphson IV extraction with validation
- 🆕 **Greeks Calculator**: Delta, Gamma, Theta, Vega, Rho
- 🆕 **Model Comparison**: Side-by-side pricing with convergence analysis

### Earlier Updates (Advanced Analytics Release)
- ✅ **Tabbed Interface**: Clean 2-tab layout (Stock Details + Advanced Analytics)
- ✅ **Advanced Analytics**: Linear regression, PCA, Monte Carlo, correlation
- ✅ **Returns-based Analysis**: All analytics use returns instead of prices
- ✅ **MongoDB Storage**: CLI-only time series persistence
- ✅ **Email Reporting**: HTML reports with analytics
- ✅ **Performance Optimization**: Parallel processing, connection pooling

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check troubleshooting section above
- Review logs: `logs/webapp.log` (web) or `logs/stock_scraper.log` (CLI)
- Check browser console (F12) for frontend errors

---

**Happy Analyzing! 📈💹**

## 📦 Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/stock-scraper.git
cd stock-scraper
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure MongoDB (Optional for CLI)
```bash
# Install MongoDB (macOS with Homebrew)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Or use Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Verify MongoDB is running
python check_mongodb.py
```

### 5. Set Up Configuration

#### For CLI Mode
Copy and configure `config.json`:
```bash
cp config.json.example config.json
# Edit config.json with your settings
```

Example `config.json`:
```json
{
  "mongodb": {
    "enabled": true,
    "connection_string": "mongodb://localhost:27017/",
    "database": "stock_data"
  },
  "alpha_vantage": {
    "mode": "time_series_daily",
    "fallback_to_yahoo": true,
    "batch_size": 100,
    "enable_retry_on_rate_limit": true
  },
  "email": {
    "enabled": true
  }
}
```

#### For Web Mode
Create a `.env` file:
```bash
# API Keys (optional but recommended)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINHUB_API_KEY=your_finhub_key

# Email Configuration (required for email feature)
FINANCE_SENDER_EMAIL=your-email@gmail.com
FINANCE_SENDER_PASSWORD=your-app-password
FINANCE_SMTP_SERVER=smtp.gmail.com
FINANCE_SMTP_PORT=587
FINANCE_USE_TLS=True

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=False
PORT=5173
```

**Gmail Users**: Use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

---

## 🚀 Quick Start

### Web Application (Recommended for Interactive Use)

#### Starting the Web App

**Option 1: Using the startup script (Unix/macOS/Linux)**
```bash
chmod +x start_webapp.sh
./start_webapp.sh
```

**Option 2: Using Python directly**
```bash
python webapp.py
```

**Option 3: Windows**
```cmd
start_webapp.bat
```

The web app will start on `http://localhost:5173`

#### Using the Web Interface

1. **Enter Ticker Symbols**
   - Type one or more stock ticker symbols separated by commas
   - Example: `AAPL, MSFT, GOOG, TSLA`

2. **Select Data Sources**
   - Choose "All Sources" for comprehensive analysis, or
   - Select specific sources (Yahoo Finance, Finviz, etc.)
   - Enable "Technical Indicators" and "Sentiment Analysis"

3. **Add API Keys** (Optional)
   - Enter Alpha Vantage API key for technical indicators
   - Enter Finhub API key for additional data
   - Or set them in `.env` file

4. **Analyze**
   - Click "🔍 Analyze Stocks"
   - View results organized by category

5. **Email Report** (Optional)
   - Enter email address
   - Add CC/BCC recipients if needed
   - Click "📨 Send Email Report"

### CLI Mode (For Automation & Scripting)

#### Basic Usage
```bash
# Single ticker
python main.py --tickers AAPL

# Multiple tickers
python main.py --tickers AAPL,MSFT,GOOG

# From file
python main.py --ticker-file tickers.txt

# Specific sources
python main.py --tickers MSFT --sources yahoo finviz

# With API keys
python main.py --tickers GOOGL --sources alphavantage finhub \
  --alpha-key YOUR_KEY --finhub-key YOUR_KEY

# Technical indicators
python main.py --tickers AAPL --sources technical --alpha-key YOUR_KEY

# Save as Excel
python main.py --tickers GOOGL --output-dir output --format excel

# Email report
python main.py --tickers AAPL,MSFT --email recipient@example.com
```

#### Performance Mode
```bash
# Fast mode with parallel processing
python main.py --tickers AAPL,MSFT,GOOG --fast-mode --parallel

# High-performance with custom workers
python main.py --tickers AAPL,MSFT,GOOG,AMZN,TSLA,NVDA,META,NFLX \
  --fast-mode --parallel --max-workers 8 --format excel --summary
```

#### Automated Runs
```bash
# Using the provided scripts
./run_scraper.sh        # Production run
./uat_run_scraper.sh    # UAT/Testing run
```

---

## 📖 Detailed Usage

### CLI Command Line Arguments

#### Basic Arguments
- `--tickers`: Comma-separated stock ticker symbols
- `--ticker-file`: File containing tickers (one per line)
- `--output-dir`: Directory for output files (default: output)
- `--sources`: Data sources to use (yahoo, finviz, google, alphavantage, finhub, technical, enhanced_sentiment, all)
- `--format`: Output format (csv, excel, text)
- `--interactive`: Run in interactive mode

#### Performance Arguments
- `--parallel`: Enable parallel processing
- `--fast-mode`: Enable fast mode (90% speed boost)
- `--max-workers`: Maximum parallel workers (default: 8)
- `--delay`: Delay between API requests in seconds

#### API & Authentication
- `--alpha-key`: Alpha Vantage API key
- `--finhub-key`: Finhub API key

#### Reporting
- `--display-mode`: Results display (table, grouped)
- `--email`: Email addresses for report (comma-separated)
- `--cc`: CC email addresses
- `--bcc`: BCC email addresses
- `--summary`: Generate summary report for all tickers

#### Logging
- `--logging`: Enable/disable logging (true, false)
- `--log-level`: Logging level (debug, info, warning, error, critical)
- `--saveReports`: Save reports to files (true, false)

### MongoDB Time Series Storage (CLI Only)

**Important**: MongoDB storage is **only active in CLI mode** (via `run_scraper.sh` or `uat_run_scraper.sh`). The web application does **NOT** store data to MongoDB to keep web requests lightweight and fast.

#### Features
- **Automatic Storage**: Data saved during each CLI scraper run
- **Deduplication**: Unique compound index on (ticker, date)
- **Fast Queries**: Indexed fields for efficient retrieval
- **Graceful Degradation**: CLI continues working if MongoDB unavailable

#### Configuration

Edit `config.json`:
```json
{
  "mongodb": {
    "enabled": true,
    "connection_string": "mongodb://localhost:27017/",
    "database": "stock_data"
  }
}
```

#### Verifying MongoDB Data

**Method 1: Quick Verification Script**
```bash
python check_mongodb.py
```

**Method 2: MongoDB Shell**
```bash
# Connect to MongoDB
mongosh stock_data

# Check total records
db.timeseries.countDocuments({})

# View recent records
db.timeseries.find().sort({last_updated: -1}).limit(5).pretty()

# Check specific ticker
db.timeseries.find({ticker: "AAPL"}).sort({date: -1}).limit(5).pretty()

# Count records per ticker
db.timeseries.aggregate([
  {$group: {_id: "$ticker", count: {$sum: 1}}},
  {$sort: {count: -1}}
])
```

**Method 3: Python Query**
```python
from src.utils.mongodb_storage import MongoDBStorage

mongodb = MongoDBStorage()
df = mongodb.get_timeseries_data('AAPL')
print(df.head())
mongodb.close()
```

#### Database Schema

**timeseries collection**:
```javascript
{
  ticker: "AAPL",
  date: ISODate("2025-10-08"),
  open: 256.53,
  high: 258.52,
  low: 256.11,
  close: 258.24,
  volume: 15894056,
  last_updated: ISODate("..."),
  run_id: "run_20251008_103000"
}
```

**Indexes**:
- Unique compound: `(ticker, date)`
- Single: `ticker`
- Single: `date`

---

## 🏗️ Architecture

### Project Structure
```
stock_scraper/
│
├── webapp.py                # Flask web application entry point
├── main.py                  # CLI application entry point
├── analytics_demo.py        # 🆕 Advanced analytics demo script
├── analytics_examples.py    # 🆕 Quick analytics examples
├── ANALYTICS_GUIDE.md       # 🆕 Comprehensive analytics documentation
├── start_webapp.sh          # Unix/macOS web app startup script
├── start_webapp.bat         # Windows web app startup script
├── run_scraper.sh           # Production CLI run script
├── uat_run_scraper.sh       # UAT CLI run script
├── requirements.txt         # Python dependencies
├── config.json              # Configuration (CLI mode)
├── config.json.example      # Configuration template
├── .env                     # Environment variables (Web mode)
│
├── templates/               # Web application templates
│   └── index.html           # Main web interface
│
├── src/                     # Source code
│   ├── scrapers/            # Web scraper modules
│   │   ├── base_scraper.py
│   │   ├── yahoo_scraper.py
│   │   ├── finviz_scraper.py
│   │   ├── google_scraper.py
│   │   ├── cnn_scraper.py
│   │   ├── api_scraper.py   # Alpha Vantage & Finhub
│   │   └── enhanced_sentiment_scraper.py
│   │
│   ├── analytics/           # 🆕 Advanced financial analytics
│   │   ├── __init__.py
│   │   └── financial_analytics.py
│   │
│   ├── indicators/          # Technical indicators
│   │   └── technical_indicators.py
│   │
│   ├── sentiment/           # Sentiment analysis
│   │   └── sentiment_analyzer.py
│   │
│   └── utils/               # Utility functions
│       ├── request_handler.py    # HTTP connection pooling
│       ├── data_formatter.py     # Data formatting
│       ├── display_formatter.py  # Output display
│       ├── email_utils.py        # Email reporting
│       └── mongodb_storage.py    # MongoDB storage (CLI only)
│
├── data/                    # Data storage
├── output/                  # Output files
├── analytics_output/        # 🆕 Analytics results
├── logs/                    # Log files
├── tests/                   # Test modules
└── trends_cache/            # Google Trends cache
```

### Key Design Decisions

1. **Dual Interface Design**
   - CLI for automation, scripting, scheduled runs
   - Web for interactive analysis and exploration
   - Shared core scrapers and utilities

2. **MongoDB Storage Strategy**
   - **CLI Only**: MongoDB stores historical data for long-term analysis
   - **Web App**: No MongoDB storage to keep requests fast and lightweight
   - Configurable via `config.json` and `webapp_config`

3. **Data Serialization**
   - NumPy types converted to native Python types before JSON serialization
   - Ensures compatibility with Flask's `jsonify()` function
   - Prevents "Object of type int64 is not JSON serializable" errors

4. **Performance Optimizations**
   - Connection pooling for HTTP requests
   - Parallel processing with configurable worker pools
   - Fast mode with reduced delays and concurrent processing

---

## 🔧 Configuration

### Environment Variables

#### Performance Settings
```bash
# Connection pooling
export CONNECTION_POOL_SIZE=20
export CONNECTION_POOL_MAXSIZE=20
export ENABLE_CONNECTION_POOLING=true

# Performance monitoring
export PERFORMANCE_MONITORING=true
```

#### API Keys
```bash
# Alpha Vantage API
export ALPHA_VANTAGE_API_KEY=your_key_here

# Finhub API
export FINHUB_API_KEY=your_key_here
```

#### Email Configuration
```bash
export FINANCE_SENDER_EMAIL=your-email@gmail.com
export FINANCE_SENDER_PASSWORD=your-app-password
export FINANCE_SMTP_SERVER=smtp.gmail.com
export FINANCE_SMTP_PORT=587
export FINANCE_USE_TLS=True
```

---

## 🎯 Use Cases

### CLI Mode Best For:
- **Scheduled/Automated Runs**: Cron jobs, task schedulers
- **Bulk Analysis**: Processing large lists of tickers
- **Data Collection**: Building historical databases with MongoDB
- **Batch Reports**: Generating reports for multiple tickers
- **Scripting**: Integration with other tools and workflows

### Web Mode Best For:
- **Interactive Analysis**: Real-time stock exploration
- **Ad-hoc Queries**: Quick checks on specific tickers
- **Visualization**: Viewing organized, categorized data
- **Sharing**: Easy access for non-technical users
- **Quick Reports**: Instant email reports without command line

### Analytics Mode Best For: 🆕
- **Portfolio Risk Assessment**: VaR, Expected Shortfall calculations
- **Beta/Alpha Analysis**: Understanding market relationships
- **Diversification Analysis**: Correlation matrices and PCA
- **Monte Carlo Simulations**: Risk scenario modeling
- **Quantitative Research**: Statistical analysis of returns

---

## 📊 Performance Benchmarks

### Speed Improvements
- **Connection Pooling**: 30-40% faster than without pooling
- **Parallel Processing**: 2-3x faster for multiple tickers
- **Fast Mode**: Up to 90% reduction in execution time
- **Combined**: 5-10x faster than sequential without pooling

### Scalability
- **Concurrent Workers**: Supports 8-12 parallel workers efficiently
- **Connection Pools**: 20 pools with 20 connections each
- **Memory Efficient**: Connection reuse reduces overhead
- **Rate Limit Handling**: Intelligent backoff and retry

---

## 💹 Derivative Pricing Features

Advanced **Options Pricing Calculator** and **Implied Volatility Extraction Engine** based on academic-grade derivative pricing methodologies.

### Features Overview

#### 1. **Options Pricing Calculator**

Multi-model pricing engine supporting three industry-standard models:

- **Black-Scholes Model**: Analytical pricing for European options with full Greeks (Delta, Gamma, Theta, Vega, Rho)
- **Binomial Tree Model**: Discrete-time model supporting both European and American options with configurable steps (10-500)
- **Trinomial Tree Model**: Enhanced convergence with three-way branching (up/down/middle)

#### 2. **Implied Volatility Extraction Engine**

Newton-Raphson algorithm for extracting implied volatility from market prices:
- Iterative convergence tracking for educational visualization
- Automatic validation via re-pricing
- Convergence history with iteration details
- Bounded search (σ ∈ [1%, 500%])

#### 3. **Greeks Calculator**

Standalone calculator for option sensitivities:
- **Delta** (Δ): Price sensitivity to underlying
- **Gamma** (Γ): Rate of change of Delta
- **Theta** (Θ): Time decay (per day)
- **Vega** (ν): Volatility sensitivity (per 1%)
- **Rho** (ρ): Interest rate sensitivity (per 1%)

#### 4. **Model Comparison Dashboard**

Side-by-side comparison of all pricing models with convergence analysis.

#### 5. **Volatility Surface Viewer** (NEW! 🌐)

Interactive 3D visualization of implied volatility surface from real market data:

**Features:**
- **3D Surface Plot**: Plotly-based interactive visualization with rotation, zoom, and hover
- **Real-Time/Historical Data**: Fetches live options chain from Yahoo Finance, auto-fallback to historical data when market closed
- **Data Filtering**: Volume and bid-ask spread filters for quality control
- **ATM Term Structure**: Extract at-the-money volatility across maturities
- **Market Data Overlay**: Scatter points showing actual options data
- **Color-Coded Heatmap**: Blue (low IV) to Red (high IV) gradient

**Quick Start:**
1. Navigate to "📈 Interactive Volatility Surface Viewer" section
2. Enter ticker (e.g., `AAPL`, `SPY`, `TSLA`)
3. Select option type (Call/Put) and adjust parameters:
   - Risk-Free Rate: Default 5%
   - Min Volume: Default 0 (recommended for maximum data coverage)
   - Max Spread: Default 50% (realistic for options)
4. Click "🌐 Build 3D Surface" and wait 30-60 seconds
5. Interact: Drag to rotate, scroll to zoom, hover for details

**Interpreting Results:**
- **Axes**: Strike Price (X), Time to Maturity (Y), Implied Volatility % (Z)
- **Colors**: Blue (low IV, calm) → Red (high IV, uncertain)
- **Black dots**: Actual market data points before interpolation
- **Historical Data Warning**: Yellow banner appears when using previous day's closing prices (market closed)

**What to Look For:**
- **Volatility Smile**: Higher IV at extreme strikes (tail risk premium)
- **Term Structure**: Upward slope = increasing uncertainty over time
- **Volatility Skew**: Asymmetric pattern (downside protection premium)
- **IV Range**: Broader range = market uncertainty about future moves

### Quick Start - Derivative Pricing

#### Web Interface

1. Navigate to **"💹 Options Pricing Calculator"** section
2. Select calculator type from dropdown:
   - **Option Pricing**: Multi-model pricing
   - **Implied Volatility**: Extract IV from market prices
   - **Greeks Calculator**: Calculate all Greeks
   - **Model Comparison**: Compare all models

3. **Example: Price a Call Option**
   ```
   Spot Price: 100
   Strike Price: 105
   Time to Maturity: 0.25 (3 months)
   Risk-Free Rate: 5 (%)
   Volatility: 20 (%)
   Option Type: Call
   ```

4. **Example: Extract Implied Volatility**
   ```
   Market Price: 5.50
   Spot Price: 100
   Strike: 105
   Maturity: 0.25
   Rate: 5%
   ```

#### API Endpoints

All endpoints accept POST requests with JSON payloads:

**`/api/option_pricing`** - Price options with selected models
```json
{
  "spot": 100,
  "strike": 105,
  "maturity": 0.25,
  "risk_free_rate": 0.05,
  "volatility": 0.20,
  "option_type": "call",
  "models": ["black_scholes", "binomial", "trinomial"],
  "steps": 100
}
```

**`/api/implied_volatility`** - Extract IV from market price
```json
{
  "market_price": 5.50,
  "spot": 100,
  "strike": 105,
  "maturity": 0.25,
  "risk_free_rate": 0.05,
  "option_type": "call"
}
```

**`/api/greeks`** - Calculate all Greeks
```json
{
  "spot": 100,
  "strike": 105,
  "maturity": 0.25,
  "risk_free_rate": 0.05,
  "volatility": 0.20,
  "option_type": "call"
}
```

**`/api/model_comparison`** - Compare all models
```json
{
  "spot": 100,
  "strike": 105,
  "maturity": 0.25,
  "risk_free_rate": 0.05,
  "volatility": 0.20,
  "option_type": "call",
  "steps": 100
}
```

**`/api/volatility_surface`** - Build 3D volatility surface
```json
{
  "ticker": "AAPL",
  "option_type": "call",
  "risk_free_rate": 0.05,
  "min_volume": 0,
  "max_spread_pct": 0.50
}
```

**Response:**
```json
{
  "success": true,
  "surface": {
    "ticker": "AAPL",
    "current_price": 185.50,
    "option_type": "call",
    "data_points": 500,
    "using_historical_data": false,
    "surface_grid": {
      "strikes": [[...], ...],
      "maturities": [[...], ...],
      "implied_volatilities": [[...], ...]
    },
    "raw_data": [
      {"strike": 180, "time_to_maturity": 0.25, "implied_volatility": 0.22},
      ...
    ],
    "metadata": {
      "min_iv": 0.185,
      "max_iv": 0.623,
      "avg_iv": 0.298
    }
  }
}
```

**Notes:**
- Set `min_volume: 0` for maximum data coverage (recommended)
- Set `max_spread_pct: 0.50` (50%) for realistic options filtering
- `using_historical_data: true` when market closed (uses lastPrice from previous day)
- Returns 20x30 interpolated grid plus raw market data points
- NaN/Inf values converted to null in JSON for valid serialization

**`/api/atm_term_structure`** - Extract ATM volatility term structure
```json
{
  "ticker": "AAPL",
  "option_type": "call",
  "risk_free_rate": 0.05
}
```

### Backend Modules

**`src/derivatives/options_pricer.py`** (425 lines)
- `black_scholes()` - Analytical pricing with Greeks
- `binomial_tree()` - Binomial model (European/American)
- `trinomial_tree()` - Trinomial model (European/American)
- `calculate_all_greeks()` - All Greeks calculation
- `compare_models()` - Multi-model comparison

**`src/derivatives/volatility_surface.py`** (445 lines)
- `VolatilitySurfaceBuilder` class with real-time and historical data support
- `fetch_options_chain()` - Fetch options data from Yahoo Finance
- `calculate_time_to_maturity()` - Convert expiration dates to years
- `calculate_moneyness()` - Compute ln(K/S) for moneyness analysis
- `build_surface()` - Build 3D IV surface with automatic historical fallback
- `get_atm_volatility_term_structure()` - Extract ATM IV term structure
- **Historical Data Fallback**: Auto-detects market closure, uses lastPrice (±5% estimated bid/ask)
- **Data Quality Filters**: Moneyness (70%-130%), bid/ask validation, intrinsic value checks
- **Cubic Interpolation**: Scipy griddata for smooth 3D surface (NaN-safe JSON serialization)

**`src/derivatives/trinomial_model.py`** (220 lines)
- `price_option()` - OOP trinomial implementation
- `analyze_convergence()` - Convergence analysis

**`src/derivatives/volatility_surface.py`** (380 lines) - NEW!
- `fetch_options_chain()` - Yahoo Finance options data
- `build_surface()` - 3D IV surface construction with cubic interpolation
- `get_atm_volatility_term_structure()` - ATM volatility extraction
- `calculate_moneyness()` - ln(K/S) calculation
- Data filtering: volume, bid-ask spread, IV range

### Testing

Comprehensive test suite available:
```bash
python3 test_derivative_pricing.py
```

Tests cover:
- ✅ Black-Scholes pricing and Greeks
- ✅ Binomial/Trinomial tree pricing
- ✅ Model comparison accuracy
- ✅ Implied volatility extraction with validation
- ✅ Convergence analysis

### Accuracy & Performance

**Pricing Accuracy:**
- Black-Scholes: Exact analytical solution
- Binomial/Trinomial at N=100: < $0.01 error vs BS
- Binomial/Trinomial at N=500: < $0.001 error vs BS

**Implied Volatility:**
- Convergence tolerance: $0.0001
- Typical iterations: 3-7
- Validation error: < 0.001%

**Performance:**
- Black-Scholes: < 1ms (instant)
- Binomial (N=100): ~10ms
- Trinomial (N=100): ~12ms
- IV Extraction: ~5-15ms

### Use Cases

**Example 1: Price ATM Call Option**
- Spot: 100, Strike: 100, Maturity: 0.25, Vol: 20%, Rate: 5%
- Expected: ~$4.00, Delta ≈ 0.55

**Example 2: Extract Market IV**
- Market Price: $5.50, Spot: 100, Strike: 105
- Expected: ~35.48% IV in 3-5 iterations

**Example 3: American vs European Put**
- Compare early exercise premium
- Use Binomial with American exercise
- Difference = early exercise value

**Example 4: Visualize AAPL Volatility Surface**
- Ticker: AAPL, Type: Call, Risk-Free Rate: 5%
- Interactive 3D plot with ~200-400 data points
- Drag to rotate, scroll to zoom, hover for values
- Typical processing time: 30-60 seconds

### Methodology

**Black-Scholes Formula:**
```
C = S × N(d₁) - K × e^(-r×T) × N(d₂)
d₁ = [ln(S/K) + (r + σ²/2)×T] / (σ×√T)
d₂ = d₁ - σ×√T
```

**Newton-Raphson IV:**
```
σ_new = σ_old - (BS_price(σ_old) - Market_price) / Vega(σ_old)
```

### References
- DerivativePricing Notebook (methodology source)
- Black-Scholes (1973) - Original paper
- Hull, J.C. - "Options, Futures, and Other Derivatives"
- Cox-Ross-Rubinstein (1979) - Binomial model

---

## 🐛 Troubleshooting

### Common Issues

#### 1. MongoDB Connection Failed (CLI)
```bash
# Check if MongoDB is running
brew services list | grep mongodb
# Or
docker ps | grep mongo

# Verify connection
python check_mongodb.py

# Disable MongoDB if not needed
# In config.json, set "mongodb.enabled" to false
```

#### 2. Web App Won't Start
```bash
# Check if port is in use
lsof -i :5173

# Try different port
export PORT=8000
python webapp.py

# Check Flask is installed
pip install flask
```

#### 3. API Rate Limits
- **Alpha Vantage**: Free tier = 25 requests/day, 5 calls/minute
- **Solution**: Use `--sources yahoo finviz` instead
- **Or**: Enable `fallback_to_yahoo` in config.json

#### 4. Email Not Sending
```bash
# Check .env file exists
ls -la .env

# Verify SMTP settings
# For Gmail, use App Password, not regular password
# Enable "Less secure app access" if needed

# Test email configuration
python -c "from src.utils.email_utils import send_consolidated_report; print('Email module loaded successfully')"
```

#### 5. int64 JSON Serialization Error
This has been fixed in the latest version. If you encounter this:
- Update `webapp.py` to latest version
- Ensure `convert_numpy_types()` function is present
- Verify it's called before `jsonify()` in `/api/scrape` endpoint

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is for educational purposes. Web scraping may violate terms of service of some websites. Use responsibly and check each website's terms before scraping.

---

## 🔗 Additional Resources

- [Alpha Vantage API Documentation](https://www.alphavantage.co/documentation/)
- [Finhub API Documentation](https://finnhub.io/docs/api)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Plotly Documentation](https://plotly.com/javascript/)
- [Yahoo Finance Options](https://finance.yahoo.com/options/)

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation and troubleshooting section
- Review logs: `logs/webapp.log` (web) or `logs/stock_scraper.log` (CLI)
- Check browser console (F12) for frontend errors
- Consult API provider documentation

---

**Happy Analyzing! 📈💹**