'use client';

import { useState, useEffect } from 'react';

// Mock analytics data — in production, fetched from API
const MOCK_ANALYTICS = {
  sharpe_ratio: 1.84,
  sortino_ratio: 2.31,
  calmar_ratio: 1.65,
  max_drawdown: 7.8,
  profit_factor: 2.14,
  avg_win: 48.32,
  avg_loss: -22.15,
  risk_reward: 2.18,
  total_pips: 1847,
  win_by_instrument: { EURUSD: 72, GBPUSD: 65, XAUUSD: 78, USDJPY: 60, NAS100: 71, BTCUSD: 55 } as Record<string, number>,
  win_by_timeframe: { M15: 58, M30: 63, H1: 72, H4: 75, D1: 68 } as Record<string, number>,
  win_by_session: { Asian: 61, London: 74, 'New York': 69 } as Record<string, number>,
  win_by_day: { Mon: 68, Tue: 72, Wed: 70, Thu: 65, Fri: 63 } as Record<string, number>,
  model_performance: {
    Trend: { accuracy: 74.2, pnl: 5420.30, trades: 142 },
    Reversion: { accuracy: 68.5, pnl: 3210.45, trades: 98 },
    Volatility: { accuracy: 81.3, pnl: 2180.10, trades: 67 },
    Sentiment: { accuracy: 62.1, pnl: 1250.80, trades: 85 },
    'Order Flow': { accuracy: 70.8, pnl: 1780.90, trades: 72 },
  } as Record<string, { accuracy: number; pnl: number; trades: number }>,
};

function BarChart({ data, colorFn }: { data: Record<string, number>; colorFn?: (val: number) => string }) {
  const max = Math.max(...Object.values(data));
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {Object.entries(data).map(([label, value]) => (
        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 60, fontSize: 12, color: 'var(--text-secondary)', textAlign: 'right', flexShrink: 0 }}>{label}</div>
          <div style={{ flex: 1, height: 24, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', overflow: 'hidden', position: 'relative' }}>
            <div style={{
              height: '100%',
              width: `${(value / max) * 100}%`,
              background: colorFn ? colorFn(value) : 'var(--gradient-blue)',
              borderRadius: 'var(--radius-sm)',
              transition: 'width 0.6s ease-out',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              paddingRight: 8,
            }}>
              <span style={{ fontSize: 11, fontWeight: 600, color: 'white', fontFamily: 'var(--font-mono)' }}>
                {value}%
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AnalysisPage() {
  const [data] = useState(MOCK_ANALYTICS);

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>🔬 Portfolio Analysis</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24, fontSize: 14 }}>
        Deep performance analytics across all dimensions — instruments, timeframes, sessions, and model categories.
      </p>

      {/* Key Metrics */}
      <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))' }}>
        {[
          { label: 'Sharpe Ratio', value: data.sharpe_ratio.toFixed(2), icon: '📐', color: 'var(--accent-blue)' },
          { label: 'Sortino Ratio', value: data.sortino_ratio.toFixed(2), icon: '📊', color: 'var(--accent-cyan)' },
          { label: 'Calmar Ratio', value: data.calmar_ratio.toFixed(2), icon: '⚖️', color: 'var(--accent-indigo)' },
          { label: 'Profit Factor', value: data.profit_factor.toFixed(2), icon: '💹', color: 'var(--success)' },
          { label: 'Risk:Reward', value: `1:${data.risk_reward.toFixed(1)}`, icon: '🎯', color: 'var(--warning)' },
          { label: 'Total Pips', value: data.total_pips.toLocaleString(), icon: '📈', color: 'var(--text-primary)' },
        ].map(metric => (
          <div key={metric.label} className="card animate-fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                {metric.label}
              </span>
              <span>{metric.icon}</span>
            </div>
            <div style={{ fontSize: 26, fontWeight: 700, color: metric.color, fontFamily: 'var(--font-mono)' }}>
              {metric.value}
            </div>
          </div>
        ))}
      </div>

      {/* Win / Loss Averages */}
      <div className="section-grid" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Avg Win vs Avg Loss</div>
          <div style={{ display: 'flex', gap: 24 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: 'var(--success)', marginBottom: 4 }}>Average Win</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--success)', fontFamily: 'var(--font-mono)' }}>
                +${data.avg_win.toFixed(2)}
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: 'var(--danger)', marginBottom: 4 }}>Average Loss</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--danger)', fontFamily: 'var(--font-mono)' }}>
                -${Math.abs(data.avg_loss).toFixed(2)}
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Max Drawdown</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--danger)', fontFamily: 'var(--font-mono)', marginBottom: 8 }}>
            {data.max_drawdown}%
          </div>
          <div className="drawdown-progress">
            <div className="drawdown-fill drawdown-warning" style={{ width: `${data.max_drawdown * 10}%` }} />
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
            Measured from peak equity to trough
          </div>
        </div>
      </div>

      {/* Win Rate Breakdowns */}
      <div className="section-grid" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Win Rate by Instrument</div>
          <BarChart data={data.win_by_instrument} colorFn={(v) => v >= 70 ? 'var(--success)' : v >= 60 ? 'var(--accent-blue)' : 'var(--warning)'} />
        </div>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Win Rate by Timeframe</div>
          <BarChart data={data.win_by_timeframe} colorFn={(v) => v >= 70 ? 'var(--success)' : v >= 60 ? 'var(--accent-blue)' : 'var(--warning)'} />
        </div>
      </div>

      <div className="section-grid" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Win Rate by Session</div>
          <BarChart data={data.win_by_session} colorFn={(v) => v >= 70 ? 'var(--success)' : v >= 60 ? 'var(--accent-blue)' : 'var(--warning)'} />
        </div>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Win Rate by Day of Week</div>
          <BarChart data={data.win_by_day} colorFn={(v) => v >= 70 ? 'var(--success)' : v >= 60 ? 'var(--accent-blue)' : 'var(--warning)'} />
        </div>
      </div>

      {/* Model Performance Matrix */}
      <div className="card">
        <div className="card-title" style={{ marginBottom: 16 }}>Model Category Performance</div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Model Category</th>
                <th>Accuracy</th>
                <th>P/L</th>
                <th>Trades</th>
                <th>Performance</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.model_performance).map(([name, perf]) => (
                <tr key={name}>
                  <td style={{ fontWeight: 600 }}>{name}</td>
                  <td>
                    <span style={{ 
                      color: perf.accuracy >= 75 ? 'var(--success)' : perf.accuracy >= 65 ? 'var(--accent-blue)' : 'var(--warning)',
                      fontFamily: 'var(--font-mono)', fontWeight: 600,
                    }}>
                      {perf.accuracy}%
                    </span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: perf.pnl > 0 ? 'var(--success)' : 'var(--danger)' }}>
                    +${perf.pnl.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{perf.trades}</td>
                  <td>
                    <div style={{ width: 100, height: 6, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        width: `${perf.accuracy}%`,
                        background: perf.accuracy >= 75 ? 'var(--success)' : perf.accuracy >= 65 ? 'var(--accent-blue)' : 'var(--warning)',
                        borderRadius: 'var(--radius-full)',
                      }} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
