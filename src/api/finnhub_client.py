"""
Finnhub API Client for company data - EXTENDED VERSION
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List


class FinnhubClient:
    """Finnhub API Client for company data"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('FINNHUB_API_KEY', '')
        self.base_url = "https://finnhub.io/api/v1"
    
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Helper method to make API requests"""
        try:
            if params is None:
                params = {}
            params['token'] = self.api_key
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            print(f"API Error: {e}")
            return {}
    
    # BASIC COMPANY INFO
    def get_company_profile(self, symbol: str) -> dict:
        """Get company profile"""
        return self._make_request('stock/profile2', {'symbol': symbol})
    
    def get_basic_financials(self, symbol: str) -> dict:
        """Get basic financial metrics"""
        return self._make_request('stock/metric', {'symbol': symbol, 'metric': 'all'})
    
    def get_quote(self, symbol: str) -> dict:
        """Get real-time quote"""
        return self._make_request('quote', {'symbol': symbol})
    
    def get_peers(self, symbol: str) -> list:
        """Get company peers"""
        data = self._make_request('stock/peers', {'symbol': symbol})
        return data if isinstance(data, list) else []
    
    # INSIDER TRADING & OWNERSHIP
    def get_insider_transactions(self, symbol: str, limit: int = 10) -> list:
        """Get recent insider transactions"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        data = self._make_request('stock/insider-transactions', {
            'symbol': symbol,
            'from': start_date,
            'to': end_date
        })
        transactions = data.get('data', [])
        return transactions[:limit] if transactions else []
    
    def get_ownership(self, symbol: str) -> dict:
        """Get institutional ownership"""
        return self._make_request('stock/institutional-ownership', {'symbol': symbol})
    
    # ANALYST DATA
    def get_recommendation_trends(self, symbol: str) -> list:
        """Get analyst recommendation trends"""
        return self._make_request('stock/recommendation', {'symbol': symbol})
    
    def get_price_target(self, symbol: str) -> dict:
        """Get analyst price targets"""
        return self._make_request('stock/price-target', {'symbol': symbol})
    
    def get_upgrades_downgrades(self, symbol: str) -> list:
        """Get analyst upgrades/downgrades"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')  # 1 year
        
        data = self._make_request('stock/upgrade-downgrade', {
            'symbol': symbol,
            'from': start_date,
            'to': end_date
        })
        return data if isinstance(data, list) else []
    
    # EARNINGS & ESTIMATES
    def get_earnings(self, symbol: str) -> list:
        """Get earnings data"""
        return self._make_request('stock/earnings', {'symbol': symbol})
    
    def get_earnings_surprises(self, symbol: str) -> list:
        """Get earnings surprises history"""
        return self._make_request('stock/earnings', {'symbol': symbol})
    
    def get_revenue_estimates(self, symbol: str, freq: str = 'quarterly') -> list:
        """Get revenue estimates"""
        return self._make_request('stock/revenue-estimate', {'symbol': symbol, 'freq': freq})
    
    def get_eps_estimates(self, symbol: str, freq: str = 'quarterly') -> list:
        """Get EPS estimates"""
        return self._make_request('stock/eps-estimate', {'symbol': symbol, 'freq': freq})
    
    # DIVIDENDS
    def get_dividends(self, symbol: str) -> list:
        """Get dividend history"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=1825)).strftime('%Y-%m-%d')  # 5 years
        
        data = self._make_request('stock/dividend', {
            'symbol': symbol,
            'from': start_date,
            'to': end_date
        })
        return data if isinstance(data, list) else []
    
    # FINANCIAL STATEMENTS
    def get_financials_reported(self, symbol: str, freq: str = 'annual') -> dict:
        """Get financial statements (Balance Sheet, Income Statement, Cash Flow)
        
        Args:
            symbol: Stock ticker
            freq: 'annual' or 'quarterly'
        
        Returns:
            dict with 'data' list containing financial reports
        """
        return self._make_request('stock/financials-reported', {
            'symbol': symbol,
            'freq': freq
        })
    
    # NEWS & SENTIMENT
    def get_news_sentiment(self, symbol: str) -> dict:
        """Get news sentiment"""
        return self._make_request('news-sentiment', {'symbol': symbol})