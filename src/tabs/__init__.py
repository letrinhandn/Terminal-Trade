"""Tab components for Terminal Trade"""

# Import all tabs from modular files
from .overview_tab import OverviewTab
from .backtest_tab import BacktestTab
from .options_tab import OptionsTab
from .portfolio_tab import PortfolioTab

__all__ = ['OverviewTab', 'BacktestTab', 'OptionsTab', 'PortfolioTab']