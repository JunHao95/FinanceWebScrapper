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
from src.utils.email_utils import send_stock_report, parse_email_list
from src.config import setup_logging

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Stock Financial Metrics Scraper")
    parser.add_argument('--ticker', type=str, help="Stock ticker symbol to scrape")
    parser.add_argument('--output', type=str, help="Output file path (CSV or Excel)")
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
    
    return parser.parse_args()

def get_ticker_interactively():
    """Get ticker symbol from user input"""
    while True:
        ticker = input("\nEnter stock ticker symbol (or 'quit' to exit): ").strip().upper()
        
        if ticker.lower() == 'quit':
            print("Exiting program.")
            sys.exit(0)
        
        if not ticker:
            print("Please enter a valid ticker symbol.")
            continue
            
        return ticker

def run_scrapers(ticker, sources, logger, alpha_key=None, finhub_key=None):
    """Run the selected scrapers and combine results"""
    results = {"Ticker": ticker, "Data Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    if 'all' in sources or 'yahoo' in sources:
        logger.info(f"Scraping Yahoo Finance data for {ticker}...")
        print(f"Scraping Yahoo Finance data for {ticker}...")
        yahoo_scraper = YahooFinanceScraper()
        results.update(yahoo_scraper.get_data(ticker))
    
    if 'all' in sources or 'finviz' in sources:
        logger.info(f"Scraping Finviz data for {ticker}...")
        print(f"Scraping Finviz data for {ticker}...")
        finviz_scraper = FinvizScraper()
        results.update(finviz_scraper.get_data(ticker))
    
    if 'all' in sources or 'google' in sources:
        logger.info(f"Scraping Google Finance data for {ticker}...")
        print(f"Scraping Google Finance data for {ticker}...")
        google_scraper = GoogleFinanceScraper()
        results.update(google_scraper.get_data(ticker))
    
    # MarketWatch scraper removed due to access restrictions
    
    # Alpha Vantage API (only if API key is available)
    if 'all' in sources or 'alphavantage' in sources:
        logger.info(f"Fetching Alpha Vantage API data for {ticker}...")
        print(f"Fetching Alpha Vantage API data for {ticker}...")
        alpha_scraper = AlphaVantageAPIScraper(api_key=alpha_key)
        if alpha_key or os.environ.get("ALPHA_VANTAGE_API_KEY"):
            results.update(alpha_scraper.get_data(ticker))
        else:
            logger.warning("Alpha Vantage API key not provided. Skipping this data source.")
            print("Alpha Vantage API key not provided. Skipping this data source.")
            print("Set with --alpha-key or ALPHA_VANTAGE_API_KEY environment variable.")
    
    # Finhub API (only if API key is available)
    if 'all' in sources or 'finhub' in sources:
        logger.info(f"Fetching Finhub API data for {ticker}...")
        print(f"Fetching Finhub API data for {ticker}...")
        finhub_scraper = FinhubAPIScraper(api_key=finhub_key)
        if finhub_key or os.environ.get("FINHUB_API_KEY"):
            results.update(finhub_scraper.get_data(ticker))
        else:
            logger.warning("Finhub API key not provided. Skipping this data source.")
            print("Finhub API key not provided. Skipping this data source.")
            print("Set with --finhub-key or FINHUB_API_KEY environment variable.")
    
    # Technical indicators (only if API key is available)
    if 'all' in sources or 'technical' in sources:
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
                logger.warning(f"Error calculating technical indicators: {indicator_data['error']}")
                print(f"Error calculating technical indicators: {indicator_data['error']}")
        else:
            logger.warning("Alpha Vantage API key not provided. Cannot calculate technical indicators.")
            print("Alpha Vantage API key not provided. Cannot calculate technical indicators.")
            print("Set with --alpha-key or ALPHA_VANTAGE_API_KEY environment variable.")
    
    # Filter out any error messages
    results = {k: v for k, v in results.items() if not isinstance(v, dict) or "error" not in v}
    
    return results

def save_report(data, ticker, file_format, custom_path=None):
    """
    Save report to file and return the file path
    
    Args:
        data (dict): Stock data dictionary
        ticker (str): Stock ticker symbol
        file_format (str): Output format (csv, excel, text)
        custom_path (str, optional): Custom file path
        
    Returns:
        str: Path to the saved file
    """
    # Generate default filename if not specified
    if not custom_path:
        filename = os.path.join(
            "output", 
            f"{ticker}_financial_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Add extension
        if file_format == 'excel':
            filename += ".xlsx"
        elif file_format == 'text':
            filename += ".txt"
        else:
            filename += ".csv"
    else:
        filename = custom_path
    
    # Ensure directory exists
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

def send_email_report(data, ticker, recipients, report_path, cc=None, bcc=None):
    """
    Send report via email to multiple recipients
    
    Args:
        data (dict): Stock data dictionary
        ticker (str): Stock ticker symbol
        recipients (str or list): Recipient email address(es)
        report_path (str): Path to the report file
        cc (str or list, optional): CC email address(es)
        bcc (str or list, optional): BCC email address(es)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if isinstance(recipients, str):
        recipients_list = parse_email_list(recipients)
    else:
        recipients_list = recipients
        
    recipient_count = len(recipients_list)
    cc_count = len(parse_email_list(cc)) if cc else 0
    bcc_count = len(parse_email_list(bcc)) if bcc else 0
    
    total_recipients = recipient_count + cc_count + bcc_count
    
    if total_recipients == 0:
        print("No valid email addresses provided.")
        return False
        
    plural = "s" if total_recipients > 1 else ""
    print(f"Sending report to {total_recipients} recipient{plural}...")
    
    # Check if email configuration is set
    if not os.environ.get("FINANCE_SENDER_EMAIL") or not os.environ.get("FINANCE_SENDER_PASSWORD"):
        print("Email configuration not set. Set the following environment variables:")
        print("  - FINANCE_SENDER_EMAIL: Sender email address")
        print("  - FINANCE_SENDER_PASSWORD: Sender email password")
        print("  - FINANCE_SMTP_SERVER: SMTP server (default: smtp.gmail.com)")
        print("  - FINANCE_SMTP_PORT: SMTP port (default: 587)")
        print("  - FINANCE_USE_TLS: Use TLS (default: True)")
        return False
    
    # Send the report
    success = send_stock_report(ticker, recipients_list, report_path, data, cc, bcc)
    
    if success:
        print(f"Report successfully sent to {total_recipients} recipient{plural}")
    else:
        print(f"Failed to send report")
    
    return success

def main():
    """Main application entry point"""
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
    
    if args.interactive:
        while True:
            ticker = get_ticker_interactively()
            logger.info(f"Starting interactive scrape for {ticker}")
            data = run_scrapers(ticker, args.sources, logger, 
                           alpha_key=args.alpha_key, 
                           finhub_key=args.finhub_key)
            
            # Display results
            print("\n" + "="*80)
            print(f"Financial Metrics for {ticker}")
            print("="*80)
            
            if args.display_mode == 'grouped':
                print_grouped_metrics(data)
            else:
                df = format_data_as_dataframe(data)
                # Set display options to show more rows
                with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
                    print(df.T)  # Transpose for better display
            
            # Ask if user wants to save to file
            save = input("\nWould you like to save this data to a file? (y/n): ").strip().lower()
            if save == 'y':
                # Ask for file format if not specified
                file_format = args.format
                if not file_format:
                    format_choice = input("Choose a file format (csv/excel/text): ").strip().lower()
                    file_format = format_choice if format_choice in ['csv', 'excel', 'text'] else 'csv'
                
                # Save the file
                saved_file = save_report(data, ticker, file_format)
                
                # Ask if user wants to email the report
                email = input("\nWould you like to email this report? (y/n): ").strip().lower()
                if email == 'y':
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
                        send_email_report(data, ticker, recipients, saved_file, cc, bcc)
                    else:
                        print("No email addresses provided. Skipping email.")
            
            # Ask if user wants to analyze another stock
            continue_scraping = input("\nWould you like to analyze another stock? (y/n): ").strip().lower()
            if continue_scraping != 'y':
                print("Exiting program.")
                break
    else:
        if not args.ticker:
            print("Error: Please provide a ticker symbol with --ticker or use --interactive mode")
            sys.exit(1)
            
        ticker = args.ticker.upper()
        logger.info(f"Starting scrape for {ticker}")
        data = run_scrapers(ticker, args.sources, logger,
                       alpha_key=args.alpha_key,
                       finhub_key=args.finhub_key)
        
        # Display results
        print("\n" + "="*80)
        print(f"Financial Metrics for {ticker}")
        print("="*80)
        
        if args.display_mode == 'grouped':
            print_grouped_metrics(data)
        else:
            df = format_data_as_dataframe(data)
            # Set display options to show more rows
            with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
                print(df.T)  # Transpose for better display
        
        # Save to file if output is specified or email is requested
        report_path = None
        if args.output or args.email or args.cc or args.bcc:
            # Determine file format
            file_format = args.format
            
            # Save the report
            report_path = save_report(data, ticker, file_format, args.output)
            
            # Send email if requested
            if args.email or args.cc or args.bcc:
                send_email_report(data, ticker, args.email, report_path, args.cc, args.bcc)

if __name__ == "__main__":
    main()