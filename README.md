# Stock Data Scraper

A Python web scraping application that fetches financial metrics like P/E ratio, P/B ratio, P/S ratio, and Forward P/E ratio for stocks from multiple financial sources.

## Features

- Collects financial data from multiple sources:
  - Web sources:
    - Yahoo Finance
    - Finviz
    - Google Finance
  - API services:
    - Alpha Vantage API
    - Finhub API
  - Technical indicators:
    - Bollinger Bands
    - Moving Averages (SMA, EMA, MACD)
    - RSI (Relative Strength Index)
    - Volume indicators (OBV, Volume MA)
- Provides comprehensive financial ratios and metrics
- Works with any valid stock ticker symbol
- Offers both command-line and interactive modes
- Exports data to CSV format
- Robust error handling and retry mechanisms

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

### Interactive Mode

```bash
python main.py --interactive
```

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

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Disclaimer

This program is for educational purposes only. Web scraping may violate the terms of service of some websites. Use responsibly and check the terms of service of each website before scraping.