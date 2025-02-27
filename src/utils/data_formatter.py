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
    
    return df

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