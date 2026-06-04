"""
MACD (Moving Average Convergence Divergence) Strategy
Classic momentum strategy using MACD crossover signals
"""

import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.strategy_base import BaseStrategy


class MACDStrategy(BaseStrategy):
    """
    MACD Strategy Implementation.
    
    Generates buy signals when MACD crosses above signal line.
    Generates sell signals when MACD crosses below signal line.
    
    Parameters:
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line EMA period (default: 9)
    """
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """
        Initialize MACD strategy.
        
        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
        """
        params = {
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period
        }
        super().__init__(name="MACD", params=params)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MACD indicators.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with MACD indicators added
        """
        df = df.copy()
        
        # Get parameters
        fast = self.params['fast_period']
        slow = self.params['slow_period']
        signal = self.params['signal_period']
        
        # Calculate EMAs
        df['EMA_Fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
        df['EMA_Slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
        
        # Calculate MACD line
        df['MACD'] = df['EMA_Fast'] - df['EMA_Slow']
        
        # Calculate signal line
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        
        # Calculate histogram (MACD - Signal)
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on MACD crossover.
        
        Args:
            df: DataFrame with MACD indicators
            
        Returns:
            DataFrame with Signal column added (1=Buy, -1=Sell, 0=Hold)
        """
        df = df.copy()
        
        # Initialize signal column
        df['Signal'] = 0
        
        # Create shifted columns for comparison
        macd_prev = df['MACD'].shift(1)
        signal_prev = df['MACD_Signal'].shift(1)
        
        # Buy signal: MACD crosses above signal line
        buy_condition = (df['MACD'] > df['MACD_Signal']) & (macd_prev <= signal_prev)
        
        # Sell signal: MACD crosses below signal line
        sell_condition = (df['MACD'] < df['MACD_Signal']) & (macd_prev >= signal_prev)
        
        # Apply signals
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df
    
    def get_strategy_description(self) -> str:
        """Get a description of the strategy"""
        return (
            f"MACD Strategy\n"
            f"Parameters: Fast={self.params['fast_period']}, "
            f"Slow={self.params['slow_period']}, "
            f"Signal={self.params['signal_period']}\n"
            f"Buy when MACD crosses above signal line.\n"
            f"Sell when MACD crosses below signal line."
        )


# Example: Additional strategy template for future use
class RSIStrategy(BaseStrategy):
    """
    RSI (Relative Strength Index) Strategy - Template for future implementation.
    
    Buy when RSI crosses below oversold level (e.g., 30).
    Sell when RSI crosses above overbought level (e.g., 70).
    """
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        params = {
            'period': period,
            'oversold': oversold,
            'overbought': overbought
        }
        super().__init__(name="RSI", params=params)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI indicator - TO BE IMPLEMENTED"""
        df = df.copy()
        
        # Calculate price changes
        delta = df['Close'].diff()
        
        # Separate gains and losses
        gain = (delta.where(delta > 0, 0)).rolling(window=self.params['period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.params['period']).mean()
        
        # Calculate RS and RSI
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals based on RSI"""
        df = df.copy()
        df['Signal'] = 0
        
        # Create shifted column for comparison
        rsi_prev = df['RSI'].shift(1)
        
        # Buy when RSI crosses below oversold
        buy_condition = (df['RSI'] < self.params['oversold']) & (rsi_prev >= self.params['oversold'])
        
        # Sell when RSI crosses above overbought
        sell_condition = (df['RSI'] > self.params['overbought']) & (rsi_prev <= self.params['overbought'])
        
        # Apply signals
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df