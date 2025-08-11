"""
Technical Indicators Module for Stock Analysis
"""
import numpy as np
import pandas as pd
import requests
import os
import logging
from datetime import datetime, timedelta
import yfinance as yf
from pandas_datareader import data as pdr
from ..utils.request_handler import make_request

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
        Retrieve historical price data for a ticker with optimized fallback strategy.

        Args:
            ticker (str): Stock ticker symbol.
            days (int): Number of days of historical data to fetch.

        Returns:
            pandas.DataFrame: DataFrame containing the historical data.
        """
        if not self.api_key:
            self.logger.error("Alpha Vantage API key not available. Cannot fetch historical data.")
            return pd.DataFrame()

            
        # 1. Try Alpha Vantage
        self.logger.info("Yahoo Finance failed, trying Alpha Vantage API...")
        df = self._fetch_alpha_vantage_data(ticker, days)
        if not df.empty:
            return df
        
        # 2. Try Yahoo Finance if Alpha Vantage does not work
        df = self._fetch_yahoo_finance_data(ticker, days)
        if not df.empty:
            return df
        
        # 3. Try Finnhub as last backup
        self.logger.info("Alpha Vantage failed, trying Finnhub API...")
        df = self._fetch_finnhub_data(ticker, days)
        if not df.empty:
            return df
            
        # If all APIs fail
        self.logger.error("All APIs failed. Unable to fetch historical data.")
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
            response = make_request(url, timeout=10)
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
        df.fillna(method='ffill', inplace=True)
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
            if df.empty:
                self.logger.warning(f"No data returned from Yahoo Finance for {ticker}.")
                return pd.DataFrame()

            # Rename columns to match the standard format
            df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }, inplace=True)
            df.sort_index(ascending=False, inplace=True)
            return df

        except Exception as e:
            self.logger.error(f"Yahoo Finance API request failed for {ticker}: {str(e)}")
            return pd.DataFrame()
        
    def _fetch_google_finance_data(self, ticker: str, days: int) -> pd.DataFrame:
        """
        Fetch historical data from Google Finance.

        Args:
            ticker (str): Stock ticker symbol.
            days (int): Number of days of historical data to fetch.

        Returns:
            pandas.DataFrame: DataFrame containing the historical data.
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            self.logger.info(f"Fetching data from Google Finance for {ticker} from {start_date} to {end_date}.")

            df = pdr.get_data_google(ticker, start=start_date, end=end_date)
            if df.empty:
                self.logger.warning(f"No data returned from Google Finance for {ticker}.")
                return pd.DataFrame()

            # Rename columns to match the standard format
            df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }, inplace=True)
            df.sort_index(ascending=False, inplace=True)
            return df

        except Exception as e:
            self.logger.error(f"Google Finance API request failed for {ticker}: {str(e)}")
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
            if df['close'].isnull().all().item():
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

            current_middle = middle_band.loc[valid_idx].squeeze()
            current_upper = upper_band.loc[valid_idx].squeeze()
            current_lower = lower_band.loc[valid_idx].squeeze()
            current_close = df['close'].loc[valid_idx].squeeze()
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
        if df['close'].isnull().all().item():
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
            current_close = df['close'].iloc[0].squeeze()
            
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
        if df['close'].isnull().all().item():
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
                current_rsi = round(rsi.loc[last_valid].squeeze(), 2)
            else:
                current_rsi = np.nan
            
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
            if period == 'daily':
                df['returns'] = df['close'].pct_change()
            elif period == 'weekly':
                df['returns'] = df['close'].pct_change(5)  # Approximately 5 trading days in a week
            elif period == 'monthly':
                df['returns'] = df['close'].pct_change(21)  # Approximately 21 trading days in a month
            elif period == 'annual':
                df['returns'] = df['close'].pct_change(252)  # Approximately 252 trading days in a year
            
            # Drop NaN values
            returns = df['returns'].dropna()
            
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
            if df['volume'].isnull().all().squeeze():
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
                    if not np.isnan(volume_ma.iloc[0].squeeze()):
                        volume_mas[f"Volume MA{window}"] = int(volume_ma.iloc[0].squeeze())
                    else:
                        volume_mas[f"Volume MA{window}"] = 0
            
            # Current volume - safely get as int
            try:
                current_volume = int(df['volume'].iloc[0].squeeze())
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
                if df['close'].iloc[i].squeeze() > df['close'].iloc[i-1].squeeze():
                    obv.append(obv[-1] + safe_volume.iloc[i])
                elif df['close'].iloc[i].squeeze() < df['close'].iloc[i-1].squeeze():
                    obv.append(obv[-1] - safe_volume.iloc[i].squeeze())
                else:
                    obv.append(obv[-1])
            
            # Create a Series with the OBV values
            obv_series = pd.Series(obv, index=df.index)
            
            # Calculate OBV moving average
            obv_ma = obv_series.rolling(window=20).mean()
            
            # Determine OBV trend
            obv_trend = "Neutral"
            if len(obv_series) > 5:
                if obv_series.iloc[0] > obv_series.iloc[4].squeeze():
                    obv_trend = "Bullish"
                elif obv_series.iloc[0] < obv_series.iloc[4].squeeze():
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