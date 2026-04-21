import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { theme } from '../styles/theme';
import { TrendingUp, TrendingDown, Minus, Target, Shield, Crosshair, AlertOctagon } from 'lucide-react';

export default function Signals() {
  const [signals, setSignals] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSignals = async () => {
      try {
        const response = await apiClient.get('/api/signals');
        setSignals(response.data);
      } catch (err) {
        console.error("Failed to fetch signals:", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchSignals();
    const interval = setInterval(fetchSignals, 180000); // 3 minutes
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div style={{ color: theme.colors.text.secondary }}>Scanning terminal signals...</div>;
  }

  // Ensure strict ordering: Gold, SPX, NQ
  const cardsOrder = ['Gold', 'SPX', 'NQ'];
  const displayNames = {
      'Gold': 'GC=F (Gold Futures)',
      'SPX': '^GSPC (S&P 500)',
      'NQ': '^NDX (Nasdaq 100)'
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* Header */}
      <div>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '28px', color: theme.colors.text.primary }}>Asset Intraday Signals</h1>
        <p style={{ margin: 0, color: theme.colors.text.secondary, fontSize: '15px' }}>Live breakdown of Technical and VSA output modules.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
        {cardsOrder.map(assetKey => {
            const tickerData = signals && signals[assetKey] ? signals[assetKey] : null;
            if (!tickerData) return null;

            const isLong = tickerData.direction === 'LONG';
            const isShort = tickerData.direction === 'SHORT';
            const dirColor = isLong ? theme.colors.signals.green : isShort ? theme.colors.signals.red : theme.colors.text.secondary;
            const DirIcon = isLong ? TrendingUp : isShort ? TrendingDown : Minus;

            return (
                <div key={assetKey} style={{
                    backgroundColor: theme.colors.background.card,
                    borderRadius: '12px',
                    border: `1px solid ${theme.colors.ui.border}`,
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column'
                }}>
                    {/* Top Bar Accent */}
                    <div style={{ height: '4px', backgroundColor: dirColor, width: '100%' }} />
                    
                    <div style={{ padding: '24px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
                            <div>
                                <h2 style={{ margin: '0 0 4px 0', fontSize: '22px', fontWeight: 'bold', color: theme.colors.text.primary }}>
                                    {displayNames[assetKey]}
                                </h2>
                                <span style={{ color: theme.colors.text.secondary, fontSize: '13px', textTransform: 'uppercase' }}>
                                    {assetKey}
                                </span>
                            </div>
                            
                            <div style={{
                                padding: '6px 12px',
                                backgroundColor: isLong ? 'rgba(34, 197, 94, 0.1)' : isShort ? 'rgba(239, 68, 68, 0.1)' : theme.colors.background.secondary,
                                color: dirColor,
                                borderRadius: '6px',
                                fontWeight: 'bold',
                                fontSize: '13px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px'
                            }}>
                                <DirIcon size={16} />
                                {tickerData.direction}
                            </div>
                        </div>

                        {/* Badges row */}
                        <div style={{ display: 'flex', gap: '12px', marginBottom: '32px', flexWrap: 'wrap' }}>
                            <div style={{ padding: '4px 10px', borderRadius: '4px', backgroundColor: theme.colors.background.secondary, fontSize: '12px', color: theme.colors.text.secondary, border: `1px solid ${theme.colors.ui.border}` }}>
                                Score: <strong style={{ color: theme.colors.text.primary }}>{tickerData.final_score.toFixed(1)}/10</strong>
                            </div>
                            <div style={{ padding: '4px 10px', borderRadius: '4px', backgroundColor: theme.colors.background.secondary, fontSize: '12px', color: theme.colors.text.secondary, border: `1px solid ${theme.colors.ui.border}` }}>
                                Strength: <strong style={{ color: theme.colors.text.primary }}>{tickerData.signal_strength.replace('_', ' ')}</strong>
                            </div>
                            {tickerData.vsa_flag && tickerData.vsa_flag !== 'NONE' && (
                                <div style={{ padding: '4px 10px', borderRadius: '4px', backgroundColor: 'rgba(245, 158, 11, 0.1)', color: theme.colors.signals.neutral, fontSize: '12px', border: `1px solid rgba(245, 158, 11, 0.2)` }}>
                                    VSA: <strong>{tickerData.vsa_flag}</strong>
                                </div>
                            )}
                        </div>

                        {/* Trade Layout */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: `1px solid ${theme.colors.ui.border}` }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: theme.colors.text.secondary, fontSize: '14px' }}>
                                    <Crosshair size={16} /> Entry Zone
                                </div>
                                <span style={{ fontWeight: '600', color: theme.colors.text.primary }}>
                                    {tickerData.entry_zone ? tickerData.entry_zone.join(' - ') : '-'}
                                </span>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: `1px solid ${theme.colors.ui.border}` }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: theme.colors.text.secondary, fontSize: '14px' }}>
                                    <Shield size={16} /> Stop Loss
                                </div>
                                <span style={{ fontWeight: '600', color: theme.colors.signals.red }}>
                                    {tickerData.stop_loss ? `$${tickerData.stop_loss}` : '-'}
                                </span>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: `1px solid ${theme.colors.ui.border}` }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: theme.colors.text.secondary, fontSize: '14px' }}>
                                    <Target size={16} /> Target 1
                                </div>
                                <span style={{ fontWeight: '600', color: theme.colors.signals.green }}>
                                    {tickerData.target_1 ? `$${tickerData.target_1}` : '-'}
                                </span>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: `1px solid ${theme.colors.ui.border}` }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: theme.colors.text.secondary, fontSize: '14px' }}>
                                    <Target size={16} /> Target 2
                                </div>
                                <span style={{ fontWeight: '600', color: theme.colors.signals.green }}>
                                    {tickerData.target_2 ? `$${tickerData.target_2}` : '-'}
                                </span>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: theme.colors.text.secondary, fontSize: '14px' }}>
                                    <AlertOctagon size={16} /> R/R Ratio
                                </div>
                                <span style={{ fontWeight: '600', color: theme.colors.text.primary }}>
                                    {tickerData.rr_ratio ? `1:${tickerData.rr_ratio.toFixed(2)}` : '-'}
                                </span>
                            </div>

                        </div>
                    </div>
                </div>
            )
        })}
      </div>
    </div>
  );
}
