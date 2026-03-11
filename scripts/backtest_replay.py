"""
scripts/backtest_replay.py
Replay OHLCV candles through the current strategy and risk rules.

CSV columns required:
    timestamp,symbol,open,high,low,close,volume
Optional columns:
    market_bias_pct
"""
import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import MAX_OPEN_POSITIONS, PORTFOLIO_VALUE, RISK_REWARD_RATIO
from risk.daily_guard import DailyGuard
from risk.position_sizer import calculate_quantity, calculate_stop_and_target
from strategies.signal_scorer import calculate_signals, reset_opening_ranges, set_nifty_bias, update_opening_range


@dataclass
class ReplayPosition:
    symbol: str
    action: str
    qty: int
    entry: float
    stop: float
    target: float
    score: int
    entry_index: int
    entry_time: str


class ReplayEngine:
    def __init__(self, time_stop_bars: int = 3):
        self.guard = DailyGuard()
        self.positions = {}
        self.trade_log = []
        self.price_history = {}
        self.volume_history = {}
        self.high_history = {}
        self.low_history = {}
        self.brokerage = 0.0
        self.time_stop_bars = time_stop_bars

    def _series(self, symbol):
        self.price_history.setdefault(symbol, [])
        self.volume_history.setdefault(symbol, [])
        self.high_history.setdefault(symbol, [])
        self.low_history.setdefault(symbol, [])
        return self.price_history[symbol], self.volume_history[symbol], self.high_history[symbol], self.low_history[symbol]

    def _current_vwap(self, symbol):
        prices = self.price_history.get(symbol, [])
        volumes = self.volume_history.get(symbol, [])
        if not prices or not volumes:
            return 0.0
        total_vol = sum(volumes[-20:])
        if total_vol <= 0:
            return prices[-1]
        return sum(p * v for p, v in zip(prices[-20:], volumes[-20:])) / total_vol

    def _record_trade(self, position, exit_price, reason, exit_time):
        pnl = ((exit_price - position.entry) if position.action == "BUY" else (position.entry - exit_price)) * position.qty - 40
        self.brokerage += 40
        self.guard.update(round(pnl, 2))
        self.trade_log.append({
            "stock": position.symbol,
            "action": position.action,
            "qty": position.qty,
            "entry": round(position.entry, 2),
            "exit": round(exit_price, 2),
            "pnl": round(pnl, 2),
            "reason": reason,
            "score": position.score,
            "entry_time": position.entry_time,
            "exit_time": exit_time,
        })

    def on_bar(self, row_index, row):
        symbol = row.symbol
        prices, volumes, highs, lows = self._series(symbol)
        prices.append(float(row.close))
        volumes.append(float(row.volume))
        highs.append(float(row.high))
        lows.append(float(row.low))
        if len(prices) > 120:
            del prices[:-120], volumes[:-120], highs[:-120], lows[:-120]

        if row.timestamp.hour == 9 and row.timestamp.minute <= 34:
            update_opening_range(symbol, float(row.high), float(row.low), row.timestamp.minute)

        if symbol in self.positions:
            position = self.positions[symbol]
            hit_stop = (position.action == "BUY" and row.low <= position.stop) or (position.action == "SELL" and row.high >= position.stop)
            hit_target = (position.action == "BUY" and row.high >= position.target) or (position.action == "SELL" and row.low <= position.target)
            timed_out = row_index - position.entry_index >= self.time_stop_bars
            if hit_target:
                self._record_trade(position, position.target, "TARGET HIT", row.timestamp.strftime("%H:%M:%S"))
                del self.positions[symbol]
            elif hit_stop:
                self._record_trade(position, position.stop, "STOP LOSS", row.timestamp.strftime("%H:%M:%S"))
                del self.positions[symbol]
            elif timed_out:
                self._record_trade(position, float(row.close), f"TIME STOP ({self.time_stop_bars} bars)", row.timestamp.strftime("%H:%M:%S"))
                del self.positions[symbol]

        if len(prices) < 30 or symbol in self.positions or len(self.positions) >= MAX_OPEN_POSITIONS:
            return

        vwap = self._current_vwap(symbol)
        signal = calculate_signals(prices, volumes, vwap, highs=highs, lows=lows, symbol=symbol)
        allowed, _ = self.guard.can_trade(signal["score"])
        if not allowed or signal["action"] not in {"BUY", "SELL"}:
            return

        stop, target = calculate_stop_and_target(float(row.close), signal["action"], signal.get("atr"))
        sizing = calculate_quantity(float(row.close), stop)
        if sizing["qty"] <= 0:
            return

        self.brokerage += 20
        self.positions[symbol] = ReplayPosition(
            symbol=symbol,
            action=signal["action"],
            qty=sizing["qty"],
            entry=float(row.close),
            stop=stop,
            target=target,
            score=signal["score"],
            entry_index=row_index,
            entry_time=row.timestamp.strftime("%H:%M:%S"),
        )

    def close_all(self, timestamp):
        for symbol in list(self.positions.keys()):
            position = self.positions.pop(symbol)
            self._record_trade(position, position.entry, "END OF DAY CLOSE", timestamp.strftime("%H:%M:%S"))

    def report(self):
        wins = [t for t in self.trade_log if t["pnl"] > 0]
        losses = [t for t in self.trade_log if t["pnl"] <= 0]
        gross = round(sum(t["pnl"] for t in self.trade_log), 2)
        net = round(gross - self.brokerage, 2)

        avg_win = round(sum(t["pnl"] for t in wins) / len(wins), 2) if wins else 0.0
        avg_loss = round(sum(t["pnl"] for t in losses) / len(losses), 2) if losses else 0.0
        gross_profit = round(sum(t["pnl"] for t in wins), 2)
        gross_loss = round(abs(sum(t["pnl"] for t in losses)), 2)
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss else 0.0
        expectancy = round((gross / len(self.trade_log)), 2) if self.trade_log else 0.0

        running = PORTFOLIO_VALUE
        peak = PORTFOLIO_VALUE
        max_drawdown = 0.0
        equity_curve = []
        loss_streak = 0
        longest_loss_streak = 0
        per_symbol = {}
        reason_breakdown = {}

        for trade in self.trade_log:
            running += trade["pnl"] - 40
            peak = max(peak, running)
            drawdown = peak - running
            max_drawdown = max(max_drawdown, drawdown)
            equity_curve.append({"exit_time": trade["exit_time"], "equity": round(running, 2)})

            if trade["pnl"] <= 0:
                loss_streak += 1
                longest_loss_streak = max(longest_loss_streak, loss_streak)
            else:
                loss_streak = 0

            sym = trade["stock"]
            per_symbol.setdefault(sym, {"trades": 0, "pnl": 0.0, "wins": 0, "losses": 0})
            per_symbol[sym]["trades"] += 1
            per_symbol[sym]["pnl"] = round(per_symbol[sym]["pnl"] + trade["pnl"], 2)
            if trade["pnl"] > 0:
                per_symbol[sym]["wins"] += 1
            else:
                per_symbol[sym]["losses"] += 1

            reason_breakdown[trade["reason"]] = reason_breakdown.get(trade["reason"], 0) + 1

        for sym_data in per_symbol.values():
            total = sym_data["trades"]
            sym_data["win_rate"] = round((sym_data["wins"] / total) * 100, 1) if total else 0.0

        return {
            "trades": len(self.trade_log),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round((len(wins) / len(self.trade_log) * 100), 1) if self.trade_log else 0.0,
            "gross_pnl": gross,
            "brokerage": round(self.brokerage, 2),
            "net_pnl": net,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "max_drawdown": round(max_drawdown, 2),
            "longest_loss_streak": longest_loss_streak,
            "guard": self.guard.summary(),
            "portfolio_value_end": round(PORTFOLIO_VALUE + net, 2),
            "risk_reward_ratio": RISK_REWARD_RATIO,
            "reason_breakdown": reason_breakdown,
            "per_symbol": per_symbol,
            "equity_curve": equity_curve,
        }


def run_backtest(csv_path: Path, output_path: Path | None = None, time_stop_bars: int = 3):
    df = pd.read_csv(csv_path)
    required = {"timestamp", "symbol", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["timestamp", "symbol"]).reset_index(drop=True)

    engine = ReplayEngine(time_stop_bars=time_stop_bars)
    reset_opening_ranges()

    for idx, row in enumerate(df.itertuples(index=False)):
        if hasattr(row, "market_bias_pct") and pd.notna(row.market_bias_pct):
            set_nifty_bias(float(row.market_bias_pct))
        engine.on_bar(idx, row)

    if not df.empty:
        engine.close_all(df.iloc[-1]["timestamp"])

    report = engine.report()
    payload = {"summary": report, "trades": engine.trade_log}

    if output_path:
        output_path.write_text(json.dumps(payload, indent=2))
    return payload


def main():
    parser = argparse.ArgumentParser(description="Replay candles through the trading strategy")
    parser.add_argument("csv_path", help="Path to OHLCV CSV")
    parser.add_argument("--output", help="Optional JSON output path")
    parser.add_argument("--time-stop-bars", type=int, default=3, help="Bars before forced time-stop exit")
    args = parser.parse_args()

    payload = run_backtest(Path(args.csv_path), Path(args.output) if args.output else None, time_stop_bars=args.time_stop_bars)
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
