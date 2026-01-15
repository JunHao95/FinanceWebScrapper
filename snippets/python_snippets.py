"""
Short Snippets for Troubleshooting FinanceWebScrapper Webapp Results
=====================================================================

Minimal code snippets to reproduce and debug webapp analytics and scrapers:

Analytics Snippets:
1. snippet_fundamental_analysis() - Test fundamental scoring
2. snippet_monte_carlo_var() - Test VaR/ES calculations
3. snippet_correlation_analysis() - Test correlation matrix
4. snippet_single_asset_stress_test() - Test single asset stress test
5. snippet_multi_asset_stress_test() - Test multi-asset portfolio stress test

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


def snippet_single_asset_stress_test(ticker: str = 'AAPL', initial_investment: float = 100000) -> Dict[str, Any]:
    """
    Run single asset stress test using webapp's FinancialAnalytics.
    
    Tests stress scenarios on a single stock with increased volatility.
    
    Args:
        ticker: Stock ticker symbol
        initial_investment: Initial portfolio value
    
    Returns:
        dict: Stress test results with Base Case, Stress Case, and Impact
    """
    if not WEBAPP_MODULES_AVAILABLE:
        raise ImportError("Webapp modules required. Run from project root.")
    
    print(f"\n⚠️  Single Asset Stress Test for {ticker}...")
    print(f"   Initial Investment: ${initial_investment:,.2f}")
    
    analytics = FinancialAnalytics()
    result = analytics.stress_test_var(
        tickers=[ticker],
        initial_investment=initial_investment,
        simulations=10000,
        confidence_level=0.95,
        forecast_days=252,
        vol_stress_multiplier=2.0  # 2x volatility stress
    )
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        base_var = result.get('Base Case', {}).get('VaR', 0)
        stress_var = result.get('Stress Case', {}).get('VaR', 0)
        var_increase_pct = result.get('Stress Impact', {}).get('VaR Increase %', 0)
        
        print(f"✅ Base Case VaR (95%): ${base_var:,.2f}")
        print(f"   Stress Case VaR (95%): ${stress_var:,.2f}")
        print(f"   VaR Increase: {var_increase_pct}% of portfolio")
    
    return result


def snippet_multi_asset_stress_test(
    tickers: List[str] = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
    initial_investment: float = 100000,
    vol_stress_multiplier: float = 4.0,
    degrees_of_freedom: int = 3,
    liquidity_haircut: float = 0.05
) -> Dict[str, Any]:
    """
    Run multi-asset portfolio stress test with extreme parameters.
    
    Tests diversified portfolio under extreme crisis conditions with:
    - Fat-tailed distributions (Student-t) for Black Swan events
    - High correlation breakdown (90%) during crisis
    - Increased volatility
    - Liquidity haircuts
    
    Args:
        tickers: List of stock ticker symbols
        initial_investment: Initial portfolio value
        vol_stress_multiplier: Volatility multiplier (default: 4.0x)
        degrees_of_freedom: Lower = fatter tails (default: 3)
        liquidity_haircut: Transaction cost % in crisis (default: 0.05 = 5%)
    
    Returns:
        dict: Comprehensive stress test results with Base/Stress Cases and Impact
    """
    if not WEBAPP_MODULES_AVAILABLE:
        raise ImportError("Webapp modules required. Run from project root.")
    
    print(f"\n⚠️  Multi-Asset Portfolio Stress Test...")
    print(f"   Portfolio: {', '.join(tickers)}")
    print(f"   Initial Investment: ${initial_investment:,.2f}")
    print(f"   Parameters: {vol_stress_multiplier}x vol, df={degrees_of_freedom}, {liquidity_haircut*100}% haircut")
    
    analytics = FinancialAnalytics()
    
    # Optional: Define custom portfolio weights (or use None for equal weights)
    portfolio_weights = {
        'AAPL': 0.25,
        'MSFT': 0.25,
        'GOOGL': 0.20,
        'AMZN': 0.15,
        'TSLA': 0.15
    }
    
    result = analytics.stress_test_var(
        tickers=tickers,
        initial_investment=initial_investment,
        simulations=10000,
        confidence_level=0.95,
        forecast_days=252,
        vol_stress_multiplier=vol_stress_multiplier,
        rho_stress=0.9,  # 90% correlation during crisis
        use_fat_tails=True,  # Use Student-t distribution
        degrees_of_freedom=degrees_of_freedom,
        liquidity_haircut=liquidity_haircut,
        portfolio_weights=portfolio_weights
    )
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        base_var = result.get('Base Case', {}).get('VaR', 0)
        base_var_pct = result.get('Base Case', {}).get('VaR %', 0)
        stress_var = result.get('Stress Case', {}).get('VaR', 0)
        stress_var_pct = result.get('Stress Case', {}).get('VaR %', 0)
        var_99 = result.get('Stress Case', {}).get('VaR 99%', 0)
        var_99_pct = result.get('Stress Case', {}).get('VaR 99% %', 0)
        es = result.get('Stress Case', {}).get('Expected Shortfall', 0)
        
        print(f"\n✅ BASE CASE (Normal Market):")
        print(f"   VaR (95%): ${base_var:,.2f} ({base_var_pct:.2f}% of portfolio)")
        
        print(f"\n⚠️  STRESS CASE (Extreme Crisis):")
        print(f"   VaR (95%): ${stress_var:,.2f} ({stress_var_pct:.2f}% of portfolio)")
        print(f"   VaR (99%): ${var_99:,.2f} ({var_99_pct:.2f}% of portfolio)")
        print(f"   Expected Shortfall: ${es:,.2f}")
        
        print(f"\n💡 INTERPRETATION:")
        print(f"   In an EXTREME crisis, with 95% confidence:")
        print(f"   • Maximum loss: {stress_var_pct:.1f}% (${stress_var:,.0f})")
        print(f"   • Tail event (99%): {var_99_pct:.1f}% (${var_99:,.0f})")
    
    return result
