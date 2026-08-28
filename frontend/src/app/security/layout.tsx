'use client';

import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import Sidebar from '@/components/layout/Sidebar';

export default function SecurityLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="auth-page">
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🦅</div>
          <div style={{ color: 'var(--text-secondary)' }}>Loading...</div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <header className="header">
          <div className="header-left">
            <h2 className="header-title">Kestrel Intelligence</h2>
          </div>
          <div className="header-right">
            <span className="badge badge-online">
              <span className="pulse-dot online" />
              Online
            </span>
          </div>
        </header>
        <div className="page-content">
          {children}
        </div>
        <div className="disclaimer-bar">
          ⚠️ Trading involves risk of loss. Past performance does not guarantee future results. Kestrel is a decision-support tool — not financial advice.
        </div>
      </main>
    </div>
  );
}
