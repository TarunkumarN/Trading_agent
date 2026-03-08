"""
agent/pre_market.py
Runs at 8:30 AM every trading day.
Uses MiniMax web search to collect market intelligence and build the watchlist.
"""
import json
from agent.minimax_brain import ask_minimax, parse_json_response
from notifications.telegram_alerts import alert_pre_market, send_telegram
from config import DEFAULT_WATCHLIST


def run_pre_market() -> dict:
    """
    Collect pre-market data and return a trading plan for the day.
    Returns dict with: market_bias, confidence, watchlist, avoid_today, key_news
    """
    print("[PRE-MARKET] Starting analysis at 8:30 AM...")
    send_telegram("⏰ Pre-market analysis started...")

    prompt = """
    It is 8:30 AM IST. The Indian stock market (NSE/BSE) opens in 45 minutes.
    Please search the web right now and provide a complete trading plan.

    Search for:
    1. SGX Nifty current value (indicates Nifty 50 opening direction)
    2. US markets last close: Dow Jones, S&P 500, NASDAQ (up or down %)
    3. Crude oil current price and direction
    4. Top India market news from last 12 hours (RBI, FII data, major earnings)
    5. Top 5 high-liquidity NSE stocks expected to move today
       (only from Nifty 50, Bank Nifty, or F&O segment)

    Return ONLY this JSON (no other text):
    {
      "market_bias": "BULLISH or BEARISH or NEUTRAL",
      "confidence": 0-100,
      "sgx_nifty": "value and % change",
      "us_markets": "brief summary of Dow and Nasdaq",
      "crude_oil": "price and direction",
      "watchlist": ["STOCK1","STOCK2","STOCK3","STOCK4","STOCK5"],
      "avoid_today": ["any stocks to avoid and why"],
      "key_news": "one sentence summary of most important market news"
    }
    """

    raw    = ask_minimax(prompt, web_search=True)
    result = parse_json_response(raw)

    # Fallback if MiniMax fails
    if not result or "watchlist" not in result:
        print("[PRE-MARKET] MiniMax failed — using default watchlist")
        result = {
            "market_bias":  "NEUTRAL",
            "confidence":   50,
            "sgx_nifty":    "Unavailable",
            "us_markets":   "Unavailable",
            "crude_oil":    "Unavailable",
            "watchlist":    DEFAULT_WATCHLIST,
            "avoid_today":  [],
            "key_news":     "Could not fetch news — using default watchlist"
        }

    alert_pre_market(
        bias       = result.get("market_bias", "NEUTRAL"),
        confidence = result.get("confidence", 50),
        watchlist  = result.get("watchlist", DEFAULT_WATCHLIST),
        news       = result.get("key_news", "No news available")
    )

    print(f"[PRE-MARKET] Bias: {result['market_bias']} | Watchlist: {result['watchlist']}")
    return result


def run_end_of_day_review(trade_log: list, daily_pnl: float) -> str:
    """
    Runs at 3:30 PM. MiniMax reviews today's trades and gives insights.
    """
    if not trade_log:
        return "No trades today."

    wins   = [t for t in trade_log if t["pnl"] >= 0]
    losses = [t for t in trade_log if t["pnl"] < 0]

    prompt = f"""
    Review today's trading performance and provide brief insights.
    
    Total trades: {len(trade_log)}
    Wins: {len(wins)}, Losses: {len(losses)}
    Daily P&L: Rs {daily_pnl:+.2f}
    
    Trade log: {json.dumps(trade_log[:10])}
    
    Return ONLY this JSON:
    {{
      "performance": "EXCELLENT/GOOD/AVERAGE/POOR",
      "best_strategy": "which strategy worked best today",
      "improvement": "one specific tip to improve tomorrow",
      "summary": "two sentence summary"
    }}
    """

    raw    = ask_minimax(prompt, web_search=False)
    result = parse_json_response(raw)
    return result.get("summary", "Review unavailable.")
