"""
data/nse_live.py — Real-time NSE market data via API scraping.
"""
import requests, time, logging
from datetime import datetime

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

class NSELive:
    def __init__(self):
        self.session = None
        self.last_refresh = 0
        self._init_session()

    def _init_session(self):
        try:
            self.session = requests.Session()
            self.session.headers.update(HEADERS)
            self.session.get("https://www.nseindia.com", timeout=8)
            self.last_refresh = time.time()
            logger.info("NSE session initialised")
        except Exception as e:
            logger.error(f"NSE session init failed: {e}")

    def _get(self, url: str) -> dict:
        if time.time() - self.last_refresh > 300:
            self._init_session()
        try:
            r = self.session.get(url, timeout=8)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 401:
                self._init_session()
        except Exception as e:
            logger.warning(f"NSE fetch failed: {e}")
        return {}

    def get_all_indices(self) -> list:
        return self._get("https://www.nseindia.com/api/allIndices").get("data", [])

    def get_nifty50(self) -> dict:
        for idx in self.get_all_indices():
            if idx.get("index") == "NIFTY 50":
                return idx
        return {}

    def get_banknifty(self) -> dict:
        for idx in self.get_all_indices():
            if idx.get("index") == "NIFTY BANK":
                return idx
        return {}

    def get_india_vix(self) -> dict:
        for idx in self.get_all_indices():
            if idx.get("index") == "INDIA VIX":
                return idx
        return {}

    def get_nifty_pct_change(self) -> float:
        return float(self.get_nifty50().get("percentChange", 0))

    def get_nifty50_stocks(self) -> list:
        data = self._get("https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050")
        result = []
        for s in data.get("data", [])[1:]:
            try:
                result.append({
                    "symbol":  s["symbol"],
                    "price":   float(s["lastPrice"]),
                    "open":    float(s["open"]),
                    "high":    float(s["dayHigh"]),
                    "low":     float(s["dayLow"]),
                    "prev":    float(s["previousClose"]),
                    "change":  float(s["change"]),
                    "pChange": float(s["pChange"]),
                    "volume":  int(s["totalTradedVolume"]),
                    "gap_pct": round((float(s["open"]) - float(s["previousClose"])) / float(s["previousClose"]) * 100, 2),
                })
            except (KeyError, ValueError):
                continue
        return result

    def get_top_gainers(self, n=5):
        return sorted(self.get_nifty50_stocks(), key=lambda x: x["pChange"], reverse=True)[:n]

    def get_top_losers(self, n=5):
        return sorted(self.get_nifty50_stocks(), key=lambda x: x["pChange"])[:n]

    def get_top_gap_ups(self, n=5):
        return sorted(self.get_nifty50_stocks(), key=lambda x: x["gap_pct"], reverse=True)[:n]

    def get_top_gap_downs(self, n=5):
        return sorted(self.get_nifty50_stocks(), key=lambda x: x["gap_pct"])[:n]

    def get_premarket_summary(self) -> dict:
        stocks  = self.get_nifty50_stocks()
        nifty   = self.get_nifty50()
        bnifty  = self.get_banknifty()
        vix     = self.get_india_vix()
        nifty_pct = float(nifty.get("percentChange", 0))
        regime = "BULLISH" if nifty_pct > 1.0 else "BEARISH" if nifty_pct < -1.0 else "NEUTRAL"
        scored = []
        for s in stocks:
            sc = 0
            if s["pChange"] > 0:    sc += 1
            if s["gap_pct"] > 0:    sc += 1
            if s["pChange"] > 1:    sc += 1
            if s["gap_pct"] > 0.5:  sc += 1
            if s["pChange"] > 1.5:      mom = "Strong Bullish"
            elif s["pChange"] > 0.3:    mom = "Bullish"
            elif s["pChange"] < -1.5:   mom = "Strong Bearish"
            elif s["pChange"] < -0.3:   mom = "Bearish"
            else:                       mom = "Neutral"
            scored.append({**s, "momentum": mom, "score": sc})
        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "indices": {
                "nifty50":   {"price": nifty.get("last", 0),  "change": nifty.get("percentChange", 0)},
                "banknifty": {"price": bnifty.get("last", 0), "change": bnifty.get("percentChange", 0)},
                "vix":       {"price": vix.get("last", 0),    "change": vix.get("percentChange", 0)},
            },
            "regime": regime,
            "nifty_pct": nifty_pct,
            "gap_ups":   sorted(scored, key=lambda x: x["gap_pct"],  reverse=True)[:5],
            "gap_downs": sorted(scored, key=lambda x: x["gap_pct"])[:5],
            "movers":    sorted(scored, key=lambda x: abs(x["pChange"]), reverse=True)[:15],
        }

nse = NSELive()
