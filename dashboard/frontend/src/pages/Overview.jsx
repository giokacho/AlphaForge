import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { Target, Shield, Crosshair } from 'lucide-react';

const MONO = "'JetBrains Mono', 'Courier New', monospace";

const SectionLabel = ({ children, right }) => (
  <div style={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    color: '#ff6600',
    fontSize: '10px',
    fontWeight: '700',
    letterSpacing: '1.5px',
    borderBottom: '1px solid #222',
    paddingBottom: '6px',
    marginBottom: '12px',
  }}>
    <span>{children}</span>
    {right && <span style={{ color: '#333', fontWeight: '400' }}>{right}</span>}
  </div>
);


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
        console.error('Failed to load overview data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 180000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !data.overview) {
    return (
      <div style={{ color: '#333', fontSize: '11px', letterSpacing: '1px', paddingTop: '40px', textAlign: 'center' }}>
        LOADING TELEMETRY...
      </div>
    );
  }

  const { overview, signals } = data;
  const isOnline = overview.pipeline_status?.verdict === 'OK';
  const activeCount = signals ? Object.values(signals).filter(s => s.direction !== 'NO_SIGNAL').length : 0;

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
    if (status === 'OK') return '#00ff41';
    if (status === 'MISSING_FILE') return '#ffaa00';
    return '#ff3333';
  };

  const getBadges = () => {
    const st = overview.pipeline_status || {};
    return [
      { name: 'MACRO', status: st.context || 'UNKNOWN' },
      { name: 'NEWS', status: st.news || 'UNKNOWN' },
      { name: 'TECH', status: st.technicals || 'UNKNOWN' },
      { name: 'COT', status: st.cot || 'UNKNOWN' },
      { name: 'DEBATE', status: st.debate || 'UNKNOWN' },
      { name: 'RISK', status: st.trade_sheet || 'UNKNOWN' },
    ];
  };

  const dt = overview.last_run_time && overview.last_run_time !== 'N/A'
    ? (() => { const d = new Date(overview.last_run_time); return isNaN(d) ? 'N/A' : d.toLocaleString('en-US', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }); })()
    : 'N/A';

  const conviction = typeof overview.final_conviction === 'number' ? overview.final_conviction : 0;
  const convPct = (conviction / 10) * 100;

  const dirColor = topSignal
    ? topSignal.direction === 'LONG' ? '#00ff41' : '#ff3333'
    : '#666';

  const panel = {
    border: '1px solid #222',
    backgroundColor: '#0d0d0d',
    marginBottom: '12px',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>

      {/* Page label */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '16px' }}>
        <div style={{ color: '#ff6600', fontSize: '13px', fontWeight: '700', letterSpacing: '2px' }}>
          GLOBAL OVERVIEW
        </div>
        <div style={{ color: '#333', fontSize: '10px' }}>SYSTEM TELEMETRY — LIVE PIPELINE</div>
      </div>

      {/* Status Bar — 4 cells */}
      <div style={{ ...panel, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)' }}>
        {[
          {
            label: 'PIPELINE STATUS',
            value: isOnline ? 'OP LIVE' : 'OFFLINE',
            color: isOnline ? '#00ff41' : '#ff3333',
          },
          {
            label: 'LAST RUN',
            value: dt,
            color: '#cccccc',
          },
          {
            label: 'ACTIVE SIGNALS',
            value: `${activeCount} / ${Object.keys(signals || {}).length}`,
            color: activeCount > 0 ? '#00ff41' : '#444',
          },
          {
            label: 'COMBINED RISK',
            value: overview.combined_risk_level || 'UNKNOWN',
            color: '#ffaa00',
          },
        ].map((stat, i) => (
          <div key={i} style={{
            padding: '14px 16px',
            borderRight: i < 3 ? '1px solid #222' : 'none',
          }}>
            <div style={{ color: '#444', fontSize: '10px', letterSpacing: '1px', marginBottom: '8px' }}>
              {stat.label}
            </div>
            <div style={{ color: stat.color, fontSize: '18px', fontWeight: '700', fontFamily: MONO }}>
              {stat.value}
            </div>
          </div>
        ))}
      </div>

      {/* Bot Integrity Array */}
      <div style={{ ...panel }}>
        <div style={{ padding: '10px 16px' }}>
          <SectionLabel right="PIPELINE MODULE STATUS">BOT INTEGRITY ARRAY</SectionLabel>
          <div style={{ display: 'flex', gap: '0', flexWrap: 'wrap' }}>
            {getBadges().map((b, i) => (
              <div key={b.name} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 14px 4px 0',
                marginRight: '14px',
                borderRight: i < 5 ? '1px solid #1a1a1a' : 'none',
                marginBottom: '4px',
              }}>
                <div style={{
                  width: '6px',
                  height: '6px',
                  backgroundColor: getStatusColor(b.status),
                  flexShrink: 0,
                }} />
                <span style={{ color: b.status === 'OK' ? '#555' : getStatusColor(b.status), fontSize: '11px', letterSpacing: '0.5px' }}>
                  {b.name}
                </span>
                <span style={{ color: '#2a2a2a', fontSize: '10px' }}>{b.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Master Conviction Output */}
      <div style={{ ...panel }}>
        <div style={{ padding: '10px 16px', borderBottom: '1px solid #1a1a1a' }}>
          <SectionLabel right="HIGHEST CONVICTION SIGNAL">MASTER CONVICTION OUTPUT</SectionLabel>
        </div>

        {topSignal ? (
          <>
            {/* Asset header row */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '12px 16px',
              borderBottom: '1px solid #1a1a1a',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ color: '#cccccc', fontSize: '22px', fontWeight: '700', fontFamily: MONO }}>
                  {topSignal.asset === 'Gold' ? 'GLD' : topSignal.asset}
                </span>
                <span style={{
                  color: dirColor,
                  fontSize: '11px',
                  fontWeight: '700',
                  padding: '2px 8px',
                  border: `1px solid ${dirColor}`,
                  backgroundColor: `${dirColor}11`,
                  letterSpacing: '1px',
                }}>
                  {topSignal.direction}
                </span>
                <span style={{ color: '#444', fontSize: '11px' }}>
                  BASE SCORE: <span style={{ color: '#ff6600' }}>{topSignal.final_score.toFixed(1)}/10</span>
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#444', fontSize: '10px', letterSpacing: '1px', marginBottom: '4px' }}>CIO CONVICTION</div>
                  <div style={{ color: '#ff6600', fontSize: '20px', fontWeight: '700', fontFamily: MONO }}>
                    {conviction}<span style={{ color: '#333', fontSize: '13px' }}>/10</span>
                  </div>
                </div>
                <div style={{ width: '140px' }}>
                  <div style={{ height: '4px', backgroundColor: '#1a1a1a' }}>
                    <div style={{ height: '100%', width: `${convPct}%`, backgroundColor: '#ff6600', transition: 'width 1s ease' }} />
                  </div>
                </div>
              </div>
            </div>

            {/* Trade detail cells */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)' }}>
              {[
                { label: 'ENTRY ZONE', value: topSignal.entry_zone ? topSignal.entry_zone.join(' – ') : 'N/A', color: '#cccccc', icon: Crosshair },
                { label: 'HARD STOP', value: topSignal.stop_loss ? `$${topSignal.stop_loss}` : 'N/A', color: '#ff3333', icon: Shield },
                { label: 'TARGET 1', value: topSignal.target_1 ? `$${topSignal.target_1}` : 'N/A', color: '#00ff41', icon: Target },
                { label: 'TARGET 2', value: topSignal.target_2 ? `$${topSignal.target_2}` : 'N/A', color: '#00ff41', icon: Target },
              ].map((item, i) => (
                <div key={i} style={{
                  padding: '14px 16px',
                  borderRight: i < 3 ? '1px solid #1a1a1a' : 'none',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#444', fontSize: '10px', letterSpacing: '1px', marginBottom: '8px' }}>
                    <item.icon size={11} />
                    {item.label}
                  </div>
                  <div style={{ color: item.color, fontSize: '15px', fontWeight: '600', fontFamily: MONO }}>
                    {item.value}
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div style={{ padding: '32px 16px', color: '#333', fontSize: '11px', textAlign: 'center', letterSpacing: '1px' }}>
            NO ACTIVE SIGNALS — PIPELINE AWAITING MARKET CONFIRMATION
          </div>
        )}
      </div>

      {/* Asset Signal Matrix */}
      {signals && Object.keys(signals).length > 0 && (
        <div style={{ ...panel }}>
          <div style={{ padding: '10px 16px', borderBottom: '1px solid #1a1a1a' }}>
            <SectionLabel right={`${Object.keys(signals).length} ASSETS MONITORED`}>ASSET SIGNAL MATRIX</SectionLabel>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)' }}>
            {Object.entries(signals).map(([asset, s], i) => {
              const total = Object.keys(signals).length;
              const cols = 5;
              const isLastRow = i >= Math.floor((total - 1) / cols) * cols;
              const isLastCol = (i + 1) % cols === 0 || i === total - 1;
              const dc = s.direction === 'LONG' ? '#00ff41' : s.direction === 'SHORT' ? '#ff3333' : '#444';
              const sc = { STRONG: '#00ff41', SIGNAL: '#ffaa00', WEAK: '#ff6600', NO_SIGNAL: '#333' }[s.signal_strength] || '#333';
              const scorePct = ((s.final_score || 0) / 10) * 100;
              return (
                <div key={asset} style={{
                  padding: '10px 12px',
                  borderRight: !isLastCol ? '1px solid #1a1a1a' : 'none',
                  borderBottom: !isLastRow ? '1px solid #1a1a1a' : 'none',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
                    <span style={{ color: '#ff6600', fontSize: '12px', fontWeight: '700', fontFamily: MONO }}>
                      {s.ticker || asset}
                    </span>
                    <span style={{ color: dc, fontSize: '8px', fontWeight: '700', padding: '1px 5px', border: `1px solid ${dc}44`, backgroundColor: `${dc}0d` }}>
                      {s.direction}
                    </span>
                  </div>
                  <div style={{ height: '3px', backgroundColor: '#111', marginBottom: '5px' }}>
                    <div style={{ height: '100%', width: `${scorePct}%`, backgroundColor: sc, transition: 'width 0.8s ease' }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#333', fontSize: '9px', fontFamily: MONO }}>{(s.final_score || 0).toFixed(1)}/10</span>
                    <span style={{ color: sc, fontSize: '9px', letterSpacing: '0.5px' }}>{(s.signal_strength || '').replace('_', ' ')}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

    </div>
  );
}
