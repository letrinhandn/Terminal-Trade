"""
Visualization module for backtest results.
Creates charts and plots for equity curves, drawdowns, and performance analysis.
"""

import logging
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Set style
plt.style.use('seaborn-v0_8-darkgrid')  # Use matplotlib built-in style
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10


class BacktestVisualizer:
    """Creates visualizations for backtest results"""
    
    def __init__(self):
        self.colors = {
            'equity': '#2E86AB',
            'drawdown': '#A23B72',
            'buy': '#06A77D',
            'sell': '#D62246',
            'benchmark': '#F77F00',
        }
    
    def plot_equity_curve(self, equity_curve: List[float], 
                         benchmark_curve: Optional[List[float]] = None,
                         trades: Optional[List] = None,
                         title: str = "Equity Curve"):
        """
        Plot equity curve with optional benchmark and trade markers.
        
        Args:
            equity_curve: List of equity values over time
            benchmark_curve: Optional buy-and-hold equity curve
            trades: Optional list of Trade objects to mark on chart
            title: Chart title
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                        gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot equity curve
        dates = range(len(equity_curve))
        ax1.plot(dates, equity_curve, label='Strategy', 
                color=self.colors['equity'], linewidth=2)
        
        if benchmark_curve:
            ax1.plot(dates, benchmark_curve, label='Buy & Hold', 
                    color=self.colors['benchmark'], linewidth=2, alpha=0.7, linestyle='--')
        
        # Mark trades
        if trades:
            for trade in trades:
                # This is simplified - in real implementation, 
                # we'd need to map trade dates to equity curve indices
                pass
        
        ax1.set_title(title, fontsize=16, fontweight='bold')
        ax1.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax1.legend(loc='upper left', fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Plot drawdown
        drawdowns = self._calculate_drawdowns(equity_curve)
        ax2.fill_between(dates, drawdowns, 0, 
                         color=self.colors['drawdown'], alpha=0.3)
        ax2.plot(dates, drawdowns, color=self.colors['drawdown'], linewidth=1.5)
        ax2.set_xlabel('Time Period', fontsize=12)
        ax2.set_ylabel('Drawdown (%)', fontsize=12)
        ax2.set_title('Drawdown Over Time', fontsize=14)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_trade_analysis(self, trades: List, initial_capital: float = 10000):
        """
        Plot trade analysis including win/loss distribution and returns.
        
        Args:
            trades: List of Trade objects
            initial_capital: Starting capital
        """
        if not trades:
            logger.debug("No trades to visualize")
            return None
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        # Extract trade data
        returns = [t.return_pct for t in trades]
        holding_periods = [t.holding_period for t in trades]
        profits = [t.profit_loss for t in trades]
        
        # 1. Returns distribution
        ax1.hist(returns, bins=20, color=self.colors['equity'], alpha=0.7, edgecolor='black')
        ax1.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax1.set_xlabel('Return (%)', fontsize=11)
        ax1.set_ylabel('Frequency', fontsize=11)
        ax1.set_title('Trade Returns Distribution', fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # 2. Win/Loss pie chart
        wins = sum(1 for r in returns if r > 0)
        losses = sum(1 for r in returns if r < 0)
        breakeven = len(returns) - wins - losses
        
        sizes = [wins, losses, breakeven] if breakeven > 0 else [wins, losses]
        labels = ['Wins', 'Losses', 'Breakeven'] if breakeven > 0 else ['Wins', 'Losses']
        colors_pie = [self.colors['buy'], self.colors['sell'], '#FFB703'] if breakeven > 0 else [self.colors['buy'], self.colors['sell']]
        
        ax2.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%',
               startangle=90, textprops={'fontsize': 11})
        ax2.set_title(f'Win/Loss Ratio ({wins}W / {losses}L)', fontsize=13, fontweight='bold')
        
        # 3. Cumulative P&L
        cumulative_pnl = np.cumsum(profits)
        ax3.plot(cumulative_pnl, color=self.colors['equity'], linewidth=2, marker='o', markersize=4)
        ax3.axhline(y=0, color='red', linestyle='--', linewidth=1)
        ax3.set_xlabel('Trade Number', fontsize=11)
        ax3.set_ylabel('Cumulative P&L ($)', fontsize=11)
        ax3.set_title('Cumulative Profit/Loss', fontsize=13, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.fill_between(range(len(cumulative_pnl)), cumulative_pnl, 0, 
                         alpha=0.3, color=self.colors['equity'])
        
        # 4. Holding period vs Return
        colors_scatter = [self.colors['buy'] if r > 0 else self.colors['sell'] for r in returns]
        ax4.scatter(holding_periods, returns, c=colors_scatter, alpha=0.6, s=100, edgecolors='black')
        ax4.axhline(y=0, color='red', linestyle='--', linewidth=1)
        ax4.set_xlabel('Holding Period (days)', fontsize=11)
        ax4.set_ylabel('Return (%)', fontsize=11)
        ax4.set_title('Holding Period vs Return', fontsize=13, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_strategy_comparison(self, comparison_data: pd.DataFrame):
        """
        Plot comparison of multiple strategies.
        
        Args:
            comparison_data: DataFrame with strategy comparison results
        """
        if comparison_data.empty:
            logger.debug("No data to compare")
            return None
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        strategies = comparison_data['Strategy'].tolist()
        
        # 1. Returns comparison
        returns = comparison_data['Avg Return (%)'].tolist()
        colors_bar = [self.colors['buy'] if r > 0 else self.colors['sell'] for r in returns]
        ax1.barh(strategies, returns, color=colors_bar, edgecolor='black')
        ax1.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax1.set_xlabel('Return (%)', fontsize=11)
        ax1.set_title('Strategy Returns Comparison', fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='x')
        
        # 2. Sharpe ratio comparison
        sharpe = comparison_data['Avg Sharpe'].tolist()
        ax2.bar(strategies, sharpe, color=self.colors['equity'], edgecolor='black', alpha=0.7)
        ax2.axhline(y=0, color='red', linestyle='--', linewidth=2)
        ax2.set_ylabel('Sharpe Ratio', fontsize=11)
        ax2.set_title('Risk-Adjusted Returns (Sharpe)', fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Max Drawdown comparison
        drawdowns = comparison_data['Avg Max DD (%)'].tolist()
        ax3.bar(strategies, drawdowns, color=self.colors['drawdown'], edgecolor='black', alpha=0.7)
        ax3.set_ylabel('Max Drawdown (%)', fontsize=11)
        ax3.set_title('Maximum Drawdown', fontsize=13, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')
        ax3.tick_params(axis='x', rotation=45)
        ax3.invert_yaxis()  # More negative = worse
        
        # 4. Win Rate comparison
        win_rates = comparison_data['Avg Win Rate (%)'].tolist()
        ax4.bar(strategies, win_rates, color=self.colors['buy'], edgecolor='black', alpha=0.7)
        ax4.axhline(y=50, color='orange', linestyle='--', linewidth=2, label='50% threshold')
        ax4.set_ylabel('Win Rate (%)', fontsize=11)
        ax4.set_title('Win Rate Comparison', fontsize=13, fontweight='bold')
        ax4.set_ylim(0, 100)
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.tick_params(axis='x', rotation=45)
        ax4.legend()
        
        plt.tight_layout()
        return fig
    
    def plot_comparison_equity_curves(self, equity_curves_dict: Dict[str, List],
                                     title: str = "Strategy Comparison - Equity Curves"):
        """
        Plot multiple equity curves overlaid on the same chart.
        
        Args:
            equity_curves_dict: Dictionary {strategy_name: [equity_curve1, equity_curve2, ...]}
            title: Chart title
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Color palette for different strategies
        colors = ['#2E86AB', '#A23B72', '#06A77D', '#F77F00', '#D62246', 
                 '#6A4C93', '#1982C4', '#8AC926', '#FF595E', '#FFCA3A']
        
        max_length = 0
        
        for idx, (strategy_name, equity_curves) in enumerate(equity_curves_dict.items()):
            color = colors[idx % len(colors)]
            
            # If multiple curves (multiple symbols), average them
            if len(equity_curves) > 1:
                # Normalize all curves to same length
                max_len = max(len(curve) for curve in equity_curves)
                max_length = max(max_length, max_len)
                
                # Normalize each curve to percentage returns
                normalized_curves = []
                for curve in equity_curves:
                    initial = curve[0]
                    pct_curve = [(val / initial - 1) * 100 for val in curve]
                    # Pad if needed
                    if len(pct_curve) < max_len:
                        pct_curve += [pct_curve[-1]] * (max_len - len(pct_curve))
                    normalized_curves.append(pct_curve)
                
                # Average the normalized curves
                avg_curve = [sum(vals) / len(vals) for vals in zip(*normalized_curves)]
                
                ax.plot(range(len(avg_curve)), avg_curve, 
                       label=f'{strategy_name} (avg {len(equity_curves)} symbols)',
                       color=color, linewidth=2.5, alpha=0.8)
            else:
                # Single curve - normalize to percentage
                curve = equity_curves[0]
                max_length = max(max_length, len(curve))
                initial = curve[0]
                pct_curve = [(val / initial - 1) * 100 for val in curve]
                
                ax.plot(range(len(pct_curve)), pct_curve,
                       label=strategy_name,
                       color=color, linewidth=2.5, alpha=0.8)
        
        # Formatting
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.7)
        ax.set_xlabel('Time (bars)', fontsize=12)
        ax.set_ylabel('Return (%)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=10, framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        # Add info text
        info_text = f'Comparing {len(equity_curves_dict)} strategies over {max_length} bars'
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
               fontsize=9, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        plt.tight_layout()
        return fig
    
    def plot_monthly_returns(self, equity_curve: List[float], start_date: str):
        """
        Plot monthly returns heatmap.
        
        Args:
            equity_curve: List of equity values
            start_date: Starting date (YYYY-MM-DD)
        """
        # This is a simplified version
        # In real implementation, we'd need actual dates for each equity point
        fig, ax = plt.subplots(figsize=(14, 6))
        
        ax.text(0.5, 0.5, 'Monthly Returns Heatmap\n(Requires date-aligned data)', 
               ha='center', va='center', fontsize=14)
        ax.set_title('Monthly Returns Analysis', fontsize=16, fontweight='bold')
        
        return fig
    
    def _calculate_drawdowns(self, equity_curve: List[float]) -> List[float]:
        """Calculate drawdown percentages from equity curve"""
        peak = equity_curve[0]
        drawdowns = []
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = ((value - peak) / peak) * 100 if peak > 0 else 0
            drawdowns.append(dd)
        
        return drawdowns
    
    def plot_options_payoff(self, strategy, current_price: float, 
                           price_range: Optional[Tuple[float, float]] = None,
                           title: str = "Options Strategy Payoff Diagram"):
        """
        Plot payoff diagram for an options strategy.
        
        Args:
            strategy: OptionsStrategy instance
            current_price: Current underlying price
            price_range: (min_price, max_price) or None for auto
            title: Chart title
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Determine price range
        if price_range is None:
            min_price = current_price * 0.7
            max_price = current_price * 1.3
        else:
            min_price, max_price = price_range
        
        # Get payoff data
        prices, payoffs = strategy.get_payoff_range(min_price, max_price, num_points=200)
        
        # Plot payoff line
        colors = ['red' if p < 0 else 'green' for p in payoffs]
        ax.plot(prices, payoffs, linewidth=3, color='blue', label='Payoff at Expiration')
        
        # Fill profit/loss areas
        ax.fill_between(prices, payoffs, 0, where=[p >= 0 for p in payoffs], 
                        alpha=0.3, color='green', label='Profit Zone')
        ax.fill_between(prices, payoffs, 0, where=[p < 0 for p in payoffs], 
                        alpha=0.3, color='red', label='Loss Zone')
        
        # Mark current price
        current_payoff = strategy.calculate_payoff(current_price)
        ax.axvline(x=current_price, color='orange', linestyle='--', linewidth=2, 
                  label=f'Current Price: ${current_price:,.2f}')
        ax.plot([current_price], [current_payoff], 'o', markersize=10, color='orange')
        
        # Mark breakeven points
        breakevens = strategy.get_breakeven_points()
        for be in breakevens:
            if min_price <= be <= max_price:
                ax.axvline(x=be, color='gray', linestyle=':', linewidth=1.5, alpha=0.7)
                ax.text(be, ax.get_ylim()[1] * 0.9, f'BE: ${be:,.0f}', 
                       rotation=90, va='top', ha='right', fontsize=9)
        
        # Mark strikes if available
        if hasattr(strategy, 'legs') and strategy.legs:
            for leg in strategy.legs:
                strike = leg['strike']
                if min_price <= strike <= max_price:
                    ax.axvline(x=strike, color='purple', linestyle='-.', linewidth=1, alpha=0.5)
        
        # Zero line
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
        
        # Formatting
        ax.set_xlabel('Underlying Price at Expiration ($)', fontsize=12)
        ax.set_ylabel('Profit / Loss ($)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Add info box
        max_profit = strategy.get_max_profit()
        max_loss = strategy.get_max_loss()
        info_text = f'Max Profit: ${max_profit:,.2f}\nMax Loss: ${max_loss:,.2f}'
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        return fig
    
    def plot_greeks_surface(self, strikes: List[float], prices: List[float],
                           greeks_matrix: Dict[str, List[List[float]]],
                           greek_name: str = 'delta',
                           title: str = "Greeks Surface"):
        """
        Plot 2D surface/heatmap of a Greek across strikes and prices.
        
        Args:
            strikes: List of strike prices
            prices: List of underlying prices
            greeks_matrix: Dict with greek names as keys, 2D arrays as values
            greek_name: Which Greek to plot
            title: Chart title
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        greek_data = greeks_matrix.get(greek_name)
        if greek_data is None:
            ax.text(0.5, 0.5, f'No data for {greek_name}', 
                   ha='center', va='center', fontsize=14)
            return fig
        
        # Create heatmap
        import matplotlib.colors as mcolors
        
        # Determine color map based on Greek
        if greek_name in ['delta', 'gamma', 'vega']:
            cmap = 'RdYlGn'
        else:  # theta, rho
            cmap = 'RdYlBu_r'
        
        im = ax.imshow(greek_data, cmap=cmap, aspect='auto', origin='lower',
                      extent=[min(prices), max(prices), min(strikes), max(strikes)])
        
        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(greek_name.capitalize(), fontsize=12)
        
        # Contour lines
        contour = ax.contour(greek_data, levels=10, colors='black', alpha=0.3,
                            extent=[min(prices), max(prices), min(strikes), max(strikes)])
        ax.clabel(contour, inline=True, fontsize=8)
        
        # Formatting
        ax.set_xlabel('Underlying Price ($)', fontsize=12)
        ax.set_ylabel('Strike Price ($)', fontsize=12)
        ax.set_title(f'{title} - {greek_name.capitalize()}', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def plot_iv_smile(self, strikes: List[float], ivs: List[float],
                     current_price: float, expiry: str,
                     title: str = "Implied Volatility Smile"):
        """
        Plot implied volatility smile/skew.
        
        Args:
            strikes: List of strike prices
            ivs: List of implied volatilities (decimals, e.g., 0.25 for 25%)
            current_price: Current underlying price
            expiry: Expiration date string
            title: Chart title
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Convert to percentages
        iv_pct = [iv * 100 for iv in ivs]
        
        # Calculate moneyness (Strike/Spot)
        moneyness = [k / current_price for k in strikes]
        
        # Plot IV vs Strike
        ax.plot(strikes, iv_pct, 'o-', linewidth=2, markersize=8, 
               color=self.colors['equity'], label='Implied Volatility')
        
        # Mark ATM
        ax.axvline(x=current_price, color='orange', linestyle='--', linewidth=2,
                  label=f'Current Price: ${current_price:,.0f}')
        
        # Formatting
        ax.set_xlabel('Strike Price ($)', fontsize=12)
        ax.set_ylabel('Implied Volatility (%)', fontsize=12)
        ax.set_title(f'{title} - Expiry: {expiry}', fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Add secondary x-axis for moneyness
        ax2 = ax.twiny()
        ax2.set_xlim(ax.get_xlim())
        ax2.set_xlabel('Moneyness (K/S)', fontsize=11, color='gray')
        moneyness_ticks = [0.8, 0.9, 1.0, 1.1, 1.2]
        ax2.set_xticks([m * current_price for m in moneyness_ticks])
        ax2.set_xticklabels([f'{m:.2f}' for m in moneyness_ticks])
        
        plt.tight_layout()
        return fig
    
    def plot_options_chain(self, options_df: pd.DataFrame, 
                          current_price: float,
                          title: str = "Options Chain"):
        """
        Plot options chain with bid/ask, volume, OI.
        
        Args:
            options_df: DataFrame with columns: strike, type, bid, ask, volume, oi, iv
            current_price: Current underlying price
            title: Chart title
            
        Returns:
            Matplotlib figure
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
        
        # Separate calls and puts
        calls = options_df[options_df['type'] == 'call'].sort_values('strike')
        puts = options_df[options_df['type'] == 'put'].sort_values('strike')
        
        # 1. Bid-Ask spread
        if not calls.empty:
            ax1.plot(calls['strike'], calls['bid'], 'g-', label='Call Bid', linewidth=2)
            ax1.plot(calls['strike'], calls['ask'], 'g--', label='Call Ask', linewidth=2, alpha=0.7)
        if not puts.empty:
            ax1.plot(puts['strike'], puts['bid'], 'r-', label='Put Bid', linewidth=2)
            ax1.plot(puts['strike'], puts['ask'], 'r--', label='Put Ask', linewidth=2, alpha=0.7)
        
        ax1.axvline(x=current_price, color='orange', linestyle='--', linewidth=2)
        ax1.set_xlabel('Strike Price', fontsize=11)
        ax1.set_ylabel('Option Price ($)', fontsize=11)
        ax1.set_title('Option Prices', fontsize=12, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # 2. Volume
        if not calls.empty:
            ax2.bar(calls['strike'], calls['volume'], alpha=0.7, color='green', 
                   label='Call Volume', width=calls['strike'].diff().median())
        if not puts.empty:
            ax2.bar(puts['strike'], -puts['volume'], alpha=0.7, color='red', 
                   label='Put Volume', width=puts['strike'].diff().median())
        
        ax2.axvline(x=current_price, color='orange', linestyle='--', linewidth=2)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax2.set_xlabel('Strike Price', fontsize=11)
        ax2.set_ylabel('Volume', fontsize=11)
        ax2.set_title('Volume Distribution', fontsize=12, fontweight='bold')
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3)
        
        # 3. Open Interest
        if not calls.empty:
            ax3.bar(calls['strike'], calls['open_interest'], alpha=0.7, color='green', 
                   label='Call OI', width=calls['strike'].diff().median())
        if not puts.empty:
            ax3.bar(puts['strike'], -puts['open_interest'], alpha=0.7, color='red', 
                   label='Put OI', width=puts['strike'].diff().median())
        
        ax3.axvline(x=current_price, color='orange', linestyle='--', linewidth=2)
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax3.set_xlabel('Strike Price', fontsize=11)
        ax3.set_ylabel('Open Interest', fontsize=11)
        ax3.set_title('Open Interest', fontsize=12, fontweight='bold')
        ax3.legend(fontsize=9)
        ax3.grid(True, alpha=0.3)
        
        # 4. Implied Volatility
        if not calls.empty and 'iv' in calls.columns:
            ax4.plot(calls['strike'], calls['iv'] * 100, 'go-', label='Call IV', linewidth=2)
        if not puts.empty and 'iv' in puts.columns:
            ax4.plot(puts['strike'], puts['iv'] * 100, 'ro-', label='Put IV', linewidth=2)
        
        ax4.axvline(x=current_price, color='orange', linestyle='--', linewidth=2, 
                   label=f'Spot: ${current_price:,.0f}')
        ax4.set_xlabel('Strike Price', fontsize=11)
        ax4.set_ylabel('Implied Volatility (%)', fontsize=11)
        ax4.set_title('IV Smile', fontsize=12, fontweight='bold')
        ax4.legend(fontsize=9)
        ax4.grid(True, alpha=0.3)
        
        plt.suptitle(title, fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        return fig
    
    def show_plot(self, fig):
        """Display the plot"""
        if fig:
            plt.show()
    
    def save_plot(self, fig, filename: str):
        """Save plot to file"""
        if fig:
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            logger.info("Plot saved to %s", filename)


def plot_backtest_results(backtest_results: dict, title: str = "Backtest Results"):
    """
    Quick function to plot backtest results.
    
    Args:
        backtest_results: Results dictionary from BacktestEngine
        title: Plot title
    """
    visualizer = BacktestVisualizer()
    
    # Plot equity curve
    fig1 = visualizer.plot_equity_curve(
        backtest_results['equity_curve'],
        title=title
    )
    visualizer.show_plot(fig1)
    
    # Plot trade analysis if trades exist
    if backtest_results.get('trades'):
        fig2 = visualizer.plot_trade_analysis(
            backtest_results['trades'],
            backtest_results['equity_curve'][0]
        )
        visualizer.show_plot(fig2)