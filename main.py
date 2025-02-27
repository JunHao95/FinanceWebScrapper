#!/usr/bin/env python3
"""
Stock Data Scraper - Main Application Entry Point
"""
import os
import sys
import argparse
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from src.scrapers.yahoo_scraper import YahooFinanceScraper
from src.scrapers.finviz_scraper import FinvizScraper
from src.scrapers.google_scraper import GoogleFinanceScraper
from src.scrapers.marketwatch_scraper import MarketWatchScraper
from src.utils.data_formatter import format_data_as_dataframe, save_to_csv

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Stock Financial Metrics Scraper")
    parser.add_argument('--ticker', type=str, help="Stock ticker symbol to scrape")
    parser.add_argument('--output', type=str, help="Output CSV file path")
    parser.add_argument('--sources', type=str, nargs='+', 
                      choices=['yahoo', 'finviz', 'google', 'marketwatch', 'all'],
                      default=['all'], help="Data sources to scrape from")
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

def run_scrapers(ticker, sources):
    """Run the selected scrapers and combine results"""
    results = {"Ticker": ticker, "Data Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    if 'all' in sources or 'yahoo' in sources:
        print(f"Scraping Yahoo Finance data for {ticker}...")
        yahoo_scraper = YahooFinanceScraper()
        results.update(yahoo_scraper.get_data(ticker))
    
    if 'all' in sources or 'finviz' in sources:
        print(f"Scraping Finviz data for {ticker}...")
        finviz_scraper = FinvizScraper()
        results.update(finviz_scraper.get_data(ticker))
    
    if 'all' in sources or 'google' in sources:
        print(f"Scraping Google Finance data for {ticker}...")
        google_scraper = GoogleFinanceScraper()
        results.update(google_scraper.get_data(ticker))
    
    if 'all' in sources or 'marketwatch' in sources:
        print(f"Scraping MarketWatch data for {ticker}...")
        marketwatch_scraper = MarketWatchScraper()
        results.update(marketwatch_scraper.get_data(ticker))
    
    # Filter out any error messages
    results = {k: v for k, v in results.items() if not isinstance(v, dict) or "error" not in v}
    
    return results

def main():
    """Main application entry point"""
    print("="*80)
    print("Stock Financial Metrics Scraper")
    print("="*80)
    print("This program scrapes key financial ratios from multiple sources.")
    
    args = parse_arguments()
    
    if args.interactive:
        while True:
            ticker = get_ticker_interactively()
            data = run_scrapers(ticker, args.sources)
            
            # Display results
            df = format_data_as_dataframe(data)
            print("\n" + "="*80)
            print(f"Financial Metrics for {ticker}")
            print("="*80)
            print(df.T)  # Transpose for better display
            
            # Ask if user wants to save to CSV
            save = input("\nWould you like to save this data to CSV? (y/n): ").strip().lower()
            if save == 'y':
                filename = os.path.join(
                    "output", 
                    f"{ticker}_financial_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                save_to_csv(df, filename)
                print(f"Data saved to {filename}")
    else:
        if not args.ticker:
            print("Error: Please provide a ticker symbol with --ticker or use --interactive mode")
            sys.exit(1)
            
        ticker = args.ticker.upper()
        data = run_scrapers(ticker, args.sources)
        
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
            save_to_csv(df, output_path)
            print(f"Data saved to {output_path}")

if __name__ == "__main__":
    main()