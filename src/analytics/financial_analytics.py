"""
Financial Analytics Module

Provides advanced analytics capabilities including:
1. Linear Regression on Asset Returns (not prices)
2. PCA with Data Standardization and Interpretation
3. Monte Carlo Simulation for VaR and Expected Shortfall
4. Basic Correlation Analysis
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
import yfinance as yf


class FinancialAnalytics:
    """
    Advanced financial analytics for portfolio analysis and risk management
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Financial Analytics module
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
    
    def _get_portfolio_weights(self, tickers: List[str]) -> Dict[str, float]:
        """
        Get portfolio weights from config or return equal weights
        
        Args:
            tickers (list): List of ticker symbols
            
        Returns:
            dict: Portfolio weights for each ticker
        """
        weights = {}
        
        # Try to get weights from config
        if self.config and 'portfolio' in self.config:
            portfolio_config = self.config['portfolio']
            if 'allocations' in portfolio_config:
                config_allocations = portfolio_config['allocations']
                
                # Get weights for requested tickers
                for ticker in tickers:
                    if ticker in config_allocations:
                        weights[ticker] = float(config_allocations[ticker])
        
        # If we got weights for some tickers, use them
        if weights:
            # For tickers not in config, assign equal weight from remaining
            missing_tickers = [t for t in tickers if t not in weights]
            if missing_tickers:
                # Calculate remaining weight
                used_weight = sum(weights.values())
                remaining_weight = max(0, 1.0 - used_weight)
                equal_share = remaining_weight / len(missing_tickers) if missing_tickers else 0
                for ticker in missing_tickers:
                    weights[ticker] = equal_share
            
            self.logger.info(f"Using portfolio weights from config for {len(weights)} tickers")
            return weights
        
        # Fall back to equal weights
        self.logger.info(f"No config weights found, using equal weights for {len(tickers)} tickers")
        return {ticker: 1.0/len(tickers) for ticker in tickers}
        
    def get_historical_returns(
        self, 
        tickers: List[str], 
        days: int = 252,
        return_type: str = 'simple'
    ) -> pd.DataFrame:
        """
        Get historical returns for multiple tickers
        
        Args:
            tickers (list): List of stock ticker symbols
            days (int): Number of trading days to fetch
            return_type (str): 'simple' or 'log' returns
            
        Returns:
            pd.DataFrame: DataFrame with returns for each ticker
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=int(days * 1.5))  # Buffer for weekends/holidays
            
            self.logger.info(f"Fetching historical data for {len(tickers)} tickers")
            
            # Download data for all tickers
            data = yf.download(
                tickers, 
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                auto_adjust=True,
                progress=False
            )
            
            # Check if download returned any data
            if data.empty:
                self.logger.warning("yfinance returned empty data for all tickers")
                return pd.DataFrame()
            
            # Handle both single and multiple tickers
            if len(tickers) == 1:
                # For single ticker, yfinance returns a DataFrame with columns like 'Close', 'Open', etc.
                # Extract the 'Close' column and convert to DataFrame with ticker name
                if isinstance(data['Close'], pd.Series):
                    prices = data['Close'].to_frame(name=tickers[0])
                else:
                    prices = data['Close']
                    if not isinstance(prices, pd.DataFrame):
                        prices = pd.DataFrame(prices, columns=[tickers[0]])
            else:
                prices = data['Close']
            
            # Remove columns (tickers) that are entirely NaN or empty (failed downloads)
            if isinstance(prices, pd.DataFrame):
                original_columns = list(prices.columns)
                prices = prices.dropna(axis=1, how='all')
                failed_tickers = set(original_columns) - set(prices.columns)
                if failed_tickers:
                    self.logger.warning(f"Failed to fetch data for tickers: {failed_tickers}")
                successful_tickers = list(prices.columns)
                if successful_tickers:
                    self.logger.info(f"Successfully fetched data for {len(successful_tickers)} tickers: {successful_tickers}")
            
            # Check if we have any valid price data
            if prices.empty or len(prices.columns) == 0:
                self.logger.warning("No valid price data after removing failed tickers")
                return pd.DataFrame()
            
            # Calculate returns
            if return_type == 'log':
                returns = np.log(prices / prices.shift(1))
            else:  # simple returns
                returns = prices.pct_change()
            
            # Drop rows with NaN values (first row will always be NaN after pct_change)
            returns = returns.dropna()
            
            # Remove any columns that still have too many NaN values (>50%)
            if not returns.empty:
                threshold = len(returns) * 0.5
                returns = returns.dropna(axis=1, thresh=int(threshold))
            
            # Check if we still have data after cleanup
            if returns.empty or len(returns.columns) == 0:
                self.logger.warning("No valid returns data after NaN removal")
                return pd.DataFrame()
            
            # Ensure we have the requested number of days (approximately)
            if len(returns) > days:
                returns = returns.tail(days)
            
            self.logger.info(f"Successfully fetched {len(returns)} days of returns for {len(returns.columns)} tickers")
            return returns
            
        except Exception as e:
            self.logger.error(f"Error fetching historical returns: {str(e)}")
            return pd.DataFrame()
    
    def linear_regression_analysis(
        self, 
        tickers: List[str], 
        benchmark: str = '^GSPC',
        days: int = 252
    ) -> Dict:
        """
        Perform linear regression on asset returns vs benchmark
        
        This analyzes the relationship between individual stock returns
        and market returns (beta analysis)
        
        Args:
            tickers (list): List of stock ticker symbols
            benchmark (str): Benchmark ticker (default: S&P 500)
            days (int): Number of trading days
            
        Returns:
            dict: Regression statistics for each ticker
        """
        try:
            self.logger.info(f"Performing linear regression analysis for {len(tickers)} tickers")
            
            # Get returns for tickers and benchmark
            all_tickers = tickers + [benchmark]
            returns = self.get_historical_returns(all_tickers, days=days)
            
            if returns.empty:
                return {"error": "Could not fetch returns data"}
            
            # Ensure benchmark is in returns
            if benchmark not in returns.columns:
                return {"error": f"Benchmark {benchmark} not found in returns"}
            
            results = {}
            benchmark_returns = returns[benchmark].values.reshape(-1, 1)
            
            for ticker in tickers:
                if ticker not in returns.columns:
                    self.logger.warning(f"Ticker {ticker} not found in returns")
                    continue
                
                try:
                    # Prepare data
                    ticker_returns = returns[ticker].values.reshape(-1, 1)
                    
                    # Fit linear regression: Y = alpha + beta * X
                    # Where Y = stock returns, X = benchmark returns
                    model = LinearRegression()
                    model.fit(benchmark_returns, ticker_returns)
                    
                    # Get predictions
                    predictions = model.predict(benchmark_returns)
                    
                    # Calculate statistics
                    beta = float(model.coef_[0][0])
                    alpha = float(model.intercept_[0])
                    
                    # R-squared
                    ss_res = np.sum((ticker_returns - predictions) ** 2)
                    ss_tot = np.sum((ticker_returns - np.mean(ticker_returns)) ** 2)
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                    
                    # Calculate residuals statistics
                    residuals = ticker_returns - predictions
                    residual_std = float(np.std(residuals))
                    
                    # Calculate correlation
                    correlation = float(np.corrcoef(
                        benchmark_returns.flatten(), 
                        ticker_returns.flatten()
                    )[0, 1])
                    
                    # Annualize alpha (daily to annual)
                    annualized_alpha = alpha * 252
                    
                    # Information ratio (excess return over benchmark relative to tracking error)
                    excess_returns = ticker_returns.flatten() - predictions.flatten()
                    tracking_error = np.std(excess_returns) * np.sqrt(252)
                    mean_excess_return = np.mean(excess_returns) * 252
                    information_ratio = mean_excess_return / tracking_error if tracking_error != 0 else 0
                    
                    results[ticker] = {
                        "Beta": round(beta, 4),
                        "Alpha (Daily)": round(alpha, 6),
                        "Alpha (Annualized)": round(annualized_alpha, 4),
                        "R-Squared": round(r_squared, 4),
                        "Correlation": round(correlation, 4),
                        "Residual Std Dev": round(residual_std, 6),
                        "Tracking Error (Ann.)": round(tracking_error, 4),
                        "Information Ratio": round(information_ratio, 4),
                        "Interpretation": self._interpret_regression(beta, alpha, r_squared),
                        "Data Points": len(ticker_returns)
                    }
                    
                except Exception as e:
                    self.logger.error(f"Error in regression for {ticker}: {str(e)}")
                    results[ticker] = {"error": str(e)}
            
            # Add benchmark info
            results["Benchmark"] = benchmark
            results["Analysis Period"] = f"{days} trading days"
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in linear regression analysis: {str(e)}")
            return {"error": str(e)}
    
    def _interpret_regression(self, beta: float, alpha: float, r_squared: float) -> str:
        """
        Interpret regression results
        
        Args:
            beta (float): Beta coefficient
            alpha (float): Alpha (intercept)
            r_squared (float): R-squared value
            
        Returns:
            str: Human-readable interpretation
        """
        # Beta interpretation
        if beta > 1.2:
            beta_desc = "High volatility - amplifies market movements"
        elif beta > 1.0:
            beta_desc = "Moderate volatility - slightly amplifies market"
        elif beta > 0.8:
            beta_desc = "Moderate volatility - tracks market closely"
        elif beta > 0.5:
            beta_desc = "Low volatility - dampens market movements"
        elif beta > 0:
            beta_desc = "Very low volatility - weak market correlation"
        else:
            beta_desc = "Negative correlation - inverse market relationship"
        
        # Alpha interpretation (annualized)
        alpha_ann = alpha * 252
        if alpha_ann > 0.05:
            alpha_desc = "Strong outperformance"
        elif alpha_ann > 0.02:
            alpha_desc = "Moderate outperformance"
        elif alpha_ann > -0.02:
            alpha_desc = "Market-level performance"
        elif alpha_ann > -0.05:
            alpha_desc = "Moderate underperformance"
        else:
            alpha_desc = "Significant underperformance"
        
        # R-squared interpretation
        if r_squared > 0.7:
            fit_desc = "Strong explanatory power"
        elif r_squared > 0.4:
            fit_desc = "Moderate explanatory power"
        else:
            fit_desc = "Weak explanatory power"
        
        return f"{beta_desc}; {alpha_desc}; {fit_desc}"
    
    def pca_analysis(
        self, 
        tickers: List[str], 
        days: int = 252,
        n_components: Optional[int] = None
    ) -> Dict:
        """
        Perform Principal Component Analysis on asset returns with standardization
        
        Args:
            tickers (list): List of stock ticker symbols
            days (int): Number of trading days
            n_components (int, optional): Number of components to keep
            
        Returns:
            dict: PCA results with interpretation
        """
        try:
            self.logger.info(f"Performing PCA analysis for {len(tickers)} tickers")
            
            # Get returns data
            returns = self.get_historical_returns(tickers, days=days)
            
            if returns.empty or len(returns.columns) < 2:
                return {"error": "Insufficient data for PCA analysis"}
            
            # Drop any columns with NaN values
            returns = returns.dropna(axis=1)
            
            if len(returns.columns) < 2:
                return {"error": "Need at least 2 assets for PCA"}
            
            # Standardize the data (zero mean, unit variance)
            scaler = StandardScaler()
            returns_standardized = scaler.fit_transform(returns)
            
            # Determine number of components
            if n_components is None:
                n_components = min(len(returns.columns), len(returns))
            
            # Perform PCA
            pca = PCA(n_components=n_components)
            principal_components = pca.fit_transform(returns_standardized)
            
            # Create results dictionary
            results = {
                "Standardization": {
                    "Mean": {ticker: round(float(mean), 6) 
                            for ticker, mean in zip(returns.columns, scaler.mean_)},
                    "Std Dev": {ticker: round(float(std), 6) 
                               for ticker, std in zip(returns.columns, scaler.scale_)},
                    "Explanation": "Data standardized to zero mean and unit variance"
                },
                "Explained Variance Ratio": {
                    f"PC{i+1}": round(float(var), 4) 
                    for i, var in enumerate(pca.explained_variance_ratio_)
                },
                "Cumulative Variance Explained": {
                    f"PC{i+1}": round(float(cum_var), 4) 
                    for i, cum_var in enumerate(np.cumsum(pca.explained_variance_ratio_))
                },
                "Component Loadings": {},
                "Interpretation": {}
            }
            
            # Get component loadings (how much each asset contributes to each PC)
            loadings = pca.components_
            
            for i in range(len(pca.explained_variance_ratio_)):
                pc_name = f"PC{i+1}"
                results["Component Loadings"][pc_name] = {
                    ticker: round(float(loading), 4)
                    for ticker, loading in zip(returns.columns, loadings[i])
                }
                
                # Interpret each component
                results["Interpretation"][pc_name] = self._interpret_pc(
                    loadings[i], 
                    returns.columns,
                    pca.explained_variance_ratio_[i]
                )
            
            # Add summary statistics
            results["Summary"] = {
                "Total Components": len(pca.explained_variance_ratio_),
                "Tickers Analyzed": list(returns.columns),
                "Data Points": len(returns),
                "Total Variance Explained": round(
                    float(sum(pca.explained_variance_ratio_)), 4
                ),
                "Components for 90% Variance": self._components_for_variance_threshold(
                    pca.explained_variance_ratio_, 0.90
                ),
                "Components for 95% Variance": self._components_for_variance_threshold(
                    pca.explained_variance_ratio_, 0.95
                )
            }
            
            # Eigenvalues (variance explained by each component)
            results["Eigenvalues"] = {
                f"PC{i+1}": round(float(eigen), 4)
                for i, eigen in enumerate(pca.explained_variance_)
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in PCA analysis: {str(e)}")
            return {"error": str(e)}
    
    def _interpret_pc(
        self, 
        loadings: np.ndarray, 
        tickers: List[str],
        variance_explained: float
    ) -> str:
        """
        Interpret a principal component
        
        Args:
            loadings (np.ndarray): Component loadings
            tickers (list): List of ticker symbols
            variance_explained (float): Variance explained by this component
            
        Returns:
            str: Interpretation of the component
        """
        # Find dominant contributors
        abs_loadings = np.abs(loadings)
        sorted_indices = np.argsort(abs_loadings)[::-1]
        
        # Get top 3 contributors
        top_contributors = []
        for i in sorted_indices[:3]:
            ticker = tickers[i]
            loading = loadings[i]
            weight = abs_loadings[i]
            direction = "positive" if loading > 0 else "negative"
            top_contributors.append(f"{ticker} ({direction}, {weight:.3f})")
        
        variance_pct = variance_explained * 100
        
        interpretation = (
            f"Explains {variance_pct:.2f}% of variance. "
            f"Top contributors: {', '.join(top_contributors)}"
        )
        
        return interpretation
    
    def _components_for_variance_threshold(
        self, 
        explained_variance_ratio: np.ndarray,
        threshold: float
    ) -> int:
        """
        Calculate number of components needed to explain threshold variance
        
        Args:
            explained_variance_ratio (np.ndarray): Variance ratio for each component
            threshold (float): Variance threshold (e.g., 0.90 for 90%)
            
        Returns:
            int: Number of components needed
        """
        cumsum = np.cumsum(explained_variance_ratio)
        return int(np.argmax(cumsum >= threshold) + 1)
    
    def monte_carlo_var_es(
        self,
        tickers: List[str],
        portfolio_weights: Optional[Dict[str, float]] = None,
        days: int = 252,
        simulations: int = 10000,
        forecast_days: int = 252,
        confidence_level: float = 0.95,
        initial_investment: float = 100000
    ) -> Dict:
        """
        Monte Carlo simulation for Value at Risk (VaR) and Expected Shortfall (ES)
        
        Args:
            tickers (list): List of stock ticker symbols
            portfolio_weights (dict): Portfolio weights for each ticker (uses config or equal weights if None)
            days (int): Historical days for parameter estimation
            simulations (int): Number of Monte Carlo simulations
            forecast_days (int): Days to forecast
            confidence_level (float): Confidence level (e.g., 0.95 for 95%)
            initial_investment (float): Initial portfolio value
            
        Returns:
            dict: VaR and ES estimates with simulation details
        """
        try:
            self.logger.info(f"Running Monte Carlo simulation: {simulations} scenarios")
            
            # Get historical returns
            returns = self.get_historical_returns(tickers, days=days)
            
            if returns.empty:
                return {"error": "Could not fetch returns data"}
            
            # Clean data
            returns = returns.dropna(axis=1)
            tickers = list(returns.columns)
            
            if len(tickers) == 0:
                return {"error": "No valid tickers with data"}
            
            # Get portfolio weights from config if not provided
            if portfolio_weights is None:
                portfolio_weights = self._get_portfolio_weights(tickers)
            
            # Normalize weights to ensure they sum to 1.0
            total_weight = sum(portfolio_weights.values())
            if total_weight > 0:
                portfolio_weights = {
                    k: v/total_weight for k, v in portfolio_weights.items()
                }
            else:
                # Fall back to equal weights if all weights are zero
                portfolio_weights = {ticker: 1.0/len(tickers) for ticker in tickers}
            
            # Ensure all tickers have weights
            weights = np.array([portfolio_weights.get(ticker, 0) for ticker in tickers])
            
            # Calculate portfolio statistics
            mean_returns = returns.mean()
            cov_matrix = returns.cov()
            
            # Portfolio mean and std
            portfolio_mean = np.dot(weights, mean_returns)
            portfolio_std = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            
            # Run Monte Carlo simulations
            simulated_returns = np.random.normal(
                portfolio_mean,
                portfolio_std,
                (simulations, forecast_days)
            )
            
            # Calculate cumulative returns for each simulation
            cumulative_returns = np.cumprod(1 + simulated_returns, axis=1)
            
            # Final portfolio values
            final_values = initial_investment * cumulative_returns[:, -1]
            
            # Calculate returns (profit/loss)
            portfolio_returns = final_values - initial_investment
            portfolio_returns_pct = (final_values / initial_investment - 1) * 100
            
            # Sort returns for VaR and ES calculation
            sorted_returns = np.sort(portfolio_returns)
            sorted_returns_pct = np.sort(portfolio_returns_pct)
            
            # Calculate VaR (Value at Risk)
            var_index = int((1 - confidence_level) * simulations)
            var_value = -sorted_returns[var_index]  # Negative because it's a loss
            var_pct = -sorted_returns_pct[var_index]
            
            # Calculate ES (Expected Shortfall / Conditional VaR)
            # Average of all losses beyond VaR
            es_value = -np.mean(sorted_returns[:var_index])
            es_pct = -np.mean(sorted_returns_pct[:var_index])
            
            # Calculate percentiles
            percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
            percentile_values = {
                f"{p}th Percentile": {
                    "Value": round(float(np.percentile(final_values, p)), 2),
                    "Return": round(float(np.percentile(portfolio_returns_pct, p)), 2)
                }
                for p in percentiles
            }
            
            # Probability of loss
            prob_loss = np.sum(portfolio_returns < 0) / simulations * 100
            
            # Best and worst case scenarios
            best_case = float(np.max(final_values))
            worst_case = float(np.min(final_values))
            
            results = {
                "VaR": {
                    f"VaR at {confidence_level*100}% confidence": {
                        "Value": round(var_value, 2),
                        "Percentage": round(var_pct, 2),
                        "Interpretation": (
                            f"With {confidence_level*100}% confidence, the portfolio will not lose "
                            f"more than ${var_value:,.2f} ({var_pct:.2f}%) over {forecast_days} days"
                        )
                    }
                },
                "Expected Shortfall": {
                    f"ES at {confidence_level*100}% confidence": {
                        "Value": round(es_value, 2),
                        "Percentage": round(es_pct, 2),
                        "Interpretation": (
                            f"If losses exceed VaR threshold, expected loss is "
                            f"${es_value:,.2f} ({es_pct:.2f}%)"
                        )
                    }
                },
                "Simulation Parameters": {
                    "Simulations": simulations,
                    "Forecast Days": forecast_days,
                    "Initial Investment": initial_investment,
                    "Confidence Level": confidence_level,
                    "Historical Days": days
                },
                "Portfolio Statistics": {
                    "Daily Mean Return": round(float(portfolio_mean), 6),
                    "Daily Std Dev": round(float(portfolio_std), 6),
                    "Annualized Return": round(float(portfolio_mean * 252 * 100), 2),
                    "Annualized Volatility": round(float(portfolio_std * np.sqrt(252) * 100), 2)
                },
                "Scenario Analysis": {
                    "Expected Value": round(float(np.mean(final_values)), 2),
                    "Median Value": round(float(np.median(final_values)), 2),
                    "Best Case": round(best_case, 2),
                    "Worst Case": round(worst_case, 2),
                    "Probability of Loss": round(prob_loss, 2)
                },
                "Distribution Percentiles": percentile_values,
                "Portfolio Composition": {
                    ticker: round(weight * 100, 2) 
                    for ticker, weight in zip(tickers, weights)
                }
            }
            
            # Add stress test results if we have multiple assets
            if len(tickers) >= 2:
                try:
                    self.logger.info(f"=== STRESS TEST START === Running for {len(tickers)} tickers")
                    stress_results = self.stress_test_var(
                        tickers=tickers,
                        portfolio_weights=portfolio_weights,
                        days=days,
                        simulations=simulations,
                        forecast_days=1,  # Stress tests typically use 1-day horizon
                        confidence_level=confidence_level,
                        initial_investment=initial_investment
                    )
                    
                    if stress_results and 'error' not in stress_results:
                        results["Stress Test"] = stress_results
                        self.logger.info(f"=== STRESS TEST COMPLETE === Added to results with keys: {list(stress_results.keys())}")
                    else:
                        self.logger.warning(f"Stress test returned error: {stress_results.get('error', 'Unknown')}")
                except Exception as stress_error:
                    self.logger.warning(f"Stress test failed with exception: {str(stress_error)}")
            else:
                self.logger.info(f"Skipping stress test - only {len(tickers)} ticker(s), need 2+ for multi-asset stress test")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in Monte Carlo simulation: {str(e)}")
            return {"error": str(e)}
    
    def stress_test_var(
        self,
        tickers: List[str],
        portfolio_weights: Optional[Dict[str, float]] = None,
        days: int = 252,
        simulations: int = 10000,
        forecast_days: int = 1,
        confidence_level: float = 0.95,
        initial_investment: float = 100000,
        vol_stress_multiplier: float = 3.0,
        rho_stress: float = 0.95,
        use_fat_tails: bool = True,
        degrees_of_freedom: int = 3,
        liquidity_haircut: float = 0.02
    ) -> Dict:
        """
        Perform stress testing comparing normal market conditions to stressed conditions
        
        This method compares VaR under:
        - Base Case: Normal historical volatility and correlation
        - Stress Case: Elevated volatility and high correlation (crisis scenario)
        
        Enhanced Features:
        - Fat Tails: Uses Student-t distribution to capture extreme "Black Swan" events
        - Correlation Breakdown: Models the "crisis effect" where all correlations → 1
        - Liquidity Haircuts: Accounts for illiquidity costs during market stress
        
        Args:
            tickers (list): List of stock ticker symbols
            portfolio_weights (dict): Portfolio weights for each ticker
            days (int): Historical days for parameter estimation
            simulations (int): Number of Monte Carlo simulations
            forecast_days (int): Days to forecast (typically 1 for stress tests)
            confidence_level (float): Confidence level (e.g., 0.95 for 95%)
            initial_investment (float): Initial portfolio value
            vol_stress_multiplier (float): Multiplier for stressed volatility (default 3.0x)
            rho_stress (float): Correlation in stress scenario (default 0.95 - near total breakdown)
            use_fat_tails (bool): Use Student-t distribution for fat tails (default True)
            degrees_of_freedom (int): DoF for Student-t (lower = fatter tails, default 3), lower df captures more extreme events
            liquidity_haircut (float): Liquidity cost in stress (default 2%)
            
        Returns:
            dict: Stress test results with base and stressed VaR comparisons
        """
        try:
            self.logger.info(f"Running stress test VaR simulation: {simulations} scenarios")
            
            # Get historical returns
            returns = self.get_historical_returns(tickers, days=days)
            
            if returns.empty:
                return {"error": "Could not fetch returns data"}
            
            # Clean data
            returns = returns.dropna(axis=1)
            tickers = list(returns.columns)
            
            if len(tickers) == 0:
                return {"error": "No valid tickers with data"}
            
            # For single asset, default to simple Monte Carlo
            if len(tickers) == 1:
                self.logger.warning("Stress test requires multiple assets. Single asset provided.")
                # Still run a simplified stress test
                vol_base = returns.std().values[0]
                vol_stress = vol_base * vol_stress_multiplier
                mean_return = returns.mean().values[0]
                
                # Base case simulations
                base_returns = np.random.normal(mean_return, vol_base, simulations)
                base_final_values = initial_investment * (1 + base_returns)
                base_returns_dollars = base_final_values - initial_investment
                base_var_idx = int((1 - confidence_level) * simulations)
                base_var = -np.sort(base_returns_dollars)[base_var_idx]
                
                # Stress case simulations
                stress_returns = np.random.normal(mean_return, vol_stress, simulations)
                stress_final_values = initial_investment * (1 + stress_returns)
                stress_returns_dollars = stress_final_values - initial_investment
                stress_var_idx = int((1 - confidence_level) * simulations)
                stress_var = -np.sort(stress_returns_dollars)[stress_var_idx]
                
                return {
                    "Base Case": {
                        "VaR": round(float(base_var), 2),
                        "VaR %": round(float(base_var / initial_investment * 100), 2),
                        "Volatility": round(float(vol_base * 100), 2)
                    },
                    "Stress Case": {
                        "VaR": round(float(stress_var), 2),
                        "VaR %": round(float(stress_var / initial_investment * 100), 2),
                        "Volatility": round(float(vol_stress * 100), 2)
                    },
                    "Stress Impact": {
                        "VaR Increase": round(float(stress_var - base_var), 2),
                        "VaR Increase %": round(float((stress_var / base_var - 1) * 100), 2)
                    },
                    "Parameters": {
                        "Assets": len(tickers),
                        "Simulations": simulations,
                        "Forecast Days": forecast_days,
                        "Confidence Level": confidence_level,
                        "Volatility Multiplier": vol_stress_multiplier
                    },
                    "Note": "Single asset stress test: correlation effects not applicable"
                }
            
            # Get portfolio weights from config if not provided
            if portfolio_weights is None:
                portfolio_weights = self._get_portfolio_weights(tickers)
            
            # Normalize weights
            total_weight = sum(portfolio_weights.values())
            if total_weight > 0:
                portfolio_weights = {k: v/total_weight for k, v in portfolio_weights.items()}
            else:
                portfolio_weights = {ticker: 1.0/len(tickers) for ticker in tickers}
            
            weights = np.array([portfolio_weights.get(ticker, 0) for ticker in tickers])
            
            # Calculate base case parameters
            mean_returns = returns.mean().values
            vol_base = returns.std().values
            corr_base = returns.corr().values
            
            # Calculate average base correlation (excluding diagonal)
            n = len(tickers)
            if n > 1:
                rho_base = (corr_base.sum() - n) / (n * (n - 1))
            else:
                rho_base = 0
            
            # Construct base covariance matrix
            cov_base = np.zeros((len(tickers), len(tickers)))
            for i in range(len(tickers)):
                for j in range(len(tickers)):
                    if i == j:
                        cov_base[i, j] = vol_base[i] ** 2
                    else:
                        cov_base[i, j] = corr_base[i, j] * vol_base[i] * vol_base[j]
            
            # Construct stress covariance matrix
            vol_stress_vec = vol_base * vol_stress_multiplier
            cov_stress = np.zeros((len(tickers), len(tickers)))
            for i in range(len(tickers)):
                for j in range(len(tickers)):
                    if i == j:
                        cov_stress[i, j] = vol_stress_vec[i] ** 2
                    else:
                        cov_stress[i, j] = rho_stress * vol_stress_vec[i] * vol_stress_vec[j]
            
            # Ensure matrices are positive definite
            try:
                L_base = np.linalg.cholesky(cov_base)
            except np.linalg.LinAlgError:
                # Add small value to diagonal for numerical stability
                cov_base += np.eye(len(tickers)) * 1e-6
                L_base = np.linalg.cholesky(cov_base)
            
            try:
                L_stress = np.linalg.cholesky(cov_stress)
            except np.linalg.LinAlgError:
                cov_stress += np.eye(len(tickers)) * 1e-6
                L_stress = np.linalg.cholesky(cov_stress)
            
            # Generate standard normal random variables
            Z = np.random.normal(0, 1, size=(len(tickers), simulations))
            
            # Base case returns (Normal distribution)
            epsilon_base = L_base @ Z
            portfolio_returns_base = weights @ epsilon_base
            
            # Stress case returns with FAT TAILS (Student-t distribution)
            if use_fat_tails:
                # Generate Multivariate Student-t for "Black Swan" events
                # Math: Y = sqrt(df / W) * L * Z, where W ~ Chi-squared(df)
                W = np.random.chisquare(degrees_of_freedom, size=simulations)
                # Scale to create fat-tailed distribution
                fat_tail_scale = np.sqrt(degrees_of_freedom / W)
                epsilon_stress = L_stress @ Z * fat_tail_scale
                
                # Add asymmetric downside bias (negative returns are worse)
                # This captures the "leverage effect" in equity markets
                downside_mask = (epsilon_stress < 0)
                epsilon_stress[downside_mask] *= 1.2  # 20% worse on downside
            else:
                # Standard Normal stress (less realistic)
                epsilon_stress = L_stress @ Z
            
            portfolio_returns_stress = weights @ epsilon_stress
            
            # Apply LIQUIDITY HAIRCUT to stress returns
            # In a crisis, you can't exit at fair value - add transaction costs
            portfolio_returns_stress = portfolio_returns_stress - liquidity_haircut
            
            # Calculate final portfolio values
            base_final_values = initial_investment * (1 + portfolio_returns_base)
            stress_final_values = initial_investment * (1 + portfolio_returns_stress)
            
            # Calculate returns in dollars
            base_returns_dollars = base_final_values - initial_investment
            stress_returns_dollars = stress_final_values - initial_investment
            
            # Sort for VaR calculation
            sorted_base = np.sort(base_returns_dollars)
            sorted_stress = np.sort(stress_returns_dollars)
            
            # Calculate VaR at confidence level
            # Calculate 99th percentile VaR for extreme stress scenarios
            var_99_idx = int(0.01 * simulations)  # 99% confidence
            var_99_stress = -sorted_stress[var_99_idx]
            es_99_stress = -np.mean(sorted_stress[:var_99_idx])
            
            var_idx = int((1 - confidence_level) * simulations)
            var_base = -sorted_base[var_idx]
            var_stress = -sorted_stress[var_idx]
            
            # Calculate VaR as percentage
            var_base_pct = var_base / initial_investment * 100
            var_stress_pct = var_stress / initial_investment * 100
            
            # Calculate Expected Shortfall for both scenarios
            es_base = -np.mean(sorted_base[:var_idx])
            es_stress = -np.mean(sorted_stress[:var_idx])
            
            es_base_pct = es_base / initial_investment * 100
            es_stress_pct = es_stress / initial_investment * 100
            
            # Calculate probability of loss in each scenario
            prob_loss_base = np.sum(portfolio_returns_base < 0) / simulations * 100
            prob_loss_stress = np.sum(portfolio_returns_stress < 0) / simulations * 100
            
            results = {
                "Base Case": {
                    "VaR": round(float(var_base), 2),
                    "VaR %": round(float(var_base_pct), 2),
                    "Expected Shortfall": round(float(es_base), 2),
                    "ES %": round(float(es_base_pct), 2),
                    "Avg Volatility": round(float(np.mean(vol_base) * 100), 2),
                    "Avg Correlation": round(float(rho_base), 3),
                    "Probability of Loss": round(float(prob_loss_base), 2),
                    "Interpretation": (
                        f"Under normal conditions, with {confidence_level*100}% confidence, "
                        f"maximum loss is ${var_base:,.2f} ({var_base_pct:.2f}%)"
                    )
                },
                "Stress Case": {
                    "VaR": round(float(var_stress), 2),
                    "VaR %": round(float(var_stress_pct), 2),
                    "VaR 99%": round(float(var_99_stress), 2),
                    "VaR 99% %": round(float(var_99_stress / initial_investment * 100), 2),
                    "Expected Shortfall": round(float(es_stress), 2),
                    "ES %": round(float(es_stress_pct), 2),
                    "ES 99%": round(float(es_99_stress), 2),
                    "ES 99% %": round(float(es_99_stress / initial_investment * 100), 2),
                    "Avg Volatility": round(float(np.mean(vol_stress_vec) * 100), 2),
                    "Avg Correlation": round(float(rho_stress), 3),
                    "Probability of Loss": round(float(prob_loss_stress), 2),
                    "Distribution": "Student-t (Fat Tails)" if use_fat_tails else "Normal",
                    "Liquidity Haircut": f"{liquidity_haircut * 100}%",
                    "Interpretation": (
                        f"Under EXTREME crisis conditions (fat tails + volatility spike + correlation breakdown + liquidity crisis), "
                        f"with {confidence_level*100}% confidence, maximum loss is ${var_stress:,.2f} ({var_stress_pct:.2f}%)"
                    )
                },
                "Stress Impact": {
                    "VaR Increase": round(float(var_stress - var_base), 2),
                    "VaR Increase %": round(float((var_stress / var_base - 1) * 100), 2),
                    "VaR 99% Increase": round(float(var_99_stress - var_base), 2),
                    "ES Increase": round(float(es_stress - es_base), 2),
                    "ES Increase %": round(float((es_stress / es_base - 1) * 100), 2),
                    "Prob Loss Increase": round(float(prob_loss_stress - prob_loss_base), 2),
                    "Interpretation": (
                        f"LEPTOKURTIC STRESS: Crisis scenario increases VaR by ${var_stress - var_base:,.2f} "
                        f"({(var_stress / var_base - 1) * 100:.1f}% worse). "
                        f"Fat-tailed distribution captures extreme 'Black Swan' events. "
                        f"Extreme stress (99% VaR) shows ${var_99_stress:,.2f} loss - "
                        f"{((var_99_stress / var_base - 1) * 100):.1f}% worse than base case"
                    )
                },
                "Parameters": {
                    "Assets": len(tickers),
                    "Simulations": simulations,
                    "Forecast Days": forecast_days,
                    "Initial Investment": initial_investment,
                    "Confidence Level": confidence_level,
                    "Volatility Multiplier": vol_stress_multiplier,
                    "Stress Correlation": rho_stress,
                    "Historical Days": days,
                    "Fat Tails (Student-t)": "Yes" if use_fat_tails else "No",
                    "Degrees of Freedom": degrees_of_freedom if use_fat_tails else "N/A",
                    "Liquidity Haircut": f"{liquidity_haircut * 100}%",
                    "Downside Asymmetry": "20% amplification" if use_fat_tails else "None"
                },
                "Portfolio Composition": {
                    ticker: round(weight * 100, 2) 
                    for ticker, weight in zip(tickers, weights)
                }
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in stress test VaR: {str(e)}")
            return {"error": str(e)}
    
    def correlation_analysis(
        self,
        tickers: List[str],
        days: int = 252,
        method: str = 'pearson'
    ) -> Dict:
        """
        Perform correlation analysis on asset returns
        
        Args:
            tickers (list): List of stock ticker symbols
            days (int): Number of trading days
            method (str): Correlation method ('pearson', 'spearman', 'kendall')
            
        Returns:
            dict: Correlation matrix and analysis
        """
        try:
            self.logger.info(f"Performing correlation analysis for {len(tickers)} tickers")
            
            # Get returns data
            returns = self.get_historical_returns(tickers, days=days)
            
            self.logger.info(f"Returns shape after fetch: {returns.shape if not returns.empty else 'EMPTY'}")
            self.logger.info(f"Columns in returns: {list(returns.columns) if not returns.empty else 'NONE'}")
            
            if returns.empty:
                self.logger.warning("No returns data fetched - all tickers may have failed to download")
                return {"error": "Unable to fetch historical data for any tickers"}
            
            if len(returns.columns) < 2:
                self.logger.warning(f"Only {len(returns.columns)} ticker(s) with data, need at least 2")
                return {"error": "Need at least 2 assets for correlation analysis"}
            
            # Drop any columns with too many NaN values (keep columns with at least 50% valid data)
            threshold = len(returns) * 0.5
            returns = returns.dropna(axis=1, thresh=int(threshold))
            
            self.logger.info(f"After dropping NaN columns: {len(returns.columns)} tickers remaining")
            
            if len(returns.columns) < 2:
                self.logger.warning(f"After filtering NaN, only {len(returns.columns)} ticker(s) remain")
                return {"error": "Insufficient data for correlation analysis after filtering"}
            
            # Calculate correlation matrix
            corr_matrix = returns.corr(method=method)
            
            # Convert to dictionary format
            correlation_dict = {}
            for ticker1 in corr_matrix.columns:
                correlation_dict[ticker1] = {
                    ticker2: round(float(corr_matrix.loc[ticker1, ticker2]), 4)
                    for ticker2 in corr_matrix.columns
                }
            
            # Find highly correlated pairs (exclude diagonal)
            high_corr_pairs = []
            low_corr_pairs = []
            negative_corr_pairs = []
            
            for i, ticker1 in enumerate(corr_matrix.columns):
                for j, ticker2 in enumerate(corr_matrix.columns):
                    if i < j:  # Only upper triangle (avoid duplicates)
                        corr_val = corr_matrix.loc[ticker1, ticker2]
                        
                        if corr_val > 0.7:
                            high_corr_pairs.append({
                                "Pair": f"{ticker1}-{ticker2}",
                                "Correlation": round(float(corr_val), 4),
                                "Interpretation": "Strong positive correlation"
                            })
                        elif corr_val < -0.5:
                            negative_corr_pairs.append({
                                "Pair": f"{ticker1}-{ticker2}",
                                "Correlation": round(float(corr_val), 4),
                                "Interpretation": "Strong negative correlation"
                            })
                        elif abs(corr_val) < 0.3:
                            low_corr_pairs.append({
                                "Pair": f"{ticker1}-{ticker2}",
                                "Correlation": round(float(corr_val), 4),
                                "Interpretation": "Low correlation"
                            })
            
            # Calculate average correlation
            # Extract upper triangle (excluding diagonal)
            upper_triangle = corr_matrix.where(
                np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
            )
            avg_correlation = float(upper_triangle.stack().mean())
            
            # Diversification ratio
            # Lower correlation = better diversification
            diversification_score = 1 - abs(avg_correlation)
            
            results = {
                "Correlation Matrix": correlation_dict,
                "Summary Statistics": {
                    "Average Correlation": round(avg_correlation, 4),
                    "Diversification Score": round(diversification_score, 4),
                    "Number of Assets": len(returns.columns),
                    "Data Points": len(returns),
                    "Method": method.capitalize()
                },
                "Highly Correlated Pairs": high_corr_pairs[:10],  # Top 10
                "Negatively Correlated Pairs": negative_corr_pairs[:10],
                "Low Correlation Pairs": low_corr_pairs[:10],
                "Interpretation": self._interpret_correlation_matrix(
                    avg_correlation, 
                    len(high_corr_pairs),
                    len(negative_corr_pairs)
                )
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in correlation analysis: {str(e)}")
            return {"error": str(e)}
    
    def _interpret_correlation_matrix(
        self,
        avg_correlation: float,
        high_corr_count: int,
        negative_corr_count: int
    ) -> str:
        """
        Interpret correlation analysis results
        
        Args:
            avg_correlation (float): Average correlation
            high_corr_count (int): Number of highly correlated pairs
            negative_corr_count (int): Number of negatively correlated pairs
            
        Returns:
            str: Interpretation
        """
        if avg_correlation > 0.6:
            diversification = "Poor diversification - assets move together"
        elif avg_correlation > 0.4:
            diversification = "Moderate diversification"
        elif avg_correlation > 0.2:
            diversification = "Good diversification"
        else:
            diversification = "Excellent diversification - assets move independently"
        
        # Check if there are many highly correlated pairs (more than 30% threshold is concerning)
        if high_corr_count > 5:
            concern = "Many highly correlated pairs - consider portfolio rebalancing"
        else:
            concern = "Correlation levels are acceptable"
        
        if negative_corr_count > 0:
            hedge = f"Found {negative_corr_count} negative correlations - natural hedging opportunities"
        else:
            hedge = "No significant negative correlations found"
        
        return f"{diversification}. {concern}. {hedge}"
    
    def comprehensive_analysis(
        self,
        tickers: List[str],
        benchmark: str = '^GSPC',
        days: int = 252,
        simulations: int = 10000,
        portfolio_weights: Optional[Dict[str, float]] = None,
        initial_investment: float = 100000
    ) -> Dict:
        """
        Perform all four analyses in one comprehensive report
        
        Args:
            tickers (list): List of stock ticker symbols
            benchmark (str): Benchmark for regression
            days (int): Historical days for analysis
            simulations (int): Monte Carlo simulations
            portfolio_weights (dict): Portfolio weights
            initial_investment (float): Initial portfolio value
            
        Returns:
            dict: Comprehensive analysis results
        """
        self.logger.info("Starting comprehensive financial analysis")
        
        results = {
            "Analysis Metadata": {
                "Tickers": tickers,
                "Benchmark": benchmark,
                "Analysis Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Historical Period": f"{days} trading days",
                "Monte Carlo Simulations": simulations
            },
            "1. Linear Regression Analysis": self.linear_regression_analysis(
                tickers, benchmark, days
            ),
            "2. Correlation Analysis": self.correlation_analysis(
                tickers, days
            ),
            "3. PCA Analysis": self.pca_analysis(
                tickers, days
            ),
            "4. Monte Carlo VaR & ES": self.monte_carlo_var_es(
                tickers, portfolio_weights, days, simulations,
                initial_investment=initial_investment
            )
        }
        
        self.logger.info("Comprehensive analysis completed")
        return results
    
    def fundamental_analysis(
        self,
        stock_data: Dict,
        ticker: str
    ) -> Dict:
        """
        Provide succinct investment analysis based on fundamental metrics
        
        Args:
            stock_data (dict): Stock data containing valuation, profitability, earnings, 
                             financial metrics, and cashflow information
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Investment outlook and analysis summary
        """
        try:
            self.logger.info(f"Performing fundamental analysis for {ticker}")
            
            # Debug: Log available keys
            self.logger.info(f"Available data keys for {ticker}: {list(stock_data.keys())[:20]}")
            
            analysis = {
                "ticker": ticker,
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "valuation_score": 0,
                "profitability_score": 0,
                "financial_health_score": 0,
                "growth_score": 0,
                "overall_score": 0,
                "investment_outlook": "",
                "key_strengths": [],
                "key_concerns": [],
                "summary": ""
            }
            
            scores = []
            strengths = []
            concerns = []
            
            # Valuation Analysis
            valuation_score = self._analyze_valuation(stock_data, strengths, concerns)
            if valuation_score is not None:
                analysis["valuation_score"] = valuation_score
                scores.append(valuation_score)
            
            # Profitability Analysis
            profitability_score = self._analyze_profitability(stock_data, strengths, concerns)
            if profitability_score is not None:
                analysis["profitability_score"] = profitability_score
                scores.append(profitability_score)
            
            # Financial Health Analysis
            financial_score = self._analyze_financial_health(stock_data, strengths, concerns)
            if financial_score is not None:
                analysis["financial_health_score"] = financial_score
                scores.append(financial_score)
            
            # Growth Analysis
            growth_score = self._analyze_growth(stock_data, strengths, concerns)
            if growth_score is not None:
                analysis["growth_score"] = growth_score
                scores.append(growth_score)
            
            # Calculate overall score
            if scores:
                analysis["overall_score"] = round(sum(scores) / len(scores), 1)
            
            # Determine investment outlook
            overall = analysis["overall_score"]
            if overall >= 8.0:
                analysis["investment_outlook"] = "Strong Buy"
            elif overall >= 7.0:
                analysis["investment_outlook"] = "Buy"
            elif overall >= 6.0:
                analysis["investment_outlook"] = "Moderate Buy"
            elif overall >= 5.0:
                analysis["investment_outlook"] = "Hold"
            elif overall >= 4.0:
                analysis["investment_outlook"] = "Moderate Sell"
            else:
                analysis["investment_outlook"] = "Sell"
            
            # Assign strengths and concerns
            analysis["key_strengths"] = strengths[:5]  # Top 5 strengths
            analysis["key_concerns"] = concerns[:5]  # Top 5 concerns
            
            # Generate summary
            analysis["summary"] = self._generate_investment_summary(
                ticker, analysis["investment_outlook"], 
                analysis["overall_score"], strengths, concerns
            )
            
            self.logger.info(f"Fundamental analysis completed for {ticker}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in fundamental analysis: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_valuation(self, data: Dict, strengths: List[str], concerns: List[str]) -> Optional[float]:
        """Analyze valuation metrics (P/E, P/B, P/S, etc.)"""
        score = 5.0  # Neutral starting point
        metrics_found = 0
        
        try:
            # P/E Ratio
            pe = self._extract_metric(data, ['P/E Ratio', 'PE Ratio', 'Price to Earnings', 'P/E', 'PE', 'Trailing P/E', 'Forward P/E'])
            if pe:
                metrics_found += 1
                if pe < 15: # undervalued, a good buy
                    score += 1.5
                    strengths.append(f"Attractive P/E ratio of {pe:.2f} (below 15)")
                elif pe < 25: # generally fair value
                    score += 0.5
                elif 25 <= pe < 40: 
                    score += 0.1
                    concerns.append(f"Relatively High P/E ratio of {pe:.2f}")
                elif pe > 40: # overvalued
                    score -= 1.5
                    concerns.append(f"High P/E ratio of {pe:.2f} suggests overvaluation")
            
            # P/B Ratio
            pb = self._extract_metric(data, ['P/B Ratio', 'Price to Book', 'Price/Book'])
            if pb:
                metrics_found += 1
                if pb < 1.5: # fairly/under valued 
                    score += 1.0
                    strengths.append(f"Low P/B ratio of {pb:.2f} indicates value")
                elif 1.5 < pb < 4:
                    score += 0.25
                    concerns.append(f"Decent/Average P/B ratio of {pb:.2f}")
                elif pb > 5 : # overvalued
                    score -= 1.0
                    concerns.append(f"High P/B ratio of {pb:.2f}")
            
            # P/S Ratio
            ps = self._extract_metric(data, ['P/S Ratio', 'Price to Sales', 'Price/Sales', 'PS Ratio'])
            if ps:
                metrics_found += 1
                if ps < 2: # cheap
                    score += 1.0
                    strengths.append(f"Attractive P/S ratio of {ps:.2f} (below 2)")
                elif ps < 5: # reasonable
                    score += 0.3
                elif 5 < ps < 10: # slightly expensive
                    score += 0.05
                elif ps > 10: # too expensive
                    score -= 1.0
                    concerns.append(f"High P/S ratio of {ps:.2f} suggests overvaluation")
            
            # Dividend Yield
            div_yield = self._extract_metric(data, ['Dividend Yield', 'Yield'])
            if div_yield:
                metrics_found += 1
                if div_yield > 3:
                    score += 0.5
                    strengths.append(f"Attractive dividend yield of {div_yield:.2f}%")
            
            # PEG Ratio
            peg = self._extract_metric(data, ['PEG Ratio', 'PEG'])
            if peg:
                metrics_found += 1
                if peg < 1: # very undervalued, high growth potential
                    score += 1.0
                    strengths.append(f"PEG ratio of {peg:.2f} suggests undervaluation")
                elif 1 <= peg < 2:
                    score += 0.5
                    strengths.append(f"PEG ratio of {peg:.2f} suggests normal valuation")
                elif peg > 2:
                    score -= 0.5
            
            return max(0, min(10, score)) if metrics_found > 0 else None
            
        except Exception as e:
            self.logger.warning(f"Error analyzing valuation: {str(e)}")
            return None
    
    def _analyze_profitability(self, data: Dict, strengths: List[str], concerns: List[str]) -> Optional[float]:
        """Analyze profitability metrics (ROE, ROA, margins, etc.)"""
        score = 5.0
        metrics_found = 0
        
        try:
            # ROE
            roe = self._extract_metric(data, ['ROE', 'Return on Equity', 'Return On Equity', 'ROE %'])
            if roe:
                metrics_found += 1
                if roe > 20:
                    score += 2.0
                    strengths.append(f"Excellent ROE of {roe:.2f}% (above 20%)")
                elif roe > 15:
                    score += 1.0
                    strengths.append(f"Strong ROE of {roe:.2f}%")
                elif 5 <= roe <= 15:
                    score += 0.5
                    strengths.append(f"Decent ROE of {roe:.2f}%")
                elif roe < 5: # too low
                    score -= 1.5
                    concerns.append(f"Low ROE of {roe:.2f}%")
            
            # Profit Margin
            profit_margin = self._extract_metric(data, ['Profit Margin', 'Net Margin', 'Net Profit Margin', 'Profit Margin %', 'Net Margin %'])
            if profit_margin:
                metrics_found += 1
                if profit_margin > 20:
                    score += 1.5
                    strengths.append(f"High profit margin of {profit_margin:.2f}%")
                elif profit_margin > 10:
                    score += 0.5
                elif 0 < profit_margin < 10:
                    score += 0.1
                elif profit_margin < 0:
                    score -= 2.0
                    concerns.append("Company is unprofitable")
            
            # Operating Margin
            op_margin = self._extract_metric(data, ['Operating Margin', 'EBIT Margin'])
            if op_margin:
                metrics_found += 1
                if op_margin > 15:
                    score += 1.0
                elif op_margin < 0:
                    score -= 1.0
            
            # ROA
            roa = self._extract_metric(data, ['ROA', 'Return on Assets'])
            if roa:
                metrics_found += 1
                if roa > 10:
                    score += 1.0
                    strengths.append(f"Strong ROA of {roa:.2f}%")
                elif roa < 2:
                    score -= 0.5
            
            return max(0, min(10, score)) if metrics_found > 0 else None
            
        except Exception as e:
            self.logger.warning(f"Error analyzing profitability: {str(e)}")
            return None
    
    def _analyze_financial_health(self, data: Dict, strengths: List[str], concerns: List[str]) -> Optional[float]:
        """Analyze financial health metrics (debt, liquidity, etc.)"""
        score = 5.0
        metrics_found = 0
        
        try:
            # Debt to Equity
            de = self._extract_metric(data, ['Debt to Equity', 'D/E', 'Debt/Equity', 'Debt-to-Equity', 'Total Debt/Equity'])
            if de:
                metrics_found += 1
                if de < 0.5:
                    score += 1.5
                    strengths.append(f"Low debt with D/E ratio of {de:.2f}")
                elif de < 1.0:
                    score += 0.5
                elif de > 2.0:
                    score -= 1.5
                    concerns.append(f"High leverage with D/E ratio of {de:.2f}")
            
            # Current Ratio
            current_ratio = self._extract_metric(data, ['Current Ratio'])
            if current_ratio:
                metrics_found += 1
                if current_ratio > 2.0:
                    score += 1.0
                    strengths.append(f"Strong liquidity with current ratio of {current_ratio:.2f}")
                elif current_ratio < 1.0:
                    score -= 1.5
                    concerns.append(f"Liquidity concerns with current ratio of {current_ratio:.2f}")
            
            # Quick Ratio: measures a company's ability to meet short-term obligations with its most liquid assets
            quick_ratio = self._extract_metric(data, ['Quick Ratio'])
            if quick_ratio:
                metrics_found += 1
                if quick_ratio > 1.5: # has $1.5 liquid assets for every $1 liability
                    score += 1.0
                elif 0.5 > quick_ratio <= 1.5:
                    score += 0.5
                elif quick_ratio < 0.5:
                    score -= 1.0
            
            # Free Cash Flow
            fcf = self._extract_metric(data, ['Free Cash Flow', 'FCF'])
            if fcf:
                metrics_found += 1
                if fcf > 0:
                    score += 0.5
                    strengths.append("Positive free cash flow generation")
                else:
                    score -= 0.5
                    concerns.append("Negative free cash flow")
            
            # Operating Cash Flow
            ocf = self._extract_metric(data, ['Operating Cash Flow', 'OCF', 'Cash from Operations'])
            if ocf:
                metrics_found += 1
                if ocf > 0:
                    score += 0.5
                    strengths.append("Positive operating cash flow")
                else:
                    score -= 1.0
                    concerns.append("Negative operating cash flow")
            
            # EBITDA: profitability measure that looks at a company's earnings before interest, taxes, depreciation, and amortization
            ebitda = self._extract_metric(data, ['EBITDA', 'Ebitda'])
            if ebitda:
                metrics_found += 1
                if ebitda > 0:
                    score += 0.5
                else:
                    score -= 0.5
            
            return max(0, min(10, score)) if metrics_found > 0 else None
            
        except Exception as e:
            self.logger.warning(f"Error analyzing financial health: {str(e)}")
            return None
    
    def _analyze_growth(self, data: Dict, strengths: List[str], concerns: List[str]) -> Optional[float]:
        """Analyze growth metrics (revenue growth, earnings growth, etc.)"""
        score = 5.0
        metrics_found = 0
        
        try:
            # Revenue Growth
            rev_growth = self._extract_metric(data, ['Revenue Growth', 'Sales Growth'])
            if rev_growth:
                metrics_found += 1
                if rev_growth > 20:
                    score += 2.0
                    strengths.append(f"Exceptional revenue growth of {rev_growth:.2f}%")
                elif rev_growth > 10:
                    score += 1.0
                    strengths.append(f"Strong revenue growth of {rev_growth:.2f}%")
                elif rev_growth > 0:
                    score += 0.25
                    strengths.append(f"Positive revenue growth of {rev_growth:.2f}%")
                elif rev_growth < 0:
                    score -= 1.5
                    concerns.append(f"Declining revenue ({rev_growth:.2f}%)")
            
            # Earnings Growth
            earnings_growth = self._extract_metric(data, ['Earnings Growth', 'EPS Growth'])
            if earnings_growth:
                metrics_found += 1
                if earnings_growth > 15:
                    score += 1.5
                    strengths.append(f"Strong earnings growth of {earnings_growth:.2f}%")
                elif earnings_growth > 0:
                    score += 0.25
                    strengths.append(f"Positive earnings growth of {earnings_growth:.2f}%")
                elif earnings_growth < 0:
                    score -= 1.0
                    concerns.append(f"Declining earnings ({earnings_growth:.2f}%)")
            
            # Note: EPS absolute value removed as it's not meaningful across different stocks
            # (a $5 EPS might be high for one company but low for another)
            
            return max(0, min(10, score)) if metrics_found > 0 else None
            
        except Exception as e:
            self.logger.warning(f"Error analyzing growth: {str(e)}")
            return None
    
    def _extract_metric(self, data: Dict, possible_keys: List[str]) -> Optional[float]:
        """Extract a metric from data dict with multiple possible key names"""
        for key in possible_keys:
            # Check in main data (exact match)
            if key in data:
                value = data[key]
                if value is not None and value != 'N/A' and value != 'N/A%':
                    try:
                        return self._parse_numeric_value(value)
                    except (ValueError, TypeError):
                        continue
            
            # Check for partial match in main data
            for data_key in data.keys():
                if isinstance(data_key, str) and key.lower() in data_key.lower():
                    value = data[data_key]
                    if value is not None and value != 'N/A' and value != 'N/A%':
                        try:
                            return self._parse_numeric_value(value)
                        except (ValueError, TypeError):
                            continue
            
            # Check in nested dicts
            for section in ['valuation', 'profitability', 'financial_metrics', 
                          'earnings', 'cashflow', 'statistics', 'financials']:
                if section in data and isinstance(data[section], dict):
                    if key in data[section]:
                        value = data[section][key]
                        if value is not None and value != 'N/A' and value != 'N/A%':
                            try:
                                return self._parse_numeric_value(value)
                            except (ValueError, TypeError):
                                continue
        return None
    
    def _parse_numeric_value(self, value) -> float:
        """Parse numeric value handling suffixes like B, M, K properly"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Clean the string
            value = value.replace('%', '').replace(',', '').replace('$', '').strip()
            
            # Handle suffixes with proper multiplication
            multiplier = 1
            if value.endswith('B'):
                multiplier = 1_000_000_000
                value = value[:-1].strip()
            elif value.endswith('M'):
                multiplier = 1_000_000
                value = value[:-1].strip()
            elif value.endswith('K'):
                multiplier = 1_000
                value = value[:-1].strip()
            
            return float(value) * multiplier
        
        raise ValueError(f"Cannot parse value: {value}")
    
    def _generate_investment_summary(
        self, 
        ticker: str, 
        outlook: str, 
        score: float,
        strengths: List[str], 
        concerns: List[str]
    ) -> str:
        """Generate a concise investment summary"""
        
        # Build summary
        summary = f"{ticker} receives a {outlook} rating with an overall score of {score:.1f}/10. "
        
        if strengths:
            summary += f"Key strengths include: {', '.join(strengths[:3])}. "
        
        if concerns:
            summary += f"However, concerns include: {', '.join(concerns[:3])}. "
        
        # Add outlook context
        if score >= 7:
            summary += "The company demonstrates strong fundamentals and appears well-positioned for growth."
        elif score >= 5:
            summary += "The company shows mixed signals; further research is recommended before investing."
        else:
            summary += "The company faces significant challenges that warrant caution."
        
        return summary
