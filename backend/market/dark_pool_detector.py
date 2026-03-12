"""
dark_pool_detector.py - Simulated Dark Pool / Institutional Activity Detection
===============================================================================
Since real dark pool data is unavailable for Indian markets,
this module simulates institutional accumulation/distribution detection using:
- Large volume clusters
- VWAP deviations
- Sudden absorption candles (high volume, small body)
"""
import numpy as np
from datetime import datetime, timezone, timedelta


def get_ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


def detect_dark_pool_zones(prices, volumes, vwap=0.0, symbol=""):
    """
    Detect institutional accumulation/distribution zones.

    Args:
        prices: list of close prices (min 20)
        volumes: list of volumes (min 20)
        vwap: current VWAP value
        symbol: stock symbol

    Returns:
        dict with zone_price, zone_type, confidence, zones list
    """
    if len(prices) < 20 or len(volumes) < 20:
        return {
            "zone_price": 0,
            "zone_type": "none",
            "confidence": 0,
            "zones": [],
            "institutional_activity": False,
            "symbol": symbol,
        }

    prices_arr = np.array(prices[-30:] if len(prices) >= 30 else prices, dtype=float)
    volumes_arr = np.array(volumes[-30:] if len(volumes) >= 30 else volumes, dtype=float)
    n = len(prices_arr)

    avg_vol = np.mean(volumes_arr)
    if avg_vol <= 0:
        avg_vol = 1

    zones = []
    primary_zone = None
    primary_confidence = 0

    for i in range(2, n):
        vol = volumes_arr[i]
        vol_ratio = vol / avg_vol

        # Absorption candle: high volume but small price change
        if i > 0:
            body_size = abs(prices_arr[i] - prices_arr[i - 1])
            avg_body = np.mean(np.abs(np.diff(prices_arr[max(0, i - 10):i]))) if i > 1 else body_size
            is_absorption = vol_ratio > 1.8 and (body_size < avg_body * 0.5 if avg_body > 0 else False)
        else:
            is_absorption = False

        # Volume cluster: 3+ consecutive high-volume candles
        is_cluster = False
        if i >= 2:
            cluster_vols = volumes_arr[i - 2:i + 1]
            is_cluster = all(v > avg_vol * 1.3 for v in cluster_vols)

        # VWAP deviation zone
        vwap_dev = 0
        if vwap > 0:
            vwap_dev = (prices_arr[i] - vwap) / vwap * 100

        if is_absorption or is_cluster:
            # Determine accumulation vs distribution
            price_trend = prices_arr[i] - prices_arr[max(0, i - 5)]
            recent_momentum = prices_arr[i] - prices_arr[i - 1] if i > 0 else 0

            if recent_momentum >= 0 and is_absorption:
                zone_type = "accumulation"
                confidence = min(95, 40 + vol_ratio * 10 + (10 if is_cluster else 0))
            elif recent_momentum < 0 and is_absorption:
                zone_type = "distribution"
                confidence = min(95, 40 + vol_ratio * 10 + (10 if is_cluster else 0))
            elif price_trend > 0:
                zone_type = "accumulation"
                confidence = min(90, 35 + vol_ratio * 8)
            else:
                zone_type = "distribution"
                confidence = min(90, 35 + vol_ratio * 8)

            zone = {
                "zone_price": round(float(prices_arr[i]), 2),
                "zone_type": zone_type,
                "confidence": round(confidence),
                "volume_ratio": round(vol_ratio, 2),
                "absorption_candle": bool(is_absorption),
                "volume_cluster": bool(is_cluster),
                "vwap_deviation": round(float(vwap_dev), 3),
                "candle_index": int(i),
            }
            zones.append(zone)

            if confidence > primary_confidence:
                primary_confidence = confidence
                primary_zone = zone

    # Determine overall institutional activity
    institutional = len(zones) >= 2 or (primary_confidence >= 60)

    return {
        "zone_price": primary_zone["zone_price"] if primary_zone else 0,
        "zone_type": primary_zone["zone_type"] if primary_zone else "none",
        "confidence": primary_zone["confidence"] if primary_zone else 0,
        "zones": zones[-5:],  # Last 5 zones
        "total_zones_detected": len(zones),
        "institutional_activity": bool(institutional),
        "vwap": round(float(vwap), 2),
        "symbol": symbol,
        "timestamp": get_ist_now().isoformat(),
    }


def is_near_accumulation_zone(current_price, zones, threshold_pct=0.5):
    """Check if current price is near an accumulation zone."""
    for zone in zones:
        if zone["zone_type"] == "accumulation":
            zone_price = zone["zone_price"]
            if zone_price > 0:
                deviation = abs(current_price - zone_price) / zone_price * 100
                if deviation <= threshold_pct:
                    return True, zone
    return False, None
