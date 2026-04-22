import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { TrendingUp, TrendingDown, Minus, ChevronDown, ChevronUp } from 'lucide-react';

const MONO = "'JetBrains Mono', 'Courier New', monospace";

function strengthColor(s) {
  if (s === 'STRONG')    return '#00ff41';
  if (s === 'SIGNAL')    return '#ffaa00';
  if (s === 'WEAK')      return '#ff6600';
  if (s === 'SYSTEM_FAILURE') return '#ff3333';
  return '#333';
}

function dirColor(d) {
  if (d === 'LONG')  return '#00ff41';
  if (d === 'SHORT') return '#ff3333';
  return '#444';
}

function factorColor(v) {
  if (v > 0)  return '#00ff41';
  if (v < 0)  return '#ff3333';
  return '#333';
}

function FactorRadar({ factors }) {
  const cx = 70, cy = 70, R = 48;
  const axes = [
    { key: 'F1_Trend',      label: 'TREND' },
    { key: 'F2_Momentum',   label: 'MTM'   },
    { key: 'F3_Volatility', label: 'ATR'   },
    { key: 'F4_Volume',     label: 'VOL'   },
  ];
  const N = axes.length;

  const pt = (i, r) => {
    const phi = (i / N) * 2 * Math.PI;
    return { x: cx + r * Math.sin(phi), y: cy - r * Math.cos(phi) };
  };

  // map factor value [-2..+2] → [0..R]; center = neutral (0), edge = +2
  const toR = (v) => Math.max(0, ((Math.max(-2, Math.min(2, v || 0)) + 2) / 4) * R);

  const dataPoints = axes.map((a, i) => pt(i, toR(factors[a.key] || 0)));
  const polygon = dataPoints.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  const avg = axes.reduce((s, a) => s + (factors[a.key] || 0), 0) / N;
  const fillColor = avg > 0.3 ? '#00ff41' : avg < -0.3 ? '#ff3333' : '#ffaa00';

  return (
    <svg width="140" height="140" viewBox="0 0 140 140" style={{ overflow: 'visible' }}>
      {/* Background rings at 25%, 50% (neutral), 75%, 100% */}
      {[0.25, 0.5, 0.75, 1.0].map(lvl => {
        const pts = axes.map((_, i) => { const p = pt(i, lvl * R); return `${p.x.toFixed(1)},${p.y.toFixed(1)}`; }).join(' ');
        return <polygon key={lvl} points={pts} fill="none" stroke={lvl === 0.5 ? '#2a2a2a' : '#181818'} strokeWidth={lvl === 0.5 ? '1.5' : '1'} />;
      })}
      {/* Axis lines */}
      {axes.map((_, i) => { const e = pt(i, R); return <line key={i} x1={cx} y1={cy} x2={e.x.toFixed(1)} y2={e.y.toFixed(1)} stroke="#1e1e1e" strokeWidth="1" />; })}
      {/* Data polygon */}
      <polygon points={polygon} fill={`${fillColor}1a`} stroke={fillColor} strokeWidth="1.5" strokeLinejoin="round" />
      {/* Data dots */}
      {dataPoints.map((p, i) => <circle key={i} cx={p.x.toFixed(1)} cy={p.y.toFixed(1)} r="2.5" fill={fillColor} />)}
      {/* Center dot */}
      <circle cx={cx} cy={cy} r="2" fill="#222" />
      {/* Axis labels */}
      {axes.map((a, i) => {
        const lp = pt(i, R + 14);
        return <text key={i} x={lp.x.toFixed(1)} y={lp.y.toFixed(1)} textAnchor="middle" dominantBaseline="middle" fill="#2a2a2a" fontSize="8" fontFamily="'JetBrains Mono', monospace" letterSpacing="0.5">{a.label}</text>;
      })}
    </svg>
  );
}

function ScoreStep({ label, value, sign }) {
  const isMultiplier = sign === '×';
  const isNeutral = value === 0 || value === 1.0;
  const color = isNeutral
    ? '#2a2a2a'
    : value > 0
    ? '#00ff41'
    : '#ff3333';

  const display = isMultiplier
    ? `×${value.toFixed(2)}`
    : value >= 0
    ? `+${value.toFixed(2)}`
    : value.toFixed(2);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
      <div style={{ color: '#2a2a2a', fontSize: '9px', letterSpacing: '0.5px' }}>{label}</div>
      <div style={{ color, fontSize: '11px', fontFamily: MONO, fontWeight: '600' }}>{display}</div>
    </div>
  );
}

function Arrow() {
  return <div style={{ color: '#1a1a1a', fontSize: '14px', alignSelf: 'center', marginBottom: '10px' }}>›</div>;
}

function AssetCard({ name, data: d }) {
  const [showReasons, setShowReasons] = useState(false);

  const dColor = dirColor(d.direction);
  const sColor = strengthColor(d.signal_strength);
  const DirIcon = d.direction === 'LONG' ? TrendingUp : d.direction === 'SHORT' ? TrendingDown : Minus;
  const scorePct = (d.final_score / 10) * 100;

  const factors = d.factors || {};
  const FACTOR_LABELS = {
    F1_Trend: 'TREND',
    F2_Momentum: 'MOMENTUM',
    F3_Volatility: 'VOLATILITY',
    F4_Volume: 'VOLUME',
  };

  const entryZone = d.entry_zone;
  const ezStr = Array.isArray(entryZone) && entryZone.length === 2
    ? `${entryZone[0].toFixed(2)} – ${entryZone[1].toFixed(2)}`
    : typeof entryZone === 'string'
    ? entryZone
    : '—';

  const fmt = (v) => v ? v.toFixed(4) : '—';

  return (
    <div style={{ border: '1px solid #222', backgroundColor: '#0d0d0d', marginBottom: '12px' }}>

      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 14px',
        backgroundColor: '#0a0a0a',
        borderBottom: `1px solid ${dColor}22`,
      }}>
        <div>
          <span style={{ color: '#ff6600', fontSize: '15px', fontWeight: '700', fontFamily: MONO, letterSpacing: '1px' }}>
            {d.ticker || name}
          </span>
          <span style={{ color: '#2a2a2a', fontSize: '11px', marginLeft: '10px' }}>{name}</span>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '5px',
            color: dColor, fontSize: '11px', fontWeight: '700',
            padding: '3px 10px', border: `1px solid ${dColor}`, backgroundColor: `${dColor}0d`,
            fontFamily: MONO,
          }}>
            <DirIcon size={11} />
            {d.direction}
          </div>
          <div style={{
            color: sColor, fontSize: '10px', fontWeight: '700',
            padding: '3px 10px', border: `1px solid ${sColor}`, backgroundColor: `${sColor}0d`,
            fontFamily: MONO,
          }}>
            {d.signal_strength.replace('_', ' ')}
          </div>
          <div style={{
            color: '#444', fontSize: '10px', fontFamily: MONO,
            padding: '3px 8px', border: '1px solid #1a1a1a',
          }}>
            {d.position_size_pct}% SIZE
          </div>
        </div>
      </div>

      {/* Score trail + progress */}
      <div style={{ padding: '10px 14px', borderBottom: '1px solid #181818' }}>
        <div style={{ color: '#333', fontSize: '9px', letterSpacing: '1px', marginBottom: '8px' }}>
          SCORE PIPELINE
        </div>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <ScoreStep label="BASE"    value={d.base_score}       sign="+" />
          <Arrow />
          <ScoreStep label="+QUALITY" value={d.quality_bonus}   sign="+" />
          <Arrow />
          <ScoreStep label="+VSA"    value={d.vsa_adjustment}   sign="+" />
          <Arrow />
          <ScoreStep label="+FLAGS"  value={d.flag_adjustments} sign="+" />
          {d.weekly_cap_applied && (
            <>
              <Arrow />
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
                <div style={{ color: '#ff6600', fontSize: '9px' }}>CAPPED</div>
                <div style={{ color: '#ff6600', fontSize: '10px', fontFamily: MONO }}>{d.score_cap?.toFixed(1)}</div>
              </div>
            </>
          )}
          <Arrow />
          <ScoreStep label="×MACRO"  value={d.macro_multiplier} sign="×" />
          <Arrow />
          <ScoreStep label="-NEWS"   value={d.news_penalty}     sign="+" />
          <Arrow />
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
            <div style={{ color: '#ff6600', fontSize: '9px', letterSpacing: '1px' }}>FINAL</div>
            <div style={{ color: '#ff6600', fontSize: '16px', fontWeight: '700', fontFamily: MONO }}>
              {d.final_score.toFixed(1)}<span style={{ color: '#333', fontSize: '11px' }}>/10</span>
            </div>
          </div>
        </div>
        <div style={{ marginTop: '8px', height: '3px', backgroundColor: '#111' }}>
          <div style={{ height: '100%', width: `${scorePct}%`, backgroundColor: sColor, transition: 'width 0.8s ease' }} />
        </div>
      </div>

      {/* Main content: Factors | Trade Setup | Technical Context */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0', borderBottom: '1px solid #181818' }}>

        {/* Factors */}
        <div style={{ padding: '10px 14px', borderRight: '1px solid #181818' }}>
          <div style={{ color: '#444', fontSize: '9px', letterSpacing: '1px', marginBottom: '4px' }}>FACTOR ALIGNMENT</div>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '4px' }}>
            <FactorRadar factors={factors} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            {Object.entries(FACTOR_LABELS).map(([key, label]) => {
              const val = factors[key];
              const fc = factorColor(val);
              return (
                <div key={key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#2a2a2a', fontSize: '10px' }}>{label}</span>
                  <div style={{
                    color: fc, fontSize: '11px', fontWeight: '700', fontFamily: MONO,
                    padding: '1px 8px', border: `1px solid ${fc}33`, backgroundColor: `${fc}08`,
                    minWidth: '28px', textAlign: 'center',
                  }}>
                    {val !== undefined ? (val > 0 ? `+${val}` : val) : '—'}
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{ marginTop: '6px', borderTop: '1px solid #1a1a1a', paddingTop: '5px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#333', fontSize: '10px' }}>TOTAL FACTORS</span>
              <span style={{ color: '#ff6600', fontSize: '11px', fontFamily: MONO }}>
                {d.total_factor_score > 0 ? `+${d.total_factor_score}` : d.total_factor_score}
              </span>
            </div>
          </div>
        </div>

        {/* Trade Setup */}
        <div style={{ padding: '10px 14px', borderRight: '1px solid #181818' }}>
          <div style={{ color: '#444', fontSize: '9px', letterSpacing: '1px', marginBottom: '8px' }}>TRADE SETUP</div>
          {[
            { label: 'ENTRY ZONE', value: ezStr, color: '#cccccc' },
            { label: 'STOP LOSS',  value: fmt(d.stop_loss),  color: '#ff3333' },
            { label: 'TARGET 1',   value: fmt(d.target_1),   color: '#00ff41' },
            { label: 'TARGET 2',   value: fmt(d.target_2),   color: '#00ff41' },
            { label: 'R/R RATIO',  value: d.rr_ratio ? `1:${d.rr_ratio.toFixed(2)}` : '—', color: '#ffaa00' },
          ].map(({ label, value, color }, i, arr) => (
            <div key={label} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '4px 0',
              borderBottom: i < arr.length - 1 ? '1px solid #181818' : 'none',
              fontSize: '11px',
            }}>
              <span style={{ color: '#333', fontSize: '10px' }}>{label}</span>
              <span style={{ color, fontFamily: MONO }}>{value}</span>
            </div>
          ))}
        </div>

        {/* Technical Context */}
        <div style={{ padding: '10px 14px' }}>
          <div style={{ color: '#444', fontSize: '9px', letterSpacing: '1px', marginBottom: '8px' }}>TECHNICAL CONTEXT</div>
          {[
            { label: 'WEEKLY GATE',  value: d.weekly_gate,  color: '#cccccc' },
            { label: 'ADX QUALITY',  value: d.adx_quality,  color: '#cccccc' },
            { label: 'ATR REGIME',   value: d.atr_regime,   color: '#cccccc' },
            { label: 'ATR %ile',     value: d.atr_percentile ? `${d.atr_percentile.toFixed(0)}th` : '—', color: '#cccccc' },
            { label: '4H ENTRY MODE', value: d.entry_mode,  color: '#cccccc' },
            { label: 'ENTRY CONF.',  value: d.entry_confirmed ? 'YES' : 'NO', color: d.entry_confirmed ? '#00ff41' : '#ff3333' },
            { label: 'VSA FLAG',     value: d.vsa_flag || 'NONE', color: d.vsa_flag && d.vsa_flag !== 'NONE' ? '#ffaa00' : '#2a2a2a' },
            { label: 'SUPPORT',      value: d.nearest_support  ? d.nearest_support.toFixed(2)  : '—', color: '#00ff41' },
            { label: 'RESISTANCE',   value: d.nearest_resistance ? d.nearest_resistance.toFixed(2) : '—', color: '#ff3333' },
          ].map(({ label, value, color }, i, arr) => (
            <div key={label} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '3px 0',
              borderBottom: i < arr.length - 1 ? '1px solid #181818' : 'none',
              fontSize: '11px',
            }}>
              <span style={{ color: '#333', fontSize: '10px' }}>{label}</span>
              <span style={{ color, fontFamily: MONO, fontSize: '10px' }}>{value || '—'}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Audit Trail — collapsible */}
      {Array.isArray(d.reasons) && d.reasons.length > 0 && (
        <div style={{ padding: '8px 14px' }}>
          <button
            onClick={() => setShowReasons(r => !r)}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              background: 'none', border: 'none', cursor: 'pointer',
              color: '#333', fontSize: '9px', letterSpacing: '1px', fontFamily: MONO,
              padding: 0,
            }}
          >
            {showReasons ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
            AUDIT TRAIL ({d.reasons.length} steps)
          </button>
          {showReasons && (
            <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '3px' }}>
              {d.reasons.map((r, i) => (
                <div key={i} style={{ display: 'flex', gap: '8px', fontSize: '10px' }}>
                  <span style={{ color: '#2a2a2a', flexShrink: 0, fontFamily: MONO }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span style={{ color: '#444', lineHeight: '1.5' }}>{r}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function Technicals() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await apiClient.get('/api/technicals');
        setData(res.data);
      } catch (err) {
        console.error('Failed to load technicals', err);
      } finally {
        setLoading(false);
      }
    };
    fetch();
    const interval = setInterval(fetch, 180000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div style={{ color: '#333', fontSize: '11px', letterSpacing: '1px', paddingTop: '40px', textAlign: 'center' }}>RUNNING FACTOR ANALYSIS...</div>;
  }

  if (!data || Object.keys(data).length === 0) {
    return <div style={{ color: '#333', fontSize: '11px', letterSpacing: '1px', paddingTop: '40px', textAlign: 'center' }}>NO TECHNICAL DATA AVAILABLE</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '16px' }}>
        <div style={{ color: '#ff6600', fontSize: '13px', fontWeight: '700', letterSpacing: '2px' }}>
          TECHNICAL FACTOR BREAKDOWN
        </div>
        <div style={{ color: '#333', fontSize: '10px' }}>FULL SCORING AUDIT — {Object.keys(data).length} ASSETS</div>
      </div>

      {Object.entries(data).map(([name, assetData]) => (
        <AssetCard key={name} name={name} data={assetData} />
      ))}
    </div>
  );
}
