"""
Trinomial Tree Model Module

Object-oriented implementation of the trinomial tree model
for option pricing with convergence analysis.
"""

import numpy as np
from typing import Dict, List, Optional
import logging


class TrinomialModel:
    """
    Trinomial tree model for option pricing
    """
    
    def __init__(self, S0: float, r: float, sigma: float, T: float):
        """
        Initialize Trinomial Model
        
        Args:
            S0 (float): Initial stock price
            r (float): Risk-free rate
            sigma (float): Volatility
            T (float): Time to maturity
        """
        self.__s0 = S0
        self.__r = r
        self.__sigma = sigma
        self.__T = T
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def __compute_probs(self):
        """Compute risk-neutral probabilities"""
        self.__pu = (
            (np.exp(self.__r * self.__h / 2) - np.exp(-self.__sigma * np.sqrt(self.__h / 2)))
            / (np.exp(self.__sigma * np.sqrt(self.__h / 2)) - np.exp(-self.__sigma * np.sqrt(self.__h / 2)))
        ) ** 2
        
        self.__pd = (
            (-np.exp(self.__r * self.__h / 2) + np.exp(self.__sigma * np.sqrt(self.__h / 2)))
            / (np.exp(self.__sigma * np.sqrt(self.__h / 2)) - np.exp(-self.__sigma * np.sqrt(self.__h / 2)))
        ) ** 2
        
        self.__pm = 1 - self.__pu - self.__pd
        
        # Validate probabilities
        assert 0 <= self.__pu <= 1.0, f"p_u should lie in [0, 1], got {self.__pu}"
        assert 0 <= self.__pd <= 1.0, f"p_d should lie in [0, 1], got {self.__pd}"
        assert 0 <= self.__pm <= 1.0, f"p_m should lie in [0, 1], got {self.__pm}"
    
    def __check_up_value(self, up: Optional[float] = None):
        """
        Check and set up/down values for recombining tree
        
        
        """
        if up is None:
            up = np.exp(self.__sigma * np.sqrt(2 * self.__h))
        
        assert up > 0.0, "up should be non-negative"
        
        down = 1 / up
        assert down < up, "up <= 1/up = down (recombining tree condition violated)"
        
        self.__up = up
        self.__down = down
    
    def __gen_stock_vec(self, nb: int) -> np.ndarray:
        """
        Generate stock price vector for given number of steps
        
        Args:
            nb (int): Number of steps
            
        Returns:
            np.ndarray: Stock price vector
        """
        vec_u = self.__up * np.ones(nb)
        np.cumprod(vec_u, out=vec_u)
        
        vec_d = self.__down * np.ones(nb)
        np.cumprod(vec_d, out=vec_d)
        
        vec = np.concatenate([vec_d[::-1], [1.0], vec_u])
        return self.__s0 * vec
    
    def price_option(
        self,
        K: float,
        nb_steps: int,
        option_type: str = 'call',
        exercise_type: str = 'european',
        up: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Price option using trinomial tree
        
        Args:
            K (float): Strike price
            nb_steps (int): Number of time steps
            option_type (str): 'call' or 'put'
            exercise_type (str): 'european' or 'american'
            up (float, optional): Up factor (calculated if not provided)
            
        Returns:
            dict: Pricing results including price and tree parameters
        """
        try:
            # Set time step
            self.__h = self.__T / nb_steps
            
            # Compute discount factor
            discount = np.exp(-self.__r * self.__h)
            
            # Check and set up/down values
            self.__check_up_value(up)
            
            # Compute probabilities
            self.__compute_probs()
            
            # Generate stock prices at maturity
            s = self.__gen_stock_vec(nb_steps)
            
            # Define payoff at maturity
            if option_type.lower() == 'call':
                final_payoff = np.maximum(s - K, 0)
            else:  # put
                final_payoff = np.maximum(K - s, 0)
            
            nxt_vec_prices = final_payoff
            
            # Backward induction
            for i in range(1, nb_steps + 1):
                vec_stock = self.__gen_stock_vec(nb_steps - i)
                expectation = np.zeros(vec_stock.size)
                
                for j in range(expectation.size):
                    tmp = nxt_vec_prices[j] * self.__pd
                    tmp += nxt_vec_prices[j + 1] * self.__pm
                    tmp += nxt_vec_prices[j + 2] * self.__pu
                    expectation[j] = tmp
                
                # Discount expected payoff
                nxt_vec_prices = discount * expectation
                
                # For American options, check early exercise
                if exercise_type.lower() == 'american':
                    for j in range(len(vec_stock)):
                        if option_type.lower() == 'call':
                            exercise_value = max(vec_stock[j] - K, 0)
                        else:
                            exercise_value = max(K - vec_stock[j], 0)
                        nxt_vec_prices[j] = max(nxt_vec_prices[j], exercise_value)
            
            return {
                'price': float(nxt_vec_prices[0]),
                'steps': nb_steps,
                'up': float(self.__up),
                'down': float(self.__down),
                'p_up': float(self.__pu),
                'p_down': float(self.__pd),
                'p_mid': float(self.__pm),
                'dt': float(self.__h),
                'discount_factor': float(discount)
            }
            
        except Exception as e:
            self.logger.error(f"Error pricing option with trinomial tree: {e}")
            raise
    
    def analyze_convergence(
        self,
        K: float,
        step_range: List[int],
        option_type: str = 'call',
        exercise_type: str = 'european'
    ) -> List[Dict[str, float]]:
        """
        Analyze price convergence across different step sizes
        Expected Behaviours:
            - As steps increase, price should stabilize
            - Price changes should decrease with more steps
            - For European options, should only converge to Black-Scholes price

        Trinomial Advantage:
            - Converge faster than binomial due to fewer steps needed for similar accuracy
            - Better stability (3 probs provide more flexibility)

        Args:
            K (float): Strike price
            step_range (list): List of step counts to test
            option_type (str): 'call' or 'put'
            exercise_type (str): 'european' or 'american'
            
        Returns:
            list: Convergence data for each step count
        """
        convergence_data = []
        
        for steps in step_range:
            try:
                result = self.price_option(K, steps, option_type, exercise_type)
                convergence_data.append({
                    'steps': steps,
                    'price': result['price']
                })
            except Exception as e:
                self.logger.warning(f"Could not price with {steps} steps: {e}")
                continue
        
        # Calculate price differences
        if len(convergence_data) > 1:
            for i in range(1, len(convergence_data)):
                prev_price = convergence_data[i-1]['price']
                curr_price = convergence_data[i]['price']
                convergence_data[i]['price_change'] = abs(curr_price - prev_price)
                convergence_data[i]['percent_change'] = (
                    abs(curr_price - prev_price) / prev_price * 100 
                    if prev_price > 0 else 0
                )
        
        return convergence_data
    
    def get_tree_parameters(self) -> Dict[str, float]:
        """
        Get current tree parameters
        
        Returns:
            dict: Tree parameters
        """
        return {
            'S0': float(self.__s0),
            'r': float(self.__r),
            'sigma': float(self.__sigma),
            'T': float(self.__T)
        }
