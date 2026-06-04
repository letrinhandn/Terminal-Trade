"""
Trading strategy implementations
"""

from .macd_advanced import MACDAdvancedStrategy, MACDAggressive, MACDConservative
from .macd_strategy import MACDStrategy
from .options_strategies import (
    BearPutSpread,
    BullCallSpread,
    CoveredCall,
    IronCondor,
    LongStraddle,
    OptionsStrategy,
    ProtectivePut
)

__all__ = [
    'MACDStrategy',
    'MACDAdvancedStrategy',
    'MACDConservative',
    'MACDAggressive',
    'OptionsStrategy',
    'CoveredCall',
    'ProtectivePut',
    'IronCondor',
    'LongStraddle',
    'BullCallSpread',
    'BearPutSpread',
]