"""
hedging_engine.py - Portfolio Hedging Engine
=============================================
Reduces portfolio risk by detecting overexposure
and recommending protective hedges.

Rules:
- If exposure > 60% bullish -> recommend protective PUT
- Hedge instrument: NIFTY PUT
"""
from datetime import datetime, timezone, timedelta


def get_ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


HEDGE_THRESHOLD_PCT = 60  # Trigger hedge when bullish exposure > 60%
HEDGE_INSTRUMENT = "NIFTY"
HEDGE_OPTION_TYPE = "PE"  # Protective PUT


def analyze_portfolio_exposure(open_positions, portfolio_value=50000):
    """
    Analyze portfolio directional exposure and recommend hedges.

    Args:
        open_positions: list of open position dicts
        portfolio_value: total portfolio value

    Returns:
        dict with exposure analysis and hedge recommendations
    """
    if not open_positions:
        return {
            "bullish_exposure_pct": 0,
            "bearish_exposure_pct": 0,
            "net_exposure": "FLAT",
            "hedge_needed": False,
            "hedge_recommendation": None,
            "positions_analysis": [],
            "timestamp": get_ist_now().isoformat(),
        }

    bullish_capital = 0
    bearish_capital = 0
    total_capital = 0
    positions_analysis = []

    for pos in open_positions:
        entry = pos.get("entry_price", pos.get("entry", 0))
        qty = pos.get("quantity", pos.get("qty", 0))
        action = pos.get("action", "BUY")
        symbol = pos.get("symbol", "UNKNOWN")
        capital_used = entry * qty

        total_capital += capital_used

        unreal_pnl = pos.get("unrealised_pnl", pos.get("unrealized_pnl", 0))

        if action == "BUY":
            bullish_capital += capital_used
        else:
            bearish_capital += capital_used

        positions_analysis.append({
            "symbol": symbol,
            "action": action,
            "capital": round(capital_used, 2),
            "unrealised_pnl": round(unreal_pnl, 2),
            "direction": "LONG" if action == "BUY" else "SHORT",
        })

    # Calculate exposure percentages
    if total_capital <= 0:
        total_capital = 1

    bullish_pct = round(bullish_capital / total_capital * 100, 1) if total_capital > 0 else 0
    bearish_pct = round(bearish_capital / total_capital * 100, 1) if total_capital > 0 else 0

    # Determine net exposure
    if bullish_pct > 70:
        net_exposure = "HEAVY LONG"
    elif bullish_pct > HEDGE_THRESHOLD_PCT:
        net_exposure = "LONG BIASED"
    elif bearish_pct > 70:
        net_exposure = "HEAVY SHORT"
    elif bearish_pct > HEDGE_THRESHOLD_PCT:
        net_exposure = "SHORT BIASED"
    else:
        net_exposure = "BALANCED"

    # Determine if hedge is needed
    hedge_needed = bullish_pct > HEDGE_THRESHOLD_PCT or bearish_pct > HEDGE_THRESHOLD_PCT
    hedge_recommendation = None

    if bullish_pct > HEDGE_THRESHOLD_PCT:
        # Too much long exposure — buy protective PUTs
        hedge_size = round((bullish_pct - 50) / 100 * portfolio_value * 0.02, 2)  # 2% of overexposure
        hedge_recommendation = {
            "action": "BUY",
            "instrument": f"{HEDGE_INSTRUMENT} {HEDGE_OPTION_TYPE}",
            "reason": f"Bullish exposure {bullish_pct:.0f}% exceeds {HEDGE_THRESHOLD_PCT}% threshold",
            "estimated_cost": hedge_size,
            "hedge_type": "PROTECTIVE_PUT",
            "urgency": "HIGH" if bullish_pct > 80 else "MEDIUM",
        }
    elif bearish_pct > HEDGE_THRESHOLD_PCT:
        # Too much short exposure — buy protective CALLs
        hedge_size = round((bearish_pct - 50) / 100 * portfolio_value * 0.02, 2)
        hedge_recommendation = {
            "action": "BUY",
            "instrument": f"{HEDGE_INSTRUMENT} CE",
            "reason": f"Bearish exposure {bearish_pct:.0f}% exceeds {HEDGE_THRESHOLD_PCT}% threshold",
            "estimated_cost": hedge_size,
            "hedge_type": "PROTECTIVE_CALL",
            "urgency": "HIGH" if bearish_pct > 80 else "MEDIUM",
        }

    return {
        "bullish_exposure_pct": bullish_pct,
        "bearish_exposure_pct": bearish_pct,
        "bullish_capital": round(bullish_capital, 2),
        "bearish_capital": round(bearish_capital, 2),
        "total_deployed": round(total_capital, 2),
        "net_exposure": net_exposure,
        "hedge_needed": hedge_needed,
        "hedge_recommendation": hedge_recommendation,
        "positions_count": len(open_positions),
        "positions_analysis": positions_analysis,
        "portfolio_value": portfolio_value,
        "utilization_pct": round(total_capital / portfolio_value * 100, 1) if portfolio_value > 0 else 0,
        "timestamp": get_ist_now().isoformat(),
    }
