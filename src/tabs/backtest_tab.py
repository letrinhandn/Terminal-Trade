"""
BacktestTab - Extracted from terminal_trade_desktop.py
Full implementation for modular architecture
"""

import os
import io
import traceback
from datetime import datetime
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTextEdit, QTableWidget, QTableWidgetItem, QGroupBox,
    QTabWidget, QSplitter, QMessageBox, QHeaderView, QListWidget,
    QListWidgetItem, QCheckBox, QDateEdit
)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QFont, QColor, QPixmap
from PyQt6.QtWebEngineWidgets import QWebEngineView

from strategies.macd_strategy import MACDStrategy, RSIStrategy
from strategies.macd_advanced import MACDAdvancedStrategy, MACDConservative, MACDAggressive
from backtest.engine import BacktestEngine
from metrics.performance import PerformanceMetrics
from core.strategy_base import BaseStrategy
from data.data_loader import load_data

matplotlib.use('Agg')


class BacktestTab(QWidget):
    """Backtest tab - Full backtesting functionality with sub-tabs"""
    
    def __init__(self):
        super().__init__()
        self.backtest_results = None
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Title bar
        title_bar = QWidget()
        title_bar.setStyleSheet("background: #1a1a1a; border-bottom: 2px solid #ff6600;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 10, 15, 10)
        
        title = QLabel("🔬 BACKTESTING MODULE")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #ff6600; background: transparent;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        main_layout.addWidget(title_bar)
        
        # SUB-TABS
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
                color: #fff;
            }
        """)
        
        # Create sub-tabs
        self.run_tab = self.create_run_backtest_tab()
        self.manager_tab = self.create_strategy_manager_tab()
        self.editor_tab = self.create_strategy_editor_tab()
        
        self.sub_tabs.addTab(self.run_tab, "▶ Run Backtest")
        self.sub_tabs.addTab(self.manager_tab, "📋 Strategy Manager")
        self.sub_tabs.addTab(self.editor_tab, "💻 Strategy Editor")
        
        main_layout.addWidget(self.sub_tabs)
    
    def create_run_backtest_tab(self) -> QWidget:
        """Create the run backtest tab (original functionality)"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Splitter for parameters and results
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
    # LEFT PANEL: Parameters
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)
        
        params_group = QGroupBox("⚙️ BACKTEST PARAMETERS")
        params_layout = QVBoxLayout()
        params_layout.setSpacing(12)
        
        # Strategy selection
        strategy_label = QLabel("Strategy:")
        strategy_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "MACD Strategy",
            "MACD Advanced",
            "MACD Conservative",
            "MACD Aggressive",
            "RSI Strategy"
        ])
        self.strategy_combo.setToolTip("Select trading strategy to backtest")
        
        # Symbol input
        symbol_label = QLabel("Symbol:")
        symbol_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("BTC-USD, ETH-USD, AAPL, etc.")
        self.symbol_input.setText("BTC-USD")
        self.symbol_input.setToolTip("Enter ticker symbol")
        
        # Date range
        date_label = QLabel("Date Range:")
        date_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        date_layout = QHBoxLayout()
        self.start_date = QLineEdit()
        self.start_date.setPlaceholderText("YYYY-MM-DD")
        self.start_date.setText("2023-01-01")
        self.end_date = QLineEdit()
        self.end_date.setPlaceholderText("Latest")
        self.end_date.setText("")
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.end_date)
        
        # Capital
        capital_label = QLabel("Initial Capital ($):")
        capital_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.capital_input = QLineEdit()
        self.capital_input.setText("10000")
        self.capital_input.setPlaceholderText("10000")
        
        # Commission
        commission_label = QLabel("Commission (%):")
        commission_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.commission_input = QLineEdit()
        self.commission_input.setText("0.1")
        self.commission_input.setPlaceholderText("0.1")
        
        # Add to layout
        params_layout.addWidget(strategy_label)
        params_layout.addWidget(self.strategy_combo)
        params_layout.addWidget(symbol_label)
        params_layout.addWidget(self.symbol_input)
        params_layout.addWidget(date_label)
        params_layout.addLayout(date_layout)
        params_layout.addWidget(capital_label)
        params_layout.addWidget(self.capital_input)
        params_layout.addWidget(commission_label)
        params_layout.addWidget(self.commission_input)
        
        params_group.setLayout(params_layout)
        left_layout.addWidget(params_group)
        
        # Run button
        self.run_btn = QPushButton("▶ RUN BACKTEST")
        self.run_btn.clicked.connect(self.run_backtest)
        self.run_btn.setMinimumHeight(50)
        self.run_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: #00ff00;
                color: #000000;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #00cc00;
            }
            QPushButton:pressed {
                background: #009900;
            }
        """)
        left_layout.addWidget(self.run_btn)
        
        # Export button
        self.export_btn = QPushButton("💾 Export Results")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        left_layout.addWidget(self.export_btn)
        
        left_layout.addStretch()
        
    # RIGHT PANEL: Results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(5)
        
        results_group = QGroupBox("BACKTEST RESULTS")
        results_layout = QVBoxLayout()
        
        # Create horizontal splitter for table and charts
        results_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Results table
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(2)
        self.results_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.results_table.setAlternatingRowColors(True)
        
        # Auto-resize columns: Metric fits content, Value stretches to fill
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        table_layout.addWidget(self.results_table)
        
        # Right side: Charts
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        charts_layout.setContentsMargins(5, 0, 0, 0)
        
        # Equity curve chart
        equity_label = QLabel("� Equity Curve")
        equity_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        equity_label.setStyleSheet("color: #00aaff;")
        self.equity_chart = QLabel()
        self.equity_chart.setMinimumHeight(200)
        self.equity_chart.setStyleSheet("border: 1px solid #444; background: #1a1a1a; border-radius: 3px;")
        self.equity_chart.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.equity_chart.setText("Run backtest to see equity curve")
        
        # Drawdown chart
        dd_label = QLabel("📉 Drawdown")
        dd_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        dd_label.setStyleSheet("color: #ff6600;")
        self.drawdown_chart = QLabel()
        self.drawdown_chart.setMinimumHeight(150)
        self.drawdown_chart.setStyleSheet("border: 1px solid #444; background: #1a1a1a; border-radius: 3px;")
        self.drawdown_chart.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drawdown_chart.setText("Run backtest to see drawdown")
        
        # Trade distribution
        trades_label = QLabel("📊 Trade Distribution")
        trades_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        trades_label.setStyleSheet("color: #00ff00;")
        self.trades_chart = QLabel()
        self.trades_chart.setMinimumHeight(120)
        self.trades_chart.setStyleSheet("border: 1px solid #444; background: #1a1a1a; border-radius: 3px;")
        self.trades_chart.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.trades_chart.setText("Run backtest to see trades")
        
        charts_layout.addWidget(equity_label)
        charts_layout.addWidget(self.equity_chart, 2)
        charts_layout.addWidget(dd_label)
        charts_layout.addWidget(self.drawdown_chart, 1)
        charts_layout.addWidget(trades_label)
        charts_layout.addWidget(self.trades_chart, 1)
        
        # Add to splitter
        results_splitter.addWidget(table_widget)
        results_splitter.addWidget(charts_widget)
        results_splitter.setStretchFactor(0, 1)
        results_splitter.setStretchFactor(1, 1)
        
        results_layout.addWidget(results_splitter)
        
        # Log at bottom
        log_label = QLabel("📜 Backtest Log:")
        log_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setFont(QFont("Consolas", 9))
        
        results_layout.addWidget(log_label)
        results_layout.addWidget(self.log_text)
        
        results_group.setLayout(results_layout)
        right_layout.addWidget(results_group)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # Initial log
        self.log("Backtest module ready")
        self.log("Select parameters and click 'RUN BACKTEST'")
        
        return tab
    
    def create_strategy_manager_tab(self) -> QWidget:
        """Create strategy manager tab - list and manage strategies"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("📋 STRATEGY MANAGER")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #ff6600; padding: 10px;")
        layout.addWidget(header)
        
        # Description
        desc = QLabel("Manage your custom trading strategies. View, edit, delete, or create new strategies.")
        desc.setStyleSheet("color: #888; font-size: 10pt; padding: 5px;")
        layout.addWidget(desc)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.new_strategy_btn = QPushButton("➕ New Strategy")
        self.new_strategy_btn.setMinimumHeight(40)
        self.new_strategy_btn.setStyleSheet("""
            QPushButton {
                background: #00aa00;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover { background: #00cc00; }
            QPushButton:pressed { background: #008800; }
        """)
        self.new_strategy_btn.clicked.connect(self.create_new_strategy)
        
        self.refresh_strategies_btn = QPushButton("🔄 Refresh")
        self.refresh_strategies_btn.setMinimumHeight(40)
        self.refresh_strategies_btn.setStyleSheet("""
            QPushButton {
                background: #ff6600;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover { background: #ff8800; }
            QPushButton:pressed { background: #dd5500; }
        """)
        self.refresh_strategies_btn.clicked.connect(self.load_strategies)
        
        btn_layout.addWidget(self.new_strategy_btn)
        btn_layout.addWidget(self.refresh_strategies_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Strategy list table
        self.strategy_table = QTableWidget()
        self.strategy_table.setColumnCount(5)
        self.strategy_table.setHorizontalHeaderLabels([
            "Strategy Name", "Type", "Parameters", "Description", "Actions"
        ])
        
        # Set column widths for better layout
        self.strategy_table.setColumnWidth(0, 180)  # Strategy Name
        self.strategy_table.setColumnWidth(1, 90)   # Type
        self.strategy_table.setColumnWidth(2, 220)  # Parameters
        self.strategy_table.setColumnWidth(4, 350)  # Actions (wider for 3 buttons - INCREASED MORE)
        
        # Description column stretches to fill remaining space
        self.strategy_table.horizontalHeader().setStretchLastSection(False)
        self.strategy_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        # Set vertical header to fixed mode with enough height for buttons
        self.strategy_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.strategy_table.verticalHeader().setDefaultSectionSize(60)  # More space for buttons - INCREASED MORE 
        
        self.strategy_table.setAlternatingRowColors(True)
        self.strategy_table.setStyleSheet("""
            QTableWidget {
                background: #1a1a1a;
                color: white;
                gridline-color: #333;
                border: 1px solid #444;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 12px 8px;
            }
            QTableWidget::item:selected {
                background: #ff6600;
                color: black;
            }
            QHeaderView::section {
                background: #2a2a2a;
                color: #ff6600;
                padding: 10px 8px;
                border: 1px solid #444;
                font-weight: bold;
                font-size: 10pt;
            }
        """)
        
        layout.addWidget(self.strategy_table)
        
        # Load strategies
        self.load_strategies()
        
        return tab
    
    def create_strategy_editor_tab(self) -> QWidget:
        """Create strategy editor tab - code editor for strategies"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("💻 STRATEGY EDITOR")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #ff6600;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Template selector
        template_label = QLabel("Template:")
        template_label.setStyleSheet("color: #888; font-weight: bold;")
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "Blank Strategy",
            "MACD Template",
            "RSI Template",
            "Moving Average Crossover",
            "Bollinger Bands Strategy"
        ])
        self.template_combo.currentTextChanged.connect(self.load_template)
        
        # Strategy name input
        name_label = QLabel("Strategy Name:")
        name_label.setStyleSheet("color: #888; font-weight: bold;")
        self.strategy_name_input = QLineEdit()
        self.strategy_name_input.setPlaceholderText("my_custom_strategy")
        self.strategy_name_input.setMaximumWidth(300)
        
        toolbar.addWidget(template_label)
        toolbar.addWidget(self.template_combo)
        toolbar.addSpacing(20)
        toolbar.addWidget(name_label)
        toolbar.addWidget(self.strategy_name_input)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Code editor
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setStyleSheet("""
            QTextEdit {
                background: #0d0d0d;
                color: #f0f0f0;
                border: 2px solid #444;
                border-radius: 5px;
                padding: 10px;
                selection-background-color: #ff6600;
            }
        """)
        self.code_editor.setPlaceholderText("# Write your strategy code here...\n# Use Tab for indentation\n")
        
        layout.addWidget(self.code_editor, 1)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("✓ Validate Syntax")
        self.validate_btn.setMinimumHeight(40)
        self.validate_btn.setStyleSheet("""
            QPushButton {
                background: #0066cc;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover { background: #0088ff; }
        """)
        self.validate_btn.clicked.connect(self.validate_strategy)
        
        self.save_strategy_btn = QPushButton("💾 Save Strategy")
        self.save_strategy_btn.setMinimumHeight(40)
        self.save_strategy_btn.setStyleSheet("""
            QPushButton {
                background: #00aa00;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover { background: #00cc00; }
        """)
        self.save_strategy_btn.clicked.connect(self.save_strategy)
        
        self.test_strategy_btn = QPushButton("🧪 Quick Test")
        self.test_strategy_btn.setMinimumHeight(40)
        self.test_strategy_btn.setStyleSheet("""
            QPushButton {
                background: #ff6600;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover { background: #ff8800; }
        """)
        self.test_strategy_btn.clicked.connect(self.quick_test_strategy)
        
        action_layout.addWidget(self.validate_btn)
        action_layout.addWidget(self.save_strategy_btn)
        action_layout.addWidget(self.test_strategy_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # Output console
        console_label = QLabel("📋 Output Console:")
        console_label.setStyleSheet("color: #888; font-weight: bold;")
        layout.addWidget(console_label)
        
        self.editor_console = QTextEdit()
        self.editor_console.setReadOnly(True)
        self.editor_console.setMaximumHeight(120)
        self.editor_console.setFont(QFont("Consolas", 9))
        self.editor_console.setStyleSheet("""
            QTextEdit {
                background: #0d0d0d;
                color: #0f0;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.editor_console)
        
        # Load blank template initially
        self.load_template("Blank Strategy")
        
        return tab
    
    def log(self, message: str, level: str = "info"):
        """Log message to console"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if level == "error":
            color = "red"
            icon = "✗"
        elif level == "success":
            color = "green"
            icon = "✓"
        elif level == "warning":
            color = "orange"
            icon = "⚠"
        else:
            color = "#00aaff"
            icon = "•"
        
        html = f'<span style="color: #666;">[{timestamp}]</span> <span style="color: {color}; font-weight: bold;">{icon}</span> <span style="color: {color};">{message}</span>'
        self.log_text.append(html)
        
        # Auto-scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def run_backtest(self):
        """Run backtest with selected parameters"""
        self.log("Starting backtest...", "info")
        self.run_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        try:
            # Import required modules
            
            # Get parameters
            symbol = self.symbol_input.text().strip().upper()
            start_date = self.start_date.text().strip()
            end_date = self.end_date.text().strip() or None
            
            try:
                capital = float(self.capital_input.text().strip())
            except ValueError:
                self.log("Invalid capital amount", "error")
                self.run_btn.setEnabled(True)
                return
            
            try:
                commission = float(self.commission_input.text().strip()) / 100
            except ValueError:
                self.log("Invalid commission rate", "error")
                self.run_btn.setEnabled(True)
                return
            
            if not symbol or not start_date:
                self.log("Please enter symbol and start date", "error")
                self.run_btn.setEnabled(True)
                return
            
            # Select strategy
            strategy_name = self.strategy_combo.currentText()
            self.log(f"Strategy: {strategy_name}", "info")
            
            if strategy_name == "MACD Strategy":
                strategy = MACDStrategy()
            elif strategy_name == "MACD Advanced":
                strategy = MACDAdvancedStrategy()
            elif strategy_name == "MACD Conservative":
                strategy = MACDConservative()
            elif strategy_name == "MACD Aggressive":
                strategy = MACDAggressive()
            elif strategy_name == "RSI Strategy":
                strategy = RSIStrategy()
            else:
                strategy = MACDStrategy()
            
            # Load data
            self.log(f"Loading data for {symbol}...", "info")
            df = load_data(symbol, start_date, end_date, source='yahoo')
            
            if df is None or df.empty:
                self.log(f"No data available for {symbol}", "error")
                self.run_btn.setEnabled(True)
                return
            
            # This prevents stale signals from previous backtests
            cols_to_drop = [col for col in df.columns if col not in ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']]
            if cols_to_drop:
                df = df.drop(columns=cols_to_drop)
                self.log(f"Cleared {len(cols_to_drop)} cached indicator columns", "info")
            
            # AGGRESSIVE COPY: Force deep copy to avoid any reference issues
            df = df.copy(deep=True)
            
            self.log(f"Loaded {len(df)} bars from {df.index[0].date()} to {df.index[-1].date()}", "success")
            
            # Run strategy
            self.log("Calculating indicators...", "info")
            df = strategy.run(df)
            
            # Verify signals were generated
            if 'Signal' in df.columns:
                num_buy = (df['Signal'] == 1).sum()
                num_sell = (df['Signal'] == -1).sum()
                self.log(f"Generated {num_buy} BUY and {num_sell} SELL signals", "info")
            
            # Run backtest
            self.log("Running backtest...", "info")
            engine = BacktestEngine(initial_capital=capital, commission=commission)
            backtest_results = engine.run(df)
            
            # Calculate metrics
            self.log("Calculating performance metrics...", "info")
            metrics_calc = PerformanceMetrics()
            metrics = metrics_calc.calculate_all_metrics(
                backtest_results,
                backtest_results['equity_curve']
            )
            
            # Store results
            self.backtest_results = {
                'metrics': metrics,
                'backtest': backtest_results,
                'symbol': symbol,
                'strategy': strategy_name,
                'df': df
            }
            
            # Display results
            self.display_results(metrics, backtest_results)
            
            self.log(f"Backtest completed successfully!", "success")
            self.log(f"Total Return: {metrics['total_return']:.2f}%", "success")
            self.export_btn.setEnabled(True)
            
        except Exception as e:
            self.log(f"Error: {str(e)}", "error")
        
        finally:
            self.run_btn.setEnabled(True)
    
    def display_results(self, metrics: dict, backtest_results: dict):
        """Display backtest results in table"""
        results = [
            ("📈 PERFORMANCE", ""),
            ("Total Return", f"{metrics['total_return']:.2f}%"),
            ("Final Capital", f"${backtest_results['final_capital']:,.2f}"),
            ("Max Drawdown", f"{metrics['max_drawdown']:.2f}%"),
            ("", ""),
            ("📊 RISK METRICS", ""),
            ("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}"),
            ("Sortino Ratio", f"{metrics['sortino_ratio']:.2f}"),
            ("Calmar Ratio", f"{metrics['calmar_ratio']:.2f}"),
            ("Volatility", f"{metrics['volatility']:.2f}%"),
            ("", ""),
            ("💼 TRADE STATISTICS", ""),
            ("Total Trades", f"{metrics['num_trades']}"),
            ("Win Rate", f"{metrics['win_rate']:.2f}%"),
            ("Winning Trades", f"{backtest_results.get('num_winning', 0)}"),
            ("Losing Trades", f"{backtest_results.get('num_losing', 0)}"),
            ("Avg Win", f"{metrics['avg_win']:.2f}%"),
            ("Avg Loss", f"{metrics['avg_loss']:.2f}%"),
            ("Profit Factor", f"{metrics['profit_factor']:.2f}"),
            ("", ""),
            ("📅 TRADE DURATION", ""),
            ("Avg Holding Period", f"{metrics['avg_holding_period']:.1f} days"),
        ]
        
        self.results_table.setRowCount(len(results))
        
        for i, (metric, value) in enumerate(results):
            metric_item = QTableWidgetItem(metric)
            value_item = QTableWidgetItem(value)
            
            # Bold headers
            if value == "":
                font = QFont("Arial", 10, QFont.Weight.Bold)
                metric_item.setFont(font)
                metric_item.setForeground(QColor("#ff6600"))
            
            # Color code values
            if "Return" in metric and value:
                try:
                    val = float(value.replace('%', '').replace('$', '').replace(',', ''))
                    if val > 0:
                        value_item.setForeground(QColor("#00ff00"))
                    elif val < 0:
                        value_item.setForeground(QColor("#ff0000"))
                except:
                    pass
            
            self.results_table.setItem(i, 0, metric_item)
            self.results_table.setItem(i, 1, value_item)
        
        # Don't resize - keep fixed widths
        # Generate and display charts
        self.generate_charts(metrics, backtest_results)
    
    def generate_charts(self, metrics: dict, backtest_results: dict):
        """Generate visualization charts"""
        try:
            # 1. Equity Curve Chart
            equity_curve = backtest_results['equity_curve']
            initial_capital = equity_curve[0] if len(equity_curve) > 0 else 10000
            
            fig, ax = plt.subplots(figsize=(6, 3), facecolor='#1a1a1a')
            ax.set_facecolor('#1a1a1a')
            
            dates = range(len(equity_curve))
            ax.plot(dates, equity_curve, color='#00ff00', linewidth=2, label='Equity')
            ax.axhline(y=initial_capital, color='#666', 
                      linestyle='--', linewidth=1, label='Initial')
            
            ax.set_title('Equity Curve', color='#00aaff', fontsize=10, pad=10)
            ax.set_xlabel('Time', color='#888', fontsize=8)
            ax.set_ylabel('Capital ($)', color='#888', fontsize=8)
            ax.tick_params(colors='#666', labelsize=7)
            ax.legend(loc='upper left', fontsize=7, facecolor='#2a2a2a', edgecolor='#444')
            ax.grid(True, alpha=0.2, color='#444')
            
            for spine in ax.spines.values():
                spine.set_color('#444')
            
            plt.tight_layout()
            
            # Convert to pixmap
            buf = io.BytesIO()
            plt.savefig(buf, format='png', facecolor='#1a1a1a', dpi=100)
            buf.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.read())
            self.equity_chart.setPixmap(pixmap.scaled(
                self.equity_chart.size(), 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            plt.close()
            
            # 2. Drawdown Chart
            drawdown = [(1 - equity / max(equity_curve[:i+1])) * 100 
                       for i, equity in enumerate(equity_curve)]
            
            fig, ax = plt.subplots(figsize=(6, 2.5), facecolor='#1a1a1a')
            ax.set_facecolor('#1a1a1a')
            
            ax.fill_between(dates, drawdown, 0, color='#ff3333', alpha=0.5)
            ax.plot(dates, drawdown, color='#ff0000', linewidth=1.5)
            
            ax.set_title('Drawdown (%)', color='#ff6600', fontsize=10, pad=10)
            ax.set_xlabel('Time', color='#888', fontsize=8)
            ax.set_ylabel('Drawdown (%)', color='#888', fontsize=8)
            ax.tick_params(colors='#666', labelsize=7)
            ax.grid(True, alpha=0.2, color='#444')
            ax.invert_yaxis()
            
            for spine in ax.spines.values():
                spine.set_color('#444')
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', facecolor='#1a1a1a', dpi=100)
            buf.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.read())
            self.drawdown_chart.setPixmap(pixmap.scaled(
                self.drawdown_chart.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            plt.close()
            
            # 3. Trade Distribution (Win/Loss bar chart)
            winning = backtest_results.get('num_winning', 0)
            losing = backtest_results.get('num_losing', 0)
            
            fig, ax = plt.subplots(figsize=(6, 2), facecolor='#1a1a1a')
            ax.set_facecolor('#1a1a1a')
            
            categories = ['Winning', 'Losing']
            values = [winning, losing]
            colors = ['#00ff00', '#ff0000']
            
            bars = ax.bar(categories, values, color=colors, alpha=0.7, width=0.6)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(value)}',
                       ha='center', va='bottom', color='#fff', fontsize=9, fontweight='bold')
            
            ax.set_title(f'Trade Distribution (Win Rate: {metrics["win_rate"]:.1f}%)', 
                        color='#00ff00', fontsize=10, pad=10)
            ax.set_ylabel('Count', color='#888', fontsize=8)
            ax.tick_params(colors='#666', labelsize=8)
            ax.grid(True, axis='y', alpha=0.2, color='#444')
            
            for spine in ax.spines.values():
                spine.set_color('#444')
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', facecolor='#1a1a1a', dpi=100)
            buf.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.read())
            self.trades_chart.setPixmap(pixmap.scaled(
                self.trades_chart.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            plt.close()
            
            self.log("Charts generated successfully", "success")
            
        except Exception as e:
            self.log(f"Error generating charts: {str(e)}", "warning")
    
    def export_results(self):
        """Export backtest results to CSV"""
        if not self.backtest_results:
            return
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backtest_{self.backtest_results['symbol']}_{timestamp}.csv"
            
            # Create results dataframe
            metrics = self.backtest_results['metrics']
            data = {
                'Metric': list(metrics.keys()),
                'Value': list(metrics.values())
            }
            
            df_results = pd.DataFrame(data)
            df_results.to_csv(filename, index=False)
            
            self.log(f"Results exported to {filename}", "success")
            
            # Show message box
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Export Successful")
            msg.setText(f"Results exported to:\n{filename}")
            msg.exec()
            
        except Exception as e:
            self.log(f"Export failed: {str(e)}", "error")
    
    # ========================================================================
    # STRATEGY MANAGER METHODS
    # ========================================================================
    
    def load_strategies(self):
        """Load and display available strategies"""
        self.strategy_table.setRowCount(0)
        
        # Built-in strategies
        strategies = [
            {
                'name': 'MACD Strategy',
                'type': 'Built-in',
                'params': 'fast=12, slow=26, signal=9',
                'description': 'Classic MACD crossover strategy'
            },
            {
                'name': 'MACD Advanced',
                'type': 'Built-in',
                'params': 'fast=8, slow=21, signal=5',
                'description': 'Advanced MACD with optimized parameters'
            },
            {
                'name': 'MACD Conservative',
                'type': 'Built-in',
                'params': 'fast=12, slow=26, signal=9, trend filter',
                'description': 'Conservative MACD with trend confirmation'
            },
            {
                'name': 'MACD Aggressive',
                'type': 'Built-in',
                'params': 'fast=6, slow=19, signal=9',
                'description': 'Aggressive MACD for faster signals'
            },
            {
                'name': 'RSI Strategy',
                'type': 'Built-in',
                'params': 'period=14, oversold=30, overbought=70',
                'description': 'RSI overbought/oversold strategy'
            }
        ]
        
        # Load custom strategies from strategies folder
        strategies_dir = Path("strategies")
        if strategies_dir.exists():
            for file in strategies_dir.glob("*.py"):
                if file.name not in ['__init__.py', 'macd_strategy.py', 'macd_advanced.py', 'options_strategies.py']:
                    strategies.append({
                        'name': file.stem,
                        'type': 'Custom',
                        'params': 'User defined',
                        'description': f'Custom strategy from {file.name}'
                    })
        
        # Populate table
        for strategy in strategies:
            row = self.strategy_table.rowCount()
            self.strategy_table.insertRow(row)
            
            self.strategy_table.setItem(row, 0, QTableWidgetItem(strategy['name']))
            self.strategy_table.setItem(row, 1, QTableWidgetItem(strategy['type']))
            self.strategy_table.setItem(row, 2, QTableWidgetItem(strategy['params']))
            self.strategy_table.setItem(row, 3, QTableWidgetItem(strategy['description']))
            
            # Action buttons
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(8, 6, 8, 6)
            btn_layout.setSpacing(10)
            
            if strategy['type'] == 'Custom':
                # Edit button
                edit_btn = QPushButton("✏️ Edit")
                edit_btn.setFixedSize(75, 32)
                edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background: #0066cc;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 9pt;
                    }
                    QPushButton:hover { 
                        background: #0088ff;
                        border: 1px solid #00aaff;
                    }
                    QPushButton:pressed { background: #004499; }
                """)
                edit_btn.clicked.connect(lambda checked, name=strategy['name']: self.edit_strategy(name))
                
                # View button
                view_btn = QPushButton("👁️ View")
                view_btn.setFixedSize(75, 32)
                view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                view_btn.setStyleSheet("""
                    QPushButton {
                        background: #555;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 9pt;
                    }
                    QPushButton:hover { 
                        background: #777;
                        border: 1px solid #999;
                    }
                    QPushButton:pressed { background: #333; }
                """)
                view_btn.clicked.connect(lambda checked, name=strategy['name']: self.view_custom_strategy(name))
                
                # Remove button
                remove_btn = QPushButton("🗑️ Del")
                remove_btn.setFixedSize(75, 32)
                remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                remove_btn.setStyleSheet("""
                    QPushButton {
                        background: #cc0000;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 9pt;
                    }
                    QPushButton:hover { 
                        background: #ff0000;
                        border: 1px solid #ff3333;
                    }
                    QPushButton:pressed { background: #990000; }
                """)
                remove_btn.clicked.connect(lambda checked, name=strategy['name']: self.remove_strategy(name))
                
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(view_btn)
                btn_layout.addWidget(remove_btn)
            else:
                # Built-in: View button
                view_btn = QPushButton("👁️ View")
                view_btn.setFixedSize(75, 32)
                view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                view_btn.setStyleSheet("""
                    QPushButton {
                        background: #555;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 9pt;
                    }
                    QPushButton:hover { 
                        background: #777;
                        border: 1px solid #999;
                    }
                    QPushButton:pressed { background: #333; }
                """)
                view_btn.clicked.connect(lambda checked, name=strategy['name']: self.view_builtin_strategy(name))
                
                # Remove from list button
                remove_btn = QPushButton("❌ Remove")
                remove_btn.setFixedSize(95, 32)
                remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                remove_btn.setStyleSheet("""
                    QPushButton {
                        background: #aa6600;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 9pt;
                    }
                    QPushButton:hover { 
                        background: #cc7700;
                        border: 1px solid #ff8800;
                    }
                    QPushButton:pressed { background: #884400; }
                """)
                remove_btn.clicked.connect(lambda checked, name=strategy['name']: self.remove_from_dropdown(name))
                
                btn_layout.addWidget(view_btn)
                btn_layout.addWidget(remove_btn)
            
            btn_layout.addStretch()
            self.strategy_table.setCellWidget(row, 4, btn_widget)
    
    def create_new_strategy(self):
        """Switch to editor tab with blank template"""
        self.sub_tabs.setCurrentIndex(2)  # Switch to editor tab
        self.template_combo.setCurrentText("Blank Strategy")
        self.strategy_name_input.clear()
        self.editor_console.clear()
        self.editor_log("Ready to create new strategy", "info")
    
    def edit_strategy(self, name: str):
        """Load strategy for editing"""
        file_path = Path("strategies") / f"{name}.py"
        
        if file_path.exists():
            with open(file_path, 'r') as f:
                code = f.read()
            
            self.sub_tabs.setCurrentIndex(2)  # Switch to editor
            self.code_editor.setText(code)
            self.strategy_name_input.setText(name)
            self.editor_log(f"Loaded {name} for editing", "success")
        else:
            self.editor_log(f"Strategy file not found: {name}", "error")
    
    def view_custom_strategy(self, name: str):
        """View custom strategy code"""
        file_path = Path("strategies") / f"{name}.py"
        
        if file_path.exists():
            with open(file_path, 'r') as f:
                code = f.read()
            
            # Show in dialog
            dialog = QMessageBox(self)
            dialog.setWindowTitle(f"View {name}")
            dialog.setText(f"Custom strategy source code:\n")
            dialog.setDetailedText(code)
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            dialog.exec()
        else:
            self.editor_log(f"Strategy file not found: {name}", "error")
    
    def remove_strategy(self, name: str):
        """Remove (delete) custom strategy permanently"""
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            'Confirm Deletion',
            f'Are you sure you want to permanently DELETE "{name}"?\n\nThis will:\n• Delete the .py file from disk\n• Remove from dropdown\n• Cannot be undone\n\nContinue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            file_path = Path("strategies") / f"{name}.py"
            if file_path.exists():
                try:
                    file_path.unlink()
                    self.load_strategies()  # Refresh list
                    self.editor_log(f"✓ Permanently deleted: {name}", "success")
                    
                    # Remove from Run Backtest dropdown if present
                    for i in range(self.strategy_combo.count()):
                        if self.strategy_combo.itemText(i) == name:
                            self.strategy_combo.removeItem(i)
                            break
                except Exception as e:
                    self.editor_log(f"Failed to delete: {str(e)}", "error")
    
    def remove_from_dropdown(self, name: str):
        """Remove built-in strategy from dropdown (not delete file)"""
        reply = QMessageBox.question(
            self,
            'Remove from Dropdown',
            f'Remove "{name}" from the Run Backtest dropdown?\n\n(The strategy code will remain, you can re-add it later)',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from dropdown
            for i in range(self.strategy_combo.count()):
                if self.strategy_combo.itemText(i) == name:
                    self.strategy_combo.removeItem(i)
                    self.editor_log(f"Removed {name} from dropdown", "success")
                    
                    # Show info
                    QMessageBox.information(
                        self,
                        "Removed",
                        f"{name} has been removed from the dropdown.\n\nTo re-add it, you'll need to manually add it back to the strategy list."
                    )
                    break
    
    def view_builtin_strategy(self, name: str):
        """View built-in strategy code (read-only)"""
        
        # Map strategy names to files
        file_map = {
            'MACD Strategy': 'macd_strategy.py',
            'MACD Advanced': 'macd_advanced.py',
            'MACD Conservative': 'macd_advanced.py',
            'MACD Aggressive': 'macd_advanced.py',
            'RSI Strategy': 'macd_strategy.py'
        }
        
        filename = file_map.get(name)
        if filename:
            file_path = Path("strategies") / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    code = f.read()
                
                # Show in dialog
                dialog = QMessageBox(self)
                dialog.setWindowTitle(f"View {name}")
                dialog.setText(f"Built-in strategy source code (read-only):\n\n")
                dialog.setDetailedText(code)
                dialog.exec()
    
    # ========================================================================
    # STRATEGY EDITOR METHODS
    # ========================================================================
    
    def editor_log(self, message: str, level: str = "info"):
        """Log to editor console"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if level == "error":
            color = "#ff0000"
            icon = "✗"
        elif level == "success":
            color = "#00ff00"
            icon = "✓"
        elif level == "warning":
            color = "#ffaa00"
            icon = "⚠"
        else:
            color = "#00aaff"
            icon = "•"
        
        html = f'<span style="color: #666;">[{timestamp}]</span> <span style="color: {color};">{icon} {message}</span>'
        self.editor_console.append(html)
    
    def load_template(self, template_name: str):
        """Load strategy template"""
        templates = {
            "Blank Strategy": '''"""
Custom Trading Strategy
"""



class MyStrategy(BaseStrategy):
    """
    My custom trading strategy
    """
    
    def __init__(self, param1: int = 10, param2: int = 20):
        params = {
            'param1': param1,
            'param2': param2
        }
        super().__init__(name="MyStrategy", params=params)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        df = df.copy()
        
        # Add your indicator calculations here
        # Example: df['SMA'] = df['Close'].rolling(window=20).mean()
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals"""
        df = df.copy()
        df['Signal'] = 0
        
        # Add your signal logic here
        # Buy signal: df.loc[condition, 'Signal'] = 1
        # Sell signal: df.loc[condition, 'Signal'] = -1
        
        return df
''',
            
            "MACD Template": '''"""
MACD-based Trading Strategy Template
"""



class MACDCustomStrategy(BaseStrategy):
    """
    Custom MACD strategy with your own rules
    """
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        params = {
            'fast_period': fast,
            'slow_period': slow,
            'signal_period': signal
        }
        super().__init__(name="MACDCustom", params=params)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD indicators"""
        df = df.copy()
        
        fast = self.params['fast_period']
        slow = self.params['slow_period']
        signal = self.params['signal_period']
        
        # Calculate EMAs
        df['EMA_Fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
        df['EMA_Slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
        
        # MACD line
        df['MACD'] = df['EMA_Fast'] - df['EMA_Slow']
        
        # Signal line
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        
        # Histogram
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate MACD crossover signals"""
        df = df.copy()
        df['Signal'] = 0
        
        macd_prev = df['MACD'].shift(1)
        signal_prev = df['MACD_Signal'].shift(1)
        
        # Buy: MACD crosses above signal
        buy = (df['MACD'] > df['MACD_Signal']) & (macd_prev <= signal_prev)
        
        # Sell: MACD crosses below signal
        sell = (df['MACD'] < df['MACD_Signal']) & (macd_prev >= signal_prev)
        
        df.loc[buy, 'Signal'] = 1
        df.loc[sell, 'Signal'] = -1
        
        return df
''',
            
            "RSI Template": '''"""
RSI-based Trading Strategy Template
"""



class RSICustomStrategy(BaseStrategy):
    """
    Custom RSI strategy
    """
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        params = {
            'period': period,
            'oversold': oversold,
            'overbought': overbought
        }
        super().__init__(name="RSICustom", params=params)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI"""
        df = df.copy()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.params['period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.params['period']).mean()
        
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate RSI signals"""
        df = df.copy()
        df['Signal'] = 0
        
        rsi_prev = df['RSI'].shift(1)
        
        # Buy: RSI crosses below oversold
        buy = (df['RSI'] < self.params['oversold']) & (rsi_prev >= self.params['oversold'])
        
        # Sell: RSI crosses above overbought  
        sell = (df['RSI'] > self.params['overbought']) & (rsi_prev <= self.params['overbought'])
        
        df.loc[buy, 'Signal'] = 1
        df.loc[sell, 'Signal'] = -1
        
        return df
'''
        }
        
        code = templates.get(template_name, templates["Blank Strategy"])
        self.code_editor.setText(code)
        self.editor_log(f"Loaded template: {template_name}", "info")
    
    def validate_strategy(self):
        """Validate strategy syntax"""
        code = self.code_editor.toPlainText()
        
        if not code.strip():
            self.editor_log("No code to validate", "warning")
            return
        
        try:
            compile(code, '<string>', 'exec')
            self.editor_log("✓ Syntax is valid!", "success")
        except SyntaxError as e:
            self.editor_log(f"Syntax Error at line {e.lineno}: {e.msg}", "error")
        except Exception as e:
            self.editor_log(f"Error: {str(e)}", "error")
    
    def save_strategy(self):
        """Save strategy to file"""
        name = self.strategy_name_input.text().strip()
        code = self.code_editor.toPlainText()
        
        if not name:
            self.editor_log("Please enter a strategy name", "warning")
            return
        
        if not code.strip():
            self.editor_log("Cannot save empty strategy", "warning")
            return
        
        # Validate first
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            self.editor_log(f"Cannot save: Syntax Error at line {e.lineno}", "error")
            return
        
        strategies_dir = Path("strategies")
        strategies_dir.mkdir(exist_ok=True)
        
        file_path = strategies_dir / f"{name}.py"
        
        try:
            with open(file_path, 'w') as f:
                f.write(code)
            
            self.editor_log(f"✓ Strategy saved: {file_path}", "success")
            
            # Refresh strategy manager
            self.load_strategies()
            
            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"Strategy saved successfully!\n\nFile: {file_path}\n\nYou can now use it in the Run Backtest tab."
            )
            
        except Exception as e:
            self.editor_log(f"Failed to save: {str(e)}", "error")
    
    def quick_test_strategy(self):
        """Quick test the strategy"""
        name = self.strategy_name_input.text().strip() or "test_strategy"
        code = self.code_editor.toPlainText()
        
        if not code.strip():
            self.editor_log("No code to test", "warning")
            return
        
        self.editor_log("Testing strategy...", "info")
        
        try:
            # Compile code
            compiled = compile(code, '<string>', 'exec')
            
            # Create namespace
            namespace = {}
            exec(compiled, namespace)
            
            # Find strategy class
            strategy_class = None
            for item in namespace.values():
                if isinstance(item, type) and hasattr(item, 'calculate_indicators'):
                    strategy_class = item
                    break
            
            if not strategy_class:
                self.editor_log("No strategy class found in code", "error")
                return
            
            # Test instantiation
            strategy = strategy_class()
            self.editor_log(f"✓ Strategy instantiated: {strategy.name}", "success")
            
            # Quick data test
            
            # Generate fake data
            dates = pd.date_range('2023-01-01', periods=100)
            df = pd.DataFrame({
                'Open': np.random.randn(100).cumsum() + 100,
                'High': np.random.randn(100).cumsum() + 102,
                'Low': np.random.randn(100).cumsum() + 98,
                'Close': np.random.randn(100).cumsum() + 100,
                'Volume': np.random.randint(1000, 10000, 100)
            }, index=dates)
            
            # Run strategy
            df = strategy.run(df)
            
            if 'Signal' not in df.columns:
                self.editor_log("Warning: No Signal column generated", "warning")
            else:
                num_buy = (df['Signal'] == 1).sum()
                num_sell = (df['Signal'] == -1).sum()
                self.editor_log(f"✓ Test passed! Generated {num_buy} BUY and {num_sell} SELL signals", "success")
            
        except Exception as e:
            self.editor_log(f"Test failed: {str(e)}", "error")
            self.editor_log(traceback.format_exc(), "error")