import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { theme } from '../styles/theme';

export default function COT() {
  const [data, setData] = useState({ cot: null, signals: null });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [cotRes, sigRes] = await Promise.all([
           apiClient.get('/api/cot'),
           apiClient.get('/api/signals')
        ]);
        setData({ cot: cotRes.data, signals: sigRes.data });
      } catch (err) {
        console.error("Failed to load COT", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 180000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !data.cot || !data.signals) {
    return <div style={{ color: theme.colors.text.secondary }}>Loading COT and technical positioning...</div>;
  }

  const assets = [
      { id: 'Gold', name: 'GLD (Physical Gold)' },
      { id: '^GSPC', name: 'SPY (S&P 500)' },
      { id: '^NDX', name: 'QQQ (Nasdaq 100)' }
  ];
  
  const getCrowdingColor = (rs) => {
      if (rs === 'LOW') return theme.colors.signals.green;
      if (rs === 'HIGH') return theme.colors.signals.red;
      return theme.colors.signals.neutral; // MEDIUM
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '28px', color: theme.colors.text.primary }}>Institutional & Technical Profiles</h1>
        <p style={{ margin: 0, color: theme.colors.text.secondary, fontSize: '15px' }}>Commitment of Traders (CoT) positioning intersecting with multi-factor technicals.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
        {assets.map(asset => {
            const cotData = data.cot[asset.id] || {};
            const sigData = data.signals[asset.id] || {};
            
            const bias = cotData.institutional_bias || 'UNKNOWN';
            const bColor = bias.includes('LONG') ? theme.colors.signals.green : bias.includes('SHORT') ? theme.colors.signals.red : theme.colors.text.secondary;
            
            const pTile = typeof cotData.positioning_percentile === 'number' ? cotData.positioning_percentile : 50;
            const ptColor = pTile >= 90 ? theme.colors.signals.green : pTile <= 10 ? theme.colors.signals.red : theme.colors.text.secondary;

            return (
                <div key={asset.id} style={{
                    backgroundColor: theme.colors.background.card,
                    borderRadius: '12px',
                    border: `1px solid ${theme.colors.ui.border}`,
                    padding: '24px',
                    display: 'flex',
                    flexDirection: 'column'
                }}>
                    <div style={{ marginBottom: '24px' }}>
                        <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: theme.colors.text.primary }}>{asset.name}</h2>
                        <span style={{ color: theme.colors.text.secondary, fontSize: '13px' }}>{asset.id}</span>
                    </div>

                    {/* COT Section */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center', marginBottom: '16px' }}>
                        <div style={{
                            padding: '6px 12px',
                            backgroundColor: `${bColor}22`,
                            color: bColor,
                            borderRadius: '4px',
                            fontWeight: 'bold',
                            fontSize: '13px',
                            border: `1px solid ${bColor}44`,
                            width: '100%',
                            textAlign: 'center'
                        }}>
                            Bias: {bias}
                        </div>

                        <div style={{ textAlign: 'center', margin: '16px 0' }}>
                            <span style={{ color: theme.colors.text.secondary, fontSize: '13px' }}>Positioning Percentile</span>
                            <div style={{
                                width: '120px',
                                height: '120px',
                                borderRadius: '50%',
                                background: `conic-gradient(${ptColor} ${pTile}%, ${theme.colors.background.secondary} 0)`,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                margin: '12px auto'
                            }}>
                                <div style={{
                                    width: '100px', height: '100px', 
                                    borderRadius: '50%', 
                                    backgroundColor: theme.colors.background.card,
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontSize: '24px', fontWeight: 'bold', color: theme.colors.text.primary
                                }}>
                                    {typeof cotData.positioning_percentile === 'number' ? `${pTile.toFixed(0)}%` : 'N/A'}
                                </div>
                            </div>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', padding: '0 8px', fontSize: '14px' }}>
                           <span style={{ color: theme.colors.text.secondary }}>Crowding Risk</span>
                           <span style={{ color: getCrowdingColor(cotData.crowding_risk), fontWeight: 'bold' }}>
                               {cotData.crowding_risk || 'UNKNOWN'}
                           </span>
                        </div>
                    </div>

                    {/* Technicals Panel */}
                    <div style={{ marginTop: '24px', paddingTop: '24px', borderTop: `1px solid ${theme.colors.ui.border}` }}>
                       <h4 style={{ color: theme.colors.text.primary, margin: '0 0 16px 0', fontSize: '15px' }}>Core Technicals</h4>
                       <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px' }}>
                           <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                               <span style={{ color: theme.colors.text.secondary }}>Weekly Gate</span>
                               <span style={{ color: theme.colors.text.primary, fontWeight: 'bold' }}>{sigData.weekly_gate || '-'}</span>
                           </div>
                           <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                               <span style={{ color: theme.colors.text.secondary }}>ATR Regime</span>
                               <span style={{ color: theme.colors.text.primary, fontWeight: 'bold' }}>{sigData.atr_regime || '-'}</span>
                           </div>
                           <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                               <span style={{ color: theme.colors.text.secondary }}>4H Entry Mode</span>
                               <span style={{ color: theme.colors.text.primary, fontWeight: 'bold' }}>{sigData.entry_mode || '-'}</span>
                           </div>
                           <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                               <span style={{ color: theme.colors.text.secondary }}>VSA Signature</span>
                               <span style={{ color: theme.colors.signals.neutral, fontWeight: 'bold' }}>{sigData.vsa_flag || 'NONE'}</span>
                           </div>
                       </div>
                       
                       <h4 style={{ color: theme.colors.text.primary, margin: '24px 0 12px 0', fontSize: '14px' }}>Factor Signatures</h4>
                       <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                           {Object.entries(sigData.factors || {}).map(([fk, fv]) => {
                               let fColor = theme.colors.text.secondary;
                               let bgFill = theme.colors.background.secondary;
                               if (fv >= 1) { fColor = theme.colors.signals.green; bgFill = 'rgba(34, 197, 94, 0.1)'; }
                               if (fv <= -1) { fColor = theme.colors.signals.red; bgFill = 'rgba(239, 68, 68, 0.1)'; }
                               
                               return (
                                   <div key={fk} style={{
                                       padding: '4px 8px',
                                       borderRadius: '4px',
                                       backgroundColor: bgFill,
                                       border: `1px solid ${fColor}44`,
                                       color: fColor,
                                       fontSize: '11px',
                                       fontWeight: 'bold',
                                       letterSpacing: '0.5px'
                                   }}>
                                       {fk}: {fv}
                                   </div>
                               );
                           })}
                       </div>
                    </div>

                </div>
            );
        })}
      </div>
    </div>
  );
}
