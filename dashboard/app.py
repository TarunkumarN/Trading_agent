"""
dashboard/app.py
Live P&L dashboard — run with: streamlit run dashboard/app.py
Access at: http://localhost:8501
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PORTFOLIO_VALUE, DAILY_LOSS_LIMIT, DAILY_PROFIT_STOP

st.set_page_config(
    page_title  = "MiniMax Scalping Agent",
    page_icon   = "📈",
    layout      = "wide",
    initial_sidebar_state = "collapsed"
)

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<style>
    .big-metric { font-size: 2rem; font-weight: bold; }
    .green { color: #00cc66; }
    .red { color: #ff4444; }
    .neutral { color: #aaaaaa; }
</style>
""", unsafe_allow_html=True)

st.title("📈 MiniMax Scalping Agent — Live Dashboard")
st.caption(f"Portfolio: ₹{PORTFOLIO_VALUE:,.0f} | Daily SL: ₹{DAILY_LOSS_LIMIT} | Target: ₹300–500")

# ── Load trade log ────────────────────────────────────────────
LOG_FILE = Path(__file__).parent.parent / "logs" / "trades.json"

def load_trades():
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE) as f:
                return json.load(f)
        except Exception:
            return []
    return []

trades = load_trades()

# ── Key Metrics Row ───────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

total_pnl  = sum(t.get("pnl", 0) for t in trades)
wins       = len([t for t in trades if t.get("pnl", 0) >= 0])
losses     = len([t for t in trades if t.get("pnl", 0) < 0])
win_rate   = (wins / len(trades) * 100) if trades else 0
state      = "NORMAL"
if total_pnl <= -DAILY_LOSS_LIMIT:    state = "HALTED 🛑"
elif total_pnl >= DAILY_PROFIT_STOP:  state = "PROTECTED 🏆"
elif total_pnl >= 500:                state = "SELECTIVE 🎯"

pnl_color = "green" if total_pnl >= 0 else "red"

with col1:
    st.metric("Day P&L", f"₹{total_pnl:+.2f}",
              delta=f"{'▲' if total_pnl >= 0 else '▼'} {abs(total_pnl/PORTFOLIO_VALUE*100):.1f}%")
with col2:
    st.metric("Total Trades", len(trades))
with col3:
    st.metric("Wins / Losses", f"{wins} / {losses}")
with col4:
    st.metric("Win Rate", f"{win_rate:.0f}%")
with col5:
    st.metric("Agent State", state)

st.divider()

# ── P&L Chart ─────────────────────────────────────────────────
if trades:
    cumulative = []
    running    = 0
    for t in trades:
        running += t.get("pnl", 0)
        cumulative.append({
            "time":  t.get("exit_time", ""),
            "pnl":   round(running, 2),
            "stock": t.get("stock", "")
        })

    df_chart = pd.DataFrame(cumulative)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x    = list(range(len(df_chart))),
        y    = df_chart["pnl"],
        mode = "lines+markers",
        name = "Cumulative P&L",
        line = dict(color="#00cc66" if total_pnl >= 0 else "#ff4444", width=2),
        hovertemplate = "Trade #%{x}<br>P&L: ₹%{y:.2f}<extra></extra>"
    ))
    fig.add_hline(y=0,   line_dash="dash", line_color="white", opacity=0.3)
    fig.add_hline(y=300, line_dash="dot",  line_color="#00cc66", opacity=0.5,
                  annotation_text="Target ₹300")
    fig.add_hline(y=-DAILY_LOSS_LIMIT, line_dash="dot", line_color="#ff4444", opacity=0.5,
                  annotation_text="SL ₹500")
    fig.update_layout(
        title      = "Cumulative P&L Today",
        paper_bgcolor = "#0e1117",
        plot_bgcolor  = "#0e1117",
        font_color    = "white",
        height        = 350,
        showlegend    = False
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Trade Log Table ───────────────────────────────────────────
st.subheader("📋 Trade Log")
if trades:
    df = pd.DataFrame(trades)
    df["pnl"] = df["pnl"].apply(lambda x: f"₹{x:+.2f}")
    st.dataframe(
        df[["exit_time", "stock", "action", "qty", "entry", "exit", "pnl", "reason"]],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No trades yet today. Waiting for market signals...")

# ── Auto-refresh every 30 seconds ────────────────────────────
st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')} | Refreshes every 30s")
st.markdown("""
<script>
setTimeout(function() { window.location.reload(); }, 30000);
</script>
""", unsafe_allow_html=True)
