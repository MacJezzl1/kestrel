'use client';

import { useState } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import MobileNav from '@/components/layout/MobileNav';

export default function AnalyticsPage() {
  const [selectedRange, setSelectedRange] = useState('30d');

  // Pair Correlation Matrix Data (-1.0 to +1.0)
  const pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'];
  const correlationMatrix: number[][] = [
    [1.00,  0.84, -0.68,  0.72, -0.76],
    [0.84,  1.00, -0.59,  0.78, -0.69],
    [-0.68, -0.59,  1.00, -0.62,  0.71],
    [0.72,  0.78, -0.62,  1.00, -0.81],
    [-0.76, -0.69,  0.71, -0.81,  1.00],
  ];

  // Session Performance Data
  const sessionStats = [
    { session: 'Asian (Tokyo/Sydney)', trades: 64, winRate: 67.2, pnl: 2840.50, profitFactor: 2.12, status: 'Active' },
    { session: 'London Session', trades: 142, winRate: 78.4, pnl: 7920.20, profitFactor: 2.85, status: 'Optimal' },
    { session: 'New York Session', trades: 118, winRate: 72.8, pnl: 5410.80, profitFactor: 2.38, status: 'Optimal' },
    { session: 'London/NY Overlap', trades: 86, winRate: 81.2, pnl: 6180.40, profitFactor: 3.10, status: 'Peak Alpha' },
  ];

  // Trade Duration Histogram Data
  const durationBuckets = [
    { label: '< 15 mins (Scalp)', count: 82, pct: 20, winRate: 71 },
    { label: '15m - 1h (Intraday)', count: 168, pct: 41, winRate: 76 },
    { label: '1h - 4h (Core Swing)', count: 112, pct: 27, winRate: 74 },
    { label: '4h - 24h (Session)', count: 38, pct: 9, winRate: 68 },
    { label: '> 24h (Multi-Day)', count: 10, pct: 3, winRate: 60 },
  ];

  // Monthly PnL Matrix (Past 8 Months)
  const monthlyPnL = [
    { month: 'Jan 2026', pnl: '+8.4%', val: 8400, winRate: 72 },
    { month: 'Feb 2026', pnl: '+11.2%', val: 11200, winRate: 76 },
    { month: 'Mar 2026', pnl: '+6.9%', val: 6900, winRate: 70 },
    { month: 'Apr 2026', pnl: '+14.1%', val: 14100, winRate: 81 },
    { month: 'May 2026', pnl: '+9.5%', val: 9500, winRate: 74 },
    { month: 'Jun 2026', pnl: '+12.8%', val: 12800, winRate: 78 },
    { month: 'Jul 2026', pnl: '+7.4%', val: 7400, winRate: 71 },
    { month: 'Aug 2026', pnl: '+10.6%', val: 10600, winRate: 75 },
  ];

  const getCorrColor = (val: number) => {
    if (val === 1.0) return 'rgba(255,255,255,0.08)';
    if (val > 0.7) return 'rgba(239, 68, 68, 0.35)'; // High positive correlation warning
    if (val > 0.4) return 'rgba(245, 158, 11, 0.25)';
    if (val < -0.7) return 'rgba(16, 185, 129, 0.35)'; // Inverse hedge
    return 'rgba(255,255,255,0.04)';
  };

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <MobileNav />

        {/* ─── HEADER ─── */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.5rem' }}>📈</span>
              <h1 style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.02em' }}>Deep Portfolio Analytics</h1>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Trade expectancy, session edge breakdown, duration decay, and Pearson pair correlation matrix.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', background: 'var(--bg-card)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border-secondary)' }}>
            {['7d', '30d', '90d', '1y', 'all'].map((r) => (
              <button
                key={r}
                onClick={() => setSelectedRange(r)}
                style={{
                  background: selectedRange === r ? 'var(--accent-blue)' : 'transparent',
                  color: selectedRange === r ? '#fff' : 'var(--text-secondary)',
                  border: 'none',
                  padding: '4px 12px',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textTransform: 'uppercase'
                }}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        {/* ─── EXPECTANCY METRICS ─── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Expectancy ($ / Trade)</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--success)', fontFamily: 'var(--font-mono)' }}>+$164.20</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Positive mathematical edge</div>
          </div>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Average R-Multiple</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>2.34 R</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Avg Win $520 vs Loss $222</div>
          </div>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Recovery Factor</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>7.14</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Net Profit / Max DD</div>
          </div>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Kelly Criterion Fraction</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#a855f7', fontFamily: 'var(--font-mono)' }}>0.38 f*</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Optimal risk fraction capped</div>
          </div>
        </div>

        {/* ─── CORRELATION MATRIX & SESSION PERFORMANCE ─── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '2rem', marginBottom: '2rem' }}>
          {/* Pair Correlation Matrix */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Pearson Pair Correlation Matrix</h2>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>Red = High Risk Correlation (&gt; 0.70) • Green = Natural Hedge</div>
              </div>
              <span style={{ fontSize: '0.75rem', background: 'rgba(0,229,255,0.1)', color: 'var(--accent-cyan)', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
                H1 Rolling 200
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center', fontSize: '0.85rem' }}>
                <thead>
                  <tr>
                    <th style={{ padding: '8px' }}></th>
                    {pairs.map((p) => (
                      <th key={p} style={{ padding: '8px', color: 'var(--text-secondary)', fontWeight: 600 }}>{p}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {pairs.map((rowPair, rIdx) => (
                    <tr key={rowPair}>
                      <td style={{ padding: '8px', fontWeight: 700, color: 'var(--text-secondary)', textAlign: 'left' }}>{rowPair}</td>
                      {correlationMatrix[rIdx].map((val, cIdx) => (
                        <td
                          key={cIdx}
                          style={{
                            padding: '10px',
                            background: getCorrColor(val),
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 700,
                            borderRadius: '4px',
                            border: '1px solid rgba(255,255,255,0.02)'
                          }}
                        >
                          {val >= 0 ? `+${val.toFixed(2)}` : val.toFixed(2)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '1rem' }}>
              * Pairs with correlation &gt; 0.70 automatically trigger the EA Correlation Guard to block simultaneous same-direction exposure.
            </div>
          </div>

          {/* Session Performance Breakdown */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '1.5rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1.25rem' }}>Session Edge Breakdown</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {sessionStats.map((s) => (
                <div key={s.session} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-secondary)', borderRadius: '10px', padding: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{s.session}</span>
                    <span style={{ fontSize: '0.75rem', background: s.status === 'Peak Alpha' ? 'rgba(0,229,255,0.15)' : 'rgba(16,185,129,0.1)', color: s.status === 'Peak Alpha' ? 'var(--accent-cyan)' : 'var(--success)', padding: '2px 8px', borderRadius: '4px', fontWeight: 700 }}>
                      {s.status}
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', fontSize: '0.8rem' }}>
                    <div>
                      <span style={{ color: 'var(--text-tertiary)' }}>Win Rate: </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--success)' }}>{s.winRate}%</span>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-tertiary)' }}>P/F: </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)' }}>{s.profitFactor}</span>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-tertiary)' }}>PnL: </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--success)' }}>+${s.pnl.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ─── DURATION HISTOGRAM & MONTHLY HEATMAP ─── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '2rem' }}>
          {/* Duration Histogram */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '1.5rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1.25rem' }}>Trade Holding Duration Histogram</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {durationBuckets.map((b) => (
                <div key={b.label}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{b.label}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{b.count} trades ({b.winRate}% WR)</span>
                  </div>
                  <div style={{ height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${b.pct * 2.2}%`, height: '100%', background: 'linear-gradient(90deg, var(--accent-cyan) 0%, var(--accent-blue) 100%)', borderRadius: '4px' }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Monthly PnL Performance Grid */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '1.5rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1.25rem' }}>Monthly Performance Matrix (2026)</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
              {monthlyPnL.map((m) => (
                <div key={m.month} style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: '8px', padding: '12px 10px', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginBottom: '4px' }}>{m.month}</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--success)', fontFamily: 'var(--font-mono)' }}>{m.pnl}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '2px' }}>{m.winRate}% Win</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
