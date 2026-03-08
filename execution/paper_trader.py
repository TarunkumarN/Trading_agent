"""
execution/paper_trader.py
Simulates trades in paper mode — no real money, no real orders.
Implements the full trailing stop logic.
"""
from datetime import datetime
from risk.daily_guard import DailyGuard
from notifications.telegram_alerts import (
    alert_trade_entry, alert_trade_exit, alert_sl_moved
)


class PaperTrader:

    def __init__(self, guard: DailyGuard):
        self.guard      = guard
        self.positions  = {}   # stock → position dict
        self.trade_log  = []   # closed trades history
        self.brokerage  = 0.0  # total simulated brokerage

    # ── Open a new position ───────────────────────────────────
    def enter(self, stock: str, action: str, qty: int,
              entry: float, sl: float, target: float, score: int):

        if stock in self.positions:
            print(f"[PAPER] Already have open position in {stock}, skipping")
            return

        self.positions[stock] = {
            "action":   action,
            "qty":      qty,
            "entry":    entry,
            "sl":       sl,
            "target":   target,
            "peak_pnl": 0.0,
            "sl_phase": "INITIAL",
            "time":     datetime.now().strftime("%H:%M:%S")
        }

        # Simulate brokerage: Rs 20 per order (Zerodha intraday)
        self.brokerage += 20

        alert_trade_entry(stock, action, qty, entry, sl, target, score)
        print(f"[PAPER] ENTER {action} {qty}x {stock} @ ₹{entry:.2f} | SL:₹{sl:.2f} | TGT:₹{target:.2f}")

    # ── Update with latest price (call on every tick/candle) ──
    def update_price(self, stock: str, current_price: float):
        if stock not in self.positions:
            return

        pos    = self.positions[stock]
        qty    = pos["qty"]
        entry  = pos["entry"]
        action = pos["action"]

        # Calculate current unrealised P&L
        if action == "BUY":
            pnl = (current_price - entry) * qty
        else:
            pnl = (entry - current_price) * qty

        # Track peak P&L for trailing stop
        if pnl > pos["peak_pnl"]:
            pos["peak_pnl"] = pnl

        # ── Trailing Stop Logic ───────────────────────────────
        new_sl, phase = self._calculate_trailing_sl(pos, current_price, pnl)
        if new_sl and phase != pos["sl_phase"]:
            pos["sl"]       = new_sl
            pos["sl_phase"] = phase
            alert_sl_moved(stock, new_sl, phase)
            print(f"[PAPER] SL moved for {stock}: ₹{new_sl:.2f} ({phase})")

        # ── Check Exit Conditions ─────────────────────────────
        hit_sl = (
            (action == "BUY"  and current_price <= pos["sl"]) or
            (action == "SELL" and current_price >= pos["sl"])
        )
        hit_target = (
            (action == "BUY"  and current_price >= pos["target"]) or
            (action == "SELL" and current_price <= pos["target"])
        )

        if hit_target:
            self._close(stock, current_price, pnl, "TARGET HIT")
        elif hit_sl:
            self._close(stock, current_price, pnl, "STOP LOSS")

    def _calculate_trailing_sl(self, pos, current_price, pnl):
        """
        Phase 1: Entry → No change (initial hard stop)
        Phase 2: +Rs100 profit → Move SL to breakeven
        Phase 3: +Rs150 profit → Lock Rs75 minimum profit
        Phase 4: +Rs200 profit → Trail at 50% of peak profit
        """
        entry  = pos["entry"]
        action = pos["action"]
        qty    = pos["qty"]
        current_sl = pos["sl"]

        if pnl >= 200 and pos["peak_pnl"] >= 200:
            # Phase 4: Trail at 50% of peak
            locked_per_share = (pos["peak_pnl"] * 0.5) / qty
            if action == "BUY":
                new_sl = round(entry + locked_per_share, 2)
                if new_sl > current_sl:
                    return new_sl, "TRAILING 50%"
            else:
                new_sl = round(entry - locked_per_share, 2)
                if new_sl < current_sl:
                    return new_sl, "TRAILING 50%"

        elif pnl >= 150:
            # Phase 3: Lock Rs75 minimum
            locked_per_share = 75 / qty
            if action == "BUY":
                new_sl = round(entry + locked_per_share, 2)
                if new_sl > current_sl:
                    return new_sl, "LOCKED +Rs75"
            else:
                new_sl = round(entry - locked_per_share, 2)
                if new_sl < current_sl:
                    return new_sl, "LOCKED +Rs75"

        elif pnl >= 100:
            # Phase 2: Breakeven
            if action == "BUY" and entry > current_sl:
                return entry, "BREAKEVEN"
            elif action == "SELL" and entry < current_sl:
                return entry, "BREAKEVEN"

        return None, pos["sl_phase"]

    # ── Close a position ──────────────────────────────────────
    def _close(self, stock: str, exit_price: float, pnl: float, reason: str):
        pos = self.positions.pop(stock)
        self.brokerage += 20   # Exit order brokerage

        self.guard.update(pnl)

        self.trade_log.append({
            "stock":      stock,
            "action":     pos["action"],
            "qty":        pos["qty"],
            "entry":      pos["entry"],
            "exit":       exit_price,
            "pnl":        round(pnl, 2),
            "reason":     reason,
            "entry_time": pos["time"],
            "exit_time":  datetime.now().strftime("%H:%M:%S")
        })

        alert_trade_exit(
            stock, pos["action"], pos["entry"],
            exit_price, pnl, self.guard.realised_pnl, reason
        )
        print(f"[PAPER] EXIT {stock} @ ₹{exit_price:.2f} | P&L: ₹{pnl:+.2f} | {reason}")

    # ── Force close all positions (end of day 3:15 PM) ───────
    def close_all(self, latest_prices: dict):
        for stock in list(self.positions.keys()):
            pos   = self.positions[stock]
            price = latest_prices.get(stock, pos["entry"])
            qty   = pos["qty"]
            if pos["action"] == "BUY":
                pnl = (price - pos["entry"]) * qty
            else:
                pnl = (pos["entry"] - price) * qty
            self._close(stock, price, pnl, "END OF DAY CLOSE")

    # ── Time stop (exit if trade flat after 15 minutes) ──────
    def check_time_stops(self, latest_prices: dict):
        now = datetime.now()
        for stock in list(self.positions.keys()):
            pos = self.positions[stock]
            try:
                entry_time = datetime.strptime(
                    f"{now.date()} {pos['time']}", "%Y-%m-%d %H:%M:%S"
                )
                elapsed_min = (now - entry_time).seconds / 60
                if elapsed_min >= 15:
                    price = latest_prices.get(stock, pos["entry"])
                    qty   = pos["qty"]
                    pnl   = (price - pos["entry"]) * qty if pos["action"] == "BUY" \
                            else (pos["entry"] - price) * qty
                    self._close(stock, price, pnl, "TIME STOP (15 min)")
            except Exception:
                pass
