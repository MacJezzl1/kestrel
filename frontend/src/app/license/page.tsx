'use client';

import { useState } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import MobileNav from '@/components/layout/MobileNav';

export default function LicensePage() {
  const [licenseKey, setLicenseKey] = useState('KST-PRO-773571-992019-X9');
  const [terminalHash, setTerminalHash] = useState('MT5_WIN64_41230754_B89F2A');
  const [accountLogin, setAccountLogin] = useState('41230754');
  const [tier, setTier] = useState<'Starter' | 'Pro' | 'Institutional'>('Pro');
  const [daysRemaining, setDaysRemaining] = useState(28);
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedAdapterSecret, setCopiedAdapterSecret] = useState(false);
  const [isUpgrading, setIsUpgrading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<'pro' | 'institutional'>('pro');

  const adapterSecret = 'kst_sec_99a812df88e104b2c8901844e12';

  const handleCopyKey = () => {
    navigator.clipboard.writeText(licenseKey);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const handleCopySecret = () => {
    navigator.clipboard.writeText(adapterSecret);
    setCopiedAdapterSecret(true);
    setTimeout(() => setCopiedAdapterSecret(false), 2000);
  };

  const handleUnbindTerminal = () => {
    if (confirm('Are you sure you want to unbind this MT5 terminal? The EA will pause trading until rebound.')) {
      setTerminalHash('UNBOUND — Awaiting Next EA Connection');
    }
  };

  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <MobileNav />

        {/* ─── PAGE HEADER ─── */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.5rem' }}>💳</span>
              <h1 style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.02em' }}>License Key &amp; Hardware Binding</h1>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Cryptographically bound terminal license and HMAC-SHA256 credentials for KestrelEA.mq5.
            </p>
          </div>

          <button
            onClick={() => setIsUpgrading(true)}
            style={{
              background: 'linear-gradient(135deg, #00e5ff 0%, #0070f3 100%)',
              border: 'none',
              color: '#05070a',
              padding: '10px 20px',
              borderRadius: '8px',
              fontWeight: 800,
              fontSize: '0.9rem',
              cursor: 'pointer',
              boxShadow: '0 0 20px rgba(0, 229, 255, 0.3)'
            }}
          >
            Upgrade Plan / Renew
          </button>
        </div>

        {/* ─── ACTIVE TIER CARD ─── */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(20, 28, 46, 0.9) 0%, rgba(10, 14, 26, 0.9) 100%)',
          border: '1px solid var(--accent-cyan)',
          borderRadius: '16px',
          padding: '2rem',
          marginBottom: '2rem',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1.5rem'
        }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>
              Active Membership
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>{tier} Quant Desk</span>
              <span style={{ fontSize: '0.75rem', background: 'rgba(0, 229, 255, 0.15)', padding: '2px 8px', borderRadius: '9999px', border: '1px solid var(--accent-cyan)' }}>
                VERIFIED
              </span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Renews automatically via Stripe
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>
              Time Remaining
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#f1f5f9', fontFamily: 'var(--font-mono)' }}>
              {daysRemaining} Days
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--success)' }}>
              Full 180-Agent Swarm Access
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>
              Max Risk Per Trade
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>
              1.0% (Kelly Capped)
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Max Daily Loss Cap: 5.0%
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>
              Allowed Terminals
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--success)', fontFamily: 'var(--font-mono)' }}>
              1 of 3 Used
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              PAMM Copy Engine: ACTIVE
            </div>
          </div>
        </div>

        {/* ─── CREDENTIALS & HARDWARE BINDING ─── */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '1.5rem', marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1.5rem' }}>MT5 EA Installation Credentials</h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '6px' }}>
                1. JWT License Key (Input into KestrelEA: KestrelAPIToken)
              </label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input
                  type="text"
                  readOnly
                  value={licenseKey}
                  style={{ flex: 1, padding: '12px 14px', background: 'var(--bg-input)', border: '1px solid var(--border-secondary)', borderRadius: '8px', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}
                />
                <button
                  onClick={handleCopyKey}
                  style={{ background: 'var(--accent-blue)', color: '#fff', border: 'none', padding: '0 20px', borderRadius: '8px', fontWeight: 700, cursor: 'pointer' }}
                >
                  {copiedKey ? '✓ Copied!' : 'Copy Key'}
                </button>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '6px' }}>
                2. HMAC Adapter Secret (Input into KestrelEA: AdapterSecret)
              </label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input
                  type="password"
                  readOnly
                  value={adapterSecret}
                  style={{ flex: 1, padding: '12px 14px', background: 'var(--bg-input)', border: '1px solid var(--border-secondary)', borderRadius: '8px', color: '#fff', fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}
                />
                <button
                  onClick={handleCopySecret}
                  style={{ background: 'rgba(255, 255, 255, 0.08)', color: '#fff', border: '1px solid var(--border-secondary)', padding: '0 20px', borderRadius: '8px', fontWeight: 700, cursor: 'pointer' }}
                >
                  {copiedAdapterSecret ? '✓ Copied!' : 'Copy Secret'}
                </button>
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--border-secondary)', paddingTop: '1.25rem', marginTop: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>Bound MT5 Terminal Hash</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.95rem', fontWeight: 700, color: '#f1f5f9', marginTop: '4px' }}>
                    {terminalHash}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Primary Account Login: #{accountLogin}
                  </div>
                </div>

                <button
                  onClick={handleUnbindTerminal}
                  style={{ background: 'transparent', border: '1px solid var(--danger)', color: 'var(--danger)', padding: '8px 16px', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }}
                >
                  Unbind Terminal (Reset HWID)
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* ─── UPGRADE MODAL ─── */}
        {isUpgrading && (
          <div
            onClick={() => setIsUpgrading(false)}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 100,
              background: 'rgba(5, 7, 10, 0.85)',
              backdropFilter: 'blur(8px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '1rem'
            }}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-primary)',
                borderRadius: '16px',
                padding: '2.5rem',
                width: '100%',
                maxWidth: '520px',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.8)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Upgrade or Extend License</h3>
                <button onClick={() => setIsUpgrading(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}>✕</button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
                <div
                  onClick={() => setSelectedPlan('pro')}
                  style={{
                    border: selectedPlan === 'pro' ? '2px solid var(--accent-cyan)' : '1px solid var(--border-secondary)',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    cursor: 'pointer',
                    background: selectedPlan === 'pro' ? 'rgba(0, 229, 255, 0.05)' : 'transparent'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700 }}>
                    <span>Pro Quant Desk</span>
                    <span style={{ color: 'var(--accent-cyan)' }}>$249 / month</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    3 MT5 terminals, 180-agent swarm, prop firm shield, PAMM copier.
                  </div>
                </div>

                <div
                  onClick={() => setSelectedPlan('institutional')}
                  style={{
                    border: selectedPlan === 'institutional' ? '2px solid var(--accent-cyan)' : '1px solid var(--border-secondary)',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    cursor: 'pointer',
                    background: selectedPlan === 'institutional' ? 'rgba(0, 229, 255, 0.05)' : 'transparent'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700 }}>
                    <span>Institutional Enterprise</span>
                    <span style={{ color: 'var(--accent-cyan)' }}>$799 / month</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    Unlimited terminals, dedicated VPC bridge, custom regime ML models.
                  </div>
                </div>
              </div>

              <button
                onClick={() => {
                  alert(`Redirecting to Stripe Checkout for ${selectedPlan.toUpperCase()} plan...`);
                  setIsUpgrading(false);
                }}
                style={{
                  width: '100%',
                  background: 'linear-gradient(135deg, #00e5ff 0%, #0070f3 100%)',
                  border: 'none',
                  color: '#05070a',
                  padding: '14px',
                  borderRadius: '8px',
                  fontWeight: 800,
                  fontSize: '1rem',
                  cursor: 'pointer',
                  boxShadow: '0 0 20px rgba(0, 229, 255, 0.4)'
                }}
              >
                Proceed to Secure Checkout →
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
