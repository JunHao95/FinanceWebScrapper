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

from src.scrapers.yahoo_scraper import YahooFinanceScraper
from src.scrapers.finviz_scraper import FinvizScraper
from src.scrapers.google_scraper import GoogleFinanceScraper
from src.scrapers.cnn_scraper import CNNFearGreedScraper
from src.scrapers.api_scraper import AlphaVantageAPIScraper, FinhubAPIScraper
from src.indicators.technical_indicators import TechnicalIndicators
from src.utils.data_formatter import format_data_as_dataframe
from src.utils.email_utils import send_consolidated_report
from src.scrapers.enhanced_sentiment_scraper import EnhancedSentimentScraper
from src.analytics.financial_analytics import FinancialAnalytics

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

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
if 'mongodb' not in webapp_config:
    webapp_config['mongodb'] = {}
webapp_config['mongodb']['enabled'] = False  # Disable MongoDB for Flask app
logger.info("MongoDB storage disabled for web application - storage only via CLI scripts")

def convert_numpy_types(data):
    """
    Convert numpy types to native Python types for JSON serialization
    
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
        return data.tolist()
    elif hasattr(data, 'item'):  # numpy scalar types have .item() method
        try:
            return data.item()
        except (ValueError, AttributeError):
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
    
    if 'all' in sources or 'enhanced_sentiment' in sources:
        # Enhanced sentiment analysis can work without Alpha Vantage key (uses other sources)
        scraper_tasks.append(("Enhanced Sentiment", lambda: EnhancedSentimentScraper(alpha_vantage_key=alpha_key or "", delay=1)._scrape_data(ticker)))

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
            
            # Wait for all to complete with timeout (60 seconds per ticker)
            concurrent.futures.wait(futures, timeout=60)
        
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
            
            # Use up to 3 parallel workers for multiple tickers
            max_ticker_workers = min(3, len(tickers))
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
        
        # Compute analytics for the portfolio
        analytics_data = {}
        if len(all_data) >= 1:
            try:
                logger.info("Computing advanced financial analytics...")
                
                # Create a modified config with custom allocation if provided
                analytics_config = copy.deepcopy(config) if config else {}
                if portfolio_allocation:
                    logger.info(f"Using custom portfolio allocation from UI: {portfolio_allocation}")
                    if 'portfolio' not in analytics_config:
                        analytics_config['portfolio'] = {}
                    analytics_config['portfolio']['allocations'] = portfolio_allocation
                
                analytics = FinancialAnalytics(config=analytics_config)
                tickers_list = list(all_data.keys())
                
                # Correlation Analysis (requires 2+ tickers)
                if len(tickers_list) >= 2:
                    try:
                        correlation_result = analytics.correlation_analysis(tickers_list, days=252)
                        if correlation_result and 'error' not in correlation_result:
                            analytics_data['correlation'] = correlation_result
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
