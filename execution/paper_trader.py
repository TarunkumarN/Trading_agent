import json
from datetime import datetime
from pathlib import Path
from risk.daily_guard import DailyGuard
from notifications.telegram_alerts import alert_trade_entry, alert_trade_exit, alert_sl_moved

TRADES_FILE    = Path("logs/trades.json")
POSITIONS_FILE = Path("logs/positions.json")

def _load_trades():
    try:
        return json.loads(TRADES_FILE.read_text()) if TRADES_FILE.exists() else []
    except:
        return []

def _save_trades(trades):
    TRADES_FILE.write_text(json.dumps(trades, indent=2))

def _save_positions(positions):
    POSITIONS_FILE.write_text(json.dumps(list(positions.values()), indent=2))

class PaperTrader:
    def __init__(self, guard):
        self.guard     = guard
        self.positions = {}
        self.trade_log = _load_trades()
        self.brokerage = 0.0

    def enter(self, stock, action, qty, entry, sl, target, score):
        if stock in self.positions:
            print(f"[PAPER] Already in {stock}, skipping")
            return
        if qty <= 0 or entry <= 0:
            print(f"[PAPER] Invalid qty/entry for {stock}")
            return
        # SELL/SHORT is now allowed
        # SELL/SHORT is now allowed
        self.positions[stock] = {
            "stock": stock, "action": action, "qty": qty,
            "entry": entry, "sl": sl, "target": target,
            "peak_pnl": 0.0, "sl_phase": "INITIAL", "score": score,
            "time": datetime.now().strftime("%H:%M:%S"),
            "current_price": entry,
        }
        self.brokerage += 20
        _save_positions(self.positions)
        alert_trade_entry(stock, action, qty, entry, sl, target, score)
        print(f"[PAPER] ENTER {action} {qty}x {stock} @ Rs{entry:.2f} | SL:Rs{sl:.2f} | TGT:Rs{target:.2f}")

    def update_price(self, stock, current_price):
        if stock not in self.positions or not current_price or current_price <= 0:
            return
        pos = self.positions[stock]
        pos["current_price"] = current_price
        qty, entry, action = pos["qty"], pos["entry"], pos["action"]
        pnl = (current_price - entry) * qty if action == "BUY" else (entry - current_price) * qty
        if pnl > pos["peak_pnl"]:
            pos["peak_pnl"] = pnl
        new_sl, phase = self._trailing_sl(pos, current_price, pnl)
        if new_sl and phase != pos["sl_phase"]:
            pos["sl"] = new_sl
            pos["sl_phase"] = phase
            alert_sl_moved(stock, new_sl, phase)
        hit_sl     = (action == "BUY" and current_price <= pos["sl"]) or (action == "SELL" and current_price >= pos["sl"])
        hit_target = (action == "BUY" and current_price >= pos["target"]) or (action == "SELL" and current_price <= pos["target"])
        if hit_target:
            self._close(stock, current_price, pnl, "TARGET HIT")
        elif hit_sl:
            self._close(stock, current_price, pnl, "STOP LOSS")
        else:
            _save_positions(self.positions)

    def _trailing_sl(self, pos, current_price, pnl):
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
            if action == "BUY" and entry > cur_sl:   return entry, "BREAKEVEN"
            if action == "SELL" and entry < cur_sl:  return entry, "BREAKEVEN"
        return None, pos["sl_phase"]

    def _close(self, stock, exit_price, pnl, reason):
        pos = self.positions.get(stock)
        if not pos:
            return
        if not exit_price or exit_price <= 0:
            exit_price = pos.get("current_price") or pos["entry"]
            qty, action = pos["qty"], pos["action"]
            pnl = (exit_price - pos["entry"]) * qty if action == "BUY" else (pos["entry"] - exit_price) * qty
            print(f"[PAPER] WARNING: Zero price for {stock} - using current_price")
        self.positions.pop(stock)
        self.brokerage += 20
        net_pnl = round(pnl - 40, 2)
        self.guard.update(net_pnl)
        trade = {
            "stock": stock, "action": pos["action"], "qty": pos["qty"],
            "entry": pos["entry"], "exit": round(exit_price, 2),
            "pnl": net_pnl, "reason": reason, "score": pos.get("score", 0),
            "entry_time": pos["time"], "exit_time": datetime.now().strftime("%H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        self.trade_log.append(trade)
        _save_trades(self.trade_log)
        _save_positions(self.positions)
        alert_trade_exit(stock, pos["action"], pos["entry"], exit_price, net_pnl, self.guard.realised_pnl, reason)
        print(f"[PAPER] EXIT {stock} @ Rs{exit_price:.2f} | Net P&L: Rs{net_pnl:+.2f} | {reason}")

    def close_all(self, latest_prices):
        for stock in list(self.positions.keys()):
            pos = self.positions[stock]
            price = latest_prices.get(stock) or pos.get("current_price") or pos["entry"]
            if price <= 0: price = pos.get("current_price") or pos["entry"]
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
                    price = latest_prices.get(stock) or pos.get("current_price") or pos["entry"]
                    if price <= 0: price = pos.get("current_price") or pos["entry"]
                    qty, action = pos["qty"], pos["action"]
                    pnl = (price - pos["entry"]) * qty if action == "BUY" else (pos["entry"] - price) * qty
                    self._close(stock, price, pnl, "TIME STOP (15 min)")
            except Exception as e:
                print(f"[PAPER] Time stop error for {stock}: {e}")
