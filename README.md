# Stock Data Scraper

A high-performance Python web scraping application that fetches financial metrics like P/E ratio, P/B ratio, P/S ratio, and Forward P/E ratio for stocks from multiple financial sources. Optimized with parallel processing and connection pooling for faster execution.

## Features

- **High-Performance Architecture**:
  - ⚡ **Parallel Processing**: Uses `concurrent.futures` ThreadPoolExecutor for concurrent data fetching
  - 🔄 **Connection Pooling**: HTTP connection reuse for speed improvement
  - 🚀 **Fast Mode**: Minimal delays with optimized concurrent processing 
  - 📈 **Scalable**: Handles multiple tickers efficiently with configurable worker pools

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

4. Set API keys (optional but recommended)
```bash
# For Alpha Vantage API
export ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# For Finhub API
export FINHUB_API_KEY=your_finhub_key_here
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
│   │   └── email_utils.py     # Email reporting functionality
│   └── config.py            # Configuration settings
│
├── data/                    # Data storage directory
├── output/                  # Output files directory
├── logs/                    # Log files directory
├── tests/                   # Test modules
├── trends_cache/            # Google Trends cache directory
│
├── main.py                  # Main application entry point
├── requirements.txt         # Dependencies
├── config.json              # Configuration file
├── test_connection_pooling.py # Connection pooling performance test
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