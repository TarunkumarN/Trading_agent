"""
execution/live_trader.py
Live Zerodha execution with the same interface as PaperTrader.
"""
import json
import logging
import os
from datetime import date, datetime, timedelta
from pathlib import Path

from kiteconnect import KiteConnect

from config import (
    DAILY_LOSS_LIMIT,
    DAILY_PROFIT_STOP,
    KITE_ACCESS_TOKEN,
    KITE_API_KEY,
    MAX_OPEN_POSITIONS,
    MAX_RISK_PCT,
    PORTFOLIO_VALUE,
    REENTRY_COOLDOWN_MINUTES,
)

logger = logging.getLogger(__name__)
TRADES_FILE = Path("logs/trades.json")
POSITIONS_FILE = Path("logs/positions.json")
MAX_ORDER_VAL = 75000


def _load_json(path, default):
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except Exception:
        return default


def _save_json(path, data):
    path.write_text(json.dumps(data, indent=2, default=str))


class LiveTrader:
    def __init__(self, guard):
        self.guard = guard
        self.kite = KiteConnect(api_key=KITE_API_KEY)
        self.kite.set_access_token(KITE_ACCESS_TOKEN or os.getenv("KITE_ACCESS_TOKEN", ""))
        self.positions = _load_json(POSITIONS_FILE, {})
        self.trade_log = _load_json(TRADES_FILE, [])
        self.brokerage = 0.0
        self.recent_exits = {}
        self._restore_recent_exits()
        logger.info("LiveTrader initialised")

    def _restore_recent_exits(self):
        today = datetime.now().strftime("%Y-%m-%d")
        for trade in reversed(self.trade_log):
            if trade.get("date") != today:
                continue
            stock = trade.get("stock")
            exit_time = trade.get("exit_time")
            if stock and exit_time and stock not in self.recent_exits:
                try:
                    self.recent_exits[stock] = datetime.strptime(f"{today} {exit_time}", "%Y-%m-%d %H:%M:%S")
                except Exception:
                    continue

    def can_open(self, stock):
        if stock in self.positions:
            return False, "Position already open"
        if len(self.positions) >= MAX_OPEN_POSITIONS:
            return False, f"Max open positions reached ({MAX_OPEN_POSITIONS})"
        last_exit = self.recent_exits.get(stock)
        if not last_exit:
            return True, "OK"
        elapsed = datetime.now() - last_exit
        if elapsed < timedelta(minutes=REENTRY_COOLDOWN_MINUTES):
            wait_left = REENTRY_COOLDOWN_MINUTES - int(elapsed.total_seconds() // 60)
            return False, f"Cooldown active for {max(wait_left, 1)} more min"
        return True, "OK"

    def _position_size(self, entry, stop_loss):
        risk = abs(entry - stop_loss)
        if risk <= 0:
            return 0
        qty = int((PORTFOLIO_VALUE * MAX_RISK_PCT / 100) / risk)
        if qty * entry > MAX_ORDER_VAL:
            qty = int(MAX_ORDER_VAL / entry)
        return max(qty, 1)

    def enter(self, stock, action, qty, entry, sl, target, score):
        if qty <= 0:
            return
        can_trade, reason = self.guard.can_trade(score)
        if not can_trade:
            logger.warning(f"[LIVE] Blocked {stock}: {reason}")
            return
        try:
            txn = self.kite.TRANSACTION_TYPE_BUY if action == "BUY" else self.kite.TRANSACTION_TYPE_SELL
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=self.kite.EXCHANGE_NSE,
                tradingsymbol=stock,
                transaction_type=txn,
                quantity=qty,
                product=self.kite.PRODUCT_MIS,
                order_type=self.kite.ORDER_TYPE_MARKET,
            )
            self.positions[stock] = {
                "stock": stock,
                "action": action,
                "qty": qty,
                "entry": entry,
                "sl": sl,
                "target": target,
                "score": score,
                "order_id": order_id,
                "current_price": entry,
                "peak_pnl": 0.0,
                "sl_phase": "INITIAL",
                "time": datetime.now().strftime("%H:%M:%S"),
            }
            self.brokerage += 20
            _save_json(POSITIONS_FILE, self.positions)
        except Exception as exc:
            logger.error(f"[LIVE] Order failed {stock}: {exc}")

    def update_price(self, stock, current_price):
        if stock not in self.positions or current_price <= 0:
            return
        pos = self.positions[stock]
        pos["current_price"] = current_price
        qty, entry, action = pos["qty"], pos["entry"], pos["action"]
        pnl = (current_price - entry) * qty if action == "BUY" else (entry - current_price) * qty
        if pnl > pos["peak_pnl"]:
            pos["peak_pnl"] = pnl
        hit_sl = (action == "BUY" and current_price <= pos["sl"]) or (action == "SELL" and current_price >= pos["sl"])
        hit_target = (action == "BUY" and current_price >= pos["target"]) or (action == "SELL" and current_price <= pos["target"])
        if hit_target:
            self._close(stock, current_price, pnl, "TARGET HIT")
        elif hit_sl:
            self._close(stock, current_price, pnl, "STOP LOSS")
        else:
            _save_json(POSITIONS_FILE, self.positions)

    def _close(self, stock, exit_price, pnl, reason):
        pos = self.positions.get(stock)
        if not pos:
            return
        try:
            txn = self.kite.TRANSACTION_TYPE_SELL if pos["action"] == "BUY" else self.kite.TRANSACTION_TYPE_BUY
            self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=self.kite.EXCHANGE_NSE,
                tradingsymbol=stock,
                transaction_type=txn,
                quantity=pos["qty"],
                product=self.kite.PRODUCT_MIS,
                order_type=self.kite.ORDER_TYPE_MARKET,
            )
        except Exception as exc:
            logger.error(f"[LIVE] Exit failed {stock}: {exc}")
        self.positions.pop(stock, None)
        self.brokerage += 20
        net_pnl = round(pnl - 40, 2)
        self.guard.update(net_pnl)
        exit_now = datetime.now()
        self.recent_exits[stock] = exit_now
        trade = {
            "stock": stock,
            "action": pos["action"],
            "qty": pos["qty"],
            "entry": pos["entry"],
            "exit": round(exit_price, 2),
            "pnl": net_pnl,
            "reason": reason,
            "score": pos.get("score", 0),
            "entry_time": pos["time"],
            "exit_time": exit_now.strftime("%H:%M:%S"),
            "date": date.today().isoformat(),
            "mode": "LIVE",
        }
        self.trade_log.append(trade)
        _save_json(TRADES_FILE, self.trade_log)
        _save_json(POSITIONS_FILE, self.positions)

    def close_all(self, latest_prices):
        for stock in list(self.positions.keys()):
            pos = self.positions[stock]
            price = latest_prices.get(stock) or pos["entry"]
            qty, action = pos["qty"], pos["action"]
            pnl = (price - pos["entry"]) * qty if action == "BUY" else (pos["entry"] - price) * qty
            self._close(stock, price, pnl, "END OF DAY CLOSE")

    def check_time_stops(self, latest_prices):
        now = datetime.now()
        for stock in list(self.positions.keys()):
            pos = self.positions[stock]
            try:
                entry_time = datetime.strptime(f"{now.date()} {pos['time']}", "%Y-%m-%d %H:%M:%S")
                if (now - entry_time).seconds / 60 >= 15:
                    price = latest_prices.get(stock) or pos["entry"]
                    qty, action = pos["qty"], pos["action"]
                    pnl = (price - pos["entry"]) * qty if action == "BUY" else (pos["entry"] - price) * qty
                    self._close(stock, price, pnl, "TIME STOP (15 min)")
            except Exception:
                continue
