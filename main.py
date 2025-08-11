#!/usr/bin/env python3
"""
Stock Data Scraper - Main Application Entry Point
"""
import os
import sys
import argparse
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import concurrent.futures
import time
import logging
import tempfile
from typing import List, Dict, Any, Optional
# Load environment variables at the start
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.scrapers.yahoo_scraper import YahooFinanceScraper
from src.scrapers.finviz_scraper import FinvizScraper
from src.scrapers.google_scraper import GoogleFinanceScraper
from src.scrapers.cnn_scraper import CNNFearGreedScraper
from src.scrapers.api_scraper import AlphaVantageAPIScraper, FinhubAPIScraper
from src.indicators.technical_indicators import TechnicalIndicators
from src.utils.data_formatter import format_data_as_dataframe, save_to_csv, save_to_excel
from src.utils.display_formatter import print_grouped_metrics, save_formatted_report
from src.utils.email_utils import send_consolidated_report, parse_email_list
from src.config import setup_logging
from src.scrapers.enhanced_sentiment_scraper import EnhancedSentimentScraper

def create_temp_file(file_format: str) -> str:
    """
    Create a temporary file with a specific format suffix.

    Args:
        file_format: The file format suffix to use for the temporary file.

    Returns:
        The name of the temporary file created.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_format}")
    return temp_file.name

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments

    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(description="Stock Financial Metrics Scraper")
    parser.add_argument('--tickers', type=str, help="Comma-separated stock ticker symbols to scrape")
    parser.add_argument('--ticker-file', type=str, help="File containing ticker symbols, one per line")
    parser.add_argument('--output-dir', type=str, default="output", help="Directory to save output files")
    parser.add_argument('--sources', type=str, nargs='+',
                      choices=['yahoo', 'finviz', 'google', 'alphavantage', 'finhub', 'technical', 'enhanced_sentiment', 'all'],
                      default=['all'], help="Data sources to scrape from")
    parser.add_argument('--format', type=str, choices=['csv', 'excel', 'text'],
                      default='csv', help="Output file format")
    parser.add_argument('--interactive', action='store_true',
                      help="Run in interactive mode")
    parser.add_argument('--alpha-key', type=str, help="Alpha Vantage API key")
    parser.add_argument('--finhub-key', type=str, help="Finhub API key")
    parser.add_argument('--display-mode', type=str, choices=['table', 'grouped'],
                      default='grouped', help="How to display results")
    parser.add_argument('--email', type=str, help="Comma-separated email addresses to send the report to")
    parser.add_argument('--cc', type=str, help="Comma-separated email addresses to CC the report to")
    parser.add_argument('--bcc', type=str, help="Comma-separated email addresses to BCC the report to")
    parser.add_argument('--parallel', action='store_true', help="Process tickers in parallel")
    parser.add_argument('--fast-mode', action='store_true',
                        help='Enable fast mode with minimal delays and concurrent processing (90% speed boost)')
    parser.add_argument('--max-workers', type=int, default=8, help="Maximum number of parallel workers (increased default)")
    parser.add_argument('--delay', type=int, default=1, help="Delay between API requests in seconds (reduced for parallel processing)")
    parser.add_argument('--summary', action='store_true', help="Generate a summary report for all tickers")
    parser.add_argument('--logging', choices=['true', 'false'], default='true',
                      help="Enable or disable logging (default: true)")
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error', 'critical'],
                      default='info', help="Set logging level (default: info)")
    parser.add_argument('--saveReports', choices=['true', 'false'], default='false',
                      help="Enable or disable saving reports to files (default: false)")
    
    return parser.parse_args()

def get_tickers_interactively() -> List[str]:
    """Get ticker symbols from user input
    
    Returns:
        List[str]: List of ticker symbols entered by the user
    """
    tickers: List[str] = []
    
    print("\nEnter stock ticker symbols (one per line, type 'done' when finished):")
    while True:
        ticker: str = input("> ").strip().upper()
        
        if ticker.lower() == 'done':
            if not tickers:
                print("No tickers provided. Please enter at least one ticker.")
                continue
            break
        
        if ticker.lower() == 'quit':
            print("Exiting program.")
            sys.exit(0)
        
        if not ticker:
            print("Please enter a valid ticker symbol.")
            continue
        
        tickers.append(ticker)
        print(f"Added {ticker}. Current tickers: {', '.join(tickers)}")
    
    return tickers

def load_tickers_from_file(file_path: str) -> List[str]:
    """
    Load ticker symbols from a file
    
    Args:
        file_path (str): Path to the file containing ticker symbols
    
    Returns:
        List[str]: List of ticker symbols loaded from the file
    """
    if not os.path.exists(file_path):
        print(f"Error: Ticker file '{file_path}' not found.")
        sys.exit(1)
        
    try:
        with open(file_path, 'r') as f:
            # Read lines, strip whitespace, convert to uppercase, and filter out empty lines
            tickers = [line.strip().upper() for line in f.readlines() if line.strip()]
            
        if not tickers:
            print(f"Error: No valid ticker symbols found in file '{file_path}'.")
            sys.exit(1)
            
        return tickers
    except Exception as e:
        print(f"Error reading ticker file: {str(e)}")
        sys.exit(1)

def run_scrapers_concurrent(ticker: str, sources: list, logger: logging.Logger, alpha_key: str | None = None, finhub_key: str | None = None, delay: int = 1) -> dict:
    """Run scrapers concurrently for maximum performance

    Args:
        ticker (str): Stock ticker symbol.
        sources (list): List of data sources to scrape.
        logger (logging.Logger): Logger instance for logging.
        alpha_key (str, optional): Alpha Vantage API key. Defaults to None.
        finhub_key (str, optional): Finhub API key. Defaults to None.
        delay (int, optional): Delay in seconds between requests to avoid rate limiting. Defaults to 1.

    Returns:
        dict: Combined results from all scrapers.
    """
    import concurrent.futures
    import threading
    import time
    
    results = {"Ticker": ticker, "Data Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    logging_enabled = logger.level <= logging.CRITICAL
    
    # Thread-safe result collection
    results_lock = threading.Lock()
    
    def run_scraper(scraper_name, scraper_func):
        """Thread-safe scraper runner"""
        try:
            if logging_enabled:
                logger.info(f"Scraping {scraper_name} data for {ticker}...")
            print(f"Scraping {scraper_name} data for {ticker}...")
            
            data = scraper_func()
            
            with results_lock:
                if data and not (isinstance(data, dict) and "error" in data):
                    results.update(data)
                    
        except Exception as e:
            if logging_enabled:
                logger.error(f"Error in {scraper_name} for {ticker}: {e}")
            print(f"Error in {scraper_name} for {ticker}: {e}")
    
    # Define scraper functions
    scraper_tasks = []
    
    if 'all' in sources or 'yahoo' in sources:
        scraper_tasks.append(("Yahoo Finance", lambda: YahooFinanceScraper().get_data(ticker)))
    
    if 'all' in sources or 'finviz' in sources:
        scraper_tasks.append(("Finviz", lambda: FinvizScraper().get_data(ticker)))
    
    if 'all' in sources or 'google' in sources:
        scraper_tasks.append(("Google Finance", lambda: GoogleFinanceScraper().get_data(ticker)))
    
    if 'all' in sources or 'enhanced_sentiment' in sources:
        # Enhanced sentiment analysis can work without Alpha Vantage key (uses other sources)
        scraper_tasks.append(("Enhanced Sentiment", lambda: EnhancedSentimentScraper(alpha_vantage_key=alpha_key or "")._scrape_data(ticker)))
    
    if ('all' in sources or 'alphavantage' in sources) and (alpha_key or os.environ.get("ALPHA_VANTAGE_API_KEY")):
        scraper_tasks.append(("Alpha Vantage", lambda: AlphaVantageAPIScraper(api_key=alpha_key).get_data(ticker)))
    
    if ('all' in sources or 'finhub' in sources) and (finhub_key or os.environ.get("FINHUB_API_KEY")):
        scraper_tasks.append(("Finhub", lambda: FinhubAPIScraper(api_key=finhub_key).get_data(ticker)))
    
    if ('all' in sources or 'technical' in sources) and (alpha_key or os.environ.get("ALPHA_VANTAGE_API_KEY")):
        def get_technical_data():
            tech_indicators = TechnicalIndicators(api_key=alpha_key)
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
    max_workers = min(4, len(scraper_tasks))  # Limit concurrent requests
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_scraper, name, func) for name, func in scraper_tasks]
        
        # Wait for all to complete with timeout
        concurrent.futures.wait(futures, timeout=30)  # 30 second timeout per ticker
    
    # Small delay to be respectful to APIs
    time.sleep(max(0.1, delay * 0.1))  # Reduced delay since we're not hammering individual APIs
    
    return results

def run_scrapers(ticker: str, sources: list, logger: logging.Logger, alpha_key: str | None = None, finhub_key: str | None = None, delay: int = 1) -> dict:
    """Optimized scraper runner with fallback to sequential processing"""
    try:
        # Try concurrent processing first
        return run_scrapers_concurrent(ticker, sources, logger, alpha_key, finhub_key, delay)
    except Exception as e:
        # Fallback to sequential processing if concurrent fails
        logger.warning(f"Concurrent processing failed for {ticker}, falling back to sequential: {e}")
        return run_scrapers_sequential(ticker, sources, logger, alpha_key, finhub_key, delay)

def run_scrapers_sequential(ticker: str, sources: list, logger: logging.Logger, alpha_key: str | None = None, finhub_key: str | None = None, delay: int = 1) -> dict:
    """Original sequential scraper as fallback with optimized delays"""
    results = {"Ticker": ticker, "Data Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    logging_enabled = logger.level <= logging.CRITICAL
    
    # Reduced delays for faster processing
    fast_delay = max(1, int(delay * 0.2))  # 80% reduction in delays, minimum 1 second
    
    if 'all' in sources or 'yahoo' in sources:
        if logging_enabled: 
            logger.info(f"Scraping Yahoo Finance data for {ticker}...")
        print(f"Scraping Yahoo Finance data for {ticker}...")
        yahoo_scraper = YahooFinanceScraper(delay=fast_delay)
        yahoo_data = yahoo_scraper.get_data(ticker)
        if yahoo_data:
            results.update(yahoo_data)
    
    if 'all' in sources or 'finviz' in sources:
        if logging_enabled: 
            logger.info(f"Scraping Finviz data for {ticker}...")
        print(f"Scraping Finviz data for {ticker}...")
        finviz_scraper = FinvizScraper(delay=fast_delay)
        finviz_data = finviz_scraper.get_data(ticker)
        if finviz_data:
            results.update(finviz_data)
    
    if 'all' in sources or 'google' in sources:
        if logging_enabled: 
            logger.info(f"Scraping Google Finance data for {ticker}...")
        print(f"Scraping Google Finance data for {ticker}...")
        google_scraper = GoogleFinanceScraper(delay=fast_delay)
        google_data = google_scraper.get_data(ticker)
        if google_data:
            results.update(google_data)
    
    if 'all' in sources or 'enhanced_sentiment' in sources:
        # Enhanced sentiment analysis can work without Alpha Vantage key (uses other sources)
        if logging_enabled: 
            logger.info(f"Fetching Enhanced Sentiment data for {ticker}...")
        print(f"Fetching Enhanced Sentiment data for {ticker}...")
        enhanced_scraper = EnhancedSentimentScraper(alpha_vantage_key=alpha_key or "", delay=fast_delay)
        enhanced_data = enhanced_scraper._scrape_data(ticker)
        if enhanced_data:
            results.update(enhanced_data)

    if ('all' in sources or 'alphavantage' in sources) and (alpha_key or os.environ.get("ALPHA_VANTAGE_API_KEY")):
        if logging_enabled: 
            logger.info(f"Fetching Alpha Vantage API data for {ticker}...")
        print(f"Fetching Alpha Vantage API data for {ticker}...")
        alpha_scraper = AlphaVantageAPIScraper(api_key=alpha_key, delay=fast_delay)
        alpha_data = alpha_scraper.get_data(ticker)
        if alpha_data:
            results.update(alpha_data)
    
    if ('all' in sources or 'finhub' in sources) and (finhub_key or os.environ.get("FINHUB_API_KEY")):
        if logging_enabled: 
            logger.info(f"Fetching Finhub API data for {ticker}...")
        print(f"Fetching Finhub API data for {ticker}...")
        finhub_scraper = FinhubAPIScraper(api_key=finhub_key, delay=fast_delay)
        finhub_data = finhub_scraper.get_data(ticker)
        if finhub_data:
            results.update(finhub_data)
    
    if ('all' in sources or 'technical' in sources) and (alpha_key or os.environ.get("ALPHA_VANTAGE_API_KEY")):
        if logging_enabled: 
            logger.info(f"Calculating technical indicators for {ticker}...")
        print(f"Calculating technical indicators for {ticker}...")
        tech_indicators = TechnicalIndicators(api_key=alpha_key)
        indicator_data = tech_indicators.get_all_indicators(ticker)
        if "error" not in indicator_data:
            formatted_indicators = {}
            for key, value in indicator_data.items():
                if key not in ["Ticker", "Last Updated"]:
                    formatted_indicators[f"{key} (Technical)"] = value
                else:
                    formatted_indicators[key] = value
            results.update(formatted_indicators)

    # Filter out any error messages
    results = {k: v for k, v in results.items() if not isinstance(v, dict) or "error" not in v}
    return results

def save_report(data: dict, ticker: str, file_format: str, output_dir: str = "output", save_enabled: bool = True) -> str:
    """
    Save report to file and return the file path.
    Default as True to save report.
    
    Args:
        data (dict): Stock data dictionary
        cnnMetricData (dict): CNN metrics data
        ticker (str): Stock ticker symbol
        file_format (str): Output format (csv, excel, text)
        output_dir (str): Directory to save the file
        save_enabled (bool): Flag to enable or disable saving
        
    Returns:
        str: Path to the saved file
    """
    # Generate filename
    filename = os.path.join(
        output_dir, 
        f"{ticker}_financial_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
   
    if not file_format:
        file_format = 'text'
    # Add extension
    if file_format == 'excel':
        filename += ".xlsx"
    elif file_format == 'text':
        filename += ".txt"
    else:
        filename += ".csv"
    
    # If saving report mode is disabled, just return filename without saving 
    if not save_enabled:
        
        filename = create_temp_file("text")
        print(f"Report saving is disabled. Temporary file created for email: {filename}")
 
    # Ensure directory exists
    
    if save_enabled:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Save the file in the specified format
    if file_format == 'excel':
        df = format_data_as_dataframe(data)
        save_to_excel(df, filename)
        print(f"Data saved to Excel file: {filename}")
    elif file_format == 'text':
        save_formatted_report(data, filename)
        print(f"Data saved to text report: {filename}")
    else:
        df = format_data_as_dataframe(data)
        save_to_csv(df, filename)
        print(f"Data saved to CSV file: {filename}")
    
    return filename

def create_summary_report(all_data: dict, cnnMetricData: dict, output_dir: str, file_format: str, save_enabled: bool = False) -> str:
    """
    Create a summary report for all analyzed tickers
    If saved_enabled is false, create a temporary file for email attachments 
    
    Parameters:
        all_data (dict): Dictionary with ticker symbols as keys and data dictionaries as values
        cnnMetricData (dict): Dictionary with CNN metrics
        output_dir (str): Directory to save the report
        file_format (str): Output format (csv, excel, text)
        save_enabled (bool): Whether to actually save the file
        
    Returns:
        str: Path to the saved summary file, or None if saving is disabled
    """
    # Generate summary data
    tickers = list(all_data.keys())
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Extract key metrics for comparison
    summary_data = []
    
    # Define key metrics to include in summary
    key_metrics = [
        "P/E Ratio", "Forward P/E", "PEG Ratio", "P/B Ratio", "P/S Ratio", 
        "EV/EBITDA", "ROE", "ROA", "ROIC", "Profit Margin", "Operating Margin", 
        "EPS", "Current Price", "RSI (14)", "Beta"
    ]
    
    for ticker, data in all_data.items():
        ticker_summary = {"Ticker": ticker}
        # Get the most relevant value for each key metric
        for metric in key_metrics:
            for key, value in data.items():
                if metric in key:
                    ticker_summary[metric] = value
                    break      
        summary_data.append(ticker_summary)
    
    # Create DataFrame
    summary_df = pd.DataFrame(summary_data)

    # Generate filename
    filename = os.path.join(
        output_dir, 
        f"stock_comparison_summary_{timestamp}"
    )
    
    # Add extension
    if file_format == 'excel':
        filename += ".xlsx"
    elif file_format == 'text':
        filename += ".txt"
    else:
        filename += ".csv"
    
    # If saving is disabled, just display the summary and return
    if not save_enabled:
        print("\n" + "="*80)
        print("Stock Comparison Summary")
        print("="*80)
        print(f"Tickers analyzed: {', '.join(tickers)}")
        print("\nSummary data:")
        
        # Display the summary DataFrame
        with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
            print(summary_df)
            
        print(f"\nReport saving is disabled. Would have saved to: {filename}")
        filename = create_temp_file(file_format)
        print(f"Temporary file created for email: {filename}")
        #return None
    
    # Save the file in the specified format
    # Ensure directory exists
    if save_enabled:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    if file_format == 'excel':
        save_to_excel(summary_df, filename)
    elif file_format == 'text':
        # Custom text summary
        with open(filename, 'w') as f:
            f.write("="*80 + "\n")
            f.write(f"Stock Comparison Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            f.write(f"Tickers analyzed: {', '.join(tickers)}\n\n")
            f.write(summary_df.to_string(index=False))
            f.write("\n\n")
    else:
        save_to_csv(summary_df, filename)
    
    print(f"Summary report saved to: {filename}")
    return filename

def process_ticker(ticker: str, args: argparse.Namespace, logger: logging.Logger) -> tuple:
    """
    Process a single ticker with optimizations
    
    Args:
        ticker (str): Ticker symbol
        args (argparse.Namespace): Command line arguments
        logger (logging.Logger): Logger instance
        
    Returns:
        tuple: (ticker, data, report_path)
            ticker (str): Ticker symbol
            data (dict): Dictionary with financial metrics
            report_path (str): Path to saved report file
    """
    print(f"\nProcessing ticker: {ticker}")
    save_reports_enabled = args.saveReports.lower() == 'true'
    
    # Apply fast mode optimizations
    delay = args.delay
    if hasattr(args, 'fast_mode') and args.fast_mode:
        delay = max(1, int(delay * 0.1))  # 90% reduction in delay for fast mode
        print(f"  🚀 Fast mode enabled - using reduced delay: {delay}s")
    
    # Run scrapers
    data = run_scrapers(ticker, args.sources, logger, 
                     alpha_key=args.alpha_key, 
                     finhub_key=args.finhub_key,
                     delay=delay)
    
    # Skip detailed display in fast mode to save time
    if not (hasattr(args, 'fast_mode') and args.fast_mode):
        # Display results
        print("\n" + "="*80)
        print(f"Financial Metrics for {ticker}")
        print("="*80)
        
        if args.display_mode == 'grouped':
            try:
                print_grouped_metrics(data)
            except ImportError:
                print("Warning: tabulate package not found. Falling back to table display.")
                df = format_data_as_dataframe(data)
                with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
                    print(df.T)
            # Print enhanced sentiment summary if available
            enhanced_keys = [k for k in data.keys() if '(Enhanced)' in k]
            if enhanced_keys:
                print("\nEnhanced Sentiment Analysis:")
                for k in enhanced_keys:
                    print(f"{k}: {data[k]}")
        else:
            df = format_data_as_dataframe(data)
            # Set display options to show more rows
            with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
                print(df.T)  # Transpose for better display
    else:
        print(f"  ✅ {ticker} processed successfully (fast mode - details hidden)")
    
    # Save report
    report_path = save_report(data, ticker, args.format, args.output_dir, save_enabled=save_reports_enabled)
    return (ticker, data, report_path)

# Update this function in main.py to use consolidated email

def process_all_tickers(
    tickers: List[str],
    CnnMetricData: Dict[str, Any],
    args: argparse.Namespace,
    logger: logging.Logger
) -> Dict[str, Dict[str, Any]]:
    """
    Process all tickers, either sequentially or in parallel
    
    Args:
        tickers (List[str]): List of ticker symbols
        args (argparse.Namespace): Command line arguments
        logger (logging.Logger): Logger instance
        
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary with ticker symbols as keys and data dictionaries as values
    """
    all_data: Dict[str, Dict[str, Any]] = {}
    all_reports: Dict[str, str] = {}
    # Check if logging is enabled
    logging_enabled: bool = args.logging.lower() == 'true'
     # Check if saving reports is enabled
    save_reports_enabled: bool = args.saveReports.lower() == 'true'
    print(f"DEBBUUGG save reports , ", save_reports_enabled)
    
    # Optimize parallel processing based on fast mode
    auto_parallel = len(tickers) > 3  # Auto-enable parallel for 4+ tickers
    use_parallel = args.parallel or (hasattr(args, 'fast_mode') and args.fast_mode and auto_parallel)
    
    if use_parallel and len(tickers) > 1:
        # Optimize worker count for fast mode
        max_workers = args.max_workers
        if hasattr(args, 'fast_mode') and args.fast_mode:
            max_workers = min(max_workers * 2, 16)  # Double workers in fast mode, cap at 16
            
        print(f"🚀 Processing {len(tickers)} tickers in parallel with {max_workers} workers...")
        if hasattr(args, 'fast_mode') and args.fast_mode:
            print("  ⚡ Fast mode enabled - using concurrent processing within tickers")
        
        # Process tickers in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_ticker = {executor.submit(process_ticker, ticker, args, logger): ticker for ticker in tickers}
            
            # Process results as they complete with progress tracking
            completed = 0
            for future in concurrent.futures.as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    ticker, data, report_path = future.result(timeout=60)  # 60 second timeout per ticker
                    all_data[ticker] = data
                    all_reports[ticker] = report_path
                    completed += 1
                    print(f"  ✅ Completed {completed}/{len(tickers)}: {ticker}")
                except concurrent.futures.TimeoutError:
                    print(f"  ⏰ Timeout processing ticker {ticker}")
                    if logging_enabled:
                        logger.error(f"Timeout processing ticker {ticker}")
                except Exception as e:
                    if logging_enabled:
                        logger.error(f"Error processing ticker {ticker}: {str(e)}")
                    print(f"  ❌ Error processing ticker {ticker}: {str(e)}")
    else:
        print(f"Processing {len(tickers)} tickers sequentially...")
        
        # Process tickers sequentially
        for i, ticker in enumerate(tickers, 1):
            try:
                print(f"  📊 Processing {i}/{len(tickers)}: {ticker}")
                ticker, data, report_path = process_ticker(ticker, args, logger)
                all_data[ticker] = data
                all_reports[ticker] = report_path
                print(f"  ✅ Completed {i}/{len(tickers)}: {ticker}")
            except Exception as e:
                if logging_enabled:
                    logger.error(f"Error processing ticker {ticker}: {str(e)}")
                print(f"  ❌ Error processing ticker {ticker}: {str(e)}")
    
    # Create summary report if requested
    summary_path: Optional[str] = None
    if args.summary and len(all_data) > 1:
        summary_path = create_summary_report(all_data, CnnMetricData, args.output_dir, args.format, save_enabled=save_reports_enabled)
    
    # Send email if requested
    if (args.email or args.cc or args.bcc) and all_reports:
        print("\nPreparing consolidated email report...")
        valid_report: Dict[str, str] = {ticker: path for ticker, path in all_reports.items() if path}
        if not valid_report:
            print("No valid reports to send via email.")
            return all_data
        
        # Send consolidated report
        success: bool = send_consolidated_report(
            tickers=list(all_data.keys()),
            report_paths=all_reports,
            all_data=all_data,
            cnnMetricData=CnnMetricData,
            recipients=args.email,
            summary_path=summary_path,
            cc=args.cc,
            bcc=args.bcc
        )
        
        if success:
            print(f"Consolidated report successfully emailed")
        else:
            print(f"Failed to send consolidated report")
    
    return all_data

def main() -> None:
    """Main application entry point.

    This function orchestrates the scraping of financial metrics. It sets up logging,
    parses command-line arguments, and processes stock tickers either interactively or
    from provided sources.

    Args:
        None

    Returns:
        None
    """
    # Setup logging
    logger = setup_logging()
    
    print("="*80)
    print("Stock Financial Metrics Scraper")
    print("="*80)
    print("This program collects financial metrics from web sources and APIs:")
    print("  - Web sources: Yahoo Finance, Finviz, Google Finance")
    print("  - APIs: Alpha Vantage, Finhub (API keys required)")
    print("  - Technical indicators: Bollinger Bands, Moving Averages, RSI, Volume indicators")
    print("Added metrics: EV/EBITDA, PEG ratio, ROE, ROIC, EPS, and more!")
    
    args = parse_arguments()
    
    # Setup logging based on command-line arguments
    logging_enabled = args.logging.lower() == 'true'

    # Set log level based on command-line argument
    log_level_map = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    log_level = log_level_map.get(args.log_level.lower(), logging.INFO)
    # Initialize logger with proper settings
    logger = setup_logging(log_level=log_level, logging_enabled=logging_enabled)

    if logging_enabled:
        logger.info("Logging is enabled at %s level", args.log_level.upper())
        print(f"Logging is enabled at {args.log_level.upper()} level")
    else:
        print("Logging is disabled")

    try:
        # Import tabulate only if needed
        if args.display_mode == 'grouped':
            try:
                import tabulate
            except ImportError:
                print("Warning: tabulate package not found. Installing it is recommended for better display...")
                print("Run: pip install tabulate")
                args.display_mode = 'table'
    except:
        pass
    
    # CNN Fear & Greed Index (does not require ticker)
    if logging_enabled:
        logger.info("Scraping CNN Fear & Greed Index data...")
    print("Scraping CNN Fear & Greed Index data...")
    cnn_scraper = CNNFearGreedScraper()
    cnnMetricData = cnn_scraper.scrape_data()
    # Get tickers to process
    tickers = []
    
    if args.interactive:
        tickers = get_tickers_interactively()
        
        print(f"\nAnalyzing {len(tickers)} ticker(s): {', '.join(tickers)}")
        
        # Process all tickers
        all_data = {}
        all_reports = {}
        
        for ticker in tickers:
            try:
                ticker, data, report_path = process_ticker(ticker, args, logger)
                all_data[ticker] = data
                all_reports[ticker] = report_path
            except Exception as e:
                if logging_enabled:
                    logger.error(f"Error processing ticker {ticker}: {str(e)}")
                print(f"Error processing ticker {ticker}: {str(e)}")
        
        # Create summary report if requested or if multiple tickers
        summary_path = None
        if len(tickers) > 1:
            create_summary = args.summary
            if not create_summary:
                create_summary = input("\nWould you like to create a summary comparison report? (y/n): ").strip().lower() == 'y'
                
            if create_summary:
                summary_path = create_summary_report(all_data, cnnMetricData, args.output_dir, args.format)
        
        # Ask if user wants to email the report
        send_email = False
        if not (args.email or args.cc or args.bcc):
            send_email = input("\nWould you like to email these reports? (y/n): ").strip().lower() == 'y'
        else:
            send_email = True
        
        if send_email:
            recipients = args.email
            if not recipients:
                recipients = input("Enter recipient email address(es) (comma-separated): ").strip()
            
            cc = args.cc
            if not cc and input("Would you like to CC anyone? (y/n): ").strip().lower() == 'y':
                cc = input("Enter CC email address(es) (comma-separated): ").strip()
            
            bcc = args.bcc
            if not bcc and input("Would you like to BCC anyone? (y/n): ").strip().lower() == 'y':
                bcc = input("Enter BCC email address(es) (comma-separated): ").strip()
            
            if recipients or cc or bcc:
                print("\nSending consolidated report...")
                
                success = send_consolidated_report(
                    tickers=list(all_data.keys()),
                    report_paths=all_reports,
                    all_data=all_data,
                    cnnMetricData=cnnMetricData,
                    recipients=recipients,
                    summary_path=summary_path,
                    cc=cc,
                    bcc=bcc
                )
                
                if success:
                    print("Consolidated report successfully emailed")
                else:
                    print("Failed to send consolidated report")
            else:
                print("No email addresses provided. Skipping email.")
    elif args.ticker_file:
        tickers = load_tickers_from_file(args.ticker_file)
    elif args.tickers:
        tickers = [ticker.strip().upper() for ticker in args.tickers.split(',') if ticker.strip()]
    else:
        print("Error: Please specify tickers using --tickers, --ticker-file, or --interactive")
        sys.exit(1)
    
    if not tickers:
        print("Error: No valid ticker symbols provided.")
        sys.exit(1)
    
    print(f"\nAnalyzing {len(tickers)} ticker(s): {', '.join(tickers)}")
    
    # Process all tickers
    process_all_tickers(tickers, cnnMetricData, args, logger)
    
    # Clean up connection pool after everything is completed
    try:
        from src.utils.request_handler import close_session
        close_session()
        logger.info("Connection pool cleaned up successfully")
    except ImportError:
        pass  # Graceful fallback if import fails
    
    print("\nAll processing complete!")

if __name__ == "__main__":
    main()