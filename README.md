# Stock Data Scraper

A Python web scraping application that fetches financial metrics like P/E ratio, P/B ratio, P/S ratio, and Forward P/E ratio for stocks from multiple financial sources.

## Features

- Scrapes financial data from multiple sources:
  - Yahoo Finance
  - Finviz
  - Google Finance
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

# Scrape data and save to a file
python main.py --ticker GOOGL --output output/google_data.csv
```

### Command Line Arguments

- `--ticker`: Stock ticker symbol to scrape
- `--output`: Output CSV file path
- `--sources`: Data sources to scrape from (choices: yahoo, finviz, google, marketwatch, all)
- `--interactive`: Run in interactive mode

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