"""
data/candle_builder.py
Builds OHLCV candles from live Kite WebSocket tick data.
Also calculates VWAP continuously.
"""
from collections import defaultdict
from datetime import datetime


class CandleBuilder:

    def __init__(self):
        # price_history[stock] = list of close prices
        self.price_history  = defaultdict(list)
        # volume_history[stock] = list of volumes
        self.volume_history = defaultdict(list)
        # vwap[stock] = current VWAP
        self.vwap           = defaultdict(float)
        # Internal VWAP accumulators
        self._vwap_tp_vol   = defaultdict(float)  # sum(typical_price * volume)
        self._vwap_vol      = defaultdict(float)  # sum(volume)
        # Current candle accumulators
        self._candle        = defaultdict(dict)

    def on_tick(self, stock: str, ltp: float, volume: int, timestamp: datetime):
        """
        Call this on every live tick from Kite WebSocket.
        ltp = last traded price
        """
        # ── VWAP calculation ──────────────────────────────────
        # Typical price = (High + Low + Close) / 3
        # For tick data we approximate with LTP
        self._vwap_tp_vol[stock] += ltp * volume
        self._vwap_vol[stock]    += volume
        if self._vwap_vol[stock] > 0:
            self.vwap[stock] = self._vwap_tp_vol[stock] / self._vwap_vol[stock]

        # ── Candle accumulation ───────────────────────────────
        candle = self._candle[stock]
        if not candle:
            candle.update({"open": ltp, "high": ltp, "low": ltp,
                           "close": ltp, "volume": volume, "start": timestamp})
        else:
            candle["high"]    = max(candle["high"], ltp)
            candle["low"]     = min(candle["low"], ltp)
            candle["close"]   = ltp
            candle["volume"] += volume

    def close_candle(self, stock: str):
        """
        Call this at the end of each candle period (every 1 or 5 minutes).
        Pushes the completed candle into history and resets accumulator.
        """
        candle = self._candle.get(stock, {})
        if not candle:
            return

        self.price_history[stock].append(candle["close"])
        self.volume_history[stock].append(candle["volume"])

        # Keep last 100 candles only
        if len(self.price_history[stock]) > 100:
            self.price_history[stock]  = self.price_history[stock][-100:]
            self.volume_history[stock] = self.volume_history[stock][-100:]

        self._candle[stock] = {}

    def reset_day(self, stock: str):
        """Call at start of each trading day to reset VWAP and history."""
        self.price_history[stock]  = []
        self.volume_history[stock] = []
        self.vwap[stock]           = 0.0
        self._vwap_tp_vol[stock]   = 0.0
        self._vwap_vol[stock]      = 0.0
        self._candle[stock]        = {}

    def get_latest_price(self, stock: str) -> float:
        candle = self._candle.get(stock, {})
        # Fallback to last closed candle price if current candle empty
        if not candle:
            hist = self.price_history.get(stock, [])
            return hist[-1] if hist else 0.0
        return candle.get("close", 0.0)

    def get_all_prices(self) -> dict:
        """Returns {stock: latest_price} for all tracked stocks."""
        return {s: self.get_latest_price(s) for s in self._candle}
