'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { ApiError } from '@/lib/api';

export default function LandingPage() {
  const { login, register, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  // Auth Modal State
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  // Redirect if already authenticated
  if (!isLoading && isAuthenticated) {
    router.push('/dashboard');
    return null;
  }

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setAuthLoading(true);

    try {
      if (isRegister) {
        await register(email, password, fullName || undefined);
      } else {
        await login(email, password);
      }
      router.push('/dashboard');
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message || 'Connection failed.');
      } else {
        setError('Connection failed. Please retry.');
      }
    } finally {
      setAuthLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)' }}>
      {/* ─── TOP INSTITUTIONAL NAVIGATION BAR ─── */}
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        backdropFilter: 'blur(16px)',
        background: 'rgba(6, 10, 20, 0.85)',
        borderBottom: '1px solid var(--border-primary)',
        padding: '0 2rem',
        height: '68px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <img src="/kestrel-logo.jpg" alt="Kestrel" style={{ width: 36, height: 36, borderRadius: 8, border: '1px solid var(--accent-cyan)' }} />
          <div>
            <div style={{ fontWeight: 800, fontSize: '1.25rem', letterSpacing: '-0.02em', background: 'linear-gradient(135deg, #f1f5f9 0%, #00e5ff 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              KESTREL
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Autonomous Quant Trading v4.0
            </div>
          </div>
        </div>

        <nav style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <a href="#features" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500, transition: 'color 0.2s' }}>Features</a>
          <a href="#performance" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>Live Metrics</a>
          <a href="#prop-firm" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>Prop-Firm Shield</a>
          <a href="#pricing" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>Tiers</a>
          <Link href="/backtest" style={{ color: 'var(--accent-cyan)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600 }}>🧪 Backtest Sim</Link>
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={() => { setIsRegister(false); setAuthModalOpen(true); }}
            style={{
              background: 'transparent',
              border: '1px solid var(--border-secondary)',
              color: 'var(--text-primary)',
              padding: '8px 18px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            Terminal Sign In
          </button>
          <button
            onClick={() => { setIsRegister(true); setAuthModalOpen(true); }}
            style={{
              background: 'linear-gradient(135deg, #00e5ff 0%, #0070f3 100%)',
              border: 'none',
              color: '#05070a',
              padding: '8px 20px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 0 20px rgba(0, 229, 255, 0.3)',
              transition: 'all 0.2s'
            }}
          >
            Claim 7-Day Trial
          </button>
        </div>
      </header>

      {/* ─── HERO SECTION ─── */}
      <section style={{ maxWidth: '1280px', margin: '0 auto', padding: '5rem 2rem 3rem', textAlign: 'center' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(0, 229, 255, 0.08)',
          border: '1px solid rgba(0, 229, 255, 0.25)',
          padding: '6px 16px',
          borderRadius: '9999px',
          fontSize: '0.8rem',
          color: 'var(--accent-cyan)',
          fontWeight: 600,
          marginBottom: '2rem'
        }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#00e676', boxShadow: '0 0 10px #00e676' }} />
          INSTITUTIONAL QUANT SYSTEM v4.0 ACTIVE • 180-AGENT SWARM
        </div>

        <h1 style={{
          fontSize: 'clamp(2.5rem, 5vw, 4.2rem)',
          fontWeight: 900,
          letterSpacing: '-0.03em',
          lineHeight: 1.1,
          maxWidth: '960px',
          margin: '0 auto 1.5rem',
          background: 'linear-gradient(180deg, #ffffff 30%, #94a3b8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          Algorithmic Alpha for Prop Desks & Institutional Capital
        </h1>

        <p style={{
          fontSize: '1.2rem',
          color: 'var(--text-secondary)',
          maxWidth: '740px',
          margin: '0 auto 2.5rem',
          lineHeight: 1.6
        }}>
          Multi-dimensional technical confluence, adaptive Hurst regime switching, Smart Money Concepts (SMC), and strict prop-firm drawdown rules. Connects directly to MT5 in milliseconds.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap', marginBottom: '4rem' }}>
          <button
            onClick={() => { setIsRegister(true); setAuthModalOpen(true); }}
            style={{
              background: 'linear-gradient(135deg, #00e5ff 0%, #0070f3 100%)',
              border: 'none',
              color: '#05070a',
              padding: '14px 32px',
              borderRadius: '10px',
              fontSize: '1.05rem',
              fontWeight: 800,
              cursor: 'pointer',
              boxShadow: '0 0 30px rgba(0, 229, 255, 0.35)',
              transition: 'transform 0.2s'
            }}
          >
            Launch Live Cockpit →
          </button>
          <Link
            href="/backtest"
            style={{
              background: 'rgba(20, 28, 46, 0.8)',
              border: '1px solid var(--border-primary)',
              color: 'var(--text-primary)',
              padding: '14px 28px',
              borderRadius: '10px',
              fontSize: '1.05rem',
              fontWeight: 600,
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <span>Explore 5-Year Backtest</span> 🧪
          </Link>
        </div>

        {/* ─── LIVE METRICS RIBBON ─── */}
        <div id="performance" style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1.5rem',
          background: 'rgba(15, 23, 42, 0.65)',
          border: '1px solid var(--border-primary)',
          borderRadius: '16px',
          padding: '2rem',
          backdropFilter: 'blur(12px)',
          textAlign: 'left'
        }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, marginBottom: 4 }}>Verified Win Rate</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--success)', fontFamily: 'var(--font-mono)' }}>73.4%</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Over 4,820 live trades</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, marginBottom: 4 }}>Profit Factor</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>2.42</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Gross Wins / Gross Losses</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, marginBottom: 4 }}>Max Recorded Drawdown</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>3.8%</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Prop Limit Buffer &gt; 50%</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, marginBottom: 4 }}>Sharpe Ratio</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#a855f7', fontFamily: 'var(--font-mono)' }}>2.85</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Annualized risk-adjusted</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, marginBottom: 4 }}>Execution Latency</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--success)', fontFamily: 'var(--font-mono)' }}>&lt; 14ms</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Direct MT5 WebRequest bridge</div>
          </div>
        </div>
      </section>

      {/* ─── INSTITUTIONAL CAPABILITIES ─── */}
      <section id="features" style={{ maxWidth: '1280px', margin: '4rem auto', padding: '0 2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.75rem' }}>Engineered Without Compromise</h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
            Built specifically to pass and preserve high-tier prop challenges (FTMO, MFF, The 5%ers, Equity Edge).
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '2rem' }}>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '2rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🤖</div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.75rem' }}>180-Agent Swarm Intelligence</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6 }}>
              Decentralized consensus engine polling trend momentum, volatility dispersion, order flow imbalances, and higher-timeframe structural breaks before dispatching trade orders.
            </p>
          </div>

          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '2rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🌐</div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.75rem' }}>Adaptive Regime Switcher</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6 }}>
              Rolling 200-bar Hurst Exponent ($H$) dynamically classifies market states into Persistent Trending ($H &gt; 0.55$), Mean-Reversion ($H &lt; 0.45$), or Random Walk Noise.
            </p>
          </div>

          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '2rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🦅</div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.75rem' }}>Smart Money Concepts (SMC)</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6 }}>
              Algorithmic order block mitigation tracking, 50% discount fair value gap (FVG) fills, institutional liquidity sweeps (&gt; 1.5x ATR rejection wicks), and multi-TF BOS/CHoCH alignment.
            </p>
          </div>

          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '2rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🛡️</div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.75rem' }}>Prop-Firm Rules & Circuit Breaker</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6 }}>
              Automated 00:00 midnight daily reset, max daily loss & total drawdown guard with a 0.5% safety threshold buffer. Closes all trades instantly if drawdown limits are approached.
            </p>
          </div>

          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '2rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📰</div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.75rem' }}>Macro News & Volatility Guard</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6 }}>
              Direct bridge to high-impact economic calendar events. Locks entry 30 minutes before/after major macro releases (CPI, NFP, FOMC) and tightens existing profitable stop losses to Break-Even.
            </p>
          </div>

          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: '16px', padding: '2rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🔄</div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.75rem' }}>Multi-Client PAMM Copier</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6 }}>
              Master-to-client sub-second execution broadcast. Mirror trades across unlimited accounts with custom risk multipliers, independent equity caps, and automated slippage tracking.
            </p>
          </div>
        </div>
      </section>

      {/* ─── PRICING TIERS ─── */}
      <section id="pricing" style={{ maxWidth: '1280px', margin: '5rem auto', padding: '0 2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.75rem' }}>Transparent Quantitative Tiers</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Instant license activation. All plans include 7-day trial and hardware-bound terminal key.</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2rem' }}>
          {/* Starter */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-secondary)', borderRadius: '16px', padding: '2.5rem', display: 'flex', flexDirection: 'column' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.5rem' }}>Starter Trader</div>
            <div style={{ fontSize: '2.8rem', fontWeight: 900, marginBottom: '1rem', fontFamily: 'var(--font-mono)' }}>$99<span style={{ fontSize: '1rem', color: 'var(--text-tertiary)', fontWeight: 400 }}>/month</span></div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '2rem' }}>For individual retail traders running a single MT5 account.</p>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 2rem', color: 'var(--text-secondary)', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <li>✓ 1 MT5 Terminal License</li>
              <li>✓ Standard Confluence Indicators (8 Models)</li>
              <li>✓ Adaptive ATR Stop Loss &amp; 3-Tier TP</li>
              <li>✓ Web Dashboard Access</li>
              <li style={{ color: 'var(--text-muted)' }}>✗ Prop-Firm Challenge Rules</li>
              <li style={{ color: 'var(--text-muted)' }}>✗ PAMM Copy Receiver</li>
            </ul>
            <button
              onClick={() => { setIsRegister(true); setAuthModalOpen(true); }}
              style={{ marginTop: 'auto', background: 'rgba(255,255,255,0.06)', border: '1px solid var(--border-secondary)', color: '#fff', padding: '12px', borderRadius: '8px', fontWeight: 700, cursor: 'pointer' }}
            >
              Get Started
            </button>
          </div>

          {/* Pro (Highlighted) */}
          <div style={{
            background: 'linear-gradient(180deg, rgba(20, 28, 46, 0.95) 0%, rgba(10, 14, 26, 0.95) 100%)',
            border: '2px solid var(--accent-cyan)',
            borderRadius: '16px',
            padding: '2.5rem',
            display: 'flex',
            flexDirection: 'column',
            position: 'relative',
            boxShadow: '0 0 35px rgba(0, 229, 255, 0.2)'
          }}>
            <div style={{
              position: 'absolute',
              top: '-12px',
              left: '50%',
              transform: 'translateX(-50%)',
              background: 'linear-gradient(90deg, #00e5ff 0%, #0070f3 100%)',
              color: '#05070a',
              fontSize: '0.75rem',
              fontWeight: 800,
              padding: '4px 14px',
              borderRadius: '9999px',
              letterSpacing: '0.05em'
            }}>
              MOST POPULAR • FUNDED CHOICE
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.5rem' }}>Pro Quant Desk</div>
            <div style={{ fontSize: '2.8rem', fontWeight: 900, marginBottom: '1rem', fontFamily: 'var(--font-mono)' }}>$249<span style={{ fontSize: '1rem', color: 'var(--text-tertiary)', fontWeight: 400 }}>/month</span></div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '2rem' }}>Full institutional capabilities for funded prop traders.</p>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 2rem', color: 'var(--text-secondary)', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <li>✓ 3 Bound MT5 Terminals</li>
              <li>✓ 180-Agent Swarm Intelligence</li>
              <li>✓ Full Prop-Firm Rules Engine (FTMO/MFF/The5ers)</li>
              <li>✓ Adaptive Hurst Regime Switcher</li>
              <li>✓ Smart Money Concepts (SMC) Engine</li>
              <li>✓ Macro News &amp; Volatility Guard Lock</li>
              <li>✓ PAMM Copy Trading Receiver (Up to 5 accounts)</li>
            </ul>
            <button
              onClick={() => { setIsRegister(true); setAuthModalOpen(true); }}
              style={{ marginTop: 'auto', background: 'linear-gradient(135deg, #00e5ff 0%, #0070f3 100%)', border: 'none', color: '#05070a', padding: '12px', borderRadius: '8px', fontWeight: 800, cursor: 'pointer', boxShadow: '0 0 20px rgba(0, 229, 255, 0.4)' }}
            >
              Start 7-Day Pro Trial
            </button>
          </div>

          {/* Institutional */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-secondary)', borderRadius: '16px', padding: '2.5rem', display: 'flex', flexDirection: 'column' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.5rem' }}>Institutional Enterprise</div>
            <div style={{ fontSize: '2.8rem', fontWeight: 900, marginBottom: '1rem', fontFamily: 'var(--font-mono)' }}>$799<span style={{ fontSize: '1rem', color: 'var(--text-tertiary)', fontWeight: 400 }}>/month</span></div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '2rem' }}>For prop trading firms, hedge funds, and asset managers.</p>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 2rem', color: 'var(--text-secondary)', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <li>✓ Unlimited MT5 &amp; cTrader Terminals</li>
              <li>✓ Unlimited Master-Receiver Copy Grid</li>
              <li>✓ Custom Machine Learning Regime Models</li>
              <li>✓ Dedicated VPC Deployment &amp; Sub-millisecond Bridge</li>
              <li>✓ Custom Circuit Breaker Sizing Algorithms</li>
              <li>✓ 24/7 Dedicated SLA &amp; Quant Engineer Support</li>
            </ul>
            <button
              onClick={() => { setIsRegister(true); setAuthModalOpen(true); }}
              style={{ marginTop: 'auto', background: 'rgba(255,255,255,0.06)', border: '1px solid var(--border-secondary)', color: '#fff', padding: '12px', borderRadius: '8px', fontWeight: 700, cursor: 'pointer' }}
            >
              Contact Desk Sales
            </button>
          </div>
        </div>
      </section>

      {/* ─── FOOTER ─── */}
      <footer style={{ borderTop: '1px solid var(--border-primary)', padding: '3rem 2rem', background: 'var(--bg-secondary)', color: 'var(--text-tertiary)', fontSize: '0.85rem' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>KESTREL QUANTITATIVE PLATFORM v4.0</div>
            <div>CapeChain Labs © 2026. All rights reserved. High risk investment warning applies.</div>
          </div>
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <Link href="/security" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Security</Link>
            <Link href="/backtest" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Backtest</Link>
            <a href="/Kestrel_Quantum_Trading_Intelligence.pdf" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-cyan)', textDecoration: 'none' }}>Deck (PDF)</a>
          </div>
        </div>
      </footer>

      {/* ─── MODAL LOGIN / REGISTER ─── */}
      {authModalOpen && (
        <div
          onClick={() => setAuthModalOpen(false)}
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
              maxWidth: '440px',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.8)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <img src="/kestrel-logo.jpg" alt="Kestrel" style={{ width: 32, height: 32, borderRadius: 6 }} />
                <span style={{ fontWeight: 800, fontSize: '1.1rem' }}>{isRegister ? 'Create Quant Account' : 'Terminal Sign In'}</span>
              </div>
              <button onClick={() => setAuthModalOpen(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}>✕</button>
            </div>

            {error && (
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger)', color: 'var(--danger)', padding: '10px 14px', borderRadius: '8px', fontSize: '0.85rem', marginBottom: '1rem' }}>
                {error}
              </div>
            )}

            <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {isRegister && (
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Full Name</label>
                  <input
                    type="text"
                    required
                    placeholder="Jane Doe"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    style={{ width: '100%', padding: '10px 14px', background: 'var(--bg-input)', border: '1px solid var(--border-secondary)', borderRadius: '8px', color: '#fff', fontSize: '0.9rem' }}
                  />
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="trader@hedgefund.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{ width: '100%', padding: '10px 14px', background: 'var(--bg-input)', border: '1px solid var(--border-secondary)', borderRadius: '8px', color: '#fff', fontSize: '0.9rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Master Password</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{ width: '100%', padding: '10px 14px', background: 'var(--bg-input)', border: '1px solid var(--border-secondary)', borderRadius: '8px', color: '#fff', fontSize: '0.9rem' }}
                />
              </div>

              <button
                type="submit"
                disabled={authLoading}
                style={{
                  background: 'linear-gradient(135deg, #00e5ff 0%, #0070f3 100%)',
                  border: 'none',
                  color: '#05070a',
                  padding: '12px',
                  borderRadius: '8px',
                  fontWeight: 800,
                  fontSize: '0.95rem',
                  cursor: authLoading ? 'wait' : 'pointer',
                  marginTop: '0.5rem'
                }}
              >
                {authLoading ? 'Authenticating...' : (isRegister ? 'Start 7-Day Trial' : 'Sign In to Cockpit')}
              </button>
            </form>

            <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-tertiary)' }}>
              {isRegister ? (
                <span>Already have a terminal key? <button onClick={() => { setIsRegister(false); setError(''); }} style={{ background: 'transparent', border: 'none', color: 'var(--accent-cyan)', fontWeight: 600, cursor: 'pointer' }}>Sign In</button></span>
              ) : (
                <span>Need a prop-firm license? <button onClick={() => { setIsRegister(true); setError(''); }} style={{ background: 'transparent', border: 'none', color: 'var(--accent-cyan)', fontWeight: 600, cursor: 'pointer' }}>Start 7-Day Trial</button></span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
