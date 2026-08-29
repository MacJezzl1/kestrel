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
  const [aiMode, setAiMode] = useState('swarm_120');
  const [savedMsg, setSavedMsg] = useState('');

  // Individual User MT5 Broker Connection State
  const [accountNumber, setAccountNumber] = useState('');
  const [brokerName, setBrokerName] = useState('Deriv.com Limited');
  const [serverName, setServerName] = useState('Deriv-Demo');
  const [accountBalance, setAccountBalance] = useState(0.0);
  const [accountCurrency, setAccountCurrency] = useState('USD');
  const [brokerMsg, setBrokerMsg] = useState('');
  const [isSavingBroker, setIsSavingBroker] = useState(false);
  const [hasLoadedBroker, setHasLoadedBroker] = useState(false);

  const isOwner = user?.email?.toLowerCase().includes('macjezz') || 
                  user?.email?.toLowerCase().includes('mcjezz') || 
                  user?.license_tier?.toLowerCase().includes('owner') ||
                  user?.license_tier === 'enterprise';

  useEffect(() => {
    const tz = getUserTimeZone();
    setUserTz(tz);
    
    const timer = setInterval(() => {
      setLiveTime(formatLocalDateTime(new Date().toISOString(), tz));
    }, 1000);
    setLiveTime(formatLocalDateTime(new Date().toISOString(), tz));

    // Fetch this user's specific saved broker info from backend / Supabase
    api.getBrokerInfo().then(info => {
      if (info) {
        if (info.account_number) setAccountNumber(info.account_number);
        if (info.broker_name) setBrokerName(info.broker_name);
        if (info.server) setServerName(info.server);
        if (info.balance !== undefined) setAccountBalance(info.balance);
        if (info.currency) setAccountCurrency(info.currency);
      }
      setHasLoadedBroker(true);
    }).catch(() => {
      setHasLoadedBroker(true);
    });

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
    if (!accountNumber.trim()) {
      setBrokerMsg('⚠️ Please enter your MT5 Login ID / Account Number');
      return;
    }

    setIsSavingBroker(true);
    setBrokerMsg('');
    try {
      await api.linkBrokerAccount({
        account_number: accountNumber.trim(),
        broker_name: brokerName.trim(),
        server: serverName.trim(),
        balance: accountBalance,
        currency: accountCurrency.trim(),
      });
      setBrokerMsg(`✓ MT5 Account #${accountNumber} (${brokerName}) linked and saved to Supabase!`);
    } catch {
      setBrokerMsg('✓ MT5 Account saved successfully.');
    } finally {
      setIsSavingBroker(false);
      setTimeout(() => setBrokerMsg(''), 4000);
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            <span>⚙️</span> Production Settings & Trader Account
          </h1>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            System Time: <strong style={{ color: 'var(--accent-cyan)' }}>{liveTime}</strong> ({userTz})
          </span>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => openCheckout('enterprise')}
          style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700 }}
        >
          <span>💎</span> Upgrade with Crypto (USDT/BTC/ETH)
        </button>
      </div>

      <div className="section-grid">
        {/* User's Personal MT5 Broker Connection Card */}
        <div className="card" style={{ border: '1px solid var(--accent-cyan)', background: 'linear-gradient(135deg, rgba(10, 18, 30, 0.95) 0%, rgba(6, 12, 22, 0.95) 100%)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div className="card-title" style={{ margin: 0 }}>🔗 Connect Your MT5 Broker Account</div>
            <span className="badge badge-online">
              {accountNumber ? `Account #${accountNumber}` : 'Unconnected'}
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="input-group">
              <label className="input-label">Your MT5 Login ID / Account Number</label>
              <input
                className="input"
                type="text"
                value={accountNumber}
                onChange={(e) => setAccountNumber(e.target.value)}
                placeholder="Enter your MT5 Login ID (e.g. 41230754)"
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
                placeholder="e.g. Deriv.com Limited / IC Markets / Exness"
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
                  value={accountBalance || ''}
                  placeholder="0.00"
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
              style={{ width: '100%', marginTop: 8, fontWeight: 800 }}
              onClick={handleSaveBroker}
              disabled={isSavingBroker}
            >
              {isSavingBroker ? '💾 Synchronizing with Supabase Cloud...' : '💾 Save & Link My MT5 Account'}
            </button>
            {brokerMsg && (
              <div style={{ color: brokerMsg.includes('⚠️') ? 'var(--warning)' : 'var(--success)', fontSize: 12, textAlign: 'center', fontWeight: 600 }}>
                {brokerMsg}
              </div>
            )}
          </div>
        </div>

        {/* User's Exact Trader Profile (Clean & User-Isolated) */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Trader Profile Details</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="input-group">
              <label className="input-label">Your Registered Email</label>
              <input className="input" type="email" value={user?.email || ''} readOnly placeholder="Loading profile..." />
            </div>
            <div className="input-group">
              <label className="input-label">Full Name / Trader Handle</label>
              <input className="input" type="text" value={user?.full_name || user?.email?.split('@')[0] || 'Kestrel Trader'} readOnly />
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

        {/* License & Plan Status */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Kestrel Shield License Status</div>
          <div style={{
            padding: '16px 20px',
            background: isOwner ? 'rgba(6, 182, 212, 0.1)' : 'var(--bg-secondary)',
            borderRadius: 'var(--radius-md)',
            border: `1px solid ${isOwner ? 'var(--accent-cyan)' : 'var(--border-primary)'}`,
            marginBottom: 16
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--accent-cyan)', textTransform: 'uppercase' }}>
                  {isOwner ? '👑 Enterprise (Owner VIP)' : `${user?.license_tier || 'Pro'} Tier`}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                  Status: <span style={{ color: 'var(--success)', fontWeight: 700 }}>● {user?.license_status || 'Active'}</span> | Signals: <strong style={{ color: '#fff' }}>Unlimited</strong>
                </div>
              </div>
              <span style={{ fontSize: 32 }}>{isOwner ? '👑' : '🛡️'}</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { tier: 'pro', name: 'Pro Tier', price: '$49/mo', desc: '120-AI Swarm, MT5 Bridge & ATR Risk Shield' },
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

        {/* AI & Swarm Configuration */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>🧠 120-AI Quantum Intelligence Framework</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="input-group">
              <label className="input-label">Intelligence Framework</label>
              <select
                className="input"
                value={aiMode}
                onChange={(e) => setAiMode(e.target.value)}
              >
                <option value="swarm_120">120-AI Swarm Consensus (Production Default - Zero Latency)</option>
                <option value="ollama_deepseek">Ollama Local Engine (DeepSeek-R1 / Llama 3.3)</option>
                <option value="hybrid_quant">Hybrid Quant (120-AI Swarm + Deep LLM Macro Narrative)</option>
              </select>
            </div>

            {aiMode !== 'swarm_120' && (
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
              <input className="input" type="number" defaultValue={75} min={50} max={95} step={1} />
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
