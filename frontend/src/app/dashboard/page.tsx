'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, DashboardSummary, DrawdownInfo, Signal, Trade } from '@/lib/api';

// Mock data for demo when backend isn't running
const MOCK_SUMMARY: DashboardSummary = {
  total_pnl: 12847.52,
  total_trades: 347,
  win_rate: 68.3,
  ai_accuracy: 72.1,
  open_trades: 3,
  today_pnl: 342.18,
  week_pnl: 1283.45,
  month_pnl: 4521.67,
  current_regime: 'trending',
  active_models: ['trend_following', 'mean_reversion', 'volatility_regime', 'sentiment', 'order_flow'],
  connection_status: 'online',
};

const MOCK_DRAWDOWN: DrawdownInfo = {
  current_drawdown_pct: 3.2,
  current_drawdown_value: 412.30,
  max_drawdown_pct: 7.8,
  max_drawdown_value: 890.45,
  guard_threshold: 10.0,
  guard_active: false,
  guard_reason: null,
  risk_per_trade: 1.0,
};

const MOCK_SIGNALS: Signal[] = [
  { id: '1', instrument: 'EURUSD', timeframe: 'H1', direction: 'buy', confidence: 0.847, regime: 'trending', model_votes: { trend_following: 'buy', mean_reversion: 'hold', volatility_regime: 'trending', sentiment: 'buy', order_flow: 'buy' }, model_confidences: { trend_following: 0.89, mean_reversion: 0.52, volatility_regime: 0.91, sentiment: 0.78, order_flow: 0.81 }, entry_price: 1.08542, stop_loss: 1.08210, take_profit: 1.09150, created_at: new Date().toISOString() },
  { id: '2', instrument: 'GBPUSD', timeframe: 'H4', direction: 'sell', confidence: 0.723, regime: 'ranging', model_votes: { trend_following: 'sell', mean_reversion: 'sell', volatility_regime: 'ranging', sentiment: 'hold', order_flow: 'sell' }, model_confidences: { trend_following: 0.71, mean_reversion: 0.82, volatility_regime: 0.68, sentiment: 0.45, order_flow: 0.74 }, entry_price: 1.26840, stop_loss: 1.27200, take_profit: 1.26100, created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: '3', instrument: 'XAUUSD', timeframe: 'H1', direction: 'buy', confidence: 0.912, regime: 'volatile', model_votes: { trend_following: 'buy', mean_reversion: 'buy', volatility_regime: 'volatile', sentiment: 'buy', order_flow: 'buy' }, model_confidences: { trend_following: 0.93, mean_reversion: 0.78, volatility_regime: 0.95, sentiment: 0.91, order_flow: 0.88 }, entry_price: 1952.30, stop_loss: 1945.00, take_profit: 1968.50, created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: '4', instrument: 'USDJPY', timeframe: 'M15', direction: 'hold', confidence: 0.421, regime: 'ranging', model_votes: { trend_following: 'buy', mean_reversion: 'sell', volatility_regime: 'ranging', sentiment: 'hold', order_flow: 'hold' }, model_confidences: { trend_following: 0.55, mean_reversion: 0.48, volatility_regime: 0.62, sentiment: 0.35, order_flow: 0.42 }, entry_price: null, stop_loss: null, take_profit: null, created_at: new Date(Date.now() - 10800000).toISOString() },
];

const MOCK_TRADES: Trade[] = [
  { id: '1', instrument: 'EURUSD', direction: 'buy', entry_price: 1.08320, exit_price: 1.08690, lot_size: 0.10, pnl: 37.00, pnl_pips: 37.0, status: 'closed', confidence_at_entry: 0.82, model_votes_at_entry: { trend_following: 'buy', mean_reversion: 'hold', sentiment: 'buy' }, opened_at: new Date(Date.now() - 86400000).toISOString(), closed_at: new Date(Date.now() - 43200000).toISOString() },
  { id: '2', instrument: 'XAUUSD', direction: 'buy', entry_price: 1948.50, exit_price: 1962.30, lot_size: 0.05, pnl: 69.00, pnl_pips: 138.0, status: 'closed', confidence_at_entry: 0.91, model_votes_at_entry: { trend_following: 'buy', mean_reversion: 'buy', order_flow: 'buy' }, opened_at: new Date(Date.now() - 172800000).toISOString(), closed_at: new Date(Date.now() - 86400000).toISOString() },
  { id: '3', instrument: 'GBPUSD', direction: 'sell', entry_price: 1.27100, exit_price: 1.27350, lot_size: 0.10, pnl: -25.00, pnl_pips: -25.0, status: 'closed', confidence_at_entry: 0.65, model_votes_at_entry: { trend_following: 'sell', mean_reversion: 'hold', sentiment: 'sell' }, opened_at: new Date(Date.now() - 259200000).toISOString(), closed_at: new Date(Date.now() - 172800000).toISOString() },
  { id: '4', instrument: 'NAS100', direction: 'buy', entry_price: 15420.50, exit_price: null, lot_size: 0.02, pnl: 0, pnl_pips: 0, status: 'open', confidence_at_entry: 0.78, model_votes_at_entry: { trend_following: 'buy', sentiment: 'buy', order_flow: 'buy' }, opened_at: new Date(Date.now() - 3600000).toISOString(), closed_at: null },
];

function formatPnl(value: number): string {
  const prefix = value >= 0 ? '+$' : '-$';
  return `${prefix}${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function pnlClass(value: number): string {
  if (value > 0) return 'pnl-positive';
  if (value < 0) return 'pnl-negative';
  return 'pnl-zero';
}

function confidenceLevel(conf: number): string {
  if (conf >= 0.75) return 'high';
  if (conf >= 0.5) return 'medium';
  return 'low';
}

function regimeBadgeClass(regime: string): string {
  switch (regime) {
    case 'trending': return 'badge-trending';
    case 'ranging': return 'badge-ranging';
    case 'volatile': return 'badge-volatile';
    default: return '';
  }
}

function formatModelName(name: string): string {
  return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function voteIcon(direction: string, signalDir: string): string {
  if (direction === signalDir) return '✓';
  if (direction === 'hold') return '○';
  return '✗';
}

function voteClass(direction: string, signalDir: string): string {
  if (direction === signalDir) return 'agree';
  if (direction === 'hold') return 'neutral';
  return 'disagree';
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary>(MOCK_SUMMARY);
  const [drawdown, setDrawdown] = useState<DrawdownInfo>(MOCK_DRAWDOWN);
  const [signals, setSignals] = useState<Signal[]>(MOCK_SIGNALS);
  const [trades, setTrades] = useState<Trade[]>(MOCK_TRADES);
  const [isLive, setIsLive] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [s, d, sig, t] = await Promise.all([
        api.getDashboardSummary(),
        api.getDrawdown(),
        api.getLatestSignals(10),
        api.getTrades(10),
      ]);
      setSummary(s);
      setDrawdown(d);
      setSignals(sig.signals);
      setTrades(t.trades);
      setIsLive(true);
    } catch {
      // Use mock data if API is not available
      setIsLive(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const ddLevel = drawdown.current_drawdown_pct < 5 ? 'safe' : drawdown.current_drawdown_pct < 8 ? 'warning' : 'danger';

  return (
    <div>
      {/* Status Bar */}
      <div className="status-bar animate-fade-in">
        <div className="status-item">
          <span className="label">Status</span>
          <span className="badge badge-online">
            <span className="pulse-dot online" />
            {isLive ? 'Live' : 'Demo'}
          </span>
        </div>
        <div className="status-divider" />
        <div className="status-item">
          <span className="label">Regime</span>
          <span className={`badge ${regimeBadgeClass(summary.current_regime)}`}>
            {summary.current_regime.toUpperCase()}
          </span>
        </div>
        <div className="status-divider" />
        <div className="status-item">
          <span className="label">Models</span>
          <span className="value">{summary.active_models.length} active</span>
        </div>
        <div className="status-divider" />
        <div className="status-item">
          <span className="label">Active Categories</span>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {summary.active_models.map(m => (
              <span key={m} className="badge" style={{
                background: 'var(--accent-blue-soft)',
                color: 'var(--accent-blue)',
                fontSize: 10,
                padding: '2px 6px',
              }}>
                {formatModelName(m)}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="metrics-grid">
        <div className="card animate-fade-in stagger-1">
          <div className="card-header">
            <span className="card-title">Total P/L</span>
            <span style={{ fontSize: 20 }}>💰</span>
          </div>
          <div className={`card-value ${pnlClass(summary.total_pnl)}`}>
            {formatPnl(summary.total_pnl)}
          </div>
          <div className="card-subtitle">{summary.total_trades} total trades</div>
        </div>

        <div className="card animate-fade-in stagger-2">
          <div className="card-header">
            <span className="card-title">Win Rate</span>
            <span style={{ fontSize: 20 }}>🎯</span>
          </div>
          <div className="card-value" style={{ color: 'var(--accent-blue)' }}>
            {summary.win_rate}%
          </div>
          <div className="card-subtitle">Across all closed trades</div>
        </div>

        <div className="card animate-fade-in stagger-3">
          <div className="card-header">
            <span className="card-title">AI Accuracy</span>
            <span style={{ fontSize: 20 }}>🤖</span>
          </div>
          <div className="card-value" style={{ color: 'var(--accent-cyan)' }}>
            {summary.ai_accuracy}%
          </div>
          <div className="card-subtitle">High-confidence signals profitable</div>
        </div>

        <div className="card animate-fade-in stagger-4">
          <div className="card-header">
            <span className="card-title">Today&apos;s P/L</span>
            <span style={{ fontSize: 20 }}>📈</span>
          </div>
          <div className={`card-value ${pnlClass(summary.today_pnl)}`}>
            {formatPnl(summary.today_pnl)}
          </div>
          <div className="card-subtitle">
            Week: <span className={pnlClass(summary.week_pnl)}>{formatPnl(summary.week_pnl)}</span>
            {' · '}
            Month: <span className={pnlClass(summary.month_pnl)}>{formatPnl(summary.month_pnl)}</span>
          </div>
        </div>
      </div>

      <div className="section-grid">
        {/* Drawdown Guard */}
        <div className="card drawdown-card animate-fade-in stagger-5">
          <div className="card-header">
            <span className="card-title">🛡️ Drawdown Guard</span>
            <span className={`badge ${drawdown.guard_active ? 'badge-offline' : 'badge-online'}`}>
              {drawdown.guard_active ? 'PAUSED' : 'ACTIVE'}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 4 }}>Current DD</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: ddLevel === 'safe' ? 'var(--success)' : ddLevel === 'warning' ? 'var(--warning)' : 'var(--danger)' }}>
                {drawdown.current_drawdown_pct}%
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>${drawdown.current_drawdown_value.toFixed(2)}</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 4 }}>Max DD</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-secondary)' }}>
                {drawdown.max_drawdown_pct}%
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>${drawdown.max_drawdown_value.toFixed(2)}</div>
            </div>
          </div>
          <div className="drawdown-progress">
            <div 
              className={`drawdown-fill drawdown-${ddLevel}`} 
              style={{ width: `${(drawdown.current_drawdown_pct / drawdown.guard_threshold) * 100}%` }} 
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)' }}>
            <span>0%</span>
            <span>Guard: {drawdown.guard_threshold}%</span>
          </div>
          <div style={{ marginTop: 12, fontSize: 13, color: 'var(--text-secondary)' }}>
            Risk per trade: <strong style={{ color: 'var(--text-primary)' }}>{drawdown.risk_per_trade}%</strong>
          </div>
          {drawdown.guard_active && drawdown.guard_reason && (
            <div className="drawdown-guard-active">⚠️ {drawdown.guard_reason}</div>
          )}
        </div>

        {/* Equity Curve Placeholder */}
        <div className="card animate-fade-in stagger-6">
          <div className="card-header">
            <span className="card-title">📈 Equity Curve</span>
            <div style={{ display: 'flex', gap: 4 }}>
              {['1D', '1W', '1M', 'ALL'].map(range => (
                <button key={range} className="btn btn-ghost btn-sm" style={{ fontSize: 11, padding: '4px 8px' }}>
                  {range}
                </button>
              ))}
            </div>
          </div>
          <div style={{ 
            height: 200, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-md)',
            position: 'relative',
            overflow: 'hidden',
          }}>
            {/* SVG Mini Chart */}
            <svg viewBox="0 0 400 150" style={{ width: '100%', height: '100%' }}>
              <defs>
                <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#06b6d4" />
                </linearGradient>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="rgba(59,130,246,0.15)" />
                  <stop offset="100%" stopColor="rgba(59,130,246,0)" />
                </linearGradient>
              </defs>
              <path d="M0 130 L30 120 L60 110 L90 100 L120 105 L150 85 L180 75 L210 80 L240 60 L270 50 L300 55 L330 35 L360 25 L400 20" 
                    fill="url(#areaGrad)" stroke="none">
                <animate attributeName="d" dur="0.8s" fill="freeze"
                  from="M0 130 L30 130 L60 130 L90 130 L120 130 L150 130 L180 130 L210 130 L240 130 L270 130 L300 130 L330 130 L360 130 L400 130"
                  to="M0 130 L30 120 L60 110 L90 100 L120 105 L150 85 L180 75 L210 80 L240 60 L270 50 L300 55 L330 35 L360 25 L400 20" />
              </path>
              <path d="M0 130 L30 120 L60 110 L90 100 L120 105 L150 85 L180 75 L210 80 L240 60 L270 50 L300 55 L330 35 L360 25 L400 20" 
                    fill="none" stroke="url(#lineGrad)" strokeWidth="2.5" strokeLinecap="round">
                <animate attributeName="d" dur="0.8s" fill="freeze"
                  from="M0 130 L30 130 L60 130 L90 130 L120 130 L150 130 L180 130 L210 130 L240 130 L270 130 L300 130 L330 130 L360 130 L400 130"
                  to="M0 130 L30 120 L60 110 L90 100 L120 105 L150 85 L180 75 L210 80 L240 60 L270 50 L300 55 L330 35 L360 25 L400 20" />
              </path>
              <circle cx="400" cy="20" r="4" fill="#06b6d4">
                <animate attributeName="opacity" values="1;0.4;1" dur="2s" repeatCount="indefinite" />
              </circle>
            </svg>
          </div>
        </div>
      </div>

      {/* Recent Signals */}
      <div className="card animate-fade-in" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">📡 Recent Signals</span>
          <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
            {signals.length} signals
          </span>
        </div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Instrument</th>
                <th>TF</th>
                <th>Direction</th>
                <th>Confidence</th>
                <th>Regime</th>
                <th>Model Votes</th>
                <th>Entry</th>
                <th>SL / TP</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((signal) => (
                <tr key={signal.id}>
                  <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)', fontSize: 13 }}>
                    {signal.instrument}
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{signal.timeframe}</td>
                  <td>
                    <span className={`badge badge-${signal.direction}`}>
                      {signal.direction.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <div className="confidence-gauge">
                      <div className="confidence-bar">
                        <div 
                          className={`confidence-fill ${confidenceLevel(signal.confidence)}`}
                          style={{ width: `${signal.confidence * 100}%` }}
                        />
                      </div>
                      <span className={`confidence-value ${pnlClass(signal.confidence - 0.5)}`}>
                        {(signal.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${regimeBadgeClass(signal.regime)}`}>
                      {signal.regime}
                    </span>
                  </td>
                  <td>
                    <div className="model-votes">
                      {Object.entries(signal.model_votes)
                        .filter(([k]) => k !== 'volatility_regime')
                        .map(([cat, dir]) => (
                          <span key={cat} className={`model-vote ${voteClass(dir, signal.direction)}`}>
                            <span className="vote-icon">{voteIcon(dir, signal.direction)}</span>
                            {cat.split('_').map(w => w[0].toUpperCase()).join('')}
                          </span>
                        ))}
                    </div>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                    {signal.entry_price?.toFixed(signal.entry_price > 100 ? 2 : 5) || '—'}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)' }}>
                    {signal.stop_loss ? (
                      <>
                        <span style={{ color: 'var(--danger)' }}>{signal.stop_loss.toFixed(signal.stop_loss > 100 ? 2 : 5)}</span>
                        {' / '}
                        <span style={{ color: 'var(--success)' }}>{signal.take_profit?.toFixed(signal.take_profit > 100 ? 2 : 5)}</span>
                      </>
                    ) : '—'}
                  </td>
                  <td style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                    {new Date(signal.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Trade History */}
      <div className="card animate-fade-in">
        <div className="card-header">
          <span className="card-title">📋 Trade History</span>
          <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
            {trades.filter(t => t.status === 'open').length} open · {trades.filter(t => t.status === 'closed').length} closed
          </span>
        </div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Instrument</th>
                <th>Direction</th>
                <th>Entry</th>
                <th>Exit</th>
                <th>Lots</th>
                <th>P/L</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade) => (
                <tr key={trade.id}>
                  <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)', fontSize: 13 }}>
                    {trade.instrument}
                  </td>
                  <td>
                    <span className={`badge badge-${trade.direction}`}>
                      {trade.direction.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                    {trade.entry_price.toFixed(trade.entry_price > 100 ? 2 : 5)}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                    {trade.exit_price?.toFixed(trade.exit_price > 100 ? 2 : 5) || '—'}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                    {trade.lot_size.toFixed(2)}
                  </td>
                  <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                    <span className={pnlClass(trade.pnl)}>
                      {formatPnl(trade.pnl)}
                    </span>
                  </td>
                  <td>
                    {trade.confidence_at_entry ? (
                      <div className="confidence-gauge">
                        <div className="confidence-bar" style={{ maxWidth: 60 }}>
                          <div 
                            className={`confidence-fill ${confidenceLevel(trade.confidence_at_entry)}`}
                            style={{ width: `${trade.confidence_at_entry * 100}%` }}
                          />
                        </div>
                        <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                          {(trade.confidence_at_entry * 100).toFixed(0)}%
                        </span>
                      </div>
                    ) : '—'}
                  </td>
                  <td>
                    <span className={`badge ${trade.status === 'open' ? 'badge-trending' : trade.pnl >= 0 ? 'badge-online' : 'badge-offline'}`}>
                      {trade.status === 'open' ? '● OPEN' : trade.status.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                    {new Date(trade.opened_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
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
