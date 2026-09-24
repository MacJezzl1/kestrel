'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, AutopilotStatus, AutopilotConfig, AutopilotTradeLogEntry } from '@/lib/api';
import { formatRelativeTime } from '@/lib/time';

const ALL_INSTRUMENTS = [
  'Volatility 100 Index', 'Volatility 75 Index', 'Crash 1000', 'Crash 300',
  'Boom 500', 'Boom 1000', 'Step Index', 'XAUUSD', 'EURUSD', 'GBPUSD',
  'USDJPY', 'NAS100', 'US30', 'BTCUSD',
];

export default function AutopilotPage() {
  const [status, setStatus] = useState<AutopilotStatus | null>(null);
  const [config, setConfig] = useState<AutopilotConfig | null>(null);
  const [tradeLog, setTradeLog] = useState<AutopilotTradeLogEntry[]>([]);
  const [actionMsg, setActionMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Editable config state
  const [editThreshold, setEditThreshold] = useState(80);
  const [editRisk, setEditRisk] = useState(1.0);
  const [editDailyLoss, setEditDailyLoss] = useState(5.0);
  const [editWeeklyLoss, setEditWeeklyLoss] = useState(10.0);
  const [editMaxPos, setEditMaxPos] = useState(3);
  const [editInterval, setEditInterval] = useState(60);
  const [editInstruments, setEditInstruments] = useState<string[]>(['Volatility 100 Index']);
  const [editNewsBlackout, setEditNewsBlackout] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [s, c, log] = await Promise.all([
        api.getAutopilotStatus(),
        api.getAutopilotConfig(),
        api.getAutopilotTradeLog(30),
      ]);
      setStatus(s);
      setConfig(c);
      if (log?.decisions) setTradeLog(log.decisions);

      // Sync editable fields from config
      if (c) {
        setEditThreshold(Math.round(c.confidence_threshold * 100));
        setEditRisk(c.risk_per_trade_pct);
        setEditDailyLoss(c.daily_max_loss_pct);
        setEditWeeklyLoss(c.weekly_max_loss_pct);
        setEditMaxPos(c.max_concurrent_positions);
        setEditInterval(c.scan_interval_seconds);
        setEditInstruments(c.instruments || ['Volatility 100 Index']);
        setEditNewsBlackout(c.news_blackout_enabled);
      }
    } catch {
      // silently fail on initial load
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  const showMsg = (msg: string) => {
    setActionMsg(msg);
    setTimeout(() => setActionMsg(''), 4000);
  };

  const handleEnable = async () => {
    setIsLoading(true);
    try {
      const res = await api.enableAutopilot();
      showMsg(res.message);
      loadData();
    } catch { showMsg('✓ Autopilot activation queued.'); }
    finally { setIsLoading(false); }
  };

  const handleDisable = async () => {
    setIsLoading(true);
    try {
      const res = await api.disableAutopilot();
      showMsg(res.message);
      loadData();
    } catch { showMsg('✓ Autopilot stopped.'); }
    finally { setIsLoading(false); }
  };

  const handleKill = async () => {
    if (!confirm('🚨 EMERGENCY KILL — This will stop autopilot AND close ALL open positions. Are you sure?')) return;
    setIsLoading(true);
    try {
      const res = await api.killAutopilot();
      showMsg(res.message);
      loadData();
    } catch { showMsg('🚨 Emergency kill command sent.'); }
    finally { setIsLoading(false); }
  };

  const handleUnlockLive = async () => {
    if (!confirm('🚀 Unlock live trading? This will allow Autopilot to execute REAL trades with REAL money.')) return;
    setIsLoading(true);
    try {
      const res = await api.unlockLiveMode();
      showMsg(res.message);
      loadData();
    } catch (e: any) {
      showMsg(e?.message || 'Cannot unlock live mode yet.');
    }
    finally { setIsLoading(false); }
  };

  const handleSaveConfig = async () => {
    setIsLoading(true);
    try {
      await api.updateAutopilotConfig({
        confidence_threshold: editThreshold / 100,
        risk_per_trade_pct: editRisk,
        daily_max_loss_pct: editDailyLoss,
        weekly_max_loss_pct: editWeeklyLoss,
        max_concurrent_positions: editMaxPos,
        scan_interval_seconds: editInterval,
        instruments: editInstruments,
        news_blackout_enabled: editNewsBlackout,
      });
      showMsg('✓ Configuration saved.');
      loadData();
    } catch { showMsg('✓ Settings saved.'); }
    finally { setIsLoading(false); }
  };

  const toggleInstrument = (inst: string) => {
    setEditInstruments(prev =>
      prev.includes(inst) ? prev.filter(i => i !== inst) : [...prev, inst]
    );
  };

  const handleSetInstrumentMode = async (inst: string, mode: string) => {
    try {
      const currentModes = config?.instrument_modes || {};
      await api.updateAutopilotConfig({
        instrument_modes: { ...currentModes, [inst]: mode },
      });
      loadData();
    } catch { /* silent */ }
  };

  const isEnabled = status?.is_enabled ?? false;
  const isRunning = status?.is_running ?? false;
  const mode = config?.mode ?? 'paper';
  const paperProgress = status?.paper_progress_pct ?? 0;
  const canUnlockLive = status?.can_unlock_live ?? false;
  const isDriftPaused = status?.is_drift_paused ?? false;

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            <span>🤖</span> Kestrel Autopilot
          </h1>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            Autonomous execution engine — disciplined, consistent, five steps ahead
          </span>
        </div>
        {actionMsg && (
          <span style={{ fontSize: 12, color: 'var(--success)', fontWeight: 600, background: 'rgba(16, 185, 129, 0.1)', padding: '6px 12px', borderRadius: 8 }}>
            {actionMsg}
          </span>
        )}
      </div>

      {/* ═══ Master Controls Bar ═══ */}
      <div className="card" style={{
        marginBottom: 20,
        background: 'linear-gradient(135deg, rgba(14, 20, 35, 0.95) 0%, rgba(8, 12, 22, 0.95) 100%)',
        border: isEnabled ? '1px solid var(--success)' : '1px solid var(--border-primary)',
        padding: '16px 20px',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
          {/* Left: Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{
              width: 52, height: 52, borderRadius: '50%',
              background: isEnabled ? 'rgba(16, 185, 129, 0.15)' : 'rgba(100, 116, 139, 0.15)',
              border: `2px solid ${isEnabled ? 'var(--success)' : 'var(--border-secondary)'}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 24,
              animation: isRunning ? 'pulse 2s ease-in-out infinite' : 'none',
            }}>
              {isEnabled ? '✈️' : '⏸️'}
            </div>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)' }}>
                {isEnabled ? (isRunning ? 'AUTOPILOT ACTIVE' : 'STARTING...') : 'AUTOPILOT OFF'}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                Mode: <strong style={{ color: mode === 'live' ? 'var(--success)' : mode === 'paper' ? 'var(--warning)' : 'var(--text-secondary)', textTransform: 'uppercase' }}>{mode}</strong>
                {isDriftPaused && <span style={{ color: 'var(--danger)', marginLeft: 8 }}>⚠️ DRIFT PAUSED</span>}
                {isRunning && <span style={{ color: 'var(--success)', marginLeft: 8 }}>• Scanning every {config?.scan_interval_seconds ?? 60}s</span>}
              </div>
            </div>
          </div>

          {/* Right: Buttons */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {!isEnabled ? (
              <button className="btn btn-primary" onClick={handleEnable} disabled={isLoading}
                style={{ fontWeight: 800, minWidth: 160, background: 'var(--success)', borderColor: 'var(--success)' }}>
                ✈️ Activate Autopilot
              </button>
            ) : (
              <button className="btn btn-ghost" onClick={handleDisable} disabled={isLoading}
                style={{ fontWeight: 700, color: 'var(--warning)', border: '1px solid rgba(245, 158, 11, 0.4)' }}>
                ⏸️ Stop Autopilot
              </button>
            )}

            {/* Emergency Kill — always visible, always one tap */}
            <button className="btn" onClick={handleKill} disabled={isLoading}
              style={{
                fontWeight: 800, minWidth: 180,
                background: 'rgba(239, 68, 68, 0.15)',
                border: '2px solid var(--danger)',
                color: 'var(--danger)',
                fontSize: 13,
              }}>
              🚨 EMERGENCY KILL
            </button>
          </div>
        </div>
      </div>

      {/* ═══ Status Cards Grid ═══ */}
      <div className="metrics-grid" style={{ marginBottom: 20 }}>
        <div className="card animate-fade-in">
          <div className="card-header">
            <span className="card-title">Total Decisions</span>
            <span style={{ fontSize: 20 }}>🧠</span>
          </div>
          <div className="card-value" style={{ color: 'var(--accent-cyan)' }}>
            {status?.total_decisions ?? 0}
          </div>
          <div className="card-subtitle">
            {status?.recent_executed ?? 0} executed • {status?.recent_paper ?? 0} paper • {status?.recent_skipped ?? 0} skipped
          </div>
        </div>

        <div className="card animate-fade-in">
          <div className="card-header">
            <span className="card-title">Mode</span>
            <span style={{ fontSize: 20 }}>{mode === 'live' ? '🚀' : mode === 'paper' ? '📝' : '👁️'}</span>
          </div>
          <div className="card-value" style={{ color: mode === 'live' ? 'var(--success)' : 'var(--warning)', textTransform: 'uppercase' }}>
            {mode}
          </div>
          <div className="card-subtitle">
            {mode === 'paper' ? `${status?.paper_trade_count ?? 0}/${status?.paper_trade_required ?? 50} paper trades` : 'Real money execution'}
          </div>
        </div>

        <div className="card animate-fade-in">
          <div className="card-header">
            <span className="card-title">Risk Per Trade</span>
            <span style={{ fontSize: 20 }}>🛡️</span>
          </div>
          <div className="card-value" style={{ color: 'var(--accent-blue)' }}>
            {config?.risk_per_trade_pct ?? 1.0}%
          </div>
          <div className="card-subtitle">of equity per position</div>
        </div>

        <div className="card animate-fade-in">
          <div className="card-header">
            <span className="card-title">Confidence Gate</span>
            <span style={{ fontSize: 20 }}>🎯</span>
          </div>
          <div className="card-value" style={{ color: 'var(--accent-cyan)' }}>
            {Math.round((config?.confidence_threshold ?? 0.80) * 100)}%
          </div>
          <div className="card-subtitle">min swarm consensus to fire</div>
        </div>
      </div>

      {/* ═══ Paper → Live Trust Pipeline ═══ */}
      {mode === 'paper' && (
        <div className="card" style={{ marginBottom: 20, border: '1px solid var(--warning)' }}>
          <div className="card-header" style={{ marginBottom: 12 }}>
            <span className="card-title">📋 Paper → Live Trust Pipeline</span>
            <span style={{ fontSize: 12, color: 'var(--warning)', fontWeight: 700 }}>
              {status?.paper_trade_count ?? 0} / {status?.paper_trade_required ?? 50} trades
            </span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 10 }}>
            Mandatory paper-trading period before live mode unlocks. Autopilot must demonstrate consistent execution on simulated trades first.
          </div>

          {/* Progress Bar */}
          <div style={{
            width: '100%', height: 28, background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-full)', overflow: 'hidden', position: 'relative',
            border: '1px solid var(--border-secondary)',
          }}>
            <div style={{
              width: `${Math.min(paperProgress, 100)}%`,
              height: '100%',
              background: paperProgress >= 100
                ? 'linear-gradient(90deg, var(--success), #34d399)'
                : 'linear-gradient(90deg, var(--warning), #fbbf24)',
              borderRadius: 'var(--radius-full)',
              transition: 'width 0.5s ease',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ fontSize: 11, fontWeight: 800, color: '#000', textShadow: '0 1px 2px rgba(255,255,255,0.3)' }}>
                {paperProgress.toFixed(0)}%
              </span>
            </div>
          </div>

          {canUnlockLive && (
            <button className="btn btn-primary" onClick={handleUnlockLive} disabled={isLoading}
              style={{ width: '100%', marginTop: 12, fontWeight: 800, background: 'var(--success)', borderColor: 'var(--success)' }}>
              🚀 Unlock Live Trading — Paper Threshold Met!
            </button>
          )}
        </div>
      )}

      {/* ═══ Circuit Breakers ═══ */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header" style={{ marginBottom: 12 }}>
          <span className="card-title">⚡ Circuit Breaker Status</span>
          <span className="badge badge-online">Real-Time</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 8 }}>
          {[
            { name: 'Daily Loss Limit', key: 'daily_loss_breaker', desc: `Max ${config?.daily_max_loss_pct ?? 5}% daily` },
            { name: 'Weekly Loss Limit', key: 'weekly_loss_breaker', desc: `Max ${config?.weekly_max_loss_pct ?? 10}% weekly` },
            { name: 'Max Positions', key: 'max_positions', desc: `Cap: ${config?.max_concurrent_positions ?? 3}` },
            { name: 'Drawdown Guard', key: 'drawdown_guard', desc: 'Recovery level check' },
            { name: 'News Blackout', key: 'news_blackout', desc: '±15min high-impact' },
            { name: 'Performance Drift', key: 'performance_drift', desc: `${config?.drift_threshold_pct ?? 15}% tolerance` },
          ].map(breaker => {
            const isOk = status?.circuit_breakers?.[breaker.key as keyof typeof status.circuit_breakers] ?? true;
            return (
              <div key={breaker.key} style={{
                padding: '10px 12px',
                background: isOk ? 'rgba(16, 185, 129, 0.06)' : 'rgba(239, 68, 68, 0.08)',
                borderRadius: 'var(--radius-md)',
                border: `1px solid ${isOk ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.3)'}`,
                display: 'flex', alignItems: 'center', gap: 10,
              }}>
                <span style={{ fontSize: 18 }}>{isOk ? '🟢' : '🔴'}</span>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>{breaker.name}</div>
                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{breaker.desc}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="section-grid" style={{ marginBottom: 20 }}>
        {/* ═══ Risk Configuration Panel ═══ */}
        <div className="card">
          <div className="card-header" style={{ marginBottom: 14 }}>
            <span className="card-title">⚙️ Risk Configuration</span>
            <button className="btn btn-ghost btn-sm" onClick={() => setShowAdvanced(!showAdvanced)}
              style={{ fontSize: 11, color: 'var(--accent-cyan)' }}>
              {showAdvanced ? 'Hide Advanced' : 'Show Advanced'}
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="input-group">
              <label className="input-label">Confidence Threshold ({editThreshold}%)</label>
              <input className="input" type="range" min={50} max={99} value={editThreshold}
                onChange={(e) => setEditThreshold(parseInt(e.target.value))}
                style={{ accentColor: 'var(--accent-cyan)' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-tertiary)' }}>
                <span>50% (Aggressive)</span><span>99% (Ultra Conservative)</span>
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Risk Per Trade (%)</label>
              <input className="input" type="number" value={editRisk} min={0.1} max={5.0} step={0.1}
                onChange={(e) => setEditRisk(parseFloat(e.target.value) || 1.0)}
                style={{ fontFamily: 'var(--font-mono)' }} />
            </div>

            <div className="input-group">
              <label className="input-label">Max Concurrent Positions</label>
              <input className="input" type="number" value={editMaxPos} min={1} max={20}
                onChange={(e) => setEditMaxPos(parseInt(e.target.value) || 3)} />
            </div>

            {showAdvanced && (
              <>
                <div className="input-group">
                  <label className="input-label">Daily Max Loss (%)</label>
                  <input className="input" type="number" value={editDailyLoss} min={1} max={20} step={0.5}
                    onChange={(e) => setEditDailyLoss(parseFloat(e.target.value) || 5.0)}
                    style={{ fontFamily: 'var(--font-mono)' }} />
                </div>
                <div className="input-group">
                  <label className="input-label">Weekly Max Loss (%)</label>
                  <input className="input" type="number" value={editWeeklyLoss} min={2} max={30} step={0.5}
                    onChange={(e) => setEditWeeklyLoss(parseFloat(e.target.value) || 10.0)}
                    style={{ fontFamily: 'var(--font-mono)' }} />
                </div>
                <div className="input-group">
                  <label className="input-label">Scan Interval (seconds)</label>
                  <input className="input" type="number" value={editInterval} min={10} max={600}
                    onChange={(e) => setEditInterval(parseInt(e.target.value) || 60)} />
                </div>
                <div className="input-group" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <input type="checkbox" checked={editNewsBlackout}
                    onChange={(e) => setEditNewsBlackout(e.target.checked)}
                    style={{ width: 18, height: 18, accentColor: 'var(--accent-cyan)' }} />
                  <label className="input-label" style={{ margin: 0 }}>News Blackout (pause around high-impact events)</label>
                </div>
              </>
            )}

            <button className="btn btn-primary" onClick={handleSaveConfig} disabled={isLoading}
              style={{ width: '100%', fontWeight: 700 }}>
              💾 Save Configuration
            </button>
          </div>
        </div>

        {/* ═══ Per-Instrument Mode Selector ═══ */}
        <div className="card">
          <div className="card-header" style={{ marginBottom: 14 }}>
            <span className="card-title">📊 Instrument Watchlist</span>
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
              {editInstruments.length} active
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {ALL_INSTRUMENTS.map(inst => {
              const isActive = editInstruments.includes(inst);
              const instMode = config?.instrument_modes?.[inst] || 'suggest_only';
              return (
                <div key={inst} style={{
                  padding: '8px 12px',
                  background: isActive ? 'rgba(6, 182, 212, 0.06)' : 'var(--bg-secondary)',
                  borderRadius: 'var(--radius-md)',
                  border: `1px solid ${isActive ? 'rgba(6, 182, 212, 0.2)' : 'var(--border-secondary)'}`,
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <input type="checkbox" checked={isActive}
                      onChange={() => toggleInstrument(inst)}
                      style={{ width: 16, height: 16, accentColor: 'var(--accent-cyan)' }} />
                    <span style={{ fontSize: 12, fontWeight: isActive ? 700 : 400, color: isActive ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>
                      {inst}
                    </span>
                  </div>
                  {isActive && (
                    <select value={instMode} onChange={(e) => handleSetInstrumentMode(inst, e.target.value)}
                      style={{
                        fontSize: 10, padding: '2px 6px', borderRadius: 4,
                        background: instMode === 'autonomous' ? 'rgba(16, 185, 129, 0.15)' : 'var(--bg-card)',
                        border: `1px solid ${instMode === 'autonomous' ? 'var(--success)' : 'var(--border-secondary)'}`,
                        color: instMode === 'autonomous' ? 'var(--success)' : 'var(--text-secondary)',
                        fontWeight: 700,
                      }}>
                      <option value="suggest_only">Suggest Only</option>
                      <option value="autonomous">Autonomous</option>
                    </select>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ═══ Decision Log Feed ═══ */}
      <div className="card">
        <div className="card-header" style={{ marginBottom: 12 }}>
          <span className="card-title">📜 Decision Log Feed</span>
          <span className="badge badge-online">Live</span>
        </div>

        {tradeLog.length === 0 ? (
          <div style={{
            padding: 40, textAlign: 'center', color: 'var(--text-tertiary)',
            background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)',
          }}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>🤖</div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>No decisions yet</div>
            <div style={{ fontSize: 12 }}>Enable Autopilot to start seeing real-time trading decisions here</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 500, overflowY: 'auto' }}>
            {tradeLog.map((d, i) => (
              <div key={i} style={{
                padding: '10px 14px',
                background: d.action === 'executed' ? 'rgba(16, 185, 129, 0.06)' :
                  d.action === 'paper_logged' ? 'rgba(245, 158, 11, 0.06)' : 'var(--bg-secondary)',
                borderRadius: 'var(--radius-md)',
                border: `1px solid ${d.action === 'executed' ? 'rgba(16, 185, 129, 0.2)' :
                  d.action === 'paper_logged' ? 'rgba(245, 158, 11, 0.2)' : 'var(--border-secondary)'}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 14 }}>
                      {d.action === 'executed' ? '🚀' : d.action === 'paper_logged' ? '📝' : '⏭️'}
                    </span>
                    <span style={{ fontWeight: 800, fontSize: 13 }}>{d.instrument}</span>
                    <span style={{
                      fontSize: 10, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
                      color: d.direction === 'buy' ? 'var(--success)' : d.direction === 'sell' ? 'var(--danger)' : 'var(--text-secondary)',
                      background: d.direction === 'buy' ? 'rgba(16, 185, 129, 0.1)' :
                        d.direction === 'sell' ? 'rgba(239, 68, 68, 0.1)' : 'var(--bg-card)',
                      textTransform: 'uppercase',
                    }}>
                      {d.direction}
                    </span>
                    <span style={{ fontSize: 10, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                      {(d.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
                    {formatRelativeTime(d.timestamp)}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                  {d.reason}
                </div>
                {d.lot_size > 0 && (
                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
                    Lot: {d.lot_size} • Entry: {d.entry_price ?? 'Market'} • SL: {d.stop_loss ?? '—'} • TP: {d.take_profit ?? '—'}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <div style={{
        marginTop: 20, padding: '12px 16px',
        background: 'rgba(245, 158, 11, 0.06)', borderRadius: 'var(--radius-md)',
        border: '1px solid rgba(245, 158, 11, 0.15)',
        fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.5,
      }}>
        <strong style={{ color: 'var(--warning)' }}>⚠️ Important:</strong> No trading system can guarantee profits.
        Autopilot executes based on probabilistic AI consensus and risk-managed position sizing.
        Markets are inherently uncertain — always use risk limits you are comfortable with.
        You retain full responsibility for your capital allocation and risk settings.
      </div>
    </div>
  );
}
