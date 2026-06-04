"""
Company Fundamentals Viewer
Real-time company information display
"""

import yfinance as yf
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from typing import Optional, Dict
import pandas as pd


class FundamentalsViewer:
    """
    Display company fundamental data (balance sheet, income statement, etc.)
    """
    
    def __init__(self):
        self.console = Console()
    
    def view_company_overview(self, symbol: str):
        """
        Display comprehensive company overview
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL', 'MSFT')
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'longName' not in info:
                self.console.print(f"[red]No data found for {symbol}[/red]")
                return
            
            # Company Header
            self._display_header(symbol, info)
            
            # Main sections
            self._display_description(info)
            self._display_key_stats(info)
            self._display_financial_ratios(info)
            self._display_profitability(info)
            
        except Exception as e:
            self.console.print(f"[red]Error fetching data: {e}[/red]")
    
    def _display_header(self, symbol: str, info: Dict):
        """Display company header with name and basic info"""
        name = info.get('longName', symbol)
        sector = info.get('sector', 'N/A')
        industry = info.get('industry', 'N/A')
        country = info.get('country', 'N/A')
        
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        prev_close = info.get('previousClose', 0)
        
        if current_price and prev_close:
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100
            price_color = "green" if change >= 0 else "red"
            arrow = "▲" if change >= 0 else "▼"
            
            price_str = f"${current_price:,.2f} {arrow} ${abs(change):.2f} ({change_pct:+.2f}%)"
        else:
            price_str = f"${current_price:,.2f}" if current_price else "N/A"
            price_color = "white"
        
        header = f"""[bold cyan]{name}[/bold cyan] ([yellow]{symbol}[/yellow])
[dim]{sector} • {industry} • {country}[/dim]
[{price_color}]{price_str}[/{price_color}]"""
        
        self.console.print(Panel(header, border_style="cyan"))
    
    def _display_description(self, info: Dict):
        """Display company description"""
        description = info.get('longBusinessSummary', 'No description available')
        
        # Truncate if too long
        if len(description) > 500:
            description = description[:500] + "..."
        
        self.console.print("\n[bold]📄 COMPANY DESCRIPTION[/bold]")
        self.console.print(Panel(description, border_style="blue"))
    
    def _display_key_stats(self, info: Dict):
        """Display key statistics"""
        self.console.print("\n[bold]📊 KEY STATISTICS[/bold]")
        
        # Create two-column layout
        table1 = Table(show_header=False, box=None)
        table1.add_column("Metric", style="cyan")
        table1.add_column("Value", style="white")
        
        # Market data
        market_cap = info.get('marketCap', 0)
        table1.add_row("Market Cap", self._format_large_number(market_cap))
        table1.add_row("Enterprise Value", self._format_large_number(info.get('enterpriseValue', 0)))
        table1.add_row("Shares Outstanding", self._format_large_number(info.get('sharesOutstanding', 0)))
        table1.add_row("52 Week High", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")
        table1.add_row("52 Week Low", f"${info.get('fiftyTwoWeekLow', 0):,.2f}")
        
        table2 = Table(show_header=False, box=None)
        table2.add_column("Metric", style="cyan")
        table2.add_column("Value", style="white")
        
        # Trading data
        table2.add_row("Volume", self._format_large_number(info.get('volume', 0)))
        table2.add_row("Avg Volume (10d)", self._format_large_number(info.get('averageVolume10days', 0)))
        table2.add_row("Beta", f"{info.get('beta', 0):.2f}")
        table2.add_row("Dividend Yield", f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else "N/A")
        table2.add_row("Ex-Dividend Date", self._format_timestamp(info.get('exDividendDate')))
        
        self.console.print(Columns([table1, table2]))
    
    def _display_financial_ratios(self, info: Dict):
        """Display financial ratios"""
        self.console.print("\n[bold]💰 VALUATION & RATIOS[/bold]")
        
        table = Table(show_header=True, box=None)
        table.add_column("Metric", style="cyan", width=30)
        table.add_column("Value", style="white", width=15)
        table.add_column("Metric", style="cyan", width=30)
        table.add_column("Value", style="white", width=15)
        
        pe_ratio = info.get('trailingPE', info.get('forwardPE', 0))
        pb_ratio = info.get('priceToBook', 0)
        ps_ratio = info.get('priceToSalesTrailing12Months', 0)
        
        table.add_row(
            "P/E Ratio (TTM)", 
            f"{pe_ratio:.2f}" if pe_ratio else "N/A",
            "Forward P/E",
            f"{info.get('forwardPE', 0):.2f}" if info.get('forwardPE') else "N/A"
        )
        
        table.add_row(
            "Price/Book",
            f"{pb_ratio:.2f}" if pb_ratio else "N/A",
            "Price/Sales",
            f"{ps_ratio:.2f}" if ps_ratio else "N/A"
        )
        
        table.add_row(
            "PEG Ratio",
            f"{info.get('pegRatio', 0):.2f}" if info.get('pegRatio') else "N/A",
            "EV/EBITDA",
            f"{info.get('enterpriseToEbitda', 0):.2f}" if info.get('enterpriseToEbitda') else "N/A"
        )
        
        table.add_row(
            "Debt/Equity",
            f"{info.get('debtToEquity', 0):.2f}" if info.get('debtToEquity') else "N/A",
            "Current Ratio",
            f"{info.get('currentRatio', 0):.2f}" if info.get('currentRatio') else "N/A"
        )
        
        self.console.print(table)
    
    def _display_profitability(self, info: Dict):
        """Display profitability metrics"""
        self.console.print("\n[bold]📈 PROFITABILITY & MARGINS[/bold]")
        
        table = Table(show_header=True, box=None)
        table.add_column("Metric", style="cyan", width=30)
        table.add_column("Value", style="white", width=15)
        table.add_column("Metric", style="cyan", width=30)
        table.add_column("Value", style="white", width=15)
        
        profit_margin = info.get('profitMargins', 0)
        operating_margin = info.get('operatingMargins', 0)
        gross_margin = info.get('grossMargins', 0)
        
        table.add_row(
            "Gross Margin",
            f"{gross_margin * 100:.2f}%" if gross_margin else "N/A",
            "Operating Margin",
            f"{operating_margin * 100:.2f}%" if operating_margin else "N/A"
        )
        
        table.add_row(
            "Profit Margin",
            f"{profit_margin * 100:.2f}%" if profit_margin else "N/A",
            "ROE",
            f"{info.get('returnOnEquity', 0) * 100:.2f}%" if info.get('returnOnEquity') else "N/A"
        )
        
        table.add_row(
            "ROA",
            f"{info.get('returnOnAssets', 0) * 100:.2f}%" if info.get('returnOnAssets') else "N/A",
            "Revenue Growth",
            f"{info.get('revenueGrowth', 0) * 100:+.2f}%" if info.get('revenueGrowth') else "N/A"
        )
        
        table.add_row(
            "Earnings Growth",
            f"{info.get('earningsGrowth', 0) * 100:+.2f}%" if info.get('earningsGrowth') else "N/A",
            "Free Cash Flow",
            self._format_large_number(info.get('freeCashflow', 0))
        )
        
        self.console.print(table)
    
    def view_balance_sheet(self, symbol: str):
        """
        Display balance sheet
        
        Args:
            symbol: Stock ticker
        """
        try:
            ticker = yf.Ticker(symbol)
            bs = ticker.balance_sheet
            
            if bs is None or bs.empty:
                self.console.print(f"[red]No balance sheet data for {symbol}[/red]")
                return
            
            self.console.print(f"\n[bold cyan]📊 BALANCE SHEET - {symbol}[/bold cyan]\n")
            
            # Get most recent year
            latest = bs.iloc[:, 0]
            
            # Assets section
            self.console.print("[bold]ASSETS[/bold]")
            table = Table(show_header=False, box=None)
            table.add_column("Item", style="cyan", width=40)
            table.add_column("Amount", style="white", width=20, justify="right")
            
            assets = [
                ("Total Assets", "TotalAssets"),
                ("Current Assets", "CurrentAssets"),
                ("Cash & Equivalents", "CashAndCashEquivalents"),
                ("Accounts Receivable", "AccountsReceivable"),
                ("Inventory", "Inventory"),
                ("Property, Plant & Equipment", "PropertyPlantEquipment"),
                ("Goodwill", "Goodwill"),
                ("Intangible Assets", "IntangibleAssets"),
            ]
            
            for name, key in assets:
                value = latest.get(key, 0)
                if pd.notna(value) and value != 0:
                    table.add_row(name, self._format_large_number(value))
            
            self.console.print(table)
            
            # Liabilities section
            self.console.print("\n[bold]LIABILITIES & EQUITY[/bold]")
            table2 = Table(show_header=False, box=None)
            table2.add_column("Item", style="cyan", width=40)
            table2.add_column("Amount", style="white", width=20, justify="right")
            
            liabilities = [
                ("Total Liabilities", "TotalLiabilitiesNetMinorityInterest"),
                ("Current Liabilities", "CurrentLiabilities"),
                ("Accounts Payable", "AccountsPayable"),
                ("Long Term Debt", "LongTermDebt"),
                ("Total Equity", "TotalEquityGrossMinorityInterest"),
                ("Retained Earnings", "RetainedEarnings"),
                ("Treasury Stock", "TreasuryStock"),
            ]
            
            for name, key in liabilities:
                value = latest.get(key, 0)
                if pd.notna(value) and value != 0:
                    table2.add_row(name, self._format_large_number(value))
            
            self.console.print(table2)
            
        except Exception as e:
            self.console.print(f"[red]Error fetching balance sheet: {e}[/red]")
    
    def view_income_statement(self, symbol: str):
        """
        Display income statement
        
        Args:
            symbol: Stock ticker
        """
        try:
            ticker = yf.Ticker(symbol)
            income = ticker.income_stmt
            
            if income is None or income.empty:
                self.console.print(f"[red]No income statement data for {symbol}[/red]")
                return
            
            self.console.print(f"\n[bold cyan]💵 INCOME STATEMENT - {symbol}[/bold cyan]\n")
            
            # Get most recent year
            latest = income.iloc[:, 0]
            
            table = Table(show_header=False, box=None)
            table.add_column("Item", style="cyan", width=40)
            table.add_column("Amount", style="white", width=20, justify="right")
            
            items = [
                ("Total Revenue", "TotalRevenue"),
                ("Cost of Revenue", "CostOfRevenue"),
                ("Gross Profit", "GrossProfit"),
                ("Operating Expense", "OperatingExpense"),
                ("Operating Income", "OperatingIncome"),
                ("Interest Expense", "InterestExpense"),
                ("Pretax Income", "PretaxIncome"),
                ("Tax Provision", "TaxProvision"),
                ("Net Income", "NetIncome"),
                ("EBITDA", "EBITDA"),
                ("Basic EPS", "BasicEPS"),
                ("Diluted EPS", "DilutedEPS"),
            ]
            
            for name, key in items:
                value = latest.get(key, 0)
                if pd.notna(value) and value != 0:
                    if 'EPS' in key:
                        table.add_row(name, f"${value:.2f}")
                    else:
                        table.add_row(name, self._format_large_number(value))
            
            self.console.print(table)
            
        except Exception as e:
            self.console.print(f"[red]Error fetching income statement: {e}[/red]")
    
    def view_cash_flow(self, symbol: str):
        """
        Display cash flow statement
        
        Args:
            symbol: Stock ticker
        """
        try:
            ticker = yf.Ticker(symbol)
            cf = ticker.cashflow
            
            if cf is None or cf.empty:
                self.console.print(f"[red]No cash flow data for {symbol}[/red]")
                return
            
            self.console.print(f"\n[bold cyan]💰 CASH FLOW STATEMENT - {symbol}[/bold cyan]\n")
            
            # Get most recent year
            latest = cf.iloc[:, 0]
            
            # Operating activities
            self.console.print("[bold]OPERATING ACTIVITIES[/bold]")
            table1 = Table(show_header=False, box=None)
            table1.add_column("Item", style="cyan", width=40)
            table1.add_column("Amount", style="white", width=20, justify="right")
            
            operating = [
                ("Operating Cash Flow", "OperatingCashFlow"),
                ("Cash Flow from Operations", "CashFlowFromContinuingOperatingActivities"),
            ]
            
            for name, key in operating:
                value = latest.get(key, 0)
                if pd.notna(value) and value != 0:
                    table1.add_row(name, self._format_large_number(value))
            
            self.console.print(table1)
            
            # Investing activities
            self.console.print("\n[bold]INVESTING ACTIVITIES[/bold]")
            table2 = Table(show_header=False, box=None)
            table2.add_column("Item", style="cyan", width=40)
            table2.add_column("Amount", style="white", width=20, justify="right")
            
            investing = [
                ("Investing Cash Flow", "InvestingCashFlow"),
                ("Capital Expenditure", "CapitalExpenditure"),
            ]
            
            for name, key in investing:
                value = latest.get(key, 0)
                if pd.notna(value) and value != 0:
                    table2.add_row(name, self._format_large_number(value))
            
            self.console.print(table2)
            
            # Financing activities
            self.console.print("\n[bold]FINANCING ACTIVITIES[/bold]")
            table3 = Table(show_header=False, box=None)
            table3.add_column("Item", style="cyan", width=40)
            table3.add_column("Amount", style="white", width=20, justify="right")
            
            financing = [
                ("Financing Cash Flow", "FinancingCashFlow"),
                ("Free Cash Flow", "FreeCashFlow"),
            ]
            
            for name, key in financing:
                value = latest.get(key, 0)
                if pd.notna(value) and value != 0:
                    table3.add_row(name, self._format_large_number(value))
            
            self.console.print(table3)
            
        except Exception as e:
            self.console.print(f"[red]Error fetching cash flow: {e}[/red]")
    
    def _format_large_number(self, num) -> str:
        """Format large numbers with B/M/K suffixes"""
        if pd.isna(num) or num == 0:
            return "N/A"
        
        num = float(num)
        if abs(num) >= 1e12:
            return f"${num/1e12:,.2f}T"
        elif abs(num) >= 1e9:
            return f"${num/1e9:,.2f}B"
        elif abs(num) >= 1e6:
            return f"${num/1e6:,.2f}M"
        elif abs(num) >= 1e3:
            return f"${num/1e3:,.2f}K"
        else:
            return f"${num:,.2f}"
    
    def _format_timestamp(self, ts) -> str:
        """Format timestamp to readable date"""
        if pd.isna(ts) or ts is None:
            return "N/A"
        
        if isinstance(ts, (int, float)):
            import datetime
            date = datetime.datetime.fromtimestamp(ts)
            return date.strftime("%Y-%m-%d")
        
        return str(ts)


if __name__ == "__main__":
    # Test
    viewer = FundamentalsViewer()
    viewer.view_company_overview("AAPL")
    input("\nPress Enter to continue...")
    viewer.view_balance_sheet("AAPL")
    input("\nPress Enter to continue...")
    viewer.view_income_statement("AAPL")
    input("\nPress Enter to continue...")
    viewer.view_cash_flow("AAPL")