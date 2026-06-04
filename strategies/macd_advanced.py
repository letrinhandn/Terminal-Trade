"""
Advanced MACD Strategy with RSI Filter and Volume Confirmation
More sophisticated version with additional filters to reduce false signals
"""

import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from core.strategy_base import BaseStrategy


class MACDAdvancedStrategy(BaseStrategy):
    """
    Advanced MACD Strategy with multiple confirmations.
    
    Features:
    - MACD crossover as primary signal
    - RSI filter to avoid overbought/oversold extremes
    - Volume confirmation for stronger signals
    - Trend filter using EMA200
    
    Parameters:
        fast_period: Fast EMA for MACD (default: 12)
        slow_period: Slow EMA for MACD (default: 26)
        signal_period: Signal line period (default: 9)
        rsi_period: RSI calculation period (default: 14)
        rsi_overbought: RSI overbought level (default: 70)
        rsi_oversold: RSI oversold level (default: 30)
        volume_ma_period: Volume moving average period (default: 20)
        trend_period: EMA for trend filter (default: 200)
        use_volume_filter: Enable volume confirmation (default: True)
        use_trend_filter: Enable trend filter (default: True)
    """
    
    def __init__(self, 
                 fast_period: int = 12,
                 slow_period: int = 26, 
                 signal_period: int = 9,
                 rsi_period: int = 14,
                 rsi_overbought: int = 70,
                 rsi_oversold: int = 30,
                 volume_ma_period: int = 20,
                 trend_period: int = 200,
                 use_volume_filter: bool = True,
                 use_trend_filter: bool = True):
        """Initialize Advanced MACD strategy"""
        params = {
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period,
            'rsi_period': rsi_period,
            'rsi_overbought': rsi_overbought,
            'rsi_oversold': rsi_oversold,
            'volume_ma_period': volume_ma_period,
            'trend_period': trend_period,
            'use_volume_filter': use_volume_filter,
            'use_trend_filter': use_trend_filter
        }
        super().__init__(name="MACD Advanced", params=params)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators.
        
        Returns DataFrame with:
        - MACD and Signal line
        - RSI
        - Volume MA
        - Trend EMA
        """
        df = df.copy()
        
        # MACD calculation
        fast = self.params['fast_period']
        slow = self.params['slow_period']
        signal = self.params['signal_period']
        
        df['EMA_Fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
        df['EMA_Slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = df['EMA_Fast'] - df['EMA_Slow']
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # RSI calculation
        rsi_period = self.params['rsi_period']
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Volume filter
        if self.params['use_volume_filter']:
            vol_period = self.params['volume_ma_period']
            df['Volume_MA'] = df['Volume'].rolling(window=vol_period).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        
        # Trend filter
        if self.params['use_trend_filter']:
            trend_period = self.params['trend_period']
            df['EMA_Trend'] = df['Close'].ewm(span=trend_period, adjust=False).mean()
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals with multiple confirmations.
        
        Buy Signal requires:
        1. MACD crosses above signal line
        2. RSI not overbought (< overbought level)
        3. Volume above average (if enabled)
        4. Price above trend EMA (if enabled)
        
        Sell Signal requires:
        1. MACD crosses below signal line
        2. RSI not oversold (> oversold level)
        3. Volume above average (if enabled)
        4. Price below trend EMA (if enabled)
        """
        df = df.copy()
        df['Signal'] = 0
        
        # Create shifted columns
        macd_prev = df['MACD'].shift(1)
        signal_prev = df['MACD_Signal'].shift(1)
        
        # MACD crossover conditions
        macd_cross_up = (df['MACD'] > df['MACD_Signal']) & (macd_prev <= signal_prev)
        macd_cross_down = (df['MACD'] < df['MACD_Signal']) & (macd_prev >= signal_prev)
        
        # RSI filters
        rsi_not_overbought = df['RSI'] < self.params['rsi_overbought']
        rsi_not_oversold = df['RSI'] > self.params['rsi_oversold']
        
        # Build buy condition
        buy_condition = macd_cross_up & rsi_not_overbought
        
        # Add volume filter if enabled
        if self.params['use_volume_filter']:
            volume_confirmation = df['Volume_Ratio'] > 1.0
            buy_condition = buy_condition & volume_confirmation
        
        # Add trend filter if enabled
        if self.params['use_trend_filter']:
            uptrend = df['Close'] > df['EMA_Trend']
            buy_condition = buy_condition & uptrend
        
        # Build sell condition
        sell_condition = macd_cross_down & rsi_not_oversold
        
        # Add volume filter if enabled
        if self.params['use_volume_filter']:
            volume_confirmation = df['Volume_Ratio'] > 1.0
            sell_condition = sell_condition & volume_confirmation
        
        # Add trend filter if enabled
        if self.params['use_trend_filter']:
            downtrend = df['Close'] < df['EMA_Trend']
            sell_condition = sell_condition & downtrend
        
        # Apply signals
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df
    
    def get_strategy_description(self) -> str:
        """Get detailed strategy description"""
        filters = []
        if self.params['use_volume_filter']:
            filters.append("Volume confirmation")
        if self.params['use_trend_filter']:
            filters.append(f"Trend filter (EMA{self.params['trend_period']})")
        
        filters_str = " + ".join(filters) if filters else "None"
        
        return (
            f"Advanced MACD Strategy\n"
            f"MACD: {self.params['fast_period']}/{self.params['slow_period']}/{self.params['signal_period']}\n"
            f"RSI Filter: {self.params['rsi_period']} period "
            f"({self.params['rsi_oversold']}-{self.params['rsi_overbought']})\n"
            f"Additional Filters: {filters_str}\n\n"
            f"Buy: MACD cross up + RSI < {self.params['rsi_overbought']} + filters\n"
            f"Sell: MACD cross down + RSI > {self.params['rsi_oversold']} + filters"
        )


# Preset configurations for different trading styles
class MACDConservative(MACDAdvancedStrategy):
    """Conservative version - fewer but higher quality signals"""
    def __init__(self):
        super().__init__(
            rsi_overbought=65,
            rsi_oversold=35,
            use_volume_filter=True,
            use_trend_filter=True
        )


class MACDAggressive(MACDAdvancedStrategy):
    """Aggressive version - more signals with relaxed filters"""
    def __init__(self):
        super().__init__(
            rsi_overbought=75,
            rsi_oversold=25,
            use_volume_filter=False,
            use_trend_filter=False
        )


class MACDScalping(MACDAdvancedStrategy):
    """Scalping version - faster MACD with volume confirmation"""
    def __init__(self):
        super().__init__(
            fast_period=8,
            slow_period=17,
            signal_period=6,
            rsi_period=7,
            use_volume_filter=True,
            use_trend_filter=False
        )