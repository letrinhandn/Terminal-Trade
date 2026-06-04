"""Company Information Widget - Displays comprehensive company data"""

import requests
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QTableWidget, QTableWidgetItem, QScrollArea
)

from src.api.finnhub_client import FinnhubClient


class CompanyInfoLoader(QThread):
    """Background thread for loading company info data"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, symbol: str, finnhub: FinnhubClient):
        super().__init__()
        self.symbol = symbol
        self.finnhub = finnhub
    
    def run(self):
        """Load all data"""
        try:
            data = {}
            
            self.progress.emit("⏳ Fetching profile...")
            data['profile'] = self.finnhub.get_company_profile(self.symbol)
            
            self.progress.emit("⏳ Fetching quote...")
            data['quote'] = self.finnhub.get_quote(self.symbol)
            
            self.progress.emit("⏳ Fetching metrics...")
            data['metrics'] = self.finnhub.get_basic_financials(self.symbol)
            
            self.progress.emit("⏳ Fetching analyst recommendations...")
            data['recommendations'] = self.finnhub.get_recommendation_trends(self.symbol)
            
            self.progress.emit("⏳ Fetching price targets...")
            data['price_targets'] = self.finnhub.get_price_target(self.symbol)
            
            self.progress.emit("⏳ Fetching upgrades/downgrades...")
            data['upgrades'] = self.finnhub.get_upgrades_downgrades(self.symbol)
            
            self.progress.emit("⏳ Fetching earnings surprises...")
            data['earnings'] = self.finnhub.get_earnings_surprises(self.symbol)
            
            self.progress.emit("⏳ Fetching insider transactions...")
            data['insider'] = self.finnhub.get_insider_transactions(self.symbol)
            
            self.progress.emit("⏳ Fetching peers...")
            data['peers'] = self.finnhub.get_peers(self.symbol)
            
            self.finished.emit(data)
            
        except Exception as e:
            self.error.emit(str(e))


class CompanyInfoWidget(QWidget):
    """Company Information Widget - Profile, Stats, Estimates, Analyst Data"""
    
    def __init__(self):
        super().__init__()
        self.finnhub = FinnhubClient()
        self.current_symbol = None
        self.loader = None
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top bar - Live price ticker
        self.top_bar = QWidget()
        self.top_bar.setStyleSheet("background: #1a1a1a; padding: 15px;")
        self.top_bar_layout = QHBoxLayout(self.top_bar)
        self.top_bar_layout.setSpacing(20)
        
        # Symbol + Name
        self.symbol_label = QLabel("--")
        self.symbol_label.setStyleSheet("color: #ff6600; font-size: 18pt; font-weight: bold;")
        self.top_bar_layout.addWidget(self.symbol_label)
        
        self.name_label = QLabel("")
        self.name_label.setStyleSheet("color: #ccc; font-size: 12pt;")
        self.top_bar_layout.addWidget(self.name_label)
        
        self.top_bar_layout.addStretch()
        
        # Price
        self.price_label = QLabel("--")
        self.price_label.setStyleSheet("color: #fff; font-size: 16pt; font-weight: bold;")
        self.top_bar_layout.addWidget(self.price_label)
        
        # Change
        self.change_label = QLabel("--")
        self.change_label.setStyleSheet("color: #00ff00; font-size: 14pt; font-weight: bold;")
        self.top_bar_layout.addWidget(self.change_label)
        
        # Change %
        self.change_pct_label = QLabel("--")
        self.change_pct_label.setStyleSheet("color: #00ff00; font-size: 14pt; font-weight: bold;")
        self.top_bar_layout.addWidget(self.change_pct_label)
        
        # Market cap
        self.market_cap_label = QLabel("Market Cap: --")
        self.market_cap_label.setStyleSheet("color: #ccc; font-size: 11pt;")
        self.top_bar_layout.addWidget(self.market_cap_label)
        
        main_layout.addWidget(self.top_bar)
        
        # 3-column layout: Left (25%), Center (50%), Right (25%)
        columns_widget = QWidget()
        columns_layout = QHBoxLayout(columns_widget)
        columns_layout.setContentsMargins(10, 10, 10, 10)
        columns_layout.setSpacing(10)
        
        # Left column - Stats, Financials, Estimates, Dividends, Ownership (25%)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setStyleSheet("QScrollArea { border: none; background: #000; }")
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)
        
        # Key stats group
        self.stats_group = self.create_stats_group()
        left_layout.addWidget(self.stats_group)
        
        # Financials group
        self.financials_group = self.create_financials_group()
        left_layout.addWidget(self.financials_group)
        
        # Estimates group
        self.estimates_group = self.create_estimates_group()
        left_layout.addWidget(self.estimates_group)
        
        # Dividends group
        self.dividends_group = self.create_dividends_group()
        left_layout.addWidget(self.dividends_group)
        
        # Ownership group
        self.ownership_group = self.create_ownership_group()
        left_layout.addWidget(self.ownership_group)
        
        left_layout.addStretch()
        left_scroll.setWidget(left_widget)
        
        # Center column - Analyst ratings, price targets, upgrades/downgrades, earnings (50%)
        center_scroll = QScrollArea()
        center_scroll.setWidgetResizable(True)
        center_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        center_scroll.setStyleSheet("QScrollArea { border: none; background: #000; }")
        
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(15)
        
        # Analyst Recommendations chart
        self.recommendations_group = self.create_recommendations_group()
        center_layout.addWidget(self.recommendations_group)
        
        # Price Targets
        self.price_targets_group = self.create_price_targets_group()
        center_layout.addWidget(self.price_targets_group)
        
        # Upgrades/Downgrades timeline
        self.upgrades_group = self.create_upgrades_group()
        center_layout.addWidget(self.upgrades_group)
        
        # Earnings surprises
        self.earnings_group = self.create_earnings_group()
        center_layout.addWidget(self.earnings_group)
        
        center_layout.addStretch()
        center_scroll.setWidget(center_widget)
        
        # Right column - Profile card, Insider transactions, Peers (25%)
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setStyleSheet("QScrollArea { border: none; background: #000; }")
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)
        
        # Company profile card
        self.profile_group = self.create_profile_group()
        right_layout.addWidget(self.profile_group)
        
        # Insider transactions
        self.insider_group = self.create_insider_group()
        right_layout.addWidget(self.insider_group)
        
        # Peers
        self.peers_group = self.create_peers_group()
        right_layout.addWidget(self.peers_group)
        
        right_layout.addStretch()
        right_scroll.setWidget(right_widget)
        
        # Add columns with size policies
        columns_layout.addWidget(left_scroll, 25)  # 25% width
        columns_layout.addWidget(center_scroll, 50)  # 50% width
        columns_layout.addWidget(right_scroll, 25)  # 25% width
        
        main_layout.addWidget(columns_widget, 1)  # Stretch to fill
    
    def create_group(self, title: str) -> QGroupBox:
        """Create styled group box"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                color: #ff6600;
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #ff6600;
                border-radius: 5px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        return group
    
    def create_stats_group(self) -> QGroupBox:
        """Create key stats group"""
        group = self.create_group("KEY STATISTICS")
        layout = QVBoxLayout(group)
        
        # Labels to update
        self.pe_label = QLabel("P/E Ratio: --")
        self.eps_label = QLabel("EPS: --")
        self.beta_label = QLabel("Beta: --")
        self.week_52_high_label = QLabel("52-Week High: --")
        self.week_52_low_label = QLabel("52-Week Low: --")
        self.avg_volume_label = QLabel("Avg Volume: --")
        
        for label in [self.pe_label, self.eps_label, self.beta_label, 
                     self.week_52_high_label, self.week_52_low_label, self.avg_volume_label]:
            label.setStyleSheet("color: #ccc; font-size: 10pt; padding: 3px;")
            layout.addWidget(label)
        
        return group
    
    def create_financials_group(self) -> QGroupBox:
        """Create financials group"""
        group = self.create_group("FINANCIALS")
        layout = QVBoxLayout(group)
        
        self.revenue_label = QLabel("Revenue (TTM): --")
        self.net_income_label = QLabel("Net Income (TTM): --")
        self.ebitda_label = QLabel("EBITDA: --")
        self.gross_margin_label = QLabel("Gross Margin: --")
        self.operating_margin_label = QLabel("Operating Margin: --")
        self.profit_margin_label = QLabel("Profit Margin: --")
        
        for label in [self.revenue_label, self.net_income_label, self.ebitda_label,
                     self.gross_margin_label, self.operating_margin_label, self.profit_margin_label]:
            label.setStyleSheet("color: #ccc; font-size: 10pt; padding: 3px;")
            layout.addWidget(label)
        
        return group
    
    def create_estimates_group(self) -> QGroupBox:
        """Create estimates group"""
        group = self.create_group("ANALYST ESTIMATES")
        layout = QVBoxLayout(group)
        
        self.target_price_label = QLabel("Target Price: --")
        self.eps_estimate_label = QLabel("EPS Estimate: --")
        self.revenue_estimate_label = QLabel("Revenue Est: --")
        
        for label in [self.target_price_label, self.eps_estimate_label, self.revenue_estimate_label]:
            label.setStyleSheet("color: #ccc; font-size: 10pt; padding: 3px;")
            layout.addWidget(label)
        
        return group
    
    def create_dividends_group(self) -> QGroupBox:
        """Create dividends group"""
        group = self.create_group("DIVIDENDS")
        layout = QVBoxLayout(group)
        
        self.dividend_yield_label = QLabel("Dividend Yield: --")
        self.payout_ratio_label = QLabel("Payout Ratio: --")
        
        for label in [self.dividend_yield_label, self.payout_ratio_label]:
            label.setStyleSheet("color: #ccc; font-size: 10pt; padding: 3px;")
            layout.addWidget(label)
        
        return group
    
    def create_ownership_group(self) -> QGroupBox:
        """Create ownership group"""
        group = self.create_group("OWNERSHIP")
        layout = QVBoxLayout(group)
        
        self.shares_outstanding_label = QLabel("Shares Outstanding: --")
        self.float_shares_label = QLabel("Float: --")
        self.insider_ownership_label = QLabel("Insider Ownership: --")
        self.institutional_label = QLabel("Institutional: --")
        
        for label in [self.shares_outstanding_label, self.float_shares_label,
                     self.insider_ownership_label, self.institutional_label]:
            label.setStyleSheet("color: #ccc; font-size: 10pt; padding: 3px;")
            layout.addWidget(label)
        
        return group
    
    def create_recommendations_group(self) -> QGroupBox:
        """Create analyst recommendations group with table"""
        group = self.create_group("ANALYST RECOMMENDATIONS")
        layout = QVBoxLayout(group)
        
        self.recommendations_table = QTableWidget()
        self.recommendations_table.setColumnCount(6)
        self.recommendations_table.setHorizontalHeaderLabels(["Period", "Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"])
        self.recommendations_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background: #1a1a1a;
                color: #ff6600;
                font-weight: bold;
                border: 1px solid #333;
                padding: 5px;
                font-size: 9pt;
            }
        """)
        self.recommendations_table.setStyleSheet("""
            QTableWidget {
                background: #000;
                color: #ccc;
                gridline-color: #333;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        self.recommendations_table.verticalHeader().setVisible(False)
        self.recommendations_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.recommendations_table)
        
        return group
    
    def create_price_targets_group(self) -> QGroupBox:
        """Create price targets group"""
        group = self.create_group("PRICE TARGETS")
        layout = QVBoxLayout(group)
        
        self.target_high_label = QLabel("Target High: --")
        self.target_median_label = QLabel("Target Median: --")
        self.target_low_label = QLabel("Target Low: --")
        self.target_mean_label = QLabel("Target Mean: --")
        
        for label in [self.target_high_label, self.target_median_label, 
                     self.target_low_label, self.target_mean_label]:
            label.setStyleSheet("color: #ccc; font-size: 10pt; padding: 3px;")
            layout.addWidget(label)
        
        return group
    
    def create_upgrades_group(self) -> QGroupBox:
        """Create upgrades/downgrades group"""
        group = self.create_group("UPGRADES / DOWNGRADES")
        layout = QVBoxLayout(group)
        
        self.upgrades_table = QTableWidget()
        self.upgrades_table.setColumnCount(4)
        self.upgrades_table.setHorizontalHeaderLabels(["Date", "Firm", "Action", "From → To"])
        self.upgrades_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background: #1a1a1a;
                color: #ff6600;
                font-weight: bold;
                border: 1px solid #333;
                padding: 5px;
                font-size: 9pt;
            }
        """)
        self.upgrades_table.setStyleSheet("""
            QTableWidget {
                background: #000;
                color: #ccc;
                gridline-color: #333;
                font-size: 9pt;
            }
        """)
        self.upgrades_table.verticalHeader().setVisible(False)
        self.upgrades_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.upgrades_table)
        
        return group
    
    def create_earnings_group(self) -> QGroupBox:
        """Create earnings surprises group"""
        group = self.create_group("EARNINGS SURPRISES")
        layout = QVBoxLayout(group)
        
        self.earnings_table = QTableWidget()
        self.earnings_table.setColumnCount(4)
        self.earnings_table.setHorizontalHeaderLabels(["Period", "Actual", "Estimate", "Surprise %"])
        self.earnings_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background: #1a1a1a;
                color: #ff6600;
                font-weight: bold;
                border: 1px solid #333;
                padding: 5px;
                font-size: 9pt;
            }
        """)
        self.earnings_table.setStyleSheet("""
            QTableWidget {
                background: #000;
                color: #ccc;
                gridline-color: #333;
                font-size: 9pt;
            }
        """)
        self.earnings_table.verticalHeader().setVisible(False)
        self.earnings_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.earnings_table)
        
        return group
    
    def create_profile_group(self) -> QGroupBox:
        """Create company profile card"""
        group = self.create_group("COMPANY PROFILE")
        layout = QVBoxLayout(group)
        
        # Logo
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedHeight(60)
        layout.addWidget(self.logo_label)
        
        # Info labels
        self.industry_label = QLabel("Industry: --")
        self.sector_label = QLabel("Sector: --")
        self.country_label = QLabel("Country: --")
        self.exchange_label = QLabel("Exchange: --")
        self.ipo_label = QLabel("IPO Date: --")
        
        for label in [self.industry_label, self.sector_label, self.country_label, 
                     self.exchange_label, self.ipo_label]:
            label.setStyleSheet("color: #ccc; font-size: 9pt; padding: 3px;")
            label.setWordWrap(True)
            layout.addWidget(label)
        
        return group
    
    def create_insider_group(self) -> QGroupBox:
        """Create insider transactions group"""
        group = self.create_group("INSIDER TRANSACTIONS")
        layout = QVBoxLayout(group)
        
        self.insider_table = QTableWidget()
        self.insider_table.setColumnCount(3)
        self.insider_table.setHorizontalHeaderLabels(["Date", "Name", "Shares"])
        self.insider_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background: #1a1a1a;
                color: #ff6600;
                font-weight: bold;
                border: 1px solid #333;
                padding: 5px;
                font-size: 9pt;
            }
        """)
        self.insider_table.setStyleSheet("""
            QTableWidget {
                background: #000;
                color: #ccc;
                gridline-color: #333;
                font-size: 9pt;
            }
        """)
        self.insider_table.verticalHeader().setVisible(False)
        self.insider_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.insider_table)
        
        return group
    
    def create_peers_group(self) -> QGroupBox:
        """Create peers comparison group"""
        group = self.create_group("PEER COMPARISON")
        layout = QVBoxLayout(group)
        
        self.peers_label = QLabel("--")
        self.peers_label.setStyleSheet("color: #ccc; font-size: 10pt; padding: 5px;")
        self.peers_label.setWordWrap(True)
        layout.addWidget(self.peers_label)
        
        return group
    
    def update_data(self, symbol: str):
        """Fetch and display company info - ASYNC VERSION"""
        self.current_symbol = symbol
        
        # Update symbol label immediately
        self.symbol_label.setText(symbol)
        
        # Show loading state
        self.name_label.setText("⏳ Loading...")
        
        # Cancel previous loader if running
        if self.loader and self.loader.isRunning():
            self.loader.terminate()
            self.loader.wait()
        
        # Start background loading
        self.loader = CompanyInfoLoader(symbol, self.finnhub)
        self.loader.progress.connect(self.on_load_progress)
        self.loader.finished.connect(self.on_data_loaded)
        self.loader.error.connect(self.on_load_error)
        self.loader.start()
    
    def on_load_progress(self, message: str):
        """Update loading progress"""
        self.name_label.setText(message)
    
    def on_data_loaded(self, data: dict):
        """Handle loaded data"""
        # Update all UI sections
        self.update_top_bar(data.get('profile'), data.get('quote'))
        self.update_stats(data.get('metrics'), data.get('quote'))
        self.update_financials(data.get('metrics'))
        self.update_estimates(data.get('price_targets'))
        self.update_dividends(data.get('metrics'))
        self.update_ownership(data.get('metrics'))
        self.update_recommendations(data.get('recommendations'))
        self.update_price_targets(data.get('price_targets'))
        self.update_upgrades(data.get('upgrades'))
        self.update_earnings(data.get('earnings'))
        self.update_profile(data.get('profile'))
        self.update_insider(data.get('insider'))
        self.update_peers(data.get('peers'))
    
    def on_load_error(self, error: str):
        """Handle loading error"""
        self.name_label.setText(f"Error: {error}")
        self.name_label.setStyleSheet("color: #ff0000; font-size: 11pt;")
    
    def update_top_bar(self, profile, quote):
        """Update top bar with live price"""
        if profile:
            self.name_label.setText(profile.get('name', '--'))
            self.name_label.setStyleSheet("color: #ccc; font-size: 12pt;")
            
            # Market cap
            market_cap = profile.get('marketCapitalization', 0)
            if market_cap:
                self.market_cap_label.setText(f"Market Cap: ${market_cap:,.0f}M")
        
        if quote:
            current = quote.get('c', 0)
            change = quote.get('d', 0)
            change_pct = quote.get('dp', 0)
            
            self.price_label.setText(f"${current:.2f}")
            self.change_label.setText(f"{change:+.2f}")
            self.change_pct_label.setText(f"({change_pct:+.2f}%)")
            
            # Color coding
            color = "#00ff00" if change >= 0 else "#ff0000"
            self.change_label.setStyleSheet(f"color: {color}; font-size: 14pt; font-weight: bold;")
            self.change_pct_label.setStyleSheet(f"color: {color}; font-size: 14pt; font-weight: bold;")
    
    def update_stats(self, metrics, quote):
        """Update key statistics"""
        if not metrics:
            return
        
        metric_data = metrics.get('metric', {})
        
        self.pe_label.setText(f"P/E Ratio: {metric_data.get('peBasicExclExtraTTM', '--')}")
        self.eps_label.setText(f"EPS: ${metric_data.get('epsExclExtraItemsTTM', '--')}")
        self.beta_label.setText(f"Beta: {metric_data.get('beta', '--')}")
        self.week_52_high_label.setText(f"52-Week High: ${metric_data.get('52WeekHigh', '--')}")
        self.week_52_low_label.setText(f"52-Week Low: ${metric_data.get('52WeekLow', '--')}")
        
        if quote:
            volume = quote.get('v', 0)
            self.avg_volume_label.setText(f"Avg Volume: {volume:,.0f}")
    
    def update_financials(self, metrics):
        """Update financials"""
        if not metrics:
            return
        
        metric_data = metrics.get('metric', {})
        
        self.revenue_label.setText(f"Revenue (TTM): ${metric_data.get('revenueTTM', '--')}M")
        self.net_income_label.setText(f"Net Income (TTM): ${metric_data.get('netIncomeTTM', '--')}M")
        self.ebitda_label.setText(f"EBITDA: ${metric_data.get('ebitdaTTM', '--')}M")
        self.gross_margin_label.setText(f"Gross Margin: {metric_data.get('grossMarginTTM', '--')}%")
        self.operating_margin_label.setText(f"Operating Margin: {metric_data.get('operatingMarginTTM', '--')}%")
        self.profit_margin_label.setText(f"Profit Margin: {metric_data.get('netProfitMarginTTM', '--')}%")
    
    def update_estimates(self, price_targets):
        """Update analyst estimates"""
        if not price_targets:
            return
        
        self.target_price_label.setText(f"Target Price: ${price_targets.get('targetMean', '--'):.2f}")
        self.eps_estimate_label.setText(f"EPS Estimate: --")  # Not in this API
        self.revenue_estimate_label.setText(f"Revenue Est: --")  # Not in this API
    
    def update_dividends(self, metrics):
        """Update dividends info"""
        if not metrics:
            return
        
        metric_data = metrics.get('metric', {})
        
        dividend_yield = metric_data.get('dividendYieldIndicatedAnnual', '--')
        payout_ratio = metric_data.get('payoutRatioTTM', '--')
        
        self.dividend_yield_label.setText(f"Dividend Yield: {dividend_yield}%")
        self.payout_ratio_label.setText(f"Payout Ratio: {payout_ratio}%")
    
    def update_ownership(self, metrics):
        """Update ownership info"""
        if not metrics:
            return
        
        metric_data = metrics.get('metric', {})
        
        self.shares_outstanding_label.setText(f"Shares Outstanding: {metric_data.get('sharesOutstanding', '--')}M")
        self.float_shares_label.setText(f"Float: {metric_data.get('sharesFloat', '--')}M")
        self.insider_ownership_label.setText(f"Insider Ownership: --")  # Not in basic metrics
        self.institutional_label.setText(f"Institutional: --")  # Not in basic metrics
    
    def update_recommendations(self, recommendations):
        """Update analyst recommendations table"""
        if not recommendations:
            self.recommendations_table.setRowCount(0)
            return
        
        self.recommendations_table.setRowCount(len(recommendations))
        
        for row, rec in enumerate(recommendations):
            period = rec.get('period', '--')
            strong_buy = rec.get('strongBuy', 0)
            buy = rec.get('buy', 0)
            hold = rec.get('hold', 0)
            sell = rec.get('sell', 0)
            strong_sell = rec.get('strongSell', 0)
            
            self.recommendations_table.setItem(row, 0, QTableWidgetItem(period))
            self.recommendations_table.setItem(row, 1, QTableWidgetItem(str(strong_buy)))
            self.recommendations_table.setItem(row, 2, QTableWidgetItem(str(buy)))
            self.recommendations_table.setItem(row, 3, QTableWidgetItem(str(hold)))
            self.recommendations_table.setItem(row, 4, QTableWidgetItem(str(sell)))
            self.recommendations_table.setItem(row, 5, QTableWidgetItem(str(strong_sell)))
        
        self.recommendations_table.resizeColumnsToContents()
    
    def update_price_targets(self, price_targets):
        """Update price targets"""
        if not price_targets:
            return
        
        self.target_high_label.setText(f"Target High: ${price_targets.get('targetHigh', '--'):.2f}")
        self.target_median_label.setText(f"Target Median: ${price_targets.get('targetMedian', '--'):.2f}")
        self.target_low_label.setText(f"Target Low: ${price_targets.get('targetLow', '--'):.2f}")
        self.target_mean_label.setText(f"Target Mean: ${price_targets.get('targetMean', '--'):.2f}")
    
    def update_upgrades(self, upgrades):
        """Update upgrades/downgrades table"""
        if not upgrades:
            self.upgrades_table.setRowCount(0)
            return
        
        # Show last 10
        upgrades = upgrades[:10]
        self.upgrades_table.setRowCount(len(upgrades))
        
        for row, upg in enumerate(upgrades):
            date = upg.get('date', '--')
            firm = upg.get('company', '--')
            action = upg.get('action', '--')
            from_grade = upg.get('fromGrade', '--')
            to_grade = upg.get('toGrade', '--')
            
            self.upgrades_table.setItem(row, 0, QTableWidgetItem(date))
            self.upgrades_table.setItem(row, 1, QTableWidgetItem(firm))
            self.upgrades_table.setItem(row, 2, QTableWidgetItem(action))
            self.upgrades_table.setItem(row, 3, QTableWidgetItem(f"{from_grade} → {to_grade}"))
        
        self.upgrades_table.resizeColumnsToContents()
    
    def update_earnings(self, earnings):
        """Update earnings surprises table"""
        if not earnings:
            self.earnings_table.setRowCount(0)
            return
        
        self.earnings_table.setRowCount(len(earnings))
        
        for row, earn in enumerate(earnings):
            period = earn.get('period', '--')
            actual = earn.get('actual', 0)
            estimate = earn.get('estimate', 0)
            
            surprise = 0
            if estimate and estimate != 0:
                surprise = ((actual - estimate) / estimate) * 100
            
            self.earnings_table.setItem(row, 0, QTableWidgetItem(period))
            self.earnings_table.setItem(row, 1, QTableWidgetItem(f"${actual:.2f}"))
            self.earnings_table.setItem(row, 2, QTableWidgetItem(f"${estimate:.2f}"))
            
            surprise_item = QTableWidgetItem(f"{surprise:+.2f}%")
            surprise_item.setForeground(QColor("#00ff00" if surprise >= 0 else "#ff0000"))
            self.earnings_table.setItem(row, 3, surprise_item)
        
        self.earnings_table.resizeColumnsToContents()
    
    def update_profile(self, profile):
        """Update company profile"""
        if not profile:
            return
        
        # Load logo
        logo_url = profile.get('logo')
        if logo_url:
            try:
                response = requests.get(logo_url)
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.logo_label.setPixmap(pixmap.scaled(100, 60, Qt.AspectRatioMode.KeepAspectRatio))
            except:
                self.logo_label.setText("No Logo")
        
        self.industry_label.setText(f"Industry: {profile.get('finnhubIndustry', '--')}")
        self.sector_label.setText(f"Sector: --")  # Not in profile
        self.country_label.setText(f"Country: {profile.get('country', '--')}")
        self.exchange_label.setText(f"Exchange: {profile.get('exchange', '--')}")
        self.ipo_label.setText(f"IPO Date: {profile.get('ipo', '--')}")
    
    def update_insider(self, insider):
        """Update insider transactions table"""
        if not insider or not isinstance(insider, list):
            self.insider_table.setRowCount(0)
            return
        
        # Show last 10
        insider = insider[:10]
        self.insider_table.setRowCount(len(insider))
        
        for row, trans in enumerate(insider):
            date = trans.get('transactionDate', '--')
            name = trans.get('name', '--')
            shares = trans.get('share', 0)
            
            self.insider_table.setItem(row, 0, QTableWidgetItem(date))
            self.insider_table.setItem(row, 1, QTableWidgetItem(name))
            
            shares_item = QTableWidgetItem(f"{shares:,}")
            shares_item.setForeground(QColor("#00ff00" if shares > 0 else "#ff0000"))
            self.insider_table.setItem(row, 2, shares_item)
        
        self.insider_table.resizeColumnsToContents()
    
    def update_peers(self, peers):
        """Update peers comparison"""
        if not peers or not isinstance(peers, list):
            self.peers_label.setText("--")
            return
        
        peers_text = ", ".join(peers[:8])  # Show first 8
        self.peers_label.setText(peers_text)