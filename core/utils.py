"""
Utility functions for the Trading Research Terminal
"""

from typing import List, Dict
import pandas as pd
from datetime import datetime


def validate_date_format(date_str: str) -> bool:
    """
    Validate if date string is in YYYY-MM-DD format.
    
    Args:
        date_str: Date string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def parse_symbols(symbols_input: str) -> List[str]:
    """
    Parse comma-separated symbols string.
    
    Args:
        symbols_input: String like "BTC-USD,ETH-USD,AAPL"
        
    Returns:
        List of cleaned symbol strings
    """
    return [s.strip().upper() for s in symbols_input.split(",") if s.strip()]


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format a number as a percentage string.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        
    Returns:
        Formatted string like "+12.34%"
    """
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_currency(value: float, currency: str = "$", decimals: int = 2) -> str:
    """
    Format a number as currency.
    
    Args:
        value: Number to format
        currency: Currency symbol
        decimals: Number of decimal places
        
    Returns:
        Formatted string like "$1,234.56"
    """
    return f"{currency}{value:,.{decimals}f}"


def create_summary_table(results: List[Dict]) -> pd.DataFrame:
    """
    Create a formatted summary DataFrame from results.
    
    Args:
        results: List of dictionaries containing backtest results
        
    Returns:
        Formatted DataFrame
    """
    if not results:
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    return df


def print_separator(char: str = "=", length: int = 70):
    """Print a separator line."""
    print(char * length)


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    print_separator(char)
    print(f"  {text}")
    print_separator(char)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Value to return if denominator is zero
        
    Returns:
        Result of division or default value
    """
    return numerator / denominator if denominator != 0 else default