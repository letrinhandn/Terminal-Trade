"""
Fundamentals Widget - Company fundamentals display
"""

import yfinance as yf
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QTableWidget, QTableWidgetItem
from src.utils.symbol_utils import format_symbol_for_yfinance


class FundamentalsWidget(QGroupBox):
    """Fundamentals display widget"""
    
    def __init__(self):
        super().__init__("FUNDAMENTALS")
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
    
    def update_data(self, data: dict):
        """Update fundamentals"""
        try:
            # Convert to yfinance format
            yf_symbol = format_symbol_for_yfinance(data['symbol'])
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            metrics = [
                ("Company", data.get('name', data['symbol'])),
                ("Sector", data.get('sector', 'N/A')),
                ("Industry", data.get('industry', 'N/A')),
                ("Market Cap", self.format_num(data.get('market_cap', 0))),
                ("P/E Ratio", f"{data.get('pe_ratio', 0):.2f}"),
                ("EPS", f"${info.get('trailingEps', 0):.2f}"),
                ("Beta", f"{info.get('beta', 0):.2f}"),
                ("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%"),
                ("52W High", f"${info.get('fiftyTwoWeekHigh', 0):.2f}"),
                ("52W Low", f"${info.get('fiftyTwoWeekLow', 0):.2f}"),
            ]
            
            self.table.setRowCount(len(metrics))
            
            for i, (key, value) in enumerate(metrics):
                self.table.setItem(i, 0, QTableWidgetItem(key))
                self.table.setItem(i, 1, QTableWidgetItem(str(value)))
        
        except Exception as e:
            print(f"Fundamentals error: {e}")
    
    def format_num(self, num):
        if num >= 1e12:
            return f"${num/1e12:.2f}T"
        elif num >= 1e9:
            return f"${num/1e9:.2f}B"
        elif num >= 1e6:
            return f"${num/1e6:.1f}M"
        else:
            return f"${num:,.0f}"