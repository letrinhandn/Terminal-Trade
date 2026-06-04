"""
Tab-based Terminal UI with intelligent navigation.
Supports multiple asset classes, data sources, and expandable features.
"""

# Standard library imports
import logging
import sys
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Third-party imports
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Local imports - Config
from config.settings import is_api_configured

# Local imports - Data
from data.data_loader import load_data

# Local imports - Strategies
from strategies.macd_advanced import (
    MACDAdvancedStrategy,
    MACDAggressive,
    MACDConservative
)
from strategies.macd_strategy import MACDStrategy
from strategies.options_strategies import (
    BearPutSpread,
    BullCallSpread,
    CoveredCall,
    IronCondor,
    LongStraddle,
    ProtectivePut
)

# Local imports - Backtest & Metrics
from backtest.engine import BacktestEngine
from metrics.performance import PerformanceMetrics

# Local imports - UI
from ui.input_helpers import (
    confirm_action,
    get_choice,
    get_date,
    get_input_with_back,
    get_multi_choice,
    get_number,
    get_validated_input,
    pause,
    print_error,
    print_info,
    print_section_header,
    print_subsection_header,
    print_success,
    print_warning
)
from ui.visualizer import BacktestVisualizer

# Local imports - Real-time
from realtime.price_viewer import PriceViewer
from realtime.chart_display import ChartDisplay
from realtime.fundamentals import FundamentalsViewer
from realtime.tradingview_integration import TradingViewWidget


class AssetClass(Enum):
    """Asset class categories"""
    CRYPTO = "Cryptocurrency"
    STOCKS = "Stocks"
    FOREX = "Forex"
    COMMODITIES = "Commodities"
    INDICES = "Indices"
    MACRO = "Macro Economic"
    OPTIONS = "Options"  # NEW: Options trading


class Tab:
    """Represents a tab in the terminal"""
    def __init__(self, name: str, handler: Callable, shortcut: str = None):
        self.name = name
        self.handler = handler
        self.shortcut = shortcut
    
    def execute(self):
        """Execute tab handler"""
        return self.handler()


class TradingTerminalV2:
    """
    Advanced tab-based trading terminal.
    
    Architecture:
    - Tab-based navigation for different workflows
    - Asset class categorization
    - Expandable data source registry
    - Strategy registry system
    """
    
    def __init__(self):
        # Strategy registry
        self.strategy_registry = {
            'macd_basic': {
                'name': 'MACD Strategy',
                'class': MACDStrategy,
                'asset_classes': [AssetClass.CRYPTO, AssetClass.STOCKS],
                'description': 'Classic MACD crossover with RSI filter'
            },
            'macd_advanced': {
                'name': 'MACD Advanced',
                'class': MACDAdvancedStrategy,
                'asset_classes': [AssetClass.CRYPTO, AssetClass.STOCKS],
                'description': 'Enhanced MACD with volume and trend filters'
            },
            'macd_conservative': {
                'name': 'MACD Conservative',
                'class': MACDConservative,
                'asset_classes': [AssetClass.CRYPTO, AssetClass.STOCKS],
                'description': 'Conservative MACD with strict entry rules'
            },
            'macd_aggressive': {
                'name': 'MACD Aggressive',
                'class': MACDAggressive,
                'asset_classes': [AssetClass.CRYPTO, AssetClass.STOCKS],
                'description': 'Aggressive MACD with relaxed filters'
            },
            'covered_call': {
                'name': 'Covered Call',
                'class': CoveredCall,
                'asset_classes': [AssetClass.OPTIONS],
                'description': 'Long stock + Short call - Generate income with capped upside'
            },
            'protective_put': {
                'name': 'Protective Put',
                'class': ProtectivePut,
                'asset_classes': [AssetClass.OPTIONS],
                'description': 'Long stock + Long put - Downside protection with unlimited upside'
            },
            'iron_condor': {
                'name': 'Iron Condor',
                'class': IronCondor,
                'asset_classes': [AssetClass.OPTIONS],
                'description': 'Credit spread strategy - Profit from low volatility'
            },
            'long_straddle': {
                'name': 'Long Straddle',
                'class': LongStraddle,
                'asset_classes': [AssetClass.OPTIONS],
                'description': 'Long call + Long put - Profit from high volatility move'
            },
            'bull_call_spread': {
                'name': 'Bull Call Spread',
                'class': BullCallSpread,
                'asset_classes': [AssetClass.OPTIONS],
                'description': 'Bullish spread with limited risk/reward'
            },
            'bear_put_spread': {
                'name': 'Bear Put Spread',
                'class': BearPutSpread,
                'asset_classes': [AssetClass.OPTIONS],
                'description': 'Bearish spread with limited risk/reward'
            },
        }
        
        # Data source registry with asset class mapping
        self.data_source_registry = {
            'yahoo': {
                'name': 'Yahoo Finance',
                'asset_classes': [AssetClass.CRYPTO, AssetClass.STOCKS, AssetClass.INDICES],
                'requires_api': False,
                'examples': {
                    AssetClass.CRYPTO: 'BTC-USD, ETH-USD',
                    AssetClass.STOCKS: 'AAPL, MSFT, TSLA',
                    AssetClass.INDICES: '^GSPC, ^DJI'
                }
            },
            'binance': {
                'name': 'Binance',
                'asset_classes': [AssetClass.CRYPTO],
                'requires_api': False,
                'examples': {
                    AssetClass.CRYPTO: 'BTCUSDT, ETHUSDT, SOLUSDT'
                }
            },
            'alpha_vantage': {
                'name': 'Alpha Vantage',
                'asset_classes': [AssetClass.CRYPTO, AssetClass.STOCKS, AssetClass.FOREX],
                'requires_api': True,
                'examples': {
                    AssetClass.CRYPTO: 'BTC, ETH',
                    AssetClass.STOCKS: 'AAPL, MSFT',
                    AssetClass.FOREX: 'EURUSD, GBPUSD'
                }
            },
            'deribit': {
                'name': 'Deribit Options (⚠️ No Historical Data)',
                'asset_classes': [AssetClass.OPTIONS],
                'requires_api': False,
                'examples': {
                    AssetClass.OPTIONS: 'BTC-OPTION, ETH-OPTION'
                },
                'warning': '⚠️  This source provides CURRENT snapshot only, not historical data. Not suitable for backtesting!',
                'enabled': False  # Disabled until historical options data is available
            },
            # Placeholder for future data sources
            'fred': {
                'name': 'FRED Economic Data',
                'asset_classes': [AssetClass.MACRO],
                'requires_api': True,
                'examples': {
                    AssetClass.MACRO: 'GDP, UNRATE, CPIAUCSL'
                },
                'enabled': False  # Not yet implemented
            }
        }
        
        # UI components
        self.visualizer = BacktestVisualizer()
        self.price_viewer = PriceViewer()
        self.chart_display = ChartDisplay()
        self.fundamentals_viewer = FundamentalsViewer()  # NEW
        self.tradingview = TradingViewWidget()  # NEW
        self.current_tab = None
        self.session_data = {
            'last_backtest': None,
            'last_comparison': None,
            'selected_asset_class': None,
            'selected_data_source': None,
        }
        
        # Initialize tabs
        self.tabs = self._initialize_tabs()
    
    def _initialize_tabs(self) -> Dict[str, Tab]:
        """Initialize all tabs"""
        return {
            'home': Tab('Home', self.tab_home, 'h'),
            'quick': Tab('Quick Backtest', self.tab_quick_backtest, 'q'),
            'compare': Tab('Compare Strategies', self.tab_compare_strategies, 'c'),
            'market': Tab('📊 Market Analysis', self.tab_market_analysis, 'm'),  # RENAMED & MERGED
            'data': Tab('Data Sources', self.tab_data_sources, 'd'),
            'strategies': Tab('Strategy Library', self.tab_strategy_library, 's'),
            'results': Tab('View Results', self.tab_view_results, 'r'),
            'settings': Tab('Settings', self.tab_settings, 'x'),
        }
    
    def display_banner(self):
        """Display terminal banner"""
        banner = """
================================================================================
                                                                  
        QUANTITATIVE TRADING TERMINAL v2.0                        
        Professional Strategy Backtesting Platform               
                                                                  
================================================================================
        """
        print(banner)
    
    def display_tab_bar(self):
        """Display tab navigation bar"""
        print_section_header("NAVIGATION")
        
        tab_display = []
        for i, (key, tab) in enumerate(self.tabs.items(), 1):
            shortcut = f"[{tab.shortcut}]" if tab.shortcut else f"[{i}]"
            active = " *" if self.current_tab == key else ""
            tab_display.append(f"{i}. {tab.name} {shortcut}{active}")
        
        # Display in columns
        for i in range(0, len(tab_display), 3):
            row = tab_display[i:i+3]
            print("  ".join(f"{item:30s}" for item in row))
        
        print("\nType: Number, Shortcut, or 'quit' to exit")
        print("=" * 80)
    
    def tab_home(self):
        """Home tab - Overview and quick stats"""
        print_section_header("HOME - OVERVIEW")
        
        print("\nWelcome to Quantitative Trading Terminal")
        print("\nPlatform Capabilities:")
        print("  - Multi-asset class backtesting (Crypto, Stocks, Forex, Macro)")
        print("  - Multiple data source integration")
        print("  - Strategy comparison and analysis")
        print("  - Advanced visualization tools")
        
        print("\n" + "-" * 80)
        print("QUICK START")
        print("-" * 80)
        print("1. Quick Backtest  - Run a single strategy quickly")
        print("2. Compare         - Compare multiple strategies side-by-side")
        print("3. Data Sources    - Configure and test data connections")
        print("4. Strategies      - Browse and configure strategies")
        
        if self.session_data['last_backtest']:
            print("\n" + "-" * 80)
            print("RECENT ACTIVITY")
            print("-" * 80)
            print(f"Last Backtest: {self.session_data['last_backtest'].get('strategy_name', 'N/A')}")
            print(f"Asset Class: {self.session_data.get('selected_asset_class', 'N/A')}")
        
        pause()
    
    def tab_quick_backtest(self):
        """Quick backtest tab - Fast workflow"""
        print_section_header("QUICK BACKTEST")
        
        # Step 1: Select asset class
        asset_class = self._select_asset_class()
        if not asset_class:
            return
        
        self.session_data['selected_asset_class'] = asset_class
        
        # Step 2: Select data source
        data_source = self._select_data_source(asset_class)
        if not data_source:
            return
        
        # Step 3: Select strategy
        strategy_info = self._select_strategy(asset_class)
        if not strategy_info:
            return
        
        # Step 4: Get backtest parameters
        params = self._get_backtest_parameters(data_source, asset_class)
        if not params:
            return
        
        # Step 5: Run backtest
        self._execute_backtest(strategy_info, data_source, params)
    
    def tab_compare_strategies(self):
        """Compare strategies tab"""
        print_section_header("COMPARE STRATEGIES")
        
        # Step 1: Select asset class
        asset_class = self._select_asset_class()
        if not asset_class:
            return
        
        # Step 2: Select data source
        data_source = self._select_data_source(asset_class)
        if not data_source:
            return
        
        # Step 3: Multi-select strategies
        strategies = self._multi_select_strategies(asset_class)
        if not strategies or len(strategies) < 2:
            print_error("Please select at least 2 strategies to compare")
            pause()
            return
        
        # Step 4: Get parameters
        params = self._get_backtest_parameters(data_source, asset_class)
        if not params:
            return
        
        # Step 5: Run comparison
        self._execute_comparison(strategies, data_source, params)
    
    def tab_data_sources(self):
        """Data sources management tab"""
        print_section_header("DATA SOURCES")
        
        print("\nAvailable Data Sources:")
        print("-" * 80)
        
        for source_id, source_info in self.data_source_registry.items():
            enabled = source_info.get('enabled', True)
            if not enabled:
                continue
            
            status = "Ready"
            if source_info['requires_api']:
                status = "Ready" if is_api_configured(source_id) else "API Key Required"
            
            print(f"\n{source_info['name']}")
            print(f"  Status: {status}")
            print(f"  Asset Classes: {', '.join(ac.value for ac in source_info['asset_classes'])}")
            
            for asset_class, examples in source_info['examples'].items():
                print(f"    {asset_class.value}: {examples}")
        
        print("\n" + "-" * 80)
        print("Options:")
        print("1. Test data source connection")
        print("2. Configure API keys (see SETUP.md)")
        print("b. Back")
        
        choice = get_input_with_back("\nSelect option", allow_back=True)
        
        if choice == '1':
            self._test_data_source_connection()
        elif choice == '2':
            print_info("Please edit .env file to configure API keys. See SETUP.md for details.")
            pause()
    
    def tab_strategy_library(self):
        """Strategy library tab"""
        print_section_header("STRATEGY LIBRARY")
        
        print("\nAvailable Strategies:")
        print("-" * 80)
        
        for i, (strategy_id, strategy_info) in enumerate(self.strategy_registry.items(), 1):
            print(f"\n{i}. {strategy_info['name']}")
            print(f"   {strategy_info['description']}")
            print(f"   Asset Classes: {', '.join(ac.value for ac in strategy_info['asset_classes'])}")
        
        print("\n" + "-" * 80)
        print("Options:")
        print("1. View strategy details")
        print("2. Test strategy on sample data")
        print("b. Back")
        
        choice = get_input_with_back("\nSelect option", allow_back=True)
        
        if choice == '1':
            self._view_strategy_details()
        elif choice == '2':
            print_info("Strategy testing feature coming soon")
            pause()
    
    def tab_view_results(self):
        """View results tab"""
        print_section_header("VIEW RESULTS")
        
        has_backtest = self.session_data['last_backtest'] is not None
        has_comparison = self.session_data['last_comparison'] is not None
        
        if not has_backtest and not has_comparison:
            print_warning("No results available. Run a backtest or comparison first.")
            pause()
            return
        
        # Show what's available
        print("\nAvailable Results:")
        if has_backtest:
            result = self.session_data['last_backtest']
            print(f"  [Single Backtest] {result.get('strategy_name', 'Strategy')} on {result.get('symbol', 'N/A')}")
        if has_comparison:
            comp = self.session_data['last_comparison']
            print(f"  [Comparison] {len(comp['metrics'])} strategies on {', '.join(comp['symbols'])}")
            print(f"                Date Range: {comp['date_range']}")
        
        # Loop to allow multiple views without going back
        while True:
            options = {}
            
            if has_backtest:
                options['1'] = 'Single Backtest: Equity Curve & Drawdown'
                options['2'] = 'Single Backtest: Trade Analysis'
                options['3'] = 'Single Backtest: Both Charts'
            
            if has_comparison:
                options['4'] = 'Comparison: Equity Curves Overlay'
                options['5'] = 'Comparison: Metrics Bar Chart'
                options['6'] = 'Comparison: Both Charts'
            
            options['e'] = 'Export Results'
            options['b'] = 'Back to Navigation'
            
            choice = get_choice("Select visualization option", options, allow_back=True)
            
            if choice is None or choice == 'b':
                break
            elif choice in ['1', '2', '3'] and has_backtest:
                self._visualize_results(choice)
                print()
            elif choice in ['4', '5', '6'] and has_comparison:
                viz_type = {'4': '1', '5': '2', '6': '3'}[choice]
                self._visualize_comparison(viz_type)
                print()
            elif choice == 'e':
                self._export_results()
                print()
    
    def tab_settings(self):
        """Settings tab"""
        print_section_header("SETTINGS")
        
        print("\nCurrent Configuration:")
        print("-" * 80)
        print(f"Default Asset Class: {self.session_data.get('selected_asset_class', 'Not set')}")
        print(f"Default Data Source: {self.session_data.get('selected_data_source', 'Not set')}")
        print(f"Visualization: Enabled")
        
        print("\n" + "-" * 80)
        print("Options:")
        print("1. Set default asset class")
        print("2. Set default data source")
        print("3. Clear session data")
        print("b. Back")
        
        choice = get_input_with_back("\nSelect option", allow_back=True)
        
        if choice == '1':
            asset_class = self._select_asset_class()
            if asset_class:
                self.session_data['selected_asset_class'] = asset_class
                print_success(f"Default asset class set to: {asset_class.value}")
        elif choice == '2':
            print_info("Set default data source per asset class in future version")
        elif choice == '3':
            self.session_data = {
                'last_backtest': None,
                'last_comparison': None,
                'selected_asset_class': None,
                'selected_data_source': None,
            }
            print_success("Session data cleared")
        
        pause()
    
    def tab_market_analysis(self):
        """
        Market Analysis Tab - Professional Trading Terminal
        Display company fundamentals, financial statements, and real-time charts
        """
        print_section_header("📊 MARKET ANALYSIS")
        
        while True:
            print("\n" + "━" * 80)
            print("💡 Tip: View company fundamentals, financial statements, and real-time charts")
            print("   Stocks: AAPL, MSFT, TSLA | Crypto: BTC-USD, ETH-USD")
            print("━" * 80)
            
            # Get symbol
            symbol_input = get_input_with_back("\n[1/2] Enter symbol (e.g., AAPL, BTC-USD, ETH-USD)", allow_back=True)
            if not symbol_input:
                return
            
            symbol = symbol_input.strip().upper()
            
            # Main menu
            while True:
                print("\n" + "━" * 80)
                print(f"📊 {symbol} - Analysis Menu")
                print("━" * 80)
                print("\n1. Company Overview")
                print("2. Balance Sheet")
                print("3. Income Statement")
                print("4. Cash Flow Statement")
                print("5. TradingView Chart (Real-time)")
                print("6. TradingView Advanced Chart (Browser)")
                print("7. Change Symbol")
                print("\nB. Back to main menu")
                
                choice = get_input_with_back("\nSelect option", allow_back=True)
                
                if not choice or choice.lower() == 'b':
                    break
                
                if choice == '1':
                    # Company Overview
                    print_info("\n⏳ Fetching company overview...\n")
                    try:
                        self.fundamentals_viewer.view_company_overview(symbol)
                        pause()
                    except Exception as e:
                        print_error(f"Error: {e}")
                        pause()
                
                elif choice == '2':
                    # Balance Sheet
                    print_info("\n⏳ Fetching balance sheet...\n")
                    try:
                        self.fundamentals_viewer.view_balance_sheet(symbol)
                        pause()
                    except Exception as e:
                        print_error(f"Error: {e}")
                        pause()
                
                elif choice == '3':
                    # Income Statement
                    print_info("\n⏳ Fetching income statement...\n")
                    try:
                        self.fundamentals_viewer.view_income_statement(symbol)
                        pause()
                    except Exception as e:
                        print_error(f"Error: {e}")
                        pause()
                
                elif choice == '4':
                    # Cash Flow
                    print_info("\n⏳ Fetching cash flow statement...\n")
                    try:
                        self.fundamentals_viewer.view_cash_flow(symbol)
                        pause()
                    except Exception as e:
                        print_error(f"Error: {e}")
                        pause()
                
                elif choice == '5':
                    # TradingView Widget
                    print_info("\n⏳ Opening TradingView widget in browser...\n")
                    
                    # Ask for interval
                    print("\nChart Interval:")
                    print("  1. 1 minute")
                    print("  2. 5 minutes")
                    print("  3. 15 minutes")
                    print("  4. 1 hour")
                    print("  5. 1 day (default)")
                    print("  6. 1 week")
                    
                    interval_choice = get_input_with_back("Select interval (or Enter for daily)", allow_back=True)
                    
                    interval_map = {
                        '1': '1',
                        '2': '5',
                        '3': '15',
                        '4': '60',
                        '5': 'D',
                        '6': 'W',
                        '': 'D'
                    }
                    
                    interval = interval_map.get(interval_choice, 'D')
                    
                    try:
                        self.tradingview.open_widget(symbol, interval=interval)
                        print_success("\n✅ TradingView chart opened in browser!")
                        print("   Close browser tab when done viewing.")
                        pause()
                    except Exception as e:
                        print_error(f"Error: {e}")
                        pause()
                
                elif choice == '6':
                    # TradingView Advanced Chart
                    print_info("\n⏳ Opening TradingView advanced chart...\n")
                    try:
                        self.tradingview.open_advanced_chart(symbol, interval='D')
                        print_success("\n✅ TradingView.com opened in browser!")
                        pause()
                    except Exception as e:
                        print_error(f"Error: {e}")
                        pause()
                
                elif choice == '7':
                    # Change symbol
                    break
                
                else:
                    print_error("Invalid choice. Try again.")
                    pause()
    
    # Helper methods
    def _select_asset_class(self) -> Optional[AssetClass]:
        """Select asset class"""
        print_subsection_header("SELECT ASSET CLASS")
        
        # Get unique asset classes from data sources
        available_classes = set()
        for source_info in self.data_source_registry.values():
            if source_info.get('enabled', True):
                available_classes.update(source_info['asset_classes'])
        
        options = {str(i): ac.value for i, ac in enumerate(sorted(available_classes, key=lambda x: x.value), 1)}
        
        choice = get_choice("Select asset class", options, allow_back=True)
        
        if choice:
            selected_value = options[choice]
            return next(ac for ac in AssetClass if ac.value == selected_value)
        return None
    
    def _select_data_source(self, asset_class: AssetClass) -> Optional[Dict]:
        """Select data source for given asset class"""
        print_subsection_header("SELECT DATA SOURCE")
        
        # Filter sources by asset class
        compatible_sources = {}
        for source_id, source_info in self.data_source_registry.items():
            if (source_info.get('enabled', True) and 
                asset_class in source_info['asset_classes']):
                status = "Ready"
                if source_info['requires_api'] and not is_api_configured(source_id):
                    status = "API Key Required"
                
                compatible_sources[source_id] = {
                    'name': source_info['name'],
                    'status': status,
                    'examples': source_info['examples'].get(asset_class, '')
                }
        
        if not compatible_sources:
            # Special message for Options
            if asset_class == AssetClass.OPTIONS:
                print_error(f"\n❌ Options backtesting is currently DISABLED")
                print("\n  Reason: No historical options data available")
                print("\n  Why this matters:")
                print("  • Current data sources only provide price snapshots")
                print("  • Backtesting requires historical time series data")
                print("  • Results from snapshot data are meaningless")
                print("\n  To enable options backtesting:")
                print("  1. Integrate paid historical options data (CBOE, OptionMetrics, etc.)")
                print("  2. Update data_loader.py with new data source")
                print("  3. Enable 'deribit' or add new source in terminal_v2.py")
                print("\n  For now, please use:")
                print("  • BTC-USD, ETH-USD (Crypto)")
                print("  • AAPL, MSFT, TSLA (Stocks)")
                print("  • Or other asset classes with real historical data")
            else:
                print_error(f"No data sources available for {asset_class.value}")
            pause()
            return None
        
        # Create numbered options for easy selection
        source_list = list(compatible_sources.keys())
        options = {}
        
        print()
        for i, source_id in enumerate(source_list, 1):
            info = compatible_sources[source_id]
            print(f"{i}. {info['name']:20s} {info['status']:20s} Examples: {info['examples']}")
            options[str(i)] = info['name']
            # Also allow selection by source_id (e.g., "alpha_vantage")
            options[source_id] = info['name']
        
        choice = get_choice("Select data source", options, allow_back=True, show_options=False)
        
        if choice:
            # Map number back to source_id
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(source_list):
                    source_id = source_list[idx]
                else:
                    return None
            else:
                source_id = choice
            
            source_data = {
                'id': source_id,
                'name': compatible_sources[source_id]['name'],
                'examples': compatible_sources[source_id]['examples']
            }
            
            # Show warning for Deribit
            if source_id == 'deribit':
                print_warning("\n⚠️  IMPORTANT: Deribit Options Limitation")
                print("   • This data source provides CURRENT snapshot only")
                print("   • NOT historical time series data")
                print("   • Backtest results will be MISLEADING")
                print("   • Recommended: Use BTC-USD or ETH-USD instead for real backtesting\n")
                
                if not confirm_action("Continue anyway? (Not recommended)", default=False):
                    return None
            
            return source_data
        return None
    
    def _select_strategy(self, asset_class: AssetClass) -> Optional[Dict]:
        """Select strategy compatible with asset class"""
        print_subsection_header("SELECT STRATEGY")
        
        # Filter strategies by asset class
        compatible_strategies = {}
        for strategy_id, strategy_info in self.strategy_registry.items():
            if asset_class in strategy_info['asset_classes']:
                compatible_strategies[strategy_id] = strategy_info
        
        if not compatible_strategies:
            print_error(f"No strategies available for {asset_class.value}")
            pause()
            return None
        
        # Create numbered options for easy selection
        strategy_list = list(compatible_strategies.keys())
        options = {}
        
        print()
        for i, strategy_id in enumerate(strategy_list, 1):
            info = compatible_strategies[strategy_id]
            print(f"{i}. {info['name']:30s} - {info['description']}")
            options[str(i)] = info['name']
            # Also allow selection by strategy_id (e.g., "macd_basic")
            options[strategy_id] = info['name']
        
        choice = get_choice("Select strategy", options, allow_back=True, show_options=False)
        
        if choice:
            # Map number back to strategy_id
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(strategy_list):
                    strategy_id = strategy_list[idx]
                else:
                    return None
            else:
                strategy_id = choice
            
            if strategy_id in compatible_strategies:
                return compatible_strategies[strategy_id]
        return None
    
    def _multi_select_strategies(self, asset_class: AssetClass) -> Optional[List[Dict]]:
        """Multi-select strategies"""
        print_subsection_header("SELECT STRATEGIES TO COMPARE")
        
        compatible_strategies = {}
        for strategy_id, strategy_info in self.strategy_registry.items():
            if asset_class in strategy_info['asset_classes']:
                compatible_strategies[strategy_id] = strategy_info
        
        # Create numbered options
        strategy_list = list(compatible_strategies.keys())
        options = {}
        for i, strategy_id in enumerate(strategy_list, 1):
            options[str(i)] = compatible_strategies[strategy_id]['name']
            options[strategy_id] = compatible_strategies[strategy_id]['name']
        
        choices = get_multi_choice(
            "Select strategies (comma-separated, e.g., 1,2,3)",
            options,
            min_selections=2
        )
        
        if choices:
            # Map numbers back to strategy_ids
            selected_strategies = []
            for choice in choices:
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(strategy_list):
                        strategy_id = strategy_list[idx]
                        selected_strategies.append(compatible_strategies[strategy_id])
                elif choice in compatible_strategies:
                    selected_strategies.append(compatible_strategies[choice])
            return selected_strategies if selected_strategies else None
        return None
    
    def _get_backtest_parameters(self, data_source: Dict, asset_class: AssetClass) -> Optional[Dict]:
        """Get backtest parameters from user"""
        print_subsection_header("BACKTEST PARAMETERS")
        
        # Symbols
        example = data_source['examples']
        symbols_input = get_input_with_back(
            f"Enter symbols (comma-separated, e.g., {example})",
            allow_back=True
        )
        if not symbols_input:
            return None
        
        from core.utils import parse_symbols
        symbols = parse_symbols(symbols_input)
        
        # Dates
        start_date = get_date("Start date (YYYY-MM-DD)", allow_back=True)
        if start_date is None:  # User pressed back
            return None
        
        # For end_date, we allow empty but need a way to go back
        # Since get_date with allow_empty returns None for both back and empty,
        # we need to handle this differently
        while True:
            end_date_input = get_input_with_back("End date (YYYY-MM-DD) (press Enter for latest)", allow_back=True)
            if end_date_input is None:  # User pressed back
                return None
            if end_date_input == "":  # User pressed Enter for latest
                end_date = None
                break
            # Validate date format
            from core.utils import validate_date_format
            if validate_date_format(end_date_input):
                end_date = end_date_input
                break
            else:
                print("\n[ERROR] Invalid date format. Please use YYYY-MM-DD")
        
        # Capital
        capital = get_number("Initial capital", min_value=100, default=10000, allow_back=True)
        if capital is None:
            return None
        
        return {
            'symbols': symbols,
            'start_date': start_date,
            'end_date': end_date,
            'capital': capital
        }
    
    def _execute_backtest(self, strategy_info: Dict, data_source: Dict, params: Dict):
        """Execute backtest"""
        print_section_header("RUNNING BACKTEST")
        
        strategy = strategy_info['class']()
        engine = BacktestEngine(initial_capital=params['capital'])
        metrics_calc = PerformanceMetrics()
        
        results = []
        
        for symbol in params['symbols']:
            logger.info("Processing %s", symbol)

            try:
                df = load_data(
                    symbol=symbol,
                    start_date=params['start_date'],
                    end_date=params['end_date'],
                    source=data_source['id']
                )
                
                if df is None or df.empty:
                    logger.warning("No data available for %s", symbol)
                    continue

                logger.info("Loaded %s bars for %s", len(df), symbol)

                required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    logger.warning("Missing required columns %s for %s (available: %s)",
                                   missing_cols, symbol, list(df.columns))
                    continue

                # Run strategy and backtest
                df = strategy.run(df)
                
                backtest_results = engine.run(df)
                metrics = metrics_calc.calculate_all_metrics(
                    backtest_results,
                    backtest_results['equity_curve']
                )
                
                # Store for visualization
                backtest_results['strategy_name'] = strategy_info['name']
                backtest_results['symbol'] = symbol
                self.session_data['last_backtest'] = backtest_results
                
                # Display comprehensive results
                print("\n" + "  " + "-" * 60)
                print(f"  BACKTEST RESULTS - {symbol}")
                print("  " + "-" * 60)
                
                print(f"\n  Performance Metrics:")
                print(f"    Total Return:        {metrics['total_return']:>10.2f}%")
                print(f"    Sharpe Ratio:        {metrics['sharpe_ratio']:>10.2f}")
                print(f"    Max Drawdown:        {metrics['max_drawdown']:>10.2f}%")
                print(f"    Win Rate:            {metrics['win_rate']:>10.2f}%")
                
                print(f"\n  Trade Statistics:")
                print(f"    Total Trades:        {metrics['num_trades']:>10}")
                print(f"    Winning Trades:      {backtest_results.get('num_winning', 0):>10}")
                print(f"    Losing Trades:       {backtest_results.get('num_losing', 0):>10}")
                print(f"    Avg Win:             {metrics['avg_win']:>10.2f}%")
                print(f"    Avg Loss:            {metrics['avg_loss']:>10.2f}%")
                print(f"    Profit Factor:       {metrics['profit_factor']:>10.2f}")
                
                print(f"\n  Risk Metrics:")
                print(f"    Volatility:          {metrics['volatility']:>10.2f}%")
                print(f"    Sortino Ratio:       {metrics['sortino_ratio']:>10.2f}")
                print(f"    Calmar Ratio:        {metrics['calmar_ratio']:>10.2f}")
                
                print(f"\n  Portfolio:")
                print(f"    Initial Capital:     ${params['capital']:>10,.2f}")
                print(f"    Final Value:         ${backtest_results['final_capital']:>10,.2f}")
                print("  " + "-" * 60)
                
            except Exception as e:
                logger.error("Backtest error for %s: %s", symbol, e)
        
        # Ask for visualization
        if confirm_action("\nVisualize results?", default=True):
            self._visualize_results('3')
        
        pause()
    
    def _execute_comparison(self, strategies: List[Dict], data_source: Dict, params: Dict):
        """Execute strategy comparison"""
        print_section_header("COMPARING STRATEGIES")
        
        all_results = []
        all_equity_curves = {}  # Store equity curves for visualization
        metrics_calc = PerformanceMetrics()
        
        for strategy_info in strategies:
            print(f"\nTesting: {strategy_info['name']}")
            
            strategy = strategy_info['class']()
            strategy_equity_curves = []
            strategy_results = []
            
            for symbol in params['symbols']:
                try:
                    df = load_data(
                        symbol=symbol,
                        start_date=params['start_date'],
                        end_date=params['end_date'],
                        source=data_source['id']
                    )
                    
                    if df is None or df.empty:
                        continue
                    
                    # Validate required columns
                    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    if missing_cols:
                        logger.warning("Missing columns %s for %s", missing_cols, symbol)
                        continue
                    
                    logger.info("Running strategy on %s", symbol)

                    df = strategy.run(df)
                    engine = BacktestEngine(initial_capital=params['capital'])
                    backtest_results = engine.run(df)
                    metrics = metrics_calc.calculate_all_metrics(
                        backtest_results,
                        backtest_results['equity_curve']
                    )
                    
                    # Store equity curve
                    strategy_equity_curves.append(backtest_results['equity_curve'])
                    
                    strategy_results.append({
                        'Symbol': symbol,
                        'Total Return (%)': metrics['total_return'],
                        'Sharpe Ratio': metrics['sharpe_ratio'],
                        'Max Drawdown (%)': metrics['max_drawdown'],
                        'Win Rate (%)': metrics['win_rate'],
                        'Total Trades': metrics['num_trades'],
                        'Profit Factor': metrics['profit_factor'],
                    })
                    
                    logger.info("%s Return: %.2f%%, Sharpe: %.2f",
                               symbol, metrics['total_return'], metrics['sharpe_ratio'])

                except Exception as e:
                    logger.error("Strategy comparison error for %s: %s", symbol, e)
            
            if strategy_results:
                avg_metrics = {
                    'Strategy': strategy_info['name'],
                    'Symbols': len(strategy_results),
                    'Avg Return (%)': sum(r['Total Return (%)'] for r in strategy_results) / len(strategy_results),
                    'Avg Sharpe': sum(r['Sharpe Ratio'] for r in strategy_results) / len(strategy_results),
                    'Avg Max DD (%)': sum(r['Max Drawdown (%)'] for r in strategy_results) / len(strategy_results),
                    'Avg Win Rate (%)': sum(r['Win Rate (%)'] for r in strategy_results) / len(strategy_results),
                    'Avg Profit Factor': sum(r['Profit Factor'] for r in strategy_results) / len(strategy_results),
                    'Total Trades': sum(r['Total Trades'] for r in strategy_results),
                }
                all_results.append(avg_metrics)
                
                # Store equity curves (averaged across symbols)
                if strategy_equity_curves:
                    all_equity_curves[strategy_info['name']] = strategy_equity_curves
        
        if all_results:
            df_results = pd.DataFrame(all_results)
            
            # Display comprehensive comparison table
            print("\n" + "=" * 100)
            print(" " * 35 + "STRATEGY COMPARISON RESULTS")
            print("=" * 100)
            print(df_results.to_string(index=False, float_format=lambda x: f'{x:.2f}'))
            print("=" * 100)
            
            # Store for later viewing
            self.session_data['last_comparison'] = {
                'metrics': df_results,
                'equity_curves': all_equity_curves,
                'symbols': params['symbols'],
                'date_range': f"{params['start_date']} to {params['end_date'] or 'latest'}"
            }
            
            # Offer visualization
            print("\n" + "-" * 100)
            if confirm_action("Visualize comparison with equity curves?", default=True):
                self._visualize_comparison()
        else:
            print_error("No results to display")
        
        pause()
    
    def _visualize_results(self, choice: str):
        """Visualize backtest results"""
        results = self.session_data['last_backtest']
        
        try:
            if choice in ['1', '3']:
                fig = self.visualizer.plot_equity_curve(
                    results['equity_curve'],
                    title=f"{results.get('strategy_name', 'Strategy')} - {results.get('symbol', '')}"
                )
                self.visualizer.show_plot(fig)
            
            if choice in ['2', '3'] and results.get('trades'):
                fig = self.visualizer.plot_trade_analysis(
                    results['trades'],
                    results['equity_curve'][0]
                )
                self.visualizer.show_plot(fig)
        except Exception as e:
            print_error(f"Visualization error: {e}")
        
        pause()
    
    def _visualize_comparison(self, choice: str = '3'):
        """Visualize strategy comparison results"""
        comp_data = self.session_data['last_comparison']
        
        try:
            if choice in ['1', '3']:  # Equity curves overlay
                print("\nGenerating equity curves overlay...")
                fig = self.visualizer.plot_comparison_equity_curves(
                    comp_data['equity_curves'],
                    title=f"Strategy Comparison - {', '.join(comp_data['symbols'])}"
                )
                self.visualizer.show_plot(fig)
            
            if choice in ['2', '3']:  # Metrics bar chart
                print("\nGenerating metrics comparison...")
                fig = self.visualizer.plot_strategy_comparison(comp_data['metrics'])
                self.visualizer.show_plot(fig)
        except Exception as e:
            print_error(f"Visualization error: {e}")
        
        pause()
    
    def _export_results(self):
        """Export results to file"""
        print_info("Export feature coming soon")
        pause()
    
    def _test_data_source_connection(self):
        """Test data source connection"""
        print_subsection_header("TEST DATA CONNECTION")
        
        # Get enabled sources with numbers
        enabled_sources_info = {k: v['name'] for k, v in self.data_source_registry.items() 
                               if v.get('enabled', True)}
        
        source_list = list(enabled_sources_info.keys())
        options = {}
        for i, source_id in enumerate(source_list, 1):
            options[str(i)] = enabled_sources_info[source_id]
            options[source_id] = enabled_sources_info[source_id]
        
        choice = get_choice("Select data source to test", options, allow_back=True)
        
        if not choice:
            return
        
        # Map number to source_id
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(source_list):
                choice = source_list[idx]
            else:
                return
        
        source_info = self.data_source_registry[choice]
        
        # Get test symbol
        asset_class = source_info['asset_classes'][0]
        example = source_info['examples'][asset_class]
        test_symbol = input(f"\nEnter test symbol (e.g., {example}): ").strip()
        
        if not test_symbol:
            test_symbol = example.split(',')[0].strip()
        
        print(f"\nTesting connection to {source_info['name']}...")
        
        try:
            df = load_data(
                symbol=test_symbol,
                start_date='2024-01-01',
                end_date='2024-01-31',
                source=choice
            )
            
            if df is not None and not df.empty:
                print_success(f"Connection successful! Retrieved {len(df)} data points")
                print(f"\nSample data:")
                print(df.head())
            else:
                print_error("Connection failed or no data returned")
        except Exception as e:
            print_error(f"Connection failed: {str(e)}")
        
        pause()
    
    def _view_strategy_details(self):
        """View detailed strategy information"""
        print_subsection_header("STRATEGY DETAILS")
        
        # Create numbered options
        strategy_list = list(self.strategy_registry.keys())
        options = {}
        for i, strategy_id in enumerate(strategy_list, 1):
            options[str(i)] = self.strategy_registry[strategy_id]['name']
            options[strategy_id] = self.strategy_registry[strategy_id]['name']
        
        choice = get_choice("Select strategy", options, allow_back=True)
        
        if not choice:
            return
        
        # Map number to strategy_id
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(strategy_list):
                choice = strategy_list[idx]
            else:
                return
        
        strategy_info = self.strategy_registry[choice]
        strategy = strategy_info['class']()
        
        print(f"\nStrategy: {strategy_info['name']}")
        print(f"Description: {strategy_info['description']}")
        print(f"\nAsset Classes: {', '.join(ac.value for ac in strategy_info['asset_classes'])}")
        print(f"\nParameters:")
        for key, value in strategy.get_params().items():
            print(f"  {key}: {value}")
        
        if hasattr(strategy, 'get_strategy_description'):
            print(f"\nDetailed Description:")
            print(strategy.get_strategy_description())
        
        pause()
    
    def run(self):
        """Main terminal loop"""
        self.display_banner()
        
        # Show home tab first
        self.current_tab = 'home'
        self.tabs['home'].execute()
        
        while True:
            self.display_tab_bar()
            
            user_input = get_input_with_back("Navigate to", allow_back=False)
            
            if not user_input:
                continue
            
            # Handle quit (removed 'q' to avoid conflict with Quick Backtest shortcut)
            if user_input.lower() in ['quit', 'exit']:
                print_info("Thank you for using Quantitative Trading Terminal!")
                break
            
            # Map input to tab
            selected_tab = None
            
            # Try number
            if user_input.isdigit():
                tab_list = list(self.tabs.keys())
                idx = int(user_input) - 1
                if 0 <= idx < len(tab_list):
                    selected_tab = tab_list[idx]
            
            # Try shortcut
            else:
                for key, tab in self.tabs.items():
                    if tab.shortcut and user_input.lower() == tab.shortcut.lower():
                        selected_tab = key
                        break
            
            # Execute tab
            if selected_tab:
                self.current_tab = selected_tab
                self.tabs[selected_tab].execute()
            else:
                print_error("Invalid selection")


def main():
    """Entry point for terminal"""
    terminal = TradingTerminalV2()
    terminal.run()


if __name__ == "__main__":
    main()