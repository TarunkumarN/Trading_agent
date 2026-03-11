"""
risk/daily_guard.py
Daily P&L circuit breaker and portfolio state manager.
"""
from config import (
    DAILY_LOSS_LIMIT,
    DAILY_PROFIT_SELECTIVE,
    DAILY_PROFIT_STOP,
    MAX_CONSECUTIVE_LOSSES,
    MAX_TRADES_PER_DAY,
    MIN_SCORE_SELECTIVE,
    MIN_SIGNAL_SCORE,
)
from notifications.telegram_alerts import alert_circuit_breaker, alert_protect_mode, alert_selective_mode


class DailyGuard:
    def __init__(self):
        self.realised_pnl = 0.0
        self.unrealised_pnl = 0.0
        self.trades = 0
        self.wins = 0
        self.losses = 0
        self.consecutive_losses = 0
        self.halted = False
        self.selective = False
        self.protected = False

    def update(self, trade_pnl: float):
        self.realised_pnl += trade_pnl
        self.trades += 1
        if trade_pnl >= 0:
            self.wins += 1
            self.consecutive_losses = 0
        else:
            self.losses += 1
            self.consecutive_losses += 1
        self._check_thresholds()

    def _check_thresholds(self):
        pnl = self.realised_pnl
        if pnl <= -DAILY_LOSS_LIMIT and not self.halted:
            self.halted = True
            alert_circuit_breaker(pnl, self.trades)
            return
        if self.trades >= MAX_TRADES_PER_DAY and not self.halted:
            self.halted = True
            return
        if self.consecutive_losses >= MAX_CONSECUTIVE_LOSSES and not self.halted:
            self.halted = True
            return
        if pnl >= DAILY_PROFIT_STOP and not self.protected:
            self.protected = True
            alert_protect_mode(pnl)
            return
        if pnl >= DAILY_PROFIT_SELECTIVE and not self.selective:
            self.selective = True
            alert_selective_mode(pnl)

    def can_trade(self, signal_score: int):
        if self.halted:
            if self.trades >= MAX_TRADES_PER_DAY:
                return False, f"HALTED: Max trades per day {MAX_TRADES_PER_DAY} reached"
            if self.consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
                return False, f"HALTED: {self.consecutive_losses} consecutive losses"
            return False, f"HALTED: Daily loss limit of Rs {DAILY_LOSS_LIMIT:.0f} reached"
        if self.protected:
            return False, f"PROTECTED: Daily profit of Rs {DAILY_PROFIT_STOP:.0f} reached"

        min_score = MIN_SCORE_SELECTIVE if self.selective else MIN_SIGNAL_SCORE
        strength = abs(signal_score)
        if strength < min_score:
            mode = "SELECTIVE" if self.selective else "NORMAL"
            return False, f"Score strength {strength} below threshold {min_score} [{mode}]"
        if self.trades >= MAX_TRADES_PER_DAY:
            return False, f"Trade cap reached ({MAX_TRADES_PER_DAY})"
        if self.consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
            return False, f"Loss streak cap reached ({MAX_CONSECUTIVE_LOSSES})"
        return True, "OK"

    def status(self):
        if self.halted:
            return "HALTED"
        if self.protected:
            return "PROTECTED"
        if self.selective:
            return "SELECTIVE"
        return "NORMAL"

    def win_rate(self):
        return (self.wins / self.trades * 100) if self.trades > 0 else 0.0

    def summary(self):
        return {
            "realised_pnl": round(self.realised_pnl, 2),
            "trades": self.trades,
            "wins": self.wins,
            "losses": self.losses,
            "consecutive_losses": self.consecutive_losses,
            "win_rate": round(self.win_rate(), 1),
            "state": self.status(),
            "max_trades_per_day": MAX_TRADES_PER_DAY,
            "max_consecutive_losses": MAX_CONSECUTIVE_LOSSES,
        }
