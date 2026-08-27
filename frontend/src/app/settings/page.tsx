'use client';

import { useAuth } from '@/lib/auth';

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>⚙️ Settings</h1>

      <div className="section-grid">
        {/* Account */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Account</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="input-group">
              <label className="input-label">Email</label>
              <input className="input" type="email" value={user?.email || ''} readOnly />
            </div>
            <div className="input-group">
              <label className="input-label">Full Name</label>
              <input className="input" type="text" value={user?.full_name || ''} placeholder="Not set" readOnly />
            </div>
            <div className="input-group">
              <label className="input-label">Account Created</label>
              <input className="input" type="text" value={user?.created_at ? new Date(user.created_at).toLocaleDateString() : ''} readOnly />
            </div>
          </div>
        </div>

        {/* License */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>License — Kestrel Shield</div>
          <div style={{ padding: '16px 20px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-primary)', marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-blue)', textTransform: 'uppercase' }}>
                  {user?.license_tier || 'Free'} Plan
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>
                  Status: <span style={{ color: 'var(--success)' }}>{user?.license_status || 'Active'}</span>
                </div>
              </div>
              <span style={{ fontSize: 32 }}>🛡️</span>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { tier: 'Free', price: '$0/mo', features: '10 signals/day, Basic dashboard' },
              { tier: 'Pro', price: '$49/mo', features: '100 signals/day, Full analytics, Vision' },
              { tier: 'Enterprise', price: '$199/mo', features: 'Unlimited signals, Priority API, Audit export' },
            ].map(plan => (
              <div key={plan.tier} style={{
                padding: '12px 16px',
                background: plan.tier.toLowerCase() === user?.license_tier ? 'var(--accent-blue-soft)' : 'var(--bg-secondary)',
                borderRadius: 'var(--radius-md)',
                border: `1px solid ${plan.tier.toLowerCase() === user?.license_tier ? 'var(--accent-blue)' : 'var(--border-secondary)'}`,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{plan.tier}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{plan.features}</div>
                </div>
                <div style={{ fontWeight: 700, color: 'var(--accent-blue)', fontFamily: 'var(--font-mono)' }}>
                  {plan.price}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Trading Preferences */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Trading Preferences</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="input-group">
              <label className="input-label">Risk per Trade (%)</label>
              <input className="input" type="number" defaultValue={1} min={0.1} max={5} step={0.1} />
            </div>
            <div className="input-group">
              <label className="input-label">Max Drawdown Guard (%)</label>
              <input className="input" type="number" defaultValue={10} min={5} max={50} step={1} />
            </div>
            <div className="input-group">
              <label className="input-label">Min Signal Confidence (%)</label>
              <input className="input" type="number" defaultValue={65} min={50} max={95} step={5} />
            </div>
            <button className="btn btn-primary" style={{ marginTop: 8 }}>Save Preferences</button>
          </div>
        </div>

        {/* API & Bridge */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Bridge Connections</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { name: 'MT5 Bridge', status: 'connected', icon: '📊' },
              { name: 'TradingView', status: 'not configured', icon: '📺' },
              { name: 'Crypto (ccxt)', status: 'not configured', icon: '🪙' },
              { name: 'OANDA', status: 'not configured', icon: '🏦' },
            ].map(bridge => (
              <div key={bridge.name} style={{
                padding: '12px 16px',
                background: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-secondary)',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span>{bridge.icon}</span>
                  <span style={{ fontWeight: 500 }}>{bridge.name}</span>
                </div>
                <span className={`badge ${bridge.status === 'connected' ? 'badge-online' : ''}`} style={{
                  background: bridge.status !== 'connected' ? 'var(--bg-card)' : undefined,
                  color: bridge.status !== 'connected' ? 'var(--text-muted)' : undefined,
                  border: bridge.status !== 'connected' ? '1px solid var(--border-secondary)' : undefined,
                }}>
                  {bridge.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
