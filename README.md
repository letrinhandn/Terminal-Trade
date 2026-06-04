# Terminal Trade

A desktop trading research terminal built with Python and PyQt6. Combines market data, options analytics, strategy backtesting, and portfolio management in a single interface modelled on professional terminal conventions.

---

## Screenshots

| Overview | Financial Statements |
|---|---|
| ![Overview](pictures/OV%20Tab.png) | ![Financials](pictures/FIN%20Subtab.png) |

| Backtest | Options Chain |
|---|---|
| ![Backtest](pictures/BT%20Tab.png) | ![Options](pictures/OP%20Tab.png) |

| 3D Volatility Surface | Portfolio |
|---|---|
| ![Vol Surface](pictures/3D%20Vol%20Surface.png) | ![Portfolio](pictures/PORT%20Tab.png) |

---

## Features

**Market data** — live quotes, OHLCV history, company fundamentals and financial statements, RSS news feed.

**Options analytics** — live options chain with Greeks (delta, gamma, theta, vega), volatility smile, term structure, 3D volatility surface, Black-Scholes pricer.

**Backtesting** — event-driven engine with configurable commission and slippage. Included strategies: MACD crossover, advanced MACD with filters, RSI mean-reversion. Outputs equity curve, Sharpe, Sortino, max drawdown, win rate.

**Portfolio** — position tracking with P&L and backtest comparison.

**Interface** — command bar with autocomplete, multi-tab navigation, dark theme.

---

## Architecture

```
Terminal-Trade/
├── run_app.py
├── config/
│   └── settings.py              # All tunable constants and API config
├── data/
│   ├── data_loader.py           # Loader hierarchy: Yahoo, Alpha Vantage, Binance, Deribit
│   └── cache_manager.py         # Parquet-backed local cache with merge-on-write
├── backtest/
│   └── engine.py                # Event-driven backtesting engine
├── strategies/
│   ├── macd_strategy.py         # MACD and RSI implementations
│   ├── macd_advanced.py         # MACD with volume/trend filters
│   └── options_strategies.py   # Options-specific payoff strategies
├── metrics/
│   ├── performance.py           # Sharpe, Sortino, drawdown, win rate
│   └── options_metrics.py       # Greeks and IV (Black-Scholes)
├── core/
│   ├── strategy_base.py         # Abstract base for all strategies
│   └── utils.py                 # Shared formatting and validation helpers
├── realtime/
│   ├── orchestrator.py          # Coordinates live data refresh
│   ├── chart_display.py         # Matplotlib/Plotly chart rendering
│   ├── fundamentals.py          # Finnhub fundamentals fetcher
│   └── clients/
│       └── deribit_client.py    # Deribit WebSocket/REST client
├── src/
│   ├── app.py                   # Application root, tab routing, command dispatch
│   ├── tabs/                    # One file per main tab
│   └── widgets/                 # Reusable UI components
└── ui/
    ├── terminal_v2.py           # CLI interface layer
    └── visualizer.py            # Chart and graph builders
```

---

## Setup

```bash
git clone https://github.com/letrinhandn/Terminal-Trade.git
cd Terminal-Trade
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your API keys (see below), then:

```bash
python run_app.py
```

On Windows, `START_TERMINAL_TRADE.bat` is provided as a convenience launcher.

---

## Data Sources

| Source | Usage | Auth |
|---|---|---|
| yfinance | OHLCV history, company info | None |
| Deribit public API | Options chain, Greeks, IV | None |
| Finnhub | Fundamentals, financial statements | API key |
| FRED | Economic indicators | API key (optional) |

API keys are read from `.env` via python-dotenv. The application starts without any keys; features depending on Finnhub or FRED degrade gracefully when unconfigured.

---

## Extending

**New data source**: subclass `DataLoader` in `data/data_loader.py`, implement `load()`, register in `get_data_loader()`.

**New strategy**: subclass `BaseStrategy` in `core/strategy_base.py`, implement `calculate_indicators()` and `generate_signals()`. The backtest engine picks up any `BaseStrategy` subclass without modification.

---

## Known Limitations

- Deribit provides a point-in-time options snapshot, not a historical series. Backtesting options strategies with this data produces results that do not reflect real trading performance.
- Finnhub free tier is limited to 60 requests per minute. Rapid tab switching may hit this ceiling.
- The backtesting engine is long-only. Short selling and fractional position sizing are not implemented.

---

## License

MIT. See `LICENSE`.

**This project is for research and educational purposes. Nothing here constitutes financial advice.**
