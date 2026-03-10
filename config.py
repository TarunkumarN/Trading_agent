"""
config.py — Central configuration for MiniMax Scalping Agent
All settings loaded from .env file
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Trading Mode ──────────────────────────────────────────────
TRADING_MODE           = os.getenv("TRADING_MODE", "paper")
IS_LIVE                = TRADING_MODE == "live"

# ── Zerodha Kite ──────────────────────────────────────────────
KITE_API_KEY           = os.getenv("KITE_API_KEY")
KITE_API_SECRET        = os.getenv("KITE_API_SECRET")
KITE_ACCESS_TOKEN      = os.getenv("KITE_ACCESS_TOKEN")

# ── MiniMax API ───────────────────────────────────────────────
MINIMAX_API_KEY        = os.getenv("MINIMAX_API_KEY")
MINIMAX_GROUP_ID       = os.getenv("MINIMAX_GROUP_ID")

# ── Portfolio Settings ────────────────────────────────────────
PORTFOLIO_VALUE        = float(os.getenv("PORTFOLIO_VALUE", 10000))
MAX_RISK_PCT           = float(os.getenv("MAX_RISK_PCT", 2))
DAILY_LOSS_LIMIT       = float(os.getenv("DAILY_LOSS_LIMIT", 800))
DAILY_PROFIT_SELECTIVE = float(os.getenv("DAILY_PROFIT_SELECTIVE", 500))
DAILY_PROFIT_STOP      = float(os.getenv("DAILY_PROFIT_STOP", 800))
DAILY_PROFIT_STOP      = float(os.getenv("DAILY_PROFIT_STOP", 800))
MIN_SIGNAL_SCORE       = int(os.getenv("MIN_SIGNAL_SCORE", 6))
MIN_SCORE_SELECTIVE    = int(os.getenv("MIN_SIGNAL_SCORE_SELECTIVE", 9))

# ── Telegram ──────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN     = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID       = os.getenv("TELEGRAM_CHAT_ID")

# ── Stock Universe ────────────────────────────────────────────
NIFTY50_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK",
    "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA",
    "WIPRO", "ULTRACEMCO", "TITAN", "BAJFINANCE", "NESTLEIND",
    "POWERGRID", "NTPC", "ONGC", "JSWSTEEL", "TATASTEEL",
    "ADANIPORTS", "HCLTECH", "TECHM", "DRREDDY", "CIPLA"
]

BANKNIFTY_STOCKS = [
    "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN",
    "INDUSINDBK", "BANDHANBNK", "FEDERALBNK", "IDFCFIRSTB", "PNB"
]

# Default watchlist (used if pre-market analysis fails)
DEFAULT_WATCHLIST = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS"
]

# ── Market Hours (IST) ────────────────────────────────────────
MARKET_OPEN_HOUR       = 9
MARKET_OPEN_MINUTE     = 20   # Start trading at 9:20 AM (5 min after open)
MARKET_CLOSE_HOUR      = 15
MARKET_CLOSE_MINUTE    = 15   # Close all positions by 3:15 PM

# ── Strategy Settings ─────────────────────────────────────────
EMA_FAST               = 9
EMA_SLOW               = 21
RSI_PERIOD             = 14
BB_PERIOD              = 20
BB_STD                 = 2
RISK_REWARD_RATIO      = 1.5  # Target = 1.5x the risk amount
MAX_LEVERAGE           = 3    # Never use more than 3x leverage
CANDLE_INTERVAL        = "5minute"  # Primary candle for signals
