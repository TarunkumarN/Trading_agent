"""
trade_ranker.py - AI Trade Ranking Engine
==========================================
Scores trade candidates on a 0-100 scale using multiple intelligence layers.
Trade allowed only if score >= 85.

Score Components:
- Trend Strength (0-20)
- Liquidity Sweep / Dark Pool (0-15)
- Order Block Strength (0-15)
- Options Flow Alignment (0-15)
- Gamma Level Alignment (0-15)
- AI Prediction Confidence (0-20)
"""
from datetime import datetime, timezone, timedelta


def get_ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


MIN_RANK_SCORE = 85


def rank_trade(
    signal_data,
    options_flow_data=None,
    dark_pool_data=None,
    ai_prediction_data=None,
    correlation_data=None,
    market_regime="NEUTRAL",
):
    """
    Rank a trade candidate on 0-100 scale.

    Args:
        signal_data: dict from strategy signal engine {score, action, rsi, ema_fast, ema_slow, atr, reasons}
        options_flow_data: dict from options_flow.analyze_options_flow()
        dark_pool_data: dict from dark_pool_detector.detect_dark_pool_zones()
        ai_prediction_data: dict from market_predictor.predict_market_direction()
        correlation_data: dict from correlation_filter.check_correlation()
        market_regime: current market regime string

    Returns:
        dict with total_score, components, trade_allowed, reasoning
    """
    components = {}
    reasoning = []
    action = signal_data.get("action", "HOLD")

    # 1. TREND STRENGTH (0-20)
    signal_score = abs(signal_data.get("score", 0))
    rsi = signal_data.get("rsi", 50)
    ema_fast = signal_data.get("ema_fast", 0)
    ema_slow = signal_data.get("ema_slow", 0)

    trend_score = 0
    # Signal score contribution
    trend_score += min(10, signal_score * 1.2)
    # EMA alignment
    if action == "BUY" and ema_fast > ema_slow:
        trend_score += 5
    elif action == "SELL" and ema_fast < ema_slow:
        trend_score += 5
    # RSI in favorable zone
    if (action == "BUY" and 40 <= rsi <= 65) or (action == "SELL" and 35 <= rsi <= 60):
        trend_score += 5
    elif (action == "BUY" and rsi < 30) or (action == "SELL" and rsi > 70):
        trend_score += 3  # Reversal trades

    trend_score = min(20, round(trend_score))
    components["trend_strength"] = trend_score
    reasoning.append(f"Trend: {trend_score}/20 (signal={signal_score}, RSI={rsi:.0f})")

    # 2. LIQUIDITY / DARK POOL (0-15)
    dark_score = 0
    if dark_pool_data:
        zone_type = dark_pool_data.get("zone_type", "none")
        dp_confidence = dark_pool_data.get("confidence", 0)
        institutional = dark_pool_data.get("institutional_activity", False)

        if institutional:
            dark_score += 5
        if zone_type == "accumulation" and action == "BUY":
            dark_score += min(10, dp_confidence * 0.1)
        elif zone_type == "distribution" and action == "SELL":
            dark_score += min(10, dp_confidence * 0.1)
        elif zone_type != "none":
            dark_score += 2  # Some zone detected

    dark_score = min(15, round(dark_score))
    components["dark_pool_alignment"] = dark_score
    reasoning.append(f"Dark Pool: {dark_score}/15")

    # 3. ORDER BLOCK STRENGTH (0-15) — derived from price structure
    ob_score = 0
    atr = signal_data.get("atr", 0)
    if signal_score >= 8:
        ob_score += 8
    elif signal_score >= 6:
        ob_score += 5
    # ATR-based volatility alignment
    if atr > 0:
        ob_score += 4  # Trade has proper ATR for stop calculation
    # Market regime alignment with order blocks
    regime_upper = market_regime.upper()
    if ("BULL" in regime_upper and action == "BUY") or ("BEAR" in regime_upper and action == "SELL"):
        ob_score += 3

    ob_score = min(15, round(ob_score))
    components["order_block_strength"] = ob_score
    reasoning.append(f"Order Block: {ob_score}/15")

    # 4. OPTIONS FLOW ALIGNMENT (0-15)
    flow_score = 0
    if options_flow_data:
        flow_signal = options_flow_data.get("signal", "neutral")
        flow_strength = options_flow_data.get("strength", 0)
        unusual = options_flow_data.get("unusual_activity", False)

        if (flow_signal == "bullish_flow" and action == "BUY") or \
           (flow_signal == "bearish_flow" and action == "SELL"):
            flow_score += min(10, flow_strength * 0.15)
            if unusual:
                flow_score += 5
        elif flow_signal == "neutral":
            flow_score += 3  # No opposing flow

    flow_score = min(15, round(flow_score))
    components["options_flow_alignment"] = flow_score
    reasoning.append(f"Options Flow: {flow_score}/15")

    # 5. GAMMA LEVEL ALIGNMENT (0-15) — simulated from support/resistance
    gamma_score = 0
    # Use Bollinger Band position as gamma proxy
    bb_upper = signal_data.get("bb_upper", 0)
    bb_lower = signal_data.get("bb_lower", 0)
    if bb_upper > 0 and bb_lower > 0:
        # Trade direction aligned with BB boundaries
        if action == "BUY" and rsi < 40:  # Near lower band
            gamma_score += 8
        elif action == "SELL" and rsi > 60:  # Near upper band
            gamma_score += 8
        else:
            gamma_score += 3

    # Correlation boost
    if correlation_data and correlation_data.get("confirmation", False):
        gamma_score += min(7, correlation_data.get("correlation_strength", 0) * 0.07)

    gamma_score = min(15, round(gamma_score))
    components["gamma_level_alignment"] = gamma_score
    reasoning.append(f"Gamma Level: {gamma_score}/15")

    # 6. AI PREDICTION CONFIDENCE (0-20)
    ai_score = 0
    if ai_prediction_data:
        pred_dir = ai_prediction_data.get("predicted_direction", "neutral")
        pred_conf = ai_prediction_data.get("confidence", 0)
        trade_allowed = ai_prediction_data.get("trade_allowed", False)

        if (pred_dir == "bullish" and action == "BUY") or \
           (pred_dir == "bearish" and action == "SELL"):
            ai_score += min(15, pred_conf * 0.15)
            if trade_allowed:
                ai_score += 5
        elif pred_dir == "neutral":
            ai_score += 3
        # Contradicting prediction penalizes
        elif (pred_dir == "bearish" and action == "BUY") or \
             (pred_dir == "bullish" and action == "SELL"):
            ai_score = 0

    ai_score = min(20, round(ai_score))
    components["ai_prediction"] = ai_score
    reasoning.append(f"AI Prediction: {ai_score}/20")

    # TOTAL
    total_score = sum(components.values())
    trade_allowed = total_score >= MIN_RANK_SCORE and action != "HOLD"

    return {
        "total_score": total_score,
        "max_score": 100,
        "components": components,
        "trade_allowed": trade_allowed,
        "min_required": MIN_RANK_SCORE,
        "action": action,
        "reasoning": reasoning,
        "grade": _grade(total_score),
        "timestamp": get_ist_now().isoformat(),
    }


def _grade(score):
    if score >= 90:
        return "A+"
    elif score >= 85:
        return "A"
    elif score >= 75:
        return "B+"
    elif score >= 65:
        return "B"
    elif score >= 50:
        return "C"
    else:
        return "D"
