"""
PortfolioTab - Extracted from terminal_trade_desktop.py
Full implementation for modular architecture
"""

import os
import io
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTextEdit, QTableWidget, QTableWidgetItem, QGroupBox,
    QTabWidget, QSplitter, QMessageBox, QHeaderView, QListWidget,
    QListWidgetItem, QCheckBox, QDateEdit
)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QFont, QColor, QPixmap
from PyQt6.QtWebEngineWidgets import QWebEngineView

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class PortfolioTab(QWidget):
    """Portfolio tab - Compare multiple backtests"""
    

class PortfolioTab(QWidget):
    """Portfolio tab - Compare multiple backtests"""
    
    def __init__(self):
        super().__init__()
        self.backtests = []  # List of backtest results
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("💼 STRATEGY COMPARISON")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #ff6600; padding: 10px;")
        main_layout.addWidget(title)
        
    # TOP PANEL: Add Backtest
        add_group = QGroupBox("➕ ADD BACKTEST")
        add_layout = QHBoxLayout()
        add_layout.setSpacing(10)
        
        # Strategy
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "MACD Strategy",
            "MACD Advanced", 
            "MACD Conservative",
            "MACD Aggressive",
            "RSI Strategy"
        ])
        
        # Symbol
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Symbol (e.g., BTC-USD)")
        self.symbol_input.setText("BTC-USD")
        
        # Date range
        self.start_date = QLineEdit()
        self.start_date.setPlaceholderText("Start (YYYY-MM-DD)")
        self.start_date.setText("2023-01-01")
        
        self.end_date = QLineEdit()
        self.end_date.setPlaceholderText("End (optional)")
        
        # Capital
        self.capital_input = QLineEdit()
        self.capital_input.setPlaceholderText("Capital")
        self.capital_input.setText("10000")
        self.capital_input.setMaximumWidth(100)
        
        # Add button
        add_btn = QPushButton("▶ Add & Run")
        add_btn.clicked.connect(self.add_backtest)
        add_btn.setStyleSheet("""
            QPushButton {
                background: #00ff00;
                color: #000000;
                font-weight: bold;
                padding: 8px 15px;
            }
            QPushButton:hover { background: #00cc00; }
        """)
        
        # Clear button
        clear_btn = QPushButton("🗑 Clear All")
        clear_btn.clicked.connect(self.clear_all)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #ff3333;
                color: #000000;
                font-weight: bold;
                padding: 8px 15px;
            }
            QPushButton:hover { background: #cc0000; }
        """)
        
        add_layout.addWidget(QLabel("Strategy:"))
        add_layout.addWidget(self.strategy_combo, 2)
        add_layout.addWidget(QLabel("Symbol:"))
        add_layout.addWidget(self.symbol_input, 1)
        add_layout.addWidget(QLabel("From:"))
        add_layout.addWidget(self.start_date, 1)
        add_layout.addWidget(QLabel("To:"))
        add_layout.addWidget(self.end_date, 1)
        add_layout.addWidget(QLabel("Capital:"))
        add_layout.addWidget(self.capital_input)
        add_layout.addWidget(add_btn)
        add_layout.addWidget(clear_btn)
        
        add_group.setLayout(add_layout)
        main_layout.addWidget(add_group)
        
    # MIDDLE PANEL: Comparison Table
        table_group = QGroupBox("📊 COMPARISON TABLE")
        table_layout = QVBoxLayout()
        
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(10)
        self.comparison_table.setHorizontalHeaderLabels([
            "Strategy", "Symbol", "Return (%)", "Sharpe", "Max DD (%)", 
            "Win Rate (%)", "Trades", "Profit Factor", "Volatility (%)", "Actions"
        ])
        self.comparison_table.horizontalHeader().setStretchLastSection(True)
        self.comparison_table.setAlternatingRowColors(True)
        self.comparison_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        table_layout.addWidget(self.comparison_table)
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group, 1)
        
    # BOTTOM PANEL: Stats & Log
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Stats
        stats_group = QGroupBox("📈 STATISTICS")
        stats_layout = QVBoxLayout()
        
        self.stats_label = QLabel("No backtests added yet")
        self.stats_label.setFont(QFont("Consolas", 10))
        self.stats_label.setWordWrap(True)
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        stats_layout.addWidget(self.stats_label)
        stats_group.setLayout(stats_layout)
        
        # Log
        log_group = QGroupBox("📜 LOG")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMaximumHeight(150)
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        bottom_splitter.addWidget(stats_group)
        bottom_splitter.addWidget(log_group)
        bottom_splitter.setStretchFactor(0, 1)
        bottom_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(bottom_splitter, 0)
        
        # Initial log
        self.log("Strategy comparison module ready")
        self.log("Add backtests to compare performance")
    
    def log(self, message: str, level: str = "info"):
        """Log message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if level == "error":
            color = "red"
        elif level == "success":
            color = "green"
        elif level == "warning":
            color = "orange"
        else:
            color = "#00aaff"
        
        html = f'<span style="color: #666;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        self.log_text.append(html)
        
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def add_backtest(self):
        """Add and run a new backtest"""
        self.log("Adding new backtest...", "info")
        
        try:
            # Import modules
            from data.data_loader import load_data
            from strategies.macd_strategy import MACDStrategy, RSIStrategy
            from strategies.macd_advanced import MACDAdvancedStrategy, MACDConservative, MACDAggressive
            from backtest.engine import BacktestEngine
            from metrics.performance import PerformanceMetrics
            
            # Get parameters
            symbol = self.symbol_input.text().strip().upper()
            start_date = self.start_date.text().strip()
            end_date = self.end_date.text().strip() or None
            capital = float(self.capital_input.text().strip())
            strategy_name = self.strategy_combo.currentText()
            
            if not symbol or not start_date:
                self.log("Please enter symbol and start date", "error")
                return
            
            # Select strategy
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
            self.log(f"Loading {symbol}...", "info")
            df = load_data(symbol, start_date, end_date, source='yahoo')
            
            if df is None or df.empty:
                self.log(f"No data for {symbol}", "error")
                return
            
            # Run backtest
            self.log(f"Running {strategy_name}...", "info")
            df = strategy.run(df)
            engine = BacktestEngine(initial_capital=capital, commission=0.001)
            backtest_results = engine.run(df)
            
            # Calculate metrics
            metrics_calc = PerformanceMetrics()
            metrics = metrics_calc.calculate_all_metrics(
                backtest_results,
                backtest_results['equity_curve']
            )
            
            # Store results
            result = {
                'strategy': strategy_name,
                'symbol': symbol,
                'metrics': metrics,
                'backtest': backtest_results,
                'capital': capital
            }
            self.backtests.append(result)
            
            # Update UI
            self.update_comparison_table()
            self.update_statistics()
            
            self.log(f"✓ Added: {strategy_name} on {symbol} - Return: {metrics['total_return']:.2f}%", "success")
        
        except Exception as e:
            self.log(f"Error: {str(e)}", "error")
    
    def update_comparison_table(self):
        """Update comparison table with all backtests"""
        self.comparison_table.setRowCount(len(self.backtests))
        
        for i, result in enumerate(self.backtests):
            metrics = result['metrics']
            
            # Strategy
            self.comparison_table.setItem(i, 0, QTableWidgetItem(result['strategy']))
            
            # Symbol
            self.comparison_table.setItem(i, 1, QTableWidgetItem(result['symbol']))
            
            # Return (colored)
            return_item = QTableWidgetItem(f"{metrics['total_return']:.2f}")
            if metrics['total_return'] > 0:
                return_item.setForeground(QColor("#00ff00"))
            else:
                return_item.setForeground(QColor("#ff0000"))
            self.comparison_table.setItem(i, 2, return_item)
            
            # Other metrics
            self.comparison_table.setItem(i, 3, QTableWidgetItem(f"{metrics['sharpe_ratio']:.2f}"))
            self.comparison_table.setItem(i, 4, QTableWidgetItem(f"{metrics['max_drawdown']:.2f}"))
            self.comparison_table.setItem(i, 5, QTableWidgetItem(f"{metrics['win_rate']:.2f}"))
            self.comparison_table.setItem(i, 6, QTableWidgetItem(f"{metrics['num_trades']}"))
            self.comparison_table.setItem(i, 7, QTableWidgetItem(f"{metrics['profit_factor']:.2f}"))
            self.comparison_table.setItem(i, 8, QTableWidgetItem(f"{metrics['volatility']:.2f}"))
            
            # Actions
            remove_btn = QPushButton("🗑")
            remove_btn.clicked.connect(lambda checked, idx=i: self.remove_backtest(idx))
            remove_btn.setMaximumWidth(40)
            remove_btn.setStyleSheet("""
                QPushButton {
                    background: #ff3333;
                    color: #000000;
                    border: none;
                }
                QPushButton:hover { background: #cc0000; }
            """)
            self.comparison_table.setCellWidget(i, 9, remove_btn)
        
        self.comparison_table.resizeColumnsToContents()
    
    def update_statistics(self):
        """Update statistics panel"""
        if not self.backtests:
            self.stats_label.setText("No backtests added yet")
            return
        
        # Calculate aggregated stats
        avg_return = sum(b['metrics']['total_return'] for b in self.backtests) / len(self.backtests)
        avg_sharpe = sum(b['metrics']['sharpe_ratio'] for b in self.backtests) / len(self.backtests)
        avg_win_rate = sum(b['metrics']['win_rate'] for b in self.backtests) / len(self.backtests)
        total_trades = sum(b['metrics']['num_trades'] for b in self.backtests)
        
        # Find best performer
        best = max(self.backtests, key=lambda x: x['metrics']['total_return'])
        worst = min(self.backtests, key=lambda x: x['metrics']['total_return'])
        
        stats_text = f"""
📊 PORTFOLIO STATISTICS

Total Backtests: {len(self.backtests)}
Total Trades: {total_trades}

Average Performance:
  Return:     {avg_return:.2f}%
  Sharpe:     {avg_sharpe:.2f}
  Win Rate:   {avg_win_rate:.2f}%

Best Performer:
  {best['strategy']} on {best['symbol']}
  Return: {best['metrics']['total_return']:.2f}%
  Sharpe: {best['metrics']['sharpe_ratio']:.2f}

Worst Performer:
  {worst['strategy']} on {worst['symbol']}
  Return: {worst['metrics']['total_return']:.2f}%
  Sharpe: {worst['metrics']['sharpe_ratio']:.2f}
        """
        
        self.stats_label.setText(stats_text.strip())
    
    def remove_backtest(self, index: int):
        """Remove a backtest from comparison"""
        if 0 <= index < len(self.backtests):
            removed = self.backtests.pop(index)
            self.log(f"Removed: {removed['strategy']} on {removed['symbol']}", "warning")
            self.update_comparison_table()
            self.update_statistics()
    
    def clear_all(self):
        """Clear all backtests"""
        if self.backtests:
            reply = QMessageBox.question(
                self,
                "Clear All",
                f"Remove all {len(self.backtests)} backtests?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.backtests.clear()
                self.update_comparison_table()
                self.update_statistics()
                self.log("All backtests cleared", "warning")