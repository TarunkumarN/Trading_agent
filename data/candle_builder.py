"""
data/candle_builder.py — Fixed version
- Latest prices tracked correctly
- VWAP calculation fixed
- Candle history saved to disk and survives restarts
"""
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import json

CANDLE_CACHE = Path("logs/candle_cache.json")

class CandleBuilder:

    def __init__(self):
        self.price_history  = defaultdict(list)
        self.volume_history = defaultdict(list)
        self.vwap           = defaultdict(float)
        self._latest_prices = {}           # ← persists across ticks
        self._vwap_tp_vol   = defaultdict(float)
        self._vwap_vol      = defaultdict(float)
        self._candle        = defaultdict(dict)
        self._load_cache()                 # ← restore candles from disk

    def on_tick(self, stock: str, ltp: float, volume: int, timestamp: datetime):
        if not ltp or ltp <= 0:
            return

        # ── Track latest price ────────────────────────────────
        self._latest_prices[stock] = ltp   # ← fixed: don't reset dict!

        # ── VWAP calculation ──────────────────────────────────
        self._vwap_tp_vol[stock] += ltp * volume
        self._vwap_vol[stock]    += volume
        if self._vwap_vol[stock] > 0:
            self.vwap[stock] = self._vwap_tp_vol[stock] / self._vwap_vol[stock]  # ← fixed

        # ── Candle accumulation ───────────────────────────────
        candle = self._candle[stock]
        if not candle:
            candle.update({"open": ltp, "high": ltp, "low": ltp,
                           "close": ltp, "volume": volume, "start": str(timestamp)})
        else:
            candle["high"]    = max(candle["high"], ltp)
            candle["low"]     = min(candle["low"], ltp)
            candle["close"]   = ltp
            candle["volume"] += volume

    def close_candle(self, stock: str):
        candle = self._candle.get(stock, {})
        if not candle:
            return
        self.price_history[stock].append(candle["close"])
        self.volume_history[stock].append(candle["volume"])
        # Keep last 100 candles
        if len(self.price_history[stock]) > 100:
            self.price_history[stock]  = self.price_history[stock][-100:]
            self.volume_history[stock] = self.volume_history[stock][-100:]
        self._candle[stock] = {}
        self._save_cache()   # ← save to disk after every candle

    def reset_day(self, stock: str):
        """Call at start of each trading day."""
        self.price_history[stock]  = []
        self.volume_history[stock] = []
        self.vwap[stock]           = 0.0
        self._vwap_tp_vol[stock]   = 0.0
        self._vwap_vol[stock]      = 0.0
        self._candle[stock]        = {}
        self._save_cache()

    def reset_all(self):
        """Full reset at start of new day."""
        self.price_history.clear()
        self.volume_history.clear()
        self.vwap.clear()
        self._latest_prices.clear()
        self._vwap_tp_vol.clear()
        self._vwap_vol.clear()
        self._candle.clear()
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
                "price_history":  dict(self.price_history),
                "volume_history": dict(self.volume_history),
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            CANDLE_CACHE.write_text(json.dumps(cache))
        except Exception as e:
            pass

    def _load_cache(self):
        """Load candle history from disk if same trading day."""
        try:
            if not CANDLE_CACHE.exists():
                return
            cache = json.loads(CANDLE_CACHE.read_text())
            today = datetime.now().strftime("%Y-%m-%d")
            if cache.get("date") != today:
                CANDLE_CACHE.unlink()  # stale cache from yesterday
                return
            for stock, prices in cache.get("price_history", {}).items():
                self.price_history[stock] = prices
            for stock, vols in cache.get("volume_history", {}).items():
                self.volume_history[stock] = vols
            total = sum(len(v) for v in self.price_history.values())
            if total > 0:
                import logging
                logging.getLogger("candle_builder").info(
                    f"Restored candle cache: {dict({k: len(v) for k,v in self.price_history.items()})}"
                )
        except Exception as e:
            pass
