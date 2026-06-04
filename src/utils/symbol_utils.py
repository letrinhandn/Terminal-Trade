"""
Symbol formatting utilities
Convert user input to API-specific formats
"""


def format_symbol_for_yfinance(symbol: str) -> str:
    """Convert user symbol to yfinance format"""
    symbol = symbol.upper().strip()
    
    # Common crypto symbols - need -USD suffix for yfinance
    crypto_symbols = [
        'BTC', 'ETH', 'SOL', 'DOGE', 'AVAX', 'ADA', 'DOT', 'MATIC', 
        'LINK', 'UNI', 'XRP', 'LTC', 'BCH', 'ATOM', 'ALGO', 'XLM',
        'VET', 'ICP', 'FIL', 'SAND', 'MANA', 'AXS', 'SHIB', 'APE',
        'NEAR', 'FTM', 'AAVE', 'GRT', 'CRV', 'SNX', 'COMP', 'MKR',
        'SUSHI', 'YFI', '1INCH', 'ENJ', 'CHZ', 'BAT', 'ZRX', 'ANKR'
    ]
    
    # If already has -USD, return as-is
    if '-USD' in symbol:
        return symbol
    
    # If base symbol is crypto, add -USD
    if symbol in crypto_symbols:
        return f"{symbol}-USD"
    
    # Index symbols need ^ prefix
    indices_map = {
        'SPX': '^GSPC',      # S&P 500
        'DJI': '^DJI',       # Dow Jones
        'NASDAQ': '^IXIC',   # NASDAQ Composite
        'IXIC': '^IXIC',
        'RUT': '^RUT',       # Russell 2000
        'VIX': '^VIX',       # Volatility Index
        'NDX': '^NDX'        # NASDAQ 100
    }
    if symbol in indices_map:
        return indices_map[symbol]
    
    # Default: treat as stock ticker (no modification needed)
    return symbol


def format_symbol_for_finnhub(symbol: str) -> str:
    """Convert user symbol to Finnhub format (US stocks only)"""
    symbol = symbol.upper().strip()
    
    # Crypto symbols not supported by Finnhub (it's for stocks/forex)
    crypto_symbols = [
        'BTC', 'ETH', 'SOL', 'DOGE', 'AVAX', 'ADA', 'DOT', 'MATIC', 
        'LINK', 'UNI', 'XRP', 'LTC', 'BCH', 'ATOM', 'ALGO', 'XLM',
        'VET', 'ICP', 'FIL', 'SAND', 'MANA', 'AXS', 'SHIB', 'APE',
        'NEAR', 'FTM', 'AAVE', 'GRT', 'CRV', 'SNX', 'COMP', 'MKR',
        'SUSHI', 'YFI', '1INCH', 'ENJ', 'CHZ', 'BAT', 'ZRX', 'ANKR'
    ]
    
    # If crypto, return None (Finnhub doesn't support)
    if symbol in crypto_symbols or '-USD' in symbol:
        return None
    
    # Index symbols not supported
    if symbol in ['SPX', 'DJI', 'NASDAQ', 'IXIC', 'VIX', 'RUT', 'NDX'] or symbol.startswith('^'):
        return None
    
    # Return stock symbol as-is
    return symbol