# src/__init__.py
"""
Stock Scraper package
"""
__version__ = '0.1.0'

# src/scrapers/__init__.py
"""
Scraper modules for different financial data sources
"""
from .scrapers.yahoo_scraper import YahooFinanceScraper
from .scrapers.finviz_scraper import FinvizScraper
from .scrapers.google_scraper import GoogleFinanceScraper
from .scrapers.marketwatch_scraper import MarketWatchScraper

# Export all scrapers
__all__ = [
    'YahooFinanceScraper',
    'FinvizScraper',
    'GoogleFinanceScraper',
    'MarketWatchScraper',
]

# src/utils/__init__.py
"""
Utility modules for the stock scraper
"""
from .utils.data_formatter import format_data_as_dataframe, save_to_csv
from .utils.request_handler import make_request

# Export utility functions
__all__ = [
    'format_data_as_dataframe',
    'save_to_csv',
    'make_request',
]

# tests/__init__.py
"""
Test package for the stock scraper
"""