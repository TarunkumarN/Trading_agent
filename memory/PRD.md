# MiniMax Pro Trading Terminal - PRD

## Original Problem Statement
Audit and harden a trading bot from a public GitHub repository, then build a professional trading dashboard on top. The platform evolved to include advanced quant trading intelligence modules for institutional-grade trade quality.

## Architecture
```
/app
├── backend/
│   ├── ai/                          # AI Intelligence Modules
│   │   ├── market_predictor.py      # Short-term market direction prediction
│   │   └── trade_ranker.py          # 0-100 AI trade ranking engine
│   ├── market/                      # Market Analysis Modules
│   │   ├── options_flow.py          # Unusual options activity detection
│   │   ├── dark_pool_detector.py    # Institutional accumulation/distribution zones
│   │   └── correlation_filter.py    # Multi-asset correlation confirmation
│   ├── risk/                        # Risk Management
│   │   └── hedging_engine.py        # Portfolio hedging with exposure analysis
│   ├── quant/                       # Quant Pipeline
│   │   └── pipeline.py              # 10-step trade intelligence pipeline orchestrator
│   ├── dashboard/                   # API Routes
│   │   ├── api_server.py            # Route registration
│   │   ├── routes_analytics.py      # Strategy & AI endpoints
│   │   ├── routes_market.py         # Market data endpoints
│   │   ├── routes_portfolio.py      # Portfolio endpoints
│   │   ├── routes_quant.py          # Quant intelligence endpoints (8 new)
│   │   └── routes_trades.py         # Trade history endpoints
│   ├── strategies/                  # (Reserved for strategy modules)
│   ├── tests/                       # Test suite
│   │   ├── test_minimax_apis.py     # Core API tests
│   │   └── test_quant_intelligence.py  # Quant module tests
│   ├── server.py                    # Main FastAPI app + trading engine
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.js                   # React SPA (14 pages including Quant Intelligence)
│       └── App.css                  # Theme styles (light/dark)
└── memory/
    └── PRD.md
```

## What's Been Implemented

### Core Platform
- [x] Full-stack React + FastAPI + MongoDB trading platform
- [x] 14-page dashboard: Dashboard, Portfolio, Daily Report, System Health, Market Analysis, AI Brain, Quant Intelligence, Strategies, Positions, Trade History, Risk, F&O Calculator, Audit & Logs, Settings
- [x] Login authentication
- [x] Light/Dark mode toggle
- [x] SIM/LIVE mode switch
- [x] ₹50,000 initial capital
- [x] Mobile responsive UI

### Quant Intelligence Modules (NEW - Mar 2026)
- [x] **Options Flow Analysis** (`market/options_flow.py`): Detects unusual call/put buying, block trades, volume-price divergences
- [x] **Dark Pool Detection** (`market/dark_pool_detector.py`): Simulated institutional accumulation/distribution zones via volume clusters, VWAP deviations, absorption candles
- [x] **AI Market Predictor** (`ai/market_predictor.py`): 7-factor prediction model (EMA trend, RSI, VWAP, volume, momentum, BB, regime). Trade allowed only if confidence >= 65
- [x] **AI Trade Ranker** (`ai/trade_ranker.py`): 0-100 scoring across 6 components. Trade allowed only if score >= 85
- [x] **Correlation Filter** (`market/correlation_filter.py`): Multi-asset confirmation (NIFTY-BANKNIFTY, sector correlations, inverse correlations)
- [x] **Portfolio Hedging Engine** (`risk/hedging_engine.py`): Exposure analysis, hedge recommendations when bullish > 60%
- [x] **Trade Intelligence Pipeline** (`quant/pipeline.py`): 10-step sequential validation (time filter -> frequency -> regime -> dark pool -> options flow -> correlation -> AI prediction -> R:R check -> rank -> hedge)

### Trading Rules
- [x] Trading window: 09:30 - 14:45 IST
- [x] Max trades/day: 4
- [x] Max consecutive losses: 3
- [x] Daily drawdown limit: 4%
- [x] Minimum risk-reward: 1:2
- [x] Minimum trade rank score: 85/100

### API Endpoints (29 total)
Core: /api/data, /api/portfolio, /api/report/daily, /api/health, /api/risk, /api/config, /api/mode, /api/mode/switch, /api/auth/login, /api/market/live, /api/ai/regime, /api/ai-decisions, /api/strategies/performance, /api/open-positions, /api/trades, /api/fo/calculate, /api/audit, /api/logs
Quant: /api/quant/dashboard, /api/quant/pipeline/{symbol}, /api/quant/options-flow/{symbol}, /api/quant/dark-pool/{symbol}, /api/quant/ai-prediction/{symbol}, /api/quant/correlation/{symbol}, /api/quant/trade-rank/{symbol}, /api/quant/hedge-analysis, /api/quant/frequency-status

## Remaining / Backlog

### P0
- [ ] Live Trading Broker Integration (Zerodha Kite Connect) - actual order execution
- [ ] Live Market Data Feed (real-time NSE data instead of fallback/seeded)

### P1
- [ ] Commodity strategies (Gold, Silver, Crude Oil) implementation
- [ ] Telegram bot commands (/status, /positions, /halt)
- [ ] Backtesting module with historical data

### P2
- [ ] Export trade history to CSV/Excel
- [ ] Portfolio allocation optimization
- [ ] Real-time WebSocket price feed
- [ ] MiniMax AI brain integration for live signal refinement
