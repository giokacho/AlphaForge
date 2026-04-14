import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { theme } from '../styles/theme';
import Skeleton from '../components/Skeleton';
import { TrendingUp, TrendingDown, Swords } from 'lucide-react';

export default function Debate() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/api/debate');
        setData(response.data);
      } catch (err) {
        console.error("Failed to load debate", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 180000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !data) {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
             <Skeleton height="140px" />
             <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
                 <Skeleton height="350px" />
                 <Skeleton height="350px" />
                 <Skeleton height="350px" />
             </div>
             <Skeleton height="150px" />
        </div>
    );
  }

  // Verdict processing
  const direction = data.final_direction || 'NO_SIGNAL';
  const dColor = direction === 'LONG' ? theme.colors.signals.green : direction === 'SHORT' ? theme.colors.signals.red : theme.colors.text.secondary;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '28px', color: theme.colors.text.primary }}>Neural Synthesis Board</h1>
        <p style={{ margin: 0, color: theme.colors.text.secondary, fontSize: '15px' }}>CIO-level debate synthesis intersecting structural bull, bear, and tail-risk cases.</p>
      </div>

      {/* Top Card */}
      <div style={{
          backgroundColor: theme.colors.background.card,
          border: `1px solid ${theme.colors.ui.border}`,
          borderRadius: '12px',
          padding: '32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
      }}>
          <div>
              <span style={{ color: theme.colors.text.secondary, fontSize: '14px', textTransform: 'uppercase', letterSpacing: '1px' }}>Final Verdict</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '12px' }}>
                  <div style={{
                      padding: '8px 24px',
                      backgroundColor: `${dColor}22`,
                      border: `2px solid ${dColor}`,
                      borderRadius: '8px',
                      color: dColor,
                      fontSize: '32px',
                      fontWeight: 'bold',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px'
                  }}>
                      {direction === 'LONG' ? <TrendingUp size={28}/> : direction === 'SHORT' ? <TrendingDown size={28}/> : <Swords size={28}/>}
                      {direction}
                  </div>
              </div>
          </div>
          <div style={{ textAlign: 'right' }}>
              <span style={{ color: theme.colors.text.secondary, fontSize: '14px', textTransform: 'uppercase', letterSpacing: '1px' }}>Conviction Model</span>
              <div style={{ fontSize: '48px', fontWeight: 'bold', color: theme.colors.text.primary, lineHeight: '1.2' }}>
                  {data.conviction_score}<span style={{ fontSize: '24px', color: theme.colors.text.secondary }}>/10</span>
              </div>
          </div>
      </div>

      {/* 3 Panels */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
          {/* Bull */}
          <div style={{
              backgroundColor: theme.colors.background.card,
              borderLeft: `4px solid ${theme.colors.signals.green}`,
              borderRadius: '8px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column'
          }}>
              <h3 style={{ margin: '0 0 16px 0', color: theme.colors.text.primary, fontSize: '18px' }}>Structural Bull Case</h3>
              <div style={{ color: theme.colors.text.secondary, fontSize: '14px', lineHeight: '1.6', flex: 1, overflowY: 'auto', maxHeight: '400px', whiteSpace: 'pre-wrap' }}>
                  {data.bull_case}
              </div>
          </div>
          {/* Bear */}
          <div style={{
              backgroundColor: theme.colors.background.card,
              borderLeft: `4px solid ${theme.colors.signals.red}`,
              borderRadius: '8px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column'
          }}>
              <h3 style={{ margin: '0 0 16px 0', color: theme.colors.text.primary, fontSize: '18px' }}>Structural Bear Case</h3>
              <div style={{ color: theme.colors.text.secondary, fontSize: '14px', lineHeight: '1.6', flex: 1, overflowY: 'auto', maxHeight: '400px', whiteSpace: 'pre-wrap' }}>
                  {data.bear_case}
              </div>
          </div>
          {/* Risk */}
          <div style={{
              backgroundColor: theme.colors.background.card,
              borderLeft: `4px solid ${theme.colors.signals.neutral}`,
              borderRadius: '8px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column'
          }}>
              <h3 style={{ margin: '0 0 16px 0', color: theme.colors.text.primary, fontSize: '18px' }}>Tail Risk Considerations</h3>
              <div style={{ color: theme.colors.text.secondary, fontSize: '14px', lineHeight: '1.6', flex: 1, overflowY: 'auto', maxHeight: '400px', whiteSpace: 'pre-wrap' }}>
                  {data.risk_case}
              </div>
          </div>
      </div>

      {/* Synthesis Component */}
      <div style={{
          backgroundColor: theme.colors.background.card,
          borderLeft: `4px solid ${theme.colors.accent.blue}`,
          borderTopRightRadius: '8px',
          borderBottomRightRadius: '8px',
          padding: '24px',
      }}>
          <h3 style={{ margin: '0 0 16px 0', color: theme.colors.text.primary, fontSize: '18px' }}>Final Strategic Synthesis</h3>
          <div style={{ color: theme.colors.text.secondary, fontSize: '15px', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
             {data.synthesis}
          </div>
      </div>

    </div>
  );
}
