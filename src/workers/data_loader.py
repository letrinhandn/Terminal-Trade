"""
DataLoader - Background thread for loading market data
"""

import yfinance as yf
from PyQt6.QtCore import QThread, pyqtSignal
from utils import format_symbol_for_yfinance


class DataLoader(QThread):
    """Background thread for loading market data"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, symbol: str):
        super().__init__()
        self.symbol = symbol  # Store original user input
    
    def run(self):
        """Load data in background"""
        try:
            # Convert to yfinance format
            yf_symbol = format_symbol_for_yfinance(self.symbol)
            
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period="1d")
            
            if hist.empty:
                self.error.emit(f"No data for {self.symbol}")
                return
            
            info = ticker.info
            latest = hist.iloc[-1]
            previous_close = info.get('previousClose', latest['Close'])
            
            data = {
                'symbol': self.symbol,  # Return original user input
                'yf_symbol': yf_symbol,  # Store converted symbol for reference
                'price': latest['Close'],
                'change': latest['Close'] - previous_close,
                'change_pct': ((latest['Close'] - previous_close) / previous_close * 100) if previous_close else 0,
                'high': latest['High'],
                'low': latest['Low'],
                'volume': latest['Volume'],
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'name': info.get('longName', self.symbol),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
            }
            
            # Get historical data
            hist_period = ticker.history(period="1y")
            data['history'] = hist_period
            
            # Get news
            try:
                data['news'] = ticker.news[:5]
            except:
                data['news'] = []
            
            self.finished.emit(data)
            
        except Exception as e:
            self.error.emit(str(e))