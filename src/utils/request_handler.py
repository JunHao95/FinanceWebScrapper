"""
Request handler module to handle HTTP requests
"""
import logging
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

def make_request(url, headers=None, timeout=10, retries=3):
    """
    Make an HTTP GET request with error handling and retries
    
    Args:
        url (str): URL to request
        headers (dict, optional): HTTP headers to send with the request
        timeout (int, optional): Request timeout in seconds
        retries (int, optional): Number of retries for failed requests
        
    Returns:
        requests.Response: Response object
        
    Raises:
        RequestException: If the request fails after all retries
    """
    headers = headers or {}
    attempts = 0
    
    while attempts < retries:
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            
            # Check if the request was successful
            if response.status_code == 200:
                return response
                
            # If we got rate limited, retry after a delay
            if response.status_code == 429:
                logger.warning(f"Rate limited on {url}. Retrying...")
                attempts += 1
                continue
                
            # For other status codes, raise an exception
            response.raise_for_status()
            
        except RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            attempts += 1
            
            if attempts >= retries:
                raise RequestException(f"Failed to fetch data from {url} after {retries} attempts")
                
    # This should not be reached due to the exception above
    raise RequestException(f"Failed to fetch data from {url}")