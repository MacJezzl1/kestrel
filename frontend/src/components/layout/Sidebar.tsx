'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import AiChatDrawer from '@/components/AiChatDrawer';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/autopilot', label: 'Autopilot', icon: '🤖' },
  { href: '/terminal', label: 'AI Sniper Live', icon: '🎯' },
  { href: '/clients', label: 'Client Hub (5)', icon: '👥' },
  { href: '/signals', label: 'Signals', icon: '📡' },
  { href: '/trades', label: 'Trade History', icon: '📋' },
  { href: '/analysis', label: 'Analysis', icon: '🔬' },
  { href: '/vision', label: 'Chart Vision', icon: '👁️' },
];

const bottomItems = [
  { href: '/security', label: 'Security', icon: '🔐' },
  { href: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [aiDrawerOpen, setAiDrawerOpen] = useState(false);


  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <img src="/kestrel-logo.jpg" alt="Kestrel" className="sidebar-logo" />
        <div className="sidebar-brand">
          <h1>Kestrel</h1>
          <span>CapeChain Labs</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Intelligence</div>
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-item ${pathname === item.href ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </Link>
        ))}

        <button
          onClick={() => setAiDrawerOpen(true)}
          className="nav-item"
          style={{
            background: 'linear-gradient(90deg, rgba(0, 240, 255, 0.15) 0%, rgba(0, 112, 243, 0.05) 100%)',
            border: '1px solid rgba(0, 240, 255, 0.3)',
            color: '#00f0ff',
            fontWeight: 700,
            cursor: 'pointer',
            textAlign: 'left',
            marginTop: '8px',
            borderRadius: '6px'
          }}
        >
          <span className="nav-icon">🧠</span>
          AI Quorum Copilot
        </button>

        <div className="nav-section-label" style={{ marginTop: 'auto' }}>System & Docs</div>

        <a
          href="/Kestrel_Quantum_Trading_Intelligence.pdf"
          target="_blank"
          rel="noopener noreferrer"
          className="nav-item"
          style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}
        >
          <span className="nav-icon">📄</span>
          Official Deck (PDF)
        </a>
        {bottomItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-item ${pathname === item.href ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          padding: '8px 4px',
        }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
              {user?.full_name || user?.email?.split('@')[0] || 'User'}
            </div>
            <div style={{ 
              fontSize: 11, 
              color: 'var(--accent-blue)', 
              textTransform: 'uppercase',
              fontWeight: 600,
              letterSpacing: '0.05em',
            }}>
              {user?.license_tier || 'Free'} Plan
            </div>
          </div>
          <button
            className="btn btn-ghost btn-sm"
            onClick={logout}
            title="Sign Out"
          >
            🚪
          </button>
        </div>
      </div>

      {/* Slide-over AI Orchestrator Drawer */}
      <AiChatDrawer isOpen={aiDrawerOpen} onClose={() => setAiDrawerOpen(false)} />
    </aside>
  );
}

