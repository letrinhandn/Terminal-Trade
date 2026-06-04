"""
Real-time Price Viewer
Displays live cryptocurrency and stock prices with rich formatting
"""

import yfinance as yf
import time
from datetime import datetime
from typing import Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text


class PriceViewer:
    """
    Real-time price viewer with auto-refresh
    OpenBB-inspired design with Rich library
    """
    
    def __init__(self):
        self.console = Console()
        self.is_running = False
        
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """
        Fetch current price data for a symbol
        
        Args:
            symbol: Ticker symbol (e.g., 'BTC-USD', 'AAPL')
            
        Returns:
            Dictionary with price data or None if error
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get real-time quote
            current_data = ticker.history(period='1d', interval='1m')
            
            if current_data.empty:
                return None
                
            latest = current_data.iloc[-1]
            
            return {
                'symbol': symbol,
                'price': latest['Close'],
                'open': latest['Open'],
                'high': latest['High'],
                'low': latest['Low'],
                'volume': latest['Volume'],
                'change': latest['Close'] - latest['Open'],
                'change_pct': ((latest['Close'] - latest['Open']) / latest['Open']) * 100,
                'timestamp': datetime.now(),
                'market_cap': info.get('marketCap', 'N/A'),
                'name': info.get('longName', symbol)
            }
        except Exception as e:
            self.console.print(f"[red]Error fetching {symbol}: {e}[/red]")
            return None
    
    def create_price_table(self, symbols: list) -> Table:
        """
        Create a Rich table with price data for multiple symbols
        
        Args:
            symbols: List of ticker symbols
            
        Returns:
            Rich Table object
        """
        table = Table(title="📊 Real-Time Market Prices", 
                     show_header=True,
                     header_style="bold cyan",
                     border_style="blue")
        
        table.add_column("Symbol", style="cyan", width=12)
        table.add_column("Price", style="white", justify="right", width=15)
        table.add_column("Change", justify="right", width=12)
        table.add_column("Change %", justify="right", width=12)
        table.add_column("High", justify="right", width=12)
        table.add_column("Low", justify="right", width=12)
        table.add_column("Volume", justify="right", width=15)
        
        for symbol in symbols:
            data = self.get_current_price(symbol)
            
            if data:
                # Color code based on change
                change_color = "green" if data['change'] >= 0 else "red"
                change_symbol = "▲" if data['change'] >= 0 else "▼"
                
                table.add_row(
                    f"[bold]{data['symbol']}[/bold]",
                    f"${data['price']:,.2f}",
                    f"[{change_color}]{change_symbol} ${abs(data['change']):,.2f}[/{change_color}]",
                    f"[{change_color}]{data['change_pct']:+.2f}%[/{change_color}]",
                    f"${data['high']:,.2f}",
                    f"${data['low']:,.2f}",
                    f"{data['volume']:,.0f}"
                )
            else:
                table.add_row(
                    f"[bold]{symbol}[/bold]",
                    "[red]Error[/red]",
                    "-", "-", "-", "-", "-"
                )
        
        return table
    
    def display_price_table(self, symbols: list):
        """
        Display price table to console
        
        Args:
            symbols: List of ticker symbols
        """
        table = self.create_price_table(symbols)
        self.console.print(table)
    
    def display_detailed_quote(self, symbol: str):
        """
        Display detailed quote for a single symbol
        
        Args:
            symbol: Ticker symbol
        """
        data = self.get_current_price(symbol)
        
        if not data:
            self.console.print(f"[red]Could not fetch data for {symbol}[/red]")
            return
        
        # Create detailed panel
        change_color = "green" if data['change'] >= 0 else "red"
        change_symbol = "▲" if data['change'] >= 0 else "▼"
        
        info_text = Text()
        info_text.append(f"\n{data['name']}\n", style="bold white")
        info_text.append(f"Symbol: {data['symbol']}\n", style="cyan")
        info_text.append(f"\nPrice: ${data['price']:,.2f}\n", style="bold yellow")
        info_text.append(f"Change: ", style="white")
        info_text.append(f"{change_symbol} ${abs(data['change']):,.2f} ({data['change_pct']:+.2f}%)\n", 
                        style=change_color)
        info_text.append(f"\nDay Range:\n", style="white")
        info_text.append(f"  High: ${data['high']:,.2f}\n", style="green")
        info_text.append(f"  Low:  ${data['low']:,.2f}\n", style="red")
        info_text.append(f"\nVolume: {data['volume']:,.0f}\n", style="white")
        
        if data['market_cap'] != 'N/A':
            info_text.append(f"Market Cap: ${data['market_cap']:,.0f}\n", style="white")
        
        info_text.append(f"\nLast Updated: {data['timestamp'].strftime('%H:%M:%S')}\n", 
                        style="dim")
        
        panel = Panel(info_text, 
                     title=f"📈 {symbol} Quote",
                     border_style="blue",
                     padding=(1, 2))
        
        self.console.print(panel)
    
    def watch_prices(self, symbols: list, refresh_interval: int = 5):
        """
        Watch prices with auto-refresh (live view)
        
        Args:
            symbols: List of ticker symbols
            refresh_interval: Seconds between refreshes
        """
        self.console.print(f"\n[yellow]Watching {', '.join(symbols)} (Refresh: {refresh_interval}s)[/yellow]")
        self.console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        
        try:
            with Live(self.create_price_table(symbols), 
                     refresh_per_second=1/refresh_interval,
                     console=self.console) as live:
                self.is_running = True
                
                while self.is_running:
                    time.sleep(refresh_interval)
                    live.update(self.create_price_table(symbols))
                    
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Stopped watching prices[/yellow]")
            self.is_running = False
    
    def compare_symbols(self, symbols: list):
        """
        Compare multiple symbols side-by-side
        
        Args:
            symbols: List of ticker symbols to compare
        """
        self.console.print("\n")
        table = self.create_price_table(symbols)
        self.console.print(table)
        self.console.print()


# Example usage
if __name__ == "__main__":
    viewer = PriceViewer()
    
    # Test with crypto and stocks
    symbols = ['BTC-USD', 'ETH-USD', 'AAPL', 'TSLA']
    
    # Compare symbols
    viewer.compare_symbols(symbols)
    
    # Detailed quote
    viewer.display_detailed_quote('BTC-USD')
    
    # Watch prices (uncomment to test)
    # viewer.watch_prices(['BTC-USD', 'ETH-USD'], refresh_interval=5)