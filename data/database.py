"""
data/database.py
MongoDB integration — replaces all JSON file storage.
Collections: trades, positions, watchlist, pnl_history, agent_state, candles, signals, market_data
"""
import os
import logging
from datetime import datetime, date
from pymongo import MongoClient, DESCENDING

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "")
DB_NAME     = "minimax_trading"

class Database:
    def __init__(self):
        self.client    = None
        self.db        = None
        self.connected = False
        self._connect()

    def _connect(self):
        try:
            self.client    = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")
            self.db        = self.client[DB_NAME]
            self.connected = True
            logger.info(f"MongoDB connected: {DB_NAME}")
            self._ensure_indexes()
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            self.connected = False

    def _ensure_indexes(self):
        try:
            self.db.trades.create_index([("date", DESCENDING)])
            self.db.trades.create_index([("stock", 1)])
            self.db.positions.create_index([("stock", 1)], unique=True)
            self.db.pnl_history.create_index([("date", DESCENDING)], unique=True)
            self.db.candles.create_index([("symbol", 1), ("saved_at", DESCENDING)])
            self.db.signals.create_index([("symbol", 1), ("saved_at", DESCENDING)])
            self.db.market_data.create_index([("timestamp", DESCENDING)])
        except Exception as e:
            logger.warning(f"Index warning: {e}")

    # Trades
    def save_trade(self, trade: dict):
        if not self.connected: return
        try:
            trade["saved_at"] = datetime.now()
            self.db.trades.insert_one(trade)
        except Exception as e:
            logger.error(f"Save trade error: {e}")

    def get_trades(self, date_str=None, limit=100):
        if not self.connected: return []
        try:
            query = {"date": date_str} if date_str else {}
            return list(self.db.trades.find(query, {"_id": 0}).sort("saved_at", DESCENDING).limit(limit))
        except Exception as e:
            logger.error(f"Get trades error: {e}")
            return []

    def get_today_trades(self): return self.get_trades(date_str=date.today().isoformat())
    def get_all_trades(self, limit=500): return self.get_trades(limit=limit)
    def get_daily_pnl(self): return sum(t.get("pnl", 0) for t in self.get_today_trades() if t.get("status") == "CLOSED")

    # Positions
    def save_position(self, stock: str, position: dict):
        if not self.connected: return
        try:
            position["stock"] = stock
            position["updated_at"] = datetime.now()
            self.db.positions.update_one({"stock": stock}, {"$set": position}, upsert=True)
        except Exception as e:
            logger.error(f"Save position error: {e}")

    def delete_position(self, stock: str):
        if not self.connected: return
        try:
            self.db.positions.delete_one({"stock": stock})
        except Exception as e:
            logger.error(f"Delete position error: {e}")

    def get_positions(self):
        if not self.connected: return {}
        try:
            return {p["stock"]: p for p in self.db.positions.find({}, {"_id": 0})}
        except Exception as e:
            logger.error(f"Get positions error: {e}")
            return {}

    def clear_positions(self):
        if not self.connected: return
        try: self.db.positions.delete_many({})
        except Exception as e: logger.error(f"Clear positions error: {e}")

    # Watchlist
    def save_watchlist(self, symbols: list):
        if not self.connected: return
        try:
            self.db.watchlist.update_one(
                {"_id": "current"},
                {"$set": {"symbols": symbols, "updated_at": datetime.now()}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Save watchlist error: {e}")

    def get_watchlist(self):
        if not self.connected: return []
        try:
            doc = self.db.watchlist.find_one({"_id": "current"})
            return doc.get("symbols", []) if doc else []
        except Exception as e:
            logger.error(f"Get watchlist error: {e}")
            return []

    # P&L History
    def save_daily_pnl(self, pnl: float, trades: int, wins: int):
        if not self.connected: return
        try:
            today = date.today().isoformat()
            self.db.pnl_history.update_one(
                {"date": today},
                {"$set": {"date": today, "pnl": round(pnl, 2), "trades": trades,
                          "wins": wins, "losses": trades - wins, "updated_at": datetime.now()}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Save daily PnL error: {e}")

    def get_pnl_history(self, days=30):
        if not self.connected: return []
        try:
            return list(self.db.pnl_history.find({}, {"_id": 0}).sort("date", DESCENDING).limit(days))
        except Exception as e:
            logger.error(f"Get PnL history error: {e}")
            return []

    # Agent State
    def save_agent_state(self, state: dict):
        if not self.connected: return
        try:
            state["updated_at"] = datetime.now()
            self.db.agent_state.update_one({"_id": "state"}, {"$set": state}, upsert=True)
        except Exception as e:
            logger.error(f"Save agent state error: {e}")

    def get_agent_state(self):
        if not self.connected: return {}
        try:
            doc = self.db.agent_state.find_one({"_id": "state"}, {"_id": 0})
            return doc or {}
        except Exception as e:
            logger.error(f"Get agent state error: {e}")
            return {}

    # Candles
    def save_candle(self, symbol: str, candle: dict):
        if not self.connected: return
        try:
            candle["symbol"]   = symbol
            candle["date"]     = date.today().isoformat()
            candle["saved_at"] = datetime.now()
            self.db.candles.insert_one(candle)
        except Exception as e:
            logger.error(f"Save candle error: {e}")

    def get_candles(self, symbol: str, date_str=None, limit=100):
        if not self.connected: return []
        try:
            query = {"symbol": symbol}
            if date_str: query["date"] = date_str
            return list(self.db.candles.find(query, {"_id": 0}).sort("saved_at", DESCENDING).limit(limit))
        except Exception as e:
            logger.error(f"Get candles error: {e}")
            return []

    # Signals
    def save_signal(self, symbol: str, signal: dict):
        if not self.connected: return
        try:
            signal["symbol"]   = symbol
            signal["date"]     = date.today().isoformat()
            signal["saved_at"] = datetime.now()
            self.db.signals.insert_one(signal)
        except Exception as e:
            logger.error(f"Save signal error: {e}")

    def get_signals(self, symbol=None, date_str=None, limit=200):
        if not self.connected: return []
        try:
            query = {}
            if symbol:   query["symbol"] = symbol
            if date_str: query["date"]   = date_str
            return list(self.db.signals.find(query, {"_id": 0}).sort("saved_at", DESCENDING).limit(limit))
        except Exception as e:
            logger.error(f"Get signals error: {e}")
            return []

    # Market Data
    def save_market_snapshot(self, data: dict):
        if not self.connected: return
        try:
            data["timestamp"] = datetime.now()
            data["date"]      = date.today().isoformat()
            self.db.market_data.insert_one(data)
        except Exception as e:
            logger.error(f"Save market snapshot error: {e}")

    def get_latest_market(self):
        if not self.connected: return {}
        try:
            doc = self.db.market_data.find_one({}, {"_id": 0}, sort=[("timestamp", DESCENDING)])
            return doc or {}
        except Exception as e:
            logger.error(f"Get market data error: {e}")
            return {}

    # Migration
    def migrate_json_files(self):
        import json
        from pathlib import Path
        migrated = 0
        trades_file = Path("logs/trades.json")
        if trades_file.exists():
            try:
                trades = json.loads(trades_file.read_text())
                if trades and self.db.trades.count_documents({}) == 0:
                    for t in trades: t.setdefault("saved_at", datetime.now())
                    self.db.trades.insert_many(trades)
                    migrated += len(trades)
                    logger.info(f"Migrated {len(trades)} trades")
            except Exception as e:
                logger.warning(f"Trade migration warning: {e}")
        wl_file = Path("logs/watchlist.json")
        if wl_file.exists():
            try:
                wl = json.loads(wl_file.read_text())
                if wl: self.save_watchlist(wl); migrated += 1
            except Exception as e:
                logger.warning(f"Watchlist migration warning: {e}")
        logger.info(f"Migration complete: {migrated} records")
        return migrated

db = Database()
