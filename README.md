# Stock Data Scraper

A Python web scraping application that fetches financial metrics like P/E ratio, P/B ratio, P/S ratio, and Forward P/E ratio for stocks from multiple financial sources.

## Features

- Scrapes financial data from multiple sources:
  - Web sources: Yahoo Finance, Finviz, Google Finance
  - APIs: Alpha Vantage, Finhub (API keys required)
- Calculates technical indicators:
  - Bollinger Bands
  - Moving Averages
  - RSI
  - Volume indicators
- Supports multiple output formats:
  - CSV
  - Excel
  - Text reports
- Additional features:
  - Email reports
  - Parallel processing
  - Interactive mode
  - Summary reports
  - Configurable logging

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

### Command Line Mode

```bash
# Scrape data for a specific ticker
python main.py --ticker AAPL

# Scrape data from specific sources
python main.py --ticker MSFT --sources yahoo finviz

# Use API sources with keys
python main.py --ticker GOOGL --sources alphavantage finhub --alpha-key YOUR_KEY --finhub-key YOUR_KEY

# Get technical indicators
python main.py --ticker AAPL --sources technical --alpha-key YOUR_KEY

# Scrape data and save to an Excel file
python main.py --ticker GOOGL --output output/google_data.xlsx --format excel
```

### Command Line Arguments

- `--ticker`: Stock ticker symbol to scrape
- `--output`: Output CSV or Excel file path
- `--sources`: Data sources to use (choices: yahoo, finviz, google, alphavantage, finhub, technical, all)
- `--format`: Output file format (choices: csv, excel)
- `--interactive`: Run in interactive mode
- `--alpha-key`: Alpha Vantage API key
- `--finhub-key`: Finhub API key

## API Keys

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
│   ├── utils/               # Utility functions
│   └── config.py            # Configuration settings
│
├── data/                    # Data storage directory
├── output/                  # Output files directory
├── logs/                    # Log files directory
├── tests/                   # Test modules
│
├── main.py                  # Main application entry point
├── requirements.txt         # Dependencies
└── README.md                # Documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## Disclaimer

This program is for educational purposes only. Web scraping may violate the terms of service of some websites. Use responsibly and check the terms of service of each website before scraping.