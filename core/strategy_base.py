"""
Abstract base class for all trading strategies.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional

import pandas as pd


class Signal(Enum):
    BUY  =  1
    SELL = -1
    HOLD =  0


class BaseStrategy(ABC):
    """
    All strategies inherit from this class and must implement
    `calculate_indicators` and `generate_signals`.
    """

    def __init__(self, name: str, params: Optional[Dict] = None):
        self.name   = name
        self.params = params or {}
        self._data: Optional[pd.DataFrame] = None

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add indicator columns to df and return it."""
        pass

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add a 'Signal' column (1=Buy, -1=Sell, 0=Hold) and return df."""
        pass

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = self.calculate_indicators(df)
        df = self.generate_signals(df)
        self._data = df
        return df

    def get_data(self) -> Optional[pd.DataFrame]:
        return self._data

    def get_params(self) -> Dict:
        return self.params

    def set_params(self, params: Dict) -> None:
        self.params.update(params)

    def __str__(self) -> str:
        return f"{self.name} Strategy (params: {self.params})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
