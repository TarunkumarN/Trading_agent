import React, { useCallback, useEffect, useMemo, useState } from 'react';
import './App.css';
import { LayoutDashboard, HeartPulse, ScanSearch, BrainCircuit, Target, ListOrdered, ShieldAlert, TrendingUp, Calculator, Settings, ScrollText, Activity, Menu, X, Sun, Moon, FileText } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ComposedChart } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL;
const fmt = n => (n >= 0 ? '+' : '') + Number(n || 0).toFixed(2);
const fmtINR = n => new Intl.NumberFormat('en-IN').format(Math.round(Number(n || 0)));

function Stat({ label, value, sub, color }) {
  return <div className="card"><div className="card-label">{label}</div><div className="metric" style={{ color: color || 'var(--text)' }}>{value}</div>{sub && <div className="metric-sub">{sub}</div>}</div>;
}

function LoginPage({ onLogin, theme, toggleTheme }) {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [error, setError] = useState('');
  const go = async () => {
    try {
      const r = await fetch(`${API}/api/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user, pass }) });
      const d = await r.json();
      if (d.ok) { localStorage.setItem('mm_authed', 'true'); onLogin(); } else setError('Invalid credentials');
    } catch { setError('Connection failed'); }
  };
  return <div className="login-wrap"><div className="login-box"><div style={{ display: 'flex', justifyContent: 'space-between' }}><div><h1>MINIMAX</h1><p>PRO TRADING TERMINAL</p></div><button className="theme-toggle" onClick={toggleTheme}>{theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}</button></div><input type="text" placeholder="Username" value={user} onChange={e => setUser(e.target.value)} /><input type="password" placeholder="Password" value={pass} onChange={e => setPass(e.target.value)} onKeyDown={e => e.key === 'Enter' && go()} /><button className="login-btn" onClick={go}>ACCESS TERMINAL</button>{error && <div className="login-error">{error}</div>}</div></div>;
}

function DashboardPage({ data }) {
  return <div className="page-enter"><div className="grid-4"><Stat label="Day P&L" value={`Rs ${fmt(data.day_pnl || 0)}`} color={(data.day_pnl || 0) >= 0 ? 'var(--green)' : 'var(--red)'} /><Stat label="Trades Today" value={data.total_trades || 0} /><Stat label="Win Rate" value={`${data.win_rate || 0}%`} /><Stat label="Portfolio" value={`Rs ${fmtINR(data.portfolio_value || 0)}`} /></div><div className="card" style={{ marginTop: 16 }}><div className="card-head"><span className="card-head-title">Intraday P&L</span></div><div style={{ height: 220 }}><ResponsiveContainer width="100%" height="100%"><LineChart data={data.pnl_curve || []}><CartesianGrid strokeDasharray="3 3" stroke="var(--border)" /><XAxis dataKey="time" /><YAxis /><Tooltip /><Line type="monotone" dataKey="pnl" stroke="var(--green)" strokeWidth={2} dot={false} /></LineChart></ResponsiveContainer></div></div></div>;
}

function PortfolioPage({ portfolio }) {
  if (!portfolio) return <div className="empty">Loading...</div>;
  return <div className="page-enter"><div className="grid-4"><Stat label="Initial Capital" value={`Rs ${fmtINR(portfolio.initial_capital)}`} /><Stat label="Equity" value={`Rs ${fmtINR(portfolio.current_equity)}`} /><Stat label="Total P&L" value={`Rs ${fmt(portfolio.total_pnl)}`} color={portfolio.total_pnl >= 0 ? 'var(--green)' : 'var(--red)'} /><Stat label="Open P&L" value={`Rs ${fmt(portfolio.unrealised_pnl)}`} /></div></div>;
}

function ReportPage({ report }) {
  const [current, setCurrent] = useState(report);
  const [date, setDate] = useState(report?.date || '');
  useEffect(() => { setCurrent(report); setDate(report?.date || ''); }, [report]);
  const loadDate = async value => { try { const r = await fetch(`${API}/api/report/daily?date=${value}`); const d = await r.json(); setCurrent(d); setDate(d.date || value); } catch {} };
  if (!current) return <div className="empty">Loading report...</div>;
  const dates = current.available_dates || (current.date ? [current.date] : []);
  return <div className="page-enter"><div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12, gap: 12, flexWrap: 'wrap' }}><div className="card-label">Daily report</div><select value={date} onChange={e => loadDate(e.target.value)}>{dates.map(d => <option key={d} value={d}>{d}</option>)}</select></div><div className="grid-4"><Stat label="Trades" value={current.total_trades || 0} /><Stat label="Wins / Losses" value={`${current.winning_trades || 0} / ${current.losing_trades || 0}`} /><Stat label="Day P&L" value={`Rs ${fmt(current.daily_pnl || 0)}`} color={(current.daily_pnl || 0) >= 0 ? 'var(--green)' : 'var(--red)'} /><Stat label="Portfolio" value={`Rs ${fmtINR(current.portfolio_value || 0)}`} /></div><div className="card" style={{ marginTop: 16 }}><div className="card-head"><span className="card-head-title">Performance Metrics</span></div><div className="fo-row"><span className="c-dim">Avg Profit</span><span>Rs {fmt(current.avg_profit || 0)}</span></div><div className="fo-row"><span className="c-dim">Avg Loss</span><span>Rs {fmt(current.avg_loss || 0)}</span></div><div className="fo-row"><span className="c-dim">Profit Factor</span><span>{current.profit_factor || 0}x</span></div><div className="fo-row"><span className="c-dim">Best Trade</span><span>{current.best_trade ? `${current.best_trade.symbol} (${fmt(current.best_trade.pnl || 0)})` : '--'}</span></div><div className="fo-row"><span className="c-dim">Worst Trade</span><span>{current.worst_trade ? `${current.worst_trade.symbol} (${fmt(current.worst_trade.pnl || 0)})` : '--'}</span></div></div><div className="card" style={{ marginTop: 16 }}><div className="card-head"><span className="card-head-title">Strategy Breakdown</span></div>{(current.strategy_performance || []).length ? <div className="tbl-wrap"><table><thead><tr><th>Strategy</th><th>Trades</th><th>Win%</th><th>P&L</th></tr></thead><tbody>{current.strategy_performance.map((s, i) => <tr key={i}><td>{s.name}</td><td>{s.trades}</td><td>{s.win_rate}%</td><td style={{ color: s.pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>Rs {fmt(s.pnl)}</td></tr>)}</tbody></table></div> : <div className="empty">No strategy data</div>}</div></div>;
}

function PositionsPage({ positions }) {
  const pos = positions?.positions || [];
  const exposure = pos.reduce((sum, p) => sum + (p.entry_price || p.entry || 0) * (p.quantity || p.qty || 0), 0);
  return <div className="page-enter"><div className="grid-3"><Stat label="Open" value={pos.length} /><Stat label="Unreal P&L" value={`Rs ${fmt(pos.reduce((s, p) => s + (p.unrealised_pnl || 0), 0))}`} /><Stat label="Exposure" value={`Rs ${fmtINR(exposure)}`} /></div><div className="card" style={{ marginTop: 16 }}>{pos.length ? <div className="tbl-wrap"><table><thead><tr><th>Symbol</th><th>Strategy</th><th>Side</th><th>Qty</th><th>Entry</th><th>Current</th><th>SL</th><th>Target</th><th>P&L</th></tr></thead><tbody>{pos.map(p => <tr key={p.symbol}><td>{p.symbol}</td><td>{p.strategy || '--'}</td><td>{p.action}</td><td>{p.quantity || p.qty}</td><td>{Number(p.entry_price || p.entry || 0).toFixed(2)}</td><td>{Number(p.current_price || 0).toFixed(2)}</td><td>{Number(p.stop_loss || p.sl || 0).toFixed(2)}</td><td>{Number(p.target || 0).toFixed(2)}</td><td style={{ color: p.unrealised_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>Rs {fmt(p.unrealised_pnl || 0)}</td></tr>)}</tbody></table></div> : <div className="empty">No positions</div>}</div></div>;
}

function TradesPage({ tradesData }) {
  const [outcome, setOutcome] = useState('all');
  const [date, setDate] = useState('all');
  if (!tradesData) return <div className="empty">Loading...</div>;
  let trades = tradesData.trades || [];
  if (date !== 'all') trades = trades.filter(t => t.date === date);
  if (outcome === 'wins') trades = trades.filter(t => t.pnl > 0);
  if (outcome === 'loss') trades = trades.filter(t => t.pnl <= 0);
  return <div className="page-enter"><div className="grid-3"><Stat label="Total" value={trades.length} /><Stat label="Wins / Losses" value={`${trades.filter(t => t.pnl > 0).length} / ${trades.filter(t => t.pnl <= 0).length}`} /><Stat label="Net P&L" value={`Rs ${fmt(trades.reduce((s, t) => s + (t.pnl || 0), 0))}`} /></div><div style={{ marginTop: 16, marginBottom: 12, display: 'flex', gap: 10, flexWrap: 'wrap' }}><select value={outcome} onChange={e => setOutcome(e.target.value)}><option value="all">All</option><option value="wins">Wins</option><option value="loss">Losses</option></select><select value={date} onChange={e => setDate(e.target.value)}><option value="all">All Dates</option>{(tradesData.available_dates || []).map(d => <option key={d} value={d}>{d}</option>)}</select></div><div className="card">{trades.length ? <div className="tbl-wrap"><table><thead><tr><th>Date</th><th>Stock</th><th>Strategy</th><th>Side</th><th>Qty</th><th>Entry</th><th>Exit</th><th>P&L</th><th>Reason</th><th>Score</th></tr></thead><tbody>{trades.map((t, i) => <tr key={t.id || i}><td>{t.date}</td><td>{t.symbol}</td><td>{t.strategy || '--'}</td><td>{t.action}</td><td>{t.qty}</td><td>{Number(t.entry || 0).toFixed(2)}</td><td>{Number(t.exit || 0).toFixed(2)}</td><td style={{ color: t.pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>Rs {fmt(t.pnl)}</td><td>{t.reason}</td><td>{t.score}</td></tr>)}</tbody></table></div> : <div className="empty">No trades</div>}</div></div>;
}

function MarketPage({ market, regime, loadMarket }) {
  if (!market) return <div className="empty">Loading...</div>;
  const rows = market.all_stocks || market.gainers || [];
  return <div className="page-enter"><div className="grid-3"><Stat label="Advances" value={market.summary?.advances || 0} /><Stat label="Declines" value={market.summary?.declines || 0} /><Stat label="Regime" value={regime?.regime || '--'} /></div><div className="card" style={{ marginBottom: 16 }}><button className="fo-btn" onClick={loadMarket}>Refresh Market</button></div><div className="card">{rows.length ? <div className="tbl-wrap"><table><thead><tr><th>Symbol</th><th>Price</th><th>Change%</th><th>Volume</th></tr></thead><tbody>{rows.slice(0, 25).map(row => <tr key={row.symbol}><td>{row.symbol}</td><td>{row.price}</td><td style={{ color: row.change_pct >= 0 ? 'var(--green)' : 'var(--red)' }}>{row.change_pct}</td><td>{fmtINR(row.volume || 0)}</td></tr>)}</tbody></table></div> : <div className="empty">No data</div>}</div></div>;
}

function ChartPage() {
  const [universe, setUniverse] = useState(null);
  const [symbol, setSymbol] = useState('RELIANCE');
  const [underlying, setUnderlying] = useState('NIFTY');
  const [optionSide, setOptionSide] = useState('CALL');
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/market/universe`).then(r => r.json()).then(data => {
      setUniverse(data);
      if (data?.equities?.[0]?.symbol) setSymbol(data.equities[0].symbol);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!symbol) return;
    fetch(`${API}/api/chart/data?symbol=${encodeURIComponent(symbol)}`).then(r => r.json()).then(setChartData).catch(() => {});
  }, [symbol]);

  useEffect(() => {
    const timer = setInterval(() => {
      if (symbol) {
        fetch(`${API}/api/chart/data?symbol=${encodeURIComponent(symbol)}`).then(r => r.json()).then(setChartData).catch(() => {});
      }
    }, 8000);
    return () => clearInterval(timer);
  }, [symbol]);

  const groups = [
    ['Equities', universe?.equities || []],
    ['F&O', universe?.fno || []],
    ['Commodities', universe?.commodities || []],
  ];

  useEffect(() => {
    if (underlying && optionSide) {
      setSymbol(`${underlying}-${optionSide}`);
    }
  }, [underlying, optionSide]);

  const chartRows = useMemo(() => {
    const candles = chartData?.candles || [];
    const ema20Lookup = new Map((chartData?.ema20 || []).map(row => [row.time, row.value]));
    const ema50Lookup = new Map((chartData?.ema50 || []).map(row => [row.time, row.value]));
    const vwapLookup = new Map((chartData?.vwap || []).map(row => [row.time, row.value]));
    return candles.map(row => ({
      time: row.time,
      open: row.open,
      high: row.high,
      low: row.low,
      close: row.close,
      ema20: ema20Lookup.get(row.time),
      ema50: ema50Lookup.get(row.time),
      vwap: vwapLookup.get(row.time),
      volume: row.volume || 0,
    }));
  }, [chartData]);

  const commodityBadge = chartData?.instrument_type === 'COMMODITY'
    ? (symbol.includes('GOLD') || symbol.includes('SILVER') ? 'Metal breakout / VWAP hold' : 'Crude range expansion')
    : (symbol.includes('CALL') ? 'Bullish option momentum' : symbol.includes('PUT') ? 'Bearish option momentum' : 'Trend / VWAP alignment');

  return <div className="page-enter"><div className="card" style={{ marginBottom: 16 }}><div className="card-head"><span className="card-head-title">Live Chart</span><span className="tag tag-active">{chartData?.instrument_type || '--'}</span></div><div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>{groups.map(([label, rows]) => <select key={label} value={rows.some(row => row.symbol === symbol) ? symbol : ''} onChange={e => e.target.value && setSymbol(e.target.value)}><option value="">{label}</option>{rows.map(row => <option key={row.symbol} value={row.symbol}>{row.symbol}</option>)}</select>)}</div><div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}><select value={underlying} onChange={e => setUnderlying(e.target.value)}>{(universe?.fno || []).map(row => <option key={row.symbol} value={row.symbol}>{row.symbol}</option>)}</select><select value={optionSide} onChange={e => setOptionSide(e.target.value)}><option value="CALL">CALL</option><option value="PUT">PUT</option></select><button className="fo-btn" onClick={() => fetch(`${API}/api/chart/data?symbol=${encodeURIComponent(symbol)}`).then(r => r.json()).then(setChartData).catch(() => {})}>Refresh</button></div><div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}><span className="tag tag-ok">Close</span><span className="tag tag-active">EMA20</span><span className="tag tag-warn">EMA50</span><span className="tag tag-paper">VWAP</span><span className="tag tag-info">{commodityBadge}</span></div><div style={{ width: '100%', height: 420 }}>{chartRows.length ? <ResponsiveContainer width="100%" height="100%"><ComposedChart data={chartRows}><CartesianGrid strokeDasharray="3 3" stroke="var(--border)" /><XAxis dataKey="time" hide /><YAxis domain={['auto', 'auto']} /><Tooltip /><Line type="monotone" dataKey="close" stroke="#22c55e" dot={false} strokeWidth={2} name="Close" /><Line type="monotone" dataKey="ema20" stroke="#06b6d4" dot={false} strokeWidth={2} name="EMA20" /><Line type="monotone" dataKey="ema50" stroke="#eab308" dot={false} strokeWidth={2} name="EMA50" /><Line type="monotone" dataKey="vwap" stroke="#a855f7" dot={false} strokeWidth={2} name="VWAP" /></ComposedChart></ResponsiveContainer> : <div className="empty">No chart data</div>}</div></div><div className="grid-3"><Stat label="Symbol" value={chartData?.symbol || symbol} /><Stat label="Instrument" value={chartData?.instrument_type || '--'} /><Stat label="Candles" value={chartData?.candles?.length || 0} /></div><div className="card" style={{ marginTop: 16, height: 220 }}>{chartRows.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={chartRows}><CartesianGrid strokeDasharray="3 3" stroke="var(--border)" /><XAxis dataKey="time" hide /><YAxis /><Tooltip /><Bar dataKey="volume" fill="#334155" name="Volume" /></BarChart></ResponsiveContainer> : <div className="empty">No volume data</div>}</div></div>;
}

function HealthPage({ health }) {
  if (!health) return <div className="empty">Loading...</div>;
  return <div className="page-enter"><div className="card"><pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(health, null, 2)}</pre></div></div>;
}

function StrategiesPage({ stratPerf }) {
  if (!stratPerf) return <div className="empty">Loading...</div>;
  return <div className="page-enter"><div className="card"><pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(stratPerf, null, 2)}</pre></div></div>;
}

function RiskPage({ risk }) {
  if (!risk) return <div className="empty">Loading...</div>;
  return <div className="page-enter"><div className="grid-3"><Stat label="Loss Used" value={`Rs ${risk.loss_used || 0}`} /><Stat label="Open Risk" value={`Rs ${risk.open_risk || 0}`} /><Stat label="State" value={risk.agent_state || '--'} /></div></div>;
}

function AuditPage({ logs, audit }) {
  return <div className="page-enter"><div className="grid-2"><div className="card"><pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(audit, null, 2)}</pre></div><div className="card"><pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(logs, null, 2)}</pre></div></div></div>;
}

function SettingsPage({ config }) {
  if (!config) return <div className="empty">Loading...</div>;
  return <div className="page-enter"><div className="card"><pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(config, null, 2)}</pre></div></div>;
}

function SimpleJsonPage({ data }) {
  if (!data) return <div className="empty">Loading...</div>;
  return <div className="card"><pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(data, null, 2)}</pre></div>;
}

const NAV = [
  { group: 'Monitor', items: [{ id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard }, { id: 'portfolio', label: 'Portfolio', icon: TrendingUp }, { id: 'report', label: 'Daily Report', icon: FileText }, { id: 'health', label: 'System Health', icon: HeartPulse }] },
  { group: 'Market', items: [{ id: 'market', label: 'Market Analysis', icon: ScanSearch }, { id: 'chart', label: 'Live Charts', icon: Activity }, { id: 'ai', label: 'AI Brain', icon: BrainCircuit }, { id: 'strategies', label: 'Strategies', icon: Activity }] },
  { group: 'Trading', items: [{ id: 'positions', label: 'Positions', icon: Target }, { id: 'trades', label: 'Trade History', icon: ListOrdered }, { id: 'risk', label: 'Risk', icon: ShieldAlert }] },
  { group: 'Tools', items: [{ id: 'fo', label: 'F&O Calculator', icon: Calculator }, { id: 'audit', label: 'Audit & Logs', icon: ScrollText }, { id: 'settings', label: 'Settings', icon: Settings }] },
];

const TITLES = { dashboard: 'Dashboard', portfolio: 'Portfolio', report: 'Daily Report', health: 'System Health', market: 'Market Analysis', chart: 'Live Charts', ai: 'AI Brain', strategies: 'Strategies', positions: 'Positions', trades: 'Trade History', risk: 'Risk', fo: 'F&O Calculator', audit: 'Audit & Logs', settings: 'Settings' };

function App() {
  const [authed, setAuthed] = useState(() => localStorage.getItem('mm_authed') === 'true');
  const [page, setPage] = useState('dashboard');
  const [clock, setClock] = useState('');
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
  const [logs, setLogs] = useState(null);
  const [audit, setAudit] = useState(null);
  const [config, setConfig] = useState(null);

  const toggleTheme = () => { const t = theme === 'dark' ? 'light' : 'dark'; setTheme(t); localStorage.setItem('theme', t); };
  useEffect(() => { document.documentElement.setAttribute('data-theme', theme); }, [theme]);
  const f = useCallback(async (url, setter) => { try { const r = await fetch(`${API}${url}`); setter(await r.json()); } catch {} }, []);
  const loadDash = useCallback(() => f('/api/data', setData), [f]);
  useEffect(() => { if (!authed) return; loadDash(); f('/api/health', setHealth); f('/api/risk', setRisk); f('/api/config', setConfig); f('/api/audit', setAudit); f('/api/ai/regime', setRegime); f('/api/mode', d => setMode(d.mode || 'PAPER')); const t = setInterval(loadDash, 15000); return () => clearInterval(t); }, [authed, f, loadDash]);
  useEffect(() => { const tick = () => { const ist = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Kolkata' })); setClock(ist.toTimeString().substr(0, 8) + ' IST'); }; tick(); const t = setInterval(tick, 1000); return () => clearInterval(t); }, []);

  const nav = id => {
    setPage(id);
    setSidebarOpen(false);
    if (id === 'portfolio') f('/api/portfolio', setPortfolio);
    if (id === 'report') f('/api/report/daily', setReport);
    if (id === 'market') f('/api/market/live', setMarket);
    if (id === 'chart') f('/api/market/universe', () => {});
    if (id === 'ai') f('/api/ai-decisions', setAiData);
    if (id === 'strategies') f('/api/strategies/performance', setStratPerf);
    if (id === 'positions') f('/api/open-positions', setPositions);
    if (id === 'trades') f('/api/trades', setTradesData);
    if (id === 'risk') f('/api/risk', setRisk);
    if (id === 'audit') { f('/api/logs?limit=100', d => setLogs(d.logs || [])); f('/api/audit', setAudit); }
    if (id === 'settings') f('/api/config', setConfig);
  };

  if (!authed) return <LoginPage onLogin={() => setAuthed(true)} theme={theme} toggleTheme={toggleTheme} />;
  return (
    <div className="app-layout">
      <button className="mobile-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>{sidebarOpen ? <X size={22} /> : <Menu size={22} />}</button>
      <div className={`sidebar-overlay ${sidebarOpen ? 'show' : ''}`} onClick={() => setSidebarOpen(false)} />
      <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-logo"><h1>MINIMAX</h1><p>PRO TERMINAL</p></div>
        <nav className="sidebar-nav">{NAV.map(g => <React.Fragment key={g.group}><div className="nav-group">{g.group}</div>{g.items.map(item => <div key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => nav(item.id)}><item.icon size={18} /><span>{item.label}</span></div>)}</React.Fragment>)}</nav>
      </div>
      <div className="main-content">
        <div className="topbar"><div className="topbar-title">{TITLES[page]}</div><div className="topbar-right"><span style={{ color: 'var(--text-dim)' }}>MODE: {mode}</span><button className="theme-toggle" onClick={toggleTheme}>{theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}</button><span className="clock">{clock}</span></div></div>
        <div className="content-area">
          {page === 'dashboard' && <DashboardPage data={data} />}
          {page === 'portfolio' && <PortfolioPage portfolio={portfolio} />}
          {page === 'report' && <ReportPage report={report} />}
          {page === 'health' && <HealthPage health={health} />}
          {page === 'market' && <MarketPage market={market} regime={regime} loadMarket={() => f('/api/market/live', setMarket)} />}
          {page === 'chart' && <ChartPage />}
          {page === 'ai' && <SimpleJsonPage data={aiData} />}
          {page === 'strategies' && <StrategiesPage stratPerf={stratPerf} />}
          {page === 'positions' && <PositionsPage positions={positions} />}
          {page === 'trades' && <TradesPage tradesData={tradesData} />}
          {page === 'risk' && <RiskPage risk={risk} />}
          {page === 'fo' && <SimpleJsonPage data={{ message: 'Use F&O calculator in backend endpoint /api/fo/calculate' }} />}
          {page === 'audit' && <AuditPage logs={logs} audit={audit} />}
          {page === 'settings' && <SettingsPage config={config} />}
        </div>
      </div>
    </div>
  );
}

export default App;
