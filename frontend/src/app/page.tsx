'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { ApiError } from '@/lib/api';

export default function LoginPage() {
  const { login, register, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Connection failed. Is the Kestrel API running?');
      }
    } finally {
      setLoading(false);
    }
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
            <input
              id="password"
              className="input"
              type="password"
              placeholder="Min 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>

          {error && (
            <div style={{
              padding: '10px 14px',
              background: 'var(--danger-soft)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--danger)',
              fontSize: 13,
            }}>
              {error}
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
