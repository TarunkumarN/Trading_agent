"""
strategies/signal_scorer.py
Combines EMA crossover, VWAP, RSI, and Bollinger Bands
into a single signal score from -10 to +10.

Score >= 6  → BUY
Score <= -6 → SELL
Score -5 to +5 → HOLD
"""
import pandas as pd
import ta
from config import EMA_FAST, EMA_SLOW, RSI_PERIOD, BB_PERIOD, BB_STD


def calculate_signals(prices: list, volumes: list, vwap: float) -> dict:
    """
    Main signal function. Call this on every new candle.

    Args:
        prices:  list of closing prices (minimum 26 candles needed)
        volumes: list of volumes (same length as prices)
        vwap:    current day VWAP value (float)

    Returns:
        dict with score, action, reasons, and all indicator values
    """
    if len(prices) < 26:
        return {
            "score":  0,
            "action": "HOLD",
            "reasons": ["Not enough candles yet — need at least 26"],
            "rsi": 50, "ema_fast": 0, "ema_slow": 0,
            "bb_lower": 0, "bb_upper": 0
        }

    df = pd.DataFrame({"close": prices, "volume": volumes})

    # ── Indicators ──────────────────────────────────────────
    df["ema_fast"] = ta.trend.ema_indicator(df["close"], window=EMA_FAST)
    df["ema_slow"] = ta.trend.ema_indicator(df["close"], window=EMA_SLOW)
    df["rsi"]      = ta.momentum.rsi(df["close"], window=RSI_PERIOD)

    bb = ta.volatility.BollingerBands(df["close"], window=BB_PERIOD, window_dev=BB_STD)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()

    latest        = df.iloc[-1]
    prev          = df.iloc[-2]
    current_price = prices[-1]
    avg_vol       = pd.Series(volumes).tail(20).mean()
    current_vol   = volumes[-1]

    score   = 0
    reasons = []

    # ── 1. EMA Crossover (+2 to +3) ─────────────────────────
    if latest["ema_fast"] > latest["ema_slow"]:
        score += 2
        reasons.append(f"EMA{EMA_FAST} > EMA{EMA_SLOW} (bullish) +2")
        # Fresh crossover bonus
        if prev["ema_fast"] <= prev["ema_slow"]:
            score += 1
            reasons.append("Fresh EMA crossover (just happened) +1")
    else:
        score -= 2
        reasons.append(f"EMA{EMA_FAST} < EMA{EMA_SLOW} (bearish) -2")
        if prev["ema_fast"] >= prev["ema_slow"]:
            score -= 1
            reasons.append("Fresh bearish EMA crossover -1")

    # ── 2. VWAP (+2) ─────────────────────────────────────────
    if vwap and vwap > 0:
        if current_price > vwap:
            score += 2
            reasons.append(f"Price ₹{current_price:.2f} above VWAP ₹{vwap:.2f} +2")
        else:
            score -= 2
            reasons.append(f"Price ₹{current_price:.2f} below VWAP ₹{vwap:.2f} -2")

        # VWAP retest bounce (high probability setup)
        prev_price = prices[-2] if len(prices) >= 2 else current_price
        if abs(prev_price - vwap) / vwap < 0.002:   # within 0.2% of VWAP
            if current_price > vwap and current_price > prev_price:
                score += 1
                reasons.append("VWAP retest bounce detected +1")

    # ── 3. Volume Confirmation (+1) ──────────────────────────
    if avg_vol > 0 and current_vol > avg_vol * 1.5:
        score += 1
        reasons.append(f"Volume spike {current_vol/avg_vol:.1f}x average +1")

    # ── 4. RSI (+2 to -2) ────────────────────────────────────
    rsi = latest["rsi"]
    if rsi < 30:
        score += 2
        reasons.append(f"RSI oversold ({rsi:.1f}) +2")
    elif rsi > 70:
        score -= 2
        reasons.append(f"RSI overbought ({rsi:.1f}) -2")
    elif 50 <= rsi <= 70:
        score += 1
        reasons.append(f"RSI bullish zone ({rsi:.1f}) +1")
    elif 30 <= rsi < 50:
        score -= 1
        reasons.append(f"RSI bearish zone ({rsi:.1f}) -1")

    # ── 5. Bollinger Bands (+1 to -1) ────────────────────────
    if current_price < latest["bb_lower"]:
        score += 1
        reasons.append("Price below lower Bollinger Band (oversold) +1")
    elif current_price > latest["bb_upper"]:
        score -= 1
        reasons.append("Price above upper Bollinger Band (overbought) -1")

    # ── Final Decision ────────────────────────────────────────
    if score >= 6:
        action = "BUY"
    elif score <= -6:
        action = "SELL"
    else:
        action = "HOLD"

    return {
        "score":    score,
        "action":   action,
        "reasons":  reasons,
        "rsi":      round(float(rsi), 1),
        "ema_fast": round(float(latest["ema_fast"]), 2),
        "ema_slow": round(float(latest["ema_slow"]), 2),
        "bb_lower": round(float(latest["bb_lower"]), 2),
        "bb_upper": round(float(latest["bb_upper"]), 2),
        "vwap":     round(vwap, 2) if vwap else 0
    }
