"""
3D Volatility Surface Visualization
Lightweight matplotlib-based renderer for Options tab
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
import io


class VolatilitySurfaceVisualizer:
    """Create 3D volatility surface visualizations"""
    
    def __init__(self, df: pd.DataFrame, dark_theme: bool = True):
        self.df = df
        self.dark_theme = dark_theme
        self.setup_style()
    
    def setup_style(self):
        """Setup matplotlib style"""
        if self.dark_theme:
            plt.style.use('dark_background')
            self.bg_color = '#1a1a1a'
            self.grid_color = '#333333'
            self.text_color = '#ffffff'
        else:
            self.bg_color = 'white'
            self.grid_color = '#cccccc'
            self.text_color = '#000000'
    
    def create_static_surface(self, title: str = "BTC IV Surface",
                             elev: int = 25, azim: int = 235) -> bytes:
        """
        Create static 3D volatility surface
        Returns: PNG image data as bytes
        """
        if self.df.empty or len(self.df) < 10:
            raise ValueError("Insufficient data for surface plot")
        
        # Prepare data
        df = self.df.copy()
        
        # Filter valid data
        df = df[(df['iv'] > 0) & (df['iv'] < 3) & (df['dte'] > 0)]
        
        if len(df) < 10:
            raise ValueError("Insufficient valid data points")
        
        # Extract coordinates
        moneyness = df['strike'] / df['spot_close']
        dte = df['dte']
        iv = df['iv']
        
        # Create grid
        money_grid = np.linspace(moneyness.min(), moneyness.max(), 50)
        dte_grid = np.linspace(dte.min(), dte.max(), 50)
        money_mesh, dte_mesh = np.meshgrid(money_grid, dte_grid)
        
        # Interpolate
        points = np.column_stack([moneyness, dte])
        iv_mesh = griddata(points, iv, (money_mesh, dte_mesh), method='cubic')
        
        # Smooth
        iv_mesh = gaussian_filter(iv_mesh, sigma=1.5)
        
        # Plot
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')
        
        surf = ax.plot_surface(
            money_mesh, dte_mesh, iv_mesh,
            cmap='viridis',
            alpha=0.9,
            edgecolor='none'
        )
        
        # Styling
        ax.set_xlabel('Moneyness (K/S)', color=self.text_color, fontsize=10)
        ax.set_ylabel('Days to Expiry', color=self.text_color, fontsize=10)
        ax.set_zlabel('Implied Volatility', color=self.text_color, fontsize=10)
        ax.set_title(title, color=self.text_color, fontsize=12, pad=20)
        
        ax.view_init(elev=elev, azim=azim)
        ax.grid(True, alpha=0.3)
        
        # Colorbar
        cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
        cbar.set_label('IV', color=self.text_color, fontsize=9)
        cbar.ax.tick_params(labelsize=8, colors=self.text_color)
        
        # Background
        fig.patch.set_facecolor(self.bg_color)
        ax.set_facecolor(self.bg_color)
        
        ax.tick_params(colors=self.text_color, labelsize=8)
        
        # Save to bytes
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=100, facecolor=self.bg_color)
        plt.close(fig)
        
        buf.seek(0)
        return buf.read()


def create_simple_surface(df: pd.DataFrame) -> bytes:
    """
    Quick helper function for basic surface creation
    """
    viz = VolatilitySurfaceVisualizer(df, dark_theme=True)
    return viz.create_static_surface()