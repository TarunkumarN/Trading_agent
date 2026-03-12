
def score_trade(trend_strength: float, volume_ratio: float, ai_confidence: int, risk_reward_ratio: float, liquidity_score: float):
    trend_component = min(30, trend_strength * 0.3)
    volume_component = max(0, min(20, (volume_ratio - 1.0) * 25))
    ai_component = max(0, min(25, ai_confidence * 0.25))
    rr_component = max(0, min(15, (risk_reward_ratio - 1.0) * 12))
    liquidity_component = max(0, min(10, liquidity_score))
    total = round(trend_component + volume_component + ai_component + rr_component + liquidity_component, 2)
    return {
        "score": total,
        "allowed": total >= 80,
        "components": {
            "trend": round(trend_component, 2),
            "volume": round(volume_component, 2),
            "ai": round(ai_component, 2),
            "risk_reward": round(rr_component, 2),
            "liquidity": round(liquidity_component, 2),
        },
    }
