"""
Configuration settings for the Trading Research Terminal
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Data Settings
DEFAULT_DATA_SOURCE = "yahoo"
DATA_CACHE_ENABLED = os.getenv('DATA_CACHE_ENABLED', 'False').lower() == 'true'
DATA_CACHE_DIR = os.getenv('DATA_CACHE_DIR', 'cache/')

# Backtest Settings
DEFAULT_INITIAL_CAPITAL = 10000.0
DEFAULT_COMMISSION = 0.001  # 0.1% per trade
DEFAULT_SLIPPAGE = 0.0005   # 0.05% slippage

# Risk Settings
DEFAULT_RISK_FREE_RATE = 0.02  # 2% annual risk-free rate
TRADING_DAYS_PER_YEAR = 252    # For stocks
CRYPTO_DAYS_PER_YEAR = 365     # For crypto (24/7 trading)

# Strategy Settings
STRATEGY_DEFAULTS = {
    'MACD': {
        'fast_period': 12,
        'slow_period': 26,
        'signal_period': 9
    },
    'RSI': {
        'period': 14,
        'oversold': 30,
        'overbought': 70
    },
    'BollingerBands': {
        'period': 20,
        'std_dev': 2
    }
}

# Display Settings
DECIMAL_PLACES = 2
CURRENCY_SYMBOL = "$"
PERCENTAGE_DECIMALS = 2

# Date Settings
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_START_DATE = "2020-01-01"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "trading_terminal.log"

# Export Settings
EXPORT_DIR = "exports/"
EXPORT_FORMATS = ['csv', 'json', 'excel']

# API Settings - Loaded from environment variables
API_SETTINGS = {
    'yahoo_finance': {
        'enabled': os.getenv('YAHOO_FINANCE_ENABLED', 'true').lower() == 'true',
        'auto_adjust': True
    },
    'alpha_vantage': {
        'enabled': os.getenv('ALPHA_VANTAGE_ENABLED', 'false').lower() == 'true',
        'api_key': os.getenv('ALPHA_VANTAGE_API_KEY')
    },
    'cryptoquant': {
        'enabled': os.getenv('CRYPTOQUANT_ENABLED', 'false').lower() == 'true',
        'api_key': os.getenv('CRYPTOQUANT_API_KEY')
    },
    'fred': {
        'enabled': os.getenv('FRED_ENABLED', 'false').lower() == 'true',
        'api_key': os.getenv('FRED_API_KEY')
    },
    'binance': {
        'enabled': os.getenv('BINANCE_ENABLED', 'false').lower() == 'true',
        'api_key': os.getenv('BINANCE_API_KEY'),
        'api_secret': os.getenv('BINANCE_API_SECRET')
    },
    'coinbase': {
        'enabled': os.getenv('COINBASE_ENABLED', 'false').lower() == 'true',
        'api_key': os.getenv('COINBASE_API_KEY'),
        'api_secret': os.getenv('COINBASE_API_SECRET')
    },
    'polygon': {
        'enabled': os.getenv('POLYGON_ENABLED', 'false').lower() == 'true',
        'api_key': os.getenv('POLYGON_API_KEY')
    }
}

# Helper function to check if an API is configured
def is_api_configured(api_name: str) -> bool:
    """
    Check if an API is properly configured with credentials.
    
    Args:
        api_name: Name of the API (e.g., 'alpha_vantage', 'binance')
        
    Returns:
        True if API is enabled and has necessary credentials
    """
    if api_name not in API_SETTINGS:
        return False
    
    api_config = API_SETTINGS[api_name]
    
    if not api_config.get('enabled', False):
        return False
    
    # Yahoo Finance doesn't need API key
    if api_name == 'yahoo_finance':
        return True
    
    # Check for API key
    if 'api_key' in api_config and api_config['api_key']:
        # For APIs that need both key and secret
        if 'api_secret' in api_config:
            return bool(api_config['api_secret'])
        return True
    
    return False

# Get available data sources
def get_available_data_sources() -> list:
    """
    Get list of properly configured data sources.
    
    Returns:
        List of available data source names
    """
    return [name for name in API_SETTINGS.keys() if is_api_configured(name)]

# Performance Metrics to Display
METRICS_TO_DISPLAY = [
    'total_return',
    'sharpe_ratio',
    'sortino_ratio',
    'max_drawdown',
    'win_rate',
    'profit_factor',
    'num_trades',
    'volatility'
]

# Terminal UI Settings
TERMINAL_WIDTH = 70
USE_COLORS = True
SHOW_PROGRESS_BAR = False

# GUI Application Settings
APP_TITLE = "Terminal Trade"
APP_SUBTITLE = "Open Source Trading Platform"
DEFAULT_WIDTH = 1400
DEFAULT_HEIGHT = 900
THEME = "dark"