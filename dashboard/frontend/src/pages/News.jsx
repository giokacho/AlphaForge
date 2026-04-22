import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react';

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

const SHORT_NAMES = {
  'Fed Policy':       'FED',
  'Inflation':        'INFL',
  'GDP / Growth':     'GDP',
  'Employment':       'EMP',
  'Geopolitics':      'GEO',
  'Risk Appetite':    'RISK',
  'Earnings':         'EARN',
  'Dollar Strength':  'DXY',
  'Commodity Demand': 'CMDTY',
};

function CategoryRadar({ categories }) {
  const keys = Object.keys(categories);
  const N = keys.length;
  const cx = 110, cy = 110, R = 80;

  const pt = (i, r) => {
    const phi = (i / N) * 2 * Math.PI;
    return { x: cx + r * Math.sin(phi), y: cy - r * Math.cos(phi) };
  };

  // map score [-1..+1] → [0..R]; center = -1, middle = neutral, edge = +1
  const toR = (v) => ((Math.max(-1, Math.min(1, v || 0)) + 1) / 2) * R;

  const dataPoints = keys.map((k, i) => pt(i, toR(categories[k].score || 0)));
  const polygon = dataPoints.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');

  return (
    <svg width="220" height="220" viewBox="0 0 220 220" style={{ overflow: 'visible', flexShrink: 0 }}>
      {[0.25, 0.5, 0.75, 1.0].map(lvl => {
        const pts = keys.map((_, i) => { const p = pt(i, lvl * R); return `${p.x.toFixed(1)},${p.y.toFixed(1)}`; }).join(' ');
        return <polygon key={lvl} points={pts} fill="none" stroke={lvl === 0.5 ? '#282828' : '#181818'} strokeWidth={lvl === 0.5 ? '1.5' : '1'} />;
      })}
      {keys.map((_, i) => { const e = pt(i, R); return <line key={i} x1={cx} y1={cy} x2={e.x.toFixed(1)} y2={e.y.toFixed(1)} stroke="#1e1e1e" strokeWidth="1" />; })}
      <polygon points={polygon} fill="#ff660012" stroke="#ff6600" strokeWidth="1.5" strokeLinejoin="round" />
      {dataPoints.map((p, i) => {
        const cat = categories[keys[i]];
        const c = cat.available !== false
          ? (cat.direction === 'BULLISH' ? '#00ff41' : cat.direction === 'BEARISH' ? '#ff3333' : '#ffaa00')
          : '#2a2a2a';
        return <circle key={i} cx={p.x.toFixed(1)} cy={p.y.toFixed(1)} r="3.5" fill={c} />;
      })}
      <circle cx={cx} cy={cy} r="2" fill="#222" />
      {keys.map((k, i) => {
        const lp = pt(i, R + 16);
        const available = categories[k].available !== false;
        return (
          <text key={i} x={lp.x.toFixed(1)} y={lp.y.toFixed(1)}
            textAnchor="middle" dominantBaseline="middle"
            fill={available ? '#444' : '#282828'} fontSize="8"
            fontFamily="'JetBrains Mono', monospace" letterSpacing="0.3">
            {SHORT_NAMES[k] || k.slice(0, 5)}
          </text>
        );
      })}
    </svg>
  );
}

function dirColor(direction) {
  if (direction === 'BULLISH') return '#00ff41';
  if (direction === 'BEARISH') return '#ff3333';
  return '#444';
}

function nmBadge(nm) {
  if (!nm || typeof nm !== 'object') return 'STABLE';
  const total = Math.abs(nm.gold_change || 0) + Math.abs(nm.spx_change || 0) + Math.abs(nm.nq_change || 0);
  if (total < 0.05) return 'STABLE';
  const net = (nm.gold_change || 0) + (nm.spx_change || 0) + (nm.nq_change || 0);
  return net >= 0 ? 'ACCELERATING' : 'REVERSING';
}

function nmBadgeColor(badge) {
  if (badge === 'ACCELERATING') return '#00ff41';
  if (badge === 'REVERSING') return '#ff3333';
  return '#ffaa00';
}

export default function News() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/api/news');
        setData(response.data);
      } catch (err) {
        console.error('Failed to load news', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 180000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !data) {
    return <div style={{ color: '#333', fontSize: '11px', letterSpacing: '1px', paddingTop: '40px', textAlign: 'center' }}>LOADING NEWS INTELLIGENCE...</div>;
  }

  const badge = nmBadge(data.narrative_momentum);
  const badgeColor = nmBadgeColor(badge);
  const categories = data.categories || {};
  const panel = { border: '1px solid #222', backgroundColor: '#0d0d0d', marginBottom: '12px' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ color: '#ff6600', fontSize: '13px', fontWeight: '700', letterSpacing: '2px' }}>
          NEWS INTELLIGENCE
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <div style={{
            padding: '3px 10px',
            border: `1px solid ${badgeColor}`,
            backgroundColor: `${badgeColor}0d`,
            color: badgeColor,
            fontSize: '10px',
            fontWeight: '700',
            letterSpacing: '1px',
            fontFamily: MONO,
          }}>
            {badge}
          </div>
          <div style={{
            padding: '3px 10px',
            border: '1px solid #222',
            backgroundColor: '#0d0d0d',
            color: '#444',
            fontSize: '10px',
            fontWeight: '700',
            letterSpacing: '1px',
            fontFamily: MONO,
          }}>
            EVT RISK: {data.forward_event_risk || 'N/A'}
          </div>
        </div>
      </div>

      {/* Contradiction Banner */}
      {data.contradiction_flag && (
        <div style={{
          border: '1px solid #ff333344',
          backgroundColor: '#1a0000',
          padding: '10px 14px',
          marginBottom: '12px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '10px',
        }}>
          <AlertTriangle size={14} color="#ff3333" style={{ flexShrink: 0, marginTop: '1px' }} />
          <div>
            <div style={{ color: '#ff3333', fontSize: '10px', fontWeight: '700', letterSpacing: '1px', marginBottom: '3px' }}>
              CONTRADICTION DETECTED
            </div>
            <div style={{ color: '#555', fontSize: '11px', lineHeight: '1.5' }}>
              {data.contradiction_reason || 'Conflicting signals across fundamental categories.'}
            </div>
          </div>
        </div>
      )}

      {/* Category Sentiment Grid */}
      <div style={{ ...panel, padding: '14px' }}>
        <SectionLabel right="9-CATEGORY ANALYSIS">CATEGORY SENTIMENT SCORES</SectionLabel>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-start' }}>
          <CategoryRadar categories={categories} />
          <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', alignContent: 'start' }}>
          {Object.entries(categories).map(([label, cat]) => {
            const score = cat.score || 0;
            const direction = cat.direction || 'NEUTRAL';
            const available = cat.available !== false;
            const sColor = available ? dirColor(direction) : '#2a2a2a';
            const DirIcon = direction === 'BULLISH' ? TrendingUp : direction === 'BEARISH' ? TrendingDown : Minus;

            return (
              <div key={label} style={{
                border: '1px solid #1a1a1a',
                padding: '8px 10px',
                opacity: available ? 1 : 0.4,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ color: '#444', fontSize: '10px', letterSpacing: '0.3px', textTransform: 'uppercase' }}>
                    {label}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <DirIcon size={11} color={sColor} />
                    <span style={{ color: sColor, fontSize: '10px', fontWeight: '700' }}>{direction}</span>
                  </div>
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
                      left: score >= 0 ? '50%' : `calc(50% - ${Math.abs(score) * 50}%)`,
                      width: `${Math.abs(score) * 50}%`,
                      transition: 'width 0.4s ease',
                    }} />
                  </div>
                </div>
                {!available && (
                  <div style={{ color: '#2a2a2a', fontSize: '10px', marginTop: '4px' }}>NOT TRACKED</div>
                )}
              </div>
            );
          })}
          </div>
        </div>
      </div>

      {/* Dominant Narrative */}
      {data.dominant_narrative && (
        <div style={{
          border: '1px solid #222',
          borderLeft: '2px solid #ff6600',
          backgroundColor: '#0d0d0d',
          padding: '12px 16px',
          marginBottom: '12px',
        }}>
          <div style={{ color: '#ff6600', fontSize: '9px', letterSpacing: '2px', marginBottom: '6px' }}>
            DOMINANT NARRATIVE
          </div>
          <div style={{ color: '#888', fontSize: '12px', lineHeight: '1.6', fontFamily: MONO }}>
            {data.dominant_narrative}
          </div>
        </div>
      )}

      {/* Top Headlines */}
      {Array.isArray(data.top_3_headlines) && data.top_3_headlines.length > 0 && (
        <div style={{ border: '1px solid #222', backgroundColor: '#0d0d0d', padding: '14px' }}>
          <SectionLabel>TOP HEADLINES</SectionLabel>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
            {data.top_3_headlines.map((hl, i) => (
              <div key={i} style={{
                padding: '8px 0',
                borderBottom: i < data.top_3_headlines.length - 1 ? '1px solid #181818' : 'none',
                color: '#555',
                fontSize: '11px',
                lineHeight: '1.5',
                fontFamily: MONO,
                display: 'flex',
                gap: '10px',
              }}>
                <span style={{ color: '#2a2a2a', flexShrink: 0 }}>{String(i + 1).padStart(2, '0')}</span>
                <span>{typeof hl === 'string' ? hl : (hl.title || hl.headline || JSON.stringify(hl))}</span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
