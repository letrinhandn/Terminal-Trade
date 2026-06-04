"""
CompanyInfoLoader - Background thread for loading company info data
"""

from PyQt6.QtCore import QThread, pyqtSignal
from utils import format_symbol_for_finnhub


class CompanyInfoLoader(QThread):
    """Background thread for loading company info data"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)  # Progress updates
    
    def __init__(self, symbol: str, finnhub_client):
        super().__init__()
        self.symbol = symbol
        self.finnhub = finnhub_client
    
    def run(self):
        """Load all company info data in background"""
        try:
            # Check if Finnhub supports this symbol
            fh_symbol = format_symbol_for_finnhub(self.symbol)
            
            if fh_symbol is None:
                # Crypto or index - Finnhub doesn't support, return minimal data
                self.finished.emit({
                    'symbol': self.symbol,
                    'is_crypto_or_index': True,
                    'message': 'Company data not available for crypto/index symbols'
                })
                return
            
            data = {}
            
            self.progress.emit("Loading quote...")
            data['quote'] = self.finnhub.get_quote(fh_symbol)
            
            self.progress.emit("Loading profile...")
            data['profile'] = self.finnhub.get_company_profile(fh_symbol)
            
            self.progress.emit("Loading financials...")
            data['financials'] = self.finnhub.get_basic_financials(fh_symbol)
            
            self.progress.emit("Loading targets...")
            data['price_target'] = self.finnhub.get_price_target(fh_symbol)
            
            self.progress.emit("Loading ratings...")
            data['recommendations'] = self.finnhub.get_recommendation_trends(fh_symbol)
            
            self.progress.emit("Loading earnings...")
            data['earnings'] = self.finnhub.get_earnings(fh_symbol)
            
            self.progress.emit("Loading estimates...")
            data['eps_estimates'] = self.finnhub.get_eps_estimates(fh_symbol)
            data['rev_estimates'] = self.finnhub.get_revenue_estimates(fh_symbol)
            
            self.progress.emit("Loading dividends...")
            data['dividends'] = self.finnhub.get_dividends(fh_symbol)
            
            self.progress.emit("Loading insiders...")
            data['insider_trans'] = self.finnhub.get_insider_transactions(fh_symbol, limit=10)
            
            self.progress.emit("Loading analyst actions...")
            data['upgrades'] = self.finnhub.get_upgrades_downgrades(fh_symbol)
            
            self.progress.emit("Loading peers...")
            data['peers'] = self.finnhub.get_peers(self.symbol)
            
            self.progress.emit("Complete!")
            self.finished.emit(data)
            
        except Exception as e:
            self.error.emit(str(e))