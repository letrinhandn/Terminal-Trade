"""
Performance Metrics - Comprehensive trading performance analysis
Calculates key metrics: returns, Sharpe ratio, max drawdown, win rate, etc.
"""

import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    Calculate and analyze trading strategy performance metrics.
    
    Provides industry-standard metrics used by professional traders and funds:
    - Total return, CAGR
    - Sharpe ratio, Sortino ratio
    - Maximum drawdown, recovery time
    - Win rate, profit factor
    - Risk-adjusted metrics
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """Initialize with annualized risk-free rate."""
        self.risk_free_rate = risk_free_rate
    
    def calculate_all_metrics(self, backtest_results: dict,
                              equity_curve: List[float],
                              trading_days: int = 252) -> Dict:
        """Calculate all performance metrics from backtest results."""
        trades = backtest_results.get('trades', [])
        
        metrics = {
            # Basic metrics
            'total_return': backtest_results.get('total_return', 0.0),
            'num_trades': backtest_results.get('num_trades', 0),
            'win_rate': backtest_results.get('win_rate', 0.0),
            'max_drawdown': backtest_results.get('max_drawdown', 0.0),
            
            # Advanced metrics
            'sharpe_ratio': self.calculate_sharpe_ratio(equity_curve, trading_days),
            'sortino_ratio': self.calculate_sortino_ratio(equity_curve, trading_days),
            'calmar_ratio': self.calculate_calmar_ratio(
                backtest_results.get('total_return', 0.0),
                backtest_results.get('max_drawdown', 1.0)
            ),
            'profit_factor': self.calculate_profit_factor(
                backtest_results.get('avg_win', 0.0),
                backtest_results.get('avg_loss', 0.0),
                backtest_results.get('num_winning', 0),
                backtest_results.get('num_losing', 1)
            ),
            
            # Trade statistics
            'avg_win': backtest_results.get('avg_win', 0.0),
            'avg_loss': backtest_results.get('avg_loss', 0.0),
            'largest_win': self._get_largest_win(trades),
            'largest_loss': self._get_largest_loss(trades),
            'avg_holding_period': self._get_avg_holding_period(trades),
            
            # Risk metrics
            'volatility': self.calculate_volatility(equity_curve, trading_days),
            'downside_deviation': self.calculate_downside_deviation(equity_curve, trading_days),
        }
        
        return metrics
    
    def calculate_sharpe_ratio(self, equity_curve: List[float],
                               trading_days: int = 252) -> float:
        """Calculate Sharpe ratio (risk-adjusted return)."""
        if len(equity_curve) < 2:
            return 0.0
        
        returns = pd.Series(equity_curve).pct_change().dropna()
        
        if returns.std() == 0:
            return 0.0
        
        excess_returns = returns - (self.risk_free_rate / trading_days)
        sharpe = excess_returns.mean() / returns.std() * np.sqrt(trading_days)
        
        return float(sharpe)
    
    def calculate_sortino_ratio(self, equity_curve: List[float],
                                trading_days: int = 252) -> float:
        """Calculate Sortino ratio (focuses only on downside volatility)."""
        if len(equity_curve) < 2:
            return 0.0
        
        returns = pd.Series(equity_curve).pct_change().dropna()
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        excess_returns = returns.mean() - (self.risk_free_rate / trading_days)
        sortino = excess_returns / downside_returns.std() * np.sqrt(trading_days)
        
        return float(sortino)
    
    def calculate_calmar_ratio(self, total_return: float, max_drawdown: float) -> float:
        """Calculate Calmar ratio (return / max drawdown)."""
        if max_drawdown == 0:
            return 0.0
        
        return total_return / max_drawdown
    
    def calculate_profit_factor(self, avg_win: float, avg_loss: float,
                                num_wins: int, num_losses: int) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        gross_profit = avg_win * num_wins
        gross_loss = abs(avg_loss * num_losses)
        
        if gross_loss == 0:
            return 0.0
        
        return gross_profit / gross_loss
    
    def calculate_volatility(self, equity_curve: List[float],
                            trading_days: int = 252) -> float:
        """Calculate annualized volatility (%)."""
        if len(equity_curve) < 2:
            return 0.0
        
        returns = pd.Series(equity_curve).pct_change().dropna()
        volatility = returns.std() * np.sqrt(trading_days) * 100
        
        return float(volatility)
    
    def calculate_downside_deviation(self, equity_curve: List[float],
                                     trading_days: int = 252) -> float:
        """Calculate annualized downside deviation (only negative returns, %)."""
        if len(equity_curve) < 2:
            return 0.0
        
        returns = pd.Series(equity_curve).pct_change().dropna()
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            return 0.0
        
        downside_dev = downside_returns.std() * np.sqrt(trading_days) * 100
        
        return float(downside_dev)
    
    def _get_largest_win(self, trades: List) -> float:
        """Get largest winning trade percentage"""
        if not trades:
            return 0.0
        
        wins = [t.return_pct for t in trades if t.return_pct > 0]
        return max(wins) if wins else 0.0
    
    def _get_largest_loss(self, trades: List) -> float:
        """Get largest losing trade percentage"""
        if not trades:
            return 0.0
        
        losses = [t.return_pct for t in trades if t.return_pct < 0]
        return min(losses) if losses else 0.0
    
    def _get_avg_holding_period(self, trades: List) -> float:
        """Get average holding period in days"""
        if not trades:
            return 0.0
        
        return sum(t.holding_period for t in trades) / len(trades)
    
    def format_metrics(self, metrics: Dict) -> str:
        """Format metrics as a readable string."""
        lines = [
            "╔══════════════════════════════════════════════════════════╗",
            "║           PERFORMANCE METRICS SUMMARY                    ║",
            "╠══════════════════════════════════════════════════════════╣",
            "║  Returns & Risk                                          ║",
            f"║    Total Return:          {metrics['total_return']:>10.2f}%            ║",
            f"║    Sharpe Ratio:          {metrics['sharpe_ratio']:>10.2f}             ║",
            f"║    Sortino Ratio:         {metrics['sortino_ratio']:>10.2f}             ║",
            f"║    Max Drawdown:          {metrics['max_drawdown']:>10.2f}%            ║",
            f"║    Volatility:            {metrics['volatility']:>10.2f}%            ║",
            "║                                                          ║",
            "║  Trade Statistics                                        ║",
            f"║    Total Trades:          {metrics['num_trades']:>10}              ║",
            f"║    Win Rate:              {metrics['win_rate']:>10.2f}%            ║",
            f"║    Profit Factor:         {metrics['profit_factor']:>10.2f}             ║",
            f"║    Avg Win:               {metrics['avg_win']:>10.2f}%            ║",
            f"║    Avg Loss:              {metrics['avg_loss']:>10.2f}%            ║",
            f"║    Largest Win:           {metrics['largest_win']:>10.2f}%            ║",
            f"║    Largest Loss:          {metrics['largest_loss']:>10.2f}%            ║",
            f"║    Avg Hold Period:       {metrics['avg_holding_period']:>10.1f} days        ║",
            "╚══════════════════════════════════════════════════════════╝",
        ]
        
        return "\n".join(lines)