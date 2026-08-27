'use client';

import { useState } from 'react';
import { api, Signal } from '@/lib/api';

const INSTRUMENTS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'XAUUSD', 'NAS100', 'US30', 'BTCUSD'];
const TIMEFRAMES = ['M5', 'M15', 'M30', 'H1', 'H4', 'D1'];

function formatModelName(name: string): string {
  return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

export default function SignalsPage() {
  const [instrument, setInstrument] = useState('EURUSD');
  const [timeframe, setTimeframe] = useState('H1');
  const [signal, setSignal] = useState<Signal | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const generateSignal = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await api.generateSignal(instrument, timeframe);
      setSignal(result);
    } catch {
      setError('Failed to generate signal. Is the Kestrel API running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>📡 Signal Generator</h1>

      {/* Controls */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div className="input-group">
            <label className="input-label">Instrument</label>
            <select className="input" value={instrument} onChange={(e) => setInstrument(e.target.value)}>
              {INSTRUMENTS.map(i => <option key={i} value={i}>{i}</option>)}
            </select>
          </div>
          <div className="input-group">
            <label className="input-label">Timeframe</label>
            <select className="input" value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
              {TIMEFRAMES.map(tf => <option key={tf} value={tf}>{tf}</option>)}
            </select>
          </div>
          <button className="btn btn-primary" onClick={generateSignal} disabled={loading}>
            {loading ? '⏳ Analyzing...' : '🦅 Generate Signal'}
          </button>
        </div>
        {error && (
          <div style={{ marginTop: 12, padding: '10px 14px', background: 'var(--danger-soft)', borderRadius: 'var(--radius-md)', color: 'var(--danger)', fontSize: 13 }}>
            {error}
          </div>
        )}
      </div>

      {/* Signal Result */}
      {signal && (
        <div className="animate-scale-in">
          <div className="metrics-grid">
            <div className="card">
              <div className="card-title" style={{ marginBottom: 12 }}>Direction</div>
              <div className={`card-value badge-${signal.direction}`} style={{ 
                fontSize: 32, 
                color: signal.direction === 'buy' ? 'var(--success)' : signal.direction === 'sell' ? 'var(--danger)' : 'var(--text-secondary)' 
              }}>
                {signal.direction.toUpperCase()}
              </div>
            </div>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 12 }}>Confidence</div>
              <div className="card-value" style={{ color: 'var(--accent-cyan)' }}>
                {(signal.confidence * 100).toFixed(1)}%
              </div>
              <div className="confidence-bar" style={{ marginTop: 8, maxWidth: '100%' }}>
                <div className={`confidence-fill ${signal.confidence >= 0.75 ? 'high' : signal.confidence >= 0.5 ? 'medium' : 'low'}`} style={{ width: `${signal.confidence * 100}%` }} />
              </div>
            </div>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 12 }}>Regime</div>
              <div style={{ marginTop: 8 }}>
                <span className={`badge ${signal.regime === 'trending' ? 'badge-trending' : signal.regime === 'ranging' ? 'badge-ranging' : 'badge-volatile'}`} style={{ fontSize: 16, padding: '6px 16px' }}>
                  {signal.regime.toUpperCase()}
                </span>
              </div>
            </div>
          </div>

          {/* Model Category Votes */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-title" style={{ marginBottom: 16 }}>Model Category Votes</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
              {Object.entries(signal.model_votes).map(([cat, dir]) => (
                <div key={cat} style={{
                  padding: '12px 16px',
                  background: 'var(--bg-secondary)',
                  borderRadius: 'var(--radius-md)',
                  border: `1px solid ${dir === signal.direction ? 'rgba(16, 185, 129, 0.2)' : 'var(--border-secondary)'}`,
                }}>
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 4 }}>{formatModelName(cat)}</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{
                      fontWeight: 700,
                      color: dir === 'buy' ? 'var(--success)' : dir === 'sell' ? 'var(--danger)' : 'var(--text-secondary)',
                    }}>
                      {String(dir).toUpperCase()}
                    </span>
                    <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                      {((signal.model_confidences[cat] || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Price Levels */}
          {signal.entry_price && (
            <div className="card">
              <div className="card-title" style={{ marginBottom: 16 }}>Price Levels</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                <div>
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Entry</div>
                  <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                    {signal.entry_price.toFixed(signal.entry_price > 100 ? 2 : 5)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 12, color: 'var(--danger)' }}>Stop Loss</div>
                  <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--danger)' }}>
                    {signal.stop_loss?.toFixed(signal.stop_loss > 100 ? 2 : 5) || '—'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 12, color: 'var(--success)' }}>Take Profit</div>
                  <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--success)' }}>
                    {signal.take_profit?.toFixed(signal.take_profit > 100 ? 2 : 5) || '—'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
