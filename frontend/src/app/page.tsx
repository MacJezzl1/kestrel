'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { ApiError } from '@/lib/api';

export default function LoginPage() {
  const { login, register, isAuthenticated, isLoading, rememberMe, setRememberMe } = useAuth();
  const router = useRouter();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Redirect if already authenticated
  if (!isLoading && isAuthenticated) {
    router.push('/dashboard');
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

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
        setError(err.message || 'Connection failed. Is the Kestrel API running?');
      } else {
        setError('Connection failed. Please check your internet or retry.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setError('');
    handleSubmit(new Event('submit') as unknown as React.FormEvent);
  };

  if (isLoading) {
    return (
      <div className="auth-page">
        <div className="auth-card animate-scale-in" style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🦅</div>
          <div style={{ color: 'var(--text-secondary)' }}>Loading Kestrel...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-card animate-scale-in">
        <div className="auth-header">
          <img src="/kestrel-logo.jpg" alt="Kestrel" className="logo-img" />
          <h2 style={{ 
            background: 'var(--gradient-blue)', 
            WebkitBackgroundClip: 'text', 
            backgroundClip: 'text', 
            color: 'transparent' 
          }}>
            Kestrel
          </h2>
          <p>See every market. Miss nothing.</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {isRegister && (
            <div className="input-group animate-fade-in">
              <label className="input-label" htmlFor="fullName">Full Name</label>
              <input
                id="fullName"
                className="input"
                type="text"
                placeholder="John Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
          )}

          <div className="input-group">
            <label className="input-label" htmlFor="email">Email</label>
            <input
              id="email"
              className="input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="password">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                id="password"
                className="input"
                type={showPassword ? 'text' : 'password'}
                placeholder="Min 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                style={{ paddingRight: 44 }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: 8,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 18,
                  padding: '4px 6px',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-tertiary)',
                  transition: 'color var(--transition-fast)',
                  lineHeight: 1,
                }}
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          {/* Remember me */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            margin: '4px 0 8px',
          }}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              cursor: 'pointer',
              fontSize: 13,
              color: 'var(--text-secondary)',
              userSelect: 'none',
            }}>
              <div
                onClick={() => setRememberMe(!rememberMe)}
                style={{
                  width: 18,
                  height: 18,
                  borderRadius: 4,
                  border: `2px solid ${rememberMe ? 'var(--accent-blue)' : 'var(--border-primary)'}`,
                  background: rememberMe ? 'var(--accent-blue)' : 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'all var(--transition-fast)',
                  flexShrink: 0,
                }}
              >
                {rememberMe && (
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M2.5 6L5 8.5L9.5 3.5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </div>
              <span onClick={() => setRememberMe(!rememberMe)}>Remember me</span>
            </label>
          </div>

          {error && (
            <div style={{
              padding: '10px 14px',
              background: 'var(--danger-soft)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--danger)',
              fontSize: 13,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 8,
            }}>
              <span>{error}</span>
              {error.includes('Connection failed') && (
                <button
                  type="button"
                  onClick={handleRetry}
                  style={{
                    background: 'rgba(239, 68, 68, 0.15)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--danger)',
                    cursor: 'pointer',
                    padding: '4px 10px',
                    fontSize: 12,
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                    transition: 'background var(--transition-fast)',
                  }}
                >
                  Retry
                </button>
              )}
            </div>
          )}

          <button className="btn btn-primary btn-lg" type="submit" disabled={loading}>
            {loading ? '⏳' : '🦅'} {isRegister ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <div className="auth-footer">
          {isRegister ? (
            <>Already have an account?{' '}
              <a href="#" onClick={(e) => { e.preventDefault(); setIsRegister(false); setError(''); }}>
                Sign in
              </a>
            </>
          ) : (
            <>New to Kestrel?{' '}
              <a href="#" onClick={(e) => { e.preventDefault(); setIsRegister(true); setError(''); }}>
                Create account
              </a>
            </>
          )}
        </div>

        <div style={{ 
          marginTop: 24, 
          fontSize: 11, 
          color: 'var(--text-muted)', 
          textAlign: 'center',
          lineHeight: 1.5,
        }}>
          Trading involves risk of loss. Past performance does not guarantee future results. 
          Kestrel is a decision-support tool by CapeChain Labs.
        </div>
      </div>
    </div>
  );
}
