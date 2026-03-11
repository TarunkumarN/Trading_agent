"""
risk/daily_guard.py
Daily P&L circuit breaker and trading state manager.

States:
  NORMAL     → Trade freely (score >= 6)
  SELECTIVE  → Daily profit >= Rs 500 (score >= 9 only)
  PROTECTED  → Daily profit >= Rs 800 (no new trades)
  HALTED     → Daily loss >= Rs 500 (no new trades, all closed)
"""
from config import (
    DAILY_LOSS_LIMIT, DAILY_PROFIT_SELECTIVE, DAILY_PROFIT_STOP,
    MIN_SIGNAL_SCORE, MIN_SCORE_SELECTIVE
)
from notifications.telegram_alerts import (
    alert_circuit_breaker, alert_selective_mode, alert_protect_mode
)


class DailyGuard:

    def __init__(self):
        self.realised_pnl   = 0.0
        self.unrealised_pnl = 0.0
        self.trades         = 0
        self.wins           = 0
        self.losses         = 0
        self.halted         = False
        self.selective      = False
        self.protected      = False

    # ── Call after every trade closes ────────────────────────
    def update(self, trade_pnl: float):
        self.realised_pnl += trade_pnl
        self.trades       += 1
        if trade_pnl >= 0:
            self.wins   += 1
        else:
            self.losses += 1
        self._check_thresholds()

    def _check_thresholds(self):
        pnl = self.realised_pnl

        # Loss side — halt immediately
        if pnl <= -DAILY_LOSS_LIMIT and not self.halted:
            self.halted = True
            alert_circuit_breaker(pnl, self.trades)

        # Profit side — protect the great day
        elif pnl >= DAILY_PROFIT_STOP and not self.protected:
            self.protected = True
            alert_protect_mode(pnl)

        # Profit side — switch to selective mode
        elif pnl >= DAILY_PROFIT_SELECTIVE and not self.selective:
            self.selective = True
            alert_selective_mode(pnl)

    # ── Call before placing any new order ────────────────────
    def can_trade(self, signal_score: int) -> tuple[bool, str]:
        """
        Returns (allowed: bool, reason: str)
        Always call this before placing a new trade.
        """
        if self.halted:
            return False, "HALTED: Daily loss limit of Rs 500 reached"

        if self.protected:
            return False, "PROTECTED: Daily profit of Rs 800 reached — locking the day"

        min_score = MIN_SCORE_SELECTIVE if self.selective else MIN_SIGNAL_SCORE

        if signal_score < min_score:
            mode = "SELECTIVE (9+ required)" if self.selective else "NORMAL (6+ required)"
            return False, f"Score {signal_score} below threshold {min_score} [{mode}]"

        return True, "OK"

    # ── Utility ───────────────────────────────────────────────
    def status(self) -> str:
        if self.halted:    return "HALTED"
        if self.protected: return "PROTECTED"
        if self.selective: return "SELECTIVE"
        return "NORMAL"

    def win_rate(self) -> float:
        return (self.wins / self.trades * 100) if self.trades > 0 else 0.0

    def summary(self) -> dict:
        return {
            "realised_pnl": round(self.realised_pnl, 2),
            "trades":       self.trades,
            "wins":         self.wins,
            "losses":       self.losses,
            "win_rate":     round(self.win_rate(), 1),
            "state":        self.status()
        }
