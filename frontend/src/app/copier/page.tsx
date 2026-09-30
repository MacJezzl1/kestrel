'use client';

import { useState } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import MobileNav from '@/components/layout/MobileNav';

interface ReceiverAccount {
  id: string;
  accountLogin: string;
  broker: string;
  accountType: 'FTMO' | 'The5ers' | 'MFF' | 'Personal' | 'Live';
  multiplier: number;
  equity: number;
  balance: number;
  status: 'ONLINE' | 'SYNCED' | 'DISCONNECTED';
  latencyMs: number;
  slippagePips: number;
  lastCopiedTime: string;
}

interface CopyLogItem {
  id: string;
  timestamp: string;
  masterDeal: string;
  symbol: string;
  type: 'BUY' | 'SELL';
  masterLot: number;
  receiverId: string;
  receiverLot: number;
  slippage: number;
  status: 'SUCCESS' | 'REJECTED' | 'TIMEOUT';
}

const INITIAL_RECEIVERS: ReceiverAccount[] = [
  { id: '1', accountLogin: '41230754', broker: 'FTMO Global Markets', accountType: 'FTMO', multiplier: 1.0, equity: 104520.40, balance: 100000.00, status: 'ONLINE', latencyMs: 14, slippagePips: 0.2, lastCopiedTime: '12s ago' },
  { id: '2', accountLogin: '88291032', broker: 'The 5%ers Capital', accountType: 'The5ers', multiplier: 0.8, equity: 51240.10, balance: 50000.00, status: 'SYNCED', latencyMs: 19, slippagePips: 0.3, lastCopiedTime: '12s ago' },
  { id: '3', accountLogin: '99201923', broker: 'FundedNext Prop Ltd', accountType: 'MFF', multiplier: 1.2, equity: 208390.80, balance: 200000.00, status: 'ONLINE', latencyMs: 11, slippagePips: 0.1, lastCopiedTime: '12s ago' },
  { id: '4', accountLogin: '20491022', broker: 'IC Markets Raw ECN', accountType: 'Personal', multiplier: 0.5, equity: 24890.30, balance: 25000.00, status: 'SYNCED', latencyMs: 28, slippagePips: 0.4, lastCopiedTime: '45m ago' },
];

const INITIAL_COPY_LOGS: CopyLogItem[] = [
  { id: 'log-1', timestamp: '14:22:04', masterDeal: '#9840129', symbol: 'EURUSD', type: 'BUY', masterLot: 2.0, receiverId: '41230754', receiverLot: 2.0, slippage: 0.1, status: 'SUCCESS' },
  { id: 'log-2', timestamp: '14:22:04', masterDeal: '#9840129', symbol: 'EURUSD', type: 'BUY', masterLot: 2.0, receiverId: '88291032', receiverLot: 1.6, slippage: 0.2, status: 'SUCCESS' },
  { id: 'log-3', timestamp: '14:22:04', masterDeal: '#9840129', symbol: 'EURUSD', type: 'BUY', masterLot: 2.0, receiverId: '99201923', receiverLot: 2.4, slippage: 0.1, status: 'SUCCESS' },
  { id: 'log-4', timestamp: '13:05:12', masterDeal: '#9839912', symbol: 'XAUUSD', type: 'SELL', masterLot: 1.0, receiverId: '41230754', receiverLot: 1.0, slippage: 0.3, status: 'SUCCESS' },
  { id: 'log-5', timestamp: '13:05:12', masterDeal: '#9839912', symbol: 'XAUUSD', type: 'SELL', masterLot: 1.0, receiverId: '20491022', receiverLot: 0.5, slippage: 0.5, status: 'SUCCESS' },
];

export default function CopierPage() {
  const [receivers, setReceivers] = useState<ReceiverAccount[]>(INITIAL_RECEIVERS);
  const [copyLogs, setCopyLogs] = useState<CopyLogItem[]>(INITIAL_COPY_LOGS);
  const [masterCopierActive, setMasterCopierActive] = useState(true);

  // New Receiver Form State
  const [isAdding, setIsAdding] = useState(false);
  const [newLogin, setNewLogin] = useState('');
  const [newBroker, setNewBroker] = useState('');
  const [newType, setNewType] = useState<'FTMO' | 'The5ers' | 'MFF' | 'Personal' | 'Live'>('FTMO');
  const [newMultiplier, setNewMultiplier] = useState(1.0);

  const handleAddReceiver = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLogin || !newBroker) return;
    const newRec: ReceiverAccount = {
      id: Date.now().toString(),
      accountLogin: newLogin,
      broker: newBroker,
      accountType: newType,
      multiplier: newMultiplier,
      equity: 100000.0,
      balance: 100000.0,
      status: 'ONLINE',
      latencyMs: 16,
      slippagePips: 0.2,
      lastCopiedTime: 'Just now',
    };
    setReceivers([...receivers, newRec]);
    setIsAdding(false);
    setNewLogin('');
    setNewBroker('');
  };

  const handleRemoveReceiver = (id: string) => {
    setReceivers(receivers.filter(r => r.id !== id));
  };

  const handleUpdateMultiplier = (id: string, delta: number) => {
    setReceivers(receivers.map(r => {
      if (r.id === id) {
        const nextMult = Math.max(0.2, Math.min(3.0, +(r.multiplier + delta).toFixed(1)));
        return { ...r, multiplier: nextMult };
      }
      return r;
    }));
  };

  const handleEmergencyHalt = () => {
    setMasterCopierActive(false);
    setReceivers(receivers.map(r => ({ ...r, status: 'DISCONNECTED' })));
    alert('🚨 EMERGENCY HALT TRIGGERED: Master broadcast paused. All receiver positions frozen.');
  };

  const totalAllocatedCapital = receivers.reduce((acc, r) => acc + r.equity, 0);
  const avgLatency = Math.round(receivers.reduce((acc, r) => acc + r.latencyMs, 0) / (receivers.length || 1));

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <MobileNav />

        {/* ─── HEADER ─── */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.5rem' }}>🔄</span>
              <h1 style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.02em' }}>PAMM &amp; Copy-Trading Hub</h1>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Sub-second trade mirror across multiple prop challenges and private institutional broker accounts.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={() => setIsAdding(true)}
              style={{
                background: 'linear-gradient(135deg, #00e5ff 0%, #0070f3 100%)',
                border: 'none',
                color: '#05070a',
                padding: '8px 18px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              + Add Receiver Account
            </button>
            <button
              onClick={handleEmergencyHalt}
              style={{
                background: masterCopierActive ? 'rgba(239, 68, 68, 0.15)' : 'rgba(239, 68, 68, 0.4)',
                border: '1px solid var(--danger)',
                color: 'var(--danger)',
                padding: '8px 16px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              {masterCopierActive ? '🛑 Emergency Halt All' : '⚠️ Copier Frozen'}
            </button>
          </div>
        </div>

        {/* ─── STATS RIBBON ─── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Connected Receivers</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{receivers.length}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--success)' }}>All in sync</div>
          </div>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Total Mirrored Equity</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f1f5f9', fontFamily: 'var(--font-mono)' }}>${totalAllocatedCapital.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Aggregated portfolio pool</div>
          </div>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Avg Copy Latency</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--success)', fontFamily: 'var(--font-mono)' }}>{avgLatency} ms</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Low latency webhook pipeline</div>
          </div>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Avg Slippage</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>0.2 pips</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Sub-tick execution quality</div>
          </div>
        </div>

        {/* ─── ADD RECEIVER MODAL ─── */}
        {isAdding && (
          <div style={{ background: 'rgba(0, 229, 255, 0.05)', border: '1px solid var(--accent-cyan)', borderRadius: '16px', padding: '1.5rem', marginBottom: '2rem' }}>
            <div style={{ fontWeight: 700, marginBottom: '1rem', color: 'var(--accent-cyan)' }}>Add New Client Account</div>
            <form onSubmit={handleAddReceiver} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', alignItems: 'flex-end' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>MT5 Account Login #</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 50192831"
                  value={newLogin}
                  onChange={(e) => setNewLogin(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-input)', border: '1px solid var(--border-secondary)', borderRadius: '6px', color: '#fff' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Broker Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. FTMO Server 2"
                  value={newBroker}
                  onChange={(e) => setNewBroker(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-input)', border: '1px solid var(--border-secondary)', borderRadius: '6px', color: '#fff' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Account Profile</label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value as any)}
                  style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-input)', border: '1px solid var(--border-secondary)', borderRadius: '6px', color: '#fff' }}
                >
                  <option value="FTMO">FTMO Challenge</option>
                  <option value="The5ers">The 5%ers</option>
                  <option value="MFF">FundedNext / MFF</option>
                  <option value="Personal">Personal Raw ECN</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Risk Multiplier ({newMultiplier}x)</label>
                <input
                  type="range"
                  min="0.2"
                  max="2.0"
                  step="0.1"
                  value={newMultiplier}
                  onChange={(e) => setNewMultiplier(+e.target.value)}
                  style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
                />
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button type="submit" style={{ flex: 1, background: 'var(--accent-blue)', color: '#fff', border: 'none', padding: '9px', borderRadius: '6px', fontWeight: 700, cursor: 'pointer' }}>
                  Save Receiver
                </button>
                <button type="button" onClick={() => setIsAdding(false)} style={{ background: 'transparent', border: '1px solid var(--border-secondary)', color: 'var(--text-secondary)', padding: '9px 14px', borderRadius: '6px', cursor: 'pointer' }}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* ─── RECEIVER ACCOUNTS GRID ─── */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '1.5rem', marginBottom: '2rem' }}>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Configured Receiver Accounts</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', fontWeight: 400 }}>Master Account: CapeChain Prime #41230754</span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-secondary)', color: 'var(--text-tertiary)', textAlign: 'left' }}>
                  <th style={{ padding: '12px' }}>Account Login</th>
                  <th style={{ padding: '12px' }}>Broker Server</th>
                  <th style={{ padding: '12px' }}>Profile</th>
                  <th style={{ padding: '12px' }}>Live Equity</th>
                  <th style={{ padding: '12px' }}>Multiplier</th>
                  <th style={{ padding: '12px' }}>Latency</th>
                  <th style={{ padding: '12px' }}>Slippage</th>
                  <th style={{ padding: '12px' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {receivers.map((r) => (
                  <tr key={r.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                      #{r.accountLogin}
                    </td>
                    <td style={{ padding: '12px' }}>{r.broker}</td>
                    <td style={{ padding: '12px' }}>
                      <span style={{ background: 'rgba(255,255,255,0.06)', padding: '3px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>
                        {r.accountType}
                      </span>
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)' }}>
                      ${r.equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <button onClick={() => handleUpdateMultiplier(r.id, -0.1)} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-secondary)', color: '#fff', borderRadius: '4px', width: 22, height: 22, cursor: 'pointer' }}>-</button>
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{r.multiplier}x</span>
                        <button onClick={() => handleUpdateMultiplier(r.id, 0.1)} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-secondary)', color: '#fff', borderRadius: '4px', width: 22, height: 22, cursor: 'pointer' }}>+</button>
                      </div>
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', color: r.latencyMs < 20 ? 'var(--success)' : '#f59e0b' }}>
                      {r.latencyMs} ms
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)' }}>
                      {r.slippagePips} pips
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: r.status === 'ONLINE' ? 'var(--success)' : '#94a3b8', fontSize: '0.8rem', fontWeight: 600 }}>
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: r.status === 'ONLINE' ? '#00e676' : '#94a3b8' }} />
                        {r.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>
                      <button
                        onClick={() => handleRemoveReceiver(r.id)}
                        style={{ background: 'transparent', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: '1rem' }}
                        title="Remove Receiver"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* ─── LIVE COPY EXECUTION LOG ─── */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '1.5rem' }}>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Sub-Second Broadcast Log</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>WebSockets Stream: LIVE</span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-secondary)', color: 'var(--text-tertiary)', textAlign: 'left' }}>
                  <th style={{ padding: '10px' }}>Time</th>
                  <th style={{ padding: '10px' }}>Master Deal</th>
                  <th style={{ padding: '10px' }}>Pair</th>
                  <th style={{ padding: '10px' }}>Action</th>
                  <th style={{ padding: '10px' }}>Master Lot</th>
                  <th style={{ padding: '10px' }}>Target Account</th>
                  <th style={{ padding: '10px' }}>Receiver Lot</th>
                  <th style={{ padding: '10px' }}>Slippage</th>
                  <th style={{ padding: '10px' }}>Execution</th>
                </tr>
              </thead>
              <tbody>
                {copyLogs.map((l) => (
                  <tr key={l.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{l.timestamp}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>{l.masterDeal}</td>
                    <td style={{ padding: '10px', fontWeight: 600 }}>{l.symbol}</td>
                    <td style={{ padding: '10px', color: l.type === 'BUY' ? 'var(--success)' : 'var(--danger)', fontWeight: 700 }}>{l.type}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>{l.masterLot}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>#{l.receiverId}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>{l.receiverLot}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>{l.slippage} pips</td>
                    <td style={{ padding: '10px' }}>
                      <span style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700 }}>
                        {l.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
