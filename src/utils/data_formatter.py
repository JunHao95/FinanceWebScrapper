"""
Data formatting utilities for the stock scraper
"""
import os
import pandas as pd

def format_data_as_dataframe(data):
    """
    Format the scraped data as a pandas DataFrame
    
    Args:
        data (dict): Dictionary containing scraped data
        
    Returns:
        pandas.DataFrame: DataFrame containing the formatted data
    """
    # Create a DataFrame with a single row
    df = pd.DataFrame([data])
    
    # Group metrics for better display
    grouped_data = {}
    
    # Define metric groups
    metric_groups = {
        "Basic Info": ["Ticker", "Data Timestamp"],
        "Valuation Ratios": [
            "P/E Ratio", "Forward P/E", "P/B Ratio", "P/S Ratio", 
            "PEG Ratio", "EV/EBITDA"
        ],
        "Profitability": [
            "ROE", "ROIC", "ROA", "Profit Margin", "Operating Margin"
        ],
        "Earnings": [
            "EPS", "EPS Estimate Current Year", "EPS Estimate Next Year",
            "EPS Growth This Year", "EPS Growth Next Year", "EPS Growth Next 5Y",
            "EPS Growth QoQ"
        ]
    }
    
    # Initialize the grouped DataFrame
    for group in metric_groups:
        grouped_data[group] = {}
        
    # Sort data into groups
    for key, value in data.items():
        # Skip any error messages
        if isinstance(value, dict) and "error" in value:
            continue
            
        # Skip metadata
        if key in ["Ticker", "Data Timestamp"]:
            grouped_data["Basic Info"][key] = value
            continue
            
        # Determine which group this metric belongs to
        assigned = False
        for group, metrics in metric_groups.items():
            for metric in metrics:
                if metric in key:
                    grouped_data[group][key] = value
                    assigned = True
                    break
            if assigned:
                break
                
        # If not assigned to any group, put it in a misc group
        if not assigned:
            if "Other Metrics" not in grouped_data:
                grouped_data["Other Metrics"] = {}
            grouped_data["Other Metrics"][key] = value
    
    # Convert grouped data to DataFrame
    result_df = pd.DataFrame([data])
    
    return result_df

def save_to_csv(df, file_path):
    """
    Save the DataFrame to a CSV file
    
    Args:
        df (pandas.DataFrame): DataFrame to save
        file_path (str): Path to the output file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save the DataFrame to CSV
        df.to_csv(file_path, index=False)
        return True
    except Exception as e:
        print(f"Error saving to CSV: {str(e)}")
        return False

def save_to_excel(df, file_path):
    """
    Save the DataFrame to an Excel file with better formatting
    
    Args:
        df (pandas.DataFrame): DataFrame to save
        file_path (str): Path to the output file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Create a writer
        writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
        
        # Transpose the DataFrame for better readability
        df_t = df.T.reset_index()
        df_t.columns = ['Metric', 'Value']
        
        # Write the DataFrame to Excel
        df_t.to_excel(writer, sheet_name='Metrics', index=False)
        
        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Metrics']
        
        # Add some formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Write the column headers with the defined format
        for col_num, value in enumerate(df_t.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Adjust column widths
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 15)
        
        # Save the workbook
        writer.save()
        return True
    except Exception as e:
        print(f"Error saving to Excel: {str(e)}")
        return False