"""
Request handler module to handle HTTP requests with connection pooling
"""
import logging
import os
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Global session instance for connection pooling
_session = None

def create_session():
    """
    Create a requests session with connection pooling and retry strategy
    
    Returns:
        requests.Session: Configured session with connection pooling
    """
    session = requests.Session()
    
    # Get pool settings from environment or use defaults
    pool_connections = int(os.environ.get('CONNECTION_POOL_SIZE', 20))
    pool_maxsize = int(os.environ.get('CONNECTION_POOL_MAXSIZE', 20))
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    # Configure HTTP adapter with connection pooling
    adapter = HTTPAdapter(
        pool_connections=pool_connections,  # Use environment variable
        pool_maxsize=pool_maxsize,          # Use environment variable
        max_retries=retry_strategy,
        pool_block=False      # Don't block when pool is full
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set default headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                     '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    logger.info(f"Created session with connection pooling: {pool_connections} pools, {pool_maxsize} max connections each")
    
    return session

def get_session():
    """
    Get the global session instance (singleton pattern)
    
    Returns:
        requests.Session: Global session with connection pooling
    """
    global _session
    if _session is None:
        _session = create_session()
    return _session

def make_request(url, headers=None, timeout=10, retries=3, use_session=True):
    """
    Make an HTTP GET request with error handling, retries, and connection pooling
    
    Args:
        url (str): URL to request
        headers (dict, optional): HTTP headers to send with the request
        timeout (int, optional): Request timeout in seconds
        retries (int, optional): Number of retries for failed requests
        use_session (bool, optional): Whether to use session with connection pooling
        
    Returns:
        requests.Response: Response object
        
    Raises:
        RequestException: If the request fails after all retries
    """
    headers = headers or {}
    attempts = 0
    
    # Choose between session (with connection pooling) or direct requests
    request_func = get_session().get if use_session else requests.get
    
    while attempts < retries:
        try:
            if use_session:
                # Merge headers with session headers
                response = request_func(url, headers=headers, timeout=timeout)
            else:
                response = request_func(url, headers=headers, timeout=timeout)
            
            # Check if the request was successful
            if response.status_code == 200:
                logger.debug(f"Successfully fetched data from {url}")
                return response
                
            # If we got rate limited, retry after a delay
            if response.status_code == 429:
                logger.warning(f"Rate limited on {url}. Retrying... (attempt {attempts + 1}/{retries})")
                attempts += 1
                continue
                
            # For other status codes, raise an exception
            response.raise_for_status()
            
        except RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)} (attempt {attempts + 1}/{retries})")
            attempts += 1
            
            if attempts >= retries:
                raise RequestException(f"Failed to fetch data from {url} after {retries} attempts: {str(e)}")
                
    # This should not be reached due to the exception above
    raise RequestException(f"Failed to fetch data from {url}")

def close_session():
    """
    Close the global session and cleanup connections
    Should be called when shutting down the application
    """
    global _session
    if _session is not None:
        _session.close()
        _session = None
        logger.info("Session closed and connections cleaned up")