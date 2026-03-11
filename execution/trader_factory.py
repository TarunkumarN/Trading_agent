"""
execution/trader_factory.py
Selects the correct trader implementation for the configured mode.
"""
from config import TRADING_MODE
from execution.live_trader import LiveTrader
from execution.paper_trader import PaperTrader


def create_trader(guard):
    if TRADING_MODE.lower() == "live":
        return LiveTrader(guard)
    return PaperTrader(guard)
