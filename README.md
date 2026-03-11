# MiniMax Scalping Agent
### NSE/BSE Intraday Scalping | Zerodha Kite | ₹10,000 Portfolio

---

## Quick Start (Windows)

### Step 1 — Setup
```
1. Rename .env.template to .env
2. Fill in all API keys in .env
3. Open Command Prompt in this folder
```

### Step 2 — Install Dependencies
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3 — Get Zerodha Token (Every Morning)
```cmd
venv\Scripts\activate
python scripts\get_token.py
```

### Step 4 — Run Agent
```cmd
venv\Scripts\activate
python main.py
```

### Step 5 — Open Dashboard
```cmd
(new Command Prompt window)
venv\Scripts\activate
streamlit run dashboard\app.py
```
Then open: http://localhost:8501

---

## Project Structure
```
trading-agent/
├── .env                  ← Your API keys (never share this)
├── .env.template         ← Template — rename to .env and fill in
├── config.py             ← All settings
├── main.py               ← Start here
├── requirements.txt      ← Python packages
│
├── agent/
│   ├── minimax_brain.py  ← MiniMax M2 API
│   └── pre_market.py     ← 8:30 AM market analysis
│
├── data/
│   ├── candle_builder.py ← Builds OHLCV candles + VWAP
│   └── kite_stream.py    ← Zerodha WebSocket live data
│
├── strategies/
│   └── signal_scorer.py  ← EMA + VWAP + RSI + BB signals (-10 to +10)
│
├── risk/
│   ├── position_sizer.py ← 2% risk per trade = ₹200 max
│   └── daily_guard.py    ← Circuit breaker + selective mode
│
├── execution/
│   └── paper_trader.py   ← Paper trading with trailing stop
│
├── notifications/
│   └── telegram_alerts.py← All Telegram alerts
│
├── dashboard/
│   └── app.py            ← Streamlit live dashboard
│
├── scripts/
│   └── get_token.py      ← Daily Zerodha token refresh
│
└── logs/
    ├── agent.log         ← Agent activity log
    └── trades.json       ← Trade history (used by dashboard)
```

---

## Go Live Checklist
- [ ] 4 weeks paper trading completed
- [ ] Net positive P&L on paper
- [ ] Win rate above 50%
- [ ] No crashes for 5 consecutive days
- [ ] Real ₹10,000 in Zerodha account
- [ ] Zerodha API subscription paid (₹500/month)

**To go live:** Change `TRADING_MODE=paper` to `TRADING_MODE=live` in `.env`

---

## Daily Costs
| Item | Cost |
|------|------|
| Zerodha Kite API | ₹500/month |
| MiniMax API credits | ~₹40/month |
| Server (Oracle Cloud) | ₹0/month |
| **Total** | **₹540/month** |
