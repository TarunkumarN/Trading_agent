"""
risk/position_sizer.py
Smart position sizing with confidence-aware risk allocation.
"""
from config import MAX_LEVERAGE, MAX_RISK_PCT, PORTFOLIO_VALUE, RISK_REWARD_RATIO


def _risk_pct_for_confidence(ai_confidence: int, trade_score: float = 0.0) -> float:
    if ai_confidence >= 85 and trade_score >= 90:
        return min(MAX_RISK_PCT, 2.0)
    if ai_confidence >= 70 and trade_score >= 80:
        return min(MAX_RISK_PCT, 1.0)
    return 0.0


def calculate_position_plan(entry_price: float, stop_price: float, ai_confidence: int, trade_score: float):
    risk_pct = _risk_pct_for_confidence(ai_confidence, trade_score)
    if risk_pct <= 0:
        return {
            "qty": 0,
            "risk_amount": 0,
            "capital_needed": 0,
            "target_profit": 0,
            "risk_pct": 0,
            "allowed": False,
            "reason": "Low confidence trade",
        }

    max_risk = PORTFOLIO_VALUE * (risk_pct / 100)
    risk_per_share = abs(entry_price - stop_price)
    if risk_per_share <= 0:
        return {
            "qty": 0,
            "risk_amount": 0,
            "capital_needed": 0,
            "target_profit": 0,
            "risk_pct": risk_pct,
            "allowed": False,
            "reason": "Invalid stop distance",
        }

    qty = int(max_risk / risk_per_share)
    max_capital = PORTFOLIO_VALUE * MAX_LEVERAGE
    capital_needed = qty * entry_price
    if capital_needed > max_capital:
        qty = int(max_capital / entry_price)

    actual_risk = round(qty * risk_per_share, 2)
    capital_needed = round(qty * entry_price, 2)
    target_profit = round(actual_risk * RISK_REWARD_RATIO, 2)
    return {
        "qty": max(qty, 0),
        "risk_amount": actual_risk,
        "capital_needed": capital_needed,
        "target_profit": target_profit,
        "risk_pct": risk_pct,
        "allowed": qty > 0,
        "reason": "OK" if qty > 0 else "Quantity too small",
    }


def calculate_quantity(entry_price: float, stop_price: float) -> dict:
    return calculate_position_plan(entry_price, stop_price, ai_confidence=80, trade_score=80)


def calculate_stop_and_target(entry: float, action: str, atr: float = None):
    offset = atr if atr and atr > 0 else entry * 0.01
    if action == "BUY":
        stop = round(entry - offset, 2)
        target = round(entry + offset * RISK_REWARD_RATIO, 2)
    else:
        stop = round(entry + offset, 2)
        target = round(entry - offset * RISK_REWARD_RATIO, 2)
    return stop, target
