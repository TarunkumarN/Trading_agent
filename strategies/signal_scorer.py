"""
strategies/signal_scorer.py — Professional Edition
Changes:
- TWO-WAY: BUY (score>=6) and SELL/SHORT (score<=-6)
- ATR-based dynamic stop loss
- Market Regime filter (Nifty bias)
- Opening Range Breakout (ORB)
- Multi-timeframe alignment check
"""
import pandas as pd
import ta
from config import EMA_FAST, EMA_SLOW, RSI_PERIOD, BB_PERIOD, BB_STD

# ── Opening Range Store (resets daily at 9:15 AM) ────────────────────────────
_opening_range = {}   # {symbol: {"high": x, "low": x, "set": bool}}
_nifty_bias    = 0.0  # Nifty % change today — set externally

def set_nifty_bias(pct_change: float):
    """Call this every minute with Nifty % change for market regime filter."""
    global _nifty_bias
    _nifty_bias = pct_change

def update_opening_range(symbol: str, candle_high: float, candle_low: float,
                          candle_time_minute: int):
    """
    Call during 9:15–9:30 AM (minutes 0–14) to build the opening range.
    After 9:30 AM the range is locked and used for ORB signals.
    """
    if symbol not in _opening_range:
        _opening_range[symbol] = {"high": candle_high, "low": candle_low,
                                   "set": False, "minutes": 0}
    r = _opening_range[symbol]
    if not r["set"]:
        r["high"]    = max(r["high"], candle_high)
        r["low"]     = min(r["low"],  candle_low)
        r["minutes"] += 1
        if r["minutes"] >= 15:   # 15 candles = 15 minutes
            r["set"] = True

def reset_opening_ranges():
    """Call at 9:15 AM every day."""
    global _opening_range
    _opening_range = {}


def calculate_signals(prices: list, volumes: list, vwap: float,
                       highs: list = None, lows: list = None,
                       symbol: str = "") -> dict:
    """
    Main signal function. Returns score -10 to +10.
    BUY  if score >= +6
    SELL if score <= -6
    HOLD otherwise
    """
    if len(prices) < 26:
        return {
            "score": 0, "action": "HOLD",
            "reasons": [f"Need 26 candles, have {len(prices)}"],
            "rsi": 50, "ema_fast": 0, "ema_slow": 0,
            "bb_lower": 0, "bb_upper": 0, "atr": 0,
            "sl_long": 0, "sl_short": 0,
        }

    df = pd.DataFrame({
        "close":  prices,
        "volume": volumes,
        "high":   highs  if highs  else prices,
        "low":    lows   if lows   else prices,
    })

    # ── Indicators ──────────────────────────────────────────────────────────
    df["ema_fast"] = ta.trend.ema_indicator(df["close"], window=EMA_FAST)
    df["ema_slow"] = ta.trend.ema_indicator(df["close"], window=EMA_SLOW)
    df["ema_200"]  = ta.trend.ema_indicator(df["close"], window=min(200, len(prices)))
    df["rsi"]      = ta.momentum.rsi(df["close"], window=RSI_PERIOD)

    bb = ta.volatility.BollingerBands(df["close"], window=BB_PERIOD, window_dev=BB_STD)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()

    # ATR — Volatility-Based Stop Loss
    atr_ind     = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14)
    df["atr"]   = atr_ind.average_true_range()

    latest        = df.iloc[-1]
    prev          = df.iloc[-2]
    current_price = prices[-1]
    avg_vol       = pd.Series(volumes).tail(20).mean()
    current_vol   = volumes[-1]
    atr           = float(latest["atr"]) if not pd.isna(latest["atr"]) else 0
    rsi           = float(latest["rsi"])

    # ATR Stop Loss levels
    sl_long  = round(current_price - (2 * atr), 2)   # For BUY trades
    sl_short = round(current_price + (2 * atr), 2)   # For SELL trades

    score   = 0
    reasons = []

    # ── MARKET REGIME FILTER ─────────────────────────────────────────────────
    regime = "BIDIRECTIONAL"
    if _nifty_bias > 1.0:
        regime = "LONG_ONLY"
        reasons.append(f"Nifty +{_nifty_bias:.1f}% → Long-only mode")
    elif _nifty_bias < -1.0:
        regime = "SHORT_ONLY"
        reasons.append(f"Nifty {_nifty_bias:.1f}% → Short-only mode")
    else:
        reasons.append(f"Nifty {_nifty_bias:+.1f}% → Bidirectional mode")

    # ── 1. EMA CROSSOVER (±3) ────────────────────────────────────────────────
    if latest["ema_fast"] > latest["ema_slow"]:
        score += 2
        reasons.append(f"EMA{EMA_FAST}>{EMA_SLOW} bullish +2")
        if prev["ema_fast"] <= prev["ema_slow"]:
            score += 1
            reasons.append("Fresh bullish crossover +1")
    else:
        score -= 2
        reasons.append(f"EMA{EMA_FAST}<{EMA_SLOW} bearish -2")
        if prev["ema_fast"] >= prev["ema_slow"]:
            score -= 1
            reasons.append("Fresh bearish crossover -1")

    # ── 2. VWAP (±3) ─────────────────────────────────────────────────────────
    if vwap and vwap > 0:
        if current_price > vwap:
            score += 2
            reasons.append(f"Price ₹{current_price:.0f} above VWAP ₹{vwap:.0f} +2")
        else:
            score -= 2
            reasons.append(f"Price ₹{current_price:.0f} below VWAP ₹{vwap:.0f} -2")
        prev_price = prices[-2]
        if abs(prev_price - vwap) / vwap < 0.002:
            if current_price > vwap and current_price > prev_price:
                score += 1
                reasons.append("VWAP retest bounce +1")
            elif current_price < vwap and current_price < prev_price:
                score -= 1
                reasons.append("VWAP rejection bounce -1")

    # ── 3. VOLUME CONFIRMATION (±1) ──────────────────────────────────────────
    if avg_vol > 0:
        vol_ratio = current_vol / avg_vol
        if vol_ratio > 1.5:
            # Volume confirms direction of EMA
            if latest["ema_fast"] > latest["ema_slow"]:
                score += 1
                reasons.append(f"Volume {vol_ratio:.1f}x confirms bullish +1")
            else:
                score -= 1
                reasons.append(f"Volume {vol_ratio:.1f}x confirms bearish -1")
        elif vol_ratio < 0.5:
            score -= 1
            reasons.append("Very low volume — weak signal -1")

    # ── 4. RSI (±2) ──────────────────────────────────────────────────────────
    if rsi < 30:
        score += 2
        reasons.append(f"RSI oversold {rsi:.0f} +2")
    elif rsi > 70:
        score -= 2
        reasons.append(f"RSI overbought {rsi:.0f} -2")
    elif 50 <= rsi <= 70:
        score += 1
        reasons.append(f"RSI bullish zone {rsi:.0f} +1")
    elif 30 <= rsi < 50:
        score -= 1
        reasons.append(f"RSI bearish zone {rsi:.0f} -1")

    # ── 5. BOLLINGER BANDS (±1) ──────────────────────────────────────────────
    if current_price < latest["bb_lower"]:
        score += 1
        reasons.append("Below lower BB oversold +1")
    elif current_price > latest["bb_upper"]:
        score -= 1
        reasons.append("Above upper BB overbought -1")

    # ── 6. OPENING RANGE BREAKOUT (±2 bonus) ─────────────────────────────────
    orb = _opening_range.get(symbol, {})
    if orb.get("set"):
        orb_range = orb["high"] - orb["low"]
        if orb_range > 0:
            if current_price > orb["high"]:
                score += 2
                reasons.append(f"ORB breakout above ₹{orb['high']:.0f} +2")
            elif current_price < orb["low"]:
                score -= 2
                reasons.append(f"ORB breakdown below ₹{orb['low']:.0f} -2")

    # ── MARKET REGIME ENFORCEMENT ─────────────────────────────────────────────
    # Override: In strong trending markets, block counter-trend signals
    if regime == "LONG_ONLY" and score < 0:
        score = max(score, 0)
        reasons.append("Score floored to 0 — Long-only mode active")
    elif regime == "SHORT_ONLY" and score > 0:
        score = min(score, 0)
        reasons.append("Score capped to 0 — Short-only mode active")

    # ── FINAL DECISION ────────────────────────────────────────────────────────
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
        "regime":   regime,
        "rsi":      round(rsi, 1),
        "ema_fast": round(float(latest["ema_fast"]), 2),
        "ema_slow": round(float(latest["ema_slow"]), 2),
        "bb_lower": round(float(latest["bb_lower"]), 2),
        "bb_upper": round(float(latest["bb_upper"]), 2),
        "atr":      round(atr, 2),
        "sl_long":  sl_long,
        "sl_short": sl_short,
        "vwap":     round(vwap, 2) if vwap else 0,
        "orb_high": orb.get("high", 0),
        "orb_low":  orb.get("low", 0),
        "orb_set":  orb.get("set", False),
    }
