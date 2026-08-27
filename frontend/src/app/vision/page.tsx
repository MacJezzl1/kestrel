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

  const handleFile = useCallback((f: File) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setAnalysis(null);
    setError('');
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
    try {
      const result = await api.analyzeChart(file);
      setAnalysis(result);
    } catch {
      setError('Analysis failed. Is the Kestrel API running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>👁️ Kestrel Vision</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24, fontSize: 14 }}>
        Upload or photograph any chart — any platform, any broker — for AI-driven pattern analysis.
      </p>

      <div className="section-grid">
        {/* Upload Zone */}
        <div>
          <div
            className={`upload-zone ${isDragging ? 'dragging' : ''}`}
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => document.getElementById('chart-upload')?.click()}
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
              <div>
                <img src={preview} alt="Chart preview" style={{ maxHeight: 300, borderRadius: 'var(--radius-md)', margin: '0 auto' }} />
                <div style={{ marginTop: 12, fontSize: 13, color: 'var(--text-secondary)' }}>{file?.name}</div>
              </div>
            ) : (
              <>
                <div className="upload-icon">📸</div>
                <div className="upload-text">Drop a chart image here or click to browse</div>
                <div className="upload-hint">Supports PNG, JPEG, WebP • Max 10MB</div>
                <div className="upload-hint" style={{ marginTop: 8 }}>On mobile, tap to use camera</div>
              </>
            )}
          </div>

          {file && (
            <button className="btn btn-primary btn-lg" style={{ width: '100%', marginTop: 16 }} onClick={handleAnalyze} disabled={loading}>
              {loading ? '⏳ Analyzing chart...' : '🦅 Analyze Chart'}
            </button>
          )}

          {error && (
            <div style={{ marginTop: 12, padding: '10px 14px', background: 'var(--danger-soft)', borderRadius: 'var(--radius-md)', color: 'var(--danger)', fontSize: 13 }}>
              {error}
            </div>
          )}
        </div>

        {/* Analysis Results */}
        <div>
          {analysis ? (
            <div className="animate-scale-in">
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">
                  <span className="card-title">Analysis Results</span>
                  <span className={`badge ${analysis.confidence >= 0.7 ? 'badge-online' : 'badge-ranging'}`}>
                    {(analysis.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 4 }}>Image Quality</div>
                <span className={`badge ${analysis.image_quality === 'good' ? 'badge-online' : 'badge-ranging'}`}>
                  {analysis.image_quality.toUpperCase()}
                </span>
              </div>

              {/* Detected Patterns */}
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-title" style={{ marginBottom: 12 }}>Detected Patterns</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {analysis.detected_patterns.map((p, i) => (
                    <div key={i} style={{
                      padding: '12px 16px',
                      background: 'var(--bg-secondary)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-secondary)',
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 600, fontSize: 14 }}>{p.pattern}</span>
                        <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                          {(p.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      {Object.entries(p).filter(([k]) => !['pattern', 'confidence'].includes(k)).map(([k, v]) => (
                        <div key={k} style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>
                          {k}: <span style={{ color: 'var(--text-secondary)' }}>{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>

              {/* Summary */}
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-title" style={{ marginBottom: 8 }}>AI Summary</div>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {analysis.summary}
                </p>
              </div>

              {/* Suggested Action */}
              <div className="card" style={{ borderColor: 'rgba(59, 130, 246, 0.2)' }}>
                <div className="card-title" style={{ marginBottom: 12 }}>Suggested Action</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 12 }}>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Direction</div>
                    <div style={{
                      fontSize: 18, fontWeight: 700, marginTop: 4,
                      color: analysis.suggested_action.direction === 'buy' ? 'var(--success)' : 'var(--danger)',
                    }}>
                      {analysis.suggested_action.direction.toUpperCase()}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Entry Zone</div>
                    <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, fontFamily: 'var(--font-mono)' }}>
                      {analysis.suggested_action.entry_zone}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--danger)' }}>Stop Loss</div>
                    <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, fontFamily: 'var(--font-mono)', color: 'var(--danger)' }}>
                      {analysis.suggested_action.stop_loss}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--success)' }}>Take Profit</div>
                    <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, fontFamily: 'var(--font-mono)', color: 'var(--success)' }}>
                      {analysis.suggested_action.take_profit}
                    </div>
                  </div>
                </div>
              </div>

              <div style={{ marginTop: 12, fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                {analysis.disclaimer}
              </div>
            </div>
          ) : (
            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 400 }}>
              <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                <div style={{ fontSize: 48, marginBottom: 12, opacity: 0.4 }}>🔍</div>
                <div>Upload a chart to see analysis results</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
