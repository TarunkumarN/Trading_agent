from collections import defaultdict


def calculate_performance_metrics(trades, starting_capital=10000):
    closed = [trade for trade in trades if trade.get("pnl") is not None]
    wins = [trade for trade in closed if trade.get("pnl", 0) > 0]
    losses = [trade for trade in closed if trade.get("pnl", 0) <= 0]
    gross = round(sum(trade.get("pnl", 0) for trade in closed), 2)
    equity = starting_capital
    peak = starting_capital
    max_drawdown = 0.0
    equity_curve = []
    strategy_pnl = defaultdict(float)
    heatmap = defaultdict(float)

    for trade in closed:
        pnl = float(trade.get("pnl", 0))
        equity += pnl
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
        equity_curve.append({
            "time": trade.get("exit_time", ""),
            "equity": round(equity, 2),
        })
        strategy = trade.get("strategy", "unknown")
        strategy_pnl[strategy] += pnl
        hour = (trade.get("entry_time") or "00:00:00")[:2]
        heatmap[hour] += pnl

    gross_profit = sum(trade.get("pnl", 0) for trade in wins)
    gross_loss = abs(sum(trade.get("pnl", 0) for trade in losses))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss else 0.0

    return {
        "daily_pnl": gross,
        "strategy_wise_pnl": {k: round(v, 2) for k, v in strategy_pnl.items()},
        "win_rate": round((len(wins) / len(closed) * 100), 1) if closed else 0.0,
        "max_drawdown": round(max_drawdown, 2),
        "equity_curve": equity_curve,
        "trade_heatmap": dict(heatmap),
        "profit_factor": profit_factor,
        "avg_win": round(gross_profit / len(wins), 2) if wins else 0.0,
        "avg_loss": round(sum(trade.get("pnl", 0) for trade in losses) / len(losses), 2) if losses else 0.0,
        "total_trades": len(closed),
    }
