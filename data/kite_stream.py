"""
data/kite_stream.py — with auto-reconnect
"""
import logging
import threading
import time
from kiteconnect import KiteTicker
from data.candle_builder import CandleBuilder
from config import KITE_API_KEY, KITE_ACCESS_TOKEN

logger = logging.getLogger(__name__)

class KiteStream:
    def __init__(self, candle_builder: CandleBuilder, watchlist_tokens: dict):
        self.candle_builder   = candle_builder
        self.watchlist_tokens = watchlist_tokens
        self.ticker           = None
        self._running         = False
        self._reconnect_delay = 5

    def start(self):
        self._running = True
        self._connect()

    def _connect(self):
        try:
            if self.ticker:
                try: self.ticker.close()
                except: pass
            self.ticker = KiteTicker(KITE_API_KEY, KITE_ACCESS_TOKEN)
            self.ticker.on_ticks   = self._on_ticks
            self.ticker.on_connect = self._on_connect
            self.ticker.on_close   = self._on_close
            self.ticker.on_error   = self._on_error
            self.ticker.connect(threaded=True)
            logger.info(f"KiteStream connecting for {len(self.watchlist_tokens)} instruments")
        except Exception as e:
            logger.error(f"KiteStream connect error: {e}")
            self._schedule_reconnect()

    def _on_connect(self, ws, response):
        tokens = list(self.watchlist_tokens.keys())
        ws.subscribe(tokens)
        ws.set_mode(ws.MODE_FULL, tokens)
        self._reconnect_delay = 5  # reset delay on success
        logger.info(f"WebSocket connected. Subscribed to {tokens}")

    def _on_ticks(self, ws, ticks):
        from datetime import datetime
        for tick in ticks:
            token  = tick.get("instrument_token")
            symbol = self.watchlist_tokens.get(token)
            if not symbol:
                continue
            ltp    = tick.get("last_price", 0)
            volume = tick.get("volume_traded", 0)
            ts     = tick.get("exchange_timestamp", datetime.now())
            self.candle_builder.on_tick(symbol, ltp, volume, ts)

    def _on_close(self, ws, code, reason):
        logger.warning(f"WebSocket closed: {code} {reason}")
        if self._running:
            self._schedule_reconnect()

    def _on_error(self, ws, code, reason):
        logger.error(f"WebSocket error: {code} {reason}")
        if self._running:
            self._schedule_reconnect()

    def _schedule_reconnect(self):
        logger.info(f"Reconnecting in {self._reconnect_delay}s...")
        threading.Timer(self._reconnect_delay, self._connect).start()
        self._reconnect_delay = min(self._reconnect_delay * 2, 60)

    def stop(self):
        self._running = False
        if self.ticker:
            try: self.ticker.close()
            except: pass


def get_instrument_tokens(kite, symbols: list) -> dict:
    try:
        instruments = kite.instruments("NSE")
        token_map   = {}
        for inst in instruments:
            if inst["tradingsymbol"] in symbols:
                token_map[inst["instrument_token"]] = inst["tradingsymbol"]
        return token_map
    except Exception as e:
        logger.error(f"Failed to fetch instrument tokens: {e}")
        return {}

def start_stream(candle_builder, watchlist_tokens):
    stream = KiteStream(candle_builder, watchlist_tokens)
    stream.start()
    return stream
