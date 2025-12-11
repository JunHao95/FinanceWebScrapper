"""
Volatility Surface Builder
Fetches options chain data and constructs implied volatility surface
"""

import logging
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from .implied_volatility import ImpliedVolatilityCalculator

logger = logging.getLogger(__name__)


class VolatilitySurfaceBuilder:
    """
    Build volatility surface from real market options data
    
    Volatility surface is a 3D representation showing how implied volatility varies across:
        - Strike Prices (K) : Horizontal Axis (Moneyness)
        - Time to Maturity (T) : Depth Axis
        - Implied Volatility Values (IV) : Vertical Axis
    Reveals market pricing patterns like volatility smiles and term structure.
    """
    
    def __init__(self):
        self.iv_calculator = ImpliedVolatilityCalculator()
        
    def fetch_options_chain(self, ticker: str) -> Dict:
        """
        Fetch live options chain data from Yahoo Finance
        Data includes:
            - Current Stock Prices (S)
            - Expiration Dates
            - Call & Puts with :
                - Bid/Ask Prices
                - Strike (K)
                - Volumes
                - Open Interests
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
            
        Returns:
            Dictionary containing options data and current stock price
        """
        try:
            logger.info(f"Fetching options chain for {ticker}")
            stock = yf.Ticker(ticker)
            
            # Get current stock price
            info = stock.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if not current_price:
                # Fallback: get from history
                hist = stock.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                else:
                    raise ValueError(f"Could not fetch current price for {ticker}")
            
            # Get available expiration dates
            expirations = stock.options
            
            if not expirations or len(expirations) == 0:
                raise ValueError(f"No options data available for {ticker}")
            
            logger.info(f"Found {len(expirations)} expiration dates for {ticker}")
            logger.info(f"Current stock price: ${current_price:.2f}")
            
            # Fetch options data for all expirations
            all_options = []
            
            for expiration in expirations:
                try:
                    opt_chain = stock.option_chain(expiration)
                    
                    # Process calls
                    calls = opt_chain.calls.copy()
                    calls['expiration'] = expiration
                    calls['option_type'] = 'call'
                    
                    # Process puts
                    puts = opt_chain.puts.copy()
                    puts['expiration'] = expiration
                    puts['option_type'] = 'put'
                    
                    # Combine calls and puts
                    all_options.append(calls)
                    all_options.append(puts)
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch options for expiration {expiration}: {str(e)}")
                    continue
            
            if not all_options:
                raise ValueError(f"Could not fetch any options data for {ticker}")
            
            # Combine all options into single DataFrame
            options_df = pd.concat(all_options, ignore_index=True)
            
            # Filter out options with no volume or bid/ask
            options_df = options_df[
                (options_df['volume'] > 0) | 
                ((options_df['bid'] > 0) & (options_df['ask'] > 0))
            ]
            
            logger.info(f"Fetched {len(options_df)} tradable options")
            
            return {
                'ticker': ticker,
                'current_price': float(current_price),
                'options': options_df,
                'expirations': list(expirations)
            }
            
        except Exception as e:
            logger.error(f"Error fetching options chain for {ticker}: {str(e)}")
            raise
    
    def calculate_time_to_maturity(self, expiration_date: str) -> float:
        """
        Calculate time to maturity in years
        
        Args:
            expiration_date: Expiration date string (YYYY-MM-DD)
            
        Returns:
            Time to maturity in years
        """
        try:
            exp_date = datetime.strptime(expiration_date, '%Y-%m-%d')
            today = datetime.now()
            days_to_expiry = (exp_date - today).days
            
            # Convert to years (using 252 trading days convention)
            years = max(days_to_expiry / 365.0, 1/365.0)  # Minimum 1 day
            
            return years
            
        except Exception as e:
            logger.warning(f"Error calculating maturity for {expiration_date}: {str(e)}")
            return 0.25  # Default to 3 months
    
    def calculate_moneyness(self, strike: float, spot: float) -> float:
        """
        Calculate moneyness as log(K/S)
        
        Args:
            strike: Strike price
            spot: Current stock price
            
        Returns:
            Moneyness value
        """
        return np.log(strike / spot)
    
    def build_surface(
        self, 
        ticker: str, 
        risk_free_rate: float = 0.05,
        option_type: str = 'call',
        min_volume: int = 10,
        max_spread_pct: float = 0.20
    ) -> Dict:
        """
        Build implied volatility surface from market data
        
        Args:
            ticker: Stock ticker symbol
            risk_free_rate: Risk-free interest rate (default 5%)
            option_type: 'call' or 'put' (default 'call')
            min_volume: Minimum volume filter (default 10)
            max_spread_pct: Maximum bid-ask spread as % of mid (default 20%)
            
        Returns:
            Dictionary containing surface data for plotting
        """
        try:
            # Fetch options chain
            chain_data = self.fetch_options_chain(ticker)
            options_df = chain_data['options']
            current_price = chain_data['current_price']
            
            # Filter by option type
            options_df = options_df[options_df['option_type'] == option_type].copy()
            
            # Step 1: Filter for near-the-money options (where quotes exist)
            # Focus on strikes between 70% and 130% of current price
            #   - Deep OTM options have low vega -> unreliable IV
            #   - Deep ITM Options have low time value -> unreliable
            options_df['moneyness_ratio'] = options_df['strike'] / current_price
            options_df = options_df[
                (options_df['moneyness_ratio'] >= 0.7) & 
                (options_df['moneyness_ratio'] <= 1.3)
            ]
            logger.info(f"After moneyness filter (70%-130% of spot): {len(options_df)} options")
            
            # Step 2: Filter for valid bid/ask quotes
            # Remove options with zero bid or ask (no market makers)
            valid_quotes_df = options_df[
                (options_df['bid'] > 0) & 
                (options_df['ask'] > 0)
            ]
            logger.info(f"After bid/ask filter (bid>0, ask>0): {len(valid_quotes_df)} options")
            
            # Fallback mechanism when market is close, fall back to last price (previous day's data)
            use_historical = False
            if len(valid_quotes_df) == 0:
                logger.warning(
                    f"No live bid/ask quotes for {ticker}. Market may be closed. "
                    f"Falling back to lastPrice (previous trading day's data)..."
                )
                
                # Use lastPrice column if available
                if 'lastPrice' in options_df.columns:
                    historical_df = options_df[
                        (options_df['lastPrice'].notna()) & 
                        (options_df['lastPrice'] > 0)
                    ].copy()
                    
                    if len(historical_df) > 0:
                        # Use lastPrice as market price
                        historical_df['mid_price'] = historical_df['lastPrice']
                        historical_df['bid'] = historical_df['lastPrice'] * 0.95  # Estimate
                        historical_df['ask'] = historical_df['lastPrice'] * 1.05  # Estimate
                        options_df = historical_df
                        use_historical = True
                        logger.info(f"Using historical data: {len(options_df)} options with lastPrice")
                    else:
                        raise ValueError(
                            f"No options with valid quotes or historical data for {ticker}. "
                            f"Try again during market hours (9:30 AM - 4:00 PM ET, Mon-Fri). "
                            f"For best results, use highly liquid tickers: SPY, QQQ, AAPL, MSFT"
                        )
                else:
                    raise ValueError(
                        f"No options with valid quotes for {ticker}. "
                        f"All bid/ask prices are $0 (no market makers posting quotes). "
                        f"This typically means the market is closed. "
                        f"Try again during market hours (9:30 AM - 4:00 PM ET, Mon-Fri). "
                        f"For best results, use highly liquid tickers: SPY, QQQ, AAPL, MSFT"
                    )
            else:
                options_df = valid_quotes_df
            
            # Step 3: Calculate mid price and filter (if not already set) to get "Fair Value" estimate
            if not use_historical:
                options_df['mid_price'] = (options_df['bid'] + options_df['ask']) / 2
            
            options_df = options_df[options_df['mid_price'] >= 0.01]  # At least $0.01
            logger.info(f"After mid price filter (>=$0.01): {len(options_df)} options")
            
            # Step 4: Filter by volume
            if min_volume > 0:
                options_df = options_df[options_df['volume'] >= min_volume]
                logger.info(f"After volume filter (>={min_volume}): {len(options_df)} options")
            
            # Step 5: Filter by bid-ask spread
            # Wide spread (>20% indicates)
            #    - Low liquidity
            #    - Unreliable pricing
            #    - High Transaction cost
            if not use_historical:
                options_df['spread_pct'] = (options_df['ask'] - options_df['bid']) / options_df['mid_price']
                options_df = options_df[
                    (options_df['spread_pct'] <= max_spread_pct) & 
                    (options_df['spread_pct'].notna())
                ]
                logger.info(f"After spread filter (<={max_spread_pct*100:.0f}%): {len(options_df)} options")
            else:
                # Skip spread filter for historical data (no real bid/ask)
                logger.info(f"Skipping spread filter (using historical lastPrice data)")
            
            if len(options_df) == 0:
                raise ValueError(
                    f"No options remaining after filtering for {ticker}. "
                    f"Try: min_volume=0, max_spread_pct=0.50 (50%)"
                )
            
            # Calculate time to maturity for each option
            options_df['time_to_maturity'] = options_df['expiration'].apply(
                self.calculate_time_to_maturity
            )
            
            # Calculate moneyness
            options_df['moneyness'] = options_df['strike'].apply(
                lambda k: self.calculate_moneyness(k, current_price)
            )
            
            # Calculate implied volatility for each option
            iv_results = []
            failed_count = 0
            skip_count = 0
            
            logger.info(f"Starting IV calculation for {len(options_df)} options...")
            
            # Calculate IV for each option
            # Sanity checks :
            #   - Market price must exceed intrinsic value (allow 5% tolerance for bid-ask bounce)
            #   - IV must be reasonable: 1% ≤ σ ≤ 300%
            #   - Must converge within 50 iterations
            for idx, row in options_df.iterrows():
                try:
                    # Use mid price as market price
                    market_price = row['mid_price']
                    strike = row['strike']
                    
                    # Skip if price is too low (likely far OTM)
                    if market_price < 0.01:
                        skip_count += 1
                        continue
                    
                    # Calculate intrinsic value
                    if option_type == 'call':
                        intrinsic = max(current_price - strike, 0)
                    else:
                        intrinsic = max(strike - current_price, 0)
                    
                    # Skip if market price is less than intrinsic (arbitrage or bad data)
                    if market_price < intrinsic * 0.95:  # Allow 5% tolerance
                        skip_count += 1
                        logger.debug(f"Skipping strike {strike}: market_price ({market_price:.2f}) < intrinsic ({intrinsic:.2f})")
                        continue
                    
                    # Calculate IV
                    iv_result = self.iv_calculator.calculate_implied_volatility(
                        market_price=market_price,
                        S=current_price,
                        K=strike,
                        T=row['time_to_maturity'],
                        r=risk_free_rate,
                        option_type=option_type,
                        sigma_init=0.3,
                        tol=0.001,  # Relaxed tolerance for speed
                        max_iterations=50
                    )
                    
                    if iv_result['converged'] and 0.01 <= iv_result['implied_volatility'] <= 3.0:
                        iv_results.append({
                            'strike': row['strike'],
                            'expiration': row['expiration'],
                            'time_to_maturity': row['time_to_maturity'],
                            'moneyness': row['moneyness'],
                            'implied_volatility': iv_result['implied_volatility'],
                            'market_price': market_price,
                            'volume': row['volume'],
                            'open_interest': row.get('openInterest', 0)
                        })
                    else:
                        failed_count += 1
                        logger.debug(f"IV failed convergence for strike {row['strike']}: converged={iv_result['converged']}, IV={iv_result.get('implied_volatility', 'N/A')}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.debug(f"Failed to calculate IV for strike {row['strike']}: {str(e)}")
                    continue
            
            logger.info(
                f"IV Calculation complete: {len(iv_results)} succeeded, "
                f"{failed_count} failed, {skip_count} skipped (out of {len(options_df)} total)"
            )
            
            if not iv_results:
                error_msg = f"Could not calculate IV for any options of {ticker}. "
                error_msg += f"Processed {len(options_df)} options: {failed_count} failed IV convergence, {skip_count} skipped (price < $0.01 or arbitrage). "
                error_msg += "Try: 1) More liquid ticker (SPY, QQQ), 2) During market hours (9:30 AM-4:00 PM ET), "
                error_msg += "3) max_spread_pct=0.50, 4) min_volume=0"
                raise ValueError(error_msg)
            
            logger.info(f"Successfully calculated IV for {len(iv_results)} options")
            
            # Convert to DataFrame for easier manipulation
            surface_df = pd.DataFrame(iv_results)
            
            # Create grid data for 3D surface plot
            # Interpolate IV values onto regular grid
            strikes = np.sort(surface_df['strike'].unique())
            maturities = np.sort(surface_df['time_to_maturity'].unique())
            
            # Create meshgrid
            strike_grid = np.linspace(strikes.min(), strikes.max(), 30)
            maturity_grid = np.linspace(maturities.min(), maturities.max(), 20)
            
            Strike_mesh, Maturity_mesh = np.meshgrid(strike_grid, maturity_grid)
            
            # Interpolate IV values
            from scipy.interpolate import griddata
            
            points = surface_df[['strike', 'time_to_maturity']].values
            values = surface_df['implied_volatility'].values
            
            # Interpolate Scattered IV points onto regular grid
            # Why interpolation?
            #   - Market data is scattered (discrete strikes, irregular expirations)
            #   - Need a smooth surface for visualization and pricing intermediate strikes
            #   - method='cubic' gives smooth, continuous surface
            IV_mesh = griddata(
                points, 
                values, 
                (Strike_mesh, Maturity_mesh), 
                method='cubic',
                fill_value=np.nan
            )
            
            # Calculate moneyness for grid
            #   - Moneyness = 0: ATM (at-the-money)
            #   - Moneyness < 0: OTM calls / OTM puts
            #   - Moneyness > 0: ITM calls / ITM puts
            Moneyness_mesh = np.log(Strike_mesh / current_price)
            
            return {
                'ticker': ticker,
                'current_price': current_price,
                'option_type': option_type,
                'risk_free_rate': risk_free_rate,
                'data_points': len(iv_results),
                'using_historical_data': use_historical,
                'raw_data': iv_results,
                'surface_grid': {
                    'strikes': Strike_mesh.tolist(),
                    'maturities': Maturity_mesh.tolist(),
                    'moneyness': Moneyness_mesh.tolist(),
                    'implied_volatilities': IV_mesh.tolist()
                },
                'metadata': {
                    'min_strike': float(strikes.min()),
                    'max_strike': float(strikes.max()),
                    'min_maturity': float(maturities.min()),
                    'max_maturity': float(maturities.max()),
                    'min_iv': float(surface_df['implied_volatility'].min()),
                    'max_iv': float(surface_df['implied_volatility'].max()),
                    'avg_iv': float(surface_df['implied_volatility'].mean())
                }
            }
            
        except Exception as e:
            logger.error(f"Error building volatility surface: {str(e)}")
            raise
    
    def get_atm_volatility_term_structure(
        self, 
        ticker: str, 
        risk_free_rate: float = 0.05,
        option_type: str = 'call'
    ) -> List[Dict]:
        """
        Extract ATM (at-the-money) volatility term structure vs time to maturity
        Why ATM?
        - ATM option is most liquid
        - ATM volatility represents "pure" time value (no intrinsic value)
        - Shows Term structure of volatility expectations

        Typical patterns:
            - Contango: Short-term vol < long-term vol (normal market)
            - Backwardation: Short-term vol > long-term vol (stress/events)

        Args:
            ticker: Stock ticker symbol
            risk_free_rate: Risk-free rate
            option_type: 'call' or 'put'
            
        Returns:
            List of ATM volatility points by maturity
        """
        try:
            surface_data = self.build_surface(ticker, risk_free_rate, option_type)
            raw_data = surface_data['raw_data']
            current_price = surface_data['current_price']
            
            # Group by expiration and find ATM strike for each
            df = pd.DataFrame(raw_data)
            df['strike_diff'] = abs(df['strike'] - current_price)
            
            atm_vols = []
            for exp in df['expiration'].unique():
                exp_data = df[df['expiration'] == exp]
                atm_option = exp_data.loc[exp_data['strike_diff'].idxmin()]
                
                atm_vols.append({
                    'expiration': exp,
                    'time_to_maturity': atm_option['time_to_maturity'],
                    'strike': atm_option['strike'],
                    'implied_volatility': atm_option['implied_volatility']
                })
            
            # Sort by maturity
            atm_vols = sorted(atm_vols, key=lambda x: x['time_to_maturity'])
            
            return atm_vols
            
        except Exception as e:
            logger.error(f"Error extracting ATM term structure: {str(e)}")
            raise
