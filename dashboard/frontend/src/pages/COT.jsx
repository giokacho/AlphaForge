import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';

const MONO = "'JetBrains Mono', 'Courier New', monospace";

const TICKER_MAP = {
  Gold:   'GC=F',
  SPX:    '^GSPC',
  NQ:     '^NDX',
  DOW:    '^DJI',
  BTC:    'BTC-USD',
  ETH:    'ETH-USD',
  Oil:    'CL=F',
  EURUSD: 'EURUSD=X',
  USDJPY: 'JPY=X',
  USDCAD: 'CAD=X',
};

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

const SectionLabel = ({ children }) => (
  <div style={{
    color: '#ff6600',
    fontSize: '9px',
    fontWeight: '700',
    letterSpacing: '1.5px',
    borderBottom: '1px solid #222',
    paddingBottom: '5px',
    marginBottom: '8px',
  }}>
    {children}
  </div>
);

const DataRow = ({ label, value, valueColor = '#cccccc', noBorder }) => (
  <div style={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '5px 0',
    borderBottom: noBorder ? 'none' : '1px solid #181818',
    fontSize: '11px',
  }}>
    <span style={{ color: '#444' }}>{label}</span>
    <span style={{ color: valueColor, fontFamily: MONO }}>{value}</span>
  </div>
);

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
        console.error('Failed to load COT', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 180000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !data.cot || !data.signals) {
    return <div style={{ color: '#333', fontSize: '11px', letterSpacing: '1px', paddingTop: '40px', textAlign: 'center' }}>LOADING COT POSITIONING...</div>;
  }

  const getCrowdingColor = (r) => {
    if (r === 'LOW')  return '#00ff41';
    if (r === 'HIGH') return '#ff3333';
    return '#ffaa00';
  };

  // Merge COT assets and signal assets — use signal keys as primary source
  const allAssets = Array.from(new Set([
    ...Object.keys(data.signals),
    ...Object.keys(data.cot),
  ]));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '16px' }}>
        <div style={{ color: '#ff6600', fontSize: '13px', fontWeight: '700', letterSpacing: '2px' }}>
          INSTITUTIONAL & TECHNICAL PROFILES
        </div>
        <div style={{ color: '#333', fontSize: '10px' }}>COT POSITIONING × MULTI-FACTOR TECHNICALS</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
        {allAssets.map(assetId => {
          const cotData = data.cot[assetId]  || {};
          const sigData = data.signals[assetId] || {};
          const ticker   = sigData.ticker || TICKER_MAP[assetId] || assetId;
          const fullName = FULL_NAMES[assetId] || assetId;

          const bias    = cotData.institutional_bias || 'NO COT DATA';
          const hasCOT  = !!cotData.institutional_bias;
          const bColor  = hasCOT
            ? (bias.includes('LONG') ? '#00ff41' : bias.includes('SHORT') ? '#ff3333' : '#444')
            : '#2a2a2a';

          const pTile = typeof cotData.positioning_percentile === 'number' ? cotData.positioning_percentile : null;
          const pTileColor = pTile !== null
            ? (pTile >= 80 ? '#ff3333' : pTile <= 20 ? '#00ff41' : '#ffaa00')
            : '#444';

          return (
            <div key={assetId} style={{ border: '1px solid #222', backgroundColor: '#0d0d0d' }}>

              {/* Card header */}
              <div style={{ padding: '8px 12px', backgroundColor: '#0a0a0a', borderBottom: '1px solid #222' }}>
                <div style={{ color: '#ff6600', fontSize: '13px', fontWeight: '700', fontFamily: MONO, letterSpacing: '1px' }}>
                  {ticker}
                </div>
                <div style={{ color: '#333', fontSize: '10px', letterSpacing: '0.5px' }}>{fullName}</div>
              </div>

              <div style={{ padding: '10px 12px' }}>

                {/* COT section */}
                <SectionLabel>CFTC POSITIONING</SectionLabel>

                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '6px 8px',
                  border: `1px solid ${bColor}33`,
                  backgroundColor: `${bColor}08`,
                  marginBottom: '8px',
                  opacity: hasCOT ? 1 : 0.4,
                }}>
                  <span style={{ color: '#444', fontSize: '10px', letterSpacing: '1px' }}>INSTITUTIONAL BIAS</span>
                  <span style={{ color: bColor, fontSize: '12px', fontWeight: '700', fontFamily: MONO }}>{bias}</span>
                </div>

                {hasCOT && (
                  <>
                    <DataRow
                      label="POSITIONING %ile"
                      value={pTile !== null ? `${pTile.toFixed(0)}th` : 'N/A'}
                      valueColor={pTileColor}
                    />
                    {pTile !== null && (
                      <div style={{ marginBottom: '8px', marginTop: '4px' }}>
                        <div style={{ height: '3px', backgroundColor: '#1a1a1a', position: 'relative' }}>
                          <div style={{ height: '100%', width: `${pTile}%`, backgroundColor: pTileColor }} />
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: '#2a2a2a', marginTop: '2px' }}>
                          <span>0</span><span>50</span><span>100</span>
                        </div>
                      </div>
                    )}
                    <DataRow
                      label="CROWDING RISK"
                      value={cotData.crowding_risk || 'UNKNOWN'}
                      valueColor={getCrowdingColor(cotData.crowding_risk)}
                      noBorder
                    />
                  </>
                )}

                {/* Technicals section */}
                <div style={{ borderTop: '1px solid #1a1a1a', marginTop: '10px', paddingTop: '10px' }}>
                  <SectionLabel>CORE TECHNICALS</SectionLabel>
                  <DataRow label="WEEKLY GATE"  value={sigData.weekly_gate || '—'} />
                  <DataRow label="ATR REGIME"   value={sigData.atr_regime  || '—'} />
                  <DataRow label="4H ENTRY MODE" value={sigData.entry_mode || '—'} />
                  <DataRow label="VSA SIGNATURE" value={sigData.vsa_flag || 'NONE'}
                    valueColor={sigData.vsa_flag && sigData.vsa_flag !== 'NONE' ? '#ffaa00' : '#2a2a2a'} noBorder />
                </div>

                {/* Factor signatures */}
                {Object.keys(sigData.factors || {}).length > 0 && (
                  <div style={{ borderTop: '1px solid #1a1a1a', marginTop: '10px', paddingTop: '10px' }}>
                    <SectionLabel>FACTOR SIGNATURES</SectionLabel>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {Object.entries(sigData.factors).map(([fk, fv]) => {
                        const fColor = fv >= 1 ? '#00ff41' : fv <= -1 ? '#ff3333' : '#333';
                        return (
                          <div key={fk} style={{
                            padding: '2px 6px',
                            border: `1px solid ${fColor}44`,
                            backgroundColor: `${fColor}08`,
                            color: fColor,
                            fontSize: '10px',
                            fontFamily: MONO,
                          }}>
                            {fk.replace('F1_', '').replace('F2_', '').replace('F3_', '').replace('F4_', '')}:{fv > 0 ? `+${fv}` : fv}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
