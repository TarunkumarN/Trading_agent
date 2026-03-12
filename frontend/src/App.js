import React, { useCallback, useEffect, useState } from 'react';
import './App.css';
import { LayoutDashboard, HeartPulse, ScanSearch, BrainCircuit, Target, ListOrdered, ShieldAlert, TrendingUp, Calculator, Settings, ScrollText, Activity, Menu, X, Sun, Moon, FileText } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

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
  return <div className="page-enter"><div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12, gap: 12, flexWrap: 'wrap' }}><div className="card-label">Daily report</div><select value={date} onChange={e => loadDate(e.target.value)}>{(current.available_dates || []).map(d => <option key={d} value={d}>{d}</option>)}</select></div><div className="grid-4"><Stat label="Trades" value={current.total_trades || 0} /><Stat label="Wins / Losses" value={`${current.winning_trades || 0} / ${current.losing_trades || 0}`} /><Stat label="Day P&L" value={`Rs ${fmt(current.daily_pnl || 0)}`} color={(current.daily_pnl || 0) >= 0 ? 'var(--green)' : 'var(--red)'} /><Stat label="Profit Factor" value={current.profit_factor || 0} /></div><div className="card" style={{ marginTop: 16 }}><div className="card-head"><span className="card-head-title">Strategy Breakdown</span></div>{(current.strategy_performance || []).length ? <div className="tbl-wrap"><table><thead><tr><th>Strategy</th><th>Trades</th><th>Win%</th><th>P&L</th></tr></thead><tbody>{current.strategy_performance.map((s, i) => <tr key={i}><td>{s.name}</td><td>{s.trades}</td><td>{s.win_rate}%</td><td style={{ color: s.pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>Rs {fmt(s.pnl)}</td></tr>)}</tbody></table></div> : <div className="empty">No strategy data</div>}</div></div>;
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

function SimpleJsonPage({ data }) {
  if (!data) return <div className="empty">Loading...</div>;
  return <div className="card"><pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(data, null, 2)}</pre></div>;
}

const NAV = [
  { group: 'Monitor', items: [{ id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard }, { id: 'portfolio', label: 'Portfolio', icon: TrendingUp }, { id: 'report', label: 'Daily Report', icon: FileText }, { id: 'health', label: 'System Health', icon: HeartPulse }] },
  { group: 'Market', items: [{ id: 'market', label: 'Market Analysis', icon: ScanSearch }, { id: 'ai', label: 'AI Brain', icon: BrainCircuit }, { id: 'strategies', label: 'Strategies', icon: Activity }] },
  { group: 'Trading', items: [{ id: 'positions', label: 'Positions', icon: Target }, { id: 'trades', label: 'Trade History', icon: ListOrdered }, { id: 'risk', label: 'Risk', icon: ShieldAlert }] },
  { group: 'Tools', items: [{ id: 'fo', label: 'F&O Calculator', icon: Calculator }, { id: 'audit', label: 'Audit & Logs', icon: ScrollText }, { id: 'settings', label: 'Settings', icon: Settings }] },
];

const TITLES = { dashboard: 'Dashboard', portfolio: 'Portfolio', report: 'Daily Report', health: 'System Health', market: 'Market Analysis', ai: 'AI Brain', strategies: 'Strategies', positions: 'Positions', trades: 'Trade History', risk: 'Risk', fo: 'F&O Calculator', audit: 'Audit & Logs', settings: 'Settings' };

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
