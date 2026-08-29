'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/signals', label: 'Signals', icon: '📡' },
  { href: '/trades', label: 'Trades', icon: '📋' },
  { href: '/vision', label: 'Vision', icon: '👁️' },
  { href: '/analysis', label: 'Analysis', icon: '🔬' },
];

const allNavItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/signals', label: 'AI Signals', icon: '📡' },
  { href: '/trades', label: 'Trade History', icon: '📋' },
  { href: '/analysis', label: 'Portfolio Analysis', icon: '🔬' },
  { href: '/vision', label: 'Chart Vision Scanner', icon: '👁️' },
  { href: '/security', label: 'Security & Audit', icon: '🔐' },
  { href: '/settings', label: 'Settings & License', icon: '⚙️' },
];

export default function MobileNav() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <>
      {/* Mobile Top App Bar */}
      <header className="mobile-header-bar">
        <button
          className="mobile-menu-btn"
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Toggle Menu"
        >
          {isOpen ? '✕' : '☰'}
        </button>
        
        <div className="mobile-header-brand">
          <img src="/kestrel-logo.jpg" alt="Kestrel" className="mobile-logo" />
          <span className="mobile-title">KESTREL AI</span>
        </div>

        <div className="mobile-status-badge">
          <span className="pulse-dot online" />
          <span>100 AI</span>
        </div>
      </header>

      {/* Mobile Drawer Overlay */}
      {isOpen && (
        <div className="mobile-drawer-backdrop" onClick={() => setIsOpen(false)}>
          <div className="mobile-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="mobile-drawer-header">
              <div className="drawer-user-info">
                <img src="/kestrel-logo.jpg" alt="Kestrel" className="drawer-logo" />
                <div>
                  <div className="drawer-name">{user?.full_name || user?.email?.split('@')[0] || 'Trader'}</div>
                  <div className="drawer-tier">{user?.license_tier || 'Pro'} Tier Active</div>
                </div>
              </div>
              <button className="drawer-close-btn" onClick={() => setIsOpen(false)}>✕</button>
            </div>

            <nav className="mobile-drawer-links">
              {allNavItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`drawer-link ${pathname === item.href ? 'active' : ''}`}
                  onClick={() => setIsOpen(false)}
                >
                  <span className="drawer-icon">{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              ))}
            </nav>

            <div className="mobile-drawer-footer">
              <button className="btn btn-danger btn-sm w-full" onClick={logout}>
                🚪 Sign Out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Fixed Bottom Navigation */}
      <nav className="mobile-bottom-nav">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`bottom-nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="bottom-nav-icon">{item.icon}</span>
              <span className="bottom-nav-label">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
