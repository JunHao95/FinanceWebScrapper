"""
CNN Fear and Greed Index Scraper
"""
import requests
from bs4 import BeautifulSoup


class CNNFearGreedScraper:
    """Scraper for CNN Fear and Greed Index"""

    def __init__(self):
        self.url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.metrics = [
            'fear_and_greed',
            'fear_and_greed_historical',
            'market_momentum_sp500',
            'market_momentum_sp125',
            'stock_price_strength',
            'stock_price_breadth',
            'put_call_options',
            'market_volatility_vix',
            'market_volatility_vix_50',
            'junk_bond_demand',
            'safe_haven_demand'
        ]

    def scrape_data(self):
        """
        Scrape Fear and Greed Index data from CNN.

        Returns:
            dict: Dictionary containing score and rating for each metric.
        """
        try:
            response = requests.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = {}
            for metric in self.metrics:
                metric_data = data.get(metric)
                if isinstance(metric_data, dict):
                    score = metric_data.get('score')
                    rating = metric_data.get('rating')
                    results[metric] = {'score': score, 'rating': rating}
                elif isinstance(metric_data, list) and metric_data:
                    # For historical data, get the latest entry
                    latest = metric_data[-1]
                    score = latest.get('score')
                    rating = latest.get('rating')
                    results[metric] = {'score': score, 'rating': rating}
                else:
                    results[metric] = {'score': None, 'rating': None}
            print(f"DEBUG, results: {results}")
            return results

        except Exception as e:
            print(f"Error fetching data from CNN Fear and Greed API: {e}")
            return {"error": str(e)}

