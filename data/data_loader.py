"""
Data loading framework with smart caching.
Supports Yahoo Finance, Alpha Vantage, Binance, and Deribit.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
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

logger = logging.getLogger(__name__)


class DataLoader(ABC):
    """Abstract base class for all data loaders."""

    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def load(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """Load OHLCV data for a single symbol. start/end dates: YYYY-MM-DD."""
        pass

    def load_multiple(self, symbols: List[str], start_date: str,
                      end_date: Optional[str] = None) -> dict:
        """Load data for multiple symbols. Returns {symbol: DataFrame | None}."""
        data: dict = {}
        for symbol in symbols:
            try:
                data[symbol] = self.load(symbol, start_date, end_date)
                logger.info("Loaded %s: %d bars", symbol, len(data[symbol]))
            except ValueError as e:
                logger.warning("Failed to load %s: %s", symbol, e)
                data[symbol] = None
        return data

    def validate_data(self, df: pd.DataFrame) -> bool:
        required = {'Open', 'High', 'Low', 'Close', 'Volume'}
        return required.issubset(df.columns)

    def __str__(self) -> str:
        return f"{self.source_name} DataLoader"


class YahooFinanceLoader(DataLoader):
    """Yahoo Finance loader with local parquet caching."""

    def __init__(self, use_cache: bool = True):
        super().__init__("Yahoo Finance")
        self.auto_adjust = True
        self.use_cache = use_cache
        self.cache_manager = get_cache_manager() if use_cache else None

    def load(self, symbol: str, start_date: str, end_date: Optional[str] = None,
             interval: str = '1d') -> pd.DataFrame:
        if self.use_cache:
            cached = self.cache_manager.get_cached_data(
                symbol, start_date,
                end_date or datetime.now().strftime('%Y-%m-%d'),
                interval
            )
            if cached is not None and not cached.empty:
                return cached

        logger.info("Downloading %s from Yahoo Finance", symbol)
        try:
            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=self.auto_adjust,
                progress=False,
            )
        except Exception as e:
            raise ValueError(f"Download failed for {symbol}: {e}") from e

        if df.empty:
            raise ValueError(f"No data returned for {symbol}")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if not self.validate_data(df):
            raise ValueError(f"Unexpected data structure for {symbol}: {list(df.columns)}")

        if self.use_cache:
            self.cache_manager.save_to_cache(symbol, df, interval)

        return df

    def get_info(self, symbol: str) -> dict:
        try:
            return yf.Ticker(symbol).info
        except Exception as e:
            logger.debug("Could not fetch info for %s: %s", symbol, e)
            return {}


class AlphaVantageLoader(DataLoader):
    """
    Alpha Vantage loader.
    Requires ALPHA_VANTAGE_API_KEY in .env.
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__("Alpha Vantage")
        self.api_key = api_key or API_SETTINGS['alpha_vantage'].get('api_key')
        self.base_url = "https://www.alphavantage.co/query"
        if not self.api_key:
            raise ValueError(
                "Alpha Vantage API key required. Set ALPHA_VANTAGE_API_KEY in .env"
            )

    def load(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        try:
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',
                'symbol': symbol,
                'outputsize': 'full',
                'apikey': self.api_key,
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise ValueError(f"Request failed for {symbol}: {e}") from e

        if 'Error Message' in data:
            raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
        if 'Time Series (Daily)' not in data:
            raise ValueError(f"No data found for {symbol}")

        df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        df.columns = [
            'Open', 'High', 'Low', 'Close',
            'Adjusted Close', 'Volume', 'Dividend Amount', 'Split Coefficient'
        ]
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        df = df[start_date:end_date] if end_date else df[start_date:]

        if df.empty:
            raise ValueError(f"No data for {symbol} in range {start_date} to {end_date}")

        return df


class BinanceLoader(DataLoader):
    """
    Binance loader. Works without API key for public market data.
    Symbol format: 'BTCUSDT', 'ETHUSDT'.
    """

    BASE_URL = "https://api.binance.com/api/v3"

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        super().__init__("Binance")
        self.api_key = api_key or API_SETTINGS['binance'].get('api_key')
        self.api_secret = api_secret or API_SETTINGS['binance'].get('api_secret')

    def load(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
        end_ts = int(
            pd.Timestamp(end_date).timestamp() * 1000
            if end_date
            else pd.Timestamp.now().timestamp() * 1000
        )

        all_data: list = []
        current_ts = start_ts

        try:
            while current_ts < end_ts:
                params = {
                    'symbol': symbol.upper(),
                    'interval': '1d',
                    'startTime': current_ts,
                    'endTime': end_ts,
                    'limit': 1000,
                }
                response = requests.get(
                    f"{self.BASE_URL}/klines", params=params, timeout=10
                )
                response.raise_for_status()
                data = response.json()

                if isinstance(data, dict) and 'code' in data:
                    raise ValueError(f"Binance API error: {data.get('msg', 'unknown')}")
                if not data:
                    break

                all_data.extend(data)
                current_ts = data[-1][0] + 1
        except requests.RequestException as e:
            raise ValueError(f"Request failed for {symbol}: {e}") from e

        if not all_data:
            raise ValueError(f"No data found for {symbol}")

        df = pd.DataFrame(all_data, columns=[
            'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
            'close_time', 'quote_volume', 'trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore',
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        return df


class DeribitLoader(DataLoader):
    """
    Deribit options data loader.

    WARNING: The public Deribit API provides only a current-snapshot of the
    options chain, not a historical time series. Data returned by this loader
    is not suitable for backtesting. Use BTC-USD / ETH-USD with standard
    strategies for backtesting purposes.

    Symbol format:
        'BTC-OPTION' or 'ETH-OPTION'  - full chain snapshot
        'BTC-25DEC24-50000-C'          - specific contract
    """

    BASE_URL = "https://www.deribit.com/api/v2/public"

    def __init__(self, **kwargs):
        super().__init__("Deribit")
        self.timeout = kwargs.get('timeout', 10)

    def load(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        if symbol.upper() in ('BTC-OPTION', 'ETH-OPTION'):
            currency = 'BTC' if 'BTC' in symbol.upper() else 'ETH'
            return self._load_options_chain(currency)
        return self._load_contract_history(symbol, start_date, end_date)

    def load_multiple(self, symbols: List[str], start_date: str,
                      end_date: Optional[str] = None) -> pd.DataFrame:
        """Returns concatenated DataFrame (not dict) with a 'symbol' column."""
        frames = []
        for symbol in symbols:
            try:
                df = self.load(symbol, start_date, end_date)
                df['symbol'] = symbol
                frames.append(df)
            except ValueError as e:
                logger.warning("Failed to load %s: %s", symbol, e)
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def _load_options_chain(self, currency: str) -> pd.DataFrame:
        """
        Returns a point-in-time snapshot of the active options chain.
        All rows share the same timestamp; this is NOT a time series.
        """
        params = {'currency': currency, 'kind': 'option', 'expired': 'false'}
        try:
            response = requests.get(
                f"{self.BASE_URL}/get_instruments", params=params, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise ValueError(f"Deribit request failed: {e}") from e

        if 'result' not in data:
            raise ValueError(f"Unexpected Deribit response: {data}")

        chain_data = []
        for instrument in data['result'][:30]:
            name = instrument['instrument_name']
            ticker = self._get_ticker(name)
            if not ticker:
                continue
            greeks = ticker.get('greeks', {})
            chain_data.append({
                'instrument': name,
                'strike': instrument.get('strike'),
                'expiry': instrument.get('expiration_timestamp'),
                'type': instrument.get('option_type'),
                'bid': ticker.get('best_bid_price'),
                'ask': ticker.get('best_ask_price'),
                'mark_price': ticker.get('mark_price'),
                'last_price': ticker.get('last_price'),
                'iv': ticker.get('mark_iv'),
                'delta': greeks.get('delta'),
                'gamma': greeks.get('gamma'),
                'theta': greeks.get('theta'),
                'vega': greeks.get('vega'),
                'open_interest': ticker.get('open_interest'),
                'volume': ticker.get('stats', {}).get('volume'),
            })

        if not chain_data:
            return pd.DataFrame()

        df = pd.DataFrame(chain_data)
        df = df[df['mark_price'].notna()].copy()

        if df.empty:
            return pd.DataFrame()

        df['Open'] = df['mark_price']
        df['High'] = df['mark_price'] * 1.01
        df['Low'] = df['mark_price'] * 0.99
        df['Close'] = df['mark_price']
        df['Volume'] = df['volume'].fillna(0)

        if 'expiry' in df.columns:
            df['expiry_datetime'] = pd.to_datetime(df['expiry'], unit='ms')

        df = df.reset_index(drop=True)
        logger.info("Loaded %d options (snapshot only, not time series)", len(df))
        return df

    def _get_ticker(self, instrument_name: str) -> Optional[dict]:
        try:
            response = requests.get(
                f"{self.BASE_URL}/ticker",
                params={'instrument_name': instrument_name},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json().get('result')
        except requests.RequestException as e:
            logger.debug("Ticker fetch failed for %s: %s", instrument_name, e)
            return None

    def _load_contract_history(self, instrument_name: str,
                               start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
        end_ts = int(
            datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000
            if end_date
            else datetime.now().timestamp() * 1000
        )
        params = {
            'instrument_name': instrument_name,
            'start_timestamp': start_ts,
            'end_timestamp': end_ts,
            'resolution': '60',
        }
        try:
            response = requests.get(
                f"{self.BASE_URL}/get_tradingview_chart_data",
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise ValueError(f"Failed to load history for {instrument_name}: {e}") from e

        if 'result' not in data:
            raise ValueError("Unexpected Deribit response")

        result = data['result']
        df = pd.DataFrame({
            'timestamp': result.get('ticks', []),
            'Open': result.get('open', []),
            'High': result.get('high', []),
            'Low': result.get('low', []),
            'Close': result.get('close', []),
            'Volume': result.get('volume', []),
        })
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
        return df

    def get_underlying_price(self, currency: str) -> Optional[float]:
        try:
            response = requests.get(
                f"{self.BASE_URL}/get_index_price",
                params={'index_name': f'{currency.lower()}_usd'},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json().get('result', {}).get('index_price')
        except requests.RequestException as e:
            logger.debug("Could not fetch underlying price for %s: %s", currency, e)
            return None


def get_data_loader(source: str = 'yahoo', **kwargs) -> DataLoader:
    """
    Factory returning an initialised DataLoader for the given source.
    Raises ValueError for unsupported or unconfigured sources.
    """
    source = source.lower()

    if source in ('yahoo', 'yahoo_finance'):
        return YahooFinanceLoader()
    if source in ('alpha_vantage', 'alphavantage'):
        if not is_api_configured('alpha_vantage'):
            raise ValueError(
                "Alpha Vantage not configured. Set ALPHA_VANTAGE_API_KEY in .env"
            )
        return AlphaVantageLoader(**kwargs)
    if source == 'binance':
        return BinanceLoader(**kwargs)
    if source == 'deribit':
        return DeribitLoader(**kwargs)

    raise ValueError(
        f"Unsupported source: '{source}'. "
        "Available: yahoo, alpha_vantage, binance, deribit"
    )


def load_data(
    symbol: str,
    start_date: str,
    end_date: Optional[str] = None,
    source: str = 'yahoo',
    interval: str = '1d',
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Convenience wrapper with caching support.

    Example:
        df = load_data('BTC-USD', '2023-01-01', '2024-01-01')
    """
    if source == 'yahoo':
        return YahooFinanceLoader(use_cache=use_cache).load(
            symbol, start_date, end_date, interval
        )
    return get_data_loader(source).load(symbol, start_date, end_date)
