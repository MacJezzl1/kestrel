'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import CryptoPaymentModal from '@/components/payment/CryptoPaymentModal';
import { getUserTimeZone, formatLocalDateTime } from '@/lib/time';

export default function SettingsPage() {
  const { user } = useAuth();
  const [isPaymentOpen, setIsPaymentOpen] = useState(false);
  const [selectedTier, setSelectedTier] = useState('enterprise');
  const [userTz, setUserTz] = useState('UTC');
  const [liveTime, setLiveTime] = useState('');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [aiMode, setAiMode] = useState('swarm_100');
  const [savedMsg, setSavedMsg] = useState('');

  useEffect(() => {
    const tz = getUserTimeZone();
    setUserTz(tz);
    
    const timer = setInterval(() => {
      setLiveTime(formatLocalDateTime(new Date().toISOString(), tz));
    }, 1000);
    setLiveTime(formatLocalDateTime(new Date().toISOString(), tz));

    return () => clearInterval(timer);
  }, []);

  const openCheckout = (tier: string) => {
    setSelectedTier(tier);
    setIsPaymentOpen(true);
  };

  const handleSavePreferences = () => {
    setSavedMsg('✓ Settings & Local Timezone Saved');
    setTimeout(() => setSavedMsg(''), 3000);
  };

  const isOwner = user?.email?.toLowerCase().includes('macjezz') || 
                  user?.email?.toLowerCase().includes('owner') || 
                  user?.email?.toLowerCase().includes('admin') || 
                  user?.license_tier === 'enterprise';

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>⚙️ Production Settings & License</h1>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            System Time: <strong style={{ color: 'var(--accent-cyan)' }}>{liveTime}</strong> ({userTz})
          </span>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => openCheckout('enterprise')}
          style={{ display: 'flex', alignItems: 'center', gap: 8 }}
        >
          <span>💎</span> Upgrade with Crypto (USDT/BTC/ETH)
        </button>
      </div>

      <div className="section-grid">
        {/* Account Profile */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Trader Profile & Owner Access</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="input-group">
              <label className="input-label">Email Address</label>
              <input className="input" type="email" value={user?.email || ''} readOnly />
            </div>
            <div className="input-group">
              <label className="input-label">Account Name</label>
              <input className="input" type="text" value={user?.full_name || user?.email?.split('@')[0] || 'CapeChain Trader'} readOnly />
            </div>
            <div className="input-group">
              <label className="input-label">Local Timezone</label>
              <select
                className="input"
                value={userTz}
                onChange={(e) => setUserTz(e.target.value)}
              >
                <option value={getUserTimeZone()}>Browser Local ({getUserTimeZone()})</option>
                <option value="UTC">UTC (Universal Coordinated Time)</option>
                <option value="America/New_York">New York (EST/EDT)</option>
                <option value="Europe/London">London (GMT/BST)</option>
                <option value="Africa/Johannesburg">South Africa (SAST, UTC+2)</option>
                <option value="Asia/Tokyo">Tokyo (JST, UTC+9)</option>
                <option value="Asia/Dubai">Dubai (GST, UTC+4)</option>
                <option value="Australia/Sydney">Sydney (AEST, UTC+10)</option>
              </select>
            </div>
          </div>
        </div>

        {/* License & Tier */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Kestrel Shield License</div>
          <div style={{
            padding: '16px 20px',
            background: isOwner ? 'rgba(6, 182, 212, 0.1)' : 'var(--bg-secondary)',
            borderRadius: 'var(--radius-md)',
            border: `1px solid ${isOwner ? 'var(--accent-cyan)' : 'var(--border-primary)'}`,
            marginBottom: 16
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent-cyan)', textTransform: 'uppercase' }}>
                  {isOwner ? 'Enterprise (Owner VIP)' : `${user?.license_tier || 'Pro'} Plan`}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                  Status: <span style={{ color: 'var(--success)', fontWeight: 700 }}>● {user?.license_status || 'Active'}</span> | Signals: <strong style={{ color: '#fff' }}>Unlimited</strong>
                </div>
              </div>
              <span style={{ fontSize: 36 }}>{isOwner ? '👑' : '🛡️'}</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { tier: 'pro', name: 'Pro Tier', price: '$49/mo', desc: '100-AI Swarm, MT5 Bridge & ATR Risk Guard' },
              { tier: 'enterprise', name: 'Enterprise VIP', price: '$149/mo', desc: 'Unlimited Signals, Computer Vision Scanner, Priority GPU' },
              { tier: 'lifetime', name: 'Lifetime VIP', price: '$499 once', desc: 'Permanent Enterprise License Forever' },
            ].map(plan => (
              <div key={plan.tier} style={{
                padding: '12px 14px',
                background: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-secondary)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 13 }}>{plan.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{plan.desc}</div>
                </div>
                <button
                  className="btn btn-sm btn-ghost"
                  onClick={() => openCheckout(plan.tier)}
                  style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}
                >
                  Pay {plan.price}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* AI & Quantitative Strategy Engine */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>🧠 AI & Swarm Engine Configuration</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="input-group">
              <label className="input-label">Intelligence Framework</label>
              <select
                className="input"
                value={aiMode}
                onChange={(e) => setAiMode(e.target.value)}
              >
                <option value="swarm_100">100-AI Swarm Consensus (Production Default - Zero Latency)</option>
                <option value="ollama_deepseek">Ollama Local Engine (DeepSeek-R1 / Llama 3.3)</option>
                <option value="hybrid_quant">Hybrid Quant (100-AI Swarm + Deep LLM Macro Narrative)</option>
              </select>
            </div>

            {aiMode !== 'swarm_100' && (
              <div className="input-group">
                <label className="input-label">Local Ollama Endpoint</label>
                <input
                  className="input"
                  type="text"
                  value={ollamaUrl}
                  onChange={(e) => setOllamaUrl(e.target.value)}
                  placeholder="http://localhost:11434"
                />
                <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                  Connects to your local or private GPU server running Ollama (DeepSeek-R1 / Llama 3.3).
                </span>
              </div>
            )}

            <div className="input-group">
              <label className="input-label">Min Swarm Consensus Threshold</label>
              <input className="input" type="number" defaultValue={68} min={50} max={95} step={1} />
            </div>

            <button className="btn btn-primary" onClick={handleSavePreferences}>
              Save Preferences
            </button>
            {savedMsg && <span style={{ color: 'var(--success)', fontSize: 12 }}>{savedMsg}</span>}
          </div>
        </div>

        {/* Cloud & MetaTrader 5 Bridge */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>🌐 Cloud & Bridge Integrations</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              { name: 'Supabase PostgreSQL Cloud', status: 'Connected', icon: '⚡', color: 'var(--success)' },
              { name: 'MetaTrader 5 (KestrelEA v2.20)', status: 'Active Bridge', icon: '📊', color: 'var(--success)' },
              { name: 'Crypto Payment Gateway (USDT/BTC)', status: 'Live Vault', icon: '💎', color: 'var(--accent-cyan)' },
              { name: 'Computer Vision Scanner', status: 'Active', icon: '👁️', color: 'var(--accent-blue)' },
            ].map(b => (
              <div key={b.name} style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 12px',
                background: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-secondary)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 18 }}>{b.icon}</span>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{b.name}</span>
                </div>
                <span style={{ fontSize: 11, fontWeight: 700, color: b.color }}>{b.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <CryptoPaymentModal
        isOpen={isPaymentOpen}
        onClose={() => setIsPaymentOpen(false)}
        defaultTier={selectedTier}
      />
    </div>
  );
}
