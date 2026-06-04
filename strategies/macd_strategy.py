"""
MACD and RSI strategy implementations.
"""

import pandas as pd

from core.strategy_base import BaseStrategy


class MACDStrategy(BaseStrategy):
    """
    MACD crossover strategy.
    Buy when MACD crosses above signal line; sell on the opposite crossover.
    Default periods: fast=12, slow=26, signal=9.
    """

    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__(
            name="MACD",
            params={
                'fast_period': fast_period,
                'slow_period': slow_period,
                'signal_period': signal_period,
            },
        )

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        fast   = self.params['fast_period']
        slow   = self.params['slow_period']
        signal = self.params['signal_period']

        df['EMA_Fast']       = df['Close'].ewm(span=fast,   adjust=False).mean()
        df['EMA_Slow']       = df['Close'].ewm(span=slow,   adjust=False).mean()
        df['MACD']           = df['EMA_Fast'] - df['EMA_Slow']
        df['MACD_Signal']    = df['MACD'].ewm(span=signal,  adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df        = df.copy()
        df['Signal'] = 0

        prev_macd   = df['MACD'].shift(1)
        prev_signal = df['MACD_Signal'].shift(1)

        df.loc[(df['MACD'] > df['MACD_Signal']) & (prev_macd <= prev_signal), 'Signal'] =  1
        df.loc[(df['MACD'] < df['MACD_Signal']) & (prev_macd >= prev_signal), 'Signal'] = -1
        return df

    def get_strategy_description(self) -> str:
        p = self.params
        return (
            f"MACD Strategy — "
            f"Fast={p['fast_period']}, Slow={p['slow_period']}, Signal={p['signal_period']}"
        )


class RSIStrategy(BaseStrategy):
    """
    RSI mean-reversion strategy.
    Buy when RSI crosses below oversold; sell when it crosses above overbought.
    Default: period=14, oversold=30, overbought=70.
    """

    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__(
            name="RSI",
            params={'period': period, 'oversold': oversold, 'overbought': overbought},
        )

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df    = df.copy()
        delta = df['Close'].diff()
        period = self.params['period']

        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs        = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['Signal'] = 0

        prev_rsi   = df['RSI'].shift(1)
        oversold   = self.params['oversold']
        overbought = self.params['overbought']

        df.loc[(df['RSI'] < oversold)   & (prev_rsi >= oversold),   'Signal'] =  1
        df.loc[(df['RSI'] > overbought) & (prev_rsi <= overbought), 'Signal'] = -1
        return df
