"""
Chart Display Module
Displays candlestick charts and technical indicators
OpenBB-inspired visualization
"""

import logging
import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
from rich.console import Console

logger = logging.getLogger(__name__)


class ChartDisplay:
    """
    Display candlestick charts with technical indicators
    """
    
    def __init__(self):
        self.console = Console()
        plt.style.use('dark_background')
        
    def fetch_chart_data(self, symbol: str, period: str = '1mo', 
                        interval: str = '1d') -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for charting
        
        Args:
            symbol: Ticker symbol
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            interval: Data interval ('1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo')
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                self.console.print(f"[red]No data found for {symbol}[/red]")
                return None
            
            return df
            
        except Exception as e:
            self.console.print(f"[red]Error fetching chart data: {e}[/red]")
            return None
    
    def plot_candlestick(self, symbol: str, period: str = '1mo',
                        interval: str = '1d', indicators: List[str] = None,
                        save_path: Optional[str] = None):
        """
        Plot candlestick chart with optional indicators
        
        Args:
            symbol: Ticker symbol
            period: Time period
            interval: Data interval
            indicators: List of indicators to add ('sma', 'ema', 'volume', 'macd', 'rsi')
            save_path: Path to save chart (if None, displays interactively)
        """
        df = self.fetch_chart_data(symbol, period, interval)
        
        if df is None:
            return
        
        # Check if we have enough data
        if len(df) < 2:
            self.console.print(f"[red]Insufficient data: Only {len(df)} data points available[/red]")
            self.console.print("[yellow]Try using a different period or interval combination[/yellow]")
            return
        
        # Prepare indicators
        add_plots = []
        
        if indicators:
            # Check if we have enough data for indicators
            min_required = 50 if 'sma' in indicators or 'ema' in indicators else 2
            
            if len(df) < min_required:
                self.console.print(f"[yellow]⚠️  Warning: Only {len(df)} data points available[/yellow]")
                self.console.print(f"[yellow]   Indicators require at least {min_required} points for accuracy[/yellow]")
                self.console.print("[yellow]   Showing price chart without indicators...[/yellow]\n")
                indicators = None  # Disable indicators
            
            if indicators and 'sma' in indicators:
                # Add Simple Moving Averages (only if enough data)
                if len(df) >= 50:
                    df['SMA20'] = df['Close'].rolling(window=20).mean()
                    df['SMA50'] = df['Close'].rolling(window=50).mean()
                    # Only plot non-empty series
                    if not df['SMA20'].isna().all():
                        add_plots.append(mpf.make_addplot(df['SMA20'], color='cyan', width=1))
                    if not df['SMA50'].isna().all():
                        add_plots.append(mpf.make_addplot(df['SMA50'], color='orange', width=1))
                elif len(df) >= 20:
                    # Only use SMA20 if we have at least 20 points
                    df['SMA20'] = df['Close'].rolling(window=20).mean()
                    if not df['SMA20'].isna().all():
                        add_plots.append(mpf.make_addplot(df['SMA20'], color='cyan', width=1))
            
            if indicators and 'ema' in indicators:
                # Add Exponential Moving Averages
                if len(df) >= 26:
                    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
                    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
                    if not df['EMA12'].isna().all():
                        add_plots.append(mpf.make_addplot(df['EMA12'], color='lime', width=1))
                    if not df['EMA26'].isna().all():
                        add_plots.append(mpf.make_addplot(df['EMA26'], color='pink', width=1))
        
        # Chart style
        style = mpf.make_mpf_style(
            base_mpf_style='charles',
            marketcolors=mpf.make_marketcolors(
                up='green',
                down='red',
                edge='inherit',
                wick='inherit',
                volume='in'
            ),
            gridstyle='--',
            gridcolor='gray',
            gridaxis='both',
            facecolor='#1e1e1e',
            figcolor='#0e0e0e',
            edgecolor='white'
        )
        
        # Chart title
        title = f"{symbol} - {period.upper()} ({interval})"
        
        # Plot
        kwargs = {
            'type': 'candle',
            'style': style,
            'title': title,
            'ylabel': 'Price ($)',
            'volume': True,
            'figratio': (16, 9),
            'figscale': 1.2,
            'tight_layout': True,
        }
        
        if add_plots:
            kwargs['addplot'] = add_plots
        
        if save_path:
            kwargs['savefig'] = save_path
            mpf.plot(df, **kwargs)
            self.console.print(f"[green]Chart saved to: {save_path}[/green]")
        else:
            try:
                mpf.plot(df, **kwargs)
                plt.show()
            except Exception as e:
                self.console.print(f"[red]Error plotting chart: {e}[/red]")
                logger.warning("Error plotting chart: %s", e, exc_info=True)
    
    def plot_with_indicators(self, symbol: str, period: str = '3mo'):
        """
        Plot comprehensive chart with all indicators
        
        Args:
            symbol: Ticker symbol
            period: Time period
        """
        df = self.fetch_chart_data(symbol, period, '1d')
        
        if df is None:
            return
        
        # Check if we have enough data for full analysis
        if len(df) < 50:
            self.console.print(f"[yellow]⚠️  Warning: Only {len(df)} data points available[/yellow]")
            self.console.print("[yellow]   Full analysis requires at least 50 points[/yellow]")
            self.console.print("[yellow]   Falling back to simple chart with Moving Averages...[/yellow]\n")
            # Use simpler chart instead
            self.plot_candlestick(symbol, period, '1d', indicators=['sma'])
            return
        
        # Calculate indicators
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Prepare plots - check for empty series before adding
        apds = []
        
        # Add moving averages if not empty
        if not df['SMA20'].isna().all():
            apds.append(mpf.make_addplot(df['SMA20'], color='cyan', width=1, panel=0))
        if not df['SMA50'].isna().all():
            apds.append(mpf.make_addplot(df['SMA50'], color='orange', width=1, panel=0))
        
        # Add MACD if not empty
        if not df['MACD'].isna().all():
            apds.append(mpf.make_addplot(df['MACD'], color='fuchsia', width=1, panel=1, ylabel='MACD'))
            apds.append(mpf.make_addplot(df['Signal'], color='lime', width=1, panel=1))
            apds.append(mpf.make_addplot(df['MACD_Hist'], type='bar', color='dimgray', width=0.7, panel=1, alpha=0.5))
        
        # Add RSI if not empty
        if not df['RSI'].isna().all():
            apds.append(mpf.make_addplot(df['RSI'], color='orange', width=1, panel=2, ylabel='RSI'))
            apds.append(mpf.make_addplot([70]*len(df), color='red', width=0.5, linestyle='--', panel=2, alpha=0.5))
            apds.append(mpf.make_addplot([30]*len(df), color='green', width=0.5, linestyle='--', panel=2, alpha=0.5))
        
        # Style
        style = mpf.make_mpf_style(
            base_mpf_style='charles',
            marketcolors=mpf.make_marketcolors(
                up='#00ff00',
                down='#ff0000',
                edge='inherit',
                wick='inherit',
                volume='in'
            ),
            gridstyle='--',
            gridcolor='#404040',
            facecolor='#1e1e1e',
            figcolor='#0e0e0e'
        )
        
        # Plot with subplots
        # panel_ratios: (price+volume, MACD, RSI) = 3 panels
        fig, axes = mpf.plot(
            df,
            type='candle',
            style=style,
            title=f"{symbol} - Technical Analysis",
            ylabel='Price ($)',
            volume=True,
            addplot=apds,
            figratio=(16, 10),
            figscale=1.3,
            panel_ratios=(6, 2, 2),  # Fixed: 3 panels (price+volume, MACD, RSI)
            returnfig=True
        )
        
        plt.show()
    
    def plot_intraday(self, symbol: str, interval: str = '5m'):
        """
        Plot intraday chart (today's trading)
        
        Args:
            symbol: Ticker symbol
            interval: Data interval ('1m', '5m', '15m', '30m', '1h')
        """
        df = self.fetch_chart_data(symbol, period='1d', interval=interval)
        
        if df is None:
            return
        
        # Add moving averages
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA30'] = df['Close'].rolling(window=30).mean()
        
        apds = [
            mpf.make_addplot(df['MA10'], color='cyan', width=1),
            mpf.make_addplot(df['MA30'], color='orange', width=1),
        ]
        
        style = mpf.make_mpf_style(
            base_mpf_style='charles',
            marketcolors=mpf.make_marketcolors(
                up='green',
                down='red',
                edge='inherit',
                wick='inherit',
                volume='in'
            ),
            gridstyle=':',
            gridcolor='gray',
            facecolor='#1e1e1e',
            figcolor='#0e0e0e'
        )
        
        mpf.plot(
            df,
            type='candle',
            style=style,
            title=f"{symbol} - Intraday ({interval})",
            ylabel='Price ($)',
            volume=True,
            addplot=apds,
            figratio=(16, 9),
            figscale=1.2
        )
        
        plt.show()



if __name__ == "__main__":
    chart = ChartDisplay()
    # chart.plot_candlestick('BTC-USD', period='1mo', interval='1d', indicators=['sma'])
    # chart.plot_with_indicators('AAPL', period='3mo')
    # chart.plot_intraday('BTC-USD', interval='5m')
    logger.info("Chart display module ready")