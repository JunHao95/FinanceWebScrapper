#!/usr/bin/env python3
"""
Flask Web Application for Stock Financial Metrics Scraper
"""
import os
import sys
import json
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
            max_ticker_workers = min(6, max(3, int(math.sqrt(len(tickers)) * 1.5)))
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
        
        # Filter out tickers with errors or no valid data
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
        
        # Compute analytics for the portfolio
        analytics_data = {}
        # Skip heavy analytics for very large portfolios (>50 tickers) unless explicitly requested
        skip_analytics = len(valid_tickers) > 50
        
        if len(valid_tickers) >= 1 and not skip_analytics:
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
                tickers_list = valid_tickers  # Use only valid tickers for analytics
                
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
        elif len(valid_tickers) >= 1 and skip_analytics:
            logger.info(f"Skipping advanced analytics for large portfolio ({len(valid_tickers)} tickers). Enable for smaller portfolios (≤50 tickers).")
            analytics_data['info'] = {
                'message': f'Advanced analytics skipped for large portfolio ({len(valid_tickers)} tickers)',
                'recommendation': 'For detailed analytics, analyze portfolios with 50 or fewer tickers'
            }
        
        # Log what analytics were computed
        logger.info(f"Analytics computed: {list(analytics_data.keys())}")
        logger.info(f"Analytics data size: {len(str(analytics_data))} chars")
        
        # Convert numpy types to native Python types for JSON serialization
        all_data = convert_numpy_types(all_data)
        cnn_data = convert_numpy_types(cnn_data)
        analytics_data = convert_numpy_types(analytics_data)
        
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
