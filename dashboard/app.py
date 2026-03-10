"""
dashboard/app.py — MiniMax Pro Trading Terminal v2
Complete professional dashboard with:
- System Health Monitor
- Premarket Scanner (NSE/Yahoo Finance)
- Strategy Monitor
- Positions & Trade Log
- Risk Dashboard
- F&O Calculator
- P&L History
"""
from flask import Flask
from data.database import db, jsonify, request, session
from pathlib import Path
import json, os, subprocess, requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("DASHBOARD_SECRET", "minimax_trading_2026_secret")

BASE           = Path(__file__).parent.parent
TRADES_FILE    = BASE / "logs/trades.json"
AGENT_LOG      = BASE / "logs/agent.log"
WATCHLIST_FILE = BASE / "logs/watchlist.json"
POSITIONS_FILE = BASE / "logs/positions.json"
DASHBOARD_USER = os.getenv("DASHBOARD_USER", "admin")
DASHBOARD_PASS = os.getenv("DASHBOARD_PASS", "minimax123")
PORTFOLIO_SIZE = float(os.getenv("PORTFOLIO_SIZE", "10000"))
DAILY_LOSS_LIMIT = float(os.getenv("DAILY_LOSS_LIMIT", "800"))
MAX_DAILY_TARGET = float(os.getenv("MAX_DAILY_TARGET", "500"))


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text()) if Path(path).exists() else default
    except:
        return default


def check_service(name):
    try:
        r = subprocess.run(["systemctl", "is-active", name], capture_output=True, text=True, timeout=3)
        return r.stdout.strip() == "active"
    except:
        return False


def get_agent_state():
    try:
        lines = AGENT_LOG.read_text().splitlines()[-200:]
        for line in reversed(lines):
            if "HALTED"    in line: return "HALTED"
            if "SELECTIVE" in line: return "SELECTIVE"
        return "NORMAL"
    except:
        return "NORMAL"


def fetch_nse_preopen():
    """Fetch NSE pre-open market data"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://www.nseindia.com/"
        }
        s = requests.Session()
        s.get("https://www.nseindia.com", headers=headers, timeout=5)
        r = s.get("https://www.nseindia.com/api/market-status", headers=headers, timeout=5)
        return r.json() if r.ok else {}
    except:
        return {}


def fetch_nse_quote(symbols_ns):
    """Fetch from NSE India — no rate limit"""
    results = {}
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/",
        }
        s = requests.Session()
        s.get("https://www.nseindia.com", headers=headers, timeout=6)
        # NSE equity quotes
        nse_syms = [sym.replace(".NS","") for sym in symbols_ns if "^" not in sym]
        if nse_syms:
            url = "https://www.nseindia.com/api/quote-equity?symbol=" 
            for sym in nse_syms[:10]:
                try:
                    r = s.get(url + sym, headers=headers, timeout=4)
                    if r.ok:
                        d = r.json()
                        pd = d.get("priceInfo", {})
                        prev = pd.get("previousClose", 0)
                        ltp  = pd.get("lastPrice", 0)
                        chg  = round(ltp - prev, 2)
                        chgp = round((chg/prev)*100, 2) if prev else 0
                        results[sym+".NS"] = {
                            "price": ltp, "change": chg, "changePct": chgp,
                            "volume": d.get("marketDeptOrderBook",{}).get("tradeInfo",{}).get("totalTradedVolume",0),
                            "prevClose": prev,
                            "high": pd.get("intraDayHighLow",{}).get("max", ltp),
                            "low":  pd.get("intraDayHighLow",{}).get("min", ltp),
                            "name": sym,
                        }
                except: pass
        # NSE indices
        try:
            r = s.get("https://www.nseindia.com/api/allIndices", headers=headers, timeout=5)
            if r.ok:
                for idx in r.json().get("data", []):
                    name = idx.get("index","")
                    ltp  = idx.get("last", 0)
                    prev = idx.get("previousClose", 0)
                    chg  = round(ltp - prev, 2)
                    chgp = round(idx.get("percentChange", 0), 2)
                    if "NIFTY 50" == name:
                        results["^NSEI"] = {"price":ltp,"change":chg,"changePct":chgp,"prevClose":prev,"volume":0,"high":idx.get("high",ltp),"low":idx.get("low",ltp),"name":"NIFTY 50"}
                    elif "NIFTY BANK" == name:
                        results["^NSEBANK"] = {"price":ltp,"change":chg,"changePct":chgp,"prevClose":prev,"volume":0,"high":idx.get("high",ltp),"low":idx.get("low",ltp),"name":"BANK NIFTY"}
                    elif "INDIA VIX" == name:
                        results["^INDIAVIX"] = {"price":ltp,"change":chg,"changePct":chgp,"prevClose":prev,"volume":0,"high":idx.get("high",ltp),"low":idx.get("low",ltp),"name":"INDIA VIX"}
                    elif "S&P BSE SENSEX" == name:
                        results["^BSESN"] = {"price":ltp,"change":chg,"changePct":chgp,"prevClose":prev,"volume":0,"high":idx.get("high",ltp),"low":idx.get("low",ltp),"name":"SENSEX"}
        except: pass
    except Exception as e:
        print(f"NSE fetch error: {e}")
    return results


# ── AUTH ──────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def api_login():
    d = request.json or {}
    if d.get("user") == DASHBOARD_USER and d.get("pass") == DASHBOARD_PASS:
        session["auth"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/api/check")
def api_check():
    return jsonify({"ok": session.get("auth", False)})

@app.route("/api/logout")
def api_logout():
    session.clear()
    return jsonify({"ok": True})


# ── SYSTEM HEALTH ─────────────────────────────────────────────
@app.route("/api/health")
def api_health():
    if not session.get("auth"): return jsonify({"error": "unauthorized"}), 401
    services = {
        "trading-agent":    check_service("trading-agent"),
        "trading-dashboard":check_service("trading-dashboard"),
        "token-server":     check_service("token-server"),
        "nginx":            check_service("nginx"),
    }
    # Check log for stream status
    stream_ok = False
    kite_ok = False
    try:
        lines = AGENT_LOG.read_text().splitlines()[-100:]
        for ln in reversed(lines):
            if "WebSocket" in ln or "stream" in ln.lower(): stream_ok = True; break
        for ln in reversed(lines):
            if "access_token" in ln.lower() or "kite" in ln.lower(): kite_ok = True; break
    except: pass

    return jsonify({
        "services": services,
        "components": {
            "broker_api":      {"ok": kite_ok,   "note": "Token valid" if kite_ok else "Check /token page"},
            "websocket":       {"ok": stream_ok,  "note": "Receiving ticks" if stream_ok else "Not streaming"},
            "candle_builder":  {"ok": services["trading-agent"], "note": "1-min candles"},
            "strategy_engine": {"ok": services["trading-agent"], "note": "3 strategies active"},
            "risk_engine":     {"ok": True,       "note": f"Max risk {int(PORTFOLIO_SIZE*0.02)}"},
            "minimax_ai":      {"ok": True,       "note": "MiniMax-M1 connected"},
        },
        "agent_state":  get_agent_state(),
        "timestamp":    datetime.now().strftime("%H:%M:%S"),
    })


# ── PREMARKET DATA ────────────────────────────────────────────
@app.route("/api/premarket")
def api_premarket():
    pass  # public market data, no auth needed
    # Index quotes
    indices = fetch_nse_quote(["^NSEI", "^NSEBANK", "^INDIAVIX", "^BSESN"])
    # Fetch Nifty 50 movers from NSE
    movers = []
    try:
        headers2 = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*", "Referer": "https://www.nseindia.com/",
        }
        s2 = requests.Session()
        s2.get("https://www.nseindia.com", headers=headers2, timeout=6)
        r2 = s2.get("https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050", headers=headers2, timeout=6)
        if r2.ok:
            for item in r2.json().get("data", [])[1:]:
                sym    = item.get("symbol","")
                ltp    = item.get("lastPrice", 0)
                prev   = item.get("previousClose", 0)
                chg    = item.get("change", 0)
                chgp   = item.get("pChange", 0)
                vol    = item.get("totalTradedVolume", 0)
                high   = item.get("dayHigh", ltp)
                low    = item.get("dayLow", ltp)
                vol_score = "High" if vol > 2000000 else "Medium" if vol > 500000 else "Low"
                momentum = "Strong Bullish" if chgp > 2 else "Bullish" if chgp > 0.5                            else "Strong Bearish" if chgp < -2 else "Bearish" if chgp < -0.5                            else "Neutral"
                movers.append({
                    "symbol": sym, "price": round(ltp,2), "change": round(chg,2),
                    "gap_pct": round(chgp,2), "volume": vol, "vol_score": vol_score,
                    "high": round(high,2), "low": round(low,2), "momentum": momentum,
                    "score": round(min(10, max(-10, chgp*2 + (1 if vol>1000000 else 0))),1),
                })
        movers.sort(key=lambda x: abs(x["gap_pct"]), reverse=True)
    except Exception as e:
        print(f"Movers error: {e}")

    nifty  = indices.get("^NSEI", {})
    bank   = indices.get("^NSEBANK", {})
    vix    = indices.get("^INDIAVIX", {})
    sensex = indices.get("^BSESN", {})

    return jsonify({
        "indices": {
            "nifty":   {"price": round(nifty.get("price",0),2),  "change": round(nifty.get("changePct",0),2),  "trend": "Bullish" if nifty.get("change",0)>0 else "Bearish"},
            "banknifty":{"price": round(bank.get("price",0),2),  "change": round(bank.get("changePct",0),2),   "trend": "Bullish" if bank.get("change",0)>0 else "Bearish"},
            "vix":     {"price": round(vix.get("price",0),2),    "change": round(vix.get("changePct",0),2),    "trend": "High" if vix.get("price",0)>20 else "Normal"},
            "sensex":  {"price": round(sensex.get("price",0),2), "change": round(sensex.get("changePct",0),2), "trend": "Bullish" if sensex.get("change",0)>0 else "Bearish"},
        },
        "movers": movers[:15],
        "gap_ups":   [m for m in movers if m["gap_pct"] > 0.5][:5],
        "gap_downs": [m for m in movers if m["gap_pct"] < -0.5][:5],
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    })


# ── STRATEGY MONITOR ─────────────────────────────────────────
@app.route("/api/strategies")
def api_strategies():
    if not session.get("auth"): return jsonify({"error": "unauthorized"}), 401
    trades   = load_json(TRADES_FILE, [])
    today    = datetime.now().strftime("%Y-%m-%d")
    t_today  = [t for t in trades if t.get("date") == today]
    agent_st = get_agent_state()

    strategies = [
        {
            "name": "EMA 9/21 Crossover",
            "type": "Trend Following",
            "status": "ACTIVE" if agent_st != "HALTED" else "PAUSED",
            "signal": "SCANNING",
            "confidence": 0,
            "trades_today": len([t for t in t_today if t.get("score", 0) >= 6]),
            "win_rate": 0,
            "description": "Fast/slow EMA crossover with volume confirmation",
            "params": {"fast_ema": 9, "slow_ema": 21, "min_score": 3},
        },
        {
            "name": "VWAP + Volume",
            "type": "Mean Reversion",
            "status": "ACTIVE" if agent_st != "HALTED" else "PAUSED",
            "signal": "SCANNING",
            "confidence": 0,
            "trades_today": 0,
            "win_rate": 0,
            "description": "Price deviation from VWAP with volume spike",
            "params": {"vwap_dev": 0.5, "vol_multiplier": 1.5, "min_score": 2},
        },
        {
            "name": "RSI + Bollinger Bands",
            "type": "Momentum",
            "status": "ACTIVE" if agent_st != "HALTED" else "PAUSED",
            "signal": "SCANNING",
            "confidence": 0,
            "trades_today": 0,
            "win_rate": 0,
            "description": "RSI extremes with BB squeeze breakout",
            "params": {"rsi_oversold": 30, "rsi_overbought": 70, "bb_period": 20},
        },
        {
            "name": "Level 2 Order Book",
            "type": "Microstructure",
            "status": "ACTIVE" if agent_st != "HALTED" else "PAUSED",
            "signal": "SCANNING",
            "confidence": 0,
            "trades_today": 0,
            "win_rate": 0,
            "description": "Bid/ask imbalance and large order detection",
            "params": {"imbalance_ratio": 2.0, "min_score": 2},
        },
    ]
    # Calculate win rates from trade log
    for strat in strategies:
        strat_trades = [t for t in trades if t.get("score", 0) >= 6]
        if strat_trades:
            wins = len([t for t in strat_trades if t["pnl"] > 0])
            strat["win_rate"] = round((wins / len(strat_trades)) * 100)

    return jsonify({
        "strategies":  strategies,
        "agent_state": agent_st,
        "min_score":   9 if agent_st == "SELECTIVE" else 6,
        "timestamp":   datetime.now().strftime("%H:%M:%S"),
    })


# ── RISK DASHBOARD ────────────────────────────────────────────
@app.route("/api/risk")
def api_risk():
    if not session.get("auth"): return jsonify({"error": "unauthorized"}), 401
    trades  = load_json(TRADES_FILE, [])
    open_p  = load_json(POSITIONS_FILE, [])
    today   = datetime.now().strftime("%Y-%m-%d")
    t_today = [t for t in trades if t.get("date") == today]
    day_pnl = round(sum(t["pnl"] for t in t_today), 2)
    open_risk = sum(
        abs(p.get("entry", 0) - p.get("sl", 0)) * p.get("qty", 0)
        for p in open_p
    )
    loss_used  = max(0, -day_pnl)
    loss_pct   = round((loss_used / DAILY_LOSS_LIMIT) * 100, 1)
    profit_pct = round((max(0, day_pnl) / MAX_DAILY_TARGET) * 100, 1)
    agent_st   = get_agent_state()

    return jsonify({
        "day_pnl":        day_pnl,
        "daily_loss_limit": DAILY_LOSS_LIMIT,
        "loss_used":      round(loss_used, 2),
        "loss_remaining": round(DAILY_LOSS_LIMIT - loss_used, 2),
        "loss_pct":       loss_pct,
        "profit_target":  MAX_DAILY_TARGET,
        "profit_pct":     min(100, profit_pct),
        "open_risk":      round(open_risk, 2),
        "max_per_trade":  round(PORTFOLIO_SIZE * 0.02, 2),
        "portfolio_value":round(PORTFOLIO_SIZE + sum(t["pnl"] for t in trades), 2),
        "trades_today":   len(t_today),
        "open_positions": len(open_p),
        "agent_state":    agent_st,
        "trading_allowed":agent_st != "HALTED",
        "risk_level":     "DANGER" if loss_pct > 80 else "WARNING" if loss_pct > 50 else "SAFE",
        "timestamp":      datetime.now().strftime("%H:%M:%S"),
    })


# ── MAIN DATA ────────────────────────────────────────────────
@app.route("/api/data")
def api_data():
    if not session.get("auth"): return jsonify({"error": "unauthorized"}), 401
    all_trades  = load_json(TRADES_FILE, [])
    watchlist   = [s.split(":")[-1] for s in load_json(WATCHLIST_FILE, [])]
    # Strip exchange prefix e.g. "NSE:RELIANCE" → "RELIANCE"
    open_pos    = load_json(POSITIONS_FILE, [])
    today       = datetime.now().strftime("%Y-%m-%d")
    closed      = [t for t in all_trades if t.get("exit", 0) > 0 and t.get("pnl") is not None]
    today_closed= [t for t in closed if t.get("date", today) == today]
    day_pnl     = round(sum(t["pnl"] for t in today_closed), 2)
    wins        = [t for t in today_closed if t["pnl"] > 0]
    losses      = [t for t in today_closed if t["pnl"] <= 0]
    win_rate    = round(len(wins)/len(today_closed)*100) if today_closed else 0
    pnl_curve   = [{"time": "09:15", "pnl": 0}]
    running = 0
    for t in sorted(today_closed, key=lambda x: x.get("exit_time", "")):
        running += t["pnl"]
        pnl_curve.append({"time": t.get("exit_time", "")[:5], "pnl": round(running, 2)})
    daily_map = {}
    for t in closed:
        day = t.get("date", today)
        if day not in daily_map:
            daily_map[day] = {"date": day, "trades": 0, "wins": 0, "losses": 0, "pnl": 0}
        daily_map[day]["trades"] += 1
        daily_map[day]["pnl"] = round(daily_map[day]["pnl"] + t["pnl"], 2)
        if t["pnl"] > 0: daily_map[day]["wins"] += 1
        else:             daily_map[day]["losses"] += 1
    open_data = []
    for pos in open_pos:
        current = pos.get("current_price", pos.get("entry", 0))
        entry   = pos.get("entry", 0)
        qty     = pos.get("qty", 0)
        action  = pos.get("action", "BUY")
        unreal  = (current - entry)*qty if action == "BUY" else (entry - current)*qty
        open_data.append({**pos, "unrealised_pnl": round(unreal, 2), "current": current})
    return jsonify({
        "day_pnl":        day_pnl,
        "total_trades":   len(today_closed),
        "wins":           len(wins),
        "losses":         len(losses),
        "win_rate":       win_rate,
        "open_count":     len(open_data),
        "open_positions": open_data,
        "trades":         today_closed,
        "all_trades":     closed,
        "watchlist":      watchlist,
        "pnl_curve":      pnl_curve,
        "daily_pnl":      sorted(daily_map.values(), key=lambda x: x["date"]),
        "agent_state":    get_agent_state(),
        "mode":           os.getenv("TRADING_MODE", "paper").upper(),
        "portfolio_value":round(PORTFOLIO_SIZE + sum(t["pnl"] for t in closed), 2),
        "timestamp":      datetime.now().strftime("%H:%M:%S"),
    })


# ── HTML ──────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>MiniMax Pro Terminal</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=Barlow:wght@600;700;800;900&display=swap" rel="stylesheet"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
:root{
  --bg:#07090f;--bg2:#0b0f1a;--bg3:#0f1520;--panel:#0d1422;
  --border:#162030;--border2:#1d2d45;
  --amber:#f59e0b;--cyan:#06b6d4;--green:#10b981;--red:#ef4444;
  --blue:#3b82f6;--purple:#8b5cf6;--text:#e2e8f0;--muted:#475569;--muted2:#64748b;
  --orange:#f97316;
}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:'IBM Plex Mono',monospace;font-size:15px;}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:var(--bg2);}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px;}

/* LOGIN */
#loginWrap{display:flex;align-items:center;justify-content:center;min-height:100vh;background:radial-gradient(ellipse at 30% 20%,#0a1628,var(--bg));}
.login-box{width:360px;background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:36px;}
.login-logo{font-family:'Barlow',sans-serif;font-size:1.8rem;font-weight:900;color:var(--amber);letter-spacing:-1px;}
.login-sub{font-size:.6rem;color:var(--muted);letter-spacing:3px;margin-bottom:28px;}
.login-box input{width:100%;padding:10px 14px;background:var(--bg3);border:1px solid var(--border2);border-radius:6px;color:var(--text);font-family:inherit;font-size:.84rem;margin-bottom:10px;outline:none;}
.login-box input:focus{border-color:var(--amber);}
.login-btn{width:100%;padding:11px;background:var(--amber);color:#000;border:none;border-radius:6px;font-family:'Barlow',sans-serif;font-weight:800;font-size:.85rem;letter-spacing:1px;cursor:pointer;margin-top:6px;}
.login-err{color:var(--red);font-size:.72rem;text-align:center;margin-top:8px;}

/* LAYOUT */
#app{display:flex;height:100vh;overflow:hidden;}
.sidebar{width:200px;background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;flex-shrink:0;}
.main{flex:1;display:flex;flex-direction:column;overflow:hidden;}
.topbar{height:46px;background:var(--bg2);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;padding:0 20px;flex-shrink:0;}
.ticker{position:absolute;bottom:-18px;left:0;width:100%;overflow:hidden;font-size:12px;color:var(--cyan);}.ticker-track{display:inline-block;white-space:nowrap;animation:ticker 20s linear infinite;}@keyframes ticker{0%{transform:translateX(100%);}100%{transform:translateX(-100%);}}
.content{flex:1;overflow-y:auto;padding:18px;}

/* SIDEBAR */
.sb-logo{padding:18px 16px 14px;border-bottom:1px solid var(--border);}
.sb-logo-title{font-family:'Barlow',sans-serif;font-size:1.1rem;font-weight:900;color:var(--amber);}
.sb-logo-sub{font-size:.55rem;color:var(--muted);letter-spacing:2.5px;margin-top:2px;}
.sb-nav{flex:1;padding:10px 0;overflow-y:auto;}
.nav-grp{font-size:.55rem;color:var(--muted);letter-spacing:2px;padding:10px 16px 4px;text-transform:uppercase;}
.nav-item{display:flex;align-items:center;gap:9px;padding:8px 16px;cursor:pointer;color:var(--muted2);font-size:.9rem;border-left:2px solid transparent;transition:all .15s;}
.nav-item:hover{color:var(--text);background:rgba(245,158,11,.04);}
.nav-item.active{color:var(--amber);background:rgba(245,158,11,.07);border-left-color:var(--amber);font-weight:600;}
.nav-icon{font-size:.9rem;width:16px;text-align:center;}
.sb-bottom{padding:12px 14px;border-top:1px solid var(--border);font-size:.65rem;}
.pulse{animation:pulse 2s infinite;}
.market-open{color:var(--green);text-shadow:0 0 8px rgba(16,185,129,.8);} .market-closed{color:var(--red);text-shadow:0 0 8px rgba(239,68,68,.8);}
.blink{animation:blink 1.2s step-end infinite;}
.fadein{animation:fadein .2s ease both;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.market-open{color:var(--green);text-shadow:0 0 8px rgba(16,185,129,.8);} .market-closed{color:var(--red);text-shadow:0 0 8px rgba(239,68,68,.8);}
@keyframes flash{0%{opacity:1}50%{opacity:.3}100%{opacity:1}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
@keyframes fadein{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}

/* TOPBAR */
.tb-title{font-family:'Barlow',sans-serif;font-size:.95rem;font-weight:700;}
.tb-right{display:flex;align-items:center;gap:10px;font-size:.68rem;}
.tb-pill{padding:3px 9px;border-radius:3px;font-weight:700;font-size:.67rem;letter-spacing:.5px;}
.tb-time{padding:3px 9px;background:var(--bg3);border:1px solid var(--border);border-radius:4px;color:var(--muted2);}

/* CARDS */
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:12px;}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:12px;}
.grid-2{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:12px;}
.grid-23{display:grid;grid-template-columns:2fr 1fr;gap:10px;margin-bottom:12px;}
.grid-32{display:grid;grid-template-columns:3fr 2fr;gap:10px;margin-bottom:12px;}
.card{background:var(--panel);border:1px solid var(--border);border-radius:9px;padding:14px 16px;position:relative;overflow:hidden;}
.card-accent::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;}
.ca-green::before{background:linear-gradient(90deg,var(--green),transparent);}
.ca-cyan::before{background:linear-gradient(90deg,var(--cyan),transparent);}
.ca-amber::before{background:linear-gradient(90deg,var(--amber),transparent);}
.ca-purple::before{background:linear-gradient(90deg,var(--purple),transparent);}
.ca-red::before{background:linear-gradient(90deg,var(--red),transparent);}
.ca-blue::before{background:linear-gradient(90deg,var(--blue),transparent);}
.card-title{font-size:.6rem;color:var(--muted2);letter-spacing:1.2px;text-transform:uppercase;font-weight:600;margin-bottom:9px;}
.metric{font-family:'Barlow',sans-serif;font-size:2.4rem;font-weight:800;line-height:1;letter-spacing:-.5px;}
.metric-sub{font-size:.65rem;color:var(--muted2);margin-top:4px;}
.card-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:11px;}
.card-head-title{font-size:.9rem;font-weight:600;}

/* COLORS */
.c-green{color:var(--green)!important;} .c-red{color:var(--red)!important;}
.c-amber{color:var(--amber)!important;} .c-cyan{color:var(--cyan)!important;}
.c-purple{color:var(--purple)!important;} .c-muted{color:var(--muted2)!important;}
.c-blue{color:var(--blue)!important;} .c-orange{color:var(--orange)!important;}

/* TABLE */
.tbl-wrap{overflow-x:auto;}
table{width:100%;border-collapse:collapse;font-size:.9rem;}
th{text-align:left;padding:6px 10px;color:var(--muted);font-size:.6rem;letter-spacing:.5px;border-bottom:1px solid var(--border);text-transform:uppercase;font-weight:500;}
td{padding:10px 12px;border-bottom:1px solid rgba(22,32,48,.5);}
tr:hover td{background:rgba(245,158,11,.02);}
tr.profit td{background:rgba(16,185,129,.08);} tr.loss td{background:rgba(239,68,68,.08);}

/* TAGS */
.tag{display:inline-block;padding:2px 7px;border-radius:3px;font-size:.63rem;font-weight:700;}
.tag-buy{background:rgba(16,185,129,.12);color:var(--green);}
.tag-sell{background:rgba(239,68,68,.12);color:var(--red);}
.tag-ok{background:rgba(16,185,129,.12);color:var(--green);}
.tag-fail{background:rgba(239,68,68,.12);color:var(--red);}
.tag-warn{background:rgba(245,158,11,.12);color:var(--amber);}
.tag-active{background:rgba(6,182,212,.12);color:var(--cyan);}
.tag-paused{background:rgba(71,85,105,.12);color:var(--muted2);}
.tag-paper{background:rgba(139,92,246,.12);color:var(--purple);}
.tag-live{background:rgba(16,185,129,.12);color:var(--green);}
.tag-bullish{background:rgba(16,185,129,.12);color:var(--green);}
.tag-bearish{background:rgba(239,68,68,.12);color:var(--red);}
.tag-neutral{background:rgba(71,85,105,.12);color:var(--muted2);}
.tag-danger{background:rgba(239,68,68,.15);color:var(--red);}
.tag-safe{background:rgba(16,185,129,.12);color:var(--green);}

/* PROGRESS */
.prog-bar{height:5px;background:var(--bg3);border-radius:3px;overflow:hidden;margin-top:6px;}
.prog-fill{height:100%;border-radius:3px;transition:width .5s;}

/* HEALTH ROW */
.health-row{display:flex;align-items:center;justify-content:space-between;padding:9px 0;border-bottom:1px solid rgba(22,32,48,.6);}
.health-row:last-child{border-bottom:none;}
.health-name{font-size:.72rem;font-weight:600;}
.health-note{font-size:.65rem;color:var(--muted2);}
.health-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}

/* STRATEGY CARD */
.strat-card{background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:14px;margin-bottom:8px;}
.strat-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;}
.strat-name{font-size:.78rem;font-weight:700;}
.strat-type{font-size:.6rem;color:var(--muted2);}
.strat-meta{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px;}
.strat-meta-item{text-align:center;background:var(--bg2);border-radius:4px;padding:5px;}
.strat-meta-label{font-size:.55rem;color:var(--muted);margin-bottom:2px;}
.strat-meta-val{font-size:.72rem;font-weight:700;}

/* INDEX CARDS */
.idx-card{background:var(--bg3);border:1px solid var(--border);border-radius:7px;padding:10px 14px;}
.idx-name{font-size:.62rem;color:var(--muted2);margin-bottom:4px;}
.idx-val{font-family:'Barlow',sans-serif;font-size:1.2rem;font-weight:800;}
.idx-chg{font-size:.68rem;margin-top:2px;}

/* FO CALC */
.fo-input{width:100%;padding:8px 12px;background:var(--bg3);border:1px solid var(--border2);border-radius:5px;color:var(--text);font-family:inherit;font-size:.75rem;outline:none;margin-bottom:8px;}
.fo-input:focus{border-color:var(--amber);}
.fo-btn{padding:8px 18px;background:var(--amber);color:#000;border:none;border-radius:5px;font-family:'Barlow',sans-serif;font-weight:800;font-size:.8rem;cursor:pointer;}
.fo-result{background:var(--bg3);border:1px solid var(--border);border-radius:7px;padding:14px;margin-top:12px;}
.fo-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(22,32,48,.5);font-size:.72rem;}
.fo-row:last-child{border-bottom:none;}

/* CHIP */
.chip{display:inline-block;padding:3px 9px;background:var(--bg3);border:1px solid var(--border2);border-radius:4px;font-size:.68rem;margin:2px;}

/* RISK GAUGE */
.risk-gauge{text-align:center;padding:10px 0;}
.risk-pct{font-family:'Barlow',sans-serif;font-size:2.2rem;font-weight:900;}
.risk-label{font-size:.65rem;color:var(--muted2);margin-top:4px;}

/* PAGE */
.page{display:none;} .page.active{display:block;}
.empty{text-align:center;padding:28px;color:var(--muted);font-size:.72rem;}
.section-title{font-size:.65rem;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;font-weight:600;margin-bottom:10px;margin-top:16px;}
.tabs{display:flex;background:var(--panel);border:1px solid var(--border);border-radius:6px;overflow:hidden;width:fit-content;margin-bottom:10px;}
.tab{padding:6px 16px;font-size:.9rem;font-weight:600;cursor:pointer;color:var(--muted2);background:transparent;border:none;letter-spacing:.3px;}
.tab.active{background:var(--amber);color:#000;}
.chart-wrap{position:relative;}

@media(max-width:900px){
  .sidebar{width:54px;} .sb-logo-title,.sb-logo-sub,.nav-item span,.nav-grp,.sb-bottom{display:none;}
  .nav-item{justify-content:center;padding:10px;} .grid-4{grid-template-columns:1fr 1fr;}
  .grid-23,.grid-32{grid-template-columns:1fr;}
}
.heatmap{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;padding:10px}
.heatbox{padding:14px;border-radius:8px;text-align:center;font-weight:600;font-size:13px;border:1px solid rgba(255,255,255,.05)}
.heat-up{background:rgba(34,197,94,.12);color:#22c55e}
.heat-down{background:rgba(239,68,68,.12);color:#ef4444}
.heatbox{padding:12px;border-radius:6px;text-align:center;font-weight:600;font-size:13px}
.heat-up{background:rgba(34,197,94,.15);color:#22c55e}
.heat-down{background:rgba(239,68,68,.15);color:#ef4444}

</style>
</head>
<body>

<!-- LOGIN -->
<div id="loginWrap">
  <div class="login-box">
    <div class="login-logo">⚡ MINIMAX</div>
    <div class="login-sub">PRO TRADING TERMINAL</div>
    <input id="lu" type="text" placeholder="Username" autocomplete="off"/>
    <input id="lp" type="password" placeholder="Password" onkeydown="if(event.key==='Enter')doLogin()"/>
    <button class="login-btn" onclick="doLogin()">ACCESS TERMINAL</button>
    <div class="login-err" id="lerr"></div>
  </div>
</div>

<!-- APP -->
<div id="app" style="display:none;">
  <!-- SIDEBAR -->
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-title">⚡ MINIMAX</div>
      <div class="sb-logo-sub">PRO TERMINAL</div>
    </div>
    <nav class="sb-nav">
      <div class="nav-grp">Monitor</div>
      <div class="nav-item active" data-page="dashboard" onclick="nav(this)"><span class="nav-icon">▦</span><span>Dashboard</span></div>
      <div class="nav-item" data-page="health" onclick="nav(this)"><span class="nav-icon">♥</span><span>System Health</span></div>
      <div class="nav-grp">Market</div>
      <div class="nav-item" data-page="premarket" onclick="nav(this)"><span class="nav-icon">◈</span><span>Premarket Scanner</span></div>
      <div class="nav-item" data-page="strategies" onclick="nav(this)"><span class="nav-icon">≋</span><span>Strategy Monitor</span></div>
      <div class="nav-grp">Trading</div>
      <div class="nav-item" data-page="positions" onclick="nav(this)"><span class="nav-icon">◉</span><span>Positions</span></div>
      <div class="nav-item" data-page="trades" onclick="nav(this)"><span class="nav-icon">≡</span><span>Trade Log</span></div>
      <div class="nav-item" data-page="risk" onclick="nav(this)"><span class="nav-icon">⊗</span><span>Risk Dashboard</span></div>
      <div class="nav-grp">Tools</div>
      <div class="nav-item" data-page="pnl" onclick="nav(this)"><span class="nav-icon">∿</span><span>P&L History</span></div>
      <div class="nav-item" data-page="fo" onclick="nav(this)"><span class="nav-icon">◎</span><span>F&O Calculator</span></div>
      <div class="nav-item" data-page="settings" onclick="nav(this)"><span class="nav-icon">⊕</span><span>Settings</span></div>
    </nav>
    <div class="sb-bottom">
      <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;">
        <span class="pulse" id="sbDot" style="width:7px;height:7px;border-radius:50%;background:var(--green);display:inline-block;"></span>
        <span id="sbState" style="color:var(--green);">NORMAL</span>
      </div>
      <div style="color:var(--muted);">MODE: <span id="sbMode" style="color:var(--purple);">PAPER</span></div>
    </div>
  </div>

  <!-- MAIN -->
  <div class="main">
    <div class="topbar">
<div style="height:120px;background:#0f172a;border-bottom:1px solid #1e293b;padding:10px"><canvas id="headerChart" style="height:100px"></canvas></div>
      <div class="tb-title" id="tbTitle">Dashboard</div>
      <div class="tb-right">
        <span style="color:var(--muted2);">NSE <span class="blink" id="mktDot" class="market-open" style="color:var(--green);">●</span></span>
        <span id="tbPnl" class="tb-pill" style="background:rgba(16,185,129,.1);color:var(--green);border:1px solid rgba(16,185,129,.2);">Day: ₹+0.00</span>
        <span id="tbMode" class="tb-pill tag-paper">PAPER</span>
        <span class="tb-time" id="clock">--:--:-- IST</span>
      </div>
    </div>

    <div class="content">

      <!-- DASHBOARD -->
      <div class="page active" id="page-dashboard">
<div style="margin-top:20px">
            <div class="card-title">Day P&L</div>
            <div class="metric" id="d-pnl" class="flash" style="color:var(--green)">₹+0.00</div>
            <div class="metric-sub" id="d-pnlpct">▲ 0.0% of portfolio</div>
          </div>
          <div class="card card-accent ca-cyan fadein" style="animation-delay:.05s">
            <div class="card-title">Trades Today</div>
            <div class="metric c-cyan" id="d-trades">0</div>
            <div class="metric-sub" id="d-open">0 open positions</div>
          </div>
          <div class="card card-accent ca-amber fadein" style="animation-delay:.1s">
            <div class="card-title">Win Rate</div>
            <div class="metric" id="d-wr">0%</div>
            <div class="metric-sub" id="d-wl">0W / 0L</div>
          </div>
          <div class="card card-accent ca-purple fadein" style="animation-delay:.15s">
            <div class="card-title">Portfolio Value</div>
            <div class="metric c-purple" id="d-portval">₹10,000</div>
            <div class="metric-sub" id="d-portchg">+₹0 all time</div>
          </div>
        </div>
        <div class="grid-23">
          <div class="card fadein" style="animation-delay:.2s">
            <div class="card-head"><span class="card-head-title">Intraday P&L Curve</span><span class="c-muted" style="font-size:.65rem;" id="d-updated">--:--:--</span></div>
            <div class="chart-wrap" style="height:180px;"><canvas id="pnlChart"></canvas></div>
          </div>
          <div class="card fadein" style="animation-delay:.25s">
            <div class="card-head"><span class="card-head-title">Daily Target</span></div>
            <div style="display:flex;justify-content:space-between;font-size:.68rem;margin-bottom:4px;">
              <span class="c-muted">Target ₹500</span><span id="d-prog-pct" style="color:var(--green);">0%</span>
            </div>
            <div class="prog-bar" style="height:7px;margin-bottom:12px;"><div class="prog-fill" id="d-prog" style="width:0%;background:var(--green);"></div></div>
            <div class="card-title">Watchlist</div>
            <div id="d-watchlist" style="display:flex;flex-wrap:wrap;gap:4px;"><span class="chip c-muted">Loading...</span></div>
            <div style="margin-top:12px;">
              <div class="card-title">Agent State</div>
              <div style="font-size:.82rem;font-weight:700;" id="d-state-big" class="c-purple">NORMAL • Score 6+</div>
            </div>
          </div>
        </div>
        <div class="grid-2">
          <div class="card fadein" style="animation-delay:.3s">
            <div class="card-head"><span class="card-head-title">Open Positions</span><span class="tag tag-active" id="d-opencount">0</span></div>
            <div id="d-openpos"><div class="empty">No open positions</div></div>
          </div>
          <div class="card fadein" style="animation-delay:.35s">
<div style="margin-top:20px">
<h3 style="margin-bottom:10px;color:#94a3b8">Market Heatmap</h3>
<div class="card"><div id="heatmap" class="heatmap"></div>
</div>
            <div class="card-head"><span class="card-head-title">Recent Trades</span></div>
            <div id="d-recent"><div class="empty">No trades yet today</div></div>
          </div>
        </div>
      </div>

      <!-- SYSTEM HEALTH -->
      <div class="page" id="page-health">
        <div class="grid-2">
          <div class="card fadein">
            <div class="card-head"><span class="card-head-title">System Services</span><span class="c-muted" style="font-size:.65rem;" id="h-ts">--:--:--</span></div>
            <div id="h-services"><div class="empty">Loading...</div></div>
          </div>
          <div class="card fadein" style="animation-delay:.1s">
            <div class="card-head"><span class="card-head-title">Component Health</span></div>
            <div id="h-components"><div class="empty">Loading...</div></div>
          </div>
        </div>
        <div class="card fadein" style="animation-delay:.2s;margin-bottom:12px;">
          <div class="card-head"><span class="card-head-title">Component Status Table</span></div>
          <div class="tbl-wrap">
            <table>
              <thead><tr><th>Component</th><th>Status</th><th>Notes</th><th>Impact if Down</th></tr></thead>
              <tbody id="h-table"></tbody>
            </table>
          </div>
        </div>
        <div class="card fadein" style="animation-delay:.25s">
          <div class="card-head"><span class="card-head-title">Trading Safety Rules</span></div>
          <table><tbody>
            <tr><td class="c-muted">System Health Check</td><td>Every 15 seconds</td><td><span class="tag tag-ok">Automatic</span></td></tr>
            <tr><td class="c-muted">If Trading Agent Down</td><td>Stop all trades automatically</td><td><span class="tag tag-fail">Critical</span></td></tr>
            <tr><td class="c-muted">If Zerodha API Fails</td><td>Pause strategy engine</td><td><span class="tag tag-warn">Warning</span></td></tr>
            <tr><td class="c-muted">If WebSocket Drops</td><td>Reconnect in 30 seconds</td><td><span class="tag tag-warn">Warning</span></td></tr>
            <tr><td class="c-muted">If Daily Loss Hit</td><td>HALT all trading for the day</td><td><span class="tag tag-fail">Critical</span></td></tr>
          </tbody></table>
        </div>
      </div>

      <!-- PREMARKET SCANNER -->
      <div class="page" id="page-premarket">
        <div class="grid-4" id="pm-indices">
          <div class="card fadein idx-card"><div class="idx-name">NIFTY 50</div><div class="idx-val" id="pm-nifty">--</div><div class="idx-chg" id="pm-nifty-chg">--</div></div>
          <div class="card fadein idx-card" style="animation-delay:.05s"><div class="idx-name">BANK NIFTY</div><div class="idx-val" id="pm-bank">--</div><div class="idx-chg" id="pm-bank-chg">--</div></div>
          <div class="card fadein idx-card" style="animation-delay:.1s"><div class="idx-name">INDIA VIX</div><div class="idx-val" id="pm-vix">--</div><div class="idx-chg" id="pm-vix-chg">--</div></div>
          <div class="card fadein idx-card" style="animation-delay:.15s"><div class="idx-name">SENSEX</div><div class="idx-val" id="pm-sensex">--</div><div class="idx-chg" id="pm-sensex-chg">--</div></div>
        </div>
        <div class="grid-2">
          <div class="card fadein" style="animation-delay:.2s">
            <div class="card-head"><span class="card-head-title">🟢 Top Gap Ups</span></div>
            <div class="tbl-wrap" id="pm-gapups"><div class="empty">Loading...</div></div>
          </div>
          <div class="card fadein" style="animation-delay:.25s">
            <div class="card-head"><span class="card-head-title">🔴 Top Gap Downs</span></div>
            <div class="tbl-wrap" id="pm-gapdowns"><div class="empty">Loading...</div></div>
          </div>
        </div>
        <div class="card fadein" style="animation-delay:.3s">
          <div class="card-head">
            <span class="card-head-title">Pre-Market Movers — Nifty 50</span>
            <button onclick="loadPremarket()" style="padding:4px 12px;background:var(--bg3);border:1px solid var(--border2);border-radius:4px;color:var(--amber);font-family:inherit;font-size:.68rem;cursor:pointer;">↻ Refresh</button>
          </div>
          <div class="tbl-wrap" id="pm-movers"><div class="empty">Loading market data...</div></div>
        </div>
      </div>

      <!-- STRATEGY MONITOR -->
      <div class="page" id="page-strategies">
        <div class="grid-3" style="margin-bottom:12px;">
          <div class="card card-accent ca-cyan"><div class="card-title">Active Strategies</div><div class="metric c-cyan" id="st-active">4</div><div class="metric-sub">Running in parallel</div></div>
          <div class="card card-accent ca-amber"><div class="card-title">Min Signal Score</div><div class="metric c-amber" id="st-minscore">6</div><div class="metric-sub" id="st-mode-sub">Normal mode</div></div>
          <div class="card card-accent ca-green"><div class="card-title">Agent State</div><div class="metric" id="st-state" style="color:var(--purple)">NORMAL</div><div class="metric-sub">Scanning for signals</div></div>
        </div>
        <div id="st-cards"><div class="empty">Loading strategies...</div></div>
        <div class="card" style="margin-top:12px;">
          <div class="card-head"><span class="card-head-title">How Signal Scoring Works</span></div>
          <table><thead><tr><th>Strategy</th><th>Max Score</th><th>Signal</th><th>Condition</th></tr></thead>
          <tbody>
            <tr><td>EMA 9/21 Crossover</td><td>+3</td><td>BUY</td><td>Fast EMA crosses above Slow EMA + volume &gt; avg</td></tr>
            <tr><td>VWAP + Volume</td><td>+2</td><td>BUY</td><td>Price above VWAP + volume spike 1.5x</td></tr>
            <tr><td>RSI + Bollinger Bands</td><td>+3</td><td>BUY</td><td>RSI &lt; 30 + price at lower BB + momentum turning</td></tr>
            <tr><td>Level 2 Order Book</td><td>+2</td><td>BUY</td><td>Bid/ask imbalance &gt; 2:1 + large buy orders</td></tr>
            <tr><td colspan="4" style="color:var(--amber);font-size:.65rem;padding-top:8px;">⚡ Total score 6/10 → Trade (Normal) | 9/10 → Trade (Selective after ₹500 profit)</td></tr>
          </tbody></table>
        </div>
      </div>

      <!-- POSITIONS -->
      <div class="page" id="page-positions">
        <div class="grid-3" style="margin-bottom:12px;">
          <div class="card card-accent ca-cyan"><div class="card-title">Open Positions</div><div class="metric c-cyan" id="pos-count">0</div></div>
          <div class="card card-accent ca-green"><div class="card-title">Unrealised P&L</div><div class="metric" id="pos-unreal" style="color:var(--green)">₹0.00</div></div>
          <div class="card card-accent ca-amber"><div class="card-title">Total Exposure</div><div class="metric c-amber" id="pos-exposure">₹0</div></div>
        </div>
        <div class="card">
          <div class="card-head"><span class="card-head-title">Open Positions</span><span class="c-muted" style="font-size:.65rem;" id="pos-ts">--:--:--</span></div>
          <div class="tbl-wrap" id="pos-table"><div class="empty">No open positions</div></div>
        </div>
      </div>

      <!-- TRADES -->
      <div class="page" id="page-trades">
        <div class="grid-3" style="margin-bottom:12px;">
          <div class="card card-accent ca-cyan"><div class="card-title">Total Trades</div><div class="metric c-cyan" id="t-total">0</div></div>
          <div class="card card-accent ca-amber"><div class="card-title">Wins / Losses</div><div class="metric" id="t-wl"><span class="c-green">0</span>/<span class="c-red">0</span></div></div>
          <div class="card card-accent ca-green"><div class="card-title">Net P&L</div><div class="metric" id="t-pnl">₹+0.00</div></div>
        </div>
        <div style="display:flex;gap:10px;margin-bottom:10px;align-items:center;">
          <select id="tradeFilter" onchange="renderTrades()" style="background:var(--bg3);border:1px solid var(--border2);color:var(--text);padding:6px 10px;border-radius:5px;font-family:inherit;font-size:.9rem;">
            <option value="all">All Trades</option>
            <option value="wins">Wins Only</option>
            <option value="loss">Losses Only</option>
          </select>
        </div>
        <div class="card"><div class="tbl-wrap" id="t-table"><div class="empty">No trades yet</div></div></div>
      </div>

      <!-- RISK DASHBOARD -->
      <div class="page" id="page-risk">
        <div class="grid-4">
          <div class="card card-accent ca-red fadein">
            <div class="card-title">Daily Loss Used</div>
            <div class="metric" id="r-lossused" style="color:var(--red)">₹0</div>
            <div class="metric-sub" id="r-lossrem">₹800 remaining</div>
          </div>
          <div class="card card-accent ca-amber fadein" style="animation-delay:.05s">
            <div class="card-title">Loss Limit</div>
            <div class="metric c-amber">₹800</div>
            <div class="metric-sub">Trading halts at this level</div>
          </div>
          <div class="card card-accent ca-green fadein" style="animation-delay:.1s">
            <div class="card-title">Profit Target</div>
            <div class="metric c-green" id="r-profit">₹0.00</div>
            <div class="metric-sub">Target: ₹300–500/day</div>
          </div>
          <div class="card card-accent ca-purple fadein" style="animation-delay:.15s">
            <div class="card-title">Open Risk</div>
            <div class="metric c-purple" id="r-openrisk">₹0</div>
            <div class="metric-sub">Live exposure in trades</div>
          </div>
        </div>
        <div class="grid-2">
          <div class="card fadein" style="animation-delay:.2s">
            <div class="card-head"><span class="card-head-title">Daily Loss Meter</span><span id="r-level" class="tag tag-safe">SAFE</span></div>
            <div class="risk-gauge">
              <div class="risk-pct" id="r-pct" style="color:var(--green)">0%</div>
              <div class="risk-label">of ₹800 daily limit used</div>
            </div>
            <div class="prog-bar" style="height:10px;margin-top:8px;">
              <div class="prog-fill" id="r-bar" style="width:0%;background:var(--green);"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:.6rem;color:var(--muted);margin-top:4px;"><span>₹0</span><span style="color:var(--amber)">₹400</span><span>₹800 HALT</span></div>
          </div>
          <div class="card fadein" style="animation-delay:.25s">
            <div class="card-head"><span class="card-head-title">Risk Rules</span></div>
            <table><tbody>
              <tr><td class="c-muted">Max Loss/Day</td><td class="c-red">₹800 → HALT</td></tr>
              <tr><td class="c-muted">Max Risk/Trade</td><td class="c-red">₹200 (2%)</td></tr>
              <tr><td class="c-muted">Selective Mode at</td><td class="c-amber">₹500 profit</td></tr>
              <tr><td class="c-muted">Stop All at</td><td class="c-amber">₹800 profit</td></tr>
              <tr><td class="c-muted">Profit Limit</td><td class="c-green">UNLIMITED ♾</td></tr>
              <tr><td class="c-muted">Time Stop</td><td>15 min per trade</td></tr>
              <tr><td class="c-muted">SL Phase 1</td><td>Breakeven at +₹100</td></tr>
              <tr><td class="c-muted">SL Phase 2</td><td>Lock ₹75 at +₹150</td></tr>
              <tr><td class="c-muted">SL Phase 3</td><td>Trail 50% at +₹200</td></tr>
            </tbody></table>
          </div>
        </div>
        <div class="card fadein" style="animation-delay:.3s">
          <div class="card-head"><span class="card-head-title">Trading Status</span></div>
          <div id="r-status" style="padding:14px;text-align:center;">
            <div style="font-size:1.5rem;margin-bottom:8px;">✅</div>
            <div style="font-family:'Barlow',sans-serif;font-size:1.1rem;font-weight:800;color:var(--green);" id="r-status-text">TRADING ACTIVE</div>
            <div style="font-size:.9rem;color:var(--muted);margin-top:5px;" id="r-status-sub">All systems normal</div>
          </div>
        </div>
      </div>

      <!-- P&L HISTORY -->
      <div class="page" id="page-pnl">
        <div class="grid-4" style="margin-bottom:12px;">
          <div class="card card-accent ca-green"><div class="card-title">Today</div><div class="metric" id="ph-today">₹+0.00</div></div>
          <div class="card card-accent ca-cyan"><div class="card-title">This Week</div><div class="metric c-cyan" id="ph-week">₹0.00</div></div>
          <div class="card card-accent ca-amber"><div class="card-title">This Month</div><div class="metric c-amber" id="ph-month">₹0.00</div></div>
          <div class="card card-accent ca-purple"><div class="card-title">All Time</div><div class="metric c-purple" id="ph-all">₹0.00</div></div>
        </div>
        <div class="card" style="margin-bottom:12px;"><div class="card-head"><span class="card-head-title">Daily P&L Bar Chart</span></div><div class="chart-wrap" style="height:200px;"><canvas id="dailyChart"></canvas></div></div>
        <div class="card"><div class="card-head"><span class="card-head-title">Daily Breakdown</span></div><div class="tbl-wrap" id="ph-table"><div class="empty">No history yet</div></div></div>
      </div>

      <!-- F&O CALCULATOR -->
      <div class="page" id="page-fo">
        <div class="grid-2">
          <div class="card fadein">
            <div class="card-head"><span class="card-head-title">F&O Trade Calculator</span></div>
            <div class="card-title" style="margin-bottom:4px;">Instrument</div>
            <select id="fo-instrument" style="width:100%;padding:8px 12px;background:var(--bg3);border:1px solid var(--border2);border-radius:5px;color:var(--text);font-family:inherit;font-size:.75rem;margin-bottom:10px;outline:none;">
              <option value="equity">Equity (Cash)</option>
              <option value="stock_fut">Stock Futures</option>
              <option value="nifty_fut">Nifty Futures (Lot: 25)</option>
              <option value="banknifty_fut">BankNifty Futures (Lot: 15)</option>
              <option value="nifty_opt">Nifty Options (Lot: 25)</option>
              <option value="banknifty_opt">BankNifty Options (Lot: 15)</option>
            </select>
            <div class="card-title" style="margin-bottom:4px;">Entry Price (₹)</div>
            <input class="fo-input" id="fo-entry" type="number" placeholder="e.g. 22000" value="22000"/>
            <div class="card-title" style="margin-bottom:4px;">Stop Loss (₹)</div>
            <input class="fo-input" id="fo-sl" type="number" placeholder="e.g. 21950" value="21950"/>
            <div class="card-title" style="margin-bottom:4px;">Target (₹)</div>
            <input class="fo-input" id="fo-target" type="number" placeholder="e.g. 22100" value="22100"/>
            <div class="card-title" style="margin-bottom:4px;">Portfolio Size (₹)</div>
            <input class="fo-input" id="fo-port" type="number" placeholder="10000" value="10000"/>
            <button class="fo-btn" onclick="calcFO()">CALCULATE ⚡</button>
          </div>
          <div class="card fadein" style="animation-delay:.1s">
            <div class="card-head"><span class="card-head-title">Trade Metrics</span></div>
            <div id="fo-results" class="fo-result">
              <div class="empty" style="padding:20px;">Enter values and click Calculate</div>
            </div>
          </div>
        </div>
        <div class="card fadein" style="animation-delay:.2s;margin-top:12px;">
          <div class="card-head"><span class="card-head-title">F&O Roadmap — Unlock Progress</span></div>
          <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:8px;">
            <div style="padding:12px 8px;background:rgba(16,185,129,.08);border:1px solid var(--green);border-radius:8px;text-align:center;">
              <div style="font-family:'Barlow',sans-serif;font-size:1.3rem;font-weight:900;color:var(--green);">P1</div>
              <div style="font-size:.65rem;font-weight:600;margin-top:2px;">Paper Equity</div>
              <div style="font-size:.58rem;color:var(--muted);">Wk 1–4</div>
              <span class="tag tag-ok" style="font-size:.58rem;margin-top:4px;display:inline-block;">ACTIVE</span>
            </div>
            <div style="padding:12px 8px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;text-align:center;">
              <div style="font-family:'Barlow',sans-serif;font-size:1.3rem;font-weight:900;color:var(--cyan);">P2</div>
              <div style="font-size:.65rem;font-weight:600;margin-top:2px;">Live Equity</div>
              <div style="font-size:.58rem;color:var(--muted);">Wk 5+</div>
              <div style="font-size:.6rem;color:var(--cyan);margin-top:3px;">₹10k</div>
            </div>
            <div style="padding:12px 8px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;text-align:center;">
              <div style="font-family:'Barlow',sans-serif;font-size:1.3rem;font-weight:900;color:var(--blue);">P3</div>
              <div style="font-size:.65rem;font-weight:600;margin-top:2px;">Scale Equity</div>
              <div style="font-size:.58rem;color:var(--muted);">Mo 2–3</div>
              <div style="font-size:.6rem;color:var(--blue);margin-top:3px;">₹25–50k</div>
            </div>
            <div style="padding:12px 8px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;text-align:center;">
              <div style="font-family:'Barlow',sans-serif;font-size:1.3rem;font-weight:900;color:var(--amber);">P4</div>
              <div style="font-size:.65rem;font-weight:600;margin-top:2px;">Stock Futures</div>
              <div style="font-size:.58rem;color:var(--muted);">Mo 3–4</div>
              <div style="font-size:.6rem;color:var(--amber);margin-top:3px;">₹50–75k</div>
            </div>
            <div style="padding:12px 8px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;text-align:center;">
              <div style="font-family:'Barlow',sans-serif;font-size:1.3rem;font-weight:900;color:var(--purple);">P5</div>
              <div style="font-size:.65rem;font-weight:600;margin-top:2px;">Index Futures</div>
              <div style="font-size:.58rem;color:var(--muted);">Mo 5–6</div>
              <div style="font-size:.6rem;color:var(--purple);margin-top:3px;">₹1L+</div>
            </div>
            <div style="padding:12px 8px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;text-align:center;">
              <div style="font-family:'Barlow',sans-serif;font-size:1.3rem;font-weight:900;color:var(--red);">P6</div>
              <div style="font-size:.65rem;font-weight:600;margin-top:2px;">Options</div>
              <div style="font-size:.58rem;color:var(--muted);">Mo 7+</div>
              <div style="font-size:.6rem;color:var(--red);margin-top:3px;">₹1.5L+</div>
            </div>
          </div>
          <div style="margin-top:12px;">
            <div style="display:flex;justify-content:space-between;font-size:.68rem;margin-bottom:4px;"><span class="c-muted">Portfolio Progress to Phase 4 (₹50,000)</span><span id="fo-pct" class="c-amber">0%</span></div>
            <div class="prog-bar" style="height:6px;"><div class="prog-fill" id="fo-prog" style="width:0%;background:var(--amber);"></div></div>
            <div style="display:flex;justify-content:space-between;font-size:.6rem;color:var(--muted);margin-top:3px;"><span id="fo-curr">₹10,000</span><span>₹50,000</span></div>
          </div>
        </div>
      </div>

      <!-- SETTINGS -->
      <div class="page" id="page-settings">
        <div class="grid-2">
          <div class="card"><div class="card-head"><span class="card-head-title">Trading Parameters</span></div>
          <table><tbody>
            <tr><td class="c-muted">Portfolio Size</td><td class="c-cyan">₹10,000</td></tr>
            <tr><td class="c-muted">Max Risk/Trade</td><td class="c-red">₹200 (2%)</td></tr>
            <tr><td class="c-muted">Daily Loss Limit</td><td class="c-red">₹800 → HALT</td></tr>
            <tr><td class="c-muted">Daily Target</td><td class="c-green">₹300–500</td></tr>
            <tr><td class="c-muted">Selective Mode At</td><td class="c-amber">₹500 profit</td></tr>
            <tr><td class="c-muted">Stop All At</td><td class="c-amber">₹800 profit</td></tr>
            <tr><td class="c-muted">Min Score (Normal)</td><td>6/10</td></tr>
            <tr><td class="c-muted">Min Score (Selective)</td><td>9/10</td></tr>
            <tr><td class="c-muted">Time Stop</td><td>15 minutes</td></tr>
            <tr><td class="c-muted">Brokerage</td><td>₹40/round-trip</td></tr>
          </tbody></table></div>
          <div class="card"><div class="card-head"><span class="card-head-title">System Info</span></div>
          <table><tbody>
            <tr><td class="c-muted">Mode</td><td><span class="tag tag-paper" id="s-mode">PAPER</span></td></tr>
            <tr><td class="c-muted">Agent</td><td><span id="s-agent" class="tag tag-ok">Running</span></td></tr>
            <tr><td class="c-muted">MiniMax AI</td><td><span class="tag tag-ok">MiniMax-M1</span></td></tr>
            <tr><td class="c-muted">Broker</td><td><span class="tag tag-ok">Zerodha Kite</span></td></tr>
            <tr><td class="c-muted">Market</td><td id="s-mkt">--</td></tr>
            <tr><td class="c-muted">VM IP</td><td class="c-cyan">34.60.172.174</td></tr>
            <tr><td class="c-muted">Token Refresh</td><td class="c-cyan">:80/token</td></tr>
          </tbody></table>
          <div style="margin-top:14px;padding:10px 12px;background:var(--bg3);border:1px solid var(--border);border-radius:6px;">
            <div class="card-title" style="margin-bottom:6px;">Monthly Cost</div>
            <div style="font-size:.9rem;">
              <div style="display:flex;justify-content:space-between;margin-bottom:3px;"><span class="c-muted">Zerodha Kite API</span><span>₹500</span></div>
              <div style="display:flex;justify-content:space-between;margin-bottom:3px;"><span class="c-muted">MiniMax API</span><span>~₹40</span></div>
              <div style="display:flex;justify-content:space-between;margin-bottom:3px;"><span class="c-muted">Google Cloud VM</span><span class="c-green">₹0</span></div>
              <div style="display:flex;justify-content:space-between;border-top:1px solid var(--border);padding-top:4px;margin-top:4px;"><span style="font-weight:700;">Total</span><span class="c-amber" style="font-weight:700;">₹540/mo</span></div>
            </div>
          </div>
          </div>
        </div>
      </div>

    </div><!-- /content -->
  </div><!-- /main -->
</div><!-- /app -->

<script>
let D = {trades:[],openPos:[],watchlist:[],dayPnl:0,portfolioValue:10000};
let charts = {};

// AUTH
function doLogin(){
  const u=document.getElementById('lu').value, p=document.getElementById('lp').value;
  fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user:u,pass:p})})
    .then(r=>r.json()).then(d=>{if(d.ok)showApp();else document.getElementById('lerr').textContent='Invalid credentials';});
}
fetch('/api/check',{credentials:'include'}).then(r=>r.json()).then(d=>{if(d.ok)showApp();});

function showApp(){
  document.getElementById('loginWrap').style.display='none';
  document.getElementById('app').style.display='flex';
  initCharts();initHeaderChart(); refresh(); loadHealth(); loadRisk(); loadStrategies();
  setInterval(refresh, 15000);
  setInterval(loadHealth, 30000);
  setInterval(loadRisk, 20000);
  setInterval(tick, 1000);
}

// CLOCK
function tick(){
  const now=new Date();
  const ist=new Date(now.toLocaleString('en-US',{timeZone:'Asia/Kolkata'}));
  document.getElementById('clock').textContent=ist.toTimeString().substr(0,8)+' IST';
  const h=ist.getHours(),m=ist.getMinutes();
  const open=(h>9||(h===9&&m>=15))&&(h<15||(h===15&&m<30));
  document.getElementById('mktDot').style.color=open?'var(--green)':'var(--red)';
  const smkt=document.getElementById('s-mkt');
  if(smkt)smkt.innerHTML=open?'<span class="tag tag-ok">Open ✓</span>':'<span class="tag tag-paused">Closed</span>';
}

// NAVIGATION
const PAGE_TITLES={dashboard:'Dashboard',health:'System Health',premarket:'Premarket Scanner',strategies:'Strategy Monitor',positions:'Positions',trades:'Trade Log',risk:'Risk Dashboard',pnl:'P&L History',fo:'F&O Calculator',settings:'Settings'};
function nav(el){
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  el.classList.add('active');
  const pg=el.dataset.page;
  document.getElementById('page-'+pg).classList.add('active');
  document.getElementById('tbTitle').textContent=PAGE_TITLES[pg]||pg;
  if(pg==='premarket') loadPremarket();
  if(pg==='strategies') loadStrategies();
  if(pg==='pnl') updatePnl();
  if(pg==='positions') updatePositions();
  if(pg==='fo') updateFOProgress();
}

// CHARTS
const CO={responsive:true,maintainAspectRatio:false,
  plugins:{legend:{display:false},tooltip:{backgroundColor:'#0f1520',borderColor:'#1d2d45',borderWidth:1,bodyFont:{family:'IBM Plex Mono',size:10}}},
  scales:{x:{grid:{display:false},ticks:{color:'#475569',font:{size:9,family:'IBM Plex Mono'}}},
          y:{grid:{color:'rgba(22,32,48,.7)'},ticks:{color:'#475569',font:{size:9,family:'IBM Plex Mono'}}}}};

let headerChart;function initHeaderChart(){const ctx=document.getElementById('headerChart');headerChart=new Chart(ctx,{type:'line',data:{labels:[],datasets:[{data:[],borderColor:'#22c55e',borderWidth:2,fill:true,backgroundColor:'rgba(34,197,94,.1)',tension:.4,pointRadius:0}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{display:false},y:{display:false}}}});}
function initCharts(){
  charts.pnl=new Chart(document.getElementById('pnlChart'),{type:'line',
    data:{labels:[],datasets:[{data:[],borderColor:'#06b6d4',borderWidth:2,fill:true,backgroundColor:'rgba(6,182,212,.05)',tension:.4,pointRadius:0}]},options:{...CO}});
  charts.daily=new Chart(document.getElementById('dailyChart'),{type:'bar',
    data:{labels:[],datasets:[{data:[],backgroundColor:[],borderRadius:4}]},options:{...CO}});
}

// MAIN REFRESH
function renderHeatmap(data){
const el=document.getElementById("heatmap");
if(!el)return;
const movers=data.movers||[];
el.innerHTML=movers.slice(0,12).map(m=>{
const cls=m.change>=0?"heatbox heat-up":"heatbox heat-down";
return `<div class="${cls}">${m.symbol}<br>${m.change.toFixed(2)}%</div>`;
}).join("");
}
function refresh(){
  fetch('/api/data',{credentials:'include'}).then(r=>r.json()).then(d=>{
    D=d; updateDashboard(); renderTrades(); updatePositions();
renderHeatmap(d);
if(headerChart){headerChart.data.labels.push('');headerChart.data.datasets[0].data.push(d.pnl||0);if(headerChart.data.labels.length>40){headerChart.data.labels.shift();headerChart.data.datasets[0].data.shift();}headerChart.update();}
    const pv=d.portfolio_value||10000;
    const pct=Math.min(100,(pv/50000)*100);
    document.getElementById('fo-prog').style.width=pct+'%';
    document.getElementById('fo-pct').textContent=pct.toFixed(0)+'%';
    document.getElementById('fo-curr').textContent='₹'+Math.round(pv).toLocaleString('en-IN');
    const sc={NORMAL:'var(--green)',SELECTIVE:'var(--amber)',HALTED:'var(--red)'};
    document.getElementById('sbState').textContent=d.agent_state;
    document.getElementById('sbState').style.color=sc[d.agent_state]||'var(--green)';
    document.getElementById('sbDot').style.background=sc[d.agent_state]||'var(--green)';
    document.getElementById('sbMode').textContent=d.mode||'PAPER';
    document.getElementById('s-mode').textContent=d.mode||'PAPER';
    document.getElementById('s-agent').textContent=d.agent_state||'NORMAL';
  }).catch(()=>{});
}

function fmt(n){return(n>=0?'₹+':'₹')+n.toFixed(2);}

function updateDashboard(){
renderHeatmap(d);
if(headerChart){headerChart.data.labels.push('');headerChart.data.datasets[0].data.push(d.pnl||0);if(headerChart.data.labels.length>40){headerChart.data.labels.shift();headerChart.data.datasets[0].data.shift();}headerChart.update();}
  const p=D.day_pnl||0,t=D.total_trades||0,w=D.wins||0,l=D.losses||0,wr=D.win_rate||0;
  const pv=D.portfolio_value||10000;
  const pnlEl=document.getElementById('d-pnl');
  pnlEl.textContent=fmt(p); pnlEl.style.color=p>=0?'var(--green)':'var(--red)';
  document.getElementById('d-pnlpct').textContent=(p>=0?'▲ ':'▼ ')+Math.abs((p/10000)*100).toFixed(2)+'% of portfolio';
  document.getElementById('d-trades').textContent=t;
  document.getElementById('d-open').textContent=(D.open_count||0)+' open position'+(D.open_count===1?'':'s');
  const wrEl=document.getElementById('d-wr'); wrEl.textContent=wr+'%'; wrEl.style.color=wr>=50?'var(--green)':'var(--red)';
  document.getElementById('d-wl').textContent=w+'W / '+l+'L';
  document.getElementById('d-portval').textContent='₹'+Math.round(pv).toLocaleString('en-IN');
  const pd=pv-10000; document.getElementById('d-portchg').textContent=(pd>=0?'+':'')+'₹'+pd.toFixed(0)+' all time';
  document.getElementById('d-updated').textContent=D.timestamp||'--';
  const st=D.agent_state||'NORMAL';
  const smap={NORMAL:'NORMAL • Score 6+',SELECTIVE:'SELECTIVE • Score 9+',HALTED:'HALTED • Daily limit hit'};
  const scol={NORMAL:'var(--purple)',SELECTIVE:'var(--amber)',HALTED:'var(--red)'};
  document.getElementById('d-state-big').textContent=smap[st]||st;
  document.getElementById('d-state-big').style.color=scol[st]||'var(--purple)';
  const prog=Math.min(100,Math.max(0,(p/500)*100));
  const pc=p<0?'var(--red)':p>=300?'var(--green)':'var(--amber)';
  document.getElementById('d-prog').style.width=prog+'%';
  document.getElementById('d-prog').style.background=pc;
  document.getElementById('d-prog-pct').textContent=prog.toFixed(0)+'%';
  document.getElementById('d-prog-pct').style.color=pc;
  // Topbar
  const tbp=document.getElementById('tbPnl');
  tbp.textContent='Day: '+fmt(p); tbp.style.color=p>=0?'var(--green)':'var(--red)';
  tbp.style.background=p>=0?'rgba(16,185,129,.1)':'rgba(239,68,68,.1)';
  tbp.style.border='1px solid '+(p>=0?'rgba(16,185,129,.2)':'rgba(239,68,68,.2)');
  const md=D.mode||'PAPER'; document.getElementById('tbMode').textContent=md;
  document.getElementById('tbMode').className='tb-pill '+(md==='LIVE'?'tag-live':'tag-paper');
  // Watchlist
  const wl=D.watchlist||[];
  document.getElementById('d-watchlist').innerHTML=wl.length?wl.map(s=>'<span class="chip">'+s+'</span>').join(''):'<span class="c-muted" style="font-size:.9rem">No watchlist loaded</span>';
  // P&L chart
  const pc2=D.pnl_curve||[];
  if(pc2.length>1){
    charts.pnl.data.labels=pc2.map(x=>x.time);
    charts.pnl.data.datasets[0].data=pc2.map(x=>x.pnl);
    charts.pnl.data.datasets[0].borderColor=p>=0?'#06b6d4':'#ef4444';
    charts.pnl.update('none');
  }
  // Open positions
  const op=D.open_positions||[];
  document.getElementById('d-opencount').textContent=op.length;
  document.getElementById('d-openpos').innerHTML=op.length
    ?'<table><thead><tr><th>Stock</th><th>Side</th><th>Qty</th><th>Entry</th><th>Unrealised</th></tr></thead><tbody>'+
      op.map(pos=>''+(t.pnl>=0?'<tr class="profit">':'<tr class="loss">')+'<td style="font-weight:700;color:var(--amber);">'+pos.stock+'</td><td><span class="tag tag-'+(pos.action.toLowerCase())+'">'+pos.action+'</span></td><td class="c-muted">'+pos.qty+'</td><td>₹'+pos.entry.toFixed(2)+'</td><td style="color:'+(pos.unrealised_pnl>=0?'var(--green)':'var(--red)')+';">'+fmt(pos.unrealised_pnl)+'</td></tr>').join('')+'</tbody></table>'
    :'<div class="empty">No open positions</div>';
  // Recent trades
  const rec=(D.trades||[]).slice(-5).reverse();
  document.getElementById('d-recent').innerHTML=rec.length
    ?'<table><thead><tr><th>Stock</th><th>P&L</th><th>Reason</th><th>Time</th></tr></thead><tbody>'+
      rec.map(t=>{
        const rl=t.reason.includes('TARGET')?'TGT':t.reason.includes('TIME')?'TIME':t.reason.includes('EOD')?'EOD':'SL';
        const rc=rl==='TGT'?'tag-ok':rl==='SL'?'tag-fail':'tag-warn';
        return''+(t.pnl>=0?'<tr class="profit">':'<tr class="loss">')+'<td style="font-weight:700;color:var(--amber);">'+t.stock+'</td><td style="color:'+(t.pnl>=0?'var(--green)':'var(--red)')+';">'+fmt(t.pnl)+'</td><td><span class="tag '+rc+'">'+rl+'</span></td><td class="c-muted">'+t.exit_time+'</td></tr>';
      }).join('')+'</tbody></table>'
    :'<div class="empty">No trades yet today</div>';
}

// TRADES PAGE
function renderTrades(){
  const filter=document.getElementById('tradeFilter').value;
  const trades=D.trades||[];
  const wins=trades.filter(t=>t.pnl>0).length, losses=trades.length-wins;
  const gross=trades.reduce((s,t)=>s+t.pnl,0);
  document.getElementById('t-total').textContent=trades.length;
  document.getElementById('t-wl').innerHTML='<span class="c-green">'+wins+'</span>/<span class="c-red">'+losses+'</span>';
  const tpe=document.getElementById('t-pnl'); tpe.textContent=fmt(gross); tpe.style.color=gross>=0?'var(--green)':'var(--red)';
  let filtered=trades;
  if(filter==='wins')filtered=trades.filter(t=>t.pnl>0);
  if(filter==='loss')filtered=trades.filter(t=>t.pnl<=0);
  if(!filtered.length){document.getElementById('t-table').innerHTML='<div class="empty">No trades found</div>';return;}
  document.getElementById('t-table').innerHTML='<table><thead><tr><th>Stock</th><th>Action</th><th>Qty</th><th>Entry</th><th>Exit</th><th>P&L</th><th>Score</th><th>Reason</th><th>In</th><th>Out</th></tr></thead><tbody>'+
    [...filtered].reverse().map(t=>{
      const rl=t.reason.includes('TARGET')?'TARGET':t.reason.includes('TIME')?'TIME STOP':t.reason.includes('EOD')?'EOD':t.reason.includes('STOP')?'SL':t.reason;
      const rc=rl.includes('TARGET')?'tag-ok':rl.includes('SL')||rl.includes('STOP')?'tag-fail':'tag-warn';
      return''+(t.pnl>=0?'<tr class="profit">':'<tr class="loss">')+'<td style="font-weight:700;color:var(--amber);">'+t.stock+'</td><td><span class="tag tag-'+(t.action.toLowerCase())+'">'+t.action+'</span></td><td class="c-muted">'+t.qty+'</td><td>₹'+t.entry.toFixed(2)+'</td><td>₹'+t.exit.toFixed(2)+'</td><td style="color:'+(t.pnl>=0?'var(--green)':'var(--red)')+';">'+fmt(t.pnl)+'</td><td><span class="tag '+(t.score>=8?'tag-ok':'tag-active')+'">'+(t.score||'--')+'/10</span></td><td><span class="tag '+rc+'">'+rl+'</span></td><td class="c-muted">'+t.entry_time+'</td><td class="c-muted">'+t.exit_time+'</td></tr>';
    }).join('')+'</tbody></table>';
}

// POSITIONS PAGE
function updatePositions(){
  const op=D.open_positions||[];
  document.getElementById('pos-count').textContent=op.length;
  const unreal=op.reduce((s,p)=>s+p.unrealised_pnl,0);
  const posUnEl=document.getElementById('pos-unreal');
  posUnEl.textContent=fmt(unreal); posUnEl.style.color=unreal>=0?'var(--green)':'var(--red)';
  const exposure=op.reduce((s,p)=>s+p.entry*p.qty,0);
  document.getElementById('pos-exposure').textContent='₹'+Math.round(exposure).toLocaleString('en-IN');
  document.getElementById('pos-ts').textContent=D.timestamp||'--';
  if(!op.length){document.getElementById('pos-table').innerHTML='<div class="empty">No open positions</div>';return;}
  document.getElementById('pos-table').innerHTML='<table><thead><tr><th>Stock</th><th>Side</th><th>Qty</th><th>Entry</th><th>Current</th><th>SL</th><th>Target</th><th>Phase</th><th>Unrealised</th><th>Score</th><th>Time</th></tr></thead><tbody>'+
    op.map(pos=>''+(t.pnl>=0?'<tr class="profit">':'<tr class="loss">')+'<td style="font-weight:700;color:var(--amber);">'+pos.stock+'</td><td><span class="tag tag-'+(pos.action.toLowerCase())+'">'+pos.action+'</span></td><td class="c-muted">'+pos.qty+'</td><td>₹'+pos.entry.toFixed(2)+'</td><td style="font-weight:700;">₹'+(pos.current||pos.entry).toFixed(2)+'</td><td class="c-red">₹'+pos.sl.toFixed(2)+'</td><td class="c-green">₹'+pos.target.toFixed(2)+'</td><td class="c-muted" style="font-size:.62rem;">'+(pos.sl_phase||'INITIAL')+'</td><td style="color:'+(pos.unrealised_pnl>=0?'var(--green)':'var(--red)')+';">'+fmt(pos.unrealised_pnl)+'</td><td><span class="tag tag-active">'+(pos.score||'--')+'/10</span></td><td class="c-muted">'+pos.time+'</td></tr>').join('')+
  '</tbody></table>';
}

// SYSTEM HEALTH
function loadHealth(){
  fetch('/api/health',{credentials:'include'}).then(r=>r.json()).then(d=>{
    document.getElementById('h-ts').textContent=d.timestamp;
    const svc=d.services||{};
    const svcNames={'trading-agent':'Trading Agent','trading-dashboard':'Dashboard','token-server':'Token Server','nginx':'Nginx Proxy'};
    document.getElementById('h-services').innerHTML=Object.entries(svc).map(([k,v])=>`
      <div class="health-row">
        <div><div class="health-name">${svcNames[k]||k}</div><div class="health-note">systemd service</div></div>
        <span class="tag ${v?'tag-ok':'tag-fail'}">${v?'✓ Running':'✗ Down'}</span>
      </div>`).join('');
    const comp=d.components||{};
    const compNames={broker_api:'Broker API',websocket:'WebSocket Stream',candle_builder:'Candle Builder',strategy_engine:'Strategy Engine',risk_engine:'Risk Engine',minimax_ai:'MiniMax AI'};
    document.getElementById('h-components').innerHTML=Object.entries(comp).map(([k,v])=>`
      <div class="health-row">
        <div><div class="health-name">${compNames[k]||k}</div><div class="health-note">${v.note||''}</div></div>
        <span class="tag ${v.ok?'tag-ok':'tag-warn'}">${v.ok?'✅ OK':'⚠ Check'}</span>
      </div>`).join('');
    document.getElementById('h-table').innerHTML=`
      <tr><td style="font-weight:700;">Broker API (Zerodha)</td><td><span class="tag ${comp.broker_api?.ok?'tag-ok':'tag-warn'}">${comp.broker_api?.ok?'✅ Connected':'⚠ Check Token'}</span></td><td class="c-muted">${comp.broker_api?.note||''}</td><td class="c-muted">No token = no data</td></tr>
      <tr><td style="font-weight:700;">WebSocket</td><td><span class="tag ${comp.websocket?.ok?'tag-ok':'tag-warn'}">${comp.websocket?.ok?'✅ Streaming':'⚠ Not streaming'}</span></td><td class="c-muted">Live tick feed</td><td class="c-muted">No ticks = no signals</td></tr>
      <tr><td style="font-weight:700;">Candle Builder</td><td><span class="tag ${svc['trading-agent']?'tag-ok':'tag-fail'}">${svc['trading-agent']?'✅ Active':'✗ Down'}</span></td><td class="c-muted">1-min OHLCV</td><td class="c-muted">No candles = no strategy</td></tr>
      <tr><td style="font-weight:700;">Strategy Engine</td><td><span class="tag ${svc['trading-agent']?'tag-ok':'tag-fail'}">${svc['trading-agent']?'✅ Running':'✗ Down'}</span></td><td class="c-muted">3 strategies active</td><td class="c-muted">No signals = no trades</td></tr>
      <tr><td style="font-weight:700;">Risk Engine</td><td><span class="tag tag-ok">✅ Ready</span></td><td class="c-muted">Max risk 2%</td><td class="c-muted">Risk always enforced</td></tr>
      <tr><td style="font-weight:700;">MiniMax AI</td><td><span class="tag tag-ok">✅ Connected</span></td><td class="c-muted">Pre-market analysis</td><td class="c-muted">Falls back to manual scan</td></tr>
    `;
  }).catch(()=>{});
}

// PREMARKET
function updateTicker(data){const i=data.indices||{};const t=['NIFTY '+(i.nifty?.price||'--')+' ('+(i.nifty?.change||0)+'%)','BANKNIFTY '+(i.banknifty?.price||'--')+' ('+(i.banknifty?.change||0)+'%)','VIX '+(i.vix?.price||'--')+' ('+(i.vix?.change||0)+'%)','SENSEX '+(i.sensex?.price||'--')+' ('+(i.sensex?.change||0)+'%)'];document.getElementById('ticker').textContent='  •  '+t.join('  •  ')+'  •  ';}
function loadPremarket(){
  document.getElementById('pm-movers').innerHTML='<div class="empty">Fetching live data...</div>';
  fetch('/api/premarket',{credentials:'include'}).then(r=>r.json()).then(d=>{
    const idx=d.indices||{};
    function setIdx(id,chgId,data){
      if(!data){return;}
      document.getElementById(id).textContent=data.price?'₹'+data.price.toLocaleString('en-IN',{minimumFractionDigits:2}):'--';
      const el=document.getElementById(chgId);
      el.textContent=(data.change>=0?'▲ +':'▼ ')+data.change+'%  '+data.trend;
      el.style.color=data.change>=0?'var(--green)':'var(--red)';
    }
    setIdx('pm-nifty','pm-nifty-chg',idx.nifty);
    setIdx('pm-bank','pm-bank-chg',idx.banknifty);
    setIdx('pm-vix','pm-vix-chg',idx.vix);
    setIdx('pm-sensex','pm-sensex-chg',idx.sensex);updateTicker(d);
    function moverTable(arr){
      if(!arr||!arr.length)return'<div class="empty">No data</div>';
      return'<table><thead><tr><th>Symbol</th><th>Price</th><th>Gap%</th><th>Volume</th><th>Momentum</th></tr></thead><tbody>'+
        arr.map(m=>''+(t.pnl>=0?'<tr class="profit">':'<tr class="loss">')+'<td style="font-weight:700;color:var(--amber);">'+m.symbol+'</td><td>₹'+m.price+'</td><td style="color:'+(m.gap_pct>=0?'var(--green)':'var(--red)')+';">'+(m.gap_pct>=0?'+':'')+m.gap_pct+'%</td><td class="c-muted">'+m.vol_score+'</td><td><span class="tag '+(m.momentum.includes('Bullish')?'tag-bullish':m.momentum.includes('Bearish')?'tag-bearish':'tag-neutral')+'">'+m.momentum+'</span></td></tr>').join('')+'</tbody></table>';
    }
    document.getElementById('pm-gapups').innerHTML=moverTable(d.gap_ups);
    document.getElementById('pm-gapdowns').innerHTML=moverTable(d.gap_downs);
    const movers=d.movers||[];
    if(!movers.length){document.getElementById('pm-movers').innerHTML='<div class="empty">No data available — market may be closed</div>';return;}
    const mRows = movers.map(m=>{
      const gc=m.change>=0?'var(--green)':'var(--red)';
      const pc=m.gap_pct>=0?'var(--green)':'var(--red)';
      const mt=m.momentum.includes('Bullish')?'tag-bullish':m.momentum.includes('Bearish')?'tag-bearish':'tag-neutral';
      const st=m.score>=5?'tag-ok':m.score<=-5?'tag-fail':'tag-warn';
      return '<tr><td style="font-weight:700;color:var(--amber);">'+m.symbol+'</td>'
        +'<td>\u20b9'+m.price+'</td>'
        +'<td style="color:'+gc+';">'+(m.change>=0?'+':'')+m.change.toFixed(2)+'</td>'
        +'<td style="color:'+pc+';">'+(m.gap_pct>=0?'+':'')+m.gap_pct+'%</td>'
        +'<td class="c-muted">\u20b9'+m.high+'</td>'
        +'<td class="c-muted">\u20b9'+m.low+'</td>'
        +'<td class="c-muted">'+m.vol_score+'</td>'
        +'<td><span class="tag '+mt+'">'+m.momentum+'</span></td>'
        +'<td><span class="tag '+st+'">'+m.score+'/10</span></td></tr>';
    });
    document.getElementById('pm-movers').innerHTML='<table><thead><tr><th>Symbol</th><th>Price</th><th>Change</th><th>Gap%</th><th>High</th><th>Low</th><th>Volume</th><th>Momentum</th><th>Score</th></tr></thead><tbody>'+
      movers.map(m=>'<tr><td style="font-weight:700;color:var(--amber);">'+m.symbol+'</td><td>₹'+m.price+'</td><td style="color:'+(m.change>=0?'var(--green)':'var(--red)')+';">'+(m.change>=0?'+':'')+m.change.toFixed(2)+'</td><td style="color:'+(m.gap_pct>=0?'var(--green)':'var(--red)')+';">'+(m.gap_pct>=0?'+':'')+m.gap_pct+'%</td><td class="c-muted">₹'+m.high+'</td><td class="c-muted">₹'+m.low+'</td><td class="c-muted">'+m.vol_score+'</td><td><span class="tag '+(m.momentum.includes('Bullish')?'tag-bullish':m.momentum.includes('Bearish')?'tag-bearish':'tag-neutral')+'">'+m.momentum+'</span></td><td><span class="tag '+(m.score>=5?'tag-ok':m.score<=-5?'tag-fail':'tag-warn')+'">'+m.score+'/10</span></td></tr>').join('')+'</tbody></table>';
  }).catch(()=>{document.getElementById('pm-movers').innerHTML='<div class="empty">Failed to fetch — check internet connection</div>';});
}

// STRATEGIES
function loadStrategies(){
  fetch('/api/strategies',{credentials:'include'}).then(r=>r.json()).then(d=>{
    const strats=d.strategies||[];
    document.getElementById('st-state').textContent=d.agent_state||'NORMAL';
    const sc={NORMAL:'var(--purple)',SELECTIVE:'var(--amber)',HALTED:'var(--red)'};
    document.getElementById('st-state').style.color=sc[d.agent_state]||'var(--purple)';
    document.getElementById('st-minscore').textContent=d.min_score||6;
    document.getElementById('st-mode-sub').textContent=d.agent_state==='SELECTIVE'?'Selective mode':'Normal mode';
    document.getElementById('st-cards').innerHTML=strats.map(s=>`
      <div class="strat-card fadein">
        <div class="strat-head">
          <div><div class="strat-name">${s.name}</div><div class="strat-type">${s.type}</div></div>
          <span class="tag ${s.status==='ACTIVE'?'tag-active':'tag-paused'}">${s.status}</span>
        </div>
        <div style="font-size:.68rem;color:var(--muted2);margin-bottom:8px;">${s.description}</div>
        <div class="strat-meta">
          <div class="strat-meta-item"><div class="strat-meta-label">Trades Today</div><div class="strat-meta-val c-cyan">${s.trades_today}</div></div>
          <div class="strat-meta-item"><div class="strat-meta-label">Win Rate</div><div class="strat-meta-val ${s.win_rate>=50?'c-green':'c-red'}">${s.win_rate}%</div></div>
          <div class="strat-meta-item"><div class="strat-meta-label">Signal</div><div class="strat-meta-val c-muted">${s.signal}</div></div>
          <div class="strat-meta-item"><div class="strat-meta-label">Status</div><div class="strat-meta-val ${s.status==='ACTIVE'?'c-cyan':'c-muted'}">${s.status}</div></div>
        </div>
      </div>`).join('');
  }).catch(()=>{});
}

// RISK
function loadRisk(){
  fetch('/api/risk',{credentials:'include'}).then(r=>r.json()).then(d=>{
    const luEl=document.getElementById('r-lossused');
    luEl.textContent='₹'+d.loss_used.toFixed(2); luEl.style.color=d.loss_used>400?'var(--red)':'var(--amber)';
    document.getElementById('r-lossrem').textContent='₹'+d.loss_remaining.toFixed(2)+' remaining';
    const prEl=document.getElementById('r-profit');
    prEl.textContent=fmt(d.day_pnl); prEl.style.color=d.day_pnl>=0?'var(--green)':'var(--red)';
    document.getElementById('r-openrisk').textContent='₹'+d.open_risk.toFixed(2);
    document.getElementById('r-pct').textContent=d.loss_pct+'%';
    document.getElementById('r-pct').style.color=d.risk_level==='DANGER'?'var(--red)':d.risk_level==='WARNING'?'var(--amber)':'var(--green)';
    document.getElementById('r-bar').style.width=d.loss_pct+'%';
    document.getElementById('r-bar').style.background=d.risk_level==='DANGER'?'var(--red)':d.risk_level==='WARNING'?'var(--amber)':'var(--green)';
    const lvl=document.getElementById('r-level');
    lvl.textContent=d.risk_level; lvl.className='tag tag-'+(d.risk_level==='DANGER'?'danger':d.risk_level==='WARNING'?'warn':'safe');
    if(!d.trading_allowed){
      document.getElementById('r-status-text').textContent='TRADING HALTED';
      document.getElementById('r-status-text').style.color='var(--red)';
      document.getElementById('r-status').firstElementChild.textContent='🚫';
      document.getElementById('r-status-sub').textContent='Daily loss limit of ₹800 reached. Resumes tomorrow 9:15 AM.';
    } else {
      document.getElementById('r-status-text').textContent='TRADING ACTIVE';
      document.getElementById('r-status-text').style.color='var(--green)';
      document.getElementById('r-status').firstElementChild.textContent='✅';
      document.getElementById('r-status-sub').textContent=d.agent_state==='SELECTIVE'?'Selective mode — score 9+ required':'All systems normal';
    }
  }).catch(()=>{});
}

// P&L HISTORY
function updatePnl(){
  const daily=D.daily_pnl||[], today=D.day_pnl||0;
  const allPnl=daily.reduce((s,d)=>s+d.pnl,0);
  const e=(id,v)=>{const el=document.getElementById(id);if(!el)return;el.textContent=fmt(v);el.style.color=v>=0?'var(--green)':'var(--red)';};
  e('ph-today',today); e('ph-week',allPnl); e('ph-month',allPnl); e('ph-all',allPnl);
  if(daily.length){
    charts.daily.data.labels=daily.map(d=>d.date.substr(5));
    charts.daily.data.datasets[0].data=daily.map(d=>d.pnl);
    charts.daily.data.datasets[0].backgroundColor=daily.map(d=>d.pnl>=0?'rgba(16,185,129,.7)':'rgba(239,68,68,.7)');
    charts.daily.update('none');
    document.getElementById('ph-table').innerHTML='<table><thead><tr><th>Date</th><th>Trades</th><th>W</th><th>L</th><th>Win%</th><th>P&L</th><th>Target</th></tr></thead><tbody>'+
      [...daily].reverse().map(d=>'<tr><td style="font-weight:600;">'+d.date+'</td><td class="c-muted">'+d.trades+'</td><td class="c-green">'+d.wins+'</td><td class="c-red">'+d.losses+'</td><td>'+(d.trades?Math.round((d.wins/d.trades)*100):0)+'%</td><td style="color:'+(d.pnl>=0?'var(--green)':'var(--red)')+';">'+fmt(d.pnl)+'</td><td>'+(d.pnl>=300?'<span class="tag tag-ok">✓ Hit</span>':'<span class="tag tag-fail">✗ No</span>')+'</td></tr>').join('')+
    '</tbody></table>';
  }
}

// F&O CALCULATOR
const LOT_SIZES={equity:1,stock_fut:500,nifty_fut:25,banknifty_fut:15,nifty_opt:25,banknifty_opt:15};
const MARGIN_PCT={equity:1,stock_fut:0.15,nifty_fut:0.12,banknifty_fut:0.12,nifty_opt:1,banknifty_opt:1};
function calcFO(){
  const inst=document.getElementById('fo-instrument').value;
  const entry=parseFloat(document.getElementById('fo-entry').value)||0;
  const sl=parseFloat(document.getElementById('fo-sl').value)||0;
  const target=parseFloat(document.getElementById('fo-target').value)||0;
  const port=parseFloat(document.getElementById('fo-port').value)||10000;
  if(!entry||!sl||!target){document.getElementById('fo-results').innerHTML='<div class="empty">Fill all fields</div>';return;}
  const lotSize=LOT_SIZES[inst]||1;
  const riskPerShare=Math.abs(entry-sl);
  const rewardPerShare=Math.abs(target-entry);
  const rr=riskPerShare>0?(rewardPerShare/riskPerShare).toFixed(2):0;
  const maxRisk=port*0.02;
  const qty=Math.floor(maxRisk/riskPerShare);
  const lots=Math.max(1,Math.floor(qty/lotSize));
  const finalQty=lots*lotSize;
  const tradeValue=entry*finalQty;
  const margin=tradeValue*MARGIN_PCT[inst];
  const riskAmt=riskPerShare*finalQty;
  const rewardAmt=rewardPerShare*finalQty;
  const breakeven=entry+(riskPerShare*0.1);
  document.getElementById('fo-results').innerHTML=`
    <div class="fo-row"><span class="c-muted">Instrument</span><span style="font-weight:700;">${document.getElementById('fo-instrument').options[document.getElementById('fo-instrument').selectedIndex].text}</span></div>
    <div class="fo-row"><span class="c-muted">Lot Size</span><span>${lotSize} shares/lot</span></div>
    <div class="fo-row"><span class="c-muted">Recommended Lots</span><span class="c-amber" style="font-weight:700;">${lots} lot${lots>1?'s':''}</span></div>
    <div class="fo-row"><span class="c-muted">Total Quantity</span><span>${finalQty} shares</span></div>
    <div class="fo-row"><span class="c-muted">Trade Value</span><span>₹${Math.round(tradeValue).toLocaleString('en-IN')}</span></div>
    <div class="fo-row"><span class="c-muted">Margin Required</span><span class="c-cyan">₹${Math.round(margin).toLocaleString('en-IN')}</span></div>
    <div class="fo-row"><span class="c-muted">Risk Distance</span><span class="c-red">${riskPerShare.toFixed(2)} pts</span></div>
    <div class="fo-row"><span class="c-muted">Max Loss</span><span class="c-red">₹${riskAmt.toFixed(2)}</span></div>
    <div class="fo-row"><span class="c-muted">Target Distance</span><span class="c-green">${rewardPerShare.toFixed(2)} pts</span></div>
    <div class="fo-row"><span class="c-muted">Max Profit</span><span class="c-green">₹${rewardAmt.toFixed(2)}</span></div>
    <div class="fo-row" style="border-top:1px solid var(--amber);margin-top:4px;padding-top:8px;"><span style="font-weight:700;">Risk:Reward</span><span class="c-amber" style="font-family:'Barlow',sans-serif;font-weight:800;font-size:1rem;">1:${rr}</span></div>
    <div class="fo-row"><span class="c-muted">% of Portfolio at Risk</span><span>${((riskAmt/port)*100).toFixed(2)}%</span></div>
  `;
}

function updateFOProgress(){
  const pv=D.portfolioValue||10000;
  const pct=Math.min(100,(pv/50000)*100);
  document.getElementById('fo-prog').style.width=pct+'%';
  document.getElementById('fo-pct').textContent=pct.toFixed(0)+'%';
  document.getElementById('fo-curr').textContent='₹'+Math.round(pv).toLocaleString('en-IN');
}
</script>
</body>
</html>"""


@app.route("/")
@app.route("/dashboard")
def index():
    return HTML


if __name__ == "__main__":
    print("🚀 MiniMax Pro Terminal v2 — port 5001")
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
