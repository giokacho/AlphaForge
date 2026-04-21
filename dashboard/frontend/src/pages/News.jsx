import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { theme } from '../styles/theme';
import { AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react';

function dirColor(direction, t) {
  if (direction === 'BULLISH') return t.colors.signals.green;
  if (direction === 'BEARISH') return t.colors.signals.red;
  return t.colors.signals.neutral;
}

function nmBadge(nm) {
  if (!nm || typeof nm !== 'object') return 'STABLE';
  const total = Math.abs(nm.gold_change || 0) + Math.abs(nm.spx_change || 0) + Math.abs(nm.nq_change || 0);
  if (total < 0.05) return 'STABLE';
  const net = (nm.gold_change || 0) + (nm.spx_change || 0) + (nm.nq_change || 0);
  return net >= 0 ? 'ACCELERATING' : 'REVERSING';
}

function nmBadgeColor(badge, t) {
  if (badge === 'ACCELERATING') return t.colors.signals.green;
  if (badge === 'REVERSING') return t.colors.signals.red;
  return t.colors.signals.neutral;
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
    return <div style={{ color: theme.colors.text.secondary }}>Loading news intelligence...</div>;
  }

  const badge = nmBadge(data.narrative_momentum);
  const badgeColor = nmBadgeColor(badge, theme);
  const categories = data.categories || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ margin: '0 0 8px 0', fontSize: '28px', color: theme.colors.text.primary }}>News Intelligence</h1>
          <p style={{ margin: 0, color: theme.colors.text.secondary, fontSize: '15px' }}>Sentiment scoring across macro categories from live news sources.</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {/* Narrative Momentum Badge */}
          <div style={{
            padding: '6px 16px',
            borderRadius: '20px',
            border: `1px solid ${badgeColor}`,
            backgroundColor: `${badgeColor}18`,
            color: badgeColor,
            fontSize: '12px',
            fontWeight: '600',
            letterSpacing: '0.5px'
          }}>
            {badge}
          </div>
          {/* Forward Event Risk */}
          <div style={{
            padding: '6px 16px',
            borderRadius: '20px',
            border: `1px solid ${theme.colors.ui.border}`,
            backgroundColor: theme.colors.background.secondary,
            color: theme.colors.text.secondary,
            fontSize: '12px',
            fontWeight: '600'
          }}>
            EVENT RISK: {data.forward_event_risk}
          </div>
        </div>
      </div>

      {/* Contradiction Warning Banner */}
      {data.contradiction_flag && (
        <div style={{
          backgroundColor: `${theme.colors.signals.red}18`,
          border: `1px solid ${theme.colors.signals.red}`,
          borderRadius: '8px',
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '12px'
        }}>
          <AlertTriangle size={20} color={theme.colors.signals.red} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ color: theme.colors.signals.red, fontWeight: '600', fontSize: '14px', marginBottom: '4px' }}>
              Contradiction Detected
            </div>
            <div style={{ color: theme.colors.text.secondary, fontSize: '13px', lineHeight: '1.5' }}>
              {data.contradiction_reason || 'Conflicting signals across fundamental categories.'}
            </div>
          </div>
        </div>
      )}

      {/* 9-Category Sentiment Grid */}
      <div>
        <h3 style={{ color: theme.colors.text.primary, borderBottom: `1px solid ${theme.colors.ui.border}`, paddingBottom: '12px', margin: '0 0 20px 0' }}>
          Category Sentiment Scores
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          {Object.entries(categories).map(([label, cat]) => {
            const score = cat.score || 0;
            const direction = cat.direction || 'NEUTRAL';
            const available = cat.available !== false;
            const sColor = available ? dirColor(direction, theme) : theme.colors.text.secondary;
            const DirIcon = direction === 'BULLISH' ? TrendingUp : direction === 'BEARISH' ? TrendingDown : Minus;

            return (
              <div key={label} style={{
                backgroundColor: theme.colors.background.card,
                border: `1px solid ${theme.colors.ui.border}`,
                borderRadius: '8px',
                padding: '16px',
                opacity: available ? 1 : 0.45,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                  <span style={{ color: theme.colors.text.primary, fontWeight: '500', fontSize: '13px' }}>{label}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <DirIcon size={14} color={sColor} />
                    <span style={{ color: sColor, fontSize: '11px', fontWeight: '700' }}>{direction}</span>
                  </div>
                </div>

                {/* Score bar */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: sColor, width: '38px', textAlign: 'right', fontSize: '13px', fontWeight: '600' }}>
                    {score >= 0 ? '+' : ''}{score.toFixed(2)}
                  </span>
                  <div style={{ flex: 1, position: 'relative', height: '6px', backgroundColor: theme.colors.background.secondary, borderRadius: '3px' }}>
                    <div style={{ position: 'absolute', left: '50%', height: '100%', width: '1px', backgroundColor: theme.colors.ui.border }} />
                    <div style={{
                      position: 'absolute',
                      height: '100%',
                      backgroundColor: sColor,
                      left: score >= 0 ? '50%' : `calc(50% - ${Math.abs(score) * 50}%)`,
                      width: `${Math.abs(score) * 50}%`,
                      borderRadius: '3px',
                      transition: 'width 0.4s ease'
                    }} />
                  </div>
                </div>

                {!available && (
                  <div style={{ color: theme.colors.text.secondary, fontSize: '11px', marginTop: '8px', fontStyle: 'italic' }}>
                    Not tracked
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Dominant Narrative */}
      {data.dominant_narrative && (
        <div style={{
          backgroundColor: theme.colors.background.card,
          border: `1px solid ${theme.colors.ui.border}`,
          borderLeft: `4px solid ${theme.colors.accent.blue}`,
          borderRadius: '8px',
          padding: '20px 24px'
        }}>
          <div style={{ color: theme.colors.text.secondary, fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>
            Dominant Narrative
          </div>
          <div style={{ color: theme.colors.text.primary, fontSize: '15px', lineHeight: '1.6' }}>
            {data.dominant_narrative}
          </div>
        </div>
      )}

      {/* Top Headlines */}
      {Array.isArray(data.top_3_headlines) && data.top_3_headlines.length > 0 && (
        <div>
          <h3 style={{ color: theme.colors.text.primary, borderBottom: `1px solid ${theme.colors.ui.border}`, paddingBottom: '12px', margin: '0 0 16px 0' }}>
            Top Headlines
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {data.top_3_headlines.map((hl, i) => (
              <div key={i} style={{
                backgroundColor: theme.colors.background.card,
                border: `1px solid ${theme.colors.ui.border}`,
                borderRadius: '8px',
                padding: '14px 18px',
                color: theme.colors.text.secondary,
                fontSize: '14px',
                lineHeight: '1.5'
              }}>
                {typeof hl === 'string' ? hl : (hl.title || hl.headline || JSON.stringify(hl))}
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
