"""
Application-wide configuration. All tunable values live here.
Runtime secrets are loaded from .env via python-dotenv.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# ── Data ──────────────────────────────────────────────────────────────────────

DEFAULT_DATA_SOURCE   = "yahoo"
DATA_CACHE_ENABLED    = os.getenv('DATA_CACHE_ENABLED', 'False').lower() == 'true'
DATA_CACHE_DIR        = os.getenv('DATA_CACHE_DIR', 'cache/')

# ── Backtest ──────────────────────────────────────────────────────────────────

DEFAULT_INITIAL_CAPITAL = 10_000.0
DEFAULT_COMMISSION      = 0.001   # 0.1% per trade
DEFAULT_SLIPPAGE        = 0.0005  # 0.05%
DEFAULT_RISK_FREE_RATE  = 0.02    # annualised, used in Sharpe/Sortino

TRADING_DAYS_PER_YEAR = 252
CRYPTO_DAYS_PER_YEAR  = 365

# ── Strategy defaults ─────────────────────────────────────────────────────────

STRATEGY_DEFAULTS = {
    'MACD': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
    'RSI':  {'period': 14, 'oversold': 30, 'overbought': 70},
    'BollingerBands': {'period': 20, 'std_dev': 2},
}

# ── Display ───────────────────────────────────────────────────────────────────

DECIMAL_PLACES       = 2
CURRENCY_SYMBOL      = "$"
PERCENTAGE_DECIMALS  = 2
DEFAULT_DATE_FORMAT  = "%Y-%m-%d"
DEFAULT_START_DATE   = "2020-01-01"

# ── Logging ───────────────────────────────────────────────────────────────────

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE  = os.getenv('LOG_FILE',  'trading_terminal.log')

# ── Export ────────────────────────────────────────────────────────────────────

EXPORT_DIR     = "exports/"
EXPORT_FORMATS = ['csv', 'json', 'excel']

# ── API credentials ───────────────────────────────────────────────────────────

API_SETTINGS = {
    'yahoo_finance': {
        'enabled': os.getenv('YAHOO_FINANCE_ENABLED', 'true').lower() == 'true',
        'auto_adjust': True,
    },
    'alpha_vantage': {
        'enabled': os.getenv('ALPHA_VANTAGE_ENABLED', 'false').lower() == 'true',
        'api_key': os.getenv('ALPHA_VANTAGE_API_KEY'),
    },
    'cryptoquant': {
        'enabled': os.getenv('CRYPTOQUANT_ENABLED', 'false').lower() == 'true',
        'api_key': os.getenv('CRYPTOQUANT_API_KEY'),
    },
    'fred': {
        'enabled': os.getenv('FRED_ENABLED', 'false').lower() == 'true',
        'api_key': os.getenv('FRED_API_KEY'),
    },
    'binance': {
        'enabled': os.getenv('BINANCE_ENABLED', 'false').lower() == 'true',
        'api_key':    os.getenv('BINANCE_API_KEY'),
        'api_secret': os.getenv('BINANCE_API_SECRET'),
    },
    'coinbase': {
        'enabled': os.getenv('COINBASE_ENABLED', 'false').lower() == 'true',
        'api_key':    os.getenv('COINBASE_API_KEY'),
        'api_secret': os.getenv('COINBASE_API_SECRET'),
    },
    'polygon': {
        'enabled': os.getenv('POLYGON_ENABLED', 'false').lower() == 'true',
        'api_key': os.getenv('POLYGON_API_KEY'),
    },
}

# ── UI ────────────────────────────────────────────────────────────────────────

APP_TITLE      = "Terminal Trade"
APP_SUBTITLE   = "Open Source Trading Platform"
DEFAULT_WIDTH  = 1400
DEFAULT_HEIGHT = 900
THEME          = "dark"
TERMINAL_WIDTH = 70

METRICS_TO_DISPLAY = [
    'total_return', 'sharpe_ratio', 'sortino_ratio', 'max_drawdown',
    'win_rate', 'profit_factor', 'num_trades', 'volatility',
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def is_api_configured(api_name: str) -> bool:
    """Return True if the named API is enabled and has the required credentials."""
    cfg = API_SETTINGS.get(api_name)
    if not cfg or not cfg.get('enabled', False):
        return False
    if api_name == 'yahoo_finance':
        return True
    if cfg.get('api_key'):
        return bool(cfg.get('api_secret', True))
    return False


def get_available_data_sources() -> list:
    return [name for name in API_SETTINGS if is_api_configured(name)]


def configure_logging() -> None:
    """Call once at application startup to set up root logger."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format='%(asctime)s  %(levelname)-8s  %(name)s  %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
        ],
    )
