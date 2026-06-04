"""
Overview Tab - Market Data, Company Info, Financials
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QGroupBox, QTextEdit, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

# Import widgets
from widgets import (
    PriceWidget, FundamentalsWidget, NewsWidget, 
    TradingViewWidget, CompanyInfoWidget, FinancialStatementsWidget
)
from workers import DataLoader


class OverviewTab(QWidget):
    """Overview tab with sub-tabs: Market Data and Company Info"""
    
    def __init__(self):
        super().__init__()
        self.current_symbol = "AAPL"
        
        # Panel visibility states (for Market View only)
        self.left_panel_visible = True
        self.right_panel_visible = True
        
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # SUB-TABS (like Options tab)
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #000;
            }
            QTabBar::tab {
                background: #1a1a1a;
                color: #888;
                padding: 10px 30px;
                border: 1px solid #333;
                border-bottom: none;
                font-weight: bold;
                font-size: 10pt;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #ff6600;
                color: #000;
            }
            QTabBar::tab:hover:!selected {
                background: #333;
                color: #ff8800;
            }
        """)
        
        # TAB 1: MARKET DATA
        market_data_tab = QWidget()
        market_layout = QHBoxLayout(market_data_tab)
        market_layout.setContentsMargins(5, 5, 5, 5)
        market_layout.setSpacing(5)
        
        # LEFT: Price + Fundamentals
        self.left_panel = QWidget()
        self.left_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        
        self.price_widget = PriceWidget()
        self.fundamentals_widget = FundamentalsWidget()
        
        left_layout.addWidget(self.price_widget)
        left_layout.addWidget(self.fundamentals_widget, 1)
        
        # CENTER: TradingView Chart
        center_panel = QWidget()
        center_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        
        self.tradingview = TradingViewWidget()
        center_layout.addWidget(self.tradingview, 1)
        
        # Connect TradingView signals
        self.tradingview.symbol_changed.connect(self.sync_all_panels)
        self.tradingview.maximize_requested.connect(self.handle_maximize_request)
        
        # RIGHT: News
        self.right_panel = QWidget()
        self.right_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        self.news_widget = NewsWidget()
        right_layout.addWidget(self.news_widget, 1)
        
        # Connect News search signal
        self.news_widget.symbol_searched.connect(self.sync_all_panels)
        
        # Add 3 panels to market view (2-6-2 ratio)
        market_layout.addWidget(self.left_panel, 2)
        market_layout.addWidget(center_panel, 6)
        market_layout.addWidget(self.right_panel, 2)
        
        # TAB 2: COMPANY INFO
        company_info_tab = QWidget()
        company_layout = QVBoxLayout(company_info_tab)
        company_layout.setContentsMargins(5, 5, 5, 5)
        company_layout.setSpacing(0)
        
        self.company_info_widget = CompanyInfoWidget()
        company_layout.addWidget(self.company_info_widget, 1)
        
        # TAB 3: FINANCIALS
        financials_tab = QWidget()
        financials_layout = QVBoxLayout(financials_tab)
        financials_layout.setContentsMargins(5, 5, 5, 5)
        financials_layout.setSpacing(0)
        
        self.financials_widget = FinancialStatementsWidget()
        financials_layout.addWidget(self.financials_widget, 1)
        
        # Add tabs
        self.sub_tabs.addTab(market_data_tab, "MARKET DATA")
        self.sub_tabs.addTab(company_info_tab, "COMPANY INFO")
        self.sub_tabs.addTab(financials_tab, "FINANCIALS")
        
        # Connect tab change
        self.sub_tabs.currentChanged.connect(self.on_sub_tab_changed)
        
        main_layout.addWidget(self.sub_tabs)
        
        # COMMAND LOG - BOTTOM
        log_group = QGroupBox("SYSTEM LOG")
        log_group.setStyleSheet("""
            QGroupBox {
                color: #ff6600;
                font-weight: bold;
                border: 2px solid #ff6600;
                border-radius: 5px;
                margin-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(5, 10, 5, 5)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(80)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: #000;
                color: #ff8800;
                border: 1px solid #333;
            }
        """)
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        main_layout.addWidget(log_group)
        
        # Log initial messages
        self.log_formatted("Overview tab ready - Type symbol in TradingView or News search", "success")
        self.log_formatted("Try: AAPL, BTC, TSLA, MSFT, ETH, etc.", "info")
    
    def on_sub_tab_changed(self, index: int):
        """Handle sub-tab change"""
        if index == 0:
            self.log_formatted("Switched to MARKET DATA view", "info")
        elif index == 1:
            self.log_formatted("Switched to COMPANY INFO view", "info")
            # Refresh company info for current symbol
            if self.current_symbol:
                self.company_info_widget.update_data(self.current_symbol)
        elif index == 2:
            self.log_formatted("Switched to FINANCIALS view", "info")
            # Refresh financials for current symbol
            if self.current_symbol:
                self.financials_widget.update_data(self.current_symbol)
    
    def sync_all_panels(self, symbol: str):
        """Sync all panels when symbol changes from any source"""
        symbol = symbol.strip().upper()
        if not symbol:
            return
        
        self.current_symbol = symbol
        
        # Update TradingView (if not already matching)
        if self.tradingview.current_symbol != symbol:
            self.tradingview.symbol_input.setText(symbol)
            self.tradingview.current_symbol = symbol
            self.tradingview.load_chart()
        
        # Update News search (if not already matching)
        if self.news_widget.current_symbol != symbol:
            self.news_widget.search_input.setText(symbol)
            self.news_widget.current_symbol = symbol
        
        # Load data for all panels
        self.load_symbol(symbol)
        
        # Update Company Info if on that tab
        if self.sub_tabs.currentIndex() == 1:
            self.company_info_widget.update_data(symbol)
        
        # Update Financials if on that tab
        if self.sub_tabs.currentIndex() == 2:
            self.financials_widget.update_data(symbol)
    
    def handle_maximize_request(self, maximize: bool):
        """Handle maximize/restore request from TradingView"""
        if maximize:
            self.maximize_chart()
        else:
            self.restore_chart()
    
    def maximize_chart(self):
        """Maximize TradingView chart (hide side panels)"""
        self.left_panel.hide()
        self.right_panel.hide()
        self.left_panel_visible = False
        self.right_panel_visible = False
    
    def restore_chart(self):
        """Restore chart to normal size (show side panels)"""
        self.left_panel.show()
        self.right_panel.show()
        self.left_panel_visible = True
        self.right_panel_visible = True
    
    def load_symbol(self, symbol: str):
        """Load symbol data (called by sync_all_panels) with error handling"""
        try:
            self.log_formatted(f"Loading {symbol}...", "loading")
            self.current_symbol = symbol
            
            # Stop any existing loader
            if hasattr(self, 'loader') and self.loader:
                try:
                    self.loader.terminate()
                    self.loader.wait(100)  # Wait max 100ms
                except Exception as e:
                    logger.debug("Could not stop previous loader: %s", e)
            
            # Load data in background
            self.loader = DataLoader(symbol)
            self.loader.finished.connect(self.on_data_loaded)
            self.loader.error.connect(self.on_data_error)
            self.loader.start()
            
            # Load TradingView chart
            if hasattr(self, 'tradingview'):
                self.tradingview.set_symbol(symbol)
        except Exception as e:
            self.log_formatted(f"Error loading {symbol}: {str(e)}", "error")
            logger.warning("Error in load_symbol for %s: %s", symbol, e)
    
    def on_data_loaded(self, data: dict):
        """Handle loaded data"""
        self.price_widget.update_price(data)
        self.fundamentals_widget.update_data(data)
        self.news_widget.update_news(data.get('news', []))
        
        # Update Company Info widget with Finnhub data
        self.company_info_widget.update_data(data['symbol'])
        
        self.log_formatted(f"{data['symbol']} loaded successfully", "success")
    
    def on_data_error(self, error: str):
        """Handle data error"""
        self.log_formatted(f"Error: {error}", "error")
    
    def log_formatted(self, message: str, msg_type: str = "info"):
        """Log message with formatting"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Color and icon based on type
        if msg_type == "success":
            color = "#00ff00"
            icon = "✓"
        elif msg_type == "error":
            color = "#ff3333"
            icon = "✗"
        elif msg_type == "loading":
            color = "#ffaa00"
            icon = "⏳"
        elif msg_type == "command":
            color = "#ff6600"
            icon = ">>"
        else:  # info
            color = "#00aaff"
            icon = "•"
        
        html = f'<span style="color: #666;">[{timestamp}]</span> <span style="color: {color}; font-weight: bold;">{icon}</span> <span style="color: {color};">{message}</span>'
        
        self.log_text.append(html)
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def log(self, message: str):
        """Log message (deprecated, use log_formatted)"""
        self.log_formatted(message, "info")