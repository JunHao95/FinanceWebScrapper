"""
Short Snippets for Troubleshooting FinanceWebScrapper Webapp Results
=====================================================================

Minimal code snippets to reproduce and debug webapp analytics and scrapers:

Analytics Snippets:
1. snippet_fundamental_analysis() - Test fundamental scoring
2. snippet_monte_carlo_var() - Test VaR/ES calculations
3. snippet_correlation_analysis() - Test correlation matrix

Scraper Snippets:
4. snippet_yahoo_scraper() - Test Yahoo Finance scraper
5. snippet_finviz_scraper() - Test Finviz scraper
6. snippet_google_scraper() - Test Google Finance scraper
7. snippet_cnn_feargreed() - Test CNN Fear & Greed Index scraper
8. snippet_sentiment_scraper() - Test enhanced sentiment scraper

Requirements: pip install yfinance numpy pandas beautifulsoup4 requests

Usage:
    from python_snippets import snippet_yahoo_scraper
    result = snippet_yahoo_scraper("AAPL")
"""

from typing import Dict, List, Any
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.analytics.financial_analytics import FinancialAnalytics
    from src.scrapers.yahoo_scraper import YahooFinanceScraper
    from src.scrapers.finviz_scraper import FinvizScraper
    from src.scrapers.google_scraper import GoogleFinanceScraper
    from src.scrapers.cnn_scraper import CNNFearGreedScraper
    from src.scrapers.enhanced_sentiment_scraper import EnhancedSentimentScraper
    WEBAPP_MODULES_AVAILABLE = True
except ImportError:
    WEBAPP_MODULES_AVAILABLE = False
    print("⚠️  Cannot import webapp modules. Run from project root.")


# =============================================================================
# SCRAPER SNIPPETS
# =============================================================================

def snippet_yahoo_scraper(ticker: str = "AAPL") -> Dict[str, Any]:
    """Test Yahoo Finance scraper."""
    if not WEBAPP_MODULES_AVAILABLE:
        raise ImportError("Webapp modules required. Run from project root.")
    
    print(f"\n🔍 Yahoo scraper for {ticker}...")
    scraper = YahooFinanceScraper()
    data = scraper._scrape_data(ticker)
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
    else:
        print(f"✅ Scraped {len(data)} fields")
        print(f"   Price: ${data.get('currentPrice', 'N/A')}")
        print(f"   P/E: {data.get('trailingPE', 'N/A')}")
    
    return data


def snippet_finviz_scraper(ticker: str = "AAPL") -> Dict[str, Any]:
    """Test Finviz scraper."""
    if not WEBAPP_MODULES_AVAILABLE:
        raise ImportError("Webapp modules required. Run from project root.")
    
    print(f"\n🔍 Finviz scraper for {ticker}...")
    scraper = FinvizScraper()
    data = scraper._scrape_data(ticker)
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
    else:
        print(f"✅ Scraped {len(data)} fields")
        print(f"   Analyst Target: {data.get('Analyst Price Target (Finviz)', 'N/A')}")
        print(f"   Current Price: {data.get('Current Price (Finviz)', 'N/A')}")
    
    return data


def snippet_google_scraper(ticker: str = "AAPL") -> Dict[str, Any]:
    """Test Google Finance scraper."""
    if not WEBAPP_MODULES_AVAILABLE:
        raise ImportError("Webapp modules required. Run from project root.")
    
    print(f"\n🔍 Google scraper for {ticker}...")
    scraper = GoogleFinanceScraper()
    data = scraper._scrape_data(ticker)
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
    else:
        print(f"✅ Scraped {len(data)} fields")
        for key, value in list(data.items())[:3]:
            print(f"   {key}: {value}")
    
    return data


def snippet_cnn_feargreed() -> Dict[str, Any]:
    """Test CNN Fear & Greed Index scraper."""
    if not WEBAPP_MODULES_AVAILABLE:
        raise ImportError("Webapp modules required. Run from project root.")
    
    print(f"\n📊 CNN Fear & Greed Index...")
    scraper = CNNFearGreedScraper()
    data = scraper.scrape_data()
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
    else:
        fg = data.get('fear_and_greed', {})
        print(f"✅ Fear & Greed Score: {fg.get('score', 'N/A')}")
        print(f"   Rating: {fg.get('rating', 'N/A')}")
        print(f"   Metrics: {len(data)} indicators")
    
    return data


def snippet_sentiment_scraper(ticker: str = "AAPL") -> Dict[str, Any]:
    """Test enhanced sentiment scraper."""
    if not WEBAPP_MODULES_AVAILABLE:
        raise ImportError("Webapp modules required. Run from project root.")
    
    print(f"\n💬 Sentiment analysis for {ticker}...")
    scraper = EnhancedSentimentScraper()
    data = scraper._scrape_data(ticker)
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
    else:
        print(f"✅ Sentiment data collected")
        if 'sentiment_score' in data:
            print(f"   Score: {data.get('sentiment_score', 'N/A')}")
        if 'sentiment_label' in data:
            print(f"   Label: {data.get('sentiment_label', 'N/A')}")
    
    return data


# =============================================================================
# ANALYTICS SNIPPETS
# =============================================================================

def snippet_fundamental_analysis(ticker: str = "AAPL") -> Dict[str, Any]:
    """Run fundamental analysis using webapp's FinancialAnalytics."""
    if not WEBAPP_MODULES_AVAILABLE:
        raise ImportError("Webapp modules required. Run from project root.")
    
    import yfinance as yf
    
    print(f"\n📊 Analyzing {ticker}...")
    stock = yf.Ticker(ticker)
    analytics = FinancialAnalytics()
    result = analytics.fundamental_analysis(stock.info, ticker)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Score: {result.get('overall_score', 0):.1f}/10")
        print(f"   Outlook: {result.get('investment_outlook', 'N/A')}")
    
    return result


def snippet_monte_carlo_var(ticker: str = 'AAPL') -> Dict[str, Any]:
    """Run Monte Carlo VaR using webapp's FinancialAnalytics."""
    if not WEBAPP_MODULES_AVAILABLE:
        raise ImportError("Webapp modules required. Run from project root.")
    
    print(f"\n🎲 Monte Carlo for {ticker}...")
    analytics = FinancialAnalytics()
    result = analytics.monte_carlo_var_es(
        tickers=[ticker],
        days=252,
        simulations=5000,
        forecast_days=252,
        confidence_level=0.95,
        initial_investment=100000
    )
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        var_dict = result.get('VaR', {})
        var_value = var_dict.get('VaR at 95.0% confidence', {}).get('Value', 0)
        print(f"✅ VaR (95%): {var_value:,.2f}")
        print(f"   ES: {result.get('ES', 0):,.2f}")
    
    return result


def snippet_correlation_analysis(tickers: List[str] = ['AAPL', 'MSFT', 'GOOGL']) -> Dict[str, Any]:
    """Run correlation analysis using webapp's FinancialAnalytics."""
    if not WEBAPP_MODULES_AVAILABLE:
        raise ImportError("Webapp modules required. Run from project root.")
    
    print(f"\n📊 Correlation for {len(tickers)} tickers...")
    analytics = FinancialAnalytics()
    result = analytics.correlation_analysis(tickers, days=252)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Avg Correlation: {result.get('Average Correlation', 0):.3f}")
        print(f"   Diversification: {result.get('Diversification Level', 'N/A')}")
    
    return result
