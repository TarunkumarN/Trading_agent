/**
 * charts.js — Chart.js configuration for MiniMax Trading Dashboard
 * Dark theme, responsive, with INR formatting
 */

const CHART_COLORS = {
  green: '#22c55e',
  red: '#ef4444',
  amber: '#eab308',
  blue: '#3b82f6',
  purple: '#a855f7',
  cyan: '#06b6d4',
  grid: '#27272a',
  text: '#71717a',
  bg: '#121214',
};

const DARK_THEME = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: CHART_COLORS.text, font: { family: "'JetBrains Mono', monospace", size: 11 } } },
    tooltip: { backgroundColor: CHART_COLORS.bg, borderColor: CHART_COLORS.grid, borderWidth: 1, titleColor: '#fafafa', bodyColor: '#a1a1aa', bodyFont: { family: "'JetBrains Mono', monospace" } },
  },
  scales: {
    x: { grid: { color: CHART_COLORS.grid }, ticks: { color: CHART_COLORS.text, font: { size: 10 } } },
    y: { grid: { color: CHART_COLORS.grid }, ticks: { color: CHART_COLORS.text, font: { size: 10 } } },
  },
};

function createEquityCurve(ctx, data) {
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.date),
      datasets: [{ label: 'Equity', data: data.map(d => d.equity), borderColor: CHART_COLORS.green, backgroundColor: 'rgba(34,197,94,0.1)', fill: true, tension: 0.3, pointRadius: 3 }],
    },
    options: { ...DARK_THEME },
  });
}

function createDailyPnL(ctx, data) {
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.date),
      datasets: [{ label: 'P&L', data: data.map(d => d.pnl), backgroundColor: data.map(d => d.pnl >= 0 ? CHART_COLORS.green : CHART_COLORS.red), borderRadius: 4 }],
    },
    options: { ...DARK_THEME },
  });
}

function createStrategyPerformance(ctx, strategies) {
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: strategies.map(s => s.name),
      datasets: [
        { label: 'Total P&L', data: strategies.map(s => s.metrics?.total_pnl || 0), backgroundColor: strategies.map(s => (s.metrics?.total_pnl || 0) >= 0 ? CHART_COLORS.green : CHART_COLORS.red), borderRadius: 4 },
      ],
    },
    options: { ...DARK_THEME, indexAxis: 'y' },
  });
}

function createTradeDistribution(ctx, data) {
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.map(d => d.range),
      datasets: [{ data: data.map(d => d.count), backgroundColor: [CHART_COLORS.red, '#f97316', CHART_COLORS.amber, CHART_COLORS.cyan, CHART_COLORS.green, CHART_COLORS.blue] }],
    },
    options: { ...DARK_THEME, plugins: { ...DARK_THEME.plugins, legend: { position: 'right', labels: { color: CHART_COLORS.text } } } },
  });
}
