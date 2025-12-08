"""
Options Pricing Module

Implements multiple option pricing models:
1. Black-Scholes Model
2. Binomial Tree Model
3. Trinomial Tree Model
4. Greeks Calculation
"""

import numpy as np
from scipy.stats import norm
from typing import Dict, Optional, Tuple
import logging


class OptionsPricer:
    """
    Comprehensive options pricing calculator supporting multiple models
    """
    
    def __init__(self):
        """Initialize Options Pricer"""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Standard normal cumulative distribution function"""
        return norm.cdf(x)
    
    @staticmethod
    def _normal_pdf(x: float) -> float:
        """Standard normal probability density function"""
        return norm.pdf(x)
    
    def black_scholes(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'call'
    ) -> Dict[str, float]:
        """
        Black-Scholes option pricing model
        d1: Standardized distance to strike price, adjusted for drift and volatility over time
        d2: d1 minus volatility scaling, represents expected price at maturity

        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to maturity (in years)
            r (float): Risk-free interest rate (annualized)
            sigma (float): Volatility (annualized)
            option_type (str): 'call' or 'put'
            
        Returns:
            dict: Option price and Greeks
        """
        try:
            # Validate inputs
            if T <= 0:
                raise ValueError("Time to maturity must be positive")
            if sigma <= 0:
                raise ValueError("Volatility must be positive")
            if S <= 0 or K <= 0:
                raise ValueError("Stock and strike prices must be positive")
            
            # Calculate d1 and d2
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            # Calculate option price
            if option_type.lower() == 'call':
                price = S * self._normal_cdf(d1) - K * np.exp(-r * T) * self._normal_cdf(d2)
                delta = self._normal_cdf(d1)
                theta = (-(S * self._normal_pdf(d1) * sigma) / (2 * np.sqrt(T)) 
                        - r * K * np.exp(-r * T) * self._normal_cdf(d2))
            else:  # put
                price = K * np.exp(-r * T) * self._normal_cdf(-d2) - S * self._normal_cdf(-d1)
                delta = -self._normal_cdf(-d1)
                theta = (-(S * self._normal_pdf(d1) * sigma) / (2 * np.sqrt(T)) 
                        + r * K * np.exp(-r * T) * self._normal_cdf(-d2))
            
            # Calculate Greeks (common for both call and put)
            gamma = self._normal_pdf(d1) / (S * sigma * np.sqrt(T))
            vega = S * np.sqrt(T) * self._normal_pdf(d1)
            
            if option_type.lower() == 'call':
                rho = K * T * np.exp(-r * T) * self._normal_cdf(d2)
            else:
                rho = -K * T * np.exp(-r * T) * self._normal_cdf(-d2)
            
            return {
                'price': float(price),
                'delta': float(delta),
                'gamma': float(gamma),
                'theta': float(theta / 365),  # Convert to per-day
                'vega': float(vega / 100),    # Convert to per 1% change in volatility
                'rho': float(rho / 100),      # Convert to per 1% change in interest rate
                'd1': float(d1),
                'd2': float(d2)
            }
            
        except Exception as e:
            self.logger.error(f"Error in Black-Scholes calculation: {e}")
            raise
    
    def binomial_tree(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        N: int = 100,
        option_type: str = 'call',
        exercise_type: str = 'european'
    ) -> Dict[str, float]:
        """
        Discrete-time approximation of the continuous Black-Scholes world
        
        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to maturity (in years)
            r (float): Risk-free interest rate
            sigma (float): Volatility
            N (int): Number of time steps
            option_type (str): 'call' or 'put'
            exercise_type (str): 'european' or 'american'
            
        Returns:
            dict: Option price and convergence info
        """
        try:
            # Calculate time step
            dt = T / N
            
            # Calculate up and down factors
            u = np.exp(sigma * np.sqrt(dt))
            d = 1 / u
            
            # Risk-neutral probability
            p = (np.exp(r * dt) - d) / (u - d)
            
            # Validate probability
            if not (0 <= p <= 1):
                raise ValueError(f"Invalid risk-neutral probability: {p}")
            
            # Initialize asset prices at maturity
            asset_prices = np.zeros(N + 1)
            for i in range(N + 1):
                asset_prices[i] = S * (u ** (N - i)) * (d ** i)
            
            # Initialize option values at maturity
            if option_type.lower() == 'call':
                option_values = np.maximum(asset_prices - K, 0)
            else:  # put
                option_values = np.maximum(K - asset_prices, 0)
            
            # Backward induction
            for j in range(N - 1, -1, -1):
                for i in range(j + 1):
                    # Calculate discounted expected value
                    option_values[i] = np.exp(-r * dt) * (
                        p * option_values[i] + (1 - p) * option_values[i + 1]
                    )
                    
                    # For American options, check early exercise
                    if exercise_type.lower() == 'american':
                        stock_price = S * (u ** (j - i)) * (d ** i)
                        if option_type.lower() == 'call':
                            exercise_value = max(stock_price - K, 0)
                        else:
                            exercise_value = max(K - stock_price, 0)
                        option_values[i] = max(option_values[i], exercise_value)
            
            return {
                'price': float(option_values[0]),
                'steps': N,
                'u': float(u),
                'd': float(d),
                'p': float(p)
            }
            
        except Exception as e:
            self.logger.error(f"Error in Binomial Tree calculation: {e}")
            raise
    
    def trinomial_tree(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        N: int = 100,
        option_type: str = 'call',
        exercise_type: str = 'european'
    ) -> Dict[str, float]:
        """
        Trinomial tree option pricing model
        
        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to maturity (in years)
            r (float): Risk-free interest rate
            sigma (float): Volatility
            N (int): Number of time steps
            option_type (str): 'call' or 'put'
            exercise_type (str): 'european' or 'american'
            
        Returns:
            dict: Option price and convergence info
        """
        try:
            # Calculate time step
            h = T / N
            discount = np.exp(-r * h)
            
            # Calculate up and down factors
            u = np.exp(sigma * np.sqrt(2 * h))
            d = 1 / u
            
            # Risk-neutral probabilities
            pu = ((np.exp(r * h / 2) - np.exp(-sigma * np.sqrt(h / 2))) /
                  (np.exp(sigma * np.sqrt(h / 2)) - np.exp(-sigma * np.sqrt(h / 2))))**2
            pd = ((np.exp(r * h / 2) - np.exp(sigma * np.sqrt(h / 2))) /
                  (np.exp(sigma * np.sqrt(h / 2)) - np.exp(-sigma * np.sqrt(h / 2))))**2
            pm = 1 - pu - pd
            
            # Validate probabilities
            if not (0 <= pu <= 1 and 0 <= pd <= 1 and 0 <= pm <= 1):
                raise ValueError(f"Invalid probabilities: pu={pu}, pd={pd}, pm={pm}")
            
            # Initialize stock prices at maturity
            stock_vec = self._gen_stock_vec_trinomial(S, N, u, d)
            
            # Initialize option payoffs
            if option_type.lower() == 'call':
                option_values = np.maximum(stock_vec - K, 0)
            else:
                option_values = np.maximum(K - stock_vec, 0)
            
            # Backward induction
            for i in range(1, N + 1):
                stock_vec = self._gen_stock_vec_trinomial(S, N - i, u, d)
                expectation = np.zeros(len(stock_vec))
                
                for j in range(len(expectation)):
                    expectation[j] = (option_values[j] * pd +
                                     option_values[j + 1] * pm +
                                     option_values[j + 2] * pu)
                
                option_values = discount * expectation
                
                # For American options, check early exercise
                if exercise_type.lower() == 'american':
                    for j in range(len(stock_vec)):
                        if option_type.lower() == 'call':
                            exercise_value = max(stock_vec[j] - K, 0)
                        else:
                            exercise_value = max(K - stock_vec[j], 0)
                        option_values[j] = max(option_values[j], exercise_value)
            
            return {
                'price': float(option_values[0]),
                'steps': N,
                'u': float(u),
                'd': float(d),
                'pu': float(pu),
                'pd': float(pd),
                'pm': float(pm)
            }
            
        except Exception as e:
            self.logger.error(f"Error in Trinomial Tree calculation: {e}")
            raise
    
    @staticmethod
    def _gen_stock_vec_trinomial(S0: float, nb: int, u: float, d: float) -> np.ndarray:
        """
        Generate stock price vector for trinomial tree
        
        Args:
            S0 (float): Initial stock price
            nb (int): Number of steps
            u (float): Up factor
            d (float): Down factor
            
        Returns:
            np.ndarray: Stock price vector
        """
        vec_u = u * np.ones(nb)
        np.cumprod(vec_u, out=vec_u)
        
        vec_d = d * np.ones(nb)
        np.cumprod(vec_d, out=vec_d)
        
        vec = np.concatenate([vec_d[::-1], [1.0], vec_u])
        return S0 * vec
    
    def calculate_all_greeks(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'call'
    ) -> Dict[str, float]:
        """
        Calculate all Greeks for an option
        Delta: Rate of change with respect to S (current stock price)
            - Call: ranges from 0 to 1
            - Put: ranges from -1 to 0

        Gamma: Rate of change of Delta with respect to S. Same for calls and puts, measures convexity/curvature of option price
            Formula: φ(d1) / (S * σ * √T)

        Theta: Rate of change with respect to time (T)
            - Call: -(S * φ(d1) * σ) / (2√T) - r * K * exp(-rT) * N(d2)
            - Put: -(S * φ(d1) * σ) / (2√T) + r * K * exp(-rT) * N(-d2)
            - First Term: Volatility decay (Common to both calls and puts)
            - Second Term: Interest rate effect (Differs for calls and puts)
            Divided by 365 for per-day theta

        Vega: Rate of change with respect to volatility (sigma)
            Formula : vega = S * √T * φ(d1)
            Divided by 100 for per 1% volatility change

        Rho: Rate of change with respect to risk-free rate (r)
            - Call: K * T * exp(-rT) * N(d2) 
            - Put: -K * T * exp(-rT) * N(-d2)
            Divided by 100 for per 1% interest rate change

        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to maturity
            r (float): Risk-free rate
            sigma (float): Volatility
            option_type (str): 'call' or 'put'
            
        Returns:
            dict: All Greeks
        """
        result = self.black_scholes(S, K, T, r, sigma, option_type)
        return {
            'delta': result['delta'],
            'gamma': result['gamma'],
            'theta': result['theta'],
            'vega': result['vega'],
            'rho': result['rho']
        }
    
    def compare_models(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'call',
        N: int = 100
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare prices across different pricing models
        
        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to maturity
            r (float): Risk-free rate
            sigma (float): Volatility
            option_type (str): 'call' or 'put'
            N (int): Number of steps for tree models
            
        Returns:
            dict: Comparison of all models
        """
        try:
            bs_result = self.black_scholes(S, K, T, r, sigma, option_type)
            binomial_result = self.binomial_tree(S, K, T, r, sigma, N, option_type, 'european')
            trinomial_result = self.trinomial_tree(S, K, T, r, sigma, N, option_type, 'european')
            
            return {
                'black_scholes': {
                    'price': bs_result['price'],
                    'model': 'Black-Scholes'
                },
                'binomial': {
                    'price': binomial_result['price'],
                    'steps': binomial_result['steps'],
                    'model': 'Binomial Tree'
                },
                'trinomial': {
                    'price': trinomial_result['price'],
                    'steps': trinomial_result['steps'],
                    'model': 'Trinomial Tree'
                },
                'differences': {
                    'binomial_vs_bs': abs(binomial_result['price'] - bs_result['price']),
                    'trinomial_vs_bs': abs(trinomial_result['price'] - bs_result['price']),
                    'binomial_vs_trinomial': abs(binomial_result['price'] - trinomial_result['price'])
                }
            }
        except Exception as e:
            self.logger.error(f"Error comparing models: {e}")
            raise
