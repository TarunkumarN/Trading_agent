
def evaluate(context: dict):
    current_price = context["current_price"]
    prev_close = context["prices"][-2]
    candle_range = context["highs"][-1] - context["lows"][-1]
    regime = context["market_regime"]

    if regime.bullish and current_price > context["vwap"] and prev_close <= context["vwap"] and candle_range >= context["atr"] * 0.6:
        return {
            "strategy": "vwap_reclaim_long",
            "action": "BUY",
            "entry": current_price,
            "stop_loss": current_price - context["atr"] * 1.1,
            "target": current_price + context["atr"] * 2.2,
            "reason": "Price reclaimed VWAP with bullish candle",
            "strategy_confidence": 76,
            "instrument_type": "EQUITY",
        }

    if regime.bearish and current_price < context["vwap"] and prev_close >= context["vwap"] and candle_range >= context["atr"] * 0.6:
        return {
            "strategy": "vwap_reject_short",
            "action": "SELL",
            "entry": current_price,
            "stop_loss": current_price + context["atr"] * 1.1,
            "target": current_price - context["atr"] * 2.2,
            "reason": "Price rejected VWAP with bearish candle",
            "strategy_confidence": 76,
            "instrument_type": "EQUITY",
        }
    return None
