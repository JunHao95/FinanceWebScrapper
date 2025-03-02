"""
Financial API scraper module
"""
import os
import requests
import time
import logging
from .base_scraper import BaseScraper

class AlphaVantageAPIScraper(BaseScraper):
    """Scraper for Alpha Vantage Financial API"""
    
    def __init__(self, api_key=None, delay=1):
        """
        Initialize the Alpha Vantage API scraper
        
        Args:
            api_key (str): Alpha Vantage API key. If None, will try to get from ALPHA_VANTAGE_API_KEY environment variable
            delay (int): Delay in seconds between requests to avoid rate limiting
        """
        super().__init__(delay=delay)
        # Get API key from environment variable if not provided
        self.api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            self.logger.warning("Alpha Vantage API key not provided. Set ALPHA_VANTAGE_API_KEY environment variable.")
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _scrape_data(self, ticker):
        """
        Get financial data from Alpha Vantage API
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Dictionary containing scraped data
        """
        if not self.api_key:
            self.logger.error("Alpha Vantage API key not available. Skipping API data source.")
            return {"error": "Alpha Vantage API key not available"}
        
        data = {}
        
        # Get company overview (contains most fundamental data)
        try:
            self.logger.info(f"Fetching company overview from Alpha Vantage for {ticker}")
            overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={self.api_key}"
            
            response = requests.get(overview_url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # Check if we have actual data or an error
            if "Symbol" not in result:
                self.logger.warning(f"No overview data found for {ticker} on Alpha Vantage")
                return {}
            
            # Map Alpha Vantage fields to our standard format
            field_mapping = {
                "PERatio": "P/E Ratio (AlphaVantage)",
                "PriceToBookRatio": "P/B Ratio (AlphaVantage)",
                "PriceToSalesRatioTTM": "P/S Ratio (AlphaVantage)",
                "EPS": "EPS (AlphaVantage)",
                "ForwardPE": "Forward P/E (AlphaVantage)",
                "PEGRatio": "PEG Ratio (AlphaVantage)",
                "EVToEBITDA": "EV/EBITDA (AlphaVantage)",
                "ReturnOnEquityTTM": "ROE (AlphaVantage)",
                "ReturnOnAssetsTTM": "ROA (AlphaVantage)",
                "ProfitMargin": "Profit Margin (AlphaVantage)",
                "OperatingMarginTTM": "Operating Margin (AlphaVantage)",
                "DividendYield": "Dividend Yield (AlphaVantage)",
                "BookValue": "Book Value (AlphaVantage)",
                "TrailingPE": "Trailing P/E (AlphaVantage)",
                "Beta": "Beta (AlphaVantage)"
            }
            
            for av_field, our_field in field_mapping.items():
                if av_field in result and result[av_field]:
                    # Ensure values are numeric where possible
                    try:
                        value = float(result[av_field])
                        # Format percentages in a recognizable way
                        if "Margin" in our_field or "ROA" in our_field or "ROE" in our_field or "Yield" in our_field:
                            data[our_field] = f"{value:.2f}%"
                        else:
                            data[our_field] = f"{value:.2f}"
                    except (ValueError, TypeError):
                        data[our_field] = result[av_field]
            
            # Add additional metrics for context
            if "Name" in result:
                data["Company Name (AlphaVantage)"] = result["Name"]
            if "Sector" in result:
                data["Sector (AlphaVantage)"] = result["Sector"]
            if "Industry" in result:
                data["Industry (AlphaVantage)"] = result["Industry"]
            
            # Wait before next API call (if needed)
            time.sleep(self.delay)
            
            # Get additional cash flow data
            try:
                self.logger.info(f"Fetching cash flow data from Alpha Vantage for {ticker}")
                cash_flow_url = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={self.api_key}"
                
                cf_response = requests.get(cash_flow_url, timeout=10)
                cf_response.raise_for_status()
                
                cf_result = cf_response.json()
                
                if "annualReports" in cf_result and cf_result["annualReports"]:
                    latest_report = cf_result["annualReports"][0]
                    
                    if "operatingCashflow" in latest_report and latest_report["operatingCashflow"]:
                        data["Operating Cash Flow (AlphaVantage)"] = latest_report["operatingCashflow"]
                    
                    if "capitalExpenditures" in latest_report and latest_report["capitalExpenditures"]:
                        data["Capital Expenditures (AlphaVantage)"] = latest_report["capitalExpenditures"]
                        
                        # Calculate Free Cash Flow
                        try:
                            ocf = float(latest_report["operatingCashflow"])
                            capex = float(latest_report["capitalExpenditures"])
                            fcf = ocf - abs(capex)  # capex is usually negative
                            data["Free Cash Flow (AlphaVantage)"] = f"{fcf:.2f}"
                        except (ValueError, TypeError):
                            pass
            
            except Exception as e:
                self.logger.warning(f"Error fetching cash flow data for {ticker}: {str(e)}")
            
            return data
                
        except Exception as e:
            self.logger.error(f"Error scraping Alpha Vantage API for {ticker}: {str(e)}")
            return {"error": f"Error scraping Alpha Vantage API: {str(e)}"}


class FinhubAPIScraper(BaseScraper):
    """Scraper for Finhub Financial API"""
    
    def __init__(self, api_key=None, delay=1):
        """
        Initialize the Finhub API scraper
        
        Args:
            api_key (str): Finhub API key. If None, will try to get from FINHUB_API_KEY environment variable
            delay (int): Delay in seconds between requests to avoid rate limiting
        """
        super().__init__(delay=delay)
        # Get API key from environment variable if not provided
        self.api_key = api_key or os.environ.get("FINHUB_API_KEY")
        if not self.api_key:
            self.logger.warning("Finhub API key not provided. Set FINHUB_API_KEY environment variable.")
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _scrape_data(self, ticker):
        """
        Get financial data from Finhub API
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Dictionary containing scraped data
        """
        if not self.api_key:
            self.logger.error("Finhub API key not available. Skipping API data source.")
            return {"error": "Finhub API key not available"}
        
        data = {}
        
        # Get basic metrics
        try:
            self.logger.info(f"Fetching metrics from Finhub for {ticker}")
            metrics_url = f"https://finnhub.io/api/v1/stock/metric?symbol={ticker}&metric=all&token={self.api_key}"
            
            response = requests.get(metrics_url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if "metric" not in result:
                self.logger.warning(f"No metric data found for {ticker} on Finhub")
                return {}
            
            metrics = result["metric"]
            
            # Map Finhub fields to our standard format
            field_mapping = {
                "currentPE": "P/E Ratio (Finhub)",
                "pbLTM": "P/B Ratio (Finhub)",
                "psLTM": "P/S Ratio (Finhub)",
                "epsBasicExclExtraItemsAnnual": "EPS (Finhub)",
                "peForward": "Forward P/E (Finhub)",
                "pegTTM": "PEG Ratio (Finhub)",
                "evToEbitdaTTM": "EV/EBITDA (Finhub)",
                "roeTTM": "ROE (Finhub)",
                "roaTTM": "ROA (Finhub)",
                "roicTTM": "ROIC (Finhub)",
                "netProfitMarginTTM": "Profit Margin (Finhub)",
                "operatingMarginTTM": "Operating Margin (Finhub)",
                "dividendYieldIndicatedAnnual": "Dividend Yield (Finhub)",
                "bookValuePerShareQuarterly": "Book Value (Finhub)",
                "beta": "Beta (Finhub)"
            }
            
            for fh_field, our_field in field_mapping.items():
                if fh_field in metrics and metrics[fh_field] is not None:
                    # Format percentages in a recognizable way
                    if "Margin" in our_field or "ROA" in our_field or "ROE" in our_field or "ROIC" in our_field or "Yield" in our_field:
                        data[our_field] = f"{metrics[fh_field]:.2f}%"
                    else:
                        data[our_field] = f"{metrics[fh_field]:.2f}"
            
            # Get company profile for additional context
            try:
                profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={self.api_key}"
                
                profile_response = requests.get(profile_url, timeout=10)
                profile_response.raise_for_status()
                
                profile = profile_response.json()
                
                if profile:
                    if "name" in profile:
                        data["Company Name (Finhub)"] = profile["name"]
                    if "finnhubIndustry" in profile:
                        data["Industry (Finhub)"] = profile["finnhubIndustry"]
                    if "marketCapitalization" in profile:
                        data["Market Cap (Finhub)"] = f"{profile['marketCapitalization']:.2f}B"
            
            except Exception as e:
                self.logger.warning(f"Error fetching company profile for {ticker}: {str(e)}")
            
            return data
                
        except Exception as e:
            self.logger.error(f"Error scraping Finhub API for {ticker}: {str(e)}")
            return {"error": f"Error scraping Finhub API: {str(e)}"}