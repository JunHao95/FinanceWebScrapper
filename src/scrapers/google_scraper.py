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
                self.logger.info(f"Trying Google Finance URL: {url}")
                response = make_request(url, headers=self.headers)
                
                # If we get here, the URL worked
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for key metrics in the About section
                about_section = None
                sections = soup.find_all('div', class_='bLLb2d')
                for section in sections:
                    if "About" in section.text:
                        about_section = section
                        break
                
                if about_section:
                    # Google Finance structure is different from other sources
                    # It has a grid of metrics with labels and values
                    metrics = soup.find_all('div', class_='P6K39c')
                    for metric in metrics:
                        label_div = metric.find('div')
                        if not label_div:
                            continue
                            
                        label = label_div.text.strip().lower()
                        value_div = metric.find('div', class_='YMlKec')
                        
                        if value_div:
                            value = value_div.text.strip()
                            
                            # Basic metrics
                            if "p/e ratio" in label:
                                data["P/E Ratio (Google)"] = value
                            elif "price-to-book" in label or "p/b ratio" in label:
                                data["P/B Ratio (Google)"] = value
                            elif "price-to-sales" in label or "p/s ratio" in label:
                                data["P/S Ratio (Google)"] = value
                            
                            # Additional metrics
                            elif "eps" in label or "earnings per share" in label:
                                data["EPS (Google)"] = value
                            elif "roe" in label or "return on equity" in label:
                                data["ROE (Google)"] = value
                            elif "roic" in label or "return on invested capital" in label:
                                data["ROIC (Google)"] = value
                            elif "ev/ebitda" in label or "enterprise value to ebitda" in label:
                                data["EV/EBITDA (Google)"] = value
                            elif "peg" in label:
                                data["PEG Ratio (Google)"] = value
                
                # Look for EPS in description text or elsewhere on the page
                desc_div = soup.find('div', class_='bLLb2d')
                if desc_div:
                    desc_text = desc_div.text
                    eps_match = re.search(r'EPS.*?(\$[\d.]+|\d+\.\d+)', desc_text)
                    if eps_match and "EPS (Google)" not in data:
                        data["EPS (Google)"] = eps_match.group(1)
                
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