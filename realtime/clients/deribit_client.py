"""
Deribit API Client - Live Options Chain
Real-time options data from Deribit exchange (FREE, no API key needed)
"""

import requests
import pandas as pd
from datetime import datetime, date
from typing import Optional, List, Dict, Any


class DeribitClient:
    """Deribit live options data client - FREE public API"""
    
    BASE_URL = "https://www.deribit.com/api/v2"
    
    def __init__(self, api_key: str = ""):
        # Deribit public API doesn't need authentication for market data
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
    
    def fetch_instruments(self, underlying: str) -> pd.DataFrame:
        """
        Fetch available options instruments from Deribit
        
        Args:
            underlying: BTC or ETH
            
        Returns:
            DataFrame with columns: instrument_name, expiry_date, strike, option_type
        """
        try:
            url = f"{self.BASE_URL}/public/get_instruments"
            params = {
                "currency": underlying.upper(),
                "kind": "option",
                "expired": "false"
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'result' not in data:
                return pd.DataFrame()
            
            instruments = []
            for item in data['result']:
                # Parse instrument name: BTC-29DEC23-40000-C
                parts = item['instrument_name'].split('-')
                if len(parts) >= 4:
                    exp_str = parts[1]  # e.g., "29DEC23"
                    strike = float(parts[2])
                    opt_type = parts[3]  # C or P
                    
                    # Parse expiry date
                    try:
                        expiry_dt = datetime.strptime(exp_str, "%d%b%y").date()
                    except:
                        expiry_dt = None
                    
                    instruments.append({
                        'instrument_name': item['instrument_name'],
                        'expiry_date': expiry_dt,
                        'strike': strike,
                        'option_type': opt_type,
                        'base': underlying.upper()
                    })
            
            return pd.DataFrame(instruments)
            
        except Exception as e:
            print(f"Deribit fetch_instruments error: {e}")
            return pd.DataFrame()
    
    def fetch_chain_snapshot(self, underlying: str, expiries: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Fetch live options chain snapshot from Deribit
        
        Args:
            underlying: BTC or ETH
            expiries: Optional list of expiry dates to filter
            
        Returns:
            DataFrame with options chain data
        """
        try:
            # Get instruments first
            instruments_df = self.fetch_instruments(underlying)
            
            if instruments_df.empty:
                return pd.DataFrame()
            
            
            # Filter by expiries if specified
            if expiries:
                instruments_df = instruments_df[instruments_df['expiry_date'].isin(expiries)]
            
            # Fetch market data for each instrument (limit to first 50 for speed)
            chain_data = []
            
            for idx, instr in instruments_df.head(50).iterrows():
                instrument_name = instr['instrument_name']
                
                # Fetch ticker data for this instrument
                ticker = self._fetch_ticker(instrument_name)
                
                if ticker:
                    # Get underlying price
                    underlying_price = ticker.get('underlying_price', 0)
                    
                    # Calculate moneyness
                    strike = instr['strike']
                    moneyness = strike / underlying_price if underlying_price > 0 else 1.0
                    
                    # Calculate DTE
                    expiry_date = instr['expiry_date']
                    if expiry_date:
                        dte = (expiry_date - date.today()).days
                    else:
                        dte = 0
                    
                    chain_data.append({
                        'instrument': instrument_name,
                        'strike': strike,
                        'expiry_date': expiry_date,
                        'option_type': instr['option_type'],
                        'dte': dte,
                        'bid': ticker.get('best_bid_price', 0),
                        'ask': ticker.get('best_ask_price', 0),
                        'mark': ticker.get('mark_price', 0),
                        'last': ticker.get('last_price', 0),
                        'iv': ticker.get('mark_iv', 0) / 100.0,  # Convert from percentage
                        'delta': ticker.get('greeks', {}).get('delta', 0),
                        'gamma': ticker.get('greeks', {}).get('gamma', 0),
                        'vega': ticker.get('greeks', {}).get('vega', 0),
                        'theta': ticker.get('greeks', {}).get('theta', 0),
                        'rho': ticker.get('greeks', {}).get('rho', 0),
                        'open_interest': ticker.get('open_interest', 0),
                        'volume': ticker.get('stats', {}).get('volume', 0),
                        'spot_close': underlying_price,
                        'moneyness': moneyness,
                        'date': date.today()
                    })
            
            df = pd.DataFrame(chain_data)
            
            
            return df
            
        except Exception as e:
            print(f"Deribit fetch_chain_snapshot error: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def _fetch_ticker(self, instrument_name: str) -> Optional[Dict[str, Any]]:
        """Fetch ticker data for a single instrument"""
        try:
            url = f"{self.BASE_URL}/public/ticker"
            params = {"instrument_name": instrument_name}
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data and 'result' in data:
                return data['result']
            
            return None
            
        except Exception as e:
            print(f"Error fetching ticker for {instrument_name}: {e}")
            return None
    
    def fetch_contract_history(self, symbol: str, days: int = 7) -> pd.DataFrame:
        """
        Fetch historical IV/Greeks for a specific contract
        
        Args:
            symbol: Contract symbol
            days: Number of days of history
            
        Returns:
            DataFrame with timestamp, iv, delta, gamma, vega, theta
        """
        try:
            url = f"{self.BASE_URL}/historical/days"
            params = {
                "market": "deribit",
                "symbol": symbol,
                "limit": days
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'data' not in data:
                return pd.DataFrame()
            
            history = []
            for item in data['data']:
                history.append({
                    'timestamp': item.get('timestamp', ''),
                    'iv': float(item.get('iv', 0)),
                    'delta': float(item.get('delta', 0)),
                    'gamma': float(item.get('gamma', 0)),
                    'vega': float(item.get('vega', 0)),
                    'theta': float(item.get('theta', 0)),
                    'mark': float(item.get('mark', 0))
                })
            
            return pd.DataFrame(history)
            
        except Exception as e:
            print(f"Deribit fetch_contract_history error: {e}")
            return pd.DataFrame()