
def evaluate(context: dict):
    current_price = context["current_price"]
    prev_high = max(context["highs"][-21:-1])
    prev_low = min(context["lows"][-21:-1])
    vol_ratio = context["vol_ratio"]
    regime = context["market_regime"]

    if regime.bullish and current_price > prev_high and vol_ratio >= 1.5 and current_price > context["vwap"]:
        return {
            "strategy": "breakout_long",
            "action": "BUY",
            "entry": current_price,
            "stop_loss": context["lows"][-2],
            "target": current_price + max(context["atr"] * 2.0, current_price - context["lows"][-2]) * 2,
            "reason": f"Breakout above {prev_high:.2f} with volume {vol_ratio:.2f}x",
            "strategy_confidence": 82,
            "instrument_type": "EQUITY",
        }

    if regime.bearish and current_price < prev_low and vol_ratio >= 1.5 and current_price < context["vwap"]:
        return {
            "strategy": "breakout_short",
            "action": "SELL",
            "entry": current_price,
            "stop_loss": context["highs"][-2],
            "target": current_price - max(context["atr"] * 2.0, context["highs"][-2] - current_price) * 2,
            "reason": f"Breakdown below {prev_low:.2f} with volume {vol_ratio:.2f}x",
            "strategy_confidence": 82,
            "instrument_type": "EQUITY",
        }
    return None
