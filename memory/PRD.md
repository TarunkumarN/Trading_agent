# MiniMax Pro Trading Terminal - PRD

## Original Problem Statement
Audit and harden a trading bot from a public GitHub repository, then build a professional trading dashboard on top. The platform evolved to include advanced quant trading intelligence modules for institutional-grade trade quality.

## Architecture
```
/app
├── backend/
│   ├── ai/                          # AI Intelligence Modules
│   │   ├── market_predictor.py      # Short-term market direction prediction (7 factors)
│   │   └── trade_ranker.py          # 0-100 AI trade ranking (6 components, min 85)
│   ├── market/                      # Market Analysis Modules
│   │   ├── options_flow.py          # Unusual options activity detection
│   │   ├── dark_pool_detector.py    # Institutional accumulation/distribution zones
│   │   └── correlation_filter.py    # Multi-asset correlation confirmation
│   ├── risk/                        # Risk Management
│   │   └── hedging_engine.py        # Portfolio hedging with exposure analysis
│   ├── data/                        # Data Modules
│   │   └── contract_resolver.py     # F&O contract resolution (CE/PE, strikes, expiry, lot sizes)
│   ├── quant/                       # Quant Pipeline
│   │   └── pipeline.py              # 10-step trade intelligence pipeline orchestrator
│   ├── dashboard/                   # API Routes
│   │   ├── api_server.py            # Route registration
│   │   ├── routes_analytics.py      # Strategy & AI endpoints
│   │   ├── routes_market.py         # Market data endpoints
│   │   ├── routes_portfolio.py      # Portfolio endpoints
│   │   ├── routes_quant.py          # Quant intelligence endpoints (12 total)
│   │   └── routes_trades.py         # Trade history endpoints
│   ├── strategies/                  # (Reserved for strategy modules)
│   ├── tests/                       # Test suite
│   │   ├── test_minimax_apis.py
│   │   ├── test_quant_intelligence.py
│   │   └── test_contract_resolution_charts.py
│   ├── server.py                    # Main FastAPI app + trading engine
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.js                   # React SPA (15 pages including Quant Intelligence)
│       └── App.css                  # Theme styles (light/dark)
└── memory/
    └── PRD.md
```

## What's Been Implemented

### Core Platform
- [x] Full-stack React + FastAPI + MongoDB trading platform
- [x] 15-page dashboard (Dashboard, Portfolio, Daily Report, System Health, Market Analysis, AI Brain, Quant Intelligence, Strategies, Positions, Trade History, Risk, F&O Calculator, Audit & Logs, Settings)
- [x] Login authentication (admin/minimax123)
- [x] Light/Dark mode toggle
- [x] SIM/LIVE mode switch
- [x] ₹50,000 initial capital

### Quant Intelligence Modules
- [x] Options Flow Analysis
- [x] Dark Pool Detection (simulated)
- [x] AI Market Predictor (7-factor, confidence >= 65 required)
- [x] AI Trade Ranker (0-100, min 85 required)
- [x] Multi-Asset Correlation Filter
- [x] Portfolio Hedging Engine
- [x] 10-step Trade Intelligence Pipeline

### F&O Contract Resolution (NEW)
- [x] BUY signal → CE (Call), SELL signal → PE (Put)
- [x] NSE equity lot sizes (RELIANCE:250, TCS:150, HDFCBANK:550, etc.)
- [x] Index lot sizes (NIFTY:25, BANKNIFTY:15)
- [x] Commodity specs (GOLD, SILVER, CRUDEOIL)
- [x] ATM strike calculation with proper intervals
- [x] Weekly/Monthly expiry resolution
- [x] Premium estimation and capital requirements
- [x] Pipeline integration: contract appears after pipeline pass

### Market Charts (NEW)
- [x] NIFTY 50 intraday area chart (5-min candles, 09:15-15:30)
- [x] BANK NIFTY intraday area chart
- [x] Stock sparklines for 8 watchlist stocks
- [x] Individual stock OHLCV chart endpoint (intraday + daily)
- [x] Full-day data generation for consistent charts

### Trading Rules
- [x] Trading window: 09:30 - 14:45 IST
- [x] Max trades/day: 4
- [x] Max consecutive losses: 3
- [x] Daily drawdown limit: 4%
- [x] Minimum risk-reward: 1:2
- [x] Minimum trade rank score: 85/100

### API Endpoints (33 total)
Core: /api/data, /api/portfolio, /api/report/daily, /api/health, /api/risk, /api/config, /api/mode, /api/mode/switch, /api/auth/login, /api/market/live, /api/ai/regime, /api/ai-decisions, /api/strategies/performance, /api/open-positions, /api/trades, /api/fo/calculate, /api/audit, /api/logs
Quant: /api/quant/dashboard, /api/quant/pipeline/{symbol}, /api/quant/pipeline-full/{symbol}, /api/quant/options-flow/{symbol}, /api/quant/dark-pool/{symbol}, /api/quant/ai-prediction/{symbol}, /api/quant/correlation/{symbol}, /api/quant/trade-rank/{symbol}, /api/quant/contract/{symbol}, /api/quant/hedge-analysis, /api/quant/frequency-status
Charts: /api/market/chart/{symbol}, /api/market/charts-summary

## Remaining / Backlog

### P0
- [ ] Live Trading Broker Integration (Zerodha Kite Connect) - actual order execution
- [ ] Live Market Data Feed (real-time NSE data instead of fallback/seeded)

### P1
- [ ] Commodity strategies (Gold, Silver, Crude Oil) - VWAP, liquidity sweeps, range breakouts
- [ ] Telegram bot commands (/status, /positions, /halt)
- [ ] Backtesting module with historical data

### P2
- [ ] Export trade history to CSV/Excel
- [ ] Portfolio allocation optimization
- [ ] Real-time WebSocket price feed
- [ ] MiniMax AI brain integration for live signal refinement
