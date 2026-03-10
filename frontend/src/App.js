import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import {
  LayoutDashboard, HeartPulse, ScanSearch, BrainCircuit,
  Target, ListOrdered, ShieldAlert, TrendingUp, Calculator,
  Settings, ScrollText, LogOut, Activity, Wifi, WifiOff,
  ChevronRight, AlertTriangle, CheckCircle2, XCircle, Clock,
  ArrowUpRight, ArrowDownRight, Minus, RefreshCw
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL;

const fmt = (n) => (n >= 0 ? '+' : '') + n.toFixed(2);
const fmtINR = (n) => new Intl.NumberFormat('en-IN').format(Math.round(n));

// ═══════════════════════════════════════════════════════════════
// LOGIN PAGE
// ═══════════════════════════════════════════════════════════════
function LoginPage({ onLogin }) {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user, pass })
      });
      const data = await res.json();
      if (data.ok) onLogin(data.token);
      else setError('Invalid credentials');
    } catch {
      setError('Connection failed');
    }
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

// ═══════════════════════════════════════════════════════════════
// STAT CARD COMPONENT
// ═══════════════════════════════════════════════════════════════
function StatCard({ label, value, sub, color, accent }) {
  return (
    <div className={`card card-accent ${accent || ''}`}>
      <div className="card-label">{label}</div>
      <div className="metric" style={{ color: color || 'var(--text)' }}>{value}</div>
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// DASHBOARD PAGE
// ═══════════════════════════════════════════════════════════════
function DashboardPage({ data }) {
  const p = data.day_pnl || 0;
  const pv = data.portfolio_value || 10000;
  const prog = Math.min(100, Math.max(0, (p / 500) * 100));
  const progColor = p < 0 ? 'var(--red)' : p >= 300 ? 'var(--green)' : 'var(--amber)';
  const stateMap = { NORMAL: 'NORMAL | Score 6+', SELECTIVE: 'SELECTIVE | Score 9+', HALTED: 'HALTED | Limit Hit', PROTECTED: 'PROTECTED | Profit Locked' };
  const stateColor = { NORMAL: 'var(--green)', SELECTIVE: 'var(--amber)', HALTED: 'var(--red)', PROTECTED: 'var(--blue)' };

  return (
    <div className="page-enter" data-testid="dashboard-page">
      <div className="grid-4">
        <StatCard label="Day P&L" value={`₹${fmt(p)}`} sub={`${p >= 0 ? 'Up' : 'Down'} ${Math.abs((p / 10000) * 100).toFixed(2)}% of portfolio`} color={p >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" />
        <StatCard label="Trades Today" value={data.total_trades || 0} sub={`${data.open_count || 0} open positions`} color="var(--cyan)" accent="ca-cyan" />
        <StatCard label="Win Rate" value={`${data.win_rate || 0}%`} sub={`${data.wins || 0}W / ${data.losses || 0}L`} color={(data.win_rate || 0) >= 50 ? 'var(--green)' : 'var(--red)'} accent="ca-amber" />
        <StatCard label="Portfolio Value" value={`₹${fmtINR(pv)}`} sub={`${pv - 10000 >= 0 ? '+' : ''}₹${(pv - 10000).toFixed(0)} all time`} color="var(--purple)" accent="ca-purple" />
      </div>

      <div className="grid-28">
        <div className="card">
          <div className="card-head">
            <span className="card-head-title">Intraday P&L Curve</span>
            <span className="c-dim" style={{ fontSize: '0.65rem' }}>{data.timestamp}</span>
          </div>
          <div style={{ height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.pnl_curve || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="time" tick={{ fill: '#71717a', fontSize: 10 }} />
                <YAxis tick={{ fill: '#71717a', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#121214', border: '1px solid #27272a', fontSize: 11 }} />
                <Line type="monotone" dataKey="pnl" stroke={p >= 0 ? '#22c55e' : '#ef4444'} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-head"><span className="card-head-title">Daily Target</span></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', marginBottom: 4 }}>
            <span className="c-dim">Target ₹500</span>
            <span style={{ color: progColor }}>{prog.toFixed(0)}%</span>
          </div>
          <div className="prog-bar" style={{ height: 7, marginBottom: 14 }}>
            <div className="prog-fill" style={{ width: `${prog}%`, background: progColor }} />
          </div>
          <div className="card-label">Watchlist</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {(data.watchlist || []).length > 0
              ? data.watchlist.map(s => <span key={s} className="chip">{s}</span>)
              : <span className="c-dim" style={{ fontSize: '0.7rem' }}>No watchlist loaded</span>}
          </div>
          <div style={{ marginTop: 12 }}>
            <div className="card-label">Agent State</div>
            <div style={{ fontSize: '0.82rem', fontWeight: 700, color: stateColor[data.agent_state] || 'var(--green)' }}>
              {stateMap[data.agent_state] || data.agent_state}
            </div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-head">
            <span className="card-head-title">Open Positions</span>
            <span className="tag tag-active">{(data.open_positions || []).length}</span>
          </div>
          {(data.open_positions || []).length > 0 ? (
            <div className="tbl-wrap">
              <table>
                <thead><tr><th>Stock</th><th>Side</th><th>Qty</th><th>Entry</th><th>Unrealised</th></tr></thead>
                <tbody>
                  {data.open_positions.map(pos => (
                    <tr key={pos.symbol}>
                      <td style={{ fontWeight: 700, color: 'var(--amber)' }}>{pos.symbol}</td>
                      <td><span className={`tag tag-${pos.action?.toLowerCase()}`}>{pos.action}</span></td>
                      <td className="c-muted">{pos.qty}</td>
                      <td>₹{pos.entry?.toFixed(2)}</td>
                      <td style={{ color: pos.unrealised_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{fmt(pos.unrealised_pnl || 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <div className="empty">No open positions</div>}
        </div>

        <div className="card">
          <div className="card-head"><span className="card-head-title">Recent Trades</span></div>
          {(data.trades || []).length > 0 ? (
            <div className="tbl-wrap">
              <table>
                <thead><tr><th>Stock</th><th>P&L</th><th>Reason</th><th>Time</th></tr></thead>
                <tbody>
                  {data.trades.slice(0, 5).map((t, i) => {
                    const rl = t.reason?.includes('TARGET') ? 'TGT' : t.reason?.includes('TIME') ? 'TIME' : t.reason?.includes('EOD') ? 'EOD' : 'SL';
                    const rc = rl === 'TGT' ? 'tag-ok' : rl === 'SL' ? 'tag-fail' : 'tag-warn';
                    return (
                      <tr key={i}>
                        <td style={{ fontWeight: 700, color: 'var(--amber)' }}>{t.symbol}</td>
                        <td style={{ color: t.pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{fmt(t.pnl || 0)}</td>
                        <td><span className={`tag ${rc}`}>{rl}</span></td>
                        <td className="c-dim">{t.exit_time}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : <div className="empty">No trades yet today</div>}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// SYSTEM HEALTH PAGE
// ═══════════════════════════════════════════════════════════════
function HealthPage({ health }) {
  if (!health) return <div className="empty">Loading...</div>;
  const components = health.components || {};
  return (
    <div className="page-enter" data-testid="health-page">
      <div className="grid-2">
        <div className="card">
          <div className="card-head"><span className="card-head-title">Component Health</span><span className="c-dim" style={{ fontSize: '0.65rem' }}>{health.timestamp}</span></div>
          {Object.entries(components).map(([k, v]) => (
            <div key={k} className="health-row">
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600 }}>{k.replace(/_/g, ' ').toUpperCase()}</div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-dim)' }}>{v.note}</div>
              </div>
              <div className="health-dot" style={{ background: v.ok ? 'var(--green)' : 'var(--red)' }} />
            </div>
          ))}
        </div>
        <div className="card">
          <div className="card-head"><span className="card-head-title">Risk Summary</span></div>
          {health.risk_summary && Object.entries(health.risk_summary).map(([k, v]) => (
            <div key={k} className="health-row">
              <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>{k.replace(/_/g, ' ')}</span>
              <span style={{ fontSize: '0.72rem', fontWeight: 600, fontFamily: "'JetBrains Mono',monospace" }}>{typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v)}</span>
            </div>
          ))}
          <div className="health-row">
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Market Open</span>
            <span className={`tag ${health.market_open ? 'tag-ok' : 'tag-fail'}`}>{health.market_open ? 'OPEN' : 'CLOSED'}</span>
          </div>
          <div className="health-row">
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Trading Hours</span>
            <span className={`tag ${health.trading_hours ? 'tag-ok' : 'tag-paused'}`}>{health.trading_hours ? 'ACTIVE' : 'INACTIVE'}</span>
          </div>
        </div>
      </div>
      <div className="card" style={{ marginTop: 10 }}>
        <div className="card-head"><span className="card-head-title">Safety Rules</span></div>
        <table><tbody>
          <tr><td className="c-dim">System Health Check</td><td>Every 15 seconds</td><td><span className="tag tag-ok">Auto</span></td></tr>
          <tr><td className="c-dim">Daily Loss &gt; 5%</td><td>HALT all trading</td><td><span className="tag tag-fail">Critical</span></td></tr>
          <tr><td className="c-dim">Portfolio Drawdown &gt; 10%</td><td>Pause strategies</td><td><span className="tag tag-fail">Critical</span></td></tr>
          <tr><td className="c-dim">WebSocket Drops</td><td>Auto-reconnect (exp backoff)</td><td><span className="tag tag-warn">Warning</span></td></tr>
          <tr><td className="c-dim">Order Fails</td><td>Retry 3x, then log CRITICAL</td><td><span className="tag tag-warn">Warning</span></td></tr>
          <tr><td className="c-dim">Duplicate Order</td><td>MongoDB check blocks it</td><td><span className="tag tag-ok">Protected</span></td></tr>
        </tbody></table>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// PREMARKET SCANNER PAGE
// ═══════════════════════════════════════════════════════════════
function PremarketPage({ premarket, loadPremarket }) {
  if (!premarket) return <div className="empty">Loading market data...</div>;
  const idx = premarket.indices || {};
  const MoverTable = ({ movers, title }) => (
    <div className="tbl-wrap">
      {movers.length > 0 ? (
        <table>
          <thead><tr><th>Symbol</th><th>Price</th><th>Change</th><th>Volume</th><th>Momentum</th></tr></thead>
          <tbody>
            {movers.map(m => (
              <tr key={m.symbol}>
                <td style={{ fontWeight: 700, color: 'var(--amber)' }}>{m.symbol}</td>
                <td>₹{m.price}</td>
                <td style={{ color: m.gap_pct >= 0 ? 'var(--green)' : 'var(--red)' }}>{m.gap_pct >= 0 ? '+' : ''}{m.gap_pct}%</td>
                <td><span className={`tag ${m.vol_score === 'High' ? 'tag-ok' : m.vol_score === 'Medium' ? 'tag-warn' : 'tag-paused'}`}>{m.vol_score}</span></td>
                <td><span className={`tag ${m.momentum?.includes('Bullish') ? 'tag-buy' : m.momentum?.includes('Bearish') ? 'tag-sell' : 'tag-paused'}`}>{m.momentum}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : <div className="empty">No data available</div>}
    </div>
  );

  return (
    <div className="page-enter" data-testid="premarket-page">
      <div className="grid-4">
        {['nifty', 'banknifty', 'vix', 'sensex'].map(k => {
          const d = idx[k] || {};
          const label = { nifty: 'NIFTY 50', banknifty: 'BANK NIFTY', vix: 'INDIA VIX', sensex: 'SENSEX' }[k];
          return (
            <div key={k} className="card idx-card">
              <div className="idx-name">{label}</div>
              <div className="idx-val">{d.price ? fmtINR(d.price) : '--'}</div>
              <div className="idx-chg" style={{ color: (d.change || 0) >= 0 ? 'var(--green)' : 'var(--red)' }}>
                {d.change !== undefined ? `${d.change >= 0 ? '+' : ''}${d.change}%` : '--'}
              </div>
            </div>
          );
        })}
      </div>
      <div className="grid-2">
        <div className="card">
          <div className="card-head"><span className="card-head-title" style={{ color: 'var(--green)' }}>Top Gap Ups</span></div>
          <MoverTable movers={premarket.gap_ups || []} />
        </div>
        <div className="card">
          <div className="card-head"><span className="card-head-title" style={{ color: 'var(--red)' }}>Top Gap Downs</span></div>
          <MoverTable movers={premarket.gap_downs || []} />
        </div>
      </div>
      <div className="card">
        <div className="card-head">
          <span className="card-head-title">Pre-Market Movers &mdash; Nifty 50</span>
          <button data-testid="premarket-refresh" onClick={loadPremarket} style={{ padding: '4px 12px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 3, color: 'var(--green)', fontFamily: 'inherit', fontSize: '0.68rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}>
            <RefreshCw size={12} /> Refresh
          </button>
        </div>
        <MoverTable movers={premarket.movers || []} />
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// STRATEGIES PAGE
// ═══════════════════════════════════════════════════════════════
function StrategiesPage({ strategies }) {
  if (!strategies) return <div className="empty">Loading...</div>;
  const st = strategies.agent_state || 'NORMAL';
  return (
    <div className="page-enter" data-testid="strategies-page">
      <div className="grid-3">
        <StatCard label="Active Strategies" value={(strategies.strategies || []).length} sub="Running in parallel" color="var(--cyan)" accent="ca-cyan" />
        <StatCard label="Min Signal Score" value={strategies.min_score || 6} sub={st === 'SELECTIVE' ? 'Selective mode' : 'Normal mode'} color="var(--amber)" accent="ca-amber" />
        <StatCard label="Agent State" value={st} color={st === 'HALTED' ? 'var(--red)' : st === 'SELECTIVE' ? 'var(--amber)' : 'var(--green)'} accent="ca-green" />
      </div>
      {(strategies.strategies || []).map((s, i) => (
        <div key={i} className="strat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <div>
              <div style={{ fontSize: '0.82rem', fontWeight: 700 }}>{s.name}</div>
              <div style={{ fontSize: '0.6rem', color: 'var(--text-dim)' }}>{s.type}</div>
            </div>
            <span className={`tag ${s.status === 'ACTIVE' ? 'tag-active' : 'tag-paused'}`}>{s.status}</span>
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginBottom: 8 }}>{s.description}</div>
          {s.params && (
            <div className="strat-meta">
              {Object.entries(s.params).map(([pk, pv]) => (
                <div key={pk} className="strat-meta-item">
                  <div className="strat-meta-label">{pk.replace(/_/g, ' ')}</div>
                  <div className="strat-meta-val">{pv}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// POSITIONS PAGE
// ═══════════════════════════════════════════════════════════════
function PositionsPage({ data }) {
  const positions = data.open_positions || [];
  const totalUnreal = positions.reduce((s, p) => s + (p.unrealised_pnl || 0), 0);
  const exposure = positions.reduce((s, p) => s + (p.entry || 0) * (p.qty || 0), 0);
  return (
    <div className="page-enter" data-testid="positions-page">
      <div className="grid-3">
        <StatCard label="Open Positions" value={positions.length} color="var(--cyan)" accent="ca-cyan" />
        <StatCard label="Unrealised P&L" value={`₹${fmt(totalUnreal)}`} color={totalUnreal >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" />
        <StatCard label="Total Exposure" value={`₹${fmtINR(exposure)}`} color="var(--amber)" accent="ca-amber" />
      </div>
      <div className="card">
        <div className="card-head"><span className="card-head-title">Open Positions</span></div>
        {positions.length > 0 ? (
          <div className="tbl-wrap">
            <table>
              <thead><tr><th>Stock</th><th>Side</th><th>Qty</th><th>Entry</th><th>Current</th><th>SL</th><th>Target</th><th>Phase</th><th>P&L</th></tr></thead>
              <tbody>
                {positions.map(p => (
                  <tr key={p.symbol}>
                    <td style={{ fontWeight: 700, color: 'var(--amber)' }}>{p.symbol}</td>
                    <td><span className={`tag tag-${p.action?.toLowerCase()}`}>{p.action}</span></td>
                    <td>{p.qty}</td>
                    <td>₹{p.entry?.toFixed(2)}</td>
                    <td>₹{p.current?.toFixed(2)}</td>
                    <td style={{ color: 'var(--red)' }}>₹{p.sl?.toFixed(2)}</td>
                    <td style={{ color: 'var(--green)' }}>₹{p.target?.toFixed(2)}</td>
                    <td><span className="tag tag-info">{p.sl_phase}</span></td>
                    <td style={{ color: (p.unrealised_pnl || 0) >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{fmt(p.unrealised_pnl || 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <div className="empty">No open positions</div>}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// TRADES PAGE
// ═══════════════════════════════════════════════════════════════
function TradesPage({ data }) {
  const [filter, setFilter] = useState('all');
  let trades = data.all_trades || [];
  if (filter === 'wins') trades = trades.filter(t => t.pnl > 0);
  if (filter === 'loss') trades = trades.filter(t => t.pnl <= 0);
  const todayTrades = data.trades || [];
  const totalPnl = todayTrades.reduce((s, t) => s + (t.pnl || 0), 0);

  return (
    <div className="page-enter" data-testid="trades-page">
      <div className="grid-3">
        <StatCard label="Total Trades" value={todayTrades.length} color="var(--cyan)" accent="ca-cyan" />
        <StatCard label="Wins / Losses" value={`${data.wins || 0} / ${data.losses || 0}`} color="var(--amber)" accent="ca-amber" />
        <StatCard label="Net P&L" value={`₹${fmt(totalPnl)}`} color={totalPnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" />
      </div>
      <div style={{ marginBottom: 10 }}>
        <select data-testid="trade-filter" value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="all">All Trades</option>
          <option value="wins">Wins Only</option>
          <option value="loss">Losses Only</option>
        </select>
      </div>
      <div className="card">
        <div className="tbl-wrap">
          {trades.length > 0 ? (
            <table>
              <thead><tr><th>Date</th><th>Stock</th><th>Side</th><th>Qty</th><th>Entry</th><th>Exit</th><th>P&L</th><th>Reason</th><th>Score</th></tr></thead>
              <tbody>
                {trades.slice(0, 50).map((t, i) => (
                  <tr key={i}>
                    <td className="c-dim">{t.date}</td>
                    <td style={{ fontWeight: 700, color: 'var(--amber)' }}>{t.symbol}</td>
                    <td><span className={`tag tag-${t.action?.toLowerCase()}`}>{t.action}</span></td>
                    <td>{t.qty}</td>
                    <td>₹{t.entry?.toFixed(2)}</td>
                    <td>₹{t.exit?.toFixed(2)}</td>
                    <td style={{ color: t.pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{fmt(t.pnl || 0)}</td>
                    <td><span className={`tag ${t.reason?.includes('TARGET') ? 'tag-ok' : t.reason?.includes('STOP') ? 'tag-fail' : 'tag-warn'}`}>{t.reason}</span></td>
                    <td>{t.score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <div className="empty">No trades yet</div>}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// RISK PAGE
// ═══════════════════════════════════════════════════════════════
function RiskPage({ risk }) {
  if (!risk) return <div className="empty">Loading...</div>;
  const lp = risk.loss_pct || 0;
  const barColor = lp > 80 ? 'var(--red)' : lp > 50 ? 'var(--amber)' : 'var(--green)';
  return (
    <div className="page-enter" data-testid="risk-page">
      <div className="grid-4">
        <StatCard label="Daily Loss Used" value={`₹${risk.loss_used?.toFixed(0) || 0}`} sub={`₹${risk.loss_remaining?.toFixed(0) || 0} remaining`} color="var(--red)" accent="ca-red" />
        <StatCard label="Loss Limit (5%)" value={`₹${risk.daily_loss_limit?.toFixed(0) || 500}`} sub="Trading halts at this level" color="var(--amber)" accent="ca-amber" />
        <StatCard label="Day Profit" value={`₹${fmt(risk.day_pnl || 0)}`} sub="Target: ₹300-500/day" color={risk.day_pnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" />
        <StatCard label="Open Risk" value={`₹${risk.open_risk?.toFixed(0) || 0}`} sub="Live exposure in trades" color="var(--purple)" accent="ca-purple" />
      </div>
      <div className="grid-2">
        <div className="card">
          <div className="card-head">
            <span className="card-head-title">Daily Loss Meter</span>
            <span className={`tag ${risk.risk_level === 'SAFE' ? 'tag-safe' : risk.risk_level === 'WARNING' ? 'tag-warn' : 'tag-danger'}`}>{risk.risk_level}</span>
          </div>
          <div className="risk-gauge">
            <div className="risk-pct" style={{ color: barColor }}>{lp.toFixed(0)}%</div>
            <div style={{ fontSize: '0.62rem', color: 'var(--text-dim)', marginTop: 4 }}>of daily limit used</div>
          </div>
          <div className="prog-bar" style={{ height: 10, marginTop: 8 }}>
            <div className="prog-fill" style={{ width: `${Math.min(100, lp)}%`, background: barColor }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.58rem', color: 'var(--text-dim)', marginTop: 4 }}>
            <span>₹0</span><span style={{ color: 'var(--amber)' }}>50%</span><span>HALT</span>
          </div>
          {risk.drawdown_pct > 0 && (
            <div style={{ marginTop: 12 }}>
              <div className="card-label">Portfolio Drawdown</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: risk.drawdown_pct >= risk.max_drawdown ? 'var(--red)' : 'var(--amber)' }}>
                {risk.drawdown_pct.toFixed(1)}% / {risk.max_drawdown}% max
              </div>
            </div>
          )}
        </div>
        <div className="card">
          <div className="card-head"><span className="card-head-title">Risk Rules</span></div>
          <table><tbody>
            <tr><td className="c-dim">Max Loss/Day</td><td style={{ color: 'var(--red)' }}>5% Portfolio &rarr; HALT</td></tr>
            <tr><td className="c-dim">Max Drawdown</td><td style={{ color: 'var(--red)' }}>{risk.max_drawdown || 10}% &rarr; Pause</td></tr>
            <tr><td className="c-dim">Max Risk/Trade</td><td style={{ color: 'var(--red)' }}>₹{risk.max_per_trade || 200} (2%)</td></tr>
            <tr><td className="c-dim">Selective Mode</td><td style={{ color: 'var(--amber)' }}>₹500 profit</td></tr>
            <tr><td className="c-dim">Protect Mode</td><td style={{ color: 'var(--amber)' }}>₹800 profit</td></tr>
            <tr><td className="c-dim">Order Retries</td><td>3x with backoff</td></tr>
            <tr><td className="c-dim">Duplicate Prevention</td><td style={{ color: 'var(--green)' }}>MongoDB check</td></tr>
            <tr><td className="c-dim">Time Stop</td><td>15 min per trade</td></tr>
            <tr><td className="c-dim">SL Phase 1</td><td>Breakeven at +₹100</td></tr>
            <tr><td className="c-dim">SL Phase 2</td><td>Lock ₹75 at +₹150</td></tr>
            <tr><td className="c-dim">SL Phase 3</td><td>Trail 50% at +₹200</td></tr>
          </tbody></table>
        </div>
      </div>
      <div className="card" style={{ marginTop: 10 }}>
        <div style={{ padding: 14, textAlign: 'center' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>{risk.trading_allowed ? '✅' : '⛔'}</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 800, color: risk.trading_allowed ? 'var(--green)' : 'var(--red)' }}>
            {risk.trading_allowed ? 'TRADING ACTIVE' : 'TRADING HALTED'}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: 5 }}>
            {risk.agent_state === 'NORMAL' ? 'All systems normal' : `State: ${risk.agent_state}`}
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// P&L HISTORY PAGE
// ═══════════════════════════════════════════════════════════════
function PnlHistoryPage({ data }) {
  const dailyPnl = data.daily_pnl || [];
  const todayPnl = data.day_pnl || 0;
  const allTimePnl = dailyPnl.reduce((s, d) => s + d.pnl, 0);
  const weekPnl = dailyPnl.slice(-5).reduce((s, d) => s + d.pnl, 0);
  const monthPnl = dailyPnl.slice(-22).reduce((s, d) => s + d.pnl, 0);

  return (
    <div className="page-enter" data-testid="pnl-page">
      <div className="grid-4">
        <StatCard label="Today" value={`₹${fmt(todayPnl)}`} color={todayPnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-green" />
        <StatCard label="This Week" value={`₹${fmt(weekPnl)}`} color={weekPnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-cyan" />
        <StatCard label="This Month" value={`₹${fmt(monthPnl)}`} color={monthPnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-amber" />
        <StatCard label="All Time" value={`₹${fmt(allTimePnl)}`} color={allTimePnl >= 0 ? 'var(--green)' : 'var(--red)'} accent="ca-purple" />
      </div>
      <div className="card" style={{ marginBottom: 12 }}>
        <div className="card-head"><span className="card-head-title">Daily P&L</span></div>
        <div style={{ height: 200 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={dailyPnl}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="date" tick={{ fill: '#71717a', fontSize: 9 }} />
              <YAxis tick={{ fill: '#71717a', fontSize: 9 }} />
              <Tooltip contentStyle={{ background: '#121214', border: '1px solid #27272a', fontSize: 11 }} />
              <Bar dataKey="pnl" radius={[3, 3, 0, 0]}>
                {dailyPnl.map((d, i) => <Cell key={i} fill={d.pnl >= 0 ? '#22c55e' : '#ef4444'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="card">
        <div className="card-head"><span className="card-head-title">Daily Breakdown</span></div>
        {dailyPnl.length > 0 ? (
          <div className="tbl-wrap">
            <table>
              <thead><tr><th>Date</th><th>Trades</th><th>W/L</th><th>P&L</th></tr></thead>
              <tbody>
                {[...dailyPnl].reverse().map((d, i) => (
                  <tr key={i}>
                    <td className="c-dim">{d.date}</td>
                    <td>{d.trades}</td>
                    <td><span className="c-green">{d.wins}</span>/<span className="c-red">{d.losses}</span></td>
                    <td style={{ color: d.pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>₹{fmt(d.pnl)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <div className="empty">No history</div>}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// AUDIT LOG PAGE
// ═══════════════════════════════════════════════════════════════
function AuditPage({ logs, audit }) {
  const typeColor = {
    BOT_START: 'var(--green)', BOT_STOP: 'var(--red)',
    WEBSOCKET_CONNECTED: 'var(--green)', WEBSOCKET_DISCONNECTED: 'var(--red)',
    SIGNAL_GENERATED: 'var(--cyan)', ORDER_PLACED: 'var(--green)',
    ORDER_FAILED: 'var(--red)', ORDER_CRITICAL_FAIL: 'var(--red)',
    ORDER_DUPLICATE_BLOCKED: 'var(--amber)', ORDER_REJECTED: 'var(--text-dim)',
    TRADE_EXITED: 'var(--blue)', RISK_HALT: 'var(--red)',
    RISK_SELECTIVE: 'var(--amber)', RISK_PROTECT: 'var(--blue)',
    RISK_DRAWDOWN: 'var(--red)',
  };

  return (
    <div className="page-enter" data-testid="audit-page">
      {audit && (
        <div className="card" style={{ marginBottom: 12 }}>
          <div className="card-head">
            <span className="card-head-title">System Audit Summary</span>
            <span className={`tag ${audit.all_fixed ? 'tag-ok' : 'tag-fail'}`}>{audit.all_fixed ? 'ALL FIXED' : 'ISSUES OPEN'}</span>
          </div>
          <div className="grid-4" style={{ marginBottom: 0 }}>
            <div style={{ textAlign: 'center' }}><div style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--red)' }}>{audit.critical}</div><div className="card-label">Critical</div></div>
            <div style={{ textAlign: 'center' }}><div style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--amber)' }}>{audit.high}</div><div className="card-label">High</div></div>
            <div style={{ textAlign: 'center' }}><div style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--blue)' }}>{audit.medium}</div><div className="card-label">Medium</div></div>
            <div style={{ textAlign: 'center' }}><div style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--text-dim)' }}>{audit.low}</div><div className="card-label">Low</div></div>
          </div>
          <div className="tbl-wrap" style={{ marginTop: 12 }}>
            <table>
              <thead><tr><th>ID</th><th>Severity</th><th>Category</th><th>Issue</th><th>Fix</th><th>Status</th></tr></thead>
              <tbody>
                {(audit.issues || []).map(iss => (
                  <tr key={iss.id}>
                    <td>#{iss.id}</td>
                    <td><span className={`tag ${iss.severity === 'CRITICAL' ? 'tag-fail' : iss.severity === 'HIGH' ? 'tag-warn' : 'tag-info'}`}>{iss.severity}</span></td>
                    <td>{iss.category}</td>
                    <td style={{ fontFamily: "'Outfit',sans-serif", fontSize: '0.72rem' }}>{iss.description}</td>
                    <td style={{ fontFamily: "'Outfit',sans-serif", fontSize: '0.68rem', color: 'var(--text-muted)' }}>{iss.fix}</td>
                    <td><span className="tag tag-ok">{iss.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      <div className="card">
        <div className="card-head"><span className="card-head-title">Event Logs</span><span className="c-dim" style={{ fontSize: '0.62rem' }}>{(logs || []).length} entries</span></div>
        {(logs || []).length > 0 ? (
          <div style={{ maxHeight: 400, overflowY: 'auto' }}>
            {logs.map((l, i) => (
              <div key={i} className="log-entry">
                <span className="log-time">{l.timestamp?.slice(11, 19) || '--'}</span>
                <span className="log-type" style={{ color: typeColor[l.event_type] || 'var(--text-muted)' }}>{l.event_type}</span>
                <span className="log-msg">{l.message}</span>
              </div>
            ))}
          </div>
        ) : <div className="empty">No logs yet</div>}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// F&O CALCULATOR PAGE
// ═══════════════════════════════════════════════════════════════
function FOPage({ data }) {
  const [entry, setEntry] = useState(22000);
  const [sl, setSl] = useState(21950);
  const [target, setTarget] = useState(22100);
  const [port, setPort] = useState(10000);
  const [inst, setInst] = useState('equity');
  const [result, setResult] = useState(null);

  const calculate = async () => {
    try {
      const r = await fetch(`${API}/api/fo/calculate?entry=${entry}&sl=${sl}&target=${target}&portfolio=${port}&instrument=${inst}`);
      setResult(await r.json());
    } catch { }
  };

  const pv = data.portfolio_value || 10000;
  const pct = Math.min(100, (pv / 50000) * 100);

  return (
    <div className="page-enter" data-testid="fo-page">
      <div className="grid-2">
        <div className="card">
          <div className="card-head"><span className="card-head-title">F&O Trade Calculator</span></div>
          <div className="card-label">Instrument</div>
          <select data-testid="fo-instrument" value={inst} onChange={e => setInst(e.target.value)} style={{ width: '100%', marginBottom: 10 }}>
            <option value="equity">Equity (Cash)</option>
            <option value="stock_fut">Stock Futures</option>
            <option value="nifty_fut">Nifty Futures (Lot: 25)</option>
            <option value="banknifty_fut">BankNifty Futures (Lot: 15)</option>
            <option value="nifty_opt">Nifty Options (Lot: 25)</option>
            <option value="banknifty_opt">BankNifty Options (Lot: 15)</option>
          </select>
          <div className="card-label">Entry Price</div>
          <input className="fo-input" data-testid="fo-entry" type="number" value={entry} onChange={e => setEntry(+e.target.value)} />
          <div className="card-label">Stop Loss</div>
          <input className="fo-input" data-testid="fo-sl" type="number" value={sl} onChange={e => setSl(+e.target.value)} />
          <div className="card-label">Target</div>
          <input className="fo-input" data-testid="fo-target" type="number" value={target} onChange={e => setTarget(+e.target.value)} />
          <div className="card-label">Portfolio Size</div>
          <input className="fo-input" data-testid="fo-port" type="number" value={port} onChange={e => setPort(+e.target.value)} />
          <button className="fo-btn" data-testid="fo-calculate" onClick={calculate}>CALCULATE</button>
        </div>
        <div className="card">
          <div className="card-head"><span className="card-head-title">Trade Metrics</span></div>
          {result ? (
            <div>
              {Object.entries(result).map(([k, v]) => (
                <div key={k} className="fo-row">
                  <span className="c-dim">{k.replace(/_/g, ' ')}</span>
                  <span style={{ fontWeight: 600 }}>{typeof v === 'number' ? (k.includes('pct') ? `${v}%` : k === 'rr_ratio' ? `${v}:1` : `₹${v}`) : v}</span>
                </div>
              ))}
            </div>
          ) : <div className="empty">Enter values and click Calculate</div>}
        </div>
      </div>
      <div className="card" style={{ marginTop: 10 }}>
        <div className="card-head"><span className="card-head-title">F&O Roadmap</span></div>
        <div style={{ marginTop: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', marginBottom: 4 }}>
            <span className="c-dim">Portfolio Progress to Phase 4 (₹50,000)</span>
            <span style={{ color: 'var(--amber)' }}>{pct.toFixed(0)}%</span>
          </div>
          <div className="prog-bar" style={{ height: 6 }}>
            <div className="prog-fill" style={{ width: `${pct}%`, background: 'var(--amber)' }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.58rem', color: 'var(--text-dim)', marginTop: 3 }}>
            <span>₹{fmtINR(pv)}</span><span>₹50,000</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// SETTINGS PAGE
// ═══════════════════════════════════════════════════════════════
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
            <tr><td className="c-dim">Selective Mode At</td><td style={{ color: 'var(--amber)' }}>₹{config.daily_profit_selective}</td></tr>
            <tr><td className="c-dim">Stop All At</td><td style={{ color: 'var(--amber)' }}>₹{config.daily_profit_stop}</td></tr>
            <tr><td className="c-dim">Min Score (Normal)</td><td>{config.min_signal_score}/10</td></tr>
            <tr><td className="c-dim">Min Score (Selective)</td><td>{config.min_score_selective}/10</td></tr>
            <tr><td className="c-dim">Order Retries</td><td>{config.order_max_retries}x</td></tr>
            <tr><td className="c-dim">Risk:Reward</td><td>1:{config.risk_reward_ratio}</td></tr>
            <tr><td className="c-dim">EMA Fast/Slow</td><td>{config.ema_fast}/{config.ema_slow}</td></tr>
          </tbody></table>
        </div>
        <div className="card">
          <div className="card-head"><span className="card-head-title">System Info</span></div>
          <table><tbody>
            <tr><td className="c-dim">Mode</td><td><span className={`tag ${config.trading_mode === 'live' ? 'tag-ok' : 'tag-paper'}`}>{config.trading_mode?.toUpperCase()}</span></td></tr>
            <tr><td className="c-dim">Broker</td><td><span className={`tag ${config.kite_configured ? 'tag-ok' : 'tag-fail'}`}>Zerodha Kite {config.kite_configured ? '(OK)' : '(No Token)'}</span></td></tr>
            <tr><td className="c-dim">Telegram</td><td><span className={`tag ${config.telegram_configured ? 'tag-ok' : 'tag-fail'}`}>{config.telegram_configured ? 'Connected' : 'Not Set'}</span></td></tr>
            <tr><td className="c-dim">Market Hours</td><td>{config.market_open} - {config.market_close}</td></tr>
            <tr><td className="c-dim">Trading Window</td><td>{config.trading_start} - {config.trading_end}</td></tr>
            <tr><td className="c-dim">Max Leverage</td><td>{config.max_leverage}x</td></tr>
          </tbody></table>
          <div style={{ marginTop: 14, padding: '10px 12px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 4 }}>
            <div className="card-label">Monthly Cost</div>
            <div style={{ fontSize: '0.72rem' }}>
              <div className="fo-row"><span className="c-dim">Zerodha API</span><span>₹500</span></div>
              <div className="fo-row"><span className="c-dim">MiniMax AI</span><span>~₹40</span></div>
              <div className="fo-row"><span className="c-dim">GCP VM</span><span className="c-green">₹0</span></div>
              <div className="fo-row" style={{ borderTop: '1px solid var(--border)', paddingTop: 4 }}><span style={{ fontWeight: 700 }}>Total</span><span style={{ fontWeight: 700, color: 'var(--amber)' }}>₹540/mo</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════════════════
const NAV_ITEMS = [
  { group: 'Monitor', items: [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'health', label: 'System Health', icon: HeartPulse },
  ]},
  { group: 'Market', items: [
    { id: 'premarket', label: 'Premarket Scanner', icon: ScanSearch },
    { id: 'strategies', label: 'Strategy Monitor', icon: BrainCircuit },
  ]},
  { group: 'Trading', items: [
    { id: 'positions', label: 'Positions', icon: Target },
    { id: 'trades', label: 'Trade Log', icon: ListOrdered },
    { id: 'risk', label: 'Risk Dashboard', icon: ShieldAlert },
  ]},
  { group: 'Tools', items: [
    { id: 'pnl', label: 'P&L History', icon: TrendingUp },
    { id: 'fo', label: 'F&O Calculator', icon: Calculator },
    { id: 'audit', label: 'Audit & Logs', icon: ScrollText },
    { id: 'settings', label: 'Settings', icon: Settings },
  ]},
];

const PAGE_TITLES = {
  dashboard: 'Dashboard', health: 'System Health', premarket: 'Premarket Scanner',
  strategies: 'Strategy Monitor', positions: 'Positions', trades: 'Trade Log',
  risk: 'Risk Dashboard', pnl: 'P&L History', fo: 'F&O Calculator',
  audit: 'Audit & Logs', settings: 'Settings'
};

function App() {
  const [authed, setAuthed] = useState(false);
  const [page, setPage] = useState('dashboard');
  const [clock, setClock] = useState('');
  const [marketOpen, setMarketOpen] = useState(false);

  const [data, setData] = useState({});
  const [health, setHealth] = useState(null);
  const [risk, setRisk] = useState(null);
  const [strategies, setStrategies] = useState(null);
  const [premarket, setPremarket] = useState(null);
  const [logs, setLogs] = useState([]);
  const [audit, setAudit] = useState(null);
  const [config, setConfig] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/data`);
      const d = await r.json();
      setData(d);
    } catch { }
  }, []);

  const fetchHealth = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/health`);
      setHealth(await r.json());
    } catch { }
  }, []);

  const fetchRisk = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/risk`);
      setRisk(await r.json());
    } catch { }
  }, []);

  const fetchStrategies = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/strategies`);
      setStrategies(await r.json());
    } catch { }
  }, []);

  const loadPremarket = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/premarket`);
      setPremarket(await r.json());
    } catch { }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/logs?limit=100`);
      const d = await r.json();
      setLogs(d.logs || []);
    } catch { }
  }, []);

  const fetchAudit = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/audit`);
      setAudit(await r.json());
    } catch { }
  }, []);

  const fetchConfig = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/config`);
      setConfig(await r.json());
    } catch { }
  }, []);

  useEffect(() => {
    if (!authed) return;
    fetchData();
    fetchHealth();
    fetchRisk();
    fetchConfig();
    fetchAudit();
    const t1 = setInterval(fetchData, 15000);
    const t2 = setInterval(fetchHealth, 30000);
    const t3 = setInterval(fetchRisk, 20000);
    return () => { clearInterval(t1); clearInterval(t2); clearInterval(t3); };
  }, [authed, fetchData, fetchHealth, fetchRisk, fetchConfig, fetchAudit]);

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      const ist = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
      setClock(ist.toTimeString().substr(0, 8) + ' IST');
      const h = ist.getHours(), m = ist.getMinutes();
      setMarketOpen((h > 9 || (h === 9 && m >= 15)) && (h < 15 || (h === 15 && m < 30)));
    };
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, []);

  const handleNav = (id) => {
    setPage(id);
    if (id === 'premarket') loadPremarket();
    if (id === 'strategies') fetchStrategies();
    if (id === 'audit') { fetchLogs(); fetchAudit(); }
    if (id === 'settings') fetchConfig();
  };

  if (!authed) return <LoginPage onLogin={() => setAuthed(true)} />;

  const p = data.day_pnl || 0;
  const stateColors = { NORMAL: 'var(--green)', SELECTIVE: 'var(--amber)', HALTED: 'var(--red)', PROTECTED: 'var(--blue)' };

  return (
    <div className="app-layout" data-testid="app-layout">
      <div className="sidebar">
        <div className="sidebar-logo">
          <h1>MINIMAX</h1>
          <p>PRO TERMINAL</p>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map(g => (
            <React.Fragment key={g.group}>
              <div className="nav-group">{g.group}</div>
              {g.items.map(item => (
                <div key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => handleNav(item.id)} data-testid={`nav-${item.id}`}>
                  <item.icon size={16} />
                  <span>{item.label}</span>
                </div>
              ))}
            </React.Fragment>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 3 }}>
            <span className="status-dot" style={{ background: stateColors[data.agent_state] || 'var(--green)' }} />
            <span style={{ color: stateColors[data.agent_state] || 'var(--green)' }}>{data.agent_state || 'NORMAL'}</span>
          </div>
          <span style={{ color: 'var(--text-dim)' }}>MODE: <span style={{ color: 'var(--purple)' }}>{data.mode || 'PAPER'}</span></span>
        </div>
      </div>

      <div className="main-content">
        <div className="topbar">
          <div className="topbar-title">{PAGE_TITLES[page]}</div>
          <div className="topbar-right">
            <span style={{ color: 'var(--text-dim)' }}>NSE <span className="blink" style={{ color: marketOpen ? 'var(--green)' : 'var(--red)' }}>●</span></span>
            <span className="pill pill-pnl" style={{ background: p >= 0 ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)', color: p >= 0 ? 'var(--green)' : 'var(--red)', borderColor: p >= 0 ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)' }}>
              Day: ₹{fmt(p)}
            </span>
            <span className={`pill ${data.mode === 'LIVE' ? 'pill-live' : 'pill-mode'}`}>{data.mode || 'PAPER'}</span>
            <span className="clock">{clock}</span>
          </div>
        </div>

        <div className="content-area">
          {page === 'dashboard' && <DashboardPage data={data} />}
          {page === 'health' && <HealthPage health={health} />}
          {page === 'premarket' && <PremarketPage premarket={premarket} loadPremarket={loadPremarket} />}
          {page === 'strategies' && <StrategiesPage strategies={strategies} />}
          {page === 'positions' && <PositionsPage data={data} />}
          {page === 'trades' && <TradesPage data={data} />}
          {page === 'risk' && <RiskPage risk={risk} />}
          {page === 'pnl' && <PnlHistoryPage data={data} />}
          {page === 'fo' && <FOPage data={data} />}
          {page === 'audit' && <AuditPage logs={logs} audit={audit} />}
          {page === 'settings' && <SettingsPage config={config} />}
        </div>
      </div>
    </div>
  );
}

export default App;
