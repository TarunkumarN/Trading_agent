"""
notifications/telegram_alerts.py
Sends real-time trade alerts to your Telegram account
"""
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram(message: str):
    """Send any message to your Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[ALERT] {message}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram error: {e}")


def alert_startup(mode: str):
    send_telegram(
        f"🤖 <b>MiniMax Scalping Agent STARTED</b>\n"
        f"Mode: {mode.upper()}\n"
        f"Portfolio: ₹50,000 | Daily SL: ₹2,500 | Target: ₹1,500–2,500"
    )


def alert_pre_market(bias: str, confidence: int, watchlist: list, news: str):
    stocks = ", ".join(watchlist[:5])
    send_telegram(
        f"📊 <b>Pre-Market Analysis</b>\n"
        f"Bias: {bias} ({confidence}% confidence)\n"
        f"Watchlist: {stocks}\n"
        f"News: {news}"
    )


def alert_trade_entry(stock: str, action: str, qty: int,
                      price: float, sl: float, target: float, score: int):
    emoji = "🟢" if action == "BUY" else "🔴"
    send_telegram(
        f"{emoji} <b>{action} {stock}</b>\n"
        f"Qty: {qty} shares @ ₹{price:.2f}\n"
        f"Stop Loss: ₹{sl:.2f}\n"
        f"Target: ₹{target:.2f}\n"
        f"Signal Score: {score}/10"
    )


def alert_sl_moved(stock: str, new_sl: float, phase: str):
    send_telegram(
        f"🔄 <b>Trailing SL Updated — {stock}</b>\n"
        f"New SL: ₹{new_sl:.2f} ({phase})"
    )


def alert_trade_exit(stock: str, action: str, entry: float,
                     exit_price: float, pnl: float, daily_pnl: float, reason: str):
    emoji = "✅" if pnl >= 0 else "❌"
    send_telegram(
        f"{emoji} <b>EXIT {stock}</b>\n"
        f"Entry: ₹{entry:.2f} → Exit: ₹{exit_price:.2f}\n"
        f"Trade P&L: ₹{pnl:+.2f} | Reason: {reason}\n"
        f"Day Total: ₹{daily_pnl:+.2f}"
    )


def alert_selective_mode(daily_pnl: float):
    send_telegram(
        f"🎯 <b>SELECTIVE MODE ACTIVATED</b>\n"
        f"Daily profit ₹{daily_pnl:.0f} reached ₹2,500 target.\n"
        f"Now accepting score 9+ signals only.\n"
        f"Keep going — protect the gains!"
    )


def alert_circuit_breaker(daily_pnl: float, trades: int):
    send_telegram(
        f"⛔ <b>CIRCUIT BREAKER — TRADING STOPPED</b>\n"
        f"Daily loss limit of ₹2,500 reached.\n"
        f"Final P&L: ₹{daily_pnl:.2f} | Trades today: {trades}\n"
        f"All positions closed. Resume tomorrow."
    )


def alert_protect_mode(daily_pnl: float):
    send_telegram(
        f"🏆 <b>PROTECT MODE — GREAT DAY!</b>\n"
        f"Daily profit ₹{daily_pnl:.0f} hit ₹4,000.\n"
        f"No new trades. Locking in the exceptional day."
    )


def alert_daily_summary(trades: int, wins: int, losses: int,
                        gross_pnl: float, brokerage: float, net_pnl: float):
    win_rate = (wins / trades * 100) if trades > 0 else 0
    emoji = "📈" if net_pnl >= 0 else "📉"
    send_telegram(
        f"{emoji} <b>End of Day Summary</b>\n"
        f"Trades: {trades} | Wins: {wins} | Losses: {losses}\n"
        f"Win Rate: {win_rate:.0f}%\n"
        f"Gross P&L: ₹{gross_pnl:+.2f}\n"
        f"Brokerage: -₹{brokerage:.2f}\n"
        f"Net P&L: ₹{net_pnl:+.2f}"
    )


def send_heartbeat(daily_pnl: float, open_positions: int, state: str):
    send_telegram(
        f"💓 Agent alive | State: {state}\n"
        f"P&L today: ₹{daily_pnl:+.2f}\n"
        f"Open positions: {open_positions}"
    )
