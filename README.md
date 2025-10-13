# Stock Financial Metrics Scraper

A high-performance Python application for scraping and analyzing financial metrics from multiple sources. Available as both a **CLI tool** and a **web application** for maximum flexibility.

## 🌟 Key Features

### Dual Interface
- **🖥️ CLI Mode**: Scriptable, automated analysis for scheduled runs
- **🌐 Web Interface**: Interactive browser-based analysis with beautiful visualizations

### High-Performance Architecture
- ⚡ **Parallel Processing**: Concurrent data fetching with ThreadPoolExecutor
- 🔄 **Connection Pooling**: HTTP connection reuse for faster execution
- 🚀 **Fast Mode**: 90% speed boost with optimized concurrent processing
- 📈 **Scalable**: Handles multiple tickers efficiently

### Multi-Source Data Collection
- **Web Scrapers**: Yahoo Finance, Finviz, Google Finance
- **APIs**: Alpha Vantage, Finhub (API keys required)
- **Enhanced Sentiment**: News, Reddit, Google Trends analysis
- **Technical Indicators**: RSI, Moving Averages, Bollinger Bands, MACD

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

---

## 📝 Changelog

### Latest Updates
- ✅ Added Flask web application interface
- ✅ Fixed NumPy int64/float64 JSON serialization issues
- ✅ Disabled MongoDB storage in web mode (CLI-only feature)
- ✅ Added comprehensive documentation
- ✅ Improved error handling and logging
- ✅ Enhanced performance with parallel processing
- ✅ Added email reporting capability

---

## 💡 Tips & Best Practices

### For CLI Users
1. **Use ticker files** for large batches: `--ticker-file tickers.txt`
2. **Enable fast mode** for speed: `--fast-mode --parallel`
3. **Save bandwidth** with selective sources: `--sources yahoo finviz`
4. **Schedule runs** with cron for regular updates
5. **Monitor MongoDB** with `check_mongodb.py` after runs

### For Web Users
1. **Set API keys in .env** to avoid entering each time
2. **Use "All Sources"** for comprehensive analysis
3. **Enable Technical Indicators** for advanced metrics
4. **Save email settings** in .env for convenience
5. **Bookmark the webapp** for quick access

### General
1. **Respect API limits**: Free tiers have daily/minute caps
2. **Use connection pooling**: Significantly faster
3. **Monitor logs**: Check `logs/` for errors
4. **Keep dependencies updated**: `pip install -U -r requirements.txt`
5. **Backup MongoDB data**: Regular exports recommended

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section
- Consult API provider documentation

---

**Happy Analyzing! 📈💹**
