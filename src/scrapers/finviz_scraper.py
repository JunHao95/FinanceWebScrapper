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
            self.logger.debug(f"Analyst Price Target (Finviz): {price_target}")
        except Exception as e:
            self.logger.warning(f"Error scraping analyst price target for {ticker} from Finviz: {str(e)}")
        # Scrape current price 
        try:
            price_target = soup.find(text="Price").find_next("td").text
            data["Current Price (Finviz)"] = price_target
            self.logger.debug(f"Current Price (Finviz): {price_target}")
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

        soup.decompose()

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

            cf_soup.decompose()

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

    def get_peer_data(self, ticker):
        """
        Fetch similar stocks and their 4 key metrics from Finviz.

        Args:
            ticker (str): Primary stock ticker (e.g. "AAPL")

        Returns:
            dict: {
                "sector": str,
                "peers": [peer_ticker, ...],          # peer tickers only (not primary)
                "peer_data": [                         # primary + peers rows
                    {"ticker": str, "pe": float|None, "pb": float|None,
                     "roe": float|None, "op_margin": float|None},
                    ...
                ]
            }
        """
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        response = make_request(url, headers=self.headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Extract sector ---
        # Finviz (2025+): sector link has href containing "sec_" in quote-links div.
        # Fallback: legacy snapshot-table2 "Sector" td label.
        sector = ""
        sector_link = soup.find('a', class_='tab-link',
                                href=lambda h: h and 'sec_' in h and 'screener' in h)
        if sector_link:
            sector = sector_link.text.strip()
        if not sector:
            snapshot_table = soup.find('table', class_='snapshot-table2')
            if snapshot_table:
                for row in snapshot_table.find_all('tr'):
                    cells = row.find_all('td')
                    for i in range(0, len(cells), 2):
                        if i + 1 < len(cells) and cells[i].text.strip() == "Sector":
                            sector = cells[i + 1].text.strip()

        # --- Extract peer stock tickers ---
        # Finviz (2025+): peers are in span[data-boxover-ticker] elements
        # inside a div preceded by an <a>Peers</a> label.
        # Fallback: legacy "Similar" td label for older page versions.
        peer_tickers = []
        try:
            # New layout: <a class="tab-link" href="screener.ashx?t=...">Peers</a>:
            #             <span style="font-size:11px">
            #               <span data-boxover-ticker="MSFT"><a>MSFT</a></span> ...
            peers_link = soup.find('a', class_='tab-link', string='Peers')
            if peers_link:
                peer_span = peers_link.find_next_sibling('span')
                if peer_span:
                    peer_tickers = [
                        sp.get('data-boxover-ticker', '').strip()
                        for sp in peer_span.find_all('span', attrs={'data-boxover-ticker': True})
                        if sp.get('data-boxover-ticker', '').strip()
                    ]
            # Legacy fallback: "Similar" td label
            if not peer_tickers:
                similar_label = soup.find(string=lambda t: t and t.strip() == 'Similar')
                if similar_label:
                    similar_td = similar_label.find_parent('td')
                    if similar_td:
                        next_td = similar_td.find_next_sibling('td')
                        if next_td:
                            links = next_td.find_all('a')
                            if links:
                                peer_tickers = [a.text.strip() for a in links if a.text.strip()]
                            else:
                                peer_tickers = [t.strip() for t in next_td.text.split(',') if t.strip()]
        except Exception as e:
            self.logger.warning(f"Could not parse peer stocks for {ticker}: {e}")

        soup.decompose()

        # Limit to 10 peers
        peer_tickers = peer_tickers[:10]

        def _parse_metric(value):
            """Convert string metric to float, return None on failure."""
            if not value or value in ('-', 'N/A', ''):
                return None
            try:
                return float(value.replace('%', '').replace(',', ''))
            except (ValueError, AttributeError):
                return None

        def _fetch_metrics(tkr):
            """Fetch pe/pb/roe/op_margin for a single ticker."""
            try:
                data = self._scrape_data(tkr)
                return {
                    "ticker": tkr,
                    "pe": _parse_metric(data.get("P/E Ratio (Finviz)")),
                    "pb": _parse_metric(data.get("P/B Ratio (Finviz)")),
                    "roe": _parse_metric(data.get("ROE (Finviz)")),
                    "op_margin": _parse_metric(data.get("Operating Margin (Finviz)")),
                }
            except Exception as e:
                self.logger.warning(f"Failed to fetch metrics for {tkr}: {e}")
                return {"ticker": tkr, "pe": None, "pb": None, "roe": None, "op_margin": None}

        # Primary ticker first, then peers
        peer_data = [_fetch_metrics(ticker)] + [_fetch_metrics(p) for p in peer_tickers]

        return {
            "sector": sector,
            "peers": peer_tickers,
            "peer_data": peer_data,
        }