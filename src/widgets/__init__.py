"""Widget components for Terminal Trade"""

from .price_widget import PriceWidget
from .fundamentals_widget import FundamentalsWidget
from .news_widget import NewsWidget
from .company_info_widget import CompanyInfoWidget
from .financial_statements_widget import FinancialStatementsWidget
from .tradingview_widget import TradingViewWidget

__all__ = [
    'PriceWidget',
    'FundamentalsWidget', 
    'NewsWidget',
    'CompanyInfoWidget',
    'FinancialStatementsWidget',
    'TradingViewWidget'
]