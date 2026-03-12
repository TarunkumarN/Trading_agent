"""
market_predictor.py - AI Short-Term Market Direction Prediction
================================================================
Predicts short-term market direction using technical indicators,
volume analysis, VWAP, and market regime context.
Trade allowed only if confidence >= 65.
"""
import numpy as np
from datetime import datetime, timezone, timedelta


def get_ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


def predict_market_direction(prices, volumes, vwap=0.0, market_regime="NEUTRAL"):
    """
    Predict short-term market direction.

    Args:
        prices: list of last 100+ close prices
        volumes: list of last 100+ volumes
        vwap: current VWAP
        market_regime: current regime from regime detector

    Returns:
        dict with predicted_direction, confidence, factors
    """
    if len(prices) < 26:
        return {
            "predicted_direction": "neutral",
            "confidence": 0,
            "details": "Insufficient data for prediction",
            "factors": {},
            "trade_allowed": False,
        }

    prices_arr = np.array(prices, dtype=float)
    volumes_arr = np.array(volumes, dtype=float)
    n = len(prices_arr)

    factors = {}
    bullish_score = 0
    bearish_score = 0

    # 1. EMA Trend (EMA9 vs EMA21)
    ema9 = _ema(prices_arr, 9)
    ema21 = _ema(prices_arr, 21)
    if ema9[-1] > ema21[-1]:
        bullish_score += 15
        factors["ema_trend"] = {"direction": "bullish", "weight": 15}
    else:
        bearish_score += 15
        factors["ema_trend"] = {"direction": "bearish", "weight": 15}

    # EMA crossover recency
    if n > 2 and ema9[-2] <= ema21[-2] and ema9[-1] > ema21[-1]:
        bullish_score += 10
        factors["ema_crossover"] = {"direction": "fresh_bullish", "weight": 10}
    elif n > 2 and ema9[-2] >= ema21[-2] and ema9[-1] < ema21[-1]:
        bearish_score += 10
        factors["ema_crossover"] = {"direction": "fresh_bearish", "weight": 10}

    # 2. RSI Analysis
    rsi = _rsi(prices_arr, 14)
    if rsi < 30:
        bullish_score += 12  # Oversold = reversal likely
        factors["rsi"] = {"value": round(rsi, 1), "signal": "oversold_reversal", "weight": 12}
    elif rsi > 70:
        bearish_score += 12  # Overbought
        factors["rsi"] = {"value": round(rsi, 1), "signal": "overbought_reversal", "weight": 12}
    elif 50 <= rsi <= 60:
        bullish_score += 5
        factors["rsi"] = {"value": round(rsi, 1), "signal": "bullish_momentum", "weight": 5}
    elif 40 <= rsi < 50:
        bearish_score += 5
        factors["rsi"] = {"value": round(rsi, 1), "signal": "bearish_momentum", "weight": 5}
    else:
        factors["rsi"] = {"value": round(rsi, 1), "signal": "neutral", "weight": 0}

    # 3. VWAP Position
    if vwap > 0:
        vwap_dev = (prices_arr[-1] - vwap) / vwap * 100
        if vwap_dev > 0.3:
            bullish_score += 10
            factors["vwap"] = {"deviation": round(vwap_dev, 3), "signal": "above_vwap", "weight": 10}
        elif vwap_dev < -0.3:
            bearish_score += 10
            factors["vwap"] = {"deviation": round(vwap_dev, 3), "signal": "below_vwap", "weight": 10}
        else:
            factors["vwap"] = {"deviation": round(vwap_dev, 3), "signal": "at_vwap", "weight": 0}

    # 4. Volume Trend
    if len(volumes_arr) >= 10:
        recent_vol = np.mean(volumes_arr[-5:])
        older_vol = np.mean(volumes_arr[-10:-5])
        if older_vol > 0:
            vol_change = (recent_vol - older_vol) / older_vol
            if vol_change > 0.3 and prices_arr[-1] > prices_arr[-5]:
                bullish_score += 8
                factors["volume_trend"] = {"change": round(vol_change, 3), "signal": "bullish_volume", "weight": 8}
            elif vol_change > 0.3 and prices_arr[-1] < prices_arr[-5]:
                bearish_score += 8
                factors["volume_trend"] = {"change": round(vol_change, 3), "signal": "bearish_volume", "weight": 8}
            else:
                factors["volume_trend"] = {"change": round(vol_change, 3), "signal": "neutral", "weight": 0}

    # 5. Price Momentum (ROC)
    if n >= 10:
        roc_5 = (prices_arr[-1] - prices_arr[-5]) / prices_arr[-5] * 100
        roc_10 = (prices_arr[-1] - prices_arr[-10]) / prices_arr[-10] * 100
        if roc_5 > 0.5 and roc_10 > 0.5:
            bullish_score += 10
            factors["momentum"] = {"roc5": round(roc_5, 3), "roc10": round(roc_10, 3), "signal": "bullish", "weight": 10}
        elif roc_5 < -0.5 and roc_10 < -0.5:
            bearish_score += 10
            factors["momentum"] = {"roc5": round(roc_5, 3), "roc10": round(roc_10, 3), "signal": "bearish", "weight": 10}
        else:
            factors["momentum"] = {"roc5": round(roc_5, 3), "roc10": round(roc_10, 3), "signal": "mixed", "weight": 0}

    # 6. Bollinger Band Position
    if n >= 20:
        bb_mid = np.mean(prices_arr[-20:])
        bb_std = np.std(prices_arr[-20:])
        bb_upper = bb_mid + 2 * bb_std
        bb_lower = bb_mid - 2 * bb_std
        current = prices_arr[-1]
        bb_pct = (current - bb_lower) / (bb_upper - bb_lower) * 100 if (bb_upper - bb_lower) > 0 else 50

        if bb_pct < 20:
            bullish_score += 8  # Near lower band = oversold
            factors["bollinger"] = {"position_pct": round(bb_pct, 1), "signal": "oversold", "weight": 8}
        elif bb_pct > 80:
            bearish_score += 8
            factors["bollinger"] = {"position_pct": round(bb_pct, 1), "signal": "overbought", "weight": 8}
        else:
            factors["bollinger"] = {"position_pct": round(bb_pct, 1), "signal": "neutral", "weight": 0}

    # 7. Market Regime Alignment
    regime_upper = market_regime.upper()
    if "BULL" in regime_upper:
        bullish_score += 10
        factors["regime"] = {"value": market_regime, "signal": "bullish_aligned", "weight": 10}
    elif "BEAR" in regime_upper:
        bearish_score += 10
        factors["regime"] = {"value": market_regime, "signal": "bearish_aligned", "weight": 10}
    else:
        factors["regime"] = {"value": market_regime, "signal": "neutral", "weight": 0}

    # Compute final prediction
    total = bullish_score + bearish_score
    if total == 0:
        return {
            "predicted_direction": "neutral",
            "confidence": 0,
            "details": "No clear directional signal",
            "factors": factors,
            "trade_allowed": False,
        }

    if bullish_score > bearish_score:
        direction = "bullish"
        confidence = round(bullish_score / (total) * 100)
        net_score = bullish_score - bearish_score
    elif bearish_score > bullish_score:
        direction = "bearish"
        confidence = round(bearish_score / (total) * 100)
        net_score = bearish_score - bullish_score
    else:
        direction = "neutral"
        confidence = 50
        net_score = 0

    # Adjust confidence based on net score magnitude
    confidence = min(98, max(20, confidence + net_score))

    return {
        "predicted_direction": direction,
        "confidence": confidence,
        "bullish_score": bullish_score,
        "bearish_score": bearish_score,
        "net_score": net_score,
        "factors": factors,
        "trade_allowed": confidence >= 65,
        "timestamp": get_ist_now().isoformat(),
    }


def _ema(data, period):
    """Calculate EMA."""
    multiplier = 2.0 / (period + 1)
    ema = [float(data[0])]
    for i in range(1, len(data)):
        ema.append(float(data[i]) * multiplier + ema[-1] * (1 - multiplier))
    return np.array(ema)


def _rsi(data, period=14):
    """Calculate RSI."""
    if len(data) < period + 1:
        return 50.0
    deltas = np.diff(data)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)
