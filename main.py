#!/usr/bin/env python3
"""
Stock Data Scraper - Main Application Entry Point
"""
import os
import sys
import argparse
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.scrapers.yahoo_scraper import YahooFinanceScraper
from src.scrapers.finviz_scraper import FinvizScraper
from src.scrapers.google_scraper import GoogleFinanceScraper
from src.utils.data_formatter import format_data_as_dataframe, save_to_csv, save_to_excel
from src.config import setup_logging

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Stock Financial Metrics Scraper")
    parser.add_argument('--ticker', type=str, help="Stock ticker symbol to scrape")
    parser.add_argument('--output', type=str, help="Output file path (CSV or Excel)")
    parser.add_argument('--sources', type=str, nargs='+', 
                      choices=['yahoo', 'finviz', 'google', 'all'],
                      default=['all'], help="Data sources to scrape from")
    parser.add_argument('--format', type=str, choices=['csv', 'excel'], 
                      default='csv', help="Output file format")
    parser.add_argument('--interactive', action='store_true', 
                      help="Run in interactive mode")
    
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

def run_scrapers(ticker, sources, logger):
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
    
    # Filter out any error messages
    results = {k: v for k, v in results.items() if not isinstance(v, dict) or "error" not in v}
    
    return results

def main():
    """Main application entry point"""
    # Setup logging
    logger = setup_logging()
    
    print("="*80)
    print("Stock Financial Metrics Scraper")
    print("="*80)
    print("This program scrapes key financial ratios and metrics from Yahoo Finance, Finviz, and Google Finance.")
    print("Added metrics: EV/EBITDA, PEG ratio, ROE, ROIC, EPS, and more!")
    
    args = parse_arguments()
    
    if args.interactive:
        while True:
            ticker = get_ticker_interactively()
            logger.info(f"Starting interactive scrape for {ticker}")
            data = run_scrapers(ticker, args.sources, logger)
            
            # Display results
            df = format_data_as_dataframe(data)
            print("\n" + "="*80)
            print(f"Financial Metrics for {ticker}")
            print("="*80)
            print(df.T)  # Transpose for better display
            
            # Ask if user wants to save to file
            save = input("\nWould you like to save this data to a file? (y/n): ").strip().lower()
            if save == 'y':
                # Ask for file format if not specified
                file_format = args.format
                if not file_format:
                    format_choice = input("Choose a file format (csv/excel): ").strip().lower()
                    file_format = format_choice if format_choice in ['csv', 'excel'] else 'csv'
                
                # Generate filename
                filename = os.path.join(
                    "output", 
                    f"{ticker}_financial_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                # Add extension
                filename += ".xlsx" if file_format == 'excel' else ".csv"
                
                # Save the file
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                if file_format == 'excel':
                    save_to_excel(df, filename)
                    print(f"Data saved to Excel file: {filename}")
                else:
                    save_to_csv(df, filename)
                    print(f"Data saved to CSV file: {filename}")
    else:
        if not args.ticker:
            print("Error: Please provide a ticker symbol with --ticker or use --interactive mode")
            sys.exit(1)
            
        ticker = args.ticker.upper()
        logger.info(f"Starting scrape for {ticker}")
        data = run_scrapers(ticker, args.sources, logger)
        
        # Display results
        df = format_data_as_dataframe(data)
        print("\n" + "="*80)
        print(f"Financial Metrics for {ticker}")
        print("="*80)
        print(df.T)  # Transpose for better display
        
        # Save to file if output is specified
        if args.output:
            output_path = args.output
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Determine file format
            file_format = args.format
            if file_format == 'excel' or output_path.endswith('.xlsx') or output_path.endswith('.xls'):
                save_to_excel(df, output_path)
                print(f"Data saved to Excel file: {output_path}")
            else:
                save_to_csv(df, output_path)
                print(f"Data saved to CSV file: {output_path}")

if __name__ == "__main__":
    main()