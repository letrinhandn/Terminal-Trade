"""
Smart Data Cache Manager
Manages local database of OHLCV data with intelligent caching
"""

import os
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
import hashlib


class DataCacheManager:
    """Smart local database for market data"""
    
    def __init__(self, base_dir: str = "market_data_cache"):
        self.base_dir = Path(base_dir)
        self.setup_directories()
        self.metadata_file = self.base_dir / "metadata.json"
        self.metadata = self.load_metadata()
    
    def setup_directories(self):
        """Create organized directory structure"""
        # Main categories
        self.stocks_dir = self.base_dir / "stocks"
        self.crypto_dir = self.base_dir / "crypto"
        self.etf_dir = self.base_dir / "etf"
        self.options_dir = self.base_dir / "options"
        self.forex_dir = self.base_dir / "forex"
        
        # Create all directories
        for dir_path in [self.stocks_dir, self.crypto_dir, self.etf_dir, 
                        self.options_dir, self.forex_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def load_metadata(self) -> dict:
        """Load metadata index"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            'symbols': {},
            'last_updated': {},
            'cache_stats': {
                'total_symbols': 0,
                'total_records': 0,
                'total_size_mb': 0
            }
        }
    
    def save_metadata(self):
        """Save metadata index"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def get_category(self, symbol: str) -> str:
        """Determine symbol category"""
        symbol_upper = symbol.upper()
        
        # Crypto
        if any(x in symbol_upper for x in ['BTC', 'ETH', 'SOL', 'ADA', 'BNB', 
                                            'USDT', 'USDC', '-USD']):
            return 'crypto'
        
        # ETF
        elif any(x in symbol_upper for x in ['SPY', 'QQQ', 'IWM', 'DIA', 
                                              'VTI', 'VOO']):
            return 'etf'
        
        # Options (contains option indicators)
        elif any(x in symbol_upper for x in ['CALL', 'PUT', 'C', 'P']) and \
             any(char.isdigit() for char in symbol_upper):
            return 'options'
        
        # Forex
        elif any(x in symbol_upper for x in ['EUR', 'GBP', 'JPY', 'CHF', 
                                              'AUD', 'CAD', 'NZD']):
            return 'forex'
        
        # Default to stocks
        else:
            return 'stocks'
    
    def get_cache_path(self, symbol: str, interval: str = '1d') -> Path:
        """Get file path for symbol data"""
        category = self.get_category(symbol)
        category_dir = self.base_dir / category
        
        # Clean symbol name
        clean_symbol = symbol.replace('-', '_').replace('/', '_').upper()
        
        # Create subdirectory by first letter for organization
        first_letter = clean_symbol[0] if clean_symbol else 'OTHER'
        symbol_dir = category_dir / first_letter
        symbol_dir.mkdir(exist_ok=True)
        
        # Filename: SYMBOL_INTERVAL.parquet (faster than CSV)
        filename = f"{clean_symbol}_{interval}.parquet"
        return symbol_dir / filename
    
    def cache_key(self, symbol: str, start_date: str, end_date: str, 
                  interval: str = '1d') -> str:
        """Generate unique cache key"""
        key_str = f"{symbol}_{start_date}_{end_date}_{interval}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_cached_data(self, symbol: str, start_date: str, end_date: str,
                       interval: str = '1d') -> pd.DataFrame:
        """Retrieve cached data if available and up-to-date"""
        cache_path = self.get_cache_path(symbol, interval)
        
        if not cache_path.exists():
            return None
        
        try:
            # Read cached data
            df = pd.read_parquet(cache_path)
            df.index = pd.to_datetime(df.index)
            
            # Check if cached data covers requested range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date) if end_date else pd.Timestamp.now()
            
            if df.index.min() <= start_dt and df.index.max() >= end_dt:
                # Filter to requested range
                mask = (df.index >= start_dt) & (df.index <= end_dt)
                filtered_df = df[mask].copy()
                
                print(f"✅ Cache HIT: {symbol} requested {start_date} to {end_date}")
                print(f"   Cached: {df.index.min().date()} to {df.index.max().date()} ({len(df)} bars)")
                print(f"   Filtered: {filtered_df.index.min().date()} to {filtered_df.index.max().date()} ({len(filtered_df)} bars)")
                return filtered_df
            else:
                print(f"⚠️ Cache PARTIAL: {symbol} (needs update)")
                return None  # ← CRITICAL FIX: Return None instead of full df
                
        except Exception as e:
            print(f"❌ Cache ERROR: {symbol} - {str(e)}")
            return None
    
    def save_to_cache(self, symbol: str, df: pd.DataFrame, interval: str = '1d'):
        """Save data to cache with intelligent merging"""
        if df is None or df.empty:
            return
        
        cache_path = self.get_cache_path(symbol, interval)
        
        try:
            # If cache exists, merge with existing data
            if cache_path.exists():
                existing_df = pd.read_parquet(cache_path)
                existing_df.index = pd.to_datetime(existing_df.index)
                
                # Combine and remove duplicates
                combined_df = pd.concat([existing_df, df])
                combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
                combined_df.sort_index(inplace=True)
                
                df = combined_df
            
            # Save to parquet (faster and smaller than CSV)
            df.to_parquet(cache_path, compression='snappy')
            
            # Update metadata
            category = self.get_category(symbol)
            symbol_key = f"{symbol}_{interval}"
            
            self.metadata['symbols'][symbol_key] = {
                'symbol': symbol,
                'category': category,
                'interval': interval,
                'first_date': df.index.min().strftime('%Y-%m-%d'),
                'last_date': df.index.max().strftime('%Y-%m-%d'),
                'num_records': len(df),
                'file_size_kb': cache_path.stat().st_size / 1024,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.metadata['last_updated'][symbol] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Update stats
            self.update_cache_stats()
            self.save_metadata()
            
            
        except Exception as e:
            pass
    
    def update_cache_stats(self):
        """Update cache statistics"""
        total_symbols = len(self.metadata['symbols'])
        total_records = sum(s['num_records'] for s in self.metadata['symbols'].values())
        total_size_kb = sum(s['file_size_kb'] for s in self.metadata['symbols'].values())
        
        self.metadata['cache_stats'] = {
            'total_symbols': total_symbols,
            'total_records': total_records,
            'total_size_mb': round(total_size_kb / 1024, 2),
            'last_scan': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_cache_info(self, symbol: str = None) -> dict:
        """Get cache information"""
        if symbol:
            matches = {k: v for k, v in self.metadata['symbols'].items() 
                      if v['symbol'] == symbol}
            return matches
        return self.metadata
    
    def clear_old_cache(self, days_old: int = 90):
        """Clear cache older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        removed = 0
        
        for symbol_key, info in list(self.metadata['symbols'].items()):
            last_updated = datetime.strptime(info['last_updated'], '%Y-%m-%d %H:%M:%S')
            
            if last_updated < cutoff_date:
                # Remove file
                category = info['category']
                symbol = info['symbol']
                interval = info['interval']
                cache_path = self.get_cache_path(symbol, interval)
                
                if cache_path.exists():
                    cache_path.unlink()
                    removed += 1
                
                # Remove from metadata
                del self.metadata['symbols'][symbol_key]
        
        if removed > 0:
            self.update_cache_stats()
            self.save_metadata()
            print(f"🗑️ Removed {removed} old cache files")
    
    def print_cache_stats(self):
        """Print cache statistics"""
        stats = self.metadata['cache_stats']
        
        print("\n" + "="*50)
        print("📊 MARKET DATA CACHE STATISTICS")
        print("="*50)
        print(f"Total Symbols:    {stats['total_symbols']}")
        print(f"Total Records:    {stats['total_records']:,}")
        print(f"Total Size:       {stats['total_size_mb']:.2f} MB")
        print(f"Last Scan:        {stats.get('last_scan', 'N/A')}")
        print("="*50)
        
        # Category breakdown
        categories = {}
        for info in self.metadata['symbols'].values():
            cat = info['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\n📂 BY CATEGORY:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat.upper():.<20} {count:>4} symbols")
        print("="*50 + "\n")


# Global cache instance
_cache_manager = None

def get_cache_manager() -> DataCacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = DataCacheManager()
    return _cache_manager