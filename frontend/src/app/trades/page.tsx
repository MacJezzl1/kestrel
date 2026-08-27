'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, Trade, TradeStats } from '@/lib/api';

const MOCK_STATS: TradeStats = {
  total_trades: 347, open_trades: 3, closed_trades: 344,
  total_pnl: 12847.52, win_rate: 68.3, avg_pnl: 37.35,
  best_trade: 284.50, worst_trade: -127.30, avg_confidence: 0.724,
};

const MOCK_TRADES: Trade[] = [
  { id: '1', instrument: 'EURUSD', direction: 'buy', entry_price: 1.08320, exit_price: 1.08690, lot_size: 0.10, pnl: 37.00, pnl_pips: 37, status: 'closed', confidence_at_entry: 0.82, model_votes_at_entry: { trend_following: 'buy', mean_reversion: 'hold', sentiment: 'buy' }, opened_at: new Date(Date.now() - 86400000).toISOString(), closed_at: new Date(Date.now() - 43200000).toISOString() },
  { id: '2', instrument: 'XAUUSD', direction: 'buy', entry_price: 1948.50, exit_price: 1962.30, lot_size: 0.05, pnl: 69.00, pnl_pips: 138, status: 'closed', confidence_at_entry: 0.91, model_votes_at_entry: { trend_following: 'buy', mean_reversion: 'buy', order_flow: 'buy' }, opened_at: new Date(Date.now() - 172800000).toISOString(), closed_at: new Date(Date.now() - 86400000).toISOString() },
  { id: '3', instrument: 'GBPUSD', direction: 'sell', entry_price: 1.27100, exit_price: 1.27350, lot_size: 0.10, pnl: -25.00, pnl_pips: -25, status: 'closed', confidence_at_entry: 0.65, model_votes_at_entry: { trend_following: 'sell', mean_reversion: 'hold' }, opened_at: new Date(Date.now() - 259200000).toISOString(), closed_at: new Date(Date.now() - 172800000).toISOString() },
  { id: '4', instrument: 'NAS100', direction: 'buy', entry_price: 15420.50, exit_price: null, lot_size: 0.02, pnl: 0, pnl_pips: 0, status: 'open', confidence_at_entry: 0.78, model_votes_at_entry: { trend_following: 'buy', sentiment: 'buy' }, opened_at: new Date(Date.now() - 3600000).toISOString(), closed_at: null },
  { id: '5', instrument: 'USDJPY', direction: 'sell', entry_price: 149.852, exit_price: 149.450, lot_size: 0.10, pnl: 40.20, pnl_pips: 40.2, status: 'closed', confidence_at_entry: 0.88, model_votes_at_entry: { trend_following: 'sell', order_flow: 'sell' }, opened_at: new Date(Date.now() - 345600000).toISOString(), closed_at: new Date(Date.now() - 259200000).toISOString() },
];

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>(MOCK_TRADES);
  const [stats, setStats] = useState<TradeStats>(MOCK_STATS);
  const [filter, setFilter] = useState<'all' | 'open' | 'closed'>('all');

  const loadData = useCallback(async () => {
    try {
      const [t, s] = await Promise.all([api.getTrades(100), api.getTradeStats()]);
      setTrades(t.trades);
      setStats(s);
    } catch { /* Use mock data */ }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const filtered = filter === 'all' ? trades : trades.filter(t => t.status === filter);

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>📋 Trade History</h1>

      {/* Stats Cards */}
      <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', marginBottom: 24 }}>
        {[
          { label: 'Total Trades', value: stats.total_trades, color: 'var(--text-primary)' },
          { label: 'Win Rate', value: `${stats.win_rate}%`, color: 'var(--accent-blue)' },
          { label: 'Total P/L', value: `$${stats.total_pnl.toLocaleString()}`, color: stats.total_pnl >= 0 ? 'var(--success)' : 'var(--danger)' },
          { label: 'Avg P/L', value: `$${stats.avg_pnl.toFixed(2)}`, color: stats.avg_pnl >= 0 ? 'var(--success)' : 'var(--danger)' },
          { label: 'Best Trade', value: `$${stats.best_trade.toFixed(2)}`, color: 'var(--success)' },
          { label: 'Worst Trade', value: `$${stats.worst_trade.toFixed(2)}`, color: 'var(--danger)' },
        ].map(m => (
          <div key={m.label} className="card">
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, marginBottom: 6 }}>{m.label}</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: m.color, fontFamily: 'var(--font-mono)' }}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {(['all', 'open', 'closed'] as const).map(f => (
          <button key={f} className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'} btn-sm`} onClick={() => setFilter(f)}>
            {f.charAt(0).toUpperCase() + f.slice(1)} {f === 'open' ? `(${trades.filter(t => t.status === 'open').length})` : ''}
          </button>
        ))}
      </div>

      {/* Trade Table */}
      <div className="card">
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
                <th>Pips</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Opened</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(trade => (
                <tr key={trade.id}>
                  <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{trade.instrument}</td>
                  <td><span className={`badge badge-${trade.direction}`}>{trade.direction.toUpperCase()}</span></td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{trade.entry_price.toFixed(trade.entry_price > 100 ? 2 : 5)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{trade.exit_price?.toFixed(trade.exit_price > 100 ? 2 : 5) || '—'}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{trade.lot_size.toFixed(2)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: trade.pnl > 0 ? 'var(--success)' : trade.pnl < 0 ? 'var(--danger)' : 'var(--text-secondary)' }}>
                    {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: trade.pnl_pips > 0 ? 'var(--success)' : trade.pnl_pips < 0 ? 'var(--danger)' : 'var(--text-secondary)' }}>
                    {trade.pnl_pips > 0 ? '+' : ''}{trade.pnl_pips.toFixed(1)}
                  </td>
                  <td>
                    {trade.confidence_at_entry ? (
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{(trade.confidence_at_entry * 100).toFixed(0)}%</span>
                    ) : '—'}
                  </td>
                  <td>
                    <span className={`badge ${trade.status === 'open' ? 'badge-trending' : trade.pnl >= 0 ? 'badge-online' : 'badge-offline'}`}>
                      {trade.status.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                    {new Date(trade.opened_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
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
