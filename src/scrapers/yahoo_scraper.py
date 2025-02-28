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
        # Statistics page contains most valuation metrics
        statistics_url = f"https://finance.yahoo.com/quote/{ticker}/key-statistics"
        
        # Analysis page contains EPS and growth estimates
        analysis_url = f"https://finance.yahoo.com/quote/{ticker}/analysis"
        
        # Initialize data dictionary
        data = {}
        
        # Scrape statistics page
        try:
            self.logger.info(f"Fetching statistics from Yahoo Finance for {ticker}")
            response = make_request(statistics_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse valuation ratios from tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        header = cols[0].text.strip()
                        value = cols[1].text.strip()
                        
                        # Basic valuation metrics
                        if "P/E Ratio" in header:
                            data["P/E Ratio (Yahoo)"] = value
                        elif "Price/Book" in header:
                            data["P/B Ratio (Yahoo)"] = value
                        elif "Price/Sales" in header:
                            data["P/S Ratio (Yahoo)"] = value
                        elif "Forward P/E" in header:
                            data["Forward P/E (Yahoo)"] = value
                        
                        # Additional metrics
                        elif "PEG Ratio" in header:
                            data["PEG Ratio (Yahoo)"] = value
                        elif "Enterprise Value/EBITDA" in header or "EV/EBITDA" in header:
                            data["EV/EBITDA (Yahoo)"] = value
                        elif "Return on Equity" in header or "ROE" in header:
                            data["ROE (Yahoo)"] = value
                        elif "Return on Assets" in header or "ROA" in header:
                            data["ROA (Yahoo)"] = value
                        elif "Profit Margin" in header:
                            data["Profit Margin (Yahoo)"] = value
                        elif "Operating Margin" in header:
                            data["Operating Margin (Yahoo)"] = value
                        elif "Diluted EPS" in header:
                            data["EPS (Yahoo)"] = value
                        elif "Return on Investment" in header or "Return on Capital" in header:
                            data["ROIC (Yahoo)"] = value
            
            # Scrape analysis page for additional EPS data
            try:
                analysis_response = make_request(analysis_url, headers=self.headers)
                analysis_soup = BeautifulSoup(analysis_response.text, 'html.parser')
                
                # Looking for EPS estimates and growth rates
                tables = analysis_soup.find_all('table')
                for table in tables:
                    table_text = table.text.lower()
                    if "earnings estimate" in table_text:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                header = cells[0].text.strip().lower()
                                if "current year" in header and len(cells) > 1:
                                    data["EPS Estimate Current Year (Yahoo)"] = cells[1].text.strip()
                                elif "next year" in header and len(cells) > 1:
                                    data["EPS Estimate Next Year (Yahoo)"] = cells[1].text.strip()
            
            except Exception as e:
                self.logger.warning(f"Error scraping Yahoo Finance analysis page: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Error scraping Yahoo Finance statistics page: {str(e)}")
        
        # Add source metadata
        if data:
            self.logger.info(f"Successfully scraped Yahoo Finance data for {ticker}")
        else:
            self.logger.warning(f"No data found for {ticker} on Yahoo Finance")
            
        return data