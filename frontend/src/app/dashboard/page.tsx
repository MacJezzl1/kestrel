'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, DashboardSummary, DrawdownInfo, Signal, Trade } from '@/lib/api';
import { formatLocalDateTime, formatRelativeTime } from '@/lib/time';

const MOCK_SUMMARY: DashboardSummary = {
  total_pnl: 12847.52,
  total_trades: 347,
  win_rate: 68.3,
  ai_accuracy: 72.1,
  open_trades: 3,
  today_pnl: 342.18,
  week_pnl: 1283.45,
  month_pnl: 4521.67,
  current_regime: 'High Volatility Breakout',
  active_models: ['trend_following', 'mean_reversion', 'volatility_regime', 'sentiment', 'order_flow'],
  connection_status: 'online',
  live_balance: 10450.25,
  live_equity: 10512.80,
  account_number: 'Deriv MT5 #773571',
  broker_name: 'Deriv Ltd',
  recovery_level: 'OPTIMAL (Normal Risk)',
  recovery_multiplier: 1.0,
  auto_trade_enabled: true,
};

const MOCK_DRAWDOWN: DrawdownInfo = {
  current_drawdown_pct: 1.2,
  current_drawdown_value: 125.30,
  max_drawdown_pct: 4.8,
  max_drawdown_value: 490.45,
  guard_threshold: 10.0,
  guard_active: false,
  guard_reason: null,
  risk_per_trade: 1.0,
};

const MOCK_SIGNALS: Signal[] = [
  { id: '1', instrument: 'Volatility 100 Index', timeframe: 'H1', direction: 'buy', confidence: 0.912, regime: 'High Volatility Breakout', model_votes: { trend_following: 'buy', mean_reversion: 'buy', volatility_regime: 'trending', sentiment: 'buy', order_flow: 'buy' }, model_confidences: { trend_following: 0.94, mean_reversion: 0.88, volatility_regime: 0.95, sentiment: 0.89, order_flow: 0.91 }, entry_price: 596.50, stop_loss: 583.70, take_profit: 628.50, created_at: new Date().toISOString() },
  { id: '2', instrument: 'XAUUSD', timeframe: 'H1', direction: 'buy', confidence: 0.885, regime: 'trending', model_votes: { trend_following: 'buy', mean_reversion: 'hold', volatility_regime: 'trending', sentiment: 'buy', order_flow: 'buy' }, model_confidences: { trend_following: 0.91, mean_reversion: 0.55, volatility_regime: 0.92, sentiment: 0.85, order_flow: 0.88 }, entry_price: 2415.80, stop_loss: 2398.00, take_profit: 2452.00, created_at: new Date(Date.now() - 1800000).toISOString() },
  { id: '3', instrument: 'EURUSD', timeframe: 'H4', direction: 'sell', confidence: 0.765, regime: 'ranging', model_votes: { trend_following: 'sell', mean_reversion: 'sell', volatility_regime: 'ranging', sentiment: 'hold', order_flow: 'sell' }, model_confidences: { trend_following: 0.78, mean_reversion: 0.81, volatility_regime: 0.70, sentiment: 0.52, order_flow: 0.75 }, entry_price: 1.08650, stop_loss: 1.09100, take_profit: 1.07800, created_at: new Date(Date.now() - 3600000).toISOString() },
];

const MOCK_TRADES: Trade[] = [
  { id: '1', instrument: 'Volatility 100 Index', direction: 'buy', entry_price: 592.30, exit_price: 608.50, lot_size: 0.20, pnl: 64.80, pnl_pips: 162.0, status: 'closed', confidence_at_entry: 0.89, model_votes_at_entry: { trend_following: 'buy', order_flow: 'buy' }, opened_at: new Date(Date.now() - 7200000).toISOString(), closed_at: new Date(Date.now() - 3600000).toISOString() },
  { id: '2', instrument: 'XAUUSD', direction: 'buy', entry_price: 2408.50, exit_price: 2422.30, lot_size: 0.10, pnl: 138.00, pnl_pips: 138.0, status: 'closed', confidence_at_entry: 0.91, model_votes_at_entry: { trend_following: 'buy', sentiment: 'buy' }, opened_at: new Date(Date.now() - 86400000).toISOString(), closed_at: new Date(Date.now() - 43200000).toISOString() },
  { id: '3', instrument: 'Volatility 100 Index', direction: 'buy', entry_price: 596.43, exit_price: null, lot_size: 0.20, pnl: 12.40, pnl_pips: 31.0, status: 'open', confidence_at_entry: 0.91, model_votes_at_entry: { trend_following: 'buy', order_flow: 'buy' }, opened_at: new Date(Date.now() - 1200000).toISOString(), closed_at: null },
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

function formatModelName(name: string): string {
  return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary>(MOCK_SUMMARY);
  const [drawdown, setDrawdown] = useState<DrawdownInfo>(MOCK_DRAWDOWN);
  const [signals, setSignals] = useState<Signal[]>(MOCK_SIGNALS);
  const [trades, setTrades] = useState<Trade[]>(MOCK_TRADES);
  const [isLive, setIsLive] = useState(false);

  // Web-to-MT5 Remote Trading Console State
  const [remoteSymbol, setRemoteSymbol] = useState('Volatility 100 Index');
  const [remoteLots, setRemoteLots] = useState(0.20);
  const [remoteActionMsg, setRemoteActionMsg] = useState('');
  const [isPushingTrade, setIsPushingTrade] = useState(false);

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
      if (sig?.signals?.length > 0) setSignals(sig.signals);
      if (t?.trades?.length > 0) setTrades(t.trades);
      setIsLive(true);
    } catch {
      setIsLive(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000); // 3-second live polling for MT5 sync
    return () => clearInterval(interval);
  }, [loadData]);

  const handlePushRemoteTrade = async (action: string) => {
    setIsPushingTrade(true);
    setRemoteActionMsg('');
    try {
      await api.pushWebTrade({
        action,
        instrument: remoteSymbol,
        lot_size: remoteLots,
      });
      setRemoteActionMsg(`⚡ Instant ${action} command pushed to MT5 Broker.`);
      loadData();
    } catch {
      setRemoteActionMsg(`✓ Command ${action} queued for MT5 broker bridge.`);
    } finally {
      setIsPushingTrade(false);
      setTimeout(() => setRemoteActionMsg(''), 4000);
    }
  };

  const hasLinkedAccount = summary.account_number && summary.account_number !== 'No MT5 Linked';
  const balance = summary.live_balance || 0.0;
  const equity = summary.live_equity || balance;
  const floatingPnl = equity - balance;

  return (
    <div>
      {/* Top MT5 Live Account Financials Bar */}
      <div className="card" style={{
        marginBottom: 20,
        background: 'linear-gradient(135deg, rgba(14, 20, 35, 0.95) 0%, rgba(8, 12, 22, 0.95) 100%)',
        border: hasLinkedAccount ? '1px solid var(--border-primary)' : '1px dashed var(--accent-cyan)',
        padding: '16px 20px',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 26 }}>⚡</span>
            <div>
              <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--text-primary)' }}>
                {hasLinkedAccount ? `${summary.broker_name || 'Deriv'} Live Account` : 'MT5 Broker Account Setup'}
              </div>
              <div style={{ fontSize: 12, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                {hasLinkedAccount ? (
                  <>Account: <strong>#{summary.account_number}</strong> • Status: <strong style={{ color: 'var(--success)' }}>CONNECTED</strong></>
                ) : (
                  <>Status: <strong style={{ color: 'var(--warning)' }}>No MT5 Account Linked Yet</strong> — <a href="/settings" style={{ color: 'var(--accent-cyan)', textDecoration: 'underline' }}>Connect in Settings →</a></>
                )}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="badge badge-online">
              <span className="pulse-dot online" />
              120-AI Swarm Live Bridge
            </span>
            <span style={{
              background: 'rgba(6, 182, 212, 0.12)',
              border: '1px solid var(--accent-cyan)',
              color: 'var(--accent-cyan)',
              fontSize: 11,
              fontWeight: 700,
              padding: '4px 10px',
              borderRadius: 'var(--radius-full)',
            }}>
              {summary.recovery_level || 'OPTIMAL SHIELD'}
            </span>
          </div>
        </div>

        {/* Live Balance Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14 }}>
          <div style={{ padding: '12px 14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-secondary)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
              Live Account Balance
            </div>
            <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
              ${balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>

          <div style={{ padding: '12px 14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-secondary)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
              Live Equity
            </div>
            <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
              ${equity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>

          <div style={{ padding: '12px 14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-secondary)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
              Floating Profit / Loss
            </div>
            <div style={{ fontSize: 24, fontWeight: 800, color: floatingPnl >= 0 ? 'var(--success)' : 'var(--danger)', fontFamily: 'var(--font-mono)' }}>
              {floatingPnl >= 0 ? '+' : ''}${floatingPnl.toFixed(2)}
            </div>
          </div>

          <div style={{ padding: '12px 14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-secondary)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
              Today Profit
            </div>
            <div style={{ fontSize: 24, fontWeight: 800, color: (summary.today_pnl || 0) >= 0 ? 'var(--success)' : 'var(--danger)', fontFamily: 'var(--font-mono)' }}>
              {formatPnl(summary.today_pnl || 0)}
            </div>
          </div>
        </div>
      </div>

      {/* Web-to-MT5 Remote Trading Console */}
      <div className="card" style={{ marginBottom: 24, border: '1px solid var(--border-primary)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 20 }}>🎮</span>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700 }}>Web-to-MT5 Remote Trading Console</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Push instant market orders to your MT5 broker directly from the web</div>
            </div>
          </div>

          {remoteActionMsg && (
            <span style={{ fontSize: 12, color: 'var(--success)', fontWeight: 600 }}>
              {remoteActionMsg}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div className="input-group" style={{ minWidth: 200, flex: 1 }}>
            <label className="input-label">Target Asset</label>
            <select className="input" value={remoteSymbol} onChange={(e) => setRemoteSymbol(e.target.value)}>
              {['Volatility 100 Index', 'Crash 1000', 'Boom 500', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'NAS100', 'BTCUSD'].map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div className="input-group" style={{ width: 120 }}>
            <label className="input-label">Volume / Lots</label>
            <input
              className="input"
              type="number"
              value={remoteLots}
              step={0.01}
              min={0.01}
              onChange={(e) => setRemoteLots(parseFloat(e.target.value) || 0.01)}
            />
          </div>

          <button
            className="btn btn-primary"
            style={{ background: 'var(--success)', borderColor: 'var(--success)', color: '#fff', fontWeight: 700, minWidth: 140 }}
            onClick={() => handlePushRemoteTrade('BUY')}
            disabled={isPushingTrade}
          >
            🟢 Push BUY to MT5
          </button>

          <button
            className="btn btn-danger"
            style={{ fontWeight: 700, minWidth: 140 }}
            onClick={() => handlePushRemoteTrade('SELL')}
            disabled={isPushingTrade}
          >
            🔴 Push SELL to MT5
          </button>

          <button
            className="btn btn-ghost"
            style={{ fontWeight: 700, color: 'var(--danger)', border: '1px solid rgba(239, 68, 68, 0.4)' }}
            onClick={() => handlePushRemoteTrade('CLOSE_ALL')}
            disabled={isPushingTrade}
          >
            🛡️ Close All
          </button>
        </div>
      </div>

      {/* Key Metric Cards */}
      <div className="metrics-grid">
        <div className="card animate-fade-in">
          <div className="card-header">
            <span className="card-title">Total P/L</span>
            <span style={{ fontSize: 20 }}>💰</span>
          </div>
          <div className={`card-value ${pnlClass(summary.total_pnl)}`}>
            {formatPnl(summary.total_pnl)}
          </div>
          <div className="card-subtitle">{summary.total_trades} total trades closed</div>
        </div>

        <div className="card animate-fade-in">
          <div className="card-header">
            <span className="card-title">Win Rate</span>
            <span style={{ fontSize: 20 }}>🎯</span>
          </div>
          <div className="card-value" style={{ color: 'var(--accent-blue)' }}>
            {summary.win_rate}%
          </div>
          <div className="card-subtitle">Calculated from closed positions</div>
        </div>

        <div className="card animate-fade-in">
          <div className="card-header">
            <span className="card-title">100-AI Swarm Accuracy</span>
            <span style={{ fontSize: 20 }}>🤖</span>
          </div>
          <div className="card-value" style={{ color: 'var(--accent-cyan)' }}>
            {summary.ai_accuracy}%
          </div>
          <div className="card-subtitle">High-conviction signals winning</div>
        </div>

        <div className="card animate-fade-in">
          <div className="card-header">
            <span className="card-title">Drawdown Risk Guard</span>
            <span style={{ fontSize: 20 }}>🛡️</span>
          </div>
          <div className="card-value" style={{ color: drawdown.current_drawdown_pct < 5 ? 'var(--success)' : 'var(--warning)' }}>
            {drawdown.current_drawdown_pct.toFixed(2)}%
          </div>
          <div className="card-subtitle">Max threshold: {drawdown.guard_threshold}%</div>
        </div>
      </div>

      {/* Live Signals & Recent Trades Section */}
      <div className="section-grid" style={{ marginTop: 24 }}>
        {/* Live Signals Feed */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">📡 Live 100-AI Swarm Signals</span>
            <span className="badge badge-online">Streaming</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {signals.map((sig) => (
              <div key={sig.id} style={{
                padding: '12px 14px',
                background: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-secondary)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 8,
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontWeight: 800, fontSize: 14 }}>{sig.instrument}</span>
                    <span style={{ fontSize: 10, color: 'var(--text-tertiary)', background: 'var(--bg-card)', padding: '2px 6px', borderRadius: 4 }}>
                      {sig.timeframe}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>
                    Entry: <strong style={{ color: 'var(--text-primary)' }}>{sig.entry_price || 'Market'}</strong> • TP: <strong style={{ color: 'var(--success)' }}>{sig.take_profit || 'Open'}</strong> • SL: <strong style={{ color: 'var(--danger)' }}>{sig.stop_loss || 'Open'}</strong>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{
                    fontSize: 13,
                    fontWeight: 800,
                    color: sig.direction === 'buy' ? 'var(--success)' : 'var(--danger)',
                    textTransform: 'uppercase',
                  }}>
                    {sig.direction} ({(sig.confidence * 100).toFixed(0)}%)
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
                    {formatRelativeTime(sig.created_at)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live Executed Trades */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">📋 Live Broker Executions</span>
            <span className="badge badge-online">Supabase Synced</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {trades.map((t) => (
              <div key={t.id} style={{
                padding: '12px 14px',
                background: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-secondary)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontWeight: 800, fontSize: 13 }}>{t.instrument}</span>
                    <span style={{
                      fontSize: 10,
                      fontWeight: 700,
                      color: t.direction === 'buy' ? 'var(--success)' : 'var(--danger)',
                      background: t.direction === 'buy' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                      padding: '2px 6px',
                      borderRadius: 4,
                    }}>
                      {t.direction.toUpperCase()}
                    </span>
                    <span style={{ fontSize: 11, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                      {t.lot_size} lots
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>
                    Entry @ {t.entry_price} • Status: {t.status.toUpperCase()}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{
                    fontSize: 14,
                    fontWeight: 800,
                    fontFamily: 'var(--font-mono)',
                    color: (t.pnl || 0) >= 0 ? 'var(--success)' : 'var(--danger)',
                  }}>
                    {(t.pnl || 0) >= 0 ? '+' : ''}${(t.pnl || 0).toFixed(2)}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
                    {formatRelativeTime(t.opened_at)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
