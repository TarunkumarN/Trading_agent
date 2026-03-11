import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import { LayoutDashboard, HeartPulse, ScanSearch, BrainCircuit, Target, ListOrdered, ShieldAlert, TrendingUp, Calculator, Settings, ScrollText, Activity, Menu, X, RefreshCw, ChevronRight, Zap, Sun, Moon, FileText } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL;
const fmt = n => (n >= 0 ? '+' : '') + Number(n).toFixed(2);
const fmtINR = n => new Intl.NumberFormat('en-IN').format(Math.round(n));
const CAPITAL = 50000;

function LoginPage({ onLogin, theme, toggleTheme }) {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const go = async () => {
    setLoading(true); setError('');
    try { const r = await fetch(`${API}/api/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user, pass }) }); const d = await r.json(); if (d.ok) { localStorage.setItem("mm_authed", "true"); onLogin(); } else setError('Invalid credentials'); } catch { setError('Connection failed'); }
    setLoading(false);
  };
  return (
    <div className="login-wrap" data-testid="login-page">
      <div className="login-box">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
          <div><h1 data-testid="login-logo">MINIMAX</h1><p>PRO TRADING TERMINAL</p></div>
          <button className="theme-toggle" onClick={toggleTheme} data-testid="login-theme-toggle">{theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}</button>
        </div>
        <input data-testid="login-username" type="text" placeholder="Username" value={user} onChange={e => setUser(e.target.value)} autoComplete="off" />
        <input data-testid="login-password" type="password" placeholder="Password" value={pass} onChange={e => setPass(e.target.value)} onKeyDown={e => e.key === 'Enter' && go()} />
        <button data-testid="login-submit" className="login-btn" onClick={go} disabled={loading}>{loading ? 'CONNECTING...' : 'ACCESS TERMINAL'}</button>
        {error && <div className="login-error" data-testid="login-error">{error}</div>}
      </div>
    </div>
  );
}

function Stat({ label, value, sub, color, accent }) {
  return <div className={`card card-accent ${accent || ''}`}><div className="card-label">{label}</div><div className="metric" style={{ color: color || 'var(--text)' }}>{value}</div>{sub && <div className="metric-sub">{sub}</div>}</div>;
}

function TradeModal({ trade, onClose }) {
  const [d, setD] = useState(null);
  useEffect(() => { if (!trade) return; fetch(`${API}/api/trades/${trade.symbol}_${(trade.entry_time || '').replace(/:/g, '')}`).then(r => r.json()).then(setD).catch(() => {}); }, [trade]);
  if (!trade) return null;
  return (
    <div className="modal-overlay" onClick={onClose} data-testid="trade-detail-modal"><div className="modal-box" onClick={e => e.stopPropagation()}>
      <button className="modal-close" onClick={onClose} data-testid="modal-close">&times;</button>
      <h2 style={{ fontSize: '1.3rem', fontWeight: 900, marginBottom: 4 }}><span style={{ color: 'var(--amber)' }}>{trade.symbol}</span> Trade Detail</h2>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: 18 }}>{trade.date} | {trade.entry_time} - {trade.exit_time}</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginBottom: 18 }}>
        <div className="strat-meta-item"><div className="strat-meta-label">Action</div><div className="strat-meta-val"><span className={`tag tag-${trade.action?.toLowerCase()}`}>{trade.action}</span></div></div>
        <div className="strat-meta-item"><div className="strat-meta-label">P&L</div><div className="strat-meta-val" style={{ color: trade.pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>{fmt(trade.pnl)}</div></div>
        <div className="strat-meta-item"><div className="strat-meta-label">Score</div><div className="strat-meta-val" style={{ color: 'var(--cyan)' }}>{trade.score}/10</div></div>
      </div>
      <div className="card-label">Parameters</div>
      {[['Strategy', d?.strategy || trade.strategy || 'MiniMax'], ['Entry', `₹${trade.entry?.toFixed(2)}`], ['Exit', `₹${trade.exit?.toFixed(2)}`], ['Qty', trade.qty], ['Reason', trade.reason]].map(([k, v]) => <div key={k} className="fo-row"><span className="c-dim">{k}</span><span>{v}</span></div>)}
      {d?.market_regime && (<><div className="card-label" style={{ marginTop: 16 }}>AI Analysis</div>{[['Market Regime', d.market_regime], ['Liquidity', d.liquidity_signal], ['Prediction', d.prediction_probability], ['Entry Reason', d.entry_reason]].map(([k, v]) => <div key={k} className="fo-row"><span className="c-dim">{k}</span><span style={{ color: 'var(--cyan)' }}>{v}</span></div>)}</>)}
      {d?.ai_validation && (<><div className="card-label" style={{ marginTop: 16 }}>AI Validation</div>{Object.entries(d.ai_validation).map(([k, v]) => <div key={k} className="fo-row"><span className="c-dim">{k.replace(/_/g, ' ')}</span><span style={{ color: v === true ? 'var(--green)' : v === false ? 'var(--red)' : 'var(--amber)' }}>{typeof v === 'boolean' ? (v ? 'YES' : 'NO') : v}</span></div>)}</>)}
    </div></div>
  );
}

/* ═══ Pages ═══ */
function DashboardPage({ data, regime }) {
  const p = data.day_pnl || 0;
  const pv = data.portfolio_value || CAPITAL;
  const rc = regime?.regime?.includes('BULL') ? 'bullish' : regime?.regime?.includes('BEAR') ? 'bearish' : 'neutral';
  return (
    <div className="page-enter" data-testid="dashboard-page">
      {regime && <div className={`regime-banner ${rc}`}>
        <div><div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', letterSpacing: 1 }}>AI MARKET REGIME</div><div style={{ fontSize: '1.1rem', fontWeight: 900, color: regime.regime?.includes('BULL') ? 'var(--green)' : regime.regime?.includes('BEAR') ? 'var(--red)' : 'var(--amber)' }}>{regime.regime} | {regime.recommendation}</div></div>
        <div style={{ textAlign: 'right' }}><div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Confidence: <span style={{ color: 'var(--cyan)', fontWeight: 700 }}>{regime.confidence}%</span></div><div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>VIX: {regime.volatility?.vix} | Liquidity: {regime.liquidity?.status}</div></div>
      </div>}
      <div className="grid-4">
        <Stat label="Day P&L" value={`₹${fmt(p)}`} sub={`${Math.abs((p / CAPITAL) * 100).toFixed(2)}% of portfolio`} color={p >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" />
        <Stat label="Trades Today" value={data.total_trades || 0} sub={`${data.open_count || 0} open`} color="var(--cyan)" accent="ca-cyan" />
        <Stat label="Win Rate" value={`${data.win_rate || 0}%`} sub={`${data.wins || 0}W / ${data.losses || 0}L`} color={(data.win_rate || 0) >= 50 ? 'var(--green)' : 'var(--red)'} accent="ca-amber" />
        <Stat label="Portfolio" value={`₹${fmtINR(pv)}`} sub={`${fmt(pv - CAPITAL)} all time`} color="var(--purple)" accent="ca-purple" />
      </div>
      <div className="grid-28">
        <div className="card"><div className="card-head"><span className="card-head-title">Intraday P&L</span></div><div style={{ height: 210 }}><ResponsiveContainer width="100%" height="100%"><LineChart data={data.pnl_curve || []}><CartesianGrid strokeDasharray="3 3" stroke="var(--border)" /><XAxis dataKey="time" tick={{ fill: 'var(--text-dim)', fontSize: 11 }} /><YAxis tick={{ fill: 'var(--text-dim)', fontSize: 11 }} /><Tooltip contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)', fontSize: 12 }} /><Line type="monotone" dataKey="pnl" stroke={p >= 0 ? 'var(--green)' : 'var(--red)'} strokeWidth={2} dot={false} /></LineChart></ResponsiveContainer></div></div>
        <div className="card"><div className="card-head"><span className="card-head-title">Status</span></div><div className="card-label">Watchlist</div><div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 16 }}>{(data.watchlist || []).map(s => <span key={s} className="chip">{s}</span>)}</div><div className="card-label">Agent</div><div style={{ fontSize: '1rem', fontWeight: 800, color: data.agent_state === 'HALTED' ? 'var(--red)' : 'var(--green)', marginBottom: 12 }}>{data.agent_state || 'NORMAL'}</div><div className="card-label">Market</div><div style={{ fontWeight: 600, color: data.market_open ? 'var(--green)' : 'var(--red)' }}>{data.market_open ? 'NSE OPEN' : 'NSE CLOSED'}</div></div>
      </div>
      <div className="grid-2">
        <div className="card"><div className="card-head"><span className="card-head-title">Open Positions</span><span className="tag tag-active">{(data.open_positions || []).length}</span></div>{(data.open_positions || []).length > 0 ? <div className="tbl-wrap"><table><thead><tr><th>Stock</th><th>Side</th><th>Qty</th><th>Entry</th><th>Unreal</th></tr></thead><tbody>{data.open_positions.map(pos => <tr key={pos.symbol}><td style={{ fontWeight: 700, color: 'var(--amber)' }}>{pos.symbol}</td><td><span className={`tag tag-${pos.action?.toLowerCase()}`}>{pos.action}</span></td><td>{pos.qty}</td><td>₹{pos.entry?.toFixed(2)}</td><td style={{ color: pos.unrealised_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{fmt(pos.unrealised_pnl || 0)}</td></tr>)}</tbody></table></div> : <div className="empty">No positions</div>}</div>
        <div className="card"><div className="card-head"><span className="card-head-title">Recent Trades</span></div>{(data.trades || []).length > 0 ? <div className="tbl-wrap"><table><thead><tr><th>Stock</th><th>P&L</th><th>Reason</th><th>Time</th></tr></thead><tbody>{data.trades.slice(0, 6).map((t, i) => <tr key={i}><td style={{ fontWeight: 700, color: 'var(--amber)' }}>{t.symbol}</td><td style={{ color: t.pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{fmt(t.pnl)}</td><td><span className={`tag ${t.reason?.includes('TARGET') ? 'tag-ok' : t.reason?.includes('STOP') ? 'tag-fail' : 'tag-warn'}`}>{t.reason?.replace(' (15 min)', '')}</span></td><td className="c-dim">{t.exit_time}</td></tr>)}</tbody></table></div> : <div className="empty">No trades</div>}</div>
      </div>
    </div>
  );
}

function PortfolioPage({ portfolio }) {
  if (!portfolio) return <div className="empty">Loading...</div>;
  const p = portfolio;
  return (<div className="page-enter" data-testid="portfolio-page">
    <div className="grid-4"><Stat label="Initial Capital" value={`₹${fmtINR(p.initial_capital)}`} color="var(--text-muted)" accent="ca-blue" /><Stat label="Equity" value={`₹${fmtINR(p.current_equity)}`} color={p.total_pnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" /><Stat label="Total P&L" value={`₹${fmt(p.total_pnl)}`} sub={`Day: ₹${fmt(p.day_pnl)}`} color={p.total_pnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-cyan" /><Stat label="Open P&L" value={`₹${fmt(p.unrealised_pnl)}`} sub={`${p.open_positions} pos`} color={p.unrealised_pnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-amber" /></div>
    <div className="card" style={{ marginBottom: 16 }}><div className="card-head"><span className="card-head-title">Equity Curve</span></div><div style={{ height: 220 }}><ResponsiveContainer width="100%" height="100%"><LineChart data={p.equity_curve || []}><CartesianGrid strokeDasharray="3 3" stroke="var(--border)" /><XAxis dataKey="date" tick={{ fill: 'var(--text-dim)', fontSize: 10 }} /><YAxis tick={{ fill: 'var(--text-dim)', fontSize: 10 }} domain={['dataMin-200', 'dataMax+200']} /><Tooltip contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)' }} /><Line type="monotone" dataKey="equity" stroke="var(--green)" strokeWidth={2} dot={{ r: 4 }} /></LineChart></ResponsiveContainer></div></div>
    <div className="card" style={{ marginBottom: 16 }}><div className="card-head"><span className="card-head-title">Daily P&L</span></div><div style={{ height: 200 }}><ResponsiveContainer width="100%" height="100%"><BarChart data={p.daily_pnl_chart || []}><CartesianGrid strokeDasharray="3 3" stroke="var(--border)" /><XAxis dataKey="date" tick={{ fill: 'var(--text-dim)', fontSize: 10 }} /><YAxis tick={{ fill: 'var(--text-dim)', fontSize: 10 }} /><Tooltip contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)' }} /><Bar dataKey="pnl" radius={[4, 4, 0, 0]}>{(p.daily_pnl_chart || []).map((d, i) => <Cell key={i} fill={d.pnl >= 0 ? 'var(--green)' : 'var(--red)'} />)}</Bar></BarChart></ResponsiveContainer></div></div>
    <div className="grid-3"><div className="card"><div className="card-label">Total Trades</div><div className="metric" style={{ color: 'var(--cyan)' }}>{p.total_trades}</div><div className="metric-sub">{p.wins}W / {p.losses}L</div></div><div className="card"><div className="card-label">Win Rate</div><div className="metric" style={{ color: p.win_rate >= 50 ? 'var(--green)' : 'var(--red)' }}>{p.win_rate}%</div><div className="metric-sub">Avg Win: ₹{p.avg_profit} | Loss: ₹{p.avg_loss}</div></div><div className="card"><div className="card-label">Profit Factor</div><div className="metric" style={{ color: 'var(--amber)' }}>{p.profit_factor}x</div><div className="metric-sub">Max DD: {p.max_drawdown}%</div></div></div>
  </div>);
}

function ReportPage({ report }) {
  if (!report) return <div className="empty">Loading report...</div>;
  return (<div className="page-enter" data-testid="report-page">
    <div className="grid-4"><Stat label="Trades" value={report.total_trades} color="var(--cyan)" accent="ca-cyan" /><Stat label="Wins / Losses" value={`${report.winning_trades} / ${report.losing_trades}`} sub={`Win Rate: ${report.win_rate}%`} color="var(--amber)" accent="ca-amber" /><Stat label="Day P&L" value={`₹${fmt(report.daily_pnl)}`} color={report.daily_pnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" /><Stat label="Portfolio" value={`₹${fmtINR(report.portfolio_value)}`} sub={`Cumulative: ₹${fmt(report.cumulative_pnl)}`} color="var(--purple)" accent="ca-purple" /></div>
    <div className="grid-2">
      <div className="card"><div className="card-head"><span className="card-head-title">Performance Metrics</span></div>{[['Avg Profit', `₹${report.avg_profit}`, 'var(--green)'], ['Avg Loss', `₹${report.avg_loss}`, 'var(--red)'], ['Profit Factor', `${report.profit_factor}x`, 'var(--amber)'], ['Best Trade', report.best_trade ? `${report.best_trade.symbol}: ₹${fmt(report.best_trade.pnl)}` : '--', 'var(--green)'], ['Worst Trade', report.worst_trade ? `${report.worst_trade.symbol}: ₹${fmt(report.worst_trade.pnl)}` : '--', 'var(--red)']].map(([k, v, c]) => <div key={k} className="fo-row"><span className="c-dim">{k}</span><span style={{ color: c, fontWeight: 600 }}>{v}</span></div>)}</div>
      <div className="card"><div className="card-head"><span className="card-head-title">Strategy Breakdown</span></div>{(report.strategy_performance || []).length > 0 ? <div className="tbl-wrap"><table><thead><tr><th>Strategy</th><th>Trades</th><th>Win%</th><th>P&L</th></tr></thead><tbody>{report.strategy_performance.map((s, i) => <tr key={i}><td>{s.name}</td><td>{s.trades}</td><td style={{ color: s.win_rate >= 50 ? 'var(--green)' : 'var(--red)' }}>{s.win_rate}%</td><td style={{ color: s.pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{fmt(s.pnl)}</td></tr>)}</tbody></table></div> : <div className="empty">No strategy data</div>}</div>
    </div>
    <div className="card" style={{ marginTop: 16 }}><div className="card-head"><span className="card-head-title">Portfolio Growth</span></div><div style={{ height: 200 }}><ResponsiveContainer width="100%" height="100%"><LineChart data={report.portfolio_growth || []}><CartesianGrid strokeDasharray="3 3" stroke="var(--border)" /><XAxis dataKey="date" tick={{ fill: 'var(--text-dim)', fontSize: 10 }} /><YAxis tick={{ fill: 'var(--text-dim)', fontSize: 10 }} domain={['dataMin-500', 'dataMax+500']} /><Tooltip contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)' }} /><Line type="monotone" dataKey="value" stroke="var(--green)" strokeWidth={2} dot={{ r: 3 }} /></LineChart></ResponsiveContainer></div></div>
    <div className="card" style={{ marginTop: 16 }}><div className="card-head"><span className="card-head-title">Cumulative P&L</span></div><div style={{ height: 180 }}><ResponsiveContainer width="100%" height="100%"><BarChart data={report.daily_pnl_history || []}><CartesianGrid strokeDasharray="3 3" stroke="var(--border)" /><XAxis dataKey="date" tick={{ fill: 'var(--text-dim)', fontSize: 10 }} /><YAxis tick={{ fill: 'var(--text-dim)', fontSize: 10 }} /><Tooltip contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)' }} /><Bar dataKey="daily_pnl" radius={[3, 3, 0, 0]}>{(report.daily_pnl_history || []).map((d, i) => <Cell key={i} fill={d.daily_pnl >= 0 ? 'var(--green)' : 'var(--red)'} />)}</Bar><Line type="monotone" dataKey="cumulative_pnl" stroke="var(--cyan)" strokeWidth={2} dot={false} /></BarChart></ResponsiveContainer></div></div>
  </div>);
}

function MarketPage({ market, regime, loadMarket }) {
  if (!market) return <div className="empty">Loading market data...</div>;
  const StockTable = ({ stocks }) => stocks?.length ? <div className="tbl-wrap"><table><thead><tr><th>Symbol</th><th>Price</th><th>Change</th><th>Volume</th><th>High</th><th>Low</th></tr></thead><tbody>{stocks.map(s => <tr key={s.symbol}><td style={{ fontWeight: 700, color: 'var(--amber)' }}>{s.symbol}</td><td>₹{s.price}</td><td style={{ color: s.change_pct >= 0 ? 'var(--green)' : 'var(--red)' }}>{s.change_pct >= 0 ? '+' : ''}{s.change_pct}%</td><td className="c-muted">{fmtINR(s.volume || 0)}</td><td>₹{s.high}</td><td>₹{s.low}</td></tr>)}</tbody></table></div> : <div className="empty">No data</div>;
  const idx = market.indices || {};
  return (<div className="page-enter" data-testid="market-page">
    {regime && <div className={`regime-banner ${regime.regime?.includes('BULL') ? 'bullish' : regime.regime?.includes('BEAR') ? 'bearish' : 'neutral'}`}><div><div style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>AI REGIME</div><div style={{ fontSize: '1.1rem', fontWeight: 900, color: regime.regime?.includes('BULL') ? 'var(--green)' : regime.regime?.includes('BEAR') ? 'var(--red)' : 'var(--amber)' }}>{regime.regime}</div></div><div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}><div><div className="strat-meta-label">VIX</div><div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{regime.volatility?.vix}</div></div><div><div className="strat-meta-label">Breadth</div><div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{regime.breadth?.ratio}</div></div><div><div className="strat-meta-label">Liquidity</div><div style={{ fontWeight: 700, fontSize: '0.9rem', color: regime.liquidity?.status === 'HIGH' ? 'var(--green)' : 'var(--amber)' }}>{regime.liquidity?.status}</div></div><div><div className="strat-meta-label">Action</div><div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--cyan)' }}>{regime.recommendation}</div></div></div></div>}
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}><span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Source: {market.source} | {market.data_valid ? 'Validated' : 'Fallback'} | {market.timestamp}</span><button data-testid="market-refresh" onClick={loadMarket} style={{ padding: '6px 14px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--green)', cursor: 'pointer', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 6 }}><RefreshCw size={13} /> Refresh</button></div>
    <div className="grid-4">{Object.entries(idx).map(([k, v]) => <div key={k} className="card idx-card"><div className="idx-name">{k.replace(/_/g, ' ').toUpperCase()}</div><div className="idx-val">{fmtINR(v.price || 0)}</div><div className="idx-chg" style={{ color: (v.change_pct || 0) >= 0 ? 'var(--green)' : 'var(--red)' }}>{v.change_pct >= 0 ? '+' : ''}{v.change_pct}%</div></div>)}</div>
    <div className="grid-2"><div className="card"><div className="card-head"><span className="card-head-title" style={{ color: 'var(--green)' }}>Top Gainers</span><span className="tag tag-ok">{(market.gainers || []).length}</span></div><StockTable stocks={market.gainers} /></div><div className="card"><div className="card-head"><span className="card-head-title" style={{ color: 'var(--red)' }}>Top Losers</span><span className="tag tag-fail">{(market.losers || []).length}</span></div><StockTable stocks={market.losers} /></div></div>
    <div className="card"><div className="card-head"><span className="card-head-title">Most Active</span><span className="c-dim" style={{ fontSize: '0.75rem' }}>Adv: {market.summary?.advances} | Dec: {market.summary?.declines}</span></div><StockTable stocks={market.most_active} /></div>
  </div>);
}

function HealthPage({ health }) { if (!health) return <div className="empty">Loading...</div>; const c = health.components || {}; return (<div className="page-enter" data-testid="health-page"><div className="grid-2"><div className="card"><div className="card-head"><span className="card-head-title">Components</span></div>{Object.entries(c).map(([k, v]) => <div key={k} className="health-row"><div><div style={{ fontWeight: 700 }}>{k.replace(/_/g, ' ').toUpperCase()}</div><div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{v.note}</div></div><div className="health-dot" style={{ background: v.ok ? 'var(--green)' : 'var(--red)' }} /></div>)}</div><div className="card"><div className="card-head"><span className="card-head-title">Risk Summary</span></div>{health.risk_summary && Object.entries(health.risk_summary).map(([k, v]) => <div key={k} className="health-row"><span style={{ color: 'var(--text-dim)' }}>{k.replace(/_/g, ' ')}</span><span style={{ fontWeight: 600, fontFamily: "'JetBrains Mono',monospace" }}>{typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v)}</span></div>)}<div className="health-row"><span className="c-dim">Market</span><span className={`tag ${health.market_open ? 'tag-ok' : 'tag-fail'}`}>{health.market_open ? 'OPEN' : 'CLOSED'}</span></div></div></div></div>); }

function AIBrainPage({ aiData }) { if (!aiData) return <div className="empty">Loading...</div>; return (<div className="page-enter" data-testid="ai-brain-page"><div className="grid-3"><Stat label="AI Accuracy" value={`${aiData.ai_accuracy}%`} sub={`${aiData.correct_decisions}/${aiData.total_decisions}`} color={aiData.ai_accuracy >= 50 ? 'var(--green)' : 'var(--red)'} accent="ca-cyan" /><Stat label="Decisions" value={aiData.total_decisions} color="var(--amber)" accent="ca-amber" /><Stat label="Correct" value={aiData.correct_decisions} color="var(--green)" accent="ca-green" /></div>{(aiData.decisions || []).map((d, i) => <div key={i} className="ai-card"><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}><div><span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--amber)', marginRight: 10 }}>{d.symbol}</span><span className={`tag tag-${d.action?.toLowerCase()}`}>{d.action}</span><span className={`tag ${d.outcome === 'WIN' ? 'tag-ok' : 'tag-fail'}`} style={{ marginLeft: 6 }}>{d.outcome}</span></div><div style={{ textAlign: 'right' }}><div style={{ color: d.pnl >= 0 ? 'var(--green)' : 'var(--red)', fontWeight: 800, fontSize: '1.1rem' }}>₹{fmt(d.pnl)}</div><div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>{d.date}</div></div></div><div className="card-label">Reasoning</div>{d.reasoning && Object.entries(d.reasoning).map(([k, v]) => <div key={k} className="ai-step"><span className="ai-step-label">{k.replace('step_', '').replace(/_/g, ' ')}</span><span className="ai-step-val">{v}</span></div>)}<div style={{ marginTop: 12 }}><div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}><span className="c-dim">Confidence</span><span style={{ color: d.confidence >= 70 ? 'var(--green)' : 'var(--amber)' }}>{d.confidence}%</span></div><div className="confidence-bar"><div className="confidence-fill" style={{ width: `${d.confidence}%`, background: d.confidence >= 70 ? 'var(--green)' : 'var(--amber)' }} /></div></div></div>)}</div>); }

function StrategiesPage({ stratPerf }) { if (!stratPerf) return <div className="empty">Loading...</div>; return (<div className="page-enter" data-testid="strategies-page">{(stratPerf.strategies || []).map((s, i) => <div key={i} className="strat-card"><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}><div><div style={{ fontSize: '1.05rem', fontWeight: 800 }}>{s.name}</div><div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{s.type}</div></div><span className={`tag ${s.status === 'ACTIVE' ? 'tag-active' : 'tag-paused'}`}>{s.status}</span></div><div className="strat-meta"><div className="strat-meta-item"><div className="strat-meta-label">Trades</div><div className="strat-meta-val">{s.metrics?.total_trades || 0}</div></div><div className="strat-meta-item"><div className="strat-meta-label">Win Rate</div><div className="strat-meta-val" style={{ color: (s.metrics?.win_rate || 0) >= 50 ? 'var(--green)' : 'var(--red)' }}>{s.metrics?.win_rate || 0}%</div></div><div className="strat-meta-item"><div className="strat-meta-label">P&L</div><div className="strat-meta-val" style={{ color: (s.metrics?.total_pnl || 0) >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{s.metrics?.total_pnl || 0}</div></div><div className="strat-meta-item"><div className="strat-meta-label">Max DD</div><div className="strat-meta-val c-amber">₹{s.metrics?.max_drawdown || 0}</div></div></div>{(s.pnl_history || []).length > 0 && <div style={{ height: 100, marginTop: 10 }}><ResponsiveContainer width="100%" height="100%"><LineChart data={s.pnl_history}><XAxis dataKey="date" tick={false} /><YAxis tick={{ fill: 'var(--text-dim)', fontSize: 9 }} /><Line type="monotone" dataKey="pnl" stroke={s.metrics?.total_pnl >= 0 ? 'var(--green)' : 'var(--red)'} strokeWidth={2} dot={false} /></LineChart></ResponsiveContainer></div>}</div>)}</div>); }

function PositionsPage({ positions }) { const pos = positions?.positions || []; return (<div className="page-enter" data-testid="positions-page"><div className="grid-3"><Stat label="Open" value={pos.length} color="var(--cyan)" accent="ca-cyan" /><Stat label="Unreal P&L" value={`₹${fmt(pos.reduce((s, p) => s + (p.unrealised_pnl || 0), 0))}`} color="var(--green)" accent="ca-green" /><Stat label="Exposure" value={`₹${fmtINR(pos.reduce((s, p) => s + (p.entry_price || 0) * (p.quantity || 0), 0))}`} color="var(--amber)" accent="ca-amber" /></div><div className="card">{pos.length > 0 ? <div className="tbl-wrap"><table><thead><tr><th>Symbol</th><th>Strategy</th><th>Side</th><th>Qty</th><th>Entry</th><th>Current</th><th>SL</th><th>Target</th><th>P&L</th></tr></thead><tbody>{pos.map(p => <tr key={p.symbol}><td style={{ fontWeight: 700, color: 'var(--amber)' }}>{p.symbol}</td><td className="c-dim">{p.strategy}</td><td><span className={`tag tag-${p.action?.toLowerCase()}`}>{p.action}</span></td><td>{p.quantity}</td><td>₹{p.entry_price?.toFixed(2)}</td><td>₹{p.current_price?.toFixed(2)}</td><td className="c-red">₹{p.stop_loss?.toFixed(2)}</td><td className="c-green">₹{p.target?.toFixed(2)}</td><td style={{ color: p.unrealised_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{fmt(p.unrealised_pnl || 0)}</td></tr>)}</tbody></table></div> : <div className="empty">No positions</div>}</div></div>); }

function TradesPage({ tradesData }) { const [filter, setFilter] = useState('all'); const [sel, setSel] = useState(null); if (!tradesData) return <div className="empty">Loading...</div>; let trades = tradesData.trades || []; if (filter === 'wins') trades = trades.filter(t => t.pnl > 0); if (filter === 'loss') trades = trades.filter(t => t.pnl <= 0); const tp = trades.reduce((s, t) => s + (t.pnl || 0), 0); return (<div className="page-enter" data-testid="trades-page"><TradeModal trade={sel} onClose={() => setSel(null)} /><div className="grid-3"><Stat label="Total" value={trades.length} color="var(--cyan)" accent="ca-cyan" /><Stat label="W / L" value={`${trades.filter(t => t.pnl > 0).length} / ${trades.filter(t => t.pnl <= 0).length}`} color="var(--amber)" accent="ca-amber" /><Stat label="Net P&L" value={`₹${fmt(tp)}`} color={tp >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" /></div><div style={{ marginBottom: 14 }}><select data-testid="trade-filter" value={filter} onChange={e => setFilter(e.target.value)}><option value="all">All</option><option value="wins">Wins</option><option value="loss">Losses</option></select></div><div className="card"><div className="tbl-wrap">{trades.length > 0 ? <table><thead><tr><th>Date</th><th>Stock</th><th>Strategy</th><th>Side</th><th>Qty</th><th>Entry</th><th>Exit</th><th>P&L</th><th>Reason</th><th>Score</th><th></th></tr></thead><tbody>{trades.slice(0, 50).map((t, i) => <tr key={i} style={{ cursor: 'pointer' }} onClick={() => setSel(t)}><td className="c-dim">{t.date}</td><td style={{ fontWeight: 700, color: 'var(--amber)' }}>{t.symbol}</td><td className="c-dim" style={{ fontSize: '0.78rem' }}>{t.strategy || '--'}</td><td><span className={`tag tag-${t.action?.toLowerCase()}`}>{t.action}</span></td><td>{t.qty}</td><td>₹{t.entry?.toFixed(2)}</td><td>₹{t.exit?.toFixed(2)}</td><td style={{ color: t.pnl >= 0 ? 'var(--green)' : 'var(--red)', fontWeight: 700 }}>₹{fmt(t.pnl)}</td><td><span className={`tag ${t.reason?.includes('TARGET') ? 'tag-ok' : t.reason?.includes('STOP') ? 'tag-fail' : 'tag-warn'}`}>{t.reason}</span></td><td style={{ color: 'var(--cyan)' }}>{t.score}</td><td><ChevronRight size={14} className="c-dim" /></td></tr>)}</tbody></table> : <div className="empty">No trades</div>}</div></div></div>); }

function RiskPage({ risk }) { if (!risk) return <div className="empty">Loading...</div>; const lp = risk.loss_pct || 0; const bc = lp > 80 ? 'var(--red)' : lp > 50 ? 'var(--amber)' : 'var(--green)'; return (<div className="page-enter" data-testid="risk-page"><div className="grid-4"><Stat label="Loss Used" value={`₹${risk.loss_used?.toFixed(0) || 0}`} sub={`₹${risk.loss_remaining?.toFixed(0)} left`} color="var(--red)" accent="ca-red" /><Stat label="Loss Limit (5%)" value={`₹${risk.daily_loss_limit?.toFixed(0) || 2500}`} color="var(--amber)" accent="ca-amber" /><Stat label="Day P&L" value={`₹${fmt(risk.day_pnl || 0)}`} color={risk.day_pnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" /><Stat label="Open Risk" value={`₹${risk.open_risk?.toFixed(0) || 0}`} color="var(--purple)" accent="ca-purple" /></div><div className="grid-2"><div className="card"><div className="card-head"><span className="card-head-title">Loss Meter</span><span className={`tag ${risk.risk_level === 'SAFE' ? 'tag-safe' : risk.risk_level === 'WARNING' ? 'tag-warn' : 'tag-danger'}`}>{risk.risk_level}</span></div><div className="risk-gauge"><div className="risk-pct" style={{ color: bc }}>{lp.toFixed(0)}%</div></div><div className="prog-bar" style={{ height: 12 }}><div className="prog-fill" style={{ width: `${Math.min(100, lp)}%`, background: bc }} /></div><div style={{ textAlign: 'center', marginTop: 14, fontSize: '1.1rem', fontWeight: 800, color: risk.trading_allowed ? 'var(--green)' : 'var(--red)' }}>{risk.trading_allowed ? 'TRADING ACTIVE' : 'TRADING HALTED'}</div></div><div className="card"><div className="card-head"><span className="card-head-title">Risk Rules</span></div><table><tbody>{[['Max Loss/Day', '5% (₹2,500)'], ['Max Drawdown', `${risk.max_drawdown}%`], ['Max Risk/Trade', `₹${risk.max_per_trade} (2%)`], ['Order Retries', '3x backoff'], ['Duplicate Block', 'MongoDB'], ['Time Stop', '15 min'], ['SL Phases', 'BE / Lock / Trail']].map(([k, v]) => <tr key={k}><td className="c-dim">{k}</td><td>{v}</td></tr>)}</tbody></table></div></div></div>); }

function FOPage() { const [e, setE] = useState(22000); const [s, setS] = useState(21950); const [t, setT] = useState(22100); const [po, setPo] = useState(50000); const [inst, setInst] = useState('equity'); const [r, setR] = useState(null); const go = async () => { try { const res = await fetch(`${API}/api/fo/calculate?entry=${e}&sl=${s}&target=${t}&portfolio=${po}&instrument=${inst}`); setR(await res.json()); } catch {} }; return (<div className="page-enter" data-testid="fo-page"><div className="grid-2"><div className="card"><div className="card-head"><span className="card-head-title">Calculator</span></div><select data-testid="fo-instrument" value={inst} onChange={ev => setInst(ev.target.value)} style={{ width: '100%', marginBottom: 12 }}><option value="equity">Equity</option><option value="stock_fut">Stock Futures</option><option value="nifty_fut">Nifty Futures (25)</option><option value="banknifty_fut">BankNifty Futures (15)</option></select><div className="card-label">Entry</div><input className="fo-input" data-testid="fo-entry" type="number" value={e} onChange={ev => setE(+ev.target.value)} /><div className="card-label">Stop Loss</div><input className="fo-input" data-testid="fo-sl" type="number" value={s} onChange={ev => setS(+ev.target.value)} /><div className="card-label">Target</div><input className="fo-input" data-testid="fo-target" type="number" value={t} onChange={ev => setT(+ev.target.value)} /><div className="card-label">Portfolio</div><input className="fo-input" type="number" value={po} onChange={ev => setPo(+ev.target.value)} /><button className="fo-btn" data-testid="fo-calculate" onClick={go} style={{ width: '100%' }}>CALCULATE</button></div><div className="card"><div className="card-head"><span className="card-head-title">Results</span></div>{r ? Object.entries(r).map(([k, v]) => <div key={k} className="fo-row"><span className="c-dim">{k.replace(/_/g, ' ')}</span><span style={{ fontWeight: 600 }}>{typeof v === 'number' ? (k.includes('pct') ? `${v}%` : k === 'rr_ratio' ? `${v}:1` : `₹${v}`) : v}</span></div>) : <div className="empty">Enter values</div>}</div></div></div>); }

function AuditPage({ logs, audit }) { const tc = { BOT_START: 'var(--green)', SIGNAL_GENERATED: 'var(--cyan)', ORDER_PLACED: 'var(--green)', ORDER_FAILED: 'var(--red)', TRADE_EXITED: 'var(--blue)', RISK_HALT: 'var(--red)', MODE_SWITCH: 'var(--purple)' }; return (<div className="page-enter" data-testid="audit-page">{audit && <div className="card" style={{ marginBottom: 16 }}><div className="card-head"><span className="card-head-title">Audit</span><span className={`tag ${audit.all_fixed ? 'tag-ok' : 'tag-fail'}`}>{audit.all_fixed ? 'ALL FIXED' : 'ISSUES'}</span></div><div className="grid-4" style={{ marginBottom: 8 }}><div style={{ textAlign: 'center' }}><div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--red)' }}>{audit.critical}</div><div className="card-label">Critical</div></div><div style={{ textAlign: 'center' }}><div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--amber)' }}>{audit.high}</div><div className="card-label">High</div></div><div style={{ textAlign: 'center' }}><div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--blue)' }}>{audit.medium}</div><div className="card-label">Medium</div></div><div style={{ textAlign: 'center' }}><div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--text-dim)' }}>{audit.low}</div><div className="card-label">Low</div></div></div><div className="tbl-wrap"><table><thead><tr><th>#</th><th>Severity</th><th>Category</th><th>Issue</th><th>Fix</th><th>Status</th></tr></thead><tbody>{(audit.issues || []).map(iss => <tr key={iss.id}><td>{iss.id}</td><td><span className={`tag ${iss.severity === 'CRITICAL' ? 'tag-fail' : iss.severity === 'HIGH' ? 'tag-warn' : 'tag-info'}`}>{iss.severity}</span></td><td>{iss.category}</td><td style={{ whiteSpace: 'normal' }}>{iss.description}</td><td className="c-muted" style={{ whiteSpace: 'normal' }}>{iss.fix}</td><td><span className="tag tag-ok">{iss.status}</span></td></tr>)}</tbody></table></div></div>}<div className="card"><div className="card-head"><span className="card-head-title">Logs</span></div>{(logs || []).length > 0 ? <div style={{ maxHeight: 400, overflowY: 'auto' }}>{logs.map((l, i) => <div key={i} className="log-entry"><span className="log-time">{l.timestamp?.slice(11, 19)}</span><span className="log-type" style={{ color: tc[l.event_type] || 'var(--text-muted)' }}>{l.event_type}</span><span className="log-msg">{l.message}</span></div>)}</div> : <div className="empty">No logs</div>}</div></div>); }

function SettingsPage({ config }) { if (!config) return <div className="empty">Loading...</div>; return (<div className="page-enter" data-testid="settings-page"><div className="grid-2"><div className="card"><div className="card-head"><span className="card-head-title">Trading</span></div><table><tbody>{[['Portfolio', `₹${fmtINR(config.portfolio_value)}`], ['Max Risk/Trade', `₹${(config.portfolio_value * config.max_risk_pct / 100).toFixed(0)} (${config.max_risk_pct}%)`], ['Daily Loss Limit', `₹${config.daily_loss_limit?.toFixed(0)} (5%)`], ['Max Drawdown', `${config.max_drawdown_pct}%`], ['Selective', `₹${config.daily_profit_selective}`], ['Stop All', `₹${config.daily_profit_stop}`], ['Min Score', `${config.min_signal_score}/10`], ['Retries', `${config.order_max_retries}x`], ['RR', `1:${config.risk_reward_ratio}`], ['EMA', `${config.ema_fast}/${config.ema_slow}`]].map(([k, v]) => <tr key={k}><td className="c-dim">{k}</td><td>{v}</td></tr>)}</tbody></table></div><div className="card"><div className="card-head"><span className="card-head-title">System</span></div><table><tbody><tr><td className="c-dim">Mode</td><td><span className={`tag ${config.trading_mode === 'live' ? 'tag-ok' : 'tag-paper'}`}>{config.trading_mode?.toUpperCase()}</span></td></tr><tr><td className="c-dim">Broker</td><td><span className={`tag ${config.kite_configured ? 'tag-ok' : 'tag-fail'}`}>Zerodha {config.kite_configured ? '(OK)' : '(No Token)'}</span></td></tr><tr><td className="c-dim">Telegram</td><td><span className={`tag ${config.telegram_configured ? 'tag-ok' : 'tag-fail'}`}>{config.telegram_configured ? 'Connected' : 'Not Set'}</span></td></tr><tr><td className="c-dim">Hours</td><td>{config.market_open} - {config.market_close}</td></tr><tr><td className="c-dim">Leverage</td><td>{config.max_leverage}x</td></tr></tbody></table></div></div></div>); }

/* ═══ MAIN ═══ */
const NAV = [
  { group: 'Monitor', items: [{ id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard }, { id: 'portfolio', label: 'Portfolio', icon: TrendingUp }, { id: 'report', label: 'Daily Report', icon: FileText }, { id: 'health', label: 'System Health', icon: HeartPulse }] },
  { group: 'Market', items: [{ id: 'market', label: 'Market Analysis', icon: ScanSearch }, { id: 'ai', label: 'AI Brain', icon: BrainCircuit }, { id: 'strategies', label: 'Strategies', icon: Activity }] },
  { group: 'Trading', items: [{ id: 'positions', label: 'Positions', icon: Target }, { id: 'trades', label: 'Trade History', icon: ListOrdered }, { id: 'risk', label: 'Risk', icon: ShieldAlert }] },
  { group: 'Tools', items: [{ id: 'fo', label: 'F&O Calculator', icon: Calculator }, { id: 'audit', label: 'Audit & Logs', icon: ScrollText }, { id: 'settings', label: 'Settings', icon: Settings }] },
];
const TITLES = { dashboard: 'Dashboard', portfolio: 'Portfolio', report: 'Daily Report', health: 'System Health', market: 'Market Analysis', ai: 'AI Brain', strategies: 'Strategies', positions: 'Positions', trades: 'Trade History', risk: 'Risk', fo: 'F&O Calculator', audit: 'Audit & Logs', settings: 'Settings' };

function App() {
  const [authed, setAuthed] = useState(() => localStorage.getItem("mm_authed") === "true");
  const [page, setPage] = useState('dashboard');
  const [clock, setClock] = useState('');
  const [mktOpen, setMktOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  const [mode, setMode] = useState('PAPER');

  const [data, setData] = useState({});
  const [portfolio, setPortfolio] = useState(null);
  const [report, setReport] = useState(null);
  const [health, setHealth] = useState(null);
  const [risk, setRisk] = useState(null);
  const [market, setMarket] = useState(null);
  const [regime, setRegime] = useState(null);
  const [aiData, setAiData] = useState(null);
  const [stratPerf, setStratPerf] = useState(null);
  const [positions, setPositions] = useState(null);
  const [tradesData, setTradesData] = useState(null);
  const [logs, setLogs] = useState([]);
  const [audit, setAudit] = useState(null);
  const [config, setConfig] = useState(null);

  const toggleTheme = () => { const t = theme === 'dark' ? 'light' : 'dark'; setTheme(t); localStorage.setItem('theme', t); };
  useEffect(() => { document.documentElement.setAttribute('data-theme', theme); }, [theme]);

  const f = useCallback(async (url, setter) => { try { const r = await fetch(`${API}${url}`); setter(await r.json()); } catch {} }, []);
  const loadDash = useCallback(() => f('/api/data', setData), [f]);
  const loadHealth = useCallback(() => f('/api/health', setHealth), [f]);
  const loadRisk = useCallback(() => f('/api/risk', setRisk), [f]);
  const loadRegime = useCallback(() => f('/api/ai/regime', setRegime), [f]);
  const loadMarket = useCallback(() => f('/api/market/live', setMarket), [f]);
  const loadConfig = useCallback(() => f('/api/config', setConfig), [f]);
  const loadAudit = useCallback(() => f('/api/audit', setAudit), [f]);
  const loadMode = useCallback(() => f('/api/mode', d => setMode(d.mode || 'PAPER')), [f]);

  useEffect(() => { if (!authed) return; loadDash(); loadHealth(); loadRisk(); loadConfig(); loadAudit(); loadRegime(); loadMode(); const t1 = setInterval(loadDash, 15000); const t2 = setInterval(() => { loadHealth(); loadRegime(); }, 30000); const t3 = setInterval(loadRisk, 20000); return () => { clearInterval(t1); clearInterval(t2); clearInterval(t3); }; }, [authed, loadDash, loadHealth, loadRisk, loadConfig, loadAudit, loadRegime, loadMode]);

  useEffect(() => { const tick = () => { const ist = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Kolkata' })); setClock(ist.toTimeString().substr(0, 8) + ' IST'); const h = ist.getHours(), m = ist.getMinutes(); setMktOpen((h > 9 || (h === 9 && m >= 15)) && (h < 15 || (h === 15 && m < 30))); }; tick(); const t = setInterval(tick, 1000); return () => clearInterval(t); }, []);

  const switchMode = async (newMode) => {
    if (newMode === 'LIVE' && !window.confirm('Switch to LIVE trading? Real orders will be placed through Zerodha.')) return;
    try { const r = await fetch(`${API}/api/mode/switch`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: newMode.toLowerCase() }) }); const d = await r.json(); if (d.ok) setMode(d.mode); else alert(d.error || 'Failed'); } catch { alert('Connection error'); }
  };

  const nav = id => { setPage(id); setSidebarOpen(false); if (id === 'portfolio') f('/api/portfolio', setPortfolio); if (id === 'report') f('/api/report/daily', setReport); if (id === 'market') { loadMarket(); loadRegime(); } if (id === 'ai') f('/api/ai-decisions', setAiData); if (id === 'strategies') f('/api/strategies/performance', setStratPerf); if (id === 'positions') f('/api/open-positions', setPositions); if (id === 'trades') f('/api/trades', setTradesData); if (id === 'audit') { f('/api/logs?limit=100', d => setLogs(d.logs || [])); loadAudit(); } if (id === 'settings') loadConfig(); };

  if (!authed) return <LoginPage onLogin={() => setAuthed(true)} theme={theme} toggleTheme={toggleTheme} />;
  const p = data.day_pnl || 0;
  const sc = { NORMAL: 'var(--green)', SELECTIVE: 'var(--amber)', HALTED: 'var(--red)', PROTECTED: 'var(--blue)' };

  return (
    <div className="app-layout" data-testid="app-layout">
      <button className="mobile-toggle" data-testid="mobile-menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>{sidebarOpen ? <X size={22} /> : <Menu size={22} />}</button>
      <div className={`sidebar-overlay ${sidebarOpen ? 'show' : ''}`} onClick={() => setSidebarOpen(false)} />
      <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-logo"><h1>MINIMAX</h1><p>PRO TERMINAL</p></div>
        <nav className="sidebar-nav">{NAV.map(g => <React.Fragment key={g.group}><div className="nav-group">{g.group}</div>{g.items.map(item => <div key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => nav(item.id)} data-testid={`nav-${item.id}`}><item.icon size={18} /><span>{item.label}</span></div>)}</React.Fragment>)}</nav>
        <div className="sidebar-footer"><div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}><span className="status-dot" style={{ background: sc[data.agent_state] || 'var(--green)' }} /><span style={{ color: sc[data.agent_state] || 'var(--green)', fontWeight: 600 }}>{data.agent_state || 'NORMAL'}</span></div><span style={{ color: 'var(--text-dim)' }}>MODE: <span style={{ color: mode === 'LIVE' ? 'var(--green)' : 'var(--purple)', fontWeight: 700 }}>{mode}</span></span></div>
      </div>
      <div className="main-content">
        <div className="topbar">
          <div className="topbar-title">{TITLES[page]}</div>
          <div className="topbar-right">
            <div className="mode-switch" data-testid="mode-switch">
              <button className={`mode-btn ${mode === 'PAPER' ? 'active-sim' : 'inactive'}`} onClick={() => switchMode('PAPER')} data-testid="mode-sim">SIM</button>
              <button className={`mode-btn ${mode === 'LIVE' ? 'active-live' : 'inactive'}`} onClick={() => switchMode('LIVE')} data-testid="mode-live">LIVE</button>
            </div>
            <span style={{ color: 'var(--text-dim)' }}>NSE <span className="blink" style={{ color: mktOpen ? 'var(--green)' : 'var(--red)' }}>●</span></span>
            <span className="pill pill-pnl" style={{ background: p >= 0 ? 'var(--green-bg)' : 'var(--red-bg)', color: p >= 0 ? 'var(--green)' : 'var(--red)', borderColor: p >= 0 ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)' }}>₹{fmt(p)}</span>
            <button className="theme-toggle" onClick={toggleTheme} data-testid="theme-toggle">{theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}</button>
            <span className="clock">{clock}</span>
          </div>
        </div>
        <div className="content-area">
          {page === 'dashboard' && <DashboardPage data={data} regime={regime} />}
          {page === 'portfolio' && <PortfolioPage portfolio={portfolio} />}
          {page === 'report' && <ReportPage report={report} />}
          {page === 'health' && <HealthPage health={health} />}
          {page === 'market' && <MarketPage market={market} regime={regime} loadMarket={loadMarket} />}
          {page === 'ai' && <AIBrainPage aiData={aiData} />}
          {page === 'strategies' && <StrategiesPage stratPerf={stratPerf} />}
          {page === 'positions' && <PositionsPage positions={positions} />}
          {page === 'trades' && <TradesPage tradesData={tradesData} />}
          {page === 'risk' && <RiskPage risk={risk} />}
          {page === 'fo' && <FOPage />}
          {page === 'audit' && <AuditPage logs={logs} audit={audit} />}
          {page === 'settings' && <SettingsPage config={config} />}
        </div>
      </div>
    </div>
  );
}

export default App;
