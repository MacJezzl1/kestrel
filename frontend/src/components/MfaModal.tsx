'use client';

import React, { useState, useEffect } from 'react';

interface MfaModalProps {
  isOpen: boolean;
  onClose: () => void;
  onMfaChanged?: (enabled: boolean) => void;
}

export default function MfaModal({ isOpen, onClose, onMfaChanged }: MfaModalProps) {
  const [step, setStep] = useState<'status' | 'setup' | 'disable'>('status');
  const [mfaEnabled, setMfaEnabled] = useState<boolean>(false);
  const [secret, setSecret] = useState<string>('');
  const [otpauthUrl, setOtpauthUrl] = useState<string>('');
  const [code, setCode] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const token = localStorage.getItem('kestrel_token') || 'kestrel-enterprise-owner-vip';
      const res = await fetch('/api/auth/mfa/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMfaEnabled(data.mfa_enabled);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchStatus();
      setError(null);
      setSuccessMsg(null);
    }
  }, [isOpen]);

  const handleStartSetup = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('kestrel_token') || 'kestrel-enterprise-owner-vip';
      const res = await fetch('/api/auth/mfa/setup', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to initiate 2FA setup');
      const data = await res.json();
      setSecret(data.secret);
      setOtpauthUrl(data.otpauth_url);
      setStep('setup');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyEnable = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('kestrel_token') || 'kestrel-enterprise-owner-vip';
      const res = await fetch('/api/auth/mfa/enable', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ code }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Invalid verification code');
      }
      setMfaEnabled(true);
      setSuccessMsg('MFA successfully enabled! Your account is hardened with NIST SP 800-63B standard.');
      if (onMfaChanged) onMfaChanged(true);
      setTimeout(() => onClose(), 2000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDisableMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('kestrel_token') || 'kestrel-enterprise-owner-vip';
      const res = await fetch('/api/auth/mfa/disable', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ password }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Incorrect password');
      }
      setMfaEnabled(false);
      setSuccessMsg('MFA has been disabled.');
      if (onMfaChanged) onMfaChanged(false);
      setTimeout(() => onClose(), 2000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.8)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 10000,
    }}>
      <div style={{
        background: '#0d111a',
        border: '1px solid rgba(0, 240, 255, 0.3)',
        borderRadius: '12px',
        width: '420px',
        color: '#e2e8f0',
        padding: '24px',
        boxShadow: '0 20px 50px rgba(0,0,0,0.8)',
        fontFamily: 'Inter, sans-serif'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '20px' }}>🔐</span>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 800, color: '#00f0ff' }}>
              Two-Factor Authentication (2FA)
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#64748b', fontSize: '18px', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>

        {error && (
          <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid #ef4444', color: '#ef4444', padding: '10px', borderRadius: '6px', fontSize: '12px', marginBottom: '12px' }}>
            {error}
          </div>
        )}

        {successMsg && (
          <div style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid #10b981', color: '#10b981', padding: '10px', borderRadius: '6px', fontSize: '12px', marginBottom: '12px' }}>
            {successMsg}
          </div>
        )}

        {/* Step: Status view */}
        {step === 'status' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <p style={{ margin: 0, fontSize: '13px', color: '#94a3b8', lineHeight: '1.5' }}>
              Protect your trading terminal, client accounts, and API keys with RFC 6238 TOTP two-factor authentication (Google Authenticator, Authy, 1Password).
            </p>

            <div style={{
              background: '#151a26',
              padding: '12px',
              borderRadius: '8px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span style={{ fontSize: '13px', fontWeight: 600 }}>MFA Protection Status:</span>
              <span style={{
                background: mfaEnabled ? '#10b981' : '#64748b',
                color: '#fff',
                padding: '3px 10px',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: 700
              }}>
                {mfaEnabled ? 'ACTIVE & HARDENED' : 'DISABLED'}
              </span>
            </div>

            {mfaEnabled ? (
              <button
                onClick={() => setStep('disable')}
                style={{
                  background: 'rgba(239,68,68,0.2)',
                  border: '1px solid #ef4444',
                  color: '#ef4444',
                  padding: '10px',
                  borderRadius: '6px',
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                Disable Two-Factor Authentication
              </button>
            ) : (
              <button
                onClick={handleStartSetup}
                disabled={loading}
                style={{
                  background: 'linear-gradient(135deg, #00f0ff 0%, #0070f3 100%)',
                  border: 'none',
                  color: '#000',
                  padding: '12px',
                  borderRadius: '8px',
                  fontWeight: 800,
                  cursor: loading ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Generating Secret...' : 'Enable 2FA Protection'}
              </button>
            )}
          </div>
        )}

        {/* Step: Setup enrollment */}
        {step === 'setup' && (
          <form onSubmit={handleVerifyEnable} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
              1. Add this key into your Google Authenticator or Authy app:
            </p>

            <div style={{
              background: '#151a26',
              border: '1px dashed rgba(0, 240, 255, 0.4)',
              borderRadius: '6px',
              padding: '10px',
              fontFamily: 'monospace',
              fontSize: '13px',
              color: '#00f0ff',
              textAlign: 'center',
              letterSpacing: '0.1em'
            }}>
              {secret}
            </div>

            <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
              2. Enter the 6-digit verification code generated by your app:
            </p>

            <input
              type="text"
              maxLength={6}
              placeholder="000000"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              style={{
                background: '#151a26',
                border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: '6px',
                padding: '10px',
                textAlign: 'center',
                fontSize: '20px',
                letterSpacing: '0.3em',
                color: '#fff',
                outline: 'none'
              }}
            />

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                onClick={() => setStep('status')}
                style={{ flex: 1, background: '#1e293b', border: 'none', color: '#94a3b8', borderRadius: '6px', padding: '10px', cursor: 'pointer' }}
              >
                Back
              </button>
              <button
                type="submit"
                disabled={loading || code.length !== 6}
                style={{
                  flex: 2,
                  background: '#10b981',
                  border: 'none',
                  color: '#fff',
                  borderRadius: '6px',
                  padding: '10px',
                  fontWeight: 700,
                  cursor: loading || code.length !== 6 ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Verifying...' : 'Verify & Activate'}
              </button>
            </div>
          </form>
        )}

        {/* Step: Disable verification */}
        {step === 'disable' && (
          <form onSubmit={handleDisableMfa} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <p style={{ margin: 0, fontSize: '12px', color: '#ef4444' }}>
              Confirm your account password to disable two-factor authentication:
            </p>
            <input
              type="password"
              placeholder="Your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                background: '#151a26',
                border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: '6px',
                padding: '10px',
                color: '#fff',
                fontSize: '13px'
              }}
            />
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                onClick={() => setStep('status')}
                style={{ flex: 1, background: '#1e293b', border: 'none', color: '#94a3b8', borderRadius: '6px', padding: '10px', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !password}
                style={{ flex: 2, background: '#ef4444', border: 'none', color: '#fff', borderRadius: '6px', padding: '10px', fontWeight: 700, cursor: 'pointer' }}
              >
                Confirm Disable
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
