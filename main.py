"""
main.py — MiniMax Scalping Agent Entry Point
============================================
Run this file to start the agent:
    python main.py

The agent will:
  8:30 AM  → Run pre-market analysis via MiniMax
  9:20 AM  → Start scanning signals
  Every 1 min → Close candles and evaluate signals
  Every 30 min → Send heartbeat to Telegram
  3:15 PM  → Close all open positions
  3:30 PM  → Send end-of-day summary
"""

import time
import json
import logging
from datetime import datetime
from pathlib import Path
from data.market_scanner import get_dynamic_watchlist
from apscheduler.schedulers.background import BackgroundScheduler
from data.kite_stream import start_stream
from data.token_lookup import get_tokens
from data.market_scanner import get_dynamic_watchlist

from config import TRADING_MODE, MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE
from config import MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE

from agent.pre_market import run_pre_market, run_end_of_day_review
from strategies.signal_scorer import calculate_signals, set_nifty_bias, update_opening_range, reset_opening_ranges
from risk.position_sizer import calculate_quantity, calculate_stop_and_target
from risk.daily_guard import DailyGuard
from execution.paper_trader import PaperTrader
from data.candle_builder import CandleBuilder
from notifications.telegram_alerts import (
    alert_startup, alert_daily_summary, send_heartbeat, send_telegram
)

# ── Logging Setup ─────────────────────────────────────────────
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")

# ── Global State ──────────────────────────────────────────────
guard          = DailyGuard()
candle_builder = CandleBuilder()
trader         = PaperTrader(guard)
day_started    = False
stream         = None

# ── Load Watchlist from File (Survives Restarts) ──────────────
WATCHLIST_FILE = Path("logs/watchlist.json")

def load_watchlist():
    """Load watchlist from file if it exists."""
    if WATCHLIST_FILE.exists():
        try:
            wl = json.loads(WATCHLIST_FILE.read_text())
            if wl:
                logger.info(f"Loaded watchlist from file: {wl}")
                return wl
        except Exception as e:
            logger.warning(f"Could not load watchlist file: {e}")
    return []

def save_watchlist(wl):
    """Save watchlist to file so it survives restarts."""
    try:
        WATCHLIST_FILE.write_text(json.dumps(wl))
        logger.info(f"Watchlist saved to file: {wl}")
    except Exception as e:
        logger.warning(f"Could not save watchlist: {e}")

watchlist = load_watchlist()

# Auto-start stream on restart during market hours
if watchlist:
    try:
        from datetime import datetime as _dt
        _now = _dt.now()
        _open = _now.hour > 9 or (_now.hour == 9 and _now.minute >= 15)
        _closed = _now.hour > 15 or (_now.hour == 15 and _now.minute >= 30)
        if _open and not _closed:
            logger.info(f"Restarting stream for existing watchlist: {watchlist}")
            _tokens = get_tokens(watchlist)
            if _tokens:
                stream = start_stream(candle_builder, _tokens)
                logger.info(f"Stream auto-restarted for {len(_tokens)} instruments")
    except Exception as e:
        logger.error(f"Auto stream restart failed: {e}")


# Auto-start stream on restart during market hours
if watchlist:
    try:
        from datetime import datetime as _dt
        _now = _dt.now()
        _open = _now.hour > 9 or (_now.hour == 9 and _now.minute >= 15)
        _closed = _now.hour > 15 or (_now.hour == 15 and _now.minute >= 30)
        if _open and not _closed:
            logger.info(f"Restarting stream for existing watchlist: {watchlist}")
            _tokens = get_tokens(watchlist)
            if _tokens:
                stream = start_stream(candle_builder, _tokens)
                logger.info(f"Stream auto-restarted for {len(_tokens)} instruments")
    except Exception as e:
        logger.error(f"Auto stream restart failed: {e}")



def save_trade_log():
    """Save trade log to JSON for dashboard."""
    log_file = Path("logs/trades.json")
    with open(log_file, "w") as f:
        json.dump(trader.trade_log, f, indent=2)


# ── Scheduled Jobs ────────────────────────────────────────────

def pre_market_job():
    """Runs at 8:30 AM — collect market data and build watchlist."""
    global watchlist, stream
    logger.info("Starting pre-market analysis...")
    result    = run_pre_market()
    watchlist = result.get("watchlist", [])
    save_watchlist(watchlist)
    logger.info(f"Watchlist: {watchlist}")

    # Start Kite WebSocket stream for live tick data
    try:
        tokens = get_tokens(watchlist)
        if tokens:
            logger.info(f"Starting Kite stream for tokens: {tokens}")
            stream = start_stream(candle_builder, tokens)
            send_telegram(f"📡 Live stream started for {len(tokens)} stocks")
        else:
            logger.warning("No tokens found — stream not started")
            send_telegram("⚠️ Could not get instrument tokens — using simulated prices")
    except Exception as e:
        logger.error(f"Stream start error: {e}")
        send_telegram(f"⚠️ Stream error: {e} — using simulated prices")


def candle_close_job():
    """
    Runs every 1 minute — closes candles and evaluates signals.
    This is the heart of the agent.
    """
    global day_started
    now = datetime.now()

    # Not yet market open
    if now.hour < MARKET_OPEN_HOUR or \
       (now.hour == MARKET_OPEN_HOUR and now.minute < MARKET_OPEN_MINUTE):
        return

    # Market closed — close all positions
    if now.hour > MARKET_CLOSE_HOUR or \
       (now.hour == MARKET_CLOSE_HOUR and now.minute >= MARKET_CLOSE_MINUTE):
        if trader.positions:
            logger.info("3:15 PM — closing all open positions")
            trader.close_all(candle_builder.get_all_prices())
            save_trade_log()
        return

    # Mark day as started
    if not day_started:
        day_started = True
        logger.info("Market open — scanning started")

    if not watchlist:
        logger.warning("No watchlist yet — skipping scan")
        return

    # Close completed candles for all stocks
    for stock in watchlist:
        candle_builder.close_candle(stock)

    # Check time stops on open positions
    trader.check_time_stops(candle_builder.get_all_prices())

    # Evaluate signals for each stock
    for stock in watchlist:
        prices  = candle_builder.price_history.get(stock, [])
        volumes = candle_builder.volume_history.get(stock, [])
        vwap    = candle_builder.vwap.get(stock, 0)

        if len(prices) < 26:
            logger.info(f"{stock}: {len(prices)} candles built")
            continue

        sig = calculate_signals(prices, volumes, vwap)
        allowed, reason = guard.can_trade(sig["score"])

        logger.debug(
            f"{stock} | Score:{sig['score']} | Action:{sig['action']} | "
            f"Allowed:{allowed} | RSI:{sig['rsi']}"
        )

        if sig["action"] in ("BUY", "SELL") and allowed:
            current_price = prices[-1]
            sl, target    = calculate_stop_and_target(current_price, sig["action"])
            sizing        = calculate_quantity(current_price, sl)

            if sizing["qty"] > 0 and stock not in trader.positions:
                trader.enter(
                    stock, sig["action"], sizing["qty"],
                    current_price, sl, target, sig["score"]
                )
                save_trade_log()

        # Update open positions with latest price
        if stock in trader.positions and prices:
            trader.update_price(stock, prices[-1])
            save_trade_log()


def heartbeat_job():
    """Runs every 30 minutes — sends heartbeat to Telegram."""
    send_heartbeat(
        daily_pnl      = guard.realised_pnl,
        open_positions = len(trader.positions),
        state          = guard.status()
    )


def end_of_day_job():
    """Runs at 3:30 PM — sends daily summary and AI review."""
    summary = guard.summary()
    alert_daily_summary(
        trades    = summary["trades"],
        wins      = summary["wins"],
        losses    = summary["losses"],
        gross_pnl = summary["realised_pnl"],
        brokerage = trader.brokerage,
        net_pnl   = summary["realised_pnl"] - trader.brokerage
    )
    review = run_end_of_day_review(trader.trade_log, guard.realised_pnl)
    if review:
        send_telegram(f"🤖 <b>AI Review</b>\n{review}")

    # Clear watchlist file at end of day so fresh one is built tomorrow
    if WATCHLIST_FILE.exists():
        WATCHLIST_FILE.unlink()
        logger.info("Watchlist file cleared for tomorrow.")


# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info(f"=== MiniMax Scalping Agent STARTING | Mode: {TRADING_MODE.upper()} ===")
    alert_startup(TRADING_MODE)

    # If market is open and no watchlist — run pre-market immediately
    now = datetime.now()
    market_open  = now.replace(hour=MARKET_OPEN_HOUR,  minute=MARKET_OPEN_MINUTE,  second=0)
    market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0)
    if market_open <= now <= market_close and not watchlist:
        logger.info("Market is open but no watchlist — running pre-market now...")
        pre_market_job()
    elif market_open <= now <= market_close and watchlist:
        # Market open, watchlist exists — just restart the stream
        try:
            tokens = get_tokens(watchlist)
            if tokens:
                logger.info(f"Restarting stream for existing watchlist: {watchlist}")
                stream = start_stream(candle_builder, tokens)
                send_telegram(f"📡 Stream restarted for {len(tokens)} stocks")
        except Exception as e:
            logger.error(f"Stream restart error: {e}")

    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

    # Pre-market analysis at 8:30 AM on weekdays
    scheduler.add_job(pre_market_job,  "cron", hour=8,  minute=30, day_of_week="mon-fri")
    # Candle close and signal scan every minute
    scheduler.add_job(candle_close_job,"interval", seconds=60)
    # Heartbeat every 30 minutes
    scheduler.add_job(heartbeat_job,   "interval", minutes=30)
    # End of day summary at 3:30 PM
    scheduler.add_job(end_of_day_job,  "cron", hour=15, minute=30, day_of_week="mon-fri")

    scheduler.start()
    logger.info("Scheduler started. Agent is running.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping agent...")
        scheduler.shutdown()
        if trader.positions:
            send_telegram("⚠️ Agent stopped manually with open positions! Check Zerodha immediately.")
        else:
            send_telegram("🛑 Agent stopped manually.")
        logger.info("Agent stopped.")