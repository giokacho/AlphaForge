import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { TrendingUp, TrendingDown, Minus, Target, Shield, Crosshair } from 'lucide-react';

const MONO = "'JetBrains Mono', 'Courier New', monospace";

const FULL_NAMES = {
  Gold:   'GOLD FUTURES',
  SPX:    'S&P 500',
  NQ:     'NASDAQ 100',
  DOW:    'DOW JONES',
  BTC:    'BITCOIN',
  ETH:    'ETHEREUM',
  Oil:    'CRUDE OIL',
  EURUSD: 'EUR / USD',
  USDJPY: 'USD / JPY',
  USDCAD: 'USD / CAD',
};

const DataRow = ({ label, value, valueColor = '#cccccc', noBorder }) => (
  <div style={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '6px 0',
    borderBottom: noBorder ? 'none' : '1px solid #181818',
    fontSize: '12px',
  }}>
    <span style={{ color: '#444', fontSize: '11px' }}>{label}</span>
    <span style={{ color: valueColor, fontFamily: MONO }}>{value}</span>
  </div>
);

export default function Signals() {
  const [signals, setSignals] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSignals = async () => {
      try {
        const response = await apiClient.get('/api/signals');
        setSignals(response.data);
      } catch (err) {
        console.error('Failed to fetch signals:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSignals();
    const interval = setInterval(fetchSignals, 180000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div style={{ color: '#333', fontSize: '11px', letterSpacing: '1px', paddingTop: '40px', textAlign: 'center' }}>SCANNING SIGNALS...</div>;
  }

  const assetKeys = signals ? Object.keys(signals) : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '16px' }}>
        <div style={{ color: '#ff6600', fontSize: '13px', fontWeight: '700', letterSpacing: '2px' }}>
          ASSET INTRADAY SIGNALS
        </div>
        <div style={{ color: '#333', fontSize: '10px' }}>TECHNICAL + VSA MODULE OUTPUT — {assetKeys.length} ASSETS</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '12px' }}>
        {assetKeys.map(assetKey => {
          const td = signals[assetKey];
          if (!td) return (
            <div key={assetKey} style={{ border: '1px solid #222', backgroundColor: '#0d0d0d', padding: '16px' }}>
              <div style={{ color: '#333', fontSize: '11px' }}>NO DATA — {assetKey}</div>
            </div>
          );

          const isLong  = td.direction === 'LONG';
          const isShort = td.direction === 'SHORT';
          const dColor  = isLong ? '#00ff41' : isShort ? '#ff3333' : '#444';
          const DirIcon = isLong ? TrendingUp : isShort ? TrendingDown : Minus;

          const strengthColor = {
            'STRONG':    '#00ff41',
            'SIGNAL':    '#ffaa00',
            'WEAK':      '#ff6600',
            'NO_SIGNAL': '#333',
          }[td.signal_strength] || '#444';

          const ticker    = td.ticker || assetKey;
          const fullName  = FULL_NAMES[assetKey] || assetKey;
          const hasPrice  = td.stop_loss || td.target_1;
          const fmtPrice  = (v) => v ? v.toFixed(4) : '—';

          const ezStr = Array.isArray(td.entry_zone) && td.entry_zone.length === 2
            ? `${td.entry_zone[0].toFixed(2)} – ${td.entry_zone[1].toFixed(2)}`
            : '—';

          return (
            <div key={assetKey} style={{ border: '1px solid #222', backgroundColor: '#0d0d0d', display: 'flex', flexDirection: 'column' }}>

              {/* Card header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                borderBottom: `1px solid ${dColor}33`,
                backgroundColor: '#0a0a0a',
              }}>
                <div>
                  <span style={{ color: '#ff6600', fontSize: '14px', fontWeight: '700', letterSpacing: '1px', fontFamily: MONO }}>
                    {ticker}
                  </span>
                  <span style={{ color: '#333', fontSize: '10px', marginLeft: '8px', letterSpacing: '0.5px' }}>
                    {fullName}
                  </span>
                </div>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '5px',
                  color: dColor, fontSize: '11px', fontWeight: '700', letterSpacing: '1px',
                  padding: '3px 8px', border: `1px solid ${dColor}`, backgroundColor: `${dColor}0d`,
                }}>
                  <DirIcon size={12} />
                  {td.direction}
                </div>
              </div>

              {/* Score row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', borderBottom: '1px solid #1a1a1a' }}>
                <div style={{ padding: '8px 12px', borderRight: '1px solid #1a1a1a' }}>
                  <div style={{ color: '#444', fontSize: '9px', letterSpacing: '1px', marginBottom: '3px' }}>SCORE</div>
                  <div style={{ color: '#ff6600', fontSize: '16px', fontWeight: '700', fontFamily: MONO }}>
                    {td.final_score.toFixed(1)}<span style={{ color: '#333', fontSize: '11px' }}>/10</span>
                  </div>
                </div>
                <div style={{ padding: '8px 12px', borderRight: '1px solid #1a1a1a' }}>
                  <div style={{ color: '#444', fontSize: '9px', letterSpacing: '1px', marginBottom: '3px' }}>STRENGTH</div>
                  <div style={{ color: strengthColor, fontSize: '12px', fontWeight: '600', fontFamily: MONO }}>
                    {td.signal_strength.replace('_', ' ')}
                  </div>
                </div>
                <div style={{ padding: '8px 12px' }}>
                  <div style={{ color: '#444', fontSize: '9px', letterSpacing: '1px', marginBottom: '3px' }}>VSA FLAG</div>
                  <div style={{ color: td.vsa_flag && td.vsa_flag !== 'NONE' ? '#ffaa00' : '#2a2a2a', fontSize: '11px', fontWeight: '600', fontFamily: MONO }}>
                    {td.vsa_flag || 'NONE'}
                  </div>
                </div>
              </div>

              {/* Trade data */}
              <div style={{ padding: '8px 12px', flex: 1 }}>
                <DataRow label="ENTRY ZONE" value={ezStr} />
                <DataRow label="STOP LOSS"  value={fmtPrice(td.stop_loss)}  valueColor="#ff3333" />
                <DataRow label="TARGET 1"   value={fmtPrice(td.target_1)}   valueColor="#00ff41" />
                <DataRow label="TARGET 2"   value={fmtPrice(td.target_2)}   valueColor="#00ff41" />
                <DataRow label="R/R RATIO"  value={td.rr_ratio ? `1 : ${td.rr_ratio.toFixed(2)}` : '—'} noBorder />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
