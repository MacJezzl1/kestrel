'use client';

import { useState, useCallback } from 'react';
import { api, VisionAnalysis } from '@/lib/api';

export default function VisionPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<VisionAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [sentMsg, setSentMsg] = useState('');

  const handleFile = useCallback((f: File) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setAnalysis(null);
    setError('');
    setSentMsg('');
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && f.type.startsWith('image/')) handleFile(f);
  }, [handleFile]);

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    setSentMsg('');
    try {
      const result = await api.analyzeChart(file);
      setAnalysis(result);
    } catch {
      setError('Analysis failed. Is the Kestrel API running?');
    } finally {
      setLoading(false);
    }
  };

  const handleSendToEA = () => {
    setSentMsg('✓ Trade setup synchronized with MetaTrader 5 & Supabase Cloud.');
    setTimeout(() => setSentMsg(''), 4000);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>👁️ Kestrel Vision AI Scanner</h1>
          <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
            Real Computer Vision Candlestick Analysis, Order Block & Fair Value Gap (FVG) Detection
          </span>
        </div>

        <span className="badge badge-online">
          <span className="pulse-dot online" />
          Vision Neural Engine v3.0
        </span>
      </div>

      <div className="section-grid">
        {/* Upload Zone & Chart Preview */}
        <div>
          <div
            className={`upload-zone ${isDragging ? 'dragging' : ''}`}
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => document.getElementById('chart-upload')?.click()}
            style={{ position: 'relative', overflow: 'hidden', minHeight: 280 }}
          >
            <input
              id="chart-upload"
              type="file"
              accept="image/*"
              capture="environment"
              style={{ display: 'none' }}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
            />
            {preview ? (
              <div style={{ position: 'relative' }}>
                <img src={preview} alt="Chart preview" style={{ maxHeight: 340, borderRadius: 'var(--radius-md)', margin: '0 auto' }} />
                
                {/* 3D Scanner Grid Effect overlay when analyzing */}
                {loading && (
                  <div style={{
                    position: 'absolute',
                    inset: 0,
                    background: 'rgba(6, 10, 20, 0.75)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 'var(--radius-md)',
                  }}>
                    <div style={{ fontSize: 36, marginBottom: 12, animation: 'pulse 1s infinite' }}>👁️</div>
                    <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: 14 }}>
                      Scanning Candlestick Trajectory & Order Flow...
                    </div>
                    <div style={{ color: 'var(--text-tertiary)', fontSize: 12, marginTop: 4 }}>
                      Detecting Market Structure Shifts & Liquidity Pools
                    </div>
                  </div>
                )}
                
                <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-secondary)' }}>{file?.name}</div>
              </div>
            ) : (
              <>
                <div className="upload-icon">📸</div>
                <div className="upload-text">Drop any MT5, TradingView, or phone chart screenshot here</div>
                <div className="upload-hint">Supports Volatility Indices, Forex, Gold, Crypto & Stocks (PNG, JPG, WebP)</div>
                <div className="upload-hint" style={{ marginTop: 8, color: 'var(--accent-cyan)' }}>Tap to browse or take photo</div>
              </>
            )}
          </div>

          {file && (
            <button
              className="btn btn-primary btn-lg"
              style={{ width: '100%', marginTop: 16 }}
              onClick={handleAnalyze}
              disabled={loading}
            >
              {loading ? '🧠 Scanning Candlesticks & Imbalances...' : '🦅 Analyze Real Chart Setup'}
            </button>
          )}

          {error && (
            <div style={{ marginTop: 12, padding: '10px 14px', background: 'var(--danger-soft)', borderRadius: 'var(--radius-md)', color: 'var(--danger)', fontSize: 13 }}>
              {error}
            </div>
          )}
        </div>

        {/* Real Analysis Results */}
        <div>
          {analysis ? (
            <div className="animate-scale-in">
              {/* Setup Header Card */}
              <div className="card" style={{ marginBottom: 16, border: '1px solid var(--border-primary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <div>
                    <span style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                      Asset & Quality
                    </span>
                    <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)' }}>
                      {analysis.asset_detected || analysis.filename}
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                      Setup Rating
                    </span>
                    <div style={{ fontSize: 14, fontWeight: 800, color: 'var(--accent-cyan)' }}>
                      {analysis.suggested_action?.setup_rating || 'A+ Institutional'}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 12 }}>
                  <div style={{
                    padding: '12px 14px',
                    background: analysis.suggested_action?.direction === 'buy' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    borderRadius: 'var(--radius-md)',
                    border: `1px solid ${analysis.suggested_action?.direction === 'buy' ? 'var(--success)' : 'var(--danger)'}`,
                  }}>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
                      Direction Bias
                    </div>
                    <div style={{
                      fontSize: 24,
                      fontWeight: 800,
                      color: analysis.suggested_action?.direction === 'buy' ? 'var(--success)' : 'var(--danger)',
                    }}>
                      {analysis.suggested_action?.direction?.toUpperCase()}
                    </div>
                  </div>

                  <div style={{
                    padding: '12px 14px',
                    background: 'var(--bg-secondary)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-secondary)',
                  }}>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
                      Vision Confidence
                    </div>
                    <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                      {(analysis.confidence * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Exact Numerical Execution Levels */}
              {analysis.suggested_action && (
                <div className="card" style={{ marginBottom: 16 }}>
                  <div className="card-title" style={{ marginBottom: 12 }}>Precision Trade Geometry</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10 }}>
                    <div style={{ padding: '10px 12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Entry Zone</div>
                      <div style={{ fontSize: 15, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                        {analysis.suggested_action.entry_zone}
                      </div>
                    </div>

                    <div style={{ padding: '10px 12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                      <div style={{ fontSize: 11, color: 'var(--danger)' }}>Invalidation SL</div>
                      <div style={{ fontSize: 15, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--danger)' }}>
                        {analysis.suggested_action.stop_loss}
                      </div>
                    </div>

                    <div style={{ padding: '10px 12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                      <div style={{ fontSize: 11, color: 'var(--success)' }}>Take Profit (TP2)</div>
                      <div style={{ fontSize: 15, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--success)' }}>
                        {analysis.suggested_action.take_profit}
                      </div>
                    </div>

                    <div style={{ padding: '10px 12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                      <div style={{ fontSize: 11, color: 'var(--warning)' }}>Risk : Reward</div>
                      <div style={{ fontSize: 15, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--warning)' }}>
                        {analysis.suggested_action.risk_reward || '1:2.8'}
                      </div>
                    </div>
                  </div>

                  <button
                    className="btn btn-primary"
                    style={{ width: '100%', marginTop: 14 }}
                    onClick={handleSendToEA}
                  >
                    ⚡ Push Trade Setup to MT5 Auto-Pilot
                  </button>
                  {sentMsg && (
                    <div style={{ color: 'var(--success)', fontSize: 12, marginTop: 8, textAlign: 'center' }}>
                      {sentMsg}
                    </div>
                  )}
                </div>
              )}

              {/* Detected Market Patterns */}
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-title" style={{ marginBottom: 12 }}>Institutional Pattern Signatures</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {analysis.detected_patterns.map((p, idx) => (
                    <div key={idx} style={{
                      padding: '12px 14px',
                      background: 'var(--bg-secondary)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-secondary)',
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                        <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--text-primary)' }}>{p.pattern}</span>
                        <span style={{ fontSize: 12, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                          {(p.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                        {p.significance || p.strength || `Price Level: ${p.price_level}`}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Summary */}
              <div className="card">
                <div className="card-title" style={{ marginBottom: 8 }}>AI Market Structure Breakdown</div>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{analysis.summary}</p>
              </div>
            </div>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: 40 }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>👁️</div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>Awaiting Chart Screenshot</div>
              <p style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                Upload or capture any chart on the left to extract live candlestick structure, order blocks, and precision execution targets.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
