"""
MarketWatch scraper module
"""
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from ..utils.request_handler import make_request

class MarketWatchScraper(BaseScraper):
    """Scraper for MarketWatch"""
    
    def _scrape_data(self, ticker):
        """
        Scrape financial data from MarketWatch
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Dictionary containing scraped data
        """
        url = f"https://www.marketwatch.com/investing/stock/{ticker}/company-profile"
        
        response = make_request(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize data dictionary
        data = {}
        
        # Parse valuation metrics
        # MarketWatch has a unique structure we need to navigate
        
        # Try to find the valuation section
        valuation_section = None
        sections = soup.find_all('div', class_='element element--table')
        for section in sections:
            heading = section.find('h2', class_='element__heading')
            if heading and "Valuation" in heading.text:
                valuation_section = section
                break
                
        if valuation_section:
            # Find all table rows
            rows = valuation_section.find_all('tr', class_='table__row')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    header = cells[0].text.strip()
                    value = cells[1].text.strip()
                    
                    # Look for our target metrics
                    if "P/E Ratio" in header:
                        data["P/E Ratio (MW)"] = value
                    elif "Price to Book Ratio" in header:
                        data["P/B Ratio (MW)"] = value
                    elif "Price to Sales Ratio" in header:
                        data["P/S Ratio (MW)"] = value
                    elif "Forward P/E" in header:
                        data["Forward P/E (MW)"] = value
        
        # If we couldn't find the valuation section, try alternative elements
        if not data:
            valuation_items = soup.find_all('div', class_='cell')
            for item in valuation_items:
                label = item.find('span', class_='label')
                value = item.find('span', class_='primary')
                
                if label and value:
                    header = label.text.strip()
                    val = value.text.strip()
                    
                    # Look for our target metrics
                    if "Price to Earnings" in header:
                        data["P/E Ratio (MW)"] = val
                    elif "Price to Book Ratio" in header:
                        data["P/B Ratio (MW)"] = val
                    elif "Price to Sales Ratio" in header:
                        data["P/S Ratio (MW)"] = val
        
        # Add source metadata
        if data:
            self.logger.info(f"Successfully scraped MarketWatch data for {ticker}")
        else:
            self.logger.warning(f"Could not find any metrics for {ticker} on MarketWatch")
            
        return data