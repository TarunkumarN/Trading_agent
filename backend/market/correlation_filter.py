"""
correlation_filter.py - Multi-Asset Correlation Filter
=======================================================
Confirms trade direction using correlated market instruments.
Examples:
- NIFTY correlated with BANKNIFTY
- Gold inversely correlated with USD/INR
- RELIANCE correlated with NIFTY
"""
import numpy as np
from datetime import datetime, timezone, timedelta


def get_ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


# Correlation pairs: (asset, correlated_asset, expected_direction)
# direction: 1 = positive correlation, -1 = inverse correlation
CORRELATION_MAP = {
    "NIFTY": [("BANKNIFTY", 1), ("RELIANCE", 1), ("HDFCBANK", 1)],
    "BANKNIFTY": [("NIFTY", 1), ("HDFCBANK", 1), ("ICICIBANK", 1), ("AXISBANK", 1)],
    "RELIANCE": [("NIFTY", 1), ("ONGC", 0.6)],
    "TCS": [("INFY", 1), ("WIPRO", 0.8), ("NIFTY", 0.7)],
    "INFY": [("TCS", 1), ("WIPRO", 0.8), ("NIFTY", 0.7)],
    "HDFCBANK": [("BANKNIFTY", 1), ("ICICIBANK", 0.8), ("NIFTY", 0.7)],
    "ICICIBANK": [("BANKNIFTY", 1), ("HDFCBANK", 0.8), ("AXISBANK", 0.8)],
    "SBIN": [("BANKNIFTY", 0.7), ("NIFTY", 0.6)],
    "ITC": [("NIFTY", 0.5), ("HINDUNILVR", 0.4)],
    "BAJFINANCE": [("BANKNIFTY", 0.8), ("NIFTY", 0.7)],
    "GOLD": [("NIFTY", -0.3)],
    "SILVER": [("GOLD", 0.9)],
    "CRUDEOIL": [("ONGC", 0.6), ("NIFTY", -0.2)],
}


def check_correlation(symbol, action, market_data, symbol_prices=None):
    """
    Check if correlated assets confirm the trade direction.

    Args:
        symbol: trading symbol
        action: "BUY" or "SELL"
        market_data: dict of {symbol: {change_pct, price}} from market feed
        symbol_prices: optional dict of {symbol: [price_history]}

    Returns:
        dict with correlation_strength, confirmation, details
    """
    pairs = CORRELATION_MAP.get(symbol, [])
    if not pairs:
        # No known correlations — pass through with neutral score
        return {
            "correlation_strength": 50,
            "confirmation": True,
            "details": f"No correlation data for {symbol}, allowing trade",
            "pairs_checked": 0,
            "pairs_confirmed": 0,
            "symbol": symbol,
        }

    confirmed_count = 0
    total_strength = 0
    details_parts = []

    for pair_symbol, expected_corr in pairs:
        pair_data = market_data.get(pair_symbol, {})
        pair_change = pair_data.get("change_pct", 0)

        if pair_change == 0 and pair_data.get("price", 0) == 0:
            continue  # No data for this pair

        # Expected movement based on correlation
        if action == "BUY":
            expected_move = expected_corr > 0  # Positive correlation = pair should also be up
        else:
            expected_move = expected_corr < 0  # For sells, positive corr = pair should be down

        # Check if pair confirms
        # Handle positive and inverse correlations
        if expected_corr > 0:
            # Positive correlation: both should move same direction
            if action == "BUY" and pair_change > 0:
                confirmed_count += 1
                strength = min(100, abs(pair_change) * 20 * abs(expected_corr))
                details_parts.append(f"{pair_symbol} +{pair_change:.2f}% confirms BUY (corr={expected_corr})")
            elif action == "SELL" and pair_change < 0:
                confirmed_count += 1
                strength = min(100, abs(pair_change) * 20 * abs(expected_corr))
                details_parts.append(f"{pair_symbol} {pair_change:.2f}% confirms SELL (corr={expected_corr})")
            else:
                strength = 0
                details_parts.append(f"{pair_symbol} {pair_change:+.2f}% contradicts {action}")
        else:
            # Inverse correlation: should move opposite
            if action == "BUY" and pair_change < 0:
                confirmed_count += 1
                strength = min(100, abs(pair_change) * 20 * abs(expected_corr))
                details_parts.append(f"{pair_symbol} {pair_change:.2f}% confirms BUY (inv corr={expected_corr})")
            elif action == "SELL" and pair_change > 0:
                confirmed_count += 1
                strength = min(100, abs(pair_change) * 20 * abs(expected_corr))
                details_parts.append(f"{pair_symbol} +{pair_change:.2f}% confirms SELL (inv corr={expected_corr})")
            else:
                strength = 0

        total_strength += strength

    pairs_checked = len([p for p in pairs if market_data.get(p[0], {}).get("price", 0) > 0])
    if pairs_checked == 0:
        pairs_checked = len(pairs)

    avg_strength = round(total_strength / max(1, pairs_checked))
    confirmation = confirmed_count >= max(1, pairs_checked // 2)

    return {
        "correlation_strength": min(100, avg_strength),
        "confirmation": confirmation,
        "details": " | ".join(details_parts) if details_parts else "No correlation data available",
        "pairs_checked": pairs_checked,
        "pairs_confirmed": confirmed_count,
        "symbol": symbol,
        "action": action,
        "timestamp": get_ist_now().isoformat(),
    }
