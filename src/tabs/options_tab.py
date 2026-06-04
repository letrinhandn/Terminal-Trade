"""
OptionsTab - Extracted from terminal_trade_desktop.py
Full implementation for modular architecture
"""

import logging
import os
import io
import math
import traceback
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
from scipy.stats import norm

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTextEdit, QTableWidget, QTableWidgetItem, QGroupBox,
    QTabWidget, QSplitter, QMessageBox, QHeaderView, QListWidget,
    QListWidgetItem, QCheckBox, QDateEdit, QFormLayout, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QDate, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPixmap
from PyQt6.QtWebEngineWidgets import QWebEngineView

from realtime.orchestrator import DataOrchestrator
from realtime.clients.deribit_client import DeribitClient
from config.settings import DEFAULT_RISK_FREE_RATE

matplotlib.use('Agg')


class OptionsTab(QWidget):
    """Options tab - Professional Options Trading Terminal"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("COINDESK_API_KEY", "")

        self.current_data = None
        self.current_underlying = "BTC"
        self.current_mode = "live"  # live or historical
        self.last_update = None
        self.current_row = 0  # For progressive loading
        self.is_fetching = False  # Fetch state flag
        self.collected_expiries = set()  # Collect expiries for filter

        self.orchestrator = DataOrchestrator(self.api_key)
        self.orchestrator.progress.connect(self.on_fetch_progress)
        self.orchestrator.finished.connect(self.on_fetch_finished)
        self.orchestrator.error.connect(self.on_fetch_error)
        
        self.init_ui()
        
        # Don't auto-fetch on startup - wait for user to click LIVE MODE
        # QTimer.singleShot(1000, self.fetch_data)
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
    # TOP TOOLBAR
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
    # SUB-TABS
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333;
                background: #0a0a0a;
            }
            QTabBar::tab {
                background: #1a1a1a;
                color: #999;
                padding: 8px 20px;
                border: 1px solid #333;
                font-weight: bold;
                font-size: 10pt;
            }
            QTabBar::tab:selected {
                background: #ff6600;
                color: white;
            }
            QTabBar::tab:hover {
                background: #2a2a2a;
                color: #ff8800;
            }
        """)
        
        # Tab 1: Options Chain
        self.chain_tab = self.create_chain_tab()
        self.tabs.addTab(self.chain_tab, "OPTIONS CHAIN")
        
        # Tab 2: Volatility Analytics
        self.vol_tab = self.create_vol_analytics_tab()
        self.tabs.addTab(self.vol_tab, "VOL ANALYTICS")
        
        # Tab 3: Strategy & Pricing
        self.strategy_tab = self.create_strategy_tab()
        self.tabs.addTab(self.strategy_tab, "STRATEGY & PRICING")
        
        # Tab 4: Greeks Monitor
        self.greeks_tab = self.create_greeks_tab()
        self.tabs.addTab(self.greeks_tab, "GREEKS MONITOR")
        
        main_layout.addWidget(self.tabs)
        
    # STATUS BAR
        status_bar = self.create_status_bar()
        main_layout.addWidget(status_bar)
    
    def create_toolbar(self):
        """Create professional-style top toolbar"""
        toolbar = QWidget()
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff8800, stop:1 #ff6600);
                border-bottom: 2px solid #ff4400;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(15, 5, 15, 5)
        
        # LEFT GROUP: Underlying + Mode
        left_group = QWidget()
        left_group.setStyleSheet("background: transparent;")
        left_layout = QHBoxLayout(left_group)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Title
        title = QLabel("OPTIONS")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        left_layout.addWidget(title)
        
        # Underlying input (free text instead of dropdown)
        underlying_label = QLabel("Asset:")
        underlying_label.setStyleSheet("color: white; font-weight: bold;")
        left_layout.addWidget(underlying_label)
        
        self.underlying_input = QLineEdit()
        self.underlying_input.setText("BTC")
        self.underlying_input.setPlaceholderText("BTC, ETH, SOL...")
        self.underlying_input.setStyleSheet("""
            QLineEdit {
                background: #000;
                color: #ff8800;
                border: 2px solid #ff6600;
                padding: 6px 15px;
                font-weight: bold;
                font-size: 14pt;
                min-width: 100px;
            }
            QLineEdit:hover { background: #1a1a1a; }
        """)
        self.underlying_input.returnPressed.connect(self.on_underlying_changed)
        left_layout.addWidget(self.underlying_input)
        
        # Live/Historical toggle (now START/STOP)
        self.mode_toggle = QPushButton("🔴 START FETCHING")
        self.mode_toggle.setCheckable(False)
        self.mode_toggle.clicked.connect(self.toggle_fetch)
        self.mode_toggle.setStyleSheet("""
            QPushButton {
                background: #000;
                color: #ff0000;
                border: 2px solid #ff0000;
                padding: 6px 20px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover { 
                background: #1a0000;
                border-color: #ff3333;
            }
        """)
        self.mode_toggle.setToolTip("Click to START/STOP fetching live data from Deribit (FREE)")
        left_layout.addWidget(self.mode_toggle)
        
        # Data source indicator
        self.source_badge = QLabel("Deribit Live")
        self.source_badge.setStyleSheet("""
            background: #000;
            color: #00ff00;
            padding: 5px 10px;
            border: 1px solid #00ff00;
            border-radius: 3px;
            font-size: 9pt;
            font-weight: bold;
        """)
        left_layout.addWidget(self.source_badge)
        
        layout.addWidget(left_group)
        layout.addStretch()
        
        # RIGHT GROUP: Refresh + Export
        right_group = QWidget()
        right_group.setStyleSheet("background: transparent;")
        right_layout = QHBoxLayout(right_group)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # Refresh button (replaces old REFRESH - now clears and refetches)
        self.refresh_btn = QPushButton("REFRESH")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: #ff6600;
                color: white;
                border: none;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover { background: #cc5200; }
        """)
        self.refresh_btn.setToolTip("Clear all data and refetch from beginning")
        right_layout.addWidget(self.refresh_btn)
        
        # Export button
        export_btn = QPushButton("EXPORT")
        export_btn.clicked.connect(self.export_data)
        export_btn.setStyleSheet("""
            QPushButton {
                background: #ff6600;
                color: white;
                border: none;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover { background: #cc5200; }
        """)
        right_layout.addWidget(export_btn)
        
        layout.addWidget(right_group)
        
        return toolbar
    
    def create_status_bar(self):
        """Create bottom status bar"""
        status_bar = QWidget()
        status_bar.setFixedHeight(30)
        status_bar.setStyleSheet("""
            QWidget {
                background: #000;
                border-top: 1px solid #ff6600;
            }
        """)
        
        layout = QHBoxLayout(status_bar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Status label
        self.status_label = QLabel("● READY")
        self.status_label.setFont(QFont("Consolas", 9))
        self.status_label.setStyleSheet("color: #00ff00;")
        layout.addWidget(self.status_label)
        
        # Last update
        self.update_label = QLabel("Last update: —")
        self.update_label.setFont(QFont("Consolas", 8))
        self.update_label.setStyleSheet("color: #999;")
        layout.addWidget(self.update_label)
        
        layout.addStretch()
        
        # Provenance badge
        self.provenance_label = QLabel("")
        self.provenance_label.setFont(QFont("Consolas", 8))
        layout.addWidget(self.provenance_label)
        
        # Cache stats
        self.cache_stats_label = QLabel("")
        self.cache_stats_label.setFont(QFont("Consolas", 8))
        self.cache_stats_label.setStyleSheet("color: #666;")
        layout.addWidget(self.cache_stats_label)
        
        return status_bar
    
    # TAB CREATORS
    
    def create_chain_tab(self):
        """Create Options Chain tab with real-time data"""
        widget = QWidget()
        widget.setStyleSheet("background: #0a0a0a;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # LEFT: Filter panel
        filter_panel = self.create_filter_panel()
        layout.addWidget(filter_panel)
        
        # CENTER: Chain table
        chain_center = QWidget()
        chain_layout = QVBoxLayout(chain_center)
        chain_layout.setContentsMargins(5, 5, 5, 5)
        
        # Table
        self.chain_table = QTableWidget()
        self.chain_table.setStyleSheet("""
            QTableWidget {
                background: #000;
                color: #ccc;
                gridline-color: #333;
                font-family: Consolas;
                font-size: 9pt;
            }
            QHeaderView::section {
                background: #1a1a1a;
                color: #ff8800;
                padding: 5px;
                border: 1px solid #333;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 3px;
            }
            QTableWidget::item:selected {
                background: #ff6600;
                color: white;
            }
        """)
        self.chain_table.setColumnCount(14)
        self.chain_table.setHorizontalHeaderLabels([
            "Strike", "Expiry", "Type", "Bid", "Ask", "Mark", 
            "IV", "Delta", "Gamma", "Vega", "Theta", "Rho", "OI", "Volume"
        ])
        self.chain_table.horizontalHeader().setStretchLastSection(False)
        self.chain_table.verticalHeader().setVisible(False)
        self.chain_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.chain_table.setAlternatingRowColors(True)
        self.chain_table.doubleClicked.connect(self.on_contract_double_click)
        
        chain_layout.addWidget(self.chain_table)
        layout.addWidget(chain_center, 1)
        
        return widget
    
    def create_filter_panel(self):
        """Create left filter panel"""
        panel = QWidget()
        panel.setFixedWidth(200)
        panel.setStyleSheet("""
            QWidget {
                background: #1a1a1a;
                border-right: 1px solid #333;
            }
            QLabel {
                color: #ff8800;
                font-weight: bold;
                font-size: 9pt;
            }
            QCheckBox {
                color: #ccc;
            }
            QPushButton {
                background: #ff6600;
                color: white;
                border: none;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff7722;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("FILTERS")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Expiry filter (placeholder)
        layout.addWidget(QLabel("Expiry:"))
        self.expiry_list = QListWidget()
        self.expiry_list.setMaximumHeight(120)
        self.expiry_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.expiry_list)
        
        # Type filter
        layout.addWidget(QLabel("Type:"))
        self.calls_check = QCheckBox("Calls")
        self.calls_check.setChecked(True)
        layout.addWidget(self.calls_check)
        
        self.puts_check = QCheckBox("Puts")
        self.puts_check.setChecked(True)
        layout.addWidget(self.puts_check)
        
        # Apply button
        apply_btn = QPushButton("APPLY FILTERS")
        apply_btn.clicked.connect(self.apply_filters)
        layout.addWidget(apply_btn)
        
        layout.addStretch()
        
        return panel
    
    def create_vol_analytics_tab(self):
        """Create Volatility Analytics tab"""
        widget = QWidget()
        widget.setStyleSheet("background: #0a0a0a;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Sub-tabs for different views
        vol_tabs = QTabWidget()
        vol_tabs.setStyleSheet("""
            QTabBar::tab {
                background: #1a1a1a;
                color: #999;
                padding: 6px 15px;
            }
            QTabBar::tab:selected {
                background: #ff6600;
                color: white;
            }
        """)
        
        # IV Smile
        smile_widget = QWidget()
        self.smile_layout = QVBoxLayout(smile_widget)
        self.smile_label = QLabel()
        self.smile_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.smile_label.setStyleSheet("background: #1a1a1a; border: 1px solid #333;")
        self.smile_label.setMinimumHeight(400)
        self.smile_layout.addWidget(self.smile_label)
        vol_tabs.addTab(smile_widget, "IV Smile")
        
        # Term Structure
        term_widget = QWidget()
        self.term_layout = QVBoxLayout(term_widget)
        self.term_label = QLabel()
        self.term_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.term_label.setStyleSheet("background: #1a1a1a; border: 1px solid #333;")
        self.term_label.setMinimumHeight(400)
        self.term_layout.addWidget(self.term_label)
        vol_tabs.addTab(term_widget, "Term Structure")
        
        # 3D Surface (snapshot from current data)
        surface_widget = QWidget()
        surface_layout = QVBoxLayout(surface_widget)
        
        # Control bar for 3D surface
        surface_controls = QWidget()
        surface_controls.setStyleSheet("background: #1a1a1a;")
        controls_layout = QHBoxLayout(surface_controls)
        controls_layout.setContentsMargins(10, 5, 10, 5)
        
        # Mode selector (Snapshot vs Historical)
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet("color: #999; font-weight: bold;")
        controls_layout.addWidget(mode_label)
        
        self.surface_mode_combo = QComboBox()
        self.surface_mode_combo.addItems(["📸 Snapshot (Current)", "📊 Historical (CoinDesk)"])
        self.surface_mode_combo.setStyleSheet("""
            QComboBox {
                background: #000;
                color: #ff8800;
                border: 1px solid #ff6600;
                padding: 3px 8px;
                min-width: 150px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #000;
                color: #ff8800;
                selection-background-color: #ff6600;
            }
        """)
        self.surface_mode_combo.currentIndexChanged.connect(self.on_surface_mode_changed)
        controls_layout.addWidget(self.surface_mode_combo)
        
        controls_layout.addSpacing(20)
        
        # Historical date range (hidden by default)
        self.hist_date_widget = QWidget()
        hist_date_layout = QHBoxLayout(self.hist_date_widget)
        hist_date_layout.setContentsMargins(0, 0, 0, 0)
        
        start_label = QLabel("Start:")
        start_label.setStyleSheet("color: #999;")
        hist_date_layout.addWidget(start_label)
        
        self.surface_start_date = QDateEdit()
        self.surface_start_date.setDate(QDate.currentDate().addDays(-30))
        self.surface_start_date.setCalendarPopup(True)
        self.surface_start_date.setStyleSheet("""
            QDateEdit {
                background: #000;
                color: #ff8800;
                border: 1px solid #ff6600;
                padding: 3px;
            }
        """)
        hist_date_layout.addWidget(self.surface_start_date)
        
        end_label = QLabel("End:")
        end_label.setStyleSheet("color: #999;")
        hist_date_layout.addWidget(end_label)
        
        self.surface_end_date = QDateEdit()
        self.surface_end_date.setDate(QDate.currentDate())
        self.surface_end_date.setCalendarPopup(True)
        self.surface_end_date.setStyleSheet("""
            QDateEdit {
                background: #000;
                color: #ff8800;
                border: 1px solid #ff6600;
                padding: 3px;
            }
        """)
        hist_date_layout.addWidget(self.surface_end_date)
        
        self.hist_date_widget.hide()  # Hidden by default
        controls_layout.addWidget(self.hist_date_widget)
        
        controls_layout.addStretch()
        
        # Auto-regen checkbox
        self.auto_regen_surface = QCheckBox("Auto-regen after fetch")
        self.auto_regen_surface.setChecked(True)
        self.auto_regen_surface.setStyleSheet("color: #00ff00;")
        controls_layout.addWidget(self.auto_regen_surface)
        
        # Generate button
        self.generate_surface_btn = QPushButton("🎨 GENERATE 3D SURFACE")
        self.generate_surface_btn.clicked.connect(self.generate_3d_surface_snapshot)
        self.generate_surface_btn.setStyleSheet("""
            QPushButton {
                background: #ff6600;
                color: white;
                border: none;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover { background: #ff7722; }
        """)
        controls_layout.addWidget(self.generate_surface_btn)
        
        surface_layout.addWidget(surface_controls)
        
        # Container for chart (so we can replace it easily)
        self.surface_container = QWidget()
        self.surface_container_layout = QVBoxLayout(self.surface_container)
        self.surface_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.surface_label = QLabel("Click 'GENERATE 3D SURFACE' to render")
        self.surface_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.surface_label.setStyleSheet("background: #1a1a1a; border: 1px solid #333; color: #666;")
        self.surface_label.setMinimumHeight(400)
        self.surface_container_layout.addWidget(self.surface_label)
        
        surface_layout.addWidget(self.surface_container)
        vol_tabs.addTab(surface_widget, "3D Surface")
        
        layout.addWidget(vol_tabs)
        
        return widget
    
    def create_strategy_tab(self):
        """Create Strategy & Pricing tab for options analysis"""
        widget = QWidget()
        widget.setStyleSheet("background: #0a0a0a; color: #ccc;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("OPTION PRICER")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #ff8800;")
        layout.addWidget(title)
        
        # Form
        form = QFormLayout()
        form.setSpacing(10)
        
        self.pricer_underlying_input = QLineEdit("50000")
        self.pricer_strike_input = QLineEdit("55000")
        self.pricer_expiry_input = QLineEdit("30")
        self.pricer_iv_input = QLineEdit("0.80")
        self.pricer_type_combo = QComboBox()
        self.pricer_type_combo.addItems(["Call", "Put"])
        
        for widget_input in [self.pricer_underlying_input, self.pricer_strike_input, 
                             self.pricer_expiry_input, self.pricer_iv_input]:
            widget_input.setStyleSheet("""
                background: #1a1a1a;
                color: #fff;
                border: 1px solid #ff6600;
                padding: 5px;
                font-size: 10pt;
            """)
        
        form.addRow("Underlying Price:", self.pricer_underlying_input)
        form.addRow("Strike:", self.pricer_strike_input)
        form.addRow("DTE (days):", self.pricer_expiry_input)
        form.addRow("IV (decimal):", self.pricer_iv_input)
        form.addRow("Type:", self.pricer_type_combo)
        
        layout.addLayout(form)
        
        # Calculate button
        calc_btn = QPushButton("CALCULATE")
        calc_btn.clicked.connect(self.calculate_option_price)
        calc_btn.setStyleSheet("""
            QPushButton {
                background: #ff6600;
                color: white;
                border: none;
                padding: 10px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover { background: #ff7722; }
        """)
        layout.addWidget(calc_btn)
        
        # Results
        self.pricer_results = QLabel("Results will appear here")
        self.pricer_results.setStyleSheet("""
            background: #1a1a1a;
            color: #fff;
            border: 1px solid #333;
            padding: 15px;
            font-family: Consolas;
            font-size: 10pt;
        """)
        self.pricer_results.setMinimumHeight(200)
        layout.addWidget(self.pricer_results)
        
        layout.addStretch()
        
        return widget
    
    def create_greeks_tab(self):
        """Create Greeks Monitor tab"""
        widget = QWidget()
        widget.setStyleSheet("background: #0a0a0a; color: #ccc;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("GREEKS MONITOR")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #ff8800;")
        layout.addWidget(title)
        
        # Portfolio table
        self.greeks_table = QTableWidget()
        self.greeks_table.setColumnCount(8)
        self.greeks_table.setHorizontalHeaderLabels([
            "Contract", "Quantity", "Delta", "Gamma", "Vega", "Theta", "Rho", "Value"
        ])
        self.greeks_table.setStyleSheet("""
            QTableWidget {
                background: #000;
                color: #ccc;
                gridline-color: #333;
                font-family: Consolas;
                font-size: 9pt;
            }
            QHeaderView::section {
                background: #1a1a1a;
                color: #ff8800;
                padding: 5px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.greeks_table)
        
        # Add position button
        add_btn = QPushButton("+ ADD POSITION")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background: #218838; }
        """)
        layout.addWidget(add_btn)
        
        return widget
    
    # EVENT HANDLERS
    
    def on_underlying_changed(self):
        """Handle underlying change - just update internal state"""
        self.current_underlying = self.underlying_input.text().upper().strip()
    
    def toggle_fetch(self):
        """Toggle between START and STOP fetching"""
        if not self.is_fetching:
            # Start fetching
            self.is_fetching = True
            self.mode_toggle.setText("⏹ STOP FETCHING")
            self.mode_toggle.setStyleSheet("""
                QPushButton {
                    background: #dc3545;
                    color: white;
                    border: none;
                    padding: 6px 20px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover { background: #c82333; }
            """)
            self.start_live_fetch()
        else:
            # Stop fetching
            self.is_fetching = False
            if hasattr(self, 'fetch_thread') and self.fetch_thread.isRunning():
                self.fetch_thread.stop()
            self.mode_toggle.setText("🔴 START FETCHING")
            self.mode_toggle.setStyleSheet("""
                QPushButton {
                    background: #000;
                    color: #ff0000;
                    border: 2px solid #ff0000;
                    padding: 6px 20px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover { 
                    background: #1a0000;
                    border-color: #ff3333;
                }
            """)
            self.status_label.setText("⏸ STOPPED BY USER")
            self.status_label.setStyleSheet("color: #ffaa00;")
    
    def start_live_fetch(self):
        """Start fetching data progressively (called by toggle_fetch)"""
        self.current_underlying = self.underlying_input.text().upper().strip()
        
        if not self.current_underlying:
            self.status_label.setText("⚠ Enter asset symbol (e.g. BTC, ETH)")
            self.status_label.setStyleSheet("color: #ff0000;")
            self.is_fetching = False
            self.mode_toggle.setText("🔴 START FETCHING")
            return
        
        # Get filter values
        selected_expiries = []
        for i in range(self.expiry_list.count()):
            item = self.expiry_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_expiries.append(item.text())
        
        option_types = []
        if self.calls_check.isChecked():
            option_types.append("C")  # Deribit uses 'C' not 'call'
        if self.puts_check.isChecked():
            option_types.append("P")  # Deribit uses 'P' not 'put'
        
        if not option_types:
            option_types = ["C", "P"]  # Default both
        
        # Update status
        self.status_label.setText(f"⟳ FETCHING {self.current_underlying} OPTIONS...")
        self.status_label.setStyleSheet("color: #ffaa00;")
        
        self.fetch_data_progressive(selected_expiries, option_types)
    
    def fetch_data_progressive(self, expiries=None, option_types=None):
        """Fetch data progressively with filters"""
        
        class ProgressiveFetchThread(QThread):
            row_ready = pyqtSignal(dict)  # Emit each row as it's fetched
            finished_signal = pyqtSignal(int)  # Total rows
            error_signal = pyqtSignal(str)
            
            def __init__(self, client, underlying, expiries=None, option_types=None):
                super().__init__()
                self.client = client
                self.underlying = underlying
                self.expiries = expiries or []
                self.option_types = option_types or ["C", "P"]  # Deribit uses 'C'/'P'
                self._stop_flag = False
                
            def stop(self):
                """Stop the fetch thread"""
                self._stop_flag = True
                
            def run(self):
                try:
                    
                    # Get instruments
                    instruments_df = self.client.fetch_instruments(self.underlying)
                    
                    if instruments_df.empty:
                        self.error_signal.emit("No instruments found")
                        return
                    
                    # Apply filters (only if filters are specified)
                    if self.expiries and len(self.expiries) > 0:
                        instruments_df = instruments_df[
                            instruments_df['expiry_date'].astype(str).str[:10].isin(self.expiries)
                        ]
                    
                    if self.option_types and len(self.option_types) > 0:
                        instruments_df = instruments_df[
                            instruments_df['option_type'].isin(self.option_types)
                        ]
                    
                    # NO LIMIT - fetch all instruments until stopped
                    row_count = 0
                    for idx, instr in instruments_df.iterrows():
                        if self._stop_flag:
                            break
                            
                        instrument_name = instr['instrument_name']
                        
                        # Fetch ticker for this instrument
                        ticker = self.client._fetch_ticker(instrument_name)
                        
                        if ticker:
                            underlying_price = ticker.get('underlying_price', 0)
                            strike = instr['strike']
                            greeks = ticker.get('greeks', {})
                            stats = ticker.get('stats', {})
                            
                            row_data = {
                                'strike': strike,
                                'expiry_date': str(instr['expiry_date'])[:10] if instr.get('expiry_date') else '',
                                'option_type': 'Call' if instr['option_type'] == 'C' else 'Put',  # Display name
                                'bid': ticker.get('best_bid_price', 0),
                                'ask': ticker.get('best_ask_price', 0),
                                'mark': ticker.get('mark_price', 0),
                                'iv': ticker.get('mark_iv', 0) / 100.0,
                                'delta': greeks.get('delta', 0),
                                'gamma': greeks.get('gamma', 0),
                                'vega': greeks.get('vega', 0),
                                'theta': greeks.get('theta', 0),
                                'rho': greeks.get('rho', 0),
                                'open_interest': ticker.get('open_interest', 0),
                                'volume': stats.get('volume', 0),
                            }
                            
                            # Emit this row immediately
                            self.row_ready.emit(row_data)
                            row_count += 1
                    
                    self.finished_signal.emit(row_count)
                    
                except Exception as e:
                    self.error_signal.emit(str(e))
        
        # DON'T clear table - just append new data
        # (User must click REFRESH to clear)
        
        # Create and start thread
        client = DeribitClient()
        
        self.fetch_thread = ProgressiveFetchThread(
            client, 
            self.current_underlying,
            expiries,
            option_types
        )
        self.fetch_thread.row_ready.connect(self.add_row_to_table)
        self.fetch_thread.finished_signal.connect(self.on_progressive_fetch_complete)
        self.fetch_thread.error_signal.connect(self.on_fetch_error)
        self.fetch_thread.start()
    
    def add_row_to_table(self, row_data):
        """Add a single row to table immediately - NEW ROWS ON TOP"""
        # Insert at row 0 (top) instead of appending at bottom
        self.chain_table.insertRow(0)
        
        # Populate cells at row 0
        self.chain_table.setItem(0, 0, self._create_table_item(f"{row_data['strike']:.0f}"))
        self.chain_table.setItem(0, 1, self._create_table_item(row_data['expiry_date']))
        self.chain_table.setItem(0, 2, self._create_table_item(row_data['option_type']))
        self.chain_table.setItem(0, 3, self._create_table_item(f"{row_data['bid']:.4f}"))
        self.chain_table.setItem(0, 4, self._create_table_item(f"{row_data['ask']:.4f}"))
        self.chain_table.setItem(0, 5, self._create_table_item(f"{row_data['mark']:.4f}"))
        
        # IV with color
        iv_val = row_data['iv']
        iv_color = "#00ff00" if iv_val > 0 else "#999"
        self.chain_table.setItem(0, 6, self._create_table_item(f"{iv_val:.1%}", color=iv_color))
        
        # Greeks
        self.chain_table.setItem(0, 7, self._create_table_item(f"{row_data['delta']:.4f}"))
        
        # Gamma - format smaller with more decimals
        gamma_val = row_data['gamma']
        if gamma_val != 0:
            self.chain_table.setItem(0, 8, self._create_table_item(f"{gamma_val:.6f}"))
        else:
            self.chain_table.setItem(0, 8, self._create_table_item("0.000000"))
        
        # Vega
        self.chain_table.setItem(0, 9, self._create_table_item(f"{row_data['vega']:.4f}"))
        
        # Theta (usually negative)
        theta_val = row_data['theta']
        theta_color = "#ff6666" if theta_val < 0 else "#66ff66"
        self.chain_table.setItem(0, 10, self._create_table_item(f"{theta_val:.4f}", color=theta_color))
        
        # Rho
        self.chain_table.setItem(0, 11, self._create_table_item(f"{row_data['rho']:.4f}"))
        
        # Open Interest
        oi_val = row_data['open_interest']
        self.chain_table.setItem(0, 12, self._create_table_item(f"{oi_val:.1f}"))
        
        # Volume
        vol_val = row_data['volume']
        self.chain_table.setItem(0, 13, self._create_table_item(f"{vol_val:.2f}"))
        
        self.current_row += 1
        
        # Update status
        self.status_label.setText(f"⟳ LOADED {self.current_row} OPTIONS...")
        
        # Store expiry for filter (collect unique expiries)
        expiry = row_data['expiry_date']
        if expiry and expiry not in self.collected_expiries:
            self.collected_expiries.add(expiry)
            self.update_expiry_filter()
        
    def on_progressive_fetch_complete(self, total_rows):
        """Called when progressive fetch is done"""
        self.is_fetching = False
        self.status_label.setText(f"✅ LOADED {total_rows} OPTIONS")
        self.status_label.setStyleSheet("color: #00ff00;")
        
        # Reset button to START state
        self.mode_toggle.setText("� START FETCHING")
        self.mode_toggle.setStyleSheet("""
            QPushButton {
                background: #000;
                color: #ff0000;
                border: 2px solid #ff0000;
                padding: 6px 20px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover { 
                background: #1a0000;
                border-color: #ff3333;
            }
        """)
        
        # Auto-update analytics (Smile, Term Structure)
        self.update_vol_analytics()
        
        # Auto-regen 3D surface if enabled
        if self.auto_regen_surface.isChecked():
            self.generate_3d_surface_snapshot()
    
    def update_expiry_filter(self):
        """Update expiry filter list with collected expiries"""
        # Clear existing items
        self.expiry_list.clear()
        
        # Sort expiries and add to list with checkboxes
        sorted_expiries = sorted(list(self.collected_expiries))
        for expiry in sorted_expiries:
            item = QListWidgetItem(expiry)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.expiry_list.addItem(item)
    
    def toggle_mode(self):
        """Toggle between Live and Historical mode - fetches data when switching to LIVE"""
        if self.mode_toggle.isChecked():
            self.current_mode = "live"
            self.mode_toggle.setText("LIVE MODE")
            self.mode_toggle.setStyleSheet("""
                QPushButton {
                    background: #28a745;
                    color: white;
                    border: none;
                    padding: 6px 20px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover { background: #218838; }
            """)
            self.source_badge.setText("Deribit Live (Free)")
            self.source_badge.setStyleSheet("""
                background: #000;
                color: #00ff00;
                padding: 5px 10px;
                border: 1px solid #00ff00;
                border-radius: 3px;
                font-size: 9pt;
                font-weight: bold;
            """)
            # Fetch fresh data when switching to LIVE mode
            self.fetch_data(force=True)
        else:
            self.current_mode = "historical"
            self.mode_toggle.setText("HISTORICAL")
            self.mode_toggle.setStyleSheet("""
                QPushButton {
                    background: #6c757d;
                    color: white;
                    border: none;
                    padding: 6px 20px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover { background: #5a6268; }
            """)
            self.source_badge.setText("Deribit Cache (Free)")
            self.source_badge.setStyleSheet("""
                background: #000;
                color: #ffc107;
                padding: 5px 10px;
                border: 1px solid #ffc107;
                border-radius: 3px;
                font-size: 9pt;
                font-weight: bold;
            """)
        
    
    def fetch_data(self, force=False):
        """Fetch options data via orchestrator - with progressive loading"""
        
        self.status_label.setText("⟳ FETCHING FROM DERIBIT...")
        self.status_label.setStyleSheet("color: #ffc107;")
        
        # Clear existing table for fresh data
        self.chain_table.setRowCount(0)
        
        # Use threading to avoid blocking UI
        
        class FetchThread(QThread):

            def __init__(self, orchestrator, underlying, force):
                super().__init__()
                self.orchestrator = orchestrator
                self.underlying = underlying
                self.force = force
                self.df = None
                self.provenance = None
                self.error = None
                self._stop_flag = False
                
            def stop(self):
                """Stop the fetch thread"""
                self._stop_flag = True
                
            def run(self):
                try:
                    if self._stop_flag:
                        return
                    self.df, self.provenance = self.orchestrator.get_chain(
                        self.underlying,
                        mode="live",
                        force=self.force
                    )
                except Exception as e:
                    self.error = str(e)
        
        self.fetch_thread = FetchThread(self.orchestrator, self.current_underlying, force)
        self.fetch_thread.finished.connect(lambda: self._on_thread_finished(self.fetch_thread))
        self.fetch_thread.start()
    
    def _on_thread_finished(self, thread):
        """Handle thread completion"""
        if thread.error:
            self.on_fetch_error(thread.error)
        elif thread.df is not None:
            self.on_fetch_finished(thread.df, thread.provenance)
        else:
            self.on_fetch_error("No data returned")
    
    def on_fetch_progress(self, percent, message):
        """Handle fetch progress"""
        try:
            if hasattr(self, 'status_label') and self.status_label is not None:
                self.status_label.setText(f"⟳ {message} ({percent}%)")
        except RuntimeError:
            pass
    
    def on_fetch_finished(self, df, provenance):
        """Handle fetch completion"""
        self.current_data = df
        self.last_update = datetime.now()
        
        # Update UI - check if widgets exist
        try:
            if hasattr(self, 'status_label') and self.status_label is not None:
                self.status_label.setText("● LIVE (Deribit Free)")
                self.status_label.setStyleSheet("color: #00ff00;")
            if hasattr(self, 'update_label') and self.update_label is not None:
                self.update_label.setText(f"Last update: {self.last_update.strftime('%H:%M:%S')}")
            
            # Update provenance - always show Deribit source
            if provenance['from_cache']:
                badge_text = f"✅ Deribit Cache"
                badge_color = "#00ff00"
            else:
                badge_text = "🔄 Deribit API (Free)"
                badge_color = "#00ff00"
            
            if hasattr(self, 'provenance_label') and self.provenance_label is not None:
                self.provenance_label.setText(badge_text)
                self.provenance_label.setStyleSheet(f"color: {badge_color};")
            
            # Update cache stats
            stats = self.orchestrator.get_cache_stats(self.current_underlying)
            if hasattr(self, 'cache_stats_label') and self.cache_stats_label is not None:
                self.cache_stats_label.setText(
                    f"Cache: {stats['files']} files, {stats['total_rows']} rows"
                )
            
            # Populate tables
            self.populate_chain_table(df)
            self.populate_vol_analytics(df)
        except RuntimeError:
            # Widget has been deleted
            pass
    
    def on_fetch_error(self, error_msg):
        """Handle fetch error"""
        try:
            if hasattr(self, 'status_label') and self.status_label is not None:
                self.status_label.setText(f"● ERROR: {error_msg[:30]}")
                self.status_label.setStyleSheet("color: #dc3545;")
        except RuntimeError:
            pass
    
    def on_surface_mode_changed(self, index):
        """Handle surface mode change"""
        if index == 0:  # Snapshot
            self.hist_date_widget.hide()
        else:  # Historical
            self.hist_date_widget.show()
    
    def generate_3d_surface_snapshot(self):
        """Generate 3D surface - either snapshot or historical"""
        mode = self.surface_mode_combo.currentIndex()
        
        if mode == 0:
            # Snapshot from current data
            self._generate_snapshot_surface()
        else:
            # Historical from CoinDesk API
            self._generate_historical_surface()
    
    def _generate_snapshot_surface(self):
        """Generate 3D surface from current fetched data (snapshot)"""
        try:
            # Extract data from table
            data = []
            for row in range(self.chain_table.rowCount()):
                try:
                    strike = float(self.chain_table.item(row, 0).text())
                    expiry = self.chain_table.item(row, 1).text()
                    iv_text = self.chain_table.item(row, 6).text().strip('%')
                    iv = float(iv_text) / 100.0
                    
                    # Calculate days to expiry - try multiple formats
                    expiry_date = None
                    for fmt in ['%Y-%m-%d', '%d %b %y', '%Y/%m/%d']:
                        try:
                            expiry_date = datetime.strptime(expiry, fmt)
                            break
                        except Exception:
                            continue
                    
                    if not expiry_date:
                        continue
                    
                    days = (expiry_date - datetime.now()).days
                    if days < 0:
                        continue
                    
                    data.append({
                        'strike': strike,
                        'days': days,
                        'iv': iv * 100
                    })
                except Exception as e:
                    continue
            
            if len(data) < 10:
                try:
                    error_label = QLabel(f"Not enough data (need at least 10 contracts, got {len(data)})")
                    error_label.setStyleSheet("color: #ffaa00; padding: 20px;")
                    error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    while self.surface_container_layout.count():
                        item = self.surface_container_layout.takeAt(0)
                        if item.widget():
                            item.widget().deleteLater()

                    self.surface_container_layout.addWidget(error_label)
                except Exception as e:
                    logger.debug("Surface container unavailable: %s", e)
                return
            
            # Render 3D surface
            self.render_3d_surface_snapshot(data, title="Volatility Surface - Snapshot")
            
        except Exception as e:
            logger.warning("Error generating surface: %s", e)
    
    def _generate_historical_surface(self):
        """Generate 3D surface from CoinDesk historical API"""
        try:
            
            # Get date range
            start_qdate = self.surface_start_date.date()
            end_qdate = self.surface_end_date.date()
            
            start_date = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day()).date()
            end_date = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day()).date()
            
            if start_date >= end_date:
                error_label = QLabel("Start date must be before end date")
                error_label.setStyleSheet("color: #ff6666; padding: 20px;")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                while self.surface_container_layout.count():
                    item = self.surface_container_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                
                self.surface_container_layout.addWidget(error_label)
                return
            
            # Show loading indicator
            loading_label = QLabel(f"⏳ Fetching historical data from {start_date} to {end_date}...")
            loading_label.setStyleSheet("color: #ffc107; padding: 20px; font-size: 11pt;")
            loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            while self.surface_container_layout.count():
                item = self.surface_container_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            self.surface_container_layout.addWidget(loading_label)
            
            # Fetch historical data (in background thread)
            
            class HistoricalFetchThread(QThread):
                finished_signal = pyqtSignal(object)  # pandas DataFrame or dict
                error_signal = pyqtSignal(str)
                
                def __init__(self, orchestrator, underlying, start, end):
                    super().__init__()
                    self.orchestrator = orchestrator
                    self.underlying = underlying
                    self.start = start
                    self.end = end
                    
                def run(self):
                    try:
                        df, provenance = self.orchestrator.get_surface(
                            self.underlying,
                            self.start,
                            self.end,
                            force=False
                        )
                        self.finished_signal.emit(df)
                    except Exception as e:
                        self.error_signal.emit(str(e))
            
            # Create thread
            self.hist_fetch_thread = HistoricalFetchThread(
                self.orchestrator,
                self.current_underlying or 'BTC',
                start_date,
                end_date
            )
            self.hist_fetch_thread.finished_signal.connect(self.on_historical_data_ready)
            self.hist_fetch_thread.error_signal.connect(self.on_historical_error)
            self.hist_fetch_thread.start()
            
        except Exception as e:
            
            error_label = QLabel(f"Error: {str(e)}")
            error_label.setStyleSheet("color: #ff6666; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            while self.surface_container_layout.count():
                item = self.surface_container_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            self.surface_container_layout.addWidget(error_label)
    
    def on_historical_data_ready(self, df):
        """Handle historical data when ready"""
        try:
            if df.empty:
                error_label = QLabel("No historical data received")
                error_label.setStyleSheet("color: #ff6666; padding: 20px;")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                while self.surface_container_layout.count():
                    item = self.surface_container_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                
                self.surface_container_layout.addWidget(error_label)
                return
            
            # Convert DataFrame to data list format
            data = []
            for _, row in df.iterrows():
                try:
                    data.append({
                        'strike': float(row.get('strike', 0)),
                        'days': float(row.get('days_to_expiry', 0)),
                        'iv': float(row.get('iv', 0)) * 100
                    })
                except Exception:
                    continue
            
            if len(data) < 10:
                error_label = QLabel(f"Not enough data ({len(data)} points, need at least 10)")
                error_label.setStyleSheet("color: #ffaa00; padding: 20px;")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                while self.surface_container_layout.count():
                    item = self.surface_container_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                
                self.surface_container_layout.addWidget(error_label)
                return
            
            # Render historical surface
            start = self.surface_start_date.date().toString("yyyy-MM-dd")
            end = self.surface_end_date.date().toString("yyyy-MM-dd")
            self.render_3d_surface_snapshot(data, title=f"Historical Vol Surface ({start} to {end})")
            
        except Exception as e:
            logger.warning("Error in historical surface generation: %s", e)
    
    def on_historical_error(self, error_msg):
        """Handle historical fetch error"""
        error_label = QLabel(f"Historical fetch error: {error_msg}")
        error_label.setStyleSheet("color: #ff6666; padding: 20px;")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setWordWrap(True)
        
        while self.surface_container_layout.count():
            item = self.surface_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.surface_container_layout.addWidget(error_label)
    
    def render_3d_surface_snapshot(self, data, title="Volatility Surface"):
        """Render 3D volatility surface from snapshot data with interactive zoom"""
        try:
            matplotlib.use('Agg')
            
            # Extract coordinates
            strikes = np.array([d['strike'] for d in data])
            days = np.array([d['days'] for d in data])
            ivs = np.array([d['iv'] for d in data])
            
            # Remove duplicates and invalid values
            valid_mask = ~np.isnan(ivs) & ~np.isnan(strikes) & ~np.isnan(days)
            strikes = strikes[valid_mask]
            days = days[valid_mask]
            ivs = ivs[valid_mask]
            
            if len(strikes) < 4:
                try:
                    error_label = QLabel(f"Not enough valid data ({len(strikes)} points, need at least 4)")
                    error_label.setStyleSheet("color: #ffaa00; padding: 20px;")
                    error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    while self.surface_container_layout.count():
                        item = self.surface_container_layout.takeAt(0)
                        if item.widget():
                            item.widget().deleteLater()

                    self.surface_container_layout.addWidget(error_label)
                except Exception as e:
                    logger.debug("Surface container unavailable: %s", e)
                return

            # Create grid with reasonable resolution
            n_strikes = min(20, len(np.unique(strikes)))
            n_days = min(15, len(np.unique(days)))
            strike_range = np.linspace(strikes.min(), strikes.max(), n_strikes)
            days_range = np.linspace(days.min(), days.max(), n_days)
            strike_grid, days_grid = np.meshgrid(strike_range, days_range)

            try:
                iv_grid = griddata(
                    (strikes, days),
                    ivs,
                    (strike_grid, days_grid),
                    method='linear',
                    fill_value=np.nan
                )
            except Exception as interp_err:
                # Fallback to nearest neighbor if linear fails
                iv_grid = griddata(
                    (strikes, days),
                    ivs,
                    (strike_grid, days_grid),
                    method='nearest'
                )

            # Plot
            fig = Figure(figsize=(12, 8), facecolor='#0a0a0a')
            ax = fig.add_subplot(111, projection='3d')
            ax.set_facecolor('#0a0a0a')
            
            # Plot surface with NaN handling
            surf = ax.plot_surface(
                strike_grid, 
                days_grid, 
                iv_grid,
                cmap='plasma',
                alpha=0.8,
                edgecolor='k',
                linewidth=0.2,
                antialiased=True
            )
            
            # Scatter original points
            ax.scatter(strikes, days, ivs, c='cyan', marker='o', s=20, alpha=0.8, edgecolor='white', linewidth=0.5)
            
            ax.set_xlabel('Strike', color='white', fontsize=9)
            ax.set_ylabel('Days to Expiry', color='white', fontsize=9)
            ax.set_zlabel('IV (%)', color='white', fontsize=9)
            ax.set_title(f'{title} - {len(strikes)} points', color='#ff6600', fontsize=11, fontweight='bold', pad=10)
            
            # Set tick colors
            ax.tick_params(colors='white', labelsize=8)
            ax.xaxis.pane.fill = False
            ax.yaxis.pane.fill = False
            ax.zaxis.pane.fill = False
            ax.xaxis.pane.set_edgecolor('#333')
            ax.yaxis.pane.set_edgecolor('#333')
            ax.zaxis.pane.set_edgecolor('#333')
            
            # Colorbar
            cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, pad=0.1)
            cbar.set_label('IV (%)', color='white', fontsize=9)
            cbar.ax.tick_params(colors='white', labelsize=8)
            
            # Render to canvas with navigation toolbar
            canvas = FigureCanvasQTAgg(fig)
            canvas.setMinimumSize(900, 700)
            
            # Navigation toolbar for zoom/pan/rotate
            toolbar = NavigationToolbar2QT(canvas, self.surface_container)
            toolbar.setStyleSheet("""
                QToolBar {
                    background: #1a1a1a;
                    border: 1px solid #333;
                    spacing: 3px;
                    padding: 3px;
                }
                QToolButton {
                    background: #333;
                    color: white;
                    border: 1px solid #555;
                    padding: 3px;
                    margin: 1px;
                }
                QToolButton:hover {
                    background: #ff6600;
                    border-color: #ff8800;
                }
            """)
            
            canvas.draw()
            
            # Clear old widgets from CONTAINER layout only
            while self.surface_container_layout.count():
                item = self.surface_container_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add toolbar and canvas to container
            self.surface_container_layout.addWidget(toolbar)
            self.surface_container_layout.addWidget(canvas)
            
            # Force update
            self.surface_container.update()
            canvas.show()
            toolbar.show()
            
            
        except Exception as e:
            error_msg = f"Surface error: {str(e)[:100]}"
            logger.warning(error_msg)
            try:
                while self.surface_container_layout.count():
                    item = self.surface_container_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

                error_label = QLabel(error_msg)
                error_label.setStyleSheet("color: #ff6666; padding: 20px;")
                error_label.setWordWrap(True)
                self.surface_container_layout.addWidget(error_label)
            except Exception as e2:
                logger.debug("Surface container unavailable while showing error: %s", e2)
    
    def populate_chain_table(self, df):
        """Populate options chain table progressively (avoid lag)"""
        if df.empty:
            return
        
        # Limit to 100 rows for performance
        df = df.head(100)
        
        self.chain_table.setRowCount(len(df))
        
        # Populate in batches to avoid UI freeze
        batch_size = 10
        
        for batch_start in range(0, len(df), batch_size):
            batch_end = min(batch_start + batch_size, len(df))
            
            for i in range(batch_start, batch_end):
                row = df.iloc[i]
                
                # Strike
                self.chain_table.setItem(i, 0, self._create_table_item(f"{row.get('strike', 0):.0f}"))
                
                # Expiry
                expiry_str = str(row.get('expiry_date', ''))[:10] if 'expiry_date' in row else ''
                self.chain_table.setItem(i, 1, self._create_table_item(expiry_str))
                
                # Type (Call/Put)
                opt_type = row.get('option_type', row.get('type', ''))
                self.chain_table.setItem(i, 2, self._create_table_item(opt_type))
                
                # Bid
                self.chain_table.setItem(i, 3, self._create_table_item(f"{row.get('bid', 0):.4f}"))
                
                # Ask
                self.chain_table.setItem(i, 4, self._create_table_item(f"{row.get('ask', 0):.4f}"))
                
                # Mark
                self.chain_table.setItem(i, 5, self._create_table_item(f"{row.get('mark', 0):.4f}"))
                
                # IV
                iv_val = row.get('iv', 0)
                iv_color = "#00ff00" if iv_val > 0 else "#999"
                self.chain_table.setItem(i, 6, self._create_table_item(f"{iv_val:.1%}", color=iv_color))
                
                # Delta
                delta_val = row.get('delta', 0)
                self.chain_table.setItem(i, 7, self._create_table_item(f"{delta_val:.3f}"))
                
                # Gamma
                self.chain_table.setItem(i, 8, self._create_table_item(f"{row.get('gamma', 0):.4f}"))
            
            # Force UI update after each batch
            QApplication.processEvents()
    
    def _create_table_item(self, text, color="#ccc"):
        """Create styled table item"""
        
        item = QTableWidgetItem(str(text))
        item.setForeground(QColor(color))
        return item
    
    def update_vol_analytics(self):
        """Update Smile, Term Structure from chain_table data"""
        try:
            # Extract data from table
            data = []
            for row in range(self.chain_table.rowCount()):
                try:
                    strike = float(self.chain_table.item(row, 0).text())
                    expiry = self.chain_table.item(row, 1).text()
                    opt_type = self.chain_table.item(row, 2).text()
                    iv_text = self.chain_table.item(row, 6).text().strip('%')
                    iv = float(iv_text) / 100.0
                    
                    data.append({
                        'strike': strike,
                        'expiry': expiry,
                        'type': opt_type,
                        'iv': iv
                    })
                except Exception:
                    continue

            if not data:
                self.smile_label.setText("No data available")
                self.term_label.setText("No data available")
                return

            self.render_iv_smile(data)
            self.render_term_structure(data)

        except Exception as e:
            logger.warning("Vol analytics update failed: %s", e)
            self.smile_label.setText(f"Error: {str(e)}")
            self.term_label.setText(f"Error: {str(e)}")
    
    def populate_vol_analytics(self, df):
        """Deprecated - kept for compatibility"""
        pass
    
    def on_contract_double_click(self, index):
        """Handle double-click on contract"""
        # Open contract detail dialog"""
        pass
    
    def update_vol_analytics(self):
        """Update Smile, Term Structure from chain_table data"""
        try:
            # Extract data from table
            data = []
            for row in range(self.chain_table.rowCount()):
                try:
                    strike = float(self.chain_table.item(row, 0).text())
                    expiry = self.chain_table.item(row, 1).text()
                    opt_type = self.chain_table.item(row, 2).text()
                    iv_text = self.chain_table.item(row, 6).text().strip('%')
                    iv = float(iv_text) / 100.0
                    
                    data.append({
                        'strike': strike,
                        'expiry': expiry,
                        'type': opt_type,
                        'iv': iv
                    })
                except Exception:
                    continue

            if not data:
                try:
                    self.smile_label.setText("No data available - fetch options first")
                    self.term_label.setText("No data available - fetch options first")
                except Exception as e:
                    logger.debug("Labels unavailable: %s", e)
                return

            self.render_iv_smile(data)
            self.render_term_structure(data)

        except Exception as e:
            logger.warning("Vol analytics update failed: %s", e)
            try:
                self.smile_label.setText(f"Error: {str(e)}")
                self.term_label.setText(f"Error: {str(e)}")
            except Exception as e2:
                logger.debug("Labels unavailable: %s", e2)
    
    def render_iv_smile(self, data):
        """Render IV Smile chart"""
        try:
            matplotlib.use('Agg')
            
            # Group by expiry
            expiries = sorted(set(d['expiry'] for d in data))
            if not expiries:
                self.smile_label.setText("No expiry data")
                return
            
            # Use first 4 expiries
            fig = Figure(figsize=(8, 5), facecolor='#0a0a0a')
            ax = fig.add_subplot(111)
            ax.set_facecolor('#1a1a1a')
            
            colors = ['#ff6600', '#00aaff', '#00ff00', '#ffff00']
            
            for i, expiry in enumerate(expiries[:4]):
                expiry_data = [d for d in data if d['expiry'] == expiry]
                
                # Separate calls and puts
                calls = sorted([d for d in expiry_data if d['type'] == 'Call'], key=lambda x: x['strike'])
                puts = sorted([d for d in expiry_data if d['type'] == 'Put'], key=lambda x: x['strike'])
                
                if calls:
                    strikes = [c['strike'] for c in calls]
                    ivs = [c['iv'] * 100 for c in calls]
                    ax.plot(strikes, ivs, 'o-', color=colors[i % len(colors)], 
                           label=f'{expiry} (C)', linewidth=2, markersize=4)
                
                if puts:
                    strikes = [p['strike'] for p in puts]
                    ivs = [p['iv'] * 100 for p in puts]
                    ax.plot(strikes, ivs, 's--', color=colors[i % len(colors)], 
                           alpha=0.6, label=f'{expiry} (P)', linewidth=1, markersize=3)
            
            ax.set_xlabel('Strike Price', color='white', fontsize=10)
            ax.set_ylabel('Implied Volatility (%)', color='white', fontsize=10)
            ax.set_title('Volatility Smile', color='#ff6600', fontsize=12, fontweight='bold')
            ax.tick_params(colors='white')
            ax.grid(True, alpha=0.2, color='#666')
            ax.legend(facecolor='#1a1a1a', edgecolor='#666', labelcolor='white', fontsize=8)
            
            # Render to canvas
            canvas = FigureCanvasQTAgg(fig)
            canvas.draw()
            
            # Clear old widgets from layout
            while self.smile_layout.count():
                item = self.smile_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add new canvas
            self.smile_layout.addWidget(canvas)
            
        except Exception as e:
            logger.warning("IV smile chart error: %s", e)
            try:
                self.smile_label.setText(f"Chart error: {str(e)}")
            except Exception as e2:
                logger.debug("smile_label unavailable: %s", e2)
    
    def render_term_structure(self, data):
        """Render Term Structure (ATM IV over time)"""
        try:
            matplotlib.use('Agg')
            
            # Get current price (estimate from mid strikes)
            strikes = [d['strike'] for d in data]
            current_price = np.median(strikes)
            
            # Group by expiry and find ATM IV
            expiry_ivs = {}
            for expiry in sorted(set(d['expiry'] for d in data)):
                expiry_data = [d for d in data if d['expiry'] == expiry]
                
                # Find closest to ATM
                atm_data = min(expiry_data, key=lambda x: abs(x['strike'] - current_price))
                expiry_ivs[expiry] = atm_data['iv'] * 100
            
            if not expiry_ivs:
                try:
                    self.term_label.setText("No ATM data found")
                except Exception as e:
                    logger.debug("term_label unavailable: %s", e)
                return
            
            # Convert expiries to days
            expiry_dates = []
            ivs = []
            failed_dates = []
            
            for expiry_str, iv in sorted(expiry_ivs.items()):
                try:
                    # Try multiple date formats
                    expiry_date = None
                    for fmt in ['%Y-%m-%d', '%d %b %y', '%Y/%m/%d', '%m/%d/%Y']:
                        try:
                            expiry_date = datetime.strptime(expiry_str, fmt)
                            break
                        except Exception:
                            continue
                    
                    if not expiry_date:
                        failed_dates.append(expiry_str)
                        continue
                    
                    days = (expiry_date - datetime.now()).days
                    if days >= 0:  # Include today
                        expiry_dates.append(days)
                        ivs.append(iv)
                except Exception as e:
                    failed_dates.append(expiry_str)
                    continue
            
            if not expiry_dates:
                try:
                    msg = f"No valid expiries found.\nChecked: {len(expiry_ivs)} dates\nFailed: {failed_dates[:3]}"
                    self.term_label.setText(msg)
                except Exception as e:
                    logger.debug("term_label unavailable: %s", e)
                return
            
            # Plot
            fig = Figure(figsize=(8, 5), facecolor='#0a0a0a')
            ax = fig.add_subplot(111)
            ax.set_facecolor('#1a1a1a')
            
            ax.plot(expiry_dates, ivs, 'o-', color='#ff6600', linewidth=2, markersize=6)
            ax.fill_between(expiry_dates, ivs, alpha=0.3, color='#ff6600')
            
            ax.set_xlabel('Days to Expiry', color='white', fontsize=10)
            ax.set_ylabel('ATM Implied Volatility (%)', color='white', fontsize=10)
            ax.set_title('Volatility Term Structure', color='#ff6600', fontsize=12, fontweight='bold')
            ax.tick_params(colors='white')
            ax.grid(True, alpha=0.2, color='#666')
            
            # Render to canvas
            canvas = FigureCanvasQTAgg(fig)
            canvas.draw()
            
            # Clear old widgets from layout
            while self.term_layout.count():
                item = self.term_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add new canvas
            self.term_layout.addWidget(canvas)
            
        except Exception as e:
            logger.warning("Term structure chart error: %s", e)
            try:
                self.term_label.setText(f"Chart error: {str(e)}")
            except Exception as e2:
                logger.debug("term_label unavailable: %s", e2)
    
    def refresh_data(self):
        """Clear all data and refetch from beginning"""
        # Clear table
        self.chain_table.setRowCount(0)
        self.current_row = 0
        
        # Clear collected expiries
        self.collected_expiries.clear()
        self.expiry_list.clear()
        
        # Clear analytics - check if widgets still exist
        try:
            if hasattr(self, 'smile_label') and self.smile_label is not None:
                self.smile_label.setText("No data - click REFRESH or START FETCHING")
            if hasattr(self, 'term_label') and self.term_label is not None:
                self.term_label.setText("No data - click REFRESH or START FETCHING")
            if hasattr(self, 'surface_label') and self.surface_label is not None:
                self.surface_label.setText("No data - click REFRESH or START FETCHING")
        except RuntimeError:
            # Widget has been deleted
            pass
        
        # Update status
        try:
            if hasattr(self, 'status_label') and self.status_label is not None:
                self.status_label.setText("🧹 CLEARED - Click START FETCHING to reload")
                self.status_label.setStyleSheet("color: #ff8800;")
        except RuntimeError:
            pass
    
    def apply_filters(self):
        """Apply chain filters and re-fetch"""
        if self.is_fetching:
            # Stop current fetch first
            self.toggle_fetch()
        
        # Start new fetch with filters
        self.toggle_fetch()
    
    def calculate_option_price(self):
        """Calculate option theoretical price"""
        try:
            S = float(self.pricer_underlying_input.text())
            K = float(self.pricer_strike_input.text())
            T = float(self.pricer_expiry_input.text()) / 365.0
            sigma = float(self.pricer_iv_input.text())
            r = DEFAULT_RISK_FREE_RATE
            option_type = self.pricer_type_combo.currentText().lower()
            
            # Black-Scholes
            
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            
            if option_type == "call":
                price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
                delta = norm.cdf(d1)
            else:
                price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
                delta = -norm.cdf(-d1)
            
            gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
            vega = S * norm.pdf(d1) * math.sqrt(T)
            
            if option_type == "call":
                theta = (-S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) 
                        - r * K * math.exp(-r * T) * norm.cdf(d2))
            else:
                theta = (-S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) 
                        + r * K * math.exp(-r * T) * norm.cdf(-d2))
            
            # Display results
            results = f"""
THEORETICAL PRICE: ${price:.2f}

GREEKS:
Delta: {delta:.4f}
Gamma: {gamma:.6f}
Vega: {vega:.2f}
Theta: {theta:.2f} (per day)

INPUTS:
Underlying: ${S:,.2f}
Strike: ${K:,.2f}
DTE: {int(T * 365)} days
IV: {sigma*100:.1f}%
Type: {option_type.upper()}
            """
            
            self.pricer_results.setText(results)
            
        except Exception as e:
            self.pricer_results.setText(f"ERROR: {str(e)}")
    
    def export_data(self):
        """Export current data"""
        if self.current_data is None or self.current_data.empty:
            return
        
        filename = f"options_{self.current_underlying}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.current_data.to_csv(filename, index=False)
        
        QTimer.singleShot(3000, lambda: self.status_label.setText("● LIVE"))


    # OPTIONS TAB ENDS - Portfolio Tab follows