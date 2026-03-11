"""
main.py - MiniMax Scalping Agent Entry Point
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

from agent.pre_market import run_end_of_day_review, run_pre_market
from config import MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE, MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE, TRADING_MODE
from data.candle_builder import CandleBuilder
from data.kite_stream import start_stream
from data.token_lookup import get_tokens
from execution import create_trader
from notifications.telegram_alerts import alert_daily_summary, alert_startup, send_heartbeat, send_telegram
from risk.daily_guard import DailyGuard
from risk.position_sizer import calculate_quantity, calculate_stop_and_target
from strategies.signal_scorer import calculate_signals, reset_opening_ranges, set_nifty_bias, update_opening_range

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler("logs/agent.log"), logging.StreamHandler()],
)
logger = logging.getLogger("main")

WATCHLIST_FILE = Path("logs/watchlist.json")
MARKET_BIAS_FILE = Path("logs/market_bias.json")

guard = DailyGuard()
candle_builder = CandleBuilder()
trader = create_trader(guard)
day_started = False
stream = None
market_bias_pct = 0.0


def load_watchlist():
    if WATCHLIST_FILE.exists():
        try:
            watchlist = json.loads(WATCHLIST_FILE.read_text())
            if watchlist:
                logger.info(f"Loaded watchlist from file: {watchlist}")
                return watchlist
        except Exception as exc:
            logger.warning(f"Could not load watchlist file: {exc}")
    return []


def save_watchlist(watchlist):
    try:
        WATCHLIST_FILE.write_text(json.dumps(watchlist))
        logger.info(f"Watchlist saved to file: {watchlist}")
    except Exception as exc:
        logger.warning(f"Could not save watchlist: {exc}")


def load_market_bias():
    if MARKET_BIAS_FILE.exists():
        try:
            payload = json.loads(MARKET_BIAS_FILE.read_text())
            return float(payload.get("market_bias_pct", 0.0))
        except Exception as exc:
            logger.warning(f"Could not load market bias file: {exc}")
    return 0.0


def save_market_bias(value: float):
    try:
        MARKET_BIAS_FILE.write_text(json.dumps({"market_bias_pct": value}))
    except Exception as exc:
        logger.warning(f"Could not save market bias: {exc}")


def save_trade_log():
    Path("logs/trades.json").write_text(json.dumps(trader.trade_log, indent=2))


def _market_bias_to_pct(bias: str) -> float:
    bias = (bias or "").upper()
    if bias in {"STRONG_BULLISH", "BULLISH"}:
        return 1.0
    if bias in {"STRONG_BEARISH", "BEARISH"}:
        return -1.0
    return 0.0


def _is_market_session(now: datetime) -> bool:
    market_open = now.hour > 9 or (now.hour == 9 and now.minute >= 15)
    market_closed = now.hour > 15 or (now.hour == 15 and now.minute >= 30)
    return market_open and not market_closed


def _prime_existing_stream(existing_watchlist):
    global stream
    if not existing_watchlist:
        return
    try:
        now = datetime.now()
        if not _is_market_session(now):
            return
        tokens = get_tokens(existing_watchlist)
        if tokens:
            logger.info(f"Restarting stream for existing watchlist: {existing_watchlist}")
            stream = start_stream(candle_builder, tokens)
            logger.info(f"Stream auto-restarted for {len(tokens)} instruments")
    except Exception as exc:
        logger.error(f"Auto stream restart failed: {exc}")


def pre_market_job():
    global watchlist, stream, market_bias_pct

    logger.info("Starting pre-market analysis...")
    result = run_pre_market()
    watchlist = result.get("watchlist", [])
    save_watchlist(watchlist)

    market_bias_pct = _market_bias_to_pct(result.get("market_bias", "NEUTRAL"))
    set_nifty_bias(market_bias_pct)
    save_market_bias(market_bias_pct)
    logger.info(f"Watchlist: {watchlist} | Market bias pct: {market_bias_pct:+.2f}")

    try:
        tokens = get_tokens(watchlist)
        if tokens:
            logger.info(f"Starting Kite stream for tokens: {tokens}")
            stream = start_stream(candle_builder, tokens)
            send_telegram(f"Live stream started for {len(tokens)} stocks")
        else:
            logger.warning("No tokens found - stream not started")
            send_telegram("Could not get instrument tokens - using simulated prices")
    except Exception as exc:
        logger.error(f"Stream start error: {exc}")
        send_telegram(f"Stream error: {exc} - using simulated prices")


def candle_close_job():
    global day_started

    now = datetime.now()

    if now.hour < MARKET_OPEN_HOUR or (now.hour == MARKET_OPEN_HOUR and now.minute < MARKET_OPEN_MINUTE):
        return

    if now.hour > MARKET_CLOSE_HOUR or (now.hour == MARKET_CLOSE_HOUR and now.minute >= MARKET_CLOSE_MINUTE):
        if trader.positions:
            logger.info("3:15 PM - closing all open positions")
            trader.close_all(candle_builder.get_latest_prices())
            save_trade_log()
        return

    if not day_started:
        day_started = True
        reset_opening_ranges()
        logger.info(f"Market open - scanning started | bias {market_bias_pct:+.2f}%")

    if not watchlist:
        logger.warning("No watchlist yet - skipping scan")
        return

    for stock in watchlist:
        candle_builder.close_candle(stock)

    trader.check_time_stops(candle_builder.get_latest_prices())

    if now.hour == 9 and now.minute <= 34:
        for stock in watchlist:
            latest_highs = candle_builder.high_history.get(stock, [])
            latest_lows = candle_builder.low_history.get(stock, [])
            if latest_highs and latest_lows:
                update_opening_range(stock, latest_highs[-1], latest_lows[-1], now.minute)

    for stock in watchlist:
        prices = candle_builder.price_history.get(stock, [])
        volumes = candle_builder.volume_history.get(stock, [])
        highs = candle_builder.high_history.get(stock, [])
        lows = candle_builder.low_history.get(stock, [])
        vwap = candle_builder.vwap.get(stock, 0)

        if len(prices) < 30:
            logger.info(f"{stock}: {len(prices)} candles built")
            continue

        signal = calculate_signals(prices, volumes, vwap, highs=highs, lows=lows, symbol=stock)
        allowed, reason = guard.can_trade(signal["score"])
        logger.info(
            f"{stock} | score={signal['score']} | action={signal['action']} | "
            f"quality={signal.get('setup_quality')} | allowed={allowed} ({reason})"
        )

        if signal["action"] in ("BUY", "SELL") and allowed:
            current_price = prices[-1]
            stop_loss, target = calculate_stop_and_target(current_price, signal["action"], signal.get("atr"))
            sizing = calculate_quantity(current_price, stop_loss)
            can_open, open_reason = trader.can_open(stock)

            if sizing["qty"] > 0 and can_open:
                trader.enter(stock, signal["action"], sizing["qty"], current_price, stop_loss, target, signal["score"])
                save_trade_log()
            elif sizing["qty"] > 0 and not can_open:
                logger.info(f"{stock}: entry skipped - {open_reason}")

        if stock in trader.positions:
            ltp = candle_builder.get_latest_prices().get(stock) or (prices[-1] if prices else 0)
            if ltp > 0:
                trader.update_price(stock, ltp)
            save_trade_log()


def heartbeat_job():
    send_heartbeat(daily_pnl=guard.realised_pnl, open_positions=len(trader.positions), state=guard.status())


def end_of_day_job():
    summary = guard.summary()
    alert_daily_summary(
        trades=summary["trades"],
        wins=summary["wins"],
        losses=summary["losses"],
        gross_pnl=summary["realised_pnl"],
        brokerage=trader.brokerage,
        net_pnl=summary["realised_pnl"] - trader.brokerage,
    )
    review = run_end_of_day_review(trader.trade_log, guard.realised_pnl)
    if review:
        send_telegram(f"AI Review\n{review}")
    if WATCHLIST_FILE.exists():
        WATCHLIST_FILE.unlink()
        logger.info("Watchlist file cleared for tomorrow.")
    if MARKET_BIAS_FILE.exists():
        MARKET_BIAS_FILE.unlink()


watchlist = load_watchlist()
market_bias_pct = load_market_bias()
set_nifty_bias(market_bias_pct)
_prime_existing_stream(watchlist)


if __name__ == "__main__":
    logger.info(f"=== MiniMax Scalping Agent STARTING | Mode: {TRADING_MODE.upper()} ===")
    alert_startup(TRADING_MODE)

    now = datetime.now()
    market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
    market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)

    if market_open <= now <= market_close and not watchlist:
        logger.info("Market is open but no watchlist - running pre-market now...")
        pre_market_job()
    elif market_open <= now <= market_close and watchlist:
        _prime_existing_stream(watchlist)

    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(pre_market_job, "cron", hour=8, minute=30, day_of_week="mon-fri")
    scheduler.add_job(candle_close_job, "interval", seconds=60)
    scheduler.add_job(heartbeat_job, "interval", minutes=30)
    scheduler.add_job(end_of_day_job, "cron", hour=15, minute=30, day_of_week="mon-fri")
    scheduler.start()
    logger.info("Scheduler started. Agent is running.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping agent...")
        scheduler.shutdown()
        if trader.positions:
            send_telegram("Agent stopped manually with open positions. Check Zerodha immediately.")
        else:
            send_telegram("Agent stopped manually.")
        logger.info("Agent stopped.")

