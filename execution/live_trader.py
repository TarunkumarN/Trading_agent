"""
execution/live_trader.py — Zerodha Kite live order execution.
Drop-in replacement for paper_trader when TRADING_MODE=LIVE.
"""
import os, json, logging
from datetime import datetime, date
from pathlib import Path
from kiteconnect import KiteConnect
from config import (KITE_API_KEY, PORTFOLIO_SIZE, MAX_RISK_PCT,
                    DAILY_LOSS_LIMIT, DAILY_PROFIT_STOP)

logger = logging.getLogger(__name__)
TRADES_FILE    = Path("logs/trades.json")
POSITIONS_FILE = Path("logs/positions.json")
MAX_POSITIONS  = 5
MAX_ORDER_VAL  = 75000

def _load_json(path, default):
    try:
        if path.exists(): return json.loads(path.read_text())
    except: pass
    return default

def _save_json(path, data):
    path.write_text(json.dumps(data, indent=2, default=str))

class LiveTrader:
    def __init__(self):
        self.kite      = KiteConnect(api_key=KITE_API_KEY)
        self.kite.set_access_token(os.getenv("KITE_ACCESS_TOKEN", ""))
        self.positions = _load_json(POSITIONS_FILE, {})
        self.trade_log = _load_json(TRADES_FILE, [])
        self.daily_pnl = 0.0
        self.halted    = False
        self._reload_daily_pnl()
        logger.info("LiveTrader initialised — REAL MONEY MODE 🔴")

    def _reload_daily_pnl(self):
        today = date.today().isoformat()
        self.daily_pnl = sum(t.get("pnl", 0) for t in self.trade_log
                             if t.get("date","")[:10] == today and t.get("status") == "CLOSED")

    def _can_trade(self):
        if self.halted:                         return False, "HALTED"
        if self.daily_pnl <= -DAILY_LOSS_LIMIT: self.halted = True; return False, f"Loss limit ₹{DAILY_LOSS_LIMIT}"
        if self.daily_pnl >= DAILY_PROFIT_STOP: self.halted = True; return False, f"Profit target reached"
        if len(self.positions) >= MAX_POSITIONS: return False, f"Max {MAX_POSITIONS} positions"
        return True, "OK"

    def _position_size(self, entry, stop_loss):
        risk = abs(entry - stop_loss)
        if risk <= 0: return 0
        qty = int((PORTFOLIO_SIZE * MAX_RISK_PCT / 100) / risk)
        if qty * entry > MAX_ORDER_VAL: qty = int(MAX_ORDER_VAL / entry)
        return max(qty, 1)

    def enter_trade(self, stock, action, entry_price, stop_loss, target, reason=""):
        can, msg = self._can_trade()
        if not can: logger.warning(f"[LIVE] Blocked: {msg}"); return
        qty = self._position_size(entry_price, stop_loss)
        if qty <= 0: return
        try:
            txn = self.kite.TRANSACTION_TYPE_BUY if action == "BUY" else self.kite.TRANSACTION_TYPE_SELL
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR, exchange=self.kite.EXCHANGE_NSE,
                tradingsymbol=stock, transaction_type=txn, quantity=qty,
                product=self.kite.PRODUCT_MIS, order_type=self.kite.ORDER_TYPE_MARKET,
            )
            self.positions[stock] = {
                "entry": entry_price, "qty": qty, "action": action,
                "sl": stop_loss, "target": target, "order_id": order_id,
                "entry_time": datetime.now().isoformat(), "sl_phase": "INITIAL",
                "peak_pnl": 0, "reason": reason,
            }
            _save_json(POSITIONS_FILE, self.positions)
            logger.info(f"[LIVE] {action} {qty}x {stock} @ ₹{entry_price} | Order: {order_id}")
        except Exception as e:
            logger.error(f"[LIVE] Order failed {stock}: {e}")

    def exit_trade(self, stock, exit_price, reason=""):
        pos = self.positions.get(stock)
        if not pos: return
        try:
            sq = self.kite.TRANSACTION_TYPE_SELL if pos["action"] == "BUY" else self.kite.TRANSACTION_TYPE_BUY
            self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR, exchange=self.kite.EXCHANGE_NSE,
                tradingsymbol=stock, transaction_type=sq, quantity=pos["qty"],
                product=self.kite.PRODUCT_MIS, order_type=self.kite.ORDER_TYPE_MARKET,
            )
        except Exception as e:
            logger.error(f"[LIVE] Exit failed {stock}: {e}")
        pnl = ((exit_price - pos["entry"]) if pos["action"] == "BUY" else (pos["entry"] - exit_price)) * pos["qty"] - 40
        self.trade_log.append({"stock": stock, "action": pos["action"], "entry": pos["entry"],
            "exit": exit_price, "qty": pos["qty"], "pnl": round(pnl, 2),
            "reason": reason, "date": date.today().isoformat(), "status": "CLOSED", "mode": "LIVE"})
        self.daily_pnl += pnl
        del self.positions[stock]
        _save_json(TRADES_FILE, self.trade_log)
        _save_json(POSITIONS_FILE, self.positions)
        logger.info(f"[LIVE] {stock} closed P&L ₹{pnl:+.2f} | Daily ₹{self.daily_pnl:+.2f}")

    def update_trailing_sl(self, stock, current_price):
        pos = self.positions.get(stock)
        if not pos: return
        qty    = pos["qty"]
        entry  = pos["entry"]
        action = pos["action"]
        unreal = ((current_price - entry) if action == "BUY" else (entry - current_price)) * qty
        pos["peak_pnl"] = max(pos.get("peak_pnl", 0), unreal)
        peak = pos["peak_pnl"]
        if peak >= 100 and pos["sl_phase"] == "INITIAL":
            pos["sl"] = entry; pos["sl_phase"] = "BREAKEVEN"
        elif peak >= 150 and pos["sl_phase"] == "BREAKEVEN":
            locked = entry + (75/qty) if action == "BUY" else entry - (75/qty)
            pos["sl"] = round(locked, 2); pos["sl_phase"] = "LOCK75"
        elif peak >= 200 and pos["sl_phase"] in ("BREAKEVEN","LOCK75"):
            trail = entry + (peak*0.5/qty) if action == "BUY" else entry - (peak*0.5/qty)
            pos["sl"] = max(pos["sl"], round(trail,2)) if action=="BUY" else min(pos["sl"], round(trail,2))
            pos["sl_phase"] = "TRAILING"
        _save_json(POSITIONS_FILE, self.positions)
        if action == "BUY":
            if current_price <= pos["sl"]:      self.exit_trade(stock, current_price, "STOP_LOSS")
            elif current_price >= pos["target"]: self.exit_trade(stock, current_price, "TARGET")
        else:
            if current_price >= pos["sl"]:      self.exit_trade(stock, current_price, "STOP_LOSS")
            elif current_price <= pos["target"]: self.exit_trade(stock, current_price, "TARGET")

    def get_account_margins(self):
        try:
            m = self.kite.margins().get("equity", {})
            return {"available": m.get("available",{}).get("live_balance",0),
                    "used": m.get("utilised",{}).get("debits",0)}
        except: return {"available": 0, "used": 0}

    def close_all_positions(self, reason="EOD"):
        for stock in list(self.positions.keys()):
            self.exit_trade(stock, self.positions[stock].get("last_price", self.positions[stock]["entry"]), reason)
