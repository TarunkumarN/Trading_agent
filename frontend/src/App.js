import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import {
  LayoutDashboard, HeartPulse, ScanSearch, BrainCircuit,
  Target, ListOrdered, ShieldAlert, TrendingUp, Calculator,
  Settings, ScrollText, Activity, Menu, X,
  RefreshCw, ChevronRight, ExternalLink, Zap
} from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie
} from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL;
const fmt = (n) => (n >= 0 ? '+' : '') + Number(n).toFixed(2);
const fmtINR = (n) => new Intl.NumberFormat('en-IN').format(Math.round(n));

/* ════════════════════════════════════════════════════════════
   LOGIN PAGE
   ════════════════════════════════════════════════════════════ */
function LoginPage({ onLogin }) {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API}/api/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user, pass })
      });
      const data = await res.json();
      if (data.ok) onLogin(data.token);
      else setError('Invalid credentials');
    } catch { setError('Connection failed'); }
    setLoading(false);
  };

  return (
    <div className="login-wrap" data-testid="login-page">
      <div className="login-box">
        <h1 data-testid="login-logo">MINIMAX</h1>
        <p>PRO TRADING TERMINAL</p>
        <input data-testid="login-username" type="text" placeholder="Username" value={user} onChange={e => setUser(e.target.value)} autoComplete="off" />
        <input data-testid="login-password" type="password" placeholder="Password" value={pass} onChange={e => setPass(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleLogin()} />
        <button data-testid="login-submit" className="login-btn" onClick={handleLogin} disabled={loading}>
          {loading ? 'CONNECTING...' : 'ACCESS TERMINAL'}
        </button>
        {error && <div className="login-error" data-testid="login-error">{error}</div>}
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   STAT CARD
   ════════════════════════════════════════════════════════════ */
function StatCard({ label, value, sub, color, accent }) {
  return (
    <div className={`card card-accent ${accent || ''}`}>
      <div className="card-label">{label}</div>
      <div className="metric" style={{ color: color || 'var(--text)' }}>{value}</div>
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   TRADE DETAIL MODAL
   ════════════════════════════════════════════════════════════ */
function TradeDetailModal({ trade, onClose }) {
  const [detail, setDetail] = useState(null);
  useEffect(() => {
    if (!trade) return;
    const id = `${trade.symbol}_${(trade.entry_time || '').replace(/:/g, '')}`;
    fetch(`${API}/api/trades/${id}`).then(r => r.json()).then(setDetail).catch(() => {});
  }, [trade]);

  if (!trade) return null;
  const d = detail || {};

  return (
    <div className="modal-overlay" onClick={onClose} data-testid="trade-detail-modal">
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} data-testid="modal-close">&times;</button>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 900, marginBottom: 4 }}>
          <span style={{ color: 'var(--amber)' }}>{trade.symbol}</span> Trade Detail
        </h2>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: 18 }}>{trade.date} | {trade.entry_time} - {trade.exit_time}</div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 18 }}>
          <div className="strat-meta-item"><div className="strat-meta-label">Action</div><div className="strat-meta-val"><span className={`tag tag-${trade.action?.toLowerCase()}`}>{trade.action}</span></div></div>
          <div className="strat-meta-item"><div className="strat-meta-label">P&L</div><div className="strat-meta-val" style={{ color: trade.pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>{fmt(trade.pnl)}</div></div>
          <div className="strat-meta-item"><div className="strat-meta-label">Score</div><div className="strat-meta-val" style={{ color: 'var(--cyan)' }}>{trade.score}/10</div></div>
        </div>

        <div className="card-label" style={{ marginTop: 14 }}>Trade Parameters</div>
        <div className="fo-row"><span className="c-dim">Strategy</span><span>{d.strategy || trade.strategy || 'MiniMax Scalper'}</span></div>
        <div className="fo-row"><span className="c-dim">Entry Price</span><span style={{ color: 'var(--cyan)' }}>₹{trade.entry?.toFixed(2)}</span></div>
        <div className="fo-row"><span className="c-dim">Exit Price</span><span>₹{trade.exit?.toFixed(2)}</span></div>
        <div className="fo-row"><span className="c-dim">Quantity</span><span>{trade.qty}</span></div>
        <div className="fo-row"><span className="c-dim">Exit Reason</span><span className={`tag ${trade.reason?.includes('TARGET') ? 'tag-ok' : trade.reason?.includes('STOP') ? 'tag-fail' : 'tag-warn'}`}>{trade.reason}</span></div>

        {d.market_regime && (
          <>
            <div className="card-label" style={{ marginTop: 18 }}>AI Brain Analysis</div>
            <div className="fo-row"><span className="c-dim">Market Regime</span><span style={{ color: d.market_regime === 'BULLISH' ? 'var(--green)' : 'var(--red)' }}>{d.market_regime}</span></div>
            <div className="fo-row"><span className="c-dim">Liquidity Signal</span><span>{d.liquidity_signal}</span></div>
            <div className="fo-row"><span className="c-dim">Prediction Probability</span><span style={{ color: 'var(--cyan)' }}>{d.prediction_probability}</span></div>
            <div className="fo-row"><span className="c-dim">Entry Reason</span><span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{d.entry_reason}</span></div>
          </>
        )}

        {d.ai_validation && (
          <>
            <div className="card-label" style={{ marginTop: 18 }}>AI Validation</div>
            {Object.entries(d.ai_validation).map(([k, v]) => (
              <div key={k} className="fo-row">
                <span className="c-dim">{k.replace(/_/g, ' ')}</span>
                <span style={{ color: v === true ? 'var(--green)' : v === false ? 'var(--red)' : 'var(--amber)' }}>
                  {typeof v === 'boolean' ? (v ? 'YES' : 'NO') : v}
                </span>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   DASHBOARD PAGE
   ════════════════════════════════════════════════════════════ */
function DashboardPage({ data }) {
  const p = data.day_pnl || 0;
  const pv = data.portfolio_value || 10000;
  const stMap = { NORMAL: 'NORMAL | Score 6+', SELECTIVE: 'SELECTIVE | Score 9+', HALTED: 'HALTED | Limit Hit', PROTECTED: 'PROTECTED | Profit Locked' };
  const stCol = { NORMAL: 'var(--green)', SELECTIVE: 'var(--amber)', HALTED: 'var(--red)', PROTECTED: 'var(--blue)' };

  return (
    <div className="page-enter" data-testid="dashboard-page">
      <div className="grid-4">
        <StatCard label="Day P&L" value={`₹${fmt(p)}`} sub={`${p >= 0 ? 'Up' : 'Down'} ${Math.abs((p / 10000) * 100).toFixed(2)}%`} color={p >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" />
        <StatCard label="Trades Today" value={data.total_trades || 0} sub={`${data.open_count || 0} open`} color="var(--cyan)" accent="ca-cyan" />
        <StatCard label="Win Rate" value={`${data.win_rate || 0}%`} sub={`${data.wins || 0}W / ${data.losses || 0}L`} color={(data.win_rate || 0) >= 50 ? 'var(--green)' : 'var(--red)'} accent="ca-amber" />
        <StatCard label="Portfolio Value" value={`₹${fmtINR(pv)}`} sub={`${pv - 10000 >= 0 ? '+' : ''}₹${(pv - 10000).toFixed(0)} all time`} color="var(--purple)" accent="ca-purple" />
      </div>

      <div className="grid-28">
        <div className="card">
          <div className="card-head"><span className="card-head-title">Intraday P&L Curve</span><span className="c-dim" style={{ fontSize: '0.75rem' }}>{data.timestamp}</span></div>
          <div style={{ height: 210 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.pnl_curve || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="time" tick={{ fill: '#71717a', fontSize: 11 }} />
                <YAxis tick={{ fill: '#71717a', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#121214', border: '1px solid #27272a', fontSize: 12 }} />
                <Line type="monotone" dataKey="pnl" stroke={p >= 0 ? '#22c55e' : '#ef4444'} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card">
          <div className="card-head"><span className="card-head-title">Status</span></div>
          <div className="card-label">Watchlist</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 16 }}>
            {(data.watchlist || []).map(s => <span key={s} className="chip">{s}</span>)}
          </div>
          <div className="card-label">Agent State</div>
          <div style={{ fontSize: '1rem', fontWeight: 800, color: stCol[data.agent_state] || 'var(--green)', marginBottom: 14 }}>
            {stMap[data.agent_state] || data.agent_state}
          </div>
          <div className="card-label">Market</div>
          <div style={{ fontSize: '0.9rem', fontWeight: 600, color: data.market_open ? 'var(--green)' : 'var(--red)' }}>
            {data.market_open ? 'NSE OPEN' : 'NSE CLOSED'}
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-head"><span className="card-head-title">Open Positions</span><span className="tag tag-active">{(data.open_positions || []).length}</span></div>
          {(data.open_positions || []).length > 0 ? (
            <div className="tbl-wrap"><table><thead><tr><th>Stock</th><th>Side</th><th>Qty</th><th>Entry</th><th>Unrealised</th></tr></thead><tbody>
              {data.open_positions.map(pos => (
                <tr key={pos.symbol}><td style={{ fontWeight: 700, color: 'var(--amber)' }}>{pos.symbol}</td><td><span className={`tag tag-${pos.action?.toLowerCase()}`}>{pos.action}</span></td><td>{pos.qty}</td><td>₹{pos.entry?.toFixed(2)}</td><td style={{ color: pos.unrealised_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{fmt(pos.unrealised_pnl || 0)}</td></tr>
              ))}
            </tbody></table></div>
          ) : <div className="empty">No open positions</div>}
        </div>
        <div className="card">
          <div className="card-head"><span className="card-head-title">Recent Trades</span></div>
          {(data.trades || []).length > 0 ? (
            <div className="tbl-wrap"><table><thead><tr><th>Stock</th><th>P&L</th><th>Reason</th><th>Time</th></tr></thead><tbody>
              {data.trades.slice(0, 6).map((t, i) => (
                <tr key={i}><td style={{ fontWeight: 700, color: 'var(--amber)' }}>{t.symbol}</td><td style={{ color: t.pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{fmt(t.pnl || 0)}</td><td><span className={`tag ${t.reason?.includes('TARGET') ? 'tag-ok' : t.reason?.includes('STOP') ? 'tag-fail' : 'tag-warn'}`}>{t.reason?.replace(' (15 min)', '')}</span></td><td className="c-dim">{t.exit_time}</td></tr>
              ))}
            </tbody></table></div>
          ) : <div className="empty">No trades today</div>}
        </div>
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   PORTFOLIO PAGE
   ════════════════════════════════════════════════════════════ */
function PortfolioPage({ portfolio }) {
  if (!portfolio) return <div className="empty">Loading portfolio...</div>;
  const p = portfolio;
  return (
    <div className="page-enter" data-testid="portfolio-page">
      <div className="grid-4">
        <StatCard label="Initial Capital" value={`₹${fmtINR(p.initial_capital)}`} color="var(--text-muted)" accent="ca-blue" />
        <StatCard label="Current Equity" value={`₹${fmtINR(p.current_equity)}`} color={p.total_pnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" />
        <StatCard label="Total P&L" value={`₹${fmt(p.total_pnl)}`} sub={`Day: ₹${fmt(p.day_pnl)}`} color={p.total_pnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-cyan" />
        <StatCard label="Open P&L" value={`₹${fmt(p.unrealised_pnl)}`} sub={`${p.open_positions} positions`} color={p.unrealised_pnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-amber" />
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-head"><span className="card-head-title">Equity Curve</span></div>
        <div style={{ height: 220 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={p.equity_curve || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="date" tick={{ fill: '#71717a', fontSize: 10 }} />
              <YAxis tick={{ fill: '#71717a', fontSize: 10 }} domain={['dataMin - 100', 'dataMax + 100']} />
              <Tooltip contentStyle={{ background: '#121214', border: '1px solid #27272a', fontSize: 12 }} />
              <Line type="monotone" dataKey="equity" stroke="#22c55e" strokeWidth={2} dot={{ r: 4, fill: '#22c55e' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-head"><span className="card-head-title">Daily P&L</span></div>
        <div style={{ height: 200 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={p.daily_pnl_chart || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="date" tick={{ fill: '#71717a', fontSize: 10 }} />
              <YAxis tick={{ fill: '#71717a', fontSize: 10 }} />
              <Tooltip contentStyle={{ background: '#121214', border: '1px solid #27272a', fontSize: 12 }} />
              <Bar dataKey="pnl" radius={[4, 4, 0, 0]}>
                {(p.daily_pnl_chart || []).map((d, i) => <Cell key={i} fill={d.pnl >= 0 ? '#22c55e' : '#ef4444'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-3">
        <div className="card"><div className="card-label">Total Trades</div><div className="metric" style={{ color: 'var(--cyan)' }}>{p.total_trades}</div><div className="metric-sub">{p.wins}W / {p.losses}L</div></div>
        <div className="card"><div className="card-label">Win Rate</div><div className="metric" style={{ color: p.win_rate >= 50 ? 'var(--green)' : 'var(--red)' }}>{p.win_rate}%</div><div className="metric-sub">Avg Win: ₹{p.avg_profit} | Avg Loss: ₹{p.avg_loss}</div></div>
        <div className="card"><div className="card-label">Risk Metrics</div><div className="metric" style={{ color: 'var(--amber)' }}>{p.profit_factor}x</div><div className="metric-sub">Profit Factor | DD: {p.max_drawdown}%</div></div>
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   SYSTEM HEALTH PAGE
   ════════════════════════════════════════════════════════════ */
function HealthPage({ health }) {
  if (!health) return <div className="empty">Loading...</div>;
  const c = health.components || {};
  return (
    <div className="page-enter" data-testid="health-page">
      <div className="grid-2">
        <div className="card">
          <div className="card-head"><span className="card-head-title">Component Health</span><span className="c-dim" style={{ fontSize: '0.75rem' }}>{health.timestamp}</span></div>
          {Object.entries(c).map(([k, v]) => (
            <div key={k} className="health-row">
              <div><div style={{ fontSize: '0.9rem', fontWeight: 700 }}>{k.replace(/_/g, ' ').toUpperCase()}</div><div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{v.note}</div></div>
              <div className="health-dot" style={{ background: v.ok ? 'var(--green)' : 'var(--red)' }} />
            </div>
          ))}
        </div>
        <div className="card">
          <div className="card-head"><span className="card-head-title">Monitoring Panel</span></div>
          {health.risk_summary && Object.entries(health.risk_summary).map(([k, v]) => (
            <div key={k} className="health-row">
              <span style={{ color: 'var(--text-dim)' }}>{k.replace(/_/g, ' ')}</span>
              <span style={{ fontWeight: 600, fontFamily: "'JetBrains Mono',monospace" }}>{typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v)}</span>
            </div>
          ))}
          <div className="health-row"><span style={{ color: 'var(--text-dim)' }}>Market Open</span><span className={`tag ${health.market_open ? 'tag-ok' : 'tag-fail'}`}>{health.market_open ? 'OPEN' : 'CLOSED'}</span></div>
          <div className="health-row"><span style={{ color: 'var(--text-dim)' }}>Trading Hours</span><span className={`tag ${health.trading_hours ? 'tag-ok' : 'tag-paused'}`}>{health.trading_hours ? 'ACTIVE' : 'INACTIVE'}</span></div>
        </div>
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   MARKET ANALYSIS PAGE — Pre/Post Market
   ════════════════════════════════════════════════════════════ */
function MarketPage({ premarket, postmarket, loadPremarket, loadPostmarket }) {
  const [tab, setTab] = useState('pre');

  const StockTable = ({ stocks, title }) => (
    <div className="tbl-wrap">
      {(stocks || []).length > 0 ? (
        <table><thead><tr><th>Symbol</th><th>Price</th><th>Change</th><th>Volume</th><th>High</th><th>Low</th></tr></thead><tbody>
          {stocks.map(s => (
            <tr key={s.symbol}><td style={{ fontWeight: 700, color: 'var(--amber)' }}>{s.symbol}</td><td>₹{s.price}</td><td style={{ color: (s.change_pct || s.gap_pct || 0) >= 0 ? 'var(--green)' : 'var(--red)' }}>{(s.change_pct || s.gap_pct || 0) >= 0 ? '+' : ''}{s.change_pct || s.gap_pct || 0}%</td><td className="c-muted">{fmtINR(s.volume || 0)}</td><td>₹{s.high || '--'}</td><td>₹{s.low || '--'}</td></tr>
          ))}
        </tbody></table>
      ) : <div className="empty">No data available</div>}
    </div>
  );

  const pre = premarket || {};
  const post = postmarket || {};
  const indices = (tab === 'pre' ? pre.indices : post.indices) || {};

  return (
    <div className="page-enter" data-testid="market-page">
      <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
        <button data-testid="market-tab-pre" onClick={() => { setTab('pre'); loadPremarket(); }} className="fo-btn" style={{ background: tab === 'pre' ? 'var(--green)' : 'var(--card)', color: tab === 'pre' ? '#052e16' : 'var(--text)', border: '1px solid var(--border)' }}>Pre-Market</button>
        <button data-testid="market-tab-post" onClick={() => { setTab('post'); loadPostmarket(); }} className="fo-btn" style={{ background: tab === 'post' ? 'var(--green)' : 'var(--card)', color: tab === 'post' ? '#052e16' : 'var(--text)', border: '1px solid var(--border)' }}>Post-Market</button>
        <button data-testid="market-refresh" onClick={tab === 'pre' ? loadPremarket : loadPostmarket} style={{ marginLeft: 'auto', padding: '8px 16px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--green)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem' }}><RefreshCw size={14} /> Refresh</button>
      </div>

      <div className="grid-4">
        {Object.entries(indices).map(([k, v]) => (
          <div key={k} className="card idx-card">
            <div className="idx-name">{k.replace(/_/g, ' ').toUpperCase()}</div>
            <div className="idx-val">{v.price ? fmtINR(v.price) : '--'}</div>
            <div className="idx-chg" style={{ color: (v.change_pct || v.change || 0) >= 0 ? 'var(--green)' : 'var(--red)' }}>
              {v.change_pct !== undefined ? `${v.change_pct >= 0 ? '+' : ''}${v.change_pct}%` : v.change !== undefined ? `${v.change >= 0 ? '+' : ''}${v.change}` : '--'}
            </div>
          </div>
        ))}
      </div>

      {tab === 'pre' && pre.ai_recommendation && (
        <div className="card" style={{ marginBottom: 16, borderColor: 'rgba(6,182,212,0.3)' }}>
          <div className="card-head"><span className="card-head-title"><Zap size={16} style={{ color: 'var(--cyan)', marginRight: 6 }} />AI Market Analysis</span></div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10 }}>
            {Object.entries(pre.ai_recommendation).map(([k, v]) => (
              <div key={k} className="strat-meta-item">
                <div className="strat-meta-label">{k.replace(/_/g, ' ')}</div>
                <div className="strat-meta-val" style={{ color: v.includes?.('BULL') || v.includes?.('LOW') ? 'var(--green)' : v.includes?.('BEAR') || v.includes?.('HIGH') ? 'var(--red)' : 'var(--amber)' }}>{v}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'post' && post.trading_summary && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-head"><span className="card-head-title">Today's Trading Summary</span></div>
          <div className="grid-4" style={{ marginBottom: 0 }}>
            <div className="strat-meta-item"><div className="strat-meta-label">Trades</div><div className="strat-meta-val">{post.trading_summary.total_trades}</div></div>
            <div className="strat-meta-item"><div className="strat-meta-label">Win Rate</div><div className="strat-meta-val" style={{ color: post.trading_summary.win_rate >= 50 ? 'var(--green)' : 'var(--red)' }}>{post.trading_summary.win_rate}%</div></div>
            <div className="strat-meta-item"><div className="strat-meta-label">Day P&L</div><div className="strat-meta-val" style={{ color: post.trading_summary.day_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{fmt(post.trading_summary.day_pnl)}</div></div>
            <div className="strat-meta-item"><div className="strat-meta-label">Breadth</div><div className="strat-meta-val">{post.market_summary?.breadth}</div></div>
          </div>
        </div>
      )}

      <div className="grid-2">
        <div className="card"><div className="card-head"><span className="card-head-title" style={{ color: 'var(--green)' }}>Top Gainers</span></div><StockTable stocks={tab === 'pre' ? pre.gap_ups : post.best_performers} /></div>
        <div className="card"><div className="card-head"><span className="card-head-title" style={{ color: 'var(--red)' }}>Top Losers</span></div><StockTable stocks={tab === 'pre' ? pre.gap_downs : post.worst_performers} /></div>
      </div>

      <div className="card">
        <div className="card-head"><span className="card-head-title">{tab === 'pre' ? 'Volume Leaders' : 'All Stocks'}</span></div>
        <StockTable stocks={tab === 'pre' ? (pre.volume_leaders || pre.all_stocks) : (post.best_performers || []).concat(post.worst_performers || [])} />
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   AI BRAIN DECISIONS PAGE
   ════════════════════════════════════════════════════════════ */
function AIBrainPage({ aiData, loadAI }) {
  if (!aiData) return <div className="empty">Loading AI decisions...</div>;

  return (
    <div className="page-enter" data-testid="ai-brain-page">
      <div className="grid-3">
        <StatCard label="AI Accuracy" value={`${aiData.ai_accuracy}%`} sub={`${aiData.correct_decisions}/${aiData.total_decisions} correct`} color={aiData.ai_accuracy >= 50 ? 'var(--green)' : 'var(--red)'} accent="ca-cyan" />
        <StatCard label="Total Decisions" value={aiData.total_decisions} color="var(--amber)" accent="ca-amber" />
        <StatCard label="Win Decisions" value={aiData.correct_decisions} sub={`${aiData.total_decisions - aiData.correct_decisions} losses`} color="var(--green)" accent="ca-green" />
      </div>

      {(aiData.decisions || []).map((d, i) => (
        <div key={i} className="ai-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
            <div>
              <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--amber)', marginRight: 10 }}>{d.symbol}</span>
              <span className={`tag tag-${d.action?.toLowerCase()}`}>{d.action}</span>
              <span className={`tag ${d.outcome === 'WIN' ? 'tag-ok' : 'tag-fail'}`} style={{ marginLeft: 6 }}>{d.outcome}</span>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ color: d.pnl >= 0 ? 'var(--green)' : 'var(--red)', fontWeight: 800, fontSize: '1.1rem', fontFamily: "'JetBrains Mono',monospace" }}>₹{fmt(d.pnl)}</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>{d.date} {d.time}</div>
            </div>
          </div>

          <div className="card-label">AI Reasoning Chain</div>
          {d.reasoning && Object.entries(d.reasoning).map(([k, v]) => (
            <div key={k} className="ai-step">
              <span className="ai-step-label">{k.replace('step_', '').replace(/_/g, ' ')}</span>
              <span className="ai-step-val">{v}</span>
            </div>
          ))}

          <div style={{ marginTop: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: 4 }}>
              <span className="c-dim">Confidence</span>
              <span style={{ color: d.confidence >= 70 ? 'var(--green)' : 'var(--amber)' }}>{d.confidence}%</span>
            </div>
            <div className="confidence-bar">
              <div className="confidence-fill" style={{ width: `${d.confidence}%`, background: d.confidence >= 70 ? 'var(--green)' : d.confidence >= 50 ? 'var(--amber)' : 'var(--red)' }} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   STRATEGIES PERFORMANCE PAGE
   ════════════════════════════════════════════════════════════ */
function StrategiesPage({ stratPerf, loadStratPerf }) {
  if (!stratPerf) return <div className="empty">Loading...</div>;
  const st = stratPerf.strategies || [];

  return (
    <div className="page-enter" data-testid="strategies-page">
      {st.map((s, i) => (
        <div key={i} className="strat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
            <div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800 }}>{s.name}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{s.type} &mdash; {s.description}</div>
            </div>
            <span className={`tag ${s.status === 'ACTIVE' ? 'tag-active' : 'tag-paused'}`}>{s.status}</span>
          </div>

          <div className="strat-meta">
            <div className="strat-meta-item"><div className="strat-meta-label">Trades</div><div className="strat-meta-val">{s.metrics?.total_trades || 0}</div></div>
            <div className="strat-meta-item"><div className="strat-meta-label">Win Rate</div><div className="strat-meta-val" style={{ color: (s.metrics?.win_rate || 0) >= 50 ? 'var(--green)' : 'var(--red)' }}>{s.metrics?.win_rate || 0}%</div></div>
            <div className="strat-meta-item"><div className="strat-meta-label">Total P&L</div><div className="strat-meta-val" style={{ color: (s.metrics?.total_pnl || 0) >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{s.metrics?.total_pnl || 0}</div></div>
            <div className="strat-meta-item"><div className="strat-meta-label">Avg P&L</div><div className="strat-meta-val">₹{s.metrics?.avg_pnl || 0}</div></div>
          </div>

          <div className="strat-meta" style={{ marginTop: 6 }}>
            <div className="strat-meta-item"><div className="strat-meta-label">Avg Profit</div><div className="strat-meta-val c-green">₹{s.metrics?.avg_profit || 0}</div></div>
            <div className="strat-meta-item"><div className="strat-meta-label">Avg Loss</div><div className="strat-meta-val c-red">₹{s.metrics?.avg_loss || 0}</div></div>
            <div className="strat-meta-item"><div className="strat-meta-label">Max DD</div><div className="strat-meta-val c-amber">₹{s.metrics?.max_drawdown || 0}</div></div>
            <div className="strat-meta-item"><div className="strat-meta-label">W/L</div><div className="strat-meta-val">{s.metrics?.wins || 0}/{s.metrics?.losses || 0}</div></div>
          </div>

          {(s.pnl_history || []).length > 0 && (
            <div style={{ height: 120, marginTop: 12 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={s.pnl_history}>
                  <XAxis dataKey="date" tick={false} />
                  <YAxis tick={{ fill: '#71717a', fontSize: 9 }} />
                  <Line type="monotone" dataKey="pnl" stroke={s.metrics?.total_pnl >= 0 ? '#22c55e' : '#ef4444'} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   OPEN POSITIONS PAGE
   ════════════════════════════════════════════════════════════ */
function PositionsPage({ positions }) {
  const pos = positions?.positions || [];
  const totalUnreal = pos.reduce((s, p) => s + (p.unrealised_pnl || 0), 0);
  return (
    <div className="page-enter" data-testid="positions-page">
      <div className="grid-3">
        <StatCard label="Open Positions" value={pos.length} color="var(--cyan)" accent="ca-cyan" />
        <StatCard label="Unrealised P&L" value={`₹${fmt(totalUnreal)}`} color={totalUnreal >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" />
        <StatCard label="Total Exposure" value={`₹${fmtINR(pos.reduce((s, p) => s + (p.entry_price || 0) * (p.quantity || 0), 0))}`} color="var(--amber)" accent="ca-amber" />
      </div>
      <div className="card">
        <div className="card-head"><span className="card-head-title">Positions</span></div>
        {pos.length > 0 ? (
          <div className="tbl-wrap"><table><thead><tr><th>Symbol</th><th>Strategy</th><th>Side</th><th>Qty</th><th>Entry</th><th>Current</th><th>SL</th><th>Target</th><th>Phase</th><th>P&L</th></tr></thead><tbody>
            {pos.map(p => (
              <tr key={p.symbol}><td style={{ fontWeight: 700, color: 'var(--amber)' }}>{p.symbol}</td><td className="c-dim" style={{ fontSize: '0.78rem' }}>{p.strategy}</td><td><span className={`tag tag-${p.action?.toLowerCase()}`}>{p.action}</span></td><td>{p.quantity}</td><td>₹{p.entry_price?.toFixed(2)}</td><td>₹{p.current_price?.toFixed(2)}</td><td style={{ color: 'var(--red)' }}>₹{p.stop_loss?.toFixed(2)}</td><td style={{ color: 'var(--green)' }}>₹{p.target?.toFixed(2)}</td><td><span className="tag tag-info">{p.sl_phase}</span></td><td style={{ color: p.unrealised_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{fmt(p.unrealised_pnl || 0)}</td></tr>
            ))}
          </tbody></table></div>
        ) : <div className="empty">No open positions</div>}
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   TRADES PAGE (with clickable detail)
   ════════════════════════════════════════════════════════════ */
function TradesPage({ tradesData, loadTrades }) {
  const [filter, setFilter] = useState('all');
  const [selectedTrade, setSelectedTrade] = useState(null);

  if (!tradesData) return <div className="empty">Loading...</div>;
  let trades = tradesData.trades || [];
  if (filter === 'wins') trades = trades.filter(t => t.pnl > 0);
  if (filter === 'loss') trades = trades.filter(t => t.pnl <= 0);

  const totalPnl = trades.reduce((s, t) => s + (t.pnl || 0), 0);
  const wins = trades.filter(t => t.pnl > 0).length;

  return (
    <div className="page-enter" data-testid="trades-page">
      <TradeDetailModal trade={selectedTrade} onClose={() => setSelectedTrade(null)} />
      <div className="grid-3">
        <StatCard label="Total Trades" value={trades.length} color="var(--cyan)" accent="ca-cyan" />
        <StatCard label="Win / Loss" value={`${wins} / ${trades.length - wins}`} color="var(--amber)" accent="ca-amber" />
        <StatCard label="Net P&L" value={`₹${fmt(totalPnl)}`} color={totalPnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" />
      </div>
      <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
        <select data-testid="trade-filter" value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="all">All Trades</option>
          <option value="wins">Wins Only</option>
          <option value="loss">Losses Only</option>
        </select>
      </div>
      <div className="card">
        <div className="tbl-wrap">
          {trades.length > 0 ? (
            <table><thead><tr><th>Date</th><th>Stock</th><th>Strategy</th><th>Side</th><th>Qty</th><th>Entry</th><th>Exit</th><th>P&L</th><th>Reason</th><th>Score</th><th></th></tr></thead><tbody>
              {trades.slice(0, 50).map((t, i) => (
                <tr key={i} style={{ cursor: 'pointer' }} onClick={() => setSelectedTrade(t)}>
                  <td className="c-dim">{t.date}</td>
                  <td style={{ fontWeight: 700, color: 'var(--amber)' }}>{t.symbol}</td>
                  <td className="c-dim" style={{ fontSize: '0.78rem' }}>{t.strategy || '--'}</td>
                  <td><span className={`tag tag-${t.action?.toLowerCase()}`}>{t.action}</span></td>
                  <td>{t.qty}</td>
                  <td>₹{t.entry?.toFixed(2)}</td>
                  <td>₹{t.exit?.toFixed(2)}</td>
                  <td style={{ color: t.pnl >= 0 ? 'var(--green)' : 'var(--red)', fontWeight: 700 }}>₹{fmt(t.pnl || 0)}</td>
                  <td><span className={`tag ${t.reason?.includes('TARGET') ? 'tag-ok' : t.reason?.includes('STOP') ? 'tag-fail' : 'tag-warn'}`}>{t.reason}</span></td>
                  <td style={{ color: 'var(--cyan)' }}>{t.score}</td>
                  <td><ChevronRight size={14} className="c-dim" /></td>
                </tr>
              ))}
            </tbody></table>
          ) : <div className="empty">No trades</div>}
        </div>
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   RISK PAGE
   ════════════════════════════════════════════════════════════ */
function RiskPage({ risk }) {
  if (!risk) return <div className="empty">Loading...</div>;
  const lp = risk.loss_pct || 0;
  const barCol = lp > 80 ? 'var(--red)' : lp > 50 ? 'var(--amber)' : 'var(--green)';
  return (
    <div className="page-enter" data-testid="risk-page">
      <div className="grid-4">
        <StatCard label="Loss Used" value={`₹${risk.loss_used?.toFixed(0) || 0}`} sub={`₹${risk.loss_remaining?.toFixed(0) || 0} left`} color="var(--red)" accent="ca-red" />
        <StatCard label="Loss Limit (5%)" value={`₹${risk.daily_loss_limit?.toFixed(0) || 500}`} sub="Halts at this" color="var(--amber)" accent="ca-amber" />
        <StatCard label="Day Profit" value={`₹${fmt(risk.day_pnl || 0)}`} color={risk.day_pnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" />
        <StatCard label="Open Risk" value={`₹${risk.open_risk?.toFixed(0) || 0}`} color="var(--purple)" accent="ca-purple" />
      </div>
      <div className="grid-2">
        <div className="card">
          <div className="card-head"><span className="card-head-title">Daily Loss Meter</span><span className={`tag ${risk.risk_level === 'SAFE' ? 'tag-safe' : risk.risk_level === 'WARNING' ? 'tag-warn' : 'tag-danger'}`}>{risk.risk_level}</span></div>
          <div className="risk-gauge"><div className="risk-pct" style={{ color: barCol }}>{lp.toFixed(0)}%</div><div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 4 }}>of daily limit used</div></div>
          <div className="prog-bar" style={{ height: 12 }}><div className="prog-fill" style={{ width: `${Math.min(100, lp)}%`, background: barCol }} /></div>
          {risk.drawdown_pct > 0 && (<div style={{ marginTop: 14 }}><div className="card-label">Drawdown</div><div style={{ fontSize: '1.2rem', fontWeight: 800, color: risk.drawdown_pct >= risk.max_drawdown ? 'var(--red)' : 'var(--amber)' }}>{risk.drawdown_pct.toFixed(1)}% / {risk.max_drawdown}% max</div></div>)}
        </div>
        <div className="card">
          <div className="card-head"><span className="card-head-title">Risk Rules</span></div>
          <table><tbody>
            <tr><td className="c-dim">Max Loss/Day</td><td style={{ color: 'var(--red)' }}>5% Portfolio</td></tr>
            <tr><td className="c-dim">Max Drawdown</td><td style={{ color: 'var(--red)' }}>{risk.max_drawdown || 10}%</td></tr>
            <tr><td className="c-dim">Max Risk/Trade</td><td>₹{risk.max_per_trade || 200} (2%)</td></tr>
            <tr><td className="c-dim">Order Retries</td><td>3x with backoff</td></tr>
            <tr><td className="c-dim">Duplicate Block</td><td style={{ color: 'var(--green)' }}>MongoDB check</td></tr>
            <tr><td className="c-dim">Time Stop</td><td>15 min per trade</td></tr>
            <tr><td className="c-dim">SL Phases</td><td>Break-even / Lock ₹75 / Trail 50%</td></tr>
          </tbody></table>
          <div style={{ marginTop: 16, textAlign: 'center', padding: 10 }}>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: risk.trading_allowed ? 'var(--green)' : 'var(--red)' }}>{risk.trading_allowed ? 'TRADING ACTIVE' : 'TRADING HALTED'}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   F&O CALCULATOR PAGE
   ════════════════════════════════════════════════════════════ */
function FOPage() {
  const [entry, setEntry] = useState(22000);
  const [sl, setSl] = useState(21950);
  const [target, setTarget] = useState(22100);
  const [port, setPort] = useState(10000);
  const [inst, setInst] = useState('equity');
  const [result, setResult] = useState(null);

  const calc = async () => {
    try { const r = await fetch(`${API}/api/fo/calculate?entry=${entry}&sl=${sl}&target=${target}&portfolio=${port}&instrument=${inst}`); setResult(await r.json()); } catch {}
  };

  return (
    <div className="page-enter" data-testid="fo-page">
      <div className="grid-2">
        <div className="card">
          <div className="card-head"><span className="card-head-title">F&O Calculator</span></div>
          <div className="card-label">Instrument</div>
          <select data-testid="fo-instrument" value={inst} onChange={e => setInst(e.target.value)} style={{ width: '100%', marginBottom: 12 }}><option value="equity">Equity</option><option value="stock_fut">Stock Futures</option><option value="nifty_fut">Nifty Futures (25)</option><option value="banknifty_fut">BankNifty Futures (15)</option><option value="nifty_opt">Nifty Options (25)</option><option value="banknifty_opt">BankNifty Options (15)</option></select>
          <div className="card-label">Entry Price</div><input className="fo-input" data-testid="fo-entry" type="number" value={entry} onChange={e => setEntry(+e.target.value)} />
          <div className="card-label">Stop Loss</div><input className="fo-input" data-testid="fo-sl" type="number" value={sl} onChange={e => setSl(+e.target.value)} />
          <div className="card-label">Target</div><input className="fo-input" data-testid="fo-target" type="number" value={target} onChange={e => setTarget(+e.target.value)} />
          <div className="card-label">Portfolio Size</div><input className="fo-input" data-testid="fo-port" type="number" value={port} onChange={e => setPort(+e.target.value)} />
          <button className="fo-btn" data-testid="fo-calculate" onClick={calc} style={{ width: '100%' }}>CALCULATE</button>
        </div>
        <div className="card">
          <div className="card-head"><span className="card-head-title">Results</span></div>
          {result ? Object.entries(result).map(([k, v]) => (<div key={k} className="fo-row"><span className="c-dim">{k.replace(/_/g, ' ')}</span><span style={{ fontWeight: 600 }}>{typeof v === 'number' ? (k.includes('pct') ? `${v}%` : k === 'rr_ratio' ? `${v}:1` : `₹${v}`) : v}</span></div>)) : <div className="empty">Enter values and calculate</div>}
        </div>
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   AUDIT & LOGS PAGE
   ════════════════════════════════════════════════════════════ */
function AuditPage({ logs, audit }) {
  const tc = { BOT_START: 'var(--green)', WEBSOCKET_CONNECTED: 'var(--green)', WEBSOCKET_DISCONNECTED: 'var(--red)', SIGNAL_GENERATED: 'var(--cyan)', ORDER_PLACED: 'var(--green)', ORDER_FAILED: 'var(--red)', ORDER_CRITICAL_FAIL: 'var(--red)', ORDER_DUPLICATE_BLOCKED: 'var(--amber)', TRADE_EXITED: 'var(--blue)', RISK_HALT: 'var(--red)' };

  return (
    <div className="page-enter" data-testid="audit-page">
      {audit && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-head"><span className="card-head-title">System Audit</span><span className={`tag ${audit.all_fixed ? 'tag-ok' : 'tag-fail'}`}>{audit.all_fixed ? 'ALL FIXED' : 'ISSUES'}</span></div>
          <div className="grid-4" style={{ marginBottom: 8 }}>
            <div style={{ textAlign: 'center' }}><div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--red)' }}>{audit.critical}</div><div className="card-label">Critical</div></div>
            <div style={{ textAlign: 'center' }}><div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--amber)' }}>{audit.high}</div><div className="card-label">High</div></div>
            <div style={{ textAlign: 'center' }}><div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--blue)' }}>{audit.medium}</div><div className="card-label">Medium</div></div>
            <div style={{ textAlign: 'center' }}><div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--text-dim)' }}>{audit.low}</div><div className="card-label">Low</div></div>
          </div>
          <div className="tbl-wrap"><table><thead><tr><th>#</th><th>Severity</th><th>Category</th><th>Issue</th><th>Fix</th><th>Status</th></tr></thead><tbody>
            {(audit.issues || []).map(iss => (<tr key={iss.id}><td>{iss.id}</td><td><span className={`tag ${iss.severity === 'CRITICAL' ? 'tag-fail' : iss.severity === 'HIGH' ? 'tag-warn' : 'tag-info'}`}>{iss.severity}</span></td><td>{iss.category}</td><td style={{ fontFamily: "'Chivo',sans-serif", whiteSpace: 'normal' }}>{iss.description}</td><td style={{ fontFamily: "'Chivo',sans-serif", color: 'var(--text-muted)', whiteSpace: 'normal' }}>{iss.fix}</td><td><span className="tag tag-ok">{iss.status}</span></td></tr>))}
          </tbody></table></div>
        </div>
      )}
      <div className="card">
        <div className="card-head"><span className="card-head-title">Event Logs</span><span className="c-dim" style={{ fontSize: '0.75rem' }}>{(logs || []).length}</span></div>
        {(logs || []).length > 0 ? (
          <div style={{ maxHeight: 420, overflowY: 'auto' }}>
            {logs.map((l, i) => (<div key={i} className="log-entry"><span className="log-time">{l.timestamp?.slice(11, 19)}</span><span className="log-type" style={{ color: tc[l.event_type] || 'var(--text-muted)' }}>{l.event_type}</span><span className="log-msg">{l.message}</span></div>))}
          </div>
        ) : <div className="empty">No logs</div>}
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   SETTINGS PAGE
   ════════════════════════════════════════════════════════════ */
function SettingsPage({ config }) {
  if (!config) return <div className="empty">Loading...</div>;
  return (
    <div className="page-enter" data-testid="settings-page">
      <div className="grid-2">
        <div className="card">
          <div className="card-head"><span className="card-head-title">Trading Parameters</span></div>
          <table><tbody>
            <tr><td className="c-dim">Portfolio Size</td><td style={{ color: 'var(--cyan)' }}>₹{fmtINR(config.portfolio_value)}</td></tr>
            <tr><td className="c-dim">Max Risk/Trade</td><td style={{ color: 'var(--red)' }}>₹{(config.portfolio_value * config.max_risk_pct / 100).toFixed(0)} ({config.max_risk_pct}%)</td></tr>
            <tr><td className="c-dim">Daily Loss Limit</td><td style={{ color: 'var(--red)' }}>₹{config.daily_loss_limit?.toFixed(0)} (5%)</td></tr>
            <tr><td className="c-dim">Max Drawdown</td><td style={{ color: 'var(--red)' }}>{config.max_drawdown_pct}%</td></tr>
            <tr><td className="c-dim">Selective Profit</td><td style={{ color: 'var(--amber)' }}>₹{config.daily_profit_selective}</td></tr>
            <tr><td className="c-dim">Stop All Profit</td><td style={{ color: 'var(--amber)' }}>₹{config.daily_profit_stop}</td></tr>
            <tr><td className="c-dim">Min Score</td><td>{config.min_signal_score}/10</td></tr>
            <tr><td className="c-dim">Order Retries</td><td>{config.order_max_retries}x</td></tr>
            <tr><td className="c-dim">Risk:Reward</td><td>1:{config.risk_reward_ratio}</td></tr>
            <tr><td className="c-dim">EMA</td><td>{config.ema_fast}/{config.ema_slow}</td></tr>
          </tbody></table>
        </div>
        <div className="card">
          <div className="card-head"><span className="card-head-title">System Info</span></div>
          <table><tbody>
            <tr><td className="c-dim">Mode</td><td><span className={`tag ${config.trading_mode === 'live' ? 'tag-ok' : 'tag-paper'}`}>{config.trading_mode?.toUpperCase()}</span></td></tr>
            <tr><td className="c-dim">Broker</td><td><span className={`tag ${config.kite_configured ? 'tag-ok' : 'tag-fail'}`}>Zerodha {config.kite_configured ? '(OK)' : '(No Token)'}</span></td></tr>
            <tr><td className="c-dim">Telegram</td><td><span className={`tag ${config.telegram_configured ? 'tag-ok' : 'tag-fail'}`}>{config.telegram_configured ? 'Connected' : 'Not Set'}</span></td></tr>
            <tr><td className="c-dim">Market Hours</td><td>{config.market_open} - {config.market_close}</td></tr>
            <tr><td className="c-dim">Trading Window</td><td>{config.trading_start} - {config.trading_end}</td></tr>
            <tr><td className="c-dim">Max Leverage</td><td>{config.max_leverage}x</td></tr>
          </tbody></table>
        </div>
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   MAIN APP
   ════════════════════════════════════════════════════════════ */
const NAV = [
  { group: 'Monitor', items: [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'portfolio', label: 'Portfolio', icon: TrendingUp },
    { id: 'health', label: 'System Health', icon: HeartPulse },
  ]},
  { group: 'Market', items: [
    { id: 'market', label: 'Market Analysis', icon: ScanSearch },
    { id: 'ai', label: 'AI Brain', icon: BrainCircuit },
    { id: 'strategies', label: 'Strategies', icon: Activity },
  ]},
  { group: 'Trading', items: [
    { id: 'positions', label: 'Open Positions', icon: Target },
    { id: 'trades', label: 'Trade History', icon: ListOrdered },
    { id: 'risk', label: 'Risk Dashboard', icon: ShieldAlert },
  ]},
  { group: 'Tools', items: [
    { id: 'fo', label: 'F&O Calculator', icon: Calculator },
    { id: 'audit', label: 'Audit & Logs', icon: ScrollText },
    { id: 'settings', label: 'Settings', icon: Settings },
  ]},
];

const TITLES = { dashboard: 'Dashboard', portfolio: 'Portfolio', health: 'System Health', market: 'Market Analysis', ai: 'AI Brain Decisions', strategies: 'Strategy Performance', positions: 'Open Positions', trades: 'Trade History', risk: 'Risk Dashboard', fo: 'F&O Calculator', audit: 'Audit & Logs', settings: 'Settings' };

function App() {
  const [authed, setAuthed] = useState(false);
  const [page, setPage] = useState('dashboard');
  const [clock, setClock] = useState('');
  const [mktOpen, setMktOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [data, setData] = useState({});
  const [portfolio, setPortfolio] = useState(null);
  const [health, setHealth] = useState(null);
  const [risk, setRisk] = useState(null);
  const [premarket, setPremarket] = useState(null);
  const [postmarket, setPostmarket] = useState(null);
  const [aiData, setAiData] = useState(null);
  const [stratPerf, setStratPerf] = useState(null);
  const [positions, setPositions] = useState(null);
  const [tradesData, setTradesData] = useState(null);
  const [logs, setLogs] = useState([]);
  const [audit, setAudit] = useState(null);
  const [config, setConfig] = useState(null);

  const f = useCallback(async (url, setter) => { try { const r = await fetch(`${API}${url}`); setter(await r.json()); } catch {} }, []);

  const loadDash = useCallback(() => f('/api/data', setData), [f]);
  const loadPortfolio = useCallback(() => f('/api/portfolio', setPortfolio), [f]);
  const loadHealth = useCallback(() => f('/api/health', setHealth), [f]);
  const loadRisk = useCallback(() => f('/api/risk', setRisk), [f]);
  const loadPremarket = useCallback(() => f('/api/market/premarket', setPremarket), [f]);
  const loadPostmarket = useCallback(() => f('/api/market/postmarket', setPostmarket), [f]);
  const loadAI = useCallback(() => f('/api/ai-decisions', setAiData), [f]);
  const loadStratPerf = useCallback(() => f('/api/strategies/performance', setStratPerf), [f]);
  const loadPositions = useCallback(() => f('/api/open-positions', setPositions), [f]);
  const loadTrades = useCallback(() => f('/api/trades', setTradesData), [f]);
  const loadLogs = useCallback(() => f('/api/logs?limit=100', (d) => setLogs(d.logs || [])), [f]);
  const loadAudit = useCallback(() => f('/api/audit', setAudit), [f]);
  const loadConfig = useCallback(() => f('/api/config', setConfig), [f]);

  useEffect(() => {
    if (!authed) return;
    loadDash(); loadHealth(); loadRisk(); loadConfig(); loadAudit();
    const t1 = setInterval(loadDash, 15000);
    const t2 = setInterval(loadHealth, 30000);
    const t3 = setInterval(loadRisk, 20000);
    return () => { clearInterval(t1); clearInterval(t2); clearInterval(t3); };
  }, [authed, loadDash, loadHealth, loadRisk, loadConfig, loadAudit]);

  useEffect(() => {
    const tick = () => {
      const ist = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
      setClock(ist.toTimeString().substr(0, 8) + ' IST');
      const h = ist.getHours(), m = ist.getMinutes();
      setMktOpen((h > 9 || (h === 9 && m >= 15)) && (h < 15 || (h === 15 && m < 30)));
    };
    tick(); const t = setInterval(tick, 1000); return () => clearInterval(t);
  }, []);

  const nav = (id) => {
    setPage(id);
    setSidebarOpen(false);
    if (id === 'portfolio') loadPortfolio();
    if (id === 'market') { loadPremarket(); loadPostmarket(); }
    if (id === 'ai') loadAI();
    if (id === 'strategies') loadStratPerf();
    if (id === 'positions') loadPositions();
    if (id === 'trades') loadTrades();
    if (id === 'audit') { loadLogs(); loadAudit(); }
    if (id === 'settings') loadConfig();
  };

  if (!authed) return <LoginPage onLogin={() => setAuthed(true)} />;

  const p = data.day_pnl || 0;
  const sc = { NORMAL: 'var(--green)', SELECTIVE: 'var(--amber)', HALTED: 'var(--red)', PROTECTED: 'var(--blue)' };

  return (
    <div className="app-layout" data-testid="app-layout">
      <button className="mobile-toggle" data-testid="mobile-menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
        {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
      </button>
      <div className={`sidebar-overlay ${sidebarOpen ? 'show' : ''}`} onClick={() => setSidebarOpen(false)} />

      <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-logo"><h1>MINIMAX</h1><p>PRO TERMINAL</p></div>
        <nav className="sidebar-nav">
          {NAV.map(g => (
            <React.Fragment key={g.group}>
              <div className="nav-group">{g.group}</div>
              {g.items.map(item => (
                <div key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => nav(item.id)} data-testid={`nav-${item.id}`}>
                  <item.icon size={18} /><span>{item.label}</span>
                </div>
              ))}
            </React.Fragment>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}><span className="status-dot" style={{ background: sc[data.agent_state] || 'var(--green)' }} /><span style={{ color: sc[data.agent_state] || 'var(--green)', fontWeight: 600 }}>{data.agent_state || 'NORMAL'}</span></div>
          <span style={{ color: 'var(--text-dim)' }}>MODE: <span style={{ color: 'var(--purple)', fontWeight: 700 }}>{data.mode || 'PAPER'}</span></span>
        </div>
      </div>

      <div className="main-content">
        <div className="topbar">
          <div className="topbar-title">{TITLES[page]}</div>
          <div className="topbar-right">
            <span style={{ color: 'var(--text-dim)' }}>NSE <span className="blink" style={{ color: mktOpen ? 'var(--green)' : 'var(--red)' }}>●</span></span>
            <span className="pill pill-pnl" style={{ background: p >= 0 ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)', color: p >= 0 ? 'var(--green)' : 'var(--red)', borderColor: p >= 0 ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)' }}>₹{fmt(p)}</span>
            <span className={`pill ${data.mode === 'LIVE' ? 'pill-live' : 'pill-mode'}`}>{data.mode || 'PAPER'}</span>
            <span className="clock">{clock}</span>
          </div>
        </div>
        <div className="content-area">
          {page === 'dashboard' && <DashboardPage data={data} />}
          {page === 'portfolio' && <PortfolioPage portfolio={portfolio} />}
          {page === 'health' && <HealthPage health={health} />}
          {page === 'market' && <MarketPage premarket={premarket} postmarket={postmarket} loadPremarket={loadPremarket} loadPostmarket={loadPostmarket} />}
          {page === 'ai' && <AIBrainPage aiData={aiData} loadAI={loadAI} />}
          {page === 'strategies' && <StrategiesPage stratPerf={stratPerf} loadStratPerf={loadStratPerf} />}
          {page === 'positions' && <PositionsPage positions={positions} />}
          {page === 'trades' && <TradesPage tradesData={tradesData} loadTrades={loadTrades} />}
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
