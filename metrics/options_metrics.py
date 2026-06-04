"""
Options Metrics - Greeks, Pricing, and Risk Analysis
Implements Black-Scholes model and options-specific metrics
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math


class OptionsMetrics:
    """
    Options analytics and Greeks calculations.
    
    Provides:
    - Black-Scholes pricing
    - Greeks (Delta, Gamma, Theta, Vega, Rho)
    - Implied Volatility
    - Risk metrics
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        """
        Initialize options metrics calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate (default 5%)
        """
        self.risk_free_rate = risk_free_rate
    
    def black_scholes_price(self, S: float, K: float, T: float, r: float, 
                           sigma: float, option_type: str = 'call') -> float:
        """
        Calculate option price using Black-Scholes model.
        
        Args:
            S: Current stock/underlying price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            sigma: Volatility (annualized)
            option_type: 'call' or 'put'
            
        Returns:
            Option price
        """
        if T <= 0:
            # At expiration
            if option_type == 'call':
                return max(0, S - K)
            else:
                return max(0, K - S)
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:  # put
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        
        return price
    
    def calculate_delta(self, S: float, K: float, T: float, r: float, 
                       sigma: float, option_type: str = 'call') -> float:
        """
        Calculate Delta (rate of change of option price w.r.t. underlying price).
        
        Delta ranges:
        - Call: 0 to 1
        - Put: -1 to 0
        
        Args:
            S, K, T, r, sigma: Black-Scholes parameters
            option_type: 'call' or 'put'
            
        Returns:
            Delta value
        """
        if T <= 0:
            if option_type == 'call':
                return 1.0 if S > K else 0.0
            else:
                return -1.0 if S < K else 0.0
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        
        if option_type == 'call':
            delta = norm.cdf(d1)
        else:  # put
            delta = norm.cdf(d1) - 1
        
        return delta
    
    def calculate_gamma(self, S: float, K: float, T: float, r: float, 
                       sigma: float) -> float:
        """
        Calculate Gamma (rate of change of delta w.r.t. underlying price).
        
        Gamma is same for calls and puts.
        Highest at-the-money, decreases away from strike.
        
        Args:
            S, K, T, r, sigma: Black-Scholes parameters
            
        Returns:
            Gamma value
        """
        if T <= 0:
            return 0.0
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
        return gamma
    
    def calculate_theta(self, S: float, K: float, T: float, r: float, 
                       sigma: float, option_type: str = 'call') -> float:
        """
        Calculate Theta (rate of change of option price w.r.t. time).
        
        Theta is usually negative (time decay).
        Reported as daily decay (divide by 365).
        
        Args:
            S, K, T, r, sigma: Black-Scholes parameters
            option_type: 'call' or 'put'
            
        Returns:
            Theta value (annual, divide by 365 for daily)
        """
        if T <= 0:
            return 0.0
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        
        if option_type == 'call':
            term2 = -r * K * np.exp(-r * T) * norm.cdf(d2)
            theta = term1 + term2
        else:  # put
            term2 = r * K * np.exp(-r * T) * norm.cdf(-d2)
            theta = term1 + term2
        
        return theta / 365  # Daily theta
    
    def calculate_vega(self, S: float, K: float, T: float, r: float, 
                      sigma: float) -> float:
        """
        Calculate Vega (rate of change of option price w.r.t. volatility).
        
        Vega is same for calls and puts.
        Measures sensitivity to IV changes.
        
        Args:
            S, K, T, r, sigma: Black-Scholes parameters
            
        Returns:
            Vega value (per 1% change in volatility)
        """
        if T <= 0:
            return 0.0
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        vega = S * norm.pdf(d1) * np.sqrt(T)
        
        return vega / 100  # Per 1% change in vol
    
    def calculate_rho(self, S: float, K: float, T: float, r: float, 
                     sigma: float, option_type: str = 'call') -> float:
        """
        Calculate Rho (rate of change of option price w.r.t. interest rate).
        
        Args:
            S, K, T, r, sigma: Black-Scholes parameters
            option_type: 'call' or 'put'
            
        Returns:
            Rho value (per 1% change in interest rate)
        """
        if T <= 0:
            return 0.0
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type == 'call':
            rho = K * T * np.exp(-r * T) * norm.cdf(d2)
        else:  # put
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)
        
        return rho / 100  # Per 1% change in rate
    
    def calculate_all_greeks(self, S: float, K: float, T: float, r: float, 
                            sigma: float, option_type: str = 'call') -> Dict[str, float]:
        """
        Calculate all Greeks at once.
        
        Returns:
            Dictionary with price and all Greeks
        """
        return {
            'price': self.black_scholes_price(S, K, T, r, sigma, option_type),
            'delta': self.calculate_delta(S, K, T, r, sigma, option_type),
            'gamma': self.calculate_gamma(S, K, T, r, sigma),
            'theta': self.calculate_theta(S, K, T, r, sigma, option_type),
            'vega': self.calculate_vega(S, K, T, r, sigma),
            'rho': self.calculate_rho(S, K, T, r, sigma, option_type)
        }
    
    def implied_volatility(self, market_price: float, S: float, K: float, 
                          T: float, r: float, option_type: str = 'call',
                          tol: float = 0.0001, max_iterations: int = 100) -> Optional[float]:
        """
        Calculate implied volatility using Newton-Raphson method.
        
        Args:
            market_price: Observed market price of option
            S, K, T, r: Black-Scholes parameters
            option_type: 'call' or 'put'
            tol: Convergence tolerance
            max_iterations: Maximum iterations
            
        Returns:
            Implied volatility (annualized) or None if not converged
        """
        if T <= 0:
            return None
        
        # Initial guess
        sigma = 0.5
        
        for i in range(max_iterations):
            price = self.black_scholes_price(S, K, T, r, sigma, option_type)
            vega = self.calculate_vega(S, K, T, r, sigma)
            
            diff = market_price - price
            
            if abs(diff) < tol:
                return sigma
            
            if vega == 0:
                return None
            
            # Newton-Raphson update
            sigma = sigma + diff / (vega * 100)  # vega is per 1%
            
            # Keep sigma in reasonable range
            sigma = max(0.01, min(sigma, 5.0))
        
        return None  # Did not converge
    
    def calculate_moneyness(self, S: float, K: float) -> Tuple[str, float]:
        """
        Calculate option moneyness.
        
        Args:
            S: Current underlying price
            K: Strike price
            
        Returns:
            (category, ratio) where category is 'ITM', 'ATM', or 'OTM'
            ratio is S/K
        """
        ratio = S / K
        
        if abs(ratio - 1.0) < 0.02:  # Within 2%
            category = 'ATM'
        elif ratio > 1.0:
            category = 'ITM'  # Call is ITM, Put is OTM
        else:
            category = 'OTM'  # Call is OTM, Put is ITM
        
        return category, ratio
    
    def calculate_portfolio_greeks(self, positions: List[Dict]) -> Dict[str, float]:
        """
        Calculate net Greeks for a portfolio of options.
        
        Args:
            positions: List of dicts with keys:
                - option_type: 'call' or 'put'
                - S, K, T, r, sigma: BS parameters
                - quantity: Number of contracts (positive for long, negative for short)
                - contract_size: Number of shares per contract (default 1)
            
        Returns:
            Dictionary with portfolio Greeks
        """
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        total_rho = 0
        total_value = 0
        
        for pos in positions:
            quantity = pos['quantity']
            contract_size = pos.get('contract_size', 1)
            
            greeks = self.calculate_all_greeks(
                pos['S'], pos['K'], pos['T'], pos['r'], 
                pos['sigma'], pos['option_type']
            )
            
            # Multiply by quantity and contract size
            multiplier = quantity * contract_size
            
            total_delta += greeks['delta'] * multiplier
            total_gamma += greeks['gamma'] * multiplier
            total_theta += greeks['theta'] * multiplier
            total_vega += greeks['vega'] * multiplier
            total_rho += greeks['rho'] * multiplier
            total_value += greeks['price'] * multiplier
        
        return {
            'portfolio_value': total_value,
            'delta': total_delta,
            'gamma': total_gamma,
            'theta': total_theta,
            'vega': total_vega,
            'rho': total_rho,
            'delta_dollars': total_delta * positions[0]['S'] if positions else 0
        }
    
    def calculate_profit_probability(self, S: float, K: float, T: float, 
                                    sigma: float, option_type: str = 'call') -> float:
        """
        Calculate probability of profit at expiration.
        
        Args:
            S: Current price
            K: Strike price (or breakeven price for strategies)
            T: Time to expiration
            sigma: Volatility
            option_type: 'call' or 'put'
            
        Returns:
            Probability (0 to 1)
        """
        if T <= 0:
            if option_type == 'call':
                return 1.0 if S > K else 0.0
            else:
                return 1.0 if S < K else 0.0
        
        # Use log-normal distribution
        d2 = (np.log(S / K) - 0.5 * sigma ** 2 * T) / (sigma * np.sqrt(T))
        
        if option_type == 'call':
            prob = norm.cdf(d2)
        else:
            prob = norm.cdf(-d2)
        
        return prob
    
    def years_to_expiry(self, expiry_date: str, 
                       current_date: Optional[str] = None) -> float:
        """
        Calculate time to expiry in years.
        
        Args:
            expiry_date: Expiration date (YYYY-MM-DD)
            current_date: Current date (YYYY-MM-DD), default today
            
        Returns:
            Time in years
        """
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        current = datetime.strptime(current_date, '%Y-%m-%d') if current_date else datetime.now()
        
        days = (expiry - current).days
        return max(0, days / 365.0)
    
    def format_greeks(self, greeks: Dict[str, float], 
                     include_price: bool = True) -> str:
        """
        Format Greeks for display.
        
        Args:
            greeks: Dictionary from calculate_all_greeks()
            include_price: Whether to include theoretical price
            
        Returns:
            Formatted string
        """
        lines = []
        
        if include_price and 'price' in greeks:
            lines.append(f"Price:  ${greeks['price']:.2f}")
            lines.append("-" * 30)
        
        if 'delta' in greeks:
            lines.append(f"Delta:  {greeks['delta']:>8.4f}")
        if 'gamma' in greeks:
            lines.append(f"Gamma:  {greeks['gamma']:>8.4f}")
        if 'theta' in greeks:
            lines.append(f"Theta:  {greeks['theta']:>8.4f} (daily)")
        if 'vega' in greeks:
            lines.append(f"Vega:   {greeks['vega']:>8.4f} (per 1%)")
        if 'rho' in greeks:
            lines.append(f"Rho:    {greeks['rho']:>8.4f} (per 1%)")
        
        return "\n".join(lines)


class OptionsPortfolioMetrics:
    """
    Portfolio-level options metrics and risk analysis.
    """
    
    def __init__(self):
        self.options_calc = OptionsMetrics()
    
    def calculate_var(self, positions: List[Dict], confidence: float = 0.95,
                     time_horizon: int = 1) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR) for options portfolio.
        
        Uses delta-normal method.
        
        Args:
            positions: List of option positions
            confidence: Confidence level (default 95%)
            time_horizon: Time horizon in days
            
        Returns:
            Dictionary with VaR metrics
        """
        # Get portfolio Greeks
        greeks = self.options_calc.calculate_portfolio_greeks(positions)
        
        # Estimate portfolio volatility using delta
        if not positions:
            return {'var': 0, 'cvar': 0}
        
        S = positions[0]['S']
        sigma = positions[0]['sigma']
        
        # Portfolio std dev = delta * S * sigma * sqrt(days)
        portfolio_std = abs(greeks['delta']) * S * sigma * np.sqrt(time_horizon / 365)
        
        # VaR at confidence level
        z_score = norm.ppf(confidence)
        var = z_score * portfolio_std
        
        # CVaR (Expected Shortfall)
        cvar = portfolio_std * norm.pdf(z_score) / (1 - confidence)
        
        return {
            'var': var,
            'cvar': cvar,
            'portfolio_delta': greeks['delta'],
            'portfolio_value': greeks['portfolio_value']
        }
    
    def calculate_beta_weighted_delta(self, positions: List[Dict], 
                                      portfolio_beta: float = 1.0) -> float:
        """
        Calculate beta-weighted delta for portfolio.
        
        Useful for hedging across different underlyings.
        
        Args:
            positions: List of option positions
            portfolio_beta: Beta of the portfolio relative to benchmark
            
        Returns:
            Beta-weighted delta
        """
        greeks = self.options_calc.calculate_portfolio_greeks(positions)
        return greeks['delta'] * portfolio_beta