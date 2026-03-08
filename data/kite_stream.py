"""
data/kite_stream.py
Connects to Zerodha Kite WebSocket for live tick data.
Feeds ticks into CandleBuilder.
"""
import logging
from kiteconnect import KiteTicker
from data.candle_builder import CandleBuilder
from config import KITE_API_KEY, KITE_ACCESS_TOKEN

logger = logging.getLogger(__name__)


class KiteStream:

    def __init__(self, candle_builder: CandleBuilder, watchlist_tokens: dict):
        """
        watchlist_tokens: dict mapping instrument_token (int) to stock symbol (str)
        e.g. {738561: "RELIANCE", 408065: "HDFCBANK"}
        Get these tokens from Kite's instrument list.
        """
        self.candle_builder   = candle_builder
        self.watchlist_tokens = watchlist_tokens  # token → symbol
        self.ticker           = None

    def start(self):
        """Start the WebSocket connection."""
        self.ticker = KiteTicker(KITE_API_KEY, KITE_ACCESS_TOKEN)

        self.ticker.on_ticks   = self._on_ticks
        self.ticker.on_connect = self._on_connect
        self.ticker.on_close   = self._on_close
        self.ticker.on_error   = self._on_error

        tokens = list(self.watchlist_tokens.keys())
        self.ticker.connect(threaded=True)
        logger.info(f"KiteStream started for {len(tokens)} instruments")

    def _on_connect(self, ws, response):
        tokens = list(self.watchlist_tokens.keys())
        ws.subscribe(tokens)
        ws.set_mode(ws.MODE_FULL, tokens)
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

    def _on_error(self, ws, code, reason):
        logger.error(f"WebSocket error: {code} {reason}")

    def stop(self):
        if self.ticker:
            self.ticker.close()


def get_instrument_tokens(kite, symbols: list) -> dict:
    """
    Fetches instrument tokens for given stock symbols from Kite.
    Returns {token: symbol} dict.
    Example: {738561: 'RELIANCE', 408065: 'HDFCBANK'}
    """
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
