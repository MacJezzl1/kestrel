'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { api, ApiError, SessionInfo, ApiKeyInfo, ApiKeyCreated, AuditLogEntry } from '@/lib/api';

type Tab = 'sessions' | 'password' | 'apikeys' | 'audit';

export default function SecurityPage() {
  const { updateToken } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>('sessions');

  const tabs: { key: Tab; label: string; icon: string }[] = [
    { key: 'sessions', label: 'Sessions', icon: '🖥️' },
    { key: 'password', label: 'Password', icon: '🔑' },
    { key: 'apikeys', label: 'API Keys', icon: '🗝️' },
    { key: 'audit', label: 'Audit Log', icon: '📜' },
  ];

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>🔐 Security</h1>
      <p style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 24 }}>
        Manage sessions, passwords, API keys, and view your activity log.
      </p>

      {/* Tab bar */}
      <div style={{
        display: 'flex',
        gap: 4,
        marginBottom: 24,
        borderBottom: '1px solid var(--border-secondary)',
        paddingBottom: 0,
      }}>
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '10px 16px',
              background: 'none',
              border: 'none',
              borderBottom: `2px solid ${activeTab === tab.key ? 'var(--accent-blue)' : 'transparent'}`,
              color: activeTab === tab.key ? 'var(--accent-blue)' : 'var(--text-tertiary)',
              fontSize: 13,
              fontWeight: activeTab === tab.key ? 600 : 400,
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
              marginBottom: -1,
            }}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'sessions' && <SessionsPanel />}
      {activeTab === 'password' && <PasswordPanel onTokenUpdate={updateToken} />}
      {activeTab === 'apikeys' && <ApiKeysPanel />}
      {activeTab === 'audit' && <AuditLogPanel />}
    </div>
  );
}


// =========================
// Sessions Panel
// =========================
function SessionsPanel() {
  const { updateToken } = useAuth();
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [revoking, setRevoking] = useState(false);
  const [message, setMessage] = useState('');

  const loadSessions = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getSessions();
      setSessions(data);
    } catch {
      setSessions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadSessions(); }, [loadSessions]);

  const handleRevokeAll = async () => {
    if (!confirm('This will log you out of all other devices. Continue?')) return;
    try {
      setRevoking(true);
      const result = await api.revokeAllSessions();
      updateToken(result.access_token);
      setMessage('All other sessions have been revoked.');
      loadSessions();
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : 'Failed to revoke sessions');
    } finally {
      setRevoking(false);
    }
  };

  return (
    <div className="card" style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <div className="card-title">Active Sessions</div>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>
            Recent login activity on your account
          </div>
        </div>
        <button
          className="btn btn-primary btn-sm"
          onClick={handleRevokeAll}
          disabled={revoking}
          style={{ background: 'var(--danger)', borderColor: 'var(--danger)' }}
        >
          {revoking ? '⏳' : '🚫'} Revoke All
        </button>
      </div>

      {message && (
        <div style={{
          padding: '10px 14px',
          background: 'var(--success-soft)',
          border: '1px solid rgba(16, 185, 129, 0.2)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--success)',
          fontSize: 13,
          marginBottom: 16,
        }}>
          {message}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>Loading sessions...</div>
      ) : sessions.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>No login sessions found</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {sessions.map((session, i) => (
            <div key={i} style={{
              padding: '12px 16px',
              background: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-secondary)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                  {session.ip_address || 'Unknown IP'}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                  {session.user_agent ? session.user_agent.slice(0, 60) + '...' : 'Unknown device'}
                </div>
              </div>
              <div style={{
                fontSize: 11,
                color: 'var(--text-muted)',
                fontFamily: 'var(--font-mono)',
                whiteSpace: 'nowrap',
              }}>
                {new Date(session.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// =========================
// Password Panel
// =========================
function PasswordPanel({ onTokenUpdate }: { onTokenUpdate: (t: string) => void }) {
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage('');
    setError('');

    if (newPw !== confirmPw) {
      setError('New passwords do not match');
      return;
    }
    if (newPw.length < 8) {
      setError('New password must be at least 8 characters');
      return;
    }

    try {
      setLoading(true);
      const result = await api.changePassword(currentPw, newPw);
      onTokenUpdate(result.access_token);
      setMessage('Password changed successfully. All other sessions have been logged out.');
      setCurrentPw('');
      setNewPw('');
      setConfirmPw('');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ padding: 24, maxWidth: 480 }}>
      <div className="card-title" style={{ marginBottom: 4 }}>Change Password</div>
      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 20 }}>
        Changing your password will log you out of all other devices.
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div className="input-group">
          <label className="input-label">Current Password</label>
          <div style={{ position: 'relative' }}>
            <input
              className="input"
              type={showCurrent ? 'text' : 'password'}
              value={currentPw}
              onChange={e => setCurrentPw(e.target.value)}
              required
              style={{ paddingRight: 44 }}
            />
            <button type="button" onClick={() => setShowCurrent(!showCurrent)} style={{
              position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
              background: 'none', border: 'none', cursor: 'pointer', fontSize: 16,
              color: 'var(--text-tertiary)', padding: '4px 6px',
            }}>
              {showCurrent ? '🙈' : '👁️'}
            </button>
          </div>
        </div>

        <div className="input-group">
          <label className="input-label">New Password</label>
          <div style={{ position: 'relative' }}>
            <input
              className="input"
              type={showNew ? 'text' : 'password'}
              value={newPw}
              onChange={e => setNewPw(e.target.value)}
              required
              minLength={8}
              placeholder="Min 8 characters"
              style={{ paddingRight: 44 }}
            />
            <button type="button" onClick={() => setShowNew(!showNew)} style={{
              position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
              background: 'none', border: 'none', cursor: 'pointer', fontSize: 16,
              color: 'var(--text-tertiary)', padding: '4px 6px',
            }}>
              {showNew ? '🙈' : '👁️'}
            </button>
          </div>
        </div>

        <div className="input-group">
          <label className="input-label">Confirm New Password</label>
          <input
            className="input"
            type="password"
            value={confirmPw}
            onChange={e => setConfirmPw(e.target.value)}
            required
            minLength={8}
          />
        </div>

        {/* Password strength indicator */}
        {newPw && (
          <div style={{ display: 'flex', gap: 4, height: 4 }}>
            {[1, 2, 3, 4].map(level => {
              const strength = (newPw.length >= 8 ? 1 : 0) + (newPw.length >= 12 ? 1 : 0)
                + (/[A-Z]/.test(newPw) && /[a-z]/.test(newPw) ? 1 : 0)
                + (/[^a-zA-Z0-9]/.test(newPw) ? 1 : 0);
              const colors = ['var(--danger)', 'var(--warning)', 'var(--accent-blue)', 'var(--success)'];
              return (
                <div key={level} style={{
                  flex: 1,
                  borderRadius: 2,
                  background: level <= strength ? colors[strength - 1] : 'var(--bg-tertiary)',
                  transition: 'background var(--transition-fast)',
                }} />
              );
            })}
          </div>
        )}

        {error && (
          <div style={{
            padding: '10px 14px', background: 'var(--danger-soft)',
            border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: 'var(--radius-md)',
            color: 'var(--danger)', fontSize: 13,
          }}>{error}</div>
        )}

        {message && (
          <div style={{
            padding: '10px 14px', background: 'var(--success-soft)',
            border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: 'var(--radius-md)',
            color: 'var(--success)', fontSize: 13,
          }}>{message}</div>
        )}

        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? '⏳ Changing...' : '🔑 Change Password'}
        </button>
      </form>
    </div>
  );
}


// =========================
// API Keys Panel
// =========================
function ApiKeysPanel() {
  const [keys, setKeys] = useState<ApiKeyInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');

  const loadKeys = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.listApiKeys();
      setKeys(data);
    } catch {
      setKeys([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadKeys(); }, [loadKeys]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    setError('');

    try {
      setCreating(true);
      const result = await api.createApiKey(newKeyName.trim());
      setCreatedKey(result);
      setNewKeyName('');
      setShowCreate(false);
      loadKeys();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create API key');
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (keyId: string, keyName: string) => {
    if (!confirm(`Revoke API key "${keyName}"? Any integration using this key will stop working.`)) return;
    try {
      await api.revokeApiKey(keyId);
      loadKeys();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to revoke');
    }
  };

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="card" style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <div className="card-title">API Keys</div>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>
            Generate keys for MT5 EA, TradingView webhooks, and other integrations
          </div>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => { setShowCreate(true); setCreatedKey(null); }}>
          + New Key
        </button>
      </div>

      {error && (
        <div style={{
          padding: '10px 14px', background: 'var(--danger-soft)',
          border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: 'var(--radius-md)',
          color: 'var(--danger)', fontSize: 13, marginBottom: 16,
        }}>{error}</div>
      )}

      {/* Created key banner — shown once */}
      {createdKey && (
        <div style={{
          padding: 16,
          background: 'var(--success-soft)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: 'var(--radius-md)',
          marginBottom: 16,
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--success)', marginBottom: 8 }}>
            ✅ API Key Created — Copy it now, it won&apos;t be shown again!
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '10px 14px',
            background: 'var(--bg-primary)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-secondary)',
          }}>
            <code style={{
              flex: 1,
              fontSize: 12,
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-primary)',
              wordBreak: 'break-all',
            }}>
              {createdKey.raw_key}
            </code>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => handleCopy(createdKey.raw_key)}
              style={{ whiteSpace: 'nowrap', fontSize: 12 }}
            >
              {copied ? '✅ Copied' : '📋 Copy'}
            </button>
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 8 }}>
            Paste this key into your MT5 EA&apos;s &quot;JWT Access Token&quot; field or use as <code>X-API-Key</code> header.
          </div>
        </div>
      )}

      {/* Create form */}
      {showCreate && (
        <form onSubmit={handleCreate} style={{
          display: 'flex',
          gap: 8,
          marginBottom: 16,
          padding: 16,
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-secondary)',
        }}>
          <input
            className="input"
            type="text"
            placeholder="Key name (e.g., MT5 EA Production)"
            value={newKeyName}
            onChange={e => setNewKeyName(e.target.value)}
            required
            style={{ flex: 1 }}
            autoFocus
          />
          <button className="btn btn-primary btn-sm" type="submit" disabled={creating}>
            {creating ? '⏳' : '✨'} Generate
          </button>
          <button className="btn btn-ghost btn-sm" type="button" onClick={() => setShowCreate(false)}>
            Cancel
          </button>
        </form>
      )}

      {/* Keys list */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>Loading keys...</div>
      ) : keys.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>🗝️</div>
          No API keys yet. Create one to connect your MT5 EA.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {keys.map(key => (
            <div key={key.id} style={{
              padding: '12px 16px',
              background: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-md)',
              border: `1px solid ${key.is_active ? 'var(--border-secondary)' : 'var(--danger-soft)'}`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              opacity: key.is_active ? 1 : 0.5,
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {key.name}
                  </span>
                  <span className={`badge ${key.is_active ? 'badge-online' : ''}`} style={{
                    fontSize: 10,
                    ...(!key.is_active ? { background: 'var(--danger-soft)', color: 'var(--danger)', border: '1px solid rgba(239, 68, 68, 0.2)' } : {}),
                  }}>
                    {key.is_active ? 'Active' : 'Revoked'}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
                  {key.key_prefix}••••••••
                  {key.last_used_at && (
                    <span style={{ marginLeft: 12, fontFamily: 'inherit' }}>
                      Last used: {new Date(key.last_used_at).toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
              {key.is_active && (
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => handleRevoke(key.id, key.name)}
                  style={{ color: 'var(--danger)', fontSize: 12 }}
                >
                  Revoke
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// =========================
// Audit Log Panel
// =========================
function AuditLogPanel() {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const loadEntries = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getAuditLog(100);
      setEntries(data);
    } catch {
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadEntries(); }, [loadEntries]);

  const actionIcons: Record<string, string> = {
    login: '🔓',
    register: '📝',
    password_changed: '🔑',
    sessions_revoked: '🚫',
    api_key_created: '🗝️',
    api_key_revoked: '❌',
    signal_generated: '📡',
    trade_opened: '📈',
    trade_closed: '📉',
    license_checked: '🛡️',
    vision_scan: '👁️',
  };

  const actionLabels: Record<string, string> = {
    login: 'Logged in',
    register: 'Account created',
    password_changed: 'Password changed',
    sessions_revoked: 'Sessions revoked',
    api_key_created: 'API key created',
    api_key_revoked: 'API key revoked',
    signal_generated: 'Signal generated',
    trade_opened: 'Trade opened',
    trade_closed: 'Trade closed',
    license_checked: 'License checked',
    vision_scan: 'Chart analyzed',
  };

  return (
    <div className="card" style={{ padding: 24 }}>
      <div className="card-title" style={{ marginBottom: 4 }}>Audit Log</div>
      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 20 }}>
        Complete activity history on your account
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>Loading audit log...</div>
      ) : entries.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>No activity yet</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {entries.map(entry => (
            <div key={entry.id} style={{
              padding: '10px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              borderBottom: '1px solid var(--border-secondary)',
            }}>
              <span style={{ fontSize: 18, width: 28, textAlign: 'center', flexShrink: 0 }}>
                {actionIcons[entry.action] || '📌'}
              </span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                  {actionLabels[entry.action] || entry.action}
                </div>
                {Object.keys(entry.details).length > 0 && (
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                    {Object.entries(entry.details).map(([k, v]) => `${k}: ${v}`).join(' · ')}
                  </div>
                )}
              </div>
              <div style={{
                fontSize: 11,
                color: 'var(--text-muted)',
                fontFamily: 'var(--font-mono)',
                whiteSpace: 'nowrap',
                flexShrink: 0,
              }}>
                {entry.ip_address && <span style={{ marginRight: 12 }}>{entry.ip_address}</span>}
                {new Date(entry.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
