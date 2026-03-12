"""
strategies/signal_scorer.py - Professional trend-following signal engine
- Two-way trading with explicit long/short trend filters
- Market regime enforcement using Nifty bias
- Opening range breakout support
- ATR, ADX, EMA200, VWAP and volume-based quality checks
"""
import pandas as pd
import ta
from config import EMA_FAST, EMA_SLOW, RSI_PERIOD, BB_PERIOD, BB_STD

_opening_range = {}
_nifty_bias = 0.0


def set_nifty_bias(pct_change: float):
    global _nifty_bias
    _nifty_bias = pct_change


def update_opening_range(symbol: str, candle_high: float, candle_low: float, candle_time_minute: int):
    if symbol not in _opening_range:
        _opening_range[symbol] = {"high": candle_high, "low": candle_low, "set": False, "minutes": 0}
    rng = _opening_range[symbol]
    if not rng["set"]:
        rng["high"] = max(rng["high"], candle_high)
        rng["low"] = min(rng["low"], candle_low)
        rng["minutes"] += 1
        if rng["minutes"] >= 15:
            rng["set"] = True


def reset_opening_ranges():
    global _opening_range
    _opening_range = {}


def _hold_response(reason: str, latest=None, atr: float = 0.0, vwap: float = 0.0, orb=None):
    if latest is None or (hasattr(latest, "empty") and latest.empty): latest = {}
    elif hasattr(latest, "to_dict"): latest = latest.to_dict()
    if orb is None: orb = {}
    return {
        "score": 0,
        "action": "HOLD",
        "reasons": [reason],
        "regime": "BIDIRECTIONAL",
        "rsi": round(float(latest.get("rsi", 50) or 50), 1),
        "ema_fast": round(float(latest.get("ema_fast", 0) or 0), 2),
        "ema_slow": round(float(latest.get("ema_slow", 0) or 0), 2),
        "ema_200": round(float(latest.get("ema_200", 0) or 0), 2),
        "adx": round(float(latest.get("adx", 0) or 0), 2),
        "bb_lower": round(float(latest.get("bb_lower", 0) or 0), 2),
        "bb_upper": round(float(latest.get("bb_upper", 0) or 0), 2),
        "atr": round(float(atr or 0), 2),
        "sl_long": 0,
        "sl_short": 0,
        "vwap": round(vwap, 2) if vwap else 0,
        "orb_high": orb.get("high", 0),
        "orb_low": orb.get("low", 0),
        "orb_set": orb.get("set", False),
        "setup_quality": "FILTERED",
        "direction_ok": False,
    }


def calculate_signals(prices: list, volumes: list, vwap: float,
                      highs: list = None, lows: list = None,
                      symbol: str = "") -> dict:
    if len(prices) < 30:
        return _hold_response(f"Need 30 candles, have {len(prices)}")

    highs = highs if highs else prices
    lows = lows if lows else prices

    df = pd.DataFrame({
        "close": prices,
        "volume": volumes,
        "high": highs,
        "low": lows,
    })

    df["ema_fast"] = ta.trend.ema_indicator(df["close"], window=EMA_FAST)
    df["ema_slow"] = ta.trend.ema_indicator(df["close"], window=EMA_SLOW)
    df["ema_200"] = ta.trend.ema_indicator(df["close"], window=min(200, len(prices)))
    df["rsi"] = ta.momentum.rsi(df["close"], window=RSI_PERIOD)
    bb = ta.volatility.BollingerBands(df["close"], window=BB_PERIOD, window_dev=BB_STD)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["atr"] = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
    df["adx"] = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14).adx()

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    current_price = float(latest["close"])
    prev_price = float(prev["close"])
    atr = float(latest["atr"]) if not pd.isna(latest["atr"]) else 0.0
    adx = float(latest["adx"]) if not pd.isna(latest["adx"]) else 0.0
    rsi = float(latest["rsi"]) if not pd.isna(latest["rsi"]) else 50.0
    ema_200 = float(latest["ema_200"]) if not pd.isna(latest["ema_200"]) else current_price
    ema_200_prev = float(df.iloc[-3]["ema_200"]) if len(df) >= 3 and not pd.isna(df.iloc[-3]["ema_200"]) else ema_200
    avg_vol = pd.Series(volumes).tail(20).mean()
    current_vol = volumes[-1]
    vol_ratio = (current_vol / avg_vol) if avg_vol else 0.0
    atr_pct = (atr / current_price * 100) if current_price else 0.0
    recent_high = max(prices[-5:-1])
    recent_low = min(prices[-5:-1])

    bull_trend = current_price > ema_200 and latest["ema_fast"] > latest["ema_slow"] and ema_200 >= ema_200_prev
    bear_trend = current_price < ema_200 and latest["ema_fast"] < latest["ema_slow"] and ema_200 <= ema_200_prev

    if _nifty_bias >= 0.15:
        regime = "LONG_ONLY"
    elif _nifty_bias <= -0.15:
        regime = "SHORT_ONLY"
    else:
        regime = "BIDIRECTIONAL"

    orb = _opening_range.get(symbol, {})
    score = 0
    reasons = [f"Nifty bias {_nifty_bias:+.2f}% -> {regime}"]

    if bull_trend:
        score += 3
        reasons.append("Trend aligned bullish +3")
    elif bear_trend:
        score -= 3
        reasons.append("Trend aligned bearish -3")
    else:
        reasons.append("Trend structure mixed")

    if vwap and vwap > 0:
        if current_price > vwap and latest["ema_fast"] > latest["ema_slow"]:
            score += 2
            reasons.append("Price above VWAP with bullish structure +2")
        elif current_price < vwap and latest["ema_fast"] < latest["ema_slow"]:
            score -= 2
            reasons.append("Price below VWAP with bearish structure -2")
        else:
            reasons.append("VWAP not aligned")

    if current_price > recent_high and bull_trend:
        score += 2
        reasons.append("Breakout above recent range +2")
    elif current_price < recent_low and bear_trend:
        score -= 2
        reasons.append("Breakdown below recent range -2")

    if vol_ratio >= 1.2:
        if bull_trend:
            score += 1
            reasons.append(f"Volume confirmation {vol_ratio:.2f}x +1")
        elif bear_trend:
            score -= 1
            reasons.append(f"Volume confirmation {vol_ratio:.2f}x -1")
    else:
        reasons.append(f"Volume muted {vol_ratio:.2f}x")

    if bull_trend and 55 <= rsi <= 68:
        score += 1
        reasons.append(f"RSI trend support {rsi:.1f} +1")
    elif bear_trend and 32 <= rsi <= 45:
        score -= 1
        reasons.append(f"RSI bearish pressure {rsi:.1f} -1")
    elif bull_trend and rsi < 45:
        score -= 1
        reasons.append(f"Bull trend losing momentum {rsi:.1f} -1")
    elif bear_trend and rsi > 55:
        score += 1
        reasons.append(f"Bear trend squeeze risk {rsi:.1f} +1")

    if adx >= 20:
        if bull_trend:
            score += 1
            reasons.append(f"ADX trend strength {adx:.1f} +1")
        elif bear_trend:
            score -= 1
            reasons.append(f"ADX trend strength {adx:.1f} -1")
    else:
        reasons.append(f"ADX weak {adx:.1f}")

    if orb.get("set"):
        if current_price > orb["high"] and bull_trend:
            score += 1
            reasons.append("ORB bullish confirmation +1")
        elif current_price < orb["low"] and bear_trend:
            score -= 1
            reasons.append("ORB bearish confirmation -1")

    if atr_pct < 0.10:
        return _hold_response(f"ATR too low for scalping ({atr_pct:.2f}%)", latest, atr, vwap, orb)
    if adx < 10:
        return _hold_response(f"Trend too weak (ADX {adx:.1f})", latest, atr, vwap, orb)
    if vol_ratio < 0.5:
        return _hold_response(f"Volume too weak ({vol_ratio:.2f}x)", latest, atr, vwap, orb)

    allow_long = bull_trend and current_price > vwap and latest["ema_fast"] > latest["ema_slow"]
    allow_short = bear_trend and current_price < vwap and latest["ema_fast"] < latest["ema_slow"]

    if regime == "LONG_ONLY":
        allow_short = False
        if score < 0:
            score = 0
    elif regime == "SHORT_ONLY":
        allow_long = False
        if score > 0:
            score = 0

    action = "HOLD"
    setup_quality = "FILTERED"
    direction_ok = False
    if score >= 7 and allow_long:
        action = "BUY"
        setup_quality = "A"
        direction_ok = True
    elif score <= -6 and allow_short:
        action = "SELL"
        setup_quality = "A"
        direction_ok = True
    elif abs(score) >= 6 and (allow_long or allow_short):
        setup_quality = "B"

    if action == "HOLD" and abs(score) >= 6:
        reasons.append("High score blocked by direction filter")

    return {
        "score": int(score),
        "action": action,
        "reasons": reasons,
        "regime": regime,
        "rsi": round(rsi, 1),
        "ema_fast": round(float(latest["ema_fast"]), 2),
        "ema_slow": round(float(latest["ema_slow"]), 2),
        "ema_200": round(ema_200, 2),
        "adx": round(adx, 2),
        "bb_lower": round(float(latest["bb_lower"]), 2),
        "bb_upper": round(float(latest["bb_upper"]), 2),
        "atr": round(atr, 2),
        "sl_long": round(current_price - (2.5 * atr), 2) if atr else 0,
        "sl_short": round(current_price + (2.5 * atr), 2) if atr else 0,
        "vwap": round(vwap, 2) if vwap else 0,
        "orb_high": orb.get("high", 0),
        "orb_low": orb.get("low", 0),
        "orb_set": orb.get("set", False),
        "setup_quality": setup_quality,
        "direction_ok": direction_ok,
        "vol_ratio": round(vol_ratio, 2),
        "atr_pct": round(atr_pct, 2),
    }
