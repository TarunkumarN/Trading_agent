from dataclasses import dataclass


@dataclass
class DrawdownControl:
    initial_capital: float
    max_drawdown_pct: float = 8.0

    def __post_init__(self):
        self.peak_equity = self.initial_capital
        self.current_equity = self.initial_capital
        self.breached = False

    def update(self, realised_pnl: float):
        self.current_equity = self.initial_capital + realised_pnl
        self.peak_equity = max(self.peak_equity, self.current_equity)
        if self.peak_equity <= 0:
            self.breached = True
            return self.breached
        drawdown_pct = ((self.peak_equity - self.current_equity) / self.peak_equity) * 100
        self.breached = drawdown_pct >= self.max_drawdown_pct
        return self.breached

    def summary(self):
        drawdown_pct = ((self.peak_equity - self.current_equity) / self.peak_equity * 100) if self.peak_equity else 0.0
        return {
            "initial_capital": round(self.initial_capital, 2),
            "peak_equity": round(self.peak_equity, 2),
            "current_equity": round(self.current_equity, 2),
            "drawdown_pct": round(drawdown_pct, 2),
            "breached": self.breached,
        }
