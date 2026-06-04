"""
Data Orchestrator - Smart routing between Deribit, Coindesk, and Cache
The brain that decides: cache vs API, live vs historical
"""

import pandas as pd
from datetime import date, datetime, timedelta
from typing import Tuple, Optional, List
from PyQt6.QtCore import QObject, pyqtSignal

from .clients.deribit_client import DeribitClient
from .clients.coindesk_client import CoindeskClient
from .cache.cache_manager import CacheManager


class DataOrchestrator(QObject):
    """
    Orchestrates data fetching with intelligent caching
    Minimizes API usage while keeping data fresh
    """
    
    # Signals
    progress = pyqtSignal(int, str)  # percent, message
    finished = pyqtSignal(pd.DataFrame, dict)  # df, provenance_info
    error = pyqtSignal(str)  # error message
    
    def __init__(self, api_key: str):
        super().__init__()
        self.deribit = DeribitClient(api_key)
        self.coindesk = CoindeskClient(api_key)
        self.cache = CacheManager()
        self.api_key = api_key
    
    def get_chain(self, underlying: str, mode: str = "live", 
                  force: bool = False, expiries: Optional[List[str]] = None) -> Tuple[pd.DataFrame, dict]:
        """
        Get options chain with intelligent routing
        
        Args:
            underlying: BTC or ETH
            mode: "live" or "historical"
            force: Force API fetch (bypass cache)
            expiries: Optional expiry filter
            
        Returns:
            (DataFrame, provenance_info dict)
        """
        provenance = {
            'source': '',
            'from_cache': False,
            'from_api': False,
            'timestamp': datetime.now()
        }
        
        try:
            if mode == "live":
                # Live mode: use Deribit
                return self._get_live_chain(underlying, force, expiries, provenance)
            else:
                # Historical mode: use Coindesk + cache
                return self._get_historical_chain(underlying, force, provenance)
                
        except Exception as e:
            self.error.emit(str(e))
            return pd.DataFrame(), provenance
    
    def _get_live_chain(self, underlying: str, force: bool, 
                        expiries: Optional[List[str]], provenance: dict) -> Tuple[pd.DataFrame, dict]:
        """Get live chain from Deribit (with 10-min cache)"""
        
        today = date.today()
        
        # Check cache first (if not force)
        if not force:
            cached_dates = self.cache.get_cached_dates(underlying)
            
            if today in cached_dates:
                # Check if stale (10-min TTL for live)
                if not self.cache.is_stale(underlying, today, self.cache.TTL_LIVE):
                    # Use cache
                    self.progress.emit(50, "Loading from cache...")
                    df = self.cache.read_parquets(underlying, [today])
                    
                    if not df.empty:
                        provenance['source'] = 'deribit_cache'
                        provenance['from_cache'] = True
                        self.progress.emit(100, "Loaded from cache")
                        return df, provenance
        
        # Fetch from Deribit API
        self.progress.emit(30, "Fetching from Deribit API...")
        df = self.deribit.fetch_chain_snapshot(underlying, expiries)
        
        if df.empty:
            raise RuntimeError("No data received from Deribit")
        
        # Cache the result
        self.progress.emit(80, "Caching data...")
        self.cache.write_parquet(underlying, today, df, source="deribit")
        
        provenance['source'] = 'deribit_api'
        provenance['from_api'] = True
        self.progress.emit(100, "Fetched from API")
        
        return df, provenance
    
    def _get_historical_chain(self, underlying: str, force: bool, 
                             provenance: dict) -> Tuple[pd.DataFrame, dict]:
        """Get historical chain from Coindesk (with 24h cache)"""
        
        # Get last 7 days (excluding today - use historical data only)
        end = date.today() - timedelta(days=1)  # Yesterday
        start = end - timedelta(days=6)  # 7 days total
        
        return self.get_surface(underlying, start, end, force)
    
    def get_surface(self, underlying: str, start: date, end: date, 
                    force: bool = False) -> Tuple[pd.DataFrame, dict]:
        """
        Get volatility surface data (historical)
        Uses intelligent caching to minimize Coindesk API calls
        
        Args:
            underlying: BTC or ETH
            start: Start date
            end: End date (must be in the past, not today or future)
            force: Force API fetch
            
        Returns:
            (DataFrame, provenance_info)
        """
        provenance = {
            'source': 'coindesk',
            'from_cache': False,
            'from_api': False,
            'cached_days': 0,
            'fetched_days': 0,
            'timestamp': datetime.now()
        }
        
        try:
            # Validate: don't request future dates or today (historical API only has past data)
            today = date.today()
            if end >= today:
                end = today - timedelta(days=1)  # Use yesterday as max
                self.progress.emit(10, f"Adjusted end date to {end} (historical data only)")
            
            if start >= today:
                start = today - timedelta(days=7)  # Default to last 7 days
                self.progress.emit(10, f"Adjusted start date to {start}")
            
            # Get missing dates
            if force:
                # Force: mark all as missing
                missing_dates = []
                current = start
                while current <= end:
                    self.cache.mark_stale(underlying, current)
                    missing_dates.append(current)
                    current += timedelta(days=1)
            else:
                missing_dates = self.cache.get_missing_dates(underlying, start, end)
            
            # Get cached dates
            all_dates = []
            current = start
            while current <= end:
                all_dates.append(current)
                current += timedelta(days=1)
            
            cached_dates = [d for d in all_dates if d not in missing_dates]
            
            provenance['cached_days'] = len(cached_dates)
            provenance['fetched_days'] = len(missing_dates)
            
            dfs = []
            
            # Load cached data
            if cached_dates:
                self.progress.emit(20, f"Loading {len(cached_dates)} days from cache...")
                cached_df = self.cache.read_parquets(underlying, cached_dates)
                if not cached_df.empty:
                    dfs.append(cached_df)
                    provenance['from_cache'] = True
            
            # Fetch missing data
            if missing_dates:
                total = len(missing_dates)
                for i, day in enumerate(missing_dates):
                    progress_pct = 20 + int((i / total) * 70)
                    self.progress.emit(progress_pct, f"Fetching {day} from Coindesk API...")
                    
                    df_day = self.coindesk.fetch_day(underlying, day)
                    
                    if not df_day.empty:
                        # Cache it
                        self.cache.write_parquet(underlying, day, df_day, source="coindesk")
                        dfs.append(df_day)
                
                provenance['from_api'] = True
            
            # Merge all data
            if dfs:
                self.progress.emit(95, "Merging data...")
                result = pd.concat(dfs, ignore_index=True)
                self.progress.emit(100, "Complete")
                return result, provenance
            else:
                raise RuntimeError("No data available")
                
        except Exception as e:
            self.error.emit(str(e))
            return pd.DataFrame(), provenance
    
    def get_contract_detail(self, symbol: str, days: int = 30) -> Tuple[pd.DataFrame, dict]:
        """
        Get detailed history for a single contract
        
        Args:
            symbol: Contract symbol
            days: Days of history
            
        Returns:
            (DataFrame, provenance_info)
        """
        provenance = {
            'source': 'deribit',
            'from_api': True,
            'timestamp': datetime.now()
        }
        
        try:
            self.progress.emit(50, f"Fetching contract history...")
            df = self.deribit.fetch_contract_history(symbol, days)
            self.progress.emit(100, "Complete")
            return df, provenance
            
        except Exception as e:
            self.error.emit(str(e))
            return pd.DataFrame(), provenance
    
    def get_cache_stats(self, underlying: str) -> dict:
        """Get cache statistics"""
        return self.cache.get_cache_stats(underlying)