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
                        
                        # Cash metrics
                        elif header == "Cash/sh":
                            data["Cash Per Share (Finviz)"] = value
        else:
            self.logger.warning(f"Could not find snapshot table for {ticker} on Finviz")
        
        # Scrape Cash Flow tab for detailed cash flow metrics
        try:
            cashflow_url = f"https://finviz.com/quote.ashx?t={ticker}&ty=c&p=d&b=1"
            self.logger.info(f"Fetching cash flow data from Finviz for {ticker}")
            
            cf_response = make_request(cashflow_url, headers=self.headers)
            cf_soup = BeautifulSoup(cf_response.text, 'html.parser')
            
            # Find the financial table with cash flow data
            financial_tables = cf_soup.find_all('table', class_='js-table-wrapper')
            
            for table in financial_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].text.strip()
                        # Get the most recent value (usually the second column)
                        value = cells[1].text.strip() if len(cells) > 1 else None
                        
                        # Cash flow metrics
                        if "Operating Cash Flow" in label and value:
                            data["Operating Cash Flow (Finviz)"] = value
                        elif "Capital Expenditure" in label and value:
                            data["Capital Expenditures (Finviz)"] = value
                        elif "Free Cash Flow" in label and value:
                            data["Free Cash Flow (Finviz)"] = value
                        elif "Cash" in label and "Equivalents" in label and value:
                            data["Cash (Finviz)"] = value
                        elif label == "Cash & Short Term Investments" and value:
                            data["Cash and ST Investments (Finviz)"] = value
            
            if any(key.startswith("Operating Cash Flow") or key.startswith("Free Cash Flow") for key in data.keys()):
                self.logger.info(f"Successfully scraped cash flow data from Finviz for {ticker}")
        
        except Exception as e:
            self.logger.warning(f"Error scraping cash flow tab for {ticker} from Finviz: {str(e)}")
        
        # Add source metadata
        if data:
            self.logger.info(f"Successfully scraped Finviz data for {ticker}")
        else:
            self.logger.warning(f"No data found for {ticker} on Finviz")
            
        return data