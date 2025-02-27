"""
Yahoo Finance scraper module
"""
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from ..utils.request_handler import make_request

class YahooFinanceScraper(BaseScraper):
    """Scraper for Yahoo Finance"""
    
    def _scrape_data(self, ticker):
        """
        Scrape financial data from Yahoo Finance
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Dictionary containing scraped data
        """
        url = f"https://finance.yahoo.com/quote/{ticker}/key-statistics"
        
        response = make_request(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize data dictionary
        data = {}
        
        # Parse valuation ratios
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    header = cols[0].text.strip()
                    value = cols[1].text.strip()
                    
                    # Look for our target metrics
                    if "P/E Ratio" in header:
                        data["P/E Ratio (Yahoo)"] = value
                    elif "Price/Book" in header:
                        data["P/B Ratio (Yahoo)"] = value
                    elif "Price/Sales" in header:
                        data["P/S Ratio (Yahoo)"] = value
                    elif "Forward P/E" in header:
                        data["Forward P/E (Yahoo)"] = value
        
        # Add source metadata
        self.logger.info(f"Successfully scraped Yahoo Finance data for {ticker}")
        return data