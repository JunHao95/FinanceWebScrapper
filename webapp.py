#!/usr/bin/env python3
"""
Flask Web Application for Stock Financial Metrics Scraper
"""
import os
import sys
import json
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
import tempfile
import logging
from logging.handlers import RotatingFileHandler
import numpy as np
import copy
import concurrent.futures
import threading
import time
import traceback
import gc

try:
    import openai
except ImportError:
    openai = None

# Load environment variables
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

# Import lightweight scrapers immediately
from src.scrapers.yahoo_scraper import YahooFinanceScraper
from src.scrapers.finviz_scraper import FinvizScraper
from src.scrapers.google_scraper import GoogleFinanceScraper
from src.scrapers.cnn_scraper import CNNFearGreedScraper
from src.scrapers.api_scraper import AlphaVantageAPIScraper, FinhubAPIScraper
from src.indicators.technical_indicators import TechnicalIndicators
from src.utils.data_formatter import format_data_as_dataframe
from src.utils.email_utils import send_consolidated_report

# LAZY IMPORTS: Only import heavy ML libraries when actually needed
# These imports load torch, transformers (500MB+ in memory)
# from src.scrapers.enhanced_sentiment_scraper import EnhancedSentimentScraper
# from src.analytics.financial_analytics import FinancialAnalytics

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Set socket timeout for cloud hosting (prevents timeout during long scraping operations)
import socket
socket.setdefaulttimeout(600)  # 10 minutes timeout

# Helper functions for lazy loading heavy modules
def get_enhanced_sentiment_scraper(alpha_vantage_key="", delay=1):
    """Lazy load EnhancedSentimentScraper only when needed"""
    from src.scrapers.enhanced_sentiment_scraper import EnhancedSentimentScraper
    return EnhancedSentimentScraper(alpha_vantage_key=alpha_vantage_key, delay=delay)

def get_financial_analytics(config=None):
    """Lazy load FinancialAnalytics only when needed"""
    from src.analytics.financial_analytics import FinancialAnalytics
    return FinancialAnalytics(config=config)

# Environment helpers
def is_cloud_environment() -> bool:
    """Detect if running on a cloud platform (Render).

    Render sets the environment variable RENDER=true and may also expose
    RENDER_SERVICE_ID/RENDER_EXTERNAL_URL. We check these to decide defaults.
    """
    if os.environ.get("RENDER", "").lower() == "true":
        return True
    if os.environ.get("RENDER_SERVICE_ID") or os.environ.get("RENDER_EXTERNAL_URL"):
        return True
    return False

def get_sentiment_enabled_default() -> bool:
    """Sentiment default: ON locally, OFF on cloud; env var can override.

    ENABLE_SENTIMENT_ANALYSIS env var ("true"/"false") takes precedence.
    If not set, default to False on cloud (memory heavy) and True locally.
    """
    override = os.environ.get("ENABLE_SENTIMENT_ANALYSIS")
    if override is not None:
        return str(override).lower() == "true"
    return not is_cloud_environment()

# Setup logging
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
file_handler = RotatingFileHandler(
    os.path.join(LOGS_DIR, 'webapp.log'),
    maxBytes=1024*1024*5,
    backupCount=5
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(file_handler)

# Load configuration
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

def load_config():
    """Load configuration from config.json file"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logger.warning(f"Configuration file {CONFIG_FILE} not found. Using default settings.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing configuration file: {e}. Using default settings.")
        return {}

config = load_config()

# Create webapp-specific config that disables MongoDB storage
# MongoDB storage should only happen via CLI (run_scraper.sh/uat_run_scraper.sh)
webapp_config = copy.deepcopy(config) if config else {}

# Force disable MongoDB for cloud deployment
if os.environ.get('MONGODB_ENABLED', 'true').lower() == 'false':
    logger.info("MongoDB disabled via environment variable (cloud deployment)")
    if 'mongodb' not in webapp_config:
        webapp_config['mongodb'] = {}
    webapp_config['mongodb']['enabled'] = False
if 'mongodb' not in webapp_config:
    webapp_config['mongodb'] = {}
webapp_config['mongodb']['enabled'] = False  # Disable MongoDB for Flask app
logger.info("MongoDB storage disabled for web application - storage only via CLI scripts")

def convert_numpy_types(data):
    """
    Convert numpy types to native Python types for JSON serialization
    Also converts NaN/Inf to None for valid JSON
    
    Args:
        data: Data to convert (dict, list, or primitive type)
        
    Returns:
        Converted data with Python native types
    """
    if isinstance(data, dict):
        return {key: convert_numpy_types(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_numpy_types(item) for item in data]
    elif isinstance(data, np.ndarray):
        # Convert array to list and handle NaN/Inf
        return convert_numpy_types(data.tolist())
    elif hasattr(data, 'item'):  # numpy scalar types have .item() method
        try:
            value = data.item()
            # Check for NaN or Inf
            if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                return None
            return value
        except (ValueError, AttributeError):
            return data
    elif isinstance(data, float):
        # Handle Python float NaN/Inf
        if np.isnan(data) or np.isinf(data):
            return None
        return data
    else:
        return data

def run_scrapers_for_ticker(ticker, sources=['all'], alpha_key=None, finhub_key=None):
    """
    Run scrapers for a single ticker with concurrent processing for maximum performance
    
    Args:
        ticker (str): Stock ticker symbol
        sources (list): List of data sources to scrape
        alpha_key (str): Alpha Vantage API key
        finhub_key (str): Finhub API key
        
    Returns:
        dict: Dictionary containing scraped data
    """
    results = {
        "Ticker": ticker,
        "Data Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Thread-safe result collection
    results_lock = threading.Lock()
    
    def run_scraper(scraper_name, scraper_func):
        """Thread-safe scraper runner"""
        try:
            logger.info(f"Scraping {scraper_name} data for {ticker}...")
            data = scraper_func()
            
            with results_lock:
                if data and not (isinstance(data, dict) and "error" in data):
                    results.update(data)
                    
        except Exception as e:
            logger.error(f"Error in {scraper_name} for {ticker}: {e}")
    
    # Define scraper tasks based on requested sources
    scraper_tasks = []
    
    if 'all' in sources or 'yahoo' in sources:
        scraper_tasks.append(("Yahoo Finance", lambda: YahooFinanceScraper(delay=1).get_data(ticker)))
    
    if 'all' in sources or 'finviz' in sources:
        scraper_tasks.append(("Finviz", lambda: FinvizScraper(delay=1).get_data(ticker)))
    
    if 'all' in sources or 'google' in sources:
        scraper_tasks.append(("Google Finance", lambda: GoogleFinanceScraper(delay=1).get_data(ticker)))
    
    # Enhanced sentiment analysis - memory intensive; default ON locally, OFF on cloud
    sentiment_enabled = get_sentiment_enabled_default()
    if sentiment_enabled and ('all' in sources or 'enhanced_sentiment' in sources):
        # Enhanced sentiment analysis can work without Alpha Vantage key (uses other sources)
        # Lazy load to save memory
        def get_sentiment_data():
            scraper = get_enhanced_sentiment_scraper(alpha_vantage_key=alpha_key or "", delay=1)
            return scraper._scrape_data(ticker)
        scraper_tasks.append(("Enhanced Sentiment", get_sentiment_data))

    if ('all' in sources or 'alphavantage' in sources) and (alpha_key or os.environ.get("ALPHA_VANTAGE_API_KEY")):
        scraper_tasks.append(("Alpha Vantage", lambda: AlphaVantageAPIScraper(api_key=alpha_key, delay=1).get_data(ticker)))
    
    if ('all' in sources or 'finhub' in sources) and (finhub_key or os.environ.get("FINHUB_API_KEY")):
        scraper_tasks.append(("Finhub", lambda: FinhubAPIScraper(api_key=finhub_key, delay=1).get_data(ticker)))
    
    if ('all' in sources or 'technical' in sources) and (alpha_key or os.environ.get("ALPHA_VANTAGE_API_KEY")):
        def get_technical_data():
            tech_indicators = TechnicalIndicators(api_key=alpha_key, config=webapp_config)
            indicator_data = tech_indicators.get_all_indicators(ticker)
            if "error" not in indicator_data:
                # Format the indicator data with source labels
                formatted_indicators = {}
                for key, value in indicator_data.items():
                    if key not in ["Ticker", "Last Updated"]:
                        formatted_indicators[f"{key} (Technical)"] = value
                    else:
                        formatted_indicators[key] = value
                return formatted_indicators
            return {}
        
        scraper_tasks.append(("Technical Indicators", get_technical_data))
    
    # Run scrapers concurrently with limited workers to avoid overwhelming APIs
    max_workers = min(4, len(scraper_tasks))  # Limit to 4 concurrent scrapers
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(run_scraper, name, func) for name, func in scraper_tasks]
            
            # Wait for all to complete with timeout (90 seconds per ticker for cloud hosting)
            concurrent.futures.wait(futures, timeout=90)
        
        # Small delay to be respectful to APIs
        time.sleep(0.2)
        
    except Exception as e:
        logger.error(f"Error in concurrent scraping for {ticker}: {str(e)}")
    
    return results

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/fundamental-analysis', methods=['POST'])
def fundamental_analysis():
    """
    API endpoint for fundamental analysis of a stock
    
    Expected JSON payload:
    {
        "ticker": "AAPL",
        "data": {
            "P/E Ratio": 28.5,
            "P/B Ratio": 5.2,
            "P/S Ratio": 7.8,
            "ROE": 25.3,
            "ROA": 12.1,
            "Operating Margin": 30.2,
            "EPS": 6.15,
            "EBITDA": 125000000000,
            "Free Cash Flow": 95000000000,
            "Operating Cash Flow": 110000000000
        }
    }
    
    Returns:
        JSON response with investment analysis
    """
    try:
        payload = request.get_json()
        
        if not payload:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        ticker = payload.get('ticker')
        stock_data = payload.get('data', {})
        
        if not ticker:
            return jsonify({
                'success': False,
                'error': 'Ticker symbol is required'
            }), 400
        
        if not stock_data:
            return jsonify({
                'success': False,
                'error': 'Stock data is required'
            }), 400
        
        logger.info(f"Performing fundamental analysis for {ticker}")
        
        # Lazy load analytics module
        analytics = get_financial_analytics()
        
        # Perform fundamental analysis
        analysis = analytics.fundamental_analysis(stock_data, ticker)
        
        if 'error' in analysis:
            return jsonify({
                'success': False,
                'error': analysis['error']
            }), 500
        
        gc.collect()
        return jsonify({
            'success': True,
            'analysis': analysis,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        logger.error(f"Error in fundamental_analysis endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scrape', methods=['POST'])
def scrape_data():
    """
    API endpoint to scrape stock data
    
    Expected JSON payload:
    {
        "tickers": ["AAPL", "MSFT"],
        "sources": ["all"],
        "alpha_key": "optional",
        "finhub_key": "optional",
        "portfolio_allocation": {"AAPL": 0.6, "MSFT": 0.4}  // optional
    }
    
    Returns:
        JSON response with scraped data
    """
    try:
        data = request.get_json()
        
        if not data or 'tickers' not in data:
            return jsonify({
                'success': False,
                'error': 'No tickers provided'
            }), 400
        
        tickers = data.get('tickers', [])
        sources = data.get('sources', ['all'])
        alpha_key = data.get('alpha_key') or os.environ.get("ALPHA_VANTAGE_API_KEY")
        finhub_key = data.get('finhub_key') or os.environ.get("FINHUB_API_KEY")
        portfolio_allocation = data.get('portfolio_allocation')  # Get custom allocation from UI
        
        # Validate tickers
        if not isinstance(tickers, list) or len(tickers) == 0:
            return jsonify({
                'success': False,
                'error': 'Invalid tickers format'
            }), 400
        
        # Get CNN Fear & Greed Index
        logger.info("Scraping CNN Fear & Greed Index data...")
        cnn_scraper = CNNFearGreedScraper()
        cnn_data = cnn_scraper.scrape_data()
        
        # Scrape data for each ticker with parallel processing for multiple tickers
        all_data = {}
        
        if len(tickers) == 1:
            # Single ticker - process directly
            ticker = tickers[0].strip().upper()
            logger.info(f"Processing ticker: {ticker}")
            ticker_data = run_scrapers_for_ticker(ticker, sources, alpha_key, finhub_key)
            all_data[ticker] = ticker_data
        else:
            # Multiple tickers - process in parallel
            logger.info(f"Processing {len(tickers)} tickers in parallel...")
            
            def process_ticker(ticker):
                ticker = ticker.strip().upper()
                logger.info(f"Processing ticker: {ticker}")
                return ticker, run_scrapers_for_ticker(ticker, sources, alpha_key, finhub_key)
            
            # Use up to 6 parallel workers for multiple tickers
            # Scale workers based on portfolio size using sqrt for better scaling
            import math
            max_ticker_workers = min(4, max(2, int(math.sqrt(len(tickers)) * 1.5)))
            logger.info(f"Using {max_ticker_workers} parallel workers for {len(tickers)} tickers")
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_ticker_workers) as executor:
                futures = [executor.submit(process_ticker, ticker) for ticker in tickers]
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        ticker, ticker_data = future.result(timeout=90)  # 90 second timeout per ticker
                        all_data[ticker] = ticker_data
                        logger.info(f"Successfully processed ticker: {ticker}")
                    except concurrent.futures.TimeoutError:
                        logger.error(f"Timeout processing ticker")
                    except Exception as e:
                        logger.error(f"Error processing ticker: {str(e)}")
        
        logger.info(f"Total tickers processed: {len(all_data)}, Tickers: {list(all_data.keys())}")
        
        # Filter out tickers with errors or no valid data for DISPLAY purposes
        # Check for substantial data (at least 5 fields excluding Ticker and Timestamp)
        valid_tickers = [
            t for t, d in all_data.items() 
            if d and isinstance(d, dict) and 'error' not in d and 
            len([k for k in d.keys() if k not in ['Ticker', 'Data Timestamp', 'error']]) >= 5
        ]
        logger.info(f"Valid tickers with data: {len(valid_tickers)} out of {len(all_data)}")
        
        # Log which tickers were excluded
        excluded_tickers = set(all_data.keys()) - set(valid_tickers)
        if excluded_tickers:
            logger.warning(f"Excluded tickers (insufficient data): {excluded_tickers}")
        
        # For ANALYTICS, use original ticker list (not just ones with scraper data)
        # Analytics like Monte Carlo only need price data, which yfinance fetches independently
        analytics_tickers = [t.strip().upper() for t in tickers]
        logger.info(f"Will run analytics for {len(analytics_tickers)} tickers: {analytics_tickers}")
        
        # Compute analytics for the portfolio
        analytics_data = {}
        # Skip heavy analytics for very large portfolios (>50 tickers) unless explicitly requested
        skip_analytics = len(analytics_tickers) > 50
        
        if len(analytics_tickers) >= 1 and not skip_analytics:
            try:
                logger.info("Computing advanced financial analytics...")
                
                # Create a modified config with custom allocation if provided
                analytics_config = copy.deepcopy(config) if config else {}
                if portfolio_allocation:
                    logger.info(f"Using custom portfolio allocation from UI: {portfolio_allocation}")
                    if 'portfolio' not in analytics_config:
                        analytics_config['portfolio'] = {}
                    analytics_config['portfolio']['allocations'] = portfolio_allocation
                
                # Lazy load analytics to save memory
                analytics = get_financial_analytics(config=analytics_config)
                tickers_list = analytics_tickers  # Use all input tickers for analytics (yfinance fetches data independently)
                
                # Correlation Analysis (requires 2+ tickers)
                if len(tickers_list) >= 2:
                    try:
                        logger.info(f"Computing correlation analysis for {len(tickers_list)} tickers...")
                        correlation_result = analytics.correlation_analysis(tickers_list, days=252)
                        if correlation_result and 'error' not in correlation_result:
                            analytics_data['correlation'] = correlation_result
                            logger.info(f"✓ Correlation analysis completed successfully")
                        else:
                            logger.warning(f"Correlation analysis returned error: {correlation_result.get('error', 'Unknown error')}")
                    except Exception as e:
                        logger.warning(f"Correlation analysis failed: {str(e)}")
                
                # Individual ticker analytics
                for ticker in tickers_list:
                    ticker_analytics = {}
                    
                    # Fundamental Analysis - add to stock data for Stock Details tab
                    try:
                        if ticker in all_data and all_data[ticker]:
                            logger.info(f"Computing fundamental analysis for {ticker}...")
                            fundamental_result = analytics.fundamental_analysis(all_data[ticker], ticker)
                            if fundamental_result and 'error' not in fundamental_result:
                                # Add to all_data for Stock Details tab display
                                all_data[ticker]['_fundamental_analysis'] = fundamental_result
                                logger.info(f"✓ Fundamental analysis completed for {ticker}")
                    except Exception as e:
                        logger.warning(f"Fundamental analysis failed for {ticker}: {str(e)}")
                    
                    try:
                        regression_result = analytics.linear_regression_analysis([ticker], benchmark='SPY', days=252)
                        if regression_result and 'error' not in regression_result:
                            ticker_analytics['regression'] = regression_result
                    except Exception as e:
                        logger.warning(f"Regression analysis failed for {ticker}: {str(e)}")
                    
                    try:
                        mc_result = analytics.monte_carlo_var_es([ticker], days=252, simulations=5000)
                        if mc_result and 'error' not in mc_result:
                            ticker_analytics['monte_carlo'] = mc_result
                    except Exception as e:
                        logger.warning(f"Monte Carlo analysis failed for {ticker}: {str(e)}")
                    
                    if ticker_analytics:
                        analytics_data[ticker] = ticker_analytics
                
                # Portfolio-level Monte Carlo with Stress Test (if 2+ tickers)
                if len(tickers_list) >= 2:
                    try:
                        logger.info(f"Running portfolio-level Monte Carlo for {len(tickers_list)} tickers...")
                        portfolio_mc_result = analytics.monte_carlo_var_es(tickers_list, days=252, simulations=5000)
                        if portfolio_mc_result and 'error' not in portfolio_mc_result:
                            analytics_data['portfolio_monte_carlo'] = portfolio_mc_result
                            logger.info(f"✓ Portfolio Monte Carlo completed (includes stress test)")
                        else:
                            logger.warning(f"Portfolio Monte Carlo returned error: {portfolio_mc_result.get('error', 'Unknown')}")
                    except Exception as e:
                        logger.warning(f"Portfolio Monte Carlo analysis failed: {str(e)}")
                
                # PCA Analysis (if 3+ tickers)
                if len(tickers_list) >= 3:
                    try:
                        pca_result = analytics.pca_analysis(tickers_list, days=252, n_components=min(3, len(tickers_list)))
                        if pca_result and 'error' not in pca_result:
                            analytics_data['pca'] = pca_result
                    except Exception as e:
                        logger.warning(f"PCA analysis failed: {str(e)}")
                
            except Exception as e:
                logger.error(f"Analytics computation error: {str(e)}")
        elif len(analytics_tickers) >= 1 and skip_analytics:
            logger.info(f"Skipping advanced analytics for large portfolio ({len(analytics_tickers)} tickers). Enable for smaller portfolios (≤50 tickers).")
            analytics_data['info'] = {
                'message': f'Advanced analytics skipped for large portfolio ({len(analytics_tickers)} tickers)',
                'recommendation': 'For detailed analytics, analyze portfolios with 50 or fewer tickers'
            }
        
        # Log what analytics were computed
        logger.info(f"Analytics computed: {list(analytics_data.keys())}")
        logger.info(f"Analytics data size: {len(str(analytics_data))} chars")
        
        # Convert numpy types to native Python types for JSON serialization
        all_data = convert_numpy_types(all_data)
        cnn_data = convert_numpy_types(cnn_data)
        analytics_data = convert_numpy_types(analytics_data)

        gc.collect()
        return jsonify({
            'success': True,
            'data': all_data,
            'cnn_data': cnn_data,
            'analytics_data': analytics_data,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    except Exception as e:
        logger.error(f"Error in scrape_data endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/send-email', methods=['POST'])
def send_email_report():
    """
    API endpoint to send email report
    
    Expected JSON payload:
    {
        "tickers": ["AAPL", "MSFT"],
        "data": {...},
        "cnn_data": {...},
        "email": "user@example.com",
        "cc": "optional@example.com",
        "bcc": "optional@example.com"
    }
    
    Returns:
        JSON response with success status
    """
    try:
        payload = request.get_json()
        
        if not payload:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        tickers = payload.get('tickers', [])
        all_data = payload.get('data', {})
        cnn_data = payload.get('cnn_data', {})
        analytics_data = payload.get('analytics_data', {})
        recipients = payload.get('email')
        cc = payload.get('cc')
        bcc = payload.get('bcc')
        
        if not recipients:
            return jsonify({
                'success': False,
                'error': 'No recipient email provided'
            }), 400
        
        # Create temporary report files
        report_paths = {}
        temp_files = []
        
        for ticker, data in all_data.items():
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_files.append(temp_file.name)
            
            # Write report content
            temp_file.write(f"Financial Report for {ticker}\n")
            temp_file.write("=" * 80 + "\n")
            temp_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for key, value in data.items():
                if key not in ['error']:
                    temp_file.write(f"{key}: {value}\n")
            
            temp_file.close()
            report_paths[ticker] = temp_file.name
        
        # Send consolidated email
        success = send_consolidated_report(
            tickers=tickers,
            report_paths=report_paths,
            all_data=all_data,
            cnnMetricData=cnn_data,
            recipients=recipients,
            cc=cc,
            bcc=bcc,
            analytics_data=analytics_data
        )
        
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Email sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send email. Please check email configuration.'
            }), 500
    
    except Exception as e:
        logger.error(f"Error in send_email_report endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/option_pricing', methods=['POST'])
def option_pricing():
    """
    Calculate option price using multiple models
    
    Expected JSON payload:
    {
        "spot": 100,
        "strike": 105,
        "maturity": 0.25,
        "risk_free_rate": 0.05,
        "volatility": 0.20,
        "option_type": "call",
        "models": ["black_scholes", "binomial", "trinomial"],
        "steps": 100
    }
    """
    try:
        from src.derivatives.options_pricer import OptionsPricer
        
        data = request.json
        
        # Validate required fields
        required_fields = ['spot', 'strike', 'maturity', 'risk_free_rate', 'volatility']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Extract parameters
        S = float(data['spot'])
        K = float(data['strike'])
        T = float(data['maturity'])
        r = float(data['risk_free_rate'])
        sigma = float(data['volatility'])
        option_type = data.get('option_type', 'call').lower()
        models = data.get('models', ['black_scholes'])
        steps = int(data.get('steps', 100))
        exercise_type = data.get('exercise_type', 'european').lower()
        
        pricer = OptionsPricer()
        results = {}
        
        # Calculate prices for requested models
        if 'black_scholes' in models:
            bs_result = pricer.black_scholes(S, K, T, r, sigma, option_type)
            results['black_scholes'] = bs_result
        
        if 'binomial' in models:
            binomial_result = pricer.binomial_tree(
                S, K, T, r, sigma, steps, option_type, exercise_type
            )
            results['binomial'] = binomial_result
        
        if 'trinomial' in models:
            trinomial_result = pricer.trinomial_tree(
                S, K, T, r, sigma, steps, option_type, exercise_type
            )
            results['trinomial'] = trinomial_result
        
        # Convert numpy types for JSON serialization
        results = convert_numpy_types(results)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in option pricing: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/implied_volatility', methods=['POST'])
def calculate_implied_volatility():
    """
    Calculate implied volatility from market price
    
    Expected JSON payload:
    {
        "market_price": 5.50,
        "spot": 100,
        "strike": 105,
        "maturity": 0.25,
        "risk_free_rate": 0.05,
        "option_type": "call",
        "sigma_init": 0.3,
        "tolerance": 0.0001
    }
    """
    try:
        from src.derivatives.implied_volatility import ImpliedVolatilityCalculator
        
        data = request.json
        
        # Validate required fields
        required_fields = ['market_price', 'spot', 'strike', 'maturity', 'risk_free_rate']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Extract parameters
        market_price = float(data['market_price'])
        S = float(data['spot'])
        K = float(data['strike'])
        T = float(data['maturity'])
        r = float(data['risk_free_rate'])
        option_type = data.get('option_type', 'call').lower()
        sigma_init = float(data.get('sigma_init', 0.3))
        tol = float(data.get('tolerance', 0.0001))
        
        calculator = ImpliedVolatilityCalculator()
        result = calculator.calculate_implied_volatility(
            market_price, S, K, T, r, option_type, sigma_init, tol
        )
        
        # Validate the result
        if result['converged']:
            validation = calculator.validate_implied_volatility(
                result['implied_volatility'], market_price, S, K, T, r, option_type
            )
            result['validation'] = validation
        
        # Convert numpy types for JSON serialization
        result = convert_numpy_types(result)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error calculating implied volatility: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/greeks', methods=['POST'])
def calculate_greeks():
    """
    Calculate option Greeks
    
    Expected JSON payload:
    {
        "spot": 100,
        "strike": 105,
        "maturity": 0.25,
        "risk_free_rate": 0.05,
        "volatility": 0.20,
        "option_type": "call"
    }
    """
    try:
        from src.derivatives.options_pricer import OptionsPricer
        
        data = request.json
        
        # Validate required fields
        required_fields = ['spot', 'strike', 'maturity', 'risk_free_rate', 'volatility']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Extract parameters
        S = float(data['spot'])
        K = float(data['strike'])
        T = float(data['maturity'])
        r = float(data['risk_free_rate'])
        sigma = float(data['volatility'])
        option_type = data.get('option_type', 'call').lower()
        
        pricer = OptionsPricer()
        greeks = pricer.calculate_all_greeks(S, K, T, r, sigma, option_type)
        
        # Convert numpy types for JSON serialization
        greeks = convert_numpy_types(greeks)
        
        return jsonify({
            'success': True,
            'greeks': greeks
        })
        
    except Exception as e:
        logger.error(f"Error calculating Greeks: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/model_comparison', methods=['POST'])
def model_comparison():
    """
    Compare option prices across different models
    
    Expected JSON payload:
    {
        "spot": 100,
        "strike": 105,
        "maturity": 0.25,
        "risk_free_rate": 0.05,
        "volatility": 0.20,
        "option_type": "call",
        "steps": 100
    }
    """
    try:
        from src.derivatives.options_pricer import OptionsPricer
        
        data = request.json
        
        # Validate required fields
        required_fields = ['spot', 'strike', 'maturity', 'risk_free_rate', 'volatility']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Extract parameters
        S = float(data['spot'])
        K = float(data['strike'])
        T = float(data['maturity'])
        r = float(data['risk_free_rate'])
        sigma = float(data['volatility'])
        option_type = data.get('option_type', 'call').lower()
        steps = int(data.get('steps', 100))
        
        pricer = OptionsPricer()
        comparison = pricer.compare_models(S, K, T, r, sigma, option_type, steps)
        
        # Convert numpy types for JSON serialization
        comparison = convert_numpy_types(comparison)
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
        
    except Exception as e:
        logger.error(f"Error comparing models: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/convergence_analysis', methods=['POST'])
def convergence_analysis():
    """
    Analyze trinomial model convergence
    
    Expected JSON payload:
    {
        "spot": 100,
        "strike": 105,
        "maturity": 0.25,
        "risk_free_rate": 0.05,
        "volatility": 0.20,
        "option_type": "call",
        "min_steps": 10,
        "max_steps": 500,
        "step_increment": 50
    }
    """
    try:
        from src.derivatives.trinomial_model import TrinomialModel
        
        data = request.json
        
        # Validate required fields
        required_fields = ['spot', 'strike', 'maturity', 'risk_free_rate', 'volatility']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Extract parameters
        S = float(data['spot'])
        K = float(data['strike'])
        T = float(data['maturity'])
        r = float(data['risk_free_rate'])
        sigma = float(data['volatility'])
        option_type = data.get('option_type', 'call').lower()
        min_steps = int(data.get('min_steps', 10))
        max_steps = int(data.get('max_steps', 500))
        step_increment = int(data.get('step_increment', 50))
        
        # Create step range
        step_range = list(range(min_steps, max_steps + 1, step_increment))
        
        model = TrinomialModel(S, r, sigma, T)
        convergence_data = model.analyze_convergence(K, step_range, option_type)
        
        # Convert numpy types for JSON serialization
        convergence_data = convert_numpy_types(convergence_data)
        
        return jsonify({
            'success': True,
            'convergence_data': convergence_data
        })
        
    except Exception as e:
        logger.error(f"Error in convergence analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/volatility_surface', methods=['POST'])
def volatility_surface():
    """
    Build implied volatility surface from real market data
    
    Expected JSON payload:
    {
        "ticker": "AAPL",
        "option_type": "call",
        "risk_free_rate": 0.05,
        "min_volume": 10,
        "max_spread_pct": 0.20
    }
    """
    try:
        from src.derivatives.volatility_surface import VolatilitySurfaceBuilder
        
        data = request.json
        
        # Validate required fields
        if 'ticker' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: ticker'
            }), 400
        
        # Extract parameters
        ticker = data['ticker'].upper()
        option_type = data.get('option_type', 'call').lower()
        risk_free_rate = float(data.get('risk_free_rate', 0.05))
        min_volume = int(data.get('min_volume', 10))
        max_spread_pct = float(data.get('max_spread_pct', 0.20))
        
        builder = VolatilitySurfaceBuilder()
        
        # Build the surface
        surface_data = builder.build_surface(
            ticker=ticker,
            risk_free_rate=risk_free_rate,
            option_type=option_type,
            min_volume=min_volume,
            max_spread_pct=max_spread_pct
        )
        
        # Convert numpy types for JSON serialization
        surface_data = convert_numpy_types(surface_data)
        
        return jsonify({
            'success': True,
            'surface': surface_data
        })
        
    except Exception as e:
        logger.error(f"Error building volatility surface: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/atm_term_structure', methods=['POST'])
def atm_term_structure():
    """
    Get ATM volatility term structure
    
    Expected JSON payload:
    {
        "ticker": "AAPL",
        "option_type": "call",
        "risk_free_rate": 0.05
    }
    """
    try:
        from src.derivatives.volatility_surface import VolatilitySurfaceBuilder
        
        data = request.json
        
        # Validate required fields
        if 'ticker' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: ticker'
            }), 400
        
        # Extract parameters
        ticker = data['ticker'].upper()
        option_type = data.get('option_type', 'call').lower()
        risk_free_rate = float(data.get('risk_free_rate', 0.05))
        
        builder = VolatilitySurfaceBuilder()
        
        # Get ATM term structure
        term_structure = builder.get_atm_volatility_term_structure(
            ticker=ticker,
            risk_free_rate=risk_free_rate,
            option_type=option_type
        )
        
        # Convert numpy types for JSON serialization
        term_structure = convert_numpy_types(term_structure)
        
        return jsonify({
            'success': True,
            'term_structure': term_structure
        })
        
    except Exception as e:
        logger.error(f"Error extracting ATM term structure: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/heston_price', methods=['POST'])
def heston_price_endpoint():
    """
    Price a European option under Heston (1993) stochastic volatility model.

    Expected JSON payload:
    {
        "spot": 100, "strike": 105, "maturity": 0.25, "risk_free_rate": 0.05,
        "v0": 0.04, "kappa": 2.0, "theta": 0.04, "sigma_v": 0.3, "rho": -0.7,
        "option_type": "call"
    }
    """
    try:
        from src.derivatives.fourier_pricer import heston_price

        data = request.json
        required = ['spot', 'strike', 'maturity', 'risk_free_rate',
                    'v0', 'kappa', 'theta', 'sigma_v', 'rho']
        for f in required:
            if f not in data:
                return jsonify({'success': False, 'error': f'Missing field: {f}'}), 400

        result = heston_price(
            S=float(data['spot']),
            K=float(data['strike']),
            T=float(data['maturity']),
            r=float(data['risk_free_rate']),
            v0=float(data['v0']),
            kappa=float(data['kappa']),
            theta=float(data['theta']),
            sigma_v=float(data['sigma_v']),
            rho=float(data['rho']),
            option_type=data.get('option_type', 'call')
        )

        # Black-Scholes comparison
        from src.derivatives.options_pricer import OptionsPricer
        pricer = OptionsPricer()
        sigma = np.sqrt(float(data.get('v0', 0.04)))
        bs = pricer.black_scholes(
            float(data['spot']), float(data['strike']),
            float(data['maturity']), float(data['risk_free_rate']),
            sigma,
            data.get('option_type', 'call')
        )
        bs = convert_numpy_types(bs)

        result = convert_numpy_types(result)
        return jsonify({
            'success': True,
            'heston': result,
            'black_scholes_comparison': {'price': bs['price']},
            'price_difference': abs(result['price'] - bs['price'])
        })

    except Exception as e:
        logger.error(f"Error in Heston pricing: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/heston_iv_surface', methods=['POST'])
def heston_iv_surface_endpoint():
    """
    Compute Heston implied volatility surface across a grid of strikes and maturities.

    Expected JSON payload:
    {
        "S": 100, "r": 0.05, "v0": 0.04, "kappa": 2.0, "theta": 0.04,
        "sigma_v": 0.3, "rho": -0.7, "option_type": "call",
        "K_min": 80, "K_max": 120, "K_steps": 10,
        "T_min": 0.1, "T_max": 2.0, "T_steps": 8
    }
    Returns:
    {
        "success": true, "strikes": [...], "maturities": [...], "iv_grid": [[...], ...]
    }
    """
    try:
        from src.derivatives.fourier_pricer import heston_price
        from src.derivatives.options_pricer import black_scholes as bs_func
        from scipy.optimize import brentq

        data = request.json or {}

        S = float(data.get('S', 100))
        r = float(data.get('r', 0.05))
        v0 = float(data.get('v0', 0.04))
        kappa = float(data.get('kappa', 2.0))
        theta = float(data.get('theta', 0.04))
        sigma_v = float(data.get('sigma_v', 0.3))
        rho = float(data.get('rho', -0.7))
        option_type = data.get('option_type', 'call')
        K_min = float(data.get('K_min', 80))
        K_max = float(data.get('K_max', 120))
        K_steps = int(data.get('K_steps', 10))
        T_min = float(data.get('T_min', 0.1))
        T_max = float(data.get('T_max', 2.0))
        T_steps = int(data.get('T_steps', 8))

        strikes = np.linspace(K_min, K_max, K_steps).tolist()
        maturities = np.linspace(T_min, T_max, T_steps).tolist()

        iv_grid = []
        for T in maturities:
            row = []
            for K in strikes:
                try:
                    heston_result = heston_price(
                        S=S, K=K, T=T, r=r,
                        v0=v0, kappa=kappa, theta=theta,
                        sigma_v=sigma_v, rho=rho,
                        option_type=option_type
                    )
                    hp = float(heston_result['price'])

                    def bs_diff(sigma):
                        return bs_func(S, K, T, r, sigma, option_type)['price'] - hp

                    try:
                        iv = brentq(bs_diff, 0.001, 2.0, xtol=1e-6, maxiter=100)
                        iv = max(0.001, min(2.0, iv))
                    except Exception:
                        iv = 0.001
                except Exception:
                    iv = 0.001
                row.append(iv)
            iv_grid.append(row)

        return jsonify({
            'success': True,
            'strikes': strikes,
            'maturities': maturities,
            'iv_grid': iv_grid
        })

    except Exception as e:
        logger.error(f"Error in Heston IV surface: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/merton_price', methods=['POST'])
def merton_price_endpoint():
    """
    Price a European option under Merton (1976) jump-diffusion.

    Expected JSON payload:
    {
        "spot": 100, "strike": 105, "maturity": 0.25, "risk_free_rate": 0.05,
        "sigma": 0.2, "lambda": 2.0, "mu_j": -0.05, "delta_j": 0.10,
        "option_type": "call"
    }
    """
    try:
        from src.derivatives.fourier_pricer import merton_price

        data = request.json
        required = ['spot', 'strike', 'maturity', 'risk_free_rate',
                    'sigma', 'lambda', 'mu_j', 'delta_j']
        for f in required:
            if f not in data:
                return jsonify({'success': False, 'error': f'Missing field: {f}'}), 400

        result = merton_price(
            S=float(data['spot']),
            K=float(data['strike']),
            T=float(data['maturity']),
            r=float(data['risk_free_rate']),
            sigma=float(data['sigma']),
            lam=float(data['lambda']),
            mu_j=float(data['mu_j']),
            delta_j=float(data['delta_j']),
            option_type=data.get('option_type', 'call')
        )

        result = convert_numpy_types(result)
        return jsonify({'success': True, 'result': result})

    except Exception as e:
        logger.error(f"Error in Merton pricing: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/regime_detection', methods=['POST'])
def regime_detection_endpoint():
    """
    Detect market regime using 2-state HMM (Hamilton filter).

    Supports two calling conventions:
    1. New (ticker + date range):
       {"ticker": "SPY", "start_date": "2020-01-01", "end_date": "2021-12-31"}
    2. Legacy (tickers list + days):
       {"tickers": ["SPY", "AAPL"], "days": 1260}

    Always returns top-level fields:
      filtered_probs  — list of P(stressed) per trading day
      signal          — RISK_ON / RISK_OFF / NEUTRAL
      transition_matrix, parameters, current_probabilities
      dates           — ISO date strings aligned with filtered_probs
      prices          — closing prices aligned with filtered_probs
      regime_sequence — list of 0/1 per day (1 = stressed)
    """
    try:
        import yfinance as yf
        from src.analytics.regime_detection import RegimeDetector

        data = request.json or {}

        # --- Determine ticker and fetch price data ---
        import pandas as pd
        import numpy as np

        if 'ticker' in data or 'start_date' in data or 'end_date' in data:
            # New API: ticker + date range
            ticker = str(data.get('ticker', 'SPY')).upper()
            start_date = data.get('start_date', '2019-01-01')
            end_date = data.get('end_date', datetime.now().strftime('%Y-%m-%d'))

            # Use Ticker.history() (instance-isolated) to avoid shared-session
            # contamination when concurrent regime detection requests run in parallel.
            hist = yf.Ticker(ticker).history(start=start_date, end=end_date,
                                             auto_adjust=True)
            if hist.empty:
                return jsonify({'success': False, 'error': f'No data for {ticker}'}), 400

            closes: pd.Series = hist['Close'].dropna()

            # Align index (dates correspond to returns, which are 1 shorter)
            price_dates = pd.DatetimeIndex(closes.index).tz_localize(None).strftime('%Y-%m-%d').tolist()
            price_values = closes.tolist()

            log_ret = np.asarray(np.log(closes / closes.shift(1)).dropna())
            # dates/prices aligned to returns (drop first row)
            ret_dates = price_dates[1:]
            ret_prices = price_values[1:]

        else:
            # Legacy API: tickers list + days
            tickers = data.get('tickers', ['SPY'])
            ticker = tickers[0] if tickers else 'SPY'
            days = int(data.get('days', 1260))

            from datetime import timedelta
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=int(days * 1.5))

            # Use Ticker.history() (instance-isolated) to avoid shared-session contamination
            hist = yf.Ticker(ticker).history(start=start_dt.strftime('%Y-%m-%d'),
                                             end=end_dt.strftime('%Y-%m-%d'),
                                             auto_adjust=True)
            if hist.empty:
                return jsonify({'success': False, 'error': f'No data for {ticker}'}), 400

            closes: pd.Series = hist['Close'].dropna()

            price_dates = pd.DatetimeIndex(closes.index).tz_localize(None).strftime('%Y-%m-%d').tolist()
            price_values = closes.tolist()

            log_ret = np.asarray(np.log(closes / closes.shift(1)).dropna())
            ret_dates = price_dates[1:]
            ret_prices = price_values[1:]

        # --- Fit HMM ---
        detector = RegimeDetector()
        result = detector.fit(log_ret, n_restarts=3)
        result['ticker_used'] = ticker

        # --- Determine stressed state index ---
        # filtered_probs_full is (T, 2); column order matches internal state indices
        full_probs = np.array(result.get('filtered_probs_full', []))
        if full_probs.ndim == 2 and full_probs.shape[1] == 2:
            # Use current_probabilities to identify which column is stressed
            # by comparing last row to reported current_probabilities
            current_probs = result.get('current_probabilities', {})
            stressed_prob_value = current_probs.get('stressed', None)
            if stressed_prob_value is not None:
                last_row = full_probs[-1]
                # The stressed column is whichever col is closer to stressed_prob_value
                if abs(last_row[0] - stressed_prob_value) < abs(last_row[1] - stressed_prob_value):
                    stressed_col = 0
                else:
                    stressed_col = 1
            else:
                stressed_col = 1  # fallback

            filtered_probs_stressed: list = full_probs[:, stressed_col].tolist()
        else:
            filtered_probs_stressed: list = []

        # regime_sequence: 1 if P(stressed) >= 0.5, else 0
        regime_sequence = [1 if p >= 0.5 else 0 for p in filtered_probs_stressed]

        # Truncate dates/prices to match number of returns if needed
        n = len(log_ret)
        ret_dates = ret_dates[:n]
        ret_prices = ret_prices[:n]

        # Build flat response compatible with new frontend
        response = {
            'success': True,
            # New flat fields for Plotly charts
            'dates': ret_dates,
            'prices': [float(p) for p in ret_prices],
            'filtered_probs': filtered_probs_stressed,
            'regime_sequence': regime_sequence,
            'signal': result.get('signal', 'NEUTRAL'),
            'signal_description': result.get('signal_description', ''),
            'current_probabilities': result.get('current_probabilities', {}),
            'transition_matrix': result.get('transition_matrix', {}),
            'parameters': result.get('parameters', {}),
            'log_likelihood': result.get('log_likelihood', None),
            'n_observations': result.get('n_observations', None),
            'label_confidence': result.get('label_confidence', None),
            # Legacy nested field for backward compatibility
            'regime': convert_numpy_types(result),
        }

        return jsonify(convert_numpy_types(response))

    except Exception as e:
        logger.error(f"Error in regime detection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/calibrate_heston', methods=['POST'])
def calibrate_heston_endpoint():
    """
    Calibrate Heston parameters to real market options data.

    Expected JSON payload:
    {
        "ticker": "AAPL",
        "risk_free_rate": 0.05,
        "option_type": "call"
    }
    """
    try:
        from src.derivatives.model_calibration import HestonCalibrator

        data = request.json or {}
        ticker = data.get('ticker', 'AAPL').upper()
        risk_free_rate = float(data.get('risk_free_rate', 0.05))
        option_type = data.get('option_type', 'call')

        calibrator = HestonCalibrator()
        result = calibrator.calibrate(ticker, risk_free_rate, option_type)
        result = convert_numpy_types(result)

        return jsonify({'success': True, 'calibration': result})

    except Exception as e:
        logger.error(f"Error in Heston calibration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/calibrate_heston_stream', methods=['GET'])
def calibrate_heston_stream():
    """
    SSE endpoint for Heston calibration with live progress events.

    Query params: ticker, risk_free_rate, option_type
    Emits: data: {"iteration": N, "error": float}\\n\\n per step,
           data: {"done": true}\\n\\n as terminal event.
    """
    from flask import Response, stream_with_context

    ticker = request.args.get('ticker', 'AAPL').upper()
    rate = float(request.args.get('risk_free_rate', 0.05))
    option_type = request.args.get('option_type', 'call')

    def generate():
        try:
            from src.derivatives.model_calibration import HestonCalibrator
            calibrator = HestonCalibrator()
            for event in calibrator.calibrate_stream(ticker, rate, option_type=option_type):
                yield event
        except Exception as e:
            import json
            import requests
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@app.route('/api/calibrate_merton', methods=['POST'])
def calibrate_merton_endpoint():
    """
    Calibrate Merton jump-diffusion parameters to real market options data.

    Expected JSON payload:
    {
        "ticker": "AAPL",
        "risk_free_rate": 0.05,
        "option_type": "call"
    }
    """
    try:
        from src.derivatives.model_calibration import MertonCalibrator

        data = request.json or {}
        ticker = data.get('ticker', 'AAPL').upper()
        risk_free_rate = float(data.get('risk_free_rate', 0.05))
        option_type = data.get('option_type', 'call')

        calibrator = MertonCalibrator()
        result = calibrator.calibrate(ticker, risk_free_rate, option_type)
        result = convert_numpy_types(result)

        return jsonify({'success': True, 'calibration': result})

    except Exception as e:
        logger.error(f"Error in Merton calibration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/calibrate_bcc', methods=['POST'])
def calibrate_bcc_endpoint():
    """
    Calibrate BCC (Bates-Chan-Chang) parameters to real market options data.

    Expected JSON payload:
    {
        "ticker": "AAPL",
        "risk_free_rate": 0.05,
        "option_type": "call"
    }

    Returns:
    {
        "success": true,
        "result": {
            "calibrated_params": {...heston params...},
            "jump_params": {"lambda_j": float, "mu_j": float, "sigma_j": float},
            "rmse": float,
            "spot": float
        }
    }
    """
    try:
        from src.derivatives.model_calibration import BCCCalibrator

        data = request.json or {}
        ticker         = data.get('ticker', 'AAPL').upper()
        risk_free_rate = float(data.get('risk_free_rate', 0.05))
        option_type    = data.get('option_type', 'call')

        calibrator = BCCCalibrator()
        result = calibrator.calibrate(ticker, risk_free_rate=risk_free_rate,
                                      option_type=option_type)

        # Propagate market data errors gracefully
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 500

        # Normalize jump parameters from calibrator's internal field names
        # BCCCalibrator returns 'jump': {'lam': ..., 'mu_j': ..., 'delta_j': ...}
        # Response convention: 'jump_params': {'lambda_j': ..., 'mu_j': ..., 'sigma_j': ...}
        jump_raw = result.get('calibrated_params', {}).get('jump', {})
        result['jump_params'] = {
            'lambda_j': jump_raw.get('lam', jump_raw.get('lambda_j')),
            'mu_j':     jump_raw.get('mu_j'),
            'sigma_j':  jump_raw.get('delta_j', jump_raw.get('sigma_j')),
        }

        result = convert_numpy_types(result)

        # Build flat params dict for frontend display
        heston_p = result.get('calibrated_params', {}).get('heston', {})
        jump_p   = result.get('calibrated_params', {}).get('jump', {})
        flat_params = {**heston_p, **{k: v for k, v in jump_p.items()}}

        return jsonify({
            'success': True,
            'rmse':       result.get('rmse', 0),
            'params':     flat_params,
            'result':     result,
            'strikes':    result.get('strikes', []),
            'market_ivs': result.get('market_ivs', []),
            'fitted_ivs': result.get('fitted_ivs', []),
        })

    except Exception as e:
        logger.error(f"Error in BCC calibration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/interest_rate_model', methods=['POST'])
def interest_rate_model_endpoint():
    """
    CIR / Vasicek interest rate model: bond pricing and yield curve.

    Expected JSON payload:
    {
        "model": "cir",            // "cir" (default) or "vasicek"
        "r0": 0.053,
        "kappa": 1.5,
        "theta": 0.05,
        "sigma": 0.1,
        "maturities": [0.25, 0.5, 1, 2, 5, 10, 30],
        "calibrate_to_treasuries": false
    }
    """
    try:
        from src.analytics.interest_rate_models import (
            CIRCalibrator, cir_yield_curve, calibrate_to_treasuries, vasicek_yield_curve
        )

        data = request.json or {}
        model = data.get('model', 'cir').lower()

        if data.get('calibrate_to_treasuries', False):
            r0 = float(data.get('r0', 0.053))
            result = calibrate_to_treasuries(r0=r0)
            # Add feller_ratio to calibrate_to_treasuries result
            kappa = result['calibrated_params']['kappa']
            theta_val = result['calibrated_params']['theta']
            sigma_val = result['calibrated_params']['sigma']
            result['feller_ratio'] = float((2 * kappa * theta_val) / (sigma_val ** 2))
        elif model == 'vasicek':
            r0    = float(data.get('r0', 0.053))
            kappa = float(data.get('kappa', 0.5))
            theta = float(data.get('theta', 0.06))
            sigma = float(data.get('sigma', 0.02))
            mats  = data.get('maturities', [0.25, 0.5, 1, 2, 5, 10, 30])
            curve = vasicek_yield_curve(r0, mats, kappa, theta, sigma)
            result = {
                'model': 'Vasicek (1977)',
                'params': {'r0': r0, 'kappa': kappa, 'theta': theta, 'sigma': sigma},
                'feller_condition_satisfied': True,
                'feller_ratio': None,
                'yield_curve': curve,
            }
        else:  # CIR (default)
            r0    = float(data.get('r0', 0.053))
            kappa = float(data.get('kappa', 1.5))
            theta = float(data.get('theta', 0.05))
            sigma = float(data.get('sigma', 0.1))
            mats  = data.get('maturities', [0.25, 0.5, 1, 2, 5, 10, 30])
            curve = cir_yield_curve(r0, mats, kappa, theta, sigma)
            feller = 2 * kappa * theta > sigma ** 2
            feller_ratio = float((2 * kappa * theta) / (sigma ** 2))
            result = {
                'model': 'CIR (1985)',
                'params': {'r0': r0, 'kappa': kappa, 'theta': theta, 'sigma': sigma},
                'feller_condition_satisfied': feller,
                'feller_ratio': feller_ratio,
                'yield_curve': curve,
            }

        result = convert_numpy_types(result)
        return jsonify({'success': True, 'result': result})

    except Exception as e:
        logger.error(f"Error in interest rate model: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/credit_risk', methods=['POST'])
def credit_risk_endpoint():
    """
    Credit risk analysis using Markov chain credit transitions.

    Expected JSON payload:
    {
        "rating": "BBB",
        "horizon": 5,
        "recovery_rate": 0.40,
        "face_value": 1000,
        "coupon_rate": 0.05
    }
    """
    try:
        from src.analytics.credit_transitions import credit_risk_analysis

        data = request.json or {}
        rating        = data.get('rating', 'BBB').upper()
        horizon       = int(data.get('horizon', 5))
        recovery_rate = float(data.get('recovery_rate', 0.40))
        face_value    = float(data.get('face_value', 1000.0))
        coupon_rate   = float(data.get('coupon_rate', 0.05))

        result = credit_risk_analysis(
            rating, horizon, recovery_rate, face_value, coupon_rate
        )
        result = convert_numpy_types(result)

        return jsonify({'success': True, 'result': result})

    except Exception as e:
        logger.error(f"Error in credit risk analysis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/markov_chain', methods=['POST'])
def markov_chain_endpoint():
    """
    Unified Markov chain endpoint. Dispatches on mode field.

    Expected JSON payload:
    {
        "mode": "steady_state" | "absorption" | "nstep" | "term_structure" | "mdp",
        "transition_matrix": [[...], ...],  // optional; defaults to S&P 8-rating matrix
        "n": 5,                             // for mode=nstep
        "current_rating": "BBB",           // for mode=nstep, term_structure
        "horizons": [1,3,5,10],            // for mode=term_structure (optional)
        "gamma": 0.95,                     // for mode=mdp
        "n_periods": 1000                  // for mode=mdp
    }
    """
    try:
        from src.analytics.markov_chains import (
            steady_state_distribution,
            absorption_probabilities,
            portfolio_mdp_value_iteration,
        )
        from src.analytics.credit_transitions import (
            n_year_transition,
            default_probability_term_structure,
            SP_TRANSITION_MATRIX,
            RATINGS,
        )
        import numpy as np

        data = request.json or {}
        mode = data.get('mode', 'steady_state')
        raw_matrix = data.get('transition_matrix')
        P = np.array(raw_matrix) if raw_matrix is not None else SP_TRANSITION_MATRIX.copy()

        if mode == 'steady_state':
            pi = steady_state_distribution(P)
            result = {'mode': mode, 'steady_state': pi.tolist(), 'ratings': RATINGS}

        elif mode == 'absorption':
            result = absorption_probabilities(P)
            result['mode'] = mode
            if 'error' in result:
                # Not an exception — just no absorbing states; return as success with error field
                pass

        elif mode == 'nstep':
            n = int(data.get('n', 5))
            Pn = n_year_transition(P, n)
            term = default_probability_term_structure(
                data.get('current_rating', 'BBB'), P=P
            )
            result = {
                'mode': mode,
                'n': n,
                'transition_matrix_n': Pn.tolist(),
                'term_structure': term,
                'ratings': RATINGS,
            }

        elif mode == 'term_structure':
            rating = data.get('current_rating', 'BBB').upper()
            horizons = data.get('horizons')
            term = default_probability_term_structure(rating, horizons=horizons, P=P)
            result = {
                'mode': mode,
                'current_rating': rating,
                'term_structure': term,
            }

        elif mode == 'mdp':
            gamma     = float(data.get('gamma', 0.95))
            n_periods = int(data.get('n_periods', 1000))
            result = portfolio_mdp_value_iteration(gamma=gamma, n_periods=n_periods)
            result['mode'] = mode

        else:
            return jsonify({'success': False, 'error': f"Unknown mode: {mode}"}), 400

        result = convert_numpy_types(result)
        return jsonify({'success': True, 'result': result})

    except Exception as e:
        logger.error(f"Error in markov_chain endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# M6: Reinforcement Learning Routes
# ---------------------------------------------------------------------------

def _get_rl_models():
    """Lazy-load RL models to avoid import-time cost."""
    from src.analytics.rl_models import (
        investment_mdp_policy_iteration,
        gridworld_policy_iteration,
        portfolio_rotation_policy_iteration,
        portfolio_rotation_qlearning,
    )
    return (
        investment_mdp_policy_iteration,
        gridworld_policy_iteration,
        portfolio_rotation_policy_iteration,
        portfolio_rotation_qlearning,
    )


@app.route('/api/rl_investment_mdp', methods=['POST'])
def rl_investment_mdp():
    """L1: Investment MDP policy iteration (Bull/Bear/Crash)."""
    try:
        body  = request.json or {}
        gamma = float(body.get('gamma', 0.95))
        fn    = _get_rl_models()[0]
        result = fn(gamma=gamma)
        return jsonify(convert_numpy_types(result))
    except Exception as e:
        logger.error(f"Error in rl_investment_mdp: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/rl_gridworld', methods=['POST'])
def rl_gridworld():
    """L2: 4×4 gridworld policy iteration (deterministic or windy)."""
    try:
        body     = request.json or {}
        use_wind = bool(body.get('use_wind', False))
        gamma    = float(body.get('gamma', 0.95))
        fn       = _get_rl_models()[1]
        result   = fn(use_wind=use_wind, gamma=gamma)
        return jsonify(convert_numpy_types(result))
    except Exception as e:
        logger.error(f"Error in rl_gridworld: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/rl_portfolio_rotation_pi', methods=['POST'])
def rl_portfolio_rotation_pi():
    """L3: Portfolio rotation via policy iteration on SPY/IEF/SHY MDP."""
    try:
        body   = request.json or {}
        fn     = _get_rl_models()[2]
        result = fn(
            train_end  = body.get('train_end',  '2016-12-31'),
            test_start = body.get('test_start', '2017-01-01'),
            gamma      = float(body.get('gamma',     0.99)),
            cost_bps   = int(body.get('cost_bps',   10)),
        )
        return jsonify(convert_numpy_types(result))
    except Exception as e:
        logger.error(f"Error in rl_portfolio_rotation_pi: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stoch_portfolio_mdp', methods=['POST'])
def stoch_portfolio_mdp():
    """Portfolio MDP policy iteration with user-specified tickers (Stochastic Models tab)."""
    try:
        from src.analytics.rl_models import portfolio_mdp_user_stocks
        body   = request.json or {}
        result = portfolio_mdp_user_stocks(
            equity_ticker = body.get('equity_ticker', 'SPY'),
            bond_ticker   = body.get('bond_ticker',   'IEF'),
            start_date    = body.get('start_date',    '2010-01-01'),
            train_end     = body.get('train_end',     '2020-12-31'),
            test_start    = body.get('test_start',    '2021-01-01'),
            gamma         = float(body.get('gamma',    0.99)),
            cost_bps      = int(body.get('cost_bps',  10)),
        )
        return jsonify(convert_numpy_types(result))
    except Exception as e:
        logger.error(f"Error in stoch_portfolio_mdp: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/rl_portfolio_rotation_ql', methods=['POST'])
def rl_portfolio_rotation_ql():
    """L4: Portfolio rotation via Q-learning (ε-greedy TD)."""
    try:
        body   = request.json or {}
        fn     = _get_rl_models()[3]
        result = fn(
            alpha     = float(body.get('alpha',     0.10)),
            epochs    = int(body.get('epochs',    200)),
            eps_start = float(body.get('eps_start', 0.15)),
            eps_end   = float(body.get('eps_end',   0.01)),
            optimistic = float(body.get('optimistic', 0.005)),
            gamma     = float(body.get('gamma',     0.99)),
            cost_bps  = int(body.get('cost_bps',   10)),
        )
        return jsonify(convert_numpy_types(result))
    except Exception as e:
        logger.error(f"Error in rl_portfolio_rotation_ql: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio_sharpe', methods=['POST'])
def portfolio_sharpe():
    """
    Compute annualized portfolio Sharpe ratio.
    Body: { "tickers": [...], "weights": {...}, "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }
    Returns: { "sharpe": float, "rf_rate": float, "period": "YYYY-MM-DD to YYYY-MM-DD" }
    """
    data = request.json or {}
    tickers = data.get('tickers', [])
    weights = data.get('weights', {})
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    try:
        import yfinance as yf
        import numpy as np
        import pandas as pd

        # Fetch risk-free rate (annualized %) — silent fallback to 0.0
        rf_rate = 0.0
        try:
            irx = yf.Ticker('^IRX').history(period='5d')
            if not irx.empty:
                rf_rate = float(irx['Close'].iloc[-1]) / 100.0  # ^IRX in % already
        except Exception:
            rf_rate = 0.0

        # Fetch price data
        prices = yf.download(tickers, start=start_date, end=end_date,
                             auto_adjust=True, progress=False)['Close']
        # Coerce single-ticker Series to DataFrame
        if isinstance(prices, pd.Series):
            prices = prices.to_frame(tickers[0])
        prices = prices.dropna()

        # Build weight vector — equal-weight fallback for missing tickers
        n = len(tickers)
        w = np.array([weights.get(t, 1.0 / n) for t in tickers])
        w = w / w.sum()  # normalize

        # Weighted daily log-returns
        daily_log = np.log(prices / prices.shift(1)).dropna()
        port_ret = (daily_log.values * w).sum(axis=1)

        ann_ret = port_ret.mean() * 252
        ann_vol = port_ret.std() * np.sqrt(252)
        sharpe = (ann_ret - rf_rate) / ann_vol if ann_vol > 0 else 0.0

        return jsonify({
            'sharpe': round(float(sharpe), 4),
            'rf_rate': round(float(rf_rate), 4),
            'period': f'{start_date} to {end_date}'
        })
    except Exception as e:
        logger.error(f"Error in portfolio_sharpe: {e}")
        return jsonify({'error': str(e)}), 500

SYSTEM_PROMPTS = {
    'quant': (
        "You are an expert MFE (Master of Financial Engineering) quantitative assistant "
        "named 'QuantAssistant'. Respond informatively but concisely, focusing on financial "
        "data and quantitative analysis principles."
    ),
    'financial': (
        "You are a sell-side financial analyst named 'FinancialAnalyst'. "
        "Your domain is company fundamentals: P/E ratios, revenue trends, EPS, earnings analysis, "
        "sector dynamics, and macro trends. Respond in concise bullet-point analyst style — "
        "key metrics first, brief context, one actionable insight. "
        "Avoid stochastic models, derivatives, and quant math — those are QuantAssistant's domain."
    ),
}


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Endpoint for Quantitative Assistant chatbot using Ollama model.
    """
    try:
        data = request.json or {}
        message = data.get("message", "").strip()

        if not message:
            return jsonify({"error": "Message is required."}), 400

        agent = data.get('agent', 'quant')
        page_context = data.get("context", "")
        history = data.get("history", [])
        system_prompt = SYSTEM_PROMPTS.get(agent, SYSTEM_PROMPTS['quant'])

        effective_system_prompt = system_prompt
        if page_context and isinstance(page_context, str) and page_context.strip():
            effective_system_prompt = system_prompt + "\n\n" + page_context.strip()

        history_messages = [
            {"role": ("assistant" if h.get("sender") == "bot" else "user"), "content": h.get("text", "")}
            for h in (history or [])[-10:]
            if h.get("text")
        ]

        # Check if we have a Groq API Key setup in the environment
        groq_api_key = os.environ.get('GROQ_API_KEY')
        
        if groq_api_key:
            # --- GROQ (CLOUD) IMPLEMENTATION ---
            URL = "https://api.groq.com/openai/v1/chat/completions"
            MODEL = os.environ.get('GROQ_MODEL', 'llama3-8b-8192')
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": effective_system_prompt},
                    *history_messages,
                    {"role": "user", "content": message}
                ]
            }

            response = requests.post(URL, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Groq/OpenAI response formatting
            result = response.json()
            reply = result.get("choices", [{}])[0].get("message", {}).get("content", "No response content found.")
            
        else:
            # --- OLLAMA (LOCAL) IMPLEMENTATION ---
            URL = os.environ.get('OLLAMA_API_URL', 'http://localhost:11434/api/chat')
            MODEL = os.environ.get('OLLAMA_MODEL', 'llama3')
            payload = {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": effective_system_prompt},
                    *history_messages,
                    {"role": "user", "content": message}
                ],
                "stream": False
            }
            
            response = requests.post(URL, json=payload, timeout=120)
            response.raise_for_status()
            
            # Ollama response formatting
            result = response.json()
            reply = result.get("message", {}).get("content", "No response content found.")
            
        return jsonify({"reply": reply})
        
    except requests.exceptions.RequestException as e:
        error_body = e.response.text if hasattr(e, 'response') and e.response is not None else str(e)
        logger.error(f"LLM connection error: {error_body}")
        return jsonify({"reply": f"Error communicating with LLM. Details: {str(e)}. Response: {error_body}"})
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500

_ticker_validation_cache = {}

_peer_cache = {}        # { sector: { "data": [...], "fetched_at": float, "peers": [...] } }
_ticker_sector_map = {}  # { ticker: sector } — avoids re-scraping to find sector


@app.route('/api/peers', methods=['GET'])
def get_peers():
    ticker = request.args.get('ticker', '').strip().upper()
    if not ticker:
        return jsonify({'error': 'ticker parameter required'})
    try:
        now = time.time()

        # Fast path: if we already know this ticker's sector and the cache is warm, skip scrape
        known_sector = _ticker_sector_map.get(ticker)
        if known_sector and known_sector in _peer_cache:
            entry = _peer_cache[known_sector]
            if now - entry['fetched_at'] < 1800:
                cached_peer_data = entry['data']
                cached_peers = entry['peers']
                sector = known_sector

                def percentile_rank(rows, field, target):
                    if target is None:
                        return 50
                    vals = sorted([r[field] for r in rows if r[field] is not None])
                    if len(vals) < 2:
                        return 50
                    if target not in vals:
                        return 50
                    idx = vals.index(target)
                    return round(100 * idx / (len(vals) - 1))

                ticker_row = next((r for r in cached_peer_data if r['ticker'] == ticker), None)
                if ticker_row:
                    percentiles = {
                        'pe':        {'value': ticker_row['pe'],        'rank': percentile_rank(cached_peer_data, 'pe',        ticker_row['pe'])},
                        'pb':        {'value': ticker_row['pb'],        'rank': percentile_rank(cached_peer_data, 'pb',        ticker_row['pb'])},
                        'roe':       {'value': ticker_row['roe'],       'rank': percentile_rank(cached_peer_data, 'roe',       ticker_row['roe'])},
                        'op_margin': {'value': ticker_row['op_margin'], 'rank': percentile_rank(cached_peer_data, 'op_margin', ticker_row['op_margin'])},
                    }
                    return jsonify({'sector': sector, 'peers': cached_peers, 'peer_data': cached_peer_data, 'percentiles': percentiles})

        scraper = FinvizScraper()
        raw = scraper.get_peer_data(ticker)
        sector = raw.get('sector', '')
        peer_data = raw.get('peer_data', [])

        if len(peer_data) < 2:
            return jsonify({'error': 'Peer data unavailable: fewer than 2 comparable companies'})

        # Store in sector-scoped cache and update ticker->sector map
        _peer_cache[sector] = {'data': peer_data, 'fetched_at': now, 'peers': raw.get('peers', [])}
        _ticker_sector_map[ticker] = sector

        # Nearest-rank percentile calculation
        def percentile_rank(rows, field, target):
            if target is None:
                return 50
            vals = sorted([r[field] for r in rows if r[field] is not None])
            if len(vals) < 2:
                return 50
            if target not in vals:
                return 50
            idx = vals.index(target)
            return round(100 * idx / (len(vals) - 1))

        ticker_row = next((r for r in peer_data if r['ticker'] == ticker), None)
        if not ticker_row:
            return jsonify({'error': 'Ticker not found in peer data'})

        percentiles = {
            'pe':        {'value': ticker_row['pe'],        'rank': percentile_rank(peer_data, 'pe',        ticker_row['pe'])},
            'pb':        {'value': ticker_row['pb'],        'rank': percentile_rank(peer_data, 'pb',        ticker_row['pb'])},
            'roe':       {'value': ticker_row['roe'],       'rank': percentile_rank(peer_data, 'roe',       ticker_row['roe'])},
            'op_margin': {'value': ticker_row['op_margin'], 'rank': percentile_rank(peer_data, 'op_margin', ticker_row['op_margin'])},
        }

        return jsonify({
            'sector': sector,
            'peers': raw.get('peers', []),
            'peer_data': peer_data,
            'percentiles': percentiles,
        })
    except Exception as e:
        logger.error(f"Error in get_peers for {ticker}: {e}")
        return jsonify({'error': f'Peer data unavailable: {str(e)}'})


@app.route('/api/trading_indicators', methods=['GET'])
def get_trading_indicators():
    ticker = request.args.get('ticker', '').strip().upper()
    lookback = int(request.args.get('lookback', 90))
    if not ticker:
        return jsonify({'error': 'ticker parameter required'})
    try:
        from src.analytics.trading_indicators import (
            fetch_ohlcv, compute_volume_profile, compute_anchored_vwap,
            compute_order_flow, compute_liquidity_sweep, compute_composite_bias
        )
        df = fetch_ohlcv(ticker, lookback)
        df_365 = fetch_ohlcv(ticker, 365)
        results = {
            'volume_profile':  compute_volume_profile(df, ticker, lookback),
            'anchored_vwap':   compute_anchored_vwap(df_365, ticker, lookback),
            'order_flow':      compute_order_flow(df, ticker, lookback),
            'liquidity_sweep': compute_liquidity_sweep(df, lookback),
        }
        results['composite_bias'] = compute_composite_bias(results)
        return jsonify({'ticker': ticker, 'lookback': lookback, **results})
    except Exception as e:
        logger.error(f"Error in get_trading_indicators for {ticker}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/footprint', methods=['GET'])
def get_footprint():
    ticker = request.args.get('ticker', '').strip().upper()
    days = min(int(request.args.get('days', 60)), 60)
    if not ticker:
        return jsonify({'error': 'ticker parameter required'})
    try:
        from src.analytics.trading_indicators import fetch_intraday, compute_footprint
        df_15m = fetch_intraday(ticker, days)
        result = compute_footprint(df_15m, ticker)
        return jsonify({'ticker': ticker, 'days': days, **result})
    except Exception as e:
        logger.error(f"Error in get_footprint for {ticker}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate_ticker', methods=['GET'])
def validate_ticker():
    symbol = request.args.get('symbol', '').strip().upper()
    if not symbol:
        return jsonify({'valid': False, 'name': ''})
    if symbol in _ticker_validation_cache:
        return jsonify(_ticker_validation_cache[symbol])
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        fi = t.fast_info
        name = getattr(fi, 'display_name', None) or getattr(fi, 'company_name', None)
        if not name:
            info = t.info
            name = info.get('longName') or info.get('shortName') or ''
        result = {'valid': bool(name), 'name': name or symbol}
    except Exception:
        result = {'valid': False, 'name': ''}
    _ticker_validation_cache[symbol] = result
    return jsonify(result)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5173))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
