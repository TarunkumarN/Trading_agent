# MiniMax Scalping Agent — PRD

## Original Problem Statement
Audit and harden the TarunkumarN/Trading_agent repository for production trading. Build a professional monitoring dashboard with analytics interface. Zerodha broker, NSE/BSE India market, paper trading mode. Extended with: dashboard/ folder structure, pre/post market analysis, AI brain decisions, bigger fonts, mobile responsive.

## Architecture
- **Backend**: FastAPI (Python) on port 8001 with modular dashboard/ routes
- **Frontend**: React dashboard on port 3000 (responsive, Chivo + JetBrains Mono fonts)
- **Database**: MongoDB (minimax_trading) — 8 collections
- **Broker**: Zerodha Kite Connect
- **Market**: NSE/BSE India (9:15 AM - 3:30 PM IST)

## User Personas
- Indian retail trader running automated scalping bot
- Algo trading enthusiast monitoring performance via dashboard (desktop + mobile)

## Dashboard Folder Structure
```
/app/backend/dashboard/
├── __init__.py
├── api_server.py              # Router registration
├── routes_portfolio.py        # /api/portfolio, /api/open-positions
├── routes_trades.py           # /api/trades, /api/trades/{trade_id}
├── routes_market.py           # /api/market/premarket, /postmarket, /gainers, /losers, /active
├── routes_analytics.py        # /api/strategies/performance, /api/ai-decisions, /api/analytics/summary
├── templates/                 # HTML templates (for standalone mode)
└── static/
    ├── dashboard.css          # Custom styles
    └── charts.js              # Chart.js configurations
```

## What's Been Implemented

### Phase 1 (2026-03-10) — System Audit & Hardening
- Full system audit: 14 issues identified and FIXED
- MongoDB state persistence (8 collections)
- Duplicate order prevention, 3-retry logic, risk controls
- Market hours enforcement, trailing SL, drawdown detection

### Phase 2 (2026-03-10) — Dashboard Extension
- Created dashboard/ folder with modular route files
- **Portfolio Page**: Equity curve, daily P&L chart, metrics (win rate, profit factor, max drawdown, avg profit/loss)
- **AI Brain Page**: 6-step reasoning chain per trade, confidence bars, accuracy stats
- **Market Analysis**: Pre-market (gap ups/downs, volume leaders, AI market bias) + Post-market (day summary, best/worst performers, breadth)
- **Strategy Performance**: Per-strategy metrics with P&L history charts
- **Trade Detail Modal**: Full trade analysis with AI validation, market regime, prediction probability
- **Bigger Fonts**: Base 16px (was 14px), metrics at 2.2rem
- **Mobile Responsive**: Hamburger menu, stacked grids, collapsible sidebar
- 21 API endpoints total, 12 dashboard pages, 21 sample trades across 6 days

## Testing Status
- Backend: 100% (21/21 endpoints passed)
- Frontend: 100% (12 pages, navigation, login, modals, charts all working)
- Mobile: CSS media queries at 768px and 480px breakpoints

## MongoDB Collections
- `open_positions` — Active positions (unique by symbol)
- `trades` — Closed trade history (21 seeded)
- `event_logs` — System events
- `portfolio_history` — Portfolio snapshots
- `active_strategies` — 4 strategies
- `signals_generated` — AI signal history
- `bot_state` — Runtime config
- `daily_stats` — Daily risk state

## Prioritized Backlog

### P0 (Critical for Live)
- [ ] Kite Connect WebSocket integration (KiteTicker)
- [ ] Live order placement via Kite API
- [ ] Access token refresh automation

### P1 (High Priority)
- [ ] Real-time position monitoring with broker LTP
- [ ] Live NSE data feed (replace NSE API scraping)
- [ ] Telegram bot commands (/status, /positions, /halt)
- [ ] WebSocket reconnect with candle resume

### P2 (Nice to Have)
- [ ] MiniMax AI brain integration for live signal refinement
- [ ] Backtesting module with historical data
- [ ] Multi-timeframe analysis
- [ ] Export trade history to CSV/Excel
- [ ] Portfolio allocation optimization
