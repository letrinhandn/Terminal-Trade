"""
TradingView Widget - Embedded TradingView chart
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView


class TradingViewWidget(QWidget):
    """TradingView embedded chart widget"""
    
    # Signals to notify parent
    symbol_changed = pyqtSignal(str)
    maximize_requested = pyqtSignal(bool)  # True = maximize, False = restore
    
    def __init__(self):
        super().__init__()
        self.current_symbol = "AAPL"
        self.is_maximized = False
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title + Controls bar - FIXED HEIGHT
        title_controls = QWidget()
        title_controls.setFixedHeight(45)  # FIXED - won't take more space
        title_controls.setStyleSheet("""
            QWidget {
                background: #1a1a1a;
                border-bottom: 2px solid #ff6600;
            }
        """)
        
        controls_layout = QHBoxLayout(title_controls)
        controls_layout.setContentsMargins(8, 5, 8, 5)
        controls_layout.setSpacing(8)
        
        # Title
        title_label = QLabel("TRADINGVIEW")
        title_label.setStyleSheet("color: #ff6600; font-weight: bold; font-size: 10pt; border: none;")
        
        controls_layout.addWidget(title_label)
        controls_layout.addSpacing(15)
        
        symbol_label = QLabel("Symbol:")
        symbol_label.setStyleSheet("color: #ff8800; font-weight: bold; border: none;")
        
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("AAPL, BTC-USD...")
        self.symbol_input.returnPressed.connect(self.on_symbol_changed)
        self.symbol_input.setMaximumWidth(120)
        self.symbol_input.setFixedHeight(28)
        
        interval_label = QLabel("Int:")
        interval_label.setStyleSheet("color: #ff8800; font-weight: bold; border: none;")
        
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1 min", "5 min", "15 min", "1 hour", "1 day", "1 week"])
        self.interval_combo.setCurrentText("1 day")
        self.interval_combo.currentTextChanged.connect(self.load_chart)
        self.interval_combo.setMaximumWidth(80)
        self.interval_combo.setFixedHeight(28)
        
        load_btn = QPushButton("Load Chart")
        load_btn.clicked.connect(self.on_symbol_changed)
        load_btn.setFixedHeight(28)
        load_btn.setStyleSheet("""
            QPushButton {
                background: #ff6600;
                color: #000000;
                font-weight: bold;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #ff8800;
            }
            QPushButton:pressed {
                background: #cc5500;
            }
        """)
        
        # Maximize/Minimize button
        self.max_btn = QPushButton("⛶ Maximize")
        self.max_btn.clicked.connect(self.toggle_maximize)
        self.max_btn.setFixedHeight(28)
        self.max_btn.setStyleSheet("""
            QPushButton {
                background: #cc5500;
                color: #000000;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: #ff6600;
            }
        """)
        
        controls_layout.addWidget(symbol_label)
        controls_layout.addWidget(self.symbol_input)
        controls_layout.addSpacing(5)
        controls_layout.addWidget(interval_label)
        controls_layout.addWidget(self.interval_combo)
        controls_layout.addSpacing(5)
        controls_layout.addWidget(load_btn)
        controls_layout.addWidget(self.max_btn)
        controls_layout.addStretch()
        
        # WebView for TradingView - THIS GETS ALL REMAINING HEIGHT
        self.webview = QWebEngineView()
        self.webview.setStyleSheet("border: none;")
        
        # FORCE MINIMUM HEIGHT FOR WEBVIEW - CRITICAL!
        self.webview.setMinimumHeight(600)  # Force at least 600px tall
        
        # Add to main layout
        layout.addWidget(title_controls, 0)  # 0 = fixed, won't grow
        layout.addWidget(self.webview, 1)    # 1 = GROWS TO FILL SPACE
        
        # FORCE MINIMUM HEIGHT FOR THE ENTIRE WIDGET TOO!
        self.setMinimumHeight(650)  # Widget itself must be at least 650px
        
        # Load default chart
        self.load_chart()
    
    def toggle_maximize(self):
        """Toggle maximize/minimize chart"""
        self.is_maximized = not self.is_maximized
        
        if self.is_maximized:
            self.max_btn.setText("⛶ Restore")
            # Emit signal to hide side panels
            self.maximize_requested.emit(True)
        else:
            self.max_btn.setText("⛶ Maximize")
            # Emit signal to show side panels
            self.maximize_requested.emit(False)
    
    def on_symbol_changed(self):
        """Handle symbol change and emit signal to sync all panels"""
        symbol = self.symbol_input.text().strip().upper()
        if symbol:
            self.current_symbol = symbol
            self.load_chart()
            # Emit signal to sync other panels
            self.symbol_changed.emit(symbol)
    
    def detect_exchange_and_format(self, symbol: str) -> str:
        """Detect correct exchange and format symbol for TradingView"""
        symbol = symbol.upper().strip()
        
        # Common crypto symbols (always use BINANCE with USDT pairing)
        crypto_symbols = [
            'BTC', 'ETH', 'SOL', 'DOGE', 'AVAX', 'ADA', 'DOT', 'MATIC', 
            'LINK', 'UNI', 'XRP', 'LTC', 'BCH', 'ATOM', 'ALGO', 'XLM',
            'VET', 'ICP', 'FIL', 'SAND', 'MANA', 'AXS', 'SHIB', 'APE',
            'NEAR', 'FTM', 'AAVE', 'GRT', 'CRV', 'SNX', 'COMP', 'MKR',
            'SUSHI', 'YFI', '1INCH', 'ENJ', 'CHZ', 'BAT', 'ZRX', 'ANKR'
        ]
        
        # If already has exchange prefix, use as-is
        if ':' in symbol:
            return symbol
        
        # If has USD/USDT suffix, it's crypto on BINANCE
        if symbol.endswith('USD') or symbol.endswith('USDT'):
            base = symbol.replace('USDT', '').replace('USD', '')
            return f"BINANCE:{base}USDT"
        
        # If base symbol is in crypto list, add USDT and use BINANCE
        base_symbol = symbol.replace('-', '')
        if base_symbol in crypto_symbols:
            return f"BINANCE:{base_symbol}USDT"
        
        # Check for forex pairs (format: XXXYYY where X=base, Y=quote)
        forex_bases = ['EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD']
        forex_quotes = ['USD', 'EUR', 'GBP', 'JPY']
        if len(symbol) == 6 and symbol[:3] in forex_bases and symbol[3:] in forex_quotes:
            return f"FX:{symbol}"
        
        # Check for index symbols
        indices = ['SPX', 'DJI', 'IXIC', 'VIX', 'RUT', 'NDX']
        if symbol in indices:
            return f"INDEX:{symbol}"
        
        # Special case: NASDAQ index
        if symbol == 'NASDAQ':
            return "NASDAQ:NDAQ"
        
        # Default: treat as US stock on NASDAQ
        return f"NASDAQ:{symbol}"
    
    def load_chart(self):
        """Load TradingView chart (internal only)"""
        symbol = self.symbol_input.text().strip().upper()
        if not symbol:
            symbol = self.current_symbol
        
        self.current_symbol = symbol
        
        # Map interval
        interval_map = {
            "1 min": "1",
            "5 min": "5",
            "15 min": "15",
            "1 hour": "60",
            "1 day": "D",
            "1 week": "W"
        }
        interval = interval_map.get(self.interval_combo.currentText(), "D")
        
        # Detect exchange and format symbol
        tv_symbol = self.detect_exchange_and_format(symbol)
        
        # Generate HTML
        html = self.generate_tradingview_html(tv_symbol, interval)
        
        # Load HTML with baseUrl for stability
        self.webview.setHtml(html, QUrl("https://s.tradingview.com/"))
    
    def generate_tradingview_html(self, symbol: str, interval: str) -> str:
        """Generate TradingView widget HTML - FIXED for Qt WebEngine"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        html, body {{ 
            margin: 0; 
            padding: 0; 
            height: 100%; 
            width: 100%;
            background: #131722; 
            overflow: hidden;
        }}
        #tradingview_widget {{ 
            width: 100%; 
            height: 100%; 
        }}
    </style>
</head>
<body>
    <div id="tradingview_widget"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
        // Fit chart to exact WebView size
        function fitChart() {{
            const h = document.documentElement.clientHeight;
            const w = document.documentElement.clientWidth;
            const container = document.getElementById('tradingview_widget');
            if (container) {{
                container.style.height = h + 'px';
                container.style.width = w + 'px';
            }}
        }}
        
        window.addEventListener('resize', fitChart);
        fitChart();
        
        // Create TradingView widget with autosize
        new TradingView.widget({{
            "autosize": true,
            "width": "100%",
            "height": document.documentElement.clientHeight,
            "symbol": "{symbol}",
            "interval": "{interval}",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "allow_symbol_change": true,
            "container_id": "tradingview_widget",
            "studies": [
                "MASimple@tv-basicstudies",
                "MACD@tv-basicstudies",
                "RSI@tv-basicstudies",
                "BB@tv-basicstudies"
            ],
            "show_popup_button": true,
            "popup_width": "1000",
            "popup_height": "650"
        }});
    </script>
</body>
</html>
"""
    
    def set_symbol(self, symbol: str):
        """Set symbol from external source"""
        self.symbol_input.setText(symbol)
        self.load_chart()