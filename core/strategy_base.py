"""
Base Strategy Class - Abstract interface for all trading strategies
All strategies must inherit from this class and implement the required methods.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional
import pandas as pd


class Signal(Enum):
    """Trading signals"""
    BUY = 1
    SELL = -1
    HOLD = 0


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    
    All custom strategies should inherit from this class and implement:
    - calculate_indicators(): Compute technical indicators
    - generate_signals(): Generate buy/sell signals based on indicators
    """
    
    def __init__(self, name: str, params: Optional[Dict] = None):
        """
        Initialize strategy.
        
        Args:
            name: Strategy name
            params: Dictionary of strategy parameters
        """
        self.name = name
        self.params = params or {}
        self._data = None
    
    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicator columns
        """
        pass
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on indicators.
        
        Args:
            df: DataFrame with indicators
            
        Returns:
            DataFrame with 'Signal' column (1=Buy, -1=Sell, 0=Hold)
        """
        pass
    
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Execute the complete strategy pipeline.
        
        Args:
            df: Raw OHLCV DataFrame
            
        Returns:
            DataFrame with indicators and signals
        """
        df = df.copy()
        df = self.calculate_indicators(df)
        df = self.generate_signals(df)
        self._data = df
        return df
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get the processed data with indicators and signals."""
        return self._data
    
    def get_params(self) -> Dict:
        """Get strategy parameters."""
        return self.params
    
    def set_params(self, params: Dict):
        """Update strategy parameters."""
        self.params.update(params)
    
    def __str__(self) -> str:
        return f"{self.name} Strategy (params: {self.params})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"