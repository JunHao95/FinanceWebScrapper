"""
Implied Volatility Calculator Module

Implements Newton-Raphson method for extracting implied volatility
from market option prices.
"""

import numpy as np
from typing import Dict, List, Optional
import logging
from scipy.stats import norm


class ImpliedVolatilityCalculator:
    """
    Calculate implied volatility using Newton-Raphson method
    """
    
    def __init__(self):
        """Initialize Implied Volatility Calculator"""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Standard normal cumulative distribution function"""
        return norm.cdf(x)
    
    @staticmethod
    def _normal_pdf(x: float) -> float:
        """Standard normal probability density function"""
        return norm.pdf(x)
    
    def black_scholes_price(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'call'
    ) -> float:
        """
        Calculate Black-Scholes option price

        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to maturity
            r (float): Risk-free rate
            sigma (float): Volatility
            option_type (str): 'call' or 'put'
            
        Returns:
            float: Option price
        """
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == 'call':
            price = S * self._normal_cdf(d1) - K * np.exp(-r * T) * self._normal_cdf(d2)
        else:
            price = K * np.exp(-r * T) * self._normal_cdf(-d2) - S * self._normal_cdf(-d1)
        
        return price
    
    def vega(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """
        Calculate vega (sensitivity to volatility), measures how much the option price changes with a 1% change in volatility.
        d1 represents the "distance" to the strike price in standardized terms, accounting for drift. 
        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to maturity
            r (float): Risk-free rate
            sigma (float): Volatility
            
        Returns:
            float: Vega value
        """
        d1 = (np.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T)) # 1st term: Log-moneyness (how far stock price is from strike), 2nd term: Drift adjustment incorporating risk-free rate, 3rd term: Volatility scaling by square root of time (S.D of returns)
        vega = S * np.sqrt(T) * self._normal_pdf(d1)
        return vega
    
    def calculate_implied_volatility(
        self,
        market_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str = 'call',
        sigma_init: float = 0.3,
        tol: float = 0.0001,
        max_iterations: int = 100
    ) -> Dict[str, any]:
        """
        
        Unlike calculating an option price from known volatility, IV reverses the problem: given a market price, what volatility must the Black-Scholes model assume to produce that price?
        As no closed-form solution exists for IV, we use the Newton-Raphson iterative method to approximate it.
        BS price increases monotonically with sigma, so there's a unique IV for each market price (no multiple solutions)
        
        Args:
            market_price (float): Observed market price of option
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to maturity
            r (float): Risk-free rate
            option_type (str): 'call' or 'put'
            sigma_init (float): Initial volatility guess
            tol (float): Tolerance for convergence
            max_iterations (int): Maximum number of iterations
            
        Returns:
            dict: Implied volatility and iteration details
        """
        try:
            # Validate inputs
            if market_price <= 0:
                raise ValueError("Market price must be positive")
            if T <= 0:
                raise ValueError("Time to maturity must be positive")
            if S <= 0 or K <= 0:
                raise ValueError("Stock and strike prices must be positive")
            
            # Check for early exercise value (for American options)
            if option_type.lower() == 'call':
                intrinsic_value = max(S - K, 0)
            else:
                intrinsic_value = max(K - S, 0)
            
            if market_price < intrinsic_value:
                raise ValueError(f"Market price ({market_price}) is less than intrinsic value ({intrinsic_value})")
            
            sigma = sigma_init
            iterations = []
            
            for i in range(max_iterations):
                # Calculate Black-Scholes price with current sigma adn given market_price
                bs_price = self.black_scholes_price(S, K, T, r, sigma, option_type)
                diff = bs_price - market_price  # Difference between Black-Scholes model price and market price will be used for iteration
                
                # Record iteration
                iterations.append({
                    'iteration': i + 1,
                    'sigma': float(sigma),
                    'price': float(bs_price),
                    'difference': float(diff),
                    'abs_diff': float(abs(diff))
                })
                
                # Check for convergence
                if abs(diff) < tol:
                    self.logger.info(f"Converged in {i + 1} iterations")
                    return {
                        'implied_volatility': float(sigma),
                        'iterations': iterations,
                        'converged': True,
                        'final_difference': float(diff),
                        'num_iterations': i + 1
                    }
                
                # Calculate vega
                vega_value = self.vega(S, K, T, r, sigma) # It tells us how much to adjust sigma to close the pricing gap
                
                # Check if vega is too small. Deep OTM/ITM options have low vega, making denominator tiny and causing numerical instability
                if abs(vega_value) < 1e-10:
                    raise ValueError("Vega too small, cannot continue iteration")
                
                # Newton-Raphson update, Core Iteration here!
                sigma = sigma - diff / vega_value
                
                # Ensure sigma stays positive
                if sigma <= 0:
                    sigma = 0.01
                
                # Prevent sigma from becoming unreasonably large
                if sigma > 5.0:
                    sigma = 5.0
            
            # Did not converge within max iterations
            self.logger.warning(f"Did not converge after {max_iterations} iterations")
            return {
                'implied_volatility': float(sigma),
                'iterations': iterations,
                'converged': False,
                'final_difference': float(diff),
                'num_iterations': max_iterations
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating implied volatility: {e}")
            raise
    
    def calculate_implied_volatility_surface(
        self,
        options_data: List[Dict],
        S: float,
        r: float
    ) -> List[Dict]:
        """
        Extends IV calculation to an entire options chain
        Takes multiple options (different strikes and maturities) and computes their implied volatilities. 
        Returns surface points with moneyness = ln(K/S) and time to maturity.
        Can be used to visualized the volatility smile/skew
        
        Args:
            options_data (list): List of option data dictionaries with keys:
                                'strike', 'price', 'maturity', 'type'
            S (float): Current stock price
            r (float): Risk-free rate
            
        Returns:
            list: Surface data points with moneyness, time to maturity, and IV
        """
        surface_points = []
        
        for option in options_data:
            try:
                strike = option['strike']
                market_price = option['price']
                T = option['maturity']  # Should be in years
                option_type = option.get('type', 'call')
                
                # Skip if invalid data
                if market_price <= 0 or T <= 0 or strike <= 0:
                    continue
                
                # Calculate implied volatility
                result = self.calculate_implied_volatility(
                    market_price, S, strike, T, r, option_type
                )
                
                if result['converged']:
                    # Calculate moneyness
                    moneyness = np.log(strike / S)
                    
                    surface_points.append({
                        'strike': float(strike),
                        'moneyness': float(moneyness),
                        'time_to_maturity': float(T),
                        'implied_volatility': result['implied_volatility'],
                        'option_type': option_type,
                        'iterations': result['num_iterations']
                    })
            
            except Exception as e:
                self.logger.warning(f"Could not calculate IV for strike {option.get('strike')}: {e}")
                continue
        
        return surface_points
    
    def validate_implied_volatility(
        self,
        implied_vol: float,
        market_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str = 'call'
    ) -> Dict[str, float]:
        """
        Validate calculated implied volatility by re-pricing
        
        Args:
            implied_vol (float): Calculated implied volatility
            market_price (float): Market price
            S (float): Stock price
            K (float): Strike price
            T (float): Time to maturity
            r (float): Risk-free rate
            option_type (str): 'call' or 'put'
            
        Returns:
            dict: Validation results
        """
        bs_price = self.black_scholes_price(S, K, T, r, implied_vol, option_type)
        difference = abs(bs_price - market_price)
        percentage_error = (difference / market_price) * 100 if market_price > 0 else 0
        
        return {
            'recalculated_price': float(bs_price),
            'market_price': float(market_price),
            'absolute_difference': float(difference),
            'percentage_error': float(percentage_error),
            'is_valid': percentage_error < 0.1  # Within 0.1%
        }
