"""
data/candle_builder.py - Fixed version
- Latest prices tracked correctly
- VWAP calculation uses incremental traded volume instead of cumulative exchange volume
- Candle history saved to disk and survives restarts
"""
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import json

CANDLE_CACHE = Path("logs/candle_cache.json")


class CandleBuilder:

    def __init__(self):
        self.price_history = defaultdict(list)
        self.volume_history = defaultdict(list)
        self.high_history = defaultdict(list)
        self.low_history = defaultdict(list)
        self.vwap = defaultdict(float)
        self._latest_prices = {}
        self._vwap_tp_vol = defaultdict(float)
        self._vwap_vol = defaultdict(float)
        self._candle = defaultdict(dict)
        self._last_total_volume = {}
        self._load_cache()

    def on_tick(self, stock: str, ltp: float, total_volume: int, timestamp: datetime):
        if not ltp or ltp <= 0:
            return

        self._latest_prices[stock] = ltp

        prev_total = self._last_total_volume.get(stock)
        incremental_volume = 0
        if total_volume is not None and total_volume >= 0:
            if prev_total is not None:
                incremental_volume = max(total_volume - prev_total, 0)
            self._last_total_volume[stock] = total_volume

        if incremental_volume > 0:
            self._vwap_tp_vol[stock] += ltp * incremental_volume
            self._vwap_vol[stock] += incremental_volume
            self.vwap[stock] = self._vwap_tp_vol[stock] / self._vwap_vol[stock]

        candle = self._candle[stock]
        if not candle:
            candle.update({
                "open": ltp,
                "high": ltp,
                "low": ltp,
                "close": ltp,
                "volume": incremental_volume,
                "start": str(timestamp),
            })
        else:
            candle["high"] = max(candle["high"], ltp)
            candle["low"] = min(candle["low"], ltp)
            candle["close"] = ltp
            candle["volume"] += incremental_volume

    def close_candle(self, stock: str):
        candle = self._candle.get(stock, {})
        if not candle:
            return

        self.price_history[stock].append(candle["close"])
        self.volume_history[stock].append(candle["volume"])
        self.high_history[stock].append(candle["high"])
        self.low_history[stock].append(candle["low"])

        if len(self.price_history[stock]) > 100:
            self.price_history[stock] = self.price_history[stock][-100:]
            self.volume_history[stock] = self.volume_history[stock][-100:]
            self.high_history[stock] = self.high_history[stock][-100:]
            self.low_history[stock] = self.low_history[stock][-100:]

        self._candle[stock] = {}
        self._save_cache()

    def reset_day(self, stock: str):
        """Call at start of each trading day."""
        self.price_history[stock] = []
        self.volume_history[stock] = []
        self.high_history[stock] = []
        self.low_history[stock] = []
        self.vwap[stock] = 0.0
        self._vwap_tp_vol[stock] = 0.0
        self._vwap_vol[stock] = 0.0
        self._candle[stock] = {}
        self._last_total_volume.pop(stock, None)
        self._save_cache()

    def reset_all(self):
        """Full reset at start of new day."""
        self.price_history.clear()
        self.volume_history.clear()
        self.high_history.clear()
        self.low_history.clear()
        self.vwap.clear()
        self._latest_prices.clear()
        self._vwap_tp_vol.clear()
        self._vwap_vol.clear()
        self._candle.clear()
        self._last_total_volume.clear()
        if CANDLE_CACHE.exists():
            CANDLE_CACHE.unlink()

    def get_latest_prices(self) -> dict:
        """Returns real-time LTP for all tracked stocks."""
        return dict(self._latest_prices)

    def get_latest_price(self, stock: str) -> float:
        return self._latest_prices.get(stock) or self._candle.get(stock, {}).get("close", 0.0)

    def get_all_prices(self) -> dict:
        return self.get_latest_prices()

    def _save_cache(self):
        """Save candle history to disk so it survives restarts."""
        try:
            cache = {
                "price_history": dict(self.price_history),
                "volume_history": dict(self.volume_history),
                "high_history": dict(self.high_history),
                "low_history": dict(self.low_history),
                "date": datetime.now().strftime("%Y-%m-%d"),
            }
            CANDLE_CACHE.write_text(json.dumps(cache))
        except Exception:
            pass

    def _load_cache(self):
        """Load candle history from disk if same trading day."""
        try:
            if not CANDLE_CACHE.exists():
                return
            cache = json.loads(CANDLE_CACHE.read_text())
            today = datetime.now().strftime("%Y-%m-%d")
            if cache.get("date") != today:
                CANDLE_CACHE.unlink()
                return
            for stock, prices in cache.get("price_history", {}).items():
                self.price_history[stock] = prices
            for stock, vols in cache.get("volume_history", {}).items():
                self.volume_history[stock] = vols
            for stock, highs in cache.get("high_history", {}).items():
                self.high_history[stock] = highs
            for stock, lows in cache.get("low_history", {}).items():
                self.low_history[stock] = lows
            total = sum(len(v) for v in self.price_history.values())
            if total > 0:
                import logging
                logging.getLogger("candle_builder").info(
                    f"Restored candle cache: {dict({k: len(v) for k, v in self.price_history.items()})}"
                )
        except Exception:
            pass
