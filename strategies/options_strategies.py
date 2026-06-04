"""
Options Trading Strategies
Implementation of common options strategies with Greeks calculations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from core.strategy_base import BaseStrategy


class OptionsStrategy(BaseStrategy):
    """
    Base class for options strategies.
    
    Extends BaseStrategy with options-specific functionality:
    - Greeks calculations
    - Multi-leg position management
    - Profit/Loss at different prices
    - Expiration handling
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.legs = []  # List of option legs in the strategy
    
    def add_leg(self, option_type: str, strike: float, quantity: int, 
                premium: float, expiry: str):
        """
        Add an option leg to the strategy.
        
        Args:
            option_type: 'call' or 'put'
            strike: Strike price
            quantity: Number of contracts (positive for long, negative for short)
            premium: Option premium
            expiry: Expiration date
        """
        self.legs.append({
            'type': option_type,
            'strike': strike,
            'quantity': quantity,
            'premium': premium,
            'expiry': expiry
        })
    
    def calculate_payoff(self, underlying_price: float) -> float:
        """
        Calculate total payoff at a given underlying price.
        
        Args:
            underlying_price: Price of underlying asset
            
        Returns:
            Total payoff (positive = profit, negative = loss)
        """
        total_payoff = 0
        
        for leg in self.legs:
            option_type = leg['type']
            strike = leg['strike']
            quantity = leg['quantity']
            premium = leg['premium']
            
            # Calculate intrinsic value
            if option_type == 'call':
                intrinsic = max(0, underlying_price - strike)
            else:  # put
                intrinsic = max(0, strike - underlying_price)
            
            # Payoff = (intrinsic value - premium paid) * quantity * contract size (usually 1)
            leg_payoff = (intrinsic - premium) * quantity
            total_payoff += leg_payoff
        
        return total_payoff
    
    def get_payoff_range(self, min_price: float, max_price: float, 
                         num_points: int = 100) -> Tuple[List[float], List[float]]:
        """
        Calculate payoff across a range of underlying prices.
        
        Args:
            min_price: Minimum price to evaluate
            max_price: Maximum price to evaluate
            num_points: Number of evaluation points
            
        Returns:
            (prices, payoffs) tuple
        """
        prices = np.linspace(min_price, max_price, num_points)
        payoffs = [self.calculate_payoff(price) for price in prices]
        return prices.tolist(), payoffs
    
    def get_max_profit(self) -> float:
        """Calculate maximum possible profit"""
        # Override in specific strategies
        return float('inf')
    
    def get_max_loss(self) -> float:
        """Calculate maximum possible loss"""
        # Override in specific strategies
        return float('-inf')
    
    def get_breakeven_points(self) -> List[float]:
        """Calculate breakeven prices"""
        # Override in specific strategies
        return []


class CoveredCall(OptionsStrategy):
    """
    Covered Call Strategy
    
    Long underlying + Short call
    - Moderate bullish
    - Limited upside (capped at strike)
    - Full downside risk below purchase price
    """
    
    def __init__(self, underlying_price: float = 50000, call_strike: float = 55000, 
                 call_premium: float = 2000, **kwargs):
        super().__init__(name="Covered Call", **kwargs)
        self.underlying_price = underlying_price
        self.call_strike = call_strike
        self.call_premium = call_premium
        
        # Position: Long 100 shares + Short 1 call
        self.add_leg('call', call_strike, 'short', 1, call_premium)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Covered call doesn't need technical indicators"""
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals for covered call.
        
        Logic:
        1. Enter: When underlying is at entry price
        2. Exit: At expiration or if price moves significantly
        """
        df = df.copy()
        df['Signal'] = 0
        
        # Simplified: Enter position at start
        if len(df) > 0:
            df.loc[df.index[0], 'Signal'] = 1  # Enter covered call position
        
        return df
    
    def get_max_profit(self) -> float:
        """Max profit = Call premium + (Strike - Underlying price)"""
        return self.call_premium + max(0, self.call_strike - self.underlying_price)
    
    def get_max_loss(self) -> float:
        """Max loss = Underlying price - Call premium (if stock goes to 0)"""
        return -(self.underlying_price - self.call_premium)
    
    def get_breakeven_points(self) -> List[float]:
        """Breakeven = Underlying price - Call premium"""
        return [self.underlying_price - self.call_premium]


class ProtectivePut(OptionsStrategy):
    """
    Protective Put Strategy
    
    Long underlying + Long put
    - Insurance against downside
    - Unlimited upside
    - Limited downside (floor at strike)
    """
    
    def __init__(self, underlying_price: float = 50000, put_strike: float = 45000, 
                 put_premium: float = 1500, **kwargs):
        super().__init__(name="Protective Put", **kwargs)
        self.underlying_price = underlying_price
        self.put_strike = put_strike
        self.put_premium = put_premium
        
        # Position: Long 100 shares + Long 1 put
        self.add_leg('put', put_strike, 'long', 1, put_premium)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Protective put doesn't need technical indicators"""
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals for protective put"""
        df = df.copy()
        df['Signal'] = 0
        
        # Protective put is a hold strategy with insurance
        # Signals would be based on when to roll the put
        if len(df) > 0:
            df.loc[df.index[0], 'Signal'] = 1
        
        return df
    
    def get_max_profit(self) -> float:
        """Unlimited upside"""
        return float('inf')
    
    def get_max_loss(self) -> float:
        """Max loss = Underlying - Strike + Put premium"""
        return -(self.underlying_price - self.put_strike + self.put_premium)
    
    def get_breakeven_points(self) -> List[float]:
        """Breakeven = Underlying price + Put premium"""
        return [self.underlying_price + self.put_premium]


class IronCondor(OptionsStrategy):
    """
    Iron Condor Strategy
    
    Short put spread + Short call spread
    - Neutral strategy (profit from low volatility)
    - Profit if price stays within range
    - Limited profit and loss
    """
    
    def __init__(self, current_price: float = 50000, 
                 put_sell_strike: float = 47000, put_buy_strike: float = 45000,
                 call_sell_strike: float = 53000, call_buy_strike: float = 55000,
                 premiums: Dict[str, float] = None, **kwargs):
        """
        Args:
            current_price: Current underlying price
            put_sell_strike: Strike of short put (higher)
            put_buy_strike: Strike of long put (lower)
            call_sell_strike: Strike of short call (lower)
            call_buy_strike: Strike of long call (higher)
            premiums: Dict with keys 'put_sell', 'put_buy', 'call_sell', 'call_buy'
        """
        super().__init__(name="Iron Condor", **kwargs)
        self.current_price = current_price
        
        # Default premiums if not provided
        if premiums is None:
            premiums = {'put_sell': 1000, 'put_buy': 400, 'call_sell': 1000, 'call_buy': 400}
        
        # Short put spread
        self.add_leg('put', put_sell_strike, 'short', 1, premiums['put_sell'])
        self.add_leg('put', put_buy_strike, 'long', 1, premiums['put_buy'])
        
        # Short call spread
        self.add_leg('call', call_sell_strike, 'short', 1, premiums['call_sell'])
        self.add_leg('call', call_buy_strike, 'long', 1, premiums['call_buy'])
        
        # Calculate net credit
        self.net_credit = (premiums['put_sell'] - premiums['put_buy'] + 
                          premiums['call_sell'] - premiums['call_buy'])
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Iron condor doesn't need technical indicators"""
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals for iron condor"""
        df = df.copy()
        df['Signal'] = 0
        
        # Iron condor is typically held until expiration
        # Could add early exit logic based on profit targets
        if len(df) > 0:
            df.loc[df.index[0], 'Signal'] = 1
        
        return df
    
    def get_max_profit(self) -> float:
        """Max profit = Net credit received"""
        return self.net_credit
    
    def get_max_loss(self) -> float:
        """Max loss = Width of widest spread - Net credit"""
        # Calculate spread widths
        put_spread_width = self.legs[0]['strike'] - self.legs[1]['strike']
        call_spread_width = self.legs[3]['strike'] - self.legs[2]['strike']
        max_spread = max(put_spread_width, call_spread_width)
        return -(max_spread - self.net_credit)
    
    def get_breakeven_points(self) -> List[float]:
        """
        Two breakeven points for iron condor:
        - Lower: Short put strike - Net credit
        - Upper: Short call strike + Net credit
        """
        lower_breakeven = self.legs[0]['strike'] - self.net_credit
        upper_breakeven = self.legs[2]['strike'] + self.net_credit
        return [lower_breakeven, upper_breakeven]


class LongStraddle(OptionsStrategy):
    """
    Long Straddle Strategy
    
    Long call + Long put at same strike
    - Profit from large price moves in either direction
    - High volatility play
    - Loss if price stays near strike
    """
    
    def __init__(self, strike: float = 50000, call_premium: float = 2500, 
                 put_premium: float = 2500, **kwargs):
        super().__init__(name="Long Straddle", **kwargs)
        self.strike = strike
        
        # Position: Long call + Long put
        self.add_leg('call', strike, 'long', 1, call_premium)
        self.add_leg('put', strike, 'long', 1, put_premium)
        
        self.total_premium = call_premium + put_premium
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Long straddle doesn't need technical indicators"""
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals for long straddle"""
        df = df.copy()
        df['Signal'] = 0
        
        # Enter straddle before volatility events
        # Exit when profit target hit or at expiration
        if len(df) > 0:
            df.loc[df.index[0], 'Signal'] = 1
        
        return df
    
    def get_max_profit(self) -> float:
        """Unlimited in either direction"""
        return float('inf')
    
    def get_max_loss(self) -> float:
        """Max loss = Total premium paid"""
        return -self.total_premium
    
    def get_breakeven_points(self) -> List[float]:
        """Two breakeven points: Strike +/- Total premium"""
        return [
            self.strike - self.total_premium,
            self.strike + self.total_premium
        ]


class BullCallSpread(OptionsStrategy):
    """
    Bull Call Spread Strategy
    
    Long call (lower strike) + Short call (higher strike)
    - Bullish but capped upside
    - Lower cost than long call alone
    - Limited profit and loss
    """
    
    def __init__(self, buy_strike: float = 48000, sell_strike: float = 52000,
                 buy_premium: float = 3000, sell_premium: float = 1500, **kwargs):
        super().__init__(name="Bull Call Spread", **kwargs)
        self.buy_strike = buy_strike
        self.sell_strike = sell_strike
        
        # Position: Long call (lower) + Short call (higher)
        self.add_leg('call', buy_strike, 'long', 1, buy_premium)
        self.add_leg('call', sell_strike, 'short', 1, sell_premium)
        
        self.net_debit = buy_premium - sell_premium
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Bull call spread doesn't need technical indicators"""
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals for bull call spread"""
        df = df.copy()
        df['Signal'] = 0
        
        # Enter when bullish, exit at target or expiration
        if len(df) > 0:
            df.loc[df.index[0], 'Signal'] = 1
        
        return df
    
    def get_max_profit(self) -> float:
        """Max profit = (Sell strike - Buy strike) - Net debit"""
        return (self.sell_strike - self.buy_strike) - self.net_debit
    
    def get_max_loss(self) -> float:
        """Max loss = Net debit paid"""
        return -self.net_debit
    
    def get_breakeven_points(self) -> List[float]:
        """Breakeven = Buy strike + Net debit"""
        return [self.buy_strike + self.net_debit]


class BearPutSpread(OptionsStrategy):
    """
    Bear Put Spread (Bearish Debit Spread)
    
    Structure:
    - Buy higher strike put (more expensive)
    - Sell lower strike put (cheaper)
    
    Characteristics:
    - Bearish strategy with limited risk and limited profit
    - Net debit paid upfront
    - Max profit = Spread width - Net debit
    - Max loss = Net debit paid
    - Breakeven = Higher strike - Net debit
    
    Example:
        Current BTC: $50,000
        Buy $52,000 Put @ $3,000 premium
        Sell $48,000 Put @ $1,500 premium
        Net Debit: $1,500
        Max Profit: $4,000 - $1,500 = $2,500 (if BTC < $48,000)
        Max Loss: $1,500 (if BTC > $52,000)
    """
    
    def __init__(self, buy_strike: float = 52000, buy_premium: float = 3000,
                 sell_strike: float = 48000, sell_premium: float = 1500, **kwargs):
        super().__init__(name="Bear Put Spread", **kwargs)
        
        if buy_strike <= sell_strike:
            raise ValueError("Buy strike must be higher than sell strike for bear put spread")
        
        self.buy_strike = buy_strike
        self.sell_strike = sell_strike
        self.net_debit = buy_premium - sell_premium
        
        # Add legs
        self.add_leg('put', buy_strike, 'long', 1, buy_premium)
        self.add_leg('put', sell_strike, 'short', 1, sell_premium)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Bear put spread doesn't need technical indicators"""
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals based on bearish outlook.
        Enter when expecting downward move.
        """
        df = df.copy()
        df['Signal'] = 0
        
        # Simple bearish signal logic (can be enhanced)
        # For now, just placeholder - real logic would use technical indicators
        if len(df) > 0:
            df.loc[df.index[0], 'Signal'] = 1  # Enter position
        
        return df
    
    def get_max_profit(self) -> float:
        """Max profit = Spread width - Net debit"""
        spread_width = self.buy_strike - self.sell_strike
        return spread_width - self.net_debit
    
    def get_max_loss(self) -> float:
        """Max loss = Net debit paid"""
        return -self.net_debit
    
    def get_breakeven_points(self) -> List[float]:
        """Breakeven = Higher strike - Net debit"""
        return [self.buy_strike - self.net_debit]