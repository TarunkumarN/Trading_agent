"""
routes_portfolio.py — Portfolio data endpoints
"""
from fastapi import APIRouter
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import os

router = APIRouter(prefix="/api", tags=["portfolio"])

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
PORTFOLIO_VALUE = float(os.getenv("PORTFOLIO_VALUE", "10000"))
client = MongoClient(MONGO_URL)
db = client[DB_NAME]


def _ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


@router.get("/portfolio")
async def get_portfolio():
    all_trades = list(db["trades"].find({}, {"_id": 0}).sort("created_at", -1))
    open_pos = list(db["open_positions"].find({}, {"_id": 0}))
    today = _ist_now().strftime("%Y-%m-%d")
    today_trades = [t for t in all_trades if t.get("date") == today]

    total_pnl = round(sum(t.get("pnl", 0) for t in all_trades), 2)
    day_pnl = round(sum(t.get("pnl", 0) for t in today_trades), 2)
    wins = [t for t in all_trades if t.get("pnl", 0) > 0]
    losses = [t for t in all_trades if t.get("pnl", 0) <= 0]
    win_rate = round(len(wins) / len(all_trades) * 100, 1) if all_trades else 0

    avg_profit = round(sum(t["pnl"] for t in wins) / len(wins), 2) if wins else 0
    avg_loss = round(sum(t["pnl"] for t in losses) / len(losses), 2) if losses else 0
    gross_profit = sum(t["pnl"] for t in wins)
    gross_loss = abs(sum(t["pnl"] for t in losses))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0

    # Equity curve & max drawdown
    equity_curve = []
    running = PORTFOLIO_VALUE
    peak = running
    max_dd = 0
    daily_map = {}
    for t in sorted(all_trades, key=lambda x: (x.get("date", ""), x.get("exit_time", ""))):
        running += t.get("pnl", 0)
        peak = max(peak, running)
        dd = round(((peak - running) / peak) * 100, 2) if peak > 0 else 0
        max_dd = max(max_dd, dd)
        d = t.get("date", today)
        daily_map[d] = round(running, 2)

    equity_curve = [{"date": k, "equity": v} for k, v in sorted(daily_map.items())]

    # Daily PnL chart
    dpnl = {}
    for t in all_trades:
        d = t.get("date", today)
        dpnl[d] = round(dpnl.get(d, 0) + t.get("pnl", 0), 2)
    daily_pnl_chart = [{"date": k, "pnl": v} for k, v in sorted(dpnl.items())]

    # Unrealised P&L
    unreal = 0
    for p in open_pos:
        cur = p.get("current_price", p.get("entry", 0))
        ent = p.get("entry", 0)
        q = p.get("qty", 0)
        act = p.get("action", "BUY")
        unreal += (cur - ent) * q if act == "BUY" else (ent - cur) * q

    return {
        "initial_capital": PORTFOLIO_VALUE,
        "current_equity": round(PORTFOLIO_VALUE + total_pnl, 2),
        "total_pnl": total_pnl,
        "day_pnl": day_pnl,
        "unrealised_pnl": round(unreal, 2),
        "total_trades": len(all_trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": win_rate,
        "avg_profit": avg_profit,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "max_drawdown": round(max_dd, 2),
        "open_positions": len(open_pos),
        "equity_curve": equity_curve,
        "daily_pnl_chart": daily_pnl_chart,
        "timestamp": _ist_now().strftime("%H:%M:%S"),
    }


@router.get("/open-positions")
async def get_open_positions():
    positions = list(db["open_positions"].find({}, {"_id": 0}))
    result = []
    for p in positions:
        cur = p.get("current_price", p.get("entry", 0))
        ent = p.get("entry", 0)
        q = p.get("qty", 0)
        act = p.get("action", "BUY")
        unreal = (cur - ent) * q if act == "BUY" else (ent - cur) * q
        result.append({
            "symbol": p.get("symbol"),
            "strategy": p.get("strategy", "MiniMax Scalper"),
            "entry_price": ent,
            "current_price": cur,
            "quantity": q,
            "stop_loss": p.get("sl", 0),
            "target": p.get("target", 0),
            "unrealised_pnl": round(unreal, 2),
            "entry_time": p.get("entry_time", ""),
            "entry_date": p.get("entry_date", ""),
            "action": act,
            "sl_phase": p.get("sl_phase", "INITIAL"),
            "score": p.get("score", 0),
        })
    return {"positions": result, "count": len(result)}
