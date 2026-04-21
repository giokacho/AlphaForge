import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { theme } from '../styles/theme';

export default function Macro() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/api/macro');
        setData(response.data);
      } catch (err) {
        console.error("Failed to load macro", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 180000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !data) {
    return <div style={{ color: theme.colors.text.secondary }}>Scanning macro intelligence...</div>;
  }

  const regimeColors = {
    'RISK_ON': theme.colors.accent.blue,
    'RISK_OFF': theme.colors.signals.red,
    'TRANSITION': theme.colors.signals.neutral,
    'UNKNOWN': theme.colors.text.secondary
  };

  const rgColor = regimeColors[data.macro_regime] || regimeColors['UNKNOWN'];
  
  // Hawk/Dove Math. Scale: -5 (Dovish) to +5 (Hawkish)
  const hd = typeof data.hawk_dove_score === 'number' ? data.hawk_dove_score : 0;
  const hdPercent = ((hd + 5) / 10) * 100;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '28px', color: theme.colors.text.primary }}>Macro & Sentiment</h1>
        <p style={{ margin: 0, color: theme.colors.text.secondary, fontSize: '15px' }}>Global regime context and central bank narrative tracking.</p>
      </div>

      {/* Top Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 2fr)', gap: '24px' }}>
         <div style={{
           backgroundColor: theme.colors.background.card,
           border: `1px solid ${theme.colors.ui.border}`,
           borderRadius: '12px',
           padding: '32px',
           display: 'flex',
           flexDirection: 'column',
           alignItems: 'center',
           justifyContent: 'center',
           gap: '16px'
         }}>
            <h3 style={{ color: theme.colors.text.secondary, margin: 0, fontSize: '16px' }}>Current Macro Regime</h3>
            <div style={{ 
               padding: '12px 32px', 
               backgroundColor: `${rgColor}22`, 
               border: `2px solid ${rgColor}`, 
               borderRadius: '8px', 
               color: rgColor,
               fontSize: '24px',
               fontWeight: 'bold',
               textTransform: 'uppercase'
            }}>
               {data.macro_regime}
            </div>
         </div>

         {/* Hawk/Dove Meter */}
         <div style={{
           backgroundColor: theme.colors.background.card,
           border: `1px solid ${theme.colors.ui.border}`,
           borderRadius: '12px',
           padding: '32px',
           display: 'flex',
           flexDirection: 'column',
           justifyContent: 'center'
         }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
               <h3 style={{ color: theme.colors.text.secondary, margin: 0, fontSize: '16px' }}>Central Bank Bias (Hawk/Dove)</h3>
               <strong style={{ color: theme.colors.text.primary, fontSize: '18px' }}>{hd.toFixed(1)}</strong>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', color: theme.colors.text.secondary, fontSize: '12px', marginBottom: '8px' }}>
               <span>-5 (Ultra Dovish)</span>
               <span>0 (Neutral)</span>
               <span>+5 (Ultra Hawkish)</span>
            </div>
            <div style={{ position: 'relative', height: '12px', backgroundColor: theme.colors.background.secondary, borderRadius: '6px' }}>
                <div style={{ 
                   position: 'absolute', 
                   left: '50%', 
                   height: '100%', 
                   width: '2px', 
                   backgroundColor: theme.colors.ui.border 
                }} />
                <div style={{
                   position: 'absolute',
                   top: '-6px',
                   bottom: '-6px',
                   left: `calc(${hdPercent}% - 4px)`,
                   width: '8px',
                   backgroundColor: theme.colors.text.primary,
                   borderRadius: '4px',
                   boxShadow: `0 0 10px ${theme.colors.text.primary}`,
                   transition: 'left 1s ease'
                }} />
            </div>
         </div>
      </div>

      {/* Sentiment Cards */}
      <div>
         <h3 style={{ color: theme.colors.text.primary, borderBottom: `1px solid ${theme.colors.ui.border}`, paddingBottom: '12px' }}>Indicator Sentiment Scorer</h3>
         <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginTop: '20px' }}>
            {Object.entries(data.sentiment_scores || {}).map(([indicator, details]) => {
                const score = details.score || 0;
                const direction = details.direction || 'NEUTRAL';
                const sColor = score > 0 ? theme.colors.signals.green : score < 0 ? theme.colors.signals.red : theme.colors.signals.neutral;
                
                // Map the -1 to 1 into a width representation from center (half the bar)
                const widthMultiplier = Math.abs(score);
                
                return (
                   <div key={indicator} style={{
                      backgroundColor: theme.colors.background.card,
                      border: `1px solid ${theme.colors.ui.border}`,
                      borderRadius: '8px',
                      padding: '16px'
                   }}>
                       <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                           <span style={{ color: theme.colors.text.primary, fontWeight: '500', textTransform: 'capitalize' }}>
                               {indicator.replace(/_/g, ' ')}
                           </span>
                           <span style={{ color: sColor, fontSize: '12px', fontWeight: 'bold' }}>{direction}</span>
                       </div>
                       <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                           <span style={{ color: theme.colors.text.secondary, width: '30px', textAlign: 'right', fontSize: '12px' }}>{score.toFixed(2)}</span>
                           <div style={{ flex: 1, position: 'relative', height: '6px', backgroundColor: theme.colors.background.secondary, borderRadius: '3px' }}>
                               {/* Center Line */}
                               <div style={{ position: 'absolute', left: '50%', height: '100%', width: '2px', backgroundColor: theme.colors.ui.border }} />
                               {/* Active fill */}
                               <div style={{
                                   position: 'absolute',
                                   height: '100%',
                                   backgroundColor: sColor,
                                   left: score > 0 ? '50%' : `calc(50% - ${widthMultiplier * 50}%)`,
                                   width: `${widthMultiplier * 50}%`,
                                   borderRadius: '3px'
                               }} />
                           </div>
                       </div>
                   </div>
                );
            })}
         </div>
      </div>

      {/* Narrative Momentum */}
      <div>
         <h3 style={{ color: theme.colors.text.primary, borderBottom: `1px solid ${theme.colors.ui.border}`, paddingBottom: '12px' }}>Narrative Momentum</h3>
         <div style={{
            backgroundColor: theme.colors.background.secondary,
            padding: '24px',
            borderRadius: '8px',
            border: `1px solid ${theme.colors.ui.border}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
         }}>
            {(() => {
               const nm = (typeof data.narrative_momentum === 'object' && data.narrative_momentum !== null)
                  ? data.narrative_momentum : {};
               const rows = [
                  { label: 'Gold Change',  val: nm.gold_change },
                  { label: 'SPX Change',   val: nm.spx_change },
                  { label: 'NQ Change',    val: nm.nq_change },
               ];
               const shifting = Array.isArray(nm.shifting_assets) && nm.shifting_assets.length > 0
                  ? nm.shifting_assets.join(', ') : 'None';
               return (
                  <>
                     {rows.map(({ label, val }) => {
                        const n = typeof val === 'number' ? val : 0;
                        const color = n > 0 ? theme.colors.signals.green : n < 0 ? theme.colors.signals.red : theme.colors.text.secondary;
                        return (
                           <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ color: theme.colors.text.secondary, fontSize: '14px' }}>{label}</span>
                              <span style={{ color, fontWeight: '600', fontSize: '14px' }}>
                                 {n >= 0 ? '+' : ''}{n.toFixed(4)}
                              </span>
                           </div>
                        );
                     })}
                     <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: `1px solid ${theme.colors.ui.border}`, paddingTop: '12px' }}>
                        <span style={{ color: theme.colors.text.secondary, fontSize: '14px' }}>Shifting Assets</span>
                        <span style={{ color: theme.colors.text.primary, fontSize: '14px' }}>{shifting}</span>
                     </div>
                  </>
               );
            })()}
         </div>
      </div>

      {/* Macro Briefing */}
      {data.narrative_text && (
         <div>
            <h3 style={{ color: theme.colors.text.primary, borderBottom: `1px solid ${theme.colors.ui.border}`, paddingBottom: '12px' }}>Macro Briefing</h3>
            <div style={{
               backgroundColor: theme.colors.background.secondary,
               padding: '24px',
               borderRadius: '8px',
               border: `1px solid ${theme.colors.ui.border}`,
               color: theme.colors.text.secondary,
               fontSize: '14px',
               lineHeight: '1.8',
               whiteSpace: 'pre-wrap'
            }}>
               {data.narrative_text}
            </div>
         </div>
      )}
    </div>
  );
}
