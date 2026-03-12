import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import dotenv_values

from config import MAX_OPEN_POSITIONS, REENTRY_COOLDOWN_MINUTES
from notifications.telegram_alerts import alert_sl_moved, alert_trade_entry, alert_trade_exit

TRADES_FILE = Path("logs/trades.json")
POSITIONS_FILE = Path("logs/positions.json")
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def _load_trades():
    try:
        return json.loads(TRADES_FILE.read_text()) if TRADES_FILE.exists() else []
    except Exception:
        return []


def _save_trades(trades):
    TRADES_FILE.write_text(json.dumps(trades, indent=2))


def _save_positions(positions):
    POSITIONS_FILE.write_text(json.dumps(list(positions.values()), indent=2))


class PaperTrader:
    def __init__(self, guard):
        self.guard = guard
        self.positions = {}
        self.trade_log = _load_trades()
        self.brokerage = 0.0
        self.recent_exits = {}
        self._restore_recent_exits()

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

    def enter(self, stock, action, qty, entry, sl, target, score, metadata=None):
        if stock in self.positions or qty <= 0 or entry <= 0:
            return
        metadata = metadata or {}
        self.positions[stock] = {
            "stock": stock,
            "action": action,
            "qty": qty,
            "entry": entry,
            "sl": sl,
            "target": target,
            "peak_pnl": 0.0,
            "sl_phase": "INITIAL",
            "score": score,
            "time": datetime.now().strftime("%H:%M:%S"),
            "current_price": entry,
            **metadata,
        }
        self.brokerage += 20
        _save_positions(self.positions)
        alert_trade_entry(stock, action, qty, entry, sl, target, score)

    def update_price(self, stock, current_price):
        if stock not in self.positions or not current_price or current_price <= 0:
            return
        pos = self.positions[stock]
        pos["current_price"] = current_price
        qty, entry, action = pos["qty"], pos["entry"], pos["action"]
        pnl = (current_price - entry) * qty if action == "BUY" else (entry - current_price) * qty
        if pnl > pos["peak_pnl"]:
            pos["peak_pnl"] = pnl
        new_sl, phase = self._trailing_sl(pos, pnl)
        if new_sl and phase != pos["sl_phase"]:
            pos["sl"] = new_sl
            pos["sl_phase"] = phase
            alert_sl_moved(stock, new_sl, phase)
        hit_sl = (action == "BUY" and current_price <= pos["sl"]) or (action == "SELL" and current_price >= pos["sl"])
        hit_target = (action == "BUY" and current_price >= pos["target"]) or (action == "SELL" and current_price <= pos["target"])
        if hit_target:
            self._close(stock, current_price, pnl, "TARGET HIT")
        elif hit_sl:
            self._close(stock, current_price, pnl, "STOP LOSS")
        else:
            _save_positions(self.positions)

    def _trailing_sl(self, pos, pnl):
        entry, action, qty, cur_sl = pos["entry"], pos["action"], pos["qty"], pos["sl"]
        if pnl >= 200 and pos["peak_pnl"] >= 200:
            locked = (pos["peak_pnl"] * 0.5) / qty
            new_sl = round(entry + locked if action == "BUY" else entry - locked, 2)
            if (action == "BUY" and new_sl > cur_sl) or (action == "SELL" and new_sl < cur_sl):
                return new_sl, "TRAILING 50%"
        elif pnl >= 150:
            locked = 75 / qty
            new_sl = round(entry + locked if action == "BUY" else entry - locked, 2)
            if (action == "BUY" and new_sl > cur_sl) or (action == "SELL" and new_sl < cur_sl):
                return new_sl, "LOCKED +Rs75"
        elif pnl >= 100:
            if action == "BUY" and entry > cur_sl:
                return entry, "BREAKEVEN"
            if action == "SELL" and entry < cur_sl:
                return entry, "BREAKEVEN"
        return None, pos["sl_phase"]

    def _close(self, stock, exit_price, pnl, reason):
        pos = self.positions.get(stock)
        if not pos:
            return
        if not exit_price or exit_price <= 0:
            exit_price = pos["entry"]
            qty, action = pos["qty"], pos["action"]
            pnl = (exit_price - pos["entry"]) * qty if action == "BUY" else (pos["entry"] - exit_price) * qty
        self.positions.pop(stock)
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
            "strategy": pos.get("strategy", "unknown"),
            "strategy_confidence": pos.get("strategy_confidence"),
            "trade_score": pos.get("trade_score"),
            "ai_confidence": pos.get("ai_confidence"),
            "ai_summary": pos.get("ai_summary"),
            "market_regime": pos.get("market_regime"),
            "instrument_type": pos.get("instrument_type", "EQUITY"),
            "risk_reward": pos.get("risk_reward"),
            "volume_ratio": pos.get("volume_ratio"),
            "entry_time": pos["time"],
            "exit_time": exit_now.strftime("%H:%M:%S"),
            "date": exit_now.strftime("%Y-%m-%d"),
            "mode": "PAPER",
        }
        self.trade_log.append(trade)
        _save_trades(self.trade_log)
        _save_positions(self.positions)
        _sync_to_mongo(self.trade_log, self.positions)
        alert_trade_exit(stock, pos["action"], pos["entry"], exit_price, net_pnl, self.guard.realised_pnl, reason)

    def close_all(self, latest_prices):
        for stock in list(self.positions.keys()):
            pos = self.positions[stock]
            price = latest_prices.get(stock) or pos["entry"]
            if price <= 0:
                price = pos["entry"]
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
                    if price <= 0:
                        price = pos["entry"]
                    qty, action = pos["qty"], pos["action"]
                    pnl = (price - pos["entry"]) * qty if action == "BUY" else (pos["entry"] - price) * qty
                    self._close(stock, price, pnl, "TIME STOP (15 min)")
            except Exception:
                continue


def _sync_to_mongo(trades, positions):
    try:
        from pymongo import MongoClient
        url = os.environ.get("MONGODB_URL") or dotenv_values(ENV_FILE).get("MONGODB_URL")
        if not url:
            return
        client = MongoClient(url)
        db = client["minimax_trading"]
        if trades:
            db.trades.delete_many({})
            db.trades.insert_many([{**t} for t in trades])
        db.positions.delete_many({})
        if positions:
            db.positions.insert_many([{"symbol": k, **v} for k, v in positions.items()])
        client.close()
    except Exception:
        pass
