"""
options_flow.py - Unusual Options Activity Detection
=====================================================
Detects unusual options activity by analyzing volume patterns,
price-volume divergences, and large block trade signatures.
Since real options chain data requires broker API, this module
simulates institutional flow detection using equity volume patterns.
"""
import numpy as np
from datetime import datetime, timezone, timedelta


def get_ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


def analyze_options_flow(prices, volumes, symbol="", avg_volume_20d=None):
    """
    Detect unusual options activity from price/volume patterns.

    Args:
        prices: list of recent close prices (min 20)
        volumes: list of recent volumes (min 20)
        symbol: stock symbol
        avg_volume_20d: pre-computed 20-day avg volume (optional)

    Returns:
        dict with signal, strength, details
    """
    if len(prices) < 20 or len(volumes) < 20:
        return {
            "signal": "neutral",
            "strength": 0,
            "details": "Insufficient data for options flow analysis",
            "unusual_activity": False,
        }

    prices_arr = np.array(prices[-20:], dtype=float)
    volumes_arr = np.array(volumes[-20:], dtype=float)

    current_vol = volumes_arr[-1]
    avg_vol = avg_volume_20d if avg_volume_20d else np.mean(volumes_arr[:-1])
    if avg_vol <= 0:
        avg_vol = 1

    vol_ratio = current_vol / avg_vol

    # Price momentum (last 5 candles)
    price_change_5 = (prices_arr[-1] - prices_arr[-5]) / prices_arr[-5] * 100 if prices_arr[-5] > 0 else 0
    price_change_1 = (prices_arr[-1] - prices_arr[-2]) / prices_arr[-2] * 100 if prices_arr[-2] > 0 else 0

    # Volume surge detection (simulates block trades)
    vol_std = np.std(volumes_arr[:-1])
    vol_mean = np.mean(volumes_arr[:-1])
    vol_zscore = (current_vol - vol_mean) / vol_std if vol_std > 0 else 0

    # Detect unusual call buying (bullish): high volume + price up
    # Detect unusual put buying (bearish): high volume + price down
    strength = 0
    signal = "neutral"
    unusual = False
    block_detected = False
    details_parts = []

    # Large block trade detection: volume > 2x average with z-score > 2
    if vol_zscore > 2.0 and vol_ratio > 2.0:
        block_detected = True
        details_parts.append(f"Block trade detected: vol {vol_ratio:.1f}x avg (z={vol_zscore:.1f})")
        strength += 25

    # Unusual call buying pattern
    if vol_ratio > 1.5 and price_change_1 > 0.3:
        signal = "bullish_flow"
        strength += 20
        details_parts.append(f"Call buying signal: vol surge {vol_ratio:.1f}x with +{price_change_1:.2f}% move")

    # Unusual put buying pattern
    elif vol_ratio > 1.5 and price_change_1 < -0.3:
        signal = "bearish_flow"
        strength += 20
        details_parts.append(f"Put buying signal: vol surge {vol_ratio:.1f}x with {price_change_1:.2f}% drop")

    # Accumulation pattern: steady volume increase over 5 candles
    vol_trend = np.polyfit(range(5), volumes_arr[-5:], 1)[0]
    if vol_trend > 0 and price_change_5 > 0.5:
        if signal != "bearish_flow":
            signal = "bullish_flow"
        strength += 15
        details_parts.append("Volume accumulation pattern detected")

    # Distribution pattern: volume increase with price decline
    elif vol_trend > 0 and price_change_5 < -0.5:
        if signal != "bullish_flow":
            signal = "bearish_flow"
        strength += 15
        details_parts.append("Volume distribution pattern detected")

    # Volume-price divergence (smart money)
    if vol_ratio > 1.3 and abs(price_change_1) < 0.1:
        strength += 10
        details_parts.append("Volume-price divergence: institutional positioning")

    # Cap strength at 100
    strength = min(100, strength)
    unusual = strength >= 30

    if not details_parts:
        details_parts.append("Normal options flow, no unusual activity")

    return {
        "signal": signal,
        "strength": round(strength),
        "details": " | ".join(details_parts),
        "unusual_activity": unusual,
        "block_trade": block_detected,
        "volume_ratio": round(vol_ratio, 2),
        "volume_zscore": round(vol_zscore, 2),
        "price_momentum_1": round(price_change_1, 3),
        "price_momentum_5": round(price_change_5, 3),
        "symbol": symbol,
        "timestamp": get_ist_now().isoformat(),
    }
