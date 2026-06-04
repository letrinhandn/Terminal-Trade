"""
Data Loader - Extensible data loading framework with smart caching
Supports Yahoo Finance with intelligent local database caching
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
import sys
from pathlib import Path
import warnings

import pandas as pd
import yfinance as yf
import requests

from config.settings import API_SETTINGS, is_api_configured
from data.cache_manager import get_cache_manager


warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', message='.*possibly delisted.*')
warnings.filterwarnings('ignore', message='.*Quote not found.*')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class DataLoader(ABC):
    """
    Abstract base class for data loaders.
    Extend this to add new data sources (CryptoQuant, FRED, Alpha Vantage, etc.)
    """
    
    def __init__(self, source_name: str):
        """
        Initialize data loader.
        
        Args:
            source_name: Name of the data source
        """
        self.source_name = source_name
    
    @abstractmethod

    def load(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Load data for a single symbol.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), None for latest
            
        Returns:
            DataFrame with OHLCV data
        """
        pass
    
    @abstractmethod

    def load_multiple(self, symbols: List[str], start_date: str, 
                     end_date: Optional[str] = None) -> dict:
        """
        Load data for multiple symbols.
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), None for latest
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate that DataFrame has required OHLCV columns.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        return all(col in df.columns for col in required_columns)
    
    def __str__(self) -> str:
        return f"{self.source_name} DataLoader"


class YahooFinanceLoader(DataLoader):
    """
    Yahoo Finance data loader with smart caching.
    Automatically caches data locally to avoid repeated downloads.
    """
    
    def __init__(self, use_cache: bool = True):
        super().__init__("Yahoo Finance")
        self.auto_adjust = True  # Adjust for splits and dividends
        self.use_cache = use_cache
        self.cache_manager = get_cache_manager() if use_cache else None
    
    def load(self, symbol: str, start_date: str, end_date: Optional[str] = None, 
             interval: str = '1d') -> pd.DataFrame:
        """
        Load data from Yahoo Finance with smart caching.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'BTC-USD', '^GSPC')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), None for latest
            interval: Data interval ('1d', '1h', '5m', etc.)
            
        Returns:
            DataFrame with OHLCV data
            
        Raises:
            ValueError: If data loading fails or data is invalid
        """
        # Try cache first
        if self.use_cache:
            cached_df = self.cache_manager.get_cached_data(
                symbol, start_date, end_date or datetime.now().strftime('%Y-%m-%d'), interval
            )
            if cached_df is not None and not cached_df.empty:
                return cached_df
        
        # Download from Yahoo Finance
        print(f"📥 Downloading {symbol} from Yahoo Finance...")
        try:
            df = yf.download(
                symbol, 
                start=start_date, 
                end=end_date, 
                interval=interval,
                auto_adjust=self.auto_adjust,
                progress=False  # Disable progress bar
            )
            
            if df.empty:
                raise ValueError(f"No data found for {symbol}")
            
            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if not self.validate_data(df):
                raise ValueError(f"Invalid data structure for {symbol}")
            
            # Cache the downloaded data
            if self.use_cache:
                self.cache_manager.save_to_cache(symbol, df, interval)
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error loading {symbol}: {str(e)}")
    
    def load_multiple(self, symbols: List[str], start_date: str, 
                     end_date: Optional[str] = None) -> dict:
        """
        Load data for multiple symbols from Yahoo Finance.
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), None for latest
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        data_dict = {}
        
        for symbol in symbols:
            try:
                df = self.load(symbol, start_date, end_date)
                data_dict[symbol] = df
                print(f"Loaded {symbol}: {len(df)} data points")
            except Exception as e:
                print(f"Failed to load {symbol}: {str(e)}")
                data_dict[symbol] = None
        
        return data_dict
    
    def get_info(self, symbol: str) -> dict:
        """
        Get additional information about a symbol.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Dictionary with symbol information
        """
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info
        except:
            return {}


class AlphaVantageLoader(DataLoader):
    """
    Alpha Vantage data loader implementation.
    Requires API key from https://www.alphavantage.co/support/#api-key
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("Alpha Vantage")
        self.api_key = api_key or API_SETTINGS['alpha_vantage'].get('api_key')
        self.base_url = "https://www.alphavantage.co/query"
        
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is required. Please set ALPHA_VANTAGE_API_KEY in .env file")
    
    def load(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Load data from Alpha Vantage.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), None for latest
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',
                'symbol': symbol,
                'outputsize': 'full',
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if 'Error Message' in data:
                raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
            
            if 'Time Series (Daily)' not in data:
                raise ValueError(f"No data found for {symbol}")
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Rename columns
            df.columns = ['Open', 'High', 'Low', 'Close', 'Adjusted Close', 'Volume', 'Dividend Amount', 'Split Coefficient']
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
            
            # Filter by date range
            df = df[start_date:end_date] if end_date else df[start_date:]
            
            if df.empty:
                raise ValueError(f"No data found for {symbol} in specified date range")
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error loading {symbol} from Alpha Vantage: {str(e)}")
    
    def load_multiple(self, symbols: List[str], start_date: str, 
                     end_date: Optional[str] = None) -> dict:
        """Load data for multiple symbols from Alpha Vantage."""
        data_dict = {}
        
        for symbol in symbols:
            try:
                df = self.load(symbol, start_date, end_date)
                data_dict[symbol] = df
                print(f"Loaded {symbol}: {len(df)} data points")
            except Exception as e:
                print(f"Failed to load {symbol}: {str(e)}")
                data_dict[symbol] = None
        
        return data_dict


class BinanceLoader(DataLoader):
    """
    Binance crypto data loader.
    Can work without API key for public market data, but with key for more features.
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        super().__init__("Binance")
        self.api_key = api_key or API_SETTINGS['binance'].get('api_key')
        self.api_secret = api_secret or API_SETTINGS['binance'].get('api_secret')
        self.base_url = "https://api.binance.com/api/v3"
    
    def load(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Load data from Binance.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT', 'ETHUSDT')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), None for latest
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Convert dates to timestamps
            start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
            end_ts = int(pd.Timestamp(end_date).timestamp() * 1000) if end_date else int(pd.Timestamp.now().timestamp() * 1000)
            
            # Binance API endpoint for klines (candlestick data)
            endpoint = f"{self.base_url}/klines"
            
            all_data = []
            current_ts = start_ts
            
            while current_ts < end_ts:
                params = {
                    'symbol': symbol.upper(),
                    'interval': '1d',
                    'startTime': current_ts,
                    'endTime': end_ts,
                    'limit': 1000
                }
                
                response = requests.get(endpoint, params=params)
                data = response.json()
                
                if isinstance(data, dict) and 'code' in data:
                    raise ValueError(f"Binance API error: {data.get('msg', 'Unknown error')}")
                
                if not data:
                    break
                
                all_data.extend(data)
                current_ts = data[-1][0] + 1
            
            if not all_data:
                raise ValueError(f"No data found for {symbol}")
            
            # Convert to DataFrame
            df = pd.DataFrame(all_data, columns=[
                'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error loading {symbol} from Binance: {str(e)}")
    
    def load_multiple(self, symbols: List[str], start_date: str, 
                     end_date: Optional[str] = None) -> dict:
        """Load data for multiple symbols from Binance."""
        data_dict = {}
        
        for symbol in symbols:
            try:
                df = self.load(symbol, start_date, end_date)
                data_dict[symbol] = df
                print(f"Loaded {symbol}: {len(df)} data points")
            except Exception as e:
                print(f"Failed to load {symbol}: {str(e)}")
                data_dict[symbol] = None
        
        return data_dict


class DeribitLoader(DataLoader):
    """
    Deribit Options Data Loader.
    
    Supports:
    - Options chain data (strikes, expiries, IV)
    - Historical options prices  
    - Greeks (delta, gamma, theta, vega)
    - Underlying price (BTC, ETH)
    
    Symbol format: 'BTC-OPTION' or 'ETH-OPTION'
    For specific contracts: 'BTC-25DEC24-50000-C' (underlying-expiry-strike-type)
    """
    
    BASE_URL = "https://www.deribit.com/api/v2/public"
    
    def __init__(self, **kwargs):
        super().__init__("Deribit")
        self.timeout = kwargs.get('timeout', 10)
    
    def load(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Load options data from Deribit.
        
        ⚠️ WARNING: Deribit public API only provides CURRENT options chain snapshot,
        NOT historical options prices. This data is NOT suitable for backtesting!
        
        For real options backtesting, you need:
        - Paid historical options data (CBOE, OptionMetrics, etc.)
        - Or backtest with underlying assets (BTC-USD, ETH-USD) using regular strategies
        
        This loader returns current options chain for educational/analysis purposes only.
        
        Args:
            symbol: 'BTC-OPTION' or 'ETH-OPTION' (date params ignored)
            start_date: IGNORED - not used for options snapshot
            end_date: IGNORED - not used for options snapshot
            
        Returns:
            DataFrame with CURRENT options chain snapshot
        """
        if symbol.upper() in ['BTC-OPTION', 'ETH-OPTION']:
            currency = 'BTC' if 'BTC' in symbol.upper() else 'ETH'
            print(f"\n⚠️  WARNING: Loading CURRENT options snapshot only (not historical)")
            print(f"   This is NOT suitable for backtesting - results will be misleading!")
            print(f"   Consider using: {currency}-USD for proper backtesting\n")
            return self._load_options_chain(currency)
        else:
            # Specific contract history - also limited
            print(f"\n⚠️  WARNING: Historical options data is very limited")
            return self._load_contract_history(symbol, start_date, end_date)
    
    def load_multiple(self, symbols: List[str], start_date: str, 
                     end_date: Optional[str] = None) -> pd.DataFrame:
        """Load multiple options contracts"""
        dfs = []
        for symbol in symbols:
            try:
                df = self.load(symbol, start_date, end_date)
                df['symbol'] = symbol
                dfs.append(df)
            except Exception as e:
                print(f"[WARNING] Failed to load {symbol}: {e}")
        
        if not dfs:
            return pd.DataFrame()
        
        return pd.concat(dfs, ignore_index=True)
    
    def _load_options_chain(self, currency: str) -> pd.DataFrame:
        """
        Load CURRENT options chain snapshot for BTC or ETH.
        
        ⚠️ IMPORTANT: This is a point-in-time snapshot, not historical time series!
        All options returned are from the same moment in time, making backtesting
        results meaningless.
        
        Returns DataFrame with columns:
        - strike, expiry, type, bid, ask, mark_price
        - iv, delta, gamma, theta, vega  
        - open_interest, volume
        - OHLCV columns (synthesized from mark_price for compatibility)
        """
        endpoint = f"{self.BASE_URL}/get_instruments"
        params = {
            'currency': currency,
            'kind': 'option',
            'expired': 'false'
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if 'result' not in data:
                print(f"[ERROR] Invalid response from Deribit API: {data}")
                raise ValueError("Invalid response from Deribit API")
            
            instruments = data['result']
            
            # Get current prices and Greeks for each instrument
            chain_data = []
            for instrument in instruments[:30]:
                instrument_name = instrument['instrument_name']
                ticker_data = self._get_ticker(instrument_name)
                
                if ticker_data:
                    greeks = ticker_data.get('greeks', {})
                    chain_data.append({
                        'instrument': instrument_name,
                        'strike': instrument.get('strike'),
                        'expiry': instrument.get('expiration_timestamp'),
                        'type': instrument.get('option_type'),
                        'bid': ticker_data.get('best_bid_price'),
                        'ask': ticker_data.get('best_ask_price'),
                        'mark_price': ticker_data.get('mark_price'),
                        'last_price': ticker_data.get('last_price'),
                        'iv': ticker_data.get('mark_iv'),
                        'delta': greeks.get('delta'),
                        'gamma': greeks.get('gamma'),
                        'theta': greeks.get('theta'),
                        'vega': greeks.get('vega'),
                        'open_interest': ticker_data.get('open_interest'),
                        'volume': ticker_data.get('stats', {}).get('volume')
                    })
            
            
            if not chain_data:
                print(f"[ERROR] No options data collected")
                return pd.DataFrame()
            
            df = pd.DataFrame(chain_data)
            
            # Ensure mark_price exists and has valid data
            if 'mark_price' not in df.columns:
                print(f"[ERROR] mark_price column not found")
                return pd.DataFrame()
            
            # For options, if mark_price is NaN, the option is likely not tradeable
            df = df[df['mark_price'].notna()].copy()
            
            if df.empty:
                print(f"[ERROR] No valid mark_price data available after filtering")
                return pd.DataFrame()
            
            # Map to standard OHLCV format for backtesting compatibility FIRST
            # This is critical - we must create these columns before setting index
            df['Open'] = df['mark_price']
            df['High'] = df['mark_price'] * 1.01
            df['Low'] = df['mark_price'] * 0.99
            df['Close'] = df['mark_price']
            df['Volume'] = df['volume'].fillna(0)
            
            # Convert expiry timestamp to datetime but DON'T set as index yet
            if 'expiry' in df.columns:
                df['expiry_datetime'] = pd.to_datetime(df['expiry'], unit='ms')
            
            # For backtesting, we need a proper time series index
            # Since all options at one point in time have same expiry,
            # we'll use a sequential integer index instead
            # The expiry_datetime column will still be available for reference
            df = df.reset_index(drop=True)
            
            # Final validation - ensure OHLCV columns exist
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"[ERROR] Missing required columns after mapping: {missing_cols}")
                return pd.DataFrame()
            
            print(f"✓ Loaded {len(df)} options (current snapshot)")
            print(f"⚠️  All {len(df)} rows are from the SAME TIME POINT - not a time series!")
            print(f"   Backtest results will NOT reflect real trading performance.\n")
            
            return df
            
        except Exception as e:
            print(f"[ERROR] Failed to load options chain: {e}")
            return pd.DataFrame()
    
    def _get_ticker(self, instrument_name: str) -> Optional[dict]:
        """Get current ticker data for an instrument"""
        endpoint = f"{self.BASE_URL}/ticker"
        params = {'instrument_name': instrument_name}
        
        try:
            response = requests.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get('result')
        except:
            return None
    
    def _load_contract_history(self, instrument_name: str, 
                               start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """Load historical data for a specific options contract"""
        # Convert dates to timestamps
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
        end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000) if end_date else int(datetime.now().timestamp() * 1000)
        
        endpoint = f"{self.BASE_URL}/get_tradingview_chart_data"
        params = {
            'instrument_name': instrument_name,
            'start_timestamp': start_ts,
            'end_timestamp': end_ts,
            'resolution': '60'  # 1 hour candles
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if 'result' not in data:
                raise ValueError("Invalid response from Deribit API")
            
            result = data['result']
            
            df = pd.DataFrame({
                'timestamp': result.get('ticks', []),
                'Open': result.get('open', []),
                'High': result.get('high', []),
                'Low': result.get('low', []),
                'Close': result.get('close', []),
                'Volume': result.get('volume', [])
            })
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"[ERROR] Failed to load contract history: {e}")
            return pd.DataFrame()
    
    def get_underlying_price(self, currency: str) -> Optional[float]:
        """Get current underlying price (BTC or ETH)"""
        endpoint = f"{self.BASE_URL}/get_index_price"
        params = {'index_name': f'{currency.lower()}_usd'}
        
        try:
            response = requests.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get('result', {}).get('index_price')
        except:
            return None


def get_data_loader(source: str = 'yahoo', **kwargs) -> DataLoader:
    """
    Factory function to get appropriate data loader.
    
    Args:
        source: Data source name ('yahoo', 'alpha_vantage', 'binance', etc.)
        **kwargs: Additional arguments for the loader
        
    Returns:
        Initialized DataLoader instance
        
    Raises:
        ValueError: If source is not supported or not configured
    """
    source = source.lower()
    
    if source == 'yahoo' or source == 'yahoo_finance':
        return YahooFinanceLoader()
    
    elif source == 'alpha_vantage' or source == 'alphavantage':
        if not is_api_configured('alpha_vantage'):
            raise ValueError(
                "Alpha Vantage is not configured. "
                "Please set ALPHA_VANTAGE_API_KEY in .env file"
            )
        return AlphaVantageLoader(**kwargs)
    
    elif source == 'binance':
        return BinanceLoader(**kwargs)
    
    elif source == 'deribit':
        return DeribitLoader(**kwargs)
    
    else:
        raise ValueError(
            f"Unsupported data source: {source}. "
            f"Available sources: yahoo, alpha_vantage, binance, deribit"
        )


# Convenience function with cache support
def load_data(symbol: str, start_date: str, end_date: Optional[str] = None,
              source: str = 'yahoo', interval: str = '1d', use_cache: bool = True) -> pd.DataFrame:
    """
    Convenience function to load data with smart caching.
    
    Args:
        symbol: Ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), None for latest
        source: Data source ('yahoo', 'alpha_vantage', 'binance')
        interval: Data interval ('1d', '1h', '5m', etc.)
        use_cache: Whether to use local cache (default: True)
        
    Returns:
        DataFrame with OHLCV data
        
    Example:
        >>> df = load_data('BTC-USD', '2023-01-01', '2024-01-01')
        >>> # First call downloads and caches
        >>> df = load_data('BTC-USD', '2023-01-01', '2024-01-01')
        >>> # Second call uses cache instantly!
    """
    if source == 'yahoo':
        loader = YahooFinanceLoader(use_cache=use_cache)
        return loader.load(symbol, start_date, end_date, interval)
    else:
        loader = get_data_loader(source)
        return loader.load(symbol, start_date, end_date)