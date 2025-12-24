"""
Technical Indicators Module for Stock Analysis

This module supports two Alpha Vantage API modes for fetching stock data:

1. TIME_SERIES_DAILY (Free Tier):
   - Uses Alpha Vantage's TIME_SERIES_DAILY endpoint
   - Available with free API keys (25 requests/day, 5 requests/minute)
   - Provides historical daily OHLCV data
   - Recommended for most users

2. REALTIME_BULK_QUOTES (Premium):
   - Uses Alpha Vantage's REALTIME_BULK_QUOTES endpoint
   - Requires premium subscription (600+ requests/minute plans)
   - Supports up to 100 symbols per request
   - Provides real-time quote data
   - Falls back to Yahoo Finance for historical data

Configuration:
- Set mode in config.json under alpha_vantage.mode
- Always enable fallback_to_yahoo for reliability
- Yahoo Finance and Finnhub serve as fallback data sources

Note: The old BATCH_STOCK_QUOTES endpoint referenced in some documentation
does not exist in Alpha Vantage's API. Use REALTIME_BULK_QUOTES instead.
"""
import numpy as np
import pandas as pd
import requests
import os
import logging
import time
from datetime import datetime, timedelta
import yfinance as yf
from pandas_datareader import data as pdr
from ..utils.request_handler import make_request
from ..utils.mongodb_storage import MongoDBStorage

class TechnicalIndicators:
    """
    Class to calculate and retrieve technical indicators for stocks
    """
    
    def __init__(self, api_key=None, config=None):
        """
        Initialize the technical indicators module
        
        Args:
            api_key (str): Alpha Vantage API key. If None, will try to get from ALPHA_VANTAGE_API_KEY environment variable
            config (dict): Configuration options for Alpha Vantage mode and settings
        """
        self.api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY")
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load configuration with defaults
        self.config = config or {}
        self.alpha_vantage_config = self.config.get('alpha_vantage', {})
        
        # Configuration options
        self.mode = self.alpha_vantage_config.get('mode', 'time_series_daily')
        self.fallback_to_yahoo = self.alpha_vantage_config.get('fallback_to_yahoo', True)
        self.batch_size = self.alpha_vantage_config.get('batch_size', 100)
        self.enable_retry_on_rate_limit = self.alpha_vantage_config.get('enable_retry_on_rate_limit', True)
        
        # MongoDB configuration
        mongodb_config = self.config.get('mongodb', {})
        self.enable_mongodb = mongodb_config.get('enabled', True)
        mongodb_connection = mongodb_config.get('connection_string', 'mongodb://localhost:27017/')
        mongodb_database = mongodb_config.get('database', 'stock_data')
        
        # Initialize MongoDB storage
        if self.enable_mongodb:
            try:
                self.mongodb = MongoDBStorage(mongodb_connection, mongodb_database)
                self.logger.info("MongoDB storage initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize MongoDB storage: {str(e)}")
                self.mongodb = None
        else:
            self.mongodb = None
            self.logger.info("MongoDB storage is disabled in configuration")
        
        if not self.api_key:
            self.logger.warning("Alpha Vantage API key not provided. Set ALPHA_VANTAGE_API_KEY environment variable.")
            
        self.logger.info(f"Initialized with mode: {self.mode}, fallback_to_yahoo: {self.fallback_to_yahoo}")
        
        # Mode validation and helpful error messages
        valid_modes = ['realtime_bulk_quotes', 'time_series_daily']
        if self.mode not in valid_modes:
            self.logger.warning(f"Invalid mode '{self.mode}'. Using 'time_series_daily' as default.")
            self.mode = 'time_series_daily'
        
        # Provide helpful information about API modes
        if self.mode == 'realtime_bulk_quotes':
            self.logger.info("Using REALTIME_BULK_QUOTES mode - requires premium Alpha Vantage subscription")
        else:
            self.logger.info("Using TIME_SERIES_DAILY mode - available with free Alpha Vantage tier")
    
    def get_historical_data(self, ticker: str, days: int = 100) -> pd.DataFrame:
        """
        Retrieve historical price data for a ticker with configurable Alpha Vantage mode.

        Args:
            ticker (str): Stock ticker symbol.
            days (int): Number of days of historical data to fetch.

        Returns:
            pandas.DataFrame: DataFrame containing the historical data.
        """
        df = pd.DataFrame()
        
        # Choose strategy based on configuration
        if self.mode == 'realtime_bulk_quotes' and self.api_key:
            self.logger.info(f"Using realtime bulk quotes mode for {ticker}")
            df = self._fetch_with_realtime_bulk_quotes(ticker, days)
            if not df.empty:
                # Store in MongoDB if enabled
                self._store_to_mongodb(ticker, df)
                return df
            
            # If bulk quotes fail and fallback is enabled, try time series
            if self.fallback_to_yahoo:
                self.logger.info(f"Realtime bulk quotes failed for {ticker}, falling back to time series")
                df = self._fetch_with_time_series(ticker, days)
                if not df.empty:
                    # Store in MongoDB if enabled
                    self._store_to_mongodb(ticker, df)
                    return df
        
        elif self.mode == 'time_series_daily' and self.api_key:
            self.logger.info(f"Using time series daily mode for {ticker}")
            df = self._fetch_with_time_series(ticker, days)
            if not df.empty:
                # Store in MongoDB if enabled
                self._store_to_mongodb(ticker, df)
                return df
        
        # Fallback to Yahoo Finance if Alpha Vantage fails or no API key
        if self.fallback_to_yahoo:
            self.logger.info(f"Alpha Vantage failed or not configured, trying Yahoo Finance for {ticker}")
            df = self._fetch_yahoo_finance_data(ticker, days)
            if not df.empty:
                # Store in MongoDB if enabled
                self._store_to_mongodb(ticker, df)
                return df
        
        # Try Finnhub as last backup
        self.logger.info("Yahoo Finance failed, trying Finnhub API...")
        df = self._fetch_finnhub_data(ticker, days)
        if not df.empty:
            # Store in MongoDB if enabled
            self._store_to_mongodb(ticker, df)
            return df
            
        # If all APIs fail
        self.logger.error("All APIs failed. Unable to fetch historical data.")
        return pd.DataFrame()
    
    def _store_to_mongodb(self, ticker: str, df: pd.DataFrame):
        """
        Store time series data to MongoDB if enabled
        
        Args:
            ticker (str): Stock ticker symbol
            df (pandas.DataFrame): DataFrame with historical data
        """
        if self.mongodb and not df.empty:
            try:
                self.mongodb.store_timeseries_data(ticker, df)
            except Exception as e:
                self.logger.warning(f"Failed to store data to MongoDB for {ticker}: {str(e)}")
    
    def _fetch_with_realtime_bulk_quotes(self, ticker: str, days: int) -> pd.DataFrame:
        """
        Fetch data using Alpha Vantage realtime bulk quotes (current data only).
        For historical data, will supplement with Yahoo Finance.
        
        Args:
            ticker (str): Stock ticker symbol.
            days (int): Number of days (used for fallback to Yahoo Finance).
            
        Returns:
            pandas.DataFrame: DataFrame containing the data.
        """
        # Get current quote via realtime bulk API
        bulk_data = self.fetch_realtime_bulk_alpha_vantage_quotes([ticker])
        
        if bulk_data and ticker in bulk_data:
            current_quote = bulk_data[ticker]
            
            # For technical analysis, we need historical data
            # Use Yahoo Finance to get historical data and update latest price
            self.logger.info(f"Got current quote for {ticker}, fetching historical data from Yahoo Finance")
            df = self._fetch_yahoo_finance_data(ticker, days)
            
            if not df.empty:
                # Update the most recent price with Alpha Vantage data
                latest_date = df.index[0]
                df.loc[latest_date, 'close'] = current_quote['price']
                df.loc[latest_date, 'volume'] = current_quote['volume']
                # Keep other OHLC values from Yahoo Finance for historical context
                
                self.logger.info(f"Successfully combined Alpha Vantage current price with Yahoo Finance historical data for {ticker}")
                return df
        
        return pd.DataFrame()
    
    def _fetch_with_time_series(self, ticker: str, days: int) -> pd.DataFrame:
        """
        Fetch data using Alpha Vantage time series daily.
        
        Args:
            ticker (str): Stock ticker symbol.
            days (int): Number of days of historical data to fetch.
            
        Returns:
            pandas.DataFrame: DataFrame containing the data.
        """
        try:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={self.api_key}"
            self.logger.info(f"Fetching time series data from Alpha Vantage for {ticker}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for rate limit message
            if 'Note' in data and 'rate limit' in data['Note'].lower():
                self.logger.warning(f"Alpha Vantage rate limit hit for {ticker}")
                if self.enable_retry_on_rate_limit:
                    self.logger.info(f"Rate limit detected, checking if reset occurred...")
                    time.sleep(2)  # Brief pause
                    response = requests.get(url, timeout=30)
                    data = response.json()
                    if 'Time Series (Daily)' not in data:
                        self.logger.error(f"Rate limit still active for {ticker}")
                        return pd.DataFrame()
                else:
                    return pd.DataFrame()
            
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                df_data = []
                for date_str, values in time_series.items():
                    df_data.append({
                        'Date': pd.to_datetime(date_str),
                        'open': float(values['1. open']),
                        'high': float(values['2. high']),
                        'low': float(values['3. low']),
                        'close': float(values['4. close']),
                        'volume': int(values['5. volume'])
                    })
                
                df = pd.DataFrame(df_data)
                df.set_index('Date', inplace=True)
                df.sort_index(ascending=False, inplace=True)
                
                # Limit to requested days
                df = df.head(days)
                
                return df if len(df) > 0 else pd.DataFrame()
            
            else:
                self.logger.error(f"No time series data returned from Alpha Vantage. Response: {data}")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"Alpha Vantage time series API error: {str(e)}")
            return pd.DataFrame()

    def fetch_realtime_bulk_alpha_vantage_quotes(self, symbols):
        """Fetch current quotes for multiple symbols using the realtime bulk quotes API"""
        try:
            # Join symbols with commas (max 100 symbols)
            symbol_list = ','.join(symbols[:100])  # Limit to 100 symbols
            url = f"https://www.alphavantage.co/query?function=REALTIME_BULK_QUOTES&symbol={symbol_list}&apikey={self.api_key}"
            
            self.logger.info(f"Fetching realtime bulk quotes from Alpha Vantage for {len(symbols)} symbols")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for rate limit
            if 'Note' in data and 'rate limit' in data['Note'].lower():
                self.logger.error(f"Alpha Vantage rate limit hit for realtime bulk request")
                return None
            
            # Check for premium function error
            if 'Error Message' in data and 'premium' in data['Error Message'].lower():
                self.logger.error(f"REALTIME_BULK_QUOTES requires premium subscription: {data['Error Message']}")
                return None
            
            # Check for function error
            if 'Error Message' in data:
                self.logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return None
            
            if 'data' in data:
                quotes_data = {}
                for quote in data['data']:
                    symbol = quote['symbol']
                    quotes_data[symbol] = {
                        'price': float(quote['price']),
                        'volume': int(quote['volume']) if quote['volume'] and quote['volume'] != 'N/A' else 0,
                        'timestamp': quote['timestamp']
                    }
                self.logger.info(f"Successfully fetched realtime bulk quotes for {len(quotes_data)} symbols")
                return quotes_data
            else:
                self.logger.error(f"No realtime bulk quotes returned. Response: {data}")
                return None
                
        except Exception as e:
            self.logger.error(f"Alpha Vantage realtime bulk API error: {str(e)}")
            return None

    def get_bulk_data_for_multiple_symbols(self, symbols):
        """
        Fetch data for multiple symbols using the configured mode.
        
        Args:
            symbols (list): List of stock ticker symbols.
            
        Returns:
            dict: Dictionary with symbol as key and DataFrame as value.
        """
        results = {}
        
        if self.mode == 'realtime_bulk_quotes' and self.api_key:
            self.logger.info(f"Fetching bulk data for {len(symbols)} symbols using realtime bulk quotes")
            
            # Split symbols into batches
            batches = [symbols[i:i + self.batch_size] for i in range(0, len(symbols), self.batch_size)]
            
            for batch in batches:
                bulk_data = self.fetch_realtime_bulk_alpha_vantage_quotes(batch)
                
                if bulk_data:
                    # For each symbol in the batch, get historical data and update with current price
                    for symbol in batch:
                        if symbol in bulk_data:
                            if self.fallback_to_yahoo:
                                # Get historical data from Yahoo Finance
                                df = self._fetch_yahoo_finance_data(symbol, 100)
                                if not df.empty:
                                    # Update latest price with Alpha Vantage data
                                    current_quote = bulk_data[symbol]
                                    latest_date = df.index[0]
                                    df.loc[latest_date, 'close'] = current_quote['price']
                                    df.loc[latest_date, 'volume'] = current_quote['volume']
                                    results[symbol] = df
                                else:
                                    # Create minimal DataFrame with current data only
                                    current_quote = bulk_data[symbol]
                                    df = pd.DataFrame({
                                        'close': [current_quote['price']],
                                        'volume': [current_quote['volume']],
                                        'open': [current_quote['price']],
                                        'high': [current_quote['price']],
                                        'low': [current_quote['price']]
                                    }, index=[pd.to_datetime(current_quote['timestamp'])])
                                    results[symbol] = df
                        else:
                            # If symbol not in bulk response, try individual fetch
                            df = self.get_historical_data(symbol)
                            if not df.empty:
                                results[symbol] = df
                else:
                    # If bulk request failed, fall back to individual requests
                    for symbol in batch:
                        df = self.get_historical_data(symbol)
                        if not df.empty:
                            results[symbol] = df
        else:
            # Use individual requests for each symbol
            for symbol in symbols:
                df = self.get_historical_data(symbol)
                if not df.empty:
                    results[symbol] = df
        
        self.logger.info(f"Successfully fetched data for {len(results)} out of {len(symbols)} symbols")
        return results
    def _fetch_finnhub_data(self, ticker: str, days: int) -> pd.DataFrame:
        """
        Fetch historical data from Finnhub API.

        Args:
            ticker (str): Stock ticker symbol.
            days (int): Number of days of historical data to fetch.

        Returns:
            pandas.DataFrame: DataFrame containing the historical data.
        """
        finnhub_api_key = os.environ.get("FINHUB_API_KEY")
        if not finnhub_api_key:
            self.logger.error("Finnhub API key not available. Cannot fetch historical data.")
            return pd.DataFrame()

        url = f"https://finnhub.io/api/v1/stock/candle?symbol={ticker}&resolution=D&count={days}&token={finnhub_api_key}"
        self.logger.info(f"Fetching data from Finnhub: {url}")

        try:
            response = make_request(url, timeout=10)
            data = response.json()

            if "error" in data:
                self.logger.error(f"Finnhub API error: {data['error']}")
                return pd.DataFrame()

            if "c" not in data:
                self.logger.error("No data returned from Finnhub API.")
                return pd.DataFrame()

            return self._convert_finnhub_to_dataframe(data)

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Finnhub API request failed: {str(e)}")
            return pd.DataFrame()   
    def _convert_alpha_vantage_to_dataframe(self, time_series: dict, days: int) -> pd.DataFrame:
        """
        Convert Alpha Vantage time series data to a DataFrame.

        Args:
            time_series (dict): Time series data from Alpha Vantage.
            days (int): Number of days of historical data to fetch.

        Returns:
            pandas.DataFrame: DataFrame containing the historical data.
        """
        df = pd.DataFrame.from_dict(time_series, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.rename(columns={
            '1. open': 'open',
            '2. high': 'high',
            '3. low': 'low',
            '4. close': 'close',
            '5. volume': 'volume'
        })
        df = df.astype(float)
        df.sort_index(ascending=False, inplace=True)
        df = df.head(days)
        df = df.ffill()  # Forward fill NaN values
        return df

    def _fetch_yahoo_finance_data(self, ticker: str, days: int) -> pd.DataFrame:
        """
        Fetch historical data from Yahoo Finance.

        Args:
            ticker (str): Stock ticker symbol.
            days (int): Number of days of historical data to fetch.

        Returns:
            pandas.DataFrame: DataFrame containing the historical data.
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            self.logger.info(f"Fetching data from Yahoo Finance for {ticker} from {start_date} to {end_date}.")

            df = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), auto_adjust=False)
            if df is None or df.empty:
                self.logger.warning(f"No data returned from Yahoo Finance for {ticker}.")
                return pd.DataFrame()

            # Handle MultiIndex columns (when downloading single ticker, yfinance sometimes returns MultiIndex)
            if isinstance(df.columns, pd.MultiIndex):
                # Flatten the MultiIndex columns - take the first level (the price type)
                df.columns = df.columns.get_level_values(0)
            
            # Debug logging to understand data structure
            self.logger.debug(f"Yahoo Finance data for {ticker} - Shape: {df.shape}, Columns: {df.columns.tolist()}")
            
            # Rename columns to match the standard format
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Ensure we have the expected columns
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"Missing columns in Yahoo Finance data for {ticker}: {missing_columns}")
                return pd.DataFrame()
            
            # Make sure all columns are proper Series (not DataFrames)
            for col in required_columns:
                if isinstance(df[col], pd.DataFrame):
                    self.logger.warning(f"Column {col} is DataFrame, converting to Series")
                    df[col] = df[col].squeeze()  # Convert DataFrame to Series
            
            df = df.sort_index(ascending=False)
            return df

        except Exception as e:
            self.logger.error(f"Yahoo Finance API request failed for {ticker}: {str(e)}")
            return pd.DataFrame()
    def _convert_finnhub_to_dataframe(self, data: dict) -> pd.DataFrame:
        """
        Convert Finnhub API data to a DataFrame.

        Args:
            data (dict): Data from Finnhub API.

        Returns:
            pandas.DataFrame: DataFrame containing the historical data.
        """
        df = pd.DataFrame({
            'close': data['c'],
            'high': data['h'],
            'low': data['l'],
            'open': data['o'],
            'volume': data['v']
        }, index=pd.to_datetime(data['t'], unit='s'))
        df.sort_index(ascending=False, inplace=True)
        return df
    
    def calculate_bollinger_bands(self, df, window=20, num_std=2):
        """
        Calculate Bollinger Bands for a given DataFrame
        
        Args:
            df (pandas.DataFrame): DataFrame with price data
            window (int): Window size for moving average
            num_std (int): Number of standard deviations for bands
            
        Returns:
            dict: Dictionary with Bollinger Bands values
        """
        if df.empty:
            return {}
            
        try:
            # Make sure we have enough data
            if len(df) < window:
                self.logger.warning(f"Not enough data for Bollinger Bands calculation: {len(df)} < {window}")
                return {}
            if bool(df['close'].isnull().all()):
                self.logger.warning("No valid close price data available for Bollinger Bands.")
                return {}
                
            # Calculate middle band (SMA)
            middle_band = df['close'].rolling(window=window).mean()
            
            # Calculate standard deviation
            std = df['close'].rolling(window=window).std()
            
            # Calculate upper and lower bands
            upper_band = middle_band + (std * num_std)
            lower_band = middle_band - (std * num_std)
            
            valid_idx = middle_band.last_valid_index()
            if valid_idx is None:
                self.logger.warning("No valid Bollinger Band values found (all NaN).")
                return {}

            current_middle = float(middle_band.loc[valid_idx].squeeze())
            current_upper = float(upper_band.loc[valid_idx].squeeze())
            current_lower = float(lower_band.loc[valid_idx].squeeze())
            current_close = float(df['close'].loc[valid_idx].squeeze())
            # Calculate band width and %B
            band_width = (current_upper - current_lower) / current_middle * 100
            
            # Avoid division by zero
            if current_upper == current_lower:
                percent_b = 50.0
            else:
                percent_b = (current_close - current_lower) / (current_upper - current_lower) * 100
            
            # Determine indicator signal
            if current_close > current_upper:
                signal = "Overbought"
            elif current_close < current_lower:
                signal = "Oversold"
            else:
                signal = "Neutral"
            
            return {
                "BB Middle Band": round(current_middle, 2),
                "BB Upper Band": round(current_upper, 2),
                "BB Lower Band": round(current_lower, 2),
                "BB Width (%)": round(band_width, 2),
                "BB %B": round(percent_b, 2),
                "BB Signal": signal
            }
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {str(e)}")
            return {}
    
    def calculate_moving_averages(self, df):
        """
        Calculate various moving averages
        
        Args:
            df (pandas.DataFrame): DataFrame with price data
            
        Returns:
            dict: Dictionary with moving average values
        """
        if df.empty:
            return {}
        if bool(df['close'].isnull().all()):
            self.logger.warning("No valid close price data available for Moving Averages.")
            return {}
        try:
            # Calculate different moving averages
            ma_windows = [10, 20, 50, 100, 200]
            mas = {}
            
            for window in ma_windows:
                if len(df) >= window:
                    ma = df['close'].rolling(window=window).mean()
                    last_valid_index = ma.last_valid_index()
                    if last_valid_index is not None:
                        mas[f"MA{window}"] = round(ma.loc[last_valid_index].squeeze(), 2)
                    else:
                        mas[f"MA{window}"] = np.nan
            
            # Calculate exponential moving averages
            ema_windows = [12, 26, 50, 200]
            emas = {}
            for window in ema_windows:
                if len(df) >= window:
                    ema = df['close'].ewm(span=window, adjust=False).mean()
                    last_valid_index = ema.last_valid_index()
                    emas[f"EMA{window}"] = round(ema.loc[last_valid_index].squeeze(), 2)
            
            # Calculate MACD
            if len(df) >= 26:
                ema12 = df['close'].ewm(span=12, adjust=False).mean()
                ema26 = df['close'].ewm(span=26, adjust=False).mean()
                macd = ema12 - ema26
                signal = macd.ewm(span=9, adjust=False).mean()
                macd_hist = macd - signal
                
                last_idx = macd.dropna().last_valid_index()
                macd_data = {
                    "MACD Line": round(macd.loc[last_idx].squeeze(), 2),
                    "MACD Signal": round(signal.loc[last_idx].squeeze(), 2),
                    "MACD Histogram": round(macd_hist.loc[last_idx].squeeze(), 2)
                }
            else:
                macd_data = {}
            
            # Determine crossover signals
            signals = {}
            current_close = float(df['close'].iloc[-1].squeeze())  # Use latest value and convert to float
            
            for window in ma_windows:
                if f"MA{window}" in mas and not np.isnan(mas[f"MA{window}"]):
                    if current_close > mas[f"MA{window}"]:
                        signals[f"MA{window} Signal"] = "Bullish (Price > MA)"
                    else:
                        signals[f"MA{window} Signal"] = "Bearish (Price < MA)"
            
            # Add all data to result
            result = {**mas, **emas, **macd_data, **signals}
            
            # Add current price for reference
            result["Current Price"] = round(current_close, 2)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating Moving Averages: {str(e)}")
            return {}
    
    def calculate_rsi(self, df, window=14):
        """
        Calculate Relative Strength Index (RSI)
        
        Args:
            df (pandas.DataFrame): DataFrame with price data
            window (int): Window size for RSI calculation
            
        Returns:
            dict: Dictionary with RSI values
        """
        if df.empty or len(df) < window + 1:
            return {}
        if bool(df['close'].isnull().all()):
            self.logger.warning("No valid close price data available for RSI.")
            return {}
            
        try:
            # Calculate price differences
            delta = df['close'].diff()
            
            # Create copies for gains and losses
            gain = delta.copy()
            loss = delta.copy()
            
            # Separate gains and losses
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            loss = abs(loss)
            
            # Calculate average gain and loss
            avg_gain = gain.rolling(window=window).mean()
            avg_loss = loss.rolling(window=window).mean()
            
            # Handle division by zero
            avg_loss = avg_loss.replace(0, 0.00001)
            
            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # Get the most recent valid RSI value
            last_valid = rsi.last_valid_index()
            if last_valid is not None and not np.isnan(rsi.loc[last_valid].squeeze()):
                current_rsi = round(float(rsi.loc[last_valid].squeeze()), 2)
            else:
                current_rsi = np.nan
            
            # Determine RSI signal
            if not np.isnan(current_rsi) and current_rsi > 70:
                signal = "Overbought"
            elif not np.isnan(current_rsi) and current_rsi < 30:
                signal = "Oversold"
            else:
                signal = "Neutral"
            
            return {
                "RSI (14)": current_rsi,
                "RSI Signal": signal
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {str(e)}")
            return {}
    
    def calculate_sharpe_ratio(self, df, period='daily', risk_free_rate=None, annualize=True):
        """
        Calculate the Sharpe Ratio for a given DataFrame
        
        Args:
            df (pandas.DataFrame): DataFrame with price data
            period (str): Period of returns - 'daily', 'weekly', 'monthly', or 'annual'
            risk_free_rate (float, optional): Risk-free rate (annual). If None, will use current 10Y Treasury yield.
            annualize (bool): Whether to annualize the Sharpe ratio for periods less than a year
            
        Returns:
            dict: Dictionary with Sharpe Ratio and related metrics
        """
        if df.empty or len(df) < 2:
            return {"Sharpe Ratio": "Insufficient Data"}
        
        try:
            # Get the risk-free rate if not provided
            if risk_free_rate is None:
                risk_free_rate = self._get_current_risk_free_rate()
            
            # Determine annualization factor based on period
            period_factors = {
                'daily': 252,  # Trading days in a year
                'weekly': 52,  # Weeks in a year
                'monthly': 12,  # Months in a year
                'annual': 1     # Already annual
            }
            
            if period not in period_factors:
                self.logger.warning(f"Invalid period '{period}'. Using 'daily' as default.")
                period = 'daily'
                
            annualization_factor = period_factors[period]
            
            # Calculate returns based on period
            # Ensure we're working with the close price series correctly
            close_prices = df['close']
            if isinstance(close_prices, pd.DataFrame):
                close_prices = close_prices.squeeze()
            
            # Ensure it's a pandas Series for pct_change calculation
            if not isinstance(close_prices, pd.Series):
                self.logger.error("Close prices are not in the expected pandas Series format")
                return {"Sharpe Ratio": "Data Format Error"}
            
            returns_series = None
            if period == 'daily':
                returns_series = close_prices.pct_change()
            elif period == 'weekly':
                returns_series = close_prices.pct_change(5)  # Approximately 5 trading days in a week
            elif period == 'monthly':
                returns_series = close_prices.pct_change(21)  # Approximately 21 trading days in a month
            elif period == 'annual':
                returns_series = close_prices.pct_change(252)  # Approximately 252 trading days in a year
            
            if returns_series is None:
                return {"Sharpe Ratio": "Invalid Period"}
            
            # Ensure returns_series is a Series (not DataFrame)
            if isinstance(returns_series, pd.DataFrame):
                returns_series = returns_series.squeeze()
            
            # Drop NaN values
            returns = returns_series.dropna()
            
            if len(returns) < 2:
                return {"Sharpe Ratio": "Insufficient Data"}
            
            # Calculate excess returns (return - risk-free rate)
            # Convert annual risk-free rate to the period's rate
            period_risk_free_rate = risk_free_rate / annualization_factor
            excess_returns = returns - period_risk_free_rate
            
            # Calculate mean and standard deviation of excess returns
            mean_excess_return = excess_returns.mean()
            std_dev_excess_return = excess_returns.std()
            
            # Avoid division by zero
            if std_dev_excess_return == 0:
                return {"Sharpe Ratio": "Undefined (Zero Volatility)"}
            
            # Calculate Sharpe Ratio
            sharpe_ratio = mean_excess_return / std_dev_excess_return
            
            # Annualize if requested and not already annual
            if annualize and period != 'annual':
                sharpe_ratio = sharpe_ratio * np.sqrt(annualization_factor)
            
            # Calculate additional metrics
            # Sortino Ratio - only considers downside risk
            downside_returns = excess_returns[excess_returns < 0]
            
            if len(downside_returns) > 0:
                downside_deviation = downside_returns.std()
                
                if downside_deviation > 0:
                    sortino_ratio = mean_excess_return / downside_deviation
                    
                    # Annualize if requested and not already annual
                    if annualize and period != 'annual':
                        sortino_ratio = sortino_ratio * np.sqrt(annualization_factor)
                else:
                    sortino_ratio = "Undefined (No Downside Deviation)"
            else:
                sortino_ratio = "Undefined (No Negative Returns)"
            
            # Calculate annualized return and volatility
            annualized_return = mean_excess_return * annualization_factor if annualize else mean_excess_return
            annualized_volatility = std_dev_excess_return * np.sqrt(annualization_factor) if annualize else std_dev_excess_return
            
            # Prepare results
            results = {
                "Sharpe Ratio": round(sharpe_ratio, 3),
                "Sortino Ratio": round(sortino_ratio, 3) if isinstance(sortino_ratio, float) else sortino_ratio,
                "Sortino Ratio Interpretation": self._interpret_sortino_ratio(sortino_ratio) if isinstance(sortino_ratio, float) else "N/A",
                "Annualized Return": f"{round(annualized_return * 100, 2)}%" if annualize else f"{round(mean_excess_return * 100, 2)}%",
                "Annualized Volatility": f"{round(annualized_volatility * 100, 2)}%" if annualize else f"{round(std_dev_excess_return * 100, 2)}%",
                "Risk-Free Rate": f"{round(risk_free_rate * 100, 2)}%",
                "Period": period,
                "Data Points": len(returns),
                "Sharpe Ratio Interpretation": self._interpret_sharpe_ratio(sharpe_ratio)
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error calculating Sharpe Ratio: {str(e)}")
            return {"Sharpe Ratio": "Calculation Error", "Error": str(e)}
    
    def _get_current_risk_free_rate(self):
        """
        Get the current risk-free rate from the US 10Y Treasury yield
        
        Returns:
            float: Current 10Y Treasury yield as decimal (e.g., 0.0175 for 1.75%)
        """
        try:
            # Try to get the current 10Y Treasury yield from an API
            # This is a placeholder. In a real implementation, you'd use a financial API or service
            url = "https://www.treasury.gov/resource-center/data-chart-center/interest-rates/Pages/TextView.aspx?data=yield"
            
            # For now, use a reasonable default value if API call fails
            # The 10Y Treasury yield as of May 2025 (approximate)
            default_rate = 0.035  # 3.5%
            
            # Log that we're using a default value
            self.logger.info(f"Using default risk-free rate of {default_rate}")
            
            return default_rate
        
        except Exception as e:
            self.logger.error(f"Error getting current risk-free rate: {str(e)}")
            return 0.035  # Default to 3.5% if there's an error
        
    def _interpret_sharpe_ratio(self, sharpe_ratio):
        """
        Provide an interpretation of the Sharpe ratio value
        
        Args:
            sharpe_ratio (float): Calculated Sharpe ratio
            
        Returns:
            str: Interpretation of the Sharpe ratio
        """
        if sharpe_ratio < 0:
            return "Poor - Negative returns relative to risk-free rate"
        elif sharpe_ratio < 0.5:
            return "Poor - Suboptimal risk-adjusted returns"
        elif sharpe_ratio < 1.0:
            return "Below Average - Low risk-adjusted returns"
        elif sharpe_ratio < 1.5:
            return "Average - Acceptable risk-adjusted returns"
        elif sharpe_ratio < 2.0:
            return "Good - Strong risk-adjusted returns"
        elif sharpe_ratio < 3.0:
            return "Very Good - Excellent risk-adjusted returns"
        else:
            return "Exceptional - Outstanding risk-adjusted returns"
    def _interpret_sortino_ratio(self, sortino_ratio: float) -> str:
        """
        Provide an interpretation of the Sortino Ratio value.

        Args:
            sortino_ratio (float): Calculated Sortino Ratio.

        Returns:
            str: Interpretation of the Sortino Ratio.
        """
        if sortino_ratio < 0:
            return "Poor - Negative returns relative to risk-free rate"
        elif sortino_ratio < 0.5:
            return "Poor - Suboptimal risk-adjusted returns"
        elif sortino_ratio < 1.0:
            return "Below Average - Low risk-adjusted returns"
        elif sortino_ratio < 1.5:
            return "Average - Acceptable risk-adjusted returns"
        elif sortino_ratio < 2.0:
            return "Good - Strong risk-adjusted returns"
        elif sortino_ratio < 3.0:
            return "Very Good - Excellent risk-adjusted returns"
        else:
            return "Exceptional - Outstanding risk-adjusted returns"
    def calculate_volume_indicators(self, df):
        """
        Calculate volume-based indicators
        
        Args:
            df (pandas.DataFrame): DataFrame with price data and volume
            
        Returns:
            dict: Dictionary with volume indicator values
        """
        if df.empty:
            return {}
            
        try:
            # Ensure volume data is not NaN
            if bool(df['volume'].isnull().all()):
                self.logger.warning("No volume data available")
                return {"Volume Data": "Not Available"}
            
            # Fill any NaN values with 0
            df['volume'] = df['volume'].fillna(0)
            
            # Calculate volume moving average
            volume_ma_windows = [10, 20, 50]
            volume_mas = {}
            
            for window in volume_ma_windows:
                if len(df) >= window:
                    volume_ma = df['volume'].rolling(window=window).mean()
                    # Safely convert to int with NaN handling - use latest value
                    if not np.isnan(volume_ma.iloc[-1].squeeze()):
                        volume_mas[f"Volume MA{window}"] = int(volume_ma.iloc[-1].squeeze())
                    else:
                        volume_mas[f"Volume MA{window}"] = 0
            
            # Current volume - safely get as int (latest value)
            try:
                current_volume = int(df['volume'].iloc[-1].squeeze())
            except (TypeError, ValueError):
                current_volume = 0
            
            # Determine volume signals
            signals = {}
            for window in volume_ma_windows:
                if f"Volume MA{window}" in volume_mas:
                    if current_volume > volume_mas[f"Volume MA{window}"]:
                        signals[f"Volume MA{window} Signal"] = "Above Average"
                    else:
                        signals[f"Volume MA{window} Signal"] = "Below Average"
            
            # On-Balance Volume (OBV)
            # Handle NaN values in volume
            safe_volume = df['volume'].fillna(0).astype(int)
            
            # Start with zero OBV and add/subtract volume based on price movement
            obv = [0]
            for i in range(1, len(df)):
                current_price = float(df['close'].iloc[i].squeeze())
                prev_price = float(df['close'].iloc[i-1].squeeze())
                current_vol = int(safe_volume.iloc[i].squeeze())
                
                if current_price > prev_price:
                    obv.append(obv[-1] + current_vol)
                elif current_price < prev_price:
                    obv.append(obv[-1] - current_vol)
                else:
                    obv.append(obv[-1])
            
            # Create a Series with the OBV values
            obv_series = pd.Series(obv, index=df.index)
            
            # Calculate OBV moving average
            obv_ma = obv_series.rolling(window=20).mean()
            
            # Determine OBV trend
            obv_trend = "Neutral"
            if len(obv_series) > 5:
                if obv_series.iloc[0] > obv_series.iloc[4]:
                    obv_trend = "Bullish"
                elif obv_series.iloc[0] < obv_series.iloc[4]:
                    obv_trend = "Bearish"
            
            # Add to results
            volume_data = {
                "Current Volume": current_volume,
                "OBV Trend": obv_trend,
                **volume_mas,
                **signals
            }
            
            return volume_data
            
        except Exception as e:
            self.logger.error(f"Error calculating Volume Indicators: {str(e)}")
            return {"Volume Indicators Error": str(e)}
    
    def get_all_indicators(self, ticker):
        """
        Calculate all technical indicators for a ticker
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Dictionary with all technical indicators
        """
        # Get historical data
        df = self.get_historical_data(ticker)

        if df.empty:
            print(20*"###")
            print("No historical data available for the ticker.")
            self.logger.error("No historical data available for the ticker.")
            return {"error": "Could not retrieve historical data"}
        
        # Calculate all indicators
        results = {"Ticker": ticker, "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        # Try each indicator separately and gracefully handle failures
        try:
            bollinger_bands = self.calculate_bollinger_bands(df)
            results.update(bollinger_bands)
        except Exception as e:
            self.logger.error(f"Failed to calculate Bollinger Bands: {str(e)}")
            results["Bollinger Bands"] = "Calculation Error"
        
        try:
            moving_averages = self.calculate_moving_averages(df)
            results.update(moving_averages)
        except Exception as e:
            self.logger.error(f"Failed to calculate Moving Averages: {str(e)}")
            results["Moving Averages"] = "Calculation Error"
        
        try:
            rsi = self.calculate_rsi(df)
            results.update(rsi)
        except Exception as e:
            self.logger.error(f"Failed to calculate RSI: {str(e)}")
            results["RSI"] = "Calculation Error"
        
        try:
            volume_indicators = self.calculate_volume_indicators(df)
            results.update(volume_indicators)
        except Exception as e:
            self.logger.error(f"Failed to calculate Volume Indicators: {str(e)}")
            results["Volume Indicators"] = "Calculation Error"
        try:
            scrape_ratio = self.calculate_sharpe_ratio(df)
            results.update(scrape_ratio)
        except Exception as e:
            self.logger.error(f"Failed to calculate sharpe Ratio: {str(e)}")
            results["Sharpe Ratio"] = "Calculation Error"
        return results