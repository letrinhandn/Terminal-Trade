"""
Local parquet cache for OHLCV market data.
Organises files by asset class and uses MD5-keyed metadata for freshness checks.
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_CRYPTO_KEYWORDS  = {'BTC', 'ETH', 'SOL', 'ADA', 'BNB', 'USDT', 'USDC', '-USD'}
_ETF_SYMBOLS      = {'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO'}
_FOREX_CURRENCIES = {'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD'}


class DataCacheManager:
    """Manages a local parquet database for market data with merge-on-write semantics."""

    def __init__(self, base_dir: str = "market_data_cache"):
        self.base_dir = Path(base_dir)
        self._setup_directories()
        self.metadata_file = self.base_dir / "metadata.json"
        self.metadata = self._load_metadata()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_directories(self) -> None:
        for subdir in ('stocks', 'crypto', 'etf', 'options', 'forex'):
            (self.base_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _load_metadata(self) -> dict:
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            'symbols': {},
            'last_updated': {},
            'cache_stats': {'total_symbols': 0, 'total_records': 0, 'total_size_mb': 0},
        }

    def _save_metadata(self) -> None:
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    def _get_category(self, symbol: str) -> str:
        s = symbol.upper()
        if any(kw in s for kw in _CRYPTO_KEYWORDS):
            return 'crypto'
        if s in _ETF_SYMBOLS:
            return 'etf'
        if any(kw in s for kw in _FOREX_CURRENCIES):
            return 'forex'
        if any(kw in s for kw in ('CALL', 'PUT')) and any(c.isdigit() for c in s):
            return 'options'
        return 'stocks'

    def get_cache_path(self, symbol: str, interval: str = '1d') -> Path:
        category = self._get_category(symbol)
        clean = symbol.replace('-', '_').replace('/', '_').upper()
        subdir = self.base_dir / category / (clean[0] if clean else 'OTHER')
        subdir.mkdir(exist_ok=True)
        return subdir / f"{clean}_{interval}.parquet"

    def cache_key(self, symbol: str, start_date: str, end_date: str,
                  interval: str = '1d') -> str:
        return hashlib.md5(
            f"{symbol}_{start_date}_{end_date}_{interval}".encode()
        ).hexdigest()

    # ------------------------------------------------------------------
    # Read / write
    # ------------------------------------------------------------------

    def get_cached_data(self, symbol: str, start_date: str, end_date: str,
                        interval: str = '1d') -> pd.DataFrame | None:
        path = self.get_cache_path(symbol, interval)
        if not path.exists():
            return None

        try:
            df = pd.read_parquet(path)
            df.index = pd.to_datetime(df.index)

            start_dt = pd.to_datetime(start_date)
            end_dt   = pd.to_datetime(end_date) if end_date else pd.Timestamp.now()

            if df.index.min() <= start_dt and df.index.max() >= end_dt:
                mask = (df.index >= start_dt) & (df.index <= end_dt)
                logger.debug("Cache hit: %s (%s to %s)", symbol, start_date, end_date)
                return df[mask].copy()

            logger.debug("Cache partial: %s needs update", symbol)
            return None

        except Exception as e:
            logger.warning("Cache read error for %s: %s", symbol, e)
            return None

    def save_to_cache(self, symbol: str, df: pd.DataFrame, interval: str = '1d') -> None:
        if df is None or df.empty:
            return

        path = self.get_cache_path(symbol, interval)
        try:
            if path.exists():
                existing = pd.read_parquet(path)
                existing.index = pd.to_datetime(existing.index)
                df = pd.concat([existing, df])
                df = df[~df.index.duplicated(keep='last')].sort_index()

            df.to_parquet(path, compression='snappy')

            category   = self._get_category(symbol)
            symbol_key = f"{symbol}_{interval}"
            self.metadata['symbols'][symbol_key] = {
                'symbol': symbol,
                'category': category,
                'interval': interval,
                'first_date': df.index.min().strftime('%Y-%m-%d'),
                'last_date':  df.index.max().strftime('%Y-%m-%d'),
                'num_records': len(df),
                'file_size_kb': path.stat().st_size / 1024,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            self.metadata['last_updated'][symbol] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._update_cache_stats()
            self._save_metadata()

        except (IOError, OSError) as e:
            logger.warning("Failed to write cache for %s: %s", symbol, e)

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def _update_cache_stats(self) -> None:
        syms  = self.metadata['symbols']
        total_records  = sum(s['num_records'] for s in syms.values())
        total_size_kb  = sum(s['file_size_kb'] for s in syms.values())
        self.metadata['cache_stats'] = {
            'total_symbols': len(syms),
            'total_records': total_records,
            'total_size_mb': round(total_size_kb / 1024, 2),
            'last_scan': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def clear_old_cache(self, days_old: int = 90) -> int:
        """Remove cache files older than `days_old`. Returns count removed."""
        cutoff = datetime.now() - timedelta(days=days_old)
        removed = 0

        for key, info in list(self.metadata['symbols'].items()):
            last = datetime.strptime(info['last_updated'], '%Y-%m-%d %H:%M:%S')
            if last < cutoff:
                path = self.get_cache_path(info['symbol'], info['interval'])
                if path.exists():
                    path.unlink()
                    removed += 1
                del self.metadata['symbols'][key]

        if removed:
            self._update_cache_stats()
            self._save_metadata()
            logger.info("Removed %d stale cache files (older than %d days)", removed, days_old)

        return removed

    def get_cache_info(self, symbol: str | None = None) -> dict:
        if symbol:
            return {k: v for k, v in self.metadata['symbols'].items()
                    if v['symbol'] == symbol}
        return self.metadata

    def log_cache_stats(self) -> None:
        stats = self.metadata['cache_stats']
        by_category: dict = {}
        for info in self.metadata['symbols'].values():
            by_category[info['category']] = by_category.get(info['category'], 0) + 1

        logger.info(
            "Cache: %d symbols | %d records | %.2f MB | by category: %s",
            stats['total_symbols'],
            stats['total_records'],
            stats['total_size_mb'],
            by_category,
        )


_cache_manager: DataCacheManager | None = None


def get_cache_manager() -> DataCacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = DataCacheManager()
    return _cache_manager
