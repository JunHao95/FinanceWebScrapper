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
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in Monte Carlo simulation: {str(e)}")
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
