from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd
import ta


@dataclass
class MarketRegime:
    regime: str
    bullish: bool
    bearish: bool
    sideways: bool
    high_volatility: bool
    trend_strength: float
    atr: float
    atr_pct: float
    ema20: float
    ema50: float
    ema200: float
    vwap_distance_pct: float
    bias_pct: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_market_regime(prices, highs, lows, volumes, vwap=0.0, bias_pct=0.0, atr_threshold_pct=0.7):
    if len(prices) < 50:
        return MarketRegime(
            regime="INSUFFICIENT_DATA",
            bullish=False,
            bearish=False,
            sideways=True,
            high_volatility=False,
            trend_strength=0.0,
            atr=0.0,
            atr_pct=0.0,
            ema20=0.0,
            ema50=0.0,
            ema200=0.0,
            vwap_distance_pct=0.0,
            bias_pct=bias_pct,
        )

    df = pd.DataFrame({"close": prices, "high": highs, "low": lows, "volume": volumes})
    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["ema200"] = ta.trend.ema_indicator(df["close"], window=min(200, len(df)))
    df["atr"] = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
    df["adx"] = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14).adx()

    latest = df.iloc[-1]
    current_price = float(latest["close"])
    ema20 = float(latest["ema20"])
    ema50 = float(latest["ema50"])
    ema200 = float(latest["ema200"])
    atr = float(latest["atr"])
    atr_pct = (atr / current_price * 100) if current_price else 0.0
    adx = float(latest["adx"])
    vwap_distance_pct = ((current_price - vwap) / vwap * 100) if vwap else 0.0

    bullish = ema20 > ema50 > ema200
    bearish = ema20 < ema50 < ema200
    crossings = 0
    ema20_tail = df["ema20"].tail(12).tolist()
    ema50_tail = df["ema50"].tail(12).tolist()
    for left, right in zip(range(len(ema20_tail) - 1), range(1, len(ema20_tail))):
        prev_rel = ema20_tail[left] - ema50_tail[left]
        curr_rel = ema20_tail[right] - ema50_tail[right]
        if prev_rel == 0 or curr_rel == 0 or (prev_rel > 0 > curr_rel) or (prev_rel < 0 < curr_rel):
            crossings += 1
    sideways = not bullish and not bearish or crossings >= 3
    high_volatility = atr_pct >= atr_threshold_pct

    if bullish and not sideways:
        regime = "BULLISH"
    elif bearish and not sideways:
        regime = "BEARISH"
    elif high_volatility:
        regime = "HIGH_VOLATILITY"
    else:
        regime = "SIDEWAYS"

    trend_strength = max(0.0, min(100.0, adx * 4 + abs(vwap_distance_pct) * 5 + abs(bias_pct) * 10))

    return MarketRegime(
        regime=regime,
        bullish=bullish,
        bearish=bearish,
        sideways=sideways,
        high_volatility=high_volatility,
        trend_strength=round(trend_strength, 2),
        atr=round(atr, 2),
        atr_pct=round(atr_pct, 2),
        ema20=round(ema20, 2),
        ema50=round(ema50, 2),
        ema200=round(ema200, 2),
        vwap_distance_pct=round(vwap_distance_pct, 2),
        bias_pct=round(bias_pct, 2),
    )
