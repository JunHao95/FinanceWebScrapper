"""
Display formatting utilities for the stock scraper results
"""
import pandas as pd
import os

def format_data_for_display(data, max_width=120):
    """
    Format data dictionary into a better organized display format
    
    Args:
        data (dict): Dictionary of financial metrics
        max_width (int): Maximum width for display
        
    Returns:
        str: Formatted string ready for display
    """
    # Group the metrics by category
    categories = {
        "Basic Info": [],
        "Valuation Ratios": [],
        "Profitability Metrics": [],
        "Earnings Metrics": [],
        "Moving Averages": [],
        "Bollinger Bands": [],
        "Momentum Indicators": [],
        "Volume Indicators": [],
        "Other Metrics": []
    }
    
    # Sort data into categories
    for key, value in data.items():
        if any(term in key for term in ["Ticker", "Timestamp", "Updated", "Name", "Sector", "Industry"]):
            categories["Basic Info"].append((key, value))
        elif any(term in key for term in ["P/E", "P/B", "P/S", "EV/EBITDA", "PEG", "Forward P/E"]):
            categories["Valuation Ratios"].append((key, value))
        elif any(term in key for term in ["ROE", "ROA", "ROIC", "Margin"]):
            categories["Profitability Metrics"].append((key, value))
        elif any(term in key for term in ["EPS", "Earnings"]):
            categories["Earnings Metrics"].append((key, value))
        elif any(term in key for term in ["MA", "EMA", "MACD"]):
            categories["Moving Averages"].append((key, value))
        elif any(term in key for term in ["BB ", "Band"]):
            categories["Bollinger Bands"].append((key, value))
        elif any(term in key for term in ["RSI", "Signal"]):
            categories["Momentum Indicators"].append((key, value))
        elif any(term in key for term in ["Volume", "OBV"]):
            categories["Volume Indicators"].append((key, value))
        else:
            categories["Other Metrics"].append((key, value))
    
    # Build the output
    output = []
    
    # Terminal width detection for better formatting
    try:
        terminal_width = os.get_terminal_size().columns
        max_width = min(max_width, terminal_width)
    except (OSError, AttributeError):
        pass  # Use default max_width
    
    # Process each category
    for category, items in categories.items():
        if not items:
            continue
            
        output.append(f"\n{category}:")
        output.append("-" * len(category))
        
        # Create a table for this category
        metric_width = min(60, max_width - 20)
        value_width = max_width - metric_width - 3
        
        # Format as a simple table
        for key, value in sorted(items):
            # Truncate long keys
            if len(key) > metric_width:
                display_key = key[:metric_width-3] + "..."
            else:
                display_key = key
                
            # Format the line
            line = f"{display_key:{metric_width}} | {str(value)[:value_width]}"
            output.append(line)
        
    return "\n".join(output)

def print_grouped_metrics(data):
    """
    Print financial metrics grouped by category
    
    Args:
        data (dict): Dictionary of financial metrics
    """
    try:
        # Try to import tabulate for prettier tables
        from tabulate import tabulate
        
        # Group the metrics by category
        categories = {
            "Basic Info": [],
            "Valuation Ratios": [],
            "Profitability Metrics": [],
            "Earnings Metrics": [],
            "Moving Averages": [],
            "Bollinger Bands": [],
            "Momentum Indicators": [],
            "Volume Indicators": [],
            "Other Metrics": []
        }
        
        # Sort data into categories
        for key, value in data.items():
            if any(term in key for term in ["Ticker", "Timestamp", "Updated", "Name", "Sector", "Industry"]):
                categories["Basic Info"].append((key, value))
            elif any(term in key for term in ["P/E", "P/B", "P/S", "EV/EBITDA", "PEG", "Forward P/E"]):
                categories["Valuation Ratios"].append((key, value))
            elif any(term in key for term in ["ROE", "ROA", "ROIC", "Margin"]):
                categories["Profitability Metrics"].append((key, value))
            elif any(term in key for term in ["EPS", "Earnings"]):
                categories["Earnings Metrics"].append((key, value))
            elif any(term in key for term in ["MA", "EMA", "MACD"]):
                categories["Moving Averages"].append((key, value))
            elif any(term in key for term in ["BB ", "Band"]):
                categories["Bollinger Bands"].append((key, value))
            elif any(term in key for term in ["RSI", "Signal"]):
                categories["Momentum Indicators"].append((key, value))
            elif any(term in key for term in ["Volume", "OBV"]):
                categories["Volume Indicators"].append((key, value))
            else:
                categories["Other Metrics"].append((key, value))
        
        # Process each category
        for category, items in categories.items():
            if not items:
                continue
                
            print(f"\n{category}:")
            print("-" * len(category))
            
            # Create a table for this category
            table_data = []
            for key, value in sorted(items):
                table_data.append([key, value])
            
            # Print as table
            print(tabulate(table_data, headers=["Metric", "Value"], tablefmt="simple"))
    
    except ImportError:
        # Fall back to simple formatting if tabulate is not available
        formatted = format_data_for_display(data)
        print(formatted)

def save_formatted_report(data, filename):
    """
    Save a nicely formatted report to a text file
    
    Args:
        data (dict): Dictionary of financial metrics
        filename (str): Path to output file
    """
    formatted_output = format_data_for_display(data, max_width=100)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Write to file
    with open(filename, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write(f"Financial Metrics Report for {data.get('Ticker', 'Unknown')}\n")
        f.write("=" * 80 + "\n")
        f.write(formatted_output)
        f.write("\n\n")
        f.write(f"Generated on: {data.get('Data Timestamp', '')}\n")