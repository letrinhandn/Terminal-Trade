"""
Backtesting Engine - Clean, modular backtesting system
Executes strategies and tracks trades with realistic assumptions
"""

from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
from datetime import datetime


@dataclass
class Trade:
    """Represents a single trade with entry and exit information"""
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    shares: float = 1.0
    
    @property
    def return_pct(self) -> float:
        """Return as percentage"""
        return ((self.exit_price - self.entry_price) / self.entry_price) * 100
    
    @property
    def profit_loss(self) -> float:
        """Absolute profit/loss"""
        return (self.exit_price - self.entry_price) * self.shares
    
    @property
    def holding_period(self) -> int:
        """Holding period in days"""
        return (self.exit_date - self.entry_date).days
    
    def __str__(self) -> str:
        return (f"Trade: {self.entry_date.date()} → {self.exit_date.date()} | "
                f"P&L: {self.return_pct:.2f}% | {self.holding_period} days")


class BacktestEngine:
    """
    Backtesting engine that executes strategies and tracks performance.
    
    Features:
    - Long-only or long-short strategies
    - Configurable initial capital and position sizing
    - Transaction costs simulation
    - Detailed trade tracking
    """
    
    def __init__(self, 
                 initial_capital: float = 10000.0,
                 commission: float = 0.0,
                 slippage: float = 0.0):
        """
        Initialize backtesting engine.
        
        Args:
            initial_capital: Starting capital
            commission: Commission per trade (percentage, e.g., 0.001 = 0.1%)
            slippage: Slippage per trade (percentage)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.reset()
    
    def reset(self):
        """Reset the backtest state"""
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.position = 0  # 0 = no position, 1 = long
        self.entry_price = 0.0
        self.entry_date = None
        self.current_capital = self.initial_capital
    
    def run(self, df: pd.DataFrame) -> dict:
        """
        Execute backtest on DataFrame with signals.
        
        Args:
            df: DataFrame with 'Signal' column (1=Buy, -1=Sell, 0=Hold)
            
        Returns:
            Dictionary with backtest results and statistics
        """
        self.reset()
        
        if 'Signal' not in df.columns:
            raise ValueError("DataFrame must have 'Signal' column")
        
        if 'Close' not in df.columns:
            available_cols = list(df.columns)
            raise ValueError(
                f"DataFrame must have 'Close' column. "
                f"Available columns: {available_cols}. "
                f"DataFrame shape: {df.shape}"
            )
        
        # Iterate through each bar
        for i in range(len(df)):
            row = df.iloc[i]
            
            # Extract scalar values properly
            signal = row['Signal']
            if hasattr(signal, 'item'):
                signal = signal.item()
            else:
                signal = int(signal)
                
            price = row['Close']
            if hasattr(price, 'item'):
                price = price.item()
            else:
                price = float(price)
                
            date = row.name if isinstance(row.name, datetime) else datetime.now()
            
            # Apply slippage only on actual trades
            if signal == 1:
                adjusted_price = price * (1 + self.slippage)
            elif signal == -1:
                adjusted_price = price * (1 - self.slippage)
            else:
                adjusted_price = price
            
            # Buy signal and no position
            if signal == 1 and self.position == 0:
                self.position = 1
                self.entry_price = adjusted_price
                self.entry_date = date
                # Apply commission
                self.current_capital *= (1 - self.commission)
            
            # Sell signal and have position
            elif signal == -1 and self.position == 1:
                self.position = 0
                exit_price = adjusted_price
                exit_date = date
                
                # Create trade record
                trade = Trade(
                    entry_date=self.entry_date,
                    exit_date=exit_date,
                    entry_price=self.entry_price,
                    exit_price=exit_price
                )
                self.trades.append(trade)
                
                # Update capital
                self.current_capital *= (1 + trade.return_pct / 100)
                self.current_capital *= (1 - self.commission)  # Exit commission
            
            # Track equity curve
            if self.position == 1:
                # Mark-to-market current position
                current_return = (price - self.entry_price) / self.entry_price
                equity = self.current_capital * (1 + current_return)
            else:
                equity = self.current_capital
            
            self.equity_curve.append(equity)
        
        # Close any open position at the end
        if self.position == 1:
            last_price = df['Close'].iloc[-1]
            last_date = df.index[-1] if isinstance(df.index[-1], datetime) else datetime.now()
            
            trade = Trade(
                entry_date=self.entry_date,
                exit_date=last_date,
                entry_price=self.entry_price,
                exit_price=last_price
            )
            self.trades.append(trade)
            self.current_capital *= (1 + trade.return_pct / 100)
        
        return self._generate_results()
    
    def _generate_results(self) -> dict:
        """Generate summary statistics from backtest"""
        total_return = ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
        
        winning_trades = [t for t in self.trades if t.return_pct > 0]
        losing_trades = [t for t in self.trades if t.return_pct <= 0]
        
        num_trades = len(self.trades)
        win_rate = (len(winning_trades) / num_trades * 100) if num_trades > 0 else 0
        
        avg_win = sum(t.return_pct for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.return_pct for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Calculate max drawdown from equity curve
        max_drawdown = self._calculate_max_drawdown()
        
        return {
            'total_return': total_return,
            'final_capital': self.current_capital,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'num_winning': len(winning_trades),
            'num_losing': len(losing_trades),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage"""
        if not self.equity_curve:
            return 0.0
        
        peak = self.equity_curve[0]
        max_dd = 0.0
        
        for value in self.equity_curve:
            if value > peak:
                peak = value
            dd = ((peak - value) / peak) * 100
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def get_trades(self) -> List[Trade]:
        """Get list of all trades"""
        return self.trades
    
    def get_equity_curve(self) -> List[float]:
        """Get equity curve"""
        return self.equity_curve