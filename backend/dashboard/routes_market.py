"""
routes_market.py — Market intelligence endpoints (Pre-market, Post-market, Gainers, Losers)
"""
from fastapi import APIRouter
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import requests
import logging
import os

router = APIRouter(prefix="/api", tags=["market"])
logger = logging.getLogger("trading_agent")

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Referer": "https://www.nseindia.com/",
}


def _ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


def _fetch_nse_data():
    """Fetch NSE equity data with session handling."""
    try:
        s = requests.Session()
        s.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=6)
        indices = {}

        r = s.get("https://www.nseindia.com/api/allIndices", headers=NSE_HEADERS, timeout=6)
        if r.ok:
            for idx in r.json().get("data", []):
                name = idx.get("index", "")
                ltp = idx.get("last", 0)
                prev = idx.get("previousClose", 0)
                chg = round(ltp - prev, 2)
                chgp = round(idx.get("percentChange", 0), 2)
                if name in ("NIFTY 50", "NIFTY BANK", "INDIA VIX", "NIFTY NEXT 50", "NIFTY MIDCAP 50"):
                    indices[name] = {"price": ltp, "change": chg, "change_pct": chgp,
                                     "previous": prev, "trend": "Bullish" if chg > 0 else "Bearish"}

        stocks = []
        r2 = s.get("https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050", headers=NSE_HEADERS, timeout=6)
        if r2.ok:
            for item in r2.json().get("data", [])[1:]:
                stocks.append({
                    "symbol": item.get("symbol", ""),
                    "price": round(item.get("lastPrice", 0), 2),
                    "change": round(item.get("change", 0), 2),
                    "change_pct": round(item.get("pChange", 0), 2),
                    "open": round(item.get("open", 0), 2),
                    "high": round(item.get("dayHigh", 0), 2),
                    "low": round(item.get("dayLow", 0), 2),
                    "previous_close": round(item.get("previousClose", 0), 2),
                    "volume": item.get("totalTradedVolume", 0),
                    "value": item.get("totalTradedValue", 0),
                })
        return indices, stocks
    except Exception as e:
        logger.warning(f"NSE fetch error: {e}")
        return {}, []


@router.get("/market/gainers")
async def get_gainers():
    indices, stocks = _fetch_nse_data()
    gainers = sorted([s for s in stocks if s["change_pct"] > 0], key=lambda x: x["change_pct"], reverse=True)
    return {"gainers": gainers[:15], "total": len(gainers), "timestamp": _ist_now().strftime("%H:%M:%S")}


@router.get("/market/losers")
async def get_losers():
    indices, stocks = _fetch_nse_data()
    losers = sorted([s for s in stocks if s["change_pct"] < 0], key=lambda x: x["change_pct"])
    return {"losers": losers[:15], "total": len(losers), "timestamp": _ist_now().strftime("%H:%M:%S")}


@router.get("/market/active")
async def get_most_active():
    indices, stocks = _fetch_nse_data()
    active = sorted(stocks, key=lambda x: x.get("volume", 0), reverse=True)
    return {"active": active[:15], "total": len(active), "timestamp": _ist_now().strftime("%H:%M:%S")}


@router.get("/market/premarket")
async def get_premarket():
    """Pre-market analysis: gap ups/downs, volume leaders, index bias."""
    indices, stocks = _fetch_nse_data()
    now = _ist_now()
    h = now.hour
    phase = "PRE-MARKET" if h < 9 or (h == 9 and now.minute < 15) else "MARKET OPEN" if (h < 15 or (h == 15 and now.minute < 30)) else "POST-MARKET"

    gap_ups = sorted([s for s in stocks if s.get("change_pct", 0) > 0.5], key=lambda x: x["change_pct"], reverse=True)[:10]
    gap_downs = sorted([s for s in stocks if s.get("change_pct", 0) < -0.5], key=lambda x: x["change_pct"])[:10]
    vol_leaders = sorted(stocks, key=lambda x: x.get("volume", 0), reverse=True)[:10]

    # Market bias
    nifty = indices.get("NIFTY 50", {})
    vix = indices.get("INDIA VIX", {})
    bias = "BULLISH" if nifty.get("change", 0) > 50 else "BEARISH" if nifty.get("change", 0) < -50 else "NEUTRAL"
    vix_level = "HIGH VOLATILITY" if vix.get("price", 0) > 20 else "NORMAL" if vix.get("price", 0) > 14 else "LOW VOLATILITY"

    # AI recommendation
    bullish_count = len([s for s in stocks if s.get("change_pct", 0) > 0])
    bearish_count = len([s for s in stocks if s.get("change_pct", 0) < 0])
    breadth = round(bullish_count / max(1, len(stocks)) * 100, 1)

    ai_recommendation = {
        "market_bias": bias,
        "vix_reading": vix_level,
        "breadth": f"{breadth}% bullish",
        "suggested_action": "AGGRESSIVE LONGS" if bias == "BULLISH" and breadth > 60 else
                           "DEFENSIVE/SHORTS" if bias == "BEARISH" and breadth < 40 else
                           "SELECTIVE TRADING",
        "risk_level": "LOW" if vix.get("price", 0) < 15 else "MEDIUM" if vix.get("price", 0) < 20 else "HIGH",
    }

    return {
        "phase": phase,
        "indices": indices,
        "gap_ups": gap_ups,
        "gap_downs": gap_downs,
        "volume_leaders": vol_leaders,
        "market_bias": bias,
        "ai_recommendation": ai_recommendation,
        "all_stocks": stocks[:30],
        "timestamp": now.strftime("%H:%M:%S"),
    }


@router.get("/market/postmarket")
async def get_postmarket():
    """Post-market analysis: day summary, top performers, sector performance."""
    indices, stocks = _fetch_nse_data()
    now = _ist_now()

    # Day's trades summary
    today = now.strftime("%Y-%m-%d")
    today_trades = list(db["trades"].find({"date": today}, {"_id": 0}))
    day_pnl = round(sum(t.get("pnl", 0) for t in today_trades), 2)
    wins = len([t for t in today_trades if t.get("pnl", 0) > 0])
    total = len(today_trades)
    win_rate = round(wins / total * 100, 1) if total > 0 else 0

    # Market summary
    nifty = indices.get("NIFTY 50", {})
    bank = indices.get("NIFTY BANK", {})

    # Best & worst stocks
    sorted_stocks = sorted(stocks, key=lambda x: x.get("change_pct", 0), reverse=True)
    best = sorted_stocks[:5] if sorted_stocks else []
    worst = sorted_stocks[-5:] if len(sorted_stocks) >= 5 else []

    # Breadth
    adv = len([s for s in stocks if s.get("change_pct", 0) > 0])
    dec = len([s for s in stocks if s.get("change_pct", 0) < 0])

    return {
        "phase": "POST-MARKET",
        "indices": indices,
        "trading_summary": {
            "total_trades": total,
            "wins": wins,
            "losses": total - wins,
            "win_rate": win_rate,
            "day_pnl": day_pnl,
        },
        "market_summary": {
            "nifty_close": nifty.get("price", 0),
            "nifty_change": nifty.get("change_pct", 0),
            "banknifty_close": bank.get("price", 0),
            "banknifty_change": bank.get("change_pct", 0),
            "advances": adv,
            "declines": dec,
            "breadth": f"{adv}:{dec}",
        },
        "best_performers": best,
        "worst_performers": worst,
        "timestamp": now.strftime("%H:%M:%S"),
    }
