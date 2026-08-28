'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
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

        <div className="nav-section-label" style={{ marginTop: 'auto' }}>System</div>
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
    </aside>
  );
}
