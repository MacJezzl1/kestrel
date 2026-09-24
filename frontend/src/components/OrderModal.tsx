'use client';

import React, { useState } from 'react';

interface OrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultInstrument?: string;
  defaultPrice?: number;
  onOrderSuccess?: (order: any) => void;
}

export default function OrderModal({
  isOpen,
  onClose,
  defaultInstrument = 'Volatility 100 Index',
  defaultPrice = 1250.00,
  onOrderSuccess,
}: OrderModalProps) {
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT' | 'STOP'>('MARKET');
  const [direction, setDirection] = useState<'BUY' | 'SELL'>('BUY');
  const [qty, setQty] = useState<number>(0.1);
  const [price, setPrice] = useState<number>(defaultPrice);
  const [stopLoss, setStopLoss] = useState<number>(defaultPrice - 20);
  const [takeProfit, setTakeProfit] = useState<number>(defaultPrice + 40);
  const [broadcastToClients, setBroadcastToClients] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  // Calculate risk / reward ratio
  const risk = Math.abs(price - stopLoss);
  const reward = Math.abs(takeProfit - price);
  const rrRatio = risk > 0 ? (reward / risk).toFixed(2) : '0.00';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const clientOrderId = `ord_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      const token = localStorage.getItem('kestrel_token') || 'kestrel-enterprise-owner-vip';
      const res = await fetch('/api/orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          client_order_id: clientOrderId,
          account_number: '41230754',
          instrument: defaultInstrument,
          order_type: orderType,
          direction: direction,
          qty: Number(qty),
          price: orderType === 'MARKET' ? null : Number(price),
          stop_loss: Number(stopLoss),
          take_profit: Number(takeProfit),
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Order execution failed');
      }

      const orderData = await res.json();

      // If broadcast enabled, trigger PAMM client broadcast
      if (broadcastToClients) {
        await fetch('/api/clients/broadcast-trade', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            symbol: defaultInstrument,
            action: direction,
            master_lot: Number(qty),
            sl: Number(stopLoss),
            tp: Number(takeProfit),
            magic: 120999,
          }),
        }).catch(() => null);
      }

      if (onOrderSuccess) onOrderSuccess(orderData);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Error submitting order');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
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
        width: '440px',
        boxShadow: '0 20px 50px rgba(0,0,0,0.8)',
        color: '#e2e8f0',
        overflow: 'hidden',
        fontFamily: 'Inter, sans-serif'
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(90deg, rgba(0, 240, 255, 0.1) 0%, transparent 100%)'
        }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 800, color: '#00f0ff' }}>
              Institutional Order Entry
            </h3>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>{defaultInstrument}</span>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#64748b', fontSize: '18px', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {error && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid #ef4444',
              color: '#ef4444',
              padding: '10px',
              borderRadius: '6px',
              fontSize: '12px'
            }}>
              {error}
            </div>
          )}

          {/* Direction toggle */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <button
              type="button"
              onClick={() => setDirection('BUY')}
              style={{
                padding: '10px',
                borderRadius: '6px',
                border: 'none',
                fontWeight: 800,
                fontSize: '14px',
                cursor: 'pointer',
                background: direction === 'BUY' ? '#10b981' : '#1e293b',
                color: direction === 'BUY' ? '#fff' : '#64748b'
              }}
            >
              BUY / LONG
            </button>
            <button
              type="button"
              onClick={() => setDirection('SELL')}
              style={{
                padding: '10px',
                borderRadius: '6px',
                border: 'none',
                fontWeight: 800,
                fontSize: '14px',
                cursor: 'pointer',
                background: direction === 'SELL' ? '#ef4444' : '#1e293b',
                color: direction === 'SELL' ? '#fff' : '#64748b'
              }}
            >
              SELL / SHORT
            </button>
          </div>

          {/* Order Type */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
            {(['MARKET', 'LIMIT', 'STOP'] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setOrderType(t)}
                style={{
                  padding: '6px',
                  borderRadius: '4px',
                  border: orderType === t ? '1px solid #00f0ff' : '1px solid rgba(255,255,255,0.1)',
                  background: orderType === t ? 'rgba(0, 240, 255, 0.15)' : '#151a26',
                  color: orderType === t ? '#00f0ff' : '#94a3b8',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {t}
              </button>
            ))}
          </div>

          {/* Lot Size */}
          <div>
            <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
              LOT SIZE
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              max="100.0"
              value={qty}
              onChange={(e) => setQty(parseFloat(e.target.value))}
              style={{
                width: '100%',
                background: '#151a26',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '6px',
                padding: '8px 12px',
                color: '#fff',
                fontSize: '14px',
                outline: 'none'
              }}
            />
          </div>

          {/* Bracket SL / TP */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '11px', color: '#ef4444', display: 'block', marginBottom: '4px' }}>
                STOP LOSS (SL)
              </label>
              <input
                type="number"
                step="0.01"
                value={stopLoss}
                onChange={(e) => setStopLoss(parseFloat(e.target.value))}
                style={{
                  width: '100%',
                  background: '#151a26',
                  border: '1px solid rgba(239,68,68,0.4)',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  color: '#fff',
                  fontSize: '13px'
                }}
              />
            </div>
            <div>
              <label style={{ fontSize: '11px', color: '#10b981', display: 'block', marginBottom: '4px' }}>
                TAKE PROFIT (TP)
              </label>
              <input
                type="number"
                step="0.01"
                value={takeProfit}
                onChange={(e) => setTakeProfit(parseFloat(e.target.value))}
                style={{
                  width: '100%',
                  background: '#151a26',
                  border: '1px solid rgba(16,185,129,0.4)',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  color: '#fff',
                  fontSize: '13px'
                }}
              />
            </div>
          </div>

          {/* Risk / Reward indicator */}
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            padding: '8px 12px',
            borderRadius: '6px',
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '12px'
          }}>
            <span style={{ color: '#94a3b8' }}>Risk:Reward Ratio</span>
            <span style={{ color: '#00f0ff', fontWeight: 700 }}>1 : {rrRatio}</span>
          </div>

          {/* PAMM Broadcast Checkbox */}
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '12px' }}>
            <input
              type="checkbox"
              checked={broadcastToClients}
              onChange={(e) => setBroadcastToClients(e.target.checked)}
              style={{ accentColor: '#00f0ff' }}
            />
            <span style={{ color: '#cbd5e1' }}>Broadcast & scale lots across all 5 Client accounts</span>
          </label>

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting}
            style={{
              padding: '12px',
              borderRadius: '8px',
              border: 'none',
              background: direction === 'BUY'
                ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
              color: '#fff',
              fontWeight: 800,
              fontSize: '15px',
              cursor: submitting ? 'not-allowed' : 'pointer',
              letterSpacing: '0.04em',
              boxShadow: direction === 'BUY' ? '0 4px 15px rgba(16,185,129,0.3)' : '0 4px 15px rgba(239,68,68,0.3)'
            }}
          >
            {submitting ? 'Executing via MT5...' : `EXECUTE ${direction} (${qty} LOTS)`}
          </button>
        </form>
      </div>
    </div>
  );
}
