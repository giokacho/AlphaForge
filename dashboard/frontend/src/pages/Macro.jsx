import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';

const MONO = "'JetBrains Mono', 'Courier New', monospace";

const SectionLabel = ({ children, right }) => (
  <div style={{
    display: 'flex',
    justifyContent: 'space-between',
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

const DataRow = ({ label, value, valueColor = '#cccccc', noBorder }) => (
  <div style={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '5px 0',
    borderBottom: noBorder ? 'none' : '1px solid #181818',
    fontSize: '12px',
  }}>
    <span style={{ color: '#444' }}>{label}</span>
    <span style={{ color: valueColor, fontFamily: MONO }}>{value}</span>
  </div>
);

export default function Macro() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/api/macro');
        setData(response.data);
      } catch (err) {
        console.error('Failed to load macro', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 180000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !data) {
    return <div style={{ color: '#333', fontSize: '11px', letterSpacing: '1px', paddingTop: '40px', textAlign: 'center' }}>SCANNING MACRO INTELLIGENCE...</div>;
  }

  const regimeColors = {
    RISK_ON: '#00ff41',
    RISK_OFF: '#ff3333',
    TRANSITION: '#ffaa00',
    UNKNOWN: '#333',
  };
  const rgColor = regimeColors[data.macro_regime] || regimeColors.UNKNOWN;

  const hd = typeof data.hawk_dove_score === 'number' ? data.hawk_dove_score : 0;
  const hdPercent = ((hd + 5) / 10) * 100;
  const hdColor = hd > 1 ? '#ff3333' : hd < -1 ? '#00ff41' : '#ffaa00';

  const panel = { border: '1px solid #222', backgroundColor: '#0d0d0d', marginBottom: '12px' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '16px' }}>
        <div style={{ color: '#ff6600', fontSize: '13px', fontWeight: '700', letterSpacing: '2px' }}>
          MACRO & SENTIMENT
        </div>
        <div style={{ color: '#333', fontSize: '10px' }}>GLOBAL REGIME × CENTRAL BANK NARRATIVE</div>
      </div>

      {/* Top row: regime + hawk/dove */}
      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', marginBottom: '12px' }}>

        {/* Regime panel */}
        <div style={{ border: '1px solid #222', backgroundColor: '#0d0d0d', padding: '14px' }}>
          <SectionLabel>MACRO REGIME</SectionLabel>
          <div style={{ textAlign: 'center', paddingTop: '8px' }}>
            <div style={{
              color: rgColor,
              fontSize: '20px',
              fontWeight: '700',
              fontFamily: MONO,
              letterSpacing: '2px',
              padding: '10px',
              border: `1px solid ${rgColor}44`,
              backgroundColor: `${rgColor}0a`,
            }}>
              {data.macro_regime || 'UNKNOWN'}
            </div>
          </div>
        </div>

        {/* Hawk/Dove panel */}
        <div style={{ border: '1px solid #222', backgroundColor: '#0d0d0d', padding: '14px' }}>
          <SectionLabel right={`${hd >= 0 ? '+' : ''}${hd.toFixed(2)}`}>CENTRAL BANK BIAS (HAWK / DOVE)</SectionLabel>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#2a2a2a', marginBottom: '8px' }}>
            <span>-5 DOVISH</span>
            <span>NEUTRAL</span>
            <span>+5 HAWKISH</span>
          </div>
          <div style={{ position: 'relative', height: '8px', backgroundColor: '#111' }}>
            <div style={{ position: 'absolute', left: '50%', height: '100%', width: '1px', backgroundColor: '#2a2a2a' }} />
            <div style={{
              position: 'absolute',
              top: '-4px',
              bottom: '-4px',
              left: `calc(${hdPercent}% - 3px)`,
              width: '6px',
              backgroundColor: hdColor,
              transition: 'left 1s ease',
            }} />
          </div>
          <div style={{ marginTop: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ height: '3px', flex: 1, backgroundColor: '#111', position: 'relative' }}>
                <div style={{
                  position: 'absolute',
                  height: '100%',
                  backgroundColor: hdColor,
                  left: hd >= 0 ? '50%' : `${hdPercent}%`,
                  width: hd >= 0 ? `${(hd / 10) * 100}%` : `${50 - hdPercent}%`,
                }} />
              </div>
              <span style={{ color: hdColor, fontSize: '14px', fontWeight: '700', fontFamily: MONO, width: '50px', textAlign: 'right' }}>
                {hd >= 0 ? '+' : ''}{hd.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

      </div>

      {/* Indicator Sentiment Scorer */}
      <div style={{ ...panel, padding: '14px' }}>
        <SectionLabel>INDICATOR SENTIMENT SCORER</SectionLabel>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
          {Object.entries(data.sentiment_scores || {}).map(([indicator, details]) => {
            const score = details.score || 0;
            const direction = details.direction || 'NEUTRAL';
            const sColor = score > 0 ? '#00ff41' : score < 0 ? '#ff3333' : '#444';
            const widthMult = Math.abs(score);

            return (
              <div key={indicator} style={{ border: '1px solid #1a1a1a', padding: '8px 10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ color: '#555', fontSize: '10px', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
                    {indicator.replace(/_/g, ' ')}
                  </span>
                  <span style={{ color: sColor, fontSize: '10px', fontWeight: '700' }}>{direction}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: sColor, width: '36px', textAlign: 'right', fontSize: '11px', fontFamily: MONO }}>
                    {score >= 0 ? '+' : ''}{score.toFixed(2)}
                  </span>
                  <div style={{ flex: 1, position: 'relative', height: '4px', backgroundColor: '#111' }}>
                    <div style={{ position: 'absolute', left: '50%', height: '100%', width: '1px', backgroundColor: '#2a2a2a' }} />
                    <div style={{
                      position: 'absolute',
                      height: '100%',
                      backgroundColor: sColor,
                      left: score > 0 ? '50%' : `calc(50% - ${widthMult * 50}%)`,
                      width: `${widthMult * 50}%`,
                    }} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Narrative Momentum */}
      <div style={{ ...panel, padding: '14px' }}>
        <SectionLabel>NARRATIVE MOMENTUM</SectionLabel>
        {(() => {
          const nm = (typeof data.narrative_momentum === 'object' && data.narrative_momentum !== null)
            ? data.narrative_momentum : {};
          const rows = [
            { label: 'GOLD CHANGE', val: nm.gold_change },
            { label: 'SPX CHANGE', val: nm.spx_change },
            { label: 'NQ CHANGE', val: nm.nq_change },
          ];
          const shifting = Array.isArray(nm.shifting_assets) && nm.shifting_assets.length > 0
            ? nm.shifting_assets.join(', ') : 'NONE';
          return (
            <>
              {rows.map(({ label, val }) => {
                const n = typeof val === 'number' ? val : 0;
                const color = n > 0 ? '#00ff41' : n < 0 ? '#ff3333' : '#444';
                return (
                  <DataRow key={label} label={label} value={`${n >= 0 ? '+' : ''}${n.toFixed(4)}`} valueColor={color} />
                );
              })}
              <DataRow label="SHIFTING ASSETS" value={shifting} valueColor="#ffaa00" noBorder />
            </>
          );
        })()}
      </div>

      {/* Macro Briefing */}
      {data.narrative_text && (
        <div style={{ ...panel, padding: '14px' }}>
          <SectionLabel>MACRO BRIEFING</SectionLabel>
          <div style={{
            color: '#555',
            fontSize: '12px',
            lineHeight: '1.7',
            whiteSpace: 'pre-wrap',
            fontFamily: MONO,
          }}>
            {data.narrative_text}
          </div>
        </div>
      )}

    </div>
  );
}
