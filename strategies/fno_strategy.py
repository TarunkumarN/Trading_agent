
def evaluate(context: dict):
    current_price = context["current_price"]
    prev_day_high = max(context["highs"][-31:-1])
    prev_day_low = min(context["lows"][-31:-1])
    vol_ratio = context["vol_ratio"]
    rsi = context["rsi"]

    if current_price > prev_day_high and vol_ratio >= 1.6:
        return {
            "strategy": "fno_breakout_call",
            "action": "BUY",
            "entry": current_price,
            "stop_loss": context["lows"][-2],
            "target": current_price + (current_price - context["lows"][-2]) * 2,
            "reason": f"Prev day high breakout above {prev_day_high:.2f}",
            "strategy_confidence": 84,
            "instrument_type": "FNO",
            "option_side": "CALL",
            "market_view": "BULLISH",
        }

    if current_price < prev_day_low and vol_ratio >= 1.6:
        return {
            "strategy": "fno_breakdown_put",
            "action": "BUY",
            "entry": current_price,
            "stop_loss": context["highs"][-2],
            "target": current_price - (context["highs"][-2] - current_price) * 2,
            "reason": f"Prev day low breakdown below {prev_day_low:.2f}",
            "strategy_confidence": 84,
            "instrument_type": "FNO",
            "option_side": "PUT",
            "market_view": "BEARISH",
        }

    if current_price > context["vwap"] and rsi > 60 and vol_ratio >= 1.4:
        return {
            "strategy": "fno_momentum_call",
            "action": "BUY",
            "entry": current_price,
            "stop_loss": current_price - context["atr"] * 1.2,
            "target": current_price + context["atr"] * 2.4,
            "reason": "Momentum long above VWAP with RSI > 60",
            "strategy_confidence": 79,
            "instrument_type": "FNO",
            "option_side": "CALL",
            "market_view": "BULLISH",
        }

    if current_price < context["vwap"] and rsi < 40 and vol_ratio >= 1.4:
        return {
            "strategy": "fno_momentum_put",
            "action": "BUY",
            "entry": current_price,
            "stop_loss": current_price + context["atr"] * 1.2,
            "target": current_price - context["atr"] * 2.4,
            "reason": "Momentum short below VWAP with RSI < 40",
            "strategy_confidence": 79,
            "instrument_type": "FNO",
            "option_side": "PUT",
            "market_view": "BEARISH",
        }

    return None
