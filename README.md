# Terminal Trade

**Professional Desktop Trading Platform**

![Version](https://img.shields.io/badge/version-4.0.0-blue) ![Python](https://img.shields.io/badge/python-3.11+-green) ![License](https://img.shields.io/badge/license-MIT-orange) ![Status](https://img.shields.io/badge/status-beta-yellow)

> 💡 **Note:** This project is inspired by Bloomberg Terminal, built as a personal learning project using free APIs. It's a work in progress with UI/UX improvements and code optimizations ongoing. Contributions are very welcome!

---

## 📸 Screenshots

### Overview Tab - Market Data & Company Info
![Overview Tab](pictures/OV%20Tab.png)

### Financial Statements Analysis
![Financial Statements](pictures/FIN%20Subtab.png)

### Backtest Engine - Strategy Testing
![Backtest Tab](pictures/BT%20Tab.png)

### Options Analytics - Greeks & Volatility
![Options Tab](pictures/OP%20Tab.png)

### 3D Volatility Surface
![Volatility Surface](pictures/3D%20Vol%20Surface.png)

### Portfolio Management
![Portfolio Tab](pictures/PORT%20Tab.png)

---

## 🚀 Overview

A desktop trading terminal inspired by Bloomberg Terminal, built as a personal learning project using exclusively free APIs. This platform combines market data, backtesting, options analytics, and portfolio management in one unified interface.

**Creator:** [@letrinhandn](https://github.com/letrinhandn)  
**Status:** Beta - Active Development  
**License:** MIT - Free and Open Source

### ⚠️ Project Status

This is a **personal learning project** and **work in progress**:
- 🎨 UI/UX has some glitches and visual inconsistencies
- 🔧 Code is not 100% complete or optimized
- 📚 Documentation may be incomplete in some areas
- 🐛 Bugs and edge cases are being discovered and fixed
- ✨ Features and improvements are added regularly

**We welcome contributions!** Whether it's bug fixes, feature additions, UI improvements, or documentation - all help is appreciated. This is a community project built for learning and fun.



### ✨ Key Features (v4.0.0)

- 📈 **Real-time Market Data** - Live quotes, charts, and market analytics
- 📰 **Live News Feed** - RSS integration with 6+ professional sources 
- 💼 **Portfolio Management** - Track positions and performance
- 📊 **Options Analytics** - Greeks calculation and volatility analysis
- 🔄 **Backtesting Engine** - Multi-strategy testing framework
- 📋 **Company Research** - Fundamentals, financials, and news
- 🎯 **Professional UI** - Intuitive terminal-style interface
- ⚡ **High Performance** - Optimized for speed and reliability

### Data Sources

**Currently Using (All FREE):**
- **Deribit API** - Options data, Greeks, volatility analytics (no auth required)
- **yfinance** - Stock/crypto historical prices and market data
- **Finnhub Free Tier** - Company fundamentals (60 calls/min)
- **FRED API** - Economic indicators (optional)

**Future Roadmap:**
- Additional free APIs integration (Alpha Vantage, Polygon, etc.)
- Premium data sources (Coindesk, OptionMetrics, etc.) - optional
- Custom data connectors
- Real-time WebSocket feeds
- More brokers integration

> **Note:** This is a beta release focusing on free data sources. Paid APIs will be optional features in future versions.

---

## Quick Start

### Installation

```powershell
# Clone repository
git clone https://github.com/lenan/Terminal-Trade.git
cd Terminal-Trade

# Install dependencies
pip install -r requirements.txt

# Configure API keys (optional - some features work without keys)
cp .env.example .env
# Edit .env and add your free API keys
```

### 🚀 Launch Application

**Windows (Recommended):**
```bash
# Double-click to run
START_TERMINAL_TRADE.bat
```

**Python Direct:**
```bash
python run_app.py
```

**Alternative (Debug Mode):**
```bash
python -m src.app
```

---

## Configuration

### API Keys (All FREE to register)

Create a `.env` file for additional features:

| API Key | Purpose | Required | Free Tier |
|---------|---------|----------|-----------|
| `FINNHUB_API_KEY` | Company fundamentals | Optional | 60 calls/min |
| `FRED_API_KEY` | Economic data | Optional | Unlimited |

**No keys required for:**
- Deribit options data (public API)
- yfinance market data
- Basic backtesting features

### Future API Support

The platform is designed to support multiple data sources. Future versions may include:

- **Free APIs:** Alpha Vantage, Polygon.io, IEX Cloud (free tiers)
- **Premium APIs:** Optional paid features for advanced data
- **Broker APIs:** Interactive Brokers, TD Ameritrade, etc.
- **Custom connectors:** CSV imports, database connections

> Current version focuses on free data. Premium features will be opt-in only.

```
Terminal-Trade/
├── run_app.py                  # Main application entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # API key template (all FREE APIs)
│
├── backtest/                    # Backtesting engine
│   └── engine.py               # Core backtesting logic
│
├── strategies/                  # Trading strategies
│   ├── macd_strategy.py        # Simple MACD strategy
│   ├── macd_advanced.py        # Advanced MACD with filters
│   └── options_strategies.py  # Options-specific strategies
│
├── data/                        # Data management layer
│   ├── data_loader.py          # Multi-source data loader (Yahoo, Deribit, etc.)
│   └── cache_manager.py        # SQLite/Parquet caching system
│
├── realtime/                    # Real-time data processing
│   ├── price_viewer.py         # Live price feeds
│   ├── chart_display.py        # Chart rendering
│   ├── fundamentals.py         # Company fundamentals fetcher
│   └── tradingview_integration.py
│
├── metrics/                     # Performance metrics
│   ├── performance.py          # Sharpe, Sortino, drawdown calculations
│   └── options_metrics.py      # Greeks and IV calculations
│
├── ui/                          # User interface components
│   ├── terminal_v2.py          # CLI interface
│   └── visualizer.py           # Chart and graph generators
│
├── core/                        # Core utilities
│   ├── utils.py                # Helper functions
│   └── strategy_base.py        # Abstract strategy base class
│
└── config/                      # Configuration
    └── settings.py             # Application settings
```

---

## API Configuration

### FREE API Keys

This project uses **100% FREE APIs**. Create a `.env` file with the following keys:

| API Key | Purpose | Cost | Registration |
|---------|---------|------|--------------|
| `FINNHUB_API_KEY` | Company fundamentals, financial statements | 🆓 FREE (60 calls/min) | [finnhub.io](https://finnhub.io/) |
| `FRED_API_KEY` | Economic indicators (optional) | 🆓 FREE | [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html) |

**Note:** 
- **Deribit API** is FREE and requires no authentication for public market data (options chains, Greeks)
- **yfinance** is FREE for stock/crypto historical data
- All APIs used in this project are FREE - no paid subscriptions needed!

### Data Sources (All FREE!)

The application uses intelligent data routing with free APIs:

**Free Operations:**
- **Deribit API (FREE):** Options chain data, live Greeks, volatility analytics
- **yfinance (FREE):** Stock/crypto historical prices and market data  
- **Finnhub Free Tier (FREE):** Company fundamentals, financial statements (60 calls/min)
- **FRED API (FREE):** Economic indicators

**Features:**
- Auto-refresh options chain every 60s
- Volatility smile and term structure (live snapshots)
- Greeks monitoring (continuous updates)
- 3D volatility surface (using free Deribit current data)
- Local caching to minimize API calls

---

## Features Overview

### Options Analytics
- Real-time options chain with Greeks
- Volatility smile and term structure
- 3D volatility surface
- Strategy pricing calculator

### Backtesting Engine
- MACD and Advanced MACD strategies
- Custom strategy framework
- Performance metrics (Sharpe, Sortino, drawdown)
- Equity curve visualization

### Market Data
- Real-time quotes and charts
- Company fundamentals
- Financial statements (multi-period)
- News feed integration

### Terminal UI
- Command bar with autocomplete
- Multi-tab navigation
- Customizable layouts
- Professional dark theme

---

## Project Structure

**Core Modules:**
- `terminal_trade_desktop.py` - Main application entry
- `backtest/` - Backtesting engine
- `strategies/` - Trading strategies
- `data/` - Data loaders and cache
- `metrics/` - Performance calculations
- `ui/` - Interface components

See code for detailed structure.

---

## Contributing

**We'd love your help!** This is a learning project and contributions are very welcome.

**How to contribute:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Areas where we need help:**
- 🎨 UI/UX improvements and bug fixes
- 🔧 Code optimization and refactoring
- 📊 New data source integrations (free APIs preferred)
- 📈 Additional trading strategies
- 📚 Documentation improvements
- 🐛 Bug reports and fixes
- 💡 Feature suggestions and implementations

**All skill levels welcome!** Whether you're fixing a typo or adding a major feature, every contribution helps improve the project.

---

## Troubleshooting

**ModuleNotFoundError:**
```powershell
pip install -r requirements.txt
```

**API Authentication Errors:**
- Verify API keys in `.env` file
- Check key validity on provider websites (all are FREE to register)
- Ensure no extra spaces or quotes in `.env`
- Finnhub free tier: 60 calls/minute limit

**Rate Limit Exceeded:**
- Finnhub: Wait 1 minute or upgrade to paid tier (optional)
- Deribit: No rate limits on public data
- yfinance: No authentication required

**UI Not Responding:**
- Check terminal for error messages
- Verify PyQt6 installation
- Try: `pip install --upgrade PyQt6`

---

## License & Disclaimer

**License:** MIT - Free and open source

**Disclaimer:** 
- **Personal learning project** inspired by Bloomberg Terminal
- Built for **educational and experimental purposes only**
- **Not financial advice** - Do not use for real trading decisions
- **No guarantees** on data accuracy, performance, or reliability
- Use at your own risk - Creator assumes no liability
- This is a **fun project** using free APIs to learn and explore
- **Work in progress** - Expect bugs, glitches, and incomplete features

---

## About

**Project:** Terminal Trade  
**Inspiration:** Bloomberg Terminal (professional version)
**Creator:** [@letrinhandn](https://github.com/letrinhandn)  
**Version:** 4.0.0 (Beta)  
**Status:** Active Development

**Built with:**
- Python 3.11+ & PyQt6
- Free APIs: yfinance, Finnhub, Deribit, FRED
- Open-source libraries: pandas, matplotlib, plotly

**Acknowledgments:**
- Bloomberg Terminal for inspiration
- Open-source community (Python, PyQt6, pandas, matplotlib)
- Free API providers (Deribit, Finnhub, yfinance, FRED)
- All contributors and supporters

---

**Built with ❤️ for learning, fun, and the trading community**

---

*This is a beta project under active development. Features, UI, and code are being improved continuously. Contributions welcome!*