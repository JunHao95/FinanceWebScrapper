"""
Derivatives Module

Provides derivative pricing and analysis capabilities including:
1. Options Pricing (Binomial, Trinomial, Black-Scholes)
2. Implied Volatility Extraction (Newton-Raphson)
3. Greeks Calculation
4. Volatility Surface Construction
"""

from .options_pricer import OptionsPricer
from .implied_volatility import ImpliedVolatilityCalculator
from .trinomial_model import TrinomialModel

__all__ = ['OptionsPricer', 'ImpliedVolatilityCalculator', 'TrinomialModel']
