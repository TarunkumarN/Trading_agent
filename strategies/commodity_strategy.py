COMMODITY_SYMBOLS = {"GOLD", "SILVER", "CRUDE", "CRUDEOIL"}


def supports(symbol: str) -> bool:
    upper = symbol.upper()
    return any(token in upper for token in COMMODITY_SYMBOLS)


def evaluate(context: dict):
    current_price = context["current_price"]
    recent_high = max(context["highs"][-11:-1])
    recent_low = min(context["lows"][-11:-1])
    vol_ratio = context["vol_ratio"]
    regime = context["market_regime"]

    if regime.bullish and current_price > recent_high and current_price > context["vwap"] and vol_ratio >= 1.3:
        return {
            "strategy": "commodity_breakout_long",
            "action": "BUY",
            "entry": current_price,
            "stop_loss": current_price - context["atr"] * 1.5,
            "target": current_price + context["atr"] * 3.0,
            "reason": "Commodity breakout above consolidation range",
            "strategy_confidence": 80,
            "instrument_type": "COMMODITY",
        }

    if regime.bearish and current_price < recent_low and current_price < context["vwap"] and vol_ratio >= 1.3:
        return {
            "strategy": "commodity_breakdown_short",
            "action": "SELL",
            "entry": current_price,
            "stop_loss": current_price + context["atr"] * 1.5,
            "target": current_price - context["atr"] * 3.0,
            "reason": "Commodity breakdown below consolidation range",
            "strategy_confidence": 80,
            "instrument_type": "COMMODITY",
        }
    return None
