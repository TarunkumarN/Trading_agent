from market.volume_profile import build_volume_profile


def evaluate(context: dict):
    profile = build_volume_profile(context["prices"][-50:], context["volumes"][-50:])
    current_price = context["current_price"]
    vol_ratio = context["vol_ratio"]

    if current_price > profile.poc and profile.imbalance > 12 and vol_ratio >= 1.2:
        return {
            "strategy": "auction_long",
            "action": "BUY",
            "entry": current_price,
            "stop_loss": max(profile.value_area_low, current_price - context["atr"] * 1.2),
            "target": current_price + context["atr"] * 2.4,
            "reason": f"Price above POC {profile.poc} with imbalance {profile.imbalance}%",
            "volume_profile": profile.to_dict(),
            "strategy_confidence": 78,
            "instrument_type": "EQUITY",
        }

    if current_price < profile.poc and profile.imbalance < -12 and vol_ratio >= 1.2:
        return {
            "strategy": "auction_short",
            "action": "SELL",
            "entry": current_price,
            "stop_loss": min(profile.value_area_high, current_price + context["atr"] * 1.2),
            "target": current_price - context["atr"] * 2.4,
            "reason": f"Price below POC {profile.poc} with imbalance {profile.imbalance}%",
            "volume_profile": profile.to_dict(),
            "strategy_confidence": 78,
            "instrument_type": "EQUITY",
        }
    return None
