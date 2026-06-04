"""
Coindesk API Client - Historical Options Data
Used only for historical analysis & vol surfaces to avoid rate limits
"""

import requests
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Iterator, List, Optional


class CoindeskClient:
    """Coindesk historical options data client"""
    
    BASE_URL = "https://data-api.coindesk.com/options/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "accept": "application/json",
            "authorization": f"Bearer {api_key}"
        }
    
    def fetch_day(self, underlying: str, day: date) -> pd.DataFrame:
        """
        Fetch options data for a single day
        
        Args:
            underlying: BTC or ETH
            day: Date to fetch
            
        Returns:
            DataFrame with options data for that day
        """
        try:
            url = f"{self.BASE_URL}/historical/days"
            
            # Format date as YYYY-MM-DD
            date_str = day.strftime("%Y-%m-%d")
            
            # Validate: don't request today or future dates
            from datetime import date as date_class
            if day >= date_class.today():
                print(f"Coindesk fetch_day: Skipping future/today date {day} (historical API only)")
                return pd.DataFrame()
            
            params = {
                "market": "deribit",
                "base": underlying.upper(),
                "start_date": date_str,
                "end_date": date_str,
                "limit": 5000
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'data' not in data:
                return pd.DataFrame()
            
            records = []
            for item in data['data']:
                records.append({
                    'date': date_str,
                    'symbol': item.get('symbol', ''),
                    'strike': float(item.get('strike', 0)),
                    'expiry': item.get('expiry_date', ''),
                    'type': item.get('type', ''),
                    'mark': float(item.get('mark', 0)),
                    'iv': float(item.get('iv', 0)),
                    'delta': float(item.get('delta', 0)),
                    'gamma': float(item.get('gamma', 0)),
                    'vega': float(item.get('vega', 0)),
                    'theta': float(item.get('theta', 0)),
                    'oi': int(item.get('open_interest', 0)),
                    'volume': int(item.get('volume', 0)),
                    'underlying': underlying.upper()
                })
            
            df = pd.DataFrame(records)
            
            if not df.empty:
                # Calculate DTE
                df['expiry_dt'] = pd.to_datetime(df['expiry'])
                df['date_dt'] = pd.to_datetime(df['date'])
                df['dte'] = (df['expiry_dt'] - df['date_dt']).dt.days
            
            return df
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                print(f"Coindesk API: Bad Request for {day} - likely future date or invalid params")
            else:
                print(f"Coindesk fetch_day HTTP error for {day}: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Coindesk fetch_day error for {day}: {e}")
            return pd.DataFrame()
    
    def fetch_range(self, underlying: str, start: date, end: date) -> Iterator[pd.DataFrame]:
        """
        Fetch options data for a date range (yields per-day)
        
        Args:
            underlying: BTC or ETH
            start: Start date
            end: End date
            
        Yields:
            DataFrame for each day
        """
        current = start
        while current <= end:
            df = self.fetch_day(underlying, current)
            if not df.empty:
                yield df
            current += timedelta(days=1)
    
    def fetch_range_bulk(self, underlying: str, start: date, end: date) -> pd.DataFrame:
        """
        Fetch entire date range in one call (if API supports)
        
        Args:
            underlying: BTC or ETH
            start: Start date
            end: End date
            
        Returns:
            Combined DataFrame for all days
        """
        try:
            url = f"{self.BASE_URL}/historical/days"
            
            params = {
                "market": "deribit",
                "base": underlying.upper(),
                "start_date": start.strftime("%Y-%m-%d"),
                "end_date": end.strftime("%Y-%m-%d"),
                "limit": 10000
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'data' not in data:
                return pd.DataFrame()
            
            records = []
            for item in data['data']:
                records.append({
                    'date': item.get('date', ''),
                    'symbol': item.get('symbol', ''),
                    'strike': float(item.get('strike', 0)),
                    'expiry': item.get('expiry_date', ''),
                    'type': item.get('type', ''),
                    'mark': float(item.get('mark', 0)),
                    'iv': float(item.get('iv', 0)),
                    'delta': float(item.get('delta', 0)),
                    'gamma': float(item.get('gamma', 0)),
                    'vega': float(item.get('vega', 0)),
                    'theta': float(item.get('theta', 0)),
                    'oi': int(item.get('open_interest', 0)),
                    'volume': int(item.get('volume', 0)),
                    'underlying': underlying.upper()
                })
            
            df = pd.DataFrame(records)
            
            if not df.empty:
                df['expiry_dt'] = pd.to_datetime(df['expiry'])
                df['date_dt'] = pd.to_datetime(df['date'])
                df['dte'] = (df['expiry_dt'] - df['date_dt']).dt.days
            
            return df
            
        except Exception as e:
            print(f"Coindesk fetch_range_bulk error: {e}")
            return pd.DataFrame()