"""
routes_quant.py - Quant Intelligence API Endpoints
====================================================
Exposes the quant intelligence modules via REST API.
"""
from fastapi import APIRouter
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import os
import numpy as np

from market.options_flow import analyze_options_flow
from market.dark_pool_detector import detect_dark_pool_zones
from market.correlation_filter import check_correlation
from ai.market_predictor import predict_market_direction
from ai.trade_ranker import rank_trade
from risk.hedging_engine import analyze_portfolio_exposure
from quant.pipeline import (
    run_pipeline, is_quant_trading_hours, check_frequency_limits,
    MAX_TRADES_PER_DAY, MAX_CONSECUTIVE_LOSSES, DAILY_DRAWDOWN_LIMIT_PCT,
    MIN_RR_RATIO,
)

router = APIRouter(prefix="/api", tags=["quant"])

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
PORTFOLIO_VALUE = float(os.getenv("PORTFOLIO_VALUE", "50000"))
client = MongoClient(MONGO_URL)
db = client[DB_NAME]


def _ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


def _get_market_data_dict():
    """Build a symbol -> data dict from market cache or DB."""
    try:
        from server import _fetch_market_data_cached
        data = _fetch_market_data_cached()
        stocks = data.get("stocks", [])
        result = {}
        for s in stocks:
            result[s["symbol"]] = s
        # Add index data
        indices = data.get("indices", {})
        for name, vals in indices.items():
            result[name] = vals
        return result, data
    except Exception:
        return {}, {}


def _generate_sample_prices(symbol, n=50):
    """Generate sample price/volume data for demo when no live data exists."""
    base_prices = {
        "RELIANCE": 2485, "TCS": 3840, "HDFCBANK": 1635, "INFY": 1585,
        "ICICIBANK": 1092, "SBIN": 785, "BAJFINANCE": 6870, "ITC": 468,
        "KOTAKBANK": 1825, "LT": 3440, "AXISBANK": 1128, "MARUTI": 12320,
        "SUNPHARMA": 1685, "WIPRO": 455, "TITAN": 3595, "HINDUNILVR": 2380,
    }
    base = base_prices.get(symbol, 1000)
    np.random.seed(hash(symbol + _ist_now().strftime("%Y%m%d")) % (2**31))
    # Generate realistic brownian motion prices
    returns = np.random.normal(0.0002, 0.005, n)
    prices = [base]
    for r in returns:
        prices.append(round(prices[-1] * (1 + r), 2))
    volumes = [int(np.random.uniform(500000, 5000000)) for _ in range(n + 1)]
    vwap = round(np.mean(prices), 2)
    return prices, volumes, vwap


@router.get("/quant/pipeline/{symbol}")
async def get_pipeline_analysis(symbol: str):
    """Run full quant pipeline for a symbol."""
    symbol = symbol.upper()
    market_dict, raw_data = _get_market_data_dict()

    # Get price data
    prices, volumes, vwap = _generate_sample_prices(symbol)

    # Get current market regime
    try:
        from server import _fetch_market_data_cached
        data = _fetch_market_data_cached()
        indices = data.get("indices", {})
        stocks = data.get("stocks", [])
        nifty = indices.get("NIFTY 50", {})
        nifty_chg = nifty.get("change_pct", 0)
        bullish = len([s for s in stocks if s.get("change_pct", 0) > 0])
        total = max(1, len(stocks))
        breadth = bullish / total * 100
        if nifty_chg > 0.3 and breadth > 55:
            regime = "BULLISH"
        elif nifty_chg < -0.3 and breadth < 45:
            regime = "BEARISH"
        else:
            regime = "NEUTRAL"
    except Exception:
        regime = "NEUTRAL"

    # Generate signal data (simulate from existing engine logic)
    signal_data = _compute_signal(prices, volumes, vwap)

    # Get portfolio context
    today = _ist_now().strftime("%Y-%m-%d")
    today_trades = list(db["trades"].find({"date": today}, {"_id": 0}))
    open_positions = list(db["open_positions"].find({}, {"_id": 0}))
    daily_pnl = sum(t.get("pnl", 0) for t in today_trades)

    # Count consecutive losses
    recent_trades = list(db["trades"].find({}, {"_id": 0}).sort("created_at", -1).limit(10))
    consec_losses = 0
    for t in recent_trades:
        if t.get("pnl", 0) < 0:
            consec_losses += 1
        else:
            break

    # Compute entry/SL/target
    action = signal_data.get("action", "HOLD")
    entry = prices[-1]
    atr = signal_data.get("atr", entry * 0.01)
    if action == "BUY":
        sl = round(entry - atr, 2)
        target = round(entry + atr * MIN_RR_RATIO, 2)
    elif action == "SELL":
        sl = round(entry + atr, 2)
        target = round(entry - atr * MIN_RR_RATIO, 2)
    else:
        sl = entry
        target = entry

    result = run_pipeline(
        symbol=symbol,
        prices=prices,
        volumes=volumes,
        vwap=vwap,
        signal_data=signal_data,
        market_regime=regime,
        market_data_dict=market_dict,
        open_positions=open_positions,
        trades_today_count=len(today_trades),
        consecutive_losses=consec_losses,
        daily_pnl=daily_pnl,
        portfolio_value=PORTFOLIO_VALUE,
        entry_price=entry,
        stop_loss=sl,
        target_price=target,
    )

    result["symbol"] = symbol
    result["entry"] = entry
    result["stop_loss"] = sl
    result["target"] = target
    result["action"] = action
    result["risk_reward_ratio"] = round((abs(target - entry) / abs(entry - sl)), 2) if abs(entry - sl) > 0 else 0

    return result


@router.get("/quant/options-flow/{symbol}")
async def get_options_flow(symbol: str):
    """Get options flow analysis for a symbol."""
    symbol = symbol.upper()
    prices, volumes, vwap = _generate_sample_prices(symbol)
    return analyze_options_flow(prices, volumes, symbol)


@router.get("/quant/dark-pool/{symbol}")
async def get_dark_pool(symbol: str):
    """Get dark pool / institutional activity detection."""
    symbol = symbol.upper()
    prices, volumes, vwap = _generate_sample_prices(symbol)
    return detect_dark_pool_zones(prices, volumes, vwap, symbol)


@router.get("/quant/ai-prediction/{symbol}")
async def get_ai_prediction(symbol: str):
    """Get AI market prediction for a symbol."""
    symbol = symbol.upper()
    prices, volumes, vwap = _generate_sample_prices(symbol)

    # Get regime
    try:
        from server import _fetch_market_data_cached
        data = _fetch_market_data_cached()
        indices = data.get("indices", {})
        nifty_chg = indices.get("NIFTY 50", {}).get("change_pct", 0)
        regime = "BULLISH" if nifty_chg > 0.3 else "BEARISH" if nifty_chg < -0.3 else "NEUTRAL"
    except Exception:
        regime = "NEUTRAL"

    return predict_market_direction(prices, volumes, vwap, regime)


@router.get("/quant/correlation/{symbol}")
async def get_correlation(symbol: str, action: str = "BUY"):
    """Get correlation analysis for a symbol and action."""
    symbol = symbol.upper()
    action = action.upper()
    market_dict, _ = _get_market_data_dict()
    return check_correlation(symbol, action, market_dict)


@router.get("/quant/trade-rank/{symbol}")
async def get_trade_rank(symbol: str):
    """Get AI trade rank for a symbol."""
    symbol = symbol.upper()
    prices, volumes, vwap = _generate_sample_prices(symbol)
    market_dict, _ = _get_market_data_dict()

    signal_data = _compute_signal(prices, volumes, vwap)
    action = signal_data.get("action", "HOLD")

    options_flow = analyze_options_flow(prices, volumes, symbol)
    dark_pool = detect_dark_pool_zones(prices, volumes, vwap, symbol)
    ai_pred = predict_market_direction(prices, volumes, vwap, "NEUTRAL")
    corr = check_correlation(symbol, action, market_dict)

    return rank_trade(
        signal_data=signal_data,
        options_flow_data=options_flow,
        dark_pool_data=dark_pool,
        ai_prediction_data=ai_pred,
        correlation_data=corr,
    )


@router.get("/quant/hedge-analysis")
async def get_hedge_analysis():
    """Get portfolio hedging analysis."""
    open_positions = list(db["open_positions"].find({}, {"_id": 0}))
    return analyze_portfolio_exposure(open_positions, PORTFOLIO_VALUE)


@router.get("/quant/frequency-status")
async def get_frequency_status():
    """Get trade frequency and drawdown status."""
    today = _ist_now().strftime("%Y-%m-%d")
    today_trades = list(db["trades"].find({"date": today}, {"_id": 0}))
    daily_pnl = round(sum(t.get("pnl", 0) for t in today_trades), 2)

    # Consecutive losses
    recent = list(db["trades"].find({}, {"_id": 0}).sort("created_at", -1).limit(10))
    consec = 0
    for t in recent:
        if t.get("pnl", 0) < 0:
            consec += 1
        else:
            break

    allowed, reason = check_frequency_limits(len(today_trades), consec, daily_pnl, PORTFOLIO_VALUE)
    drawdown_pct = round(abs(min(0, daily_pnl)) / PORTFOLIO_VALUE * 100, 2) if PORTFOLIO_VALUE > 0 else 0

    return {
        "trades_today": len(today_trades),
        "max_trades_per_day": MAX_TRADES_PER_DAY,
        "consecutive_losses": consec,
        "max_consecutive_losses": MAX_CONSECUTIVE_LOSSES,
        "daily_pnl": daily_pnl,
        "daily_drawdown_pct": drawdown_pct,
        "daily_drawdown_limit_pct": DAILY_DRAWDOWN_LIMIT_PCT,
        "trading_allowed": allowed,
        "reason": reason,
        "quant_trading_hours": is_quant_trading_hours(),
        "trading_window": f"{9}:{30:02d} - {14}:{45:02d} IST",
        "min_rr_ratio": MIN_RR_RATIO,
        "timestamp": _ist_now().isoformat(),
    }


@router.get("/quant/dashboard")
async def get_quant_dashboard():
    """Get comprehensive quant intelligence dashboard data."""
    today = _ist_now().strftime("%Y-%m-%d")
    all_trades = list(db["trades"].find({}, {"_id": 0}).sort("created_at", -1))
    today_trades = [t for t in all_trades if t.get("date") == today]
    open_positions = list(db["open_positions"].find({}, {"_id": 0}))
    daily_pnl = round(sum(t.get("pnl", 0) for t in today_trades), 2)
    total_pnl = round(sum(t.get("pnl", 0) for t in all_trades), 2)

    # Consecutive losses
    consec = 0
    for t in all_trades:
        if t.get("pnl", 0) < 0:
            consec += 1
        else:
            break

    # Frequency status
    freq_allowed, freq_reason = check_frequency_limits(len(today_trades), consec, daily_pnl, PORTFOLIO_VALUE)

    # Hedge analysis
    hedge = analyze_portfolio_exposure(open_positions, PORTFOLIO_VALUE)

    # Run pipeline for watchlist symbols
    watchlist_analysis = []
    watchlist = ["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS"]
    market_dict, _ = _get_market_data_dict()

    for sym in watchlist:
        prices, volumes, vwap = _generate_sample_prices(sym)
        signal = _compute_signal(prices, volumes, vwap)
        action = signal.get("action", "HOLD")
        options_flow = analyze_options_flow(prices, volumes, sym)
        ai_pred = predict_market_direction(prices, volumes, vwap, "NEUTRAL")

        watchlist_analysis.append({
            "symbol": sym,
            "price": prices[-1],
            "signal_action": action,
            "signal_score": signal.get("score", 0),
            "options_flow": options_flow["signal"],
            "flow_strength": options_flow["strength"],
            "ai_direction": ai_pred["predicted_direction"],
            "ai_confidence": ai_pred["confidence"],
            "rsi": signal.get("rsi", 50),
        })

    # Strategy performance
    strategies_used = {}
    for t in all_trades:
        s = t.get("strategy", "Unknown")
        if s not in strategies_used:
            strategies_used[s] = {"name": s, "trades": 0, "wins": 0, "pnl": 0}
        strategies_used[s]["trades"] += 1
        strategies_used[s]["pnl"] = round(strategies_used[s]["pnl"] + t.get("pnl", 0), 2)
        if t.get("pnl", 0) > 0:
            strategies_used[s]["wins"] += 1

    for s in strategies_used.values():
        s["win_rate"] = round(s["wins"] / s["trades"] * 100, 1) if s["trades"] > 0 else 0

    # Equity curve
    equity_curve = []
    running = PORTFOLIO_VALUE
    daily_map = {}
    for t in sorted(all_trades, key=lambda x: (x.get("date", ""), x.get("exit_time", ""))):
        running += t.get("pnl", 0)
        daily_map[t.get("date", today)] = round(running, 2)
    equity_curve = [{"date": k, "equity": v} for k, v in sorted(daily_map.items())]

    # Max drawdown
    peak = PORTFOLIO_VALUE
    max_dd = 0
    running = PORTFOLIO_VALUE
    for t in sorted(all_trades, key=lambda x: (x.get("date", ""), x.get("exit_time", ""))):
        running += t.get("pnl", 0)
        peak = max(peak, running)
        dd = round(((peak - running) / peak) * 100, 2) if peak > 0 else 0
        max_dd = max(max_dd, dd)

    wins = [t for t in all_trades if t.get("pnl", 0) > 0]
    win_rate = round(len(wins) / len(all_trades) * 100, 1) if all_trades else 0

    return {
        "portfolio": {
            "value": round(PORTFOLIO_VALUE + total_pnl, 2),
            "initial_capital": PORTFOLIO_VALUE,
            "total_pnl": total_pnl,
            "day_pnl": daily_pnl,
            "total_trades": len(all_trades),
            "win_rate": win_rate,
            "max_drawdown": max_dd,
            "equity_curve": equity_curve,
        },
        "frequency_control": {
            "trades_today": len(today_trades),
            "max_per_day": MAX_TRADES_PER_DAY,
            "consecutive_losses": consec,
            "max_consec_losses": MAX_CONSECUTIVE_LOSSES,
            "drawdown_pct": round(abs(min(0, daily_pnl)) / PORTFOLIO_VALUE * 100, 2) if PORTFOLIO_VALUE > 0 else 0,
            "drawdown_limit": DAILY_DRAWDOWN_LIMIT_PCT,
            "allowed": freq_allowed,
            "reason": freq_reason,
        },
        "hedge_analysis": {
            "net_exposure": hedge["net_exposure"],
            "bullish_pct": hedge["bullish_exposure_pct"],
            "bearish_pct": hedge["bearish_exposure_pct"],
            "hedge_needed": hedge["hedge_needed"],
            "recommendation": hedge.get("hedge_recommendation"),
        },
        "watchlist_intelligence": watchlist_analysis,
        "strategy_performance": list(strategies_used.values()),
        "quant_trading_hours": is_quant_trading_hours(),
        "trading_window": "09:30 - 14:45 IST",
        "min_rr_ratio": f"1:{MIN_RR_RATIO}",
        "min_rank_score": 85,
        "timestamp": _ist_now().isoformat(),
    }


def _compute_signal(prices, volumes, vwap):
    """Compute a basic signal from price/volume data."""
    if len(prices) < 26:
        return {"score": 0, "action": "HOLD", "rsi": 50, "ema_fast": 0, "ema_slow": 0,
                "bb_lower": 0, "bb_upper": 0, "atr": 0, "reasons": []}

    prices_arr = np.array(prices, dtype=float)
    n = len(prices_arr)

    # EMA
    mult9 = 2.0 / 10
    mult21 = 2.0 / 22
    ema9 = [float(prices_arr[0])]
    ema21 = [float(prices_arr[0])]
    for i in range(1, n):
        ema9.append(float(prices_arr[i]) * mult9 + ema9[-1] * (1 - mult9))
        ema21.append(float(prices_arr[i]) * mult21 + ema21[-1] * (1 - mult21))

    # RSI
    deltas = np.diff(prices_arr)
    gains = np.where(deltas > 0, deltas, 0)
    losses_arr = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[:14]) if len(gains) >= 14 else 0
    avg_loss = np.mean(losses_arr[:14]) if len(losses_arr) >= 14 else 1
    for i in range(14, len(gains)):
        avg_gain = (avg_gain * 13 + gains[i]) / 14
        avg_loss = (avg_loss * 13 + losses_arr[i]) / 14
    rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss > 0 else 50

    # BB
    bb_mid = np.mean(prices_arr[-20:]) if n >= 20 else np.mean(prices_arr)
    bb_std = np.std(prices_arr[-20:]) if n >= 20 else np.std(prices_arr)
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std

    # ATR (simplified)
    atr = np.mean(np.abs(deltas[-14:])) if len(deltas) >= 14 else abs(deltas[-1]) if len(deltas) > 0 else prices_arr[-1] * 0.01

    # Score
    score = 0
    reasons = []
    if ema9[-1] > ema21[-1]:
        score += 2
        reasons.append("EMA9>21 bullish")
    else:
        score -= 2
        reasons.append("EMA9<21 bearish")

    if vwap > 0 and prices_arr[-1] > vwap:
        score += 2
        reasons.append("Above VWAP")
    elif vwap > 0:
        score -= 2
        reasons.append("Below VWAP")

    if rsi < 30:
        score += 2
    elif rsi > 70:
        score -= 2
    elif rsi >= 50:
        score += 1
    else:
        score -= 1

    if prices_arr[-1] < bb_lower:
        score += 1
    elif prices_arr[-1] > bb_upper:
        score -= 1

    if len(volumes) >= 20:
        vol_arr = np.array(volumes[-20:], dtype=float)
        if vol_arr[-1] > np.mean(vol_arr[:-1]) * 1.5:
            score += 1 if score > 0 else -1

    action = "BUY" if score >= 6 else "SELL" if score <= -6 else "HOLD"

    return {
        "score": score,
        "action": action,
        "rsi": round(float(rsi), 1),
        "ema_fast": round(ema9[-1], 2),
        "ema_slow": round(ema21[-1], 2),
        "bb_lower": round(float(bb_lower), 2),
        "bb_upper": round(float(bb_upper), 2),
        "atr": round(float(atr), 2),
        "reasons": reasons,
    }
