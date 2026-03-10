# MiniMax Scalping Agent — PRD

## Original Problem Statement
Audit and harden the TarunkumarN/Trading_agent repository for production trading. Analyze the entire codebase, fix potential issues that could cause failures or financial loss. Build a professional monitoring dashboard. Zerodha broker integration, NSE/BSE India market, paper trading mode.

## Architecture
- **Backend**: FastAPI (Python) on port 8001
- **Frontend**: React dashboard on port 3000
- **Database**: MongoDB (minimax_trading)
- **Broker**: Zerodha Kite Connect
- **Market**: NSE/BSE India (9:15 AM - 3:30 PM IST)

## User Personas
- Indian retail trader running automated scalping bot
- Algo trading enthusiast monitoring performance via dashboard

## Core Requirements (Static)
1. Duplicate order prevention via MongoDB check
2. Order retry logic (3 retries with exponential backoff)
3. WebSocket auto-reconnect
4. State persistence in MongoDB (positions, trades, logs, strategies)
5. Event logging to MongoDB
6. Risk controls: 5% daily loss halt, 10% max drawdown
7. Market hours enforcement (9:15-15:30 IST)
8. Structured exception handling
9. Performance optimization (threaded WS, async endpoints)
10. Professional monitoring dashboard

## What's Been Implemented (2026-03-10)
- Full system audit: 14 issues identified across CRITICAL/HIGH/MEDIUM/LOW
- All 14 issues FIXED with production-grade solutions
- FastAPI backend with 11 API endpoints
- MongoDB state persistence (8 collections)
- RiskManager: daily loss limit, drawdown detection, selective/protected modes
- OrderManager: duplicate prevention, 3-retry logic, critical fail logging
- CandleBuilder: thread-safe, bounded memory (100 candle max)
- SignalScorer: EMA/VWAP/RSI/BB strategy with scoring -10 to +10
- Time filter: market hours enforcement for NSE/BSE
- Event logger: all critical events to MongoDB
- React dashboard with 11 pages: Dashboard, System Health, Premarket Scanner, Strategy Monitor, Positions, Trade Log, Risk Dashboard, P&L History, F&O Calculator, Audit & Logs, Settings
- Login authentication
- 15-second auto-refresh polling
- Dark terminal aesthetic (Bloomberg/Zerodha inspired)

## Testing Status
- Backend: 100% pass (all 11 endpoints)
- Frontend: 100% pass (all pages, navigation, login, data integration)
- Integration: 100% pass

## MongoDB Collections
- `open_positions` — Active positions (unique by symbol)
- `trades` — Closed trade history
- `event_logs` — All system events (indexed by timestamp, event_type)
- `portfolio_history` — Portfolio snapshots
- `active_strategies` — 4 strategies (EMA, VWAP, RSI+BB, ORB)
- `signals_generated` — Signal history
- `bot_state` — Watchlist, WS status, config state
- `daily_stats` — Daily P&L and risk state (restored on restart)

## Prioritized Backlog

### P0 (Critical for Live)
- [ ] Kite Connect WebSocket integration (KiteTicker)
- [ ] Live order placement via Kite API (switch from paper to live)
- [ ] Access token refresh automation

### P1 (High Priority)
- [ ] Real-time position monitoring with actual LTP from broker
- [ ] Pre-market scanner using live NSE data feed
- [ ] Telegram alerts integration (currently configured but not streaming)
- [ ] WebSocket reconnect with candle resume

### P2 (Nice to Have)
- [ ] MiniMax AI brain integration for signal refinement
- [ ] Backtesting module
- [ ] Multi-timeframe analysis
- [ ] Portfolio allocation optimization
- [ ] Export trade history to CSV/Excel

## Next Tasks
1. Integrate Kite Connect WebSocket for live tick streaming
2. Implement live order placement with proper Kite API error handling
3. Add access token auto-refresh via token_server
4. Build real-time position P&L tracking with live prices
