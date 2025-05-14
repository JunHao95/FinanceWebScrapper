"""
Finviz scraper module
"""
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from ..utils.request_handler import make_request

class FinvizScraper(BaseScraper):
    """Scraper for Finviz"""
    
    def _scrape_data(self, ticker):
        """
        Scrape financial data from Finviz
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Dictionary containing scraped data
        """
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        
        response = make_request(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize data dictionary
        data = {}
        # Scrape analyst price target
        try:
            price_target = soup.find(text="Target Price").find_next("td").text
            data["Analyst Price Target (Finviz)"] = price_target
            print(  f"Analyst Price Target (Finviz): {price_target}")
        except Exception as e:
            self.logger.warning(f"Error scraping analyst price target for {ticker} from Finviz: {str(e)}")
        # Scrape current price 
        try:
            price_target = soup.find(text="Price").find_next("td").text
            data["Current Price (Finviz)"] = price_target
            print( f"Curernt Price (Finviz): {price_target}")
        except Exception as e:
            self.logger.warning(f"Error scraping current price  for {ticker} from Finviz: {str(e)}")
        # Find the snapshot table
        snapshot_table = soup.find('table', class_='snapshot-table2')
        if snapshot_table:
            rows = snapshot_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                for i in range(0, len(cells), 2):
                    if i + 1 < len(cells):
                        header = cells[i].text.strip()
                        value = cells[i+1].text.strip()
                        
                        # Basic valuation metrics
                        if header == "P/E":
                            data["P/E Ratio (Finviz)"] = value
                        elif header == "P/B":
                            data["P/B Ratio (Finviz)"] = value
                        elif header == "P/S":
                            data["P/S Ratio (Finviz)"] = value
                        elif header == "Forward P/E":
                            data["Forward P/E (Finviz)"] = value
                        
                        # Additional metrics
                        elif header == "PEG":
                            data["PEG Ratio (Finviz)"] = value
                        elif header == "EV/EBITDA":
                            data["EV/EBITDA (Finviz)"] = value
                        elif header == "ROE":
                            data["ROE (Finviz)"] = value
                        elif header == "ROA":
                            data["ROA (Finviz)"] = value
                        elif header == "ROI":
                            data["ROIC (Finviz)"] = value
                        # EPS metrics
                        elif header == "EPS (ttm)":
                            data["EPS (TTM) (Finviz)"] = value
                        elif header == "EPS next Y":
                            data["EPS Next Year (Finviz)"] = value
                        elif header == "EPS this Y":
                            data["EPS Growth This Year (Finviz)"] = value
                        elif header == "EPS next Y":
                            data["EPS Growth Next Year (Finviz)"] = value
                        elif header == "EPS next 5Y":
                            data["EPS Growth Next 5Y (Finviz)"] = value
                        elif header == "EPS growth qtr over qtr":
                            data["EPS Growth QoQ (Finviz)"] = value
                        
                        # Profitability metrics
                        elif header == "Profit Margin":
                            data["Profit Margin (Finviz)"] = value
                        elif header == "Oper. Margin":
                            data["Operating Margin (Finviz)"] = value
        else:
            self.logger.warning(f"Could not find snapshot table for {ticker} on Finviz")
        
        # Add source metadata
        if data:
            self.logger.info(f"Successfully scraped Finviz data for {ticker}")
        else:
            self.logger.warning(f"No data found for {ticker} on Finviz")
            
        return data