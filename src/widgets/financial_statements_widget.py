"""Financial Statements Widget - Balance Sheet, Income Statement, Cash Flow"""

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QTableWidget, QTableWidgetItem, QComboBox, QPushButton, QStackedWidget
)

from src.api.finnhub_client import FinnhubClient


class FinancialsLoader(QThread):
    """Background thread for loading financial statements"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, symbol: str, freq: str, finnhub_client):
        super().__init__()
        self.symbol = symbol
        self.freq = freq
        self.finnhub = finnhub_client
    
    def run(self):
        """Load financial statements in background"""
        try:
            self.progress.emit(f"Loading {self.freq} financials for {self.symbol}...")
            data = self.finnhub.get_financials_reported(self.symbol, freq=self.freq)
            
            if data and 'data' in data:
                self.progress.emit(f"Loaded {len(data['data'])} reports")
            
            self.finished.emit(data)
            
        except Exception as e:
            self.error.emit(str(e))


class FinancialStatementsWidget(QWidget):
    """Financial Statements Widget - Balance Sheet, Income Statement, Cash Flow"""
    
    def __init__(self):
        super().__init__()
        self.finnhub = FinnhubClient()
        self.current_symbol = None
        self.loader = None  # Background loader
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        
        # Title bar with period selector
        title_bar = QWidget()
        title_bar.setStyleSheet("background: #1a1a1a; padding: 10px;")
        title_bar_layout = QHBoxLayout(title_bar)
        
        title = QLabel("FINANCIAL STATEMENTS")
        title.setStyleSheet("color: #ff6600; font-size: 16pt; font-weight: bold;")
        title_bar_layout.addWidget(title)
        
        title_bar_layout.addStretch()
        
        # Period selector
        period_label = QLabel("Period:")
        period_label.setStyleSheet("color: #ccc; font-size: 10pt;")
        title_bar_layout.addWidget(period_label)
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Annual", "Quarterly"])
        self.period_combo.setStyleSheet("""
            QComboBox {
                background: #000;
                color: #ff6600;
                border: 2px solid #ff6600;
                padding: 5px 10px;
                font-size: 10pt;
                font-weight: bold;
            }
            QComboBox:hover {
                background: #1a1a1a;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #000;
                color: #ff6600;
                selection-background-color: #ff6600;
                selection-color: #000;
            }
        """)
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        title_bar_layout.addWidget(self.period_combo)
        
        # Periods count selector
        periods_count_label = QLabel("Periods:")
        periods_count_label.setStyleSheet("color: #ccc; font-size: 10pt; margin-left: 20px;")
        title_bar_layout.addWidget(periods_count_label)
        
        self.periods_count_combo = QComboBox()
        self.periods_count_combo.addItems(["4", "8", "12", "16"])
        self.periods_count_combo.setCurrentText("8")  # Default 8 periods
        self.periods_count_combo.setStyleSheet("""
            QComboBox {
                background: #000;
                color: #ff6600;
                border: 2px solid #ff6600;
                padding: 5px 10px;
                font-size: 10pt;
                font-weight: bold;
                min-width: 60px;
            }
            QComboBox:hover {
                background: #1a1a1a;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #000;
                color: #ff6600;
                selection-background-color: #ff6600;
                selection-color: #000;
            }
        """)
        self.periods_count_combo.currentTextChanged.connect(self.on_periods_count_changed)
        title_bar_layout.addWidget(self.periods_count_combo)
        
        main_layout.addWidget(title_bar)
        
        # Toggle bar - 3 buttons to switch between statements
        toggle_bar = QWidget()
        toggle_bar.setStyleSheet("background: #0a0a0a; padding: 10px;")
        toggle_bar_layout = QHBoxLayout(toggle_bar)
        toggle_bar_layout.setSpacing(10)
        
        # Add label
        view_label = QLabel("View:")
        view_label.setStyleSheet("color: #ff6600; font-size: 11pt; font-weight: bold;")
        toggle_bar_layout.addWidget(view_label)
        
        # Balance Sheet button
        self.bs_btn = QPushButton("BALANCE SHEET")
        self.bs_btn.setCheckable(True)
        self.bs_btn.setChecked(True)  # Default selected
        self.bs_btn.clicked.connect(lambda: self.show_statement(0))
        
        # Income Statement button
        self.is_btn = QPushButton("INCOME STATEMENT")
        self.is_btn.setCheckable(True)
        self.is_btn.clicked.connect(lambda: self.show_statement(1))
        
        # Cash Flow button
        self.cf_btn = QPushButton("CASH FLOW")
        self.cf_btn.setCheckable(True)
        self.cf_btn.clicked.connect(lambda: self.show_statement(2))
        
        # Style for toggle buttons
        button_style = """
            QPushButton {
                background: #1a1a1a;
                color: #ccc;
                border: 2px solid #333;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #2a2a2a;
                border-color: #ff6600;
            }
            QPushButton:checked {
                background: #ff6600;
                color: #000;
                border-color: #ff8800;
            }
        """
        self.bs_btn.setStyleSheet(button_style)
        self.is_btn.setStyleSheet(button_style)
        self.cf_btn.setStyleSheet(button_style)
        
        toggle_bar_layout.addWidget(self.bs_btn)
        toggle_bar_layout.addWidget(self.is_btn)
        toggle_bar_layout.addWidget(self.cf_btn)
        toggle_bar_layout.addStretch()
        
        main_layout.addWidget(toggle_bar)
        
        # Stacked widget to hold 3 tables (only 1 visible at a time)
        self.stacked_tables = QStackedWidget()
        
        # Create 3 table widgets
        self.balance_sheet_table = self.create_statement_table()
        self.income_statement_table = self.create_statement_table()
        self.cash_flow_table = self.create_statement_table()
        
        # Add to stacked widget
        self.stacked_tables.addWidget(self.balance_sheet_table)
        self.stacked_tables.addWidget(self.income_statement_table)
        self.stacked_tables.addWidget(self.cash_flow_table)
        
        # Set initial view
        self.stacked_tables.setCurrentIndex(0)
        
        main_layout.addWidget(self.stacked_tables, 1)  # Stretch to fill
        
        # Store buttons for toggle management
        self.toggle_buttons = [self.bs_btn, self.is_btn, self.cf_btn]
    
    def show_statement(self, index: int):
        """Show selected statement and update button states"""
        # Update button states (only one checked)
        for i, btn in enumerate(self.toggle_buttons):
            btn.setChecked(i == index)
        
        # Switch to selected table
        self.stacked_tables.setCurrentIndex(index)
        
    
    def create_statement_group(self, title: str) -> QGroupBox:
        """Create styled group box"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                color: #ff6600;
                font-weight: bold;
                font-size: 12pt;
                border: 2px solid #ff6600;
                border-radius: 5px;
                margin-top: 15px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        return group
    
    def create_statement_table(self) -> QTableWidget:
        """Create styled table for financial data with default 8 periods"""
        return self.create_statement_table_with_columns(8)
    
    def create_statement_table_with_columns(self, periods_count: int) -> QTableWidget:
        """Create styled table for financial data with specified column count"""
        table = QTableWidget()
        col_count = 1 + periods_count  # Item + periods
        table.setColumnCount(col_count)
        
        # Create default headers
        headers = ["Item"] + [f"P-{i}" for i in range(periods_count)]
        table.setHorizontalHeaderLabels(headers)
        
        # Set minimum column widths
        table.setColumnWidth(0, 300)  # Item column wider
        for i in range(1, col_count):
            table.setColumnWidth(i, 120)  # Value columns
        
        # Enable stretching for last section
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background: #1a1a1a;
                color: #ff6600;
                font-weight: bold;
                border: 1px solid #333;
                padding: 8px;
                font-size: 10pt;
            }
        """)
        table.setStyleSheet("""
            QTableWidget {
                background: #000;
                color: #ccc;
                gridline-color: #333;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background: #ff6600;
                color: #000;
            }
        """)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)  # Hide row numbers
        return table
    
    def on_period_changed(self, text: str):
        """Handle period change"""
        if self.current_symbol:
            self.update_data(self.current_symbol)
    
    def on_periods_count_changed(self, text: str):
        """Handle periods count change"""
        if self.current_symbol and hasattr(self, 'reports') and self.reports:
            # Re-render tables with new period count
            periods_count = int(text)
            reports = self.reports[:periods_count]
            
            # Recreate tables with new column count
            self.recreate_tables(periods_count)
            
            # Update headers and populate
            self.update_table_headers(reports)
            self.populate_balance_sheet(reports)
            self.populate_income_statement(reports)
            self.populate_cash_flow(reports)
    
    def recreate_tables(self, periods_count: int):
        """Recreate tables with new column count"""
        # Store current view index
        current_index = self.stacked_tables.currentIndex()
        
        # Remove old tables
        while self.stacked_tables.count() > 0:
            widget = self.stacked_tables.widget(0)
            self.stacked_tables.removeWidget(widget)
            widget.deleteLater()
        
        # Create new tables with updated column count
        self.balance_sheet_table = self.create_statement_table_with_columns(periods_count)
        self.income_statement_table = self.create_statement_table_with_columns(periods_count)
        self.cash_flow_table = self.create_statement_table_with_columns(periods_count)
        
        # Add to stacked widget
        self.stacked_tables.addWidget(self.balance_sheet_table)
        self.stacked_tables.addWidget(self.income_statement_table)
        self.stacked_tables.addWidget(self.cash_flow_table)
        
        # Restore view
        self.stacked_tables.setCurrentIndex(current_index)
    
    def update_data(self, symbol: str):
        """Fetch and display financial statements - ASYNC VERSION"""
        self.current_symbol = symbol
        freq = 'annual' if self.period_combo.currentText() == 'Annual' else 'quarterly'
        
        # Show loading state
        for table in [self.balance_sheet_table, self.income_statement_table, self.cash_flow_table]:
            table.setRowCount(1)
            loading_item = QTableWidgetItem("⏳ Loading financial data...")
            loading_item.setForeground(QColor("#ff6600"))
            table.setItem(0, 0, loading_item)
            table.setSpan(0, 0, 1, 5)
        
        # Cancel previous loader if running
        if self.loader and self.loader.isRunning():
            self.loader.terminate()
            self.loader.wait()
        
        # Start background loading
        self.loader = FinancialsLoader(symbol, freq, self.finnhub)
        self.loader.progress.connect(self.on_load_progress)
        self.loader.finished.connect(self.on_data_loaded)
        self.loader.error.connect(self.on_load_error)
        self.loader.start()
    
    def on_load_progress(self, message: str):
        """Update loading progress"""
        for table in [self.balance_sheet_table, self.income_statement_table, self.cash_flow_table]:
            if table.rowCount() > 0:
                item = table.item(0, 0)
                if item:
                    item.setText(message)
    
    def on_data_loaded(self, data: dict):
        """Handle loaded data"""
        if not data or 'data' not in data:
            self.show_no_data()
            return
        
        reports = data['data']
        
        if not reports:
            self.show_no_data()
            return
        
        # Store all reports (unfiltered)
        self.reports = reports
        
        # Get selected periods count
        periods_count = int(self.periods_count_combo.currentText())
        reports_to_show = reports[:periods_count]
        
        # Recreate tables with correct column count
        self.recreate_tables(periods_count)
        
        # Update table headers based on report metadata
        self.update_table_headers(reports_to_show)
        
        # Parse and display each statement
        self.populate_balance_sheet(reports_to_show)
        self.populate_income_statement(reports_to_show)
        self.populate_cash_flow(reports_to_show)
        
    
    def update_table_headers(self, reports: list):
        """Update table headers based on report metadata"""
        # Generate headers from report data
        headers = ["Item"]
        
        for i, report in enumerate(reports):
            year = report.get('year', '')
            quarter = report.get('quarter', None)
            form = report.get('form', '')
            
            if quarter and quarter > 0:
                # Quarterly report
                label = f"Q{quarter} {year}"
            else:
                # Annual report
                label = str(year) if year else f"P-{i}"
            
            headers.append(label)
        
        # Update all three tables
        for table in [self.balance_sheet_table, self.income_statement_table, self.cash_flow_table]:
            # Only set headers up to the number of columns in the table
            num_cols = min(len(headers), table.columnCount())
            table.setHorizontalHeaderLabels(headers[:num_cols])
    
    def on_load_error(self, error: str):
        """Handle loading error"""
        self.show_error(error)
    
    def populate_balance_sheet(self, reports: list):
        """Populate balance sheet table"""
        bs_items = [
            # Assets
            ("Assets", "bs", "us-gaap_Assets", True),
            ("  Current Assets", "bs", "us-gaap_AssetsCurrent", False),
            ("    Cash & Equivalents", "bs", "us-gaap_CashAndCashEquivalentsAtCarryingValue", False),
            ("    Short-term Investments", "bs", "us-gaap_MarketableSecuritiesCurrent", False),
            ("    Accounts Receivable", "bs", "us-gaap_AccountsReceivableNetCurrent", False),
            ("    Inventory", "bs", "us-gaap_InventoryNet", False),
            ("  Non-Current Assets", "bs", "us-gaap_AssetsNoncurrent", False),
            ("    Property, Plant & Equipment", "bs", "us-gaap_PropertyPlantAndEquipmentNet", False),
            ("    Intangible Assets", "bs", "us-gaap_IntangibleAssetsNetExcludingGoodwill", False),
            ("    Goodwill", "bs", "us-gaap_Goodwill", False),
            ("", "", "", True),  # Separator
            # Liabilities
            ("Liabilities", "bs", "us-gaap_Liabilities", True),
            ("  Current Liabilities", "bs", "us-gaap_LiabilitiesCurrent", False),
            ("    Accounts Payable", "bs", "us-gaap_AccountsPayableCurrent", False),
            ("    Short-term Debt", "bs", "us-gaap_ShortTermBorrowings", False),
            ("  Non-Current Liabilities", "bs", "us-gaap_LiabilitiesNoncurrent", False),
            ("    Long-term Debt", "bs", "us-gaap_LongTermDebtNoncurrent", False),
            ("", "", "", True),  # Separator
            # Equity
            ("Shareholders' Equity", "bs", "us-gaap_StockholdersEquity", True),
            ("  Common Stock", "bs", "us-gaap_CommonStockValue", False),
            ("  Retained Earnings", "bs", "us-gaap_RetainedEarningsAccumulatedDeficit", False),
        ]
        
        self.populate_table(self.balance_sheet_table, bs_items, reports)
    
    def populate_income_statement(self, reports: list):
        """Populate income statement table"""
        is_items = [
            ("Revenue", "ic", "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax", True),
            ("  Net Sales", "ic", "us-gaap_SalesRevenueNet", False),
            ("", "", "", True),
            ("Cost of Revenue", "ic", "us-gaap_CostOfGoodsAndServicesSold", True),
            ("", "", "", True),
            ("Gross Profit", "ic", "us-gaap_GrossProfit", True),
            ("", "", "", True),
            ("Operating Expenses", "ic", "us-gaap_OperatingExpenses", True),
            ("  R&D", "ic", "us-gaap_ResearchAndDevelopmentExpense", False),
            ("  SG&A", "ic", "us-gaap_SellingGeneralAndAdministrativeExpense", False),
            ("", "", "", True),
            ("Operating Income", "ic", "us-gaap_OperatingIncomeLoss", True),
            ("", "", "", True),
            ("Interest Expense", "ic", "us-gaap_InterestExpense", False),
            ("Other Income/Expense", "ic", "us-gaap_OtherNonoperatingIncomeExpense", False),
            ("", "", "", True),
            ("Income Before Tax", "ic", "us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest", True),
            ("Income Tax Expense", "ic", "us-gaap_IncomeTaxExpenseBenefit", False),
            ("", "", "", True),
            ("Net Income", "ic", "us-gaap_NetIncomeLoss", True),
            ("", "", "", True),
            ("EPS (Basic)", "ic", "us-gaap_EarningsPerShareBasic", True),
            ("EPS (Diluted)", "ic", "us-gaap_EarningsPerShareDiluted", True),
        ]
        
        self.populate_table(self.income_statement_table, is_items, reports)
    
    def populate_cash_flow(self, reports: list):
        """Populate cash flow table"""
        cf_items = [
            ("Operating Activities", "cf", "us-gaap_NetCashProvidedByUsedInOperatingActivities", True),
            ("  Net Income", "cf", "us-gaap_NetIncomeLoss", False),
            ("  Depreciation & Amortization", "cf", "us-gaap_DepreciationDepletionAndAmortization", False),
            ("  Stock-based Compensation", "cf", "us-gaap_ShareBasedCompensation", False),
            ("  Changes in Working Capital", "cf", "us-gaap_IncreaseDecreaseInOperatingCapital", False),
            ("", "", "", True),
            ("Investing Activities", "cf", "us-gaap_NetCashProvidedByUsedInInvestingActivities", True),
            ("  Capital Expenditures", "cf", "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment", False),
            ("  Acquisitions", "cf", "us-gaap_PaymentsToAcquireBusinessesNetOfCashAcquired", False),
            ("  Investment Purchases", "cf", "us-gaap_PaymentsToAcquireInvestments", False),
            ("", "", "", True),
            ("Financing Activities", "cf", "us-gaap_NetCashProvidedByUsedInFinancingActivities", True),
            ("  Dividends Paid", "cf", "us-gaap_PaymentsOfDividends", False),
            ("  Stock Repurchases", "cf", "us-gaap_PaymentsForRepurchaseOfCommonStock", False),
            ("  Debt Issuance", "cf", "us-gaap_ProceedsFromIssuanceOfLongTermDebt", False),
            ("  Debt Repayment", "cf", "us-gaap_RepaymentsOfLongTermDebt", False),
            ("", "", "", True),
            ("Net Change in Cash", "cf", "us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect", True),
        ]
        
        self.populate_table(self.cash_flow_table, cf_items, reports)
    
    def populate_table(self, table: QTableWidget, items: list, reports: list):
        """Generic table population"""
        table.setRowCount(len(items))
        
        # Use all provided reports (no hardcoded limit)
        num_periods = len(reports)
        
        for row, (label, statement, key, is_bold) in enumerate(items):
            # Item name
            item = QTableWidgetItem(label)
            if is_bold:
                font = QFont()
                font.setBold(True)
                item.setFont(font)
                item.setForeground(QColor("#ff6600"))
            table.setItem(row, 0, item)
            
            # Values for each period (no limit, use all reports)
            for col, report in enumerate(reports, start=1):
                if not label:  # Separator row
                    continue
                
                try:
                    # Navigate through report structure
                    report_data = report.get('report', {})
                    
                    if not report_data:
                        table.setItem(row, col, QTableWidgetItem("--"))
                        continue
                    
                    statement_data = report_data.get(statement, [])
                    
                    if not statement_data:
                        table.setItem(row, col, QTableWidgetItem("--"))
                        continue
                    
                    value = None
                    # Try to find the value by concept
                    if isinstance(statement_data, list):
                        for item_data in statement_data:
                            if isinstance(item_data, dict) and item_data.get('concept') == key:
                                value = item_data.get('value')
                                break
                    
                    if value is not None:
                        # Format as millions
                        try:
                            value_millions = float(value) / 1_000_000
                            value_text = f"${value_millions:,.1f}M"
                            
                            # Color coding
                            color = "#00ff00" if value_millions >= 0 else "#ff0000"
                            
                            value_item = QTableWidgetItem(value_text)
                            value_item.setForeground(QColor(color))
                            if is_bold:
                                font = QFont()
                                font.setBold(True)
                                value_item.setFont(font)
                            table.setItem(row, col, value_item)
                        except (ValueError, TypeError) as e:
                            table.setItem(row, col, QTableWidgetItem("--"))
                    else:
                        table.setItem(row, col, QTableWidgetItem("--"))
                        
                except Exception as e:
                    table.setItem(row, col, QTableWidgetItem("--"))
        
        # Adjust column widths dynamically based on table column count
        num_cols = table.columnCount()
        table.setColumnWidth(0, 300)  # Item column
        for i in range(1, num_cols):
            table.setColumnWidth(i, 120)  # Value columns
        
        # Allow horizontal scrolling if needed
        table.horizontalHeader().setStretchLastSection(True)
    
    def show_no_data(self):
        """Show no data message"""
        for table in [self.balance_sheet_table, self.income_statement_table, self.cash_flow_table]:
            table.setRowCount(1)
            item = QTableWidgetItem("No financial data available")
            item.setForeground(QColor("#ff6600"))
            table.setItem(0, 0, item)
            table.setSpan(0, 0, 1, table.columnCount())
    
    def show_error(self, error: str):
        """Show error message"""
        for table in [self.balance_sheet_table, self.income_statement_table, self.cash_flow_table]:
            table.setRowCount(1)
            item = QTableWidgetItem(f"Error: {error}")
            item.setForeground(QColor("#ff0000"))
            table.setItem(0, 0, item)
            table.setSpan(0, 0, 1, table.columnCount())