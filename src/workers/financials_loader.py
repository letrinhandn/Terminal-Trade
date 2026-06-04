"""
FinancialsLoader - Background thread for loading financial statements
"""

from PyQt6.QtCore import QThread, pyqtSignal


class FinancialsLoader(QThread):
    """Background thread for loading financial statements"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, symbol: str, freq: str, finnhub_client):
        super().__init__()
        self.symbol = symbol
        self.freq = freq
        self.finnhub = finnhub_client
    
    def run(self):
        """Load financial statements in background"""
        try:
            self.progress.emit(f"Loading {self.freq} financials for {self.symbol}...")
            data = self.finnhub.get_financials_reported(self.symbol, freq=self.freq)
            
            if data and 'data' in data:
                self.progress.emit(f"Loaded {len(data['data'])} reports")
            
            self.finished.emit(data)
            
        except Exception as e:
            self.error.emit(str(e))