"""
Utilities for comparing and analyzing multiple stocks
"""
import pandas as pd
import numpy as np
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def normalize_data(data_dict):
    """
    Normalize data from different sources into a consistent format
    
    Args:
        data_dict (dict): Dictionary with ticker symbols as keys and data dictionaries as values
    
    Returns:
        dict: Normalized data dictionary
    """
    normalized = {}
    
    # Define mappings for common metrics that might have different labels
    metric_mappings = {
        'P/E Ratio': ['P/E Ratio', 'PE Ratio', 'P/E', 'Price to Earnings'],
        'Forward P/E': ['Forward P/E', 'Fwd P/E', 'Forward PE'],
        'PEG Ratio': ['PEG Ratio', 'PEG', 'PE Growth'],
        'P/B Ratio': ['P/B Ratio', 'P/B', 'Price to Book'],
        'P/S Ratio': ['P/S Ratio', 'P/S', 'Price to Sales'],
        'EV/EBITDA': ['EV/EBITDA', 'Enterprise Value/EBITDA', 'EV to EBITDA'],
        'ROE': ['ROE', 'Return on Equity'],
        'ROA': ['ROA', 'Return on Assets'],
        'ROIC': ['ROIC', 'Return on Invested Capital', 'Return on Capital'],
        'Profit Margin': ['Profit Margin', 'Net Margin'],
        'Operating Margin': ['Operating Margin', 'EBIT Margin'],
        'EPS': ['EPS', 'Earnings Per Share'],
        'Current Price': ['Current Price', 'Price', 'Last Price'],
        'RSI': ['RSI (14)', 'RSI', 'Relative Strength Index'],
        'Beta': ['Beta']
    }
    
    for ticker, stock_data in data_dict.items():
        normalized[ticker] = {
            'Ticker': ticker,
            'Data Timestamp': stock_data.get('Data Timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        }
        
        # Process each metric type
        for normalized_name, possible_names in metric_mappings.items():
            for key in stock_data:
                if any(name in key for name in possible_names):
                    # Try to convert string values to numeric
                    try:
                        # Remove % and convert to float
                        value = stock_data[key]
                        if isinstance(value, str):
                            if '%' in value:
                                value = value.replace('%', '')
                            value = float(value)
                        normalized[ticker][normalized_name] = value
                        break
                    except (ValueError, TypeError):
                        normalized[ticker][normalized_name] = stock_data[key]
                        break
    
    return normalized

def create_comparison_dataframe(data_dict):
    """
    Create a DataFrame for comparing stocks
    
    Args:
        data_dict (dict): Dictionary with ticker symbols as keys and data dictionaries as values
    
    Returns:
        pandas.DataFrame: DataFrame with comparison data
    """
    # Normalize the data first
    normalized = normalize_data(data_dict)
    
    # Convert to DataFrame
    rows = []
    for ticker, data in normalized.items():
        rows.append(data)
    
    df = pd.DataFrame(rows)
    
    # Set ticker as index
    if 'Ticker' in df.columns:
        df.set_index('Ticker', inplace=True)
    
    return df

def create_metric_charts(df, columns, title, pdf):
    """
    Create charts for a set of metrics and add to PDF
    
    Args:
        df (pandas.DataFrame): DataFrame with comparison data
        columns (list): List of column names to chart
        title (str): Title for the page
        pdf (PdfPages): PDF object to add the page to
    """
    plt.figure(figsize=(8.5, 11))
    plt.suptitle(title, fontsize=16, y=0.98)
    
    # Calculate grid dimensions based on number of metrics
    n_metrics = len(columns)
    n_cols = 2  # Use 2 columns
    n_rows = (n_metrics + 1) // 2  # Calculate rows needed
    
    for i, metric in enumerate(columns):
        if metric in df.columns:
            plt.subplot(n_rows, n_cols, i + 1)
            
            # Convert to numeric if possible
            values = pd.to_numeric(df[metric], errors='coerce')
            
            # Create bar chart
            values.plot(kind='bar', color='skyblue')
            plt.title(metric)
            plt.xticks(rotation=45)
            plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust for suptitle
    
    pdf.savefig()
    plt.close()

def generate_comparison_report(data_dict, output_path):
    """
    Generate a comprehensive comparison report for multiple stocks
    
    Args:
        data_dict (dict): Dictionary with ticker symbols as keys and data dictionaries as values
        output_path (str): Path to save the report
        
    Returns:
        str: Path to the saved report
    """
    # Create comparison DataFrame
    df = create_comparison_dataframe(data_dict)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Determine file type based on extension
    ext = os.path.splitext(output_path)[1].lower()
    
    if ext == '.xlsx':
        # Save as Excel
        writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
        
        # Main comparison sheet
        df.to_excel(writer, sheet_name='Comparison')
        
        # Add sheet with valuation metrics
        valuation_cols = [col for col in df.columns if any(x in col for x in 
                         ['P/E', 'PEG', 'P/B', 'P/S', 'EV/EBITDA'])]
        if valuation_cols:
            df[valuation_cols].to_excel(writer, sheet_name='Valuation Metrics')
        
        # Add sheet with profitability metrics
        profit_cols = [col for col in df.columns if any(x in col for x in 
                      ['ROE', 'ROA', 'ROIC', 'Margin'])]
        if profit_cols:
            df[profit_cols].to_excel(writer, sheet_name='Profitability')
        
        # Add sheet with technical indicators
        tech_cols = [col for col in df.columns if any(x in col for x in 
                    ['RSI', 'Moving Average', 'MACD', 'Bollinger', 'Volume'])]
        if tech_cols:
            df[tech_cols].to_excel(writer, sheet_name='Technical Indicators')
        
        writer.close()
        return output_path
        
    elif ext == '.csv':
        # Save as CSV
        df.to_csv(output_path)
        return output_path
        
    elif ext == '.pdf':
        # Create a PDF report with charts
        with PdfPages(output_path) as pdf:
            # Title page
            plt.figure(figsize=(8.5, 11))
            plt.text(0.5, 0.5, 'Stock Comparison Report', 
                     ha='center', va='center', fontsize=24)
            plt.text(0.5, 0.45, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 
                     ha='center', va='center', fontsize=14)
            plt.text(0.5, 0.40, f'Comparing: {", ".join(data_dict.keys())}', 
                     ha='center', va='center', fontsize=14)
            plt.axis('off')
            pdf.savefig()
            plt.close()
            
            # Valuation metrics page
            valuation_cols = [col for col in df.columns if any(x in col for x in 
                             ['P/E', 'PEG', 'P/B', 'P/S', 'EV/EBITDA'])]
            if valuation_cols:
                create_metric_charts(df, valuation_cols, 'Valuation Metrics', pdf)
            
            # Profitability metrics page
            profit_cols = [col for col in df.columns if any(x in col for x in 
                          ['ROE', 'ROA', 'ROIC', 'Margin'])]
            if profit_cols:
                create_metric_charts(df, profit_cols, 'Profitability Metrics', pdf)
            
            # Technical indicators page
            tech_cols = [col for col in df.columns if any(x in col for x in 
                        ['RSI', 'Moving Average', 'MACD', 'Bollinger', 'Volume'])]
            if tech_cols:
                create_metric_charts(df, tech_cols, 'Technical Indicators', pdf)
            
            # Create a table with all metrics
            plt.figure(figsize=(8.5, 11))
            plt.suptitle('Comparison Table', fontsize=16, y=0.98)
            
            # Create a table at the center of the page
            ax = plt.subplot(111)
            ax.axis('off')
            tbl = ax.table(
                cellText=df.reset_index().values,
                colLabels=df.reset_index().columns,
                loc='center',
                cellLoc='center',
                colColours=['#f2f2f2']*len(df.reset_index().columns)
            )
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(8)
            tbl.scale(1, 1.5)
            
            pdf.savefig()
            plt.close()
        
        return output_path
    
    else:
        # Default to text file
        with open(output_path, 'w') as f:
            f.write("="*80 + "\n")
            f.write(f"Stock Comparison Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            f.write(f"Comparing: {', '.join(data_dict.keys())}\n\n")
            f.write(df.to_string())
            f.write("\n\n")
            
            # Add sections for different metric groups
            f.write("-"*80 + "\n")
            f.write("VALUATION METRICS\n")
            f.write("-"*80 + "\n")
            valuation_cols = [col for col in df.columns if any(x in col for x in 
                             ['P/E', 'PEG', 'P/B', 'P/S', 'EV/EBITDA'])]
            if valuation_cols:
                f.write(df[valuation_cols].to_string())
                f.write("\n\n")
            
            f.write("-"*80 + "\n")
            f.write("PROFITABILITY METRICS\n")
            f.write("-"*80 + "\n")
            profit_cols = [col for col in df.columns if any(x in col for x in 
                          ['ROE', 'ROA', 'ROIC', 'Margin'])]
            if profit_cols:
                f.write(df[profit_cols].to_string())
                f.write("\n\n")
            
            f.write("-"*80 + "\n")
            f.write("TECHNICAL INDICATORS\n")
            f.write("-"*80 + "\n")
            tech_cols = [col for col in df.columns if any(x in col for x in 
                        ['RSI', 'Moving Average', 'MACD', 'Bollinger', 'Volume'])]
            if tech_cols:
                f.write(df[tech_cols].to_string())
                f.write("\n\n")
        
        return output_path

def rank_stocks(data_dict, metrics=None, ascending=None):
    """
    Rank stocks based on selected metrics
    
    Args:
        data_dict (dict): Dictionary with ticker symbols as keys and data dictionaries as values
        metrics (list, optional): List of metrics to use for ranking. If None, use default metrics.
        ascending (list, optional): List of booleans indicating sort order for each metric.
                                   If None, use default sort orders.
    
    Returns:
        pandas.DataFrame: DataFrame with ranking results
    """
    # Default metrics if none provided
    if metrics is None:
        metrics = ['P/E Ratio', 'PEG Ratio', 'ROE', 'Profit Margin', 'EPS']
    
    # Default sort orders (True = low values are better, False = high values are better)
    if ascending is None:
        ascending = {
            'P/E Ratio': True,     # Lower is better
            'PEG Ratio': True,     # Lower is better
            'P/B Ratio': True,     # Lower is better
            'P/S Ratio': True,     # Lower is better
            'EV/EBITDA': True,     # Lower is better
            'ROE': False,          # Higher is better
            'ROA': False,          # Higher is better
            'ROIC': False,         # Higher is better
            'Profit Margin': False, # Higher is better
            'Operating Margin': False, # Higher is better
            'EPS': False,          # Higher is better
            'RSI': None,           # Middle values (40-60) are better
            'Beta': None           # Depends on risk preference
        }
    
    # Create comparison DataFrame
    df = create_comparison_dataframe(data_dict)
    
    # Calculate rankings for each metric
    rankings = pd.DataFrame(index=df.index)
    rankings['Overall Score'] = 0
    
    for metric in metrics:
        if metric in df.columns:
            # Convert to numeric, replacing non-numeric values with NaN
            values = pd.to_numeric(df[metric], errors='coerce')
            
            # Skip if all values are NaN
            if values.isna().all():
                continue
            
            # Determine sort order
            asc = ascending.get(metric, True)
            
            # Special handling for RSI
            if metric == 'RSI' and asc is None:
                # Calculate distance from ideal RSI (50)
                distance_from_ideal = abs(values - 50)
                rankings[f'{metric} Rank'] = distance_from_ideal.rank()
            else:
                # Rank values (handle NaN by assigning max rank + 1)
                rankings[f'{metric} Rank'] = values.rank(ascending=asc, na_option='bottom')
            
            # Add to overall score (lower rank is better)
            rankings['Overall Score'] += rankings[f'{metric} Rank']
    
    # Calculate overall rank
    rankings['Overall Rank'] = rankings['Overall Score'].rank()
    
    # Sort by overall rank
    rankings = rankings.sort_values('Overall Rank')
    
    # Add original values for reference
    for metric in metrics:
        if metric in df.columns:
            rankings[metric] = df[metric]
    
    return rankings

def create_screener(data_dict, criteria):
    """
    Screen stocks based on specified criteria
    
    Args:
        data_dict (dict): Dictionary with ticker symbols as keys and data dictionaries as values
        criteria (dict): Dictionary of criteria for screening
                        Format: {'metric': ('operator', value)}
                        Operators: '>', '<', '>=', '<=', '==', '!='
    
    Returns:
        pandas.DataFrame: DataFrame with filtered stocks
    """
    # Create comparison DataFrame
    df = create_comparison_dataframe(data_dict)
    
    # Apply each criterion as a filter
    for metric, (operator, value) in criteria.items():
        if metric not in df.columns:
            print(f"Warning: Metric '{metric}' not found, skipping this criterion")
            continue
        
        # Convert column to numeric
        df[metric] = pd.to_numeric(df[metric], errors='coerce')
        
        # Apply filter based on operator
        if operator == '>':
            df = df[df[metric] > value]
        elif operator == '<':
            df = df[df[metric] < value]
        elif operator == '>=':
            df = df[df[metric] >= value]
        elif operator == '<=':
            df = df[df[metric] <= value]
        elif operator == '==':
            df = df[df[metric] == value]
        elif operator == '!=':
            df = df[df[metric] != value]
        else:
            print(f"Warning: Operator '{operator}' not recognized, skipping this criterion")
    
    return df