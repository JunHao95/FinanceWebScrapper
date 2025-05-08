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
from src.scrapers.api_scraper import AlphaVantageAPIScraper, FinhubAPIScraper
from src.indicators.technical_indicators import TechnicalIndicators
from src.utils.data_formatter import format_data_as_dataframe, save_to_csv, save_to_excel
from src.utils.display_formatter import print_grouped_metrics, save_formatted_report
from src.utils.email_utils import send_consolidated_report, parse_email_list
from src.config import setup_logging

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
                      choices=['yahoo', 'finviz', 'google', 'alphavantage', 'finhub', 'technical', 'all'],
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
    parser.add_argument('--max-workers', type=int, default=4, help="Maximum number of parallel workers")
    parser.add_argument('--delay', type=int, default=1, help="Delay between API requests in seconds")
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

def run_scrapers(ticker: str, sources: list, logger: logging.Logger, alpha_key: str = None, finhub_key: str = None, delay: int = 1) -> dict:
    """Run the selected scrapers and combine results

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
    results = {"Ticker": ticker, "Data Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    # Check if logging is enabled (logger level will be set higher than CRITICAL if disabled)
    logging_enabled = logger.level <= logging.CRITICAL
    
    if 'all' in sources or 'yahoo' in sources:
        if logging_enabled: 
            logger.info(f"Scraping Yahoo Finance data for {ticker}...")
        print(f"Scraping Yahoo Finance data for {ticker}...")
        yahoo_scraper = YahooFinanceScraper()
        results.update(yahoo_scraper.get_data(ticker))
        time.sleep(delay)  # Add delay to avoid rate limiting
    
    if 'all' in sources or 'finviz' in sources:
        if logging_enabled: 
            logger.info(f"Scraping Finviz data for {ticker}...")
        print(f"Scraping Finviz data for {ticker}...")
        finviz_scraper = FinvizScraper()
        results.update(finviz_scraper.get_data(ticker))
        time.sleep(delay)  # Add delay to avoid rate limiting
    
    if 'all' in sources or 'google' in sources:
        if logging_enabled: 
            logger.info(f"Scraping Google Finance data for {ticker}...")
        print(f"Scraping Google Finance data for {ticker}...")
        google_scraper = GoogleFinanceScraper()
        results.update(google_scraper.get_data(ticker))
        time.sleep(delay)  # Add delay to avoid rate limiting
    
    # Alpha Vantage API (only if API key is available)
    if 'all' in sources or 'alphavantage' in sources:
        if logging_enabled: 
            logger.info(f"Fetching Alpha Vantage API data for {ticker}...")
        print(f"Fetching Alpha Vantage API data for {ticker}...")
        alpha_scraper = AlphaVantageAPIScraper(api_key=alpha_key)
        if alpha_key or os.environ.get("ALPHA_VANTAGE_API_KEY"):
            results.update(alpha_scraper.get_data(ticker))
        else:
            if logging_enabled: 
                logger.warning("Alpha Vantage API key not provided. Skipping this data source.")
            print("Alpha Vantage API key not provided. Skipping this data source.")
            print("Set with --alpha-key or ALPHA_VANTAGE_API_KEY environment variable.")
        time.sleep(delay)  # Add delay to avoid rate limiting
    
    # Finhub API (only if API key is available)
    if 'all' in sources or 'finhub' in sources:
        if logging_enabled: 
            logger.info(f"Fetching Finhub API data for {ticker}...")
        print(f"Fetching Finhub API data for {ticker}...")
        finhub_scraper = FinhubAPIScraper(api_key=finhub_key)
        if finhub_key or os.environ.get("FINHUB_API_KEY"):
            results.update(finhub_scraper.get_data(ticker))
        else:
            if logging_enabled: 
                logger.warning("Finhub API key not provided. Skipping this data source.")
            print("Finhub API key not provided. Skipping this data source.")
            print("Set with --finhub-key or FINHUB_API_KEY environment variable.")
        time.sleep(delay)  # Add delay to avoid rate limiting
    
    # Technical indicators (only if API key is available)
    if 'all' in sources or 'technical' in sources:
        if logging_enabled: 
            logger.info(f"Calculating technical indicators for {ticker}...")
        print(f"Calculating technical indicators for {ticker}...")
        tech_indicators = TechnicalIndicators(api_key=alpha_key)
        if alpha_key or os.environ.get("ALPHA_VANTAGE_API_KEY"):
            indicator_data = tech_indicators.get_all_indicators(ticker)
            if "error" not in indicator_data:
                # Format the indicator data with source labels
                formatted_indicators = {}
                for key, value in indicator_data.items():
                    if key not in ["Ticker", "Last Updated"]:
                        formatted_indicators[f"{key} (Technical)"] = value
                    else:
                        formatted_indicators[key] = value
                results.update(formatted_indicators)
            else:
                if logging_enabled: 
                    logger.warning(f"Error calculating technical indicators: {indicator_data['error']}")
                print(f"Error calculating technical indicators: {indicator_data['error']}")
        else:
            if logging_enabled: 
                logger.warning("Alpha Vantage API key not provided. Cannot calculate technical indicators.")
            print("Alpha Vantage API key not provided. Cannot calculate technical indicators.")
            print("Set with --alpha-key or ALPHA_VANTAGE_API_KEY environment variable.")
    
    # Filter out any error messages
    results = {k: v for k, v in results.items() if not isinstance(v, dict) or "error" not in v}
    
    return results

def save_report(data: dict, ticker: str, file_format: str, output_dir: str = "output", save_enabled: bool = True) -> str:
    """
    Save report to file and return the file path.
    Default as True to save report.
    
    Args:
        data (dict): Stock data dictionary
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
    
    # Add extension
    if file_format == 'excel':
        filename += ".xlsx"
    elif file_format == 'text':
        filename += ".txt"
    else:
        filename += ".csv"
    
    # If saving report mode is disabled, just return filename without saving 
    if not save_enabled:
        filename = create_temp_file(file_format)
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

def create_summary_report(all_data: dict, output_dir: str, file_format: str, save_enabled: bool = False) -> str:
    """
    Create a summary report for all analyzed tickers
    If saved_enabled is false, create a temporary file for email attachments 
    
    Parameters:
        all_data (dict): Dictionary with ticker symbols as keys and data dictionaries as values
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
    Process a single ticker
    
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
    # Run scrapers
    data = run_scrapers(ticker, args.sources, logger, 
                     alpha_key=args.alpha_key, 
                     finhub_key=args.finhub_key,
                     delay=args.delay)
    
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
    else:
        df = format_data_as_dataframe(data)
        # Set display options to show more rows
        with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
            print(df.T)  # Transpose for better display
    
    # Save report
    report_path = save_report(data, ticker, args.format, args.output_dir, save_enabled=save_reports_enabled)
    
    return (ticker, data, report_path)

# Update this function in main.py to use consolidated email

def process_all_tickers(
    tickers: List[str],
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
    
    if args.parallel and len(tickers) > 1:
        print(f"Processing {len(tickers)} tickers in parallel with {args.max_workers} workers...")
        
        # Process tickers in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            # Submit all tasks
            future_to_ticker = {executor.submit(process_ticker, ticker, args, logger): ticker for ticker in tickers}
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    ticker, data, report_path = future.result()
                    all_data[ticker] = data
                    all_reports[ticker] = report_path
                except Exception as e:
                    if logging_enabled:
                        logger.error(f"Error processing ticker {ticker}: {str(e)}")
                    print(f"Error processing ticker {ticker}: {str(e)}")
    else:
        print(f"Processing {len(tickers)} tickers sequentially...")
        
        # Process tickers sequentially
        for ticker in tickers:
            try:
                ticker, data, report_path = process_ticker(ticker, args, logger)
                all_data[ticker] = data
                all_reports[ticker] = report_path
            except Exception as e:
                if logging_enabled:
                    logger.error(f"Error processing ticker {ticker}: {str(e)}")
                print(f"Error processing ticker {ticker}: {str(e)}")
    
    # Create summary report if requested
    summary_path: str = None
    if args.summary and len(all_data) > 1:
        summary_path = create_summary_report(all_data, args.output_dir, args.format, save_enabled=save_reports_enabled)
    
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
    print("DEBUGG ARGS: ", args)
    
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
                summary_path = create_summary_report(all_data, args.output_dir, args.format)
        
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
    process_all_tickers(tickers, args, logger)
    
    print("\nAll processing complete!")

if __name__ == "__main__":
    main()