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
        # Main company profile page
        company_url = f"https://www.marketwatch.com/investing/stock/{ticker}/company-profile"
        
        # Financials page for more metrics
        financials_url = f"https://www.marketwatch.com/investing/stock/{ticker}/financials"
        
        # Initialize data dictionary
        data = {}
        
        # Scrape company profile page
        try:
            self.logger.info(f"Fetching company profile from MarketWatch for {ticker}")
            response = make_request(company_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse valuation metrics
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
                        
                        # Basic valuation metrics
                        if "P/E Ratio" in header:
                            data["P/E Ratio (MW)"] = value
                        elif "Price to Book Ratio" in header:
                            data["P/B Ratio (MW)"] = value
                        elif "Price to Sales Ratio" in header:
                            data["P/S Ratio (MW)"] = value
                        elif "PEG Ratio" in header:
                            data["PEG Ratio (MW)"] = value
                        elif "Enterprise Value to EBITDA" in header or "EV/EBITDA" in header:
                            data["EV/EBITDA (MW)"] = value
            
            # If we couldn't find the valuation section, try alternative elements
            if not data:
                valuation_items = soup.find_all('div', class_='cell')
                for item in valuation_items:
                    label = item.find('span', class_='label')
                    value = item.find('span', class_='primary')
                    
                    if label and value:
                        header = label.text.strip()
                        val = value.text.strip()
                        
                        # Basic valuation metrics
                        if "Price to Earnings" in header:
                            data["P/E Ratio (MW)"] = val
                        elif "Price to Book Ratio" in header:
                            data["P/B Ratio (MW)"] = val
                        elif "Price to Sales Ratio" in header:
                            data["P/S Ratio (MW)"] = val
                        elif "PEG Ratio" in header:
                            data["PEG Ratio (MW)"] = val
                        elif "Enterprise Value to EBITDA" in header or "EV/EBITDA" in header:
                            data["EV/EBITDA (MW)"] = val
        
            # Now scrape financials page for additional metrics
            try:
                financials_response = make_request(financials_url, headers=self.headers)
                financials_soup = BeautifulSoup(financials_response.text, 'html.parser')
                
                # Look for EPS
                eps_row = None
                rows = financials_soup.find_all('tr', class_='table__row')
                for row in rows:
                    if "EPS (Basic)" in row.text or "Earnings Per Share" in row.text:
                        eps_row = row
                        break
                
                if eps_row:
                    cells = eps_row.find_all('td', class_='table__cell')
                    if len(cells) > 1:
                        # Usually the most recent year is the second cell
                        data["EPS (MW)"] = cells[1].text.strip()
                
                # Look for ROE and ROIC
                for row in rows:
                    row_text = row.text.lower()
                    cells = row.find_all('td')
                    
                    if "return on equity" in row_text or "roe" in row_text:
                        if len(cells) > 1:
                            data["ROE (MW)"] = cells[1].text.strip()
                    
                    if "return on invested capital" in row_text or "roic" in row_text:
                        if len(cells) > 1:
                            data["ROIC (MW)"] = cells[1].text.strip()
            
            except Exception as e:
                self.logger.warning(f"Error scraping MarketWatch financials page: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Error scraping MarketWatch company profile: {str(e)}")
        
        # Add source metadata
        if data:
            self.logger.info(f"Successfully scraped MarketWatch data for {ticker}")
        else:
            self.logger.warning(f"No data found for {ticker} on MarketWatch")
            
        return data