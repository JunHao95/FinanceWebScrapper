# Stock Data Scraper

A high-performance Python web scraping application that fetches financial metrics like P/E ratio, P/B ratio, P/S ratio, and Forward P/E ratio for stocks from multiple financial sources. Optimized with parallel processing and connection pooling for faster execution.

## Features

- **High-Performance Architecture**:
  - ⚡ **Parallel Processing**: Uses `concurrent.futures` ThreadPoolExecutor for concurrent data fetching
  - 🔄 **Connection Pooling**: HTTP connection reuse for speed improvement
  - 🚀 **Fast Mode**: Minimal delays with optimized concurrent processing 
  - 📈 **Scalable**: Handles multiple tickers efficiently with configurable worker pools

- **Data Persistence**:
  - 💾 **MongoDB Integration**: Automatic storage of all time series data locally
  - 🔍 **Queryable History**: Fast retrieval with indexed fields
  - 🚫 **Deduplication**: Unique indexes prevent duplicate records
  - 📊 **Analytics Ready**: Data structured for analysis and visualization

- **Multi-Source Data Collection**:
  - Web sources: Yahoo Finance, Finviz, Google Finance
  - APIs: Alpha Vantage, Finhub (API keys required)
  - Enhanced sentiment analysis from news, Reddit, and Google Trends

- **Technical Analysis**:
  - Bollinger Bands
  - Moving Averages (SMA, EMA)
  - RSI (Relative Strength Index)
  - Volume indicators
  - MACD and other momentum indicators

- **Output & Reporting**:
  - Multiple formats: CSV, Excel, Text reports
  - Email reports with customizable recipients
  - Summary comparison reports
  - Interactive mode for guided usage
  - Configurable logging levels

## Installation

1. Clone this repository
```bash
git clone https://github.com/yourusername/stock-scraper.git
cd stock-scraper
```

2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure MongoDB (optional but recommended)
```bash
# Install MongoDB (macOS with Homebrew)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Or use Docker for mongoDB
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Verify MongoDB is running
python check_mongodb.py
```

5. Set up configuration
```bash
# Copy example configuration
cp config.json.example config.json

# Edit config.json with your settings
# - MongoDB connection (enabled by default)
# - Email notifications (optional)
# - API settings
```

6. Set API keys (optional but recommended)
```bash
# For Alpha Vantage API
export ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# For Finhub API
export FINHUB_API_KEY=your_finhub_key_here
```

## MongoDB Storage

All stock time series data is automatically stored in MongoDB for future analysis.

### Features
- **Automatic Storage**: Data saved during each scraper run
- **Deduplication**: Unique compound index on (ticker, date) prevents duplicates
- **Fast Queries**: Indexed fields (ticker, date) for efficient retrieval
- **Graceful Degradation**: Scraper continues working if MongoDB unavailable

### Configuration

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

### Usage

```bash
# Data is automatically stored when you run the scraper
python main.py --tickers AAPL,MSFT --sources technical

# Verify stored data
python check_mongodb.py

# Query data via MongoDB shell
mongosh stock_data --eval "db.timeseries.find({ticker: 'AAPL'}).sort({date: -1}).limit(5)"

# Query data via Python
python -c "
from src.utils.mongodb_storage import MongoDBStorage
mongodb = MongoDBStorage()
df = mongodb.get_timeseries_data('AAPL')
print(df.head())
mongodb.close()
"
```

### Database Schema

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

### Disabling MongoDB

To run without MongoDB:
```json
{
  "mongodb": {
    "enabled": false
  }
}
```

### Verifying MongoDB Data Updates

After running `./uat_run_scraper.sh` or `./run_scraper.sh`, follow these steps to verify that new time series data was stored:

#### Method 1: Quick Verification Script
```bash
# Run the MongoDB verification script
python check_mongodb.py
```

This will show:
- ✅ Connection status
- 📊 Total document counts per collection
- 📈 Sample data from most recent records
- 📁 Available tickers

#### Method 2: MongoDB Shell Verification

```bash
# Step 1: Connect to MongoDB
mongosh stock_data

# Step 2: Check total record count
db.timeseries.countDocuments({})

# Step 3: View most recent records (sorted by last_updated)
db.timeseries.find().sort({last_updated: -1}).limit(5).pretty()

# Step 4: Check specific ticker's latest data
db.timeseries.find({ticker: "AAPL"}).sort({date: -1}).limit(5).pretty()

# Step 5: Count records per ticker
db.timeseries.aggregate([
  {$group: {_id: "$ticker", count: {$sum: 1}}},
  {$sort: {count: -1}}
])

# Step 6: View records added in last hour
db.timeseries.find({
  last_updated: {$gte: new Date(Date.now() - 3600000)}
}).count()
```

#### Method 3: Python Verification

```python
# Create a verification script: verify_updates.py
from src.utils.mongodb_storage import MongoDBStorage
from datetime import datetime, timedelta

mongodb = MongoDBStorage()

# Check records updated in last hour
one_hour_ago = datetime.now() - timedelta(hours=1)

# Get all tickers
tickers = mongodb.db['timeseries'].distinct('ticker')
print(f"Total tickers in database: {len(tickers)}")
print(f"Tickers: {', '.join(sorted(tickers))}")

# Check latest update time for each ticker
for ticker in sorted(tickers):
    latest = mongodb.db['timeseries'].find_one(
        {'ticker': ticker},
        sort=[('last_updated', -1)]
    )
    if latest:
        print(f"{ticker}: Last updated {latest['last_updated']}, Latest date: {latest['date']}")

mongodb.close()
```

Run it:
```bash
python verify_updates.py
```

#### Method 4: Before/After Comparison

```bash
# Step 1: BEFORE running scraper - record current counts
mongosh stock_data --eval "
  db.timeseries.aggregate([
    {$group: {_id: '\$ticker', count: {$sum: 1}}},
    {$sort: {_id: 1}}
  ])
" > before_count.txt

# Step 2: Run your scraper
./uat_run_scraper.sh

# Step 3: AFTER running scraper - check new counts  
mongosh stock_data --eval "
  db.timeseries.aggregate([
    {$group: {_id: '\$ticker', count: {$sum: 1}}},
    {$sort: {_id: 1}}
  ])
" > after_count.txt

# Step 4: Compare the differences
diff before_count.txt after_count.txt
```

#### Method 5: Check Scraper Logs

```bash
# View logs to confirm MongoDB storage
tail -f logs/stock_scraper.log | grep -i mongodb

# Look for messages like:
# "Successfully connected to MongoDB"
# "Stored X time series records for TICKER"
# "MongoDB storage initialized successfully"
```

#### Complete Verification Sequence

```bash
# 1. Check initial state
echo "=== BEFORE SCRAPER RUN ==="
python check_mongodb.py

# 2. Run scraper
./uat_run_scraper.sh

# 3. Verify updates
echo "=== AFTER SCRAPER RUN ==="
python check_mongodb.py

# 4. Check specific ticker's latest date
mongosh stock_data --eval "
  db.timeseries.find({ticker: 'AAPL'})
    .sort({date: -1})
    .limit(1)
    .pretty()
"

# 5. Verify records were updated in last 5 minutes
mongosh stock_data --eval "
  var fiveMinutesAgo = new Date(Date.now() - 300000);
  print('Records updated in last 5 minutes:');
  print(db.timeseries.countDocuments({
    last_updated: {$gte: fiveMinutesAgo}
  }));
"
```

## Performance Optimizations

### ⚡ Parallel Processing
The scraper uses `concurrent.futures.ThreadPoolExecutor` to process multiple tickers simultaneously:

```bash
# Enable parallel processing with custom worker count
python main.py --tickers AAPL,MSFT,GOOG,AMZN,TSLA --parallel --max-workers 8
```

### 🔄 Connection Pooling
HTTP connection pooling automatically reuses connections for multiple requests:
- **Automatic**: Enabled by default for all HTTP requests
- **Configurable**: Adjust pool size via environment variables
- **Performance**: Faster execution for multiple requests

```bash
# Configure connection pool settings
export CONNECTION_POOL_SIZE=20
export CONNECTION_POOL_MAXSIZE=20
```

### 🚀 Fast Mode
Ultra-fast processing with minimal delays and maximum concurrency:

```bash
# Enable fast mode for maximum speed
python main.py --tickers AAPL,MSFT,GOOG --fast-mode --parallel
```

## Usage

### Basic Usage

```bash
python main.py --tickers AAPL,MSFT,GOOG
```

### Logging Options 

Control logging behavior:

```bash
# Turn off logging
python main.py --tickers AAPL --logging off

# Set logging level
python main.py --tickers AAPL --log-level debug
python main.py --tickers AAPL --log-level warning
```

Available logging levels:
- `debug`: Most verbose, shows all details
- `info`: Standard information (default)
- `warning`: Only warnings and errors
- `error`: Only errors
- `critical`: Only critical errors

### Advanced Usage

```bash
# High-performance mode with all optimizations
python main.py --tickers AAPL,MSFT,GOOG,AMZN,TSLA,NVDA,META,NFLX \
               --sources yahoo finviz alphavantage technical enhanced_sentiment \
               --fast-mode --parallel --max-workers 8 \
               --format excel --summary

# Process large ticker lists efficiently
python main.py --ticker-file tickers.txt --fast-mode --parallel --max-workers 12

# Custom connection pool configuration
export CONNECTION_POOL_SIZE=30
export CONNECTION_POOL_MAXSIZE=30
python main.py --tickers AAPL,MSFT --sources all --parallel
```

### Performance Tuning

For optimal performance with large datasets:

```bash
# Maximum performance configuration
python main.py --tickers AAPL,MSFT,GOOG,AMZN,TSLA,NVDA,META,NFLX,CRM,ORCL \
               --fast-mode \           # Enable fast mode
               --parallel \            # Parallel processing  
               --max-workers 10 \      # Increase worker count
               --delay 0 \             # Minimize delays
               --sources yahoo finviz alphavantage technical \
               --format excel \
               --summary
```

### Command Line Mode

```bash
# Scrape data for a specific ticker
python main.py --tickers AAPL

# Scrape data from specific sources
python main.py --tickers MSFT --sources yahoo finviz

# Use API sources with keys
python main.py --tickers GOOGL --sources alphavantage finhub --alpha-key YOUR_KEY --finhub-key YOUR_KEY

# Get technical indicators
python main.py --tickers AAPL --sources technical --alpha-key YOUR_KEY

# Scrape data and save to an Excel file
python main.py --tickers GOOGL --output output/google_data.xlsx --format excel
```

### Command Line Arguments

#### Basic Arguments
- `--tickers`: Comma-separated stock ticker symbols to scrape
- `--ticker-file`: File containing ticker symbols, one per line
- `--output-dir`: Directory to save output files (default: output)
- `--sources`: Data sources to use (choices: yahoo, finviz, google, alphavantage, finhub, technical, enhanced_sentiment, all)
- `--format`: Output file format (choices: csv, excel, text)
- `--interactive`: Run in interactive mode

#### Performance Arguments
- `--parallel`: Enable parallel processing using ThreadPoolExecutor
- `--fast-mode`: Enable fast mode with minimal delays and maximum concurrency (90% speed boost)
- `--max-workers`: Maximum number of parallel workers (default: 8, recommended: 8-12)
- `--delay`: Delay between API requests in seconds (default: 1, fast-mode uses 0)

#### API & Authentication
- `--alpha-key`: Alpha Vantage API key
- `--finhub-key`: Finhub API key

#### Reporting & Output
- `--display-mode`: How to display results (choices: table, grouped)
- `--email`: Comma-separated email addresses to send the report to
- `--cc`: Comma-separated email addresses to CC the report to
- `--bcc`: Comma-separated email addresses to BCC the report to
- `--summary`: Generate a summary report for all tickers

#### Logging & Debugging
- `--logging`: Enable or disable logging (choices: true, false)
- `--log-level`: Set logging level (choices: debug, info, warning, error, critical)

## Environment Configuration

### Performance Settings
Configure connection pooling and performance parameters:

```bash
# Connection pooling settings
export CONNECTION_POOL_SIZE=20          # Number of connection pools
export CONNECTION_POOL_MAXSIZE=20       # Max connections per pool
export ENABLE_CONNECTION_POOLING=true   # Enable/disable pooling

# Performance monitoring
export PERFORMANCE_MONITORING=true      # Enable performance timing
```

### API Keys

Some features require API keys:

- Alpha Vantage API: Set `ALPHA_VANTAGE_API_KEY` environment variable or use `--alpha-key`
- Finhub API: Set `FINHUB_API_KEY` environment variable or use `--finhub-key`

## Email Configuration

To enable email reports, set the following environment variables:

- `FINANCE_SENDER_EMAIL`: Sender email address
- `FINANCE_SENDER_PASSWORD`: Sender email password
- `FINANCE_SMTP_SERVER`: SMTP server (default: smtp.gmail.com)
- `FINANCE_SMTP_PORT`: SMTP port (default: 587)
- `FINANCE_USE_TLS`: Use TLS (default: True)

## Project Structure

```
stock_scraper/
│
├── src/                     # Source code
│   ├── scrapers/            # Web scraper modules
│   │   ├── base_scraper.py  # Base scraper with common functionality
│   │   ├── yahoo_scraper.py # Yahoo Finance scraper
│   │   ├── api_scraper.py   # Alpha Vantage & Finhub API scrapers
│   │   ├── finviz_scraper.py# Finviz scraper
│   │   └── enhanced_sentiment_scraper.py # Multi-source sentiment analysis
│   ├── sentiment/           # Sentiment analysis modules
│   │   └── sentiment_analyzer.py # Advanced sentiment analysis engine
│   ├── indicators/          # Technical indicators
│   │   └── technical_indicators.py # TA-Lib based technical analysis
│   ├── utils/               # Utility functions
│   │   ├── request_handler.py # HTTP connection pooling & retry logic
│   │   ├── data_formatter.py  # Data formatting utilities
│   │   ├── display_formatter.py # Output display formatting
│   │   ├── email_utils.py     # Email reporting functionality
│   │   └── mongodb_storage.py # MongoDB storage utility
│   └── config.py            # Configuration settings
│
├── data/                    # Data storage directory
├── output/                  # Output files directory
├── logs/                    # Log files directory
├── tests/                   # Test modules
├── trends_cache/            # Google Trends cache directory
│
├── main.py                  # Main application entry point
├── check_mongodb.py         # MongoDB verification script
├── requirements.txt         # Dependencies
├── config.json.example      # Example configuration template
├── config.json              # Configuration file (gitignored)
└── README.md                # Documentation
```

## Performance Benchmarks

### Scalability
- **Concurrent Workers**: Supports 8-12 parallel workers efficiently
- **Connection Pools**: 20 connection pools with 20 connections each
- **Memory Efficient**: Connection reuse reduces memory overhead
- **Rate Limit Handling**: Intelligent backoff and retry strategies

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## Disclaimer

This program is for educational purposes only. Web scraping may violate the terms of service of some websites. Use responsibly and check the terms of service of each website before scraping.