"""
TradingView Integration
Embed TradingView widgets for real-time charts
"""

import webbrowser
import tempfile
import os
from typing import Optional


class TradingViewWidget:
    """
    Generate and display TradingView widgets
    """
    
    @staticmethod
    def open_advanced_chart(symbol: str, interval: str = "D"):
        """
        Open TradingView advanced chart in browser
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'BTCUSD')
            interval: Chart interval (D=Daily, W=Weekly, M=Monthly, 1=1min, 5=5min, etc.)
        """
        # Convert symbol format
        if '-USD' in symbol:
            # Crypto format: BTC-USD → BTCUSD
            symbol = symbol.replace('-USD', 'USD')
        
        url = f"https://www.tradingview.com/chart/?symbol={symbol}&interval={interval}"
        webbrowser.open(url)
    
    @staticmethod
    def generate_widget_html(symbol: str, 
                            width: int = 980, 
                            height: int = 610,
                            interval: str = "D",
                            theme: str = "dark",
                            style: str = "1") -> str:
        """
        Generate TradingView widget HTML
        
        Args:
            symbol: Trading symbol
            width: Widget width
            height: Widget height
            interval: Chart interval
            theme: 'dark' or 'light'
            style: Chart style (1=Candles, 2=Bars, 3=Line, etc.)
        
        Returns:
            HTML string for widget
        """
        # Convert symbol for TradingView
        if '-USD' in symbol:
            tv_symbol = symbol.replace('-USD', 'USD')
            exchange = "BINANCE"
        elif symbol in ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMZN', 'META']:
            tv_symbol = symbol
            exchange = "NASDAQ"
        else:
            tv_symbol = symbol
            exchange = "NYSE"
        
        full_symbol = f"{exchange}:{tv_symbol}"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{symbol} - TradingView Chart</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #131722;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .header p {{
            margin: 5px 0 0 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .container {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: calc(100vh - 80px);
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 {symbol} Live Chart</h1>
        <p>Powered by TradingView • Real-time data</p>
    </div>
    <div class="container">
        <!-- TradingView Widget BEGIN -->
        <div class="tradingview-widget-container">
            <div id="tradingview_widget"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
                new TradingView.widget({{
                    "width": {width},
                    "height": {height},
                    "symbol": "{full_symbol}",
                    "interval": "{interval}",
                    "timezone": "Etc/UTC",
                    "theme": "{theme}",
                    "style": "{style}",
                    "locale": "en",
                    "toolbar_bg": "#f1f3f6",
                    "enable_publishing": false,
                    "allow_symbol_change": true,
                    "save_image": false,
                    "container_id": "tradingview_widget",
                    "studies": [
                        "MACD@tv-basicstudies",
                        "RSI@tv-basicstudies",
                        "MASimple@tv-basicstudies"
                    ]
                }});
            </script>
        </div>
        <!-- TradingView Widget END -->
    </div>
</body>
</html>
"""
        return html
    
    @staticmethod
    def open_widget(symbol: str, 
                   interval: str = "D",
                   width: int = 1200,
                   height: int = 700):
        """
        Open TradingView widget in browser
        
        Args:
            symbol: Trading symbol
            interval: Chart interval
            width: Widget width
            height: Widget height
        """
        html = TradingViewWidget.generate_widget_html(
            symbol=symbol,
            width=width,
            height=height,
            interval=interval,
            theme="dark",
            style="1"
        )
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html)
            temp_path = f.name
        
        # Open in browser
        webbrowser.open('file://' + os.path.abspath(temp_path))
        
        return temp_path
    
    @staticmethod
    def generate_mini_chart_html(symbol: str,
                                 width: int = 350,
                                 height: int = 220,
                                 theme: str = "dark") -> str:
        """
        Generate mini chart widget HTML
        
        Args:
            symbol: Trading symbol
            width: Widget width
            height: Widget height
            theme: 'dark' or 'light'
        
        Returns:
            HTML string for mini widget
        """
        # Convert symbol
        if '-USD' in symbol:
            tv_symbol = symbol.replace('-USD', 'USD')
            exchange = "BINANCE"
        else:
            tv_symbol = symbol
            exchange = "NASDAQ"
        
        full_symbol = f"{exchange}:{tv_symbol}"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{symbol} Mini Chart</title>
    <style>
        body {{
            margin: 0;
            padding: 10px;
            background-color: #131722;
        }}
    </style>
</head>
<body>
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container">
        <div class="tradingview-widget-container__widget"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
        {{
            "symbol": "{full_symbol}",
            "width": "{width}",
            "height": "{height}",
            "locale": "en",
            "dateRange": "12M",
            "colorTheme": "{theme}",
            "trendLineColor": "rgba(41, 98, 255, 1)",
            "underLineColor": "rgba(41, 98, 255, 0.3)",
            "underLineBottomColor": "rgba(41, 98, 255, 0)",
            "isTransparent": false,
            "autosize": false,
            "largeChartUrl": ""
        }}
        </script>
    </div>
    <!-- TradingView Widget END -->
</body>
</html>
"""
        return html
    
    @staticmethod
    def generate_ticker_tape_html(symbols: list, theme: str = "dark") -> str:
        """
        Generate ticker tape widget HTML
        
        Args:
            symbols: List of symbols
            theme: 'dark' or 'light'
        
        Returns:
            HTML string for ticker tape
        """
        # Convert symbols
        tv_symbols = []
        for symbol in symbols:
            if '-USD' in symbol:
                tv_sym = symbol.replace('-USD', 'USD')
                tv_symbols.append({"proName": f"BINANCE:{tv_sym}", "title": symbol})
            else:
                tv_symbols.append({"proName": f"NASDAQ:{symbol}", "title": symbol})
        
        import json
        symbols_json = json.dumps(tv_symbols)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Market Ticker</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #131722;
        }}
    </style>
</head>
<body>
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container">
        <div class="tradingview-widget-container__widget"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
        {{
            "symbols": {symbols_json},
            "showSymbolLogo": true,
            "colorTheme": "{theme}",
            "isTransparent": false,
            "displayMode": "adaptive",
            "locale": "en"
        }}
        </script>
    </div>
    <!-- TradingView Widget END -->
</body>
</html>
"""
        return html
    
    @staticmethod
    def open_market_overview(symbols: list = None):
        """
        Open market overview with multiple symbols
        
        Args:
            symbols: List of symbols to track
        """
        if symbols is None:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'BTC-USD', 'ETH-USD']
        
        html = TradingViewWidget.generate_ticker_tape_html(symbols, theme="dark")
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html)
            temp_path = f.name
        
        # Open in browser
        webbrowser.open('file://' + os.path.abspath(temp_path))
        
        return temp_path


if __name__ == "__main__":
    # Test
    print("Opening TradingView widget for AAPL...")
    TradingViewWidget.open_widget("AAPL", interval="D")
    
    print("\nOpening market overview...")
    TradingViewWidget.open_market_overview(['AAPL', 'MSFT', 'BTC-USD', 'ETH-USD'])