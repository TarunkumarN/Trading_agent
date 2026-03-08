"""
risk/position_sizer.py
Calculates safe position size based on 2% portfolio risk per trade.
"""
from config import PORTFOLIO_VALUE, MAX_RISK_PCT, MAX_LEVERAGE, RISK_REWARD_RATIO


def calculate_quantity(entry_price: float, stop_price: float) -> dict:
    """
    Calculate how many shares to buy/sell based on risk.

    Formula: Quantity = Max Risk Amount / Risk Per Share
    Max Risk Amount = 2% of portfolio = Rs 200

    Returns dict with qty, risk_amount, capital_needed, target_profit
    """
    max_risk     = PORTFOLIO_VALUE * (MAX_RISK_PCT / 100)  # Rs 200
    risk_per_share = abs(entry_price - stop_price)

    if risk_per_share <= 0:
        return {"qty": 0, "risk_amount": 0, "capital_needed": 0, "target_profit": 0}

    qty = int(max_risk / risk_per_share)

    if qty <= 0:
        return {"qty": 0, "risk_amount": 0, "capital_needed": 0, "target_profit": 0}

    # Cap position size to max leverage
    max_capital  = PORTFOLIO_VALUE * MAX_LEVERAGE
    capital_needed = qty * entry_price
    if capital_needed > max_capital:
        qty = int(max_capital / entry_price)

    actual_risk    = round(qty * risk_per_share, 2)
    capital_needed = round(qty * entry_price, 2)
    target_profit  = round(actual_risk * RISK_REWARD_RATIO, 2)

    return {
        "qty":            qty,
        "risk_amount":    actual_risk,
        "capital_needed": capital_needed,
        "target_profit":  target_profit
    }


def calculate_stop_and_target(entry: float, action: str, atr: float = None):
    """
    Calculate stop loss and target prices.
    Uses ATR if available, otherwise defaults to 1% of price.
    """
    offset = atr if atr and atr > 0 else entry * 0.01

    if action == "BUY":
        stop   = round(entry - offset, 2)
        target = round(entry + offset * RISK_REWARD_RATIO, 2)
    else:
        stop   = round(entry + offset, 2)
        target = round(entry - offset * RISK_REWARD_RATIO, 2)

    return stop, target
