"""
Main Application Window - Professional Trading Terminal
"""

import sys
import warnings
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTabWidget, QCompleter, QMessageBox
)
from PyQt6.QtCore import Qt, QStringListModel, QTimer, QEvent
from PyQt6.QtGui import QFont, QPalette, QColor, QKeyEvent

from config.settings import APP_TITLE, APP_SUBTITLE, DEFAULT_WIDTH, DEFAULT_HEIGHT
from src.tabs import OverviewTab, BacktestTab, OptionsTab, PortfolioTab


class CommandLineEdit(QLineEdit):
    """Custom QLineEdit that prevents auto-completion"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._manual_completion = False
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.completer() and self.completer().popup().isVisible():
                self.completer().popup().hide()
            self.returnPressed.emit()
            event.accept()
            return
        
        if event.key() == Qt.Key.Key_Tab:
            if self.completer() and self.completer().popup().isVisible():
                index = self.completer().popup().currentIndex()
                if index.isValid():
                    completion = self.completer().completionModel().data(index)
                    if completion:
                        self._manual_completion = True
                        self.setText(completion)
                        self._manual_completion = False
                        self.completer().popup().hide()
                event.accept()
                return
        
        super().keyPressEvent(event)
    
    def event(self, event: QEvent):
        if event.type() == QEvent.Type.ShortcutOverride:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                event.accept()
                return True
        return super().event(event)


class TradingApp(QMainWindow):
    """Main Trading Terminal Application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE} - {APP_SUBTITLE}")
        self.setGeometry(100, 100, DEFAULT_WIDTH, DEFAULT_HEIGHT)
        
        # Set dark theme
        self.set_dark_theme()
        
        self.init_ui()
    
    def set_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(26, 26, 26))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(51, 51, 51))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(26, 26, 26))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(255, 102, 0))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 102, 0))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        
        self.setPalette(palette)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }
            QTabWidget::pane {
                border: 1px solid #ff6600;
                background: #000000;
            }
            QTabBar::tab {
                background: #1a1a1a;
                color: #888888;
                padding: 12px 25px;
                margin-right: 2px;
                border: 1px solid #333333;
                border-bottom: none;
                font-weight: bold;
                font-size: 10pt;
            }
            QTabBar::tab:selected {
                background: #ff6600;
                color: #000000;
            }
            QTabBar::tab:hover:!selected {
                background: #333333;
                color: #ff8800;
            }
            QGroupBox {
                border: 2px solid #ff6600;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                padding-top: 10px;
                background: #0a0a0a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #ff6600;
                background: #000000;
            }
            QTableWidget {
                background-color: #1a1a1a;
                gridline-color: #333333;
                color: white;
                selection-background-color: #ff6600;
                selection-color: black;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ff6600;
                padding: 5px;
                border: 1px solid #444444;
                font-weight: bold;
            }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background: #ff6600;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff8800;
            }
        """)
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        title_bar = QWidget()
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #000000, stop:0.5 #1a0a00, stop:1 #000000);
                border-bottom: 3px solid #ff6600;
            }
        """)
        title_bar.setMinimumHeight(60)
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(15, 5, 15, 5)
        
        title = QLabel("TERMINAL TRADE")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #ff9500; background: transparent; border: none;")
        
        subtitle = QLabel("Open Source Trading Platform")
        subtitle.setFont(QFont("Arial", 9))
        subtitle.setStyleSheet("color: #ffb366; background: transparent; border: none;")
        
        title_layout.addWidget(title)
        title_layout.addSpacing(20)
        title_layout.addWidget(subtitle)
        title_layout.addStretch()
        
        title_bar.setLayout(title_layout)
        
        command_bar = QWidget()
        command_bar.setStyleSheet("""
            QWidget {
                background: #0a0a0a;
                border-bottom: 2px solid #ff6600;
            }
        """)
        command_bar.setMinimumHeight(50)
        
        cmd_layout = QHBoxLayout(command_bar)
        cmd_layout.setContentsMargins(10, 5, 10, 5)
        cmd_layout.setSpacing(10)
        
        cmd_label = QLabel(">>")
        cmd_label.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        cmd_label.setStyleSheet("color: #ff6600; background: transparent; border: none;")
        
        self.global_command_input = CommandLineEdit()
        self.global_command_input.setPlaceholderText("Command... (e.g., BTC, AAPL FIN, BT RUN, OP CHAIN, HELP)")
        self.global_command_input.setFont(QFont("Consolas", 11))
        self.global_command_input.returnPressed.connect(self.execute_global_command)
        self.global_command_input.setStyleSheet("""
            QLineEdit {
                background: #000;
                color: #ff8800;
                border: 2px solid #ff6600;
                padding: 8px;
                border-radius: 3px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border: 2px solid #ff8800;
            }
        """)
        
        self.setup_command_autocomplete()
        
        exec_btn = QPushButton("Execute")
        exec_btn.clicked.connect(self.execute_global_command)
        exec_btn.setStyleSheet("""
            QPushButton {
                background: #ff6600;
                color: #000;
                border: none;
                padding: 8px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff8800;
            }
        """)
        
        cmd_layout.addWidget(cmd_label)
        cmd_layout.addWidget(self.global_command_input)
        cmd_layout.addWidget(exec_btn)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(OverviewTab(), "📊 OVERVIEW")
        self.tabs.addTab(BacktestTab(), "📈 BACKTEST")
        self.tabs.addTab(OptionsTab(), "📉 OPTIONS")
        self.tabs.addTab(PortfolioTab(), "💼 PORTFOLIO")
        
        layout.addWidget(title_bar)
        layout.addWidget(command_bar)
        layout.addWidget(self.tabs)
        
        central.setLayout(layout)
    
    def setup_command_autocomplete(self):
        self.base_commands = [
            "HELP - Show command reference",
            "OV - Overview tab", 
            "OVERVIEW - Overview tab",
            "BT - Backtest tab", 
            "BACKTEST - Backtest tab",
            "OP - Options tab", 
            "OPTIONS - Options tab",
            "PF - Portfolio tab", 
            "PORTFOLIO - Portfolio tab",
            "MARKET - Market data", 
            "INFO - Company info", 
            "FIN - Financials", 
            "FINANCIALS - Financial statements",
            "RUN - Run backtest", 
            "RUNBT - Run backtest",
            "MANAGER - Strategy manager", 
            "STRATMGR - Strategy manager",
            "EDITOR - Strategy editor", 
            "STRATEDIT - Strategy editor",
            "CHAIN - Options chain", 
            "OPTCHAIN - Options chain",
            "VOL - Volatility surface", 
            "VOLSURFACE - Volatility surface",
            "STRATEGY - Options strategy", 
            "GREEKS - Options Greeks",
            "PORT - Portfolio tab",
            "PORTFOLIO - Portfolio tab",
        ]
        
        self.completer = QCompleter(self.base_commands)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setMaxVisibleItems(15)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        
        popup = self.completer.popup()
        popup.setStyleSheet("""
            QListView {
                background-color: #000000;
                border: 2px solid #ff6600;
                border-radius: 5px;
                outline: none;
                color: #ff8800;
                font-family: Consolas;
                font-size: 10pt;
                selection-background-color: #ff6600;
                selection-color: #000000;
            }
            QListView::item {
                padding: 10px 15px;
                border-bottom: 1px solid #1a1a1a;
            }
            QListView::item:hover {
                background-color: #1a1a1a;
            }
            QListView::item:selected {
                background-color: #ff6600;
                color: #000000;
                font-weight: bold;
            }
            QScrollBar:vertical {
                background: #0a0a0a;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #ff6600;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff8800;
            }
        """)
        
        self.global_command_input.setCompleter(self.completer)
        self.global_command_input.textChanged.connect(self.update_command_suggestions)
    
    def update_command_suggestions(self, text):
        if not text:
            self.completer.popup().hide()
            return
        
        parts = text.strip().upper().split()
        
        if len(parts) == 1:
            word = parts[0]
            exact_matches = [cmd for cmd in self.base_commands if cmd.upper().startswith(word + " -")]
            
            if not any(word == cmd.split(" -")[0].upper() for cmd in self.base_commands):
                if len(word) >= 1:
                    enhanced_suggestions = [
                        f"{word} - Load in Overview tab",
                        f"{word} MARKET - View market data & chart",
                        f"{word} INFO - Show company information", 
                        f"{word} FIN - Display financial statements",
                        f"{word} BT - Open in Backtest tab",
                        f"{word} BT RUN - Run backtest immediately",
                        f"{word} OP - Open in Options tab",
                        f"{word} OP CHAIN - View options chain",
                        f"{word} OP VOL - Show volatility surface",
                        f"{word} PORT - Add to Portfolio comparison",
                    ]
                    self.completer.model().setStringList(enhanced_suggestions)
                else:
                    self.completer.model().setStringList(self.base_commands)
            else:
                self.completer.model().setStringList(self.base_commands)
        
        elif len(parts) == 2:
            symbol = parts[0]
            keyword = parts[1]
            
            if keyword in ["BT", "BACKTEST"]:
                enhanced_suggestions = [
                    f"{symbol} BT - Open in Backtest tab",
                    f"{symbol} BT RUN - Run backtest immediately",
                    f"{symbol} BT MANAGER - Open strategy manager",
                    f"{symbol} BT EDITOR - Open strategy editor",
                ]
                self.completer.model().setStringList(enhanced_suggestions)
            elif keyword in ["OP", "OPTIONS"]:
                enhanced_suggestions = [
                    f"{symbol} OP - Open in Options tab",
                    f"{symbol} OP CHAIN - View options chain",
                    f"{symbol} OP VOL - Show volatility surface",
                    f"{symbol} OP STRATEGY - Build options strategy",
                    f"{symbol} OP GREEKS - Monitor Greeks values",
                ]
                self.completer.model().setStringList(enhanced_suggestions)
            elif keyword in ["OV", "OVERVIEW", "MARKET", "INFO", "FIN", "FINANCIALS"]:
                enhanced_suggestions = [
                    f"{symbol} - Load in Overview tab",
                    f"{symbol} MARKET - View market data & chart",
                    f"{symbol} INFO - Show company information",
                    f"{symbol} FIN - Display financial statements",
                ]
                self.completer.model().setStringList(enhanced_suggestions)
            else:
                self.completer.model().setStringList(self.base_commands)
        else:
            self.completer.model().setStringList(self.base_commands)
    
    def execute_global_command(self):
        try:
            cmd = self.global_command_input.text().strip()
            
            if " - " in cmd:
                cmd = cmd.split(" - ")[0].strip()
            
            if not cmd:
                return
            
            cmd = cmd.upper()
            parts = cmd.split()
            
            main_tab_map = {
                "OV": 0, "OVERVIEW": 0,
                "BT": 1, "BACKTEST": 1,
                "OP": 2, "OPTIONS": 2,
                "PF": 3, "PORTFOLIO": 3, "PORT": 3
            }
            
            overview_subtab_map = {
                "MARKET": 0,
                "INFO": 1,
                "FIN": 2, "FINANCIALS": 2
            }
            
            backtest_subtab_map = {
                "RUN": 0, "RUNBT": 0,
                "MANAGER": 1, "STRATMGR": 1,
                "EDITOR": 2, "STRATEDIT": 2
            }
            
            options_subtab_map = {
                "CHAIN": 0, "OPTCHAIN": 0,
                "VOL": 1, "VOLSURFACE": 1,
                "STRATEGY": 2, "STRAT": 2,
                "GREEKS": 3
            }
            
            if cmd == "HELP":
                self.show_help()
                self.global_command_input.clear()
                return
            
            if len(parts) == 1:
                keyword = parts[0]
                
                if keyword in main_tab_map:
                    self.tabs.setCurrentIndex(main_tab_map[keyword])
                    self.global_command_input.clear()
                    print(f"[App] Navigated to main tab {main_tab_map[keyword]}")
                    return
                
                if keyword in overview_subtab_map:
                    self.navigate_to_subtab(0, overview_subtab_map[keyword])
                    self.global_command_input.clear()
                    return
                    
                if keyword in backtest_subtab_map:
                    self.navigate_to_subtab(1, backtest_subtab_map[keyword])
                    self.global_command_input.clear()
                    return
                    
                if keyword in options_subtab_map:
                    self.navigate_to_subtab(2, options_subtab_map[keyword])
                    self.global_command_input.clear()
                    return
                    
                self.load_symbol_in_overview(keyword, subtab_index=0)
                self.global_command_input.clear()
                return
            
            if len(parts) == 2:
                word1, word2 = parts[0], parts[1]
                
                if word2 in overview_subtab_map:
                    self.load_symbol_in_overview(word1, subtab_index=overview_subtab_map[word2])
                    self.global_command_input.clear()
                    return
                
                if word1 in main_tab_map:
                    tab_idx = main_tab_map[word1]
                    
                    if tab_idx == 0 and word2 in overview_subtab_map:
                        self.navigate_to_subtab(0, overview_subtab_map[word2])
                    elif tab_idx == 1 and word2 in backtest_subtab_map:
                        self.navigate_to_subtab(1, backtest_subtab_map[word2])
                    elif tab_idx == 2 and word2 in options_subtab_map:
                        self.navigate_to_subtab(2, options_subtab_map[word2])
                    else:
                        self.tabs.setCurrentIndex(tab_idx)
                    
                    self.global_command_input.clear()
                    return
                
                if word2 in main_tab_map:
                    tab_idx = main_tab_map[word2]
                    self.tabs.setCurrentIndex(tab_idx)
                    
                    if tab_idx == 0:
                        self.load_symbol_in_overview(word1, subtab_index=0)
                    elif tab_idx == 1:
                        self.load_symbol_in_backtest(word1)
                    elif tab_idx == 2:
                        self.load_symbol_in_options(word1)
                    elif tab_idx == 3:
                        self.load_symbol_in_portfolio(word1)
                    
                    self.global_command_input.clear()
                    return
                
                print(f"[App] Unrecognized 2-word command: {cmd}")
                self.global_command_input.clear()
                return
            
            if len(parts) == 3:
                word1, word2, word3 = parts[0], parts[1], parts[2]
                
                if word2 in main_tab_map:
                    tab_idx = main_tab_map[word2]
                    
                    if tab_idx == 0 and word3 in overview_subtab_map:
                        self.load_symbol_in_overview(word1, subtab_index=overview_subtab_map[word3])
                    elif tab_idx == 1 and word3 in backtest_subtab_map:
                        self.tabs.setCurrentIndex(1)
                        self.navigate_to_subtab(1, backtest_subtab_map[word3])
                        self.load_symbol_in_backtest(word1)
                    elif tab_idx == 2 and word3 in options_subtab_map:
                        self.tabs.setCurrentIndex(2)
                        self.navigate_to_subtab(2, options_subtab_map[word3])
                        self.load_symbol_in_options(word1)
                    else:
                        self.tabs.setCurrentIndex(tab_idx)
                    
                    self.global_command_input.clear()
                    return
                
                print(f"[App] Unrecognized 3-word command: {cmd}")
                self.global_command_input.clear()
                return
            
            print(f"[App] Invalid command format (too many words): {cmd}")
            self.global_command_input.clear()
            
        except Exception as e:
            print(f"[App] Error executing command: {e}")
            import traceback
            traceback.print_exc()
            self.global_command_input.clear()
    
    def navigate_to_subtab(self, tab_index: int, subtab_index: int):
        try:
            self.tabs.setCurrentIndex(tab_index)
            
            tab_widget = self.tabs.widget(tab_index)
            subtab_attr_names = ['sub_tabs', 'tabs']
            
            for attr_name in subtab_attr_names:
                if hasattr(tab_widget, attr_name):
                    subtabs = getattr(tab_widget, attr_name)
                    if subtabs and subtab_index < subtabs.count():
                        subtabs.setCurrentIndex(subtab_index)
                        print(f"[App] Navigated to tab {tab_index}, sub-tab {subtab_index}")
                        return
            
            print(f"[App] Tab {tab_index} has no sub-tabs or invalid sub-tab index {subtab_index}")
            
        except Exception as e:
            print(f"[App] Error navigating to sub-tab: {e}")
    
    def load_symbol_in_overview(self, symbol: str, subtab_index: int = 0):
        try:
            self.tabs.setCurrentIndex(0)
            
            overview_tab = self.tabs.widget(0)
            
            if hasattr(overview_tab, 'sub_tabs'):
                overview_tab.sub_tabs.setCurrentIndex(subtab_index)
                print(f"[App] Switched to Overview sub-tab {subtab_index}")
            
            if hasattr(overview_tab, 'sync_all_panels'):
                overview_tab.sync_all_panels(symbol)
                print(f"[App] Loading symbol {symbol} in Overview")
            else:
                print(f"[App] Overview tab doesn't have sync_all_panels method")
                
        except Exception as e:
            print(f"[App] Error loading symbol in overview: {e}")
            overview_tab = self.tabs.widget(0)
            if hasattr(overview_tab, 'log_formatted'):
                overview_tab.log_formatted(f"Error loading {symbol}: {str(e)}", "error")
    
    def load_symbol_in_backtest(self, symbol: str):
        try:
            self.tabs.setCurrentIndex(1)
            
            backtest_tab = self.tabs.widget(1)
            
            if hasattr(backtest_tab, 'symbol_input'):
                backtest_tab.symbol_input.setText(symbol)
                print(f"[App] Set symbol {symbol} in Backtest tab")
            else:
                print(f"[App] Backtest tab doesn't have symbol_input")
                
        except Exception as e:
            print(f"[App] Error loading symbol in backtest: {e}")
    
    def load_symbol_in_options(self, symbol: str):
        try:
            self.tabs.setCurrentIndex(2)
            
            options_tab = self.tabs.widget(2)
            
            if hasattr(options_tab, 'underlying_input'):
                options_tab.underlying_input.setText(symbol)
                print(f"[App] Set symbol {symbol} in Options tab")
                
                if hasattr(options_tab, 'on_underlying_changed'):
                    QTimer.singleShot(100, options_tab.on_underlying_changed)
                    print(f"[App] Triggered underlying change for {symbol}")
            else:
                print(f"[App] Options tab doesn't have underlying_input")
                
        except Exception as e:
            print(f"[App] Error loading symbol in options: {e}")
    
    def load_symbol_in_portfolio(self, symbol: str):
        try:
            self.tabs.setCurrentIndex(3)
            
            portfolio_tab = self.tabs.widget(3)
            
            if hasattr(portfolio_tab, 'symbol_input'):
                portfolio_tab.symbol_input.setText(symbol)
                print(f"[App] Set symbol {symbol} in Portfolio tab")
            else:
                print(f"[App] Portfolio tab doesn't have symbol_input")
                
        except Exception as e:
            print(f"[App] Error loading symbol in portfolio: {e}")
    
    def show_help(self):
        help_text = """
TERMINAL TRADE - Complete Command Reference

═══════════════════════════════════════════════════════════

📁 MAIN TAB NAVIGATION:
  OV / OVERVIEW   - Overview Tab (Market Data & Analysis)
  BT / BACKTEST   - Backtest Tab (Strategy Testing)
  OP / OPTIONS    - Options Tab (Options Trading)
  PF / PORTFOLIO  - Portfolio Tab (Portfolio Management)
  PORT / PORTFOLIO - Portfolio Tab (Portfolio Management)
  HELP            - Show this help

═══════════════════════════════════════════════════════════

📊 OVERVIEW SUB-TABS:
  MARKET          - Market Data with TradingView
  INFO            - Company Information
  FIN/FINANCIALS  - Financial Statements

═══════════════════════════════════════════════════════════

📈 BACKTEST SUB-TABS:
  RUN / RUNBT     - Run Backtest
  MANAGER         - Strategy Manager
  EDITOR          - Strategy Editor

═══════════════════════════════════════════════════════════

📉 OPTIONS SUB-TABS:
  CHAIN           - Options Chain
  VOL             - Volatility Analytics
  STRATEGY        - Strategy & Pricing
  GREEKS          - Greeks Monitor

═══════════════════════════════════════════════════════════

🔤 COMMAND PATTERNS:

1️⃣ SYMBOL ONLY:
   [SYMBOL]                    → Load in Overview Market Data
   Example: BTC, AAPL, TSLA

2️⃣ SYMBOL + OVERVIEW SUBTAB:
   [SYMBOL] MARKET/INFO/FIN    → Load in specific Overview subtab
   Example: AAPL FIN, BTC INFO

2️⃣ SYMBOL + TAB:
   [SYMBOL] PORT               → Load in Portfolio tab
   Example: BTC PORT, AAPL PORT

3️⃣ TAB + SUBTAB:
   [TAB] [SUBTAB]              → Navigate to tab and subtab
   Example: BT RUN, OP CHAIN, OV FIN

4️⃣ SYMBOL + TAB + SUBTAB:
   [SYMBOL] [TAB] [SUBTAB]     → Load symbol in specific tab/subtab
   Example: BTC BT RUN, AAPL OP CHAIN

═══════════════════════════════════════════════════════════

💡 EXAMPLES:

Overview Commands:
  >> BTC                      → Bitcoin Market Data
  >> AAPL FIN                 → Apple Financials
  >> TSLA INFO                → Tesla Company Info
  >> MARKET                   → Switch to Market Data
  
Backtest Commands:
  >> BT RUN                   → Backtest Run tab
  >> BT MANAGER               → Strategy Manager
  >> AAPL BT RUN              → Load AAPL in Backtest
  
Options Commands:
  >> OP CHAIN                 → Options Chain
  >> BTC OP VOL               → Bitcoin Vol Surface
  >> OP GREEKS                → Greeks Monitor

Portfolio Commands:
  >> PORT                     → Portfolio tab
  >> PF                       → Portfolio tab
  >> BTC PORT                 → Load BTC in Portfolio
  >> AAPL PORT                → Load AAPL in Portfolio
  
Quick Navigation:
  >> OV                       → Overview tab
  >> BT                       → Backtest tab
  >> OP                       → Options tab
  >> PF                       → Portfolio tab

═══════════════════════════════════════════════════════════

💡 TIP: Start typing and dropdown suggestions will appear!
        """
        QMessageBox.information(self, "Command Reference", help_text)


def main():
    warnings.filterwarnings('ignore')
    os.environ['PYTHONWARNINGS'] = 'ignore'
    
    app = QApplication(sys.argv)
    window = TradingApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()