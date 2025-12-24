"""
Yahoo Finance scraper module
"""
from bs4 import BeautifulSoup
import requests
from .base_scraper import BaseScraper
from ..utils.request_handler import make_request
import yfinance as yf

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
        statistics_url = f"https://finance.yahoo.com/quote/{ticker}/key-statistics/"
        
        # Analysis page contains EPS and growth estimates
        analysis_url = f"https://finance.yahoo.com/quote/{ticker}/analysis"
        
        # Initialize data dictionary
        data = {}
        
        # Scrape statistics page
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                        '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        try:
            self.logger.info(f"Fetching statistics from Yahoo Finance for {ticker}")
            response = make_request(statistics_url, headers=self.headers, timeout=10)
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
        
        # Get additional data from yfinance API (always try, even if web scraping failed)
        try:
            self.logger.info(f"Fetching data from yfinance API for {ticker}")
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Fetch analyst price targets
            target_mean_price = info.get("targetMeanPrice", None)
            target_low_price = info.get("targetLowPrice", None)
            target_high_price = info.get("targetHighPrice", None)
            
            if target_mean_price:
                data["Analyst Price Target Mean (Yahoo)"] = f"{target_mean_price:.2f}"
            if target_low_price:
                data["Analyst Price Target Low (Yahoo)"] = f"{target_low_price:.2f}"
            if target_high_price:
                data["Analyst Price Target High (Yahoo)"] = f"{target_high_price:.2f}"
            
            # Fetch cash metrics
            total_cash = info.get("totalCash", None)
            if total_cash:
                data["Cash (Yahoo)"] = f"{total_cash:,.0f}"
            
            # Fetch additional cash flow metrics
            total_cash_per_share = info.get("totalCashPerShare", None)
            if total_cash_per_share:
                data["Cash Per Share (Yahoo)"] = f"{total_cash_per_share:.2f}"
            
            free_cashflow = info.get("freeCashflow", None)
            if free_cashflow:
                data["Free Cash Flow (Yahoo)"] = f"{free_cashflow:,.0f}"
            
            operating_cashflow = info.get("operatingCashflow", None)
            if operating_cashflow:
                data["Operating Cash Flow (Yahoo)"] = f"{operating_cashflow:,.0f}"
            
            # Fetch valuation metrics if not already scraped from web
            if "P/E Ratio (Yahoo)" not in data and info.get("trailingPE"):
                data["P/E Ratio (Yahoo)"] = f"{info.get('trailingPE'):.2f}"
            if "Forward P/E (Yahoo)" not in data and info.get("forwardPE"):
                data["Forward P/E (Yahoo)"] = f"{info.get('forwardPE'):.2f}"
            if "P/B Ratio (Yahoo)" not in data and info.get("priceToBook"):
                data["P/B Ratio (Yahoo)"] = f"{info.get('priceToBook'):.2f}"
            if "P/S Ratio (Yahoo)" not in data and info.get("priceToSalesTrailing12Months"):
                data["P/S Ratio (Yahoo)"] = f"{info.get('priceToSalesTrailing12Months'):.2f}"
            if "PEG Ratio (Yahoo)" not in data and info.get("pegRatio"):
                data["PEG Ratio (Yahoo)"] = f"{info.get('pegRatio'):.2f}"
            
            # Profitability metrics
            if "ROE (Yahoo)" not in data and info.get("returnOnEquity"):
                data["ROE (Yahoo)"] = f"{info.get('returnOnEquity')*100:.2f}%"
            if "ROA (Yahoo)" not in data and info.get("returnOnAssets"):
                data["ROA (Yahoo)"] = f"{info.get('returnOnAssets')*100:.2f}%"
            if "Profit Margin (Yahoo)" not in data and info.get("profitMargins"):
                data["Profit Margin (Yahoo)"] = f"{info.get('profitMargins')*100:.2f}%"
            if "Operating Margin (Yahoo)" not in data and info.get("operatingMargins"):
                data["Operating Margin (Yahoo)"] = f"{info.get('operatingMargins')*100:.2f}%"
            
            # EPS
            if "EPS (Yahoo)" not in data and info.get("trailingEps"):
                data["EPS (Yahoo)"] = f"{info.get('trailingEps'):.2f}"
            
            # Earnings Growth
            if info.get("earningsGrowth"):
                data["Earnings Growth (Yahoo)"] = f"{info.get('earningsGrowth')*100:.2f}%"
            
            # Financial metrics
            if info.get("grossProfits"):
                data["Gross Profits (Yahoo)"] = f"{info.get('grossProfits'):,.0f}"
            
            if info.get("totalDebt"):
                data["Total Debt (Yahoo)"] = f"{info.get('totalDebt'):,.0f}"
            
            if info.get("ebitda"):
                data["EBITDA (Yahoo)"] = f"{info.get('ebitda'):,.0f}"
            
            # Market info
            if info.get("currentPrice"):
                data["Current Price (Yahoo)"] = f"{info.get('currentPrice'):.2f}"
            if info.get("marketCap"):
                data["Market Cap (Yahoo)"] = f"{info.get('marketCap'):,.0f}"
            
            self.logger.info(f"Successfully fetched yfinance API data for {ticker}")
            
        except Exception as e:
            self.logger.warning(f"Error fetching yfinance API data for {ticker}: {str(e)}")
        
        # Add source metadata
        if data:
            self.logger.info(f"Successfully scraped Yahoo Finance data for {ticker}")
        else:
            self.logger.warning(f"No data found for {ticker} on Yahoo Finance")
            
        return data