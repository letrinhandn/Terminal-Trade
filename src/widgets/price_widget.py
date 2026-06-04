"""
Price Widget - Live price display
"""

from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont


class PriceWidget(QGroupBox):
    """Price display widget"""
    
    def __init__(self):
        super().__init__("LIVE PRICE")
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Symbol label
        self.symbol_label = QLabel("--")
        self.symbol_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.symbol_label.setStyleSheet("color: #00aaff;")
        
        # Price label
        self.price_label = QLabel("$0.00")
        self.price_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        
        # Change label
        self.change_label = QLabel("$0.00 (0.00%)")
        self.change_label.setFont(QFont("Arial", 14))
        
        # Stats
        self.stats_label = QLabel("")
        self.stats_label.setFont(QFont("Arial", 10))
        
        layout.addWidget(self.symbol_label)
        layout.addWidget(self.price_label)
        layout.addWidget(self.change_label)
        layout.addWidget(self.stats_label)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setMaximumWidth(300)
    
    def update_price(self, data: dict):
        """Update price display"""
        self.symbol_label.setText(data['symbol'])
        self.price_label.setText(f"${data['price']:.2f}")
        
        change = data['change']
        change_pct = data['change_pct']
        
        if change >= 0:
            color = "#00ff00"
            arrow = "▲"
        else:
            color = "#ff0000"
            arrow = "▼"
        
        self.change_label.setText(f"{arrow} ${abs(change):.2f} ({change_pct:+.2f}%)")
        self.change_label.setStyleSheet(f"color: {color};")
        
        # Format numbers
        def format_num(num):
            if num >= 1e12:
                return f"${num/1e12:.2f}T"
            elif num >= 1e9:
                return f"${num/1e9:.2f}B"
            elif num >= 1e6:
                return f"${num/1e6:.1f}M"
            else:
                return f"${num:,.0f}"
        
        stats = f"""High: ${data['high']:.2f}
Low:  ${data['low']:.2f}
Volume: {format_num(data['volume'])}
Market Cap: {format_num(data['market_cap'])}"""
        
        self.stats_label.setText(stats)