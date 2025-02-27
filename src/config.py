"""
Configuration settings for the stock scraper application
"""
import os
import logging
from logging.handlers import RotatingFileHandler

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Output directory for CSV files
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

# Data directory
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Logs directory
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# User agent for requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Request settings
REQUEST_TIMEOUT = 10
REQUEST_RETRIES = 3

# Delay between requests (in seconds)
REQUEST_DELAY = 1

# Configure logging
def setup_logging(log_level=logging.INFO):
    """
    Configure logging for the application
    
    Args:
        log_level (int): Logging level
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create file handler
    log_file = os.path.join(LOGS_DIR, 'stock_scraper.log')
    file_handler = RotatingFileHandler(
        log_file, maxBytes=1024*1024*5, backupCount=5
    )
    file_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Initialize logging
logger = setup_logging()