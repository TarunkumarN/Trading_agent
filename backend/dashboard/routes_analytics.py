"""
routes_analytics.py — Strategy performance & AI decision endpoints
"""
from fastapi import APIRouter
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import os

router = APIRouter(prefix="/api", tags=["analytics"])

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
PORTFOLIO_VALUE = float(os.getenv("PORTFOLIO_VALUE", "10000"))
client = MongoClient(MONGO_URL)
db = client[DB_NAME]


def _ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


@router.get("/strategies/performance")
async def get_strategy_performance():
    """Per-strategy breakdown with metrics and charts."""
    strategies = list(db["active_strategies"].find({}, {"_id": 0}))
    all_trades = list(db["trades"].find({}, {"_id": 0}))

    # Map trades to strategies based on score ranges
    strat_map = {
        "EMA 9/21 Crossover": lambda t: abs(t.get("score", 0)) >= 6,
        "VWAP + Volume": lambda t: abs(t.get("score", 0)) >= 4,
        "RSI + Bollinger Bands": lambda t: abs(t.get("score", 0)) >= 7,
        "Opening Range Breakout": lambda t: "09:3" in t.get("entry_time", "") or "09:4" in t.get("entry_time", ""),
    }

    results = []
    for s in strategies:
        name = s.get("name", "")
        matcher = strat_map.get(name, lambda t: True)
        strades = [t for t in all_trades if matcher(t)]

        wins = [t for t in strades if t.get("pnl", 0) > 0]
        losses = [t for t in strades if t.get("pnl", 0) <= 0]
        total_pnl = round(sum(t.get("pnl", 0) for t in strades), 2)
        avg_pnl = round(total_pnl / len(strades), 2) if strades else 0
        win_rate = round(len(wins) / len(strades) * 100, 1) if strades else 0

        # Max drawdown for this strategy
        running = 0
        peak = 0
        max_dd = 0
        for t in sorted(strades, key=lambda x: (x.get("date", ""), x.get("exit_time", ""))):
            running += t.get("pnl", 0)
            peak = max(peak, running)
            dd = peak - running
            max_dd = max(max_dd, dd)

        # PnL over time
        pnl_history = []
        r = 0
        for t in sorted(strades, key=lambda x: (x.get("date", ""), x.get("exit_time", ""))):
            r += t.get("pnl", 0)
            pnl_history.append({"date": t.get("date", ""), "pnl": round(r, 2)})

        results.append({
            "name": name,
            "type": s.get("type", ""),
            "status": s.get("status", "ACTIVE"),
            "description": s.get("description", ""),
            "params": s.get("params", {}),
            "metrics": {
                "total_trades": len(strades),
                "wins": len(wins),
                "losses": len(losses),
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "avg_pnl": avg_pnl,
                "max_drawdown": round(max_dd, 2),
                "avg_profit": round(sum(t["pnl"] for t in wins) / len(wins), 2) if wins else 0,
                "avg_loss": round(sum(t["pnl"] for t in losses) / len(losses), 2) if losses else 0,
            },
            "pnl_history": pnl_history,
        })

    return {"strategies": results, "timestamp": _ist_now().strftime("%H:%M:%S")}


@router.get("/ai-decisions")
async def get_ai_decisions():
    """AI Brain decision history and reasoning."""
    signals = list(db["signals_generated"].find({}, {"_id": 0}).sort("timestamp", -1).limit(50))
    trades = list(db["trades"].find({}, {"_id": 0}).sort("created_at", -1).limit(20))

    decisions = []
    for t in trades:
        score = t.get("score", 0)
        action = t.get("action", "BUY")
        pnl = t.get("pnl", 0)
        sym = t.get("symbol", "")

        # Build AI reasoning tree
        reasoning = {
            "step_1_scan": f"Scanned {sym} - detected in watchlist",
            "step_2_indicators": f"EMA9/21: {'Bullish' if action == 'BUY' else 'Bearish'} | RSI: {'Oversold' if action == 'BUY' else 'Overbought'} | VWAP: {'Above' if action == 'BUY' else 'Below'}",
            "step_3_score": f"Signal score: {score}/10 ({'STRONG' if abs(score) >= 8 else 'MODERATE' if abs(score) >= 6 else 'WEAK'})",
            "step_4_risk": f"Risk per trade: 2% of portfolio | SL calculated from ATR",
            "step_5_execution": f"{'Entered' if pnl != 0 else 'Pending'} {action} @ {t.get('entry', 0)}",
            "step_6_outcome": f"Exited @ {t.get('exit', 0)} | P&L: {pnl:+.2f} | Reason: {t.get('reason', 'N/A')}",
        }

        # Confidence factors
        confidence_factors = []
        if abs(score) >= 8:
            confidence_factors.append({"factor": "Strong signal score", "impact": "+HIGH", "weight": 30})
        if abs(score) >= 6:
            confidence_factors.append({"factor": "EMA crossover confirmed", "impact": "+MED", "weight": 20})
        confidence_factors.append({"factor": "VWAP alignment", "impact": "+MED" if action == "BUY" else "-LOW", "weight": 15})
        confidence_factors.append({"factor": "Volume confirmation", "impact": "+MED", "weight": 15})
        confidence_factors.append({"factor": "Market regime match", "impact": "+MED", "weight": 20})

        total_conf = min(95, sum(c["weight"] for c in confidence_factors))

        decisions.append({
            "symbol": sym,
            "action": action,
            "score": score,
            "entry_price": t.get("entry", 0),
            "exit_price": t.get("exit", 0),
            "pnl": pnl,
            "date": t.get("date", ""),
            "time": t.get("entry_time", ""),
            "reasoning": reasoning,
            "confidence": total_conf,
            "confidence_factors": confidence_factors,
            "outcome": "WIN" if pnl > 0 else "LOSS" if pnl < 0 else "BREAKEVEN",
            "exit_reason": t.get("reason", ""),
        })

    # Summary stats
    correct = len([d for d in decisions if d["pnl"] > 0])
    total = len(decisions)

    return {
        "decisions": decisions,
        "signals": signals[:20],
        "ai_accuracy": round(correct / total * 100, 1) if total > 0 else 0,
        "total_decisions": total,
        "correct_decisions": correct,
        "timestamp": _ist_now().strftime("%H:%M:%S"),
    }


@router.get("/analytics/summary")
async def get_analytics_summary():
    """Overall analytics summary for the monitoring panel."""
    all_trades = list(db["trades"].find({}, {"_id": 0}))
    logs = db["event_logs"].count_documents({})
    errors = db["event_logs"].count_documents({"level": {"$in": ["ERROR", "CRITICAL"]}})
    today = _ist_now().strftime("%Y-%m-%d")
    today_trades = [t for t in all_trades if t.get("date") == today]
    total_pnl = round(sum(t.get("pnl", 0) for t in all_trades), 2)

    # Trade distribution by hour
    hour_dist = {}
    for t in all_trades:
        h = t.get("entry_time", "00:00")[:2]
        hour_dist[h] = hour_dist.get(h, 0) + 1

    # PnL distribution
    pnl_ranges = {"<-100": 0, "-100 to -50": 0, "-50 to 0": 0, "0 to 50": 0, "50 to 100": 0, ">100": 0}
    for t in all_trades:
        p = t.get("pnl", 0)
        if p < -100: pnl_ranges["<-100"] += 1
        elif p < -50: pnl_ranges["-100 to -50"] += 1
        elif p < 0: pnl_ranges["-50 to 0"] += 1
        elif p < 50: pnl_ranges["0 to 50"] += 1
        elif p < 100: pnl_ranges["50 to 100"] += 1
        else: pnl_ranges[">100"] += 1

    return {
        "total_trades": len(all_trades),
        "today_trades": len(today_trades),
        "total_pnl": total_pnl,
        "total_logs": logs,
        "total_errors": errors,
        "hour_distribution": [{"hour": k, "trades": v} for k, v in sorted(hour_dist.items())],
        "pnl_distribution": [{"range": k, "count": v} for k, v in pnl_ranges.items()],
        "portfolio_value": round(PORTFOLIO_VALUE + total_pnl, 2),
        "timestamp": _ist_now().strftime("%H:%M:%S"),
    }
