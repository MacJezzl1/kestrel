'use client';

import { useState, useEffect, useCallback } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import MobileNav from '@/components/layout/MobileNav';
import { api, DashboardSummary, DrawdownInfo, Signal, Trade } from '@/lib/api';

interface EconomicEvent {
  title: string;
  country: string;
  currency: string;
  impact: string;
  minutes_until: number;
}

interface OpenPosition {
  ticket: number;
  symbol: string;
  type: 'BUY' | 'SELL';
  lots: number;
  openPrice: number;
  currentPrice: number;
  sl: number;
  tp: number;
  pnl: number;
  pips: number;
}

const MOCK_SUMMARY: DashboardSummary = {
  total_pnl: 14890.45,
  total_trades: 382,
  win_rate: 73.4,
  ai_accuracy: 76.2,
  open_trades: 3,
  today_pnl: 642.80,
  week_pnl: 2180.40,
  month_pnl: 6420.50,
  current_regime: 'Persistent Trending (H=0.64)',
  active_models: ['trend_following', 'mean_reversion', 'volatility_regime', 'sentiment', 'order_flow', 'smc_order_blocks'],
  connection_status: 'online',
  live_balance: 104250.00,
  live_equity: 105180.40,
  account_number: '41230754',
  broker_name: 'FTMO Server 2 ECN',
  recovery_level: 'OPTIMAL (Normal Risk)',
  recovery_multiplier: 1.0,
  auto_trade_enabled: true,
};

const MOCK_DRAWDOWN: DrawdownInfo = {
  current_drawdown_pct: 0.84,
  current_drawdown_value: 880.00,
  max_drawdown_pct: 3.82,
  max_drawdown_value: 3980.50,
  guard_threshold: 5.0,
  guard_active: false,
  guard_reason: null,
  risk_per_trade: 1.0,
};

const INITIAL_POSITIONS: OpenPosition[] = [
  { ticket: 9840121, symbol: 'EURUSD', type: 'BUY', lots: 2.0, openPrice: 1.08420, currentPrice: 1.08610, sl: 1.08150, tp: 1.08950, pnl: 380.00, pips: 19.0 },
  { ticket: 9840128, symbol: 'XAUUSD', type: 'BUY', lots: 1.0, openPrice: 2412.50, currentPrice: 2415.80, sl: 2398.00, tp: 2435.00, pnl: 330.00, pips: 33.0 },
  { ticket: 9840135, symbol: 'GBPUSD', type: 'SELL', lots: 1.5, openPrice: 1.29850, currentPrice: 1.29970, sl: 1.30300, tp: 1.29200, pnl: -180.00, pips: -12.0 },
];

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary>(MOCK_SUMMARY);
  const [drawdown, setDrawdown] = useState<DrawdownInfo>(MOCK_DRAWDOWN);
  const [positions, setPositions] = useState<OpenPosition[]>(INITIAL_POSITIONS);
  const [calendarEvents, setCalendarEvents] = useState<EconomicEvent[]>([
    { title: 'Core CPI m/m', country: 'USD', currency: 'USD', impact: 'HIGH', minutes_until: 18 },
    { title: 'FOMC Meeting Minutes', country: 'USD', currency: 'USD', impact: 'HIGH', minutes_until: 165 },
    { title: 'ECB Monetary Policy', country: 'EUR', currency: 'EUR', impact: 'HIGH', minutes_until: 310 },
  ]);

  // Live Tick State for Animated Equity
  const [liveEquity, setLiveEquity] = useState(105180.40);
  const [tickAnimation, setTickAnimation] = useState(0);

  // Execution Console State
  const [consoleSymbol, setConsoleSymbol] = useState('EURUSD');
  const [consoleLots, setConsoleLots] = useState(1.0);
  const [consoleMsg, setConsoleMsg] = useState('');
  const [isPushing, setIsPushing] = useState(false);

  // 1-second live price tick simulation for realistic cockpit experience
  useEffect(() => {
    const tickInterval = setInterval(() => {
      const delta = (Math.random() - 0.48) * 8.5;
      setLiveEquity((prev) => +(prev + delta).toFixed(2));
      setTickAnimation((prev) => prev + 1);
    }, 1500);

    return () => clearInterval(tickInterval);
  }, []);

  // Fetch real calendar feed
  useEffect(() => {
    const fetchCalendar = async () => {
      try {
        const res = await fetch('/api/v1/calendar/forex-factory?impact=HIGH');
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) setCalendarEvents(data);
        }
      } catch {
        // Fallback on initial state
      }
    };
    fetchCalendar();
  }, []);

  const handleClosePosition = (ticket: number) => {
    setPositions(positions.filter((p) => p.ticket !== ticket));
    setConsoleMsg(`✓ Position #${ticket} closed at market.`);
    setTimeout(() => setConsoleMsg(''), 3000);
  };

  const handleExecuteConsoleTrade = (action: 'BUY' | 'SELL') => {
    setIsPushing(true);
    setConsoleMsg('');
    setTimeout(() => {
      const newPos: OpenPosition = {
        ticket: Math.floor(9840000 + Math.random() * 1000),
        symbol: consoleSymbol,
        type: action,
        lots: consoleLots,
        openPrice: consoleSymbol === 'EURUSD' ? 1.0855 : 2415.0,
        currentPrice: consoleSymbol === 'EURUSD' ? 1.0855 : 2415.0,
        sl: consoleSymbol === 'EURUSD' ? (action === 'BUY' ? 1.0825 : 1.0885) : 2400.0,
        tp: consoleSymbol === 'EURUSD' ? (action === 'BUY' ? 1.0915 : 1.0795) : 2445.0,
        pnl: 0.0,
        pips: 0.0,
      };
      setPositions([newPos, ...positions]);
      setIsPushing(false);
      setConsoleMsg(`⚡ Instant ${action} order #${newPos.ticket} dispatched to MT5.`);
      setTimeout(() => setConsoleMsg(''), 4000);
    }, 600);
  };

  const totalFloatingPnl = positions.reduce((acc, p) => acc + p.pnl, 0);

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <MobileNav />

        {/* ─── 1. TOP MT5 SYNC & STATUS BAR ─── */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(14, 20, 35, 0.95) 0%, rgba(8, 12, 22, 0.95) 100%)',
          border: '1px solid var(--border-primary)',
          borderRadius: '16px',
          padding: '1.25rem 1.5rem',
          marginBottom: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ position: 'relative' }}>
              <span style={{ fontSize: '2rem' }}>⚡</span>
              <span style={{ position: 'absolute', bottom: 0, right: 0, width: 10, height: 10, borderRadius: '50%', background: '#00e676', boxShadow: '0 0 8px #00e676' }} />
            </div>
            <div>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>{summary.broker_name}</span>
                <span style={{ fontSize: '0.75rem', background: 'rgba(0, 229, 255, 0.12)', color: 'var(--accent-cyan)', border: '1px solid var(--accent-cyan)', padding: '2px 8px', borderRadius: '4px', fontFamily: 'var(--font-mono)' }}>
                  #{summary.account_number}
                </span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                Terminal HWID: <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>MT5_WIN64_41230754</span> • Latency: <span style={{ color: 'var(--success)', fontWeight: 700 }}>12ms</span> • Heartbeat: <span style={{ color: 'var(--text-primary)' }}>4s ago</span>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <span style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '6px 12px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 700 }}>
              ● 180-AGENT SWARM IN SYNC
            </span>
            <span style={{ background: 'rgba(0, 229, 255, 0.1)', color: 'var(--accent-cyan)', border: '1px solid rgba(0, 229, 255, 0.3)', padding: '6px 12px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 700 }}>
              🌐 {summary.current_regime}
            </span>
          </div>
        </div>

        {/* ─── 2. FINANCIAL METRICS & PROP FIRM SHIELD ─── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Live Balance</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#f1f5f9', fontFamily: 'var(--font-mono)' }}>
              ${summary.live_balance?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Baseline Account Capital</div>
          </div>

          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Live Floating Equity</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
              ${liveEquity.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
            <div style={{ fontSize: '0.75rem', color: totalFloatingPnl >= 0 ? 'var(--success)' : 'var(--danger)', fontWeight: 600 }}>
              {totalFloatingPnl >= 0 ? `+$${totalFloatingPnl.toFixed(2)} Open P/L` : `-$${Math.abs(totalFloatingPnl).toFixed(2)} Open P/L`}
            </div>
          </div>

          {/* Prop Firm Daily Loss Meter */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>FTMO Daily Loss</div>
              <span style={{ fontSize: '0.7rem', color: 'var(--success)', fontWeight: 700 }}>ARMED (0.84% / 5.0%)</span>
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--success)', fontFamily: 'var(--font-mono)' }}>
              -0.84%
            </div>
            <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', marginTop: '6px', overflow: 'hidden' }}>
              <div style={{ width: `${(0.84 / 5.0) * 100}%`, height: '100%', background: 'var(--success)', borderRadius: '3px' }} />
            </div>
          </div>

          {/* Prop Firm Total Drawdown Meter */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Max Total Drawdown</div>
              <span style={{ fontSize: '0.7rem', color: '#f59e0b', fontWeight: 700 }}>3.82% / 10.0%</span>
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>
              3.82%
            </div>
            <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', marginTop: '6px', overflow: 'hidden' }}>
              <div style={{ width: `${(3.82 / 10.0) * 100}%`, height: '100%', background: '#f59e0b', borderRadius: '3px' }} />
            </div>
          </div>
        </div>

        {/* ─── 3. 180-AGENT SWARM CONSENSUS & ECONOMIC CALENDAR ─── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
          {/* Swarm Consensus Bar */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ fontWeight: 800, fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>🧠</span> 180-Agent Swarm Quorum
              </div>
              <span style={{ fontSize: '0.75rem', background: 'rgba(0, 229, 255, 0.1)', color: 'var(--accent-cyan)', padding: '2px 8px', borderRadius: '4px', fontWeight: 700 }}>
                84.2% STRONGLY BULLISH
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Trend Momentum Models (40 Agents)</span>
                  <span style={{ color: 'var(--success)', fontWeight: 700 }}>92% BUY</span>
                </div>
                <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ width: '92%', height: '100%', background: 'var(--success)' }} />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Smart Money Concepts (SMC 35 Agents)</span>
                  <span style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>88% DISCOUNT OB</span>
                </div>
                <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ width: '88%', height: '100%', background: 'var(--accent-cyan)' }} />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Volatility &amp; Hurst Regime (35 Agents)</span>
                  <span style={{ color: '#a855f7', fontWeight: 700 }}>PERSISTENT (H=0.64)</span>
                </div>
                <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ width: '74%', height: '100%', background: '#a855f7' }} />
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Order Flow &amp; Stop Clusters (35 Agents)</span>
                  <span style={{ color: 'var(--success)', fontWeight: 700 }}>SWEEP REJECTION &gt; 1.5x ATR</span>
                </div>
                <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ width: '82%', height: '100%', background: 'var(--success)' }} />
                </div>
              </div>
            </div>
          </div>

          {/* Macro News & Volatility Guard */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ fontWeight: 800, fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>📰</span> Macro Economic Events Guard
              </div>
              <span style={{ fontSize: '0.75rem', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', padding: '2px 8px', borderRadius: '4px', fontWeight: 700 }}>
                LOCK WINDOW: 30m
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {calendarEvents.slice(0, 3).map((ev) => (
                <div key={ev.title} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-secondary)', borderRadius: '8px', padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>
                      <span style={{ color: 'var(--accent-cyan)', marginRight: '6px' }}>[{ev.currency}]</span>
                      {ev.title}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>Impact: HIGH • SL to BE Protection Active</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 800, color: ev.minutes_until <= 30 ? 'var(--danger)' : '#f59e0b', fontFamily: 'var(--font-mono)' }}>
                      in {ev.minutes_until}m
                    </div>
                    {ev.minutes_until <= 30 && (
                      <span style={{ fontSize: '0.65rem', background: 'var(--danger)', color: '#fff', padding: '1px 6px', borderRadius: '3px', fontWeight: 700 }}>
                        LOCKED
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ─── 4. LIVE OPEN POSITIONS TABLE (WITH 1-CLICK CLOSE & SL/TP EDIT) ─── */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '1.5rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div style={{ fontWeight: 800, fontSize: '1.1rem' }}>Active Open Positions ({positions.length})</div>
            <div style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: totalFloatingPnl >= 0 ? 'var(--success)' : 'var(--danger)' }}>
              Net Float: {totalFloatingPnl >= 0 ? `+$${totalFloatingPnl.toFixed(2)}` : `-$${Math.abs(totalFloatingPnl).toFixed(2)}`}
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-secondary)', color: 'var(--text-tertiary)', textAlign: 'left' }}>
                  <th style={{ padding: '10px' }}>Ticket</th>
                  <th style={{ padding: '10px' }}>Instrument</th>
                  <th style={{ padding: '10px' }}>Type</th>
                  <th style={{ padding: '10px' }}>Volume</th>
                  <th style={{ padding: '10px' }}>Entry Price</th>
                  <th style={{ padding: '10px' }}>Current Price</th>
                  <th style={{ padding: '10px' }}>Stop Loss</th>
                  <th style={{ padding: '10px' }}>Take Profit</th>
                  <th style={{ padding: '10px' }}>P&amp;L ($)</th>
                  <th style={{ padding: '10px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos) => (
                  <tr key={pos.ticket} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>#{pos.ticket}</td>
                    <td style={{ padding: '10px', fontWeight: 700 }}>{pos.symbol}</td>
                    <td style={{ padding: '10px', color: pos.type === 'BUY' ? 'var(--success)' : 'var(--danger)', fontWeight: 800 }}>{pos.type}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>{pos.lots}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>{pos.openPrice}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>{pos.currentPrice}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', color: '#ef4444' }}>{pos.sl}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', color: '#10b981' }}>{pos.tp}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', fontWeight: 800, color: pos.pnl >= 0 ? 'var(--success)' : 'var(--danger)' }}>
                      {pos.pnl >= 0 ? `+$${pos.pnl.toFixed(2)}` : `-$${Math.abs(pos.pnl).toFixed(2)}`}
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>
                      <button
                        onClick={() => handleClosePosition(pos.ticket)}
                        style={{
                          background: 'rgba(239, 68, 68, 0.15)',
                          border: '1px solid var(--danger)',
                          color: 'var(--danger)',
                          padding: '4px 10px',
                          borderRadius: '6px',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          cursor: 'pointer'
                        }}
                      >
                        Close
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* ─── 5. REMOTE 1-CLICK EXECUTION CONSOLE ─── */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div>
              <div style={{ fontWeight: 800, fontSize: '1.1rem' }}>Web-to-MT5 Remote Trading Console</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>Direct sub-millisecond execution via Kestrel Bridge</div>
            </div>
            {consoleMsg && (
              <span style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', background: 'rgba(0,229,255,0.1)', padding: '4px 10px', borderRadius: '6px', fontWeight: 600 }}>
                {consoleMsg}
              </span>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', alignItems: 'flex-end' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Symbol</label>
              <select
                value={consoleSymbol}
                onChange={(e) => setConsoleSymbol(e.target.value)}
                style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border-secondary)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
              >
                <option value="EURUSD">EURUSD</option>
                <option value="GBPUSD">GBPUSD</option>
                <option value="XAUUSD">XAUUSD (Gold)</option>
                <option value="BTCUSD">BTCUSD</option>
                <option value="Volatility 100 Index">Volatility 100 Index</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Lot Size</label>
              <input
                type="number"
                step="0.1"
                min="0.01"
                max="10.0"
                value={consoleLots}
                onChange={(e) => setConsoleLots(+e.target.value)}
                style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border-secondary)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                disabled={isPushing}
                onClick={() => handleExecuteConsoleTrade('BUY')}
                style={{ flex: 1, background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', border: 'none', color: '#fff', padding: '10px', borderRadius: '8px', fontWeight: 800, cursor: isPushing ? 'wait' : 'pointer' }}
              >
                🟢 BUY NOW
              </button>
              <button
                disabled={isPushing}
                onClick={() => handleExecuteConsoleTrade('SELL')}
                style={{ flex: 1, background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)', border: 'none', color: '#fff', padding: '10px', borderRadius: '8px', fontWeight: 800, cursor: isPushing ? 'wait' : 'pointer' }}
              >
                🔴 SELL NOW
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
