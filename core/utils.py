"""
Shared utility functions for the trading terminal.
"""

from typing import List, Dict
from datetime import datetime

import pandas as pd


def validate_date_format(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def parse_symbols(symbols_input: str) -> List[str]:
    """Parse a comma-separated symbols string, e.g. 'BTC-USD,ETH-USD,AAPL'."""
    return [s.strip().upper() for s in symbols_input.split(',') if s.strip()]


def format_percentage(value: float, decimals: int = 2) -> str:
    sign = '+' if value >= 0 else ''
    return f"{sign}{value:.{decimals}f}%"


def format_currency(value: float, currency: str = '$', decimals: int = 2) -> str:
    return f"{currency}{value:,.{decimals}f}"


def create_summary_table(results: List[Dict]) -> pd.DataFrame:
    return pd.DataFrame(results) if results else pd.DataFrame()


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divide, returning `default` when denominator is zero."""
    return numerator / denominator if denominator != 0 else default


def print_separator(char: str = '=', length: int = 70) -> None:
    print(char * length)


def print_header(text: str, char: str = '=') -> None:
    print_separator(char)
    print(f"  {text}")
    print_separator(char)
