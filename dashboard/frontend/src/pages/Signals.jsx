import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { TrendingUp, TrendingDown, Minus, Target, Shield, Crosshair, AlertOctagon } from 'lucide-react';

const MONO = "'JetBrains Mono', 'Courier New', monospace";

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

  const cardsOrder = ['Gold', 'SPX', 'NQ'];
  const displayNames = {
    Gold: 'GC=F',
    SPX: '^GSPC',
    NQ: '^NDX',
  };
  const fullNames = {
    Gold: 'GOLD FUTURES',
    SPX: 'S&P 500',
    NQ: 'NASDAQ 100',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '16px' }}>
        <div style={{ color: '#ff6600', fontSize: '13px', fontWeight: '700', letterSpacing: '2px' }}>
          ASSET INTRADAY SIGNALS
        </div>
        <div style={{ color: '#333', fontSize: '10px' }}>TECHNICAL + VSA MODULE OUTPUT</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
        {cardsOrder.map(assetKey => {
          const td = signals && signals[assetKey] ? signals[assetKey] : null;
          if (!td) return (
            <div key={assetKey} style={{ border: '1px solid #222', backgroundColor: '#0d0d0d', padding: '16px' }}>
              <div style={{ color: '#333', fontSize: '11px' }}>NO DATA — {assetKey}</div>
            </div>
          );

          const isLong = td.direction === 'LONG';
          const isShort = td.direction === 'SHORT';
          const dirColor = isLong ? '#00ff41' : isShort ? '#ff3333' : '#444';
          const DirIcon = isLong ? TrendingUp : isShort ? TrendingDown : Minus;

          const strengthColor = {
            'STRONG': '#00ff41',
            'SIGNAL': '#ffaa00',
            'WEAK': '#ff6600',
            'NO_SIGNAL': '#333',
          }[td.signal_strength] || '#444';

          return (
            <div key={assetKey} style={{ border: '1px solid #222', backgroundColor: '#0d0d0d', display: 'flex', flexDirection: 'column' }}>

              {/* Card header bar */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                borderBottom: `1px solid ${dirColor}33`,
                backgroundColor: '#0a0a0a',
              }}>
                <div>
                  <span style={{ color: '#ff6600', fontSize: '14px', fontWeight: '700', letterSpacing: '1px', fontFamily: MONO }}>
                    {displayNames[assetKey]}
                  </span>
                  <span style={{ color: '#333', fontSize: '10px', marginLeft: '8px', letterSpacing: '0.5px' }}>
                    {fullNames[assetKey]}
                  </span>
                </div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  color: dirColor,
                  fontSize: '11px',
                  fontWeight: '700',
                  letterSpacing: '1px',
                  padding: '3px 8px',
                  border: `1px solid ${dirColor}`,
                  backgroundColor: `${dirColor}0d`,
                }}>
                  <DirIcon size={12} />
                  {td.direction}
                </div>
              </div>

              {/* Score row */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                borderBottom: '1px solid #1a1a1a',
              }}>
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
                    {td.vsa_flag && td.vsa_flag !== 'NONE' ? td.vsa_flag : 'NONE'}
                  </div>
                </div>
              </div>

              {/* Trade data */}
              <div style={{ padding: '8px 12px', flex: 1 }}>
                <DataRow label="ENTRY ZONE" value={td.entry_zone ? td.entry_zone.join(' – ') : '—'} />
                <DataRow label="STOP LOSS" value={td.stop_loss ? `$${td.stop_loss}` : '—'} valueColor="#ff3333" />
                <DataRow label="TARGET 1" value={td.target_1 ? `$${td.target_1}` : '—'} valueColor="#00ff41" />
                <DataRow label="TARGET 2" value={td.target_2 ? `$${td.target_2}` : '—'} valueColor="#00ff41" />
                <DataRow label="R/R RATIO" value={td.rr_ratio ? `1 : ${td.rr_ratio.toFixed(2)}` : '—'} noBorder />
              </div>

            </div>
          );
        })}
      </div>
    </div>
  );
}
