"""
Base Scraper module that defines the interface for all scraper classes
"""
import time
import logging
from abc import ABC, abstractmethod

from ..utils.request_handler import make_request

class BaseScraper(ABC):
    """Base class for all scrapers that defines common functionality"""
    
    def __init__(self, delay=1):
        """
        Initialize the scraper
        
        Args:
            delay (int): Delay in seconds between requests to avoid rate limiting
        """
        self.delay = delay
        self.logger = logging.getLogger(self.__class__.__name__)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_data(self, ticker):
        """
        Get data for the given ticker
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Dictionary containing scraped data
        """
        # Only add delay for web scraping, not API calls (APIs handle their own rate limiting)
        if self.delay > 0 and hasattr(self, '_is_web_scraper'):
            time.sleep(self.delay)
        
        # Implement scraping logic in the derived class
        try:
            return self._scrape_data(ticker)
        except Exception as e:
            self.logger.error(f"Error scraping data for {ticker}: {str(e)}")
            return {"error": f"Error scraping data: {str(e)}"}
    
    @abstractmethod
    def _scrape_data(self, ticker):
        """
        Implement the actual scraping logic
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Dictionary containing scraped data
        """
        pass