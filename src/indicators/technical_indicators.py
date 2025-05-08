"""
Technical Indicators Module for Stock Analysis
"""
import numpy as np
import pandas as pd
import requests
import os
import logging
from datetime import datetime, timedelta

class TechnicalIndicators:
    """
    Class to calculate and retrieve technical indicators for stocks
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the technical indicators module
        
        Args:
            api_key (str): Alpha Vantage API key. If None, will try to get from ALPHA_VANTAGE_API_KEY environment variable
        """
        self.api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY")
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if not self.api_key:
            self.logger.warning("Alpha Vantage API key not provided. Set ALPHA_VANTAGE_API_KEY environment variable.")
    
    def get_historical_data(self, ticker: str, days: int = 100) -> pd.DataFrame:
        """
        Retrieve historical price data for a ticker.

        Args:
            ticker (str): Stock ticker symbol.
            days (int): Number of days of historical data to fetch.

        Returns:
            pandas.DataFrame: DataFrame containing the historical data.
        """
        if not self.api_key:
            self.logger.error("Alpha Vantage API key not available. Cannot fetch historical data.")
            return pd.DataFrame()

        # Try Alpha Vantage API
        df = self._fetch_alpha_vantage_data(ticker, days)
        if not df.empty:
            return df
        self.logger.info("Alpha Vantage API failed to fetch historical data. Trying Finnhub API...")
        # Fallback to Finnhub API
        df = self._fetch_finnhub_data(ticker, days)
        if not df.empty:
            return df

        # If both APIs fail
        self.logger.error("Both Alpha Vantage and Finnhub APIs failed. Unable to fetch historical data.")
        return pd.DataFrame()

    def _fetch_alpha_vantage_data(self, ticker: str, days: int) -> pd.DataFrame:
        """
        Fetch historical data from Alpha Vantage API.

        Args:
            ticker (str): Stock ticker symbol.
            days (int): Number of days of historical data to fetch.

        Returns:
            pandas.DataFrame: DataFrame containing the historical data.
        """
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={self.api_key}"
        self.logger.info(f"Fetching data from Alpha Vantage: {url}")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "Error Message" in data:
                self.logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return pd.DataFrame()

            if "Time Series (Daily)" not in data:
                self.logger.error(f"No time series data returned from Alpha Vantage. Response: {data}")
                return pd.DataFrame()

            return self._convert_alpha_vantage_to_dataframe(data["Time Series (Daily)"], days)

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Alpha Vantage API request failed: {str(e)}")
            return pd.DataFrame()
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
            response = requests.get(url, timeout=10)
            response.raise_for_status()
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
        df.fillna(method='ffill', inplace=True)
        return df
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
                
            # Calculate middle band (SMA)
            middle_band = df['close'].rolling(window=window).mean()
            
            # Calculate standard deviation
            std = df['close'].rolling(window=window).std()
            
            # Calculate upper and lower bands
            upper_band = middle_band + (std * num_std)
            lower_band = middle_band - (std * num_std)
            
            # Get the most recent values
            current_middle = middle_band.iloc[0]
            current_upper = upper_band.iloc[0]
            current_lower = lower_band.iloc[0]
            current_close = df['close'].iloc[0]
            
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
            
        try:
            # Calculate different moving averages
            ma_windows = [10, 20, 50, 100, 200]
            mas = {}
            
            for window in ma_windows:
                if len(df) >= window:
                    ma = df['close'].rolling(window=window).mean()
                    mas[f"MA{window}"] = round(ma.iloc[0], 2)
            
            # Calculate exponential moving averages
            ema_windows = [12, 26, 50, 200]
            emas = {}
            
            for window in ema_windows:
                if len(df) >= window:
                    ema = df['close'].ewm(span=window, adjust=False).mean()
                    emas[f"EMA{window}"] = round(ema.iloc[0], 2)
            
            # Calculate MACD
            if len(df) >= 26:
                ema12 = df['close'].ewm(span=12, adjust=False).mean()
                ema26 = df['close'].ewm(span=26, adjust=False).mean()
                macd = ema12 - ema26
                signal = macd.ewm(span=9, adjust=False).mean()
                macd_hist = macd - signal
                
                macd_data = {
                    "MACD Line": round(macd.iloc[0], 2),
                    "MACD Signal": round(signal.iloc[0], 2),
                    "MACD Histogram": round(macd_hist.iloc[0], 2)
                }
            else:
                macd_data = {}
            
            # Determine crossover signals
            signals = {}
            current_close = df['close'].iloc[0]
            
            for window in ma_windows:
                if f"MA{window}" in mas:
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
            
            # Get current RSI value
            current_rsi = round(rsi.iloc[0], 2)
            
            # Determine RSI signal
            if current_rsi > 70:
                signal = "Overbought"
            elif current_rsi < 30:
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
    
    def calculate_scrape_ratio(self,df):
        """
        Calculate the Scrape Ratio for a given DataFrame
        
        Args:
            df (pandas.DataFrame): DataFrame with price data
            
        Returns:
            dict: Dictionary with Scrape Ratio value
        """
        if df.empty:
            return {"Scrape Ratio": "Insufficient Data"}
        
        try:
            # Calculate the scrape ratio as the ratio of the highest close to the lowest close
            highest_close = df['close'].max()
            lowest_close = df['close'].min()
            
            # Avoid division by zero
            if lowest_close == 0:
                return {"Scrape Ratio": "Invalid Data (Division by Zero)"}
            
            scrape_ratio = highest_close / lowest_close
            
            return {"Scrape Ratio": round(scrape_ratio, 2)}
    
        except Exception as e:
            self.logger.error(f"Error calculating Scrape Ratio: {str(e)}")
            return {"Scrape Ratio": "Calculation Error"}
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
            if df['volume'].isnull().all():
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
                    # Safely convert to int with NaN handling
                    if not np.isnan(volume_ma.iloc[0]):
                        volume_mas[f"Volume MA{window}"] = int(volume_ma.iloc[0])
                    else:
                        volume_mas[f"Volume MA{window}"] = 0
            
            # Current volume - safely get as int
            try:
                current_volume = int(df['volume'].iloc[0])
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
                if df['close'].iloc[i] > df['close'].iloc[i-1]:
                    obv.append(obv[-1] + safe_volume.iloc[i])
                elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                    obv.append(obv[-1] - safe_volume.iloc[i])
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
            print("DEBBUUGGGGGGGGGGG Scrap ratio")
            scrape_ratio = self.calculate_scrape_ratio(df)
            results.update(scrape_ratio)
        except Exception as e:
            self.logger.error(f"Failed to calculate Scrape Ratio: {str(e)}")
            results["Scrape Ratio"] = "Calculation Error"
        return results