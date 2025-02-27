"""
Google Finance scraper module
"""
import re
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from ..utils.request_handler import make_request

class GoogleFinanceScraper(BaseScraper):
    """Scraper for Google Finance"""
    
    def _scrape_data(self, ticker):
        """
        Scrape financial data from Google Finance
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Dictionary containing scraped data
        """
        # Google Finance URL format may vary by region/market
        # Try to handle different formats
        urls = [
            f"https://www.google.com/finance/quote/{ticker}:NASDAQ",
            f"https://www.google.com/finance/quote/{ticker}:NYSE",
            f"https://www.google.com/finance/quote/{ticker}"
        ]
        
        # Initialize data dictionary
        data = {}
        
        # Try each possible URL
        for url in urls:
            try:
                response = make_request(url, headers=self.headers)
                
                # If we get here, the URL worked
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for P/E ratio
                metrics = soup.find_all('div', class_='P6K39c')
                for metric in metrics:
                    label_div = metric.find('div', class_='Mb2qrb')
                    if label_div and "P/E ratio" in label_div.text:
                        value_div = metric.find('div', class_='YMlKec')
                        if value_div:
                            data["P/E Ratio (Google)"] = value_div.text.strip()
                
                # Look for other metrics - Google Finance doesn't always show these clearly
                # but we'll try to find them if available
                all_divs = soup.find_all('div')
                for div in all_divs:
                    if "P/B ratio" in div.text or "Price to book" in div.text.lower():
                        value = re.search(r'[\d.]+', div.text)
                        if value:
                            data["P/B Ratio (Google)"] = value.group()
                            
                    if "P/S ratio" in div.text or "Price to sales" in div.text.lower():
                        value = re.search(r'[\d.]+', div.text)
                        if value:
                            data["P/S Ratio (Google)"] = value.group()
                
                # If we found at least one metric, break the loop
                if data:
                    break
                    
            except Exception as e:
                self.logger.warning(f"Failed to fetch Google Finance data from {url}: {str(e)}")
                continue
        
        # Add source metadata if we found data
        if data:
            self.logger.info(f"Successfully scraped Google Finance data for {ticker}")
        else:
            self.logger.warning(f"Could not find any metrics for {ticker} on Google Finance")
            
        return data