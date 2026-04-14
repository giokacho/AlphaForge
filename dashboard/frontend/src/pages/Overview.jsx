import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { theme } from '../styles/theme';
import { Activity, Clock, ShieldCheck, AlertTriangle, TrendingUp, TrendingDown, Target, Shield, Crosshair } from 'lucide-react';

export default function Overview() {
  const [data, setData] = useState({ overview: null, signals: null });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ovRes, sigRes] = await Promise.all([
          apiClient.get('/api/overview'),
          apiClient.get('/api/signals')
        ]);
        setData({ overview: ovRes.data, signals: sigRes.data });
      } catch (err) {
        console.error("Failed to load overview data", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 180000); // 3 minutes
    return () => clearInterval(interval);
  }, []);

  if (loading || !data.overview) {
    return <div style={{ color: theme.colors.text.secondary }}>Loading telemetry...</div>;
  }

  const { overview, signals } = data;
  const isOnline = overview.pipeline_status?.verdict === 'OK';
  
  // Count active signals
  const activeCount = signals ? Object.values(signals).filter(s => s.direction !== 'NO_SIGNAL').length : 0;
  
  // Find top signal
  let topSignal = null;
  if (signals) {
    let maxScore = -999;
    for (const [asset, sData] of Object.entries(signals)) {
      if (sData.direction !== 'NO_SIGNAL' && sData.final_score > maxScore) {
        maxScore = sData.final_score;
        topSignal = { asset, ...sData };
      }
    }
  }

  const getStatusColor = (status) => {
    if (status === 'OK') return theme.colors.signals.green;
    if (status === 'MISSING_FILE') return theme.colors.signals.neutral;
    return theme.colors.signals.red;
  };

  const getBadges = () => {
    const st = overview.pipeline_status || {};
    return [
      { name: 'Macro', status: st.context || 'UNKNOWN' },
      { name: 'News', status: st.news || 'UNKNOWN' },
      { name: 'Technicals', status: st.technicals || 'UNKNOWN' },
      { name: 'COT', status: st.cot || 'UNKNOWN' },
      { name: 'Debate', status: st.debate || 'UNKNOWN' },
      { name: 'Risk', status: st.trade_sheet || 'UNKNOWN' },
    ];
  };

  const dt = overview.last_run_time !== 'N/A' 
        ? new Date(overview.last_run_time).toLocaleString() 
        : 'N/A';

  // Format Conviction
  const conviction = typeof overview.final_conviction === 'number' ? overview.final_conviction : 0;
  const convPct = (conviction / 10) * 100;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* Top Header */}
      <div>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '28px', color: theme.colors.text.primary }}>Global Overview</h1>
        <p style={{ margin: 0, color: theme.colors.text.secondary, fontSize: '15px' }}>System telemetry securely pulled from the core pipeline.</p>
      </div>

      {/* 4 Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
        {[
          { label: 'Pipeline Status', value: isOnline ? 'OP LIVE' : 'OFFLINE', color: isOnline ? theme.colors.signals.green : theme.colors.signals.red, icon: isOnline ? ShieldCheck : AlertTriangle },
          { label: 'Last Run Time', value: dt, color: theme.colors.text.primary, icon: Clock, small: true },
          { label: 'Active Signals', value: activeCount, color: activeCount > 0 ? theme.colors.signals.green : theme.colors.text.secondary, icon: Activity },
          { label: 'Combined Risk Level', value: overview.combined_risk_level || 'UNKNOWN', color: theme.colors.signals.neutral, icon: AlertTriangle }
        ].map((stat, i) => (
          <div key={i} style={{
            backgroundColor: theme.colors.background.card,
            padding: '24px',
            borderRadius: '12px',
            border: `1px solid ${theme.colors.ui.border}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ color: theme.colors.text.secondary, fontSize: '14px', fontWeight: '500' }}>{stat.label}</span>
              <stat.icon size={20} color={stat.color} />
            </div>
            <div style={{ 
              fontSize: stat.small ? '18px' : '28px', 
              fontWeight: 'bold', 
              color: stat.color 
            }}>
              {stat.value}
            </div>
          </div>
        ))}
      </div>

      {/* Pipeline Status Badges */}
      <div style={{
        backgroundColor: theme.colors.background.card,
        padding: '24px',
        borderRadius: '12px',
        border: `1px solid ${theme.colors.ui.border}`,
      }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: theme.colors.text.primary }}>Bot Integrity Array</h3>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {getBadges().map((b) => (
            <div key={b.name} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: theme.colors.background.secondary,
              padding: '8px 16px',
              borderRadius: '20px',
              border: `1px solid ${theme.colors.ui.border}`
            }}>
              <div style={{ 
                width: '10px', 
                height: '10px', 
                borderRadius: '50%', 
                backgroundColor: getStatusColor(b.status),
                boxShadow: `0 0 8px ${getStatusColor(b.status)}`
              }} />
              <span style={{ fontSize: '14px', fontWeight: '500', color: theme.colors.text.primary }}>{b.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Top Signal Large Card */}
      <div>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: theme.colors.text.primary }}>Master Conviction Output</h3>
        {topSignal ? (
          <div style={{
            backgroundColor: theme.colors.background.card,
            padding: '32px',
            borderRadius: '12px',
            border: `1px solid ${theme.colors.ui.border}`,
            position: 'relative',
            overflow: 'hidden'
          }}>
             {/* Background glow accent */}
             <div style={{
                position: 'absolute',
                top: 0, left: 0, right: 0, height: '4px',
                background: topSignal.direction === 'LONG' ? theme.colors.signals.green : theme.colors.signals.red
             }} />

             <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
                <div>
                  <h2 style={{ fontSize: '36px', fontWeight: 'bold', margin: '0 0 8px 0', color: theme.colors.text.primary }}>
                    {topSignal.asset === 'Gold' ? 'GLD' : topSignal.asset}
                  </h2>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                     <span style={{
                        padding: '6px 12px',
                        backgroundColor: topSignal.direction === 'LONG' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        color: topSignal.direction === 'LONG' ? theme.colors.signals.green : theme.colors.signals.red,
                        borderRadius: '6px',
                        fontWeight: 'bold',
                        fontSize: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                     }}>
                        {topSignal.direction === 'LONG' ? <TrendingUp size={16}/> : <TrendingDown size={16}/>}
                        {topSignal.direction}
                     </span>
                     <span style={{ color: theme.colors.text.secondary, fontSize: '14px' }}>
                        Base Score: <strong style={{ color: theme.colors.text.primary }}>{topSignal.final_score.toFixed(1)}/10</strong>
                     </span>
                  </div>
                </div>

                <div style={{ width: '250px' }}>
                   <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', marginBottom: '8px' }}>
                      <span style={{ color: theme.colors.text.secondary }}>CIO Conviction</span>
                      <span style={{ color: theme.colors.text.primary, fontWeight: 'bold' }}>{conviction}/10</span>
                   </div>
                   <div style={{ height: '8px', backgroundColor: theme.colors.background.secondary, borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ 
                        height: '100%', 
                        width: `${convPct}%`, 
                        backgroundColor: theme.colors.accent.blue,
                        transition: 'width 1s ease-in-out'
                      }} />
                   </div>
                </div>
             </div>

             <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px', backgroundColor: theme.colors.background.secondary, padding: '24px', borderRadius: '8px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                   <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: theme.colors.text.secondary }}>
                      <Crosshair size={18} /> <span style={{ fontSize: '14px' }}>Target Entry Zone</span>
                   </div>
                   <span style={{ fontSize: '20px', fontWeight: 'bold', color: theme.colors.text.primary }}>
                     {topSignal.entry_zone ? topSignal.entry_zone.join(' - ') : 'Awaiting confirmation'}
                   </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                   <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: theme.colors.text.secondary }}>
                      <Shield size={18} /> <span style={{ fontSize: '14px' }}>Hard Stop Loss</span>
                   </div>
                   <span style={{ fontSize: '20px', fontWeight: 'bold', color: theme.colors.signals.red }}>
                     {topSignal.stop_loss ? `$${topSignal.stop_loss}` : 'N/A'}
                   </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                   <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: theme.colors.text.secondary }}>
                      <Target size={18} /> <span style={{ fontSize: '14px' }}>Primary Targets</span>
                   </div>
                   <div style={{ display: 'flex', gap: '12px', fontSize: '18px', fontWeight: 'bold', color: theme.colors.signals.green }}>
                     <span>T1: {topSignal.target_1 ? `$${topSignal.target_1}` : 'N/A'}</span>
                     {topSignal.target_2 && <span style={{ color: theme.colors.text.secondary }}>| T2: ${topSignal.target_2}</span>}
                   </div>
                </div>
             </div>

          </div>
        ) : (
          <div style={{ color: theme.colors.text.secondary, fontStyle: 'italic', padding: '32px', backgroundColor: theme.colors.background.card, borderRadius: '12px', border: `1px solid ${theme.colors.ui.border}` }}>
            No active institutional signals approved by the pipeline at this time.
          </div>
        )}
      </div>

    </div>
  );
}
