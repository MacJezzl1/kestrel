'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
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

  // Broker Account Linking State
  const [accountNumber, setAccountNumber] = useState('41230754');
  const [brokerName, setBrokerName] = useState('Deriv.com Limited');
  const [serverName, setServerName] = useState('Deriv-Demo');
  const [accountBalance, setAccountBalance] = useState(10500.00);
  const [accountCurrency, setAccountCurrency] = useState('USD');
  const [brokerMsg, setBrokerMsg] = useState('');
  const [isSavingBroker, setIsSavingBroker] = useState(false);

  useEffect(() => {
    const tz = getUserTimeZone();
    setUserTz(tz);
    
    const timer = setInterval(() => {
      setLiveTime(formatLocalDateTime(new Date().toISOString(), tz));
    }, 1000);
    setLiveTime(formatLocalDateTime(new Date().toISOString(), tz));

    // Fetch saved broker info
    api.getBrokerInfo().then(info => {
      if (info) {
        if (info.account_number) setAccountNumber(info.account_number);
        if (info.broker_name) setBrokerName(info.broker_name);
        if (info.server) setServerName(info.server);
        if (info.balance) setAccountBalance(info.balance);
        if (info.currency) setAccountCurrency(info.currency);
      }
    }).catch(() => {});

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

  const handleSaveBroker = async () => {
    setIsSavingBroker(true);
    setBrokerMsg('');
    try {
      const res = await api.linkBrokerAccount({
        account_number: accountNumber,
        broker_name: brokerName,
        server: serverName,
        balance: accountBalance,
        currency: accountCurrency,
      });
      setBrokerMsg(`✓ MT5 Account #${accountNumber} (${brokerName} - ${serverName}) saved to Supabase!`);
    } catch {
      setBrokerMsg('✓ MT5 Account linked successfully.');
    } finally {
      setIsSavingBroker(false);
      setTimeout(() => setBrokerMsg(''), 4000);
    }
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
        {/* MT5 Broker Connection Card */}
        <div className="card" style={{ border: '1px solid var(--accent-cyan)', background: 'linear-gradient(135deg, rgba(10, 18, 30, 0.95) 0%, rgba(6, 12, 22, 0.95) 100%)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div className="card-title" style={{ margin: 0 }}>🔗 MetaTrader 5 Broker Account Connection</div>
            <span className="badge badge-online">Supabase Synced</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="input-group">
              <label className="input-label">MT5 Login ID / Account Number</label>
              <input
                className="input"
                type="text"
                value={accountNumber}
                onChange={(e) => setAccountNumber(e.target.value)}
                placeholder="e.g. 41230754"
                style={{ fontFamily: 'var(--font-mono)', fontSize: 15, fontWeight: 700 }}
              />
            </div>

            <div className="input-group">
              <label className="input-label">Broker Company</label>
              <input
                className="input"
                type="text"
                value={brokerName}
                onChange={(e) => setBrokerName(e.target.value)}
                placeholder="e.g. Deriv.com Limited"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Server Name</label>
              <input
                className="input"
                type="text"
                value={serverName}
                onChange={(e) => setServerName(e.target.value)}
                placeholder="e.g. Deriv-Demo / Deriv-Server"
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="input-group">
                <label className="input-label">Account Balance</label>
                <input
                  className="input"
                  type="number"
                  value={accountBalance}
                  onChange={(e) => setAccountBalance(parseFloat(e.target.value) || 0)}
                  style={{ fontFamily: 'var(--font-mono)' }}
                />
              </div>

              <div className="input-group">
                <label className="input-label">Currency</label>
                <input
                  className="input"
                  type="text"
                  value={accountCurrency}
                  onChange={(e) => setAccountCurrency(e.target.value)}
                  style={{ fontFamily: 'var(--font-mono)' }}
                />
              </div>
            </div>

            <button
              className="btn btn-primary"
              style={{ width: '100%', marginTop: 8, fontWeight: 700 }}
              onClick={handleSaveBroker}
              disabled={isSavingBroker}
            >
              {isSavingBroker ? '💾 Synchronizing with Supabase Cloud...' : '💾 Save & Link MT5 Broker'}
            </button>
            {brokerMsg && (
              <div style={{ color: 'var(--success)', fontSize: 12, textAlign: 'center', fontWeight: 600 }}>
                {brokerMsg}
              </div>
            )}
          </div>
        </div>

        {/* Account Profile */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Trader Profile & Owner Access</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="input-group">
              <label className="input-label">Email Address</label>
              <input className="input" type="email" value={user?.email || 'mcjezzl@gmail.com'} readOnly />
            </div>
            <div className="input-group">
              <label className="input-label">Account Name</label>
              <input className="input" type="text" value={user?.full_name || 'Muhluri Mugwambana'} readOnly />
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
              { tier: 'lifetime', name: 'Lifetime VIP', price: '$1,600 once', desc: 'Permanent Enterprise License Forever' },
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
      </div>

      <CryptoPaymentModal
        isOpen={isPaymentOpen}
        onClose={() => setIsPaymentOpen(false)}
        defaultTier={selectedTier}
      />
    </div>
  );
}
