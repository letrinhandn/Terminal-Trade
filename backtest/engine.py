"""
Backtesting engine with realistic trade execution simulation.
Supports long-only strategies with configurable commission and slippage.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Single completed trade record."""

    entry_date:  datetime
    exit_date:   datetime
    entry_price: float
    exit_price:  float
    shares:      float = 1.0

    @property
    def return_pct(self) -> float:
        return ((self.exit_price - self.entry_price) / self.entry_price) * 100

    @property
    def profit_loss(self) -> float:
        return (self.exit_price - self.entry_price) * self.shares

    @property
    def holding_period(self) -> int:
        return (self.exit_date - self.entry_date).days

    def __str__(self) -> str:
        return (
            f"Trade: {self.entry_date.date()} to {self.exit_date.date()} | "
            f"P&L: {self.return_pct:.2f}% | {self.holding_period} days"
        )


class BacktestEngine:
    """
    Event-driven backtesting engine.

    Args:
        initial_capital: Starting capital in USD.
        commission: Round-trip commission as a fraction (0.001 = 0.1%).
        slippage: Execution slippage as a fraction.
    """

    def __init__(
        self,
        initial_capital: float = 10_000.0,
        commission: float = 0.0,
        slippage: float = 0.0,
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage   = slippage
        self._reset()

    def _reset(self) -> None:
        self.trades:        List[Trade] = []
        self.equity_curve:  List[float] = []
        self._in_position:  bool  = False
        self._entry_price:  float = 0.0
        self._entry_date:   Optional[datetime] = None
        self.current_capital = self.initial_capital

    def run(self, df: pd.DataFrame) -> dict:
        """
        Execute backtest on a DataFrame that already has a 'Signal' column.
        Signal values: 1=Buy, -1=Sell, 0=Hold.
        """
        self._reset()

        if 'Signal' not in df.columns:
            raise ValueError("DataFrame must have a 'Signal' column")
        if 'Close' not in df.columns:
            raise ValueError(
                f"DataFrame must have a 'Close' column. Got: {list(df.columns)}"
            )

        for i in range(len(df)):
            row    = df.iloc[i]
            signal = int(row['Signal'].item() if hasattr(row['Signal'], 'item') else row['Signal'])
            price  = float(row['Close'].item() if hasattr(row['Close'], 'item') else row['Close'])
            date   = row.name if isinstance(row.name, datetime) else datetime.now()

            exec_price = price * (1 + self.slippage * signal) if signal != 0 else price

            if signal == 1 and not self._in_position:
                self._in_position  = True
                self._entry_price  = exec_price
                self._entry_date   = date
                self.current_capital *= (1 - self.commission)

            elif signal == -1 and self._in_position:
                self._in_position = False
                trade = Trade(
                    entry_date  = self._entry_date,
                    exit_date   = date,
                    entry_price = self._entry_price,
                    exit_price  = exec_price,
                )
                self.trades.append(trade)
                self.current_capital *= (1 + trade.return_pct / 100) * (1 - self.commission)

            if self._in_position:
                mtm = (price - self._entry_price) / self._entry_price
                self.equity_curve.append(self.current_capital * (1 + mtm))
            else:
                self.equity_curve.append(self.current_capital)

        if self._in_position:
            last_price = float(df['Close'].iloc[-1])
            last_date  = df.index[-1] if isinstance(df.index[-1], datetime) else datetime.now()
            trade = Trade(
                entry_date  = self._entry_date,
                exit_date   = last_date,
                entry_price = self._entry_price,
                exit_price  = last_price,
            )
            self.trades.append(trade)
            self.current_capital *= (1 + trade.return_pct / 100)

        return self._generate_results()

    def _generate_results(self) -> dict:
        total_return = (
            (self.current_capital - self.initial_capital) / self.initial_capital * 100
        )
        winning = [t for t in self.trades if t.return_pct > 0]
        losing  = [t for t in self.trades if t.return_pct <= 0]
        n       = len(self.trades)

        return {
            'total_return':   total_return,
            'final_capital':  self.current_capital,
            'num_trades':     n,
            'win_rate':       len(winning) / n * 100 if n else 0,
            'num_winning':    len(winning),
            'num_losing':     len(losing),
            'avg_win':        sum(t.return_pct for t in winning) / len(winning) if winning else 0,
            'avg_loss':       sum(t.return_pct for t in losing)  / len(losing)  if losing  else 0,
            'max_drawdown':   self._max_drawdown(),
            'trades':         self.trades,
            'equity_curve':   self.equity_curve,
        }

    def _max_drawdown(self) -> float:
        if not self.equity_curve:
            return 0.0
        peak   = self.equity_curve[0]
        max_dd = 0.0
        for value in self.equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def get_trades(self) -> List[Trade]:
        return self.trades

    def get_equity_curve(self) -> List[float]:
        return self.equity_curve
